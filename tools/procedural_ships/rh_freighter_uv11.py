"""Q13 uv_11: one horizontal stern cornice with native freighter texture motifs."""
import collections
import json
import shutil
import subprocess
import sys
import numpy as np
import rh_freighter_uv10 as prev

aft,base,old,package=prev.aft,prev.base,prev.old,prev.package
uv,rig,f,q=prev.uv,prev.rig,prev.f,prev.q
PREVIOUS=prev.OUT
OUT=PREVIOUS.parent/'uv_11'
REFERENCE=OUT.parents[1]/'references/stern_cornice_11'
# z,y: one connected profile, a horizontal top and an inward return underneath.
PROFILE=np.array([[7.36,0],[8.51,0],[8.51,.84],[8.86,1.28],
                  [8.86,2.58],[9.02,2.80],[7.36,2.80]])
WIDTH=1.37
STATS=[]


def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def guard():
    assert shutil.disk_usage(q.ROOT).free>2*1024**3
    for folder in (PREVIOUS,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(folder,name,'manual edits')


def cornice():
    b=q.B();left=b.yz(PROFILE,-WIDTH);right=b.yz(PROFILE,WIDTH)
    # 60 top; 61 top lip; 62 native round-port fascia; 63 large-eye return;
    # 64 lower frame; 65 recessed backing; 66 closed ends; 67 recess walls.
    roles=[66,64,63,62,61,60,66]
    for i,role in enumerate(roles):
        j=(i+1)%len(PROFILE)
        if role==64:
            outer=np.array([[-WIDTH,0],[WIDTH,0],[WIDTH,.84],[-WIDTH,.84]])
            inner=np.array([[-1.17,.15],[1.17,.15],[1.17,.66],[-1.17,.66]])
            loops=b.panel(outer,2,8.51,[0,0,1],64,holes=[inner])
            face=np.column_stack((loops[1],np.full(len(loops[1]),8.51)))
            backing=face.copy();backing[:,2]=8.36
            b.bridge(face,backing,67,inner=True);b.face(backing,65,normal=[0,0,1])
        else:
            dz,dy=PROFILE[j]-PROFILE[i]
            b.face([left[i],right[i],right[j],left[j]],role,normal=[0,-dz,dy])
    b.face(left,66,normal=[-1,0,0]);b.face(right,66,normal=[1,0,0])
    groups,closure=q.coherent(b.groups())
    return dict(name='Aft single cornice - horizontal shelf and central return',groups=groups,closed=True,closure=closure)


def prepare():
    guard();OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    data['objects'].append(cornice())
    refs=json.loads((REFERENCE/'native_stern.json').read_text())
    for ref in refs:
        assert f.digest(prev.Path(ref['model']))==ref['model_sha256']
        assert f.digest(prev.Path(ref['material']))==ref['material_sha256']
    data['uv11_changes']=dict(source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),
        cornice_profile_zy=PROFILE.tolist(),single_unmirrored_motif=True)
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':'),default=lambda a:a.tolist()),encoding='utf8')
    for name in ('engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json','raised_hold_geometry.json',
                 'stern_transition_geometry.json','pale_stern_union.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})
    dump('cornice_geometry.json',dict(profile_zy=PROFILE,width=2*WIDTH,top_y=2.80,top_z=[7.36,9.02],
        fascia_z=8.86,fascia_y=[1.28,2.58],lower_frame_z=8.51,lower_frame_y=[0,.84],
        backing_z=8.36,backing_xy=[[-1.17,.15],[1.17,.66]],
        end_at_red_belt_y=0,native_reference=refs[0]['model'],native_reference_sha256=refs[0]['model_sha256'],
        pirate_reference_sha256=refs[1]['model_sha256'],
        uv_source_triangles=dict(fascia=[330,331],sloping_return=[328,441],frame=[478,479,480,481,482,483,484,485]),
        single_motif=True,cargo_floor_preserved=True,engine_mounts_preserved=True))


def map_new(groups):
    mapped=collections.defaultdict(list);charts=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t);role=g['material']
            if role==62:
                # Source left half only, preserving its vertical orientation.
                # Full four-port native motif, never mirrored/repeated at x=0.
                u=.5059+(p[:,0]+WIDTH)/(2*WIDTH)*(1-.5059)
                v=(p[:,1]-1.28)/(2.58-1.28)*.2627
                t[:,6:8]=np.column_stack((u,v));mapped[uv.P].append(t)
            elif role==63:
                u=.5137-(p[:,0]+WIDTH)/(2*WIDTH)*.5137
                v=(p[:,1]-.84)/(1.28-.84)*.2627
                t[:,6:8]=np.column_stack((u,v));mapped[uv.P].append(t)
            elif role==61:
                base.fixed_box(t,np.column_stack((p[:,0],p[:,1])),[-WIDTH,2.58],[WIDTH,2.8],
                               (.017,.165,.497,.251),uv.P,mapped)
            elif role==64:
                # Keep a single unbroken border. Chart by the physical frame
                # segment, avoiding a second mirrored bay / a middle divider.
                for low,high,side in [(-WIDTH,-1.17,-1),(-1.17,1.17,0),(1.17,WIDTH,1)]:
                    poly=uv.clip(t,0,low,True)
                    if len(poly)<3:continue
                    poly=uv.clip(poly,0,high,False)
                    if len(poly)<3:continue
                    for tt in package.triangles(poly):
                        if side:
                            base.fixed_box(tt,tt[:,[0,1]],[low,0],[high,.84],(.088,.235,.135,.910),uv.P,mapped)
                        else:
                            top=tt[:,1].mean()>.4;lo=.66 if top else 0;hi=.84 if top else .15
                            base.fixed_box(tt,tt[:,[0,1]],[-1.17,lo],[1.17,hi],(.515,.165,.995,.251),uv.P,mapped)
            elif role==65:
                base.add(charts,t,'light',p[:,[0,1]],(2.34,100),'one lower inset')
            elif role==67:
                base.add(charts,t,'brown',uv.plane_coords(p,n),(2.4,100),('lower inset walls',tuple(n.round(4))))
            else:
                base.add(charts,t,'light',uv.plane_coords(p,n),(1.9,2.1),('cornice skin',role,tuple(n.round(4))))
    return base.complete(charts,mapped)


def core_map(name,groups):
    new=[g for g in groups if 60<=g['material']<=67]
    assert {60,61,62,63,64,65,66,67}.issubset({g['material'] for g in new}),'cornice face roles lost in union'
    rest=[g for g in groups if not 60<=g['material']<=67]
    return prev.core_map(name,rest)+map_new(new)


def main():
    prepare()
    subprocess.run([sys.executable,str(q.ROOT/'tools/blender_workspace.py'),'--topic','ship_design',
        '--script',str(q.ROOT/'tools/procedural_ships/rh_freighter_uv10_union.py'),'--',
        '--variant','uv_11','--prefix','Aft single cornice','--report','cornice_union.json'],check=True,cwd=q.ROOT)
    base.configure();rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp';base.REPORT.clear()
    def mapping(name,groups):
        mapper=(prev.previous.upper_map if name.startswith('Faceted shoulder') else core_map if name.startswith('Continuous hull')
            else prev.previous.hump_map if name.startswith('Stepped circular') else prev.previous.prev.rib_map if name.startswith('Aft structural')
            else aft.engine_map if name.startswith('Engine casing') else prev.addition_map if name.startswith(('Aft transverse','Raised cargo')) else base.region_map)
        result=mapper(name,groups);bad=0.;count=0
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
    dump('uv_layout.json',dict(cmp_sha256=h,regions=base.REPORT,source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),installed=False))
    dump('engine_check.json',dict(cmp_sha256=h,engines=json.loads((OUT/'engine_geometry_check.json').read_text()),installed=False))
    package.OUT=OUT;package.open_review()
    print('UV11_READY',OUT)


if __name__=='__main__':main()
