from pathlib import Path
import json,hashlib,sys
VERSION=sys.argv[1] if len(sys.argv)>1 else 'prototype_v3'
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/base_interiors';OUT=TOP/'rh_biz_01_base/bar'/VERSION
stats=json.loads((OUT/'prototype_stats.json').read_text());source=json.loads((OUT/'source.json').read_text())
assert hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256']
names=['r_bar_14','detailmap_r_bar_10','detailmap_r_bar_04','r_bar_01','r_bar_02','r_bar_15']
if VERSION in ('prototype_v4','prototype_v5','prototype_v6'):names.insert(3,'detailmap_r_bar_03')
if VERSION in ('prototype_v5','prototype_v6'):names=['r_bar_22','r_bar_28','r_bar_05']+names
assert set(stats['material_triangles'])==set(names)
expected={5,6,8,14,16,17}
if VERSION in ('prototype_v4','prototype_v5','prototype_v6'):expected.add(7)
if VERSION in ('prototype_v5','prototype_v6'):expected.update((9,22,26))
assert set(stats['changed_batches'])==expected
style='<meta charset="utf-8"><style>body{background:#19212a;color:#e4edf4;font:17px system-ui;max-width:1500px;margin:30px auto;padding:20px}a{color:#8ad5f8}section{display:grid;grid-template-columns:1fr 1fr;gap:12px}img{width:100%}figure{margin:0}figcaption{padding:8px}p{max-width:1100px;line-height:1.5}.texture{max-width:340px}</style>'
html=style+'<h1>Бисмарк — рельеф шести указанных материалов</h1><p>Вариант 3. Углубления вырезаны по контурам рисунка: дно, боковые стенки и фаски являются геометрией. Изменены только шесть указанных групп материалов. Нет равномерного дробления пола. Исходные лучи сохранены с исправленной ориентацией импорта.</p>'
html+=f'<p>Вся сцена: {stats["source_triangles"]:,} → {stats["result_triangles"]:,} треугольников. Это офлайн-прототип Blender; игровая модель не изменена. Освещение до/после одинаковое, часть бликов остаётся запечённой в исходных текстурах.</p>'
descriptions={
 'r_bar_22':'Арочная выемка, боковые каннелюры, горизонтальные профили и углублённые нижние панели.',
 'r_bar_28':'Центральная круглая выемка, вентиляционные щели, стыки панелей и карманы ручек.',
 'r_bar_05':'Объём трубчатых полос, гнёзда и кромки панелей. Профиль полос непрерывен; участки с уже искривлёнными нормалями исходного меша исключены из повторной обработки труб.',
 'detailmap_r_bar_03':'Рельеф соседних секций полосы: круглые выемки, рамки и внутренние перекладины. Обрабатываются все экземпляры исходной UV-развёртки.',
 'r_bar_14':'Продольное ребро и две трапециевидные выемки с фасками.',
 'detailmap_r_bar_10':'Фигурная верхняя ниша, нижняя ниша, длинные углублённые панели и каналы орнамента.',
 'detailmap_r_bar_04':'Округлённые вентиляционные щели, круглые механические выемки, диагональное ребро и кромки панелей.',
 'r_bar_01':'Объёмные разделители панелей. Уже существующие круглые ниши и предметы сохранены; повторно вырезать их не нужно.',
 'r_bar_02':'Та же обработка разделителей по фактическим UV этого материала; существующая геометрия ниш сохранена.',
 'r_bar_15':'Углубление оконных секций, объём круглой детали и верхнего обрамления. Мелкая сетка рисунка пока остаётся текстурной.'}
data=json.loads((OUT/'scene_mesh.json').read_text())
def pair(a,b):
 result='<section>'
 for name,label in ((a,'До'),(b,'После')):
  assert (OUT/(name+'.png')).exists(),name
  result+=f'<figure><a href="{name}.png"><img loading="lazy" src="{name}.png"></a><figcaption>{label}</figcaption></figure>'
 return result+'</section>'
html+='<h2>Стойка в сборе</h2>'+pair('before_counter','after_counter')
if VERSION in ('prototype_v4','prototype_v5','prototype_v6'):
 html=html.replace('шести указанных материалов','материалов бара').replace('Вариант 3.','Вариант 4.').replace('шесть указанных групп материалов','семь групп материалов')
 html+='<h2>Вся полоса за столиками: r_bar_03 и r_bar_04</h2>'+pair('before_seating_fascia','after_seating_fascia')
 html+='<p>Исправлен Blender-вьюпорт: исходные заменённые объекты перенесены в коллекцию ARCHIVE, отключённую для показа и рендера. В рабочей сцене видна только одна версия каждой поверхности.</p>'
if VERSION in ('prototype_v5','prototype_v6'):html=html.replace('Вариант 4.',f'Вариант {VERSION[-1]}.').replace('семь групп материалов','десять групп материалов')
if VERSION=='prototype_v6':
 descriptions['r_bar_15']='Дополнены непрерывные дуговые профили обрамления, поля арочных панелей и выемки ручек. Решётка осталась текстурной: её отдельные прутья в этом варианте ещё не построены.'
 html+='<h2>Арочная стена целиком</h2><p>Для осмотра изолирована плоскость стены: навес и оборудование перед ней временно скрыты. В обоих вариантах одинаковый дополнительный свет для проверки рельефа.</p>'+pair('before_arch_wall','after_arch_wall')
 html+='<h2>Рельеф арочной стены без текстур</h2>'+pair('before_arch_clay','after_arch_clay')
for name in names:
 html+=f'<h2>{name.replace("detailmap_","")}</h2><p>{descriptions[name]}</p>'
 m=next(m for m in data['materials'].values() if m['name'].split('.')[0].lower()==name)
 tex=Path(m['textures']['Dt_name']['path']).name
 html+=f'<p><a href="../prototype_v1/textures/{tex}">Исходная текстура материала</a></p>'
 html+=pair(name+'_texture_before',name+'_texture_after')
 html+='<p>Без текстуры — проверка настоящего рельефа:</p>'+pair(name+'_clay_before',name+'_clay_after')
html+='<h2>Общий план</h2>'+pair('before_overview','after_overview')
html+='<p>Контуры размечены вручную; это не выдавливание яркости текстуры. Глубина и ширина фасок остаются параметрами прототипа. Мелкие потёртости, заклёпки и часть орнамента ещё текстурные. На изолированных видах скрыты остальные материалы комнаты.</p><p><a href="bismarck_material_relief.blend">Blender-сцена</a> · <a href="feature_contours.json">Контуры и глубины</a> · <a href="prototype_stats.json">Статистика по материалам</a></p>'
(OUT/'index.html').write_text(html,encoding='utf-8')
index=TOP/'index.html';text=index.read_text(encoding='utf-8')
if VERSION not in text:text=text.replace('<ul>',f'<ul><li><a href="rh_biz_01_base/bar/{VERSION}/index.html">Бисмарк — {VERSION}: рельеф материалов</a></li>')
index.write_text(text,encoding='utf-8');print('Six selected material groups checked. Live CMP unchanged. Total triangles:',stats['result_triangles'])
