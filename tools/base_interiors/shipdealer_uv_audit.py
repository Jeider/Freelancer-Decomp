"""Read-only native shipdealer audit and diagnostic UV projections."""
import io,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from native_common import ROOT,GAME,read_tree,child,crc,text,sha,leaves,get_parts,dump
from rheinland_audit import transforms

OUT=ROOT/'out/base_interiors/rh_biz_01_base/shipdealer/uv_audit'
LIVE=GAME/'DATA/BASES/RHEINLAND/rh_bizmark_shipdealer.cmp'
ORIGINAL=Path('D:/Games/FL_ND/FL_ND/DATA/BASES/RHEINLAND/rh_bizmark_shipdealer.cmp')


def render(groups,camera,fov,name):
    w,h=792,426
    image=np.zeros((h,w,3),np.uint8);depth=np.full((h,w),np.inf)
    ids=np.full((h,w),-1,np.int16)
    s=camera['spatialprops'];p=np.array(list(s['pos'].values()))
    r=np.array([list(x.values()) for x in s['orient'].values()])
    scale=w/(2*math.tan(math.radians(fov/2)))
    for gi,g in enumerate(groups):
        if g['image'] is None or 'flare' in g['name']:continue
        tex=g['image'];th,tw=tex.shape[:2]
        for t in g['corners']:
            normal=t[:,3:6].mean(0)
            if np.dot(normal,p-t[:,:3].mean(0))<0:continue
            c=(t[:,:3]-p)@r.T;z=-c[:,2]
            if z.min()<.1:continue
            xy=np.c_[w/2+c[:,0]/z*scale,h/2-c[:,1]/z*scale]
            lo=np.maximum(np.floor(xy.min(0)).astype(int),0)
            hi=np.minimum(np.ceil(xy.max(0)).astype(int),[w-1,h-1])
            if np.any(lo>hi):continue
            matrix=np.vstack((xy.T,np.ones(3)))
            if abs(np.linalg.det(matrix))<1e-8:continue
            yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            weights=np.c_[xx.ravel()+.5,yy.ravel()+.5,np.ones(xx.size)]@np.linalg.inv(matrix).T
            inside=weights.min(1)>=-1e-6
            if not inside.any():continue
            x=xx.ravel()[inside];y=yy.ravel()[inside];q=weights[inside]/z
            d=1/q.sum(1);front=d<depth[y,x]
            x=x[front];y=y[front];d=d[front];q=q[front]*d[:,None]
            if not len(x):continue
            uv=q@t[:,6:8];tx=(np.mod(uv[:,0],1)*(tw-1)).astype(int);ty=(np.mod(uv[:,1],1)*(th-1)).astype(int)
            colour=tex[ty,tx,:3]
            shade=.65+.35*abs(np.dot(normal,r[2]))
            image[y,x]=np.clip(colour*shade,0,255).astype(np.uint8)
            depth[y,x]=d;ids[y,x]=gi
    Image.fromarray(image).save(OUT/(name+'.png'))
    np.savez_compressed(OUT/(name+'_ids.npz'),groups=ids)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=LIVE.read_bytes();old=ORIGINAL.read_bytes()
    root=read_tree(raw)[1][0];original=read_tree(old)[1][0]
    same=dict(leaves(child(root,'VMeshLibrary')))==dict(leaves(child(original,'VMeshLibrary')))
    tex={}
    for n in child(root,'Texture library').children:
        data=next((x.blob for x in n.children if x.name in ('MIPS','MIP0')),None)
        if data:tex[n.name.lower()]=np.array(Image.open(io.BytesIO(data)).convert('RGB'))
    mats={crc(m.name):m for m in child(root,'Material library').children if m.children}
    trans,_=transforms(root);groups=[];records=[]
    for part in get_parts(root):
        r,p=trans[part['name']]
        for i,g in enumerate(part['groups']):
            m=mats[g['material']];props={n.name:text(n.blob) for n in m.children if n.name=='Type' or n.name.endswith('_name')}
            t=g['corners'].copy();t[:,:,:3]=t[:,:,:3]@r+p;t[:,:,3:6]=t[:,:,3:6]@r
            groups.append(dict(name=m.name,image=tex.get(props.get('Dt_name','').lower()),corners=t))
            records.append(dict(index=len(groups)-1,part=part['name'],group=i,material=m.name,triangles=len(t),
                properties=props,finite_uv0=bool(np.isfinite(t[:,:,6:8]).all()),finite_uv1=bool(np.isfinite(t[:,:,8:]).all())))
    dump(OUT/'audit.json',dict(source=str(LIVE),source_sha256=sha(raw),original_sha256=sha(old),
        geometry_and_uv_bytes_identical_to_original=same,groups=records,game_files_changed=False))
    sheet=Image.new('RGB',(1000,math.ceil(len(groups)/5)*160),(20,25,30));draw=ImageDraw.Draw(sheet)
    for i,g in enumerate(groups):
        x=i%5*200;y=i//5*160
        if g['image'] is not None:
            im=Image.fromarray(g['image']);im.thumbnail((195,130));sheet.paste(im,(x,y))
        draw.text((x,y+131),f'{i}: '+g['name'][:25],fill='white')
    sheet.save(OUT/'materials.jpg',quality=92)
    scene=json.loads((ROOT/'out/base_interiors/rheinland_batch/scenes/rh_01_shipdealer_hardpoint_01.json').read_text())
    for c in scene['entities'].values():
        if c.get('entity_name') in ('Camera_Ship_1','Camera_Ship_2','Camera_Ship_3'):
            for fov in (30,41):render(groups,c,fov,c['entity_name']+'_'+str(fov))
    assert LIVE.read_bytes()==raw
    print('AUDIT',OUT,'geometry/UV unchanged:',same)


if __name__=='__main__':main()
