"""Animated Q13 prototype CMP, first native pirate UV pass; no installation."""
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import secrets
import shutil
import struct
import numpy as np
import rh_freighter_q13 as q
import full_ship_audit as audit

f=q.f
OUT=q.OUT.parent/'rig_01'
DEST=OUT/'rh_pir_freighter.cmp'
P=f.mesh.crc('pir_r_panel01_256')
R=f.mesh.crc('pir_r_panel02_256')
RD=f.mesh.crc('pir_r_panel02_2562side')
G=f.mesh.crc('engine_grill01')
HOLD=f.mesh.crc('metal03D')
LIGHT=(.535,.30,.975,.81)
TRIM=(.012,.871,.988,.993)
OLIVE=(.680,.025,.978,.205)
RED=(.358,.328,.652,.470)


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def box_uv(coords,box,lo=None,hi=None):
    coords=np.array(coords,float);lo=coords.min(0) if lo is None else np.array(lo);hi=coords.max(0) if hi is None else np.array(hi)
    span=np.maximum(hi-lo,1e-6);u0,v0,u1,v1=box
    # Crop, never stretch a painted region independently in U and V.
    scale=min((u1-u0)/span[0],(v1-v0)/span[1]);offset=np.array([(u0+u1)/2,(v0+v1)/2])
    return (coords-(lo+hi)/2)*scale+offset


def material_map(name,groups):
    if name.startswith('Original'):return [dict(g,corners=np.array(g['corners'],float)) for g in groups]
    buckets=collections.defaultdict(list)
    # Smooth angular coordinates on curved skins, whole planar charts elsewhere.
    for g in groups:
        for tri in np.array(g['corners'],float):
            xyz=tri[:,:3];center=xyz.mean(0);n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);n/=np.linalg.norm(n)
            role=g['material'];mid=P;box=LIGHT
            if role==3:mid=RD;box=OLIVE
            elif role==4:mid=RD;box=OLIVE
            elif role==2:box=TRIM
            if name.startswith('Recess relief Aft') and abs(n[0])>.8:mid=R;box=RED
            if name.startswith('Recess relief Central') and abs(n[0])>.8:mid=R;box=OLIVE
            if name.startswith('Continuous hull'):
                hold_plane=(abs(abs(center[0])-2.39)<.001 or abs(center[1]+3.10)<.001 or
                    abs(center[2]+3.72)<.001 or abs(center[2]-5.72)<.001)
                if hold_plane and abs(center[0])<=2.391 and -3.101<=center[1]<3.9 and -3.721<=center[2]<=5.721:
                    mid=HOLD;box=(.02,.02,.98,.98)
            if name.startswith('Curved roof'):
                rho=np.hypot(xyz[:,1]-q.SHELL_Y,xyz[:,2]-q.SHELL_Z)
                theta=np.arctan2(xyz[:,2]-q.SHELL_Z,xyz[:,1]-q.SHELL_Y)
                if float(n@np.array([0,center[1]-q.SHELL_Y,center[2]-q.SHELL_Z]))<0 and rho.mean()<4.4:
                    mid=HOLD;box=(.02,.02,.98,.98)
                    co=np.column_stack((xyz[:,0],theta*4.34));key=('roof inside',)
                elif abs(center[0])<1.83 and abs(n[0])<.1:
                    index=int(np.clip(np.floor((theta.mean()+math.radians(75))/math.radians(18.75)),0,7))
                    mid=R if index in (1,5) else P;box=RED if mid==R else LIGHT
                    co=np.column_stack((xyz[:,0],theta*4.51));key=('roof panel',index)
                else:
                    co=np.column_stack((theta*4.65,xyz[:,0]));mid=P;box=TRIM;key=('roof track',round(abs(center[0]),2),int(np.sign(center[0])))
            elif name.startswith('Stepped circular'):
                rho=np.hypot(xyz[:,1]-q.SHELL_Y,xyz[:,2]-q.SHELL_Z)
                angle=np.arctan2(xyz[:,2]-q.SHELL_Z,xyz[:,1]-q.SHELL_Y)
                if abs(n[0])>.8 and n[0]*center[0]<0:
                    # Inner cheek is a plane, including its center fan. Polar
                    # coordinates collapse/stretch triangles near the center.
                    co=xyz[:,[2,1]];key=('inner cheek plane',round(center[0],2));mid=RD;box=OLIVE
                elif 3.12<rho.mean()<4.26 and abs(n[0])>.8:
                    sector=int(np.clip(np.floor((angle.mean()+math.pi/2)/(math.pi/4)),0,3))
                    co=np.column_stack((angle*3.65,rho));key=('broad arch fields',sector);mid=R if sector in (0,3) else P;box=OLIVE if mid==R else LIGHT
                elif abs(n[0])>.8:
                    co=xyz[:,[2,1]];key=('arch plane',round(center[0],2),role)
                    mid=RD if role in (3,4) else P;box=OLIVE if mid==RD else LIGHT
                else:
                    # Unwrap curved thickness with axial X, not the nearly
                    # constant radius; all facets share one continuous strip.
                    co=np.column_stack((angle*4.45,xyz[:,0]));key=('arch rim',round(rho.mean(),2));mid=P;box=TRIM
            elif name.startswith('Engine casing'):
                side=1 if center[0]>0 else -1;cx=side*2.08;cy=-.28
                if abs(n[2])>.95 and abs(center[2]-12.158)<.001 and np.max(np.hypot(xyz[:,0]-cx,xyz[:,1]-cy))<1.09:
                    mid=G;uv=(xyz[:,[0,1]]-[cx,cy])/2.16+.5
                    a=tri.copy();a[:,6:8]=uv;buckets[('fixed',mid)].append(a);continue
                if abs(n[2])<.95:
                    theta=np.arctan2(xyz[:,1]-cy,xyz[:,0]-cx)
                    theta=np.unwrap(theta);m=theta.mean();sector=math.floor((m+math.pi)/(math.pi/2))
                    region=0 if center[2]<8.17 else 1 if center[2]<10.351 else 2
                    mid=RD if 10.87<center[2]<11.64 else P;box=OLIVE if mid==RD else LIGHT
                    co=np.column_stack((theta*1.86,xyz[:,2]));key=('engine curved',sector,region)
                else:co=xyz[:,[0,1]];key=('engine end',round(center[2],3))
            else:
                axis=int(np.argmax(abs(n)));axes=[i for i in range(3) if i!=axis]
                co=xyz[:,axes]
                if name.startswith(('New transverse','Cylinder socket')) and abs(n[0])>.9:
                    mid=R if name.startswith('New transverse') else P;box=OLIVE if mid==R else TRIM
                # Coplanar triangles share one chart and texture scale.
                key=('plane',tuple(n.round(4)),round(float(n@center),4),axis)
            buckets[('chart',mid,tuple(box),key)].append((tri,co))
    result=collections.defaultdict(list)
    for key,values in buckets.items():
        if key[0]=='fixed':result[key[1]].extend(values);continue
        _,mid,box,_=key;coords=np.concatenate([co for _,co in values]);lo=coords.min(0);hi=coords.max(0)
        # Frame-like long flat strips take an intact border chart.
        if mid==P and box==LIGHT and max(hi-lo)>3*max(min(hi-lo),1e-5):box=TRIM
        if box==TRIM:
            # Orient the long dimension along the horizontal atlas border.
            # A longitudinal Z rail must not sample a tiny vertical sliver.
            pivot=coords.mean(0);_,basis=np.linalg.eigh((coords-pivot).T@(coords-pivot))
            along=basis[:,-1]
            if along[np.argmax(abs(along))]<0:along=-along
            rotation=np.column_stack((along,[-along[1],along[0]]))
            values=[(tri,(co-pivot)@rotation) for tri,co in values]
            coords=np.concatenate([co for _,co in values]);lo=coords.min(0);hi=coords.max(0)
        for tri,co in values:
            a=tri.copy();a[:,6:8]=box_uv(co,box,lo,hi);result[mid].append(a)
    return [dict(material=mid,corners=np.array(ts),unused=204) for mid,ts in result.items()]


def owner(name):
    if name.startswith('Original glazing'):return 'glass_lod1'
    if name.startswith('Curved roof'):return 'Baydoor_lod1'
    side='port' if '-1' in name else 'star'
    if name.startswith('Engine casing'):return 'port_engine_lod1' if side=='port' else 'starboard_engine_lod1'
    if name.startswith('New transverse'):
        size='big' if name.endswith(' 2') else 'sml'
        return f'rh_{side}_{size}_btn_lod1'
    if name.startswith(('Faceted shoulder','Intake vane','Cylinder socket')):return f'rh_{side}_side_lod1'
    return 'Root'


def main(input_path=None):
    assert shutil.disk_usage(q.ROOT.anchor).free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    input_path=Path(input_path) if input_path else OUT/'mechanical_geometry.json'
    data=json.loads(input_path.read_text(encoding='utf8'))
    sourcehash=f.digest(q.SOURCE);mathash=f.digest(q.MAT)
    assert sourcehash==data['source_sha256']
    header,nodes=f.mesh.read_tree(q.SOURCE.read_bytes());original=copy.deepcopy(nodes)
    names=f.component_map(nodes);oldlocal=f.local_geometry(nodes);tr_default,_=f.audit.transforms(nodes)
    tr_flight,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    # Optional explicit authoring offsets, e.g. when a prototype's engines move.
    # Geometry stays in world authoring coordinates; only named HP positions
    # follow it. All other HP bytes and all orientations remain native.
    hp_offsets={name.lower():np.array(delta,float) for name,delta in data.get('hardpoint_world_offsets',{}).items()}
    adjusted=set()
    for file in names:
        for path,node in f.mesh.walk([f.mesh.child(nodes[0],file)]):
            bits=path.split('/')
            if '/Hardpoints/' not in path or bits[-1].lower()!='position':continue
            hpname=bits[-2].lower()
            if hpname not in hp_offsets:continue
            delta=hp_offsets[hpname]
            assert delta.shape==(3,) and np.isfinite(delta).all()
            r,_=tr_flight[file.lower()]
            pos=np.frombuffer(node.blob,dtype='<f4').copy()
            assert pos.shape==(3,) and hpname not in adjusted
            node.blob=np.array(pos+r.T@delta,dtype='<f4').tobytes();adjusted.add(hpname)
    assert adjusted==set(hp_offsets)
    hp_expected=copy.deepcopy(nodes)
    authored=collections.defaultdict(list);sources=collections.defaultdict(list)
    for entry in data['objects']:
        n=owner(entry['name']);gs=material_map(entry['name'],entry['groups'])
        authored[n].extend(gs);sources[n].append(entry['name'])
    assert set(authored)==set(names.values())
    local={}
    for file,n in names.items():
        # Authoring JSON is FLIGHT, while zero construct pose is folded.
        # Inverse the flight transform, never the default transform for sliders.
        r,t=tr_flight[file.lower()]
        local[file]=f.base.world(authored[n],r.T,-r.T@t)
    # Explicit wires on every submodel avoid retail triangle-mesh fallback.
    for file in names:
        p=f.mesh.child(nodes[0],file)
        if not any(c.name.lower()=='vmeshwire' for c in p.children):
            p.children.append(f.folder('VMeshWire',f.mesh.Node('VWireData',b'')))
    f.write_geometry(nodes,[local])
    for file,n in names.items():
        p=f.mesh.child(nodes[0],file);ml=f.mesh.child(p,'MultiLevel')
        f.mesh.child(ml,'Switch2').blob=np.array([0,10000],'<f4').tobytes()
        if n in ('Baydoor_lod1','glass_lod1') or '_btn_' in n:
            wire=f.mesh.child(f.mesh.child(p,'VMeshWire'),'VWireData')
            crc=struct.unpack_from('<I',wire.blob,4)[0]
            wire.blob=struct.pack('<II4H',16,crc,0,0,0,0)
    salt=secrets.token_hex(6);resources=q.salted(nodes,salt)
    nodes[0].children=[n for n in nodes[0].children if n.name.lower() not in ('material library','texture library')]
    DEST.write_bytes(f.mesh.write_tree(header,nodes))
    _,decoded=f.mesh.read_tree(DEST.read_bytes());actual=f.local_geometry(decoded);dn=f.component_map(decoded)
    flat={p.lower():n.blob for p,n in f.mesh.walk(decoded)}
    joints=audit.constructs(flat);channels=audit.channels(flat,joints)
    assert all(c['bound_joint'] and c['native_size_valid'] and c['finite'] and not c.get('parent_mismatch') for c in channels)
    tracks={(c['script'],c['child']):c for c in channels}
    for c in channels:
        if c['script']=='sc_launch extend':assert np.allclose(c['last'],tracks['sc_extend wing',c['child']]['first'])
    # Geometry references can be pinned offline; shared libraries remain in DATA.
    mats=f.audit.material_table([q.MAT,q.MAT.parents[2]/'fx/envmapbasic.mat'])
    maximum={'vertices':0,'indices':0};counts={}
    for path,blob in flat.items():
        if path.endswith('/vmeshdata'):
            v,gs,idx=f.audit.decode(blob);assert len(v)<65536 and len(idx)<65536
            maximum['vertices']=max(maximum['vertices'],len(v));maximum['indices']=max(maximum['indices'],len(idx));at=0
            for mat,lo,hi,num,_ in gs:
                ids=idx[at:at+num]+lo;assert mat in mats and num%3==0 and ids.min()>=lo and ids.max()<=hi<len(v);at+=num
            assert at==len(idx)
    objects=[]
    for file,gs in actual.items():
        n=dn[file];counts[n]=sum(len(g['corners']) for g in gs)
        for g in gs:
            a=g['corners'];assert np.isfinite(a).all()
            assert np.allclose(np.linalg.norm(a[...,3:6],axis=-1),1,atol=1e-4)
            if 'metal' in mats[g['material']]['texture'].lower():assert n in ('Root','Baydoor_lod1')
        joint=next((j for j in joints if j['name'].lower()==n.lower()),dict(name='Root',parent=None,kind='fix',origin=[0,0,0],rotation=np.eye(3).tolist()))
        objects.append(dict(name=n,file=file,groups=gs,joint=joint,source_objects=sources[n]))
    leaves=lambda ns:{p:n.blob for p,n in f.mesh.walk(ns)}
    for tag in ('Animation','Cons'):
        sub=lambda ns:f.mesh.child(ns[0],tag) if tag=='Animation' else f.mesh.child(f.mesh.child(ns[0],'Cmpnd'),tag)
        assert leaves([sub(original)])==leaves([sub(decoded)])
    for oldfile,newfile in [(file,resources[file]) for file in names]:
        hp=lambda ns,file:{p.split('/Hardpoints/',1)[-1]:n.blob for p,n in f.mesh.walk([f.mesh.child(ns[0],file)]) if '/Hardpoints/' in p}
        assert hp(hp_expected,oldfile)==hp(decoded,newfile)
    original_hp=f.hp_world(original);actual_hp=f.hp_world(decoded)
    assert set(original_hp)==set(actual_hp)
    for name,before in original_hp.items():
        after=actual_hp[name]
        assert np.allclose(after['position'],np.array(before['position'])+hp_offsets.get(name,np.zeros(3)),atol=2e-5),name
        assert np.allclose(after['orientation'],before['orientation'],atol=1e-7),name
    assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(decoded))
    images={};td=OUT/'textures';td.mkdir(exist_ok=True)
    for mid in {g['material'] for gs in actual.values() for g in gs}:
        m=mats[mid];entry={k:v for k,v in m.items() if k!='image'}
        if m['image'] is not None:
            path=td/(m['texture'].rsplit('.',1)[0]+'.png');m['image'].save(path);entry['image_path']=str(path)
        images[mid]=entry
    dump('scene.json',dict(cmp=str(DEST),cmp_sha256=f.digest(DEST),objects=objects,materials=images,channels=channels))
    poses={}
    for label,pose in [('default',None),('flight',('Sc_extend wing',0)),('folded',('Sc_extend wing',1))]:
        tt,_=f.audit.transforms(decoded,pose)
        pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for file,gs in actual.items() for g in f.base.world(gs,*tt[file.lower()])])
        poses[label]=dict(min=pts.min(0),max=pts.max(0))
    assert all(np.allclose(poses['default'][key],poses['folded'][key]) for key in ('min','max'))
    dump('build.json',dict(cmp=str(DEST),cmp_sha256=f.digest(DEST),source=str(q.SOURCE),source_sha256=sourcehash,
        shared_mat=str(q.MAT),shared_mat_sha256=mathash,input_geometry_sha256=f.digest(input_path),
        salt=salt,resources=resources,triangles=counts,total_triangles=sum(counts.values()),maximum=maximum,
        materials=[m['name'] for m in images.values()],original_animation_and_constructs_preserved=True,
        original_hardpoint_bytes_preserved=not hp_offsets,hardpoint_world_offsets=hp_offsets,
        unlisted_hardpoint_bytes_preserved=True,hardpoints=actual_hp,poses=poses,lods=1,
        wire='Prototype part-owned feature edges; no wire on glass, door or moving buttons.',
        installed=False,game_launched=False))
    assert sourcehash==f.digest(q.SOURCE) and mathash==f.digest(q.MAT)
    print('RIG_CMP_READY',sum(counts.values()),'triangles',maximum,DEST)


if __name__=='__main__':main()
