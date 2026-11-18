"""Measure actual exported UVs and make matched offline review sheets."""
import collections
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import rh_freighter_rig_build as rig

f,q=rig.f,rig.q
OUT=rig.OUT.parent/'uv_02'

def quantile(values,weights):
    order=np.argsort(values);x=np.asarray(values)[order];w=np.cumsum(np.asarray(weights)[order]);w/=w[-1]
    return np.interp([.1,.5,.9],w,x).tolist()

def measure(path):
    _,nodes=f.mesh.read_tree(path.read_bytes());gs=[g for v in f.local_geometry(nodes).values() for g in v]
    mats=f.audit.material_table([q.MAT,q.SOURCE.parents[3]/'fx/envmapbasic.mat'])
    area_by_material=collections.Counter();densities=[];areas=[];bad_area=0.;stretches=[]
    for g in gs:
        m=mats[g['material']];a=g['corners'];xyz=a[...,:3];uv=a[...,6:8]
        e1=xyz[:,1]-xyz[:,0];e2=xyz[:,2]-xyz[:,0];w=np.linalg.norm(np.cross(e1,e2),axis=1)/2
        area_by_material[m['name']]+=float(w.sum())
        if 'panel0' not in m['name']:continue
        du=uv[:,1]-uv[:,0];dv=uv[:,2]-uv[:,0];v=np.abs(du[:,0]*dv[:,1]-du[:,1]*dv[:,0])/2
        density=np.sqrt(v/np.maximum(w,1e-20));valid=w>1e-8
        densities.extend(density[valid]);areas.extend(w[valid]);bad_area+=w[valid&(density<.08)].sum()
        # Jacobian from an orthonormal triangle basis to UV coordinates.
        ex=e1/np.maximum(np.linalg.norm(e1,axis=1)[:,None],1e-10)
        x=np.sum(e2*ex,axis=1);y=np.sqrt(np.maximum(np.sum(e2*e2,axis=1)-x*x,0))
        for i in np.flatnonzero(valid&(y>1e-7)):
            basis=np.array([[np.linalg.norm(e1[i]),x[i]],[0,y[i]]])
            jac=np.column_stack((du[i],dv[i]))@np.linalg.inv(basis);s=np.linalg.svd(jac,compute_uv=False)
            stretches.append((s[0]/max(s[1],1e-12),w[i]))
    return dict(cmp=str(path),sha256=f.digest(path),uv_per_unit_area_weighted_p10_p50_p90=quantile(densities,areas),
        area_below_008_percent=100*float(bad_area)/sum(areas),surface_area_by_material=dict(area_by_material),
        uv_anisotropy_area_weighted_p10_p50_p90=quantile(*zip(*stretches)))

def main():
    before=measure(rig.DEST);after=measure(OUT/'rh_pir_freighter.cmp');native=measure(q.SOURCE)
    (OUT/'uv_check.json').write_text(json.dumps(dict(before=before,after=after,native=native),indent=2),encoding='utf8')
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26)
    for label in ('flight','side','underside'):
        files=[rig.OUT/('textured_'+label+'.png'),OUT/('textured_'+label+'.png')]
        if not all(p.exists() for p in files):continue
        sheet=Image.new('RGB',(2000,800),(37,42,47));draw=ImageDraw.Draw(sheet)
        for i,(p,title) in enumerate(zip(files,('BEFORE / rig_01','AFTER / uv_02'))):
            im=Image.open(p).convert('RGB');im.thumbnail((1000,750));sheet.paste(im,(i*1000,50));draw.text((i*1000+24,12),title,font=font,fill='white')
        sheet.save(OUT/('comparison_'+label+'.jpg'),quality=95)
    print(json.dumps({k:after[k] for k in ('uv_per_unit_area_weighted_p10_p50_p90','area_below_008_percent','uv_anisotropy_area_weighted_p10_p50_p90')},indent=2))

if __name__=='__main__':main()
