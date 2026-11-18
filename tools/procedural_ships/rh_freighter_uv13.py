"""Q13: native-length tapered fore shelf and the rear cornice texture recipe."""
import collections
import copy
import json
import shutil
import subprocess
import sys
import numpy as np
import rh_freighter_uv12 as prev

aft,base,old,package=prev.aft,prev.base,prev.old,prev.package
uv,rig,f,q=prev.uv,prev.rig,prev.f,prev.q
PREVIOUS=prev.OUT
OUT=PREVIOUS.parent/'uv_13'
REFERENCE=prev.REFERENCE
WIDTH,TOP=prev.WIDTH,prev.TOP
FASCIA_VMAX=(2.58-1.78)*(.2627/1.30)*(2.74/(2*WIDTH))


def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def guard():
    assert shutil.disk_usage(q.ROOT).free>2*1024**3
    for folder in (prev.PREVIOUS,PREVIOUS,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(folder,name,'manual edits')


def solid(name,b):
    groups,closure=q.coherent(b.groups())
    return dict(name=name,groups=groups,closed=True,closure=closure)


def cornice_base():
    # The body/hood joint stays where it was. The separate shelf projects over it.
    profile=np.array([[-5.05,1.10],[-7.40,1.10],[-7.40,1.50],[-7.62,1.78],[-7.62,2.58],[-5.05,2.58]])
    b=q.B();left=b.yz(profile,-WIDTH);right=b.yz(profile,WIDTH)
    for i,role in enumerate([76,76,73,72,74,76]):
        j=(i+1)%len(profile);dz,dy=profile[j]-profile[i]
        b.face([left[i],right[i],right[j],left[j]],role,normal=[0,dz,-dy])
    b.face(left,76,normal=[-1,0,0]);b.face(right,76,normal=[1,0,0])
    return solid('Fore long cornice - supporting body',b)


def native_platform(ref):
    selected=[np.array(t['corners']) for t in ref['triangles']
              if t['material']=='r_panel01_256' and t['source_triangle'] in (93,94)]
    p=np.concatenate(selected)[:,:3]
    z0,z1=float(p[:,2].min()),float(p[:,2].max());center=float((p[:,0].min()+p[:,0].max())/2)
    tip=p[np.isclose(p[:,2],z0)];rear=p[np.isclose(p[:,2],z1)]
    tip_width=float(np.ptp(tip[:,0]));rear_width=float(np.ptp(rear[:,0]))
    lower=[np.array(t['corners'])[:,:3] for t in ref['triangles']
           if t['material']=='r_panel01_256' and t['source_triangle'] in (95,96)]
    lower=np.concatenate(lower);lower_z=float(lower[lower[:,1]<p[:,1].min()-.1,2].min())
    meet=-7.62+(TOP-1.38)/prev.SLOPE;front=meet-(z1-z0)
    top=np.array([[-tip_width/2,TOP,front],[tip_width/2,TOP,front],
                  [rear_width/2,TOP,meet],[-rear_width/2,TOP,meet]])
    bottom=top.copy();bottom[:,1]=2.58;bottom[:2,2]+=lower_z-z0
    b=q.B();b.face(top,70,normal=[0,1,0]);b.face(bottom,78,normal=[0,-1,0])
    # Native pointed leading bevel and narrowing sides, with actual thickness.
    for i,role in enumerate((71,79,79,79)):
        j=(i+1)%4
        normal=np.mean([top[i],top[j],bottom[j],bottom[i]],0)-np.mean(np.r_[top,bottom],0)
        b.face([top[i],top[j],bottom[j],bottom[i]],role,normal=normal)
    report=dict(native_top_length=z1-z0,visible_top_length=meet-front,
        previous_visible_length=meet-(-7.86),top_z=[front,meet],top_y=TOP,bottom_y=2.58,
        tip_width=tip_width,rear_width=rear_width,leading_bevel_length=lower_z-z0,
        source_top_y=float(p[0,1]),source_center_x=center,source_triangles=[93,94,95,96])
    return solid('Fore long cornice - native tapered shelf',b),report


def prepare():
    guard();OUT.mkdir(parents=True,exist_ok=True)
    current=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    basis=json.loads((prev.PREVIOUS/'mechanical_geometry.json').read_text())
    # Reconstruct only the changed fore cornice from the pinned pre-cornice core.
    # All other authoring objects come from uv_12, and manual CMP edits are guarded.
    core=copy.deepcopy(next(o for o in basis['objects'] if o['name'].startswith('Continuous hull')))
    removal=prev.remove_hatches(core)
    current['objects']=[core if o['name'].startswith('Continuous hull') else o for o in current['objects']]
    refs=json.loads((REFERENCE/'native_fore.json').read_text())
    for ref in refs:
        assert f.digest(prev.prev.prev.Path(ref['model']))==ref['model_sha256']
        assert f.digest(prev.prev.prev.Path(ref['material']))==ref['material_sha256']
    platform,shape=native_platform(refs[0]);current['objects'].extend([cornice_base(),platform])
    current['uv13_changes']=dict(source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),
        reconstruction_core_source_sha256=f.digest(prev.PREVIOUS/'rh_pir_freighter.cmp'),
        native_platform=shape,base_texture_recipe='rear cornice native motifs')
    (OUT/'mechanical_geometry.json').write_text(json.dumps(current,separators=(',',':'),default=lambda a:a.tolist()),encoding='utf8')
    for name in ('engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json','raised_hold_geometry.json',
                 'stern_transition_geometry.json','pale_stern_union.json','cornice_geometry.json','cornice_union.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})
    cfg=json.loads((PREVIOUS/'fore_cornice_geometry.json').read_text())
    cfg.update(profile_zy=None,top_z=shape['top_z'],ramp_meeting_z=shape['top_z'][1],
        native_platform=shape,long_platform=True,removal=removal,
        base_fascia_uv=[.5059,0,1,FASCIA_VMAX],base_return_uv=[0,0,.5137,.16],
        native_texture_recipe='rear panel01 circles and oval; pale platform',
        native_uv_source_triangles=dict(platform=[93,94,95,96],rear_fascia=[330,331],rear_return=[328,441]))
    dump('fore_cornice_geometry.json',cfg)


def new_map(groups):
    mapped=collections.defaultdict(list);charts=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t);role=g['material']
            if role==72:
                # Identical port motif to the stern. The shorter facade drops
                # unused pale bands, keeping complete circles at the same aspect.
                base.fixed_box(t,p[:,[0,1]],[-WIDTH,1.78],[WIDTH,2.58],(.5059,0,1,FASCIA_VMAX),uv.P,mapped)
            elif role==73:
                # Whole oval artwork; exclude the blank pale strip below it.
                base.fixed_box(t,np.column_stack((-p[:,0],p[:,1])),[-WIDTH,1.50],[WIDTH,1.78],
                               (0,0,.5137,.16),uv.P,mapped)
            elif role==77:
                co=np.column_stack((p[:,0],p[:,2]*np.hypot(1,prev.SLOPE)))
                base.add(charts,t,'light',co,(1.9,2.1),'hood with old hatches removed')
            elif role in (70,74,78):
                base.add(charts,t,'light',p[:,[0,2]],(1.9,2.1),('long fore shelf',role))
            else:
                base.add(charts,t,'light',uv.plane_coords(p,n),(1.9,2.1),('cornice skin',role,tuple(n.round(4))))
    return base.complete(charts,mapped)


def core_map(name,groups):
    new=[g for g in groups if 70<=g['material']<=79]
    assert {70,71,72,73,76,77,78,79}.issubset({g['material'] for g in new})
    rest=[g for g in groups if not 70<=g['material']<=79]
    assert not any(g['material'] in (10,11) for g in rest)
    return prev.prev.core_map(name,rest)+new_map(new)


def main():
    prepare()
    subprocess.run([sys.executable,str(q.ROOT/'tools/blender_workspace.py'),'--topic','ship_design',
        '--script',str(q.ROOT/'tools/procedural_ships/rh_freighter_uv10_union.py'),'--',
        '--variant','uv_13','--prefix','Fore long cornice','--expected-count','2',
        '--report','fore_cornice_union.json','--conform-seams'],check=True,cwd=q.ROOT)
    prev.export_model(OUT,PREVIOUS,core_map)


if __name__=='__main__':main()
