"""Read-only audit of IK and marker timing against installed RU voices only."""
import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace
from read_source import ROOT, PYTHONLANCER, read

os.chdir(PYTHONLANCER)
from story.cutscenes import content as c
from story.scripts.main.mission1 import Msn1Bizmark
from story.cutscenes.story_scenes.m01_bizmark import BizmarkScene

source=read()
scene_file=Path(inspect.getfile(BizmarkScene)).resolve()
code=scene_file.read_text(encoding='utf-8').splitlines()
props=Msn1Bizmark(SimpleNamespace(MISSION_INDEX=1))
report=json.loads((ROOT/'report.json').read_text())
original_init=c.Event.__init__


def capture(self,*args,**kwargs):
    frame=inspect.currentframe().f_back
    while frame:
        if Path(frame.f_code.co_filename).resolve()==scene_file:
            self.scene_line=frame.f_lineno
            previous=code[frame.f_lineno-2].strip()
            self.source_id=int(previous.split()[3].rstrip(',')) if previous.startswith('# THN event ') else None
            break
        frame=frame.f_back
    original_init(self,*args,**kwargs)


c.Event.__init__=capture
results={}
try:
    for russian in (True,):
        lang='ru' if russian else 'en'
        durations={s.line.index:s.get_duration(russian) for s in props.get_sounds()}
        scene=BizmarkScene(None,props,russian=russian)
        all_events=sorted(scene.events,key=lambda item:item[0])
        voices=[{'index':int(e.sound_name.split('_')[-2]),'start':t,
                 'duration':durations[int(e.sound_name.split('_')[-2])]} for t,e in all_events if isinstance(e,c.SoundEvent)]
        ik=[(t,e) for t,e in all_events if isinstance(e,c.IkEvent)]
        moves=[(t,e) for t,e in all_events if isinstance(e,c.MoveEvent) and ('_ik' in e.object_name or '_head_' in e.object_name)]
        rows=[]
        for t,e in ik:
            later=[u for u,f in ik if u>t and f.char_name==e.char_name and f.end_effector==e.end_effector]
            effective_end=min(t+e.duration,min(later,default=float('inf')))
            rows.append({'start':t,'end':t+e.duration,'effective_end':effective_end,'char':e.char_name,
                         'effector':e.end_effector,'target':e.target_name,'line':e.scene_line,'source_id':e.source_id})
        uncovered=[]
        for t,e in moves:
            relevant=[r for r in rows if r['target']==e.object_name]
            if not relevant: continue
            covering=[r for r in relevant if r['start']<=t+1e-6 and r['effective_end']>=t+e.duration-1e-6]
            if not covering:
                uncovered.append({'start':t,'end':t+e.duration,'marker':e.object_name,'to':e.target_name,
                                  'source_id':e.source_id,'line':e.scene_line,'bindings':relevant})
        inversions=[]
        for i,(t,e) in enumerate(moves):
            for u,f in moves[i+1:]:
                if f.object_name!=e.object_name or e.source_id is None or f.source_id is None: continue
                a=source['events'][e.source_id][0]; b=source['events'][f.source_id][0]
                if b<a and u>t:
                    inversions.append({'marker':e.object_name,'first':e.source_id,'later':f.source_id,
                                       'source_times':[a,b],'actual_times':[t,u],'lines':[e.scene_line,f.scene_line]})
        spill=[]
        active=[d for d in report['dialogue'] if not d['disabled']]
        for t,e in moves:
            if e.source_id is None: continue
            st=source['events'][e.source_id][0]
            d=next((d for d in active if d['start']<=st<d['end']),None)
            if not d: continue
            vi=next(i for i,v in enumerate(voices) if v['index']==d['index'])
            if vi+1<len(voices) and t>=voices[vi+1]['start']-1e-6:
                spill.append({'source_id':e.source_id,'line':e.scene_line,'from_line':d['index'],
                              'start':t,'next_line':voices[vi+1]['index'],'next_start':voices[vi+1]['start']})
        turns=[{'start':t,'duration':e.duration,'char':e.object_name,'anim':e.anim,'line':e.scene_line,'source_id':e.source_id}
               for t,e in all_events if isinstance(e,c.MotionEvent) and e.source_id in (313,329,333,334)]
        result={'voices':voices,'ik':rows,'uncovered_moves':uncovered,'inversions':inversions,'spill':spill,'turns':turns,'duration':scene.get_duration()}
        results[lang]=result
        print(lang.upper(),'duration',round(scene.get_duration(),3))
        print('VOICES',[(v['index'],round(v['start'],3),round(v['duration'],3)) for v in voices])
        print('IK',[(r['char'],r['effector'],round(r['start'],3),round(r['effective_end'],3),r['line']) for r in rows])
        print('UNCOVERED',[(r['source_id'],round(r['start'],3),round(r['end'],3),r['marker'],r['line']) for r in uncovered])
        print('INVERTED',inversions)
        print('SPILL',spill)
        print('FINAL BODY ACTIONS',turns)
finally:
    c.Event.__init__=original_init
(ROOT/'look_timing_audit.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
