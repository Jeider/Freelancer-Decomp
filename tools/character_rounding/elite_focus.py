"""Focused offline elite study: exact circular cuffs and rounded upper surfaces."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'out/character_rounding/li/li_male_elite_body'
OUT=ROOT/'out/character_rounding/elite_focus';OUT.mkdir(exist_ok=True)
d=json.loads((SOURCE/'before.json').read_text());(OUT/'before.json').write_text(json.dumps(d))
p=np.array(d['points']);n=np.array(d['normals']);pi=np.array(d['point_indices']);uv=np.array(d['uv']);ui=np.array(d['uv_indices'])
key=lambda x:tuple(np.round(x,6))
edges={};neighbor={};normal={}
for i,v in enumerate(p):normal.setdefault(key(v),[]).append(n[i])
for g in d['groups']:
 for tri in g['faces']:
  t=pi[tri]
  for a,b in zip(t,np.roll(t,-1)):
   a,b=key(p[a]),key(p[b]);e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1
   neighbor.setdefault(a,set()).add(b);neighbor.setdefault(b,set()).add(a)
boundary={}
for (a,b),count in edges.items():
 if count==1:boundary.setdefault(a,set()).add(b);boundary.setdefault(b,set()).add(a)
seen=set();rings=[]
for start in boundary:
 if start in seen:continue
 stack=[start];component=set()
 while stack:
  v=stack.pop()
  if v in component:continue
  component.add(v);stack.extend(boundary[v]-component)
 seen|=component
 pts=np.array(list(component));center=pts.mean(0)
 if len(pts)>=4 and abs(center[0])>.22 and center[1]<.06:
  rings.append(pts)
print('Wrist boundaries:',[(len(r),r.mean(0).tolist()) for r in rings])
if not rings:
 # This costume closes its cuff against an inset sleeve: there is no open
 # topological boundary. Use the outer lip's authored vertex row instead.
 unique=np.unique(p.round(6),axis=0)
 for side in (-1,1):
  r=unique[(unique[:,0]*side>.25)&(unique[:,1]>.001)&(unique[:,1]<.030)]
  assert len(r)>=5
  rings.append(r)
assert len(rings)==2
profiles={}
for r in rings:
 center=r.mean(0);_,_,axes=np.linalg.svd(r-center);axis=axes[-1]
 side=1 if center[0]>0 else -1
 upper=np.unique(p[(p[:,0]*side>.21)&(p[:,1]>.175)&(p[:,1]<.215)].round(6),axis=0).mean(0)
 axis=upper-center;axis/=np.linalg.norm(axis)
 planar=r-center-np.outer((r-center)@axis,axis)
 # Circumdiameter of native wrist aperture: never inflate the original maximum.
 radius=max(np.linalg.norm(a-b) for a in planar for b in planar)/2
 profiles[1 if center[0]>0 else -1]=(center,axis,radius)
print('Profiles:',[(s,c.tolist(),a.tolist(),r) for s,(c,a,r) in profiles.items()])
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
norm={k:np.mean(v,axis=0) for k,v in normal.items()}
norm={k:v/max(np.linalg.norm(v),1e-9) for k,v in norm.items()}
# Gentle rounding of original vertices is restricted to the shoulder/collar.
rounded={}
for k in norm:
 v=np.array(k);nb=neighbor.get(k,());q=v.copy()
 if v[1]>.39 and abs(v[0])<.30 and nb:
  amount=.24*(1-smooth(.60,.645,v[1]))
  delta=(np.mean(list(nb),axis=0)-v)*amount
  delta*=min(1,.008/max(np.linalg.norm(delta),1e-9));q+=delta
 rounded[k]=q
def barytris(level):
 ts=[np.eye(3)]
 for _ in range(level):
  nxt=[]
  for a,b,c in ts:
   ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2;nxt.extend([[a,ab,ca],[ab,b,bc],[ca,bc,c],[ab,bc,ca]])
  ts=np.array(nxt)
 return ts
out=dict(points=[],normals=[],uv=[],point_indices=[],uv_indices=[],groups=[]);maxmove=0;errors=[]
for group in d['groups']:
 dst=dict(group);dst['faces']=[]
 for tri in group['faces']:
  ids=pi[tri];v=p[ids];ks=[key(x) for x in v];ns=np.array([norm[k] for k in ks]);rv=np.array([rounded[k] for k in ks])
  upper=v[:,1].max()>.18;cuff=v[:,1].min()<.18 and np.abs(v[:,0]).min()>.22 and v[:,1].max()>-.06
  for sub in barytris(3 if cuff or upper else 0):
   face=[]
   for b in sub:
    old=b@v;q=old.copy();nn=b@n[ids];nn/=max(np.linalg.norm(nn),1e-9)
    if upper and old[1]>.20:
     linear=b@rv;proj=np.array([linear-ns[i]*np.dot(linear-rv[i],ns[i]) for i in range(3)])
     strength=smooth(.22,.36,old[1])*(1-smooth(.60,.645,old[1]))
     q=linear+(b@proj-linear)*strength
     delta=q-old;q=old+delta*min(1,.012/max(np.linalg.norm(delta),1e-9))
    side=1 if old[0]>0 else -1;center,axis,r=profiles[side];t=np.dot(old-center,axis)
    blend=smooth(.22,.25,abs(old[0]))*(1-smooth(.115,.185,t))
    radial=old-center-axis*t;length=np.linalg.norm(radial)
    blend*=smooth(-.045,-.015,t)
    if length>.012 and blend>0:
     # A shallow native-sized taper, fully circular through the cuff.
     radius=r*(1+.09*np.clip(t/.115,0,1))
     # Retain the inset sleeve rather than expanding it into the outer wall.
     vr=v-center;vr=vr-np.outer(vr@axis,axis)
     relative=float(b@np.linalg.norm(vr,axis=1))/max(radius,1e-9)
     # Keep distinct nested surfaces separated, including the inset cuff lip
     # and raised patch. Collapsing them onto one cylinder causes z-fighting.
     inset=relative*(1-smooth(.60,.85,relative))+(1+(relative-1)*.20)*smooth(.60,.85,relative)
     target=center+axis*t+radial/length*radius*inset
     q=q*(1-blend)+target*blend
     cn=radial/length-axis*(r*.09/.115);cn/=np.linalg.norm(cn)
     nn=nn*(1-blend)+cn*blend;nn/=np.linalg.norm(nn)
     if blend>.999 and inset==1:errors.append(abs(np.linalg.norm(q-center-axis*np.dot(q-center,axis))-radius))
    # Overall width is an absolute guard, not a reason to enlarge a cuff.
    q[0]=np.clip(q[0],p[:,0].min(),p[:,0].max())
    maxmove=max(maxmove,float(np.linalg.norm(q-old)))
    ix=len(out['points']);out['points'].append(q.tolist());out['normals'].append(nn.tolist());out['uv'].append((b@uv[ui[tri]]).tolist());face.append(ix)
   dst['faces'].append(face)
 out['groups'].append(dst)
out['point_indices']=list(range(len(out['points'])));out['uv_indices']=out['point_indices']
(OUT/'after.json').write_text(json.dumps(out))
report=dict(preview_only=True,source=str(SOURCE/'before.json'),max_move_m=maxmove,circular_section_error_m=max(errors,default=0),triangles_before=sum(len(g['faces']) for g in d['groups']),triangles_after=sum(len(g['faces']) for g in out['groups']),profiles={s:dict(center=c.tolist(),axis=a.tolist(),native_wrist_diameter_m=r*2) for s,(c,a,r) in profiles.items()})
(OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
