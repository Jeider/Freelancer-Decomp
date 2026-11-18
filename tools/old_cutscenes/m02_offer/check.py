"""Check the selected master scene with measured master RU audio, in memory."""
import argparse
import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
GAME = Path('D:/Games/FL_MOD')
PL = GAME / 'Assets/Pythonlancer'
OUT = REPO / 'out/story_cutscenes/m02_offer'
sys.path.insert(0, str(PL))
sys.path.insert(0, str(REPO / 'tools/berlin_cutscene'))
os.chdir(PL)
import read_source
from story.cutscenes import scene
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydub import AudioSegment

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--installed', action='store_true')
parser.add_argument('--scene', choices=('offer', 'accept'), default='offer')
parser.add_argument('--staged-dump', action='store_true')
args = parser.parse_args()
OUT = REPO / f'out/story_cutscenes/m02_{args.scene}'
spec = json.loads((OUT / 'spec.json').read_text())
source = json.loads((OUT / 'source.json').read_text())
name = spec['name']
path = PL / f'story/cutscenes/story_scenes/{name}.py' if args.installed else OUT / (name + '.py')
text = path.read_text(encoding='utf-8')
tree = ast.parse(text)
assert all(word not in text for word in ('preserve_', 'source_extensions', 'ReconstructedScene', 'subtitles', 'try:', 'except '))
assert not any(isinstance(n, ast.Return) for n in ast.walk(tree)), 'Early scene cutoff'
for n in ast.walk(tree):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'append_time':
        assert ast.literal_eval(n.args[0]) >= 0, 'Backward dialogue clock'

audio_path = OUT / 'master_ru_audio.json'
if not args.installed:
    audio = {}
    for line in spec['dialogue']:
        filename = line['sound'][3:] + '.wav'
        data = subprocess.check_output(['git', '-C', str(GAME), 'show',
                                       f"{spec['master_commit']}:DATA/AUDIO/MOD/M02/{filename}"])
        clip = AudioSegment.from_file(io.BytesIO(data), format='wav')
        audio[filename] = {'duration': clip.duration_seconds, 'sha256': hashlib.sha256(data).hexdigest()}
    audio_path.write_text(json.dumps({'commit': spec['master_commit'], 'files': audio}, indent=2), encoding='utf-8')
else:
    measured = json.loads(audio_path.read_text())
    assert measured['commit'] == spec['master_commit']
    audio = measured['files']

# Only the offline fixture reads archived WAVs instead of the installed audio.
# The scene uses normal props and sound lookup, without runtime substitutions.
master_bytes = (OUT / 'master_mission2.py').read_bytes()
assert hashlib.sha256(master_bytes).hexdigest() == spec['master_script_sha256']
master = ast.parse(master_bytes.decode('utf-8-sig'))
master.body = [n for n in master.body if isinstance(n, (ast.Import, ast.ImportFrom)) or
               isinstance(n, ast.ClassDef) and n.name in ('Msn2', 'Msn2Offer')]
namespace = {}
exec(compile(master, 'master:mission2.py', 'exec'), namespace)
props = namespace['Msn2Offer'](SimpleNamespace(MISSION_INDEX=2))
modspec = importlib.util.spec_from_file_location('check_master_offer', path)
module = importlib.util.module_from_spec(modspec)
modspec.loader.exec_module(module)
scene.DUMPS_PATH = OUT if args.staged_dump else GAME / 'Assets/SCENES/DUMPS'
env = Environment(loader=FileSystemLoader(str(PL / 'templates')), undefined=StrictUndefined)
templates = SimpleNamespace(get_result=lambda path, params: env.get_template(path).render(**params))


def duration(subfolder, filename, russian=True):
    assert russian and subfolder == 'm02'
    return audio[filename]['duration']


with patch('audio.sound.AudioWatcher.watch_cutscene_audio_duration', side_effect=duration):
    scene_class = getattr(module, spec.get('scene_class', 'Msn2OfferScene'))
    instance = scene_class(templates, props, extra_name='accept' if args.scene == 'accept' else '', russian=True)
    rendered = instance.get_content()
read_source.SOURCE = SimpleNamespace(read_text=lambda **kwargs: rendered)
actual = read_source.read()
voice_events = [e for e in actual['events'] if e[1] == 'START_SOUND']
assert [e[2][0] for e in voice_events] == [line['sound'] for line in spec['dialogue']]
assert len(voice_events) == (6 if args.scene == 'accept' else 19)
timeline = []
for i, event in enumerate(voice_events):
    end = event[0] + audio[event[2][0][3:] + '.wav']['duration']
    next_start = voice_events[i + 1][0] if i + 1 < len(voice_events) else instance.get_duration()
    assert event[0] >= 0 and end <= next_start + 0.00001, (event, end, next_start)
    timeline.append({'index': spec['dialogue'][i]['index'], 'start': event[0], 'end': end, 'pause': next_start - end})
starts = {line['index']: event[0] for line, event in zip(spec['dialogue'], voice_events)}


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
    candidates = [e for e in actual['events'] if equal(e[0], expected_time) and e[1] == expected[1] and e[2] == targets]
    expected_props = expected[3] if len(expected) > 3 else {}
    assert any(equal(expected_props, e[3] if len(e) > 3 else {}) for e in candidates), (index, expected_time, expected, candidates)

entities = {e['entity_name'] for e in actual['entities']}
assert len(entities) == len(actual['entities']), 'Duplicate entity names'
for event in actual['events']:
    assert set(event[2]) <= entities, event
    assert 0 <= event[0] <= instance.get_duration(), event
assert all('get_thorn' not in vars(e) for e in instance.entities.values())
report = {'master_commit': spec['master_commit'], 'scene_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'source_actions_checked': len(spec['actions']), 'master_ru_lines': len(voice_events),
          'duration': instance.get_duration(), 'backward_time_steps': 0, 'overlapping_speech': 0,
          'missing_references': [], 'timeline': timeline, 'installed': args.installed}
(OUT / ('installed_check.json' if args.installed else 'check.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(f"Master RU: {len(voice_events)} lines, {len(spec['actions'])} actions, {instance.get_duration():.3f}s; no backward clock, speech overlap or missing references.")
