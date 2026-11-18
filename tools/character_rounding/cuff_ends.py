"""Round native wrist boundaries inward; preserve the existing upper-body study."""
from all_bodies import *
from collections import Counter,defaultdict

def rims(d):
 p=np.array(d['points']);pi=np.array(d['point_indices']);keys=[tuple(x) for x in p.round(6)];edges=Counter()
 for g in d['groups']:
  for f in g['faces']:
   ids=pi[f]
   for a,b in zip(ids,np.roll(ids,-1)):
    if keys[a]!=keys[b]:edges[tuple(sorted((keys[a],keys[b])))]+=1
 graph=defaultdict(set)
 for (a,b),n in edges.items():
  if n==1:graph[a].add(b);graph[b].add(a)
 result=[];seen=set()
 for start in graph:
  if start in seen:continue
  component=[];stack=[start]
  while stack:
   k=stack.pop()
   if k in seen:continue
   seen.add(k);component.append(k);stack.extend(graph[k]-seen)
  v=np.array(component);center=v.mean(0)
  if not (4<=len(v)<=80 and abs(center[0])>.20 and -.08<center[1]<.08 and np.ptp(v[:,1])<.10):continue
  if any(len(graph[k])!=2 for k in component):continue
  order=[start];prev=None;cur=start
  while True:
   nxt=next(k for k in graph[cur] if k!=prev)
   if nxt==start:break
   order.append(nxt);prev,cur=cur,nxt
  v=np.array(order);center=v.mean(0);_,_,vt=np.linalg.svd(v-center);axis=vt[-1]
  if axis[1]<0:axis=-axis
  if axis[1]<.7:continue
  u=vt[0];w=np.cross(axis,u);xy=np.column_stack(((v-center)@u,(v-center)@w))
  curve=xy.copy()
  for _ in range(4):
   nxt=np.roll(curve,-1,axis=0);curve=np.stack((.75*curve+.25*nxt,.25*curve+.75*nxt),axis=1).reshape(-1,2)
  ang=np.arctan2(curve[:,1],curve[:,0]);order=np.argsort(ang)
  result.append((center,axis,u,w,ang[order],np.linalg.norm(curve[order],axis=1),v))
 # Many retail sleeves are capped, so there is no topological boundary.
 # Fit their terminal ring from native wrist vertices, never the rebuilt mesh.
 for side in (-1,1):
  if any(np.sign(item[0][0])==side for item in result):continue
  v=np.unique(p[(p[:,0]*side>.22)&(p[:,1]>-.055)&(p[:,1]<.025)].round(6),axis=0)
  if not 4<=len(v)<=24:continue
  center=v.mean(0);_,_,vt=np.linalg.svd(v-center);axis=vt[-1]
  if axis[1]<0:axis=-axis
  if axis[1]<.7:continue
  u=vt[0];w=np.cross(axis,u);xy=np.column_stack(((v-center)@u,(v-center)@w));order=np.argsort(np.arctan2(xy[:,1],xy[:,0]));v=v[order];curve=xy[order]
  for _ in range(4):
   nxt=np.roll(curve,-1,axis=0);curve=np.stack((.75*curve+.25*nxt,.25*curve+.75*nxt),axis=1).reshape(-1,2)
  ang=np.arctan2(curve[:,1],curve[:,0]);order=np.argsort(ang);result.append((center,axis,u,w,ang[order],np.linalg.norm(curve[order],axis=1),v))
 return result

def fix(folder):
 r=json.loads((folder/'report.json').read_text())
 if r.get('cuff_end_revision')==1:return
 if r['category'] in ('technical','dense_existing','rigid_robot'):return
 before=json.loads((folder/'before.json').read_text());profiles=rims(before)
 if not profiles:return
 path=OUT/'stage/DATA/CHARACTERS/BODIES'/(folder.name+'.dfm');raw=path.read_bytes();header,roots=read_tree(raw);root=roots[0];mesh=child(child(root,'MultiLevel'),'Mesh0');geo=child(mesh,'Geometry');groups=[g for g in child(mesh,'Face_groups').children if g.children]
 p=arr(geo,'Points','<f4',3).copy();normal=arr(geo,'Vertex_normals','<f4',3).copy();pi=arr(geo,'Point_indices','<u4').ravel();ref=np.zeros_like(p);bp=np.array(before['points']);bpi=np.array(before['point_indices']);sub=subdivisions(2)
 allfaces=[]
 for bg,g in zip(before['groups'],groups):
  f=np.array(triangles(g));assert len(f)==16*len(bg['faces'])
  native=bp[bpi[np.array(bg['faces'])]]
  positions=np.einsum('sij,tjk->tsik',sub,native).reshape(-1,3,3)
  ref[pi[f].ravel()]=positions.reshape(-1,3);allfaces.extend(pi[f])
 old=p.copy();moved=np.zeros(len(p),bool)
 for center,axis,u,w,ang,radius,ring in profiles:
  offset=ref-center;along=offset@axis;side=np.sign(center[0]);mask=(ref[:,0]*side>.20)&(along>-.025)&(along<.19)
  ids=np.flatnonzero(mask);v=offset[ids];t=along[ids];x=v@u;y=v@w;rr=np.hypot(x,y);theta=np.arctan2(y,x)
  target_r=np.interp(theta,ang,radius,period=2*np.pi)
  # Recover the native polygon radius on each ray. The rounded curve is
  # inside its convex hull, never a circle fitted to its diagonal diameter.
  polygon=np.column_stack(((ring-center)@u,(ring-center)@w));native_r=np.full(len(ids),np.inf);direction=np.column_stack((np.cos(theta),np.sin(theta)))
  for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
   edge=b-a;den=direction[:,0]*edge[1]-direction[:,1]*edge[0]
   safe=np.abs(den)>1e-9;distance=np.divide(a[0]*edge[1]-a[1]*edge[0],den,out=np.zeros_like(den),where=safe)
   pos=direction*distance[:,None];fraction=((pos-a)@edge)/max(edge@edge,1e-12)
   valid=safe&(distance>0)&(fraction>=-1e-6)&(fraction<=1+1e-6);native_r[valid]=np.minimum(native_r[valid],distance[valid])
  ratio=np.clip(target_r/np.maximum(native_r,1e-8),.70,1);ratio[~np.isfinite(native_r)]=1
  rounding=(1-smooth(.025,.10,t));undo=(1-smooth(.12,.19,t))
  q=ref[ids]+((ratio-1)*rounding)[:,None]*(x[:,None]*u+y[:,None]*w)
  p[ids]=old[ids]*(1-undo[:,None])+q*undo[:,None];moved[ids]=True
 # Recompute normals at welded UV seams in the corrected region only.
 f=np.array(allfaces);cross=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]);cross[np.einsum('ij,ij->i',cross,normal[f].mean(1))<0]*=-1
 sums=np.zeros_like(p)
 for j in range(3):np.add.at(sums,f[:,j],cross)
 buckets=defaultdict(list)
 for i,pos in enumerate(ref):buckets[tuple(pos.round(6))].append(i)
 for ids in buckets.values():
  if not moved[ids].any():continue
  for i in ids:
   compatible=[j for j in ids if normal[i]@normal[j]>.5];n=sums[compatible].sum(0)
   if np.linalg.norm(n)>1e-10:normal[i]=n/np.linalg.norm(n)
 assert np.isfinite(p).all();assert (p.min(0)>=bp.min(0)-2e-6).all() and (p.max(0)<=bp.max(0)+2e-6).all()
 put(geo,'Points',p.astype('<f4').tobytes());put(geo,'Vertex_normals',normal.astype('<f4').tobytes());data=write_tree(header,roots)
 DataFolder(root=OUT/'stage').sync_data_file('CHARACTERS/BODIES/'+path.name,data);export(root,folder/'after.json')
 r.update(output_sha256=hashlib.sha256(data).hexdigest(),cuff_end_revision=1,cuff_end_loops=len(profiles));(folder/'report.json').write_text(json.dumps(r,indent=2));print(folder.name,len(profiles),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--name');a=ap.parse_args()
 for folder in sorted(OUT.iterdir()):
  if (folder/'report.json').exists() and (not a.name or folder.name==a.name):fix(folder)
