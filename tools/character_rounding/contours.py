"""Sparse, conforming Mesh0 contour edits; no whole-body subdivision."""
import argparse
from collections import defaultdict
import copy
import hashlib
import gzip
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools/hatcher_hair'))
from build import GAME, DataFolder, read_tree, write_tree, child, blob, arr, put, faces, triangles
from repair_panel_normals import leaves
from cuff_ends import rims
from policy import load_policy, excluded_name

OUT = ROOT / 'out/character_rounding/contours_2k'
OLD = ROOT / 'out/character_rounding/all_bodies'
SPECIAL = {
    'li_hatcher_body': ('out/hatcher_body_smooth/original', 'out/hatcher_body_smooth/report.json'),
    'rh_reichman_body': ('out/reichman_body_test/original', 'out/reichman_body_test/report.json'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def key(p):
    return tuple(np.asarray(p).round(6))


def unit(v):
    return v / max(np.linalg.norm(v), 1e-12)


def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def mesh_of(root):
    return child(child(root, 'MultiLevel'), 'Mesh0')


def save_json(path, data):
    path.write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))


def load_json(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def export(root, target):
    """Reuse verified existing texture exports; never duplicate texture payloads."""
    mesh=mesh_of(root);geo=child(mesh,'Geometry')
    data={name:arr(geo,field,typ,width).tolist() for name,field,typ,width in
          [('points','Points','<f4',3),('normals','Vertex_normals','<f4',3),('uv','UV0','<f4',2)]}
    data['point_indices']=arr(geo,'Point_indices','<u4').ravel().tolist()
    data['uv_indices']=arr(geo,'UV0_indices','<u4').ravel().tolist()
    records,groups,_=as_records(root)
    data['skin']=[r['skin'] for r in records]
    data['bones']={str(int(arr(part,'Index','<u4')[0,0])):blob(part,'Object name').rstrip(b'\0').decode()
                   for part in child(root,'Cmpnd').children if part.children and any(c.name=='Index' for c in part.children)}
    data['groups']=[]
    for group in groups:
        name=blob(group,'Material_name').rstrip(b'\0').decode()
        mat=next(m for m in child(root,'Material library').children if m.name.lower()==name.lower())
        tex=next((c.blob.rstrip(b'\0').decode() for c in mat.children if c.name=='Dt_name'),None)
        texpath=OLD/target.parent.name/(digest(tex.encode())[:12]+'.png') if tex else None
        assert texpath is None or texpath.exists(), 'Missing shared texture export: '+str(texpath)
        data['groups'].append(dict(name=name,texture=str(texpath) if texpath else None,faces=triangles(group)))
    save_json(target,data)
    return data


def original(name):
    rel = 'CHARACTERS/BODIES/' + name + '.dfm'
    if name in SPECIAL:
        base, report = SPECIAL[name]
        path = ROOT / base / 'DATA' / rel
        wanted = json.loads((ROOT/report).read_text())['source_sha256']
    else:
        report = json.loads((OLD/name/'report.json').read_text())
        wanted = report['source_sha256']
        receipt = json.loads((OLD/'installed.json').read_text())
        path = Path(receipt['backup']) / 'DATA' / rel
        if not path.exists():
            path = GAME / 'DATA' / rel
    data = path.read_bytes()
    assert digest(data) == wanted, 'Unverified original: '+name
    return path, data


def as_records(root):
    mesh = mesh_of(root); geo = child(mesh, 'Geometry')
    p = arr(geo, 'Points', '<f4', 3); n = arr(geo, 'Vertex_normals', '<f4', 3)
    pi = arr(geo, 'Point_indices', '<u4').ravel()
    uv = arr(geo, 'UV0', '<f4', 2); ui = arr(geo, 'UV0_indices', '<u4').ravel()
    uv1 = arr(geo, 'UV1', '<f4', 2) if any(c.name=='UV1' for c in geo.children) else uv
    ui1 = arr(geo, 'UV1_indices', '<u4').ravel() if any(c.name=='UV1_indices' for c in geo.children) else ui
    first = arr(geo, 'Point_bone_first', '<u4').ravel(); count = arr(geo, 'Point_bone_count', '<u4').ravel()
    ids = arr(geo, 'Bone_id_chain', '<u4').ravel(); weights = arr(geo, 'Bone_weight_chain', '<f4').ravel()
    skin = [dict(zip(map(int, ids[f:f+c]), map(float, weights[f:f+c]))) for f,c in zip(first,count)]
    records = [dict(ref=p[i].astype(float), p=p[i].astype(float), n=n[i].astype(float),
                    uv=uv[j].astype(float), uv1=uv1[k].astype(float), skin=skin[i], original=True)
               for i,j,k in zip(pi,ui,ui1)]
    groups = [g for g in child(mesh,'Face_groups').children if g.children]
    fs = [[tuple(t) for t in triangles(g)] for g in groups]
    return records, groups, fs


def profile_from_ring(v):
    """Smooth a ring strictly inside its original polygon, preserving tilt."""
    v = np.unique(np.asarray(v).round(6), axis=0)
    center = v.mean(0); _,_,axes = np.linalg.svd(v-center)
    axis = axes[-1]
    if axis[1] < 0: axis = -axis
    u = axes[0]; w = np.cross(axis,u)
    xy = np.column_stack(((v-center)@u, (v-center)@w))
    # Convex hull removes inset duplicates, without fitting a larger circle.
    pts = sorted(set(map(tuple,xy)))
    def cross(a,b,c):
        x=np.array(b)-a; y=np.array(c)-a
        return x[0]*y[1]-x[1]*y[0]
    lo=[]; hi=[]
    for pt in pts:
        while len(lo)>1 and cross(lo[-2],lo[-1],pt)<=0: lo.pop()
        lo.append(pt)
    for pt in reversed(pts):
        while len(hi)>1 and cross(hi[-2],hi[-1],pt)<=0: hi.pop()
        hi.append(pt)
    xy=np.array(lo[:-1]+hi[:-1]); curve=xy.copy()
    for _ in range(4):
        nxt=np.roll(curve,-1,axis=0)
        curve=np.stack((.75*curve+.25*nxt,.25*curve+.75*nxt),axis=1).reshape(-1,2)
    angle=np.arctan2(curve[:,1],curve[:,0]); order=np.argsort(angle)
    return dict(center=center,axis=axis,u=u,w=w,polygon=xy,
                angle=angle[order],radius=np.linalg.norm(curve[order],axis=1))


def profile_delta(p, prof):
    delta=p-prof['center']; t=delta@prof['axis']
    # Local wrist/end treatment; the rest of the arm is native.
    if abs(p[0])<.20 or abs(t)>.105: return np.zeros(3)
    x=delta@prof['u']; y=delta@prof['w']; radius=np.hypot(x,y)
    if radius<.008 or radius>.10: return np.zeros(3)
    direction=np.array([x,y])/radius
    native=np.inf
    poly=prof['polygon']
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        edge=b-a; den=direction[0]*edge[1]-direction[1]*edge[0]
        if abs(den)<1e-10: continue
        dist=(a[0]*edge[1]-a[1]*edge[0])/den
        f=((direction*dist-a)@edge)/max(edge@edge,1e-12)
        if dist>0 and -1e-6<=f<=1+1e-6: native=min(native,dist)
    target=np.interp(np.arctan2(y,x),prof['angle'],prof['radius'],period=2*np.pi)
    ratio=np.clip(target/max(native,1e-9),.75,1) if np.isfinite(native) else 1
    fade=1-smooth(.025,.105,abs(t))
    change=(ratio-1)*fade*(x*prof['u']+y*prof['w'])
    if np.linalg.norm(change)>.006: change*=.006/np.linalg.norm(change)
    return change


def features(name, data, records):
    profiles=[]
    for item in rims(data):
        profiles.append(profile_from_ring(item[-1]))
    p=np.array(data['points'])
    if name=='li_hatcher_body':
        for side in (-1,1):
            ring=p[(p[:,0]*side>.20)&(p[:,1]>.085)&(p[:,1]<.142)]
            profiles.append(profile_from_ring(ring))
    belt=None
    if name=='li_hatcher_body':
        group=next(g for g in data['groups'] if g['name']=='hatcher_body_4')
        ix=np.unique(np.array(group['faces']).ravel())
        pts=np.array([records[i]['ref'] for i in ix]); uv=np.array([records[i]['uv'] for i in ix])
        front=pts[:,2]<-.095
        yfit=np.linalg.lstsq(np.column_stack((pts[front,0],uv[front,0],np.ones(front.sum()))),pts[front,1],rcond=None)[0]
        zfit=np.polyfit(pts[front,0],pts[front,2],2)
        belt=(set(map(int,ix)),yfit,zfit)
    return profiles,belt


def curved_feature(name,p):
    x,y,z=p
    if name=='li_hatcher_body' and .18<y<.535 and abs(x)<.22:
        return 'vest'
    if name=='rh_reichman_body' and .49<y<.615 and .14<abs(x)<.27:
        return 'epaulette'
    if name in ('li_male_elite_body','li_female_elite_body','li_tilton_body','li_tilton_body_alt') and .35<y<.53 and .17<abs(x)<.30:
        return 'armor_edge'
    return None


def edge_key(a,b):
    return tuple(sorted((key(a['ref']),key(b['ref']))))


def refine(name, records, fs, profiles, belt, limit):
    counts=defaultdict(int)
    wrist_cache={}
    def wrist(p):
        if abs(p[0])<.20: return np.zeros(3)
        coords=tuple(p)
        if coords in wrist_cache:return wrist_cache[coords]
        choices=[profile_delta(p,r) for r in profiles if np.sign(r['center'][0])==np.sign(p[0])]
        result=max(choices,key=lambda d: np.linalg.norm(d),default=np.zeros(3))
        wrist_cache[coords]=result
        return result
    for i,r in enumerate(records):
        r['support']={i}
        r['p']=r['ref']+wrist(r['ref'])
        if belt and i in belt[0]:
            _,yf,zf=belt; p=r['p']; blend=1-smooth(-.11,-.085,p[2])
            p[1]=p[1]*(1-blend)+blend*np.dot([p[0],r['uv'][0],1],yf)
            p[2]=p[2]*(1-blend)+blend*np.polyval(zf,p[0])
            r['belt']=True
    reserve=256 if name=='li_hatcher_body' else 400 if name=='rh_reichman_body' else 220 if name in ('li_male_elite_body','li_female_elite_body','li_tilton_body','li_tilton_body_alt') else 0
    for iteration in range(6 if reserve or belt else 3):
        if sum(map(len,fs))>=limit:break
        edges=defaultdict(list)
        for gi,group in enumerate(fs):
            for tri in group:
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    if edge_key(records[a],records[b])[0]!=edge_key(records[a],records[b])[1]:
                        edges[edge_key(records[a],records[b])].append((a,b))
        candidates=[]
        for ek,pairs in edges.items():
            a,b=pairs[0]; ra,rb=records[a],records[b]; ref=(ra['ref']+rb['ref'])/2
            linear=(ra['p']+rb['p'])/2; pos=ref+wrist(ref); tag='cuff'
            feature=curved_feature(name,ref)
            if np.linalg.norm(wrist(ref))<1e-10:
                if belt and ra.get('belt') and rb.get('belt'):
                    tag='belt';_,yf,zf=belt; uv=(ra['uv']+rb['uv'])/2
                    blend=1-smooth(-.11,-.085,ref[2]);pos=ref.copy()
                    pos[1]=ref[1]*(1-blend)+blend*np.dot([ref[0],uv[0],1],yf)
                    pos[2]=ref[2]*(1-blend)+blend*np.polyval(zf,ref[0])
                elif not feature: continue
                else:
                    tag=feature
                    # Shared normal field prevents UV seams from separating.
                    na=unit(sum((records[x]['n'] for pair in pairs for x in pair if key(records[x]['ref'])==ek[0]),np.zeros(3)))
                    nb=unit(sum((records[x]['n'] for pair in pairs for x in pair if key(records[x]['ref'])==ek[1]),np.zeros(3)))
                    pa,pb=(ra['p'],rb['p']) if key(ra['ref'])==ek[0] else (rb['p'],ra['p'])
                    if na@nb < .10: continue  # keep intentionally sharp edges
                    delta=-.5*(na*np.dot(linear-pa,na)+nb*np.dot(linear-pb,nb))
                    pos=linear+delta*.75
                    shift=pos-ref
                    if np.linalg.norm(shift)>.004: pos=ref+shift*(.004/np.linalg.norm(shift))
            if (iteration<3)!=(tag=='cuff'):continue
            error=np.linalg.norm(pos-linear); length=np.linalg.norm(ra['ref']-rb['ref'])
            if error<.00018 or length<.006: continue
            # Edges reaching protected lower body cannot be refined by an upper feature.
            if min(ra['ref'][1],rb['ref'][1])<-.10: continue
            priority=8 if tag=='cuff' else 7 if tag=='belt' else 6 if tag=='epaulette' else 3
            candidates.append((priority*error,ek,pos,tag,len(pairs)))
        selected={}; budget=limit-sum(map(len,fs))-(reserve if iteration<3 else 0)
        for _,ek,pos,tag,cost in sorted(candidates,key=lambda x:-x[0]):
            if cost>budget:continue
            selected[ek]=(pos,tag);budget-=cost;counts[tag]+=1
        if not selected:continue
        mids={}
        def midpoint(a,b):
            ik=tuple(sorted((a,b)))
            if ik in mids:return mids[ik]
            ra,rb=records[a],records[b];pos,tag=selected[edge_key(ra,rb)]
            weights=defaultdict(float)
            for record in (ra,rb):
                for bone,w in record['skin'].items():weights[bone]+=.5*w
            weights=dict(sorted(weights.items(),key=lambda x:-x[1])[:4]); total=sum(weights.values())
            weights={k:v/total for k,v in weights.items()}
            idx=len(records);records.append(dict(ref=(ra['ref']+rb['ref'])/2,p=pos.copy(),n=unit(ra['n']+rb['n']),support=ra['support']|rb['support'],
                uv=(ra['uv']+rb['uv'])/2,uv1=(ra['uv1']+rb['uv1'])/2,skin=weights,original=False,tag=tag,belt=bool(ra.get('belt') and rb.get('belt'))))
            mids[ik]=idx;return idx
        for gi,group in enumerate(fs):
            output=[]
            for tri in group:
                a,b,c=tri; es=[edge_key(records[x],records[y]) in selected for x,y in ((a,b),(b,c),(c,a))]
                n=sum(es)
                if n==0:output.append(tri);continue
                if n==3:
                    ab=midpoint(a,b);bc=midpoint(b,c);ca=midpoint(c,a)
                    output.extend(((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))
                elif n==1:
                    k=es.index(True);a,b,c=tri[k:]+tri[:k];m=midpoint(a,b)
                    output.extend(((a,m,c),(m,b,c)))
                else:
                    k=(es.index(False)+1)%3;a,b,c=tri[k:]+tri[:k];ab=midpoint(a,b);bc=midpoint(b,c)
                    output.extend(((ab,b,bc),(a,ab,c),(ab,bc,c)))
            fs[gi]=output
    # Thin nested cuff lips can fold under an otherwise valid radial correction.
    # Reduce only those local displacements, consistently on every UV seam copy.
    constrained=set()
    allfaces=np.array([t for g in fs for t in g])
    reference=np.array([r['ref'] for r in records])
    lower_bound=reference.min(0);upper_bound=reference.max(0)
    for r in records:r['p']=np.clip(r['p'],lower_bound,upper_bound)
    refnormal=np.cross(reference[allfaces[:,1]]-reference[allfaces[:,0]],reference[allfaces[:,2]]-reference[allfaces[:,0]])
    for _ in range(18):
        p=np.array([r['p'] for r in records])
        normal=np.cross(p[allfaces[:,1]]-p[allfaces[:,0]],p[allfaces[:,2]]-p[allfaces[:,0]])
        bad=(np.einsum('ij,ij->i',refnormal,normal)<=0)&(np.linalg.norm(refnormal,axis=1)>1e-12)
        if not bad.any():break
        keys={key(records[i]['ref']) for i in allfaces[bad].ravel()}
        for i,r in enumerate(records):
            if key(r['ref']) in keys:
                r['p']=r['ref']+(r['p']-r['ref'])*.5;constrained.add(i)
    else:raise ValueError('Cannot preserve local face orientation')
    counts['orientation_limited_vertices']=len(constrained)
    # Retain the artist's normal field and its hard boundaries. Interpolating
    # that field at added samples avoids triangulation-dependent cuff shading.
    # Closed wrist caps need a distinct normal from the cylindrical wall:
    # interpolating opposing wall normals across a cap creates bright spikes.
    normal_splits={}
    orient=[]
    for tri in allfaces:
        p=np.array([records[i]['ref'] for i in tri]);n0=np.cross(p[1]-p[0],p[2]-p[0])
        orient.append(n0@sum((records[i]['n'] for i in tri),np.zeros(3)))
    handed=1 if np.median(orient)>=0 else -1
    for gi,group in enumerate(fs):
        for fi,tri in enumerate(group):
            if not any(not records[i]['original'] or np.linalg.norm(records[i]['p']-records[i]['ref'])>1e-10 for i in tri):continue
            refs=np.array([records[i]['ref'] for i in tri]);face=unit(np.cross(refs[1]-refs[0],refs[2]-refs[0]))
            parent_ids=set().union(*(records[i]['support'] for i in tri))
            parent=np.array([records[i]['ref'] for i in parent_ids])
            for profile in profiles:
                if np.sign(refs[:,0].mean())!=np.sign(profile['center'][0]):continue
                offset=parent-profile['center'];along=offset@profile['axis']
                radial=np.linalg.norm(offset-np.outer(along,profile['axis']),axis=1)
                planar=max(abs(along))<.018 and abs(face@profile['axis'])>.86
                conical=(sum(abs(along)<.018)>=2 and max(abs(along))<.13 and
                         radial.min()<radial.max()*.55 and abs(face@profile['axis'])>.28)
                if not (planar or conical):continue
                normal=face*handed
                output=[]
                for i in tri:
                    split=(i,tuple(normal.round(6)))
                    if split not in normal_splits:
                        r=dict(records[i]);r['n']=normal.copy();normal_splits[split]=len(records);records.append(r)
                    output.append(normal_splits[split])
                fs[gi][fi]=tuple(output);break
    counts['cap_normal_splits']=len(normal_splits)
    return dict(counts)


def validate_local(records, fs, original_fs, baseline):
    data=baseline; source_p=np.array(data['points'])[np.array(data['point_indices'])]
    output_p=np.array([r['p'] for r in records]); unchanged_lower=0; flipped=0; degenerates=0
    for i,p in enumerate(source_p):
        if p[1]<-.10:
            assert np.array_equal(output_p[i],p), 'Lower-body point changed'
    for group,oldgroup in zip(fs,original_fs):
        parents={frozenset(t):t for t in oldgroup}
        for tri in group:
            support=frozenset().union(*(records[i].get('support',{i}) for i in tri))
            assert support in parents,'Triangle crosses an original surface boundary'
            parent=parents[support];old=source_p[list(parent)];p=output_p[list(tri)]
            n0=np.cross(old[1]-old[0],old[2]-old[0]);n1=np.cross(p[1]-p[0],p[2]-p[0])
            degenerates+=int(np.linalg.norm(n1)<1e-12)
            bad=n0@n1<=0 and np.linalg.norm(n0)>1e-12
            flipped+=int(bad)
            if np.max(old[:,1])<-.10:
                assert tri==parent, 'Lower-body triangle subdivided'
                unchanged_lower+=1
    assert not flipped, f'{flipped} flipped triangles'
    original_deg=sum(np.linalg.norm(np.cross(source_p[t[1]]-source_p[t[0]],source_p[t[2]]-source_p[t[0]]))<1e-12 for g in original_fs for t in g)
    assert degenerates<=original_deg, 'New degenerate triangles'
    return dict(flipped_triangles=flipped,degenerate_triangles=int(degenerates),lower_triangles_unchanged=unchanged_lower)


def write_mesh(mesh, records, groups, fs):
    geo=child(mesh,'Geometry'); identity=np.arange(len(records),dtype='<u4')
    for field,attr,typ in [('Points','p','<f4'),('Vertex_normals','n','<f4'),('UV0','uv','<f4')]:
        put(geo,field,np.array([r[attr] for r in records],dtype=typ).tobytes())
    for field in ('Point_indices','UV0_indices'):put(geo,field,identity.tobytes())
    if any(n.name=='UV1' for n in geo.children):
        put(geo,'UV1',np.array([r['uv1'] for r in records],dtype='<f4').tobytes());put(geo,'UV1_indices',identity.tobytes())
    first=[];count=[];ids=[];weights=[]
    for r in records:
        first.append(len(ids));count.append(len(r['skin']));ids.extend(r['skin']);weights.extend(r['skin'].values())
    for field,values,typ in [('Point_bone_first',first,'<u4'),('Point_bone_count',count,'<u4'),('Bone_id_chain',ids,'<u4'),('Bone_weight_chain',weights,'<f4')]:
        put(geo,field,np.asarray(values,dtype=typ).tobytes())
    for group,tris in zip(groups,fs):faces(group,tris)


def build(name):
    policy=load_policy();assert not excluded_name(name,policy)
    path,source=original(name); rel='CHARACTERS/BODIES/'+name+'.dfm'
    live=(GAME/'DATA'/rel).read_bytes(); old_report=json.loads((OLD/name/'report.json').read_text())
    allowed={old_report['output_sha256']}
    own_report=OUT/name/'report.json'
    if own_report.exists():allowed.add(json.loads(own_report.read_text())['output_sha256'])
    installed=OUT/'installed.json'
    if installed.exists():
        allowed.update(r['after_sha256'] for r in json.loads(installed.read_text())['files'] if r['name']==name)
    assert digest(live) in allowed,'Live file independently modified: '+name
    # Source supplies Mesh0 only. Preserve current LODs and all non-mesh payloads.
    header,roots=read_tree(live);root=roots[0];src=read_tree(source)[1][0]
    baseline=copy.deepcopy(root); ml=child(baseline,'MultiLevel')
    ml.children=[copy.deepcopy(mesh_of(src)) if m.name=='Mesh0' else m for m in ml.children]
    root=copy.deepcopy(baseline);mesh=mesh_of(root)
    folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
    data=export(baseline,folder/'before.json.gz')
    records,groups,fs=as_records(root);original_fs=copy.deepcopy(fs);count=sum(map(len,fs))
    assert count<=policy['max_mesh0_triangles'], name+' needs native geometry below budget'
    technical=old_report['category'] in ('technical','rigid_robot')
    profiles,belt=([],None) if technical else features(name,data,records)
    added=refine(name,records,fs,profiles,belt,policy['max_mesh0_triangles']) if not technical else {}
    checks=validate_local(records,fs,original_fs,data)
    geometry_changed=fs!=original_fs or any(np.linalg.norm(r['p']-r['ref'])>1e-10 for r in records)
    if geometry_changed:write_mesh(mesh,records,groups,fs)
    output=write_tree(header,[root]); baseline_raw=write_tree(header,[baseline])
    # Rebuild the full DFM in memory at installation; store only changed geometry.
    patch=write_tree(header,[mesh])
    (folder/'mesh0.utf.gz').write_bytes(gzip.compress(patch,mtime=0))
    previous=write_tree(header,[mesh_of(read_tree(live)[1][0])])
    if patch==previous:output=live  # Preserve original UTF layout for untouched technical assets.
    (folder/'previous_mesh0.utf.gz').write_bytes(gzip.compress(previous,mtime=0))
    export(root,folder/'after.json.gz')
    old={p:v for p,_,v in leaves(live)[1]};new={p:v for p,_,v in leaves(output)[1]}
    assert all('/MultiLevel/Mesh0/' in p for p in set(old)|set(new) if old.get(p)!=new.get(p))
    lower=sum(all(data['points'][data['point_indices'][i]][1]<-.10 for i in t) for g in original_fs for t in g)
    report=dict(algorithm_revision=4,name=name,source=str(path),source_sha256=digest(source),baseline_sha256=digest(baseline_raw),
        previous_sha256=digest(live),output_sha256=digest(output),patch_sha256=digest(patch),triangles_before=count,triangles_after=sum(map(len,fs)),
        previous_triangles=sum(len(triangles(g)) for g in child(mesh_of(read_tree(live)[1][0]),'Face_groups').children if g.children),points=len(arr(child(mesh,'Geometry'),'Points','<f4',3)),profiles=len(profiles),refined_edges=added,
        lower_body_triangles=lower,belt_adjusted=bool(belt),only_mesh0=True,game_animation_validated=False,checks=checks)
    (folder/'report.json').write_text(json.dumps(report,indent=2))
    print(name,count,'->',report['triangles_after'],added,flush=True)
    return report


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--name',action='append');ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    inventory=json.loads((OLD/'inventory.json').read_text()); reports=[]
    for r in inventory:
        if excluded_name(r['name']) or (args.name and r['name'] not in args.name):continue
        if args.resume and (OUT/r['name']/'report.json').exists() and json.loads((OUT/r['name']/'report.json').read_text()).get('algorithm_revision')==4:continue
        reports.append(build(r['name']))
    (OUT/'inventory.json').write_text(json.dumps([json.loads(p.read_text()) for p in sorted(OUT.glob('*/report.json'))],indent=2))


if __name__=='__main__':main()
