"""Read current F14/source evidence; write analysis metadata only in the topic.

No model export, game writes, installation, Blender or game launch.
"""
import collections
import hashlib
import json
from pathlib import Path

import numpy as np

import pirate_art_audit as a
from rh_fighter_concept_refs import bounds


OUT = a.TOPIC / 'rh_fighter' / 'analysis'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    selection = json.loads((OUT.parent / 'selection.json').read_text(encoding='utf8'))
    previous = json.loads((OUT.parent / 'source_audit.json').read_text(encoding='utf8'))
    art = OUT.parent / selection['art']
    assert sha(art) == selection['art_sha256']
    cfg = None
    for section, values in a.source.sections(a.source.GAME / 'bin/freelancer.ini'):
        for ini in values.get('ships', []):
            for kind, row in a.source.sections(a.source.DATA / ini):
                if kind == 'ship' and row.get('nickname') == ['rh_fighter_pir']:
                    cfg = dict(row, source_ini=ini)
    assert cfg, 'Active fighter archetype not found'
    source = dict(model=cfg['da_archetype'][0].replace('\\', '/'),
                  materials=[p.replace('\\', '/') for p in cfg['material_library']])
    path = a.source.DATA / source['model']
    assert sha(path) == selection['source_sha256'], 'Source changed since selected concept'
    scene, mats, stats = a.source.load(source)
    scene = [dict(g, part=g['part'].lower()) for g in scene]
    _, nodes = a.source.mesh.read_tree(path.read_bytes())
    flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
    names = {a.source.mesh.string(b).lower(): a.source.mesh.string(
        flat[p.rsplit('/', 1)[0] + '/object name'])
        for p, b in flat.items() if '/cmpnd/' in p and p.endswith('/file name')}
    constructs = a.full.constructs(flat)
    channels = a.full.channels(flat, constructs)
    assert all(c['native_size_valid'] and c['bound_joint'] and c['finite']
               and c['monotonic_times'] and not c.get('parent_mismatch') for c in channels)
    record = dict(path=source['model'], constructs=constructs, channels=channels)
    flight = a.motion.scene_at(record, scene, 0, a.SCRIPT)
    folded = a.motion.scene_at(record, scene, 2, a.SCRIPT)
    launch = a.motion.scene_at(record, scene, 7, 'sc_launch extend')
    delta = max(float(np.abs(g['corners'][..., :3] - h['corners'][..., :3]).max())
                for g, h in zip(flight, launch))
    assert delta < 1e-6
    joint_positions = {}
    for pose, endpoint in [('flight', 'first'), ('folded', 'last')]:
        values = {c['child'].lower(): c[endpoint] for c in channels if c['script'] == a.SCRIPT}
        matrices = a.full.matrices(constructs, values)
        joint_positions[pose] = {j['name']: matrices[j['name'].lower()][1].tolist()
                                 for j in constructs if 'wing' in j['name'].lower()}
    parts = []
    for part in sorted(names):
        group = [g for g in flight if g['part'] == part]
        if group:
            parts.append(dict(file=part, object=names[part],
                              triangles=sum(len(g['corners']) for g in group),
                              flight=bounds(group), folded=bounds(
                                  [g for g in folded if g['part'] == part])))
    hp = []
    for p, blob in flat.items():
        if '/hardpoints/' not in p or not p.endswith('/position'):
            continue
        file = p.split('/')[2]
        base = p.rsplit('/', 1)[0]
        hp.append(dict(name=p.split('/')[-2], object=names.get(file, file),
                       local_position=np.frombuffer(blob, '<f4').tolist(),
                       orientation=np.frombuffer(flat[base + '/orientation'], '<f4').tolist()
                       if base + '/orientation' in flat else None))
    door = next(c for c in channels if c['script'] == 'sc_open baydoor')
    dr = dict(record, channels=[door])
    door_poses = [a.motion.scene_at(dr, scene, t, door['script']) for t in (0, door['duration'])]
    door_bounds = [bounds([g for g in pose if names[g['part']].lower() == 'baydoor_lod1'])
                   for pose in door_poses]
    all_door = [g for pose in door_poses for g in pose
                if names[g['part']].lower() == 'baydoor_lod1']
    missing = []
    for g in scene:
        if mats[g['material']]['kind'] == 'MISSING':
            missing.append(dict(material_crc=f"0x{g['material']:08x}",
                                object=names[g['part']], triangles=len(g['corners'])))
    paths = [path, path.with_suffix('.sur'), art,
             a.source.GAME / 'bin/freelancer.ini', a.source.DATA / cfg['source_ini']]
    paths += [a.source.DATA / p for p in source['materials'] + cfg.get('cockpit', [])]
    paths += [Path('src/freelancer/Client/wing_anim.h'),
              Path('src/freelancer/Client/wing_anim.cpp'), Path('src/Common/common_cship.cpp')]
    recipe = Path('docs/ru/ship_design/prompt_archive/selected/rh_fighter_F14.json')
    recipe_data = json.loads(recipe.read_text(encoding='utf8'))
    paths.append(recipe)
    refs = []
    for ref in recipe_data['references'] + [recipe_data['selected_output']]:
        archived = Path(ref['archived_path'])
        current = Path(ref['original_path'])
        refs.append(dict(archived=archived.as_posix(), original=current.as_posix(),
                         expected_sha256=ref['sha256'],
                         archived_matches=sha(archived) == ref['sha256'],
                         original_matches=sha(current) == ref['sha256']))
    assert all(r['archived_matches'] and r['original_matches'] for r in refs)
    paths = list(dict.fromkeys(paths))
    assets = [dict(path=p.as_posix(), sha256=sha(p), bytes=p.stat().st_size) for p in paths]
    old_assets = {p['path'].lower(): p['sha256'] for p in previous['assets']}
    for asset in assets:
        old = old_assets.get(asset['path'].lower())
        if old:
            asset['previous_audit_sha256'] = old
            asset['matches_previous_audit'] = old == asset['sha256']
    report = dict(concept='F14', scope='Read-only current native source and selected concept analysis',
                  assets=assets, archive_reference_checks=refs, active_archetype=cfg,
                  source_stats=stats, parts=parts, hardpoints=hp,
                  hp_owners=dict(collections.Counter(h['object'] for h in hp)),
                  constructs=constructs, channels=channels,
                  wing_joint_world_origins=joint_positions,
                  flight=bounds(flight), folded=bounds(folded),
                  launch_to_flight_max_delta=delta,
                  baydoor=dict(closed=door_bounds[0], opened=door_bounds[1],
                               swept_aabb=bounds(all_door),
                               translation=(np.array(door_bounds[1]['min']) - door_bounds[0]['min']).tolist(),
                               note='Swept AABB of translating native lid, not usable cargo volume or new-geometry clearance proof'),
                  unresolved_material_groups=missing,
                  limitations=['No new geometry or collision-clearance claim',
                               'Installed mod is not authenticated retail',
                               'Historical renders depict hash-identical geometry; shared MAT has its own current hash'])
    OUT.mkdir(parents=True, exist_ok=True)
    assert all(sha(Path(row['path'])) == row['sha256'] for row in assets), 'Source changed during analysis'
    (OUT / 'f14_source_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(dict(triangles=stats['triangles'], hp_count=len(hp),
                          constructs=len(constructs), channels=len(channels),
                          flight=report['flight'], baydoor=report['baydoor'],
                          unresolved_material_groups=missing,
                          changed_assets=[p['path'] for p in assets if p.get('matches_previous_audit') is False],
                          report=str(OUT / 'f14_source_check.json')), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
