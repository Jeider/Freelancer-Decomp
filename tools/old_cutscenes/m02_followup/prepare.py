"""Import M02 Jacobo/done into the ordinary scene API; never write DATA."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import textwrap
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[3]
GAME = Path('D:/Games/FL_MOD')
PL = GAME / 'Assets/Pythonlancer'
SCENES = {
    'jacobo': ('m02_jacobo_offer', 'M02JacoboOfferScene', 'Msn2Miner', 'miner'),
    'done': ('m02_reichman', 'M02ReichmanScene', 'Msn2Done', 'done'),
}
sys.path.insert(0, str(REPO / 'tools/berlin_cutscene'))
import read_source


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(kind):
    name, scene_class, props_class, alias = SCENES[kind]
    out = REPO / f'out/story_cutscenes/m02_{kind}'
    out.mkdir(parents=True, exist_ok=True)
    git = ['git', '-c', f'safe.directory={GAME.as_posix()}', '-C', str(GAME)]
    commit = subprocess.check_output(git + ['rev-parse', 'master'], text=True).strip()
    raw = subprocess.check_output(git + ['show', f'{commit}:DATA/SCRIPTS/MOD/{name}.thn'])
    read_source.SOURCE = SimpleNamespace(read_text=lambda **kw: raw.decode('utf-8-sig'))
    source = read_source.read()
    entities = {e['entity_name']: e for e in source['entities']}
    # The working dialogue remains authoritative. Import only these two classes
    # in the checker, so an unrelated unfinished offer cannot affect validation.
    script = (PL / 'story/scripts/main/mission2.py').read_bytes()
    props = next(n for n in ast.parse(script.decode('utf-8-sig')).body
                 if isinstance(n, ast.ClassDef) and n.name == props_class)
    dialogue = {n.args[0].value: {'actor': n.args[1].id.lower(),
                'ru': next(k.value.value for k in n.keywords if k.arg == 'ru')}
                for n in ast.walk(props) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == 'VoiceLine'}
    cameras = {n for n, e in entities.items() if e['type'] == 'CAMERA' and not n.startswith('cam_dbg')}
    characters = {n for n, e in entities.items() if e['type'] == 'DEFORMABLE'}
    objects = {n: n.removeprefix('Char_') for n in characters}
    objects.update({n: n for n in cameras})
    objects.update({n: n for n, e in entities.items() if e['type'] == 'SOUND' and not n.startswith('DX_')})
    objects.update({'prop_notebook': 'notebook'} if kind == 'jacobo' else {'main_ship': 'main_ship'})
    focus = {e[2][0]: e[2][1] for e in source['events'] if e[1] == 'ATTACH_ENTITY' and e[2][0] in cameras}
    assert set(focus) == cameras
    names = {n: n for n in entities}
    for cam, target in focus.items():
        names[target] = cam + '_focus'
        for n in entities:
            for prefix, dest in ((cam + '_pos', cam), (target + '_pos', cam + '_focus'),
                                 (target, cam + '_focus')):
                suffix = n.removeprefix(prefix)
                if n.startswith(prefix) and suffix.isdecimal():
                    names[n] = dest + suffix
    targets = {n for e in source['events'] for n in e[2]}
    ik = {f'{objects[n]}_{part}_ik': (objects[n], part) for n in sorted(characters)
          for part in ('head', 'eye') if f'{objects[n]}_{part}_ik' in targets}
    anims = {}
    for cls in ast.parse((PL / 'story/cutscenes/anim.py').read_text(encoding='utf-8')).body:
        if isinstance(cls, ast.ClassDef) and cls.name in ('Male', 'Trent'):
            for item in cls.body:
                if isinstance(item, ast.Assign) and isinstance(item.value, ast.Constant):
                    anims.setdefault(item.value.value, cls.name + '.' + item.targets[0].id)

    title = 'Встреча с Якобо' if kind == 'jacobo' else 'Завершение задания у Рейхмана'
    lines = [f'"""{title}: обычный API Pythonlancer, относительная постановка реплик."""',
             'from story.cutscenes.scene import Scene', 'from story.cutscenes.content import (',
             '    MAIN, Character, LookAtCamera, Prop, Ship, Sound, MotionEvent,',
             '    MoveEvent, MoveFastEvent, NeckIkEvent, EyeIkEvent, ConnectHardpointEvent,',
             '    TARGET_PART,', ')', 'from story.cutscenes.anim import Male, Trent',
             'from story import actors', '']
    if kind == 'jacobo':
        lines += ['', 'class Notebook(Prop):', "    COMPOUND_TEMPLATE_NAME = 'notebook'", '',
                  '', 'class Bartender(actors.Actor):', "    NAME = 'bartender'", "    TYPE = 'male'",
                  "    CUTSCENE_APPEARANCE = 'botzler'", '', '',
                  'class BartenderFixture(Bartender):', "    NAME = 'bartender_fixture'",
                  "    GAME_ACTOR = 'bartender'", '']
    else:
        lines += ['', 'class MainShip(Ship):', "    COMPOUND_TEMPLATE_NAME = 'rh_elite'", '']
        for i in (1, 2):
            lines += ['', f'class Trooper{i}(actors.Actor):', f"    NAME = 'trooper{i}'",
                      "    TYPE = 'male'", f"    CUTSCENE_APPEARANCE = 'ms2_trooper{i}'",
                      f"    GAME_ACTOR = 'Trooper{i}'", '']
    lines += ['', f'class {scene_class}(Scene):', f'    DUMP_FILE = {name!r}',
              '    SCENE_AMBIENT = [128, 128, 128]', '', '    def action(self):',
              '        main_group = self.get_group(MAIN)', '', '        # Персонажи.']
    for n in entities:
        if n not in characters:
            continue
        actor = objects[n]
        actor_class = {'bartender': 'Bartender', 'bartender_fixture': 'BartenderFixture',
                       'trooper1': 'Trooper1', 'trooper2': 'Trooper2'}.get(actor, 'actors.' + actor.capitalize())
        lines += [f'        {actor} = Character(root=self, actor={actor_class}, light_group={entities[n]["lt_grp"]},',
                  f'            init_point={n!r}, rotate_from_quat=True' +
                  (', bind_actor=False)' if n == 'Char_bartender' else ')')]
    lines += ['', '        # Камеры: *_focus, *2 / *_focus2 и следующие позиции в Blender.']
    for n in entities:
        if n in cameras:
            lines.append(f'        {n} = LookAtCamera(root=self, name={n!r}, fov={entities[n]["cameraprops"]["fovh"]:g})')
    lines += ['', '        # Реквизит и звук.']
    if kind == 'jacobo':
        lines += ["        notebook = Notebook(root=self, name='notebook', light_group=0,",
                  "            init_point='prop_notebook', rotate_from_quat=True)"]
    else:
        lines += ["        main_ship = MainShip(root=self, name='main_ship', light_group=3,",
                  "            init_point='main_ship', rotate_from_quat=True, loadout='level_rh_elite_loadout04')"]
    for n, e in entities.items():
        if e['type'] == 'SOUND' and n in objects:
            p = e['audioprops']
            priority = e.get('userprops', {}).get('Priority')
            lines += [f'        {n} = Sound(root=self, name={n!r}, sound={e["template_name"]!r},',
                      f'            attenuation={p["attenuation"]}, dmin={p["dmin"]}, dmax={p["dmax"]}, priority={priority!r})']

    used = cameras | set(focus.values()) | characters | set(ik) | ({'prop_notebook'} if kind == 'jacobo' else {'main_ship'})

    def ref(n):
        if n == 'offscreen':
            return 'self.get_automarker_name(self.OFFSCREEN_POINT_NAME)'
        if n in objects:
            return objects[n] + '.name'
        if n in ik:
            actor, part = ik[n]
            return f'{actor}.{part}_ik_name'
        used.add(n)
        return f'self.get_automarker_name({names[n]!r})'

    def call(target, args):
        chunks = (['root=self'] if target.endswith('Event') else []) + ['group=MAIN'] + args + ['time_delay=t']
        result = f'        {target}('
        for i, chunk in enumerate(chunks):
            addition = chunk + (', ' if i < len(chunks) - 1 else ')')
            if len(result.rsplit('\n', 1)[-1]) + len(addition) > 112:
                result += '\n            '
            result += addition
        return '\n'.join(s.rstrip() for s in result.splitlines())

    def convert(e):
        _, event, target, *extra = e
        p = extra[0] if extra else {}
        if event == 'SET_CAMERA':
            return call(objects[target[1]] + '.set', [])
        if event == 'START_MOTION':
            assert set(p) <= {'animation', 'duration', 'time_scale', 'start_time', 'trans_time', 'weight', 'heading', 'event_flags'}, e
            assert p.get('weight', 1) == 1 and p.get('heading', -1) == -1 and p.get('event_flags', 0) in (0, 2), e
            args = [f'anim={anims.get(p["animation"], repr(p["animation"]))}', f'duration={p["duration"]:g}']
            for k, default in (('time_scale', 1), ('start_time', 0), ('trans_time', None)):
                if p.get(k, default) != default:
                    args.append(f'{k}={p[k]:g}')
            if p.get('event_flags') == 2:
                args.append('loop=True')
            if target[0] in characters:
                return call(objects[target[0]] + '.motion', args)
            return call('MotionEvent', [f'object_name={ref(target[0])}'] + args)
        if event == 'START_SPATIAL_PROP_ANIM':
            a, b = target
            assert p['spatialprops'] == {'pos': [0, 0, 0], 'q_orient': [1, 0, 0, 0]}, e
            assert p['target_type'] == 'ROOT' and p['target_part'] == '', e
            smooth = 'param_curve' in p
            if smooth:
                assert p['param_curve'] == {'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, e
            args = [f'duration={p["duration"]:g}'] + ([] if smooth else ['smooth=False'])
            if a in ik:
                actor, part = ik[a]
                return call(f'{actor}.move_{part}_ik', [f'target_name={ref(b)}'] + args)
            for cam, marker in focus.items():
                if a in (cam, marker):
                    method, prefix = ('move_cam', cam) if a == cam else ('move_focus', cam + '_focus')
                    index = names[b].removeprefix(prefix)
                    assert index.isdecimal(), e
                    used.add(b)
                    return call(f'{cam}.{method}', [f'index={index}'] + args)
            if p['duration'] <= 0.00001:
                return call('MoveFastEvent', [f'object_name={ref(a)}', f'target_name={ref(b)}'])
            return call('MoveEvent', [f'object_name={ref(a)}', f'target_name={ref(b)}'] + args)
        if event == 'START_IK':
            args = [f'duration={p["duration"]:g}']
            if p['transition_duration'] != 1:
                args.append(f'transition_duration={p["transition_duration"]:g}')
            if p['target_type'] == 'PART':
                cls = 'NeckIkEvent' if p['end_effector'] == 'Body_Head' else 'EyeIkEvent'
                return call(cls, [f'char_name={ref(target[0])}', f'target_name={ref(target[1])}',
                                 'target_type=TARGET_PART', f'target_part={p["target_part"]!r}'] + args)
            actor, part = ik[target[1]]
            assert objects[target[0]] == actor and p['target_type'] == 'ROOT', e
            return call(f'{actor}.start_{part}_ik', args)
        if event == 'START_CAMERA_PROP_ANIM':
            assert set(p['cameraprops']) == {'fovh'}
            return call(objects[target[0]] + '.change_fov', [f'fov={p["cameraprops"]["fovh"]:g}',
                        f'duration={p["duration"]:g}', f'smooth={"param_curve" in p}'])
        if event == 'START_SOUND':
            assert p.get('flags') in (None, 'LOOP'), e
            return call(objects[target[0]] + '.start', [f'duration={p["duration"]:g}'] +
                        (['loop=True'] if p.get('flags') == 'LOOP' else []))
        if event == 'START_AUDIO_PROP_ANIM':
            assert set(p['audioprops']) == {'attenuation'} and 'param_curve' not in p
            return call(objects[target[0]] + '.change_attenuation', [f'duration={p["duration"]:g}',
                        f'attenuation={p["audioprops"]["attenuation"]:g}'])
        if event == 'CONNECT_HARDPOINTS':
            return call('ConnectHardpointEvent', [f'target_name={ref(target[0])}', f'parent_name={ref(target[1])}',
                        f'duration={p["duration"]:g}', f'target_hardpoint={p["hardpoint"]!r}',
                        f'parent_hardpoint={p["parent_hardpoint"]!r}'])
        raise ValueError(('Unsupported event', e))

    actions, speech, lips, excluded, attachments, silent_faces = [], [], [], [], [], []
    first_speech = min(e[0] for e in source['events'] if e[1] == 'START_SOUND' and e[2][0].startswith('DX_'))
    for i, e in enumerate(source['events']):
        if any('subtitle' in n.lower() or n.startswith('cam_dbg') for n in e[2]):
            excluded.append(i)
        elif e[1] == 'ATTACH_ENTITY' and e[2][0] in cameras:
            assert e[0] == 0 and e[3]['flags'] == 'LOOK_AT', e
            attachments.append(i)
        elif e[1] == 'START_SOUND' and e[2][0].startswith('DX_'):
            match = re.fullmatch(rf'DX_m02_{alias}_(\d+)_(\w+)', e[2][0])
            assert match, e
            speech.append({'index': int(match[1]), 'actor': match[2], 'start': e[0], 'sound': e[2][0]})
        elif e[1] == 'START_MOTION' and e[3]['animation'].lower().startswith('sc_dx_'):
            if e[0] < first_speech:
                # Trent's silent exchange with the bartender is already a generic
                # face motion in the working scene, not a missing spoken line.
                assert kind == 'jacobo' and i == 34 and e[2] == ['Char_trent']
                code = call('trent.motion', ['anim=Male.GENERIC_ANIM', 'duration=10',
                                            'time_scale=0.6', 'trans_time=0.25'])
                actions.append((i, e, code))
                silent_faces.append(i)
            else:
                lips.append((i, e))
        else:
            actions.append((i, e, convert(e)))
    speech.sort(key=lambda line: line['start'])
    assert {line['index'] for line in speech} == set(dialogue)

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
        last = max(clips, key=lambda pair: (pair[1][0], pair[0]))[1]
        window_end = last[0] + last[3]['duration']
        line.update(window=round(window_end - start, 6), source_gap=round(end - window_end, 6))
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
    assert used_lips == {i for i, _ in lips}, [(i, e) for i, e in lips if i not in used_lips]
    assert len(actions) + len(speech) + len(lips) + len(excluded) + len(attachments) == len(source['events'])
    output = '\n'.join(lines) + '\n'
    tree = ast.parse(output)
    # Keep generated scene imports readable and limited to actual API use.
    used_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    for node in reversed(tree.body):
        if isinstance(node, ast.ImportFrom) and node.module in ('story.cutscenes.content', 'story.cutscenes.anim'):
            replacement = f'from {node.module} import (\n    ' + ', '.join(n.name for n in node.names if n.name in used_names) + ',\n)'
            parts = output.splitlines()
            parts[node.lineno - 1:node.end_lineno] = replacement.splitlines()
            output = '\n'.join(parts) + '\n'
    ast.parse(output)
    (out / (name + '.py')).write_text(output, encoding='utf-8')
    dump_path = GAME / f'Assets/SCENES/DUMPS/{name}.json'
    dump = json.loads(dump_path.read_text())
    old_points = {}
    for n in sorted(used):
        old = n if n in dump else names[n]
        assert old in dump, (n, old)
        old_points[names[n]] = old
    assert len(old_points) == len(used)
    placements = {names[e[2][1]]: e[2][0] for _, e, _ in actions
                  if e[1] == 'START_SPATIAL_PROP_ANIM' and e[2][0] in characters and e[2][1] != 'offscreen'}
    spec = {'name': name, 'scene_class': scene_class, 'props_class': props_class, 'kind': kind,
            'source': f'{commit}:DATA/SCRIPTS/MOD/{name}.thn', 'sha256': sha(raw),
            'source_commit': commit, 'duration': source['duration'], 'names': names, 'objects': objects,
            'characters': sorted(characters), 'cameras': sorted(cameras), 'ik': ik, 'focus': focus,
            'old_points': old_points, 'placements': placements, 'dialogue': speech,
            'actions': [i for i, _, _ in actions], 'excluded': excluded, 'attachments': attachments,
            'silent_faces': silent_faces,
            'lip_events': [i for i, _ in lips], 'original_dump_sha256': sha(dump_path.read_bytes()),
            'original_blend_sha256': sha((GAME / f'Assets/SCENES/{name}.blend').read_bytes()),
            'original_scene_sha256': sha((PL / f'story/cutscenes/story_scenes/{name}.py').read_bytes())}
    (out / 'spec.json').write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding='utf-8')
    (out / 'source.json').write_text(json.dumps(source, indent=2), encoding='utf-8')
    print(f'{name}: {len(actions)} actions, {len(speech)} RU lines, {len(old_points)} current points')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', choices=SCENES, required=True)
    main(parser.parse_args().scene)
