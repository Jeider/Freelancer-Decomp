"""Keep the established cuff treatment; restore the belt's original flat panels."""
import sys,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('hatcher_smoothing',ROOT/'tools/hatcher_body/full_smooth.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.OUT=ROOT/'out/character_rounding/li/hatcher_belt_study'
oldregion=m.region;oldprevious=m.previous_region
def belt(p):return 1-m.helpers.smooth(.17,.20,abs(p[0])) if -.055<p[1]<.16 else 0
m.previous_region=lambda p:oldprevious(p)*(1-belt(p))
m.region=lambda p:oldregion(p)*(1-belt(p))
m.main()
target=ROOT/'out/character_rounding/li/li_hatcher_body/after.json'
target.write_bytes((m.OUT/'after.json').read_bytes())
# Preview-only fitted belt: straight parallel edges, no convexity across width.
import numpy as np
d=json.loads(target.read_text());original=json.loads((m.OUT/'before.json').read_text())
def samples(data):
 group=next(g for g in data['groups'] if g['name']=='hatcher_body_4')
 ix=np.unique(np.array(group['faces']).ravel());pi=np.array(data['point_indices']);ui=np.array(data['uv_indices'])
 return ix,pi[ix],np.array(data['points'])[pi[ix]],np.array(data['uv'])[ui[ix]]
_,_,p,u=samples(original);front=p[:,2]<-.095
yfit=np.linalg.lstsq(np.column_stack((p[front,0],u[front,0],np.ones(front.sum()))),p[front,1],rcond=None)[0]
zfit=np.polyfit(p[front,0],p[front,2],2)
_,indices,p,u=samples(d);points=np.array(d['points']);normals=np.array(d['normals']);delta=0
for i,pt,uv in zip(indices,p,u):
 blend=float(np.clip((-pt[2]-.085)/.025,0,1))
 q=pt.copy();q[1]=(1-blend)*pt[1]+blend*np.dot([pt[0],uv[0],1],yfit)
 q[2]=(1-blend)*pt[2]+blend*np.polyval(zfit,pt[0])
 points[i]=q;delta=max(delta,float(np.linalg.norm(q-pt)))
 nn=np.array([2*zfit[0]*pt[0]+zfit[1],0,-1.]);nn/=np.linalg.norm(nn)
 normals[i]=normals[i]*(1-blend)+nn*blend;normals[i]/=max(np.linalg.norm(normals[i]),1e-9)
d['points']=points.tolist();d['normals']=normals.tolist();target.write_text(json.dumps(d))
(target.parent/'belt_preview.json').write_text(json.dumps(dict(preview_only=True,dfm_requires_reexport=True,max_belt_move_m=delta,parallel_edges=True,flat_across_width=True),indent=2))
