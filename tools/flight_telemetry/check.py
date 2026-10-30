"""Compile the production writer; verify its files with an independent JSON parser."""
from pathlib import Path
import json
import os
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/flight_telemetry_check'
out.mkdir(parents=True, exist_ok=True)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')]))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT',
                '/I'+str(repo/'src/freelancer/Client'), str(repo/'tools/flight_telemetry/check.cpp'),
                str(repo/'src/freelancer/Client/flight_telemetry_recording.cpp'), '/Fecheck.exe'],
               cwd=out, env=env, check=True)
with tempfile.TemporaryDirectory(prefix='flight_данные_', dir=out) as temporary:
    folder = Path(temporary)
    subprocess.run([str(out/'check.exe'), str(folder)], cwd=out, check=True)
    assert {p.name for p in folder.iterdir()} == {
        'flight.jsonl', 'overflow.jsonl', 'restart.jsonl', 'shutdown.jsonl'}

    def read(name):
        raw = (folder/name).read_bytes()
        assert raw.endswith(b'\n')
        rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
        assert rows[0]['schema_version'] == 1
        assert rows[-1]['type'] == 'footer'
        events = rows[1:-1]
        assert [e['sequence'] for e in events] == list(range(len(events)))
        assert [e['wall_us'] for e in events] == sorted(e['wall_us'] for e in events)
        assert rows[-1]['records'] == len(events)
        return rows

    rows = read('flight.jsonl')
    metadata = rows[0]['metadata']
    assert metadata == dict(text='quote" slash\\ line\n tab\t control\x01', nan=None, infinity=None, decimal=1.25)
    assert rows[1]['data']['down'] is True and rows[2]['data']['down'] is False
    assert rows[1]['frame'] == rows[2]['frame'] == 1
    assert len(rows) == 6004 and rows[-2]['data']['index'] == 5999
    assert rows[-1]['complete'] is True and rows[-1]['reason'] == 'test_complete'
    overflow = read('overflow.jsonl')
    assert len(overflow) == 2 and overflow[-1]['complete'] is False
    assert overflow[-1]['reason'] == 'queue_full'
    assert read('restart.jsonl')[-1]['complete'] is True
    assert read('shutdown.jsonl')[-1]['reason'] == 'shutdown'
print('PASS: JSON parsing, event order, short taps, sequence/timestamps, complete/incomplete footer, Unicode path')

# Run the production adapter against a deterministic world. Only includes are
# replaced by the facade; its collection, lifecycle and serialization run intact.
adapter = (repo/'src/freelancer/Client/flight_telemetry.cpp').read_text()
adapter = adapter[adapter.index('namespace FlightTelemetry {'):]
(out/'game_check.cpp').write_text(
    (repo/'tools/flight_telemetry/game_fixture.h').read_text() + '\n' + adapter + '\n' +
    (repo/'tools/flight_telemetry/game_check.cpp').read_text(), encoding='utf-8')
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT',
                '/I'+str(repo/'src/freelancer/Client'), 'game_check.cpp',
                str(repo/'src/freelancer/Client/flight_telemetry_recording.cpp'), '/Fegame_check.exe'],
               cwd=out, env=env, check=True)
with tempfile.TemporaryDirectory(prefix='adapter_', dir=out) as temporary:
    folder = Path(temporary)
    subprocess.run([str(out/'game_check.exe'), str(folder)], cwd=out, check=True)
    assert {p.name for p in folder.iterdir()} == {'adapter.jsonl', 'system_change.jsonl', 'ship_loss.jsonl'}
    rows = [json.loads(line) for line in (folder/'adapter.jsonl').read_text().splitlines()]
    assert rows[-1]['complete'] and rows[-1]['reason'] == 'session_changed'
    events = rows[1:-1]
    assert [e['sequence'] for e in events] == list(range(len(events)))
    assert rows[0]['metadata']['equipment'][0]['archetype'] == 444
    snapshots = [e for e in events if e['type'] == 'snapshot']
    assert len(snapshots) == 6
    first = snapshots[0]['data']
    assert first['phase'] == 'initial' and first['context']['docking'] is None
    assert first['player']['engine_active'] is False and first['player']['thrusters_active'] is True
    assert first['player']['velocity'] == [10, 0, 0] and first['player']['throttle'] == -1
    assert first['player']['thrust_energy'] == 40 and first['player']['weapon_energy'] == 30
    assert first['target']['relative_position_local'] == [0, 0, -100]
    assert first['target']['relative_velocity_local'] == [-10, 0, 20]
    assert first['target']['distance'] == 100 and first['target']['closing_speed'] == 20
    assert first['target']['shield'] is None and first['target']['shield_active'] is None
    assert first['scanner_contacts'][0]['id'] == 2 and not first['contacts_truncated']
    commands = [e['data'] for e in events if e['type'] == 'behavior_command']
    assert [e['origin'] for e in commands] == ['mapped_input', 'synthetic', 'mapped_input', 'unknown']
    shots = [e['data'] for e in events if e['type'] == 'shot']
    assert len(shots) == 2 and shots[0]['aim_world'] is None
    assert shots[1]['automatic'] and shots[1]['aim_world'] == [0, 0, -100]
    damage = next(e['data'] for e in events if e['type'] == 'damage_report')
    assert damage['cause'] == 4 and damage['entries'][0]['remaining_hp'] == 250
    collision = next(e['data'] for e in events if e['type'] == 'collision')
    assert collision['object_a'] == 1 and collision['object_b'] == 2 and collision['part_b'] == 7
    assert collision['point_world'] == [0, 0, -100]
    assert collision['relative_velocity_as_delivered_to_b'] == [0, 0, -20]
    baseline = [e['data'] for e in events if e['type'] == 'input_baseline']
    assert baseline[0]['held_mapped_commands'] == baseline[2]['held_mapped_commands'] == [120]
    assert baseline[1]['held_mapped_commands'] is None and not baseline[1]['valid']
    paused = [e for e in snapshots if e['data']['context']['paused']]
    assert len(paused) == 3 and len({e['simulation_s'] for e in paused}) == 1
    assert abs(snapshots[-1]['simulation_s'] - 2/30) < 1e-7
    for name in ('system_change.jsonl', 'ship_loss.jsonl'):
        other = [json.loads(line) for line in (folder/name).read_text().splitlines()]
        assert len(other) == 4 and other[-1]['reason'] == 'session_changed' and other[-1]['complete']
print('PASS: adapter JSON values, physics/inputs separation, focus resync and session boundaries')
