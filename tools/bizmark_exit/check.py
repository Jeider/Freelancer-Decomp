import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

ROOT=Path(__file__).resolve().parent
PL=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0,str(PL));os.chdir(PL)
manifest=json.loads((ROOT/'manifest.json').read_text())
installed='--installed' in sys.argv
def load(name,path):
    module=ModuleType(name);sys.modules[name]=module
    exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
    return module
helper=load('story.cutscenes.ru_dialogue_timing',Path(manifest['ru_dialogue_timing.py']['target']) if installed else ROOT/'ru_dialogue_timing.py')
old=load('exit_before',ROOT/'m01_bizmark.py.before')
new=load('exit_after',Path(manifest['m01_bizmark.py']['target']) if installed else ROOT/'m01_bizmark.py')
from story.scripts.main.mission1 import Msn1Bizmark
from story.cutscenes import content as c
from audio.sound import CutsceneSound
original_duration=CutsceneSound.get_duration
def ru_only(self,russian=True):
    assert russian is True
    return original_duration(self,True)
CutsceneSound.get_duration=ru_only
props=Msn1Bizmark(SimpleNamespace(MISSION_INDEX=1))
a=old.BizmarkScene(None,props,russian=True)
b=new.BizmarkScene(None,props,russian=True)
def norm(v):
    if isinstance(v,c.Point): return (v.name,v.position,v.orientation)
    if isinstance(v,c.Entity): return (v.name,norm(v.get_params()))
    if isinstance(v,dict): return {k:norm(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [norm(x) for x in v]
    return v
def snapshot(scene):
    return [(t,type(e).__name__,norm(e.get_params())) for t,e in scene.events]
assert snapshot(a)==snapshot(b) and a.get_duration()==b.get_duration()
print('PASS RU: all current events and scene duration unchanged.')

# Pure timing stress case: substitute a synthetic interval after RU choreography.
# No other-language audio is read or scene validation performed.
build=helper.RuDialogueTiming.build
def synthetic(self,choreography):
    def prepare():
        choreography()
        start,duration,_=self.spans[-1]
        self.spans[-1]=(start,duration,0.2)
    return build(self,prepare)
helper.RuDialogueTiming.build=synthetic
adapted=new.BizmarkScene(None,props,russian=True)
def exit_events(scene):
    return [(t,e) for t,e in scene.events if isinstance(e,c.MotionEvent) and e.object_name=='Char_alaric'
            and e.anim in ('Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02','Sc_MLBODY_WLKG_000LV_XA_01')]
reference=exit_events(b);changed=exit_events(adapted)
assert len(reference)==len(changed)==2
assert abs(changed[1][0]-changed[0][0]-1)<1e-8
for (_,r),(_,e) in zip(reference,changed):
    assert (r.duration,r.time_scale,r.trans_time)==(e.duration,e.time_scale,e.trans_time)
assert adapted.get_duration()>=changed[0][0]+4
print('PASS synthetic interval: turn/walk keep speed, duration, transitions and 1s separation; final shot lasts at least 4s.')
print('No EN audio or final THN generation.')
