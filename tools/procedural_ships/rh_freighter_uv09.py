"""Q13 uv_09: longitudinal trim, dark aft wall, belly and cargo lining review."""
import collections
import json
import math
import shutil
import numpy as np
import rh_freighter_aft_chevron as prev

aft,base,old,package=prev.aft,prev.base,prev.old,prev.package
uv,rig,f,q=prev.uv,prev.rig,prev.f,prev.q
PREVIOUS=prev.OUT
OUT=PREVIOUS.parent/'uv_09'
STATS=[]


def dump(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def prepare():
    assert shutil.disk_usage(OUT.parent).free>2*1024**3
    for folder in (PREVIOUS,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(folder,name,'manual edits')
    OUT.mkdir(parents=True,exist_ok=True)
    for name in ('mechanical_geometry.json','engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    shape=json.loads((PREVIOUS/'aft_chevron_geometry.json').read_text())
    shape['rear_material']='pir_r_panel02_2562side'
    dump('aft_chevron_geometry.json',shape)
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(side):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for side,r in ribs.items()})


def perimeter(side):
    a=q.B().yz(base.UP_BACK,side*2.62);b=q.B().yz(base.UP_FACE,side*3.50)
    mid=(a+b)/2
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.roll(mid,-1,axis=0)-mid,axis=1))]
    widths=np.linalg.norm(b-a,axis=1)
    quads=[]
    for i in range(len(a)):
        j=(i+1)%len(a)
        # Preserve the old along-strip / across-strip axes and small crop.
        # Carry phase through bends without rotating a full atlas over the side.
        co=np.array([[arc[i],0],[arc[i+1],0],[arc[i+1],widths[j]],[arc[i],widths[i]]])
        quads.append((np.array([a[i],a[j],b[j],b[i]]),co))
    return quads


def upper_map(name,groups):
    quads=perimeter(-1 if '-1' in name else 1)
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            for quad,co in quads:
                coords=aft.on_quad(t,quad,co)
                if coords is not None:
                    base.add(charts,t,'frame03',coords,(2.3,100),(name,'longitudinal perimeter'))
                    break
            else:rest[g['material']].append(t)
    for g in base.region_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def core_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t)
            if g['material']==30:
                x=p[:,0];ax=abs(x)
                s=np.sign(x)*(np.minimum(ax,prev.EDGE)*math.hypot(1,prev.DEPTH/prev.EDGE)+np.maximum(ax-prev.EDGE,0))
                # Two complete broad rows, constant scale through the V crease.
                base.add(charts,t,'rear_dark',np.column_stack((s,p[:,1])),(100,2.25),'dark rear wall')
            elif n[1]<-.5 and p[:,1].max()<-1.8:
                channel=abs(p[:,1]+3.40).max()<1e-4 and n[1]<-.99
                family='dark' if channel else 'panel03'
                base.add(charts,t,family,p[:,[2,0]],(2.2,1.9),('belly whole surfaces',family))
            else:rest[g['material']].append(t)
    for g in prev.core_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def hump_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t);side=np.sign(p[:,0].mean())
            if n[0]*side<-.99 and abs(abs(p[:,0])-2.35).max()<1e-4:
                base.add(charts,t,'inside',p[:,[2,1]],(2.8,2.8),(name,'cargo inner bulkhead'))
            else:rest[g['material']].append(t)
    for g in base.region_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def main():
    prepare();base.configure();uv.PATCHES['rear_dark']=[(uv.D,(.670,.012,.994,.206))]
    rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp';base.REPORT.clear()
    def mapping(name,groups):
        mapper=(upper_map if name.startswith('Faceted shoulder') else core_map if name.startswith('Continuous hull')
            else hump_map if name.startswith('Stepped circular') else prev.rib_map if name.startswith('Aft structural')
            else aft.engine_map if name.startswith('Engine casing') else base.region_map)
        result=mapper(name,groups)
        count=0;bad=0.
        for g in result:
            t=np.array(g['corners']);p=t[:,:,:3];u=t[:,:,6:8]
            area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
            a=u[:,1]-u[:,0];b=u[:,2]-u[:,0];ua=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2
            mask=(area>1e-6)&(ua<1e-12);bad+=float(area[mask].sum());count+=int(mask.sum())
        if not name.startswith(('Original','Stepped circular')):assert bad<1e-7,(name,bad)
        STATS.append(dict(object=name,owner=rig.owner(name),source_triangles=sum(len(g['corners']) for g in groups),
            export_triangles=sum(len(g['corners']) for g in result),collapsed_uv_triangles=count,collapsed_uv_area=bad))
        return result
    rig.material_map=mapping;rig.main(OUT/'mechanical_geometry.json');h=f.digest(rig.DEST)
    for name in ('mesh_breakdown.json','uv_degenerate.json'):dump(name,dict(cmp_sha256=h,objects=STATS))
    dump('uv_layout.json',dict(cmp_sha256=h,regions=base.REPORT,source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),
        geometry_identical_to_uv08=True,installed=False))
    dump('engine_check.json',dict(cmp_sha256=h,engines=json.loads((OUT/'engine_geometry_check.json').read_text()),installed=False))
    package.OUT=OUT;package.open_review()
    print('UV09_READY',OUT)


if __name__=='__main__':main()
