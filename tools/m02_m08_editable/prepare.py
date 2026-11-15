"""Refactor installed scenes for hand editing; never regenerate from old THN."""
import ast
import collections
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'m02_m08_cutscenes/bundle'
ASSETS=Path('D:/Games/FL_MOD/Assets')
PL=ASSETS/'Pythonlancer'
STAGE=ROOT/'staged'
BEFORE=ROOT/'before'
sys.path.insert(0,str(PL))
from story import actors
from story.cutscenes import anim

def digest(data):return hashlib.sha256(data).hexdigest()
def read(path):
    relative=path.relative_to(ASSETS)
    data=path.read_bytes()
    backup=BEFORE/relative
    backup.parent.mkdir(parents=True,exist_ok=True)
    if backup.exists():assert backup.read_bytes()==data, f'Live edit since snapshot: {path}'
    else:backup.write_bytes(data)
    return data.decode('utf-8-sig')

scripts={}
for mission in range(2,9):
    tree=ast.parse((PL/f'story/scripts/main/mission{mission}.py').read_text(encoding='utf-8'))
    for c in tree.body:
        if not isinstance(c,ast.ClassDef):continue
        alias=next((s.value.value for s in c.body if isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALIAS' for t in s.targets)),None)
        if not alias:continue
        voices={}
        for n in ast.walk(c):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='VoiceLine':
                ru=next((k.value for k in n.keywords if k.arg=='ru'),None)
                voices[ast.literal_eval(n.args[0])]={'actor':ast.unparse(n.args[1]),'ru':ast.literal_eval(ru) if ru else ''}
        scripts[f'm{mission:02}_{alias}']=voices

def kwargs(c):return {k.arg:k.value for k in c.keywords}
def literal(n,default=None):
    try:return ast.literal_eval(n)
    except (ValueError,TypeError):return default
def rename(name):
    if name.startswith('obj_Char_'):return name[9:].lower()
    if name.startswith('obj_char_'):return name[9:].lower()
    if name.startswith('obj_'):return name[4:]
    if name.startswith('Asset_obj_'):return 'Prop'+''.join(w.capitalize() for w in name[10:].split('_'))
    if name.startswith('Actor_obj_'):return 'Extra'+''.join(w.capitalize() for w in name[10:].split('_'))
    return name

class Rewrite(ast.NodeTransformer):
    def __init__(self,objects):self.objects=objects
    def visit_Name(self,node):
        node.id=rename(node.id);return node
    def visit_Constant(self,node):
        if isinstance(node.value,float) and abs(node.value-round(node.value,6))<1e-10:
            node.value=round(node.value,6)
        return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if not isinstance(node.func,ast.Name):return node
        cls=node.func.id;k=kwargs(node)
        if cls.startswith('Source'):return node
        if cls=='Character' and literal(k.get('floor_height'))=='=-110':
            k['floor_height']=ast.Constant(-110)
        obj=None;method=None
        target=literal(k.get('object_name'))
        if cls=='MotionEvent' and target in self.objects:
            info=self.objects[target]
            if info['type']=='Character':
                a=ast.unparse(k['anim']);gender=info.get('actor')
                # Retain low-level calls for legacy cross-gender animations.
                if gender and not ((gender.is_male() and 'FMBODY' in a.upper()) or (gender.is_female() and 'MLBODY' in a.upper())):
                    obj=info['var'];method='motion';k.pop('object_name')
        elif cls=='SetCameraEvent':
            target=literal(k.get('camera_name'))
            if target in self.objects: obj=self.objects[target]['var'];method='set';k.pop('camera_name')
        elif cls in ('StartSoundEvent','AudioAnimEvent','StartAlchemyEvent','AlchemyAnimEvent'):
            key='sound_name' if 'sound_name' in k else 'object_name'
            target=literal(k.get(key))
            if target in self.objects:
                obj=self.objects[target]['var'];method={'StartSoundEvent':'start','AudioAnimEvent':'change_attenuation','StartAlchemyEvent':'start','AlchemyAnimEvent':'set_sparam'}[cls];k.pop(key)
        if obj:
            k.pop('root',None);node.func=ast.Attribute(ast.Name(obj,ast.Load()),method,ast.Load())
        defaults={'time_scale':1,'start_time':0,'loop':False,'trans_time':None,
                  'adjust_pos':True,'adjust_orient':True,'append':True}
        # adjust_orient defaults differ for attach/path; do not change those.
        for key,default in defaults.items():
            if key.startswith('adjust_') and cls not in ('MoveEvent','MoveFastEvent'):continue
            if key in k and literal(k[key],object())==default: k.pop(key)
        node.keywords=[ast.keyword(arg=key,value=value) for key,value in k.items()]
        return node

def format_statement(node,indent):
    text=ast.unparse(node)
    if len(text)+indent<=125:return [' '*indent+text]
    call=node.value if isinstance(node,(ast.Expr,ast.Assign)) else None
    if not isinstance(call,ast.Call):return [' '*indent+text]
    prefix=(' = '.join(ast.unparse(t) for t in node.targets)+' = ') if isinstance(node,ast.Assign) else ''
    prefix+=ast.unparse(call.func)+'('
    chunks=[ast.unparse(a) for a in call.args]+[f'{k.arg}={ast.unparse(k.value)}' for k in call.keywords]
    lines=[];line=' '*indent+prefix
    for chunk in chunks:
        if len(line)+len(chunk)+2>125 and not line.endswith('('):
            lines.append(line.rstrip());line=' '*(indent+4)
        line+=chunk+', '
    lines.append(line.rstrip(' ,')+')')
    return lines

def prune_fields(fields,typ,call):
    fields=dict(fields)
    # Standard properties are supplied by the constructor, never duplicated.
    for key in ('lt_grp','srt_grp','usr_flg'):
        if fields.get(key)==0:fields.pop(key)
    if typ in ('Character','prop','Light'):fields.pop('lt_grp',None)
    if fields.get('template_id')==0:fields.pop('template_id')
    if fields.get('template_name')=='':fields.pop('template_name')
    if typ in ('Character','prop'):
        flags=fields.get('flags','')
        if isinstance(flags,str):
            remaining=[f for f in flags.split('+') if f not in ('LIT_DYNAMIC','LIT_AMBIENT')]
            if remaining:fields['flags']='+'.join(remaining)
            else:fields.pop('flags',None)
        if typ=='prop': fields.pop('template_name',None)
    if typ in ('StaticCamera','LookAtCamera'):
        p=dict(fields.get('cameraprops',{}))
        for key in ('fovh','farplane'):p.pop(key,None)
        for key,value in [('hvaspect',1.85),('nearplane',.2)]:
            if p.get(key)==value:p.pop(key)
        if p:fields['cameraprops']=p
        else:fields.pop('cameraprops',None)
        if fields.get('flags')=='HIDDEN':fields.pop('flags')
    for table,owned in [('compoundprops',{'floor_height'}),('lightprops',{'on','color','diffuse','ambient','direction','range','cutoff','type','theta','atten'}),('audioprops',{'attenuation','dmin','dmax'}),('psysprops',{'sparam'}),('pathprops',{'path_type','path_data'})]:
        if table in fields:
            p={k:v for k,v in fields[table].items() if k not in owned}
            for key,value in [('specular',[0,0,0]),('pan',0),('ain',360),('aout',360),('atout',0),('rmix',0)]:
                if p.get(key)==value:p.pop(key)
            if p:fields[table]=p
            else:fields.pop(table)
    if typ in ('Sound','SpatialSound','Alchemy'):fields.pop('template_name',None)
    if typ=='SpatialSound' and fields.get('flags')=='SPATIAL':fields.pop('flags')
    return fields

def convert(path,report):
    original=read(path);tree=ast.parse(original)
    objects={};var_types={}
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.targets[0],ast.Name) and isinstance(n.value.func,ast.Name):
            typ=n.value.func.id;k=kwargs(n.value);v=rename(n.targets[0].id)
            actor=None
            if typ=='Character':
                expr=k['actor']
                if isinstance(expr,ast.Attribute):actor=getattr(actors,expr.attr)
                entity=literal(k['init_point'])
            else:entity=literal(k.get('name'))
            if entity:objects[entity]={'var':v,'type':typ,'actor':actor}
            var_types[v]='prop' if typ.startswith('Asset_') else typ
    rewrite=Rewrite(objects)
    name=path.stem
    cls=''.join(part[:1].upper()+part[1:] for part in name.split('_'))+'Scene'
    out=[f'"""{name}: постановка для ручного редактирования.',
         '',f'Точки: SCENES/{name}.blend → DUMPS/{name}.json.',
         'Создание объектов — в начале action(); далее вход, реплики и выход.',
         't — смещение внутри текущего блока; facial()/append_time() двигают часы.' if report['clock']=='relative' else 't — абсолютные секунды исходной сцены; часы MAIN не сдвигаются.',
         'Исходные события и их номера сохранены в отчёте декомпиляции.',
         '"""']
    speech=iter(report['dialogue']);current=None
    prefixes={s['prefix'] for s in report['dialogue']};mixed=len(prefixes)>1
    last_prefix=None;seen_indices=set();removed=[]
    skipdoc=True;opening=False
    for raw in original.splitlines():
        s=raw.strip();indent=len(raw)-len(raw.lstrip())
        if skipdoc and s.startswith('"""'):
            if s.count('"""')==2:skipdoc=False
            else:opening=not opening;skipdoc=opening
            continue
        if skipdoc:continue
        if s.startswith('# source event'):continue
        match=re.match(r'# Line (\d+): source (.*)',s)
        if match:
            current=next(speech)
            assert current['index']==int(match[1])
            v=scripts.get(current['prefix'],{}).get(current['index'])
            out+=['',f"        # Реплика {current['index']} · {current['actor']} · исходное время {current['start']:g} с"]
            if v:
                import textwrap
                out+=['        # '+t for t in textwrap.wrap(v['ru'],width=105)]
                if current.get('source_actor_class')!=v['actor']:
                    out.append(f"        # TODO: в текущем сценарии говорит {v['actor']}; в старой постановке — {current['source_actor_class']}.")
            else:
                out.append('        # УДАЛЕНА ИЗ СЮЖЕТА. Озвучка отключена, движения и камеры оставлены для редактирования.')
                out.append(f"        # Старый звук: {current['sound']}")
                removed.append(current['sound'])
            out.append(f"        # Исходное окно facial: {current['window']:g} с.")
            continue
        if s=='class ReconstructedScene(Scene):':out+=['',f'class {cls}(Scene):'];continue
        if s.startswith('class Asset_obj_') or s.startswith('class Actor_obj_'):
            raw=re.sub(r'(?<=class )\w+',lambda m:rename(m[0]),raw);out.append(raw);continue
        if not s or s.startswith('#') or s.startswith('def ') or s.startswith('class '):out.append(raw);continue
        if s=='from story.cutscenes.source_extensions import *':out.append(raw);continue
        if s.startswith('select_dialogue('):
            call=ast.parse(s).body[0].value;prefix=literal(call.args[3])
            if not mixed or prefix==last_prefix:continue
            last_prefix=prefix
        if s.startswith('restore_dialogue(') and not mixed:continue
        if s.startswith('self.groups.pop('):
            if not current or current['index'] not in seen_indices:continue
        if '.facial(' in s:
            if current:seen_indices.add(current['index'])
            if current and current['index'] not in scripts.get(current['prefix'],{}):
                node=rewrite.visit(ast.parse(s).body[0]);out.append('        # '+ast.unparse(node))
                out.append(f"        main_group.append_time({round(current['window'],6)!r})  # длительность удалённой реплики")
                continue
        if s.startswith('main_group.append_time(-'):
            out.append('        # Перекрытие исходных facial-окон; менять отдельно от паузы после реплики.')
        if "floor_height='=-110'" in s:
            out.append('        # Исправлена опечатка исходного THN: floor_height==-110 → числовое -110.')
        if s=='main_group.append_time(0)':continue
        try:node=ast.parse(s).body[0]
        except SyntaxError:raise RuntimeError(f'Unexpected multiline statement in live source {path}: {s}')
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='preserve_entity':
            c=node.value
            if len(c.args)==2 and isinstance(c.args[0],ast.Name):
                typ=var_types.get(rename(c.args[0].id),'')
                fields=prune_fields(ast.literal_eval(c.args[1]),typ,None)
                c.args=c.args[:1];c.keywords=[ast.keyword(arg=k,value=ast.parse(repr(v),mode='eval').body) for k,v in fields.items()]
        node=rewrite.visit(node)
        out.extend(format_statement(node,indent))
    # Remove unused t resets left after a facial/tail with no actions.
    cleaned=[]
    for i,line in enumerate(out):
        if line.strip()=='t = 0':
            next_line=next((v.strip() for v in out[i+1:] if v.strip() and not v.lstrip().startswith('#')),'')
            if next_line.startswith('main_group.append_time(') or next_line=='restore_dialogue(self)':continue
        cleaned.append(line)
    # One explicit constructor section and one entrance section.
    idx=next(i for i,l in enumerate(cleaned) if 'main_group = self.get_group(MAIN)' in l)
    cleaned.insert(idx+1,'\n        # Объекты: параметры камеры, света, персонажей и реквизита правятся здесь.')
    first=next((i for i,l in enumerate(cleaned) if l.strip()=='t = 0'),None)
    if first is not None:cleaned.insert(first,'\n        # Вход / начальная постановка.' if report['clock']=='relative' else '\n        # Действия по абсолютному времени сцены.')
    cleaned+=['','', '# Совместимость с уже подключёнными THORN_CLASS.',f'ReconstructedScene = {cls}','']
    text='\n'.join(cleaned)
    # Explicit imports, derived from actual AST name usage.
    tree=ast.parse(text);used={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}
    from story.cutscenes import content
    extension_names={'preserve_entity','preserve_spatial','select_dialogue','restore_dialogue','SourceMotionEvent','SourceSpatialEvent','SourcePathEvent','SourceAttachEvent','SourceAlchemyAnimEvent'}
    for mod,allowed in [('content',set(vars(content))-set(vars(anim))),('anim',set(vars(anim))),('source_extensions',extension_names)]:
        names=sorted(used & allowed)
        replacement='from story.cutscenes.'+mod+' import (\n    '+',\n    '.join(names)+',\n)' if names else ''
        text=text.replace('from story.cutscenes.'+mod+' import *',replacement)
    compile(text,str(path),'exec')
    dest=STAGE/path.relative_to(ASSETS);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
    return {'class':cls,'removed_dialogue':removed,'lines_before':len(original.splitlines()),'lines_after':len(text.splitlines())}

def main():
    inventory=json.loads((OLD/'inventory.json').read_text())
    result={}
    for name in inventory['scenes']:
        path=PL/'story/cutscenes/story_scenes'/f'{name}.py'
        result[name]=convert(path,json.loads((OLD/name/'report.json').read_text()))
    extension=PL/'story/cutscenes/source_extensions.py';read(extension)
    shutil.copyfile(ROOT/'source_extensions.py',STAGE/extension.relative_to(ASSETS))
    (ROOT/'refactor_report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Prepared',len(result),'scenes; commented removed dialogue',sum(len(v['removed_dialogue']) for v in result.values()))

if __name__=='__main__':main()
