from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/base_interiors';OUT=TOP/'rh_biz_01_base/bar/prototype_v2'
old=json.loads((OUT.parent/'prototype_v1/scene_mesh.json').read_text());new=json.loads((OUT/'scene_mesh.json').read_text())
for a,b in zip(old['batches'],new['batches']):
 assert a['triangles']==b['triangles']
 if a['part']=='Root':assert a['vertices']==b['vertices']
 else:assert [v[6:] for v in a['vertices']]==[v[6:] for v in b['vertices']]
source=json.loads((OUT/'source.json').read_text());assert hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256']
stats=json.loads((OUT/'prototype_stats.json').read_text());assert 0<stats['added_triangles']<15000
style='<meta charset="utf-8"><style>body{background:#182027;color:#e4edf3;font:17px system-ui;margin:30px auto;max-width:1500px;padding:20px}a{color:#8bd4fa}section{display:grid;grid-template-columns:1fr 1fr;gap:12px}img{width:100%}figure{margin:0}p{max-width:1100px;line-height:1.5}figcaption{padding:8px}</style>'
html=style+'<h1>Бисмарк: отдельная геометрия фактуры — вариант 2</h1><p>Исходная сетка комнаты сохранена без дробления. Пол, стены, стойка и крупные формы не уплотнялись. Добавлены только отдельные кольца, металлические полосы и перекладины на местах нарисованных деталей. Прежний вариант с плотной сеткой отклонён.</p>'
html+=f'<p>Исходная сцена: {stats["original_triangles"]:,} треугольников. Добавленная фактура: {stats["added_triangles"]:,}. Кольца построены по окружности из 64 сегментов с профилем из шести контуров. Прямые полосы имеют по восемь вершин. Это офлайн-прототип, в игру не установлен.</p>'
html+='<p>Одинаковое освещение до и после. Лучи пропеллеров используют исходные вершины, UV и текстуру; исправлена ориентация матриц импорта и восстановлена двусторонняя прозрачность. Рендер Blender не является точным воспроизведением RP9.</p>'
for title,a,b in [('Общий вид','before_overview','after_overview'),('Стойка','before_counter','after_counter'),('Круглая деталь: текущая текстура','detail_texture_before','detail_texture_after'),('Та же деталь без текстуры','detail_clay_before','detail_clay_after')]:
 html+='<h2>'+title+'</h2><section>'
 for name,label in ((a,'До'),(b,'После')):
  assert (OUT/(name+'.png')).exists()
  html+=f'<figure><a href="{name}.png"><img src="{name}.png"></a><figcaption>{label}</figcaption></figure>'
 html+='</section>'
html+='<p>Крупные планы показывают изолированную группу технических панелей. Старые нарисованные блики остаются на текстуре. Перед игровым экспортом нужны окончательная подгонка профилей к рисунку, объединение добавленных деталей по материалам и проверка в движке.</p><p><a href="bismarck_bar_sparse.blend">Blender-сцена</a> · <a href="prototype_stats.json">Статистика деталей</a> · <a href="../prototype_v1/index.html">Отклонённый вариант 1 — архив</a></p>'
(OUT/'index.html').write_text(html,encoding='utf-8')
index=TOP/'index.html';text=index.read_text(encoding='utf-8');link='<li><a href="rh_biz_01_base/bar/prototype_v2/index.html">rh_biz_01_base — бар, вариант 2: отдельные детали рельефа</a></li>'
if 'prototype_v2' not in text:text=text.replace('<ul>','<ul>'+link)
index.write_text(text,encoding='utf-8')
(OUT/'validation.json').write_text(json.dumps({'root_vertices_unchanged':True,'all_original_triangle_counts_unchanged':True,'all_part_uvs_unchanged':True,'live_cmp_unchanged':True},indent=2))
print('Validated original room vertices, triangle counts, all part UVs and live CMP hash. Added:',stats['added_triangles'])
