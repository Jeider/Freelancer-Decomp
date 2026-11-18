"""Read current Liberty assets and render source references for concept design.

Offline only: no geometry changes, game launch, Blender or DATA writes.
"""
import collections
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import ImageDraw

import pirate_art_audit as a
from bw_family_audit import bounds, frame, sheet, write_json
from rh_redesign_paths import TOPIC

OUT = TOPIC/'li_elite'
REFS = OUT/'references'
ART = Path('D:/work/ART_SHIP/LI')
CAMS = [((-1, .65, -1.4), 'FRONT 3/4'), ((1, .5, 1.4), 'REAR 3/4'),
        ((0, 1, .000001), 'TOP'), ((-1, 0, 0), 'SIDE'),
        ((0, 0, -1), 'FRONT'), ((-1, .65, -1.4), 'SHAPE')]


def active_ships():
    rows = {}
    for _, section in a.source.sections(a.source.GAME/'bin/freelancer.ini'):
        for ini in section.get('ships', []):
            for kind, values in a.source.sections(a.source.DATA/ini):
                if kind == 'ship':
                    rows[values['nickname'][0].lower()] = dict(values, source_ini=ini)
    return rows


def read_ship(alias, values):
    source = dict(model=values['da_archetype'][0].replace('\\', '/').lower(),
                  materials=[x.replace('\\', '/').lower() for x in values['material_library']])
    path = a.source.DATA/source['model']
    scene, mats, stats = a.source.load(source)
    scene = [dict(g, part=g['part'].lower()) for g in scene]
    _, nodes = a.source.mesh.read_tree(path.read_bytes())
    flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
    constructs = a.full.constructs(flat)
    channels = a.full.channels(flat, constructs)
    invalid = [c for c in channels if not (c['native_size_valid'] and c['bound_joint'] and c['finite']
               and c['monotonic_times'] and not c.get('parent_mismatch'))]
    if alias == 'li_elite_pir':
        assert not invalid
    else:
        # Other installed LI originals have malformed legacy sc_end anim
        # channels. Their wing flight poses are valid; retain the unrelated
        # findings rather than claiming the comparison assets are fully valid.
        assert all(c['script'] == 'sc_end anim' for c in invalid)
    stats['non_pose_channel_warnings'] = [dict(script=c['script'], child=c['child'],
        native_size_valid=c['native_size_valid']) for c in invalid]
    names = {a.source.mesh.string(b).lower(): a.source.mesh.string(
             flat[p.rsplit('/', 1)[0]+'/object name']).lower()
             for p, b in flat.items() if '/cmpnd/' in p and p.endswith('/file name')}
    record = dict(path=source['model'], constructs=constructs, channels=channels)
    flight = a.motion.scene_at(record, scene, 0, a.SCRIPT)
    return source, path, scene, mats, stats, record, names, flight


def glass_boundary(glass):
    counts = collections.Counter()
    for g in glass:
        for tri in g['corners'][..., :3]:
            keys = [tuple(np.round(v, 5)) for v in tri]
            for i in range(3):
                counts[tuple(sorted((keys[i], keys[(i+1)%3])))] += 1
    edges = [e for e, n in counts.items() if n == 1]
    adjacent = collections.defaultdict(set)
    for p, q in edges:
        adjacent[p].add(q); adjacent[q].add(p)
    remaining, components = set(adjacent), []
    while remaining:
        seed = next(iter(remaining)); visited = {seed}; queue = [seed]
        while queue:
            for v in adjacent[queue.pop()]:
                if v not in visited:
                    visited.add(v); queue.append(v)
        remaining.difference_update(visited)
        components.append(sorted(visited))
    return edges, components, dict(collections.Counter(len(v) for v in adjacent.values()))


def main():
    free = shutil.disk_usage(TOPIC).free
    assert free > 512*1024**2
    REFS.mkdir(parents=True, exist_ok=True)
    art_names = ['l_fighter .jpg', 'libertysheet.jpg', 'freighter new perspective.jpg',
                 'l_cruiser.jpg', 'l_battleship1.jpg']
    art_records = []
    for name in art_names:
        dest = REFS/name
        shutil.copyfile(ART/name, dest)
        art_records.append(dict(source=(ART/name).as_posix(), copy=dest.as_posix(), sha256=a.sha(dest)))
    active = active_ships()
    source, path, scene, mats, stats, record, names, flight = read_ship('li_elite_pir', active['li_elite_pir'])
    old = json.loads((a.OUT/'ships/li_elite_pir/source.json').read_text(encoding='utf8'))
    assert stats['sha256'] == old['sha256'], 'Installed source changed: review before reusing older audit'
    wing = [c for c in record['channels'] if c['script'] == a.SCRIPT]
    duration = max(c['duration'] for c in wing)
    times = np.linspace(0, duration, 5).tolist()
    poses = [a.motion.scene_at(record, scene, t, a.SCRIPT) for t in times]
    center, radius = frame(flight)
    def render(pose, cam, size=600, mode='texture', origin=center, extent=radius, materials=mats):
        return a.source.render(pose, materials, origin, extent, cam, size, mode)
    rows = [[(CAMS[j][1], render(flight, CAMS[j][0], mode='clay' if j == 5 else 'texture'))
             for j in range(i*2, i*2+2)] for i in range(3)]
    sheet(REFS/'native_flight.jpg', rows, 2, 'LI PIR ELITE / CURRENT SOURCE / DEPLOYED FLIGHT',
          'Original CMP; matched framing; software shading, not in-game imagery.', size=600)
    sheet(REFS/'native_wing_motion.jpg', [[
        (f'{label} / t={times[i]:.2f}', render(poses[i], cam))
        for i, label in [(0, 'FLIGHT'), (2, 'FOLDING'), (4, 'STOWED')]]
        for cam in [CAMS[0][0], CAMS[2][0], CAMS[4][0]]], 3,
        'LI PIR ELITE / THREE CHAINED FAN LEAVES PER SIDE',
        'Native script: forward folds; reverse extends. Fixed camera and scale.', size=600)
    door_script = active['li_elite_pir']['bay_door_anim'][0].lower()
    doors = [c for c in record['channels'] if c['script'] == door_script]
    door_duration = max(c['duration'] for c in doors)
    held = [dict(c, script=door_script, times=[0, door_duration], values=[c['first'], c['first']]) for c in wing]
    door_record = dict(record, channels=doors+held)
    door_poses = [a.motion.scene_at(door_record, scene, t, door_script)
                  for t in np.linspace(0, door_duration, 5)]
    door_parts = {c['child'].lower() for c in doors}
    dc, rr = frame([g for p in door_poses for g in p if names[g['part']] in door_parts])
    sheet(REFS/'native_baydoor_motion.jpg', [[
        (label, render(pose, (-.65, 1.4, -.7), origin=dc, extent=max(rr*1.55, 3.3)))
        for label, pose in [('CLOSED', door_poses[0]), ('OPEN / native angles', door_poses[-1])]]],
        2, 'LI PIR ELITE / TOP BAYDOOR / WINGS HELD OPEN',
        'Actual parent bindings and keys; no future-design clearance proof.', size=600)
    glass = [g for g in flight if 'glass' in mats[g['material']]['name'].lower()]
    cc, cr = frame(glass)
    ccams = [CAMS[0], CAMS[2], CAMS[4], CAMS[3]]
    neutral = {k:dict(v, image=None, colour=np.ones(3)) for k,v in mats.items()}
    for material_set, filename in [(mats, 'native_cockpit_textured.jpg'), (neutral, 'native_cockpit_shape.jpg')]:
        sheet(REFS/filename, [[(label, render(flight, cam, origin=cc, extent=cr*1.5, materials=material_set))
                              for cam, label in ccams[i*2:i*2+2]] for i in range(2)],
              2, 'LI PIR ELITE / IMMUTABLE SOURCE CABIN / FOUR VIEWS',
              'Original shell and glass. Framing is based on glazing bounds, not a cabin-mesh extraction.', size=600)
    edges, components, degrees = glass_boundary(glass)
    rows = []
    for ri in range(2):
        row = []
        for cam, label in ccams[ri*2:ri*2+2]:
            im = render(glass, cam, origin=cc, extent=cr*1.5)
            f = np.array(cam)/np.linalg.norm(cam); r = np.cross([0,1,0], f); r /= np.linalg.norm(r)
            rot = np.stack((r, np.cross(f,r), f)); draw = ImageDraw.Draw(im)
            for edge in edges:
                q = (np.array(edge)-cc)@rot.T
                xy = q[:,:2]*600*.46/(cr*1.5); xy[:,0] += 300; xy[:,1] = 300-xy[:,1]
                draw.line([tuple(v) for v in xy], fill=(94,200,220), width=2)
            row.append((label, im))
        rows.append(row)
    sheet(REFS/'native_glass_contours.jpg', rows, 2, 'LI ELITE / TRUE GLASS BOUNDARIES',
          'Boundary edges only; no invented intermediate mullions. Hidden contours also shown.', size=600)
    direct = a.source.load(source, pose=(a.SCRIPT,0))[0]
    direct_delta = max(float(np.abs(g['corners']-h['corners']).max()) for g,h in zip(flight,direct))
    launch_duration = max(c['duration'] for c in record['channels'] if c['script']=='sc_launch extend')
    launch = a.motion.scene_at(record,scene,launch_duration,'sc_launch extend')
    launch_delta = max(float(np.abs(g['corners']-h['corners']).max()) for g,h in zip(flight,launch))
    # The motion helper undoes float32 native rotations by transpose. Chained
    # LI fan rotations are only approximately orthonormal: observed drift is
    # 7.45e-7 model units. Keep that measured precision visible in the report.
    assert direct_delta < 1e-6 and launch_delta < 1e-8
    transforms = a.full.matrices(record['constructs'])
    wing_info = []
    for c in wing:
        axis = np.array(c['axis'])
        wing_info.append(dict(child=c['child'], parent=c['parent'], axis=c['axis'],
             world_axis=(transforms[c['child'].lower()][0]@axis).tolist(),
             degrees_first_last=np.degrees([c['first'][0],c['last'][0]]).tolist()))
    part_bounds = []
    for part in sorted({g['part'] for g in scene}):
        subset = lambda pose: [g for g in pose if g['part']==part]
        part_bounds.append(dict(file=part,object=names[part],flight=bounds(subset(flight)),
                                stowed=bounds(subset(poses[-1]))))
    assets = [path]+[a.source.DATA/x for x in source['materials']]+[a.source.DATA/active['li_elite_pir']['cockpit'][0]]
    report = dict(alias='li_elite_pir',source_model=path.as_posix(),source_sha256=stats['sha256'],
        archetype=active['li_elite_pir'],assets=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in assets],
        source_stats=stats,constructs=record['constructs'],channels=record['channels'],
        parts=part_bounds,wing_summary=wing_info,wing_times=times,phase_bounds=[bounds(p) for p in poses],
        door_phase_bounds=[bounds([g for g in p if names[g['part']] in door_parts]) for p in door_poses],
        glazing_bounds=bounds(glass),glazing_triangles=sum(len(g['corners']) for g in glass),
        glass_boundary_edges=edges,glass_boundary_components=components,glass_boundary_vertex_degrees=degrees,
        independent_pose_loader_max_delta=direct_delta,launch_to_flight_max_delta=launch_delta,
        independent_pose_tolerance=1e-6,
        source_unchanged=a.sha(path)==stats['sha256'],all_channel_bindings_valid=True,
        earlier_audit_phase_dimensions=old['phase_dimensions_xyz'],
        caveats=['Current installed mod, not authenticated retail.',
                 'Case-normalized part bindings; old general sheets may show wrong wing state.',
                 'Offline renders do not emulate glass/envmap or validate back-face culling or collisions.'])
    write_json(OUT/'source_audit.json',report)
    family = []
    for alias in ['li_fighter','li_elite','li_freighter','li_elite_pir']:
        src,p,rest,mm,ss,rr,nn,ff = read_ship(alias,active[alias])
        ctr,rad = frame(ff)
        family.append((alias,ff,mm,ctr,rad))
        write_json(REFS/(alias+'_source.json'),dict(alias=alias,path=p.as_posix(),sha256=ss['sha256'],
                   materials=src['materials'],flight_bounds=bounds(ff),source_stats=ss))
    common = max(item[4] for item in family)
    rows = [[(alias+' / '+label,a.source.render(ff,mm,ctr,common,cam,550,'texture'))
             for alias,ff,mm,ctr,rad in family] for cam,label in [CAMS[0],CAMS[3],CAMS[2]]]
    sheet(REFS/'liberty_family_comparison.jpg',rows,4,'LIBERTY / CURRENT INSTALLED MODELS / SAME UNIT SCALE',
          'Fighter, elite, freighter and pirate elite. All native flight poses; no geometry edits.',size=550)
    copies = [dict(path=p.as_posix(),sha256=a.sha(p)) for p in sorted(REFS.glob('*.jpg'))]
    write_json(OUT/'manifest.json',dict(source=report['source_model'],source_sha256=stats['sha256'],
               art=art_records,references=copies,free_bytes_before=free,script='tools/procedural_ships/li_elite_concept_audit.py'))
    print(json.dumps(dict(out=str(OUT),flight=report['phase_bounds'][0]['dimensions'],
          stowed=report['phase_bounds'][-1]['dimensions'],glass_triangles=report['glazing_triangles'],
          glass_boundary_components=len(components),source_unchanged=report['source_unchanged'])))


if __name__ == '__main__':
    main()
