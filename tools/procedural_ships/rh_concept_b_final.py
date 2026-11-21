"""RH B final asset assembly. Offline, source/game assets are read-only.

Accepted revision 08 is the geometric source; no silent regeneration of that model.
Native pirate CMP supplies conventions, scripts, damage archetypes and materials.
"""
import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct as S
import sys

import numpy as np
import rh_concept_b_sockets as b

mesh,audit,base,native=b.mesh,b.audit,b.base,b.native
OUT=b.OUT.parent/'final_v1'
DEST=OUT/'rh_concept_b.cmp'
SHARED_MAT=b.prior.LIBRARY
LOD_MAT=OUT/'rh_concept_b_lods.mat'


def material_files():
    return [audit.DATA/p for p in b.base.ROW['materials']]+([LOD_MAT] if LOD_MAT.exists() else [])+[DEST]


IDENTITY=np.eye(3)
FOLD=np.deg2rad(62.)
WING_PIVOT=np.array([3.05,-.50,7.80])
TAIL_CUT=.70
TAIL_TOP=3.90


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def merge(gs):return native.previous.merge(gs)
def textnode(name,value):return mesh.Node(name,value.encode()+b'\0')
def folder(name,*children):
    n=mesh.Node(name);n.children=list(children);return n


def component_map(nodes):
    return {mesh.string(mesh.child(n,'File name').blob):mesh.string(mesh.child(n,'Object name').blob)
            for n in mesh.child(nodes[0],'Cmpnd').children if n.name!='Cons'}


def local_geometry(nodes,level=0):
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    result={}
    for file in component_map(nodes):
        part=mesh.child(nodes[0],file);ml=mesh.child(part,'MultiLevel')
        levels=[n for n in ml.children if n.name.lower().startswith('level')]
        lv=min(level,len(levels)-1)
        ref=mesh.child(mesh.child(mesh.child(ml,'Level'+str(lv)),'VMeshPart'),'VMeshRef')
        result[file]=audit.extract(ref.blob,libs)
    return result


def hp_world(nodes):
    tr,_=audit.transforms(nodes);result={}
    for path,node in mesh.walk(nodes):
        if '/hardpoints/' not in path.lower() or not path.lower().endswith('/position'):continue
        file=path.split('/')[2];hp=path.split('/')[-2];r,t=tr[file.lower()]
        orient=next(n.blob for p,n in mesh.walk(nodes) if p==path.rsplit('/',1)[0]+'/Orientation')
        result[hp.lower()]=dict(name=hp,file=file,position=(r@np.frombuffer(node.blob,'<f4')+t).tolist(),
                                orientation=(r@np.frombuffer(orient,'<f4').reshape(3,3)).tolist())
    return result


def clip_groups(groups,axis,bound,greater):
    out=[]
    for g in groups:
        tris=[]
        for tri in g['corners']:
            poly=[]
            for a,c in zip(tri,np.roll(tri,-1,axis=0)):
                ia=a[axis]>=bound-1e-8 if greater else a[axis]<=bound+1e-8
                ic=c[axis]>=bound-1e-8 if greater else c[axis]<=bound+1e-8
                if ia:poly.append(a)
                if ia!=ic:poly.append(a+(c-a)*((bound-a[axis])/(c[axis]-a[axis])))
            for i in range(1,len(poly)-1):
                q=np.array([poly[0],poly[i],poly[i+1]])
                if np.linalg.norm(np.cross(q[1,:3]-q[0,:3],q[2,:3]-q[0,:3]))>1e-9:
                    q[:,3:6]=mesh.unit(q[:,3:6]);tris.append(q)
        if tris:out.append(dict(g,corners=np.array(tris)))
    return out


def triangle_key(t):return tuple(sorted(tuple(v.round(4)) for v in t[:,:3]))


def split_tail(world):
    tail=next(k for k in world if '_tail_' in k.lower())
    body=next(k for k in world if k.lower().startswith('rh_elite_'))
    b.SOURCE,_,_=audit.load(base.ROW)
    drum=b.Builder();b.drum(drum)
    dy=json.loads((b.prev.OUT/'checks.json').read_text())['tail_translation'][1]
    generated=b.prev.shifted(drum.groups(),[0,dy,0])
    drum_count=sum(len(g['corners']) for g in generated)
    support=b.Builder();support.part='tail'
    for contour in ([[168,35],[180,35],[179,52],[171,52]],[[170,120],[181,120],[186,134],[165,134]],
                    [[111,81],[141,81],[141,90],[111,95]]):
        support.sharp_solid(b.old.yz(contour),-.33,.33)
    for side in (-1,1):
        support.sharp_solid(b.old.yz([[108,82],[146,82],[153,85],[151,90],[108,92]]),*sorted((side*1.17,side*1.32)))
    generated+=b.prev.shifted(support.groups(),[0,dy,0])
    keys=collections.Counter(triangle_key(t) for g in generated for t in g['corners'])
    moved=[];frame=[]
    for g in world[tail]:
        inside=[];outside=[]
        for t in g['corners']:
            key=triangle_key(t)
            if keys[key]:keys[key]-=1;inside.append(t)
            else:outside.append(t)
        if inside:moved.append(dict(g,corners=np.array(inside)))
        if outside:frame.append(dict(g,corners=np.array(outside)))
    assert sum(keys.values())==0, 'Accepted drum extraction must match every triangle'
    rear=clip_groups(clip_groups(frame,1,TAIL_CUT,True),1,TAIL_TOP,False)
    retained=clip_groups(frame,1,TAIL_CUT,False)+clip_groups(frame,1,TAIL_TOP,True)
    cuts=[]
    for height,retained_normal in ((TAIL_CUT,[0,1,0]),(TAIL_TOP,[0,-1,0])):
        edges=[]
        for g in rear:
            for tri in g['corners']:
                for a,c in zip(tri,np.roll(tri,-1,axis=0)):
                    if abs(a[1]-height)<1e-5 and abs(c[1]-height)<1e-5:edges.append((a[:3],c[:3]))
        counts=collections.Counter(tuple(sorted((tuple(a.round(5)),tuple(c.round(5))))) for a,c in edges)
        boundary=[e for e,n in counts.items() if n%2]
        while boundary:
            a,c=boundary.pop();loop=[a,c]
            while loop[-1]!=loop[0]:
                i=next(i for i,e in enumerate(boundary) if loop[-1] in e)
                e=boundary.pop(i);loop.append(e[1] if e[0]==loop[-1] else e[0])
            loop=np.array(loop[:-1]);cuts.append(dict(points=loop.tolist(),normal=retained_normal))
            for groups,normal in ((rear,-np.array(retained_normal)),(retained,retained_normal)):
                cap=b.Builder();cap.explicit(loop,b.DARK,b.prior.PLAIN,normal);groups.extend(cap.groups())
    world[body]=merge(world[body]+moved+retained);world[tail]=merge(rear)
    return dict(drum_triangles=drum_count,drum_and_support_triangles=sum(len(g['corners']) for g in moved),cut_y=TAIL_CUT,cut_top_y=TAIL_TOP,
                cut_loops=[c['points'] for c in cuts],cuts=cuts,tail=tail,body=body,tail_scope='rear upright only; upper and lower frame and drum stay on Root')


def set_rig(nodes):
    cons=mesh.child(mesh.child(nodes[0],'Cmpnd'),'Cons')
    rev=mesh.child(cons,'Rev');fixed=mesh.child(cons,'Fix');records=[]
    for at in range(0,len(rev.blob),208):
        raw=bytearray(rev.blob[at:at+208]);name=mesh.string(raw[64:128]);lower=name.lower()
        f=np.frombuffer(raw,'<f4',20,128)
        side=-1 if '_port_' in lower else 1
        if '_upperarm' in lower:
            # Slot is stationary. The concealed wing axis is inside its opening.
            fixed.blob+=raw[:128]+f[:3].astype('<f4').tobytes()+np.eye(3,dtype='<f4').tobytes()
            continue
        if '_wing_' in lower:
            raw[:64]=b'Root'.ljust(64,b'\0')
            f[:3]=WING_PIVOT*[side,1,1];f[3:6]=0;f[6:15]=IDENTITY.ravel()
            f[15:18]=[0,side,0];f[18:20]=[0,FOLD]
        if 'baydoor' in lower:
            side=-1 if '01' in lower else 1
            f[:3]=[side*.76,b.old.roof(b.old.CARGO_Z0)+.035,b.old.CARGO_Z0]
            f[3:6]=0;f[6:15]=IDENTITY.ravel()
        records.append(bytes(raw))
    rev.blob=b''.join(records)
    scripts=mesh.child(mesh.child(nodes[0],'Animation'),'Script')
    for script in scripts.children:
        keep=[]
        for joint in script.children:
            child=mesh.string(mesh.child(joint,'Child name').blob)
            if '_upperarm' in child.lower():continue
            if '_wing_' in child.lower():
                mesh.child(joint,'Parent name').blob=b'Root\0'
                kind=script.name.lower()
                if kind=='sc_launch extend':times=np.r_[0,5,np.linspace(5.0625,7,32)];phase=1-np.clip((times-5)/2,0,1)
                elif kind=='sc_force extend':times=np.array([0,1e17]);phase=np.array([0,1])
                elif kind=='sc_extend wing keep':times=np.array([0,2]);phase=np.ones(2)
                else:
                    duration=2 if kind=='sc_extend wing' else 1/30
                    times=np.linspace(0,duration,33);phase=times/duration
                vals=FOLD*phase*phase*(3-2*phase)
                channel=mesh.child(joint,'Channel')
                mesh.child(channel,'Header').blob=S.pack('<IfI',len(times),-1,1)
                mesh.child(channel,'Frames').blob=np.column_stack((times,vals)).astype('<f4').tobytes()
            joint.name='Joint map '+str(len(keep));keep.append(joint)
        script.children=keep


def place_hardpoints(nodes,before,split):
    tr,_=audit.transforms(nodes);names=component_map(nodes);byname={n.lower():f for f,n in names.items()}
    body=split['body'];tail=split['tail']
    def file_for(word):return next(f for f in names if word in f.lower())
    changes={}
    # Physical hull-facing mounts. Orientation and arc limits remain native unless
    # a new damage attachment explicitly uses the neutral identity basis.
    targets={
        'dpport_wing':(WING_PIVOT*[-1,1,1]).tolist(), 'dpstarboard_wing':WING_PIVOT.tolist(),
        'dpport_engine':[-1.8205,-.55,8.70], 'dpstarboard_engine':[1.8205,-.55,8.70],
        'dptail':[0,TAIL_CUT,12.0],
        'hpweapon05':[-.50,-1.15,-3.5565], 'hpweapon06':[.50,-1.15,-3.5565],
        'hptorpedo01':[0,-1.15,-2.40], 'hpmiscgun01':[0,-1.15,-4.20],
        'hpheadlight':[0,-.70,-5.60], 'hptractor_source':[0,-.70,-5.60],
        'hprunninglight01':[.75,.99,-2.05], 'hprunninglight02':[-.75,.99,-2.05],
        'hpbaydoor01':[0,2.75,3.625], 'hpbaydoor02':[0,4.20,3.625],
        'hpmount':[0,-2.30,3.0], 'hpshield01':[0,2.60,3.0],
        'hpcontrail03':[-2.45,1.98,5.05], 'hpcontrail04':[2.45,1.98,5.05],
        'hprunninglight03':[0,5.96,6.50], 'hprunninglight04':[0,-1.15,9.15],
        'hpcm01':[.65,-1.15,10.20], 'hpmine01':[-.65,-1.15,10.20],
        'hpthruster01':[-.55,1.05,12.56], 'hpthruster02':[.55,1.05,12.56],
        'hpturret01':[0,2.20,12.57], 'hpturret02':[0,5.96,9.70], 'hpturret03':[0,-1.15,9.20],
    }
    transfer={'hpcm01','hpmine01','hprunninglight03','hprunninglight04','hpturret02','hpturret03'}
    root_hp=mesh.child(mesh.child(nodes[0],body),'Hardpoints')
    for file in names:
        part=mesh.child(nodes[0],file)
        hp=next((n for n in part.children if n.name=='Hardpoints'),None)
        if not hp:continue
        for kind in hp.children:
            for h in list(kind.children):
                key=h.name.lower();info=before[key];target=np.array(targets.get(key,info['position']))
                if key=='dpbreak':continue
                owner=body if key in transfer else file
                r,t=tr[owner.lower()]
                mesh.child(h,'Position').blob=np.array(r.T@(target-t),'<f4').tobytes()
                orient=IDENTITY if key.startswith('dp') else np.array(info['orientation'])
                mesh.child(h,'Orientation').blob=np.array(r.T@orient,'<f4').tobytes()
                if owner!=file:
                    kind.children.remove(h);mesh.child(root_hp,kind.name).children.append(h)
                changes[key]=dict(file=owner,position=target.tolist(),moved=float(np.linalg.norm(target-info['position'])))
    # Active archetype declares this slot but the original CMP did not contain it.
    fixed=mesh.child(root_hp,'Fixed')
    if 'hphardware01' not in before:
        fixed.children.append(folder('HpHardware01',mesh.Node('Orientation',np.eye(3,dtype='<f4').tobytes()),
                                     mesh.Node('Position',np.array([0,0,0],'<f4').tobytes())))
    return changes


def fresh_ref(name,blob,vertices):
    # Exact component-local bounds; never retain old source bounds after relocation.
    nv=len(vertices);ng,ni=S.unpack_from('<HH',blob,8)
    low=vertices[:,:3].min(0);high=vertices[:,:3].max(0);center=(low+high)/2
    radius=float(np.linalg.norm(vertices[:,:3]-center,axis=1).max())
    return S.pack('<II6H10f',60,mesh.crc(name),0,nv,0,ni,0,ng,high[0],low[0],high[1],low[1],high[2],low[2],*center,radius)


def clean_feature_wire(blob,mesh_crc,angle=35):
    """LOD1 feature edges: weld UV splits, remove coplanar/front-back diagonals."""
    vertices,groups,indices=audit.decode(blob)
    points=vertices[:,:3];representative={}
    remap=[representative.setdefault(tuple(p.round(4)),i) for i,p in enumerate(points)]
    edges={};triangles=set();at=0
    for _,base_index,_,count,_ in groups:
        for tri in (indices[at:at+count]+base_index).reshape(-1,3):
            ids=tuple(remap[i] for i in tri);key=tuple(sorted(ids))
            if key in triangles:continue
            triangles.add(key);a,c,d=points[list(ids)];n=np.cross(c-a,d-a)
            if np.linalg.norm(n)<1e-8:continue
            n=mesh.unit(n)
            for u,v in zip(ids,ids[1:]+ids[:1]):edges.setdefault(tuple(sorted((u,v))),[]).append(n)
        at+=count
    threshold=math.cos(math.radians(angle))
    kept=[e for e,ns in edges.items() if len(ns)==1 or
          any(abs(float(a@c))<threshold for i,a in enumerate(ns) for c in ns[i+1:])]
    flat=[i for e in sorted(kept) for i in e]
    assert flat and len(flat)<65536 and max(flat)<len(points)
    return S.pack('<II4H',16,mesh_crc,0,len(set(flat)),len(flat),len(points))+np.array(flat,'<u2').tobytes()


def write_geometry(nodes,levels,min_cross_area=1e-8):
    lib=mesh.child(nodes[0],'VMeshLibrary');lib.children=[]
    for file in component_map(nodes):
        part=mesh.child(nodes[0],file);ml=mesh.child(part,'MultiLevel')
        ml.children=[mesh.Node('Switch2',np.array([0,180,550,10000],'<f4').tobytes())]
        for level,parts in enumerate(levels):
            groups=[]
            for g in merge(parts[file]):
                p=g['corners'][...,:3].astype('<f4').astype(float)
                keep=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>min_cross_area
                if keep.any():groups.append(dict(g,corners=g['corners'][keep]))
            blob,v=mesh.pack(groups)
            name='rh_b_final_'+hashlib.sha256((file+str(level)).encode()+blob).hexdigest()[:20]+'.vms'
            lib.children.append(folder(name,mesh.Node('VMeshData',blob)))
            ml.children.append(folder('Level'+str(level),folder('VMeshPart',mesh.Node('VMeshRef',fresh_ref(name,blob,v)))))
            if level==min(1,len(levels)-1):
                wire=next((n for n in part.children if n.name.lower()=='vmeshwire'),None)
                if wire:mesh.child(wire,'VWireData').blob=clean_feature_wire(blob,mesh.crc(name))


def export_lod0(nodes):
    single=copy.deepcopy(nodes)
    for file in component_map(single):
        ml=mesh.child(mesh.child(single[0],file),'MultiLevel')
        ml.children=[n for n in ml.children if n.name=='Switch2' or n.name=='Level0']
    native.OUT=OUT;native.DEST=DEST;native.export(single)
    source=mesh.read_tree(base.SOURCE.read_bytes())[1]
    glass=next(file for file in component_map(source) if '_glass_' in file.lower())
    (OUT/'native_glass_lods.json').write_text(json.dumps([[dict(g,corners=g['corners'].tolist()) for g in local_geometry(source,lv)[glass]] for lv in (1,2)]))
    return single


def build():
    assert shutil.disk_usage(b.OUT).free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    header,nodes=mesh.read_tree(b.DEST.read_bytes());before=hp_world(nodes)
    original=local_geometry(nodes);tr,_=audit.transforms(nodes)
    world={f:base.world(gs,*tr[f.lower()]) for f,gs in original.items()}
    for file,groups in world.items():
        if file.lower().startswith('baydoor'):
            for g in groups:
                p=g['corners'][...,:3]
                # Real hinge clearance, including the lower door skin.
                z=p[...,2].copy();p[...,2]=2.725+(z-2.70)*(1.80/1.85)
                p[...,1]+=.035+(p[...,2]-z)*((b.old.roof(4.55)-b.old.roof(2.70))/1.85)
                p[...,0]*=.72/.74
    split=split_tail(world)
    set_rig(nodes);hardpoints=place_hardpoints(nodes,before,split)
    tr,_=audit.transforms(nodes)
    local={f:base.world(gs,tr[f.lower()][0].T,-tr[f.lower()][0].T@tr[f.lower()][1]) for f,gs in world.items()}
    write_geometry(nodes,[local]);DEST.write_bytes(mesh.write_tree(header,nodes))
    single=export_lod0(nodes)
    # Intermediate authoring data is shared by LOD, collision and damage tools.
    data=dict(accepted_source=str(b.DEST),accepted_sha256=digest(b.DEST),original=str(base.SOURCE),
              original_sha256=digest(base.SOURCE),split=split,hardpoints=hardpoints,
              fold_degrees=float(np.rad2deg(FOLD)),pivot=WING_PIVOT.tolist(),lod0_triangles=sum(len(g['corners']) for gs in local.values() for g in gs))
    (OUT/'assembly.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    print('ASSEMBLED',data['lod0_triangles'],split['drum_triangles'],'drum triangles on Root',flush=True)


if __name__=='__main__':
    build()
