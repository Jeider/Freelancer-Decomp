"""Read-only native source extraction for the Blender-only aft housing prototype."""
import json
from pathlib import Path
import numpy as np
import rh_concept_b_final as f

OUT=f.OUT.parent/'tail_prototype_01'
ORIGINAL=Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_pir_elite/rh_pir_elite1.cmp')
ORIGINAL_HASH='ebc73cc3a9c653fdd19fd2498fd7ec9a3a34db42d51668d78ba156346ba33e14'


def world_parts(path):
    _,nodes=f.mesh.read_tree(path.read_bytes())
    transforms,_=f.audit.transforms(nodes)
    names=f.component_map(nodes)
    return nodes,{names[k]:f.base.world(v,*transforms[k.lower()]) for k,v in f.local_geometry(nodes).items()}


def points(groups):
    return np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])


def normals(a):
    n=np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3])
    length=np.linalg.norm(n,axis=1)
    assert np.min(length)>1e-7
    a[:,:,3:6]=(n/length[:,None])[:,None,:]


def mounted_y(y):
    return .90+(y+.08)*(2.60/2.785)


def pylon_position(p):
    p=np.array(p,copy=True,dtype=float)
    p[...,0]+=np.sign(p[...,0])*.65
    p[...,1]=mounted_y(p[...,1])
    p[...,2]+=5.15
    return p


def main():
    assert f.digest(ORIGINAL)==ORIGINAL_HASH,'Use the authenticated original, not the overwritten game CMP'
    OUT.mkdir(parents=True,exist_ok=True)
    source_nodes,source=world_parts(ORIGINAL)
    _,current=world_parts(f.DEST)
    original_tail=source['Rh_tail_lod1']
    panel=next(g for g in original_tail if g['material']==0xf6aaa5b8)
    # Audited original LOD0 housing surface IDs. Excludes the surrounding fin.
    ids=[10,11,12,*range(75,100)]
    raw=np.array(panel['corners'][ids],copy=True)
    housing=raw.copy()
    housing[...,0]*=1.25
    housing[...,1]=mounted_y(raw[...,1])
    rear=raw[...,2]>7.8
    # Flat hatch face with angular end slopes, seated inside the existing upright.
    housing[...,2]=np.where(rear,np.where((raw[...,1]>.50)&(raw[...,1]<2.10),13.38,13.02),12.54)
    normals(housing)
    assert np.array_equal(raw[...,6:8],housing[...,6:8])
    additions=[dict(name='Tail - original hatch housing',groups=[dict(material=panel['material'],corners=housing)])]
    selected=[]
    for g in original_tail:
        a=np.array(g['corners'],copy=True)
        a=a[np.max(np.abs(a[...,0]),axis=1)>1.0]
        if len(a):selected.append(dict(g,corners=a))
    assert sum(len(g['corners']) for g in selected)==56
    for side,label in ((-1,'port'),(1,'starboard')):
        for upper in (False,True):
            groups=[]
            for g in selected:
                a=g['corners']
                keep=(np.mean(a[...,0],axis=1)*side>0)&((np.mean(a[...,1],axis=1)>1.30)==upper)
                a=np.array(a[keep],copy=True)
                if not len(a):continue
                old_uv=a[...,6:8].copy()
                a[...,:3]=pylon_position(a[...,:3]);normals(a)
                assert np.array_equal(a[...,6:8],old_uv)
                groups.append(dict(material=g['material'],corners=a))
            additions.append(dict(name=f'Tail - {label} {"upper" if upper else "lower"} pylon',groups=groups))
    all_additions=[g for e in additions for g in e['groups']]
    ap=points(all_additions)
    assert ap[:,1].min()>f.TAIL_CUT and ap[:,1].max()<f.TAIL_TOP
    assert len(additions)==5
    sp=points([g for gs in source.values() for g in gs])
    cp=points([g for gs in current.values() for g in gs]+all_additions)
    original_center=(sp.min(0)+sp.max(0))*.5
    # Translate the complete hierarchy, including all hardpoints and damage caps.
    shift=original_center-(cp.min(0)+cp.max(0))*.5
    shift[0]=0  # Preserve exact bilateral symmetry; original x center differs by 0.00016.
    hp=f.hp_world(source_nodes)
    mounts=[]
    for key in ('hpcm01','hpmine01','hpthruster01','hpthruster02'):
        item=hp[key]
        mounts.append(dict(name=item['name'],position=pylon_position(item['position']),orientation=item['orientation']))
    data=dict(original=str(ORIGINAL),original_sha256=ORIGINAL_HASH,base_cmp=str(f.DEST),base_cmp_sha256=f.digest(f.DEST),
              shared_mat=str(f.SHARED_MAT),shared_mat_sha256=f.digest(f.SHARED_MAT),
              original_housing_triangles=ids,added_triangles=sum(len(g['corners']) for g in all_additions),
              original_bounds=[sp.min(0),sp.max(0)],prototype_bounds_before_recenter=[cp.min(0),cp.max(0)],
              center_shift_native=shift,original_bounds_center=original_center,
              middle_tail_band=[f.TAIL_CUT,f.TAIL_TOP],added_bounds=[ap.min(0),ap.max(0)],
              objects=additions,hardpoints=mounts,source_tail=original_tail,
              notes='Blender prototype only. Upper/lower frame, drum, cockpit unchanged. Native CMP/SUR/INI not written.')
    def serial(v):
        if isinstance(v,np.ndarray):return v.tolist()
        if isinstance(v,np.generic):return v.item()
        raise TypeError(type(v))
    (OUT/'prototype_data.json').write_text(json.dumps(data,default=serial,indent=2),encoding='utf8')
    print('PROTOTYPE:',data['added_triangles'],'added triangles; center shift',shift.tolist(),flush=True)


if __name__=='__main__':main()
