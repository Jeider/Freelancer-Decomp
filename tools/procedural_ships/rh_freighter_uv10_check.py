"""Round-trip and previous-version preservation checks for Q13 uv_10."""
import json
import numpy as np
import rh_freighter_uv10 as edit
from rh_freighter_chevron_check import hp_semantics

f,OUT=edit.f,edit.OUT


def read(path):return json.loads(path.read_text(encoding='utf8'))


def decoded(path):
    _,nodes=f.mesh.read_tree(path.read_bytes());names=f.component_map(nodes)
    flight,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    return nodes,{names[file]:f.base.world(gs,*flight[file.lower()]) for file,gs in f.local_geometry(nodes).items()}


def main():
    edit.guard()
    before=read(edit.PREVIOUS/'mechanical_geometry.json');after=read(OUT/'mechanical_geometry.json')
    lookup={o['name']:o for o in after['objects']};kept=[]
    for ob in before['objects']:
        if ob['name'].startswith('Continuous hull'):continue
        assert ob==lookup[ob['name']],ob['name'];kept.append(ob['name'])
    assert after['uv10_changes']['pale_extensions_united_with_core']
    assert read(OUT/'pale_stern_union.json')['nonmanifold_edges']==0
    nodes,parts=decoded(OUT/'rh_pir_freighter.cmp');prev,oldparts=decoded(edit.PREVIOUS/'rh_pir_freighter.cmp')
    hp,oldhp=hp_semantics(nodes),hp_semantics(prev)
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
    assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(nodes))
    build=read(OUT/'build.json');previous_build=read(edit.PREVIOUS/'build.json')
    assert build['salt']!=previous_build['salt']
    assert build['shared_mat_sha256']==previous_build['shared_mat_sha256']==f.digest(edit.q.MAT)
    assert f.digest(edit.q.SOURCE)==build['source_sha256']
    assert build['maximum']['vertices']<65536 and build['maximum']['indices']<65536
    probe=read(OUT/'hold_and_stern_probe.json');motion=read(OUT/'motion_check.json')
    assert probe['cmp_sha256']==motion['cmp_sha256']==build['cmp_sha256']
    assert not motion['collisions']
    report=dict(cmp_sha256=build['cmp_sha256'],unchanged_authoring_objects=kept,
        unchanged_decoded_parts_with_uv=unchanged,hardpoints_identical_to_uv09=len(hp),
        core_restored_from='uv_07',native_animation_and_constructs_preserved=build['original_animation_and_constructs_preserved'],
        shared_mat_unchanged=True,source_cmp_unchanged=True,materials_external=True,
        depth_ratio=probe['floor_depth_ratio'],total_triangles=build['total_triangles'],maximum=build['maximum'],
        floor_samples=len(probe['floors']),stern_samples=len(probe['stern_material_bands']),
        closed_shoulder_samples=len(probe['pale_shoulder_closures']),
        installed=False,game_launched=False)
    (OUT/'revision_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('UV10_CHECK',len(hp),'hardpoints;',len(unchanged),'decoded parts unchanged;',build['total_triangles'],'triangles')


if __name__=='__main__':main()
