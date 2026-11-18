"""One-time source import into ordinary Pythonlancer authoring code."""
import ast
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import textwrap
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[3]
PL = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
SOURCE = Path('D:/Games/FL_MOD/DATA/SCRIPTS/MOD/m02_bship_bar_offer.thn')
OUT = REPO / 'out/story_cutscenes/m02_offer'
NAME = 'm02_bship_bar_offer'
sys.path.insert(0, str(REPO / 'tools/berlin_cutscene'))
import read_source


def main(kind='offer'):
    name = f'm02_bship_bar_{kind}'
    out = REPO / f'out/story_cutscenes/m02_{kind}'
    scene_class = 'Msn2OfferScene' if kind == 'offer' else 'Msn2OfferAcceptScene'
    game = PL.parents[1]
    commit = subprocess.check_output(['git', '-C', str(game), 'rev-parse', 'master'], text=True).strip()
    def master(path):
        return subprocess.check_output(['git', '-C', str(game), 'show', f'{commit}:{path}'])
    raw_source = master(f'DATA/SCRIPTS/MOD/{name}.thn')
    master_script = master('Assets/Pythonlancer/story/scripts/mission2.py')
    script_tree = ast.parse(master_script.decode('utf-8-sig'))
    offer = next(n for n in script_tree.body if isinstance(n, ast.ClassDef) and n.name == 'Msn2Offer')
    dialogue = {n.args[0].value: {'actor': n.args[1].id.lower(),
                'ru': next(k.value.value for k in n.keywords if k.arg == 'ru')}
                for n in ast.walk(offer) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'VoiceLine'}
    read_source.SOURCE = SimpleNamespace(read_text=lambda **kwargs: raw_source.decode('utf-8-sig'))
    source = read_source.read()
    entities = {e['entity_name']: e for e in source['entities']}
    cameras = {n for n, e in entities.items() if e['type'] == 'CAMERA' and n != 'cam_dbg'}
    names = {n: n for n in entities}
    for n in cameras:
        names[n + '_point'] = n + '_focus'
        for suffix in ('2', '3'):
            names[n + '_point' + suffix] = n + '_focus' + suffix
            names[n + '_pos' + suffix] = n + suffix
    objects = {'Char_trent': 'trent', 'Char_wilham': 'wilham',
               'Prop_pda': 'pda', 'prop_cigarette_2': 'cigarette',
               'Prop_ashtray_extra_1': 'ashtray',
               'vfx_rtc_sydsmoke_3': 'smoke', 'vfx_rtc_cigaretteglow_4': 'glow'}
    objects = {n: variable for n, variable in objects.items() if n in entities}
    objects.update({n: n for n in cameras})
    targets = {n for event in source['events'] for n in event[2]}
    ik = {f'{actor}_{part}_ik': (actor, part) for actor in ('trent', 'wilham') for part in ('head', 'eye')
          if f'{actor}_{part}_ik' in targets}
    anims = {}
    for cls in ast.parse((PL / 'story/cutscenes/anim.py').read_text(encoding='utf-8')).body:
        if isinstance(cls, ast.ClassDef) and cls.name in ('Male', 'Trent'):
            for assignment in cls.body:
                if isinstance(assignment, ast.Assign) and isinstance(assignment.value, ast.Constant):
                    anims.setdefault(assignment.value.value, cls.name + '.' + assignment.targets[0].id)

    title = 'Предложение Вильгельма' if kind == 'offer' else 'Принятие задания Вильгельма'
    lines = [f'"""{title}: полная сцена master на API Pythonlancer."""',
             'from story.cutscenes.scene import Scene',
             'from story.cutscenes.content import (',
             ('    MAIN, Character, LookAtCamera, Prop, Alchemy, AttachEvent,' if kind == 'offer' else
              '    MAIN, Character, LookAtCamera, NeckIkEvent,'),
             ('    ConnectHardpointEvent, MoveEvent, MoveFastEvent, TARGET_HARDPOINT,' if kind == 'offer' else
              '    MoveEvent, MoveFastEvent, TARGET_HARDPOINT,'),
             ')', 'from story.cutscenes.anim import Male' + (', Trent' if kind == 'offer' else ''),
             'from story import actors', '']
    props = [('Cigarette', 'cigarette_2'), ('Ashtray', 'ashtray_2'), ('PDA', 'pda')] if kind == 'offer' else []
    for cls, template in props:
        lines += ['', f'class {cls}(Prop):', f'    COMPOUND_TEMPLATE_NAME = {template!r}', '']
    lines += ['', f'class {scene_class}(Scene):', f'    DUMP_FILE = {name!r}',
              '    SCENE_AMBIENT = [128, 128, 128]', '', '    def action(self):',
              '        main_group = self.get_group(MAIN)', '', '        # Персонажи.']
    for n, actor in (('Char_trent', 'Trent'), ('Char_wilham', 'Wilham')):
        lines += [f'        {objects[n]} = Character(root=self, actor=actors.{actor}, light_group=0,',
                  f'                          init_point={n!r}, rotate_from_quat=True)']
    lines += ['', '        # Камеры и их точки *_focus, *2, *_focus2 в Blender.']
    for n in entities:
        if n in cameras:
            fov = entities[n]['cameraprops']['fovh']
            lines.append(f'        {n} = LookAtCamera(root=self, name={n!r}, fov={fov:g})')
    if props:
        lines += ['', '        # Реквизит.']
    for n, cls in (('prop_cigarette_2', 'Cigarette'), ('Prop_ashtray_extra_1', 'Ashtray'), ('Prop_pda', 'PDA')):
        if n not in objects:
            continue
        ambient = ', use_ambient=True' if 'LIT_AMBIENT' in entities[n]['flags'] else ''
        lines += [f'        {objects[n]} = {cls}(root=self, name={objects[n]!r}, light_group=0,',
                  f'                          init_point={n!r}, rotate_from_quat=True{ambient})']
    for n in ('vfx_rtc_sydsmoke_3', 'vfx_rtc_cigaretteglow_4'):
        if n not in objects:
            continue
        lines += [f'        {objects[n]} = Alchemy(root=self, name={objects[n]!r},',
                  f'                          particles={entities[n]["template_name"]!r}, point_name={n!r})']

    used = set(cameras) | {n + '_point' for n in cameras} | set(objects) | set(ik)
    def ref(n):
        if n in objects:
            return objects[n] + '.name'
        if n in ik:
            actor, part = ik[n]
            return f'{actor}.{part}_ik_name'
        if n == 'offscreen':
            return 'self.get_automarker_name(self.OFFSCREEN_POINT_NAME)'
        used.add(n)
        return f'self.get_automarker_name({names[n]!r})'

    def call(target, args):
        chunks = ['group=MAIN'] + args + ['time_delay=t']
        if target.endswith('Event'):
            chunks.insert(0, 'root=self')
        text = f'        {target}('
        for i, chunk in enumerate(chunks):
            addition = chunk + (', ' if i < len(chunks) - 1 else ')')
            if len(text.rsplit('\n', 1)[-1]) + len(addition) > 115:
                text += '\n            '
            text += addition
        return '\n'.join(line.rstrip() for line in text.splitlines())

    def convert(e):
        _, kind, targets, *extra = e
        p = extra[0] if extra else {}
        if kind == 'SET_CAMERA':
            return call(objects[targets[1]] + '.set', [])
        if kind == 'START_MOTION':
            assert set(p) <= {'animation', 'duration', 'time_scale', 'start_time', 'trans_time', 'weight', 'heading', 'event_flags'}, e
            assert p.get('weight', 1) == 1 and p.get('heading', -1) == -1 and p.get('event_flags', 0) in (0, 2), e
            args = [f'anim={anims.get(p["animation"], repr(p["animation"]))}', f'duration={p["duration"]:g}']
            for k, default in (('time_scale', 1), ('start_time', 0), ('trans_time', None)):
                if p.get(k, default) != default:
                    args.append(f'{k}={p[k]:g}')
            if p.get('event_flags') == 2:
                args.append('loop=True')
            return call(objects[targets[0]] + '.motion', args)
        if kind == 'START_SPATIAL_PROP_ANIM':
            a, b = targets
            assert p['spatialprops'] == {'pos': [0, 0, 0], 'q_orient': [1, 0, 0, 0]}, e
            assert p['target_type'] == 'ROOT' and p['target_part'] == '', e
            smooth = 'param_curve' in p
            if smooth:
                assert p['param_curve'] == {'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, e
            args = [f'duration={p["duration"]:g}']
            if not smooth:
                args.append('smooth=False')
            if a in ik:
                actor, part = ik[a]
                return call(f'{actor}.move_{part}_ik', [f'target_name={ref(b)}'] + args)
            for camera in cameras:
                if a in (camera, camera + '_point'):
                    method = 'move_cam' if a == camera else 'move_focus'
                    prefix = camera if a == camera else camera + '_focus'
                    index = names[b].removeprefix(prefix)
                    assert index in ('2', '3'), e
                    used.add(b)
                    return call(f'{camera}.{method}', [f'index={index}'] + args)
            if p['duration'] <= 0.00001:
                return call('MoveFastEvent', [f'object_name={ref(a)}', f'target_name={ref(b)}'])
            return call('MoveEvent', [f'object_name={ref(a)}', f'target_name={ref(b)}'] + args)
        if kind == 'START_IK':
            if p['target_type'] == 'HARDPOINT':
                assert p['end_effector'] == 'Body_Head', e
                return call('NeckIkEvent', [f'char_name={ref(targets[0])}', f'target_name={ref(targets[1])}',
                            f'duration={p["duration"]:g}', 'target_type=TARGET_HARDPOINT',
                            f'target_part={p["target_part"]!r}'])
            actor, part = ik[targets[1]]
            assert objects[targets[0]] == actor and p['target_type'] == 'ROOT', e
            return call(f'{actor}.start_{part}_ik', [f'duration={p["duration"]:g}'])
        if kind == 'ATTACH_ENTITY':
            assert p['up'] == 'Y_AXIS' and p['front'] == 'NEG_Z_AXIS' and p['offset'] == [0, 0, 0], e
            assert p['flags'] in ('POSITION', 'POSITION+ORIENTATION') and p['target_type'] == 'HARDPOINT', e
            return call('AttachEvent', [f'target_name={ref(targets[0])}', f'parent_name={ref(targets[1])}',
                        f'duration={p["duration"]:g}', f'target_part={p["target_part"]!r}',
                        'target_type=TARGET_HARDPOINT', f'adjust_orient={"ORIENTATION" in p["flags"]}'])
        if kind == 'CONNECT_HARDPOINTS':
            return call('ConnectHardpointEvent', [f'target_name={ref(targets[0])}', f'parent_name={ref(targets[1])}',
                        f'duration={p["duration"]:g}', f'target_hardpoint={p["hardpoint"]!r}',
                        f'parent_hardpoint={p["parent_hardpoint"]!r}'])
        if kind == 'START_PSYS':
            return call(objects[targets[0]] + '.start', [f'duration={p["duration"]:g}'])
        raise ValueError(('Unsupported event', e))

    actions, speech, lips, excluded, duplicate_sounds = [], [], [], [], []
    seen_sounds = {}
    for i, e in enumerate(source['events']):
        if any('subtitle' in n.lower() or n.startswith('cam_dbg') for n in e[2]):
            excluded.append(i)
        elif e[1] == 'ATTACH_ENTITY' and e[2][0] in cameras:
            pass  # LookAtCamera creates this attachment.
        elif e[1] == 'START_SOUND':
            match = re.fullmatch(r'DX_m02_offer_(\d+)_(trent|wilham)', e[2][0])
            assert match, e
            key = (e[0], e[2][0])
            if key in seen_sounds:
                assert source['events'][seen_sounds[key]] == e
                duplicate_sounds.append({'event': i, 'same_as': seen_sounds[key]})
                continue
            seen_sounds[key] = i
            speech.append({'index': int(match[1]), 'actor': match[2], 'start': e[0], 'sound': e[2][0]})
        elif e[1] == 'START_MOTION' and e[3]['animation'].lower().startswith('sc_dx_'):
            lips.append((i, e))
        else:
            actions.append((i, e, convert(e)))
    speech.sort(key=lambda x: x['start'])

    def emit(items, base):
        cursor = None
        for _, event, code in sorted(items, key=lambda x: (round(x[1][0], 4), x[0])):
            offset = round(round(event[0], 4) - base, 6)
            if cursor is None:
                lines.append(f'        t = {offset:g}')
            elif offset != cursor:
                lines.append(f'        t += {round(offset - cursor, 6):g}')
            lines.append(code)
            cursor = offset

    lines += ['', '        # Начальная расстановка взглядов.']
    for n, (actor, part) in ik.items():
        lines.append(f'        {actor}.move_{part}_ik(group=MAIN, target_name=self.get_automarker_name({n!r}), immediately=True)')
    lines += ['', '        # Вход.']
    emit([a for a in actions if a[1][0] < speech[0]['start']], 0)
    lines.append(f'        main_group.append_time({speech[0]["start"]:g})')
    used_lips = set()
    for j, line in enumerate(speech):
        start = line['start']
        end = speech[j + 1]['start'] if j + 1 < len(speech) else source['duration']
        clips = [(i, e) for i, e in lips if start <= e[0] < end and e[2] == ['Char_' + line['actor']]]
        assert clips, line
        used_lips.update(i for i, _ in clips)
        # Later facial cues replace the earlier clip, including its unused tail.
        last = max(clips, key=lambda pair: (pair[1][0], pair[0]))[1]
        window_end = last[0] + last[3]['duration']
        line['window'] = round(window_end - start, 6)
        line['source_gap'] = round(end - window_end, 6)
        # Old facial tails may overlap the next speaker. They do not authorize
        # rewinding the new dialogue clock, which facial() advances by the WAV.
        line['gap'] = max(0, line['source_gap'])
        assert dialogue[line['index']]['actor'] == line['actor'], line
        line['ru'] = dialogue[line['index']]['ru']
        section = [a for a in actions if start <= a[1][0] < end]
        lines += ['', f'        # {line["index"]}: {line["actor"]}.']
        lines += ['        # ' + part for part in textwrap.wrap(line['ru'], width=100)]
        emit([a for a in section if a[1][0] < window_end], start)
        lines.append(f'        {line["actor"]}.facial(group=MAIN, index={line["index"]}, auto_lip=True, extra_delay=0)')
        tail = [a for a in section if a[1][0] >= window_end]
        if tail:
            lines.append('        # Действие после реплики.')
            emit(tail, window_end)
        if line['gap']:
            lines.append(f'        main_group.append_time({line["gap"]:g})')
    assert used_lips == {i for i, _ in lips}
    lines.append('')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'master_mission2.py').write_bytes(master_script)
    output = '\n'.join(lines)
    ast.parse(output)
    (out / f'{name}.py').write_text(output, encoding='utf-8')
    points = {names[n]: entities[n]['spatialprops'] for n in entities if n in used}
    characters = {'Char_trent', 'Char_wilham'}
    placements = {names[e[2][1]] for _, e, _ in actions if e[1] == 'START_SPATIAL_PROP_ANIM' and e[2][0] in characters}
    spec = {'name': name, 'scene_class': scene_class, 'source': f'{commit}:DATA/SCRIPTS/MOD/{name}.thn',
            'master_commit': commit, 'master_script_sha256': hashlib.sha256(master_script).hexdigest(),
            'sha256': hashlib.sha256(raw_source).hexdigest(),
            'duration': source['duration'], 'points': points, 'characters': sorted(characters),
            'placements': sorted(placements), 'cameras': sorted(cameras), 'dialogue': speech,
            'names': {n: names[n] for n in entities if n in used},
            'objects': objects, 'ik': ik, 'actions': [i for i, _, _ in actions], 'excluded': excluded,
            'duplicate_sounds': duplicate_sounds}
    (out / 'spec.json').write_text(json.dumps(spec, indent=2), encoding='utf-8')
    (out / 'source.json').write_text(json.dumps(source, indent=2), encoding='utf-8')
    print(f'{len(actions)} actions, {len(speech)} source lines, {len(points)} points; {len(lines)} code lines')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', choices=('offer', 'accept'), default='offer')
    main(parser.parse_args().scene)
