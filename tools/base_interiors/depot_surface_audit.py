"""Fresh depot wall inventory: FL_ND geometry, installed material artwork.

Analysis only. Never exports or installs a CMP, changes DATA, or reuses the old
relief contours. Coplanarity identifies surfaces, not painted feature semantics.
"""
import collections
import html
import io
import json
import re
import shutil
from pathlib import Path

import numpy as np

from native_common import ROOT, child, crc, get_parts, read_tree, sha, text
from rheinland_audit import transforms

OUT = ROOT / 'out/base_interiors/rheinland_batch/rh_depot_deck/rework'
ORIGINAL = Path('D:/Games/FL_ND/FL_ND/DATA/BASES/RHEINLAND/rh_depot_deck.cmp')
CURRENT = Path('D:/Games/FL_MOD/DATA/BASES/RHEINLAND/rh_depot_deck.cmp')


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def inspect_sources():
    raw = ORIGINAL.read_bytes()
    current_raw = CURRENT.read_bytes()
    root = read_tree(raw)[1][0]
    current_root = read_tree(current_raw)[1][0]
    parts = get_parts(root)
    current_parts = {p['name']: p for p in get_parts(current_root)}
    comparison = []
    for part in parts:
        other = current_parts[part['name']]
        identical = len(part['groups']) == len(other['groups']) and all(
            a['material'] == b['material'] and np.array_equal(a['corners'], b['corners'])
            for a, b in zip(part['groups'], other['groups']))
        comparison.append(dict(part=part['name'], original_triangles=sum(len(g['corners']) for g in part['groups']),
                               installed_triangles=sum(len(g['corners']) for g in other['groups']), identical=identical))
    # Existing mod artwork is intentionally retained; FL_ND supplies geometry.
    original_libraries = {n.name: child(n, 'VMeshData').blob for n in child(root, 'VMeshLibrary').children}
    current_libraries = {n.name: child(n, 'VMeshData').blob for n in child(current_root, 'VMeshLibrary').children}
    assert all(current_libraries.get(n) == b for n, b in original_libraries.items())
    assert all(q['identical'] for q in comparison if q['part'] not in ('Root', 'room'))
    write_json('sources.json', dict(original=str(ORIGINAL), original_sha256=sha(raw),
        installed=str(CURRENT), installed_sha256=sha(current_raw),
        geometry_source='FL_ND; unmodified native mesh libraries also retained in installed CMP',
        material_source='Current FL_MOD CMP; existing material and texture upgrades retained',
        analysis_only=True, old_contours_reused=False, parts=comparison,
        original_vmesh_payloads_still_identical=True))
    return root, current_root, parts


def materials(root):
    from PIL import Image
    textures = {}
    for t in child(root, 'Texture library').children:
        payload = next((x.blob for x in t.children if x.name in ('MIPS', 'MIP0')), None)
        if payload:
            filename = 'textures/' + sha(t.name.encode())[:12] + '.png'
            im = Image.open(io.BytesIO(payload))
            im.save(OUT / filename)
            textures[t.name.lower()] = dict(path=filename, sha256=sha(payload), size=list(im.size))
    result = {}
    for material in child(root, 'Material library').children:
        props = {n.name: n.blob for n in material.children}
        name = material.name
        number = re.search(r'room-(\d+)', name, re.I)
        result[str(crc(name))] = dict(name=name, number=number.group(1) if number else name,
            type=text(props.get('Type', b'')), textures={k: textures.get(text(v).lower()) for k, v in props.items() if k.endswith('_name')})
    return result


def inventory(root, parts, mats):
    trans, kinds = transforms(root)
    groups = []
    arrays = {}
    positions = []
    refs = []
    for part in parts:
        rotation, position = trans[part['name']]
        for gi, group in enumerate(part['groups']):
            key = f"{part['name']}_{gi:02d}"
            t = group['corners'].copy()
            t[:, :, :3] = t[:, :, :3] @ rotation + position
            t[:, :, 3:6] = t[:, :, 3:6] @ rotation
            arrays[key] = t
            groups.append(dict(key=key, part=part['name'], group=gi, material=str(group['material']),
                triangles=len(t), joint=kinds.get(part['name'], 'Root'), shape=list(t.shape)))
            if part['name'] in ('Root', 'room'):
                positions.extend(t[:, :, :3])
                refs.extend((key, ti) for ti in range(len(t)))
    np.savez_compressed(OUT / 'original_geometry.npz', **arrays)
    p = np.asarray(positions, dtype=float)
    cross = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    area = np.linalg.norm(cross, axis=1) * .5
    normals = cross / np.maximum(2 * area[:, None], 1e-20)
    # Use authored inward-facing normals only to orient geometric face normals.
    for i, (key, ti) in enumerate(refs):
        if normals[i] @ arrays[key][ti, :, 3:6].mean(0) < 0:
            normals[i] *= -1
    parents = list(range(len(p)))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    edge_owners = collections.defaultdict(list)
    for i, t in enumerate(p):
        if area[i] < 1e-10:
            continue
        for a, b in ((0, 1), (1, 2), (2, 0)):
            key = tuple(sorted((tuple(np.round(t[a], 4)), tuple(np.round(t[b], 4)))))
            for j in edge_owners[key]:
                if normals[i] @ normals[j] > .99999 and np.max(abs((p[j] - t[0]) @ normals[i])) < .0001:
                    parents[find(i)] = find(j)
            edge_owners[key].append(i)
    components = collections.defaultdict(list)
    for i in range(len(p)):
        if area[i] > 1e-10:
            components[find(i)].append(i)
    group_lookup = {g['key']: g for g in groups}
    patches = []
    for ids in components.values():
        a = float(area[ids].sum())
        normal = np.average(normals[ids], axis=0, weights=area[ids])
        normal /= np.linalg.norm(normal)
        surface = 'wall' if abs(normal[1]) < .35 else 'slope' if abs(normal[1]) < .85 else 'horizontal'
        center = np.average(p[ids].mean(1), axis=0, weights=area[ids])
        members = collections.defaultdict(list)
        for i in ids:
            key, ti = refs[i]
            members[key].append(ti)
        patches.append(dict(area=a, surface=surface, center=center.tolist(), normal=normal.tolist(),
            bounds=[p[ids].reshape(-1, 3).min(0).tolist(), p[ids].reshape(-1, 3).max(0).tolist()],
            triangles=len(ids), groups=dict(members),
            materials=sorted({group_lookup[k]['material'] for k in members})))
    patches.sort(key=lambda q: -q['area'])
    for i, patch in enumerate(patches):
        patch['id'] = f'P{i:03d}'
        patch['review_candidate'] = patch['surface'] != 'horizontal' and patch['area'] >= .5
    write_json('surfaces.json', dict(groups=groups, patches=patches, materials=mats,
        method='Connected coplanar geometric faces, across material groups; 0.0001 position and .99999 normal-dot tolerances.',
        limitation='Candidates only. Surface area and coplanarity do not identify relief, damage, or artistic importance.'))
    return groups, arrays, patches


def gallery(mats, groups, arrays, patches):
    from PIL import Image, ImageDraw
    cards = []
    for key, m in sorted(mats.items(), key=lambda item: item[1]['number']):
        used = [g for g in groups if g['material'] == key and g['part'] in ('Root', 'room')]
        if not used or not m['textures'].get('Dt_name'):
            continue
        tex = m['textures']['Dt_name']['path']
        # Diagnostic display transform only; native DDS data is never changed.
        im = Image.open(OUT / tex).convert('RGB').resize((768, 768))
        im = Image.fromarray(np.uint8(np.clip(np.asarray(im, float) / 255, 0, 1) ** .55 * 255))
        boosted = f'textures/review_{m["number"]}.jpg'
        im.save(OUT / boosted, quality=93)
        relevant = [p for p in patches if key in p['materials'] and p['review_candidate']]
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="768" height="768" viewBox="0 0 768 768"><image href="review_{m["number"]}.jpg" width="768" height="768"/>']
        for j, patch in enumerate(relevant):
            color = ['#ffb74a', '#71dfff', '#f6a4e7', '#b1f578', '#ffffff'][j % 5]
            samples = []
            for gk, indices in patch['groups'].items():
                if next(g for g in groups if g['key'] == gk)['material'] != key:
                    continue
                for t in arrays[gk][indices]:
                    if t.shape[-1] < 8:
                        continue
                    uv = t[:, 6:8]
                    # These atlases are nonrepeating. Do not fake tiled placements.
                    if np.any(uv < -.001) or np.any(uv > 1.001):
                        continue
                    xy = uv * 768
                    points = ' '.join(f'{x:.2f},{y:.2f}' for x, y in xy)
                    svg.append(f'<polygon points="{points}" fill="none" stroke="{color}" stroke-width="1.2"><title>{patch["id"]}, {patch["area"]:.2f} units²</title></polygon>')
                    samples.append(xy.mean(0))
            if samples:
                x, y = np.mean(samples, axis=0)
                svg.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="white" stroke="#111" stroke-width="3" paint-order="stroke" font-family="sans-serif" font-size="15">{patch["id"]}</text>')
        svg.append('</svg>')
        (OUT / f'textures/uv_{m["number"]}.svg').write_text(''.join(svg), encoding='utf8')
        cards.append((m, boosted, relevant))
    doc = ['''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Depot deck: новая ревизия поверхностей</title>
<style>body{background:#182029;color:#e6edf5;font:16px/1.5 system-ui;max-width:1550px;margin:auto;padding:24px}a{color:#8bd5ff}img{max-width:100%}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{border-top:1px solid #506274;margin-top:30px;padding-top:15px}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #506274;text-align:left}code{color:#b3e8fc}</style>
<h1>Рейнландский depot deck — новый разбор поверхностей</h1>
<p>Начало новой работы: исходная геометрия FL_ND, текущие текстуры FL_MOD. Старая разметка рельефа не используется. Установленный CMP не изменён.</p>
<p>Это инвентаризация, а не готовая модель. UV-линии показывают существующие треугольники плоских участков; они не являются контурами будущих вырезов. Номер P обозначает связный плоский участок, в том числе на стыке материалов.</p>
<p>Картинки осветлены одинаковым преобразованием x^0.55 для чтения рисунка. Исходные PNG и контрольные суммы текстур сохранены отдельно. Чёрные поля атласа, нарисованные тени и пятна не считаются отверстиями автоматически.</p>
<p><a href="sources.json">Источники и сравнение частей</a> · <a href="surfaces.json">Плоские участки и UV-привязка</a> · <a href="review_plan.json">Новый план</a> · <a href="depot_original_review.blend">Исходная сцена Blender</a></p>''']
    plan = json.loads((Path(__file__).parent / 'depot_rework_plan.json').read_text(encoding='utf8'))
    write_json('review_plan.json', plan)
    doc.append('<h2>Что показало сравнение</h2><ul>')
    for finding in plan['verified_findings']:
        doc.append('<li>' + html.escape(finding) + '</li>')
    doc.append('</ul><h2>Новый порядок работы</h2><p>Первые четыре зоны — приоритет первого прототипа. Ниже перечислены области работы, а не утверждённые точные контуры.</p><table><tr><th>Зона</th><th>Приоритет</th><th>Работа</th></tr>')
    for zone in plan['priorities']:
        doc.append(f'<tr><td>{zone["id"]}: {html.escape(zone["title"])}</td><td>{zone["stage"]}</td><td>{html.escape(zone["observed"])}<br><b>{html.escape("; ".join(zone["work"]))}</b></td></tr>')
    doc.append('</table><p><b>Повреждения:</b> ' + html.escape(plan['damage_policy']['review_status']) + '</p>')
    if (OUT / 'blend_review.json').exists():
        views = json.loads((OUT / 'blend_review.json').read_text(encoding='utf8'))['views']
        titles = dict(west_wall='Центральная панель под механизмами — W2',
            north_wall='Одна сторона комнаты — W1, W3, W4', south_wall='Противоположная сторона — W1, W3, W4',
            east_wall='Сторона с орлом: существующие объёмы и пустые проёмы',
            north_wide='Общий ракурс вдоль одной стороны', south_wide='Общий ракурс вдоль противоположной стороны')
        doc.append('<h2>Исходная геометрия: текстуры и нейтральный материал</h2><p>Обе картинки показывают один исходный меш FL_ND. Это не сравнение до/после улучшения. Диагностический свет, без игровых шейдеров и внешнего окружения. Все исходные объекты сохранены в кадре; видимость зависит от ракурса.</p>')
        for view in views:
            name = view['name']
            doc.append(f'<article><h3>{titles[name]}</h3><div class="pair"><a href="{name}_textured.png"><img loading="lazy" src="{name}_textured.png"></a><a href="{name}_clay.png"><img loading="lazy" src="{name}_clay.png"></a></div></article>')
    doc.append('<h2>Все архитектурные материалы и их UV-размещения</h2>')
    for m, boosted, relevant in cards:
        doc.append(f'<article id="m{m["number"]}"><h2>{html.escape(m["name"])}</h2><div class="pair"><img src="{boosted}"><img src="textures/uv_{m["number"]}.svg"></div><p>Плоские участки стен/наклонных опор: ')
        doc.append(', '.join(f'{p["id"]} ({p["area"]:.1f}, {p["surface"]})' for p in relevant) or 'нет кандидатов площадью ≥ 0,5')
        doc.append('</p></article>')
    doc.append('</html>')
    (OUT / 'index.html').write_text(''.join(doc), encoding='utf8')
    board = Image.new('RGB', (1200, ((len(cards) + 3) // 4) * 326), (24, 32, 41))
    draw = ImageDraw.Draw(board)
    for i, (m, image, _) in enumerate(cards):
        x, y = i % 4 * 300, i // 4 * 326
        board.paste(Image.open(OUT / image).resize((300, 300)), (x, y))
        draw.text((x + 8, y + 303), 'Room-' + m['number'], fill='white')
    board.save(OUT / 'material_inventory.jpg', quality=94)
    topic = ROOT / 'out/base_interiors/index.html'
    link = 'rheinland_batch/rh_depot_deck/rework/index.html'
    if topic.exists():
        previous = topic.read_text(encoding='utf8')
        if link not in previous:
            previous = previous.replace('<ul>', '<ul><li><a href="' + link + '">Depot deck — новая ревизия с исходной геометрии FL_ND, анализ стен</a></li>', 1)
            topic.write_text(previous, encoding='utf8')


def main():
    if shutil.disk_usage(ROOT).free < 2 * 1024**3:
        raise RuntimeError('Not enough free D: space for review artifacts')
    (OUT / 'textures').mkdir(parents=True, exist_ok=True)
    original, current, parts = inspect_sources()
    mats = materials(current)
    groups, arrays, patches = inventory(original, parts, mats)
    gallery(mats, groups, arrays, patches)
    print(json.dumps(dict(output=str(OUT), original_triangles=sum(g['triangles'] for g in groups),
        planar_patches=len(patches), review_candidates=sum(p['review_candidate'] for p in patches),
        original_and_installed_unchanged=True)))


if __name__ == '__main__':
    main()
