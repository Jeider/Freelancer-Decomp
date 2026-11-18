"""Review texture/contour registration explicitly, beside matched wall renders."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/base_interiors';OUT=TOP/'rh_biz_01_base/bar/prototype_v7'
data=json.loads((OUT/'scene_mesh.json').read_text());features=json.loads((OUT/'feature_contours.json').read_text());stats=json.loads((OUT/'prototype_stats.json').read_text());source=json.loads((OUT/'source.json').read_text())
assert hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256']
assert {13,17}.issubset(stats['changed_batches'])
assert all('Handle inset' not in f['label'] and 'Window bay inset' not in f['label'] for f in features['r_bar_15'])
validation=json.loads((OUT/'saved_scene_validation.json').read_text());assert validation['all_replaced_originals_disabled_in_viewport_and_render']
html='''<meta charset="utf-8"><style>body{background:#182128;color:#e8eef4;font:17px system-ui;max-width:1500px;margin:30px auto;padding:20px}a{color:#8cd5f6}section{display:grid;grid-template-columns:1fr 1fr;gap:12px}img,svg{width:100%}figure{margin:0}figcaption{padding:8px}p{line-height:1.5;max-width:1100px}.paths{opacity:.85}.off .paths{display:none}button{font:inherit;padding:10px;cursor:pointer}</style><h1>Арка: исправление совмещения рельефа с текстурой</h1><p>Вариант 7. Удалены приблизительные контуры v6, включая ошибочные прямоугольные выемки ручек и окон. Панельные поля и профили заново размечены на исходных текстурах r_bar_15 и r_bar_09. Распространение на меш выполняется через исходные UV.</p>'''
def pair(title,a,b):
 global html
 html+='<h2>'+title+'</h2><section>'
 for name,label in ((a,'Исходный меш'),(b,'Исправленный рельеф')):
  assert (OUT/(name+'.png')).exists()
  html+=f'<figure><a href="{name}.png"><img src="{name}.png"></a><figcaption>{label}</figcaption></figure>'
 html+='</section>'
pair('Вся арочная стена: одинаковый ракурс и свет','before_arch_wall','after_arch_wall')
pair('Геометрия без текстуры','before_arch_clay','after_arch_clay')
html+='<h2>Контуры непосредственно на текстурах</h2><p>Голубой — границы углублений, оранжевый — полосы выступающих профилей. Ручки остаются исходным рисунком: отдельных выдуманных выемок под ними больше нет.</p><button onclick="document.body.classList.toggle(\'off\')">Показать / скрыть контуры</button><section>'
for name in ('r_bar_15','r_bar_09'):
 m=next(m for m in data['materials'].values() if m['name'].split('.')[0].lower()==name);tex=Path(m['textures']['Dt_name']['path']).name
 html+=f'<figure><svg viewBox="0 0 1024 1024"><image href="../prototype_v1/textures/{tex}" width="1024" height="1024"/><g class="paths" fill="none">'
 for f in features[name]:
  pts=' '.join(f'{p[0]*1024:.2f},{p[1]*1024:.2f}' for p in f['uv']);color='#00e5ff' if f['depth']<0 else '#ffb32f'
  html+=f'<polygon points="{pts}" stroke="{color}" stroke-width="1.2"/>'
 html+=f'</g></svg><figcaption>{name}</figcaption></figure>'
html+='</section><p>Решётка и мелкие крепления пока остаются текстурными. Для осмотра на картинках изолирована плоскость стены, оборудование перед ней скрыто; сохранённая Blender-сцена содержит всю комнату. Игровые файлы не менялись.</p><p><a href="bismarck_material_relief.blend">Исправленная Blender-сцена</a> · <a href="saved_scene_validation.json">Проверка повторно открытой сцены</a> · <a href="feature_contours.json">Разметка UV</a></p>'
(OUT/'index.html').write_text(html,encoding='utf-8')
p=TOP/'index.html';s=p.read_text(encoding='utf-8')
if 'prototype_v7' not in s:s=s.replace('<ul>','<ul><li><a href="rh_biz_01_base/bar/prototype_v7/index.html">Бисмарк v7 — исправленное совмещение арки</a></li>')
p.write_text(s,encoding='utf-8');print('Both arch materials covered; original CMP unchanged; gallery includes texture/contour overlays.')
