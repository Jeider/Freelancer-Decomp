"""Translate audited master RTC scenes into explicit native authoring code."""
import argparse
import ast
import copy
import json
import math
import re
import sys
import textwrap
from pathlib import Path
from inventory import OUT, PL, REPO, sha

sys.path.insert(0, str(PL))
from story import actors
from story.cutscenes import anim

IDENTITY = {'pos': [0, 0, 0], 'orient': [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}
SMOOTH = {'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}
INV = json.loads((OUT / 'inventory.json').read_text())
ACTORS = {n: c for n, c in vars(actors).items() if isinstance(c, type) and issubclass(c, actors.Actor)}
ANIMS = {}
for cls_name, cls in vars(anim).items():
    if isinstance(cls, type):
        for key, value in vars(cls).items():
            if isinstance(value, str) and value.startswith('Sc_'):
                ANIMS.setdefault(value, cls_name + '.' + key)
SCRIPTS = {}
for mission in range(3, 9):
    tree = ast.parse((OUT / f'master_mission{mission}.py').read_text(encoding='utf-8-sig'))
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef) or not any(isinstance(b, ast.Attribute) and b.attr == 'CutsceneProps' for b in cls.bases):
            continue
        alias = next(ast.literal_eval(n.value) for n in cls.body if isinstance(n, ast.Assign) and n.targets[0].id == 'ALIAS')
        lines = {ast.literal_eval(n.args[0]): {'actor': n.args[1].id,
                 'ru': next(ast.literal_eval(k.value) for k in n.keywords if k.arg == 'ru')}
                 for n in ast.walk(cls) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'VoiceLine'}
        SCRIPTS[f'm{mission:02}_{alias}'] = dict(mission=mission, cls=cls.name, lines=lines)


def variable(name):
    result = re.sub(r'\W', '_', name.removeprefix('Char_').removeprefix('char_')).lower()
    return result if result.isidentifier() else 'obj_' + result


def class_name(name):
    return ''.join(s.capitalize() for s in name.split('_')) + 'Scene'


def build(name):
    folder = OUT / name
    source = json.loads((folder / 'source.json').read_text())
    # Use the previous reports only to locate the old Blender points. Their
    # guessed speakers, shortened dialogue and event emission are not reused.
    old = json.loads((REPO / f'tools/m02_m08_cutscenes/bundle/{name}/report.json').read_text())
    assert source == json.loads((REPO / f'tools/m02_m08_cutscenes/bundle/{name}/source.json').read_text())
    data = copy.deepcopy(source)
    for e in data['entities']:
        e['type'] = {1: 'COMPOUND', 5: 'LIGHT'}.get(e['type'], e['type'])
        if e['type'] == 'LIGHT':
            p = e['lightprops']
            p['type'] = {1: 'L_POINT', 2: 'L_SPOT', 3: 'L_DIRECT'}.get(p['type'], p['type'])
            p['on'] = {1: 'Y', 0: 'N'}.get(p['on'], p['on'])
        if e.get('flags') == 4:
            e['flags'] = 'LIT_AMBIENT'
    entities = {e['entity_name']: e for e in data['entities']}
    excluded = {n for n in entities if 'subtitle' in n.lower() or n.lower().startswith('cam_dbg')}
    characters = {n for n, e in entities.items() if e['type'] == 'DEFORMABLE' and n not in excluded}
    cameras = {n for n, e in entities.items() if e['type'] == 'CAMERA' and n not in excluded}
    events = data['events']
    speech, duplicates, voice_events = [], [], set()
    for i, e in enumerate(events):
        if e[1] != 'START_SOUND' or not re.match(r'DX_m\d', e[2][0], re.I):
            continue
        match = re.fullmatch(r'DX_(m\d+_.+)_(\d+)_([^_]+)', e[2][0], re.I)
        assert match, e
        prefix, index, speaker = match[1], int(match[2]), match[3]
        info = SCRIPTS[prefix]['lines'][index]
        assert ACTORS[info['actor']].NAME.lower() == speaker.lower(), (name, e, info)
        voice_events.add(i)
        previous = next((s for s in speech if s['start'] == e[0] and s['sound'] == e[2][0]), None)
        if previous:
            duplicates.append({'event': i, 'original': previous['event']})
            voice_events.remove(i)  # Retain the literal duplicate as a timed sound event.
            continue
        # The mouth animated at the sound onset is direct evidence of its target.
        near = [(j, x) for j, x in enumerate(events) if x[1] == 'START_MOTION'
                and x[3]['animation'].lower().startswith('sc_dx_') and abs(x[0] - e[0]) <= 0.5]
        exact = [(j, x) for j, x in near if abs(x[0] - e[0]) < 0.0001]
        candidates = {x[2][0] for _, x in exact or near}
        if len(candidates) == 1:
            character = next(iter(candidates))
        else:
            # Without a facial cue, a spoken sound remains audio only. No
            # fabricated allocation or animation is added for a guessed speaker.
            character = None
        speech.append(dict(event=i, start=e[0], sound=e[2][0], prefix=prefix, index=index,
                           actor=info['actor'], ru=info['ru'], character=character))
    speech.sort(key=lambda s: (s['start'], s['event']))
    lip_events = set()
    for j, line in enumerate(speech):
        next_start = speech[j + 1]['start'] if j + 1 < len(speech) else data['duration']
        clips = [(i, e) for i, e in enumerate(events) if line['character'] is not None
                 and e[1] == 'START_MOTION' and e[2] == [line['character']]
                 and e[3]['animation'].lower().startswith('sc_dx_')
                 and line['start'] - 0.5 <= e[0] < next_start - 0.5 and i not in lip_events]
        line['lip_events'] = [i for i, _ in clips]
        lip_events.update(line['lip_events'])
        line['window'] = (max(clips, key=lambda pair: (pair[1][0], pair[0]))[1][0] +
                          max(clips, key=lambda pair: (pair[1][0], pair[0]))[1][3]['duration'] - line['start']) if clips else None
        line['source_gap'] = round(next_start - line['start'] - line['window'], 6) if clips else None
        line['gap'] = max(0, line['source_gap']) if clips else next_start - line['start']
    # A line with no new mouth cue is not assigned a made-up facial window.
    # In particular Rockford's continuation in Cadiz remains an audio event.
    actor_for = {}
    for line in speech:
        if line['character']:
            actor_for.setdefault(line['character'], line['actor'])
    for n in sorted(characters):
        if n in actor_for:
            continue
        e = entities[n]
        desired = e.get('userprops', {}).get('Actor', e.get('userprops', {}).get('actor', n.removeprefix('Char_')))
        candidates = [key for key, actor in ACTORS.items() if actor.NAME and actor.NAME.lower() == desired.lower()]
        if candidates:
            actor_for[n] = candidates[0]
    focus, attachment_events = {}, set()
    for i, e in enumerate(events):
        if (e[1] == 'ATTACH_ENTITY' and e[2][0] in cameras and e[3]['flags'] == 'LOOK_AT' and e[0] == 0
                and entities.get(e[2][1], {}).get('type') == 'MARKER' and e[3]['target_type'] == 'ROOT'):
            assert e[2][0] not in focus
            focus[e[2][0]] = e[2][1]
            attachment_events.add(i)
    shared_focus = {target for target in focus.values() if list(focus.values()).count(target) > 1}
    focus = {cam: target for cam, target in focus.items() if target not in shared_focus}
    attachment_events = {i for i in attachment_events if events[i][2][0] in focus}
    names = {n: n for n in entities}
    for cam, target in focus.items():
        names[target] = cam + '_focus'
        for n in entities:
            for prefix, dest in ((cam + '_pos', cam), (target + '_pos', cam + '_focus'), (target, cam + '_focus')):
                suffix = n.removeprefix(prefix)
                if n.startswith(prefix) and suffix.isdecimal():
                    names[n] = dest + suffix
    objects = {n: variable(n) for n, e in entities.items() if n not in excluded
               and e['type'] not in ('SCENE', 'MONITOR', 'MARKER')
               and not (e['type'] == 'SOUND' and re.match('DX_m', n, re.I))}
    assert len(set(objects.values())) == len(objects), (name, objects)
    # Master shares some targets between multiple eyes/heads and moves them
    # independently. Keep those authored markers and use typed IK events.
    ik = {}
    points = {names[n]: copy.deepcopy(e.get('spatialprops', IDENTITY)) for n, e in entities.items()
              if n not in excluded and n.lower() != 'offscreen' and e['type'] not in ('SCENE', 'MONITOR', 'SOUND')}
    placements = {}
    for e in events:
        if e[1] == 'START_SPATIAL_PROP_ANIM' and len(e[2]) == 2 and e[2][0] in characters and names[e[2][1]] in points:
            placements[names[e[2][1]]] = e[2][0]
    primary = name if name in SCRIPTS else (speech[-1]['prefix'] if speech else None)
    if name == 'm07_tau_arrival':
        primary = name  # Reuses Omega13's recorded line through explicit props.
    for suffix in ('_accept', '_decision'):
        if name.endswith(suffix) and name.removesuffix(suffix) in SCRIPTS:
            primary = name.removesuffix(suffix)
    foreign = {s['prefix'] for s in speech if s['prefix'] != primary}
    absolute = old['clock'] == 'absolute' or not speech or name in ('m06_mount', 'm07_tau_arrival')
    cls = class_name(name)
    lines = [f'"""{name}: полная постановка из master; точки в {name}.blend."""',
             'from story.cutscenes.scene import Scene', 'from story.cutscenes.content import *',
             'from story.cutscenes.anim import *', 'from story import actors', '']
    prop_classes, extra_actors = {}, {}
    for n in objects:
        e = entities[n]
        if e['type'] == 'COMPOUND':
            category = e.get('userprops', {}).get('category', 'Prop')
            base = {'Spaceship': 'Ship', 'Solar': 'Solar', 'Equipment': 'Equipment'}.get(category, 'Prop')
            prop_cls = ''.join(s.capitalize() for s in re.split(r'\W|_', n)) + 'Prop'
            prop_classes[n] = prop_cls
            lines += ['', f'class {prop_cls}({base}):', f'    COMPOUND_TEMPLATE_NAME = {e["template_name"]!r}']
            for attr, key in (('SRT_GRP', 'srt_grp'), ('USR_FLG', 'usr_flg')):
                if e.get(key, 0):
                    lines.append(f'    {attr} = {e[key]!r}')
        elif n in characters and n not in actor_for:
            actor_cls = ''.join(s.capitalize() for s in re.split(r'\W|_', n)) + 'Actor'
            extra_actors[n] = actor_cls
            gender = 'female' if 'female' in e['template_name'].lower() else 'male'
            lines += ['', f'class {actor_cls}(actors.Actor):', f'    NAME = {variable(n)!r}',
                      f'    TYPE = {gender!r}', f'    CUTSCENE_APPEARANCE = {e["template_name"]!r}']
    ambient = next((e['ambient'] for e in entities.values() if e['type'] == 'SCENE' and 'ambient' in e), [0, 0, 0])
    lines += ['', '', f'class {cls}(Scene):', f'    DUMP_FILE = {name!r}', f'    SCENE_AMBIENT = {ambient!r}',
              '', '    def action(self):', '        main_group = self.get_group(MAIN)']
    for prefix in sorted(foreign):
        meta = SCRIPTS[prefix]
        lines += [f'        from story.scripts.main.mission{meta["mission"]} import {meta["cls"]}',
                  f'        {prefix}_props = {meta["cls"]}(self.props.mission)']
    if absolute:
        lines.append(f'        self.set_duration({data["duration"]!r})')
    lines += ['', '        # Персонажи, камеры, реквизит и звук.']

    def constructor(var, ctor, args):
        chunks = ['root=self'] + args
        code = f'        {var} = {ctor}('
        for i, chunk in enumerate(chunks):
            addition = chunk + (', ' if i < len(chunks) - 1 else ')')
            if len(code.rsplit('\n', 1)[-1]) + len(addition) > 115:
                code += '\n            '
            code += addition
        lines.append('\n'.join(s.rstrip() for s in code.splitlines()))

    scales = {}
    for n, var in objects.items():
        e = entities[n]
        typ = e['type']
        args = [f'name={n!r}']
        if typ in ('DEFORMABLE', 'COMPOUND'):
            flags = str(e.get('flags', ''))
            args += [f'light_group={e.get("lt_grp", 0)}', f'init_point={names[n]!r}', 'rotate_from_quat=True']
            if 'LIT_AMBIENT' in flags:
                args.append('use_ambient=True')
            if 'LIT_DYNAMIC' not in flags:
                args.append('use_dynamic=False')
            matrix = e.get('spatialprops', IDENTITY)['orient']
            scale = [math.sqrt(sum(matrix[i][j]**2 for i in range(3))) for j in range(3)]
            if any(abs(v - 1) > 0.001 for v in scale):
                scales[n] = scale
                # Scale belongs to the authored point and is exported from Blender.
            if typ == 'DEFORMABLE':
                actor = 'actors.' + actor_for[n] if n in actor_for else extra_actors[n]
                args.insert(0, f'actor={actor}')
                args.append(f'appearance={e["template_name"]!r}')
                actor_name = e.get('userprops', {}).get('Actor', e.get('userprops', {}).get('actor'))
                args.append(f'actor_name={actor_name!r}' if actor_name is not None else 'bind_actor=False')
                height = e.get('compoundprops', {}).get('floor_height', 0)
                if isinstance(height, str) and height.startswith('='):
                    height = float(height[1:])
                if height:
                    args.append(f'floor_height={height!r}')
                ctor = 'Character'
            else:
                ctor = prop_classes[n]
                user = e.get('userprops', {})
                if 'loadout' in user:
                    args.append(f'loadout={user["loadout"]!r}')
                if user.get('NoFog') == 'Y':
                    args.append('no_fog=True')
        elif typ == 'CAMERA':
            ctor = 'LookAtCamera' if n in focus else 'StaticCamera'
            p = e['cameraprops']
            args += [f'fov={p["fovh"]!r}']
            for key, kw, default in (('farplane', 'farplane', 5000), ('nearplane', 'nearplane', .2), ('hvaspect', 'aspect', 1.85)):
                if p[key] != default:
                    args.append(f'{kw}={p[key]!r}')
            if n in focus:
                duration = events[next(i for i in attachment_events if events[i][2][0] == n)][3]['duration']
                args.append(f'look_duration={duration!r}')
        elif typ == 'SOUND':
            ctor = 'SpatialSound' if 'SPATIAL' in str(e.get('flags', '')) else 'Sound'
            p = e['audioprops']
            args += [f'sound={e["template_name"]!r}', f'attenuation={p["attenuation"]!r}',
                     f'dmin={p["dmin"]!r}', f'dmax={p["dmax"]!r}', f'priority={e.get("userprops", {}).get("Priority")!r}']
        elif typ == 'PSYS':
            ctor = 'Alchemy'
            flags = e.get('flags', '')
            args += [f'particles={e["template_name"]!r}', f'point_name={names[n]!r}', f'sparam={e["psysprops"]["sparam"]!r}',
                     f'light_group={e.get("lt_grp", 0)}', f'sort_group={e.get("srt_grp", 0)}',
                     f'hidden={"HIDDEN" in flags}', f'use_ambient={"LIT_AMBIENT" in flags}']
        elif typ == 'MOTION_PATH':
            ctor = 'MotionPath'
            path = e['pathprops']['path_data']
            assert path.startswith('OPEN,')
            args += [f'point_name={names[n]!r}', f'path_data={path[5:].strip().rstrip(",")!r}']
        elif typ == 'LIGHT':
            ctor = 'Light'
            p = e['lightprops']
            args += [f'point_name={names[n]!r}', "extra_name=''", f'light_group={e["lt_grp"]!r}',
                     f'hidden={"HIDDEN" in e.get("flags", "")}', 'rotate_from_quat=True']
            for key, kw in (('diffuse', 'diffuse'), ('ambient', 'ambient'), ('direction', 'direction'), ('type', 'light_type'),
                            ('range', 'range'), ('cutoff', 'cutoff'), ('theta', 'theta'), ('color', 'color'), ('atten', 'attenuation')):
                args.append(f'{kw}={p[key]!r}')
            args.append(f'on={p["on"] == "Y"}')
            if p['specular'] != [0, 0, 0]:
                args.append(f'specular={p["specular"]!r}')
        else:
            raise ValueError((name, n, typ))
        constructor(var, ctor, args)

    def ref(n):
        if n not in entities or re.match('DX_m', n, re.I):
            return repr(n)
        if n.lower() == 'offscreen':
            return 'self.get_automarker_name(self.OFFSCREEN_POINT_NAME)'
        if n in ik:
            char, part = ik[n]
            return objects[char] + '.' + part + '_ik_name'
        if n in objects:
            return objects[n] + '.name'
        return f'self.get_automarker_name({names[n]!r})'

    def call(target, args, group='MAIN'):
        chunks = (['root=self'] if target.endswith('Event') else []) + [f'group={group}'] + args + ['time_delay=t']
        text = '        ' + target + '('
        for i, chunk in enumerate(chunks):
            addition = chunk + (', ' if i < len(chunks) - 1 else ')')
            if len(text.rsplit('\n', 1)[-1]) + len(addition) > 115:
                text += '\n            '
            text += addition
        return '\n'.join(s.rstrip() for s in text.splitlines())

    def convert(e):
        _, kind, target, *rest = e
        p = rest[0] if rest else {}
        dur = p.get('duration', 0)
        smooth = p.get('param_curve') == SMOOTH
        if 'param_curve' in p and kind != 'START_PATH_ANIMATION':
            assert smooth, e
        if kind == 'SET_CAMERA':
            if target[1] not in objects:
                return call('SetCameraEvent', [f'camera_name={ref(target[1])}'])
            return call(objects[target[1]] + '.set', [])
        if kind == 'START_MOTION':
            args = [f'anim={ANIMS.get(p["animation"], repr(p["animation"]))}', f'duration={dur!r}']
            for key, default in (('time_scale', 1), ('start_time', 0), ('trans_time', None), ('trans_scale', None)):
                if p.get(key, default) != default:
                    args.append(f'{key}={p[key]!r}')
            assert p.get('event_flags', 0) in (0, 2) and p.get('weight', 1) == 1 and p.get('heading', -1) == -1, e
            if p.get('event_flags') == 2:
                args.append('loop=True')
            actor = ACTORS.get(actor_for.get(target[0]))
            mismatch = not actor or ((actor.is_female() and 'mlbody' in p['animation'].lower()) or
                                    (not actor.is_female() and 'fmbody' in p['animation'].lower()))
            if target[0] in characters and not mismatch:
                return call(objects[target[0]] + '.motion', args)
            return call('MotionEvent', [f'object_name={ref(target[0])}'] + args)
        if kind == 'START_SPATIAL_PROP_ANIM':
            sp = p['spatialprops']
            if set(sp) == {'axisrot'}:
                return call('RotateAxisEvent', [f'object_name={ref(target[0])}', f'angle={sp["axisrot"][0]!r}',
                            f'axis={sp["axisrot"][1]!r}', f'duration={dur!r}', f'smooth={smooth}'])
            assert len(target) == 2 and set(sp) <= {'pos', 'q_orient'} and sp.get('q_orient', [1, 0, 0, 0]) == [1, 0, 0, 0], e
            args = [f'duration={dur!r}', f'smooth={smooth}']
            default = sp.get('pos', [0, 0, 0]) == [0, 0, 0] and set(sp) == {'pos', 'q_orient'}
            if default and target[0] in ik:
                char, part = ik[target[0]]
                return call(f'{objects[char]}.move_{part}_ik', [f'target_name={ref(target[1])}'] + args)
            for cam, marker in focus.items():
                if default and target[0] in (cam, marker):
                    method, prefix = ('move_cam', cam) if target[0] == cam else ('move_focus', cam + '_focus')
                    index = names[target[1]].removeprefix(prefix)
                    if index.isdecimal():
                        return call(objects[cam] + '.' + method, [f'index={index}'] + args)
            args += [f'adjust_pos={"pos" in sp}', f'adjust_orient={"q_orient" in sp}']
            if sp.get('pos', [0, 0, 0]) != [0, 0, 0]:
                args.append(f'offset={tuple(sp["pos"])!r}')
            return call('MoveEvent', [f'object_name={ref(target[0])}', f'target_name={ref(target[1])}'] + args)
        if kind == 'START_IK':
            args = [f'duration={dur!r}', f'transition_duration={p["transition_duration"]!r}']
            if target[1] in ik and ik[target[1]][0] == target[0]:
                return call(objects[target[0]] + '.start_' + ik[target[1]][1] + '_ik', args)
            cls = 'NeckIkEvent' if p['end_effector'] == 'Body_Head' else 'EyeIkEvent'
            return call(cls, [f'char_name={ref(target[0])}', f'target_name={ref(target[1])}',
                             f'target_type={p["target_type"]!r}', f'target_part={p["target_part"]!r}',
                             f'up={p["up"]!r}', f'front={p["front"]!r}'] + args)
        if kind == 'ATTACH_ENTITY':
            if p['flags'] == 'LOOK_AT':
                assert p['offset'] == [0, 0, 0], e
                return call('LookAtEvent', [f'point={ref(target[0])}',
                            f'focus={ref(target[1])}', f'duration={dur!r}',
                            f'target_type={p["target_type"]!r}', f'target_part={p["target_part"]!r}',
                            f'up={p["up"]!r}', f'front={p["front"]!r}'])
            flags = p['flags'].split('+')
            assert set(flags) <= {'POSITION', 'ORIENTATION', 'ENTITY_RELATIVE', 'ORIENTATION_RELATIVE'}, e
            args = [f'target_name={ref(target[0])}', f'parent_name={ref(target[1])}', f'duration={dur!r}',
                    f'target_part={p["target_part"]!r}', f'target_type={p["target_type"]!r}',
                    f'adjust_pos={"POSITION" in flags}', f'adjust_orient={"ORIENTATION" in flags}']
            for flag, kw in (('ENTITY_RELATIVE', 'entity_relative'), ('ORIENTATION_RELATIVE', 'orientation_relative')):
                if flag in flags:
                    args.append(f'{kw}=True')
            for key in ('up', 'front'):
                args.append(f'{key}={p[key]!r}')
            for axis, value in zip('xyz', p.get('offset', [0, 0, 0])):
                if value:
                    args.append(f'offset_{axis}={value!r}')
            return call('AttachEvent', args)
        if kind == 'START_PATH_ANIMATION':
            assert p['offset'] == [0, 0, 0] and p['up'] == 'Y_AXIS' and p['front'] == 'NEG_Z_AXIS'
            args = [f'target_name={ref(target[0])}', f'path={objects[target[1]]}', f'duration={dur!r}',
                    f'adjust_pos={"POSITION" in p["flags"]}', f'adjust_orient={"ORIENTATION" in p["flags"]}',
                    f'start_percent={p["start_percent"]!r}', f'stop_percent={p["stop_percent"]!r}']
            if smooth and p.get('pcurve_period') == -1000:
                args.append('smooth=True')
            else:
                args += [f'curve_points={p["param_curve"]["points"]!r}', f'curve_period={p["pcurve_period"]!r}']
            return call('PathAnimationEvent', args)
        if kind == 'CONNECT_HARDPOINTS':
            return call('ConnectHardpointEvent', [f'target_name={ref(target[0])}', f'parent_name={ref(target[1])}',
                        f'duration={dur!r}', f'target_hardpoint={p["hardpoint"]!r}', f'parent_hardpoint={p["parent_hardpoint"]!r}'])
        if kind == 'START_SOUND':
            if target[0] not in objects:
                return call('SoundEvent', [f'sound_name={ref(target[0])}', f'duration={dur!r}'])
            return call(objects[target[0]] + '.start', [f'duration={dur!r}', f'loop={p.get("flags") == "LOOP"}',
                        f'start_time={p.get("start_time", 0)!r}'])
        if kind == 'START_AUDIO_PROP_ANIM':
            if target[0] not in objects:
                return call('AudioAnimEvent', [f'sound_name={ref(target[0])}', f'duration={dur!r}',
                            f'attenuation={p["audioprops"]["attenuation"]!r}'])
            return call(objects[target[0]] + '.change_attenuation', [f'duration={dur!r}', f'attenuation={p["audioprops"]["attenuation"]!r}'])
        if kind == 'START_PSYS':
            return call(objects[target[0]] + '.start', [f'duration={dur!r}'])
        if kind == 'START_PSYS_PROP_ANIM':
            return call(objects[target[0]] + '.set_sparam', [f'duration={dur!r}', f'sparam={p["psysprops"]["sparam"]!r}', f'smooth={smooth}'])
        if kind == 'START_CAMERA_PROP_ANIM':
            return call(objects[target[0]] + '.change_fov', [f'duration={dur!r}', f'fov={p["cameraprops"]["fovh"]!r}', f'smooth={smooth}'])
        if kind == 'START_LIGHT_PROP_ANIM':
            args = [f'object_name={ref(target[0])}', f'duration={dur!r}', f'smooth={smooth}']
            for key, value in p['lightprops'].items():
                args.append(f'{"lt_range" if key == "range" else key}={(value == "Y") if key == "on" else repr(value)}')
            return call('LightAnimEvent', args)
        raise ValueError((name, e))

    actions, excluded_events = [], []
    for i, event in enumerate(events):
        if any(n in excluded for n in event[2]):
            excluded_events.append(i)
        elif i not in voice_events | lip_events | attachment_events:
            actions.append((i, event, convert(event)))
    lines += ['', '        # Исходные точки взгляда.']
    for marker, (char, part) in ik.items():
        lines.append(f'        {objects[char]}.move_{part}_ik(group=MAIN, target_name=self.get_automarker_name({names[marker]!r}), immediately=True)')

    def emit(items, base):
        cursor = None
        for i, e, code in sorted(items, key=lambda a: (a[1][0], a[0])):
            offset = round(e[0] - base, 6)
            if cursor is None:
                lines.append(f'        t = {offset:g}')
            elif offset != cursor:
                lines.append(f'        t += {round(offset - cursor, 6):g}')
            lines.append(code)
            cursor = offset

    def voice(line, group='MAIN', append=True):
        prop = f', props={line["prefix"]}_props' if line['prefix'] in foreign else ''
        if line['lip_events']:
            alias = f', voice_actor=actors.{line["actor"]}' if actor_for[line['character']] != line['actor'] else ''
            lines.append(f'        {objects[line["character"]]}.facial(group={group}, index={line["index"]}, '
                         f'auto_lip=True, extra_delay=0' + (', append=False' if not append else '') + prop + alias + ')')
        else:
            lines.append(f'        line_sound = self.lookup_single_sound({line["index"]}{prop})')
            lines.append(f'        SoundEvent(root=self, group={group}, sound_name=line_sound.get_nickname())')

    if absolute:
        lines += ['', '        # Абсолютное время исходной сцены; часы MAIN не сдвигаются.']
        emit(actions, 0)
        for line in speech:
            group = f'voice_{line["event"]}'
            lines += ['', f'        # {line["prefix"]} {line["index"]}: {line["ru"]}',
                      f'        self.add_group({group!r}, time={line["start"]!r})']
            voice(line, repr(group), False)
    else:
        lines += ['', '        # Вход.']
        emit([a for a in actions if a[1][0] < speech[0]['start']], 0)
        lines.append(f'        main_group.append_time({speech[0]["start"]!r})')
        for j, line in enumerate(speech):
            start = line['start']
            end = speech[j + 1]['start'] if j + 1 < len(speech) else data['duration']
            section = [a for a in actions if start <= a[1][0] < end or j == len(speech) - 1 and a[1][0] >= end]
            lines += ['', f'        # {line["prefix"]} {line["index"]}: {line["actor"]}.']
            lines += ['        # ' + part for part in textwrap.wrap(line['ru'], width=100)]
            if line['window'] is None:
                emit(section, start)
                voice(line)
                lines.append(f'        main_group.append_time({end - start:g})')
            else:
                lip_end = start + line['window']
                emit([a for a in section if a[1][0] < lip_end], start)
                voice(line)
                tail = [a for a in section if a[1][0] >= lip_end]
                if tail:
                    lines.append('        # Действие после исходного окна реплики.')
                    emit(tail, lip_end)
                if line['gap']:
                    lines.append(f'        main_group.append_time({line["gap"]:g})')
    output = '\n'.join(lines) + '\n'
    # Explicit imports keep the resulting scene usable as hand-authored code.
    tree = ast.parse(output)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    import importlib.util
    module_spec = importlib.util.spec_from_file_location('native_content_inventory', OUT / 'api/story/cutscenes/content.py')
    content_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(content_module)
    for module_name, module in (('content', content_module), ('anim', anim)):
        selected = sorted(n for n in used if n in vars(module) and not n.startswith('_'))
        output = output.replace(f'from story.cutscenes.{module_name} import *',
                                (f'from story.cutscenes.{module_name} import (\n    ' + ', '.join(selected) + ',\n)') if selected else '')
    ast.parse(output)
    assert all(term not in output for term in ('preserve_', 'source_extensions', 'ReconstructedScene', 'SourceMotion', 'SourceAttach'))
    (folder / (name + '.py')).write_text(output, encoding='utf-8')
    existing_blend = PL.parent / f'SCENES/{name}.blend'
    existing_dump = PL.parent / f'SCENES/DUMPS/{name}.json'
    point_old = {names[n]: old['point_names'].get(n, n) for n in entities if names[n] in points}
    meta = dict(name=name, scene_class=cls, source=INV['scenes'][name]['source'], source_sha256=INV['scenes'][name]['sha256'],
                primary=primary, foreign=sorted(foreign), dialogue=speech, absolute=absolute, duration=data['duration'],
                names=names, objects=objects, characters=sorted(characters), cameras=sorted(cameras), ik=ik, focus=focus,
                points=points, old_points=point_old, placements=placements, scales=scales,
                actions=[i for i, _, _ in actions], lip_events=sorted(lip_events), voice_events=sorted(voice_events),
                duplicates=duplicates, excluded_events=excluded_events, attachment_events=sorted(attachment_events),
                source_scene_sha256=sha(output.encode()), original_scene_sha256=INV['scenes'][name]['working_scene_sha256'],
                original_blend_sha256=sha(existing_blend.read_bytes()) if existing_blend.exists() else None,
                original_dump_sha256=sha(existing_dump.read_bytes()) if existing_dump.exists() else None)
    (folder / 'spec.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'{name}: {len(speech)} master lines, {len(actions)} actions, {"absolute" if absolute else "relative"}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene')
    args = parser.parse_args()
    failures = {}
    for name in ([args.scene] if args.scene else INV['scenes']):
        try:
            build(name)
        except Exception as exc:
            failures[name] = repr(exc)
            print(name, repr(exc), flush=True)
    (OUT / 'build_failures.json').write_text(json.dumps(failures, indent=2), encoding='utf-8')
    if failures:
        raise SystemExit(1)
