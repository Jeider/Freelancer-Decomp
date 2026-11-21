"""Offline BH family study and freighter reference audit; never writes game data."""
import hashlib
import json
import re
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import bw_family_audit as layout

a = layout.a
OUT = layout.TOPIC / 'bh_family'
SHIPS = [('fighter', 'bh_fighter'), ('elite', 'bh_elite'), ('vheavy_fighter', 'bh_elite2')]
DONORS = [('references/li_freighter', 'li_freighter'), ('references/bw_freighter', 'bw_freighter')]
CAMS = [((1, .55, -1.4), 'FRONT 3/4'), ((-1, .55, 1.3), 'REAR 3/4'),
        ((1, 0, 0), 'SIDE'), ((0, 1, .000001), 'TOP'),
        ((0, 0, -1), 'FRONT'), ((0, 0, 1), 'REAR')]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    layout.write_json(path, value)


def points(scene):
    return np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in scene])


def texture_sheet(mats, path, title, used=None):
    textures = {}
    for mid, mat in mats.items():
        if used is not None and mid not in used:
            continue
        if mat['image'] is not None and not mat['texture'].startswith('metal'):
            textures[mat['texture']] = mat['image']
    if not textures:
        return
    width, step = 380, 420
    im = Image.new('RGB', (3*width, ((len(textures)+2)//3)*step+50), a.BG)
    d = ImageDraw.Draw(im)
    d.text((12, 10), title, font=a.FONT, fill='white')
    for i, (name, tex) in enumerate(sorted(textures.items())):
        x, y = i % 3 * width, i // 3 * step + 50
        d.text((x+10, y), name, font=a.SMALL, fill='white')
        tile = tex.copy()
        tile.thumbnail((360, 370))
        im.paste(tile, (x+10, y+30))
    im.save(path, quality=96)


def write_gallery(records):
    rows, cards = [], []
    for key, alias in SHIPS:
        r = records[key]
        dims = [' × '.join(f'{x:.2f}' for x in r['phase_bounds'][i]['dimensions']) for i in (0, -1)]
        engines = sum(bool(re.fullmatch(r'hpengine\d+', p['name'])) for p in r['hardpoints'])
        rows.append(f'<tr><td>{alias}</td><td>{dims[0]}</td><td>{dims[1]}</td><td>{engines}</td></tr>')
        links = ' · '.join(f'<a href="{key}/{name}">{label}</a>' for name, label in [
            ('native_shape.jpg', 'Чистая форма'), ('cockpit_reference.jpg', 'Кабина'),
            ('native_wing_motion.jpg', 'Складывание'), ('native_baydoor_motion.jpg', 'Трюм'),
            ('source_audit.json', 'Исходник и численные данные')])
        cards.append(f'<article><h2>{alias}</h2><a href="{key}/native_flight.jpg"><img loading="lazy" '
                     f'src="{key}/native_flight.jpg" alt="{alias}: шесть полётных видов"></a><p>{links}</p></article>')
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BH family — исследование обычного грузовика</title>
<style>body{max-width:1450px;margin:auto;padding:30px;background:#181d25;color:#e2e8ed;font:17px/1.6 system-ui}
a{color:#a0cbd1}h1{font-size:32px}h2{font-size:24px}p{max-width:1100px}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
article,section{background:#222b34;padding:18px;margin:20px 0;border-radius:8px}img{max-width:100%;height:auto;display:block}
.cards p{font-size:14px}.wide{max-width:1100px}table{border-collapse:collapse;width:100%;font-size:16px}th,td{padding:12px;border-bottom:1px solid #495660;text-align:left}
.note{color:#aab8c2}@media(max-width:900px){.cards{grid-template-columns:1fr}body{padding:15px}table{font-size:13px}}</style>
<h1>BH family → обычный грузовик</h1><p>Исследование трёх действующих BH. Новый корабль должен продолжить их серийную конструкцию:
неизменные остекление и рама, угловатые плоскости и механические сопряжения. Компоновка нового грузовика развивается от li_freighter.</p>
<p><a href="README.md">Полный разбор</a> · <a href="freighter/BRIEF.md">Предложение для грузовика</a> · <a href="manifest.json">Источники и проверка</a></p>
<p><a href="concepts/round_03/index.html">20 рыбных компоновок — BHF11–BHF30</a> · <a href="concepts/round_03/prompts.json">Точные промпты</a> · <a href="concepts/round_01/index.html">Первая серия: слишком жёсткая привязка к кабине</a></p>
<p><strong>BHF20 — первоначальный выбор; BHF29 — альтернатива. Распределение обычной/пиратской версии не выбрано.</strong> <a href="freighter/SELECTED_CONCEPT.md">Выбранный арт и условия передачи</a></p>
<section><h2>Семейство в одинаковом масштабе</h2><p>Общий узкий корпус почти не растёт от fighter к vheavy;
основное различие создают крылья, нижний двигатель и окончания плавников. Грузовику нужен дополнительный объём самого корпуса.</p>
<a href="references/family_comparison.jpg"><img class="wide" src="references/family_comparison.jpg" alt="BH fighter, elite и vheavy в одном масштабе"></a>
<table><tr><th>Корабль</th><th>Полёт: Ш × В × Д</th><th>Сложен: Ш × В × Д</th><th>Двигатели</th></tr>__ROWS__</table>
<p class="note">Единицы модели; габарит включает плавники и крылья. Это офлайн-виды текущего мода, без игрового стекла и отражений.</p></section>
<div class="cards">__CARDS__</div>
<section><h2>Кабина BH и Liberty freighter</h2><p>Остекление трёх BH совпадает. У li_freighter узнаваемый родственный профиль;
текущие меши различаются. Для новых поисков используем остекление и раму li_freighter; пилон необязателен, носовой корпус свободно перерабатывается.</p>
<p><a href="references/li_glazing_only/native_glazing_frame.jpg">Остекление с рамой без прежнего нижнего носа</a></p>
<a href="references/bh_li_cockpit_comparison.jpg"><img loading="lazy" src="references/bh_li_cockpit_comparison.jpg" alt="Сравнение кабин BH и li_freighter"></a></section>
<section><h2>Материалы Liberty</h2><p>BH уже использует общую li_playerships.mat: холодные серые панели, сине-зелёные пояса и тёмные двигатели.
Из капшипов подходят панельные поля liberty2_256 и решётки liberty3_256. Они расширяют набор деталей для грузового корпуса.</p>
<a href="references/bh_native_textures.jpg"><img class="wide" loading="lazy" src="references/bh_native_textures.jpg" alt="Родные текстуры BH"></a>
<p><a href="references/liberty_capship_textures.jpg">Посмотреть полный набор текстур капшипов Liberty</a> · <a href="references/material_sources.json">Имена и параметры материалов</a></p></section>
<section><h2>Направление будущего грузовика</h2><p>Перепридумать li_freighter в стиле BH: продольный грузовой корпус,
разные сечения носа, трюма и кормы, боковые механизмы и подвижные плоскости. Только стёкла и рама кокпита неизменны.</p>
<p>Новая серия BHF11–BHF30 развивает рыбную тему BH: скаты, молоты, высокие и вытянутые грузовые тела; меняет
двигатели и расположение плоскостей. Предыдущая серия BHF01–BHF05 сохранена как история отклонённого подхода.</p>
<p><a href="references/li_freighter/native_flight.jpg">Liberty freighter — основной грузовой ориентир</a> · <a href="references/bw_freighter/native_flight.jpg">Обычный BW freighter — второй ориентир</a></p>
<p class="note">Двадцать поисковых направлений доступны в новой галерее. Новая модель ещё не создана; точность кабины и зазоры механики проверяются при моделировании.</p></section></html>'''
    (OUT/'index.html').write_text(page.replace('__ROWS__', ''.join(rows)).replace('__CARDS__', ''.join(cards)), encoding='utf8')


def main():
    free = shutil.disk_usage(OUT.anchor).free
    if free < 1024**3:
        raise OSError('Insufficient free space for reference renders')
    OUT.mkdir(parents=True, exist_ok=True)
    refs = OUT / 'references'
    refs.mkdir(exist_ok=True)
    ini_sources = [p for _, v in a.source.sections(a.source.GAME/'bin/freelancer.ini')
                   for p in v.get('ships', [])]
    active = {}
    for ini in ini_sources:
        for kind, values in a.source.sections(a.source.DATA/ini):
            if kind == 'ship':
                active[values['nickname'][0].lower()] = dict(values, source_ini=ini)
    records, loaded, all_assets = {}, {}, {}
    for key, alias in SHIPS + DONORS:
        folder = OUT/key
        folder.mkdir(parents=True, exist_ok=True)
        values = active[alias]
        spec = dict(model=values['da_archetype'][0].replace('\\', '/').lower(),
                    materials=[p.replace('\\', '/').lower() for p in values['material_library']])
        path = a.source.DATA/spec['model']
        scene, mats, stats = a.source.load(spec)
        scene = [dict(g, part=g['part'].lower()) for g in scene]
        _, nodes = a.source.mesh.read_tree(path.read_bytes())
        flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
        constructs = a.full.constructs(flat)
        channels = a.full.channels(flat, constructs)
        invalid = [c for c in channels if not c['native_size_valid'] or not c['bound_joint']
                   or not c['finite'] or not c['monotonic_times'] or c.get('parent_mismatch')]
        analyzed_scripts = {a.SCRIPT, 'sc_launch extend', values['bay_door_anim'][0].lower()}
        assert not [c for c in invalid if c['script'] in analyzed_scripts], (alias, invalid)
        names = {a.source.mesh.string(b).lower(): a.source.mesh.string(
                 flat[p.rsplit('/', 1)[0]+'/object name']).lower()
                 for p, b in flat.items() if '/cmpnd/' in p and p.endswith('/file name')}
        unmapped = sorted({g['part'] for g in scene}-set(names))
        assert all('nothing' in p or 'none' in p for p in unmapped), unmapped
        for part in unmapped:
            names[part] = 'root'  # Native technical placeholder; same identity fallback as pose loader.
        record = dict(path=spec['model'], constructs=constructs, channels=channels)
        wing = [c for c in channels if c['script'] == a.SCRIPT]
        duration = max(c['duration'] for c in wing)
        times = np.linspace(0, duration, 5).tolist()
        poses = [a.motion.scene_at(record, scene, t, a.SCRIPT) for t in times]
        flight = poses[0]
        direct = a.source.load(spec, pose=(a.SCRIPT, 0))[0]
        delta = max(float(np.abs(g['corners']-h['corners']).max()) for g, h in zip(flight, direct))
        launch_duration = max(c['duration'] for c in channels if c['script'] == 'sc_launch extend')
        launch = a.motion.scene_at(record, scene, launch_duration, 'sc_launch extend')
        launch_delta = max(float(np.abs(g['corners']-h['corners']).max()) for g, h in zip(flight, launch))
        assert max(delta, launch_delta) < 1e-8
        center, radius = layout.frame(flight)

        def render(pose, cam, mode='texture', origin=center, extent=radius, size=500):
            return a.source.render(pose, mats, origin, extent, cam, size, mode)

        for mode, filename in [('texture', 'native_flight.jpg'), ('clay', 'native_shape.jpg')]:
            rows = [[(label, render(flight, cam, mode)) for cam, label in CAMS[i:i+2]] for i in (0, 2, 4)]
            layout.sheet(folder/filename, rows, 2, alias+' / FLIGHT / CURRENT MOD',
                         'Native CMP geometry / software shading / not an in-game capture', size=500)
        glass = [g for g in flight if 'glass' in mats[g['material']]['name'].lower()]
        cc, cr = layout.frame(glass)
        layout.sheet(folder/'cockpit_reference.jpg', [[
            (label, render(flight, cam, origin=cc, extent=cr*1.6, size=550))
            for cam, label in CAMS[:1]+CAMS[2:3]+CAMS[4:5]]], 3,
            alias+' / ORIGINAL CABIN / whole ship cropped by camera',
            'Glazing frames the image; this is NOT an extracted cockpit boundary.', size=550)
        ds = values['bay_door_anim'][0].lower()
        doors = [c for c in channels if c['script'] == ds]
        dd = max(c['duration'] for c in doors)
        held = [dict(c, script=ds, times=[0, dd], values=[c['first'], c['first']]) for c in wing]
        dr = dict(record, channels=doors+held)
        door_poses = [a.motion.scene_at(dr, scene, t, ds) for t in np.linspace(0, dd, 5)]
        door_parts = {c['child'].lower() for c in doors}
        if key in dict(SHIPS):
            layout.sheet(folder/'native_wing_motion.jpg', [[
                (f'{label} / {times[i]:.2f}s', render(poses[i], cam))
                for i, label in [(0, 'FLIGHT'), (2, 'RETRACTING'), (4, 'STOWED')]]
                for cam in [(0, 0, -1), (1, 0, 0)]], 3, alias+' / NATIVE WING AND FIN MOTION',
                'Forward Sc_extend wing stows; native hierarchy and axes; no new animation.', size=500)
            dc, rr = layout.frame([g for pose in door_poses for g in pose if names[g['part']] in door_parts])
            layout.sheet(folder/'native_baydoor_motion.jpg', [[
                (label, render(pose, (.8, 1.3, -.6), origin=dc, extent=rr*2, size=550))
                for label, pose in [('CLOSED', door_poses[0]), ('OPEN / native keys', door_poses[-1])]]],
                2, alias+' / BAYDOOR / wings held in flight',
                'Native pivot/parents; future freighter clearance is not checked.', size=550)
        parts = []
        for name in sorted({g['part'] for g in scene}):
            states = [[g for g in pose if g['part'] == name] for pose in poses]
            lo, hi = layout.bounds(states[0]), layout.bounds(states[-1])
            parts.append(dict(file=name, object=names[name], triangles=sum(len(g['corners']) for g in states[0]),
                              flight=lo, stowed=hi, center_delta_stow=(np.mean([hi['min'], hi['max']], 0)
                              -np.mean([lo['min'], lo['max']], 0)).tolist()))
        hardpoints = []
        for p, b in flat.items():
            if '/hardpoints/' in p and p.endswith('/position'):
                hardpoints.append(dict(part=p.split('/')[2], name=p.split('/')[-2],
                                       position=np.frombuffer(b, '<f4').tolist()))
        assets = [path]+[a.source.DATA/p for p in spec['materials']]+[a.source.DATA/values['cockpit'][0]]
        asset_rows = [dict(path=p.as_posix(), sha256=a.sha(p)) for p in assets]
        all_assets.update({r['path']: r for r in asset_rows})
        report = dict(alias=alias, source_model=path.as_posix(), source_sha256=stats['sha256'],
                      archetype=values, assets=asset_rows, source_stats=stats, constructs=constructs,
                      channels=channels, parts=parts, hardpoints=hardpoints, wing_times=times,
                      phase_bounds=[layout.bounds(p) for p in poses], cockpit_glazing_bounds=layout.bounds(glass),
                      cockpit_glazing_triangles=sum(len(g['corners']) for g in glass),
                      glazing_geometry_sha256=hashlib.sha256(np.round(points(glass), 6).tobytes()).hexdigest(),
                      door_phase_bounds=[layout.bounds([g for g in pose if names[g['part']] in door_parts]) for pose in door_poses],
                      launch_to_flight_max_delta=launch_delta, independent_pose_loader_max_delta=delta,
                      analyzed_channels_valid=True, invalid_other_channels=invalid,
                      source_unchanged=a.sha(path)==stats['sha256'],
                      unbound_technical_placeholders=unmapped,
                      material_colours=[dict(name=mats[mid]['name'], texture=mats[mid]['texture'], colour=mats[mid]['colour'].tolist())
                                        for mid in sorted({g['material'] for g in scene})],
                      caveats=['Installed mod, not authenticated retail.', 'Offline software shading; no game glass/envmap or collision proof.',
                               'Glazing comparison does not establish whole-cabin equivalence.',
                               'Only existing mechanisms reconstructed. No new freighter geometry or animation authored.'])
        assert report['source_unchanged']
        write(folder/'source_audit.json', report)
        records[key] = report
        loaded[key] = dict(scene=flight, mats=mats, center=center, radius=radius, glass=glass, cabin_center=cc, cabin_radius=cr)
        print(alias, 'flight/stow', [np.round(report['phase_bounds'][i]['dimensions'], 3).tolist() for i in (0, -1)], flush=True)

    family_radius = max(loaded[key]['radius'] for key, _ in SHIPS)
    layout.sheet(refs/'family_comparison.jpg', [[
        (alias+' / '+label, a.source.render(loaded[key]['scene'], loaded[key]['mats'], loaded[key]['center'], family_radius, cam, 550, mode))
        for key, alias in SHIPS] for cam, mode, label in [(CAMS[0][0], 'texture', 'FRONT 3/4'),
        (CAMS[1][0], 'texture', 'REAR 3/4'), ((1, 0, 0), 'clay', 'SIDE'), ((0, 0, -1), 'clay', 'FRONT'),
        ((0, 1, .000001), 'clay', 'TOP')]], 3, 'BH FAMILY / CURRENT MOD / SAME UNIT SCALE',
        'Native FLIGHT poses; family proportions are not normalized to equal silhouettes.', size=550)
    cabin_keys = ['elite', 'references/li_freighter']
    cabin_radius = max(loaded[k]['cabin_radius'] for k in cabin_keys)*1.5
    layout.sheet(refs/'bh_li_cockpit_comparison.jpg', [[
        (key+' / '+label, a.source.render(loaded[key]['scene'], loaded[key]['mats'], loaded[key]['cabin_center'], cabin_radius, cam, 550, 'texture'))
        for cam, label in CAMS[:1]+CAMS[2:3]+CAMS[4:5]] for key in cabin_keys], 3,
        'BH vs LI FREIGHTER / ORIGINAL CABIN / SAME UNIT SCALE',
        'Camera crop only; no geometry scaled or edited.', size=550)
    comparisons = {}
    base = points(loaded['elite']['glass'])
    for key, item in loaded.items():
        other = points(item['glass'])
        same_order_delta = float(np.abs(base-other).max()) if base.shape == other.shape else None
        comparisons[key] = dict(triangle_count=len(other)//3, bounds=layout.bounds(item['glass']),
                               same_triangle_order_world_max_delta_vs_bh_elite=same_order_delta)
    write(refs/'cockpit_comparison.json', dict(user_evidence='исходный кокпит bh взят из li_freighter',
          observed_glazing=comparisons, scope='Glazing and visible shells inspected; no entire-cabin extraction or identity claim.'))

    bh = loaded['elite']
    texture_sheet(bh['mats'], refs/'bh_native_textures.jpg', 'BH / ACTUALLY USED EXTERIOR TEXTURES / native LI library',
                  {g['material'] for g in bh['scene']})
    cap_path = a.source.DATA/'ships/liberty/li_capships.mat'
    cap_mats = a.source.material_table([cap_path])
    texture_sheet(cap_mats, refs/'liberty_capship_textures.jpg', 'LIBERTY CAPITAL SHIP TEXTURES / candidate donors only')
    all_assets[cap_path.as_posix()] = dict(path=cap_path.as_posix(), sha256=a.sha(cap_path))
    write(refs/'material_sources.json', dict(user_permission='Liberty capital-ship textures may be borrowed if needed; regular BH ship, not pirate.',
          active_bh_libraries=records['elite']['archetype']['material_library'],
          native_bh_materials=records['elite']['material_colours'],
          capital_library=dict(path=cap_path.as_posix(), sha256=a.sha(cap_path)),
          capital_materials=[dict(name=m['name'], texture=m['texture'], colour=m['colour'].tolist(),
                                 size=list(m['image'].size) if m['image'] else None) for m in cap_mats.values()],
          restriction='metal texture family reserved for cargo interior; do not alter shared MAT libraries.'))
    art_files = sorted(str(p) for p in Path('D:/work/ART_SHIP').rglob('*') if p.suffix.lower() in ('.png', '.jpg', '.jpeg'))
    write(refs/'art_search.json', dict(root='D:/work/ART_SHIP', files=art_files,
          bh_named_matches=[p for p in art_files if re.search(r'(bh_|bounty|piranha|barracuda|hammerhead)', p, re.I)],
          note='No separately named BH source art found. Native CMPs are the design authority; no foreign art assigned by visual similarity.'))
    config = [a.source.GAME/'bin/freelancer.ini']+[a.source.DATA/p for p in ini_sources]+[Path(__file__).resolve().parents[2]/'src/freelancer/Client/wing_anim.h']
    all_assets.update({p.as_posix():dict(path=p.as_posix(), sha256=a.sha(p)) for p in config})
    verified = all(a.sha(Path(v['path']))==v['sha256'] for v in all_assets.values())
    assert verified
    write(OUT/'manifest.json', dict(date='2026-11-19', topic='bh_family', purpose='Regular BH freighter analysis; no pirate redesign.',
          disk_free_before=free, sources=list(all_assets.values()), assets_unchanged=verified,
          bh_archetypes=[n for n in active if n.startswith('bh_')],
          existing_bh_freighter_aliases=[n for n in active if n.startswith('bh_') and 'freight' in n],
          ships={k:dict(alias=v['alias'], source_sha256=v['source_sha256'], audit=k+'/source_audit.json') for k,v in records.items()},
          images=[dict(path=p.relative_to(OUT).as_posix(), sha256=a.sha(p), size=list(Image.open(p).size)) for p in sorted(OUT.rglob('*.jpg'))],
          model_authored=False, game_launched=False, installed=False))
    write_gallery(records)
    print('Saved', OUT, flush=True)


if __name__ == '__main__':
    main()
