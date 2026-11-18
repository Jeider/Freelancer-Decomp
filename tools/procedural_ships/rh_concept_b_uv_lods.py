"""Refresh only UV-affected texels in the existing distant atlas charts."""
import json
import hashlib
import sys
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
OUT=h.OUT;REVIEW=OUT.parent/'uv_refinement_01';SIZE=2048


def pixels(uv):
    uv=np.array(uv);pix=np.column_stack((uv[:,0],1-uv[:,1]))*(SIZE-1)
    lo=np.maximum(0,np.floor(pix.min(0)).astype(int));hi=np.minimum(SIZE-1,np.ceil(pix.max(0)).astype(int))
    inv=np.linalg.inv(np.column_stack((pix[1]-pix[0],pix[2]-pix[0])))
    xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
    xs=xs.ravel();ys=ys.ravel();bc=(np.column_stack((xs+.5,ys+.5))-pix[0])@inv.T
    mask=(bc.min(1)>=-1e-6)&(bc.sum(1)<=1+1e-6)
    return xs[mask],ys[mask],bc[mask]


def main():
    data=json.loads((REVIEW/'lod_refresh_input.json').read_text())
    assert hashlib.sha256((OUT/'rh_concept_b.cmp').read_bytes()).hexdigest()==data['cmp_sha256']
    source=[(g['material'],np.array(t)) for g in data['source']['groups'] for t in g['corners']]
    changed=set(data['changed_source_triangles'])
    tree=BVHTree.FromPolygons([Vector(v[:3]) for _,t in source for v in t],
                            [(i,i+1,i+2) for i in range(0,len(source)*3,3)],all_triangles=True)
    textures={}
    for key,m in data['materials'].items():
        if m['texture']:
            im=bpy.data.images.load(str(OUT/m['texture']),check_existing=True)
            raw=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(raw)
            textures[int(key)]=(raw.reshape(im.size[1],im.size[0],4)[...,:3],np.array(m['colour']))
    reports=[]
    for entry in data['levels']:
        lv=entry['level'];path=OUT/f'rh_b_lod{lv}.png'
        original=bpy.data.images.load(str(path),check_existing=False)
        raw=np.empty(len(original.pixels),np.float32);original.pixels.foreach_get(raw)
        canvas=raw.reshape(SIZE,SIZE,4).copy();baseline=canvas.copy()
        occupied=np.zeros((SIZE,SIZE),bool);touched=np.zeros((SIZE,SIZE),bool)
        for group in entry['atlas_uv']:
            for uv in group:
                x,y,_=pixels(uv);occupied[y,x]=True
        samples=0;changed_charts=0
        triangles=[np.array(t) for g in entry['root_groups'] for t in g['corners']]
        for ti,t in enumerate(triangles):
            x,y,bc=pixels(t[:,6:8]);points=t[0,:3]+bc[:,0,None]*(t[1,:3]-t[0,:3])+bc[:,1,None]*(t[2,:3]-t[0,:3])
            count=0
            for xx,yy,point in zip(x,y,points):
                nearest,_,index,_=tree.find_nearest(Vector(point))
                if index not in changed:continue
                mat,high=source[index]
                tuv=barycentric_transform(nearest,*[Vector(v[:3]) for v in high],*[Vector((v[6],v[7],0)) for v in high])
                image,colour=textures[mat];height,width=image.shape[:2]
                u=(tuv.x%1)*(width-1);v=(1-tuv.y%1)*(height-1)
                ix,iy=int(u),int(v);ax,ay=u-ix,v-iy
                rgb=(image[iy,ix]*(1-ax)*(1-ay)+image[iy,min(ix+1,width-1)]*ax*(1-ay)
                     +image[min(iy+1,height-1),ix]*(1-ax)*ay+image[min(iy+1,height-1),min(ix+1,width-1)]*ax*ay)*colour
                canvas[yy,xx,:3]=rgb;touched[yy,xx]=True;count+=1
            samples+=count;changed_charts+=bool(count)
            if ti%200==0:print('LOD UV TRANSFER',lv,ti,'/',len(triangles),'changed',samples,flush=True)
        assert samples>1000
        # Recompute only affected padding. Other components and unmodified root
        # texels retain exactly their prior colors, including their chart layout.
        filled=occupied.copy()
        for _ in range(4):
            pending=~filled;count=np.zeros((SIZE,SIZE),np.float32);summed=np.zeros((SIZE,SIZE,3),np.float32);affected=np.zeros((SIZE,SIZE),bool)
            for axis,step in ((0,1),(0,-1),(1,1),(1,-1)):
                valid=np.roll(filled,step,axis=axis)
                if axis==0:valid[0 if step==1 else -1,:]=False
                else:valid[:,0 if step==1 else -1]=False
                take=pending&valid;count+=take
                summed+=np.roll(canvas[...,:3],step,axis=axis)*take[...,None]
                affected|=take&np.roll(touched,step,axis=axis)
            take=count>0;canvas[affected,:3]=summed[affected]/count[affected,None]
            filled|=take;touched|=affected
        assert np.array_equal(canvas[~touched],baseline[~touched])
        original.pixels.foreach_set(canvas.ravel());original.file_format='PNG';original.filepath_raw=str(path);original.save()
        reports.append(dict(level=lv,changed_surface_texels=samples,changed_charts=changed_charts,
                            changed_with_padding=int(touched.sum()),untouched_texels_exact=True,
                            png_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print('LOD UV READY',lv,samples,flush=True)
    (REVIEW/'lod_refresh.json').write_text(json.dumps(dict(cmp_sha256=data['cmp_sha256'],levels=reports),indent=2))


if __name__=='__main__':main()
