"""Validate every staged DFM, including untouched LODs and normalized skin."""
import sys,json,hashlib,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import read_tree,child,blob,arr,triangles
from repair_panel_normals import leaves
OUT=ROOT/'out/character_rounding/all_bodies';results=[];errors=[]
for folder in sorted(OUT.iterdir()):
 if not (folder/'report.json').exists():continue
 try:
  report=json.loads((folder/'report.json').read_text());source=Path(report['source']);raw=source.read_bytes();data=(OUT/'stage/DATA/CHARACTERS/BODIES'/source.name).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==report['source_sha256'],'game source changed'
  assert hashlib.sha256(data).hexdigest()==report['output_sha256'],'stage hash changed'
  old={k:b for k,_,b in leaves(raw)[1]};new={k:b for k,_,b in leaves(data)[1]}
  changes=[k for k in set(old)|set(new) if old.get(k)!=new.get(k)];assert all('/MultiLevel/Mesh0/' in k for k in changes)
  root=read_tree(data)[1][0];mesh=child(child(root,'MultiLevel'),'Mesh0');g=child(mesh,'Geometry');p=arr(g,'Points','<f4',3);n=arr(g,'Vertex_normals','<f4',3)
  pi=arr(g,'Point_indices','<u4').ravel();uv=arr(g,'UV0','<f4',2);ui=arr(g,'UV0_indices','<u4').ravel();first=arr(g,'Point_bone_first','<u4').ravel();count=arr(g,'Point_bone_count','<u4').ravel();bones=arr(g,'Bone_id_chain','<u4').ravel();ws=arr(g,'Bone_weight_chain','<f4').ravel()
  assert len(p)==len(n)==len(first)==len(count) and len(pi)==len(ui)
  assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all() and np.isfinite(ws).all()
  assert pi.max()<len(p) and ui.max()<len(uv) and len(pi)<65536
  validbones={struct.unpack('<I',blob(x,'Index'))[0] for x in child(root,'Cmpnd').children if x.children and any(c.name=='Index' for c in x.children)}
  assert set(map(int,bones))<=validbones and len(ws)==len(bones) and (ws>=0).all()
  for f,c in zip(first,count):assert 0<c<=4 and f+c<=len(ws) and abs(float(ws[f:f+c].sum())-1)<1e-4
  f=np.array([t for group in child(mesh,'Face_groups').children if group.children for t in triangles(group)])
  assert f.min()>=0 and f.max()<len(pi)
  pp=p[pi[f]];area=np.linalg.norm(np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]),axis=1)
  before=json.loads((folder/'before.json').read_text());bp=np.array(before['points']);assert (p.min(0)>=bp.min(0)-2e-6).all() and (p.max(0)<=bp.max(0)+2e-6).all()
  if changes:assert np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-3
  results.append(dict(name=folder.name,triangles=len(f),vertices=len(p),max_influences=int(count.max()),degenerate_triangles=int((area<1e-12).sum()),only_mesh0_changed=True,source_unchanged=True))
 except Exception as e:errors.append(dict(name=folder.name,error=repr(e)))
(OUT/'validation.json').write_text(json.dumps(dict(valid=len(results),results=results,errors=errors,animation_validated=False),indent=2))
print('Validated',len(results),'errors',errors)
if errors:raise SystemExit(1)
