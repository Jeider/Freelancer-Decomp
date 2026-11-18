"""Isolated LOD0/CMP handoff for manual HP editing. Never writes game assets/SUR."""
import collections
import copy
import json
from pathlib import Path
import shutil

import numpy as np
import rh_concept_b_final as f
from rh_concept_b_tail_prototype import ORIGINAL, ORIGINAL_HASH, world_parts, normals

OUT = f.OUT.parent / 'hardpoint_prototype_01'
DEST = OUT / 'rh_concept_b_prototype.cmp'
PANEL = f.mesh.crc('pir_r_panel01_256')
DARK = f.mesh.crc('pir_r-dark gray')


def serial(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    raise TypeError(type(value))


def leaves(nodes, contains):
    return {p:n.blob for p,n in f.mesh.walk(nodes) if contains in p.lower() and not n.children}


def hardpoint_records(nodes):
    names=f.component_map(nodes);flat={path:node for path,node in f.mesh.walk(nodes)}
    result=[]
    for path,node in flat.items():
        if '/hardpoints/' not in path.lower() or not path.lower().endswith('/position'):continue
        bits=path.split('/');file=bits[2]
        orientation=flat[path.rsplit('/',1)[0]+'/Orientation'].blob
        result.append(dict(name=bits[-2],owner=names[file],file=file,kind=bits[-3],
            position=np.frombuffer(node.blob,'<f4').tolist(),
            orientation=np.frombuffer(orientation,'<f4').reshape(3,3).tolist()))
    return result


def fix_housing(groups, shift):
    source=json.loads((f.OUT.parent/'tail_prototype_01/prototype_data.json').read_text())
    old=np.array(source['objects'][0]['groups'][0]['corners'])
    keys={f.triangle_key(t):i for i,t in enumerate(old)}
    hit=[];before=[];after=[]
    lo,hi=old[...,:3].min((0,1)),old[...,:3].max((0,1))
    for g in groups:
        for t in g['corners']:
            local=t.copy();local[:,:3]-=shift
            key=f.triangle_key(local)
            if key not in keys:continue
            hit.append(keys[key]);before.append(t[:,:3].copy())
            p=local[:,:3]
            p[:,0]*=3.10/(hi[1]-lo[1])
            p[:,1]=.75+(p[:,1]-lo[1])*3.10/(hi[1]-lo[1])
            p[:,2]=np.where(p[:,2]>12.60,12.75,12.54)
            t[:,:3]=p+shift
            normals(t[None,...]);after.append(t[:,:3].copy())
    assert sorted(hit)==list(range(28)),hit
    return dict(triangles=len(hit),before_bounds=[np.min(before,axis=(0,1)),np.max(before,axis=(0,1))],
                after_bounds=[np.min(after,axis=(0,1)),np.max(after,axis=(0,1))],
                rear_plane_native=12.75+shift[2],height=3.10)


def fix_frame_uv(groups, shift):
    changed=[]
    for gi,g in enumerate(groups):
        if g['material']!=PANEL:continue
        for ti,t in enumerate(g['corners']):
            p=t[:,:3]-shift
            # The front-facing end of the top rear-frame bar, highlighted by user.
            if p[:,1].min()<4.90 or not np.allclose(p[:,2],6.3909,atol=.0002):continue
            before=t[:,6:8].copy();ratio=f.b.prev.distortion(t)
            t[:,6]=.52+(p[:,0]+1.32)*.175
            t[:,7]=.27+(5.9587-p[:,1])*.175
            assert f.b.prev.distortion(t)<1.0001
            changed.append(dict(group=gi,triangle=ti,before=before,after=t[:,6:8].copy(),stretch_before=ratio))
    assert len(changed)==2,len(changed)
    return changed


def fix_cabin(groups, original, shift):
    cabin_shift=shift+np.array([0,.591818,2.70])
    inner=next(g['corners'].copy() for g in original['Root'] if g['material']==f.mesh.crc('metal03D'))
    inner=inner[np.max(inner[...,2],axis=1)<-4.79]
    assert len(inner)==114
    keys={f.triangle_key(t) for t in inner}
    removed=0
    for g in groups:
        keep=[]
        for t in g['corners']:
            a=t.copy();a[:,:3]-=cabin_shift
            keep.append(f.triangle_key(a) not in keys)
        removed+=len(keep)-sum(keep);g['corners']=g['corners'][keep]
    # Original inner shell, not reversed exterior glazing. A small inward offset
    # gives the lining thickness and separates it from surviving clipped trim.
    normal_map=collections.defaultdict(list)
    for t in inner:
        n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])
        for v in t:normal_map[tuple(v[:3].round(5))].append(n)
    for t in inner:
        for v in t:
            n=np.sum(normal_map[tuple(v[:3].round(5))],axis=0);n/=np.linalg.norm(n)
            v[:3]+=cabin_shift+n*.008
    normals(inner)
    groups=[g for g in groups if len(g['corners'])]
    # The source has an opening behind the seat leading into its original neck.
    # Our shortened neck does not seal that passage: give it an actual bulkhead,
    # slightly aft of the restored inner frame and fully within the cabin contour.
    outline=np.array([[-1.38,-1.70],[-1.22,-.79],[-1.02,.42],[-.80,.56],
                      [.80,.56],[1.02,.42],[1.22,-.79],[1.38,-1.70]])
    back=[]
    for i in range(1,len(outline)-1):
        t=np.zeros((3,8));t[:,:2]=outline[[0,i,i+1]];t[:,2]=-4.77
        if np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])[2]>0:t=t[[0,2,1]]
        t[:,:3]+=cabin_shift;normals(t[None,...]);back.append(t)
    floor=[]
    for g in groups:
        for t in g['corners']:
            p=t[:,:3]-cabin_shift
            if np.allclose(p[:,1],-1.741818,atol=.00002) and p[:,2].max()<-4.79:
                a=t[[0,2,1]].copy();a[:,1]+=.018;normals(a[None,...]);floor.append(a)
    assert floor,'Cabin floor must have an inward-facing lining'
    lining=np.concatenate((inner,np.array(back),np.array(floor)))
    groups.append(dict(material=DARK,corners=lining,unused=204))
    return groups,dict(original_inner_triangles=114,replaced_existing_triangles=removed,
                       restored_missing_triangles=114-removed,lining_offset=.008,
                       closed_bulkhead_triangles=len(back),inner_floor_triangles=len(floor),
                       material='pir_r-dark gray',glass_unchanged=True)


def main():
    assert shutil.disk_usage(OUT.parent).free>500_000_000
    assert f.digest(ORIGINAL)==ORIGINAL_HASH
    # Never silently overwrite the user's manually edited prototype.
    if DEST.exists():
        old=json.loads((OUT/'prototype.json').read_text())
        assert f.digest(DEST)==old['cmp_sha256'],'Manual HP edits detected; preserve this CMP'
    OUT.mkdir(parents=True,exist_ok=True)
    watched=[f.DEST,ORIGINAL,f.SHARED_MAT,Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_concept_b/rh_concept_b.cmp'),
             Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_concept_b/rh_concept_b.sur')]
    hashes={str(p):f.digest(p) for p in watched}
    header,nodes=f.mesh.read_tree(f.DEST.read_bytes())
    frozen={key:leaves(nodes,key) for key in ('/hardpoints/','/animation/','/cmpnd/')}
    names=f.component_map(nodes);local=f.local_geometry(nodes);tr,_=f.audit.transforms(nodes)
    world={k:f.base.world(g,*tr[k.lower()]) for k,g in local.items()}
    root=next(k for k,v in names.items() if v=='Root');tail=next(k for k,v in names.items() if v=='Rh_tail_lod1')
    shift=np.array(json.loads((f.OUT/'assembly.json').read_text())['center_shift_native'])
    _,original=world_parts(ORIGINAL)
    housing=fix_housing(world[tail],shift)
    uv=fix_frame_uv(world[root],shift)
    world[root],cabin=fix_cabin(world[root],original,shift)
    for k in (root,tail):
        r,t=tr[k.lower()];local[k]=f.base.world(world[k],r.T,-r.T@t)
    from rh_concept_b_engine_shell import rebuild_engines
    engines=rebuild_engines(local)
    f.write_geometry(nodes,[local])
    for k in names:
        ml=f.mesh.child(f.mesh.child(nodes[0],k),'MultiLevel')
        f.mesh.child(ml,'Switch2').blob=np.array([0,100000],'<f4').tobytes()
    assert all(leaves(nodes,key)==value for key,value in frozen.items())
    assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(nodes))
    DEST.write_bytes(f.mesh.write_tree(header,nodes))
    decoded=f.mesh.read_tree(DEST.read_bytes())[1]
    assert all(leaves(decoded,key)==value for key,value in frozen.items())
    # Mesh payload is local-space: replace data on the existing Blender rig while
    # retaining parents, keyframes and the editable HP empties unchanged.
    payload={names[k]:[dict(g,corners=g['corners']) for g in v] for k,v in local.items()}
    (OUT/'geometry.json').write_text(json.dumps(payload,default=serial,separators=(',',':')))
    report=dict(cmp=str(DEST),cmp_sha256=f.digest(DEST),sources=hashes,
                shared_mat=str(f.SHARED_MAT),source_blend=str(f.OUT/'rh_concept_b_rigged.blend'),
                source_blend_sha256=f.digest(f.OUT/'rh_concept_b_rigged.blend'),
                original_sha256=ORIGINAL_HASH,center_shift_native=shift,housing=housing,cabin=cabin,
                frame_uv=uv,engine_shells=engines,hardpoint_bytes_unchanged=True,animation_bytes_unchanged=True,
                hierarchy_bytes_unchanged=True,hardpoints=f.hp_world(decoded),hardpoint_nodes=hardpoint_records(decoded),
                triangles=sum(len(g['corners']) for gs in local.values() for g in gs),
                sur='Deferred until user finishes manual HP edits; none supplied',lods='LOD0 prototype only')
    (OUT/'prototype.json').write_text(json.dumps(report,default=serial,indent=2),encoding='utf8')
    assert all(f.digest(Path(p))==v for p,v in hashes.items())
    print('PROTOTYPE',DEST,'triangles',report['triangles'],'cabin',cabin,flush=True)


if __name__=='__main__':main()
