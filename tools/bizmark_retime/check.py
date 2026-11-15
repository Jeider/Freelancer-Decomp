"""RU-only scene regression plus language-independent time-map invariants."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent
PYTHONLANCER=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0,str(PYTHONLANCER))
os.chdir(PYTHONLANCER)
meta=json.loads((ROOT/'baseline.json').read_text())


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


installed='--installed' in sys.argv
helper=load('story.cutscenes.ru_dialogue_timing',PYTHONLANCER/'story/cutscenes/ru_dialogue_timing.py' if installed else ROOT/'ru_dialogue_timing.py')
baseline=load('bizmark_ru_baseline',Path(meta['backup']))
upgrade=load('bizmark_ru_upgrade',Path(meta['target']) if installed else ROOT/'m01_bizmark.py')
from story.scripts.main.mission1 import Msn1Bizmark
from story.cutscenes import content as c
from audio.sound import CutsceneSound

# Enforce that every real audio access in this verification is RU.
read_duration=CutsceneSound.get_duration
def ru_only(self,russian=True):
    assert russian is True, 'Only RU audio is permitted in validation'
    return read_duration(self,True)
CutsceneSound.get_duration=ru_only
props=Msn1Bizmark(SimpleNamespace(MISSION_INDEX=1))
before=baseline.BizmarkScene(None,props,russian=True)
after=upgrade.BizmarkScene(None,props,russian=True)


def normalize(value):
    if isinstance(value,c.Point):
        return {'point':value.name,'position':value.position,'orientation':value.orientation,'rotate':value.rotate}
    if isinstance(value,c.Entity):
        return {'entity':value.name,'params':normalize(value.get_params())}
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [normalize(v) for v in value]
    return value


def snapshot(scene):
    return {'duration':scene.get_duration(),'start_time':scene.start_time,
            'events':[(time,type(e).__name__,normalize(e.get_params())) for time,e in scene.events],
            'entities':{name:normalize(e.get_params()) for name,e in scene.entities.items()},
            'groups':{name:g.time for name,g in scene.groups.items()}}


assert snapshot(before)==snapshot(after), 'RU choreography changed'
assert before.get_duration()==after.get_duration()
print(f'PASS RU: all {len(after.events)} events, {len(after.entities)} entities, group clocks and duration match the current backup exactly.')

# Pure algorithm tests use synthetic interval lengths, not EN files or an EN
# scene. A single increasing function must preserve every RU event ordering.
voices=[(t,e) for t,e in before.events if isinstance(e,c.SoundEvent)]
sounds={s.get_nickname():s for s in props.get_sounds()}
spans=[(t,sounds[e.sound_name].get_duration(True)) for t,e in voices]
for factor in (0.5,1.7):
    root=SimpleNamespace(events=[],groups={},duration=before.get_duration(),start_time=0)
    mapper=helper.RuDialogueTiming(root)
    mapper.spans=[(t,d,d*(factor if i%2 else 1/factor)) for i,(t,d) in enumerate(spans)]
    samples={0,before.get_duration()}
    for start,e in before.events:
        if isinstance(e,(c.FacialEvent,c.SoundEvent)): continue
        root.events.append((start,copy.copy(e)))
        samples.add(start)
        duration=getattr(e,'duration',0)
        if isinstance(duration,(int,float)) and duration>0: samples.add(start+duration)
    ordered=sorted(samples)
    transformed=[mapper.map_time(t) for t in ordered]
    assert all(b>a for a,b in zip(transformed,transformed[1:])), 'Event ordering reversed'
    for i,(start,ref,actual) in enumerate(mapper.spans):
        assert abs(mapper.map_time(start+ref)-mapper.map_time(start)-actual)<1e-8
        if i+1<len(mapper.spans):
            following=mapper.spans[i+1][0]
            assert abs((mapper.map_time(following)-mapper.map_time(start+ref))-(following-start-ref))<1e-8
    originals=list(root.events)
    original_durations=[getattr(e,'duration',None) for _,e in originals]
    original_scales=[getattr(e,'time_scale',None) for _,e in originals]
    mapper.build(lambda:None)
    for i,((start,_),(mapped_start,e)) in enumerate(zip(originals,root.events)):
        assert mapped_start==mapper.map_time(start)
        duration=original_durations[i]
        if isinstance(duration,(int,float)) and duration>0:
            assert abs(mapped_start+e.duration-mapper.map_time(start+duration))<1e-8
            if isinstance(e,(c.MotionEvent,c.CompoundAnim)):
                assert abs(e.time_scale*e.duration-original_scales[i]*duration)<1e-8
    assert root.duration==mapper.map_time(before.get_duration())
print('PASS algorithm: synthetic compression/expansion preserves event order, endpoints, animation progress and all non-dialogue pauses.')

# Generated lipsync offsets belong to actual audio and must not be scaled twice.
root=SimpleNamespace(events=[],groups={},duration=None,start_time=0)
mapper=helper.RuDialogueTiming(root)
mapper.spans=[(1,4,2),(6,4,8)]
voice=SimpleNamespace(duration=3)
root.events=[(6.75,voice)]
mapper.voice_events[id(voice)]=(6,0.75)
mapper.build(lambda:None)
assert root.events[0][0]==4.75 and voice.duration==3
print('PASS algorithm: lipsync offsets and durations remain tied to generated audio, without double scaling.')
print('No EN audio read; no final THN generated or synced.')
