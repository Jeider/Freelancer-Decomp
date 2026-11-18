"""Validate native M02 scenes with the working RU dialogue/audio, in memory."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
GAME = Path('D:/Games/FL_MOD')
PL = GAME / 'Assets/Pythonlancer'
sys.path.insert(0, str(PL))
sys.path.insert(0, str(REPO / 'tools/berlin_cutscene'))
os.chdir(PL)
import read_source

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scene', choices=('jacobo', 'done'), required=True)
parser.add_argument('--installed', action='store_true')
args = parser.parse_args()
api = REPO / 'out/story_cutscenes/m02_followup/api'
if not args.installed:
    content_spec = importlib.util.spec_from_file_location('story.cutscenes.content', api / 'story/cutscenes/content.py')
    content = importlib.util.module_from_spec(content_spec)
    sys.modules[content_spec.name] = content
    content_spec.loader.exec_module(content)
from story.cutscenes import scene
from story.cutscenes.anim import Male
from tools.audio_watcher import AudioWatcher
from jinja2 import Environment, FileSystemLoader, StrictUndefined
out = REPO / f'out/story_cutscenes/m02_{args.scene}'
spec = json.loads((out / 'spec.json').read_text(encoding='utf-8'))
source = json.loads((out / 'source.json').read_text())
name = spec['name']
path = PL / f'story/cutscenes/story_scenes/{name}.py' if args.installed else out / (name + '.py')
text = path.read_text(encoding='utf-8')
tree = ast.parse(text)
assert all(word not in text for word in ('preserve', 'source_extensions', 'ReconstructedScene', 'subtitles', 'try:', 'except '))
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'append_time':
        assert ast.literal_eval(node.args[0]) >= 0, 'Backward dialogue clock'
assert not any(isinstance(n, ast.Return) for n in ast.walk(next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == spec['scene_class']))), 'Early cutoff'
script_path = PL / 'story/scripts/main/mission2.py'
script = ast.parse(script_path.read_text(encoding='utf-8-sig'))
script.body = [n for n in script.body if
               isinstance(n, ast.ImportFrom) and n.module in ('audio', 'story', 'audio.sound', 'story.actors') or
               isinstance(n, ast.ClassDef) and n.name in ('Msn2', spec['props_class'])]
props_node = next(n for n in script.body if isinstance(n, ast.ClassDef) and n.name == spec['props_class'])
props_node.body = [n for n in props_node.body if not (isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id.startswith('THORN') for t in n.targets))]
dialogue_ast_hash = hashlib.sha256(ast.dump(props_node).encode()).hexdigest()
namespace = {}
exec(compile(script, str(script_path), 'exec'), namespace)
props = namespace[spec['props_class']](SimpleNamespace(MISSION_INDEX=2))
modspec = importlib.util.spec_from_file_location('check_' + name, path)
module = importlib.util.module_from_spec(modspec)
modspec.loader.exec_module(module)
scene.DUMPS_PATH = GAME / 'Assets/SCENES/DUMPS' if args.installed else out
template_paths = [str(PL / 'templates')] if args.installed else [str(api / 'templates'), str(PL / 'templates')]
env = Environment(loader=FileSystemLoader(template_paths), undefined=StrictUndefined)
templates = SimpleNamespace(get_result=lambda path, params: env.get_template(path).render(**params))
audio = {}
watch = AudioWatcher.watch_cutscene_audio_duration


def measure(watcher, subfolder, filename, russian=True):
    assert russian and subfolder == 'm02'
    wav = watcher.get_cutscene_audio_ru() / subfolder / filename
    if filename not in audio:
        audio[filename] = {'duration': watch(watcher, subfolder, filename, russian=True),
                           'sha256': hashlib.sha256(wav.read_bytes()).hexdigest(), 'path': str(wav)}
    return audio[filename]['duration']


with patch.object(AudioWatcher, 'watch_cutscene_audio_duration', measure):
    instance = getattr(module, spec['scene_class'])(templates, props, russian=True)
    rendered = instance.get_content()
read_source.SOURCE = SimpleNamespace(read_text=lambda **kw: rendered)
actual = read_source.read()
voices = [e for e in actual['events'] if e[1] == 'START_SOUND' and e[2][0].startswith('DX_')]
assert [e[2][0] for e in voices] == [line['sound'] for line in spec['dialogue']]
assert len(voices) == (13 if args.scene == 'jacobo' else 14)
starts = {line['index']: event[0] for line, event in zip(spec['dialogue'], voices)}
timeline = []
for i, (line, event) in enumerate(zip(spec['dialogue'], voices)):
    end = event[0] + audio[event[2][0][3:] + '.wav']['duration']
    next_start = voices[i + 1][0] if i + 1 < len(voices) else instance.get_duration()
    assert event[0] >= 0 and end <= next_start + 0.00002, (event, end, next_start)
    assert abs(next_start - end - line['gap']) < 0.00002, (line, end, next_start)
    timeline.append({'index': line['index'], 'start': event[0], 'end': end, 'pause': next_start - end})


def ref(n):
    if n == 'Monitor_1':
        return n
    if n == 'offscreen':
        return 'automarker_offscreen_point'
    if n in spec['characters']:
        return n
    if n in spec['objects']:
        return spec['objects'][n]
    if n in spec['ik']:
        actor, part = spec['ik'][n]
        return f'char_ik_Char_{actor}_{part}_ik'
    return 'automarker_' + spec['names'][n]


def equal(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and all(k in b and equal(v, b[k]) for k, v in a.items())
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 0.00002
    return a == b


matched = set()
for index in spec['actions']:
    expected = source['events'][index]
    source_time = expected[0]
    preceding = [line for line in spec['dialogue'] if line['start'] <= source_time]
    expected_time = source_time
    if preceding:
        line = preceding[-1]
        offset = source_time - line['start']
        if offset >= line['window'] - 0.000001:
            offset += audio[line['sound'][3:] + '.wav']['duration'] - line['window']
        expected_time = starts[line['index']] + offset
    targets = [ref(n) for n in expected[2]]
    candidates = [(i, e) for i, e in enumerate(actual['events']) if i not in matched
                  and equal(e[0], expected_time) and e[1] == expected[1] and e[2] == targets]
    params = copy.deepcopy(expected[3]) if len(expected) > 3 else {}
    if index in spec['silent_faces']:
        params['animation'] = Male.GENERIC_ANIM
    found = next((i for i, e in candidates if equal(params, e[3] if len(e) > 3 else {})), None)
    assert found is not None, (index, expected_time, expected, candidates)
    matched.add(found)

entities = {e['entity_name']: e for e in actual['entities']}
assert len(entities) == len(actual['entities']), 'Duplicate entity names'
for e in actual['events']:
    assert set(e[2]) <= entities.keys(), e
    assert 0 <= e[0] <= instance.get_duration(), e
assert all('get_thorn' not in vars(e) for e in instance.entities.values())
assert not any('subtitle' in n.lower() for n in entities)
# Check native templates carry the material scene properties, including the
# ship loadout, character appearances, light groups, camera FOV and sound gain.
source_entities = {e['entity_name']: e for e in source['entities']}
for n in spec['objects']:
    before, after = source_entities[n], entities[ref(n)]
    assert before['type'] == after['type'], n
    assert before['template_name'].lower() == after['template_name'].lower(), n
    for key in ('lt_grp', 'srt_grp', 'usr_flg', 'flags', 'compoundprops', 'cameraprops', 'audioprops'):
        if key in before:
            assert equal(before[key], after.get(key)), (n, key, before[key], after.get(key))
    if 'loadout' in before.get('userprops', {}):
        assert before['userprops']['loadout'] == after['userprops']['loadout']
    if n in spec['characters']:
        original_actor = before['userprops'].get('actor')
        new_actor = after['userprops'].get('Actor')
        assert (original_actor or '').lower() == (new_actor or '').lower(), (n, original_actor, new_actor)
        if not original_actor:
            assert 'Actor' not in after['userprops']
for cam in spec['cameras']:
    assert any(e[1] == 'ATTACH_ENTITY' and e[2] == [cam, 'automarker_' + cam + '_focus']
               and e[3]['duration'] >= instance.get_duration() for e in actual['events'])
for marker, (actor, part) in spec['ik'].items():
    assert any(e[0] == 0 and e[1] == 'START_SPATIAL_PROP_ANIM' and
               e[2] == [f'char_ik_Char_{actor}_{part}_ik', 'automarker_' + marker] for e in actual['events'])

report = {'scene_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'dump_sha256': hashlib.sha256((scene.DUMPS_PATH / (name + '.json')).read_bytes()).hexdigest(),
          'dialogue_ast_sha256': dialogue_ast_hash, 'source_actions_checked': len(matched),
          'ru_lines': len(voices), 'duration': instance.get_duration(), 'missing_references': [],
          'backward_time_steps': 0, 'overlapping_speech': 0, 'timeline': timeline, 'ru_audio': audio,
          'installed': args.installed, 'final_thn_written': False}
(out / ('installed_check.json' if args.installed else 'check.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(f'{name}: {len(voices)} working RU lines, {len(matched)} actions, {instance.get_duration():.3f}s; PASS')
