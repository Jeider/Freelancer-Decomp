"""Produce editable Scene classes and per-source Blender specifications."""
import ast
import collections
import copy
import hashlib
import json
import pprint
import re
from pathlib import Path
from inventory import ROOT, OUT, PL

SCENES = OUT / 'Pythonlancer/story/cutscenes/story_scenes'
SCENES.mkdir(parents=True, exist_ok=True)
SPECS = OUT / 'specs'
SPECS.mkdir(exist_ok=True)
IDENTITY = {'pos':[0,0,0], 'orient':[[1,0,0],[0,1,0],[0,0,1]]}
SMOOTH = {'CLSID':'FreeFormPCurve','points':[[0,0,0,0],[1,1,0,0]]}

def assignments(node):
    return {s.targets[0].id:s.value for s in node.body if isinstance(s,ast.Assign) and isinstance(s.targets[0],ast.Name)}

actor_tree = ast.parse((PL/'story/actors.py').read_text(encoding='utf-8'))
ACTORS = {}
for node in actor_tree.body:
    if isinstance(node,ast.ClassDef):
        a=assignments(node)
        if isinstance(a.get('NAME'),ast.Constant) and a['NAME'].value:
            ACTORS.setdefault(a['NAME'].value.lower(), node.name)
SCRIPT_LINES = {}
SCRIPT_CLASSES = {}
for mission in range(2,9):
    for node in ast.parse((PL/f'story/scripts/main/mission{mission}.py').read_text(encoding='utf-8')).body:
        if not isinstance(node,ast.ClassDef) or not any(isinstance(b,ast.Attribute) and b.attr=='CutsceneProps' for b in node.bases): continue
        a=assignments(node)
        prefix=f'm{mission:02}_'+ast.literal_eval(a['ALIAS'])
        SCRIPT_CLASSES[prefix]=(mission,node.name)
        SCRIPT_LINES[prefix]={ast.literal_eval(n.args[0]):n.args[1].id for n in ast.walk(node)
                              if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='VoiceLine'}
ACTOR_NAMES={node.name:ast.literal_eval(assignments(node)['NAME']) for node in actor_tree.body
             if isinstance(node,ast.ClassDef) and isinstance(assignments(node).get('NAME'),ast.Constant)}
ACTORS['trent']='Trent'
ANIMS = {}
for node in ast.parse((PL/'story/cutscenes/anim.py').read_text(encoding='utf-8')).body:
    if isinstance(node, ast.ClassDef):
        for key, value in assignments(node).items():
            if isinstance(value,ast.Constant) and isinstance(value.value,str):
                ANIMS.setdefault(value.value, f'{node.name}.{key}')

def var(name):
    return 'obj_' + re.sub(r'\W','_',name)

def call(cls, **kwargs):
    return cls+'('+', '.join(f'{k}={v!r}' for k,v in kwargs.items())+')'

def eventcall(cls, **kwargs):
    return cls+'(root=self, group=MAIN, time_delay=t, '+', '.join(f'{k}={v!r}' for k,v in kwargs.items())+')'

def normalize(data):
    for e in data['entities']:
        e['type']={1:'COMPOUND',5:'LIGHT'}.get(e['type'],e['type'])
        if e['type']=='LIGHT':
            p=e['lightprops']; p['type']={1:'L_POINT',2:'L_SPOT',3:'L_DIRECT'}.get(p['type'],p['type'])
            p['on']={1:'Y',0:'N'}.get(p['on'],p['on'])
    return data

def build(name, item):
    data=normalize(json.loads((OUT/name/'source.json').read_text()))
    entities={e['entity_name']:e for e in data['entities']}
    events=data['events']
    report={'name':name,'source':item['source'],'sha256':hashlib.sha256(Path(item['source']).read_bytes()).hexdigest(),
            'uses':item['uses'],'source_duration':data['duration'],'events':[],'dialogue':[],'notes':[]}
    # A voice entry is identified by its referenced sound entity, never by WAV duration.
    speech=[]
    for i,e in enumerate(events):
        if e[1]=='START_SOUND' and re.match(r'DX_m\d',e[2][0],re.I):
            match=re.search(r'_(\d+)_([^_]+)$',e[2][0])
            if not match: raise ValueError(('Voice ID',e))
            prefix=e[2][0][3:match.start()]
            speech.append(dict(id=i,start=e[0],index=int(match[1]),actor=match[2].lower(),sound=e[2][0],prefix=prefix))
    speech.sort(key=lambda x:(x['start'],x['id']))
    unique=[]
    for s in speech:
        previous=next((v for v in unique if (v['start'],v['sound'])==(s['start'],s['sound'])),None)
        if previous is not None:
            previous.setdefault('duplicate_events',[]).append(s['id'])
        else: unique.append(s)
    speech=unique
    action=any(e['type']=='COMPOUND' and e.get('userprops',{}).get('category')=='Spaceship' for e in entities.values())
    # A dialogue in a room can contain a model spaceship prop. Explicit known action scenes.
    action = action and name in {'m04_final','m06_mount','m06_lab_land','m06_lab_launch','m07_tau_arrival','m08_wales_init'} or not speech
    report['clock']='absolute' if action else 'relative'
    aliases={}
    characters={}
    markers=set()
    speaker_alias={'kaitlyn':'kaytlin','guard':'commander','enemy1':'jester','enemy2':'hammer','enemy3':'jester','enemy4':'jester','delta1':'delta','delta3':'prisoner3'}
    overrides={}
    for s in speech:
        desired=speaker_alias.get(s['actor'],s['actor'])
        choices=[n for n,e in entities.items() if e['type']=='DEFORMABLE' and n.lower()=='char_'+desired]
        if s['actor']=='barman':
            choices=[n for n in entities if n.lower() in ('char_barman','char_bartender')]
        if s['actor']=='delta1' and name=='m06_prison_new': choices=['Char_prisoner4']
        nearby=[e[2][0] for e in events if e[1]=='START_MOTION' and e[3].get('animation','').lower().startswith('sc_dx_') and abs(e[0]-s['start'])<=0.5]
        if len(set(nearby))==1 and (not choices or s['actor']=='trent'): choices=list(set(nearby))
        s['character']=choices[0] if len(choices)==1 else None
        cls=SCRIPT_LINES.get(s['prefix'],{}).get(s['index'])
        s['script_actor']=cls
        if cls and ACTOR_NAMES[cls]!=s['actor'] and not (s['actor'] in ('enemy3','enemy4') and cls=='CadizEnemyOne'):
            report['notes'].append(f"Actor mismatch in current script: {s['prefix']} index {s['index']}: source {s['actor']}, current {cls}; source staging retained")
            cls=ACTORS.get(s['actor'])
        if not cls:
            report['notes'].append(f"Legacy dialogue absent in current script: {s['prefix']} index {s['index']}")
            cls=ACTORS.get(s['actor'])
        if s['character'] and cls:
            overrides.setdefault(s['character'],(ACTOR_NAMES[cls],cls))
        s['source_actor_class']=cls
    for n,e in entities.items():
        if e['type']!='DEFORMABLE': continue
        actor=n.lower().removeprefix('char_')
        if actor in ('the_char',): actor=e['template_name'].lower()
        if actor=='trent': actor='trent'
        if n in overrides:
            actor,cls=overrides[n]
            aliases[n]='Char_'+actor
            characters[n]=(actor,cls)
        elif actor in ACTORS:
            canonical='Char_'+actor
            aliases[n]=canonical
            characters[n]=(actor,ACTORS[actor])
        else:
            # Silent extras retain their appearance and engine actor identity.
            characters[n]=(actor,None)
            aliases[n]='Char_'+actor
    # Secondary deformables used solely as a placement reference are markers.
    for n,e in entities.items():
        if e['type']=='DEFORMABLE' and n not in {x[2][0] for x in events if x[1] in ('START_MOTION','START_IK')}:
            target_of_move=any(x[1]=='START_SPATIAL_PROP_ANIM' and len(x[2])==2 and x[2][1]==n for x in events)
            if target_of_move:
                markers.add(n); characters.pop(n,None); aliases.pop(n,None)
    # Merge alternate placements of one actor; their source points remain meshes.
    duplicates={}
    merged_to={}
    for n,(actor,cls) in sorted(list(characters.items()),key=lambda item:item[0]!='Char_'+item[1][0]):
        if cls is None: continue
        if actor in duplicates:
            primary=duplicates[actor]
            markers.add(n)
            characters.pop(n)
            aliases.pop(n,None)
            merged_to[n]=primary
            for s in speech:
                if s['character']==n: s['character']=primary
            report['notes'].append(f'Alternate placement {n} shares actor {primary}')
        else: duplicates[actor]=n
    cameras=[n for n,e in entities.items() if e['type']=='CAMERA' and n.lower()!='cam_dbg']
    looks={}
    for i,e in enumerate(events):
        if e[1]=='ATTACH_ENTITY' and e[2][0] in cameras and e[3].get('flags')=='LOOK_AT' and e[0]==0:
            target=e[2][1]
            if target in entities and entities[target]['type']=='MARKER' and e[3].get('target_type')=='ROOT' and e[3].get('offset',[0,0,0])==[0,0,0]:
                if target not in aliases:
                    aliases[target]=e[2][0]+'_focus'
                    looks[e[2][0]]=i
    def point(n): return aliases.get(n,n)
    def obj(n):
        if n in merged_to: return aliases.get(merged_to[n],merged_to[n])
        if n in markers or entities.get(n,{}).get('type')=='MARKER':
            if n.lower()=='offscreen': return 'offscreen'
            return 'automarker_'+point(n)
        return point(n)
    excluded={n for n in entities if n.lower().startswith('cam_dbg') or n.lower()=='offscreen' or 'subtitle' in n.lower()}
    points={point(n):copy.deepcopy(e.get('spatialprops',IDENTITY)) for n,e in entities.items()
            if n not in excluded and e['type'] not in ('SCENE','MONITOR','SOUND')}
    char_markers=set(point(n) for n in markers)
    for e in events:
        if e[1]=='START_SPATIAL_PROP_ANIM' and len(e[2])==2 and e[2][0] in characters:
            if e[2][1] in points or point(e[2][1]) in points: char_markers.add(point(e[2][1]))
    lines=['"""Editable reconstruction; source and event audit in the accompanying report.json."""',
           'from story.cutscenes.scene import Scene', 'from story.cutscenes.content import *',
           'from story.cutscenes.anim import *','from story.cutscenes.source_extensions import *',
           'from story import actors','','']
    for n,e in entities.items():
        if e['type']=='COMPOUND':
            category=e.get('userprops',{}).get('category','Prop')
            base={'Spaceship':'Ship','Solar':'Solar','Equipment':'Equipment'}.get(category,'Prop')
            lines += [f'class Asset_{var(n)}({base}):',f"    COMPOUND_TEMPLATE_NAME = {e.get('template_name','')!r}",
                      f"    SRT_GRP = {e.get('srt_grp',0)!r}",f"    USR_FLG = {e.get('usr_flg',0)!r}",'','']
        elif n in characters and characters[n][1] is None:
            actor,_=characters[n]
            lines += [f'class Actor_{var(n)}(actors.Actor):',f'    NAME = {actor!r}',
                      f"    TYPE = {'female' if 'female' in e.get('template_name','') else 'male'!r}",
                      f"    CUTSCENE_APPEARANCE = {e['template_name']!r}",
                      f"    GAME_ACTOR = {e.get('userprops',{}).get('Actor',e.get('userprops',{}).get('actor',actor))!r}",'','']
            aliases[n]='Char_'+actor
    ambient=next((e['ambient'] for e in entities.values() if e['type']=='SCENE' and 'ambient' in e),[0,0,0])
    lines += ['class ReconstructedScene(Scene):',f'    DUMP_FILE = {name!r}',f'    SCENE_AMBIENT = {ambient!r}',
              '', '    def action(self):', '        main_group = self.get_group(MAIN)']
    if action: lines.append(f'        self.set_duration({data["duration"]!r})')
    for n,e in entities.items():
        typ=e['type']
        if n in excluded or n in markers or typ in ('SCENE','MONITOR','MARKER'): continue
        if typ=='SOUND' and any(s['sound']==n for s in speech): continue
        init=f'root=self, name={point(n)!r}'
        if typ=='DEFORMABLE':
            actor,cls=characters[n]
            ref='actors.'+cls if cls else 'Actor_'+var(n)
            init=f'root=self, actor={ref}'
            expr=f"Character({init}, light_group={e.get('lt_grp',0)!r}, init_point={point(n)!r}, rotate_from_quat=True, use_ambient={'LIT_AMBIENT' in str(e.get('flags',''))}, floor_height={e.get('compoundprops',{}).get('floor_height',0)!r})"
        elif typ=='CAMERA':
            cp=e['cameraprops']; cls='LookAtCamera' if n in looks else 'StaticCamera'
            extra=f', look_duration={events[looks[n]][3]["duration"]!r}' if n in looks else ''
            expr=f"{cls}({init}, fov={cp['fovh']!r}, farplane={cp['farplane']!r}{extra})"
        elif typ=='COMPOUND':
            expr=f"Asset_{var(n)}({init}, light_group={e.get('lt_grp',0)!r}, init_point={point(n)!r}, rotate_from_quat=True, use_ambient={'LIT_AMBIENT' in str(e.get('flags','')) or e.get('flags')==4})"
        elif typ=='LIGHT':
            p=e['lightprops']
            args=dict(point_name=point(n),extra_name='',light_group=e.get('lt_grp',0),diffuse=p['diffuse'],ambient=p['ambient'],direction=p['direction'],light_type=p['type'],on=p['on']=='Y',range=p['range'],cutoff=p['cutoff'],theta=p['theta'],color=p['color'],attenuation=p['atten'])
            expr='Light('+init+', '+', '.join(f'{k}={v!r}' for k,v in args.items())+')'
        elif typ=='SOUND':
            p=e['audioprops']; cls='SpatialSound' if 'SPATIAL' in str(e.get('flags','')) else 'Sound'
            expr=f"{cls}({init}, sound={e['template_name']!r}, attenuation={p['attenuation']!r}, dmin={p['dmin']!r}, dmax={p['dmax']!r}, priority={e.get('userprops',{}).get('Priority')!r})"
        elif typ=='PSYS':
            expr=f"Alchemy({init}, particles={e['template_name']!r}, point_name={point(n)!r}, sparam={e['psysprops']['sparam']!r})"
        elif typ=='MOTION_PATH':
            path=e['pathprops']['path_data']; assert path.startswith('OPEN,')
            expr=f"MotionPath({init}, point_name={point(n)!r}, path_data={path[5:].strip().rstrip(',')!r})"
        else: raise ValueError(('Entity type',typ,n))
        lines.append('        '+var(n)+' = '+expr)
        # Preserve uncommon authored fields which convenience templates do not expose.
        # Spatial transforms still come from the editable Blender dump.
        source_fields={k:v for k,v in e.items() if k not in ('spatialprops','entity_name','type')}
        lines.append(f'        preserve_entity({var(n)}, {source_fields!r})')
    # Marker userprops are significant for Act_CallThorn main_object bindings.
    for n,e in entities.items():
        if e['type']=='MARKER' and n not in excluded and e.get('userprops'):
            lines.append(f"        preserve_entity(self.get_entity({obj(n)!r}), userprops={e['userprops']!r})")

    speech_ids={i for s in speech for i in [s['id']]+s.get('duplicate_events',[])}
    lip_ids=set()
    for s in speech:
        next_start=min([x['start'] for x in speech if x['start']>s['start']]+[float('inf')])
        clips=[(i,e) for i,e in enumerate(events) if e[1]=='START_MOTION' and e[2][0]==s['character']
               and e[3].get('animation','').lower().startswith('sc_dx_') and s['start']-0.5<=e[0]<next_start-0.5 and i not in lip_ids]
        s['window']=max(e[0]+e[3]['duration'] for i,e in clips)-s['start'] if clips else 0
        if not clips:
            report['notes'].append(f"No source facial allocation: {s['sound']} at {s['start']}s; audio-only cue retained")
        s['lip_events']=[i for i,e in clips]; lip_ids.update(s['lip_events'])
    report['dialogue']=speech
    def emit(i,e):
        time,kind,targets,*rest=e
        p=rest[0] if rest else {}
        original_targets=targets
        targets=[obj(n) for n in targets]
        if kind=='START_SPATIAL_PROP_ANIM' and len(targets)==2 and original_targets[1] in merged_to:
            targets[1]='automarker_'+point(original_targets[1])
        dur=p.get('duration',0)
        smooth=p.get('param_curve')==SMOOTH
        if kind=='SET_CAMERA':
            return eventcall('SetCameraEvent',camera_name=targets[1])
        if kind=='START_MOTION':
            if p.get('animation','').lower().startswith('sc_dx_'):
                report['notes'].append(f'Unvoiced facial event {i} retained with generic facial animation, source duration {dur}')
                return eventcall('MotionEvent',object_name=targets[0],anim='__GENERIC_FACIAL__',duration=dur,start_time=0,time_scale=p.get('time_scale',1),trans_time=p.get('trans_time')).replace("'__GENERIC_FACIAL__'",'Male.GENERIC_ANIM')
            args=dict(object_name=targets[0],anim=p['animation'],duration=dur,time_scale=p.get('time_scale',1),start_time=p.get('start_time',0),loop=p.get('event_flags')==2,trans_time=p.get('trans_time'))
            result=eventcall('MotionEvent',**args)
            if p['animation'] in ANIMS: result=result.replace('anim='+repr(p['animation']),'anim='+ANIMS[p['animation']])
            if 'trans_scale' in p: return eventcall('SourceMotionEvent',targets=targets,**p)
            return result
        if kind=='START_IK':
            return eventcall('NeckIkEvent' if p['end_effector']=='Body_Head' else 'EyeIkEvent',char_name=targets[0],target_name=targets[1],**{k:p[k] for k in ('duration','transition_duration','target_type','target_part','up','front')})
        if kind=='START_SPATIAL_PROP_ANIM':
            sp=p['spatialprops']
            if len(targets)==2 and set(sp)<={'pos','q_orient'} and sp.get('pos',[0,0,0])==[0,0,0] and sp.get('q_orient',[1,0,0,0])==[1,0,0,0]:
                return eventcall('MoveEvent',object_name=targets[0],target_name=targets[1],duration=dur,smooth=smooth,adjust_pos='pos' in sp,adjust_orient='q_orient' in sp)
            if set(sp)=={'axisrot'}:
                return eventcall('RotateAxisEvent',object_name=targets[0],angle=sp['axisrot'][0],axis=sp['axisrot'][1],duration=dur,smooth=smooth)
            return eventcall('SourceSpatialEvent',targets=targets,**p)
        if kind=='ATTACH_ENTITY':
            return eventcall('SourceAttachEvent',targets=targets,**p)
        if kind=='START_PATH_ANIMATION':
            return eventcall('SourcePathEvent',targets=targets,**p)
        if kind=='CONNECT_HARDPOINTS':
            return eventcall('ConnectHardpointEvent',target_name=targets[0],parent_name=targets[1],duration=dur,target_hardpoint=p['hardpoint'],parent_hardpoint=p['parent_hardpoint'])
        if kind=='START_SOUND':
            return eventcall('StartSoundEvent',sound_name=targets[0],duration=dur,start_time=p.get('start_time',0),loop=p.get('flags')=='LOOP')
        if kind=='START_AUDIO_PROP_ANIM':
            return eventcall('AudioAnimEvent',sound_name=targets[0],duration=dur,attenuation=p['audioprops']['attenuation'])
        if kind=='START_PSYS': return eventcall('StartAlchemyEvent',object_name=targets[0],duration=dur)
        if kind=='START_PSYS_PROP_ANIM':
            return eventcall('SourceAlchemyAnimEvent',targets=targets,**p)
        if kind=='START_CAMERA_PROP_ANIM':
            return eventcall('CameraAnimEvent',camera_name=targets[0],duration=dur,fov=p['cameraprops']['fovh'],smooth=smooth)
        if kind=='START_LIGHT_PROP_ANIM':
            args=dict(object_name=targets[0],duration=dur,smooth=smooth)
            for k,v in p['lightprops'].items(): args['lt_range' if k=='range' else k]=(v=='Y') if k=='on' else v
            return eventcall('LightAnimEvent',**args)
        raise ValueError(('Unsupported event',i,e))
    kept=[]
    active_placements={n:n for n in characters}
    for i,e in enumerate(events):
        status='converted'
        if i in speech_ids: status='facial() audio'
        elif i in lip_ids: status='facial() allocation'
        elif any(n in excluded and n.lower()!='offscreen' for n in e[2]): status='debug/subtitle excluded'
        elif i in looks.values(): status='LookAtCamera initialization'
        else: kept.append((i,e,emit(i,e)))
        report['events'].append(dict(index=i,time=e[0],type=e[1],status=status))
    # A second authored deformable of one actor is a placement, not a second NPC.
    # Move to it at the first body/facial cue that changes the active placement.
    for i,e in sorted(enumerate(events),key=lambda x:(x[1][0],x[0])):
        if e[1]!='START_MOTION' or not e[2]: continue
        original=e[2][0]
        primary=merged_to.get(original,original)
        if primary not in characters: continue
        if active_placements[primary]!=original:
            code=eventcall('MoveFastEvent',object_name=obj(primary),target_name='automarker_'+point(original))
            kept.append((i-0.1,[e[0],'PLACEMENT_SWITCH',[original]],code))
            active_placements[primary]=original
            report.setdefault('placement_switches',[]).append(dict(time=e[0],actor=primary,point=point(original)))
    def actions(items,base):
        lines.append('        t = 0')
        cursor=0
        for i,e,code in sorted(items,key=lambda x:(x[1][0],x[0])):
            delay=round(e[0]-base,6)
            if delay!=cursor: lines.append(f'        t += {round(delay-cursor,6)!r}');cursor=delay
            lines.append(f'        # source event {i}, {e[0]:g}s')
            lines.append('        '+code)
    def voice(s,group,append):
        prefix=s['prefix']
        if prefix in SCRIPT_CLASSES:
            mission,cls=SCRIPT_CLASSES[prefix]
            lines.append(f"        select_dialogue(self, {mission}, {cls!r}, {prefix!r})")
        for duplicate in s.get('duplicate_events',[]):
            lines.append(f'        # Duplicate source sound event {duplicate}, same timestamp.')
            lines.append(f'        SoundEvent(root=self, group={group}, sound_name=self.lookup_single_sound({s["index"]}).get_nickname())')
        if s['character'] and s['window']:
            lines.append(f"        self.groups.pop('motion_{s['index']}', None)")
            lines.append(f'        {var(s["character"])}.facial(group={group}, index={s["index"]}, append={append}, auto_lip=True, extra_delay=0)')
        else:
            lines.append(f'        voice_sound = self.lookup_single_sound({s["index"]})')
            lines.append(f'        SoundEvent(root=self, group={group}, sound_name=voice_sound.get_nickname())')
    if action:
        actions(kept,0)
        for s in speech:
            # Absolute-clock facial uses a separate fixed-time group.
            g='voice_'+str(s['id'])
            lines += [f'        self.add_group({g!r}, time={s["start"]!r})']
            voice(s,repr(g),False)
    else:
        entrance=speech[0]['start']; actions([x for x in kept if x[1][0]<entrance],0)
        lines.append(f'        main_group.append_time({entrance!r})')
        for j,s in enumerate(speech):
            start=s['start']; end=speech[j+1]['start'] if j+1<len(speech) else data['duration']
            lip_end=start+s['window']
            selected=[x for x in kept if start<=x[1][0]<end or (j==len(speech)-1 and x[1][0]>=end)]
            lines += ['',f'        # Line {s["index"]}: source {start:g}s; allocated facial window {s["window"]:g}s.']
            actions([x for x in selected if x[1][0]<lip_end], start)
            voice(s,'MAIN',True)
            actions([x for x in selected if x[1][0]>=lip_end],lip_end)
            gap=round(end-lip_end,6)
            lines.append(f'        main_group.append_time({gap!r})')
            s['source_gap']=gap
    lines.append('        restore_dialogue(self)')
    text='\n'.join(lines)+'\n'
    compile(text,name,'exec')
    (SCENES/(name+'.py')).write_text(text,encoding='utf-8')
    spec=dict(name=name,source=item['source'],points=points,cameras=cameras,
              characters=[point(n) for n in characters],character_markers=sorted(char_markers),
              entities=data['entities'],duration=data['duration'])
    (SPECS/(name+'.json')).write_text(json.dumps(spec,indent=2),encoding='utf-8')
    report['entity_names']={n:obj(n) for n in entities}
    report['point_names']={n:point(n) for n in entities}
    (OUT/name/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

def main():
    inv=json.loads((OUT/'inventory.json').read_text())
    results={}
    for name,item in inv['scenes'].items():
        try:
            report=build(name,item)
            results[name]={'ok':True,'dialogue':len(report['dialogue'])}
        except Exception as exc:
            results[name]={'error':repr(exc)}
            print(name,repr(exc))
    (OUT/'build_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('Built',sum('ok' in r for r in results.values()),'/',len(results))

if __name__=='__main__': main()
