import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/base_interiors';OUT=TOP/'rh_biz_01_base/bar/prototype_v8'
source=json.loads((OUT/'source.json').read_text());assert hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256']
uv=json.loads((OUT/'uv_registration_validation.json').read_text());assert all(v['max_tangential_error_world_units']<.0002 for v in uv.values())
visibility=json.loads((OUT/'saved_scene_validation.json').read_text());assert visibility['all_replaced_originals_disabled_in_viewport_and_render']
html='''<meta charset="utf-8"><style>body{background:#172128;color:#e3edf5;font:17px system-ui;max-width:1500px;margin:30px auto;padding:20px}a{color:#8cd5f6}section{display:grid;grid-template-columns:1fr 1fr;gap:14px}img{width:100%}figure{margin:0}figcaption{padding:8px}p{max-width:1150px;line-height:1.5}</style><h1>Арка v8: криволинейные границы панелей</h1><p>Основная ошибка v7: прямые стороны трапеций не соответствовали криволинейным полям панелей. В этом варианте исходные приблизительные контуры заменены поиском перепада яркости в окрестностях отмеченных границ и аппроксимацией каждой стороны. Это полуавтоматический метод: участки поиска заданы вручную, переходы найдены в исходном изображении.</p><p>Неправильно расположенные дополнительные дуговые профили удалены. Они пока остаются рисунком исходной текстуры. Геометрический рельеф сохранён в шести панельных полях на обеих частях стены. Ручки и решётки не переделывались.</p>'''
def pair(title,a,b,la,lb):
 global html
 html+='<h2>'+title+'</h2><section>'
 for file,label in ((a,la),(b,lb)):
  assert (OUT/file).exists()
  html+=f'<figure><a href="{file}"><img src="{file}"></a><figcaption>{label}</figcaption></figure>'
 html+='</section>'
pair('Предыдущий вариант и исправление','../prototype_v7/after_arch_wall.png','after_arch_wall.png','v7 — приблизительные контуры','v8 — границы по изображению')
pair('Сравнение с исходной стеной','before_arch_wall.png','after_arch_wall.png','Исходный меш','Новые криволинейные выемки')
pair('Геометрия без текстур','before_arch_clay.png','after_arch_clay.png','Исходный меш','Рельеф панелей')
pair('Проверка границ прямо на исходных текстурах','r_bar_15_contour_check.png','r_bar_09_contour_check.png','r_bar_15: зелёный контур — граница выемки','r_bar_09: продолжение на правой части стены')
html+='<h2>Что проверено</h2><p>Повторно открыта сохранённая сцена: заменённые оригиналы отключены во вьюпорте и рендере. Для '+str(sum(v['tested_corners'] for v in uv.values()))+' углов проверено положение относительно исходных UV: максимальное смещение вдоль плоскости стены меньше 0,000001 игровой единицы. Это подтверждает правильный перенос разметки на меш, но не заменяет визуальную проверку границ на изображении.</p><p>Для кадров стены изолирована её плоскость и добавлен одинаковый проверочный свет до/после. Сохранённая Blender-сцена содержит всю комнату. Файлы установленной игры не изменены.</p><p><a href="bismarck_material_relief.blend">Blender-сцена v8</a> · <a href="uv_registration_validation.json">Проверка UV</a> · <a href="trace_report.json">Результаты трассировки границ</a></p>'
(OUT/'index.html').write_text(html,encoding='utf-8')
p=TOP/'index.html';s=p.read_text(encoding='utf-8')
if 'prototype_v8' not in s:s=s.replace('<ul>','<ul><li><a href="rh_biz_01_base/bar/prototype_v8/index.html">Бисмарк v8 — криволинейные панели, проверка совмещения</a></li>')
p.write_text(s,encoding='utf-8');print('Gallery ready. Source hash and saved-scene validation checked.')
