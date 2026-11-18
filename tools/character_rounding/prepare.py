"""Read-only game inventory and offline Mesh0 shape studies (no game writes)."""
import sys,json,hashlib,io
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/li';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import read_tree,child,blob,arr,triangles
GAME=Path('D:/Games/FL_MOD/DATA/CHARACTERS')
def export(path,dest):
 root=read_tree(path.read_bytes())[1][0];mesh=child(child(root,'MultiLevel'),'Mesh0');g=child(mesh,'Geometry')
 data={k:arr(g,n,t,w).tolist() for k,n,t,w in [('points','Points','<f4',3),('normals','Vertex_normals','<f4',3),('uv','UV0','<f4',2)]}
 data['point_indices']=arr(g,'Point_indices','<u4').ravel().tolist();data['uv_indices']=arr(g,'UV0_indices','<u4').ravel().tolist();data['groups']=[]
 mats=child(root,'Material library');tex=child(root,'Texture library')
 for group in child(mesh,'Face_groups').children:
  if not group.children:continue
  name=blob(group,'Material_name').rstrip(b'\0').decode();mat=next(x for x in mats.children if x.name.lower()==name.lower())
  tn=next((x.blob.rstrip(b'\0').decode() for x in mat.children if x.name=='Dt_name'),None);texture=None
  if tn:
   node=next(x for x in tex.children if x.name.lower()==tn.lower());payload=next(x.blob for x in node.children if x.name in ('MIP0','MIPS'))
   texture=dest/(hashlib.sha256(tn.encode()).hexdigest()[:12]+'.png');Image.open(io.BytesIO(payload)).save(texture)
  data['groups'].append(dict(name=name,texture=str(texture) if texture else None,faces=triangles(group)))
 return data
def improve(data):
 p=np.array(data['points']);n=np.array(data['normals']);pi=np.array(data['point_indices']);ui=np.array(data['uv_indices']);uv=np.array(data['uv'])
 keys=[tuple(np.round(x,6)) for x in p];edge_counts={};edge_sharp=set()
 for group in data['groups']:
  for tri in group['faces']:
   t=pi[tri]
   for a,b in zip(t,np.roll(t,-1)):
    key=tuple(sorted((keys[a],keys[b])));edge_counts[key]=edge_counts.get(key,0)+1
    if n[a]@n[b]<.72:edge_sharp.add(key)
 protected={k for e,c in edge_counts.items() if c==1 for k in e}
 protected|={k for e in edge_sharp for k in e}
 # Closed small rim loops: cuffs can round without turning flat strips into tubes.
 boundary={}
 for (a,b),count in edge_counts.items():
  if count==1:boundary.setdefault(a,set()).add(b);boundary.setdefault(b,set()).add(a)
 rings={};seen=set()
 for start in boundary:
  if start in seen:continue
  stack=[start];component=set()
  while stack:
   k=stack.pop()
   if k in component:continue
   component.add(k);stack.extend(boundary[k]-component)
  seen|=component
  if not 4<=len(component)<=30 or any(len(boundary[k])!=2 for k in component):continue
  pts=np.array(list(component));center=pts.mean(0);_,_,axes=np.linalg.svd(pts-center);axis=axes[-1]
  rad=pts-center-np.outer((pts-center)@axis,axis);radii=np.linalg.norm(rad,axis=1)
  if not (.025<radii.mean()<.085 and radii.min()>radii.max()*.65 and np.max(abs((pts-center)@axis))<.006):continue
  if center[1]>.50 or abs(center[0])<.19:continue
  ring=(center,axis,float(radii.max()),component)
  for k in component:rings[k]=ring
 result=dict(points=[],normals=[],uv=[],point_indices=[],uv_indices=[],groups=[])
 maxmove=0
 barytris=[[[1,0,0],[.5,.5,0],[.5,0,.5]],[[.5,.5,0],[0,1,0],[0,.5,.5]],[[.5,0,.5],[0,.5,.5],[0,0,1]],[[.5,.5,0],[0,.5,.5],[.5,0,.5]]]
 for group in data['groups']:
  dst=dict(group);dst['faces']=[]
  for tri in group['faces']:
   t=pi[tri];v=p[t];ns=n[t];ns=ns/np.maximum(np.linalg.norm(ns,axis=1,keepdims=True),1e-8)
   for sub in barytris:
    face=[]
    for weights in sub:
     b=np.array(weights);old=b@v
     # Planar belt zone, neck/wrist attachments and sole remain native.
     torso=abs(old[0])<.19
     mask=0 if (torso and -.055<old[1]<.16) or old[1]>.52 or old[1]<p[:,1].min()+.025 else 1
     if any(keys[t[i]] in protected for i in range(3) if b[i]>0):mask=0
     projected=np.array([old-ns[i]*np.dot(old-v[i],ns[i]) for i in range(3)])
     delta=(b@projected-old)*.85*mask
     active=[keys[t[i]] for i in range(3) if b[i]>0]
     ring=rings.get(active[0])
     if len(active)==2 and ring is not None and all(k in ring[3] for k in active):
      center,axis,radius,_=ring;radial=old-center-axis*np.dot(old-center,axis)
      if np.linalg.norm(radial)>1e-8:delta=radial*(radius/np.linalg.norm(radial)-1)
     length=np.linalg.norm(delta)
     if length>.006:delta*=.006/length
     pos=np.clip(old+delta,p.min(0),p.max(0));maxmove=max(maxmove,float(np.linalg.norm(pos-old)))
     normal=b@ns;normal/=max(np.linalg.norm(normal),1e-8)
     idx=len(result['points']);result['points'].append(pos.tolist());result['normals'].append(normal.tolist());result['uv'].append((b@uv[ui[tri]]).tolist());face.append(idx)
    dst['faces'].append(face)
  result['groups'].append(dst)
 result['point_indices']=list(range(len(result['points'])));result['uv_indices']=result['point_indices']
 return result,maxmove
records=[]
for kind in ('BODIES','HEADS'):
 for path in sorted((GAME/kind).glob('li_*.dfm')):
  folder=OUT/path.stem;folder.mkdir(exist_ok=True)
  data=export(path,folder);(folder/'before.json').write_text(json.dumps(data))
  if kind=='BODIES' and path.stem!='li_hatcher_body':
   after,delta=improve(data);(folder/'after.json').write_text(json.dumps(after))
  else:after=data;delta=0
  records.append(dict(name=path.stem,kind=kind,source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=sum(len(g['faces']) for g in data['groups']),preview_triangles=sum(len(g['faces']) for g in after['groups']),max_move_m=delta))
  print(path.stem,flush=True)
(OUT/'inventory.json').write_text(json.dumps(records,indent=2))
