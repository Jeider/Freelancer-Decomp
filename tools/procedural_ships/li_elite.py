"""Offline li_elite Medium geometry experiment. Source and installation stay read-only."""
import argparse
import collections
import hashlib
import heapq
import io
import json
import math
from pathlib import Path
import struct as S
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT/'tools/procedural_asteroids'))
from generate_station_lods import Node, read_tree, write_tree, child
from repair_panel_normals import leaves
from refine import crc

GAME = Path('D:/games/FL_MOD')
SOURCE = GAME/'DATA/SHIPS/LIBERTY/LI_ELITE/li_elite.cmp'
MAT = GAME/'DATA/SHIPS/LIBERTY/li_playerships.mat'
OUT = ROOT/'src/obj/procedural_ships/li_elite_medium'


def string(b):
    return b.split(b'\0', 1)[0].decode('latin1')


def walk(nodes, prefix=''):
    for node in nodes:
        path = prefix+'/'+node.name
        if node.blob is not None:
            yield path, node
        else:
            yield from walk(node.children, path)


def unit(v):
    return v/np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-20)


def decode(blob):
    flags, primitive, ng, ni, fvf, nv = S.unpack_from('<II4H', blob)
    if primitive != 4 or fvf != 0x112 or ni % 3 or flags != 1:
        raise ValueError('Expected relative-index XYZ/N/UV triangle mesh')
    start = 16+12*ng
    end = start+2*ni+nv*32
    if len(blob) not in (end, (end+3)&~3) or any(blob[end:]):
        raise ValueError('Unexpected mesh size')
    vertices = np.frombuffer(blob, '<f4', nv*8, start+2*ni).reshape(nv, 8).astype(float)
    indices = np.frombuffer(blob, '<u2', ni, start).astype(int)
    groups, offset = [], 0
    for i in range(ng):
        material, lo, hi, count, unused = S.unpack_from('<I4H', blob, 16+12*i)
        if count % 3: raise ValueError('Non-triangle group')
        groups.append(dict(material=material, low=lo, high=hi, unused=unused,
                           faces=indices[offset:offset+count].reshape(-1, 3)+lo))
        offset += count
    if offset != ni: raise ValueError('Index count mismatch')
    return vertices, groups


def extract_part(ref, libraries):
    size, mesh_id, start, count, index, nindex, group, ng = S.unpack_from('<II6H', ref)
    if size != 60 or len(ref) != 60: raise ValueError('Unsupported VMeshRef')
    verts, groups = libraries[mesh_id]
    subset = groups[group:group+ng]
    if len(subset) != ng or sum(len(g['faces'])*3 for g in subset) != nindex:
        raise ValueError('Partial group reference')
    if sum(len(g['faces'])*3 for g in groups[:group]) != index:
        raise ValueError('Reference index offset mismatch')
    out = []
    for g in subset:
        ids = g['faces']+start
        if ids.min() < start or ids.max() >= start+count or ids.max() >= len(verts):
            raise ValueError('Reference vertex range mismatch')
        out.append(dict(material=g['material'], unused=g['unused'], corners=verts[ids].copy()))
    return out


def materials():
    props, textures = collections.defaultdict(dict), {}
    for path, _, blob in leaves(MAT.read_bytes())[1]:
        chunks = path.split('/')
        if '/material library/' in path.lower():
            props[chunks[-2]][chunks[-1].lower()] = blob
        if '/texture library/' in path.lower() and chunks[-1].lower() in ('mips', 'mip0'):
            textures[chunks[-2].lower()] = Image.open(io.BytesIO(blob)).convert('RGB')
    result = {}
    for name, p in props.items():
        texture = string(p.get('dt_name', b'')).lower()
        # Explicitly exclude the single-sheet wing skins, glass, placeholders and mounts.
        # Protected materials in a changed part may still get a finer grid so
        # triangle edges match; entirely protected parts stay byte-identical.
        eligible = name.lower() in ('elite_256', 'elite_256b', 'elite_256r', 'elite_256lb', 'metal03', 'engine_grill01')
        result[crc(name)] = dict(name=name, texture=texture, image=textures.get(texture),
                                eligible=eligible, kind=string(p.get('type', b'')),
                                colour=np.frombuffer(p.get('dc', S.pack('<3f', 1, 1, 1)), '<f4')[:3].astype(float))
    return result


def transforms(nodes):
    data = {p.lower(): n.blob for p, n in walk(nodes)}
    names, joints = {}, {}
    for path, blob in data.items():
        if '/cmpnd/' in path and path.endswith('/file name'):
            names[string(blob).lower()] = string(data[path.rsplit('/', 1)[0]+'/object name']).lower()
    for path, blob in data.items():
        if '/cmpnd/cons/' not in path: continue
        kind = path.rsplit('/', 1)[-1]
        size = {'fix': 176, 'rev': 208, 'pris': 208}[kind]
        if len(blob) % size: raise ValueError('Unexpected constraint size')
        for at in range(0, len(blob), size):
            parent, name = string(blob[at:at+64]).lower(), string(blob[at+64:at+128]).lower()
            f = np.frombuffer(blob, '<f4', (size-128)//4, at+128).astype(float)
            if kind == 'fix':
                rotation, translation = f[3:12].reshape(3, 3), f[:3]
            else:
                # Zero-state construct pose: origin - rotation * child pivot.
                rotation = f[6:15].reshape(3, 3)
                translation = f[:3]-rotation @ f[3:6]
            joints[name] = (parent, rotation, translation)
    resolved = {'root': (np.eye(3), np.zeros(3))}
    def resolve(name):
        if name not in resolved:
            parent, r, t = joints[name]
            pr, pt = resolve(parent)
            resolved[name] = pr @ r, pr @ t+pt
        return resolved[name]
    return {file: resolve(name) for file, name in names.items()}


def inspect():
    OUT.mkdir(parents=True, exist_ok=True)
    _, nodes = read_tree(SOURCE.read_bytes())
    mats = materials()
    libs = {crc(p.split('/')[-2]): decode(n.blob) for p,n in walk(nodes) if p.endswith('/VMeshData')}
    refs = [(p, extract_part(n.blob, libs)) for p,n in walk(nodes) if '/Level0/' in p and p.endswith('/VMeshRef')]
    rows = []
    for p, gs in refs:
        rows.append(dict(part=p.split('/')[2], triangles=sum(len(g['corners']) for g in gs),
                         materials=[mats.get(g['material'], {}).get('name', hex(g['material'])) for g in gs]))
    used = {g['material'] for _, gs in refs for g in gs}
    images, seen = [], set()
    for k in sorted(used):
        m = mats[k]
        if m['image'] is None or m['texture'] in seen: continue
        seen.add(m['texture'])
        images.append(m)
    sheet = Image.new('RGB', (400*3, 440*math.ceil(len(images)/3)), (24,29,37))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 17)
    for i,m in enumerate(images):
        x,y = (i%3)*400,(i//3)*440
        sheet.paste(m['image'].resize((390,390)), (x,y+35))
        d.text((x+8,y+5), m['texture'], font=font, fill='white')
    sheet.save(OUT/'source_textures.jpg')
    print(json.dumps(rows, indent=2))


def sample(array, uv):
    """D3D-style wrapped bilinear sample with top-left image origin."""
    h, w = array.shape[:2]
    xy = uv*np.array([w, h])-.5
    ij = np.floor(xy).astype(int)
    f = xy-ij
    if array.ndim == 3: f = f[..., None]
    x, y = ij[:, 0]%w, ij[:, 1]%h
    return ((1-f[:, 0])*(1-f[:, 1])*array[y,x]+f[:, 0]*(1-f[:, 1])*array[y,(x+1)%w]
            +(1-f[:, 0])*f[:, 1]*array[(y+1)%h,x]+f[:, 0]*f[:, 1]*array[(y+1)%h,(x+1)%w])


def recess_map(im):
    # This is an intentionally strong, heuristic interpretation of the existing
    # painted texture, not recovery of artist-authored physical depth.
    im = im.resize((512, 512), Image.Resampling.LANCZOS).convert('L')
    small = np.asarray(im.filter(ImageFilter.GaussianBlur(1.5)), float)/255
    broad = np.asarray(im.filter(ImageFilter.GaussianBlur(12)), float)/255
    dark = np.clip((np.percentile(small, 75)-small)/max(np.ptp(np.percentile(small, [8,75])), .1), 0, 1)
    valley = np.clip((broad-small-.015)/.14, 0, 1)
    mask = np.clip(.45*dark+.8*valley, 0, 1)
    # A narrow texture groove must span several vertices to read at a Medium
    # polygon budget. Modest dilation makes the diagnostic relief legible.
    pic = Image.fromarray(np.rint(mask*255).astype('uint8'))
    return np.asarray(pic.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2)), float)/255


def thickness_limits(points, directions, triangles, requested):
    """Limit inward displacement to 35% of the first original-surface ray hit."""
    a = triangles[:, 0]
    e1, e2 = triangles[:, 1]-a, triangles[:, 2]-a
    result = np.full(len(points), requested)
    for at in range(0, len(points), 128):
        pos, ray = points[at:at+128], -directions[at:at+128]
        h = np.cross(ray[:, None, :], e2[None])
        det = np.einsum('tq,btq->bt', e1, h)
        inv = np.divide(1, det, out=np.zeros_like(det), where=np.abs(det)>1e-10)
        s = pos[:, None, :]-a[None]
        u = np.einsum('btq,btq->bt', s, h)*inv
        q = np.cross(s, e1[None])
        v = np.einsum('bq,btq->bt', ray, q)*inv
        t = np.einsum('tq,btq->bt', e2, q)*inv
        hit = (np.abs(det)>1e-10)&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(t>1e-4)
        distance = np.where(hit, t, np.inf).min(axis=1)
        result[at:at+len(pos)] = np.minimum(requested, distance*.35)
    return result


def adaptive_grid(original, baseids, eligible, target):
    """Conforming longest-edge splits, with a fixed Medium triangle budget.

    Barycentric provenance keeps all texture coordinates on the authored chart.
    All incident faces split together, including across material boundaries.
    """
    point_count=int(baseids.max())+1
    points=np.zeros((point_count,3))
    for ids,face in zip(baseids,original):points[ids]=face[:,:3]
    points=list(points)
    triangles={}
    edges=collections.defaultdict(set)
    heap=[]
    serial=0
    def score(edge):
        users=edges[edge]
        if not users:return 0.
        length=float(np.sum((points[edge[0]]-points[edge[1]])**2))
        # Keep protected mounts light and put the budget into textured hulls.
        gain=1. if any(eligible[triangles[f][0]] for f in users) else .04
        return length*gain
    def add(parent,ids,bary):
        nonlocal serial
        ix=serial;serial+=1
        triangles[ix]=(parent,tuple(ids),bary)
        for i,j in ((0,1),(1,2),(2,0)):
            edge=tuple(sorted((int(ids[i]),int(ids[j]))))
            edges[edge].add(ix)
            heapq.heappush(heap,(-score(edge),edge))
    def remove(ix):
        parent,ids,bary=triangles.pop(ix)
        for i,j in ((0,1),(1,2),(2,0)):
            edges[tuple(sorted((ids[i],ids[j])))].remove(ix)
        return parent,ids,bary
    for f,ids in enumerate(baseids):add(f,ids,np.eye(3))
    while len(triangles)<target:
        if not heap:raise ValueError('Adaptive grid exhausted')
        priority,edge=heapq.heappop(heap)
        users=sorted(edges[edge])
        if not users:continue
        actual=score(edge)
        if abs(actual+priority)>1e-10:
            heapq.heappush(heap,(-actual,edge));continue
        if len(triangles)+len(users)>target:continue
        midpoint=len(points);points.append((points[edge[0]]+points[edge[1]])/2)
        for ix in users:
            parent,ids,bary=remove(ix)
            for i,j,k in ((0,1,2),(1,2,0),(2,0,1)):
                if tuple(sorted((ids[i],ids[j])))==edge:break
            mb=(bary[i]+bary[j])/2
            add(parent,(ids[i],midpoint,ids[k]),np.array([bary[i],mb,bary[k]]))
            add(parent,(midpoint,ids[j],ids[k]),np.array([mb,bary[j],bary[k]]))
    result=[[] for _ in original]
    for f,ids,bary in triangles.values():result[f].append(bary)
    return [np.array(x).reshape(-1,3) for x in result]


def refine_part(groups, mats, depth, hardpoints):
    original = np.concatenate([g['corners'] for g in groups])
    ntri = len(original)
    eligible = np.concatenate([np.full(len(g['corners']), mats[g['material']]['eligible']) for g in groups])
    if not eligible.any(): return groups, dict(original_triangles=ntri, triangles=ntri, unchanged=True)
    face_materials = np.concatenate([np.full(len(g['corners']), g['material'], dtype=np.uint32) for g in groups])
    # Vertex/edge identity is geometric; attribute discontinuities are protected.
    keys, baseids = {}, []
    for p in original[..., :3].reshape(-1, 3):
        key = tuple(np.round(p, 5))
        baseids.append(keys.setdefault(key, len(keys)))
    baseids = np.array(baseids).reshape(-1, 3)
    cross = np.cross(original[:, 1,:3]-original[:, 0,:3], original[:, 2,:3]-original[:, 0,:3])
    flat = unit(cross)
    edge_uses = collections.defaultdict(list)
    for f, ids in enumerate(baseids):
        for i,j in ((0,1),(1,2),(2,0)):
            edge_uses[tuple(sorted((int(ids[i]),int(ids[j]))))].append((f,i,j))
    locked = set()
    for edge, uses in edge_uses.items():
        good = len(uses)==2
        if good:
            (a,i,j),(b,k,l) = uses
            if baseids[a,i] != baseids[b,k]: k,l = l,k
            good = (eligible[a] and eligible[b] and face_materials[a]==face_materials[b]
                    and np.dot(flat[a],flat[b])>math.cos(math.radians(30))
                    and np.max(np.abs(original[a,[i,j],6:]-original[b,[k,l],6:]))<1e-4
                    and np.min(np.sum(unit(original[a,[i,j],3:6])*unit(original[b,[k,l],3:6]),axis=1))>.98)
        if not good: locked.add(edge)
    grids=adaptive_grid(original,baseids,eligible,ntri*16)
    fine=np.concatenate([bary@face for bary,face in zip(grids,original)])
    pointids, points, normals, weights, masks, flags = [], [], [], [], [], []
    weld = {}
    # Shared geometric samples get a single displacement. Protected edges and
    # chart boundaries stay fixed even if different texture charts disagree.
    fine_offset=0
    for f, (face,bary) in enumerate(zip(original,grids)):
        values=fine[fine_offset:fine_offset+len(bary)]
        fine_offset+=len(bary)
        material = mats[int(face_materials[f])]
        mask = sample(material['mask'],values[:,6:]) if eligible[f] else np.zeros(len(bary))
        edge_lengths = [np.linalg.norm(face[i,:3]-face[j,:3]) for i,j in ((0,1),(1,2),(2,0))]
        local_cap = .23*min(edge_lengths)
        anchor = np.ones(len(bary))
        for opposite,(i,j) in enumerate(((1,2),(0,2),(0,1))):
            edge = tuple(sorted((int(baseids[f,i]),int(baseids[f,j]))))
            if edge in locked:
                anchor *= np.clip(bary[:,opposite]*4,0,1)
        if len(hardpoints):
            distance = np.linalg.norm(values[:,:3,None]-hardpoints.T[None],axis=1).min(axis=1)
            anchor *= np.clip((distance-.12)/.20,0,1)
        for row, value in enumerate(values):
            key = tuple(np.round(value[:3],5))
            if key not in weld:
                weld[key] = len(points)
                points.append(value[:3].copy()); normals.append(np.zeros(3)); weights.append(0)
                masks.append(0.); flags.append(min(depth,local_cap))
            ix = weld[key];pointids.append(ix)
            normals[ix] += unit(value[3:6]); weights[ix] += 1
            masks[ix] += mask[row]*anchor[row]
            flags[ix] = min(flags[ix], min(depth,local_cap) if eligible[f] and anchor[row]>0 else 0.)
    points = np.array(points);pointids=np.array(pointids); directions=unit(np.array(normals))
    masks = np.array(masks)/np.array(weights)
    caps = np.minimum(flags,thickness_limits(points,directions,original[...,:3],depth))
    displacement = directions*(-masks*caps)[:,None]
    faces = pointids.reshape(-1,3)
    # Reduce only points participating in a folded/near-collapsed triangle.
    source_fine = fine[:,:3].reshape(-1,3,3)
    source_cross=np.cross(source_fine[:,1]-source_fine[:,0],source_fine[:,2]-source_fine[:,0])
    active = np.linalg.norm(source_cross,axis=1)>1e-10
    reductions=0
    for _ in range(20):
        p=(points+displacement)[faces]
        new_cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
        bad=active&(np.sum(new_cross*source_cross,axis=1)<.15*np.sum(source_cross*source_cross,axis=1))
        if not bad.any(): break
        ids=np.unique(faces[bad]);displacement[ids]*=.5;reductions+=len(ids)
    else: raise ValueError('Could not prevent folded triangles')
    fine[:,:3]=(points+displacement)[pointids]
    # Add geometric normal change to authored normals, retaining original hard
    # edges and any original smoothing. No shader relief is added by this tool.
    normal_keys, normal_ids = {}, []
    authored=unit(fine[:,3:6])
    for ix,n in zip(pointids,authored):
        key=(int(ix),*np.round(n,3))
        normal_ids.append(normal_keys.setdefault(key,len(normal_keys)))
    normal_ids=np.array(normal_ids)
    before=np.zeros((len(normal_keys),3));after=before.copy()
    p=fine[:,:3].reshape(-1,3,3)
    new_cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
    orientation=np.sign(np.sum(source_cross*authored.reshape(-1,3,3).mean(axis=1),axis=1))
    for c in range(3):
        np.add.at(before,normal_ids[c::3],source_cross*orientation[:,None])
        np.add.at(after,normal_ids[c::3],new_cross*orientation[:,None])
    fine[:,3:6]=unit(authored+unit(after)[normal_ids]-unit(before)[normal_ids])
    out=[];offset=0;original_offset=0
    for g in groups:
        count=sum(len(grid)//3 for grid in grids[original_offset:original_offset+len(g['corners'])])
        out.append(dict(material=g['material'],unused=g['unused'],corners=fine.reshape(-1,3,8)[offset:offset+count]))
        offset+=count
        original_offset+=len(g['corners'])
    assert np.isfinite(fine).all()
    lengths=np.linalg.norm(displacement,axis=1)
    metrics=dict(original_triangles=ntri,triangles=len(fine)//3,unchanged=False,
                 moved_vertices=int((lengths>1e-6).sum()),max_depth=float(lengths.max()),
                 mean_nonzero_depth=float(lengths[lengths>1e-6].mean()) if (lengths>1e-6).any() else 0.,
                 protected_edges=len(locked),fold_prevention_reductions=reductions,
                 thin_surface_limited_vertices=int((caps < depth*.99).sum()),
                 source_degenerate_triangles=int((np.linalg.norm(cross,axis=1)<1e-10).sum()))
    return out,metrics


def pack(groups):
    verts, indices, descriptors = [], [], []
    for g in groups:
        groupverts, groupids, unique = [], [], {}
        for v in g['corners'].reshape(-1,8).astype('<f4'):
            key=v.tobytes()
            if key not in unique: unique[key]=len(groupverts);groupverts.append(v)
            groupids.append(unique[key])
        start=len(verts)
        descriptors.append((g['material'],start,start+len(groupverts)-1,len(groupids),g['unused']))
        verts.extend(groupverts);indices.extend(groupids)
    if max(len(verts),len(indices),len(groups))>65535: raise ValueError('16-bit mesh overflow')
    blob=S.pack('<II4H',1,4,len(groups),len(indices),0x112,len(verts))
    blob+=b''.join(S.pack('<I4H',*d) for d in descriptors)
    blob+=np.array(indices,dtype='<u2').tobytes()+np.array(verts,dtype='<f4').tobytes()
    return blob,np.array(verts)


def make_ref(old, name, blob, vertices):
    _,_,ng,ni,_,nv=S.unpack_from('<II4H',blob)
    result=bytearray(old)
    S.pack_into('<II6H',result,0,60,crc(name),0,nv,0,ni,0,ng)
    low,high=vertices[:,:3].min(axis=0),vertices[:,:3].max(axis=0)
    # Conservatively retain original extent as well as the new mesh extent.
    bounds=np.frombuffer(old,'<f4',10,20)
    low=np.minimum(low,bounds[[1,3,5]]);high=np.maximum(high,bounds[[0,2,4]])
    center=(low+high)/2
    radius=np.linalg.norm(vertices[:,:3]-center,axis=1).max()
    radius=max(radius,float(np.linalg.norm(bounds[6:9]-center)+bounds[9]))
    S.pack_into('<10f',result,20,high[0],low[0],high[1],low[1],high[2],low[2],*center,radius)
    return bytes(result)


def build(depth=.30, previews=True):
    OUT.mkdir(parents=True,exist_ok=True)
    source=SOURCE.read_bytes();material_source=MAT.read_bytes()
    header,nodes=read_tree(source)
    original_leaves={p:n.blob for p,n in walk(nodes)}
    mats=materials()
    for m in mats.values():
        if m['eligible']:
            if m['image'] is None: raise ValueError('Missing texture: '+m['texture'])
            m['mask']=recess_map(m['image'])
    libraries={crc(p.split('/')[-2]):decode(n.blob) for p,n in walk(nodes) if p.endswith('/VMeshData')}
    transform=transforms(nodes)
    library=child(nodes[0],'VMeshLibrary')
    original_scene,scene,report=[],[],[]
    changed={};generated={}
    for path,node in list(walk(nodes)):
        if '/Level0/' not in path or not path.endswith('/VMeshRef'):continue
        part=path.split('/')[2]
        groups=extract_part(node.blob,libraries)
        hardpoints=np.array([np.frombuffer(n.blob,'<f4') for p,n in walk(nodes)
                            if '/'+part+'/' in p and '/Hardpoints/' in p and p.endswith('/Position')]).reshape(-1,3)
        refined,metrics=refine_part(groups,mats,depth,hardpoints)
        metrics['part']=part
        report.append(metrics)
        if not metrics['unchanged']:
            blob,vertices=pack(refined)
            name='proc_li_elite_medium_'+hashlib.sha256((part+hashlib.sha256(blob).hexdigest()).encode()).hexdigest()[:16]+'.vms'
            mesh=Node(name);mesh.children=[Node('VMeshData',blob)]
            library.children.append(mesh)
            node.blob=make_ref(node.blob,name,blob,vertices)
            changed[path]=node.blob
            generated[path]=refined
            metrics['mesh_vertices']=len(vertices)
        r,t=transform[part.lower()]
        for target,gs in ((original_scene,groups),(scene,refined)):
            for g in gs:
                # Hide the existing microscopic "none" hinge placeholders in previews only.
                if mats[g['material']]['name'].lower()=='none':continue
                cs=g['corners'].copy()
                cs[...,:3]=cs[...,:3]@r.T+t
                cs[...,3:6]=cs[...,3:6]@r.T
                target.append(dict(material=g['material'],corners=cs))
    output=write_tree(header,nodes)
    final={p:b for p,_,b in leaves(output)[1]}
    for path,blob in original_leaves.items():
        if final[path] != changed.get(path,blob):raise ValueError('Unrelated leaf changed: '+path)
    h2,n2=read_tree(output)
    roundtrip={crc(p.split('/')[-2]):decode(n.blob) for p,n in walk(n2) if p.endswith('/VMeshData')}
    for path,node in walk(n2):
        if path.endswith('/VMeshRef'):extract_part(node.blob,roundtrip)
    # Compare the decoded generated streams with what was serialized, not just headers.
    for path in changed:
        decoded=extract_part(final[path],roundtrip)
        part=path.split('/')[2]
        source_groups=extract_part(original_leaves[path],libraries)
        if [g['material'] for g in decoded] != [g['material'] for g in source_groups]:raise ValueError('Material change')
        if sum(len(g['corners']) for g in decoded)!=next(x['triangles'] for x in report if x['part']==part):raise ValueError('Triangle count change')
        for expected,after in zip(generated[path],decoded):
            if not np.array_equal(after['corners'],expected['corners'].astype('<f4').astype(float)):
                raise ValueError('Generated attributes changed during serialization')
        vertices=np.concatenate([g['corners'].reshape(-1,8) for g in decoded])
        bound=np.frombuffer(final[path],'<f4',10,20)
        if (vertices[:,:3]<bound[[1,3,5]]-1e-5).any() or (vertices[:,:3]>bound[[0,2,4]]+1e-5).any():
            raise ValueError('New vertices outside reference bounds')
        if np.linalg.norm(vertices[:,:3]-bound[6:9],axis=1).max()>bound[9]+1e-5:
            raise ValueError('New vertices outside reference sphere')
        if not np.isfinite(vertices).all() or not np.allclose(np.linalg.norm(vertices[:,3:6],axis=1),1,atol=2e-5):
            raise ValueError('Non-finite geometry or non-unit normals')
    model=OUT/'DATA/SHIPS/LIBERTY/LI_ELITE/li_elite.cmp'
    model.parent.mkdir(parents=True,exist_ok=True);model.write_bytes(output)
    if SOURCE.read_bytes()!=source or MAT.read_bytes()!=material_source:raise ValueError('Source changed during run')
    totals=dict(original_triangles=sum(p['original_triangles'] for p in report),
                medium_triangles=sum(p['triangles'] for p in report),
                requested_max_depth=depth,actual_max_depth=max(p.get('max_depth',0) for p in report),
                source_sha256=hashlib.sha256(source).hexdigest(),material_sha256=hashlib.sha256(material_source).hexdigest(),
                output_sha256=hashlib.sha256(output).hexdigest(),modified_parts=len(changed),parts=report,
                limitations=['Texture luminance is an artistic depth estimate, not semantic reconstruction.',
                             'SUR and damage caps are unchanged; no in-game validation.',
                             'Ray thickness and face-fold checks are not a complete self-intersection test.',
                             'Previews show construct zero pose and simple lighting, not engine rendering.'])
    (OUT/'report.json').write_text(json.dumps(totals,indent=2)+'\n')
    if previews:
        from preview import write_previews
        write_previews(OUT,original_scene,scene,mats)
    print(json.dumps({k:v for k,v in totals.items() if k!='parts'},indent=2))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inspect',action='store_true')
    ap.add_argument('--no-previews',action='store_true')
    ap.add_argument('--depth',type=float,default=.30,help='Maximum inward depth in model units; default is intentionally exaggerated')
    args=ap.parse_args()
    if not math.isfinite(args.depth) or not 0<=args.depth<=.5:ap.error('depth must be 0..0.5')
    if args.inspect:inspect()
    else:build(args.depth,not args.no_previews)
