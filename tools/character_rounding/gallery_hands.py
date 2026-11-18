"""Compact local review index for the ordinary hand sources."""
import gzip
import html
import json
import sys
from hands import OUT,NAMES
if '--gloves' in sys.argv:
    from gloves import OUT,NAMES

parts=['<!doctype html><meta charset="utf-8"><title>Кисти персонажей</title><style>body{font:16px system-ui;background:#171b20;color:#e8edf3;max-width:1200px;margin:32px auto}img{width:100%;border-radius:8px}a{color:#85caff}section{margin:45px 0}h2{margin-bottom:6px}details{margin:12px 0}</style><h1>Обычные кисти персонажей</h1><p>Слева — исходная модель (LOD 1), справа — новая (LOD 0). Офлайн-просмотр; перчатки будут перенесены отдельно.</p>']
for name in NAMES:
    d=json.loads(gzip.decompress((OUT/name/'edited.json.gz').read_bytes()))
    parts.append(f'<section><h2>{html.escape(name)}</h2><p>{d["authoring"]["triangles"]} треугольников · <a href="{name}/hand.blend">Blender: сетка и скелет</a></p><img src="{name}/compare_texture.png">')
    for label,title in [('rest','Без текстуры'),('fist','Кулак'),('grip','Хват'),('point','Указание')]:
        parts.append(f'<details><summary>{title}</summary><img loading="lazy" src="{name}/compare_{label}.png"></details>')
    parts.append('</section>')
page=''.join(parts)
if '--gloves' in sys.argv:
    page=page.replace('Обычные кисти персонажей','Перчатки персонажей').replace('перчатки будут перенесены отдельно.','16 вариантов; отдельные MAT-исходники: br, li, rh, yel.')
    page=page.replace('</h1>','</h1><p>'+''.join(f'<a href="materials/{f}_gloves.mat">{f.upper()} MAT</a> &nbsp; ' for f in ('br','li','rh','yel'))+'</p>',1)
(OUT/'index.html').write_text(page,encoding='utf-8')
print(OUT/'index.html')
