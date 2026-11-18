"""Export the installed CMP's parts, UV sets and materials for offline review."""
from audit import *
import numpy as np,io
from PIL import Image
def c(n,k):return utf.child(n,k)
def s(n,k):return c(n,k).blob.rstrip(b'\0').decode()
texdir=OUT/'textures';texdir.mkdir(exist_ok=True);textures={}
for t in c(root,'Texture library').children:
 payload=next((x.blob for x in t.children if x.name in ('MIPS','MIP0')),None)
 if payload:
  im=Image.open(io.BytesIO(payload));dest=texdir/(hashlib.sha256(t.name.encode()).hexdigest()[:12]+'.png');im.save(dest)
  textures[t.name.lower()]=dict(path=str(dest),size=im.size)
mats={}
for m in c(root,'Material library').children:
 if not m.children:continue
 props={}
 for x in m.children:
  if x.name.endswith('_name') or x.name=='Type':props[x.name]=x.blob.rstrip(b'\0').decode()
  elif len(x.blob) in (4,12,16):props[x.name]=list(struct.unpack('<'+'f'*(len(x.blob)//4),x.blob))
 props['name']=m.name;props['textures']={k:textures.get(v.lower()) for k,v in props.items() if k.endswith('_name')}
 mats[str(utf.crc(m.name))]=props
compound=c(root,'Cmpnd');transforms={'Root':(np.eye(3),np.zeros(3))};joints=[]
for kind in c(compound,'Cons').children:
 size={'Fix':176,'Rev':208}.get(kind.name)
 if not size:raise ValueError(kind.name)
 for off in range(0,len(kind.blob),size):
  b=kind.blob[off:off+size];parent=b[:64].split(b'\0')[0].decode();name=b[64:128].split(b'\0')[0].decode();pos=np.array(struct.unpack_from('<3f',b,128));rot=np.array(struct.unpack_from('<9f',b,140 if size==176 else 152)).reshape(3,3)
  joints.append(dict(parent=parent,name=name,kind=kind.name,pos=pos.tolist(),rot=rot.tolist(),offset=list(struct.unpack_from('<3f',b,140)) if size==208 else [0,0,0]))
pending=list(joints)
while pending:
 progress=False
 for j in pending[:]:
  if j['parent'] not in transforms:continue
  pm,pp=transforms[j['parent']];transforms[j['name']]=(np.array(j['rot'])@pm,np.array(j['pos'])@pm+pp);pending.remove(j);progress=True
 assert progress,'Unresolved compound transforms'
lib={utf.crc(n.name):c(n,'VMeshData').blob for n in c(root,'VMeshLibrary').children};batches=[]
for part in compound.children:
 if part.name=='Cons':continue
 name=s(part,'Object name');filename=s(part,'File name');node=c(root,filename)
 try:ref=c(c(node,'VMeshPart'),'VMeshRef').blob
 except StopIteration:ref=c(c(c(c(node,'MultiLevel'),'Level0'),'VMeshPart'),'VMeshRef').blob
 key=struct.unpack_from('<I',ref,4)[0];sv,nv,si,ni,sg,ng=struct.unpack_from('<6H',ref,8);blob=lib[key]
 _,_,groups,indices,fvf,vertices=struct.unpack_from('<II4H',blob);assert fvf in (0x112,0x212)
 stride=8 if fvf==0x112 else 10;ib=16+12*groups;vb=ib+2*indices;v=np.frombuffer(blob,dtype='<f4',count=vertices*stride,offset=vb).reshape(-1,stride);idx=np.frombuffer(blob,dtype='<u2',count=indices,offset=ib)
 mat,pos=transforms.get(name,(np.eye(3),np.zeros(3)));offset=si
 for g in range(sg,sg+ng):
  material,start,_,count,_=struct.unpack_from('<I4H',blob,16+12*g);ix=idx[offset:offset+count].astype('int32')+start+sv;offset+=count;vv=v[ix].copy();vv[:,:3]=vv[:,:3]@mat+pos;vv[:,3:6]=vv[:,3:6]@mat
  batches.append(dict(part=name,material=str(material),vertices=vv.tolist(),stride=stride,triangles=count//3))
result=dict(materials=mats,batches=batches,joints=joints,textures=textures)
(OUT/'scene_mesh.json').write_text(json.dumps(result));print('Exported',len(batches),'batches',sum(b['triangles'] for b in batches),'triangles',len(textures),'textures')
(OUT/'materials.json').write_text(json.dumps(mats,indent=2))
