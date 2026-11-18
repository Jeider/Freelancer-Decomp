"""Restore native tailoring planes and neckline joins, retaining wrist fixes."""
from all_bodies import *

def restore(folder):
 report=json.loads((folder/'report.json').read_text());name=folder.name
 if report.get('tailoring_revision')==2:return
 previous=report.get('tailoring_revision',0)
 if report['category'] in ('technical','dense_existing'):return
 tailored=report['category']=='tailored'
 feminine=any(t in name for t in ('female','kym','darcy','kaitlyn','karina'))
 flat_armor=name in ('rh_male_elite_body','rh_female_elite_body','rh_male_guard_body','rh_female_guard_body')
 shirt=name=='br_male_elite_body'
 before=json.loads((folder/'before.json').read_text());bp=np.array(before['points']);bn=np.array(before['normals']);bpi=np.array(before['point_indices']);sub=subdivisions(2)
 path=OUT/'stage/DATA/CHARACTERS/BODIES'/(name+'.dfm');raw=path.read_bytes();header,roots=read_tree(raw);root=roots[0];mesh=child(child(root,'MultiLevel'),'Mesh0');geo=child(mesh,'Geometry');groups=[g for g in child(mesh,'Face_groups').children if g.children]
 p=arr(geo,'Points','<f4',3).copy();n=arr(geo,'Vertex_normals','<f4',3).copy();pi=arr(geo,'Point_indices','<u4').ravel();ref=np.zeros_like(p);rn=np.zeros_like(n)
 for bg,g in zip(before['groups'],groups):
  f=np.array(triangles(g));assert len(f)==16*len(bg['faces']);native=bp[bpi[np.array(bg['faces'])]];nn=bn[bpi[np.array(bg['faces'])]]
  ref[pi[f].ravel()]=np.einsum('sij,tjk->tsik',sub,native).reshape(-1,3)
  rn[pi[f].ravel()]=np.einsum('sij,tjk->tsik',sub,nn).reshape(-1,3)
 rn/=np.maximum(np.linalg.norm(rn,axis=1)[:,None],1e-9)
 blend=np.zeros(len(p))
 if not previous and (tailored or flat_armor):blend=np.maximum(blend,smooth(.26,.34,ref[:,1]))
 if not previous and feminine:
  # Both sides of a neckline/skin join retain the exact original surface.
  blend=np.maximum(blend,smooth(.24,.31,ref[:,1])*(1-smooth(.20,.26,np.abs(ref[:,0]))))
 if not previous and shirt:
  blend=np.maximum(blend,smooth(.14,.21,ref[:,1])*(1-smooth(.105,.18,np.abs(ref[:,0]))))
 # Shoulder silhouettes, including armor, must follow the native design.
 # Original protruding plates stay protruding; no new puffy cap is introduced.
 blend=np.maximum(blend,smooth(.36,.43,ref[:,1])*smooth(.11,.17,np.abs(ref[:,0])))
 oldp=p.copy();oldn=n.copy();p=p*(1-blend[:,None])+ref*blend[:,None];n=n*(1-blend[:,None])+rn*blend[:,None];n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9)
 # Even float renormalization must not touch the accepted cuffs.
 n[blend==0]=oldn[blend==0];p[blend==0]=oldp[blend==0]
 assert np.array_equal(p[ref[:,1]<.14],oldp[ref[:,1]<.14])
 assert np.array_equal(n[ref[:,1]<.14],oldn[ref[:,1]<.14])
 if not np.any(blend>0):return
 assert np.max(np.abs(p[blend==1]-ref[blend==1]),initial=0)==0
 put(geo,'Points',p.astype('<f4').tobytes());put(geo,'Vertex_normals',n.astype('<f4').tobytes());data=write_tree(header,roots)
 old={k:v for k,_,v in leaves(raw)[1]};new={k:v for k,_,v in leaves(data)[1]};assert all(k.endswith(('/Points','/Vertex_normals')) and '/Mesh0/Geometry/' in k for k in old if old[k]!=new[k])
 DataFolder(root=OUT/'stage').sync_data_file('CHARACTERS/BODIES/'+path.name,data);export(root,folder/'after.json')
 report.update(output_sha256=hashlib.sha256(data).hexdigest(),tailoring_revision=2,tailoring_native_vertices=int((blend==1).sum()),cuffs_preserved=True)
 (folder/'report.json').write_text(json.dumps(report,indent=2));print(name,int((blend==1).sum()),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--name');a=ap.parse_args()
 for folder in sorted(OUT.iterdir()):
  if (folder/'report.json').exists() and (not a.name or folder.name==a.name):restore(folder)
