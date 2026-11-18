"""Offline Q13: replace the hood hatches with a native-inspired front cornice."""
import collections
import json
import shutil
import subprocess
import sys
import numpy as np
import rh_freighter_uv11 as prev

aft,base,old,package=prev.aft,prev.base,prev.old,prev.package
uv,rig,f,q=prev.uv,prev.rig,prev.f,prev.q
PREVIOUS=prev.OUT
OUT=PREVIOUS.parent/'uv_12'
REFERENCE=OUT.parents[1]/'references/fore_cornice_12'
SLOPE=(3.81-1.38)/3.52
WIDTH=1.90
TOP=2.80
# z,y; hidden bottom/back overlap the core for a solid union. The visible
# lower return terminates at the existing sloping hood, above the cockpit.
PROFILE=np.array([[-5.05,1.10],[-7.40,1.10],[-7.40,1.50],[-7.62,1.78],
                  [-7.62,2.58],[-7.86,TOP],[-5.05,TOP]])
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


def remove_hatches(ob):
    kept=collections.defaultdict(list);counts=collections.Counter()
    for g in ob['groups']:
        for t in np.array(g['corners'],float):
            p=t[:,:3];role=g['material']
            on_ramp=(p[:,2].min()>=-7.62002 and p[:,2].max()<=-4.09998
                and abs(p[:,1]-(1.38+(p[:,2]+7.62)*SLOPE)).max()<2e-5
                and old.normal(t)[1]>.5)
            if role in (10,11) or on_ramp:counts[role]+=1
            else:kept[role].append(t)
    assert counts[10]==16 and counts[11]==6 and sum(counts.values())>22,counts
    b=q.B();outer=np.array([[-2.14,-7.62],[2.14,-7.62],[2.35,-4.10],[-2.35,-4.10]])
    p=np.column_stack((outer[:,0],1.38+(outer[:,1]+7.62)*SLOPE,outer[:,1]))
    # A real replacement surface, with no old hatch plateau under the shelf.
    b.face(p,77,normal=[0,1,-SLOPE])
    for g in b.groups():kept[g['material']].extend(g['corners'])
    ob['groups']=package.pack(kept)
    return dict(removed_by_role=dict(counts),hatches_removed=2,plateau_removed=True,
                replaced_ramp_xz=outer,original_slope=SLOPE)


def cornice():
    b=q.B();left=b.yz(PROFILE,-WIDTH);right=b.yz(PROFILE,WIDTH)
    # 70 horizontal top; 71 lip; 72 pale fascia; 73 lower return; 76 ends.
    roles=[76,76,73,72,71,70,76]
    for i,role in enumerate(roles):
        j=(i+1)%len(PROFILE);dz,dy=PROFILE[j]-PROFILE[i]
        b.face([left[i],right[i],right[j],left[j]],role,normal=[0,dz,-dy])
    b.face(left,76,normal=[-1,0,0]);b.face(right,76,normal=[1,0,0])
    groups,closure=q.coherent(b.groups())
    return dict(name='Fore single cornice - level shelf and hood return',groups=groups,closed=True,closure=closure)


def prepare():
    guard();OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    core=next(o for o in data['objects'] if o['name'].startswith('Continuous hull'))
    change=remove_hatches(core);data['objects'].append(cornice())
    refs=json.loads((REFERENCE/'native_fore.json').read_text())
    for ref in refs:
        assert f.digest(prev.prev.Path(ref['model']))==ref['model_sha256']
        assert f.digest(prev.prev.Path(ref['material']))==ref['material_sha256']
    rear=json.loads((PREVIOUS/'cornice_geometry.json').read_text())
    assert abs(TOP-rear['top_y'])<1e-8
    data['uv12_changes']=dict(source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),
        profile_zy=PROFILE.tolist(),fore_aft_shelf_height=TOP,removed_front_hatches=2)
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':'),default=lambda a:a.tolist()),encoding='utf8')
    for name in ('engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json','raised_hold_geometry.json',
                 'stern_transition_geometry.json','pale_stern_union.json','cornice_geometry.json','cornice_union.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})
    dump('fore_cornice_geometry.json',dict(profile_zy=PROFILE,width=WIDTH*2,top_y=TOP,aft_top_y=rear['top_y'],
        top_z=[-7.86,-5.05],fascia_z=-7.62,fascia_y=[1.78,2.58],lip_y=[2.58,2.80],
        lower_return_zy=[[-7.4,1.5],[-7.62,1.78]],ramp_meeting_z=-7.62+(TOP-1.38)/SLOPE,
        source=refs[0]['model'],source_sha256=refs[0]['model_sha256'],pirate_sha256=refs[1]['model_sha256'],
        native_uv_source_triangles=dict(top=[93,94],lip=[95,96],fascia=[366,367,471,472]),
        removal=change,cockpit_preserved=True,cargo_floor_preserved=True,engine_mounts_preserved=True))


def new_map(groups):
    mapped=collections.defaultdict(list);charts=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t);role=g['material']
            if role==72:
                # Original front's pale bolted panel strip, kept within atlas
                # borders. One broad horizontal plank across the new facade.
                base.fixed_box(t,p[:,[0,1]],[-WIDTH,1.78],[WIDTH,2.58],
                               (.5059,.8627,.998,.998),uv.P,mapped)
            elif role==71:
                # Same narrow pale rim crop as native triangles 95/96, axes
                # rotated so the painted long edge follows the whole shelf.
                co=np.column_stack((p[:,1],p[:,0]))
                base.fixed_box(t,co,[2.58,-WIDTH],[TOP,WIDTH],(.0904,.4159,.135,.6541),uv.P,mapped)
            elif role==73:
                base.add(charts,t,'light',np.column_stack((p[:,0],p[:,1])),(1.9,100),'fore lower hood return')
            elif role==77:
                co=np.column_stack((p[:,0],p[:,2]*np.hypot(1,SLOPE)))
                base.add(charts,t,'light',co,(1.9,2.1),'hood with old hatches removed')
            elif role==70:
                base.add(charts,t,'light',p[:,[0,2]],(1.9,2.1),'horizontal fore shelf')
            else:
                base.add(charts,t,'light',uv.plane_coords(p,n),(1.9,2.1),('fore cornice ends',tuple(n.round(4))))
    return base.complete(charts,mapped)


def core_map(name,groups):
    new=[g for g in groups if 70<=g['material']<=77]
    assert {70,71,72,73,76,77}.issubset({g['material'] for g in new}),'fore face roles lost'
    rest=[g for g in groups if not 70<=g['material']<=77]
    assert not any(g['material'] in (10,11) for g in rest),'old hatch geometry retained'
    return prev.core_map(name,rest)+new_map(new)


def export_model(out_dir,previous_dir,core_mapper):
    OUT,PREVIOUS=out_dir,previous_dir
    def dump(name,obj):
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,
            default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')
    base.configure();rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp';base.REPORT.clear();STATS.clear()
    def mapping(name,groups):
        mapper=(prev.prev.previous.upper_map if name.startswith('Faceted shoulder') else core_mapper if name.startswith('Continuous hull')
            else prev.prev.previous.hump_map if name.startswith('Stepped circular') else prev.prev.previous.prev.rib_map if name.startswith('Aft structural')
            else aft.engine_map if name.startswith('Engine casing') else prev.prev.addition_map if name.startswith(('Aft transverse','Raised cargo')) else base.region_map)
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
    print('PROTOTYPE_READY',OUT)


def main():
    prepare()
    subprocess.run([sys.executable,str(q.ROOT/'tools/blender_workspace.py'),'--topic','ship_design',
        '--script',str(q.ROOT/'tools/procedural_ships/rh_freighter_uv10_union.py'),'--',
        '--variant','uv_12','--prefix','Fore single cornice','--report','fore_cornice_union.json','--conform-seams'],check=True,cwd=q.ROOT)
    export_model(OUT,PREVIOUS,core_map)


if __name__=='__main__':main()
