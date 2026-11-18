"""Publish the modeled result and its comparisons into the existing topic."""
import json
from pathlib import Path
from depot_surface_audit import OUT
from native_common import sha

BUILD=OUT/'modeled'


def comparison(view_id,name,title,before='Исходник FL_ND'):
    return f'''<section id="{view_id}" data-view="{name}" data-style="textured"><h2>{title}</h2>
<div><button onclick="showWhole('{view_id}',0)">{before}</button><button onclick="showWhole('{view_id}',100)">Новая модель</button><button onclick="setStyle('{view_id}','textured')">С текстурой</button><button onclick="setStyle('{view_id}','clay')">Чистая геометрия</button></div>
<div class="compare"><img class="before" loading="lazy" src="{name}_textured_before.png" alt="{title}: до"><img class="after" loading="lazy" src="{name}_textured_after.png" alt="{title}: после"></div>
<input aria-label="Доля новой модели" type="range" min="0" max="100" value="100" oninput="applyClip('{view_id}',this.value)"></section>'''


def main():
    stats=json.loads((BUILD/'geometry_validation.json').read_text())
    native=json.loads((BUILD/'native_validation.json').read_text())
    preview=json.loads((BUILD/'preview_validation.json').read_text())
    checks=json.loads((BUILD/'surface_validation.json').read_text())
    assert preview['cmp_sha256']==checks['cmp_sha256']==native['exported_sha256'] and checks['all_passed']
    installed=None
    if (BUILD/'installed.json').exists():
        record=json.loads((BUILD/'installed.json').read_text())
        live=Path(record['target'])
        if record['verified'] and record['sha256']==native['exported_sha256'] and live.is_file() and sha(live.read_bytes())==record['sha256']:
            installed=record
    status='Установлено в FL_MOD, файл проверен.' if installed else 'В игру пока не установлено.'
    cmp_href=Path(installed['target']).as_uri() if installed else 'package/DATA/BASES/RHEINLAND/rh_depot_deck.cmp'
    features=json.loads((BUILD/'features.json').read_text())['features']
    titles=dict(west_wall='Центральная панель под механизмами',north_wall='Боковая стена и терминалы',
        south_wall='Противоположная стена и входная ниша',north_wide='Общий вид одной стороны',
        south_wide='Общий вид противоположной стороны',west_oblique='Центральная панель под углом')
    doc=['''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Depot deck — смоделированный рельеф</title>
<style>body{background:#141b22;color:#e6edf3;font:17px/1.55 system-ui;max-width:1320px;margin:auto;padding:24px}a{color:#8edbff}h1,h2{line-height:1.2}section{margin:38px 0}button{padding:8px 14px;margin:4px;border:1px solid #4f6678;background:#22313e;color:inherit;border-radius:5px;cursor:pointer}.compare{position:relative;line-height:0}.compare img{display:block;width:100%}.compare .after{position:absolute;inset:0;clip-path:inset(0 0 0 0)}input[type=range]{width:100%}table{border-collapse:collapse}th,td{padding:8px 15px;text-align:left;border-bottom:1px solid #40525f}.muted{color:#aebbc6}.status{padding:16px;background:#223a36}.links{display:flex;gap:24px;flex-wrap:wrap}.atlases{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.atlases img{width:100%}</style>
<h1>Depot deck: настоящий рельеф стен</h1>''']
    doc.append(f'<p class="status"><b>Геометрия смоделирована и экспортирована в CMP.</b> {stats["original_triangles"]:,} → {stats["result_triangles"]:,} треугольников. {status}</p>')
    doc.append('''<p>Углублены большие стеновые поля, каналы и жалюзи; добавлены карманы центральной панели, рельеф обрамлений терминалов и щитов внутри ниш. Краны, орёл, дисплеи и анимации сохранены.</p>
<div class="links"><a href="rh_depot_deck_relief.blend">Модель Blender</a><a href="package/DATA/BASES/RHEINLAND/rh_depot_deck.cmp">Готовый CMP</a><a href="features.json">Редактируемые контуры</a><a href="native_validation.json">Проверка экспорта</a><a href="regional_transfer.json">Перенос на KU / LI / BR</a></div>''')
    doc[-1]=doc[-1].replace('package/DATA/BASES/RHEINLAND/rh_depot_deck.cmp',cmp_href)
    if installed:doc.append('<p><a href="installed.json">Отчёт установки</a>. Копия CMP из пакета удалена после проверки установленного файла; Blender, контуры и сравнения сохранены.</p>')
    # The range is percentage of the new image shown, from the left. State this
    # explicitly rather than imply a side-by-side view at the endpoints.
    doc.append('<p class="muted">По умолчанию показана новая модель. Ползунок меняет долю новой картинки поверх исходной; кнопки переключают целиком. В обоих вариантах одинаковые текущие текстуры и диагностический свет. Внешнее окружение и игровой шейдер не воспроизводятся. Нейтральный материал показывает именно геометрию.</p>')
    if preview.get('door_views'):
        previous=json.loads((BUILD/'door_detail/before_source.json').read_text())
        delta=stats['result_triangles']-previous['triangles']
        door_titles=dict(door_north_left='Северная дверь слева',door_north_right='Северная дверь справа',
            door_south_left='Южная дверь слева',door_south_right='Южная дверь справа',
            door_oblique='Дверь под углом',door_companion='Механическая панель возле терминала')
        doc.append(f'<h2 id="doors">Дополнительная проработка дверей</h2><p>Приподнятая рамка, утопленное полотно, центральный щит, наклонные рёбра и замки теперь имеют собственную глубину. Обработаны все четыре входные двери и четыре родственных панели возле терминалов. Добавка относительно предыдущей модели стен: {delta:,} треугольников.</p>')
        doc.append('<p>В этом блоке «До дверей» — предыдущая модель с уже готовым рельефом стен. Сравнение показывает только дополнительную работу над дверями. <a href="door_validation.json">Проверка всех размещений</a>.</p><style>.door-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.door-grid section{margin:8px 0 28px}.door-grid h2{font-size:22px}@media(max-width:760px){.door-grid{grid-template-columns:1fr}}</style><div class="door-grid">')
        for i,shot in enumerate(preview['door_views']):
            name=shot['name'];doc.append(comparison(f'd{i}','door_detail/'+name,door_titles[name],'До дверей'))
        doc.append('</div><p>Контуры: <a href="door_detail/contours_14.png">входная дверь</a> · <a href="door_detail/contours_04.png">панель возле терминала</a>. Голубой — выступ, оранжевый — углубление.</p><h2>Вся комната: исходная геометрия FL_ND и новый рельеф</h2>')
    for i,name in enumerate(preview['views']):
        doc.append(comparison(f'v{i}',name,titles[name]))
    doc.append('<h2>Объём работы</h2><table><tr><th>Материал</th><th>Было</th><th>Стало</th><th>Заменено исходных граней</th></tr>')
    for g in stats['groups']:
        doc.append(f'<tr><td>Room-{g["material"]} ({g["group"]})</td><td>{g["source_triangles"]}</td><td>{g["result_triangles"]}</td><td>{g["replaced_source_triangles"]}</td></tr>')
    doc.append('</table><p>Область с вырезами триангулируется со всеми контурами одновременно. Вдоль исходных проёмов и границ материалов сохранён узкий исходный край, чтобы рельеф не разрывал стыки.</p>')
    doc.append('<p>Случайные повреждения и пятна краски не добавлялись. Несколько спорных больших контуров убраны после просмотра: граница освещения не должна становиться геометрическим вырезом.</p>')
    doc.append('<h2>Контуры на актуальных текстурах</h2><p>Ручная разметка, используемая генератором. Наложение на фактические UV-размещения и все повторения проверяется отдельно; неприменимые части атласа не получают геометрию.</p><div class="atlases">')
    for mat in sorted({f['material'] for f in features}):
        doc.append(f'<a href="contours_{mat}.png"><img loading="lazy" src="contours_{mat}.png" alt="Room-{mat}"></a>')
    doc.append('''</div><h2>Проверки</h2><ul><li>Готовый CMP перечитан; материалы, текстуры, суставы и механизмы сохранены.</li><li>Blender собран из геометрии экспортированного CMP и открыт повторно. Архив исходных поверхностей скрыт в viewport и render.</li><li>Проверено реальное смещение вершин по нормали и сохранение UV. Отчёты экспорта фиксируют исходники до установки; текущий статус установки указан вверху.</li></ul>
<p>RH, KU, LI и BR имеют общую конструкцию депо, но разные стеновые сетки и UV/материалы. Генератор геометрии, схема контуров и проверки пригодны для переноса; региональные привязки нужно составлять отдельно. Остальные регионы пока не изменены.</p>
<script>function applyClip(id,n){document.querySelector('#'+id+' .after').style.clipPath='inset(0 '+(100-n)+'% 0 0)'}function showWhole(id,n){document.querySelector('#'+id+' input').value=n;applyClip(id,n)}function setStyle(id,s){let e=document.getElementById(id);e.dataset.style=s;for(let m of ['before','after'])e.querySelector('.'+m).src=e.dataset.view+'_'+s+'_'+m+'.png'}</script></html>''')
    (BUILD/'index.html').write_text(''.join(doc),encoding='utf8')
    readme=f'''RH depot deck — modeled wall relief

Status: {'INSTALLED AND VERIFIED: '+installed['target'] if installed else 'Separate native CMP and editable Blender model; NOT INSTALLED.'}
Original geometry: FL_ND, {stats['original_triangles']} triangles.
Result: {stats['result_triangles']} triangles, {len(stats['groups'])} changed material groups.
Materials/textures: current FL_MOD, byte-preserved in native CMP.
Cranes, props, semantic part names and native joints unchanged.

Open index.html for actual before/after comparisons.
rh_depot_deck_relief.blend opens with the improved geometry visible.
Original replaced wall surfaces are in the disabled ARCHIVE collection.

Authoring: tools/base_interiors/depot_relief_features.py
Door profiles: tools/base_interiors/depot_door_features.py
Editable contour data: features.json (768px image coordinates).
To use manual edits to features.json, run the mesh step without regenerating features.
All depths are native world units. No existing relief mesh is reused.
Door comparisons use the preceding modeled walls, not the FL_ND baseline.
That compact reference is in door_detail/before_geometry.npz (two groups only).
Both original-wall and previous-door archives are disabled in viewport/render.

Rebuild from repository root:
python -B tools/base_interiors/depot_relief_features.py
python -B tools/blender_workspace.py --topic base_interiors --script tools/base_interiors/depot_relief_mesh.py
python -B tools/base_interiors/depot_relief_export.py
python -B tools/base_interiors/depot_relief_check.py
python -B tools/blender_workspace.py --topic base_interiors --script tools/base_interiors/depot_relief_preview.py
python -B tools/base_interiors/depot_relief_gallery.py

All DATA writes go through DataFolder. Installation is an explicit separate step.
After verification, the installed package CMP copy is removed; authoring files remain.
Export-private resources receive a fresh salt on every export.
See regional_transfer.json for original RH/KU/LI/BR inventory and transfer scope.
'''
    (BUILD/'README.txt').write_text(readme,encoding='utf8')
    parent=OUT/'index.html';old=parent.read_text(encoding='utf8')
    if 'modeled/index.html' not in old:
        old=old.replace('<h1>','<p style="padding:18px;background:#284638"><b>Готова новая модель с рельефом:</b> <a href="modeled/index.html">открыть CMP, Blender и сравнение до/после</a>.</p><h1>',1)
        parent.write_text(old,encoding='utf8')
    # The shared topic index is stable across room-specific prototypes.
    topic=Path(__file__).resolve().parents[2]/'out/base_interiors/index.html'
    old=topic.read_text(encoding='utf8');link='rheinland_batch/rh_depot_deck/rework/modeled/index.html'
    if link not in old:
        old=old.replace('<ul>','<ul><li><a href="'+link+'">Depot deck — новая смоделированная геометрия, CMP и Blender</a></li>',1)
        topic.write_text(old,encoding='utf8')
    print('GALLERY',BUILD/'index.html')


if __name__=='__main__':main()
