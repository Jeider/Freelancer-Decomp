"""Restore exactly the B04/03 upper wings, preserving all other B04/04 data."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

import bw_elite_b04 as base

f = base.f
PROTOTYPES = base.TOPIC / 'elite/prototypes'
OUT = PROTOTYPES / 'b04_05'
WINGS = {'bw_port_wingX01_lod1', 'bw_star_wingX01_lod1'}
SOURCES = {
    PROTOTYPES / 'b04_03/geometry.json': '21a3e6f5e1289ec9a1d251357c9bf544eb7d57d83459c515ff2170e16184956b',
    PROTOTYPES / 'b04_04/geometry.json': 'dc50eb070ed55266507207d92641228e416402802fec3def38b327359e1e94fb',
}


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def hp_data(nodes):
    semantics = {k.lower(): v for k, v in f.component_map(nodes).items()}
    return {semantics[p.split('/')[2].lower()] + '/' + p.lower().split('/hardpoints/')[-1]:
            hashlib.sha256(n.blob).hexdigest()
            for p, n in f.mesh.walk(nodes) if '/hardpoints/' in p.lower()}


def main():
    free = shutil.disk_usage(base.ROOT).free
    assert free > 2 * 1024**3
    for path, expected in SOURCES.items():
        assert f.digest(path) == expected, path
    previous = read(PROTOTYPES / 'b04_04/geometry.json')
    old = read(PROTOTYPES / 'b04_03/geometry.json')
    manifest = read(PROTOTYPES / 'b04_04/manifest.json')
    for path, expected in manifest['sources'].items():
        assert f.digest(Path(path)) == expected, path
    data = copy.deepcopy(previous)
    replacements = {o['owner']: o for o in old['objects'] if o['owner'] in WINGS}
    assert len(replacements) == 2
    data['objects'] = [copy.deepcopy(replacements[o['owner']]) if o['owner'] in WINGS else o
                       for o in data['objects']]
    remaining = lambda items: [o for o in items if o['owner'] not in WINGS]
    assert remaining(data['objects']) == remaining(previous['objects'])
    assert data['materials'] == previous['materials']
    for field in ('motion', 'cargo_ray_probes'):
        assert data[field] == previous[field]
    assert {o['owner']: o for o in data['objects'] if o['owner'] in WINGS} == replacements
    data['sources'].update({p.as_posix(): h for p, h in SOURCES.items()})
    world = {}
    for obj in data['objects']:
        world.setdefault(obj['owner'], []).extend(
            dict(g, corners=np.array(g['corners'])) for g in obj['groups'])
    world = {n: f.merge(gs) for n, gs in world.items()}
    used = {str(g['material']) for gs in world.values() for g in gs}
    assert used <= data['materials'].keys()
    assert not any('metal' in (data['materials'][m]['texture'] + ' ' +
                              data['materials'][m]['name']).lower() for m in used)
    pinned = base.TOPIC / 'elite/source/bw_pir_elite_original.cmp'
    header, native = f.mesh.read_tree(pinned.read_bytes())
    assert set(world) == set(f.component_map(native).values())
    OUT.mkdir(parents=True, exist_ok=True)
    export = base.export(header, native, world, ('Sc_extend wing', 0),
                         OUT / 'bw_pir_elite_b04_review_open.cmp')
    _, previous_cmp = f.mesh.read_tree((PROTOTYPES / 'b04_04/bw_pir_elite_b04_review_open.cmp').read_bytes())
    _, current_cmp = f.mesh.read_tree((OUT / 'bw_pir_elite_b04_review_open.cmp').read_bytes())
    assert hp_data(previous_cmp) == hp_data(current_cmp)
    assert export['salt'] != manifest['export']['salt']
    vertices = np.concatenate([g['corners'][..., :3].reshape(-1, 3)
                               for gs in world.values() for g in gs])
    checks = dict(
        unchanged_nonwing_objects=len(remaining(data['objects'])),
        nonwing_objects_sha256=fingerprint(remaining(data['objects'])),
        upper_wings_exactly_match_b04_03=True,
        nonwing_geometry_uv_normals_exactly_match_b04_04=True,
        unchanged_materials_motion_cargo_probes=True,
        exported_hardpoints_exactly_match_b04_04=True,
        restored_wing_objects={o['name']: fingerprint(o) for o in replacements.values()},
    )
    manifest.update(
        stage='static shape prototype with previous upper wings restored, user review pending',
        revision='B04/05', sources=data['sources'], free_disk_before_bytes=free,
        total_triangles=sum(len(g['corners']) for gs in world.values() for g in gs),
        dimensions=np.ptp(vertices, axis=0), export=export,
        reference_priority=['User requests exact B04/03 upper wings with everything else retained from B04/04',
                            'B04_VIEWS_B ELITE REAR', 'B04_VIEWS_A cross-check'],
        authored_changes=['Only the two upper wing objects restored exactly from B04/03'],
        preservation_checks=checks,
    )
    assert manifest['total_triangles'] == 9200
    base.dump(OUT / 'geometry.json', data)
    base.dump(OUT / 'manifest.json', manifest)
    print(json.dumps(dict(output=OUT.as_posix(), triangles=manifest['total_triangles'], checks=checks)))


if __name__ == '__main__':
    main()
