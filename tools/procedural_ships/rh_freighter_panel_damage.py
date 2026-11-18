"""Native panel-damage reference and narrow offline Q13 panel revision."""
import argparse, json, secrets, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import rh_freighter_final as d
from rh_freighter_final_preview import view

REF=d.TOPIC/'references/panel_damage'
REV=d.OUT/'panel_damage'

def reference():
    REF.mkdir(parents=True,exist_ok=True);REV.mkdir(exist_ok=True)
    mats=d.f.audit.material_table([d.GAME/'DATA/ships/rheinland/rh_playerships.mat',d.MAT,d.ENV])
    entries=[];sheet=Image.new('RGB',(1800,1200),'#18202a');draw=ImageDraw.Draw(sheet)
    for row,side in enumerate(('port','starboard')):
        path=d.GAME/('DATA/ships/rheinland/rh_freighter/rh_freighter_dmg_'+side+'_side_panel.3db')
        target=REF/path.name
        if target.exists():assert d.f.digest(target)==d.f.digest(path)
        else:shutil.copy2(path,target)
        _,ns=d.tree(target);gs=d.simple_geometry(ns)
        entries.append(dict(path=str(path),sha256=d.f.digest(path),groups=gs,
                            materials=[mats[g['material']]['name'] for g in gs]))
        s=-1 if side=='port' else 1
        for col,cam in enumerate(((s,.6,1.1),(s,-.3,-.7),(s,.1,.03))):
            sheet.paste(view(gs,mats,cam,600),(col*600,row*600))
            draw.text((col*600+15,row*600+15),side+' / native rh_freighter',fill='white')
    d.dump(REF/'source.json',entries);sheet.save(REF/'native_panel_damage.png')
    snapshot=d.read('delivery.json')
    for name,record in snapshot['files'].items():assert d.f.digest(d.ASSETS/name)==record['sha256'],('Offline asset edited',name)
    assert d.f.digest(d.OUT/'rh_pir_freighter.blend')==snapshot['blend_sha256'],'Review blend changed'
    if not (REV/'before.json').exists():
        d.dump(REV/'before.json',dict(delivery=snapshot,damage=d.read('damage_world.json')))
        shutil.copy2(d.OUT/'previews/damage_ship_above.png',REV/'before.png')
    print('Native references saved; offline delivery matches its manifest.')

def export():
    from rh_freighter_final_build import simple
    build=d.read('build.json');before=d.read('panel_damage/before.json')['delivery'];changed=[]
    for z in build['damage']:
        if 'side_panel' not in z['zone']:continue
        gs=d.packed(d.read('damage_world.json')[z['zone']]);local=d.f.base.world(gs,np.eye(3),-np.array(z['position']))
        record=simple(z['zone'],local,secrets.token_hex(6));z.update(record);changed.append(z['file'])
    d.dump(d.OUT/'build.json',build)
    for name,record in before['files'].items():
        if '_side_panel.' not in name:assert d.f.digest(d.ASSETS/name)==record['sha256'],name
    d.dump(REV/'export.json',dict(changed=changed,main_cmp_unchanged=True,engines_unchanged=True,installed=False))
    print('EXPORTED TWO DAMAGE PANELS ONLY')

def review():
    mats=d.f.audit.material_table([d.MAT,d.ENV]);before=d.read('panel_damage/before.json')['damage']
    actual={e['zone']:e['groups'] for e in d.read('review/extra_geometry.json')['damage']}
    sheet=Image.new('RGB',(1800,1500),'#18202a');draw=ImageDraw.Draw(sheet)
    for col,entries in enumerate((before,actual)):
        gs=d.packed(entries['port_side_panel'])
        for row,camera in enumerate(((-1,.35,.8),(-.35,.45,-1))):
            sheet.paste(view(gs,mats,camera,750),(col*900+75,row*750))
            draw.text((col*900+22,row*750+22),('BEFORE / flat backing','AFTER / folded sheet and raised broken structure')[col],fill='white')
    sheet.save(REV/'comparison.png')
    ref=json.loads((REF/'source.json').read_text());proof=d.read('panel_damage/geometry_check.json')
    text='''# Q13 — оторванные боковые панели

**Принято пользователем 18 ноября 2026:** «да, такая разрушаемость пойдёт».
Этот вариант — утверждённая основа разрушения боковин Q13.

Исходный ориентир — реальные damage 3DB обычного `rh_freighter`.
[Исходные боковины](../../references/panel_damage/native_panel_damage.png) показывают
глубокую механическую начинку, вывернутые края отверстий и неодинаковую глубину
изломов. Плоская подложка предыдущей Q13 этого ощущения не давала.

В новой версии деформирована кромка нашей сохранившейся панели. На каждом борту
семь отогнутых полос обшивки с широкими основаниями, разной шириной, скручиванием
и тёмной обратной стороной. Они направлены вверх, вниз, назад и наружу; правый
борт имеет немного другие отгибы. Механическая подложка получила объёмные изломы.
Реальные native треугольники служат ориентиром и не копируются в новую геометрию.

- [До / после, реальная геометрия](comparison.png).
- [Повреждённая сборка сверху](../previews/damage_ship_above.png).
- [Повреждённая сборка снизу](../previews/damage_ship_below.png).
- [Проверки замкнутости и соединений](geometry_check.json).
- [Обновлённый Blender](../rh_pir_freighter.blend): коллекция `Damage / static flight assembly`.

Все 14 полос геометрически пересекаются основанием с сохранившейся панелью или
внутренней подложкой. Проверены обе стороны: 0 открытых и неманифолдных рёбер
у каждого замкнутого элемента. После экспорта повторно проверены треугольники,
материалы, UV, расположение по damage HP и бинарные SUR.

Обновлены только две боковые damage 3DB и их SUR, а также damage-коллекция Blender.
Основной CMP, пользовательские HP, LOD, wire, анимации, движки и общий MAT
сохранены побайтно. Установка в игру не выполнялась; Pythonlancer не менялся.

Воспроизведение после основной сборки: `rh_freighter_panel_damage_blender.py --author`
через `tools/blender_workspace.py`; затем `rh_freighter_panel_damage.py --export`,
`rh_freighter_final_check.py` и обновление Blender командой `--review` первого скрипта.
Генерация основана на закреплённой предыдущей форме в `before.json`; текущие
повреждённые двигатели сохраняются независимо от этой коррекции.

## Исходники

'''
    text+='\n'.join('- `'+e['path']+'` — SHA256 `'+e['sha256']+'`.' for e in ref)
    (REV/'README.md').write_text(text,encoding='utf8')
    print('PANEL REVIEW READY',[(z,r['triangles']) for z,r in proof.items()])

if __name__=='__main__':
    if '--reference' in __import__('sys').argv:reference()
    if '--export' in __import__('sys').argv:export()
    if '--review' in __import__('sys').argv:review()
