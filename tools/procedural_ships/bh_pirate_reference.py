"""Read current BH pirate sources and render offline concept references only."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

import bh_family_audit as b

a = b.a
layout = b.layout
OUT = layout.TOPIC / 'bh_family/pirate'
SOURCES = [('fighter_basis', 'bh_fighter'), ('elite', 'bh_elite_pir'),
           ('vheavy_fighter', 'bh_elite2_pir')]


def main():
    assert shutil.disk_usage(OUT.parent).free > 1024**3
    active = {}
    ini_paths = []
    for _, values in a.source.sections(a.source.GAME/'bin/freelancer.ini'):
        for rel in values.get('ships', []):
            path = a.source.DATA/rel
            ini_paths.append(path)
            for kind, row in a.source.sections(path):
                if kind == 'ship':
                    active[row['nickname'][0].lower()] = row
    records, loaded = {}, {}
    for key, alias in SOURCES:
        values = active[alias]
        spec = dict(model=values['da_archetype'][0].replace('\\', '/'),
                    materials=[p.replace('\\', '/') for p in values['material_library']])
        path = a.source.DATA/spec['model']
        scene, mats, stats = a.source.load(spec)
        scene = [dict(g, part=g['part'].lower()) for g in scene]
        _, nodes = a.source.mesh.read_tree(path.read_bytes())
        flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
        constructs = a.full.constructs(flat)
        channels = a.full.channels(flat, constructs)
        door_script = values['bay_door_anim'][0].lower()
        used = [c for c in channels if c['script'] in (a.SCRIPT, 'sc_launch extend', door_script)]
        assert all(c['native_size_valid'] and c['bound_joint'] and c['finite']
                   and c['monotonic_times'] and not c.get('parent_mismatch') for c in used)
        record = dict(path=spec['model'], constructs=constructs, channels=channels)
        wing = [c for c in channels if c['script'] == a.SCRIPT]
        duration = max(c['duration'] for c in wing)
        flight = a.motion.scene_at(record, scene, 0, a.SCRIPT)
        stowed = a.motion.scene_at(record, scene, duration, a.SCRIPT)
        launch_end = max(c['duration'] for c in channels if c['script']=='sc_launch extend')
        launched = a.motion.scene_at(record, scene, launch_end, 'sc_launch extend')
        delta = max(float(np.abs(g['corners']-h['corners']).max()) for g,h in zip(flight,launched))
        assert delta < 1e-8
        center, radius = layout.frame(flight)
        folder = OUT/'references'/key
        folder.mkdir(parents=True, exist_ok=True)
        def render(pose, cam, origin=center, extent=radius, size=500):
            return a.source.render(pose,mats,origin,extent,cam,size,'texture')
        cams = b.CAMS
        layout.sheet(folder/'native_flight.jpg', [[(label,render(flight,cam))
                     for cam,label in cams[i:i+2]] for i in (0,2,4)], 2,
                     alias+' / CURRENT MOD / FLIGHT',
                     'Original CMP; fighter is REGULAR source because pirate CMP is absent.',size=500)
        glass = [g for g in flight if 'glass' in mats[g['material']]['name'].lower()]
        cc, cr = layout.frame(glass)
        layout.sheet(folder/'cockpit_reference.jpg', [[(label,render(flight,cam,cc,cr*1.6,550))
                     for cam,label in cams[:1]+cams[2:3]+cams[4:5]]],3,
                     alias+' / ORIGINAL COCKPIT / DO NOT REDESIGN GLAZING',
                     'Camera crop only, not a production cabin extraction.',size=550)
        layout.sheet(folder/'native_motion.jpg', [[(label,render(pose,cam))
                     for pose,label in [(flight,'FLIGHT'),(stowed,'STOWED')]]
                     for cam in [(0,0,-1),(1,0,0)]],2,alias+' / NATIVE FOLDING',
                     'Forward wing script stows; new concept clearances are not validated.',size=500)
        assets=[path]+[a.source.DATA/p for p in spec['materials']]+[a.source.DATA/values['cockpit'][0]]
        rows=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in assets]
        oldpath=layout.TOPIC/'pirate_art/ships'/alias/'source.json'
        old=json.loads(oldpath.read_text(encoding='utf8')) if oldpath.exists() else None
        regular_key='fighter' if key=='fighter_basis' else key
        regular=json.loads((layout.TOPIC/'bh_family'/regular_key/'source_audit.json').read_text(encoding='utf8'))
        glass_hash=hashlib.sha256(np.round(b.points(glass),6).tobytes()).hexdigest()
        report=dict(alias=alias,source_model=path.as_posix(),source_sha256=stats['sha256'],
                    source_role='regular_fighter_basis' if key=='fighter_basis' else 'actual_pirate_model',
                    archetype={k:values.get(k) for k in ('nickname','da_archetype','material_library','cockpit','bay_door_anim')},
                    assets=rows,constructs=constructs,channels=channels,
                    analyzed_channels_valid=True,wing_duration=duration,
                    flight_bounds=layout.bounds(flight),stowed_bounds=layout.bounds(stowed),
                    cockpit_glazing_triangles=sum(len(g['corners']) for g in glass),
                    cockpit_glazing_geometry_sha256=glass_hash,
                    glazing_matches_regular=glass_hash==regular['glazing_geometry_sha256'],
                    launch_to_flight_max_delta=delta,
                    matches_previous_pirate_audit=old['sha256']==stats['sha256'] if old else None,
                    source_unchanged=a.sha(path)==stats['sha256'])
        assert report['source_unchanged']
        b.write(folder/'source_audit.json',report)
        records[key]=report
        loaded[key]=(flight,mats,center,radius)
        print(alias,'glass',report['cockpit_glazing_triangles'],'old audit',report['matches_previous_pirate_audit'],flush=True)
    radius=max(row[3] for row in loaded.values())
    layout.sheet(OUT/'references/family_comparison.jpg', [[
        (alias+' / '+label,a.source.render(loaded[key][0],loaded[key][1],loaded[key][2],radius,cam,550,mode))
        for key,alias in SOURCES] for cam,mode,label in [(b.CAMS[0][0],'texture','FRONT 3/4'),
        (b.CAMS[1][0],'texture','REAR 3/4'),((1,0,0),'clay','SIDE')]],3,
        'BH PIRATE SOURCES / FIGHTER USES REGULAR BASIS',
        'Original meshes at native flight pose; no new geometry or game installation.',size=550)
    b.write(OUT/'source_manifest.json',dict(date='2026-11-19',models=records,
        pirate_fighter_archetype_present='bh_fighter_pir' in active,
        pirate_fighter_cmp_present=(a.source.DATA/'ships/bounty_hunter/bh_pir_fighter/bh_pir_fighter.cmp').exists(),
        ini_sources=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in ini_paths],
        runtime_controller=dict(path=(a.source.REPO/'src/freelancer/Client/wing_anim.h').as_posix()) if hasattr(a.source,'REPO') else 'src/freelancer/Client/wing_anim.h',
        model_changed=False,installed=False))


if __name__=='__main__':
    main()
