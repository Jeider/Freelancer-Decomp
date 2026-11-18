"""Prepare and archive 20 built-in imagegen calls; this script makes no image API calls."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image
from rh_redesign_paths import TOPIC

OUT = TOPIC / 'rh_freighter/concepts/round_10'
SOURCE = Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_pir_freighter/rh_pir_freighter.cmp')
SOURCE_SHA = '085e9a5d778922b1aef6ebe70a95ce0d902636177dd1b5cc03a4b6c0ffbc738b'
REFS = [
    TOPIC / 'rh_freighter/concepts/round_03/references/original_scale_hump.jpg',
    TOPIC / 'rh_freighter/references/baydoor/native_baydoor_motion.jpg',
    TOPIC / 'rh_freighter/concepts/round_02/references/cockpit_original.jpg',
    TOPIC / 'rh_elite/prototypes/concept_b/uv_refinement_01/after_bottom_corner.png',
]

COMMON = '''Use case: precise-object-edit. Create ONE NEW THREE-VIEW RH PIRATE JUNKER FREIGHTER concept variant. The user APPROVED the direction and detail level of the P01/P02 sample in image 1 and requests twenty different designs. This is one of them. Preserve that quality, native scale and circular rotating cargo roof, while making the specific structural changes below genuinely visible. Do not just recolour the reference.

REFERENCES: Image 1 is the approved P-series sample for detail density, style and underlying concept. Image 2 is the ACTUAL original freighter for proportions and ancestry. Image 3 shows its actual curved cargo shutter CLOSED, OPENING and OPEN; use it for mechanics, NOT its six-view layout. Image 4 is the IMMUTABLE original FREIGHTER cockpit. Image 5 is the executed pirate elite for well-seated recessed fields and deep closed returns ONLY, not its overall shape.

PIRATE IDENTITY: This is an independent scavenger/Junker ship, not a Rheinland military ship. REMOVE the large Rheinland cross, national flag, faction heraldry and military insignia from the reference design. No national symbols anywhere on the hull, roof or engines. Do not replace them with a different national flag or huge decorative skull. Pirate character must come from major reclaimed hull sections, physically mismatched but fitted donor housings, repaired seams, worn dark red inset panels and restrained irregular paint patches. Sparse small non-heraldic salvage marks are optional. Pale worn metal, muted reclaimed red, occasional olive, dark recesses. Preserve the original cockpit's narrow safety trim.

INVARIANTS:
1. Reuse the exact original FREIGHTER CABIN appearance from image 4, unchanged size, shape, pane divisions and position: sloping blue upper windshield, pale opaque lower face with separate rectangular blue window slots, narrow yellow-black trim, original chin and equipment block below. No redesigned canopy, visor, armour or smaller cockpit. New hull transitions fit around this existing module.
2. Original physical dimensions W9.465 H11.463 L23.722; tall narrow cargo body, not a fat transport or tiny runabout. Exactly TWO original-sized aft engines, left/right at same height, short closed solid couplers. SIDE shows one overlapping engine outline; TOP shows two engines.
3. HIGH CIRCULAR DORSAL HUMP: preserve the source's near-semicircular side outline, radius, height and longitudinal extent. The fixed solid semicircular side cheeks enclose a broad curved shutter spanning BETWEEN them. Shutter has 6-8 broad transverse solid pressed-metal sectors following the ARC, each with optional shallow relief. It rotates AFT AND DOWN about the transverse X axis through about 120 degrees to open the hold. Keep clear curved seams on both sides and a free circular swept path. No fixed plate or grille bridging the movable shutter to hull. Keep all three views CLOSED. Never replace this circular mechanism with a trapezoidal roof box, pyramid, flat cap, turret or exposed spoked wheel. Describe the curved shell with broad crisp facets, retaining its circular silhouette; the lower hull is angular. Fixed closed arc cheeks may have recessed concentric/radial fields, not external hoop frames.
4. EXACTLY THREE sliding closed-ended faceted cylinders per side: larger middle, smaller front and rear, ONE ROW, six total. All extended in FLIGHT; their sleeves must permit later lateral withdrawal. Symmetrical cylinder positions even when fixed donor housings differ. Thick solid integrated side cheeks, no wings. Do not interpret cylinders as guns, exhausts or landing wheels.

DETAIL LEVEL: Match the approved P-series, which is about 50% richer than the rejected sparse M-series. Maintain a clear hierarchy: four to six authored hull-volume decisions, then meaningful medium-scale details. Per side a substantial recessed cargo hatch with a designed stepped jamb and unequal inset fields; two or three useful service panels; a deep vent pocket with 3-4 broad blades; substantial shaped cylinder sockets and engine joins. A few recessed fields on fixed arc cheeks, broad pressed fields in the curved shutter. Calm contiguous planes between these features. Do not drop to a plain primitive box or inflate to dense D-series microdetail. No numerous repeated mini-hatches, concentric bezel stacks, uniform grids or bolt forests. The executed elite teaches coherent inset fields, closed walls, crisp joins and depth. Wear and small fasteners are painted texture, not geometry.

HARD EXCLUSIONS: no exposed pipes, hoses, cables, external trusses, open frames, braces, cages, skeletal pylons, separate external ribs or bars. No wings, thin fins, claws, cranes or attached guns. No geometric rivets. No generic smoothing/bevel on every sharp hull corner. Every recess has a closed back. Fixed solid semicircular cheek walls are functional bodywork and remain required. Keep upper housing clear of the shutter sweep.

PAGE: exactly THREE full uncropped views of the SAME design: large front-side 3/4 on LEFT, true SIDE / FLIGHT upper RIGHT nose right, true TOP / FLIGHT lower RIGHT nose up. Consistent cabin, high circular roof, cylinder count, engines, hatch locations and proportions across views. All closed cargo / flight extension. Refined Freelancer-era ink and controlled marker/gouache shading on off-white paper, sharp readable planes, restrained wear, no environment, no perspective in technical views. Only the specified title plus SIDE / FLIGHT and TOP / FLIGHT. No extra mini-views, callouts or faction insignia.
'''

VARIANTS = [
 ('Q01','P01','Развитие исходного корпуса','Глубокий грузовой борт','Keep source-like upright front/rear bulkheads. Set the broad lower cargo door deeply into a chamfered continuous sidewall with a strong stepped sill. Above it, make the cylinder carrier a separate-height solid terrace joined smoothly into fixed end shoulders. Arc cheeks have one recessed semicircular field with broad radial divisions. Six broad shutter panels. Distinct through layered vertical cargo depth, not wider overall mass.'),
 ('Q02','P02','Развитие исходного корпуса','Высокое переднее плечо','One large sloping SOLID forward shoulder rises behind the unchanged cabin and descends aft along the drum carrier. Give the lower body a longer shallow diagonal chin cut and an aft-biased cargo hatch. Rear service pocket sits low; curved roof stays prominent above the shoulder. Front-heavy hull profile with low compact engine roots.'),
 ('Q03','P01','Развитие исходного корпуса','Собранная тяжёлая корма','Concentrate solid cargo mass and a two-step hull return at the rear quarter; narrow the fixed forward sidewall behind the unchanged cabin. A forward-positioned cargo hatch balances the heavier rear housing. Enclose engine roots in compact angled donor cowls, preserving two aft modules. Roof arch stays at its native location and size; rear housing must not enter shutter sweep.'),
 ('Q04','P02','Развитие исходного корпуса','Двойной уступ днища','A deep lower cargo body with TWO substantial unequal outline steps, one forward and one aft, plus a long recessed central cargo-door field. Drum carrier is horizontal and continuous, with angular end transitions. Shoulders are quieter so the stepped lower silhouette and high circular roof dominate. Steps are cuts in a solid body, not detached plates.'),
 ('Q05','P01','Развитие исходного корпуса','Утопленная носовая стенка','Develop a deeper enclosed FRONT bulkhead recess around the original cabin connection. The forward solid corners form purposeful diagonal returns into the sidewall, never freestanding beams. Keep original cabin position/size. Side cargo hatch is taller and shorter, rear quarter has a closed stepped service housing. Fixed roof cheeks rise cleanly above a short horizontal shoulder.'),
 ('Q06','P02','Клиновидные переделки','Косые торцы корпуса','Give the main cargo block strong matching oblique FRONT and AFT end cuts creating an elongated six-sided side silhouette under the circular hump. Thick integrated cylinder cheeks echo these planes without protruding wings. Cargo hatch is a broad clipped hexagon with unequal inset leaves. Keep medium service details inside these meaningful planes.'),
 ('Q07','P02','Клиновидные переделки','Клин под цилиндрами','A substantial long closed wedge BELOW the cylinder row rises toward the nose, visibly cutting the lower side silhouette. Set the deep cargo hatch into its broad sloping plane; rear vent and service pocket sit in the deeper aft section. Upper shoulder stays almost horizontal, leaving the source semicircle fully legible. No diagonal exterior bar.'),
 ('Q08','P01','Клиновидные переделки','Ломаное плечо','Fixed shoulder line has three connected levels: short high rear housing, descending diagonal middle return, lower front ledge. All are one thick enclosed hull. Cylinder row remains straight and symmetrical. Lower cargo hatch has a low horizontal lip and a higher rear return. The circular moving roof remains separately readable with its original height.'),
 ('Q09','P02','Клиновидные переделки','Гранёные угловые кожухи','Four broad solid beveled-in-plan CORNER MASSES integrate the original cargo block, with sharp purposeful cut planes, not generic rounded bevels. Front and rear corners taper toward cabin/engines. Between them a deep straight side cargo panel and substantial cylindrical sockets. Closed circular roof cheeks seat into these corner transitions. Do not turn corners into side wings.'),
 ('Q10','P01','Клиновидные переделки','Узкий верх и тяжёлый низ','Maintain native overall width but make the fixed upper shoulders narrower and the lower cargo hull visibly deeper, joined by large oblique continuous planes. Round roof retains original radius and width. Side hatch sits low inside a broad recessed field; service pockets sit higher behind the sliding cylinders. Two compact engine roots taper out of the rear body.'),
 ('Q11','P02','Донорские сборки','Разные боковые кожухи','Physically different fixed donor housings left and right: one a long wedge with one deep cargo field, the other a stepped rectangular housing with two larger unequal inset fields. Same exterior width envelope, same cylinder centers and free lateral movement. TOP view makes asymmetry obvious. Round shutter and cabin remain centered and symmetric.'),
 ('Q12','P01','Донорские сборки','Три секции из утиля','Compose the hull as THREE joined substantial donor volumes: clipped forward bulkhead, deep central cargo section and compact stepped aft transition. Their real plane offsets and joint depths express salvage construction. A major repaired seam at each join, no dense patches. Continuous high circular roof mechanism across the original central location, no blocked shutter movement.'),
 ('Q13','P02','Донорские сборки','Диагональная замена борта','One large replacement lower side section meets the older cargo body along a pronounced diagonal RECESSED junction. Change both adjoining planes and lower contour to make a real structural rebuild, not a painted diagonal or raised beam. Drum housing remains coherent above. One deep angular cargo door and two service fields; source circular shutter untouched in principle.'),
 ('Q14','P01','Донорские сборки','Широкая грузовая створка','Build around a very broad recessed lower cargo panel divided into TWO unequal interlocking leaves with a deep angular jamb, occupying most of the side below cylinders. Smaller service recesses move to forward shoulder and aft quarter. Top shoulders are physically offset fore/aft across sides. Retain circular roof and meaningful contour cuts at nose and belly.'),
 ('Q15','P02','Донорские сборки','Восстановленный заводской корпус','The closest-to-original survivor, but with one heavily rebuilt forward lower corner, a replaced deeper aft service housing and a deliberately different solid cylinder carrier plate. Preserve original semicircular roof size and upright cargo proportions. Reclaimed roof sectors are individually pressed broad panels with subtly different inset shapes, all same circular sweep. No official emblem.'),
 ('Q16','P01','Арка и механические узлы','Ступенчатые щёки арки','Emphasize a carefully authored fixed circular cheek: a deep concentric arc field, a smaller shallow lower bearing-cover region, and four broad recessed radial sectors, all within a solid sidewall. Integrate its base into two short solid hull shoulders. Curved shutter has eight broad sectors. Lower hull uses a long low cargo hatch and diagonal corner returns. No open wheel or radial spokes.'),
 ('Q17','P02','Арка и механические узлы','Сегментная крышка и скошенный трюм','Make the six broad pressed-metal sectors of the real curved shutter especially legible, each with one substantial shallow inset. Keep precise semicircular sweep and clean side seams. Fixed arc cheeks are calmer solid crescent fields. Below, an angled cargo wall with a central deep hatch, compact paired service fields and a rear vent gives a strong sculpted hull. No raised cross-ribs.'),
 ('Q18','P01','Арка и механические узлы','Закрытые карманы привода','At the base of each FIXED arc cheek integrate short deep closed polygonal bearing-drive housings, outside the rotating shutter envelope. These housings merge into solid cylinder cheeks, not external exposed hubs or pipes. A two-tier cargo hatch and one rear ventilation pocket sit below. Preserve high circular arc above and same native size.'),
 ('Q19','P02','Арка и механические узлы','Собранные двигатель и корма','Redesign the rear fixed quarter as a compact set of two enclosed angular engine-root cowls, with shaped insets and one meaningful service access per cowl. Engines remain two original-sized cylindrical modules on the same level. Strong rear lower step, forward slanted cargo corner, central low hatch and an unobstructed high circular shutter. No large engine bells or third engine.'),
 ('Q20','P02','Арка и механические узлы','Цельная пиратская переделка','Balanced candidate combining a pronounced forward SOLID wedge shoulder, continuous three-cylinder side cheek, tall recessed cargo hatch with unequal leaves, compact rear step and an authentic high round shutter. Fixed arc cheek has a broad recessed crescent with three unequal radial fields. Two repaired roof sectors, mild asymmetric fixed service housing, closed engine roots. Every medium detail follows a major plane; keep the original cabin prominent and unchanged.'),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def prepare():
    assert shutil.disk_usage(OUT.anchor).free > 1024**3
    assert sha(SOURCE) == SOURCE_SHA
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'prompts.json').exists(), 'Prompts already prepared'
    variants = []
    for ident, base, group, title, design in VARIANTS:
        target = OUT.parent / 'round_09' / f'rh_freighter_{base}_sheet.png'
        variants.append(dict(id=ident, base_variant=base, title_ru=title, group_ru=group,
                             target_image=target.as_posix(), target_sha256=sha(target),
                             prompt=COMMON + '\nSPECIFIC DESIGN: ' + design + '\nTitle exactly: RH JUNKER FREIGHTER / ' + ident))
    write_json(OUT / 'prompts.json', dict(tool='built-in image_gen', target='rh_freighter_pir',
               user_scope='20 new variants based on approved P01/P02; faction flags not needed',
               source_cmp=SOURCE.as_posix(), source_sha256=SOURCE_SHA,
               references=[dict(path=p.as_posix(), sha256=sha(p)) for p in REFS], variants=variants))
    (OUT / 'records').mkdir(exist_ok=True)
    print(OUT / 'prompts.json')


def save(ident, source):
    pack = json.loads((OUT / 'prompts.json').read_text(encoding='utf8'))
    variant = next(v for v in pack['variants'] if v['id'] == ident)
    src = Path(source).resolve()
    assert src.is_file() and src.suffix.lower() == '.png'
    dst = OUT / f'rh_freighter_{ident}_sheet.png'
    assert dst.resolve().parent == OUT.resolve()
    if dst.exists():
        assert sha(dst) == sha(src), 'Refusing to replace existing concept'
    else:
        shutil.copyfile(src, dst)
    with Image.open(dst) as im:
        size = list(im.size)
        im.verify()
    assert sha(dst) == sha(src)
    row = {k: variant[k] for k in ('id', 'base_variant', 'title_ru', 'group_ru')}
    row.update(source=src.as_posix(), destination=dst.as_posix(), sha256=sha(dst), bytes=dst.stat().st_size, size=size,
               comparison_image=f'../round_09/rh_freighter_{variant["base_variant"]}_sheet.png',
               comparison_label='Одобренный пробник ' + variant['base_variant'])
    write_json(OUT / 'records' / f'{ident}.json', row)
    print(json.dumps(dict(id=ident, destination=dst.as_posix(), size=size), ensure_ascii=False))


def build(complete=False):
    pack = json.loads((OUT / 'prompts.json').read_text(encoding='utf8'))
    assert sha(SOURCE) == SOURCE_SHA
    for ref in pack['references']:
        assert sha(ref['path']) == ref['sha256']
    for v in pack['variants']:
        assert sha(v['target_image']) == v['target_sha256']
    rows = [json.loads(p.read_text(encoding='utf8')) for p in sorted((OUT / 'records').glob('Q*.json'))]
    assert len({r['id'] for r in rows}) == len(rows)
    for row in rows:
        assert Path(row['destination']).resolve().parent == OUT.resolve()
        assert sha(row['destination']) == row['sha256'] == sha(row['source'])
    if complete:
        assert [r['id'] for r in rows] == [v['id'] for v in pack['variants']]
        assert len(rows) == 20 and len({r['sha256'] for r in rows}) == 20
    manifest = dict(tool='built-in image_gen', target='rh_freighter_pir', source_cmp=SOURCE.as_posix(), source_sha256=SOURCE_SHA,
                    status='20 variants complete' if complete else f'{len(rows)} of 20 saved; generation in progress',
                    gallery_title='RH Junker Freighter — Q01–Q20', gallery_heading='20 вариантов на основе P01/P02',
                    gallery_intro='Круговая крышка трюма, исходная кабина, плотность деталей одобренных P-пробников. Без рейнландской символики. Различия в объёмах корпуса, донорских кожухах и узлах. Отмечайте понравившиеся звёздочкой.',
                    prompt_files=['prompts.json'], artifacts=rows)
    selection_file = OUT.parents[1] / 'selection.json'
    if selection_file.exists():
        selected = json.loads(selection_file.read_text(encoding='utf8'))
        chosen = next((r for r in rows if r['id'] == selected['concept_id']), None)
        if chosen and chosen['sha256'] == selected['art_sha256']:
            manifest.update(selected_concept=chosen['id'], selection_document='../../SELECTED_CONCEPT.md',
                            gallery_heading=chosen['id'] + ' — берём в работу · все 20 вариантов',
                            gallery_intro='Пользователь выбрал ' + chosen['id'] + ' для моделирования другими агентами. Выбранный лист отмечен зелёной рамкой. Все двадцать вариантов сохранены; исходная кабина, круговая крышка трюма и плотность деталей P01/P02 остаются основой.')
    write_json(OUT / 'artifacts.json', manifest)
    if rows:
        subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('rh_freighter_review_gallery.py')), '--round', 'round_10'], check=True)
    print(manifest['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'save', 'build'])
    parser.add_argument('--id')
    parser.add_argument('--source')
    parser.add_argument('--complete', action='store_true')
    args = parser.parse_args()
    if args.action == 'prepare': prepare()
    elif args.action == 'save': save(args.id, args.source)
    else: build(args.complete)
