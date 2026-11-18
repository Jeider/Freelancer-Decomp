"""Read-only installed pirate player-ship reference packets; no game or Blender."""
import collections
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import full_ship_audit as full
import ship_motion_preview as motion
import style_audit as source
from rh_redesign_paths import TOPIC

OUT = TOPIC / 'pirate_art'
SCRIPT = 'sc_extend wing'
FONT = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
SMALL = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 15)
BG = (24, 29, 37)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dimensions(scene):
    points = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in scene])
    return (points.max(0) - points.min(0)).tolist()


def render(scene, mats, camera, size=440):
    points = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in scene])
    center = (points.min(0) + points.max(0)) / 2
    radius = np.linalg.norm(points - center, axis=1).max()
    return source.render(scene, mats, center, radius, camera, size, 'texture')


def main():
    free = shutil.disk_usage(OUT.anchor).free
    if free < 1024**3:
        raise RuntimeError('Less than 1 GiB free; refusing reference render batch')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'ships').mkdir(exist_ok=True)
    sources = [p for _, v in source.sections(source.GAME / 'bin/freelancer.ini')
               for p in v.get('ships', [])]
    aliases = {}
    for ini in sources:
        for section, values in source.sections(source.DATA / ini):
            if section == 'ship':
                aliases[values['nickname'][0].lower()] = dict(values, source=ini)
    candidates = {n: v for n, v in aliases.items() if n.endswith('_pir')
                  and v.get('ship_class', [''])[0] in ('0', '1', '2')}
    grouped, deferred = {}, []
    for name, v in candidates.items():
        model = v['da_archetype'][0].replace('\\', '/').lower()
        family = model.split('/')[1]
        if family in ('civilian', 'corsair') or name == 'ge_csv_pir':
            deferred.append(dict(alias=name, model=model, reason='future civilian/Corsair visual'))
            continue
        materials = [x.replace('\\', '/').lower() for x in v.get('material_library', [])]
        key = (model, tuple(materials))
        row = grouped.setdefault(key, dict(model=model, family=family, materials=materials,
                                          aliases=[], classes=[], ini=v['source'], cockpit_by_alias={}))
        row['aliases'].append(name)
        row['classes'].extend(v.get('ship_class', []))
        row['cockpit_by_alias'][name] = {k: value for k, value in v.items()
                                       if k in ('cockpit', 'pilot_mesh') or k.startswith('camera_')}
    rows, missing, thumbs = [], [], []
    for row in sorted(grouped.values(), key=lambda r: (r['family'], r['model'])):
        path = source.DATA / row['model']
        if not path.is_file():
            missing.append(dict(row, reason='referenced CMP does not exist'))
            print('MISSING', row['aliases'], flush=True)
            continue
        scene, mats, stats = source.load(row)
        _, nodes = source.mesh.read_tree(path.read_bytes())
        flat = {p.lower(): n.blob for p, n in source.mesh.walk(nodes)}
        constructs = full.constructs(flat)
        channels = full.channels(flat, constructs)
        record = dict(path=row['model'], constructs=constructs, channels=channels)
        wing = [c for c in channels if c['script'] == SCRIPT]
        invalid = [c for c in wing if not c['native_size_valid'] or not c['bound_joint']
                   or c.get('parent_mismatch') or not c['finite'] or not c['monotonic_times']]
        if invalid:
            raise RuntimeError('Invalid wing channels: ' + row['model'])
        duration = max((c['duration'] for c in wing), default=0)
        poses = [motion.scene_at(record, scene, duration * t, SCRIPT)
                 for t in (0, .25, .5, .75, 1)] if wing else [scene] * 5
        flight, folded = poses[0], poses[-1]
        launch = [c for c in channels if c['script'] == 'sc_launch extend']
        delta = None
        if launch and wing:
            end = motion.scene_at(record, scene, max(c['duration'] for c in launch), 'sc_launch extend')
            delta = max(float(np.abs(a['corners'][..., :3] - b['corners'][..., :3]).max())
                        for a, b in zip(end, flight))
        row.update(sha256=sha(path), triangles=stats['triangles'],
                   material_info=stats['material_info'],
                   material_sources=[dict(path=p, sha256=sha(source.DATA / p)) for p in row['materials']],
                   constructs=constructs, wing_channels=wing, wing_duration=duration,
                   launch_to_flight_max_coordinate_delta=delta,
                   phase_dimensions_xyz=[dimensions(p) for p in poses],
                   pose_basis='wing t=0 flight, t=end dock target per wing_anim.h; not an in-game observation')
        cockpit_paths = sorted({p.replace('\\', '/').lower() for v in row['cockpit_by_alias'].values()
                                for p in v.get('cockpit', [])})
        row['cockpit_sources'] = [dict(path=p, sha256=sha(source.DATA / p)
                                     if (source.DATA / p).exists() else None) for p in cockpit_paths]
        assert row['sha256'] == stats['sha256'], 'Source changed during read'
        key = row['aliases'][0]
        target = OUT / 'ships' / key
        target.mkdir(exist_ok=True)
        panel = Image.new('RGB', (1320, 1020), BG)
        draw = ImageDraw.Draw(panel)
        flight_panel = Image.new('RGB', (880, 1000), BG)
        flight_draw = ImageDraw.Draw(flight_panel)
        flight_draw.text((12, 8), key + ' / FLIGHT ONLY', font=FONT, fill='white')
        draw.text((12, 8), ' / '.join(row['aliases']), font=FONT, fill='white')
        shots = [(flight, (1, .7, -1.3), 'FLIGHT / front 3-4'),
                 (flight, (-1, .55, 1.3), 'FLIGHT / rear 3-4'),
                 (flight, (.0001, 1, .0001), 'FLIGHT / top'),
                 (flight, (1, 0, 0), 'FLIGHT / side'),
                 (folded, (1, .7, -1.3), 'DOCK TARGET / front 3-4'),
                 (folded, (.0001, 1, .0001), 'DOCK TARGET / top')]
        for index, (pose, camera, label) in enumerate(shots):
            x, y = index % 3 * 440, 40 + index // 3 * 480
            im = render(pose, mats, camera)
            panel.paste(im, (x, y + 26))
            draw.text((x + 8, y), label if wing else label + ' [static]', font=SMALL, fill='white')
            if index == 0:
                im.save(target / 'flight.png')
                thumbs.append((row, im))
            if index < 4:
                fx, fy = index % 2 * 440, 40 + index // 2 * 480
                flight_panel.paste(im, (fx, fy + 26))
                flight_draw.text((fx + 8, fy), label, font=SMALL, fill='white')
        draw.text((12, 1000), 'Offline CMP reference; each view fitted independently; no glass/envmap emulation.',
                  font=SMALL, fill=(185, 195, 206))
        panel.save(target / 'reference.jpg', quality=93)
        flight_panel.save(target / 'flight_reference.jpg', quality=93)
        textures = {m['texture']: m['image'] for k, m in mats.items()
                    if k in {g['material'] for g in scene} and m['image'] is not None
                    and not m['texture'].lower().startswith('metal')}
        atlas = Image.new('RGB', (384 * 2, max(1, (len(textures) + 1) // 2) * 420), BG)
        ad = ImageDraw.Draw(atlas)
        for i, (name, im) in enumerate(sorted(textures.items())):
            x, y = i % 2 * 384, i // 2 * 420
            ad.text((x + 6, y + 3), name, font=SMALL, fill='white')
            im = im.copy()
            im.thumbnail((376, 376))
            atlas.paste(im, (x + 4, y + 32))
        atlas.save(target / 'materials.jpg', quality=94)
        row['reference'] = f'ships/{key}/reference.jpg'
        row['materials_reference'] = f'ships/{key}/materials.jpg'
        (target / 'source.json').write_text(json.dumps(row, indent=2), encoding='utf8')
        rows.append(row)
        print(key, len(wing), 'wing tracks; launch delta', delta, flush=True)
    contacts = []
    for start in range(0, len(thumbs), 8):
        subset = thumbs[start:start + 8]
        sheet = Image.new('RGB', (440 * 4, 490 * 2), BG)
        d = ImageDraw.Draw(sheet)
        for i, (r, im) in enumerate(subset):
            x, y = i % 4 * 440, i // 4 * 490
            sheet.paste(im, (x, y + 45))
            d.text((x + 8, y + 5), r['aliases'][0], font=FONT, fill='white')
            d.text((x + 8, y + 28), 'FLIGHT / ' + r['family'], font=SMALL, fill=(190, 200, 210))
        name = f'contact_{start // 8 + 1:02}.jpg'
        sheet.save(OUT / name, quality=93)
        contacts.append(name)
    manifest = dict(scope='fighters/freighters only; civilian and actual Corsair deferred',
                    configuration=dict(path=(source.GAME / 'bin/freelancer.ini').as_posix(),
                                       sha256=sha(source.GAME / 'bin/freelancer.ini')),
                    disk_free_before=free, candidates=len(candidates), rows=rows,
                    missing=missing, deferred=deferred, contacts=contacts,
                    sources=[dict(path=s, sha256=sha(source.DATA / s)) for s in sources])
    (OUT / 'inventory.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    lines = ['# Текущие пиратские истребители и грузовики', '',
             'Срез активных ship INI из `D:/Games/FL_MOD/bin/freelancer.ini`. '
             'Наличие архетипа не доказывает продажу корабля на рынке.', '',
             f'В INI: {len(candidates)} архетипов `_pir` классов 0/1/2. '
             f'В текущем исследовании: {len(rows)} существующих моделей; '
             f'{len(missing)} ссылка без CMP. Отложено: {len(deferred)} архетипов.', '',
             '[План генерации](../../../docs/ru/ship_design/pirate_art_workflow.md). '
             '[Данные и SHA-256](inventory.json).', '',
             'Все изображения — офлайн-рендеры. Полёт: начало wing script; '
             'цель складывания: конец. Контроллер также умеет складывание на круизе. '
             'Это не проверка фактической комплектации каждого loadout и не тест коллизий.', '',
             '| Семейство по CMP | Архетипы | Класс | Каналы wing | Текстуры / ракурсы |',
             '|---|---|---|---:|---|']
    for r in rows:
        kind = {'0': 'лёгкий', '1': 'тяжёлый', '2': 'грузовой'}[r['classes'][0]]
        lines.append(f"| {r['family']} | {', '.join('`'+x+'`' for x in r['aliases'])} | {kind} | "
                     f"{len(r['wing_channels'])} | [виды]({r['reference']}) / [материалы]({r['materials_reference']}) |")
    lines += ['', '## Обзор полётных силуэтов', '']
    lines += [f'![Полётные позы {i+1}]({name})' for i, name in enumerate(contacts)]
    lines += ['', '## Отсутствующие источники', '']
    lines += [f"- `{', '.join(r['aliases'])}` → `{r['model']}`: файла нет; облик не придуман." for r in missing]
    lines += ['', '## Отложено по указанию пользователя', '']
    lines += [f"- `{r['alias']}` → `{r['model']}`." for r in deferred]
    (OUT / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    print('COMPLETE', len(rows), 'models;', len(missing), 'missing;', len(deferred), 'deferred')


if __name__ == '__main__':
    main()
