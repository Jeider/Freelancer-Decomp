"""Deterministic software previews of assembled CMP geometry, not engine screenshots."""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def render(scene, materials, center, radius, camera, size=650, mode='clay'):
    from li_elite import unit, sample
    forward=unit(np.array(camera,float))
    right=unit(np.cross([0,1,0],forward));up=np.cross(forward,right)
    rotation=np.stack((right,up,forward))
    img=np.full((size,size,3),(24,29,37),dtype=np.uint8)
    depth=np.full((size,size),-np.inf)
    light=unit(np.array([-.55,.65,1.]));half=unit(light+np.array([0,0,1]))
    for group in scene:
        material=materials[group['material']]
        corners=group['corners'].reshape(-1,8)
        pos=(corners[:,:3]-center)@rotation.T
        ns=corners[:,3:6]@rotation.T
        uv=corners[:,6:8]
        texture=np.asarray(material['image'],float) if material['image'] is not None else None
        xy=pos[:,:2]*size*.46/radius
        xy[:,0]+=size/2;xy[:,1]=size/2-xy[:,1]
        for start in range(0,len(corners),3):
            tri=xy[start:start+3];zs=pos[start:start+3,2]
            lo=np.maximum(0,np.floor(tri.min(axis=0)).astype(int))
            hi=np.minimum(size-1,np.ceil(tri.max(axis=0)).astype(int))
            if np.any(lo>hi):continue
            a,b,c=tri
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-8:continue
            xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            w=1-u-v
            z=u*zs[0]+v*zs[1]+w*zs[2]
            region=np.s_[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            # Stable ties for the existing overlapping hull/glass surfaces;
            # software preview does not implement the game's glass blending.
            mask=(u>=-1e-6)&(v>=-1e-6)&(w>=-1e-6)&(z>depth[region]+radius*1e-5)
            if not mask.any():continue
            weights=np.stack((u[mask],v[mask],w[mask]),axis=1)
            normal=unit(weights@ns[start:start+3])
            shade=.22+.78*np.maximum(normal@light,0)
            spec=np.maximum(normal@half,0)**28*18
            colour=np.tile([172.,182.,190.],(len(weights),1))
            if mode=='texture':
                if texture is not None:
                    colour=sample(texture,weights@uv[start:start+3])*material['colour']
                elif 'glass' in material['name'].lower():
                    colour[:]=[58,91,110]
            rgb=np.clip(colour*shade[:,None]+spec[:,None],0,255).astype('uint8')
            if mode=='wire':
                edge_lengths=np.maximum(np.array([np.linalg.norm(b-c),np.linalg.norm(c-a),np.linalg.norm(a-b)]),1e-8)
                distance=weights*abs(den)/edge_lengths
                rgb[distance.min(axis=1)<.55]=[39,74,89]
            img[region][mask]=rgb;depth[region][mask]=z[mask]
    return Image.fromarray(img)


def export_obj(path,scene,materials):
    used=sorted({g['material'] for g in scene})
    with path.with_suffix('.mtl').open('w',encoding='ascii') as f:
        for key in used:
            m=materials[key];f.write(f"newmtl mat_{key:x}\nKd {' '.join(str(float(x)) for x in m['colour'])}\n")
            if m['image'] is not None:
                name=m['texture'].rsplit('.',1)[0]+'.png'
                m['image'].save(path.parent/name)
                f.write('map_Kd '+name+'\n')
    with path.open('w',encoding='ascii') as f:
        f.write('# Construct zero pose. Exported for inspection only.\nmtllib '+path.with_suffix('.mtl').name+'\n')
        base=1
        for i,g in enumerate(scene):
            f.write(f"g mesh_{i}\nusemtl mat_{g['material']:x}\n")
            cs=g['corners'].reshape(-1,8)
            for v in cs:f.write('v %.9g %.9g %.9g\n'%tuple(v[:3]))
            for v in cs:f.write('vt %.9g %.9g\n'%(v[6],1-v[7]))
            for v in cs:f.write('vn %.9g %.9g %.9g\n'%tuple(v[3:6]))
            for j in range(0,len(cs),3):
                f.write('f '+' '.join(f'{k}/{k}/{k}' for k in (base+j,base+j+1,base+j+2))+'\n')
            base+=len(cs)


def write_previews(out,original,medium,mats):
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in original])
    lo,hi=points.min(axis=0),points.max(axis=0)
    center=(lo+hi)/2;radius=np.linalg.norm(points-center,axis=1).max()
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',23)
    small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',17)
    size=720
    rows=[('texture',(1,.9,-1.3)),('clay',(1,.9,-1.3)),('clay',(-1,.6,1.3))]
    sheet=Image.new('RGB',(size*2,len(rows)*(size+32)+80),(24,29,37))
    d=ImageDraw.Draw(sheet)
    for col,(name,scene) in enumerate((('Original',original),('Medium / maximum recess',medium))):
        count=sum(len(g['corners']) for g in scene)
        d.text((col*size+20,12),f'{name} | {count:,} visible triangles',font=font,fill='white')
        for row,(mode,camera) in enumerate(rows):
            y=50+row*(size+32)
            sheet.paste(render(scene,mats,center,radius,camera,size,mode),(col*size,y+25))
            d.text((col*size+20,y),mode+' | same camera and light',font=small,fill=(172,184,196))
    d.text((20,sheet.height-27),'Offline geometry preview / construct zero pose / no normal maps / no game installation',font=small,fill=(172,184,196))
    sheet.save(out/'comparison.jpg',quality=94)
    # Close-up of the upper main hull, using the same crop before and after.
    crop_center=np.array([0.,.5,0.]);crop_radius=4.
    close=Image.new('RGB',(size*2,size*2+110),(24,29,37))
    d=ImageDraw.Draw(close)
    for col,(name,scene) in enumerate((('Original',original),('Medium / maximum recess',medium))):
        d.text((col*size+20,12),name,font=font,fill='white')
        for row,mode in enumerate(('clay','wire')):
            close.paste(render(scene,mats,crop_center,crop_radius,(.35,1.,-.6),size,mode),(col*size,50+row*size))
    d.text((20,close.height-35),'Hull close-up: geometric recesses and mesh. Identical framing; original texture not applied.',font=small,fill=(172,184,196))
    close.save(out/'hull_closeup.jpg',quality=95)
    maps=[m for m in mats.values() if 'mask' in m]
    unique={m['texture']:m for m in maps}
    masks=Image.new('RGB',(512*2,(512+35)*len(unique)),(24,29,37));d=ImageDraw.Draw(masks)
    for row,m in enumerate(unique.values()):
        y=row*547
        d.text((10,y+6),m['texture']+' / bright mask = deeper recess',font=small,fill='white')
        masks.paste(m['image'].resize((512,512)),(0,y+35))
        masks.paste(Image.fromarray(np.rint(m['mask']*255).astype('uint8')).convert('RGB'),(512,y+35))
    masks.save(out/'depth_masks.jpg',quality=93)
    export_obj(out/'original.obj',original,mats)
    export_obj(out/'li_elite_medium.obj',medium,mats)
