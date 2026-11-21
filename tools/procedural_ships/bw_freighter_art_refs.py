"""Offline native BW pirate freighter references; never writes game assets."""
import json
import shutil
from pathlib import Path

import numpy as np

import bw_family_audit as family

a = family.a
OUT = family.OUT / 'freighter'


def main():
    free = shutil.disk_usage(family.OUT).free
    if free < 1024**3:
        raise OSError('Insufficient free space for reference renders')
    OUT.mkdir(parents=True, exist_ok=True)
    alias = 'bw_freighter_pir'
    active = {}
    ini_sources = [p for _, v in a.source.sections(a.source.GAME / 'bin/freelancer.ini')
                   for p in v.get('ships', [])]
    for ini in ini_sources:
        for kind, values in a.source.sections(a.source.DATA / ini):
            if kind == 'ship':
                active[values['nickname'][0].lower()] = dict(values, source_ini=ini)
    values = active[alias]
    spec = dict(model=values['da_archetype'][0].replace('\\', '/').lower(),
                materials=[p.replace('\\', '/').lower() for p in values['material_library']])
    path = a.source.DATA / spec['model']
    old = json.loads((a.OUT / 'ships' / alias / 'source.json').read_text(encoding='utf8'))
    assert a.sha(path) == old['sha256'], 'Review changed source before reusing old audit'
    scene, mats, stats = a.source.load(spec)
    scene = [dict(g, part=g['part'].lower()) for g in scene]
    _, nodes = a.source.mesh.read_tree(path.read_bytes())
    flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
    constructs = a.full.constructs(flat)
    channels = a.full.channels(flat, constructs)
    assert all(c['native_size_valid'] and c['bound_joint'] and c['finite']
               and c['monotonic_times'] and not c.get('parent_mismatch') for c in channels)
    names = {a.source.mesh.string(b).lower(): a.source.mesh.string(
             flat[p.rsplit('/', 1)[0] + '/object name']).lower()
             for p, b in flat.items() if '/cmpnd/' in p and p.endswith('/file name')}
    record = dict(path=spec['model'], constructs=constructs, channels=channels)
    wing = [c for c in channels if c['script'] == a.SCRIPT]
    duration = max(c['duration'] for c in wing)
    times = np.linspace(0, duration, 5).tolist()
    poses = [a.motion.scene_at(record, scene, t, a.SCRIPT) for t in times]
    flight = poses[0]
    direct = a.source.load(spec, pose=(a.SCRIPT, 0))[0]
    delta = max(float(np.abs(g['corners'] - h['corners']).max()) for g, h in zip(flight, direct))
    launch_duration = max(c['duration'] for c in channels if c['script'] == 'sc_launch extend')
    launch = a.motion.scene_at(record, scene, launch_duration, 'sc_launch extend')
    launch_delta = max(float(np.abs(g['corners'] - h['corners']).max()) for g, h in zip(flight, launch))
    assert max(delta, launch_delta) < 1e-8
    center, radius = family.frame(flight)

    def render(pose, cam, mode='texture', origin=center, extent=radius, size=700):
        return a.source.render(pose, mats, origin, extent, cam, size, mode)

    cams = [((1, .6, -1.4), 'FRONT 3/4'), ((-1, .5, 1.3), 'REAR 3/4'),
            ((0, 1, .000001), 'TOP'), ((1, 0, 0), 'SIDE'),
            ((0, 0, -1), 'FRONT'), ((0, 0, 1), 'REAR / THREE ENGINES')]
    for mode, filename in [('texture', 'native_flight.jpg'), ('clay', 'native_shape.jpg')]:
        rows = [[(label, render(flight, cam, mode)) for cam, label in cams[i:i+2]]
                for i in range(0, 6, 2)]
        family.sheet(OUT / filename, rows, 2, 'BW PIR FREIGHTER / NATIVE FLIGHT',
                     'Installed CMP / software render / unchanged source geometry', size=700)
    glass = [g for g in flight if 'glass' in mats[g['material']]['name'].lower()]
    cc, cr = family.frame(glass)
    cabin_cams = [((.8, .55, -1.2), '3/4'), ((1, 0, 0), 'SIDE'),
                  ((0, 1, .000001), 'TOP'), ((0, 0, -1), 'FRONT')]
    family.sheet(OUT / 'cockpit_reference.jpg', [[
        (label, render(flight, cam, origin=cc, extent=cr*1.7)) for cam, label in cabin_cams[i:i+2]]
        for i in (0, 2)], 2, 'BW FREIGHTER / IMMUTABLE NATIVE CABIN',
        'Entire shell and three glazing panes must remain; glass bounds are NOT cabin limits.', size=700)
    family.sheet(OUT / 'native_wing_motion.jpg', [[
        (f'{label} / {times[i]:.2f}s', render(poses[i], cam))
        for i, label in [(0, 'FLIGHT'), (2, 'RETRACTING'), (4, 'STOWED')]]
        for cam in [(0, 0, -1), (0, 1, .000001)]], 3,
        'BW FREIGHTER / TRANSLATING SIDE SECTIONS', 'Flight to stowed: inward 2.5 / up 0.1 / aft 1.0', size=700)
    ds = values['bay_door_anim'][0].lower()
    doors = [c for c in channels if c['script'] == ds]
    dd = max(c['duration'] for c in doors)
    held = [dict(c, script=ds, times=[0, dd], values=[c['first'], c['first']]) for c in wing]
    dr = dict(record, channels=doors + held)
    door_poses = [a.motion.scene_at(dr, scene, t, ds) for t in np.linspace(0, dd, 5)]
    door_parts = {c['child'].lower() for c in doors}
    family.sheet(OUT / 'native_baydoor_motion.jpg', [[
        (label, render(pose, (.7, 1.2, -.6)))
        for label, pose in [('CLOSED', door_poses[0]), ('OPEN / TWO 45-DEGREE LEAVES', door_poses[-1])]]],
        2, 'BW FREIGHTER / UPPER CARGO HATCH', 'Native parents and rotation; wings held in flight.', size=700)
    parts = []
    for name in sorted({g['part'] for g in scene}):
        states = [[g for g in p if g['part'] == name] for p in poses]
        b0, b1 = family.bounds(states[0]), family.bounds(states[-1])
        parts.append(dict(file=name, object=names[name], flight=b0, stowed=b1,
                          center_delta_stow=((np.array(b1['min'])+b1['max']-b0['min']-b0['max'])/2).tolist()))
    assets = [path] + [a.source.DATA / p for p in spec['materials']] + [a.source.DATA / values['cockpit'][0]]
    report = dict(alias=alias, source_model=path.as_posix(), source_sha256=a.sha(path),
                  archetype=values, assets=[dict(path=p.as_posix(), sha256=a.sha(p)) for p in assets],
                  disk_free_before=free, constructs=constructs, channels=channels, parts=parts,
                  phase_bounds=[family.bounds(p) for p in poses], wing_times=times,
                  door_phase_bounds=[family.bounds([g for g in p if names[g['part']] in door_parts]) for p in door_poses],
                  cockpit_glazing_bounds=family.bounds(glass), source_stats=stats,
                  launch_to_flight_max_delta=launch_delta, independent_pose_loader_max_delta=delta,
                  all_bindings_valid=True, source_unchanged=a.sha(path)==old['sha256'],
                  caveats=['Installed mod, not authenticated retail.',
                           'Offline software render, not in-game, no future-model collision proof.',
                           'Cabin includes surrounding original hull, not only separate glass part.'])
    family.write_json(OUT / 'source_audit.json', report)
    print('Source unchanged:', report['source_unchanged'], 'flight:', report['phase_bounds'][0]['dimensions'])
    print('Saved references:', OUT)


if __name__ == '__main__':
    main()
