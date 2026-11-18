"""Canonical RH pirate asset, part-owned wire and freshly salted UTF resources."""
import collections
import copy
import hashlib
import json
from pathlib import Path
import secrets
import struct as S
import numpy as np
from scipy.spatial import ConvexHull
import rh_concept_b_v2 as v

f=v.f
OUT=v.OUT.parents[2]/'rh_pir_elite'
SOURCE=v.OUT/'lod_refinement/rh_concept_b.cmp'
ASSETS=OUT/'assets'
EXPECTED='1b26620bce9697efd919096ba2f26d3fc7953f157fec7889d1924910fc2e9a32'


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,default=v.hp.serial,indent=2),encoding='utf8')


def key(p):return tuple(np.round(p,5))


def clean(lines):
    positions={};edges=set()
    for a,b in lines:
        a,b=np.asarray(a),np.asarray(b);ka,kb=key(a),key(b)
        if ka==kb:continue
        positions[ka]=a;positions[kb]=b;edges.add(tuple(sorted((ka,kb))))
    while True:
        adj=collections.defaultdict(set)
        for a,b in edges:adj[a].add(b);adj[b].add(a)
        found=False
        for p,others in adj.items():
            if len(others)!=2:continue
            a,b=sorted(others);u=positions[a]-positions[p];w=positions[b]-positions[p]
            if u@w/np.linalg.norm(u)/np.linalg.norm(w)>-.99995:continue
            edges.remove(tuple(sorted((a,p))));edges.remove(tuple(sorted((b,p))))
            edges.add(tuple(sorted((a,b))));found=True;break
        if not found:break
    return [[positions[a],positions[b]] for a,b in sorted(edges)]


def contours():
    pieces=json.loads((v.OUT/'wire_pieces.json').read_text())
    shift=np.array(json.loads((v.OUT/'build.json').read_text())['center_shift_native'])
    drop=json.loads((v.OUT.parent/'revision_07/checks.json').read_text())['tail_translation'][1]
    lines={name:[] for name in pieces};owner='Root'
    def line(a,b,part=None):lines[part or owner].append([np.array(a),np.array(b)])
    def loop(ps,part=None):
        for a,b in zip(ps,np.roll(ps,-1,axis=0)):line(a,b,part)
    # Preserve the sparse body outline and add the two requested volume seams.
    body=np.concatenate([np.array(g['corners'])[...,:3] for g in pieces['Root'][:3]])
    lo,hi=body[...,2].min(),body[...,2].max()
    zs=[lo+.00001,*(np.array([-5.30,-4.45,-3.20,-2.10155,-.1,2.135,4.627])+shift[2]),hi-.00001]
    rings=[]
    for z in zs:
        points=[]
        for t in body:
            for a,b in zip(t,np.roll(t,-1,axis=0)):
                if abs(a[2]-b[2])<1e-9:continue
                r=(z-a[2])/(b[2]-a[2])
                if 0<=r<=1:points.append(a+(b-a)*r)
        p=np.array(points);x0,y0=p[:,:2].min(0);x1,y1=p[:,:2].max(0)
        bottom=p[p[:,1]<y0+.0001];top=p[p[:,1]>y1-.0001]
        left=p[p[:,0]<x0+.0001];right=p[p[:,0]>x1-.0001]
        rings.append(np.array([[bottom[:,0].min(),y0,z],[bottom[:,0].max(),y0,z],
            [x1,right[:,1].min(),z],[x1,right[:,1].max(),z],
            [top[:,0].max(),y1,z],[top[:,0].min(),y1,z],
            [x0,left[:,1].max(),z],[x0,left[:,1].min(),z]]))
    for i in (0,4,5,len(rings)-1):loop(rings[i])
    for a,b in zip(rings,rings[1:]):
        for p,q in zip(a,b):line(p,q)
    separators=[rings[4].tolist(),rings[5].tolist()]
    # Physical cut planes determine ownership, not a single root-space drawing.
    poly=f.b.old.yz([[214,16],[148,16],[95,48],[95,124],[123,153],[207,153],
                    [207,133],[140,133],[116,112],[116,59],[154,36],[214,36]])
    poly[:,0]+=drop
    cuts=np.array([f.TAIL_CUT,f.TAIL_TOP])+shift[1]
    sides=[np.column_stack((np.full(len(poly),x),poly))+shift for x in (-1.32,1.32)]
    def frame_line(a,b):
        ts=[0.,1.]
        if abs(b[1]-a[1])>1e-8:
            ts+=list((cuts-a[1])/(b[1]-a[1]))
        ts=sorted(set(t for t in ts if 0<=t<=1))
        for low,high in zip(ts,ts[1:]):
            p=a+(b-a)*low;q=a+(b-a)*high;y=(p[1]+q[1])*.5
            part='Rh_tail_lod1' if cuts[0]<y<cuts[1] else 'Root'
            line(p,q,part)
    for side in sides:
        for a,b in zip(side,np.roll(side,-1,axis=0)):frame_line(a,b)
    for i in (0,1,2,3,4,5):frame_line(sides[0][i],sides[1][i])
    for cut in cuts:
        cross=[]
        for a,b in zip(sides[0],np.roll(sides[0],-1,axis=0)):
            if min(a[1],b[1])<cut<max(a[1],b[1]):cross.append(a+(b-a)*((cut-a[1])/(b[1]-a[1])))
        assert len(cross)==2
        a,b=sorted(cross,key=lambda p:p[2]);c=b.copy();c[0]=1.32;d=a.copy();d[0]=1.32
        loop(np.array([a,b,c,d]),'Rh_tail_lod1')
    center=f.b.old.point(0,[175,86])+shift+[0,drop,0]
    angles=(np.arange(20)+.5)*2*np.pi/20
    yz=center[1:]+2.01*np.column_stack((np.cos(angles),np.sin(angles)))
    rims=[np.column_stack((np.full(20,x),yz)) for x in (-1.04,1.04)]
    for rim in rims:loop(rim)
    for i in (0,5,10,15):line(rims[0][i],rims[1][i])
    for owner,gs in pieces.items():
        p=np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in gs])
        if '_engine_' in owner.lower():
            low,high=p.min(0),p.max(0);c=(low+high)*.5;angles=np.arange(10)*2*np.pi/10
            xy=c[:2]+(high[:2]-low[:2])*.5*np.column_stack((np.cos(angles),np.sin(angles)))
            ends=[np.column_stack((xy,np.full(10,z))) for z in (low[2],high[2])]
            for ring in ends:loop(ring)
            for i in (0,2,5,7):line(ends[0][i],ends[1][i])
        elif '_wing_' in owner.lower():
            q=np.unique(np.round(p[:,[0,2]],5),axis=0);q=q[ConvexHull(q).vertices]
            loop(np.column_stack((q[:,0],np.full(len(q),p[:,1].mean()),q[:,1])))
    return {name:clean(gs) for name,gs in lines.items()},separators


def wire(nodes):
    lines,separators=contours();tr,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    names=f.component_map(nodes);library=f.mesh.child(nodes[0],'VMeshLibrary')
    # Remove the former private wire library only; all rendered meshes remain.
    library.children=[n for n in library.children if not n.name.startswith('rh_b_v2_unfolded_outer_wire_')]
    near=f.local_geometry(nodes);report={}
    for file,name in names.items():
        part=f.mesh.child(nodes[0],file);part.children=[n for n in part.children if n.name.lower()!='vmeshwire']
        r,t=tr[file.lower()];world=lines.get(name,[])
        if not world:
            # Explicit empty wire prevents HUD's full IMesh triangle fallback.
            ml=f.mesh.child(part,'MultiLevel');ref=f.mesh.child(f.mesh.child(f.mesh.child(ml,'Level0'),'VMeshPart'),'VMeshRef')
            crc=S.unpack_from('<I',ref.blob,4)[0];payload=S.pack('<II4H',16,crc,0,0,0,0)
            local=[]
        else:
            local=(np.array(world)-t)@r
            ps={key(q):q for q in local.reshape(-1,3)};keys=sorted(ps);lookup={k:i for i,k in enumerate(keys)}
            # One valid nondegenerate native triangle backs the wire-only vertex pool.
            g=near[file][0];blob,verts=f.mesh.pack([dict(g,unused=204,corners=g['corners'][:1])]);base=len(verts)
            extra=np.zeros((len(keys),8),'<f4');extra[:,:3]=[ps[k] for k in keys];extra[:,4]=1
            raw=bytearray(blob);S.pack_into('<H',raw,14,base+len(keys));raw+=extra.tobytes()
            meshname='rh_pir_wire_'+name+'.vms';library.children.append(f.folder(meshname,f.mesh.Node('VMeshData',bytes(raw))))
            ids=[lookup[key(q)] for q in local.reshape(-1,3)]
            payload=S.pack('<II4H',16,f.mesh.crc(meshname),base,len(keys),len(ids),len(keys))+np.array(ids,'<u2').tobytes()
        part.children.append(f.folder('VMeshWire',f.mesh.Node('VWireData',payload)))
        report[name]=dict(local=local,unfolded=world,edges=len(world),empty=not bool(world))
    return report,separators


def salt_tree(nodes,salt,material_map=None):
    mapping={};lib=f.mesh.child(nodes[0],'VMeshLibrary')
    for i,node in enumerate(lib.children):
        old=node.name;new=f'rh_pir_vms_{i:02d}_{salt}.vms';mapping[old]=new;node.name=new
        if material_map:
            leaf=f.mesh.child(node,'VMeshData');raw=bytearray(leaf.blob);count=S.unpack_from('<H',raw,8)[0]
            for j in range(count):
                oldmat=S.unpack_from('<I',raw,16+12*j)[0]
                if oldmat in material_map:S.pack_into('<I',raw,16+12*j,material_map[oldmat])
            leaf.blob=bytes(raw)
    crcmap={f.mesh.crc(a):f.mesh.crc(b) for a,b in mapping.items()}
    for path,node in f.mesh.walk(nodes):
        if path.lower().endswith(('/vmeshref','/vwiredata')):
            raw=bytearray(node.blob);old=S.unpack_from('<I',raw,4)[0];S.pack_into('<I',raw,4,crcmap[old]);node.blob=bytes(raw)
    cmpnd=next((n for n in nodes[0].children if n.name=='Cmpnd'),None)
    if cmpnd:
        for entry in cmpnd.children:
            if entry.name=='Cons':continue
            ref=f.mesh.child(entry,'File name');old=f.mesh.string(ref.blob);name=f.mesh.string(f.mesh.child(entry,'Object name').blob)
            new=f'rhp_{name}_{salt}.3db';assert len(new)<64
            f.mesh.child(nodes[0],old).name=new;ref.blob=new.encode()+b'\0';mapping[old]=new
    return mapping


def named_geometry(nodes,level):
    names=f.component_map(nodes);return {names[k]:gs for k,gs in f.local_geometry(nodes,level).items()}


def main():
    OUT.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(exist_ok=True)
    assert f.digest(SOURCE)==EXPECTED
    header,nodes=f.mesh.read_tree(SOURCE.read_bytes());before=copy.deepcopy(nodes)
    report,separators=wire(nodes);salt=secrets.token_hex(6)
    # Only our private atlas is renamed. The user's shared MAT is read-only.
    mh,mn=f.mesh.read_tree((v.OUT/'lod_refinement/rh_concept_b_lods.mat').read_bytes())
    material=f.mesh.child(mn[0],'Material library').children[0];oldmat=material.name
    texture=f.mesh.child(mn[0],'Texture library').children[0];oldtex=texture.name
    material.name='rh_pir_elite_lod_'+salt;texture.name=material.name+'.tga'
    f.mesh.child(material,'Dt_name').blob=texture.name.encode()+b'\0'
    matmap={f.mesh.crc(oldmat):f.mesh.crc(material.name)}
    (ASSETS/'rh_pir_elite_lods.mat').write_bytes(f.mesh.write_tree(mh,mn))
    mapping=salt_tree(nodes,salt,matmap)
    target=ASSETS/'rh_pir_elite.cmp';target.write_bytes(f.mesh.write_tree(header,nodes))
    (ASSETS/'rh_pir_elite.sur').write_bytes((v.OUT/'rh_concept_b.sur').read_bytes())
    damages=[]
    for file in sorted((v.OUT/'damage').glob('rh_b_dmg_*.3db')):
        name=file.stem.replace('rh_b_','rh_pir_elite_');dh,dn=f.mesh.read_tree(file.read_bytes())
        dm=salt_tree(dn,salt+'_'+str(len(damages)))
        (ASSETS/(name+'.3db')).write_bytes(f.mesh.write_tree(dh,dn))
        (ASSETS/(name+'.sur')).write_bytes(file.with_suffix('.sur').read_bytes())
        damages.append(dict(source=file.name,target=name+'.3db',resources=dm))
    # The user wants caps only on the surviving ship, never on flying debris.
    for zone in ('port_wing','starboard_wing','port_engine','starboard_engine','tail'):
        for suffix in ('.3db','.sur'):
            obsolete=ASSETS/('rh_pir_elite_break_'+zone+suffix)
            assert obsolete.resolve().parent==ASSETS.resolve()
            obsolete.unlink(missing_ok=True)
    after=f.mesh.read_tree(target.read_bytes())[1]
    hp_records=lambda ns:[{k:x for k,x in h.items() if k!='file'} for h in v.hp.hardpoint_records(ns)]
    assert hp_records(before)==hp_records(after)
    for tag in ('Animation','Cmpnd'):
        old=f.mesh.child(before[0],tag);new=f.mesh.child(after[0],tag)
        if tag=='Cmpnd':old=f.mesh.child(old,'Cons');new=f.mesh.child(new,'Cons')
        assert [(p,n.blob) for p,n in f.mesh.walk([old])]==[(p,n.blob) for p,n in f.mesh.walk([new])]
    counts=[]
    for level in range(3):
        a=named_geometry(before,level);b=named_geometry(after,level);count=0
        for part,gs in a.items():
            assert len(gs)==len(b[part])
            for old,new in zip(gs,b[part]):
                assert matmap.get(old['material'],old['material'])==new['material']
                assert np.array_equal(old['corners'],new['corners']);count+=len(new['corners'])
        counts.append(count)
    libs={f.mesh.crc(p.split('/')[-2]):f.audit.decode(n.blob) for p,n in f.mesh.walk(after) if p.lower().endswith('/vmeshdata')}
    newnames=f.component_map(after);decoded={}
    for file,name in newnames.items():
        data=f.mesh.child(f.mesh.child(f.mesh.child(after[0],file),'VMeshWire'),'VWireData').blob
        _,crc,bias,nv,ni,total=S.unpack_from('<II4H',data);verts=libs[crc][0];ids=np.frombuffer(data,'<u2',offset=16)
        assert ni==len(ids) and ni%2==0 and nv==len(set(ids)) and nv==total
        if ni:assert ids.max()+bias<len(verts) and np.allclose(verts[bias+ids,:3].reshape(-1,2,3),report[name]['local'],atol=2e-5)
        decoded[name]=dict(edges=ni//2,vertices=nv)
    assert len(decoded)==11 and sum(x['edges'] for x in decoded.values())*2<16000
    for name in v.ZONES:assert decoded[name]['edges']>0
    # Every detachable contour has its own wire; none is duplicated in Root.
    rootkeys={tuple(sorted((key(a),key(b)))) for a,b in report['Root']['unfolded']}
    for name in v.ZONES:
        assert not rootkeys&{tuple(sorted((key(a),key(b)))) for a,b in report[name]['unfolded']}
    dump('wire.json',dict(parts=report,separators=separators,source_cmp=str(SOURCE),source_sha256=EXPECTED,
        pose='native local coordinates; HUD snapshots current component pose; unfolded reference supplied'))
    files={p.name:dict(bytes=p.stat().st_size,sha256=f.digest(p)) for p in ASSETS.iterdir() if p.is_file()}
    dump('build.json',dict(salt=salt,resources=mapping,atlas={oldmat:material.name,oldtex:texture.name},damage=damages,files=files,
        cmp_sha256=f.digest(target),lod_triangles=counts,wire=decoded,hardpoints=79,
        geometry_and_uv_unchanged=True,rig_and_hp_unchanged=True,sur_unchanged=True,external_materials=True))
    print('RH PIR ELITE READY',json.dumps(dict(salt=salt,wire=decoded,triangles=counts)),flush=True)


if __name__=='__main__':main()
