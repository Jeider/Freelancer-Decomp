"""Integrate the approved Blender tail into the native model; no game writes."""
import copy
import json
from pathlib import Path
import numpy as np
import rh_concept_b_final as f
import rh_concept_b_final_damage as damage

OUT=f.OUT
PROTO=OUT.parent/'tail_prototype_01'


def main():
    p=json.loads((PROTO/'prototype_data.json').read_text())
    verified=json.loads((PROTO/'blender_check.json').read_text())
    assert verified['reopened_blend_validated']
    assert f.digest(PROTO/'rh_concept_b_tail_prototype.blend')==verified['blend_sha256']
    assert f.digest(Path(p['original']))==p['original_sha256']
    base=PROTO/'approved_base.cmp';meta=PROTO/'approved_base_assembly.json'
    if not base.exists():
        assert f.digest(f.DEST)==p['base_cmp_sha256']
        base.write_bytes(f.DEST.read_bytes())
        meta.write_bytes((OUT/'assembly.json').read_bytes())
    assert f.digest(base)==p['base_cmp_sha256']
    header,nodes=f.mesh.read_tree(base.read_bytes())
    original_flat={path:n.blob for path,n in f.mesh.walk(nodes) if '/Animation/' in path}
    assembly=json.loads(meta.read_text());shift=np.array(p['center_shift_native'])
    names=f.component_map(nodes);root=next(k for k,n in names.items() if n=='Root')
    tail=next(k for k,n in names.items() if n=='Rh_tail_lod1')
    tr,_=f.audit.transforms(nodes);r,t=tr[tail.lower()]
    additions=[dict(material=g['material'],corners=np.array(g['corners'])) for e in p['objects'] for g in e['groups']]
    local_added=f.base.world(additions,r.T,-r.T@t)
    before_hp=f.hp_world(nodes)
    levels=[]
    for level in range(3):
        local=f.local_geometry(nodes,level)
        local[tail]=f.merge(local[tail]+copy.deepcopy(local_added))
        local[root]=f.base.world(local[root],np.eye(3),shift)
        levels.append(local)
    # Translation of the entire native hierarchy. Rotation offsets/animation keys
    # are left untouched. Root geometry/HPs shift; direct-child origins shift.
    cons=f.mesh.child(f.mesh.child(nodes[0],'Cmpnd'),'Cons')
    for node in cons.children:
        stride={'fix':176,'rev':208}.get(node.name.lower())
        if stride is None:raise ValueError('Unaudited construct type '+node.name)
        raw=bytearray(node.blob)
        for offset in range(0,len(raw),stride):
            if f.mesh.string(raw[offset:offset+64]).lower()=='root':
                origin=np.frombuffer(raw,'<f4',3,offset+128)
                origin[:]=origin+shift
        node.blob=bytes(raw)
    root_node=f.mesh.child(nodes[0],root)
    for path,node in f.mesh.walk([root_node]):
        if '/hardpoints/' in path.lower() and path.lower().endswith('/position'):
            node.blob=(np.frombuffer(node.blob,'<f4')+shift).astype('<f4').tobytes()
    tr,_=f.audit.transforms(nodes);r,t=tr[tail.lower()]
    tail_hp=f.mesh.child(f.mesh.child(nodes[0],tail),'Hardpoints')
    for item in p['hardpoints']:
        found=[]
        for file in names:
            hp=next((n for n in f.mesh.child(nodes[0],file).children if n.name=='Hardpoints'),None)
            if hp:
                for kind in hp.children:
                    for node in kind.children:
                        if node.name.lower()==item['name'].lower():found.append((kind,node))
        assert len(found)==1,item['name']
        kind,node=found[0];kind.children.remove(node)
        target_kind=next(k for k in tail_hp.children if k.name==kind.name);target_kind.children.append(node)
        target=np.array(item['position'])+shift
        f.mesh.child(node,'Position').blob=(r.T@(target-t)).astype('<f4').tobytes()
        f.mesh.child(node,'Orientation').blob=(r.T@np.array(item['orientation'])).astype('<f4').tobytes()
    after_hp=f.hp_world(nodes)
    moved={h['name'].lower():h for h in p['hardpoints']}
    for key,hp in before_hp.items():
        if key=='dpbreak':continue
        expected=np.array(moved.get(key,hp)['position'])+shift
        assert np.allclose(after_hp[key]['position'],expected,atol=3e-6),key
    split=assembly['split']
    for key in ('cut_y','cut_top_y'):split[key]+=float(shift[1])
    split['cut_loops']=[(np.array(loop)+shift).tolist() for loop in split['cut_loops']]
    for cut in split['cuts']:cut['points']=(np.array(cut['points'])+shift).tolist()
    assembly.update(original=p['original'],center_shift_native=shift.tolist(),pivot=(np.array(assembly['pivot'])+shift).tolist(),
                    approved_tail_blend_sha256=verified['blend_sha256'],base_cmp_sha256=p['base_cmp_sha256'],
                    installed_before_sha256=f.digest(f.base.SOURCE),tail_pylon_bounds=[])
    for entry in p['objects'][1:]:
        pts=np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in entry['groups']])
        assembly['tail_pylon_bounds'].append([pts.min(0).tolist(),pts.max(0).tolist()])
    assembly['lod0_triangles']=sum(len(g['corners']) for gs in levels[0].values() for g in gs)
    (OUT/'assembly.json').write_text(json.dumps(assembly,indent=2),encoding='utf8')
    f.write_geometry(nodes,levels)
    descriptions=damage.damage(nodes);damage.config(descriptions);damage.shared_materials(nodes)
    assert original_flat=={path:n.blob for path,n in f.mesh.walk(nodes) if '/Animation/' in path}
    f.DEST.write_bytes(f.mesh.write_tree(header,nodes))
    damage.collision(nodes);f.export_lod0(nodes);damage.review(nodes,descriptions)
    manifest=dict(cmp_before_sha256=p['base_cmp_sha256'],cmp_sha256=f.digest(f.DEST),shared_mat_sha256=f.digest(f.SHARED_MAT),
                  source_mat=str(f.SHARED_MAT),source_mat_sha256=f.digest(f.SHARED_MAT),lod_mat=str(f.LOD_MAT),lod_mat_sha256=f.digest(f.LOD_MAT))
    (OUT/'materials_manifest.json').write_text(json.dumps(manifest,indent=2))
    report=dict(cmp_sha256=f.digest(f.DEST),prototype_sha256=verified['blend_sha256'],added_triangles_per_lod=p['added_triangles'],
                center_shift_native=shift.tolist(),animation_bytes_unchanged=True,hardpoints_translated=True,
                lod_triangles=[sum(len(g['corners']) for gs in level.values() for g in gs) for level in levels])
    (OUT/'tail_integration.json').write_text(json.dumps(report,indent=2))
    print('INTEGRATED',report,flush=True)


if __name__=='__main__':main()
