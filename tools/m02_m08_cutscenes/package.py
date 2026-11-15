"""Assemble mission bindings, source audits and the reviewable delivery archive."""
import ast
import collections
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile
from inventory import OUT, ROOT, PL
sys.path.insert(0,str(ROOT))
from build import SCRIPT_CLASSES, SCRIPT_LINES, ACTOR_NAMES

source_root=OUT/'Pythonlancer'
shutil.copyfile(ROOT/'source_extensions.py',source_root/'story/cutscenes/source_extensions.py')
scripts=source_root/'story/scripts/main'
scripts.mkdir(parents=True,exist_ok=True)
inv=json.loads((OUT/'inventory.json').read_text())
reports={n:json.loads((OUT/n/'report.json').read_text()) for n in inv['scenes']}
bindings={}
for name,report in reports.items():
    prefixes=list(dict.fromkeys(s['prefix'] for s in report['dialogue']))
    if not prefixes: continue
    # m07_offer is deliberately one source scene with two script segments.
    prefix=prefixes[-1]
    if prefix not in SCRIPT_CLASSES: continue
    role='THORN_ACCEPT_CLASS' if any(u['role']=='accept' for u in report['uses']) else 'THORN_CLASS'
    slots=bindings.setdefault(prefix,{})
    if slots.get(role)!=prefix or name==prefix:
        slots[role]=name
for prefix,roles in bindings.items():
    main=roles.get('THORN_CLASS')
    if main:
        decision=main.removesuffix('_offer')+'_offer_decision' if main.endswith('_offer') else main+'_decision'
        if decision in reports: roles['THORN_DECISION_CLASS']=decision
        # m02 offer has an additional "bar" component in the source name.
        if main+'_decision' in reports: roles['THORN_DECISION_CLASS']=main+'_decision'
    if main=='m02_bship_bar_offer': roles['THORN_DECISION_CLASS']='m02_bship_bar_decision'

for mission in range(2,9):
    path=PL/f'story/scripts/main/mission{mission}.py'
    original=path.read_text(encoding='utf-8')
    lines=original.splitlines(keepends=True)
    tree=ast.parse(original)
    additions=[]
    modules=set()
    for node in tree.body:
        if not isinstance(node,ast.ClassDef): continue
        prefix=next((p for p,c in SCRIPT_CLASSES.items() if c==(mission,node.name)),None)
        if prefix not in bindings: continue
        assignments={t.id for s in node.body if isinstance(s,ast.Assign) for t in s.targets if isinstance(t,ast.Name)}
        # Existing authored scenes, including both m08 classes, are untouched.
        if 'THORN_CLASS' in assignments: continue
        block=[]
        for role,mod in bindings[prefix].items():
            block.append(f'    {role} = {mod}.ReconstructedScene\n')
            modules.add(mod)
        additions.append((node.lineno,''.join(block)))
    for lineno,block in sorted(additions,reverse=True): lines.insert(lineno,block)
    output='from story.cutscenes.story_scenes import '+', '.join(sorted(modules))+'\n'+''.join(lines)
    compile(output,str(path),'exec')
    # Verify all original voice line ASTs remain exactly as authored.
    original_voices=[ast.dump(n) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='VoiceLine']
    updated_voices=[ast.dump(n) for n in ast.walk(ast.parse(output)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='VoiceLine']
    assert original_voices==updated_voices
    (scripts/path.name).write_text(output,encoding='utf-8')

registry=['"""All mission-referenced scenes, including action/camera-only THNs."""','SCENES = {']
for name,item in sorted(inv['scenes'].items()):
    registry.append(f"    {name!r}: {{'module': 'story.cutscenes.story_scenes.{name}', 'class': 'ReconstructedScene', 'uses': {item['uses']!r}}},")
registry.append('}')
(source_root/'story/cutscenes/reconstructed_m02_m08.py').write_text('\n'.join(registry)+'\n',encoding='utf-8')

compatibility={}
for name,report in reports.items():
    missing=[];mismatched=[]
    for s in report['dialogue']:
        if not s['script_actor']: missing.append({'source':s['sound'],'index':s['index']})
        elif s.get('source_actor_class')!=s['script_actor']:
            mismatched.append({'source':s['sound'],'source_actor':s.get('source_actor_class'),'script_actor':s['script_actor']})
    compatibility[name]={'missing_current_lines':missing,'actor_mismatches':mismatched,'notes':report['notes']}
(OUT/'script_compatibility.json').write_text(json.dumps(compatibility,indent=2),encoding='utf-8')
(OUT/'mission_bindings.json').write_text(json.dumps(bindings,indent=2),encoding='utf-8')

checks=json.loads((OUT/'check_results.json').read_text())
blends=json.loads((OUT/'blender_results.json').read_text())
rooms=json.loads((OUT/'room_results.json').read_text())
assert len(checks)==len(blends)==len(reports)==101
assert all(c.get('ok') and not c.get('action_differences') for c in checks.values())
by_mission=collections.defaultdict(list)
for name,item in inv['scenes'].items():
    for mission in set(u['mission'] for u in item['uses']): by_mission[mission].append(name)
lines=[
    'КАТСЦЕНЫ МИССИЙ 2–8 — ПОЛНЫЙ НАБОР ДЕКОМПИЛЯЦИИ',
    '',
    '101 использованный THN: Python Scene + отдельный JSON-дамп + отдельный blend.',
    'Также включены 7 копий mission2.py–mission8.py с привязками THORN_CLASS / THORN_ACCEPT_CLASS / THORN_DECISION_CLASS.',
    'Тексты VOICE_LINES сохранены без изменений. Готовые PrinceWalesScene и SpragueScene миссии 8 не изменены.',
    '',
    'Содержимое:',
    '  Pythonlancer/story/cutscenes/story_scenes/<source>.py — редактируемая постановка.',
    '  Pythonlancer/story/scripts/main/missionN.py — копии сценариев с привязками.',
    '  Pythonlancer/story/cutscenes/source_extensions.py — поддержка полных параметров THN, которых нет в текущих удобных классах.',
    '  SCENES/<source>.blend — персонажи и точки движения как меши; камеры и пути как маркеры.',
    '  SCENES/DUMPS/<source>.json — экспорт после сохранения и повторного открытия соответствующего blend.',
    '  <source>/source.json — полный разобранный оригинал; report.json — события, реплики, временные окна и происхождение.',
    '  inventory.json — связи mission/AddRTC/rtc.add/CallThorn -> RTC -> THN, с номерами строк.',
    '  script_compatibility.json — несовпадения старой постановки с текущими сценариями.',
    '  room_results.json — прослеженная цепочка Location -> база -> комната -> set_script -> petaldb -> OBJ.',
    '',
    'Проверки:',
    '  101/101 классов исполняются с исходными окнами facial; проверены длительность, ссылки и параметры событий.',
    f"  {sum(c['exact_source_actions'] for c in checks.values())} действий совпадают с оригиналом по времени, целям и всем исходным параметрам.",
    '  Финальные THN не записывались и не синхронизировались: этот шаг остаётся за single.py.',
    '  Игровая DATA и готовые сцены не менялись. Проверка EN не выполнялась.',
    '',
    'Важные результаты анализа:',
    '  m07_offer включает вступительный разговор Msn6Freeport и затем Msn7Offer. Они сохранены в исходной последовательности;',
    '  Msn7Offer привязан к общей постановке, а Msn6Freeport отдельно к ней не привязан, чтобы не воспроизвести её дважды.',
    '  Старые индексы/актёры не подгонялись под нынешние VOICE_LINES. При расхождении facial() намеренно выдаст ошибку:',
    '  такие сцены являются полными исходными постановками для редактирования, а не обещанием немедленной сборки через single.py.',
    '  В m04_offer_accept оригинал ссылается на отсутствующую cam_start (сразу заменяет её другой камерой в тот же момент).',
    '  В m06_lab_launch исходный неиспользуемый Camera_X ссылается на отсутствующий Mrk_CameraInit.',
    '  В m04_hatcher исходный IK ссылается на не объявленный в THN маркер wlkg_trent_front.',
    '  Эти исходные дефекты записаны в check_results.json; выдуманные координаты не добавлялись.',
    '  У исходных facial-клипов без звуковой реплики сохранены время и длительность с заменой на generic facial;',
    '  для настоящих реплик используются facial() и исходное выделенное окно, а не длина WAV.',
    '  Модели комнат включены только при наличии соответствующего OBJ. При отсутствии — точки и персонажи без подмены комнаты.',
    '  Blend предназначен для редактирования постановки и экспорта точек; движковые скелетные анимации исполняются Python/THN,',
    '  не запекаются в Blender. В каждый blend вложены Python, source.json и report.json.',
    '',
    'Развёртывание: содержимое Pythonlancer объединяется с Assets/Pythonlancer, SCENES — с Assets/SCENES.',
    'Перед заменой missionN.py сверить текущие правки: это копии на момент формирования набора.',
    'Готовые сцены миссии 8 используют уже существующие файлы m08.py и их blend/дампы, которые в этот набор не копировались.',
    '',
    'Набор по миссиям:',
]
for mission,names in sorted(by_mission.items()):
    lines += [f'Миссия {mission}: {len(names)} файлов', '  '+', '.join(sorted(names)),'']
(OUT/'README_RU.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
manifest={str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in OUT.rglob('*') if p.is_file() and p.suffix!='.blend1' and p.name!='manifest.json'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
archive=ROOT/'m02_m08_cutscenes.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for relative in manifest:
        z.write(OUT/relative,relative)
    z.write(OUT/'manifest.json','manifest.json')
print('Packaged',len(reports),'scenes;',archive.stat().st_size,'bytes')
print('Mission counts',dict((m,len(v)) for m,v in by_mission.items()))
print('Script incompatibilities',sum(bool(v['missing_current_lines'] or v['actor_mismatches']) for v in compatibility.values()))
