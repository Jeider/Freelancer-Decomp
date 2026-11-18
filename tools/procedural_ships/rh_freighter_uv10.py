"""Q13 uv_10: level stern, transverse red rib and a raised cargo deck.

Offline prototype. Keep uv_09 side UVs and every native joint / hardpoint.
"""
import collections
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import rh_freighter_uv09 as previous

aft,base,old,package=previous.aft,previous.base,previous.old,previous.package
uv,rig,f,q=previous.uv,previous.rig,previous.f,previous.q
PREVIOUS=previous.OUT
OUT=PREVIOUS.parent/'uv_10'
OLD_FLOOR=-3.10
HOLD_RIM=3.81
FLOOR=(OLD_FLOOR+HOLD_RIM)/2
BELT_Y=-.28
BELT_HALF=.28
STATS=[]


def dump(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def guard():
    assert shutil.disk_usage(OUT.parent).free>2*1024**3
    for folder in (PREVIOUS,aft.OUT,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(folder,name,'manual edits')


def solid(name,b):
    groups,closure=q.coherent(b.groups())
    return dict(name=name,groups=groups,closed=True,closure=closure)


def crossbar():
    b=q.B();lo=BELT_Y-BELT_HALF;hi=BELT_Y+BELT_HALF
    a=np.array([[-1.37,lo,8.20],[1.37,lo,8.20],[1.37,hi,8.20],[-1.37,hi,8.20]])
    c=a.copy();c[:,2]=8.51
    b.bridge(a,c,41);b.face(a,41,normal=[0,0,-1]);b.face(c,40,normal=[0,0,1])
    return solid('Aft transverse red transition',b)


def raised_deck():
    # Closed thin deck inside the shutter radius, rather than a solid block
    # intersecting the roof as it rotates below the usable cargo floor.
    # Flat ends stay below the small sliders as well as inside the roof sweep.
    # Narrow front/rear carriage slots remain outside the raised cargo deck.
    stations=np.array([[q.SHELL_Z-3.60,FLOOR],[q.SHELL_Z+3.60,FLOOR]])
    a=np.column_stack((np.full(2,-2.405),stations[:,1],stations[:,0]))
    b=a.copy();b[:,0]=2.405
    aa=a.copy();aa[:,1]-=.14
    bb=b.copy();bb[:,1]-=.14
    mesh=q.B()
    for i in range(len(stations)-1):
        j=i+1
        mesh.face([a[i],b[i],b[j],a[j]],50,normal=[0,1,0])
        mesh.face([aa[i],aa[j],bb[j],bb[i]],50,normal=[0,-1,0])
        mesh.face([a[i],a[j],aa[j],aa[i]],50,normal=[-1,0,0])
        mesh.face([b[i],bb[i],bb[j],b[j]],50,normal=[1,0,0])
    for i,sign in [(0,-1),(-1,1)]:
        mesh.face([a[i],aa[i],bb[i],b[i]],50,normal=[0,0,sign])
    # Native moving shell has r >= 4.34; all deck sections remain inside it.
    radius=np.hypot(np.r_[a[:,1],aa[:,1]]-q.SHELL_Y,np.r_[a[:,2],aa[:,2]]-q.SHELL_Z)
    assert radius.max()<4.23
    dump('raised_hold_geometry.json',dict(old_floor_y=OLD_FLOOR,new_floor_y=FLOOR,
        reference_rim_y=HOLD_RIM,old_depth=HOLD_RIM-OLD_FLOOR,new_depth=HOLD_RIM-FLOOR,
        depth_ratio=.5,thickness=.14,stations_zy=stations,
        floor_half_width=2.405,max_deck_radius=float(radius.max()),roof_inner_radius=4.34,
        roof_carriage_space_preserved=True,native_roof_geometry_unchanged=True))
    return solid('Raised cargo deck above native shutter channel',mesh)


def shoulder_infill(side):
    # Extend the pale core behind the end of the broad side shell. It meets
    # the shell at x=2.62 and closes the exposed step beside the aft rib.
    stations=[(5.75,2.68,3.80),(7.49,2.68,2.64),(8.30,2.24,1.78)]
    loops=[]
    for z,x,top in stations:
        loops.append(np.array([[side*1.96,-.22,z],[side*x,-.22,z],
                               [side*x,top-.10,z],[side*1.96,top,z]]))
    b=q.B()
    for a,c in zip(loops,loops[1:]):b.bridge(a,c,51)
    b.face(loops[0],51,normal=[0,0,-1]);b.face(loops[-1],51,normal=[0,0,1])
    return solid(f'Aft pale shoulder infill {side:+}',b)


def prepare():
    guard();OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    old_data=json.loads((aft.OUT/'mechanical_geometry.json').read_text())
    core=copy.deepcopy(next(o for o in old_data['objects'] if o['name'].startswith('Continuous hull')))
    for i,ob in enumerate(data['objects']):
        if ob['name'].startswith('Continuous hull'):data['objects'][i]=core
    data['objects'].extend([crossbar(),shoulder_infill(-1),shoulder_infill(1),raised_deck()])
    data['uv10_changes']=dict(source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),
        straight_core_source_sha256=f.digest(aft.OUT/'rh_pir_freighter.cmp'),
        flat_stern_z=8.30,raised_cargo_floor_y=FLOOR)
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':'),
        default=lambda a:a.tolist()),encoding='utf8')
    for name in ('engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})
    dump('stern_transition_geometry.json',dict(stern_z=8.30,belt_y=BELT_Y,belt_half_height=BELT_HALF,
        belt_outer_z=8.51,belt_inner_x=1.37,upper_material='pir_r_panel01_256',
        lower_material='pir_r_panel03_256',belt_material='pir_r_panel02_256',
        engine_positions_unchanged=True,side_uv_projection_unchanged=True))
    references=OUT.parents[1]/'references/stern_hold_10';references.mkdir(parents=True,exist_ok=True)
    images=['B8iCl1','LpIQfk','RwUfbA','K55nW1','GhYbK7'];records=[]
    for i,key in enumerate(images,1):
        source=Path(f'C:/Users/Freel/AppData/Local/Temp/codex-clipboard-{key}.png')
        target=references/f'{i:02}_{key}.png'
        if source.exists():shutil.copyfile(source,target)
        records.append(dict(order=i,original=str(source),file=target.name,sha256=f.digest(target)))
    (references/'sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')


def core_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t)
            if g['material']==51:
                base.add(charts,t,'light',uv.plane_coords(p,n),(1.9,2.1),('joined pale shoulder',tuple(n.round(4))))
            elif abs(p[:,2]-8.30).max()<1e-4 and n[2]>.99:
                polys=previous.prev.split([t],1,BELT_Y)
                for poly in polys:
                    for tt in package.triangles(poly):
                        upper=tt[:,1].mean()>BELT_Y;family='light' if upper else 'panel03'
                        base.add(charts,tt,family,tt[:,[0,1]],(1.9,1.9) if upper else (4.4,2.7),('rear split wall',family))
            elif n[1]<-.5 and p[:,1].max()<-1.8:
                channel=abs(p[:,1]+3.40).max()<1e-4 and n[1]<-.99
                family='dark' if channel else 'panel03'
                base.add(charts,t,family,p[:,[2,0]],(2.2,1.9),('belly whole surfaces',family))
            elif p[:,2].min()>=5.72-1e-5 and n[1]>.4:
                stations=np.array([[5.72,3.81],[7.72,2.48],[8.30,1.78]])
                arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(stations,axis=0),axis=1))]
                coords=np.column_stack((p[:,0],np.interp(p[:,2],stations[:,0],arc)))
                base.add(charts,t,'light',coords,(1.9,2.1),'continuous straight aft deck')
            else:rest[g['material']].append(t)
    for g in aft.core_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def addition_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t)
            if g['material']==40:
                base.add(charts,t,'vent',p[:,[0,1]],(1.37,100),('crossbar red panels'),exact=True)
            elif g['material']==41:
                base.add(charts,t,'light',uv.plane_coords(p,n),(2.5,1.6),(name,tuple(n.round(4))))
            elif g['material']==50:
                base.add(charts,t,'inside',uv.plane_coords(p,n),(2.2,2.4),(name,tuple(n.round(4))))
            else:
                base.add(charts,t,'light',uv.plane_coords(p,n),(1.9,2.1),(name,tuple(n.round(4))))
    return base.complete(charts,mapped)


def main():
    prepare()
    subprocess.run([sys.executable,str(q.ROOT/'tools/blender_workspace.py'),'--topic','ship_design',
        '--script',str(q.ROOT/'tools/procedural_ships/rh_freighter_uv10_union.py')],check=True,cwd=q.ROOT)
    base.configure();rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp';base.REPORT.clear()
    def mapping(name,groups):
        mapper=(previous.upper_map if name.startswith('Faceted shoulder') else core_map if name.startswith('Continuous hull')
            else previous.hump_map if name.startswith('Stepped circular') else previous.prev.rib_map if name.startswith('Aft structural')
            else aft.engine_map if name.startswith('Engine casing') else addition_map if name.startswith(('Aft transverse','Aft pale','Raised cargo')) else base.region_map)
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
    print('UV10_READY',OUT)


if __name__=='__main__':main()
