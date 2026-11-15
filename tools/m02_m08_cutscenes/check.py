"""Exercise reconstructed Python, event references and source clocks, RU only."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from inventory import ROOT, OUT, PL
import read_source

os.chdir(PL)
sys.path.insert(0,str(PL))
from story.cutscenes import scene, content
from story import actors
from jinja2 import Environment, FileSystemLoader, StrictUndefined

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

extension=load('story.cutscenes.source_extensions',ROOT/'source_extensions.py')
scene.DUMPS_PATH=OUT/'SCENES/DUMPS'
env=Environment(loader=FileSystemLoader(str(PL/'templates')),undefined=StrictUndefined)
tpl=SimpleNamespace(get_result=lambda path,params:env.get_template(path).render(**params))

class Sound:
    def __init__(self,s):
        cls=s.get('source_actor_class')
        self.line=SimpleNamespace(index=s['index'],actor=getattr(actors,cls) if cls else None)
        self.duration=max(s['window'],0.1)
        self.nickname=s['sound']
    def get_nickname(self): return self.nickname
    def get_duration(self,russian):
        assert russian
        return self.duration

results={}
for file in sorted((OUT/'Pythonlancer/story/cutscenes/story_scenes').glob('*.py')):
    name=file.stem
    report=json.loads((OUT/name/'report.json').read_text())
    try:
        module=load('check_'+name,file)
        sounds={}
        for s in report['dialogue']:
            sound=Sound(s)
            if sound.line.actor is None and s['character']:
                # Source-window validation deliberately includes legacy-only lines;
                # compatibility with the current script is audited separately.
                import re
                text=file.read_text()
                pattern=r'obj_'+re.escape(s['character'])+r' = Character\(root=self, actor=actors\.(\w+)'
                match=re.search(pattern,text)
                if match: sound.line.actor=getattr(actors,match[1])
            sounds.setdefault(s['prefix'],{})[s['index']]=sound
        props={k:SimpleNamespace(get_sounds=lambda d=d:list(d.values()),get_scene_name=lambda:name) for k,d in sounds.items()}
        original=SimpleNamespace(get_sounds=lambda:[],get_scene_name=lambda:name)
        class Checked(module.ReconstructedScene):
            validation_dialogue=props
        instance=Checked(tpl,original,russian=True)
        # Render to memory only: final THN files are the user's single.py step.
        for entity in instance.entities.values(): entity.get_thorn()
        for time,event in instance.events: event.get_thorn(time)
        rendered='duration=1\nentities={}\nevents={'+',\n'.join(event.get_thorn(time) for time,event in instance.events)+'}'
        read_source.SOURCE=SimpleNamespace(read_text=lambda **kwargs:rendered)
        actual=read_source.read()['events']
        source=json.loads((OUT/name/'source.json').read_text())
        # Match each source action at its original time, including target and all
        # authored properties. Defaults introduced by convenience APIs are allowed.
        def subset(expected,found):
            if isinstance(expected,dict):
                return isinstance(found,dict) and all(k in found and subset(v,found[k]) for k,v in expected.items())
            if isinstance(expected,list):
                return isinstance(found,list) and len(expected)==len(found) and all(subset(a,b) for a,b in zip(expected,found))
            if isinstance(expected,(int,float)) and isinstance(found,(int,float)): return abs(expected-found)<1e-5
            return expected==found
        verified=0
        differences=[]
        for audit in report['events']:
            if audit['status']!='converted': continue
            e=source['events'][audit['index']]
            if e[1]=='START_MOTION' and e[3]['animation'].lower().startswith('sc_dx_'): continue
            targets=[report['entity_names'].get(n,n) for n in e[2]]
            if e[1]=='SET_CAMERA': targets[0]='Monitor_1'
            props=e[3] if len(e)>3 else {}
            candidates=[a for a in actual if abs(a[0]-e[0])<1e-5 and a[1]==e[1] and a[2]==targets]
            if not any(subset(props,a[3] if len(a)>3 else {}) for a in candidates):
                differences.append({'event':audit['index'],'source':e,'candidates':candidates})
            else: verified+=1
        valid=set(instance.entities)|{'Monitor_1','offscreen','offscreen_back'}|{s['sound'] for s in report['dialogue']}
        for time,event in instance.events:
            refs=[]
            for field in ('object_name','target_name','parent_name','char_name','camera_name','sound_name'):
                if hasattr(event,field): refs.append(getattr(event,field))
            refs+=getattr(event,'targets',[])
            for ref in refs:
                if ref not in valid:
                    source=json.loads((OUT/name/'source.json').read_text())
                    original_names={e['entity_name'] for e in source['entities']}
                    assert ref not in original_names,(name,type(event).__name__,ref)
                    report.setdefault('source_external_references',[]).append(ref)
        delta=abs(instance.get_duration()-report['source_duration'])
        # Audio-only cues have no facial allocation; their source gaps are literal.
        assert delta<0.11,(name,instance.get_duration(),report['source_duration'])
        results[name]={'ok':True,'events':len(instance.events),'entities':len(instance.entities),'duration':instance.get_duration(),
                       'source_external_references':sorted(set(report.get('source_external_references',[]))),
                       'exact_source_actions':verified,'action_differences':differences}
        if differences: print(name,'action differences',len(differences))
    except Exception as exc:
        results[name]={'error':repr(exc)}
        print(name,repr(exc))
(OUT/'check_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Validated',sum('ok' in x for x in results.values()),'/',len(results))
