"""Check generated scene without building or syncing final THN."""
import ast
import importlib.util
import json
import os
import sys
from types import SimpleNamespace
from read_source import ROOT, PYTHONLANCER, read

os.chdir(PYTHONLANCER)
installed='--installed' in sys.argv


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


if not installed:
    load('story.cutscenes.content',ROOT/'content.py')
from story.cutscenes import content as c, scene
from story import actors
scene.DUMPS_PATH=PYTHONLANCER.parent/'SCENES/DUMPS' if installed else ROOT
module=load('bizmark_check_scene',PYTHONLANCER/'story/cutscenes/story_scenes/m01_bizmark.py' if installed else ROOT/'m01_bizmark.py')
report=json.loads((ROOT/'report.json').read_text())
data=read()
entities={e['entity_name']:e for e in data['entities']}
dialogue=[d for d in report['dialogue'] if not d['disabled']]
aliases={}
for name,e in entities.items():
    if e['type']=='CAMERA' and name!='cam_dbg':
        for n in entities:
            if n.startswith(name+'_point'):
                aliases[n]=name+'_focus'+n[len(name+'_point'):]
            if n.startswith(name+'_pos'):
                aliases[n]=name+n[len(name+'_pos'):]


def obj(name):
    if name=='offscreen': return 'automarker_offscreen_point'
    return ('automarker_' if entities[name]['type']=='MARKER' else '')+aliases.get(name,name)


class Sound:
    def __init__(self,line,duration):
        self.line=SimpleNamespace(index=line['index'],actor=getattr(actors,line['actor'].capitalize()))
        self.duration=duration
        self.nickname=f"DX_m01_bizmark_{line['index']:04}_{line['actor']}"
    def get_duration(self,russian): return self.duration
    def get_nickname(self): return self.nickname


def source_signature(time,event):
    _,kind,targets,*rest=event
    p=rest[0] if rest else {}
    names=list(map(obj,targets))
    if kind=='START_MOTION':
        value=[p['animation'],p['duration'],p.get('start_time',0),p.get('time_scale',1),p.get('trans_time'),p.get('event_flags',0)==2]
    elif kind=='SET_CAMERA':
        names=names[1:]; value=None
    elif kind=='START_IK':
        value=[p[k] for k in ('duration','end_effector','transition_duration','target_part','target_type','up','front')]
    elif kind=='START_SPATIAL_PROP_ANIM':
        value=[p['duration'],'param_curve' in p,True,True]
    elif kind=='CONNECT_HARDPOINTS':
        value=[p['duration'],p['hardpoint'],p['parent_hardpoint']]
    elif kind=='START_PATH_ANIMATION':
        value=[p['duration'],p['start_percent'],p['stop_percent'],True,True,True]
    elif kind=='START_LIGHT_PROP_ANIM':
        value=[p['duration'],True]
    else: raise AssertionError(kind)
    return round(time,6),kind,names,value


def event_signature(time,e):
    if isinstance(e,(c.FacialEvent,c.LookAtEvent,c.SoundEvent)): return None
    if isinstance(e,c.MotionEvent):
        kind='START_MOTION'; names=[e.object_name]
        value=[e.anim,e.duration,e.start_time,e.time_scale,e.trans_time,e.loop]
    elif isinstance(e,c.SetCameraEvent):
        kind='SET_CAMERA'; names=[e.camera_name]; value=None
    elif isinstance(e,c.IkEvent):
        kind='START_IK'; names=[e.char_name,e.target_name]
        value=[e.duration,e.end_effector,e.transition_duration,e.target_part,e.target_type,e.up,e.front]
    elif isinstance(e,c.MoveEvent):
        kind='START_SPATIAL_PROP_ANIM'; names=[e.object_name,e.target_name]
        value=[e.duration,e.smooth,e.adjust_pos,e.adjust_orient]
    elif isinstance(e,c.ConnectHardpointEvent):
        kind='CONNECT_HARDPOINTS'; names=[e.target_name,e.parent_name]
        value=[e.duration,e.target_hardpoint,e.parent_hardpoint]
    elif isinstance(e,c.PathAnimationEvent):
        kind='START_PATH_ANIMATION'; names=[e.target_name,e.path.name]
        value=[e.duration,e.start_percent,e.stop_percent,e.smooth,e.adjust_pos,e.adjust_orient]
    elif isinstance(e,c.LightAnimEvent):
        kind='START_LIGHT_PROP_ANIM'; names=[e.object_name]; value=[e.duration,e.on]
    else: raise AssertionError(type(e))
    return round(time,6),kind,names,value


def verify(durations):
    sounds=[Sound(d,durations[d['index']]) for d in dialogue]
    props=SimpleNamespace(get_sounds=lambda:sounds,get_scene_name=lambda:'m01_bizmark')
    instance=module.BizmarkScene(None,props)
    expected=[]
    for i in report['active_event_ids']:
        e=data['events'][i]
        if e[0]<7: expected.append(source_signature(e[0],e))
    clock=7
    starts=[]
    transition=set(report['transition_event_ids'])
    for d in dialogue:
        if d['index']==70:
            for restored in report['restored_ik']:
                expected.append(source_signature(clock,restored['event']))
            for i in transition:
                e=data['events'][i]
                expected.append(source_signature(clock+e[0]-45,e))
            clock+=2
        duration=durations[d['index']]
        starts.append(clock)
        for i in report['active_event_ids']:
            if i in transition: continue
            e=data['events'][i]
            if d['start']<=e[0]<d['end']:
                offset=e[0]-d['start']
                when=clock+offset if offset<d['window'] else clock+duration+offset-d['window']
                expected.append(source_signature(when,e))
        clock+=duration+d['gap']
    actual=[]
    for time,e in instance.events:
        for attr in ('object_name','target_name','char_name','camera_name','parent_name'):
            name=getattr(e,attr,None)
            if name is not None: assert name in instance.entities,(type(e),attr,name)
        e.get_params()
        item=event_signature(time,e)
        if item: actual.append(item)
    assert sorted(expected,key=repr)==sorted(actual,key=repr), (set(map(repr,expected))-set(map(repr,actual)),set(map(repr,actual))-set(map(repr,expected)))
    audio=[(t,e.sound_name) for t,e in instance.events if isinstance(e,c.SoundEvent)]
    assert [round(t,6) for t,_ in audio]==[round(t,6) for t in starts]
    assert [int(n.split('_')[-2]) for _,n in audio]==[d['index'] for d in dialogue]
    for i in range(len(audio)-1):
        assert audio[i+1][0]+1e-6 >= audio[i][0]+durations[dialogue[i]['index']]
    assert abs(instance.get_duration()-clock)<1e-6
    for entity in instance.entities.values(): entity.get_params()
    print(f'PASS: {len(actual)} actions including restored IK, {len(audio)} active voices, duration {clock:.4f}s; all references resolve.')
    return instance


original=verify({d['index']:d['window'] for d in dialogue})
verify({d['index']:1.5+(i%4)*2 for i,d in enumerate(dialogue)})
assert original.SCENE_AMBIENT==[0,0,0]
light=original.entities['additional_light']
assert light.color==[214,187,133] and light.attenuation==[0.8999999762,0,0.0060000001]
path_event=next(e for t,e in original.events if isinstance(e,c.PathAnimationEvent))
assert path_event.stop_percent==0.5

# Test the two extended templates in isolation, without building any cutscene THN.
from jinja2 import Template
def template(name,relative):
    return Template((PYTHONLANCER/relative if installed else ROOT/name).read_text())
assert 'stop_percent=0.5' in template('path_anim.lua','templates/cutscenes/event/path_anim.lua').render(**path_event.get_params())
assert '214, 187, 133' in template('light.lua','templates/cutscenes/entity/light.lua').render(**light.get_params())
default_light=c.Light(root=original,name='test_default_light',light_group=0,diffuse=[1,1,1],ambient=[0,0,0],direction=[0,0,1])
assert default_light.color==[255,255,255] and default_light.attenuation==[1,0,0.003]
default_path=c.PathAnimationEvent(root=original,target_name='cam_entry',path=original.entities['Path_cam_entry'],duration=1)
assert default_path.start_percent==0 and default_path.stop_percent==1
text=(PYTHONLANCER/'story/cutscenes/story_scenes/m01_bizmark.py' if installed else ROOT/'m01_bizmark.py').read_text(encoding='utf-8')
tree=ast.parse(text)
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='facial']
indices=[next(k.value.value for k in n.keywords if k.arg=='index') for n in calls]
assert indices==[d['index'] for d in dialogue]
for index in (30,40,50,60):
    assert f'DISABLED — removed from mission script: {index}' in text
    assert f'# {"luc" if index in (30,40) else "alaric" if index==50 else "trent"}.facial(group=MAIN, index={index}' in text
print('PASS: removed dialogue blocks are comments; no voice overlaps; half-path and original light preserved; API defaults unchanged.')
print('No final THN generated or synced.')
