"""Generate a periodic relief atlas; extract read-only material references for GPU checks.

RG encode tangent normal XY; B height; A vein mask. This does not modify game MATs.
"""
from pathlib import Path
import io
import json
import struct
import sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/nomad_surfaces'
sys.path.insert(0,str(ROOT/'tools'))
import generate_station_lods as utf

def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.children)

def dds(levels):
    size=levels[0].shape[0]
    header=[124,0x2100F,size,size,size*4,0,len(levels)]+[0]*11
    header += [32,0x41,0,32,0x00ff0000,0x0000ff00,0x000000ff,0xff000000,0x401008,0,0,0,0]
    return b'DDS '+struct.pack('<31I',*header)+b''.join(x[:,:,[2,1,0,3]].tobytes() for x in levels)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    size=1024;y,x=np.mgrid[:size,:size].astype(np.float32)/size
    tau=2*np.pi
    warp=.075*np.sin(tau*(y*3+x))+.035*np.sin(tau*(y*7-x*2))
    folds=(.5+.5*np.cos(tau*(x*9+warp*7+.12*np.sin(tau*y*4))))**2
    crossing=(.5+.5*np.sin(tau*(y*6+.18*np.sin(tau*x*3))))**6
    grain=np.sin(tau*(x*57+y*31))*np.sin(tau*(y*53-x*19))
    height=np.clip(.16+.56*folds+.21*crossing+.035*grain,0,1)
    veins=np.clip((folds-.78)*4,0,1)*(.5+.5*np.sin(tau*y*4))
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*11
    dy=(np.roll(height,-1,0)-np.roll(height,1,0))*11
    normal=np.stack([-dx,-dy,np.ones_like(dx)],axis=2)
    normal/=np.linalg.norm(normal,axis=2,keepdims=True)
    levels=[];h=height;v=veins;n=normal
    while True:
        n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1.e-8)
        rgba=np.stack([n[:,:,0]*.5+.5,n[:,:,1]*.5+.5,h,v],axis=2)
        levels.append(np.rint(rgba*255).clip(0,255).astype(np.uint8))
        if len(h)==1:break
        def down(a):return a.reshape(a.shape[0]//2,2,a.shape[1]//2,2,*a.shape[2:]).mean(axis=(1,3))
        n=down(n);h=down(h);v=down(v)
    dest=ROOT/'DATA_EXTRA/TEXTURES/nomad_layers.dds';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(dds(levels))
    Image.fromarray(levels[0]).save(OUT/'atlas.png')
    Image.fromarray(np.uint8(height*255)).save(OUT/'height.png')
    # Original diffuse and illumination remain separate, including their original mip chains.
    game=Path('D:/games/FL_MOD/DATA')
    wanted={'lair_skin01.tga':'inside.dds','lair_skin01_illum.tga':'illumination.dds',
            'lair_rock01.tga':'outside.dds','dyson_skin05.tga':'dyson.dds'}
    found=[]
    for library in ['SOLAR/beta_nomad.mat','SOLAR/beta_nomad_lair.mat','SOLAR/Solar_mat_dyson.mat']:
        _,tree=utf.read_tree((game/library).read_bytes())
        for node in walk(tree):
            if node.name in wanted:
                data=next((c.blob for c in node.children if c.name in ['MIPS','MIP0']),None)
                if data:
                    (OUT/wanted[node.name]).write_bytes(data)
                    image=Image.open(io.BytesIO(data));image.thumbnail((512,512));image.convert('RGB').save(OUT/(wanted[node.name]+'.png'))
                    if node.name=='dyson_skin05.tga':assert Image.open(io.BytesIO(data)).convert('RGBA').getchannel('A').getextrema()==(255,255), 'Depth prepass requires opaque authored cube texture'
                    found.append(node.name)
    assert set(wanted)<=set(found)
    print(json.dumps({'atlas':str(dest),'size':size,'mips':len(levels),'referenced_textures':found,'dyson_alpha':'opaque'},indent=2))

if __name__=='__main__':main()
