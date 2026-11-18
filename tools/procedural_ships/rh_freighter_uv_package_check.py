"""Independent decoded-CMP checks for the offline UV review package."""
import collections
import json
import sys
import numpy as np
import rh_freighter_uv_package as package
from rh_freighter_uv_report import measure

f,rig=package.f,package.rig
OUT=package.OUT
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant.replace('_','').isalnum()
    OUT=OUT.parent/variant


def area(ts):
    t=np.array(ts)
    return np.linalg.norm(np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]),axis=1).sum()/2


def main():
    source=json.loads((OUT/'mechanical_geometry.json').read_text())
    expected=collections.defaultdict(list)
    for ob in source['objects']:
        for g in ob['groups']:expected[rig.owner(ob['name'])].extend(g['corners'])
    path=OUT/'rh_pir_freighter.cmp';_,nodes=f.mesh.read_tree(path.read_bytes())
    names=f.component_map(nodes);flight,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    decoded={names[file]:f.base.world(gs,*flight[file.lower()]) for file,gs in f.local_geometry(nodes).items()}
    checks=[]
    for name,gs in decoded.items():
        actual=np.concatenate([g['corners'] for g in gs]);original=np.array(expected[name])
        a,b=area(actual),area(original)
        assert np.isclose(a,b,rtol=2e-5),(name,a,b)
        assert np.allclose(actual[:,:,:3].min((0,1)),original[:,:,:3].min((0,1)),atol=2e-5)
        assert np.allclose(actual[:,:,:3].max((0,1)),original[:,:,:3].max((0,1)),atol=2e-5)
        checks.append(dict(part=name,authoring_area=float(b),decoded_area=float(a),bounds_match=True))
    review=OUT/'rh_pir_freighter_review_open.cmp';_,rn=f.mesh.read_tree(review.read_bytes())
    rnames=f.component_map(rn);rposes,_=f.audit.transforms(rn)
    rworld={rnames[file]:f.base.world(gs,*rposes[file.lower()]) for file,gs in f.local_geometry(rn).items()}
    for name,gs in decoded.items():
        assert len(gs)==len(rworld[name])
        for a,b in zip(gs,rworld[name]):
            assert a['material']==b['material'] and np.allclose(a['corners'],b['corners'],atol=1e-5),name
    data=json.loads((OUT/'scene.json').read_text())
    brown=data['materials'][str(package.BROWN)]
    assert brown['name']=='pir_r_panel01_256D' and brown['texture']=='pir_r_panel01_256.tga'
    assert np.allclose(brown['colour'],[.470588,.3490196,.09411765],atol=1e-6)
    hp=f.hp_world(nodes);rhp=f.hp_world(rn)
    # Both resource-name salts must be distinct, even for the static review copy.
    b=json.loads((OUT/'build.json').read_text());r=json.loads((OUT/'review_open_check.json').read_text())
    assert b['salt']!=r['salt']
    motions=json.loads((OUT/'motion_check.json').read_text())
    assert motions['cmp_sha256']==f.digest(path) and not motions['collisions']
    measured=measure(path)
    report=dict(cmp_sha256=f.digest(path),review_cmp_sha256=f.digest(review),surface_checks=checks,
        static_review_matches_animated_flight=True,hardpoint_count=len(hp),
        dark_recess_material={k:v for k,v in brown.items() if k!='image_path'},
        uv_measurement=measured,installed=False,game_launched=False)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('VALIDATED',len(checks),'parts; static review matches flight; material and surface area correct')
    print('UV_DENSITY',measured['uv_per_unit_area_weighted_p10_p50_p90'])
    print('UV_ANISOTROPY',measured['uv_anisotropy_area_weighted_p10_p50_p90'])


if __name__=='__main__':main()
