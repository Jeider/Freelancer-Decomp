"""Organize existing blends without rebuilding geometry or moving dump points."""
import json
from pathlib import Path
import shutil
import bpy
from mathutils import Quaternion

ROOT=Path(__file__).resolve().parent
ASSETS=Path('D:/Games/FL_MOD/Assets')
OLD=ROOT.parent/'m02_m08_cutscenes/bundle'
STAGE=ROOT/'staged'
RX_NEG=Quaternion((1,0,0),-1.5708)
changes=json.loads((ROOT/'refactor_report.json').read_text())
results={}
for name,change in changes.items():
    source=ASSETS/'SCENES'/f'{name}.blend'
    backup=ROOT/'before/SCENES'/source.name
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copyfile(source,backup)
    dump_path=ASSETS/'SCENES/DUMPS'/f'{name}.json'
    backup_dump=ROOT/'before/SCENES/DUMPS'/dump_path.name
    backup_dump.parent.mkdir(parents=True,exist_ok=True)
    if not backup_dump.exists():shutil.copyfile(dump_path,backup_dump)
    original=json.loads(dump_path.read_text())
    spec=json.loads((OLD/'specs'/f'{name}.json').read_text())
    report=json.loads((OLD/name/'report.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(source))
    labels=['01 Characters','02 Movement positions','03 Cameras','04 Look and IK',
            '05 Lights','06 Props and paths','07 Room']
    groups={label:bpy.data.collections.new(label) for label in labels}
    for col in groups.values():bpy.context.scene.collection.children.link(col)
    for obj in list(bpy.context.scene.objects):
        n=obj.name
        if n in spec['characters']:label=labels[0]
        elif n in spec['character_markers']:label=labels[1]
        elif n in spec['cameras'] or n.startswith('cam_'):label=labels[2]
        elif 'light' in n.lower():label=labels[4]
        elif n.startswith('ROOM_'):label=labels[6]
        elif obj.type=='EMPTY' and any(k in n.lower() for k in ('head','eye','_ik','focus','look','marker')):label=labels[3]
        else:label=labels[5]
        for col in list(obj.users_collection):col.objects.unlink(obj)
        groups[label].objects.link(obj)
    for col in list(bpy.data.collections):
        if col not in groups.values() and not col.objects and not col.children:bpy.data.collections.remove(col)
    python_name=name+'.py'
    if python_name in bpy.data.texts:bpy.data.texts.remove(bpy.data.texts[python_name])
    bpy.data.texts.new(python_name).write((STAGE/'Pythonlancer/story/cutscenes/story_scenes'/python_name).read_text(encoding='utf-8'))
    note='РЕДАКТИРОВАНИЕ.txt'
    if note in bpy.data.texts:bpy.data.texts.remove(bpy.data.texts[note])
    bpy.data.texts.new(note).write(
        'Python-исходник рядом с постановкой: Assets/Pythonlancer/story/cutscenes/story_scenes/'+python_name+'\n'
        'Текст внутри blend — копия для справки. Правки постановки вносите в Pythonlancer.\n'
        'Имена объектов являются ключами дампа: не переименовывайте их без правки Python.\n'
        '01 Characters — персонажи; 02 Movement positions — их позиции с тем же мешем.\n'
        '03 Cameras — камеры; 04 Look and IK — направления взглядов; 05 Lights — свет.\n'
        'Маркеры на таймлайне показывают исходное время реплик. После изменения озвучки\n'
        'относительное время рассчитывается Python-постановкой; таймлайн — ориентир исходника.\n'
        'Экспорт точек: существующий Assets/SCENES/SCRIPTS/dumper.py.\n')
    for marker in list(bpy.context.scene.timeline_markers):
        if marker.name.startswith('RU '):bpy.context.scene.timeline_markers.remove(marker)
    fps=bpy.context.scene.render.fps/bpy.context.scene.render.fps_base
    for s in report['dialogue']:
        label=f"RU {s['index']:04} · {s['actor']}"
        if s['sound'] in change['removed_dialogue']:label+=' [removed]'
        bpy.context.scene.timeline_markers.new(label,frame=round(s['start']*fps))
    duration=min(report['source_duration'],max([s['start']+s['window'] for s in report['dialogue']]+[300]))
    bpy.context.scene.frame_end=max(1,round(duration*fps))
    dest=STAGE/'SCENES'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    bpy.ops.wm.open_mainfile(filepath=str(dest))
    dump={}
    for obj in bpy.context.scene.objects:
        obj.rotation_mode='QUATERNION';q=RX_NEG@obj.rotation_quaternion
        dump[obj.name]={'position':list(obj.location),'orientation':list(q)}
    assert dump.keys()==original.keys(),name
    for n,p in dump.items():
        for key,values in p.items():
            assert max(abs(a-b) for a,b in zip(values,original[n][key]))<1e-6,(name,n,key)
    output=STAGE/'SCENES/DUMPS'/dump_path.name;output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(dump,indent=2),encoding='utf-8')
    results[name]={'objects':len(dump),'points_unchanged':True,'collections':len(groups),'markers':len(report['dialogue'])}
    print('VERIFIED',name,flush=True)
(ROOT/'blender_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
