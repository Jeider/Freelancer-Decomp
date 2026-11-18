"""Historical uniform Mesh0 subdivision prototype; superseded by PLAN.txt."""
import sys,json,hashlib,struct,io,copy,argparse
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import read_tree,write_tree,child,blob,arr,put,triangles,faces,DataFolder
from repair_panel_normals import leaves
GAME=Path('D:/Games/FL_MOD');OUT=ROOT/'out/character_rounding/all_bodies';OUT.mkdir(parents=True,exist_ok=True)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def subdivisions(level):
 ts=[np.eye(3)]
 for _ in range(level):
  nxt=[]
  for a,b,c in ts:
   ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2;nxt.extend([[a,ab,ca],[ab,b,bc],[ca,bc,c],[ab,bc,ca]])
  ts=nxt
 return np.asarray(ts)
def export(root,dest):
 mesh=child(child(root,'MultiLevel'),'Mesh0');g=child(mesh,'Geometry')
 d={k:arr(g,n,t,w).tolist() for k,n,t,w in [('points','Points','<f4',3),('normals','Vertex_normals','<f4',3),('uv','UV0','<f4',2)]}
 d['point_indices']=arr(g,'Point_indices','<u4').ravel().tolist();d['uv_indices']=arr(g,'UV0_indices','<u4').ravel().tolist();d['groups']=[]
 mats=child(root,'Material library');textures=child(root,'Texture library')
 for group in child(mesh,'Face_groups').children:
  if not group.children:continue
  name=blob(group,'Material_name').rstrip(b'\0').decode();mat=next(x for x in mats.children if x.name.lower()==name.lower())
  tn=next((x.blob.rstrip(b'\0').decode() for x in mat.children if x.name=='Dt_name'),None);texpath=None
  if tn:
   node=next((x for x in textures.children if x.name.lower()==tn.lower()),None)
   if node:
    payload=next((x.blob for x in node.children if x.name in ('MIP0','MIPS')),None)
    if payload:
     texpath=dest.parent/(hashlib.sha256(tn.encode()).hexdigest()[:12]+'.png')
     if not texpath.exists():Image.open(io.BytesIO(payload)).save(texpath)
  d['groups'].append(dict(name=name,texture=str(texpath) if texpath else None,faces=triangles(group)))
 dest.write_text(json.dumps(d))
def build(path):
 name=path.stem;rel='CHARACTERS/BODIES/'+path.name;folder=OUT/name;folder.mkdir(exist_ok=True)
 raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest();header,roots=read_tree(raw);root=roots[0]
 export(root,folder/'before.json');mesh=child(child(root,'MultiLevel'),'Mesh0');geo=child(mesh,'Geometry');groups=[x for x in child(mesh,'Face_groups').children if x.children]
 p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3);pi=arr(geo,'Point_indices','<u4').ravel();uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
 has_uv1=any(x.name=='UV1' for x in geo.children);uv1=arr(geo,'UV1','<f4',2) if has_uv1 else uv;ui1=arr(geo,'UV1_indices','<u4').ravel() if has_uv1 else ui
 first=arr(geo,'Point_bone_first','<u4').ravel();counts=arr(geo,'Point_bone_count','<u4').ravel();ids=arr(geo,'Bone_id_chain','<u4').ravel();ws=arr(geo,'Bone_weight_chain','<f4').ravel()
 skeleton={}
 for part in child(root,'Cmpnd').children:
  if part.children and any(x.name=='Index' for x in part.children):skeleton[struct.unpack('<I',blob(part,'Index'))[0]]=blob(part,'Object name').rstrip(b'\0').decode()
 skin=[dict(zip(map(int,ids[f:f+c]),map(float,ws[f:f+c]))) for f,c in zip(first,counts)]
 protected_ids={i for i,b in skeleton.items() if any(t in b.lower() for t in ('head','eye','neck'))}
 head_weight=np.array([sum(w for k,w in s.items() if k in protected_ids) for s in skin])
 oldtri=sum(len(triangles(g)) for g in groups)
 technical=name.startswith('benchmark') or name=='worm'
 dense=oldtri>6000
 armor=any(s in name for s in ('elite','guard','scrote','tilton','darcy','deidrich','greunwald','wilham','pirate','orillion')) and not any(s in name for s in ('torture','hurt'))
 robot=name.startswith('robot');alien=name=='alien_nomad_body'
 level=0 if dense or technical else 2
 subs=subdivisions(level)
 # Shared positions at UV seams use the same shaping frame.
 keys=[tuple(np.round(x,6)) for x in p];ns={};neighbors={}
 for i,k in enumerate(keys):ns.setdefault(k,[]).append(n[i])
 for g in groups:
  for tri in triangles(g):
   t=pi[tri]
   for a,b in zip(t,np.roll(t,-1)):
    neighbors.setdefault(keys[a],set()).add(keys[b]);neighbors.setdefault(keys[b],set()).add(keys[a])
 normals={k:np.mean(v,axis=0) for k,v in ns.items()};normals={k:v/max(np.linalg.norm(v),1e-9) for k,v in normals.items()}
 rounded={}
 for k,normal in normals.items():
  old=np.array(k);q=old.copy();near=neighbors.get(k,())
  if .36<old[1]<.60 and abs(old[0])<.31 and near and not (dense or technical or robot):
   delta=(np.mean(list(near),axis=0)-old)*.22;delta*=min(1,.007/max(np.linalg.norm(delta),1e-9));q+=delta
  rounded[k]=q
 profiles={};unique=np.unique(p.round(6),axis=0)
 if armor and not dense:
  for side in (-1,1):
   low=unique[(unique[:,0]*side>.22)&(unique[:,1]>-.035)&(unique[:,1]<.035)]
   upper=unique[(unique[:,0]*side>.20)&(unique[:,1]>.165)&(unique[:,1]<.225)]
   if len(low)<5 or len(upper)<4:continue
   center=low.mean(0);axis=upper.mean(0)-center;axis/=max(np.linalg.norm(axis),1e-9)
   rad=low-center-np.outer((low-center)@axis,axis);radius=max(np.linalg.norm(a-b) for a in rad for b in rad)/2
   if .025<radius<.085 and axis[1]>.75:profiles[side]=(center,axis,radius)
 # Hatcher's accepted smooth body only needs the flat diagonal belt correction.
 belt=None
 if name=='li_hatcher_body':
  ref=json.loads((ROOT/'out/character_rounding/li/hatcher_belt_study/before.json').read_text())
  group=next(g for g in ref['groups'] if g['name']=='hatcher_body_4');ix=np.unique(np.array(group['faces']).ravel());rp=np.array(ref['points'])[np.array(ref['point_indices'])[ix]];ru=np.array(ref['uv'])[np.array(ref['uv_indices'])[ix]];sel=rp[:,2]<-.095
  yf=np.linalg.lstsq(np.column_stack((rp[sel,0],ru[sel,0],np.ones(sel.sum()))),rp[sel,1],rcond=None)[0];zf=np.polyfit(rp[sel,0],rp[sel,2],2);belt=(yf,zf)
 outputp=[];outputn=[];outputuv=[];outputuv1=[];outputskin=[];lookup={};reference=[];allfaces=[];maxmove=0
 for group in groups:
  mat=blob(group,'Material_name').rstrip(b'\0').decode();newfaces=[]
  for tri in triangles(group):
   t=np.array(tri);v=p[pi[t]];nv=n[pi[t]];vn=np.array([normals[keys[i]] for i in pi[t]]);rv=np.array([rounded[keys[i]] for i in pi[t]])
   for sub in subs:
    f=[]
    for b in sub:
     old=b@v;normal=b@nv;normal/=max(np.linalg.norm(normal),1e-9);q=old.copy();tex=b@uv[ui[t]];tex1=b@uv1[ui1[t]]
     protected=float(b@head_weight[pi[t]])>.001
     if not protected and not technical and not dense and old[1]>.20:
      lin=b@rv;proj=np.array([lin-vn[i]*np.dot(lin-rv[i],vn[i]) for i in range(3)])
      strength=smooth(.22,.36,old[1])*(1-smooth(.57,.62,old[1]))*(.45 if robot else 1)
      q=lin+(b@proj-lin)*strength;delta=q-old;q=old+delta*min(1,.012/max(np.linalg.norm(delta),1e-9))
     side=1 if old[0]>0 else -1
     if side in profiles and not protected:
      center,axis,r=profiles[side];along=np.dot(old-center,axis);radial=old-center-axis*along;length=np.linalg.norm(radial)
      blend=smooth(.20,.24,abs(old[0]))*(1-smooth(.115,.18,along))*smooth(-.045,-.015,along)
      if length>.012 and blend>0:
       radius=r*(1+.08*np.clip(along/.115,0,1));vr=v-center;vr-=np.outer(vr@axis,axis)
       relative=float(b@np.linalg.norm(vr,axis=1))/max(radius,1e-9)
       # Preserve raised patches at their native radial height; blend only the
       # base wall toward a circular section. Distinct inset layers stay apart.
       shell=1+.22*min(relative-1,0)+max(relative-1,0)
       ratio=relative*(1-smooth(.60,.85,relative))+shell*smooth(.60,.85,relative)
       target=center+axis*along+radial/length*radius*ratio;q=q*(1-blend)+target*blend
     if belt and mat=='hatcher_body_4':
      yf,zf=belt;blend=float(smooth(.085,.11,-old[2]));q[1]=(1-blend)*q[1]+blend*np.dot([old[0],tex[0],1],yf);q[2]=(1-blend)*q[2]+blend*np.polyval(zf,old[0])
     q=np.clip(q,p.min(0),p.max(0));maxmove=max(maxmove,float(np.linalg.norm(q-old)))
     influence={}
     for j,k in enumerate(pi[t]):
      for bone,w in skin[k].items():influence[bone]=influence.get(bone,0)+float(b[j])*w
     influence=dict(sorted(((k,w) for k,w in influence.items() if w>1e-8),key=lambda item:(-item[1],item[0]))[:4]);total=sum(influence.values());influence={k:w/total for k,w in influence.items()}
     # Native deformation supports at most four influences per vertex.
     k=tuple(np.round(q,7))+tuple(np.round(normal,6))+tuple(np.round(tex,7))+tuple(np.round(tex1,7))+tuple(sorted((i,round(w,7)) for i,w in influence.items()))
     if k not in lookup:
      lookup[k]=len(outputp);outputp.append(q);outputn.append(normal);outputuv.append(tex);outputuv1.append(tex1);outputskin.append(influence);reference.append(old)
     f.append(lookup[k])
    newfaces.append(f);allfaces.append(f)
  faces(group,newfaces)
 op=np.array(outputp);on=np.array(outputn);ref=np.array(reference);ff=np.array(allfaces);sums=np.zeros_like(op)
 a,b,c=op[ff[:,0]],op[ff[:,1]],op[ff[:,2]];cross=np.cross(b-a,c-a)
 sign=np.einsum('ij,ij->i',cross,on[ff].mean(1));cross[sign<0]*=-1
 for j in range(3):np.add.at(sums,ff[:,j],cross)
 # Recompute only moved regions; native shading elsewhere remains intact.
 buckets={}
 for i,pos in enumerate(op):buckets.setdefault(tuple(np.round(pos,6)),[]).append(i)
 originaln=on.copy()
 for copies in buckets.values():
  if not np.any(np.linalg.norm(op[copies]-ref[copies],axis=1)>1e-7):continue
  for i in copies:
   compatible=[j for j in copies if originaln[i]@originaln[j]>.75];nn=sums[compatible].sum(0)
   if np.linalg.norm(nn)>1e-10:on[i]=nn/np.linalg.norm(nn)
 assert len(op)<65536,(name,len(op))
 assert np.isfinite(op).all() and np.isfinite(on).all()
 assert (op.min(0)>=p.min(0)-1e-7).all() and (op.max(0)<=p.max(0)+1e-7).all()
 identity=np.arange(len(op),dtype='<u4')
 for nm,val,typ in [('Points',op,'<f4'),('Vertex_normals',on,'<f4'),('Point_indices',identity,'<u4'),('UV0',outputuv,'<f4'),('UV0_indices',identity,'<u4')]:put(geo,nm,np.asarray(val,dtype=typ).tobytes())
 if has_uv1:put(geo,'UV1',np.asarray(outputuv1,dtype='<f4').tobytes());put(geo,'UV1_indices',identity.tobytes())
 starts=[];cc=[];bb=[];ww=[]
 for s in outputskin:starts.append(len(bb));cc.append(len(s));bb.extend(s);ww.extend(s.values())
 for nm,val,typ in [('Point_bone_first',starts,'<u4'),('Point_bone_count',cc,'<u4'),('Bone_id_chain',bb,'<u4'),('Bone_weight_chain',ww,'<f4')]:put(geo,nm,np.asarray(val,dtype=typ).tobytes())
 data=write_tree(header,roots) if maxmove>1e-7 else raw
 old={k:v for k,_,v in leaves(raw)[1]};new={k:v for k,_,v in leaves(data)[1]};changed=[k for k in set(old)|set(new) if old.get(k)!=new.get(k)]
 assert all('/MultiLevel/Mesh0/' in k for k in changed)
 DataFolder(root=OUT/'stage').sync_data_file(rel,data)
 export(read_tree(data)[1][0],folder/'after.json')
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
 report=dict(version=2,name=name,source=str(path),source_sha256=sha,output_sha256=hashlib.sha256(data).hexdigest(),changed=bool(changed),only_mesh0=True,other_lods_skeleton_materials_unchanged=True,triangles_before=oldtri,triangles_after=len(ff) if changed else oldtri,points=len(op) if changed else len(p),max_move_m=maxmove,cuff_profiles=len(profiles),category='technical' if technical else 'dense_existing' if dense else 'rigid_robot' if robot else 'armored' if armor else 'tailored',animation_validated=False)
 (folder/'report.json').write_text(json.dumps(report,indent=2));print(name,report['category'],oldtri,'->',report['triangles_after'],'cuffs',len(profiles),flush=True)
 return report
def legacy_main():
 """Historical CLI retained for reference; not the active contour workflow."""
 ap=argparse.ArgumentParser();ap.add_argument('--name');ap.add_argument('--resume',action='store_true');ap.add_argument('--partition',type=int);args=ap.parse_args();reports=[];errors=[]
 for index,p in enumerate(sorted((GAME/'DATA/CHARACTERS/BODIES').glob('*.dfm'))):
  if args.partition is not None and index%2!=args.partition:continue
  if args.name and p.stem!=args.name:continue
  try:
   prev=OUT/p.stem/'report.json'
   if args.resume and prev.exists():
    cached=json.loads(prev.read_text())
    if cached.get('version')==2 or cached['category']!='armored':reports.append(cached);continue
   reports.append(build(p))
  except Exception as e:errors.append(dict(name=p.stem,error=repr(e)));print('ERROR',p.stem,repr(e),flush=True)
 suffix='' if args.partition is None else '_'+str(args.partition)
 (OUT/('inventory'+suffix+'.json')).write_text(json.dumps(reports,indent=2));(OUT/('errors'+suffix+'.json')).write_text(json.dumps(errors,indent=2))
 print('Completed',len(reports),'errors',len(errors),flush=True)

if __name__=='__main__':
 raise SystemExit('Uniform body subdivision is retired. See tools/character_rounding/PLAN.txt: local contours, <= 2000 triangles, exclusions in policy.json.')
