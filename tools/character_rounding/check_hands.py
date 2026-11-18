"""Validate authoring data and the actual serialized DFM LOD patches."""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from contours import GAME,read_tree,child,arr,triangles,digest
from hands import OUT,NAMES
from extra_lods import OUT as LODS,reconstruct
if '--gloves' in sys.argv:
    from gloves import OUT,NAMES
    from remaining_lods import OUT as LODS,reconstruct


def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def faces(d):return np.array([[d['point_indices'][v] for v in t] for g in d['groups'] for t in g['faces']],dtype=int)
def boundary(d):
    counts=Counter(tuple(sorted((int(a),int(b)))) for t in faces(d) for a,b in zip(t,np.roll(t,-1)))
    assert max(counts.values())<=2,'Non-manifold edge'
    return sorted({i for e,n in counts.items() if n==1 for i in e})


def main():
    manifest=json.loads((LODS/'models.json').read_text());records={r['name']:r for r in manifest['files']};checked=[]
    for name in NAMES:
        folder=OUT/name;source=load(folder/'source.json.gz');edited=load(folder/'edited.json.gz');r=records[name]
        report=json.loads((folder/'validation.json').read_text())
        assert report['edited_sha256']==digest((folder/'edited.json.gz').read_bytes())
        assert source['bones']==edited['bones']
        p=np.array(edited['points'],dtype='<f4');n=np.array(edited['normals'],dtype='<f4');f=faces(edited);v=p[f]
        cross=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);areas=np.linalg.norm(cross,axis=1)
        assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(edited['uv']).all()
        assert areas.min()>1e-10 and ((cross*n[f].mean(1)).sum(1)>0).all(),'Fold or degenerate triangle'
        assert len(f)<=1200 and max(abs(np.linalg.norm(n,axis=1)-1))<1e-4
        new_boundary=boundary(edited);old_boundary=boundary(source)
        for i in old_boundary:
            q=np.array(source['points'][i]);j=min(new_boundary,key=lambda j:np.linalg.norm(p[j]-q))
            assert np.linalg.norm(p[j]-q)<1e-7,('Wrist position',name,i)
            keys=set(source['skin'][i])|set(edited['skin'][j])
            assert max(abs(source['skin'][i].get(k,0)-edited['skin'][j].get(k,0)) for k in keys)<1e-6
        for weights in edited['skin']:
            assert 1<=len(weights)<=4 and abs(sum(weights.values())-1)<1e-6 and min(weights.values())>0
            assert all(0<=int(b)<len(edited['bones']) for b in weights)
        raw=(GAME/'DATA'/r['relative_path']).read_bytes();assert digest(raw)==r['before_sha256']
        built=reconstruct(raw,Path(r['patch']));assert digest(built)==r['after_sha256']
        root=read_tree(built)[1][0];g=child(child(child(root,'MultiLevel'),'Mesh0'),'Geometry')
        pi=arr(g,'Point_indices','<u4').ravel();points=arr(g,'Points','<f4',3)
        assert np.array_equal(points[pi],p[np.array(edited['point_indices'])])
        actual=arr(g,'UV0','<f4',2)[arr(g,'UV0_indices','<u4').ravel()]
        assert np.array_equal(actual,np.array(edited['uv'],dtype='<f4')[edited['uv_indices']])
        first=arr(g,'Point_bone_first','<u4').ravel();count=arr(g,'Point_bone_count','<u4').ravel()
        ids=arr(g,'Bone_id_chain','<u4').ravel();weights=arr(g,'Bone_weight_chain','<f4').ravel()
        for j,k in enumerate(edited['point_indices']):
            result={str(int(b)):float(w) for b,w in zip(ids[first[j]:first[j]+count[j]],weights[first[j]:first[j]+count[j]])}
            assert set(result)==set(edited['skin'][k]) and max(abs(result[b]-edited['skin'][k][b]) for b in result)<1e-6
        checked.append(dict(name=name,triangles=len(f),wrist_vertices_preserved=len(old_boundary),**report))
    (OUT/'validation.json').write_text(json.dumps(dict(valid=len(checked),results=checked),indent=2))
    print('PASS:',len(checked),'hands; wrist/weights, normals, topology, DFM round-trip, native animation evidence')


if __name__=='__main__':main()
