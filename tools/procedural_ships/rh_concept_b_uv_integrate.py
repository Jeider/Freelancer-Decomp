"""Apply the approved UV corners, preserving all geometry/rig/collision assets."""
import json
from pathlib import Path
import numpy as np
import rh_concept_b_final as f
import rh_concept_b_final_damage as damage

REVIEW=f.OUT.parent/'uv_refinement_01'


def main():
    data=json.loads((REVIEW/'uv_changes.json').read_text());checks=json.loads((REVIEW/'checks.json').read_text())
    assert checks['reopened'] and f.digest(REVIEW/'rh_concept_b_uv_review.blend')==checks['blend_sha256']
    base=REVIEW/'approved_base.cmp'
    if not base.exists():
        assert f.digest(f.DEST)==data['base_cmp_sha256'];base.write_bytes(f.DEST.read_bytes())
    assert f.digest(base)==data['base_cmp_sha256']
    header,nodes=f.mesh.read_tree(base.read_bytes());levels=[f.local_geometry(nodes,lv) for lv in range(3)]
    before=f.mesh.read_tree(base.read_bytes())[1]
    root=data['root_file'];source=levels[0][root]
    offsets=[];at=0
    for g in source:offsets.append(at);at+=len(g['corners'])
    changed=[]
    for e in data['edits']:
        tri=source[e['group']]['corners'][e['triangle']]
        assert source[e['group']]['material']==e['material']
        assert np.allclose(tri[:,:3],e['positions'],atol=1e-6) and np.allclose(tri[:,6:],e['before'],atol=1e-6)
        tri[:,6:]=e['after'];changed.append(offsets[e['group']]+e['triangle'])
    f.write_geometry(nodes,levels)
    f.DEST.write_bytes(f.mesh.write_tree(header,nodes))
    # Independently decode the result and check that only the approved UVs moved.
    read=f.mesh.read_tree(f.DEST.read_bytes())[1]
    for lv in range(3):
        a,b=f.local_geometry(before,lv),f.local_geometry(read,lv)
        for file in a:
            assert len(a[file])==len(b[file])
            for x,y in zip(a[file],b[file]):
                assert x['material']==y['material'] and np.array_equal(x['corners'][...,:6],y['corners'][...,:6])
                if lv or file!=root:assert np.array_equal(x['corners'],y['corners'])
    def rig(ns):return {p:n.blob for p,n in f.mesh.walk(ns) if '/hardpoints/' in p.lower() or '/animation/' in p.lower() or '/cmpnd/' in p.lower()}
    assert rig(before)==rig(read)
    f.export_lod0(read)
    scene=json.loads((f.OUT/'blender_scene.json').read_text())
    bake=dict(cmp_sha256=f.digest(f.DEST),root_file=root,changed_source_triangles=changed,
              source=next(o for o in scene['objects'] if o['file']==root),materials=scene['materials'],levels=[])
    for lv in (1,2):
        atlas=f.mesh.crc(f'rh_b_lod{lv}')
        parts=f.local_geometry(read,lv)
        bake['levels'].append(dict(level=lv,root_groups=[dict(g,corners=g['corners'].tolist()) for g in parts[root]],
            atlas_uv=[g['corners'][...,6:8].tolist() for gs in parts.values() for g in gs if g['material']==atlas]))
    (REVIEW/'lod_refresh_input.json').write_text(json.dumps(bake,separators=(',',':')))
    collisions=json.loads((f.OUT/'collision_manifest.json').read_text());collisions['cmp_sha256']=f.digest(f.DEST)
    (f.OUT/'collision_manifest.json').write_text(json.dumps(collisions,indent=2))
    report=dict(cmp_sha256=f.digest(f.DEST),base_cmp_sha256=data['base_cmp_sha256'],approved_blend_sha256=checks['blend_sha256'],
                triangles_changed=len(changed),geometry_rig_hardpoints_unchanged=True,sur_sha256=f.digest(f.OUT/'rh_concept_b.sur'),
                approval='User accepted UV refinement: да, забираем; installation resumes after LOD transfer and checks')
    (f.OUT/'uv_integration.json').write_text(json.dumps(report,indent=2))
    print('APPLIED',len(changed),'approved UV triangles; geometry/rig/HP/SUR preserved.',flush=True)


def finish():
    ns=f.mesh.read_tree(f.DEST.read_bytes())[1]
    descriptions=json.loads((f.OUT/'damage_manifest.json').read_text())
    damage.review(ns,descriptions)
    materials=json.loads((f.OUT/'materials_manifest.json').read_text())
    materials.update(cmp_sha256=f.digest(f.DEST),lod_mat_sha256=f.digest(f.LOD_MAT))
    (f.OUT/'materials_manifest.json').write_text(json.dumps(materials,indent=2))
    report=json.loads((f.OUT/'uv_integration.json').read_text())
    report.update(lod_mat_sha256=f.digest(f.LOD_MAT),lod_refresh=json.loads((REVIEW/'lod_refresh.json').read_text()))
    (f.OUT/'uv_integration.json').write_text(json.dumps(report,indent=2))
    print('UV AND LOD MAT READY',flush=True)


if __name__=='__main__':
    import sys
    finish() if '--finish' in sys.argv else main()
