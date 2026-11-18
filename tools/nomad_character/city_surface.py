"""Inventory N_CITY material/texture pairs and build isolated shader sidecars."""
import sys,json,io,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import read_tree,blob
OUT=ROOT/'out/nomad_character/city';OUT.mkdir(parents=True,exist_ok=True)
materials={};textures={};sources={}
def walk(node,path):
 if node.name.lower()=='material library':
  for m in node.children:
   props={c.name:c.blob for c in m.children}
   materials[m.name]={k:v.rstrip(b'\0').decode('ascii',errors='replace') for k,v in props.items() if k in ('Type','Dt_name')}
   sources.setdefault(m.name,[]).append(path.name)
 if node.name.lower()=='texture library':
  for t in node.children:
   for c in t.children:
    if c.name in ('MIPS','MIP0'):textures[t.name]=c.blob
 for c in node.children:walk(c,path)
for p in Path('D:/Games/FL_MOD/DATA/BASES/N_CITY').iterdir():
 if p.is_file():
  for n in read_tree(p.read_bytes())[1]:walk(n,p)
(OUT/'inventory.json').write_text(json.dumps(dict(materials=materials,sources=sources,textures=list(textures)),indent=2))
print(json.dumps(materials,indent=2))
import numpy as np
from PIL import Image,ImageFilter
for name in ('the_n_city','n_city2'):
 tex=materials[name]['Dt_name'];im=Image.open(io.BytesIO(textures[tex])).convert('RGB')
 im.thumbnail((2048,2048))
 # Bounded texture-derived relief; broad painted lighting is removed first.
 grey=im.convert('L');fine=np.asarray(grey.filter(ImageFilter.GaussianBlur(1.2)),dtype=np.float32)/255
 broad=np.asarray(grey.filter(ImageFilter.GaussianBlur(5)),dtype=np.float32)/255
 height=fine-broad;dy,dx=np.gradient(height)
 nx=-dx*3;ny=-dy*3;nz=np.ones_like(nx);length=np.sqrt(nx*nx+ny*ny+nz*nz)
 rough=np.clip(.36+np.abs(height)*.35,.32,.48)
 packed=np.stack((nx/length*.5+.5,ny/length*.5+.5,rough,np.zeros_like(nx)),axis=-1)
 dest=ROOT/'DATA_EXTRA/ROOM_MATERIALS'/('nomad_city_'+name+'.png')
 Image.fromarray(np.uint8(np.clip(packed,0,1)*255+.5),'RGBA').save(dest)
 print('Generated',dest.name,im.size)
