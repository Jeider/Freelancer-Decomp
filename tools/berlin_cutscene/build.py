"""Reimport Berlin into editable Python and a Blender build specification."""
import ast
import hashlib
import json

from read_source import ROOT, PYTHONLANCER, SOURCE, read
from story.cutscenes.old_format import parse_old_motions


data = read()
entities = {e['entity_name']: e for e in data['entities']}
events = data['events']
assert len(parse_old_motions(SOURCE.read_text(encoding='utf-8-sig'))) == sum(e[1] == 'START_MOTION' for e in events)
cameras = [n for n, e in entities.items() if e['type'] == 'CAMERA' and n != 'cam_dbg']
aliases = {}
for cam in cameras:
    aliases[cam + '_point'] = cam + '_focus'
    aliases[cam + '_point2'] = cam + '_focus2'
    aliases[cam + '_pos2'] = cam + '2'


def point(name):
    return aliases.get(name, name)


def obj(name):
    if entities[name]['type'] == 'MARKER':
        return 'automarker_' + point(name)
    return name


spatial = {point(n): e['spatialprops'] for n, e in entities.items()
           if e['type'] in ('DEFORMABLE', 'MARKER', 'CAMERA')
           and n not in ('offscreen', 'cam_dbg', 'cam_dbg_point')}
actor_classes = {'trent': 'Trent', 'alaric': 'Alaric', 'luc': 'Luc', 'adelmar': 'Adelmar'}
anim_tree = ast.parse((PYTHONLANCER / 'story/cutscenes/anim.py').read_text())
male = next(c for c in anim_tree.body if isinstance(c, ast.ClassDef) and c.name == 'Male')
constants = {n.value.value: n.targets[0].id for n in male.body
             if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}
lines = [
    '"""Reimported from DATA/SCRIPTS/MOD/m01_berlin_bar.thn.',
    '',
    'Dialogue uses relative time. Old facial windows define pauses/overlaps;',
    'facial() supplies the current voice and lipsync. Blender: m01_berlin.blend.',
    '"""',
    'from story.cutscenes.scene import Scene',
    'from story.cutscenes.content import (MAIN, Character, LookAtCamera, MoveEvent,',
    '                                     NeckIkEvent, EyeIkEvent)',
    'from story.cutscenes.anim import Male',
    'from story import actors', '', '',
    'class BerlinScene(Scene):',
    "    DUMP_FILE = 'm01_berlin'",
    f"    SCENE_AMBIENT = {entities['Layer_Fidget_Male_Sit_03']['ambient']!r}", '',
    '    def action(self):',
    '        main_group = self.get_group(MAIN)', '',
]
for cam in cameras:
    p = entities[cam]['cameraprops']
    lines.append(f"        {cam} = LookAtCamera(root=self, name={cam!r}, fov={p['fovh']}, look_duration=300)")
lines.append('')
for name, actor in actor_classes.items():
    lines.append(f"        {name} = Character(root=self, actor=actors.{actor}, light_group=0, init_point='Char_{name}', rotate_from_quat=True)")

report = {'source': str(SOURCE), 'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'events': [], 'dialogue': [], 'duration': data['duration']}
kept = []
speech = []
for i, event in enumerate(events):
    time, kind, targets, *rest = event
    props = rest[0] if rest else {}
    status = 'converted'
    if kind == 'ATTACH_ENTITY':
        assert time == 0 and props['flags'] == 'LOOK_AT'
        assert targets[1] == targets[0] + '_point'
        assert props['duration'] == 300 and props['offset'] == [0, 0, 0]
        status = 'debug camera excluded' if targets[0] == 'cam_dbg' else 'LookAtCamera initialization'
    elif kind == 'START_SOUND':
        index, actor = targets[0].split('_')[-2:]
        speech.append((time, int(index), actor))
        status = 'facial() dialogue audio'
    elif kind == 'START_MOTION' and props['animation'].lower().startswith('sc_dx_'):
        status = 'facial() replacement; allocated window retained'
    else:
        if kind not in ('START_MOTION', 'START_IK', 'START_SPATIAL_PROP_ANIM', 'SET_CAMERA'):
            raise ValueError(f'Unsupported event {i}: {kind}')
        kept.append((i, event))
    report['events'].append({'index': i, 'time': time, 'type': kind, 'status': status})


def emit(event):
    time, kind, targets, *rest = event
    p = rest[0] if rest else {}
    if kind == 'SET_CAMERA':
        assert targets[0] == 'Monitor_1' and targets[1] in cameras
        return f'{targets[1]}.set(group=MAIN, time_delay=t)'
    if kind == 'START_MOTION':
        assert len(targets) == 1 and p.get('weight', 1) == 1 and p.get('heading', -1) == -1
        assert set(p) <= {'animation','duration','time_scale','start_time','trans_time','weight','heading','event_flags'}
        assert p.get('event_flags', 0) in (0, 2)
        animation = 'Male.' + constants[p['animation']] if p['animation'] in constants else repr(p['animation'])
        args = [f'group=MAIN, anim={animation}, duration={p["duration"]}, time_delay=t']
        for key in ('time_scale', 'start_time', 'trans_time'):
            if key in p:
                args.append(f'{key}={p[key]!r}')
        if p.get('event_flags') == 2:
            args.append('loop=True')
        return f'{targets[0][5:]}.motion(' + ', '.join(args) + ')'
    if kind == 'START_SPATIAL_PROP_ANIM':
        assert p['target_type'] == 'ROOT' and p['target_part'] == ''
        assert p['spatialprops'] == {'pos': [0,0,0], 'q_orient': [1,0,0,0]}
        if 'param_curve' in p:
            assert p['param_curve'] == {'CLSID':'FreeFormPCurve','points':[[0,0,0,0],[1,1,0,0]]} and p['pcurve_period'] == -1000
        return (f'MoveEvent(root=self, group=MAIN, object_name={obj(targets[0])!r}, '
                f'target_name={obj(targets[1])!r}, duration={p["duration"]}, '
                f'smooth={"param_curve" in p}, time_delay=t)')
    if kind == 'START_IK':
        for key, value in {'count_to_root':1, 'damping':1, 'point_at':1, 'move_to':0, 'event_flags':128}.items():
            assert p[key] == value
        cls = {'Body_Head':'NeckIkEvent', 'Eye IK Left':'EyeIkEvent'}[p['end_effector']]
        args = ', '.join(f'{k}={p[k]!r}' for k in ('duration','transition_duration','target_type','target_part','up','front'))
        return f'{cls}(root=self, group=MAIN, char_name={obj(targets[0])!r}, target_name={obj(targets[1])!r}, {args}, time_delay=t)'
    raise ValueError(kind)


speech.sort()
boundaries = [0] + [s[0] for s in speech] + [float('inf')]
for block in range(len(boundaries) - 1):
    base, end = boundaries[block:block + 2]
    lines.extend(['', f'        # {"Entrance" if block == 0 else "Line " + str(speech[block-1][1])}; source time {base:g}s.', '        t = 0'])
    cursor = 0
    for i, event in sorted(kept, key=lambda item: (item[1][0], item[0])):
        if not base <= event[0] < end:
            continue
        delay = round(event[0] - base, 6)
        if delay != cursor:
            lines.append(f'        t += {round(delay - cursor, 6):g}')
            cursor = delay
        lines.append(f'        {emit(event)}')
    if block == 0:
        lines.append(f'        main_group.append_time({end:g})')
        continue
    start, index, actor = speech[block - 1]
    clips = [e for e in events if e[1] == 'START_MOTION' and e[2] == ['Char_' + actor]
             and e[3]['animation'].lower().startswith('sc_dx_') and start <= e[0] < end]
    assert clips and min(e[0] for e in clips) == start
    lip_end = max(e[0] + e[3]['duration'] for e in clips)
    gap = round((end if block < len(speech) else data['duration']) - lip_end, 6)
    source_gap = gap
    if index == 30:
        # User staging correction: Luc must wait for Trent to finish speaking.
        gap = 0
    lines.append(f'        {actor}.facial(group=MAIN, index={index}, auto_lip=True, extra_delay=0)')
    lines.append(f'        # Source facial window: {lip_end-start:g}s; following pause/overlap: {gap:g}s.')
    if index == 30:
        lines.append('        # Luc waits for Trent; do not restore the old two-second overlap.')
    if gap:
        lines.append(f'        main_group.append_time({gap:g})')
    report['dialogue'].append({'index':index, 'actor':actor, 'start':start, 'window':lip_end-start, 'gap':gap, 'source_gap':source_gap})

output = '\n'.join(lines) + '\n'
compile(output, 'm01_berlin.py', 'exec')
(ROOT / 'm01_berlin.py').write_text(output, encoding='utf-8')
(ROOT / 'blender_spec.json').write_text(json.dumps({'points':spatial, 'cameras':cameras,
    'character_markers':['trent_pos_table','alaric_pos_table']}, indent=2), encoding='utf-8')
(ROOT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(f'Converted {len(events)} events: {len(kept)} explicit actions, {len(speech)} dialogue lines, 5 camera look-at bindings; debug camera excluded.')
print(json.dumps(report['dialogue'], indent=2))
