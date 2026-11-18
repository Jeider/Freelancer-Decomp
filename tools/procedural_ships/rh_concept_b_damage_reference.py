"""Record original damage UVs and verify that remapping preserves approved cuts."""
import collections
import hashlib
import json
import sys
import numpy as np
import rh_concept_b_final as f
from preview import render

OUT=f.OUT


def groups(path):
    _,nodes=f.mesh.read_tree(path.read_bytes())
    libs={f.mesh.crc(p.split('/')[-2]):f.audit.decode(n.blob) for p,n in f.mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    return [g for p,n in f.mesh.walk(nodes) if '/level0/' in p.lower() and p.lower().endswith('/vmeshref')
            for g in f.audit.extract(n.blob,libs)]


def geometry(gs):
    # Include normals, ignore materials/UV and triangle ordering.
    result=collections.Counter()
    for g in gs:
        for tri in g['corners']:
            a=np.round(tri[:,:6],5).astype('<f4');a[a==0]=0
            result[hashlib.sha256(a.tobytes()).hexdigest()]+=1
    return dict(result)


def main():
    path=OUT/'damage_mapping_audit.json'
    if '--before' in sys.argv:
        assert not path.exists(),'Keep the original remapping baseline'
        mats=f.audit.material_table([f.b.prior.LIBRARY]);sources=[]
        for p in sorted(f.b.base.SOURCE.parent.glob('*dmg*.3db')):
            gs=groups(p);rows=[]
            for g in gs:
                uv=g['corners'][...,6:8].reshape(-1,2)
                rows.append(dict(material=mats[g['material']]['name'],triangles=len(g['corners']),uv_min=uv.min(0).tolist(),uv_max=uv.max(0).tolist()))
            sources.append(dict(path=str(p),sha256=f.digest(p),groups=rows))
            if p.name.endswith('dmg_tail.3db'):
                points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs]);center=(points.min(0)+points.max(0))/2
                render(gs,mats,center,np.linalg.norm(points-center,axis=1).max(),(1,.7,1),size=650,mode='texture').save(OUT/'source_damage_tail.png')
        data=dict(shared_mat=str(f.b.prior.LIBRARY),shared_mat_sha256=f.digest(f.b.prior.LIBRARY),sources=sources,
                  before={p.name:dict(bytes=p.stat().st_size,geometry=geometry(groups(p))) for p in sorted((OUT/'damage').glob('*.3db'))})
    else:
        data=json.loads(path.read_text());after={}
        for name,old in data['before'].items():
            p=OUT/'damage'/name;new=geometry(groups(p))
            assert not (collections.Counter(old['geometry'])-collections.Counter(new)),('changed approved damage mesh',name)
            extra=sum(new.values())-sum(old['geometry'].values())
            assert extra==0 if 'tail' not in name else extra>0
            after[name]=dict(bytes=p.stat().st_size,original_geometry_preserved=True,added_triangles=extra)
        assert f.digest(f.b.prior.LIBRARY)==data['shared_mat_sha256']
        data['after']=after
        print('GEOMETRY PRESERVED; total bytes',sum(v['bytes'] for v in data['before'].values()),'->',sum(v['bytes'] for v in after.values()))
    path.write_text(json.dumps(data,indent=2),encoding='utf8')


if __name__=='__main__':main()
