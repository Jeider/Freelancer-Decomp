"""Read-only comparison of the installed HUD panel materials and mesh references."""
import hashlib
import io
import json
from pathlib import Path
import struct
import numpy as np
from generate_station_lods import read_tree, child, crc
from PIL import Image, ImageStat

GAME=Path('D:/games/FL_MOD/DATA/INTERFACE')
OUT=Path(__file__).resolve().parents[1]/'src/obj/hud_pattern_audit'

def walk(node):
    yield node
    for n in node.children:yield from walk(n)

def value(n):
    if n.blob is None:return {c.name:value(c) for c in n.children}
    b=n.blob
    if n.name in ('Dc','Ec','Oc'):return struct.unpack('<'+'f'*(len(b)//4),b)
    if n.name in ('Type','Dt_name','Et_name','Ot_name','File name','Object name'):return b.rstrip(b'\0').decode('ascii')
    if len(b)<=64:return b.hex()
    return {'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    vms=read_tree((GAME/'interface.generic.vms').read_bytes())[1][0]
    meshes={crc(n.name):child(n,'VMeshData').blob for n in child(vms,'VMeshLibrary').children}
    result={}
    for name in ('hud_target2.cmp','HUD_target.cmp','HUD_shipinfo.cmp'):
        root=read_tree((GAME/'HUD'/name).read_bytes())[1][0]
        mats=child(root,'Material library')
        material_names={crc(n.name):n.name for n in mats.children if n.children}
        data={n.name:value(n) for n in root.children if n.name in ('Material library','MaterialAnim','Texture library','Cmpnd')}
        refs=[]
        for model in root.children:
            for n in walk(model):
                if n.name!='VMeshRef':continue
                mesh_id,base,count,first_index,_,first_group,groups=struct.unpack_from('<I6H',n.blob,4)
                b=meshes[mesh_id]
                _,_,ng,ni,fvf,nv=struct.unpack_from('<II4H',b)
                ib=16+12*ng;vb=ib+2*ni;cursor=first_index
                groups_out=[]
                for group in range(first_group,first_group+groups):
                    mat,lo,hi,indices,_=struct.unpack_from('<I4H',b,16+12*group)
                    groups_out.append({'material':material_names.get(mat,hex(mat)),'triangles':indices//3})
                    if material_names.get(mat,'').startswith('HUD_NN_tray'):
                        print('BACKGROUND FVF',name,hex(fvf))
                        stride=12+(12 if fvf&16 else 0)+(4 if fvf&64 else 0)+(4 if fvf&128 else 0)+8*((fvf>>8)&15)
                        color_off=12+(12 if fvf&16 else 0)
                        ix=np.array(struct.unpack_from('<'+'H'*indices,b,ib+2*cursor))+base+lo
                        verts=np.array([(*struct.unpack_from('<3f',b,vb+stride*int(i)),
                            *(struct.unpack_from('<3f',b,vb+stride*int(i)+12) if fvf&16 else (0,0,0)),
                            *struct.unpack_from('<2f',b,vb+stride*int(i)+stride-8)) for i in ix])
                        if fvf&64:
                            colors=[struct.unpack_from('<I',b,vb+stride*int(i)+color_off)[0] for i in ix]
                            data['pattern_vertex_colors']=sorted({hex(c) for c in colors})
                            print('VERTEX COLORS',data['pattern_vertex_colors'])
                        xy=verts[:,:2];mn=xy.min(0);mx=xy.max(0)
                        xx,yy=np.meshgrid(np.linspace(mn[0],mx[0],103)[1:-1],np.linspace(mn[1],mx[1],103)[1:-1])
                        counts=np.zeros(xx.shape,dtype=int);signs=[]
                        for tri in verts.reshape(-1,3,8):
                            a,c,d=tri[:,:2];den=(c[1]-d[1])*(a[0]-d[0])+(d[0]-c[0])*(a[1]-d[1])
                            signs.append(float(den))
                            if abs(den)<1e-14:continue
                            u=((c[1]-d[1])*(xx-d[0])+(d[0]-c[0])*(yy-d[1]))/den
                            v=((d[1]-a[1])*(xx-d[0])+(a[0]-d[0])*(yy-d[1]))/den
                            counts+=((u>1e-6)&(v>1e-6)&(u+v<1-1e-6))
                        data['pattern_geometry']={'range_min':verts.min(0).tolist(),'range_max':verts.max(0).tolist(),
                            'coverage':dict(zip(*[v.tolist() for v in np.unique(counts,return_counts=True)])),
                            'winding':signs}
                        print('GEOMETRY',data['pattern_geometry'])
                    cursor+=indices
                refs.append({'model':model.name,'groups':groups_out})
        data['meshes']=refs;result[name]=data
        blob=child(child(child(root,'Texture library'),'backgroundpattern.tga'),'MIP0').blob
        tex=Image.open(io.BytesIO(blob)).convert('RGBA')
        tex.save(OUT/(name+'.pattern.png'))
        scan=Image.open(io.BytesIO(child(child(child(root,'Texture library'),'refreshtest2.tga'),'MIP0').blob)).convert('RGBA')
        scan.save(OUT/(name+'.scanline.png'))
        print('SCANLINE',scan.size,scan.getextrema(),ImageStat.Stat(scan).mean)
        data['pattern_pixels']={'size':tex.size,'range':tex.getextrema(),'mean':ImageStat.Stat(tex).mean}
        print('PATTERN',data['pattern_pixels'])
        print(name,json.dumps({k:v for k,v in data.items() if k in ('Material library','meshes')},indent=2))
    (OUT/'comparison.json').write_text(json.dumps(result,indent=2))

if __name__=='__main__':main()
