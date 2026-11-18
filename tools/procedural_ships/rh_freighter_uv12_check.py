"""Check the new front shelf, matching rear height, and preserved native rig."""
import json
import importlib
import sys
import numpy as np
from rh_freighter_uv10_check import decoded,hp_semantics

VARIANT=sys.argv[sys.argv.index('--variant')+1] if '--variant' in sys.argv else 'uv_12'
assert VARIANT in ('uv_12','uv_13'),VARIANT
edit=importlib.import_module('rh_freighter_'+VARIANT.replace('_',''))
OUT,f=edit.OUT,edit.f
def read(path):return json.loads(path.read_text(encoding='utf8'))


def main():
    edit.guard()
    before=read(edit.PREVIOUS/'mechanical_geometry.json');after=read(OUT/'mechanical_geometry.json')
    lookup={o['name']:o for o in after['objects']};kept=[]
    for ob in before['objects']:
        if ob['name'].startswith('Continuous hull'):continue
        assert lookup[ob['name']]==ob,ob['name'];kept.append(ob['name'])
    core=next(o for o in after['objects'] if o['name'].startswith('Continuous hull'))
    assert not {10,11}.intersection(g['material'] for g in core['groups'])
    assert read(OUT/'fore_cornice_union.json')['nonmanifold_edges']==0
    for name in ('cornice_geometry.json','raised_hold_geometry.json'):
        assert (OUT/name).read_bytes()==(edit.PREVIOUS/name).read_bytes()
    nodes,parts=decoded(OUT/'rh_pir_freighter.cmp');oldnodes,oldparts=decoded(edit.PREVIOUS/'rh_pir_freighter.cmp')
    hp,oldhp=hp_semantics(nodes),hp_semantics(oldnodes)
    assert hp.keys()==oldhp.keys()
    for k in hp:
        assert np.allclose(hp[k][0],oldhp[k][0],atol=1e-7),k
        assert np.allclose(hp[k][1],oldhp[k][1],atol=1e-7),k
    unchanged=[]
    for name,gs in parts.items():
        if name=='Root':continue
        assert len(gs)==len(oldparts[name]),name
        for a,b in zip(gs,oldparts[name]):
            assert a['material']==b['material'] and np.allclose(a['corners'],b['corners'],atol=1e-6),name
        unchanged.append(name)
    cfg=read(OUT/'fore_cornice_geometry.json')
    u0,v0,u1,v1=cfg.get('base_fascia_uv',[.5059,.8627,.998,.998])
    tops={'front':[],'rear':[]};fascia=[];uv_error=0
    for g in parts['Root']:
        for t in np.array(g['corners']):
            p=t[:,:3];n=edit.old.normal(t)
            if abs(p[:,1]-edit.TOP).max()<1e-4 and n[1]>.99:
                key='front' if p[:,2].max()<-5.5 else 'rear' if p[:,2].min()>7.3 else None
                if key:tops[key].extend(p.tolist())
            if abs(p[:,2]+7.62).max()<1e-4 and p[:,1].min()>1.7799 and p[:,1].max()<2.5801 and n[2]<-.99:
                expected=np.column_stack((u0+(p[:,0]+edit.WIDTH)/(2*edit.WIDTH)*(u1-u0),
                    v0+(p[:,1]-1.78)/.8*(v1-v0)))
                assert g['material']==edit.uv.P
                error=float(abs(t[:,6:8]-expected).max());uv_error=max(uv_error,error)
                assert error<2e-5
                fascia.extend(p.tolist())
    assert len(fascia)>=6 and all(len(v)>=6 for v in tops.values())
    for p in tops.values():assert abs(np.array(p)[:,1]-2.80).max()<1e-5
    platform={}
    if cfg.get('long_platform'):
        platform=cfg['native_platform'];p=np.array(tops['front'])
        z0,z1=p[:,2].min(),p[:,2].max()
        assert abs(z0-platform['top_z'][0])<1e-5 and abs(z1-platform['top_z'][1])<1e-5
        assert abs((z1-z0)-platform['native_top_length'])<1e-5
        for z,key in ((z0,'tip_width'),(z1,'rear_width')):
            assert abs(np.ptp(p[np.isclose(p[:,2],z),0])-platform[key])<1e-5
        assert platform['tip_width']<platform['rear_width']
        assert platform['visible_top_length']>platform['previous_visible_length']*1.4
    build=read(OUT/'build.json');oldbuild=read(edit.PREVIOUS/'build.json')
    assert build['salt']!=oldbuild['salt']
    assert build['maximum']['vertices']<65536 and build['maximum']['indices']<65536
    assert f.digest(edit.q.MAT)==build['shared_mat_sha256']==oldbuild['shared_mat_sha256']
    assert f.digest(edit.q.SOURCE)==build['source_sha256']
    assert build['original_animation_and_constructs_preserved']
    assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(nodes))
    probe=read(OUT/'hold_and_stern_probe.json');motion=read(OUT/'motion_check.json')
    assert probe['cmp_sha256']==motion['cmp_sha256']==build['cmp_sha256'] and not motion['collisions']
    assert len(probe['fore_cornice_samples'])==(43 if cfg.get('long_platform') else 34)
    report=dict(cmp_sha256=build['cmp_sha256'],source_cmp_sha256=oldbuild['cmp_sha256'],unchanged_authoring_objects=kept,
        unchanged_hardpoints=len(hp),unchanged_decoded_parts_with_uv=unchanged,
        shelf_height_y=2.8,matching_horizontal_shelves=True,fore_shelf_corners=len(tops['front']),
        aft_shelf_corners=len(tops['rear']),native_fascia_corners=len(fascia),max_fascia_uv_error=uv_error,
        native_platform=platform,
        fore_cornice_rays=len(probe['fore_cornice_samples']),cargo_depth_ratio=probe['floor_depth_ratio'],
        hatch_plateau_removed=True,total_triangles=build['total_triangles'],maximum=build['maximum'],
        native_animation_and_constructs_preserved=True,shared_mat_unchanged=True,
        source_cmp_unchanged=True,materials_external=True,installed=False,game_launched=False)
    (OUT/'revision_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(VARIANT.upper()+'_CHECK',len(hp),'HP;',len(unchanged),'unchanged parts; both shelves Y=2.80;',build['total_triangles'],'triangles')


if __name__=='__main__':main()
