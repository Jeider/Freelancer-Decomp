"""Pack authored tangent normals/roughness and a geometry-restricted eye mask."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/nomad_character/surface'
m=np.load(ROOT/'out/nomad_character/game_body_v3/mesh.npz')
base=np.asarray(Image.open(OUT/'base.jpg').convert('RGB'),dtype=np.float32)/255
normal=np.asarray(Image.open(OUT/'normal.png').convert('RGB'),dtype=np.float32)/255
rough=np.asarray(Image.open(OUT/'roughness.png').convert('L'),dtype=np.float32)/255
h,w=rough.shape
pos=np.full((h,w,3),np.nan,dtype=np.float32)
for face in m['faces']:
    p=m['points'][face]
    if p[:,1].max()<.68:continue
    uv=m['uv'][face]*[w,h]-.5
    lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),[w-1,h-1])
    if np.any(hi<lo):continue
    x,y=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
    a,b,c=uv;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    if abs(den)<1e-7:continue
    u=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/den
    v=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/den
    inside=(u>=0)&(v>=0)&(u+v<=1)
    block=pos[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
    block[inside]=((1-u-v)[...,None]*p[0]+u[...,None]*p[1]+v[...,None]*p[2])[inside]
# Restrict the bright eyes above the magenta cheek plates in model space.
r,g,b=base.transpose(2,0,1)
pink=np.clip((r-g-.035)*9,0,1)*np.clip((b-g-.01)*12,0,1)
candidate=(pos[:,:,1]>.72)&(pos[:,:,1]<.82)&(pos[:,:,2]<-.10)&(np.abs(pos[:,:,0])<.095)
eye=np.clip((g-.12)*6,0,1)*np.clip((b-r+.04)*15,0,1)*candidate
eye*=np.nan_to_num(np.exp(-((pos[:,:,1]-(.756+np.abs(pos[:,:,0])*.55))/.007)**4))
eye*=np.nan_to_num(np.clip((np.abs(pos[:,:,0])-.012)/.008,0,1))
eye*=np.nan_to_num(np.clip((.069-np.abs(pos[:,:,0]))/.009,0,1))
eye=np.clip(eye*1.8,0,1)
selected=pos[eye>.25]
assert len(selected)>30,'No eyes selected'
print('Eye bounds',selected.min(0),selected.max(0),'pixels',len(selected))
# OpenGL +V normal green is inverted for the exported native UV v=1-v.
packed=np.stack((normal[:,:,0],1-normal[:,:,1],np.clip(rough*.70,.22,.68),eye),axis=-1)
dest=ROOT/'DATA_EXTRA/ROOM_MATERIALS/alien_nomad_surface.png'
Image.fromarray(np.uint8(np.clip(packed,0,1)*255+.5),'RGBA').save(dest)
np.save(OUT/'eye_positions.npy',pos)
Image.fromarray(np.uint8(eye*255),'L').save(OUT/'eye_mask.png')
(OUT/'maps.json').write_text(json.dumps(dict(eye_pixels=len(selected),eye_min=selected.min(0).tolist(),eye_max=selected.max(0).tolist(),normal_green_inverted_for_native_uv=True,map=str(dest)),indent=2))
