"""Matched comparisons for the three explicitly approved hero-body exceptions."""
import html
import json
from hero_bodies import OUT, TARGETS

reports=[json.loads((OUT/name/'report.json').read_text()) for name in TARGETS]
receipt=json.loads((OUT/'installed.json').read_text()) if (OUT/'installed.json').exists() else {}
installed={r['name']:r['after_sha256'] for r in receipt.get('files',[])}
ready=all(installed.get(r['name'])==r['output_sha256'] for r in reports)
parts=['<!doctype html><meta charset="utf-8"><title>Хетчер, Трент и Journeyman — контуры</title>',
       '<style>body{margin:32px auto;max-width:1200px;padding:0 20px;background:#20252b;color:#edf0f4;font:17px system-ui}a{color:#9bcfff}article{margin:36px 0;padding:20px;background:#2e343b;border-radius:12px}img{width:100%;height:auto}summary{cursor:pointer}small{color:#b6c2cc}</style>',
       '<h1>Хетчер, Трент и Journeyman</h1>',
       '<p>'+('Установлено и проверено.' if ready else 'Подготовлено к установке.')+' Каждому телу добавлено 2000 треугольников в разрешённых областях.</p>',
       '<p>Слева — ранее принятая модель, справа — новое уточнение контуров. У Хетчер основной бюджет направлен на верхние кромки жилетки и воротник. У двух мужских тел приоритет — концы рукавов.</p>',
       '<p>Сравнения выполнены вне игры. UV, веса костей, число материалов и остальные LOD сохранены. В blend есть редактируемые меши с группами весов, без анимационного рига; предыдущая модель скрыта в просмотре и рендере. Текстуры связаны с общими экспортами на D:.</p>',
       '<p><a href="validation.json">Проверка DFM</a> · <a href="blend_validation.json">Проверка Blender</a> · <a href="../bracer_starts/index.html">Наручи</a> · <a href="../contours_2k/index.html">Основной набор</a></p>']
for report in reports:
    name=report['name'];primary='upper_edges' if name=='li_hatcher_body' else 'cuff'
    parts.append(f'<article><h2>{html.escape(name)}</h2><p>{report["triangles_before"]} → {report["triangles_after"]} треугольников (+2000). '
                 f'<a href="{name}/hero_body.blend">Редактируемый Blender</a> · <a href="{name}/report.json">Отчёт</a></p>')
    for view in (primary,primary+'_clay'):
        parts.append(f'<a href="{name}/{view}.png"><img loading="lazy" alt="{view}: до и после" src="{name}/{view}.png"></a>')
    parts.append('<details><summary>Жилетка / куртка и общий вид</summary>')
    for view in (['upper_back','vest','front','back'] if name=='li_hatcher_body' else ['vest','front','back']):
        parts.append(f'<img loading="lazy" alt="{view}: до и после" src="{name}/{view}.png">')
    parts.append('</details></article>')
(OUT/'index.html').write_text('\n'.join(parts),encoding='utf-8')
(OUT/'README.txt').write_text('Хетчер, Трент и Journeyman: index.html\n'
    'Генератор: tools/character_rounding/hero_bodies.py\n'
    'before.json.gz — принятая установленная геометрия; after.json.gz — новая.\n'
    'hero_body.blend содержит редактируемый результат с UV, нормалями и весами, а также скрытый предыдущий вариант.\n'
    'Установка через install_contours.py --package hero_bodies --apply и Pythonlancer DataFolder.\n'
    'Игра не запускалась; синтетическая проверка весов не заменяет просмотр игровых анимаций.\n',encoding='utf-8')
print('Gallery:',OUT/'index.html','installed:',ready)
