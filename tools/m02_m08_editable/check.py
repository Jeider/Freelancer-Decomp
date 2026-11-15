"""Compare before/after runtime events, entities and actual editable properties."""
import ast
import collections
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent
ASSETS=Path('D:/Games/FL_MOD/Assets')
PL=ASSETS/'Pythonlancer'
OLD=ROOT.parent/'m02_m08_cutscenes/bundle'
sys.path.insert(0,str(PL));os.chdir(PL)
from story import actors
from story.cutscenes import content,scene
from jinja2 import Environment,FileSystemLoader,StrictUndefined
sys.path.insert(0,str(ROOT.parent/'berlin_cutscene'))
import read_source
env=Environment(loader=FileSystemLoader(str(PL/'templates')),undefined=StrictUndefined)
tpl=SimpleNamespace(get_result=lambda path,params:env.get_template(path).render(**params))
scene.DUMPS_PATH=ASSETS/'SCENES/DUMPS'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def parse(text,key):
    read_source.SOURCE=SimpleNamespace(read_text=lambda **kwargs:'duration=1\n'+key+'={'+text+'}')
    return read_source.read()[key]
class Sound:
    def __init__(self,s):
        self.line=SimpleNamespace(index=s['index'],actor=getattr(actors,s['source_actor_class']))
        self.duration=max(s['window'],.1);self.nickname=s['sound']
    def get_nickname(self):return self.nickname
    def get_duration(self,russian):assert russian;return self.duration
def instantiate(folder,name,report):
    load('story.cutscenes.source_extensions',folder/'Pythonlancer/story/cutscenes/source_extensions.py')
    mod=load('editable_check_'+name,folder/'Pythonlancer/story/cutscenes/story_scenes'/f'{name}.py')
    sounds={}
    removed=set()
    if folder.name=='staged':
        removed=set(json.loads((ROOT/'refactor_report.json').read_text())[name]['removed_dialogue'])
    for s in report['dialogue']:
        if s['sound'] in removed:continue
        sounds.setdefault(s['prefix'],{})[s['index']]=Sound(s)
    props={p:SimpleNamespace(get_sounds=lambda v=v:list(v.values()),get_scene_name=lambda:name) for p,v in sounds.items()}
    default=next(iter(props.values()),SimpleNamespace(get_sounds=lambda:[],get_scene_name=lambda:name))
    class Checked(mod.ReconstructedScene):validation_dialogue=props
    return Checked(tpl,default,russian=True)
def events(instance,removed):
    items=[]
    for time,event in instance.events:
        if isinstance(event,content.FacialEvent):continue
        if isinstance(event,content.SoundEvent) and event.sound_name in removed:continue
        items.append(event.get_thorn(time))
    return parse(','.join(items),'events')
def canonical(v):
    if isinstance(v,float):return round(v,5)
    if isinstance(v,list):return [canonical(x) for x in v]
    if isinstance(v,dict):return {k:canonical(x) for k,x in v.items()}
    return v
def entity_data(instance):
    return {e.name:parse(e.get_thorn(),'entities')[0] for e in instance.entities.values()}
def difference(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for k,v in a.items():
            if k not in b:
                # Template id zero is redundant in the native entity constructors.
                if k=='template_id' and v==0:continue
                return path+'.'+k+' missing'
            d=difference(v,b[k],path+'.'+k)
            if d:return d
        return None
    if isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):return path+' length'
        for i,(x,y) in enumerate(zip(a,b)):
            d=difference(x,y,path+f'[{i}]')
            if d:return d
        return None
    if isinstance(a,(float,int)) and isinstance(b,(float,int)) and abs(a-b)<1e-5:return None
    return None if a==b else f'{path}: {a!r} != {b!r}'

summary={};mutation_checks=0
for name,change in json.loads((ROOT/'refactor_report.json').read_text()).items():
    report=json.loads((OLD/name/'report.json').read_text())
    try:
        before=instantiate(ROOT/'before',name,report)
        after=instantiate(ROOT/'staged',name,report)
        ea=events(before,set(change['removed_dialogue']));eb=events(after,set())
        # Order of independent events is kept by the refactor as well.
        if canonical(ea)!=canonical(eb):
            (ROOT/f'diff_{name}.json').write_text(json.dumps({'before':ea,'after':eb},indent=2),encoding='utf-8')
            assert False, 'Event/time/target/parameter changes'
        assert abs(before.get_duration()-after.get_duration())<1e-5, 'Duration changed'
        a=entity_data(before);b=entity_data(after)
        assert a.keys()==b.keys(), 'Entity set changed'
        for key in a:
            if a[key].get('compoundprops',{}).get('floor_height')=='=-110':
                a[key]['compoundprops']['floor_height']=-110
            d=difference(a[key],b[key]);assert not d,(key,d)
        # Real edit regression: constructor-backed attributes must affect serialization.
        for e in after.entities.values():
            if isinstance(e,(content.StaticCamera,content.LookAtCamera)):
                e.fov+=7
                assert parse(e.get_thorn(),'entities')[0]['cameraprops']['fovh']==e.fov
                mutation_checks+=1
            elif isinstance(e,content.Light):
                e.diffuse=[.123,.234,.345]
                assert parse(e.get_thorn(),'entities')[0]['lightprops']['diffuse']==e.diffuse
                mutation_checks+=1
            elif isinstance(e,content.Character):
                e.floor_height=float(e.floor_height)+.25
                assert parse(e.get_thorn(),'entities')[0]['compoundprops']['floor_height']==e.floor_height
                mutation_checks+=1
        summary[name]={'ok':True,'actions':len(eb),'entities':len(b),'commented_lines':len(change['removed_dialogue'])}
    except Exception as exc:
        summary[name]={'error':repr(exc)};print(name,repr(exc))
(ROOT/'check_results.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('Validated',sum(r.get('ok',False) for r in summary.values()),'/',len(summary),'edit checks',mutation_checks)
if any(not r.get('ok') for r in summary.values()):sys.exit(1)
