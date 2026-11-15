"""Generate an editable Bizmark scene, archiving removed dialogue as comments."""
import ast
import hashlib
import json
import re
from read_source import ROOT, PYTHONLANCER, SOURCE, read
from story.cutscenes.old_format import parse_old_motions

data = read()
events = data['events']
entities = {e['entity_name']: e for e in data['entities']}
assert len(parse_old_motions(SOURCE.read_text(encoding='utf-8-sig'))) == sum(e[1] == 'START_MOTION' for e in events)
mission = ast.parse((PYTHONLANCER / 'story/scripts/main/mission1.py').read_text(encoding='utf-8'))
scene_class = next(c for c in mission.body if isinstance(c, ast.ClassDef) and c.name == 'Msn1Bizmark')
active = {n.args[0].value: n.args[1].id for n in ast.walk(scene_class)
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'VoiceLine'}
sounds = sorted((e[0], int(e[2][0].split('_')[-2]), e[2][0].split('_')[-1])
                for e in events if e[1] == 'START_SOUND')
removed = {index for _, index, _ in sounds} - active.keys()
assert removed == {30,40,50,60}, removed
assert {index for _, index, _ in sounds} >= active.keys()
for _, index, actor in sounds:
    if index in active:
        assert active[index].lower() == actor

cameras = [n for n,e in entities.items() if e['type'] == 'CAMERA' and n != 'cam_dbg']
aliases = {}
for cam in cameras:
    for n in entities:
        if n.startswith(cam + '_point'):
            aliases[n] = cam + '_focus' + n[len(cam + '_point'):]
        if n.startswith(cam + '_pos'):
            aliases[n] = cam + n[len(cam + '_pos'):]


def point(name):
    return aliases.get(name, name)


def obj(name):
    if name == 'offscreen':
        return 'automarker_offscreen_point'
    return ('automarker_' if entities[name]['type'] == 'MARKER' else '') + point(name)


spatial = {point(n):e['spatialprops'] for n,e in entities.items()
           if 'spatialprops' in e and e['type'] not in ('SCENE','SOUND')
           and n not in ('offscreen','cam_dbg','cam_dbg_point') and not n.startswith('subtitles')}
character_markers = sorted({point(e[2][1]) for e in events
    if e[1]=='START_SPATIAL_PROP_ANIM' and e[2][0].startswith('Char_') and e[2][1]!='offscreen'})
anim = ast.parse((PYTHONLANCER/'story/cutscenes/anim.py').read_text())
male = next(c for c in anim.body if isinstance(c, ast.ClassDef) and c.name=='Male')
constants = {n.value.value:n.targets[0].id for n in male.body
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value,str)}


def emit(e):
    time, kind, targets, *extra = e
    p = extra[0] if extra else {}
    if kind=='SET_CAMERA':
        return f'{targets[1]}.set(group=MAIN, time_delay=t)'
    if kind=='START_MOTION':
        assert set(p) <= {'animation','duration','time_scale','start_time','trans_time','weight','heading','event_flags'}
        assert p.get('weight',1)==1 and p.get('heading',-1)==-1 and p.get('event_flags',0) in (0,2)
        a = 'Male.'+constants[p['animation']] if p['animation'] in constants else repr(p['animation'])
        args = [f'group=MAIN, anim={a}, duration={p["duration"]}, time_delay=t']
        args += [f'{k}={p[k]!r}' for k in ('time_scale','start_time','trans_time') if k in p]
        if p.get('event_flags')==2:
            args.append('loop=True')
        return f'{targets[0][5:]}.motion(' + ', '.join(args) + ')'
    if kind=='START_SPATIAL_PROP_ANIM':
        assert p['target_type']=='ROOT' and p['target_part']==''
        assert p['spatialprops']=={'pos':[0,0,0],'q_orient':[1,0,0,0]}
        if 'param_curve' in p:
            assert p['param_curve']=={'CLSID':'FreeFormPCurve','points':[[0,0,0,0],[1,1,0,0]]} and p['pcurve_period']==-1000
        return (f'MoveEvent(root=self, group=MAIN, object_name={obj(targets[0])!r}, target_name={obj(targets[1])!r}, '
                f'duration={p["duration"]}, smooth={"param_curve" in p}, time_delay=t)')
    if kind=='START_IK':
        for k,v in {'count_to_root':1,'damping':1,'point_at':1,'move_to':0,'event_flags':128}.items():
            assert p[k]==v
        cls = {'Body_Head':'NeckIkEvent','Eye IK Left':'EyeIkEvent'}[p['end_effector']]
        args = ', '.join(f'{k}={p[k]!r}' for k in ('duration','transition_duration','target_type','target_part','up','front'))
        return f'{cls}(root=self, group=MAIN, char_name={obj(targets[0])!r}, target_name={obj(targets[1])!r}, {args}, time_delay=t)'
    if kind=='CONNECT_HARDPOINTS':
        return (f'ConnectHardpointEvent(root=self, group=MAIN, target_name={targets[0]!r}, parent_name={targets[1]!r}, '
                f'duration={p["duration"]}, target_hardpoint={p["hardpoint"]!r}, parent_hardpoint={p["parent_hardpoint"]!r}, time_delay=t)')
    if kind=='START_PATH_ANIMATION':
        assert p['offset']==[0,0,0] and p['up']=='Y_AXIS' and p['front']=='NEG_Z_AXIS' and p['flags']=='POSITION+ORIENTATION'
        assert p['param_curve']=={'CLSID':'FreeFormPCurve','points':[[0,0,0,0],[1,1,0,0]]}
        return (f'{targets[1]}.anim(group=MAIN, target_name={targets[0]!r}, duration={p["duration"]}, '
                f'start_percent={p["start_percent"]}, stop_percent={p["stop_percent"]}, adjust_orient=True, smooth=True, time_delay=t)')
    if kind=='START_LIGHT_PROP_ANIM':
        assert p['lightprops']=={'on':'Y'}
        return f'LightAnimEvent(root=self, group=MAIN, object_name={targets[0]!r}, duration={p["duration"]}, on=True, time_delay=t)'
    raise ValueError(f'Unsupported event: {e}')


report = {'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'removed_lines':sorted(removed),'events':[],'dialogue':[],'active_event_ids':[],
          'transition_event_ids':[], 'restored_ik':[]}
kept = []
clips = {index:[] for _,index,_ in sounds}
for i,e in enumerate(events):
    t,kind,targets,*extra=e
    p=extra[0] if extra else {}
    if targets[0].startswith('subtitles'):
        status='legacy subtitles omitted'
    elif targets[0]=='cam_dbg':
        status='debug camera omitted'
    elif kind=='ATTACH_ENTITY':
        assert targets[0] in cameras and targets[1]==targets[0]+'_point' and p['flags']=='LOOK_AT'
        status='LookAtCamera binding from initialization (extended for variable voices)'
    elif kind=='START_SOUND':
        status='facial() or commented removed dialogue'
    elif kind=='START_MOTION' and p['animation'].lower().startswith('sc_dx_'):
        actor=targets[0][5:]
        candidates=[s for s in sounds if s[2]==actor and s[0]<=t+0.3]
        assert candidates, e
        index=candidates[-1][1]
        clips[index].append(e)
        status=f'facial() allocated window for line {index}'
    else:
        emit(e)  # Fail immediately on anything we cannot represent.
        kept.append((i,e))
        status='action'
    report['events'].append({'id':i,'time':t,'type':kind,'status':status})

lines=['"""Bizmark reimport. Removed lines 30/40/50/60 are archived as comments.',
       'No negative dialogue delays: each next speaker waits for the previous voice.',
       'Original facial windows and non-dialogue pauses remain documented below.',
       '"""', 'from story.cutscenes.scene import Scene',
       'from story.cutscenes.content import (MAIN, Character, LookAtCamera, MoveEvent,',
       '    NeckIkEvent, EyeIkEvent, Prop, MotionPath, ConnectHardpointEvent, Light, LightAnimEvent)',
       'from story.cutscenes.anim import Male', 'from story import actors', '', '',
       'class Propglass(Prop):', "    COMPOUND_TEMPLATE_NAME = 'glass'", '', '',
       'class BizmarkScene(Scene):', "    DUMP_FILE = 'm01_bizmark'", '    SCENE_AMBIENT = [0, 0, 0]', '',
       '    def action(self):', '        main_group = self.get_group(MAIN)', '']
for cam in cameras:
    lines.append(f'        {cam} = LookAtCamera(root=self, name={cam!r}, fov={entities[cam]["cameraprops"]["fovh"]}, look_duration=1000)')
for name in ('trent','alaric','luc','adelmar'):
    e=entities['Char_'+name]
    lines.append(f"        {name} = Character(root=self, actor=actors.{name.capitalize()}, light_group=0, init_point='Char_{name}', rotate_from_quat=True, use_ambient=True, floor_height={e['compoundprops']['floor_height']})")
for name in ('luc_glass','trent_glass'):
    lines.append(f'        {name} = Propglass(root=self, name={name!r}, init_point={name!r}, light_group=0, rotate_from_quat=True, use_ambient=True)')
for name,e in entities.items():
    if e['type']=='MOTION_PATH':
        path=e['pathprops']['path_data']
        assert path.startswith('OPEN, ')
        lines.append(f'        {name} = MotionPath(root=self, name={name!r}, point_name={name!r}, path_data={path[6:]!r})')
p=entities['additional_light']['lightprops']
assert p['specular']==[0,0,0]
lines.append('        Light(root=self, name="additional_light", point_name="additional_light", extra_name="", light_group=0,')
lines.append(f'              diffuse={p["diffuse"]!r}, ambient={p["ambient"]!r}, direction={p["direction"]!r},')
lines.append(f'              color={p["color"]!r}, attenuation={p["atten"]!r}, light_type={p["type"]!r}, on=False,')
lines.append(f'              range={p["range"]}, cutoff={p["cutoff"]}, theta={p["theta"]})')


def actions(items, base, commented=False):
    prefix='        # ' if commented else '        '
    lines.append(prefix+'t = 0')
    cursor=0
    for i,e in sorted(items,key=lambda item:(item[1][0],item[0])):
        delay=round(e[0]-base,6)
        assert delay>=0
        if delay!=cursor:
            lines.append(prefix+f't += {round(delay-cursor,6):g}')
            cursor=delay
        lines.append(prefix+f'# THN event {i}, source {e[0]:g}s')
        lines.append(prefix+emit(e))
        if not commented:
            report['active_event_ids'].append(i)


lines.extend(['','        # Entrance, source 0..7s.'])
actions([(i,e) for i,e in kept if e[0]<7],0)
lines.append('        main_group.append_time(7)')
for n,(start,index,actor) in enumerate(sounds):
    end=sounds[n+1][0] if n+1<len(sounds) else data['duration']
    disabled=index in removed
    prefix='        # ' if disabled else '        '
    if index==70:
        lines.extend(['','        # Retained setup for line 70, source 45..47s.',
                      '        # Dialogue 60 stays disabled; these placements are required by the next shot.'])
        # Restore only persistent head/eye bindings needed after the removed block.
        latest={}
        for i,e in kept:
            if 15<=e[0]<45 and e[1]=='START_IK' and e[0]+e[3]['duration']>45:
                latest[(e[2][0],e[3]['end_effector'])]=(i,e)
        lines.append('        t = 0')
        for i,e in latest.values():
            restored=[45,e[1],e[2],dict(e[3],duration=e[0]+e[3]['duration']-45)]
            lines.append('        '+emit(restored))
            report['restored_ik'].append({'source_id':i,'event':restored})
        transition=[(i,e) for i,e in kept if 45<=e[0]<47]
        report['transition_event_ids']=[i for i,e in transition]
        actions(transition,45)
        lines.append('        main_group.append_time(2)')
    lines.extend(['',f'        # {"DISABLED — removed from mission script: " if disabled else "Line "}{index}, source {start:g}..{end:g}s.'])
    assert clips[index], index
    lip_end=max(e[0]+e[3]['duration'] for e in clips[index])
    window=lip_end-start
    source_gap=round(end-lip_end,6)
    gap=max(0,source_gap)
    selected=[(i,e) for i,e in kept if start<=e[0]<end]
    # Actions beyond the source facial window follow the actual voice, so pauses
    # and the final exit cannot be shortened by a shorter replacement recording.
    actions([(i,e) for i,e in selected if e[0]<lip_end],start,disabled)
    lines.append(prefix+f'{actor}.facial(group=MAIN, index={index}, auto_lip=True, extra_delay=0)')
    lines.append(prefix+f'# Original facial allocation {window:g}s; source gap {source_gap:g}s.')
    if source_gap<0:
        lines.append(prefix+'# Source overlap omitted: wait until the current voice finishes.')
    tail=[(i,e) for i,e in selected if e[0]>=lip_end]
    if tail:
        actions(tail,lip_end,disabled)
    if gap:
        lines.append(prefix+f'main_group.append_time({gap:g})')
    report['dialogue'].append({'index':index,'actor':actor,'start':start,'end':end,'window':window,
                               'source_gap':source_gap,'gap':gap,'disabled':disabled})

text='\n'.join(lines)+'\n'
compile(text,'m01_bizmark.py','exec')
(ROOT/'m01_bizmark.py').write_text(text,encoding='utf-8')
(ROOT/'blender_spec.json').write_text(json.dumps({'points':spatial,'cameras':cameras,'character_markers':character_markers},indent=2),encoding='utf-8')
(ROOT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f'{len(events)} source events accounted for; {len(active)} active lines; {sorted(removed)} commented out.')
print(f'{len(report["active_event_ids"])} active actions; {len(spatial)} Blender points; no room mesh available.')
