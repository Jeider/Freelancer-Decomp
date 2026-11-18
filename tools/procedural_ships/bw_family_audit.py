"""Read installed BW pirate family, reconstruct native poses and render references.

No model edits, game launch, Blender or DATA writes. Existing broad audit sheets
are retained; these focused references normalize Cmpnd file-name lookup case.
"""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import pirate_art_audit as a
from rh_redesign_paths import TOPIC

OUT = TOPIC / 'bw_family'
SHIPS = [('fighter', 'bw_fighter_pir'), ('elite', 'bw_elite_pir'),
         ('vheavy_fighter', 'bw_elite2_pir')]
ART = Path('D:/work/ART_SHIP/CO/bw_elite.png')
CAMS = [((1, .6, -1.4), 'FRONT 3/4'), ((-1, .5, 1.3), 'REAR 3/4'),
        ((0, 1, .000001), 'TOP'), ((1, 0, 0), 'SIDE'),
        ((0, 0, -1), 'FRONT'), ((1, .6, -1.4), 'SHAPE / no texture')]


def bounds(scene):
    points = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in scene])
    lo, hi = points.min(0), points.max(0)
    return dict(min=lo.tolist(), max=hi.tolist(), dimensions=(hi-lo).tolist())


def frame(scene):
    box = bounds(scene)
    center = (np.array(box['min']) + box['max']) / 2
    points = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in scene])
    return center, float(np.linalg.norm(points-center, axis=1).max())


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def sheet(path, rows, columns, title, footer, size=550):
    im = Image.new('RGB', (columns*size, len(rows)*(size+30)+85), a.BG)
    d = ImageDraw.Draw(im)
    d.text((14, 8), title, font=a.FONT, fill='white')
    for ri, row in enumerate(rows):
        for ci, (label, picture) in enumerate(row):
            x, y = ci*size, 42+ri*(size+30)
            d.text((x+12, y), label, font=a.SMALL, fill='white')
            im.paste(picture, (x, y+28))
    d.text((14, im.height-27), footer, font=a.SMALL, fill='white')
    im.save(path, quality=95)


def main():
    free = shutil.disk_usage(TOPIC).free
    if free < 512*1024**2:
        raise OSError('Insufficient free space for family reference renders')
    OUT.mkdir(parents=True, exist_ok=True)
    refs = OUT / 'references'
    refs.mkdir(exist_ok=True)
    shutil.copyfile(ART, refs/'bw_elite_original.png')
    ini_sources = [p for _, v in a.source.sections(a.source.GAME/'bin/freelancer.ini')
                   for p in v.get('ships', [])]
    active = {}
    for ini in ini_sources:
        for kind, values in a.source.sections(a.source.DATA/ini):
            if kind == 'ship':
                active[values['nickname'][0].lower()] = dict(values, source_ini=ini)
    records, loaded = {}, {}
    for key, alias in SHIPS:
        out = OUT / key
        out.mkdir(exist_ok=True)
        old = json.loads((a.OUT/'ships'/alias/'source.json').read_text(encoding='utf8'))
        values = active[alias]
        model = values['da_archetype'][0].replace('\\', '/').lower()
        assert model == old['model']
        source = dict(model=model, materials=[p.replace('\\', '/').lower()
                      for p in values['material_library']])
        path = a.source.DATA/model
        scene, mats, stats = a.source.load(source)
        assert stats['sha256'] == old['sha256'], 'Source changed since inventory; review it first'
        scene = [dict(g, part=g['part'].lower()) for g in scene]
        _, nodes = a.source.mesh.read_tree(path.read_bytes())
        flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
        constructs = a.full.constructs(flat)
        channels = a.full.channels(flat, constructs)
        assert all(c['native_size_valid'] and c['bound_joint'] and c['finite']
                   and c['monotonic_times'] and not c.get('parent_mismatch') for c in channels)
        record = dict(path=model, constructs=constructs, channels=channels)
        names = {a.source.mesh.string(b).lower(): a.source.mesh.string(
                 flat[p.rsplit('/', 1)[0]+'/object name']).lower()
                 for p, b in flat.items() if '/cmpnd/' in p and p.endswith('/file name')}
        wing = [c for c in channels if c['script'] == a.SCRIPT]
        duration = max(c['duration'] for c in wing)
        times = np.linspace(0, duration, 5).tolist()
        poses = [a.motion.scene_at(record, scene, t, a.SCRIPT) for t in times]
        flight = poses[0]
        direct = a.source.load(source, pose=(a.SCRIPT, 0))[0]
        direct_delta = max(float(np.abs(g['corners']-h['corners']).max())
                           for g, h in zip(flight, direct))
        assert direct_delta < 1e-8
        launch_duration = max(c['duration'] for c in channels if c['script'] == 'sc_launch extend')
        launch = a.motion.scene_at(record, scene, launch_duration, 'sc_launch extend')
        launch_delta = max(float(np.abs(g['corners']-h['corners']).max())
                           for g, h in zip(flight, launch))
        assert launch_delta < 1e-8
        door_script = values['bay_door_anim'][0].lower()
        doors = [c for c in channels if c['script'] == door_script]
        door_duration = max(c['duration'] for c in doors)
        # Keep wings extended while independently evaluating the cargo doors.
        held = [dict(c, script=door_script, times=[0, door_duration],
                     values=[c['first'], c['first']]) for c in wing]
        dr = dict(record, channels=doors+held)
        door_poses = [a.motion.scene_at(dr, scene, t, door_script)
                      for t in np.linspace(0, door_duration, 5)]
        center, radius = frame(flight)
        def render(pose, cam, size=550, mode='texture', origin=center, extent=radius):
            return a.source.render(pose, mats, origin, extent, cam, size, mode)
        rows = []
        for ri in range(3):
            rows.append([(CAMS[j][1], render(flight, CAMS[j][0], mode='clay' if j == 5 else 'texture'))
                         for j in range(ri*2, ri*2+2)])
        sheet(out/'native_flight.jpg', rows, 2, 'BW PIRATE / '+key+' / FLIGHT t=0',
              'Native CMP; shared scale within sheet; software shading; no game capture.')
        rows = [[(f'{label} / t={times[i]:.2f}', render(poses[i], cam))
                 for i, label in [(0, 'FLIGHT'), (2, 'RETRACTING'), (4, 'STOWED')]]
                for cam in [(0, 0, -1), (0, 1, .000001)]]
        sheet(out/'native_wing_motion.jpg', rows, 3, key+' / native translations / front + top',
              'Fixed framing; wing script plays forward to stow, reverse to extend.')
        door_parts = {c['child'].lower() for c in doors}
        focus = [g for p in door_poses for g in p if names[g['part']] in door_parts]
        dc, rr = frame(focus)
        sheet(out/'native_baydoor_motion.jpg', [[
            (label, render(pose, (.65, 1.4, -.7), origin=dc, extent=max(rr*1.7, 3.8)))
            for label, pose in [('CLOSED', door_poses[0]), ('OPEN / two 70-degree leaves', door_poses[-1])]]],
            2, key+' / cargo door / wings held in flight',
            'Native hinge axes and parent bindings; no clearance proof for a future redesign.')
        glass = [g for g in flight if 'glass' in mats[g['material']]['name'].lower()]
        cc, cr = frame(glass)
        sheet(out/'cockpit_reference.jpg', [[(label, render(flight, cam, origin=cc, extent=cr*1.65))
              for cam, label in [((.8, .55, -1.2), 'CABIN 3/4'), ((1, 0, 0), 'CABIN SIDE'),
                                  ((0, 0, -1), 'CABIN FRONT')]]],
              3, key+' / IMMUTABLE ORIGINAL CABIN / shell + glazing',
              'Focus is framed on native glazing; surrounding original shell remains visible; not an extracted cabin mesh.')
        parts = []
        for name in sorted({g['part'] for g in scene}):
            states = [[g for g in p if g['part'] == name] for p in poses]
            object_name = names[name]
            parts.append(dict(file=name, object=object_name, triangles=sum(len(g['corners']) for g in states[0]),
                              flight=bounds(states[0]), stowed=bounds(states[-1]),
                              center_delta_stow=(np.mean([bounds(states[-1])['min'], bounds(states[-1])['max']], axis=0)
                              -np.mean([bounds(states[0])['min'], bounds(states[0])['max']], axis=0)).tolist()))
        assets = [path]+[a.source.DATA/x for x in source['materials']]+[a.source.DATA/values['cockpit'][0]]
        report = dict(alias=alias, source_model=path.as_posix(), source_sha256=stats['sha256'],
                      archetype=values, assets=[dict(path=p.as_posix(), sha256=a.sha(p)) for p in assets],
                      source_stats=stats, constructs=constructs, channels=channels, parts=parts,
                      wing_times=times, phase_bounds=[bounds(p) for p in poses],
                      door_phase_bounds=[bounds([g for g in p if names[g['part']] in door_parts]) for p in door_poses],
                      cockpit_glazing_bounds=bounds(glass),
                      glazing_geometry_sha256=hashlib.sha256(b''.join(np.round(g['corners'], 6).tobytes() for g in glass)).hexdigest(),
                      launch_to_flight_max_delta=launch_delta, independent_pose_loader_max_delta=direct_delta,
                      all_channel_bindings_valid=True, source_unchanged=a.sha(path)==stats['sha256'],
                      earlier_audit_flight_dimensions=old['phase_dimensions_xyz'][0],
                      caveats=['Installed mod, not authenticated retail.',
                               'Part filenames normalized to lowercase before Cmpnd binding; earlier elite sheets missed animated X parts.',
                               'Offline software rendering: no game glass/envmap, back-face culling or collision validation.',
                               'Glass bounds frame the close-up; they are not the full immutable cockpit boundary.'])
        assert report['source_unchanged']
        write_json(out/'source_audit.json', report)
        records[key] = report
        loaded[key] = (flight, mats, center, radius)
        print(key, 'flight/stow', [report['phase_bounds'][i]['dimensions'] for i in (0, -1)], flush=True)
    common_radius = max(v[3] for v in loaded.values())
    rows = []
    for cam, mode, label in [(CAMS[0][0], 'texture', 'FLIGHT'), ((1, 0, 0), 'clay', 'SIDE'),
                              ((0, 0, -1), 'clay', 'FRONT'), ((0, 1, .000001), 'clay', 'TOP')]:
        rows.append([(key+' / '+label, a.source.render(scene, mats, center, common_radius, cam, 550, mode))
                     for key, (scene, mats, center, _) in loaded.items()])
    sheet(refs/'family_comparison.jpg', rows, 3, 'BW PIRATE FAMILY / ACTUAL FLIGHT / SAME UNIT SCALE',
          'fighter -> elite -> vheavy_fighter | native cabins | geometry unchanged | all views at the same scale')
    images = [dict(path=p.relative_to(OUT).as_posix(), sha256=a.sha(p), size=list(Image.open(p).size))
              for p in sorted(OUT.rglob('*')) if p.suffix.lower() in ('.jpg', '.png')]
    write_json(OUT/'manifest.json', dict(disk_free_before=free, primary_art=dict(path=ART.as_posix(), sha256=a.sha(ART)),
        additional_art_context=[dict(path=p.as_posix(), sha256=a.sha(p))
                                for p in sorted(set(ART.parent.glob('*.jpg')))],
        configuration=[dict(path=(a.source.GAME/'bin/freelancer.ini').as_posix(), sha256=a.sha(a.source.GAME/'bin/freelancer.ini'))]
        + [dict(path=(a.source.DATA/p).as_posix(), sha256=a.sha(a.source.DATA/p)) for p in ini_sources],
        ships={k:dict(alias=r['alias'], source_sha256=r['source_sha256'], audit=k+'/source_audit.json') for k,r in records.items()},
        references=images, no_geometry_or_game_changes=True))
    print('Saved', OUT, flush=True)


if __name__ == '__main__':
    main()
