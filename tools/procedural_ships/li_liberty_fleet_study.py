"""Read-only Liberty fleet style references, using installed CMP geometry."""
import json
import html
import os
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np

import pirate_art_audit as a
from bw_family_audit import bounds, frame, sheet, write_json
from li_elite_concept_audit import active_ships, CAMS
from li_elite_lineage_audit import valid
from rh_redesign_paths import TOPIC

OUT = TOPIC/'li_elite/fleet_study'
PRIMARY = [('fighter','li_fighter'), ('elite','li_elite'), ('elite2','li_elite2'),
           ('freighter','li_freighter'), ('cruiser','rtcprop_l_cruiser'),
           ('dreadnought','li_dreadnought')]


def reference_transforms(nodes, pose=None):
    """Native zero transforms; report unbound source placeholders explicitly."""
    assert pose is None
    flat={p.lower():n.blob for p,n in a.source.mesh.walk(nodes)}
    matrices=a.full.matrices(a.full.constructs(flat))
    result,warnings={},[]
    for path,blob in flat.items():
        if '/cmpnd/' not in path or not path.endswith('/file name'): continue
        file=a.source.mesh.string(blob).lower()
        name=a.source.mesh.string(flat[path.rsplit('/',1)[0]+'/object name']).lower()
        if name not in matrices and name!='root':
            warnings.append('Unbound source object '+name+'; reference fallback identity, not a model repair')
        result[file]=matrices.get(name,(np.eye(3),np.zeros(3)))
    return result,warnings


def write_gallery():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))
    links=[]
    for row in manifest['art']:
        source=Path(row['path'])
        existing=OUT.parent/'references'/source.name
        dest=existing if existing.exists() and a.sha(existing)==row['sha256'] else OUT/'art'/source.name
        if not dest.exists():
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,dest)
        assert a.sha(dest)==row['sha256']
        row['review_copy']=dest.as_posix()
        href=html.escape(Path(os.path.relpath(dest,OUT)).as_posix(),quote=True)
        links.append(f'<li><a href="{href}">{html.escape(source.name)}</a></li>')
    write_json(OUT/'manifest.json',manifest)
    notes={
        'fighter':'Округлый нос, суженная середина и расходящиеся тонкие лопасти.',
        'elite':'Капсула, поперечный воротник, продольное ядро и широкий веер.',
        'elite2':'Высокий профиль создают наклонные плоскости при узком корпусе.',
        'freighter':'Прямые грузовые объёмы связаны большим лучевым мотивом.',
        'cruiser':'Кольца, длинная ось, смена сечений и раскрывающиеся основания двигателей.',
        'dreadnought':'Расширенный нос, перехваты и отдельные крупные массы по длине.'}
    cards=[]
    for name,_ in PRIMARY:
        cards.append(f'<article><h2>{name}</h2><p>{notes[name]}</p>'
            f'<a href="{name}_views.jpg"><img loading="lazy" src="{name}_views.jpg" alt="{name}: четыре вида"></a></article>')
    content='''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Liberty — исследование флота</title>
<style>body{margin:0;background:#181d25;color:#e9edf4;font:17px/1.6 system-ui,sans-serif}
main{max-width:1500px;margin:auto;padding:26px}a{color:#abd3ff}h1{margin:0;font-size:32px}
button{padding:11px 18px;margin:5px 8px 12px 0;background:#34455b;color:white;border:1px solid #637c9b;cursor:pointer;border-radius:6px;font:inherit}
img{display:block;width:100%;height:auto}#board{max-width:1100px;margin:auto}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
article{padding:18px;background:#242d39;border-radius:8px}article h2{margin:0}aside{padding:18px;border-left:4px solid #dba770;background:#252c35}
@media(max-width:800px){.cards{grid-template-columns:1fr}main{padding:16px}}</style>
<main><h1>Liberty: характер всего флота</h1>
<p>Шесть основных форм, 18 вариантов материалов и семь исходных артов. Исследование после отклонения L03.</p>
<p><a href="README.md">Наблюдения и новый подход</a> · <a href="../README.md">LI elite</a> · <a href="manifest.json">Источники и хеши</a></p>
<aside>Общая ось, смена сечений и контраст объёмного ядра с тонкими плоскостями.
Высота силуэта и толщина деталей — разные параметры. На листах размеры кораблей подогнаны к кадру: физический масштаб между классами не сохранён.</aside>
<p><button onclick="show('fleet_clay.jpg')">Форма без текстур</button><button onclick="show('fleet_texture.jpg')">Родные материалы</button><button onclick="show('fleet_variants.jpg')">BASE / PIR / NMD</button></p>
<a id="full" href="fleet_clay.jpg"><img id="board" src="fleet_clay.jpg" alt="Сравнение флота Liberty"></a>
<h2>Основные формы в четырёх видах</h2><div class="cards">'''+''.join(cards)+'''</div>
<h2>Исходные арты</h2><ul>'''+''.join(links)+'''</ul>
<p>Капитальные корабли изучены как источники стиля. Новая геометрия не создавалась.
У крейсера есть исходная несогласованность привязки отдельного орудия; его положение не используется для выводов о форме корпуса. Подробности в разборе.</p>
<script>function show(file){document.getElementById('board').src=file;document.getElementById('full').href=file;}</script></main></html>'''
    (OUT/'index.html').write_text(content,encoding='utf8')


def main():
    free = shutil.disk_usage(TOPIC).free
    assert free > 512*1024**2
    OUT.mkdir(parents=True, exist_ok=True)
    active = active_ships()
    grouped = defaultdict(list)
    for alias, values in active.items():
        path = values.get('da_archetype',[''])[0].replace('\\','/').lower()
        if '/liberty/' in path:
            grouped[path].append(alias)
    old = {}
    for p in (TOPIC/'analysis/full_models/models').glob('li_*.json'):
        r = json.loads(p.read_text(encoding='utf8'))
        if r['path'].startswith('ships/liberty/') and r['extension']=='.cmp':
            old[r['path']] = r
    inventory = []
    for path, r in sorted(old.items()):
        actual = a.source.DATA/path
        assert a.sha(actual)==r['sha256'], 'Changed source: '+path
        inventory.append(dict(path=actual.as_posix(),sha256=r['sha256'],
            aliases=grouped.get(path,[]),lod0=r['lods'].get('0'),
            kind='weapon_component' if path.endswith('_gun.cmp') else 'ship',
            previous_audit=(TOPIC/'analysis/full_models/models'/(r['key']+'.json')).as_posix()))
    write_json(OUT/'inventory.json',dict(active_unique_models=len(grouped),
               inspected_cmp_files=inventory,free_bytes_before=free))
    loaded = {}

    def read(alias, override=None):
        values = active[alias]
        src = dict(model=values['da_archetype'][0].replace('\\','/').lower(),
                   materials=[v.replace('\\','/').lower() for v in values['material_library']])
        if override:
            src['model'] = override
        native_loader=a.source.transforms
        try:
            a.source.transforms=reference_transforms
            rest,mats,stats = a.source.load(src)
        finally:
            a.source.transforms=native_loader
        rest=[dict(g,part=g['part'].lower()) for g in rest]
        path = a.source.DATA/src['model']
        assert stats['sha256']==old[src['model']]['sha256']
        _,nodes=a.source.mesh.read_tree(path.read_bytes())
        flat={p.lower():n.blob for p,n in a.source.mesh.walk(nodes)}
        cons=a.full.constructs(flat); channels=a.full.channels(flat,cons)
        wing=[c for c in channels if c['script']==a.SCRIPT]
        assert all(valid(c) for c in wing)
        pose = a.motion.scene_at(dict(path=src['model'],constructs=cons,channels=channels),rest,0,a.SCRIPT) if wing else rest
        center,radius=frame(pose)
        report=dict(alias=alias if not override else None,source_model=path.as_posix(),
            source_sha256=stats['sha256'],materials=src['materials'],
            assets=[dict(path=(a.source.DATA/p).as_posix(),sha256=a.sha(a.source.DATA/p))
                    for p in [src['model']]+src['materials']],
            pose='Sc_extend wing t=0, deployed' if wing else 'native zero pose; no wing channels',
            wing_channels=wing,non_pose_findings=[c for c in channels if not valid(c)],
            bounds=bounds(pose),lod0_triangles=stats['triangles'],source_transform_findings=stats['warnings'],
            native_audit=(TOPIC/'analysis/full_models/models'/(old[src['model']]['key']+'.json')).as_posix())
        return pose,mats,center,radius,report

    for name,alias in PRIMARY:
        row=read(alias); loaded[name]=row
        pose,mats,center,radius,report=row
        write_json(OUT/(name+'_source.json'),report)
        cams=[CAMS[0],CAMS[3],CAMS[2],CAMS[4]]
        panels=[(label,a.source.render(pose,mats,center,radius,cam,500,'texture')) for cam,label in cams]
        if not (OUT/(name+'_views.jpg')).exists():
            sheet(OUT/(name+'_views.jpg'),[panels[:2],panels[2:]],2,'LIBERTY / '+name.upper(),
                  'Installed source; flight for animated player ships. Fitted to frame, not common scale.',size=500)
        print(name,report['bounds']['dimensions'],flush=True)
    for mode in ['texture','clay']:
        rows=[]
        for start in [0,3]:
            for ci in [0,3]:
                rows.append([(name+' / '+CAMS[ci][1],a.source.render(*loaded[name][:4],CAMS[ci][0],480,mode))
                             for name,_ in PRIMARY[start:start+3]])
        sheet(OUT/('fleet_'+mode+'.jpg'),rows,3,'LIBERTY / SIX CORE FORMS',
              'Each ship fitted independently. Shape comparison, NOT physical scale. Original source geometry.',size=480)
    variant_rows=[]; variant_reports=[]
    for name,alias in PRIMARY:
        aliases=[alias, 'li_'+name+'_pir' if name not in ['cruiser','dreadnought'] else 'li_pir_'+name,
                 'li_'+name+'_nmd' if name not in ['cruiser','dreadnought'] else ('li_cruiser' if name=='cruiser' else 'li_nmd_dreadnought')]
        panels=[]
        for index,(kind,al) in enumerate(zip(['BASE','PIR','NMD'],aliases)):
            if index==0:
                row=loaded[name]
            elif al in active:
                row=read(al)
            else:
                assert name=='cruiser' and kind=='PIR'
                row=read('li_pir_dreadnought','ships/liberty/li_pir_cruiser/li_pir_cruiser.cmp')
            pose,mats,center,radius,report=row
            variant_reports.append(dict(family=name,variant=kind,**report))
            panels.append((name+' / '+kind,a.source.render(pose,mats,center,radius,CAMS[0][0],370,'texture')))
        variant_rows.append(panels)
    sheet(OUT/'fleet_variants.jpg',variant_rows,3,'LIBERTY / BASE - PIR - NMD',
          'Fitted independently; pirate cruiser exists on disk without an active Ship alias.',size=370)
    write_json(OUT/'variants.json',variant_reports)
    art=[]
    for p in sorted(Path('D:/work/ART_SHIP/LI').iterdir()):
        if p.suffix.lower() not in ['.jpg','.png']: continue
        art.append(dict(path=p.as_posix(),sha256=a.sha(p)))
    outputs=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in sorted(OUT.glob('*.jpg'))]
    assert all(a.sha(Path(r['path']))==r['sha256'] for r in inventory)
    write_json(OUT/'manifest.json',dict(art=art,outputs=outputs,
        script='tools/procedural_ships/li_liberty_fleet_study.py',
        models_unchanged=True,scope='Source reference renders; no new ship geometry or deployment.',
        caveats=['Not authenticated retail.', 'VMeshRef renderer omits direct VMeshPart placeholders.',
                 'Simplified glass/environment; no back-face or collision validation.',
                 'Ship scales normalized for visual style comparison.']))
    write_gallery()
    print(json.dumps(dict(core_forms=6,variants=len(variant_reports),art=len(art),all_sources_unchanged=True)))


if __name__=='__main__':
    main()
