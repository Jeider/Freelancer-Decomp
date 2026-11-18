"""Validate preserved shape/HPs and the formerly misclassified aft belly."""
import json
import numpy as np
import rh_freighter_uv09 as edit
from rh_freighter_chevron_check import hp_semantics

f,OUT,PREVIOUS=edit.f,edit.OUT,edit.PREVIOUS


def main():
    assert (OUT/'mechanical_geometry.json').read_bytes()==(PREVIOUS/'mechanical_geometry.json').read_bytes()
    _,nodes=f.mesh.read_tree((OUT/'rh_pir_freighter.cmp').read_bytes())
    _,old_nodes=f.mesh.read_tree((PREVIOUS/'rh_pir_freighter.cmp').read_bytes())
    a,b=hp_semantics(nodes),hp_semantics(old_nodes)
    assert a.keys()==b.keys()
    for key in a:
        assert np.allclose(a[key][0],b[key][0],atol=1e-7),key
        assert np.allclose(a[key][1],b[key][1],atol=1e-7),key
    names=f.component_map(nodes);flight,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    parts={names[file]:f.base.world(gs,*flight[file.lower()]) for file,gs in f.local_geometry(nodes).items()}
    checks=[]
    for g in parts['Root']:
        for t in np.array(g['corners']):
            p=t[:,:3];n=edit.old.normal(t)
            if n[1]<-.5 and p[:,2].min()>5.72 and abs(p[:,0]).max()<1.371 and p[:,1].max()<-2.6:
                assert g['material']==edit.uv.S,(p,g['material'])
                checks.append(p.mean(0).tolist())
    assert len(checks)>10
    source=json.loads((OUT/'mechanical_geometry.json').read_text())
    core=next(o for o in source['objects'] if o['name'].startswith('Continuous hull'))
    wrong=[]
    for g in core['groups']:
        for t in np.array(g['corners']):
            p=t[:,:3];n=edit.old.normal(t)
            if n[1]<-.5 and p[:,1].mean()<-1.8 and abs(p[:,1].mean()+3.4)<.04 and abs(p[:,1]+3.4).max()>1e-4:
                wrong.append(p.mean(0).tolist())
    h=f.digest(OUT/'rh_pir_freighter.cmp')
    hold=json.loads((OUT/'hold_probe.json').read_text())
    assert hold['cmp_sha256']==h
    assert not any(hold[k] for k in ('floor_failures','side_failures','end_failures'))
    report=dict(cmp_sha256=h,geometry_identical_to_uv08=True,hardpoints_identical_to_uv08=len(a),
        formerly_misclassified_authoring_triangles=wrong,decoded_aft_belly_panel03_samples=len(checks),
        hold_samples={k:len(hold[k]) for k in ('floors','sides','ends')},installed=False,game_launched=False)
    (OUT/'revision_check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('UV09_CHECK',len(a),'hardpoints unchanged;',len(wrong),'bad centroid assignments corrected;',len(checks),'decoded belly samples')


if __name__=='__main__':main()
