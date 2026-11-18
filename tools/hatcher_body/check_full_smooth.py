"""Structural validation of the offline DFM prototype, not an animation test."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,read_tree,child,arr,triangles
from repair_panel_normals import leaves
OUT=ROOT/'out/hatcher_body_full_smooth';REL='CHARACTERS/BODIES/li_hatcher_body.dfm'
report=json.loads((OUT/'report.json').read_text())
live_before=hashlib.sha256((GAME/'DATA'/REL).read_bytes()).hexdigest()
assert hashlib.sha256((ROOT/'out/hatcher_body_smooth/original/DATA'/REL).read_bytes()).hexdigest()==report['source_sha256']
data=(OUT/'stage/DATA'/REL).read_bytes()
assert hashlib.sha256(data).hexdigest()==report['prototype_sha256']
base=(ROOT/'out/hatcher_body_smooth/original/DATA'/REL).read_bytes()
old={p:b for p,_,b in leaves(base)[1]};new={p:b for p,_,b in leaves(data)[1]}
changed=[p for p in set(old)|set(new) if old.get(p)!=new.get(p)]
assert changed and all('/MultiLevel/Mesh0/' in p for p in changed)
_,roots=read_tree(data);results=[]
for mesh in child(roots[0],'MultiLevel').children:
    if not mesh.name.startswith('Mesh'):continue
    g=child(mesh,'Geometry');p=arr(g,'Points','<f4',3);n=arr(g,'Vertex_normals','<f4',3)
    pi=arr(g,'Point_indices','<u4').ravel();uv=arr(g,'UV0','<f4',2);ui=arr(g,'UV0_indices','<u4').ravel()
    f=arr(g,'Point_bone_first','<u4').ravel();c=arr(g,'Point_bone_count','<u4').ravel();w=arr(g,'Bone_weight_chain','<f4').ravel();bones=arr(g,'Bone_id_chain','<u4').ravel()
    assert len(p)==len(n)==len(f)==len(c) and len(pi)==len(ui)
    assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()
    assert np.max(np.abs(np.linalg.norm(n,axis=1)-1))<1e-4
    assert pi.max()<len(p) and ui.max()<len(uv) and len(pi)<65536
    assert len(w)==len(bones) and np.isfinite(w).all() and w.min()>=0
    for start,count in zip(f,c):assert count>0 and start+count<=len(w) and abs(sum(w[start:start+count])-1)<1e-5
    count=0;degenerate=0
    for group in child(mesh,'Face_groups').children:
        if not group.children:continue
        for tri in triangles(group):
            assert min(tri)>=0 and max(tri)<len(pi)
            a,b,c=p[pi[tri]];count+=1
            degenerate+=int(np.linalg.norm(np.cross(b-a,c-a))<1e-12)
    results.append(dict(mesh=mesh.name,triangles=count,degenerate=degenerate))
assert all(x['degenerate']==0 for x in results)
assert hashlib.sha256((GAME/'DATA'/REL).read_bytes()).hexdigest()==live_before
(OUT/'validation.json').write_text(json.dumps(dict(live_game_unchanged=True,indices_normals_weights_valid=True,lods=results,animation_tested=False),indent=2))
print(json.dumps(results,indent=2))

