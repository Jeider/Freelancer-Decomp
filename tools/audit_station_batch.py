"""Read-only installed asset, source, dev roundtrip and placement verification."""
import hashlib,json,re
from pathlib import Path
import valensia_mega as m
from check_valensia_mega import templates
from sync_story_dev import generator_static,semantic,split_dev

out=m.REPO/'out/stations/station_batch';latest={};rows=[];failures=[]
for path in sorted(out.glob('*/installed.json'),key=lambda p:p.stat().st_mtime_ns):
    installed=json.loads(path.read_text());latest.update(installed['hashes'])
    manifest_path=path.parent/'manifest.json';manifest=json.loads(manifest_path.read_text());config=manifest['config']
    digest=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    for stamp in ('native_check.ok','physics_check.ok')+ (('dock_animation.ok',) if config.get('docks') else ()) + (('panel_animation.ok',) if config.get('panel_rotors') else ()):
        assert (path.parent/stamp).read_text()==digest,(path,stamp)
    source=(m.GAME/config['template']).read_text(encoding='utf-8-sig')
    if config.get('static'):
        assert semantic(generator_static((m.GAME/config['template']).read_bytes()))==semantic((m.GAME/config['instances'][0]['path']).read_text(encoding='utf-8-sig'))
        source=split_dev(source.encode('utf-8'))[0].decode('utf-8')
        placed=[r for r in m.b.placements_from_template(source) if r.name==config['source_prefix'] or r.name.startswith(config['source_prefix']+'_')]
    else:
        parsed=templates(source);assert config['class']+'Original' in parsed
        placed=m.b.placements_from_template(parsed[config['class']])
    assert len(placed)==manifest['after'],config['class']
    for inst in config['instances']:
        live={r.name:r for r in m.b.placements_from_template((m.GAME/inst['path']).read_text(encoding='utf-8-sig'))}
        for row in placed:
            current=live[row.name.replace(config['source_prefix'],inst['prefix'])]
            assert (row.archetype,row.rotate,row.loadout)==(current.archetype,current.rotate,current.loadout),(config['class'],row.name)
            assert all(abs(a+b-c)<.0001 for a,b,c in zip(row.pos,inst['offset'],current.pos)),row.name
        pools=re.findall(r'MAX_POOL (\d+)',(path.parent/'physics_check/result.log').read_text(errors='replace'))
        assert pools and int(pools[-1])<30000
        rows.append(dict(system=inst['system'],station=inst['prefix'],template=config['class'],before=manifest['before'],after=manifest['after'],
            draw_groups_before=sum(c['draw_groups_before'] for c in manifest['components']),draw_groups_after=sum(c['draw_groups_after'] for c in manifest['components']),
            visual_components=len(manifest['components']),collision_components=sum(len(c['bodies']) for c in manifest['components']),
            max_physics_pool=int(pools[-1]),working_docks=len(config.get('dock_model',{}).get('ports',[])),unified_core=bool(config.get('unified_core')),panel_rotors=bool(config.get('panel_rotors'))))
from optimized_station_paths import audit_paths
latest=audit_paths(latest)
for name,digest in latest.items():
    path=m.GAME/name
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:failures.append(name)
assert not failures,failures
report=dict(station_instances=len(rows),template_variants=len({r['template'] for r in rows}),before=sum(r['before'] for r in rows),after=sum(r['after'] for r in rows),
            files_verified=len(latest),failures=failures,stations=rows)
(out/'report.json').write_text(json.dumps(report,indent=2))
lines=['Installed station optimization batch','Pythonlancer generation was not run. Engine binaries were not changed.',
       'Draw-group counts cover merged geometry only; they are not measured FPS.',
       'Native checks: geometry/LODs, SUR loader, physics creation/rays/32 ticks/destruction, visual radius; dock variants also independent front-door animations.',
       'In-game NPC routes and visual appearance still require gameplay verification.','',
       'System | Station | Template | Objects before -> after | Merged draw groups before -> after | Working dock ports']
for r in rows:lines.append(f"{r['system']} | {r['station']} | {r['template']} | {r['before']} -> {r['after']} | {r['draw_groups_before']} -> {r['draw_groups_after']} | {r['working_docks'] or '-'}")
lines+=['',f"TOTAL: {len(rows)} station instances; {report['before']} -> {report['after']} objects; {len(latest)} installed files verified.",
        'Other large groups outside this batch (includes legacy systems and service-point-heavy stations):']
deferred=out/'static_deferred.json'
if deferred.exists():
    for item in json.loads(deferred.read_text()):lines.append(item['system']+' | '+item['prefix']+' | '+str(item['objects'])+' objects | '+item['reason'])
(out/'report.txt').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='stations'},indent=2))
