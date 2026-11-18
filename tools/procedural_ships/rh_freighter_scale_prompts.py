"""Third RH freighter art set: native scale and prominent original dorsal hump."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

import pirate_art_audit as a
from rh_redesign_paths import TOPIC

OUT = TOPIC / 'rh_freighter/concepts/round_03'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    refs = OUT / 'references'
    refs.mkdir(parents=True, exist_ok=True)
    source_dir = TOPIC / 'pirate_art/ships/rh_freighter_pir'
    row = json.loads((source_dir / 'source.json').read_text(encoding='utf8'))
    scene, mats, stats = a.source.load(row)
    assert stats['sha256'] == row['sha256']
    record = dict(path=row['model'], constructs=row['constructs'], channels=row['wing_channels'])
    flight = a.motion.scene_at(record, scene, 0, a.SCRIPT)
    points = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in flight])
    center = (points.min(0) + points.max(0)) / 2
    radius = np.linalg.norm(points - center, axis=1).max()
    dims = (points.max(0) - points.min(0)).tolist()
    sheet = Image.new('RGB', (1600, 1150), a.BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((15, 10), 'ORIGINAL RH PIR FREIGHTER / native scale and prominent rounded dorsal hump',
              font=a.FONT, fill='white')
    draw.text((15, 38), f'Flight dimensions: width {dims[0]:.3f}, height {dims[1]:.3f}, length {dims[2]:.3f} native units',
              font=a.FONT, fill='white')
    shots = [((1, .6, -1.3), (0, 100, 920, 1000), 'PERSPECTIVE / FLIGHT'),
             ((1, 0, 0), (930, 100, 1600, 440), 'SIDE / FLIGHT'),
             ((0, 1, .00001), (930, 490, 1600, 1100), 'TOP / FLIGHT')]
    for camera, box, label in shots:
        im = a.source.render(flight, mats, center, radius, camera, 1000, 'texture')
        arr = np.asarray(im)
        ys, xs = np.where(np.any(arr != np.array(a.BG), axis=2))
        crop = im.crop((max(0, int(xs.min()) - 25), max(0, int(ys.min()) - 25),
                        min(1000, int(xs.max()) + 26), min(1000, int(ys.max()) + 26)))
        x0, y0, x1, y1 = box
        crop = ImageOps.contain(crop, (x1 - x0 - 20, y1 - y0 - 30))
        sheet.paste(crop, (x0 + (x1 - x0 - crop.width) // 2, y0 + 30 + (y1 - y0 - 30 - crop.height) // 2))
        draw.text((x0 + 15, y0), label, font=a.FONT, fill='white')
    draw.text((15, 1120), 'Read-only source geometry. Views fitted separately. Exact cabin size is fixed; use relative hull/cabin proportions.',
              font=a.SMALL, fill=(190, 200, 210))
    scale_ref = refs / 'original_scale_hump.jpg'
    sheet.save(scale_ref, quality=96)
    previous = TOPIC / 'rh_freighter/concepts/round_02'
    common = '''Use case: precise-object-edit. Create a NEW TAKE of the three-view pirate Rheinland freighter concept sheet in IMAGE 1. The user's latest instruction is to INCREASE THE SHIP BACK TO THE SIZE OF THE ORIGINAL RH FREIGHTER while keeping its original cockpit unchanged, and to PRESERVE ITS IMPORTANT DORSAL HUMP. Keep exactly three views: big perspective, true side profile, top view. Keep the existing wingless concept and pirate character.

REFERENCE PRIORITY:
IMAGE 1 is the previous concept's design vocabulary and three-view page layout, NOT the correct ship size. Its small cargo-runabout proportions are now superseded. Increase the surrounding hull/cargo volume and aft engine assembly relative to the fixed-size cabin. Do not merely enlarge the whole drawing or zoom the camera.
IMAGE 2 is the ACTUAL ORIGINAL RH PIR FREIGHTER and is authoritative for overall physical proportions and the dorsal hump. Its native FLIGHT bounds are width 9.465, height 11.463, length 23.722 units. The full-sized current cabin must retain its existing dimensions while the rest of the craft returns approximately to this source envelope. The original non-moving main body is about 6.3 units wide and the cockpit glazing about 3.6 units wide: retain a relatively narrow central body, not a broad bulk-transport warehouse. Restore the original's larger vertical/longitudinal cargo mass and original-sized twin rear engine units. The cockpit should again read as a smaller head attached to a clearly more substantial freighter body, as in IMAGE 2. Do not scale the cockpit down to fake this.
IMAGE 3 is the IMMUTABLE ORIGINAL FREIGHTER CABIN in close-up. Keep its exact cabin shell, size, frame divisions, sloping dark-blue upper glazing, opaque pale lower metal face with SEPARATE small rectangular blue window slots, narrow black/yellow trim, lower chin and underside equipment block. No continuous dark-blue lower glazing band, no fighter canopy, no new cockpit, no different pilot scale. Match it in all three views.
IMAGE 4 is the user's original RH freighter artwork. Use its recognizable side silhouette, raised roof hump, shoulder ledge, forward cabin and separate round aft propulsion forms. Its green paint and different sketch cabin do not override the user's pirate materials or IMAGE 3.
IMAGE 5 shows the original retractable side-cylinder mechanism. Retain the current concept's heavy integrated hull cheeks with one large central short cylinder and two smaller flanking cylinders per side. These extend laterally on recessed collars, not on wings.

CRITICAL HUMP REQUIREMENT:
Replace the previous small low trapezoid roof cap with a CLEAR, PROMINENT, ROUNDED/FACETED DORSAL HUMP like the original model in IMAGE 2 and source art in IMAGE 4. It is a substantial arched loading-roof mass standing above the straight shoulder deck, approximately the upper third of the overall body height. In true SIDE PROFILE its upper silhouette rises over the middle of the hold and falls toward both the front and rear, a distinct rounded arch with authored facets, rather than a long flat roof, tiny roof vent, low wedge or fighter fin. In TOP VIEW the same hump forms a relatively narrow central roof mass, not a full-width giant barrel. In the perspective, show its height, thickness and a few broad structural sectors or recessed grille fields. This is the source freighter's characteristic cargo hump, not the exposed circular drum of the RH elite fighter. Do not remove, flatten, conceal or shrink the hump in any view. It should remain visually dominant without turning into an enormous hangar stretching the full ship length.

KEEP THE ACCEPTED MECHANICAL DIRECTION:
NO WINGS, thin side paddles or aerodynamic planes. Keep thick stepped armoured side projections structurally integrated into the hull. Each holds exactly THREE short stout closed-end cylindrical/faceted units: large central one, two smaller neighbours. All three views show the same FLIGHT extension. They can withdraw into/against their hull housings at a base. No gun barrels, rockets, wheels or lateral engine exhausts. Empty small equipment sockets can sit flush in the cheek tops. Keep the cargo opening, hull supports and engine clearance plausible. TWO actual main engines remain at the AFT end, a left/right pair at the SAME HEIGHT; their silhouettes overlap in true SIDE view and separate in TOP view. Restore their size relative to the fixed cabin toward the native model, without colossal thruster bells. Preserve bilaterally symmetric primary geometry.

ART AND VIEW CONSISTENCY:
Use the supplied aged pale grey/beige structural metal, restrained dark burgundy replacement panels and very limited hazard trim. Maintain clean Freelancer early-2000s concept-art graphite/ink contours with marker shading on off-white paper. Detail through coherent masses, functional joints, recesses and inset grilles. No decorative rivet fields, random greebles, spike/skull pirate ornaments, integrated weapons, additional cabins or giant container trains.
Landscape sheet: main 3/4 view on the left, SIDE / FLIGHT upper right with nose right, TOP / FLIGHT lower right with nose up. Every view depicts the SAME enlarged original-scale ship, SAME unmodified cabin, SAME prominent hump, same cylinder positions and two rear engines. Keep roof sectors, body proportions and attachments consistent between the views. Leave generous margins and all three complete silhouettes inside the page. Do not compensate for enlarged hull by cropping it. No fourth folded view or extra craft. The new title is specified below.

VARIANT EMPHASIS:
'''
    variants = [
        ('A', 'Исходный силуэт и высокий арочный горб', 'Preserve the previous A concept\'s clear shoulder ledge, high-mounted side cheeks and simple rectangular cargo-body organization. Restore the original-size deep central hold and a clearly arched segmented dorsal hump with only a few broad recessed grilles. Keep its silhouette closest to the source freighter.'),
        ('B', 'Несущие плечи вокруг горба', 'Preserve B\'s coherent longitudinal supports and high side cheeks, now sized around a source-scale enclosed cargo hold. Build a proud rounded dorsal hump between substantial but not bloated shoulders, with a readable gap/recess separating the load-bearing supports from the arched roof shell. Keep the closed cargo mass visually integrated.'),
        ('C', 'Ступени корпуса и округлый грузовой верх', 'Preserve C\'s stepped side surfaces, useful service hatch and recessed vertical grille. Enlarge the freight volume toward the source size and make the top an unmistakable rounded/faceted arch, with front and rear rises/falls clearly visible in side view. The hump is one coherent loading-roof volume, not a stack of little rooftop boxes.'),
        ('D', 'Угловые плечи и выраженный горб', 'Preserve D\'s sloping front shoulder, angular lower side projections and clean structural steps. Increase the hull and rear engines toward native scale while keeping the cabin fixed. Set a large round/faceted dorsal cargo hump above the angular shoulders, creating the deliberate Rheinland contrast between straight main planes and the curved raised roof. Do not let the sloping front replace the hump with a low wedge.'),
        ('E', 'Грузовой корпус на нижней опоре', 'Preserve E\'s strong lower bed and integrated low side cheeks. Restore a substantial original-scale cargo block above that bed and a prominent arched dorsal hump as its defining upper silhouette. Keep the original-style separate aft engine modules and compact front cabin connection. The hold and hump form one organized structure rather than detached cargo containers.'),
    ]
    shared = [scale_ref, previous / 'references/cockpit_original.jpg',
              Path('H:/FL/EXP/EXTRA_ART/RH/R - Freighter.jpg'), previous / 'references/side_cylinders_original.jpg']
    payload = dict(tool='built-in image_gen', target='rh_freighter_pir',
                   latest_brief='Native source scale; prominent original hump; original cockpit; three views; no wings; thick hull cheeks with three retractable cylinders each',
                   source_cmp=row['model'], source_sha256=row['sha256'], native_flight_dimensions_xyz=dims,
                   references=[dict(path=p.as_posix(), sha256=digest(p)) for p in shared],
                   variants=[dict(id=i, title_ru=title, label=i+'3',
                                  target_image=(previous / ('rh_freighter_' + i + '_sheet.png')).as_posix(),
                                  prompt=common + desc + '\nMain title exactly: "RH FREIGHTER / ' + i + '3".')
                             for i, title, desc in variants])
    (OUT / 'prompts.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
    print(OUT / 'prompts.json')


if __name__ == '__main__':
    main()
