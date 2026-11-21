"""Validate the saved static B04/03 review and write its local gallery."""
from collections import defaultdict
import hashlib
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/ship_design/bw_family/elite/prototypes/b04_03'
VIEWS = [
    ('form_rear_34.png', 'Сзади 3/4 — главный ракурс'),
    ('form_upper_rear_34.png', 'Верхний корпус крупно'),
    ('form_front_34.png', 'Спереди 3/4'),
    ('form_rear.png', 'Прямой задний вид'),
    ('form_top.png', 'Сверху'),
    ('form_side.png', 'Сбоку'),
    ('form_belly.png', 'Снизу'),
    ('form_hold.png', 'Локальный трюм, створки временно скрыты'),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf8'))


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def validate():
    manifest = read('manifest.json')
    geometry = read('geometry.json')
    validation = read('blender_validation.json')
    blend = read('blend_readback.json')
    for path, expected in manifest['sources'].items():
        assert sha(path) == expected, f'Source changed: {path}'
    assert sha(OUT / 'geometry.json') == validation['geometry_sha256']
    assert sha(manifest['export']['path']) == manifest['export']['sha256']
    assert blend['reopened'] and sha(blend['path']) == blend['sha256']
    assert not geometry['motion'] and not manifest['export']['animated']
    assert validation['render_backface_culling']
    assert all(p['hit'] and p['hit'][3] < -.9 for p in validation['cargo_inward_ray_hits'])
    triangle_count = sum(len(g['corners']) for obj in geometry['objects'] for g in obj['groups'])
    assert triangle_count == manifest['total_triangles']
    audit = []
    for obj in geometry['objects']:
        if obj['category'] in ('Immutable original cabin', 'Native rig helpers'):
            continue
        edges = defaultdict(list)
        area_min = float('inf')
        for group in obj['groups']:
            data = np.array(group['corners'])
            assert np.isfinite(data).all(), obj['name']
            for triangle in data:
                verts = [tuple(np.round(v[:3], 5)) for v in triangle]
                area_min = min(area_min, float(np.linalg.norm(np.cross(
                    triangle[1, :3] - triangle[0, :3], triangle[2, :3] - triangle[0, :3])) / 2))
                for a, b in zip(verts, verts[1:] + verts[:1]):
                    edges[tuple(sorted([a, b]))].append((a, b))
        item = dict(name=obj['name'], open_edges=sum(len(v) == 1 for v in edges.values()),
                    orientation_mismatches=sum(len(v) == 2 and v[0] == v[1] for v in edges.values()),
                    nonmanifold_edges=sum(len(v) > 2 for v in edges.values()), minimum_triangle_area=area_min)
        assert item['orientation_mismatches'] == item['nonmanifold_edges'] == 0, item
        assert area_min > 1e-10, item
        audit.append(item)
    dump('topology_audit.json', audit)
    for filename, _ in VIEWS:
        with Image.open(OUT / filename) as im:
            assert im.size == (1600, 1200), filename
            im.verify()
    artifacts = ['geometry.json', 'manifest.json', 'bw_pir_elite_b04_review_open.cmp',
                 'bw_pir_elite_b04.blend', 'blender_validation.json', 'blend_readback.json',
                 'topology_audit.json'] + [v[0] for v in VIEWS]
    report = dict(status='passed_for_static_shape_review', triangles=triangle_count,
                  source_hashes_unchanged=True, render_geometry_hash_matches=True,
                  saved_blend_reopened_and_hash_matches=True, animation_deferred=True,
                  limitations=['Visual acceptance pending', 'UVs provisional', 'Hardpoints not fitted',
                               'Separate cabin transition skins have boundary edges; not a single welded mesh'],
                  artifacts={n: sha(OUT / n) for n in artifacts})
    dump('review_validation.json', report)
    return report


def main():
    validate()
    figures = '\n'.join(f'<figure><a href="{f}"><img loading="lazy" src="{f}" alt="{html.escape(c)}"></a>'
                        f'<figcaption>{html.escape(c)}</figcaption></figure>' for f, c in VIEWS[1:])
    downloads = '\n'.join(f'<li><a href="{n}">{html.escape((OUT / n).as_posix())}</a></li>'
                          for n in ['bw_pir_elite_b04.blend', 'bw_pir_elite_b04_review_open.cmp', 'README.md'])
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>B04 ELITE — форма 03</title>
<style>
:root{color-scheme:dark}body{margin:0;background:#1b2126;color:#e3e7e9;font:16px/1.5 system-ui,sans-serif}
main{max-width:1400px;margin:auto;padding:26px}h1{font-size:30px;margin:0}h2{font-size:22px;margin:30px 0 12px}
p{max-width:1000px}a{color:#b8d9ec}figure{margin:0;background:#272e34;border:1px solid #414b53;border-radius:6px;overflow:hidden}
img{display:block;width:100%;height:auto}figcaption{padding:9px 14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.compare{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:center}li{overflow-wrap:anywhere;margin:8px 0}
.muted{color:#b2bdc5}.tag{color:#e8bb84}details{margin:24px 0}summary{cursor:pointer}
@media(max-width:800px){main{padding:14px}.grid,.compare{grid-template-columns:1fr}}
</style><main>
<div class="tag">BW PIRATE ELITE · B04/03 · 19 ноября 2026</div>
<h1>Угловатый верхний корпус. Узкая пирамидальная стойка.</h1>
<p>Главный ориентир — ELITE REAR / REAR 3/4 из B04_VIEWS_B, затем сверка с B04_VIEWS_A.
Смоделированы наклонные кормовые решётки, обрамление утопленного сопла, ступенчатые
плечи и каналы с обеих сторон крыльев. Кабина исходная.</p>
<p class="muted">Статичный прототип формы · 4436 треугольников · условная окраска Blender ·
UV CMP предварительные. Анимации отложены. Форма ожидает вашего просмотра.</p>
<figure><a href="form_rear_34.png"><img src="form_rear_34.png" alt="B04/03, задний ракурс"></a>
<figcaption>Новая форма — сзади 3/4. Все изображения открываются в полном размере.</figcaption></figure>
<h2>Сверка с выбранным задним артом</h2>
<div class="compare">
<figure><a href="../../../concepts/round_04/bw_family_B04_VIEWS_B_sheet.png">
<img src="../../references/b04_shape_review/rear_perspective.png" alt="Фрагмент ELITE, B04_VIEWS_B">
</a><figcaption>ELITE — фрагмент исходного B04_VIEWS_B. Нажать для полного листа.</figcaption></figure>
<figure><a href="form_rear.png"><img src="form_rear.png" alt="Новая модель сзади">
</a><figcaption>Модель сзади. Нижний узел намеренно легче арта по вашему указанию.</figcaption></figure>
</div>
<p><a href="../../../concepts/round_04/bw_family_B04_VIEWS_A_sheet.png">Полный B04_VIEWS_A — перед, бок, верх</a> ·
<a href="../../../concepts/round_04/bw_family_B04_VIEWS_B_sheet.png">Полный B04_VIEWS_B — зад и днище</a></p>
<h2>Остальные виды</h2><div class="grid">FIGURES</div>
<h2>Файлы</h2><ul>DOWNLOADS</ul>
<p>Blender сохранён в статичной раскрытой форме. CMP использует внешние исходные BW-материалы.
Родные HP сохранены как исходные данные, но ещё не подогнаны к новой форме.</p>
<details><summary>Проверка и история</summary><p>
<a href="review_validation.json">Комплектность и хеши</a> · <a href="topology_audit.json">Топология</a> ·
<a href="blender_validation.json">Геометрия и полость трюма</a> · <a href="manifest.json">Источники и соль экспорта</a> ·
<a href="../b04_02/index.html">Предыдущая форма 02</a></p></details></main></html>'''
    (OUT / 'index.html').write_text(page.replace('FIGURES', figures).replace('DOWNLOADS', downloads), encoding='utf8')
    print(json.dumps(dict(gallery=(OUT / 'index.html').as_posix(), status='passed_for_static_shape_review',
                          triangles=read('manifest.json')['total_triangles'], renders=len(VIEWS))))


if __name__ == '__main__':
    main()
