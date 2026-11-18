"""Verify native single-motif cornice UVs and preservation of the reviewed ship."""
import json
import numpy as np
import rh_freighter_uv11 as edit
from rh_freighter_uv10_check import decoded,hp_semantics

OUT,f=edit.OUT,edit.f
def read(path):return json.loads(path.read_text(encoding='utf8'))


def main():
    edit.guard()
    before=read(edit.PREVIOUS/'mechanical_geometry.json');after=read(OUT/'mechanical_geometry.json')
    lookup={o['name']:o for o in after['objects']};kept=[]
    for ob in before['objects']:
        if ob['name'].startswith('Continuous hull'):continue
        assert lookup[ob['name']]==ob,ob['name'];kept.append(ob['name'])
    assert read(OUT/'cornice_union.json')['nonmanifold_edges']==0
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
    fascia=[];returns=[];error=0.
    for g in parts['Root']:
        for t in np.array(g['corners']):
            p=t[:,:3];n=edit.old.normal(t);expected=None
            if abs(p[:,0]).max()>1.3701:continue
            if abs(p[:,2]-8.86).max()<1e-4 and p[:,1].min()>=1.2799 and p[:,1].max()<2.5801 and n[2]>.99:
                expected=np.column_stack((.5059+(p[:,0]+1.37)/2.74*(1-.5059),(p[:,1]-1.28)/1.3*.2627))
                fascia.extend(p.tolist())
            if p[:,1].min()>=.8399 and p[:,1].max()<=1.2801 and n[2]>.5 and n[1]<-.4:
                if abs(p[:,2]-(8.51+(p[:,1]-.84)/.44*.35)).max()<1e-4:
                    expected=np.column_stack((.5137-(p[:,0]+1.37)/2.74*.5137,(p[:,1]-.84)/.44*.2627))
                    returns.extend(p.tolist())
            if expected is not None:
                assert g['material']==edit.uv.P
                delta=float(abs(t[:,6:8]-expected).max());error=max(delta,error)
                assert delta<2e-5,(p,delta)
    assert len(fascia)>=6 and len(returns)>=6
    assert np.allclose(np.array(fascia)[:,0].min(),-1.37,atol=1e-5) and np.allclose(np.array(fascia)[:,0].max(),1.37,atol=1e-5)
    build=read(OUT/'build.json');oldbuild=read(edit.PREVIOUS/'build.json')
    assert build['salt']!=oldbuild['salt']
    assert build['maximum']['vertices']<65536 and build['maximum']['indices']<65536
    assert f.digest(edit.q.MAT)==build['shared_mat_sha256']==oldbuild['shared_mat_sha256']
    assert f.digest(edit.q.SOURCE)==build['source_sha256']
    assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(nodes))
    assert (OUT/'raised_hold_geometry.json').read_bytes()==(edit.PREVIOUS/'raised_hold_geometry.json').read_bytes()
    probe=read(OUT/'hold_and_stern_probe.json');motion=read(OUT/'motion_check.json')
    assert probe['cmp_sha256']==motion['cmp_sha256']==build['cmp_sha256'] and not motion['collisions']
    report=dict(cmp_sha256=build['cmp_sha256'],source_cmp_sha256=oldbuild['cmp_sha256'],unchanged_authoring_objects=kept,
        hardpoints_identical_to_uv10=len(hp),unchanged_decoded_parts_with_uv=unchanged,
        single_native_fascia_corners=len(fascia),single_native_return_corners=len(returns),max_motif_uv_error=error,
        cornice_rays=len(probe['cornice_samples']),cargo_depth_ratio=probe['floor_depth_ratio'],
        total_triangles=build['total_triangles'],maximum=build['maximum'],shared_mat_unchanged=True,
        source_cmp_unchanged=True,materials_external=True,installed=False,game_launched=False)
    (OUT/'revision_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('UV11_CHECK',len(hp),'hardpoints;',len(unchanged),'unchanged parts;',len(fascia),len(returns),'native UV corners;',build['total_triangles'],'triangles')


if __name__=='__main__':main()
