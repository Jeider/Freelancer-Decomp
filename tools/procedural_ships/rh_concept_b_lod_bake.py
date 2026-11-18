"""Native geometry texture transfer to distance LOD atlases, not AI image editing.

Nearest surface transfer is constrained to the same CMP component. UV seams in
the simplified meshes are replaced by packed charts; approved LOD0 is read-only.
"""
import json
import sys
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as helper
OUT=helper.OUT
SIZE=2048


def bake():
    data=json.loads((OUT/'blender_scene.json').read_text());lods=json.loads((OUT/'lod_geometry.json').read_text())
    originals={e['file']:e for e in data['objects']};textures={}
    for key,m in data['materials'].items():
        if m['texture']:
            im=bpy.data.images.load(str(OUT/m['texture']));a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a)
            textures[int(key)]=(a.reshape(im.size[1],im.size[0],4)[...,:3].copy(),np.array(m['colour']))
        else:textures[int(key)]=(None,np.array(m['colour']))
    results=[]
    for level,parts in enumerate(lods,1):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        low={}
        for file,gs in parts.items():
            obj,_=helper.mesh_object(dict(groups=gs),originals[file]['name']);low[file]=obj;obj.select_set(True)
        # Deterministic triangle charts avoid Blender's pathological packing time
        # on the preserved cockpit's many tiny islands. Surface transfer restores
        # the source appearance independently of each chart's parameterization.
        total=sum(len(o.data.polygons) for o in low.values())
        grid=int(np.ceil(np.sqrt(total)));cell=SIZE/grid;chart=0
        for obj in low.values():
            for poly in obj.data.polygons:
                assert len(poly.loop_indices)==3
                x=(chart%grid)*cell+4;y=(chart//grid)*cell+4;span=cell-8;chart+=1
                for index,uv in zip(poly.loop_indices,((x,y),(x+span,y),(x,y+span))):
                    obj.data.uv_layers.active.data[index].uv=(uv[0]/SIZE,uv[1]/SIZE)
        print('PACKED TRIANGLE CHARTS',level,total,flush=True)
        canvas=np.zeros((SIZE,SIZE,4),np.float32);filled=np.zeros((SIZE,SIZE),bool)
        transferred=0;errors=[];fallback=0
        for file,obj in low.items():
            source=[(g['material'],np.array(t)) for g in originals[file]['groups'] for t in g['corners']]
            vertices=[Vector(v[:3]) for _,t in source for v in t]
            tree=BVHTree.FromPolygons(vertices,[(i,i+1,i+2) for i in range(0,len(vertices),3)],all_triangles=True)
            me=obj.data;me.calc_loop_triangles();gs=[]
            for tri in me.loop_triangles:
                uv=np.array([me.uv_layers.active.data[i].uv[:] for i in tri.loops])
                points=np.array([helper.C.transposed()@me.vertices[i].co for i in tri.vertices])
                pix=uv*(SIZE-1)
                lo=np.maximum(0,np.floor(pix.min(0)).astype(int));hi=np.minimum(SIZE-1,np.ceil(pix.max(0)).astype(int))
                det=np.linalg.det(np.column_stack((pix[1]-pix[0],pix[2]-pix[0])))
                if abs(det)<1e-10:
                    # Smart projection can flatten tiny edge-on triangles at
                    # folded seams. Give each an isolated chart in a reserved strip.
                    col,row=fallback%64,fallback//64;fallback+=1
                    assert row<3,'Reserved UV repair strip exhausted'
                    uv=np.array([[col*32+3,row*32+3],[col*32+28,row*32+3],[col*32+3,row*32+28]],float)/SIZE
                    pix=uv*(SIZE-1);lo=np.floor(pix.min(0)).astype(int);hi=np.ceil(pix.max(0)).astype(int)
                inverse=np.linalg.inv(np.column_stack((pix[1]-pix[0],pix[2]-pix[0])))
                for y in range(lo[1],hi[1]+1):
                    xs=np.arange(lo[0],hi[0]+1);q=np.column_stack((xs+.5,np.full(len(xs),y+.5)))
                    bc=(q-pix[0])@inverse.T;mask=(bc[:,0]>=-1e-6)&(bc[:,1]>=-1e-6)&(bc.sum(1)<=1+1e-6)
                    for x,(u,v) in zip(xs[mask],bc[mask]):
                        if '--uv-only' in sys.argv:transferred+=1;continue
                        point=points[0]+u*(points[1]-points[0])+v*(points[2]-points[0])
                        nearest,normal,index,distance=tree.find_nearest(Vector(point))
                        mat,original=source[index]
                        tuv=barycentric_transform(nearest,*[Vector(p[:3]) for p in original],*[Vector((p[6],p[7],0)) for p in original])
                        im,colour=textures[mat]
                        if im is not None:
                            h,w=im.shape[:2];xx=(tuv.x%1)*(w-1);yy=(1-tuv.y%1)*(h-1)
                            ix,iy=int(xx),int(yy);ax,ay=xx-ix,yy-iy
                            rgb=(im[iy,ix]*(1-ax)*(1-ay)+im[iy,min(ix+1,w-1)]*ax*(1-ay)+im[min(iy+1,h-1),ix]*(1-ax)*ay+im[min(iy+1,h-1),min(ix+1,w-1)]*ax*ay)*colour
                        else:rgb=colour
                        canvas[y,x,:3]=rgb;canvas[y,x,3]=1;filled[y,x]=True;transferred+=1
                normals=[helper.C.transposed()@me.corner_normals[i].vector for i in tri.loops]
                if '_glass_' in originals[file]['name'].lower():
                    normals=[Vector(v[3:6]) for v in source[tri.index][1]]
                gs.append([[*p,*n,float(t[0]),float(1-t[1])] for p,n,t in zip(points,normals,uv)])
            parts[file]=[dict(material=level,unused=204,corners=gs)]
            print('BAKED',level,originals[file]['name'],flush=True)
        if '--uv-only' in sys.argv:
            assert (OUT/f'rh_b_lod{level}.tga').exists()
            results.append(dict(level=level,pixels=transferred,size=SIZE,repaired_smart_projection_triangles=fallback,method='same-component nearest LOD0 surface with barycentric source UV',padding=12))
            continue
        # Twelve texels of dilation prevent dark gutters in bilinear/mip sampling.
        for _ in range(4):
            pending=~filled;count=np.zeros((SIZE,SIZE),np.float32);summed=np.zeros((SIZE,SIZE,3),np.float32)
            for axis,shift in ((0,1),(0,-1),(1,1),(1,-1)):
                valid=np.roll(filled,shift,axis=axis)
                if axis==0:valid[0 if shift==1 else -1,:]=False
                else:valid[:,0 if shift==1 else -1]=False
                take=pending&valid;count+=take;summed+=np.roll(canvas[...,:3],shift,axis=axis)*take[...,None]
            take=count>0;canvas[take,:3]=summed[take]/count[take,None];filled|=take
        canvas[...,3]=1
        image=bpy.data.images.new(f'rh_b_lod{level}',SIZE,SIZE,alpha=False);image.pixels.foreach_set(canvas.ravel())
        # Never emit RLE TGA: the legacy game path expects uncompressed pixels.
        # Shipping LOD MAT is built separately from PNG as validated DDS/MIPS.
        image.file_format='TARGA_RAW';image.filepath_raw=str(OUT/f'rh_b_lod{level}.tga');image.save()
        image.file_format='PNG';image.filepath_raw=str(OUT/f'rh_b_lod{level}.png');image.save()
        results.append(dict(level=level,pixels=transferred,size=SIZE,repaired_smart_projection_triangles=fallback,method='same-component nearest LOD0 surface; deterministic triangle charts',padding=4))
    (OUT/'lod_baked_geometry.json').write_text(json.dumps(lods,separators=(',',':'),default=float))
    (OUT/'lod_bake.json').write_text(json.dumps(results,indent=2))
    print('READY LOD TEXTURES',flush=True)


if __name__=='__main__':bake()
