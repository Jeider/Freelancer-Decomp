"""Build the compact review index, without duplicating renders or textures."""
from pathlib import Path
import html
import json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/contours_2k'
reports=[json.loads(p.read_text()) for p in sorted(OUT.glob('*/report.json'))]
priority=['li_hatcher_body','rh_reichman_body','pl_male3_peasant_body','li_male_elite_body']
reports.sort(key=lambda r:(priority.index(r['name']) if r['name'] in priority else 99,r['name']))
receipt=json.loads((OUT/'installed.json').read_text()) if (OUT/'installed.json').exists() else None
installed_hashes={r['name']:r['after_sha256'] for r in receipt['files']} if receipt else {}
installed=bool(receipt) and all(r['output_sha256']==installed_hashes.get(r['name'],r['previous_sha256']) for r in reports)
status='Установлено в игру; запуск и проверка катсцен остаются за пользователем.' if installed else 'Подготовленный пакет. Установка ещё не выполнена.'
parts=['''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Контуры персонажей — до 2 000 треугольников</title>
<style>body{max-width:1400px;margin:32px auto;padding:0 24px;background:#17202a;color:#e4ebf3;font:17px/1.55 system-ui}
a{color:#91ceff}img{width:100%;height:auto}section{border-top:1px solid #46596b;padding:24px 0}h1,h2{line-height:1.25}
table{border-collapse:collapse}td,th{padding:8px 16px;border-bottom:1px solid #46596b;text-align:left}
.views{display:grid;grid-template-columns:1fr 1fr;gap:12px}input{font:inherit;padding:10px;width:min(95%,500px)}
@media(max-width:850px){.views{grid-template-columns:1fr}}small{color:#acbdce}details{margin:12px 0}</style>
<h1>Точечная правка контуров: до 2 000 треугольников</h1>''',f'<p>{status}</p>',
'''<p>На сравнениях <strong>слева исходная малополигональная геометрия, справа новый вариант</strong>.
Основной бюджет потрачен на концы рукавов и наручей. Дополнительно: жилетка и ремешок Хетчер,
эполеты Райхмана и выбранные выступающие края брони. Ноги и ступни сохранены по исходнику.
Это офлайн-рендеры геометрии; игровые освещение и анимации здесь не воспроизводятся.</p>
<p>torture и alien_nomad_body исключены. Лимит относится к Mesh0 одного тела, по всем материалам;
головы, отдельные кисти и остальные LOD этим проходом не меняются.</p>
<p>Blender-файлы содержат UV, исходные нормали и группы весов. Исходник скрыт в отдельной коллекции.
Анимационного рига в этих файлах нет. Текстуры связаны с существующим каталогом all_bodies;
для редактирования сохраняйте эту структуру папок.</p>
<p><a href="../../../tools/character_rounding/PLAN.txt">План</a> · <a href="validation.json">Проверка DFM</a> ·
<a href="blend_validation.json">Проверка сохранённых Blender-файлов</a></p>
<input id="filter" placeholder="Поиск: hatcher, reichman, pirate…">''']
for r in reports:
    name=r['name'];folder=OUT/name;cache=json.loads((folder/'render_source.json').read_text()) if (folder/'render_source.json').exists() else {}
    features=[]
    for key,label in [('cuff','Концы рукавов / наручей'),('vest','Края жилетки'),('belt','Ремешок'),('epaulette','Эполеты'),('armor_edge','Выступающие края брони')]:
        if r['refined_edges'].get(key):features.append(label)
    if not features:features=['Исходная геометрия без дополнительного дробления']
    parts.append(f'<section data-name="{name}" id="{name}"><h2>{name}</h2><p>{"; ".join(features)}.</p>')
    parts.append(f'<table><tr><th>Исходный Mesh0</th><th>Прежний плотный вариант</th><th>Новый Mesh0</th></tr><tr><td>{r["triangles_before"]}</td><td>{r["previous_triangles"]}</td><td><strong>{r["triangles_after"]}</strong></td></tr></table>')
    parts.append(f'<p><a href="{name}/contours_2k.blend">Редактировать в Blender</a> · <a href="{name}/report.json">Отчёт</a></p><div class="views">')
    for view,label in [('front','Спереди'),('back','Сзади')]:
        if (folder/(view+'.png')).exists():parts.append(f'<figure><figcaption>{label}</figcaption><a href="{name}/{view}.png"><img loading="lazy" src="{name}/{view}.png"></a></figure>')
    parts.append('</div>')
    for view in cache.get('views',[]):
        if view in ('front','back'):continue
        labels={'cuff':'Наруч крупно','cuff_clay':'Наруч без текстуры','vest':'Жилетка','vest_clay':'Жилетка без текстуры','belt':'Ремешок','belt_clay':'Ремешок без текстуры','epaulette':'Эполет','epaulette_clay':'Эполет без текстуры'}
        parts.append(f'<details><summary>{labels.get(view,view)}</summary><a href="{name}/{view}.png"><img loading="lazy" src="{name}/{view}.png"></a></details>')
    parts.append('</section>')
parts.append('''<script>document.getElementById('filter').addEventListener('input',e=>{let q=e.target.value.toLowerCase();document.querySelectorAll('section').forEach(s=>s.hidden=!s.dataset.name.includes(q));});</script></html>''')
(OUT/'index.html').write_text('\n'.join(parts),encoding='utf-8')
print('Gallery models:',len(reports))
