"""Reviewable upper-bracer comparisons; no duplicate texture/model packages."""
import html
import json
from bracer_starts import OUT, TARGETS

reports=[json.loads((OUT/name/'report.json').read_text()) for name in TARGETS]
reports.sort(key=lambda r:(r['name']!='li_hatcher_body',r['name']))
receipt=json.loads((OUT/'installed.json').read_text()) if (OUT/'installed.json').exists() else {}
installed={r['name']:r['after_sha256'] for r in receipt.get('files',[])}
ready=all(installed.get(r['name'])==r['output_sha256'] for r in reports)
parts=['<!doctype html><meta charset="utf-8"><title>Начала наручей</title>',
       '<style>body{margin:32px auto;max-width:1200px;padding:0 20px;background:#20252b;color:#edf0f4;font:17px system-ui}a{color:#9bcfff}article{margin:36px 0;padding:20px;background:#2e343b;border-radius:12px}img{width:100%;height:auto}summary{cursor:pointer}small{color:#b6c2cc}</style>',
       '<h1>Верхние края наручей</h1>',
       f'<p>{len(reports)} моделей. '+('Установлено и проверено.' if ready else 'Подготовлено к установке.')+'</p>',
       '<p>Слева — принятый вариант contours_2k, справа — правка начала наруча. '
       'Не более +100 треугольников на тело суммарно на обе руки; абсолютный максимум 2100. '
       'Форма скошенных краёв сохранена. Обычные рукава без такого края не требуют этой правки.</p>',
       '<p>Это офлайн-сравнения. Игра не запускалась; игровые анимации не проверялись. '
       'В blend сохранены UV, нормали и группы весов костей; анимационного рига нет. '
       'Предыдущая модель скрыта в просмотре и рендере. Текстуры связаны с общими экспортами.</p>',
       '<p><a href="../contours_2k/index.html">Полный базовый набор</a> · '
       '<a href="validation.json">Проверка DFM</a> · <a href="blend_validation.json">Проверка blend</a></p>']
for r in reports:
    name=r['name'];delta=r['triangles_after']-r['triangles_before'];label=html.escape(name)
    parts.append(f'<article><h2>{label}</h2><p>{r["triangles_before"]} → {r["triangles_after"]} треугольников ({delta:+d}). '
        f'<a href="{name}/contours_2k.blend">Blender</a> · <a href="{name}/report.json">Отчёт</a></p>'
        f'<a href="{name}/bracer_start.png"><img loading="lazy" src="{name}/bracer_start.png"></a>'
        f'<details><summary>Наруч целиком, общий вид спереди и сзади</summary>'
        f'<img loading="lazy" src="{name}/cuff.png"><img loading="lazy" src="{name}/front.png"><img loading="lazy" src="{name}/back.png"></details></article>')
(OUT/'index.html').write_text('\n'.join(parts),encoding='utf-8')
(OUT/'README.txt').write_text('Начала наручей: index.html\n'
    'Генератор: tools/character_rounding/bracer_starts.py\n'
    'Основа before.json.gz — установленный contours_2k; after.json.gz — новая геометрия.\n'
    'contours_2k.blend в каждой папке содержит редактируемую новую модель и скрытый предыдущий вариант.\n'
    'Лимит прироста +100 треугольников на тело, суммарно на обе руки; максимум 2100.\n'
    'Веса, UV и остальные LOD сохранены. Игра и игровые анимации не запускались.\n'
    'При установке только Mesh0 переносится через Pythonlancer DataFolder; после проверки временные бинарные патчи удаляются.\n',encoding='utf-8')
print('Gallery:',OUT/'index.html','installed:',ready)
