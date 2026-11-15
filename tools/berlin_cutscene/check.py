"""Validate event semantics and relative clocks without generating final THN."""
import importlib.util
import json
import os
import sys
from types import SimpleNamespace

from read_source import ROOT, PYTHONLANCER, read

os.chdir(PYTHONLANCER)
from story import actors
from story.cutscenes import scene, content

installed = '--installed' in sys.argv
scene.DUMPS_PATH = PYTHONLANCER.parent / 'SCENES/DUMPS' if installed else ROOT
module_path = PYTHONLANCER / 'story/cutscenes/story_scenes/m01_berlin.py' if installed else ROOT / 'm01_berlin.py'
spec = importlib.util.spec_from_file_location('berlin_check_scene', module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
data = read()
report = json.loads((ROOT / 'report.json').read_text())
lines = report['dialogue']


class Sound:
    def __init__(self, line, duration):
        self.line = SimpleNamespace(index=line['index'], actor=getattr(actors, line['actor'].capitalize()))
        self.duration = duration
        self.nickname = f"DX_m01_berlin_{line['index']:04}_{line['actor']}"

    def get_duration(self, russian):
        return self.duration

    def get_nickname(self):
        return self.nickname


def make(durations):
    sounds = [Sound(line, duration) for line, duration in zip(lines, durations)]
    props = SimpleNamespace(get_sounds=lambda: sounds, get_scene_name=lambda: 'm01_berlin')
    return module.BerlinScene(None, props)


instance = make([line['window'] for line in lines])
assert abs(instance.get_duration() - (data['duration'] + 2)) < 1e-6
assert instance.SCENE_AMBIENT == [0, 0, 0]
aliases = {}
for camera in ('cam_entry', 'cam_stand', 'cam_adelmar', 'cam_trent', 'cam_luc'):
    aliases.update({camera + '_point': camera + '_focus', camera + '_point2': camera + '_focus2', camera + '_pos2': camera + '2'})
types = {e['entity_name']: e['type'] for e in data['entities']}


def object_name(name):
    return ('automarker_' if types[name] == 'MARKER' else '') + aliases.get(name, name)


def signature(time, kind, targets, props):
    return (round(time, 6), kind, targets, props)


expected = []
for time, kind, targets, *extra in data['events']:
    # Requested staging correction: Luc's final block follows Trent's full line.
    if time >= 22:
        time += 2
    p = extra[0] if extra else {}
    if kind == 'ATTACH_ENTITY':
        if targets[0] == 'cam_dbg':
            continue
        expected.append(signature(time, kind, [targets[0], object_name(targets[1])], p['duration']))
    elif kind == 'START_MOTION':
        if p['animation'].lower().startswith('sc_dx_'):
            continue
        expected.append(signature(time, kind, targets, [p['animation'], p['duration'], p.get('start_time',0),
                                                       p.get('time_scale',1), p.get('trans_time'), p.get('event_flags',0)==2]))
    elif kind == 'START_SPATIAL_PROP_ANIM':
        expected.append(signature(time, kind, list(map(object_name, targets)), [p['duration'], 'param_curve' in p, True, True]))
    elif kind == 'START_IK':
        expected.append(signature(time, kind, list(map(object_name, targets)),
            [p[k] for k in ('duration','end_effector','transition_duration','target_part','target_type','up','front')]))
    elif kind == 'START_SOUND':
        expected.append(signature(time, kind, targets, None))
    elif kind == 'SET_CAMERA':
        expected.append(signature(time, kind, targets[1:], None))
    else:
        raise AssertionError(kind)

actual = []
for time, event in instance.events:
    # Resolve every reference, including generated character IK markers.
    for attr in ('object_name', 'target_name', 'char_name', 'camera_name'):
        name = getattr(event, attr, None)
        if name is not None:
            assert name in instance.entities, (type(event).__name__, attr, name)
    event.get_params()
    if isinstance(event, content.FacialEvent):
        continue
    if isinstance(event, content.LookAtEvent):
        item = signature(time, 'ATTACH_ENTITY', [event.point.name, event.focus.name], event.duration)
    elif isinstance(event, content.MotionEvent):
        item = signature(time, 'START_MOTION', [event.object_name],
                         [event.anim,event.duration,event.start_time,event.time_scale,event.trans_time,event.loop])
    elif isinstance(event, content.MoveEvent):
        item = signature(time, 'START_SPATIAL_PROP_ANIM', [event.object_name,event.target_name],
                         [event.duration,event.smooth,event.adjust_pos,event.adjust_orient])
    elif isinstance(event, content.IkEvent):
        item = signature(time, 'START_IK', [event.char_name,event.target_name],
                         [event.duration,event.end_effector,event.transition_duration,event.target_part,event.target_type,event.up,event.front])
    elif isinstance(event, content.SoundEvent):
        item = signature(time, 'START_SOUND', [event.sound_name], None)
    elif isinstance(event, content.SetCameraEvent):
        item = signature(time, 'SET_CAMERA', [event.camera_name], None)
    else:
        raise AssertionError(type(event))
    actual.append(item)
assert sorted(expected, key=repr) == sorted(actual, key=repr), (set(map(repr,expected))-set(map(repr,actual)), set(map(repr,actual))-set(map(repr,expected)))

# Different voice durations must shift following dialogue while preserving gaps.
durations = [8, 7, 5, 7]
retimed = make(durations)
clock = 5.5
expected_starts = []
for duration, line in zip(durations, lines):
    expected_starts.append(clock)
    clock += duration + line['gap']
actual_starts = [time for time, e in retimed.events if isinstance(e, content.SoundEvent)]
assert actual_starts == expected_starts, (actual_starts, expected_starts)
assert abs(retimed.get_duration() - clock) < 1e-6
trent_end = actual_starts[2] + durations[2]
assert actual_starts[3] == trent_end
luc_gestures = [time for time, e in retimed.events if isinstance(e, content.MotionEvent)
                and e.object_name == 'Char_luc' and 'SHRG_SHLDRS' in e.anim]
assert luc_gestures == [trent_end], luc_gestures
print(f'PASS: {len(actual)} source-equivalent actions/bindings/audio events; all references resolve.')
print('PASS: Luc waits for Trent; corrected timing 29.5s with source-length voices; variable voice timing verified.')
print('No final THN was generated or installed.')
