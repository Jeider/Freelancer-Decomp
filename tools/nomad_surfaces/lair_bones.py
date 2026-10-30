"""Bake bone normal/height/masks from authored UV silhouettes; no diffuse/MAT changes."""
from pathlib import Path
import sys
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from generate import dds, walk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import generate_station_lods as utf

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/nomad_lair_revision'


def mask(index):
    # Coordinates traced against the original 512-pixel material chart, tiled in U.
    # These are material masks, never a screen-space colour classifier.
    im=Image.new('L',(512,512));d=ImageDraw.Draw(im)
    def poly(points,offset=0,mirror=False):
        d.polygon([(x+offset,512-y if mirror else y) for x,y in points],fill=255)
    fork=[(59,0),(73,0),(88,27),(103,72),(118,139),(129,210),(127,239),
          (117,222),(105,173),(90,119),(77,80),(73,142),(69,204),(62,231),
          (56,201),(53,126),(50,81),(32,135),(17,191),(3,238),(-2,216),
          (7,156),(21,97),(38,44)]
    horn=[(7,0),(29,12),(46,39),(53,80),(56,22),(55,0),(72,0),(73,22),
          (77,78),(91,38),(107,10),(123,0),(108,42),(96,91),(85,145),
          (75,196),(64,231),(56,207),(44,152),(31,96),(18,45)]
    for offset in range(-128,640,128):
        if index in (0,1):
            poly(fork,offset)
            if index==1:poly(fork,offset,True)
        elif index==2:
            poly(horn,offset);poly(horn,offset,True)
            poly([(0,81),(128,81),(128,96),(0,96)],offset)
            poly([(0,81),(128,81),(128,96),(0,96)],offset,True)
        elif index==3:
            poly([(0,247),(32,241),(48,231),(63,215),(76,233),(96,244),
                  (128,248),(128,264),(94,268),(76,278),(63,296),(49,276),(30,268),(0,263)],offset)
            poly([(0,448),(23,464),(58,480),(96,491),(128,496),(128,512),(80,505),(38,485),(9,463)],offset)
            for x in (0,64):
                poly([(x-16,351),(x-5,343),(x,332),(x+7,344),(x+16,351),
                      (x+6,359),(x,372),(x-7,360)],offset)
        else:
            # skin02 uses the mirrored fork placement relative to rock_dtl02.
            poly([(x,256+y) for x,y in fork],offset);poly([(x,256-y) for x,y in fork],offset)
    if index in (1,4):
        d.rectangle((0,247,511,264),fill=255)
        d.rectangle((0,0,511,8),fill=255);d.rectangle((0,504,511,511),fill=255)
    return im.filter(ImageFilter.GaussianBlur(.8))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    textures={}
    for library in ('beta_nomad_lair.mat','beta_nomad.mat'):
        _,roots=utf.read_tree((Path('D:/games/FL_MOD/DATA/SOLAR')/library).read_bytes())
        for n in walk(roots):
            if n.name.startswith('lair_'):
                data=next((c.blob for c in n.children if c.name in ('MIPS','MIP0')),None)
                if data:
                    textures[n.name]=Image.open(io.BytesIO(data)).convert('RGB')
                    (OUT/(n.name+'.dds')).write_bytes(data)
    previews=[]
    for i,name in enumerate(['lair_rock_dtl01.tga','lair_rock_dtl02.tga','lair_rock_dtl03.tga',
                             'lair_rock_dtl04.tga','lair_skin02.tga']):
        image=textures[name].resize((512,512),Image.Resampling.LANCZOS)
        m=mask(i);a=np.asarray(m,dtype=np.float32)/255
        # Broad baked shading supplies the curved horn cross-section. Remove the
        # fine albedo grain before differentiating: bone is smooth, not asteroid grit.
        h=np.asarray(image.convert('L').filter(ImageFilter.GaussianBlur(2.2)),dtype=np.float32)/255
        h=h*.65+a*.35
        dx=(np.roll(h,1,1)-np.roll(h,-1,1))*5
        dy=(np.roll(h,1,0)-np.roll(h,-1,0))*5
        n=np.stack([dx,dy,np.ones_like(h)],axis=2);n/=np.linalg.norm(n,axis=2,keepdims=True)
        levels=[]
        while True:
            n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1.e-8)
            levels.append(np.rint(np.stack([n[:,:,0]*.5+.5,n[:,:,1]*.5+.5,h,a],axis=2)*255).clip(0,255).astype(np.uint8))
            if len(h)==1:break
            def down(v):return v.reshape(v.shape[0]//2,2,v.shape[1]//2,2,*v.shape[2:]).mean(axis=(1,3))
            h=down(h);a=down(a);n=down(n)
        (ROOT/f'DATA_EXTRA/TEXTURES/lair_bone{i+1}.dds').write_bytes(dds(levels))
        overlay=np.asarray(image).copy();alpha=np.asarray(m,dtype=np.float32)/255*.5
        overlay=np.uint8(overlay*(1-alpha[:,:,None])+np.array([80,255,120])*alpha[:,:,None])
        Image.fromarray(overlay).save(OUT/f'bone_mask{i+1}.png')
        m.save(OUT/f'bone_mask{i+1}_raw.png')
    print('Baked five 512px normal/height/mask maps with 10 mip levels; original textures unchanged.')

if __name__=='__main__':main()
