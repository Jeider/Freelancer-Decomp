"""Validate full master RTC choreography and RU audio entirely in memory."""
import argparse
import ast
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
from inventory import OUT, PL, REPO, GIT, sha

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scene')
parser.add_argument('--installed', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(PL))
os.chdir(PL)
api = OUT / 'api'


def load(name, path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[name] = module
    module_spec.loader.exec_module(module)
    return module


if not args.installed:
    load('story.cutscenes.content', api / 'story/cutscenes/content.py')
    load('story.cutscenes.scene', api / 'story/cutscenes/scene.py')
from story.cutscenes import scene
from story import script
from tools.audio_watcher import AudioWatcher
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydub import AudioSegment
import read_source

inventory = json.loads((OUT / 'inventory.json').read_text())
commit = inventory['commit']
paths = subprocess.check_output(GIT + ['ls-tree', '-r', '--name-only', commit], text=True).splitlines()
lookup = {p.lower(): p for p in paths}
cache_file = OUT / 'master_ru_audio.json'
audio = json.loads(cache_file.read_text()) if cache_file.exists() else {}
props_by_prefix = {}
for mission in range(3, 9):
    path = OUT / f'master_mission{mission}.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    tree.body = [n for n in tree.body if
                 isinstance(n, ast.ImportFrom) and n.module in ('audio', 'story', 'audio.sound', 'story.actors') or
                 isinstance(n, ast.ClassDef) and (n.name == f'Msn{mission}' or any(
                     isinstance(b, ast.Attribute) and b.attr == 'CutsceneProps' for b in n.bases))]
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef):
            cls.body = [n for n in cls.body if not (isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id.startswith('THORN') for t in n.targets))]
    module = ModuleType(f'story.scripts.main.mission{mission}')
    exec(compile(tree, str(path), 'exec'), vars(module))
    # Foreign dialogue lookup uses the same immutable master fixture.
    sys.modules[module.__name__] = module
    for cls in vars(module).values():
        if isinstance(cls, type) and issubclass(cls, script.CutsceneProps):
            props_by_prefix[f'm{mission:02}_{cls.ALIAS}'] = cls

template_paths = [str(PL / 'templates')] if args.installed else [str(api / 'templates'), str(PL / 'templates')]
env = Environment(loader=FileSystemLoader(template_paths), undefined=StrictUndefined)
templates = SimpleNamespace(get_result=lambda path, params: env.get_template(path).render(**params))


def measure(watcher, subfolder, filename, russian=True):
    assert russian, 'RU only'
    key = f'{subfolder}/{filename}'
    if key not in audio:
        path = lookup[f'data/audio/mod/{key}'.lower()]
        data = subprocess.check_output(GIT + ['show', f'{commit}:{path}'])
        # Contain FFmpeg's temporary pipe cache while keeping native relative
        # metadata paths rooted in Pythonlancer outside the decode operation.
        os.chdir(OUT)
        try:
            wav = AudioSegment.from_file(io.BytesIO(data), format='wav')
        finally:
            os.chdir(PL)
        audio[key] = dict(commit=commit, path=path, sha256=sha(data), duration=wav.duration_seconds)
        cache_file.write_text(json.dumps(audio, indent=2), encoding='utf-8')
    assert audio[key]['commit'] == commit
    return audio[key]['duration']


def equal(a, b, tolerance=.00002):
    if isinstance(a, dict):
        return isinstance(b, dict) and all(k in b and equal(v, b[k], tolerance) for k, v in a.items())
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(equal(x, y, tolerance) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < tolerance
    if isinstance(a, str) and isinstance(b, str) and ('+' in a or '+' in b):
        return {s.strip() for s in a.split('+')} == {s.strip() for s in b.split('+')}
    return a == b


def check(name):
    folder = OUT / name
    spec = json.loads((folder / 'spec.json').read_text(encoding='utf-8'))
    source = json.loads((folder / 'source.json').read_text())
    path = PL / f'story/cutscenes/story_scenes/{name}.py' if args.installed else folder / f'{name}.py'
    text = path.read_text(encoding='utf-8')
    assert all(term not in text for term in ('preserve_', 'source_extensions', 'ReconstructedScene', 'try:', 'except '))
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'append_time':
            assert ast.literal_eval(node.args[0]) >= 0
    module = load('check_' + name, path)
    mission = int(name[1:3])
    props_cls = props_by_prefix.get(spec['primary']) or type('SilentProps', (script.CutsceneProps,),
                                                          dict(MISSION_INDEX=mission, ALIAS=name[4:]))
    props = props_cls(SimpleNamespace(MISSION_INDEX=mission))
    scene.DUMPS_PATH = PL.parent / 'SCENES/DUMPS' if args.installed else folder
    with patch.object(AudioWatcher, 'watch_cutscene_audio_duration', measure):
        instance = getattr(module, spec['scene_class'])(templates, props, russian=True)
        rendered = instance.get_content()
    read_source.SOURCE = SimpleNamespace(read_text=lambda **kw: rendered)
    actual = read_source.read()
    all_voices = sorted([e for e in actual['events'] if e[1] == 'START_SOUND' and e[2][0].startswith('DX_m')], key=lambda e: e[0])
    voices = list({(e[0], e[2][0]): e for e in all_voices}.values())
    assert len(all_voices) == len(voices) + len(spec['duplicates'])
    assert [e[2][0] for e in voices] == [line['sound'] for line in spec['dialogue']], (name, voices)
    starts = {line['event']: e[0] for line, e in zip(spec['dialogue'], voices)}
    durations = {line['event']: measure(None, line['prefix'][:3], line['sound'][3:] + '.wav') for line in spec['dialogue']}
    timeline = []
    for i, (line, event) in enumerate(zip(spec['dialogue'], voices)):
        next_start = voices[i + 1][0] if i + 1 < len(voices) else instance.get_duration()
        end = event[0] + durations[line['event']]
        if spec['absolute']:
            assert equal(event[0], line['start'])
        elif line['window'] is not None:
            assert equal(next_start - end, line['gap']), (line, end, next_start)
        else:
            assert equal(next_start - event[0], line['gap'])
        timeline.append(dict(sound=line['sound'], start=event[0], end=end,
                             source_window=line['window'], source_gap=line['source_gap'], pause=next_start - end))
    source_entities = {e['entity_name']: e for e in source['entities']}

    def ref(n):
        if n not in source_entities or n == 'Monitor_1' or n.startswith('DX_m'):
            return n
        if n.lower() == 'offscreen':
            return 'automarker_offscreen_point'
        if n in spec['objects']:
            return n
        return 'automarker_' + spec['names'][n]

    def expected_time(time):
        if spec['absolute']:
            return time
        preceding = [line for line in spec['dialogue'] if line['start'] <= time]
        if not preceding:
            return time
        line = preceding[-1]
        offset = time - line['start']
        if line['window'] is not None and offset >= line['window'] - .000001:
            offset += durations[line['event']] - line['window']
        return starts[line['event']] + offset

    matched = set()
    for index in spec['actions'] + spec['attachment_events']:
        expected = source['events'][index]
        time = expected_time(expected[0])
        targets = [ref(n) for n in expected[2]]
        candidates = [(i, e) for i, e in enumerate(actual['events']) if i not in matched and
                      equal(e[0], time) and e[1] == expected[1] and e[2] == targets]
        params = expected[3] if len(expected) > 3 else {}
        found = next((i for i, e in candidates if equal(params, e[3] if len(e) > 3 else {})), None)
        assert found is not None, (index, time, expected, candidates)
        matched.add(found)
    entities = {e['entity_name']: e for e in actual['entities']}
    assert len(entities) == len(actual['entities'])
    missing_source = sorted({n for e in source['events'] for n in e[2] if n not in source_entities})
    missing_actual = sorted({n for e in actual['events'] for n in e[2] if n not in entities})
    assert set(missing_actual) <= set(missing_source), (missing_actual, missing_source)
    assert all(e[0] >= 0 for e in actual['events'])
    late_events = [e for e in actual['events'] if e[0] > instance.get_duration()]
    assert all('get_thorn' not in vars(e) for e in instance.entities.values())
    for n in spec['objects']:
        before, after = copy.deepcopy(source_entities[n]), entities[n]
        before['type'] = {1: 'COMPOUND', 5: 'LIGHT'}.get(before['type'], before['type'])
        if before.get('flags') == 4:
            before['flags'] = 'LIT_AMBIENT'
        if 'floor_height' in before.get('compoundprops', {}) and isinstance(before['compoundprops']['floor_height'], str):
            before['compoundprops']['floor_height'] = float(before['compoundprops']['floor_height'].lstrip('='))
        assert before['type'] == after['type'], (n, before['type'], after['type'])
        assert before['template_name'].lower() == after['template_name'].lower(), (n, before, after)
        for key in ('lt_grp', 'srt_grp', 'usr_flg', 'compoundprops', 'cameraprops', 'audioprops'):
            if key in before:
                actual_value = after.get(key, 0 if key in ('lt_grp', 'srt_grp', 'usr_flg') else None)
                assert equal(before[key], actual_value), (n, key, before[key], actual_value)
        if 'pathprops' in before:
            import re
            assert before['pathprops']['path_type'] == after['pathprops']['path_type']
            a, b = [re.findall(r'-?\d+(?:\.\d+)?', value['pathprops']['path_data']) for value in (before, after)]
            assert equal(list(map(float, a)), list(map(float, b))), (n, 'path_data')
        if 'flags' in before:
            assert equal(before['flags'], after.get('flags')), (n, 'flags', before['flags'], after.get('flags'))
        if before['type'] == 'LIGHT':
            lp = before['lightprops']
            lp['type'] = {1: 'L_POINT', 2: 'L_SPOT', 3: 'L_DIRECT'}.get(lp['type'], lp['type'])
            lp['on'] = {1: 'Y', 0: 'N'}.get(lp['on'], lp['on'])
            assert equal(lp, after['lightprops']), (n, lp, after['lightprops'])
        if n in spec['characters']:
            user = {k.lower(): v for k, v in before.get('userprops', {}).items()}
            assert user.get('actor') == after['userprops'].get('Actor'), (n, user, after['userprops'])
        for key in ('loadout', 'NoFog'):
            if key in before.get('userprops', {}):
                assert before['userprops'][key] == after['userprops'][key]
        if before['type'] not in ('SOUND', 'CAMERA') or n not in spec['focus']:
            sp = before.get('spatialprops')
            if sp:
                assert equal(sp['pos'], after['spatialprops']['pos'], .011), (n, 'position', sp, after['spatialprops'])
                assert equal(sp['orient'], after['spatialprops']['orient'], .0001), (n, 'orientation', sp, after['spatialprops'])
    for n, p in spec['points'].items():
        marker = entities['automarker_' + n]
        assert equal(p['pos'], marker['spatialprops']['pos'], .011), n
        assert equal(p['orient'], marker['spatialprops']['orient'], .0001), (n, p, marker)
    report = dict(scene_sha256=sha(path.read_bytes()), dump_sha256=sha((scene.DUMPS_PATH / f'{name}.json').read_bytes()),
                  master_commit=commit, master_actions_checked=len(matched), master_lines=len(voices),
                  duration=instance.get_duration(), timeline=timeline, source_unresolved_references=missing_source,
                  inherited_unresolved_references=missing_actual, events_past_scene_end=late_events,
                  source_negative_lip_gaps=[s for s in spec['dialogue'] if s['source_gap'] is not None and s['source_gap'] < 0],
                  ru_audio={line['sound']: audio[line['prefix'][:3] + '/' + line['sound'][3:] + '.wav'] for line in spec['dialogue']},
                  installed=args.installed, final_thn_written=False)
    (folder / ('installed_check.json' if args.installed else 'check.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'{name}: PASS; {len(voices)} master RU lines; {len(matched)} actions; {len(missing_actual)} inherited unresolved references', flush=True)
    return report


failures, results = {}, {}
for name in ([args.scene] if args.scene else inventory['scenes']):
    try:
        results[name] = check(name)
    except Exception as exc:
        failures[name] = repr(exc)
        print(name, repr(exc), flush=True)
(OUT / ('installed_validation.json' if args.installed else 'validation.json')).write_text(json.dumps(
    dict(failures=failures, passed=list(results), final_thn_written=False), indent=2), encoding='utf-8')
if failures:
    raise SystemExit(1)
