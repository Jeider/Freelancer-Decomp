"""Prepare five RH fighter prompt examples and a native cockpit close-up. No AI calls."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import pirate_art_audit as audit


def main():
    out = audit.OUT
    folder = out / 'ships/rh_fighter_pir'
    row = json.loads((folder / 'source.json').read_text(encoding='utf8'))
    assert audit.sha(audit.source.DATA / row['model']) == row['sha256']
    scene, mats, _ = audit.source.load(row)
    # Exact original geometry. These are camera crops, NOT a segmented cockpit mesh.
    center = np.array([0., -1.9, -6.1])
    radius = 3.25
    panel = Image.new('RGB', (1440, 540), audit.BG)
    draw = ImageDraw.Draw(panel)
    draw.text((12, 8), 'rh_fighter_pir / ORIGINAL COCKPIT / shape, glazing, frame and chin are immutable',
              font=audit.FONT, fill='white')
    for i, (camera, label) in enumerate([((1, .35, -1.4), 'front 3/4'),
                                        ((0, 0, -1), 'front'), ((1, 0, 0), 'side')]):
        panel.paste(audit.source.render(scene, mats, center, radius, camera, 480, 'texture'),
                    (i * 480, 45))
        draw.text((i * 480 + 12, 30), label, font=audit.SMALL, fill='white')
    draw.text((12, 520), 'Native CMP close-up, not an isolated cabin; glass appearance is approximate offline.',
              font=audit.SMALL, fill=(190, 200, 210))
    cockpit = folder / 'cockpit_reference.jpg'
    panel.save(cockpit, quality=95)
    reference_paths = [cockpit, folder / 'flight_reference.jpg', folder / 'materials.jpg',
                       Path('D:/work/ART_SHIP/RH/r_fighter01.JPG')]
    references = [dict(image=i + 1, path=p.as_posix(), sha256=audit.sha(p))
                  for i, p in enumerate(reference_paths)]
    base = '''Create ONE new design concept for the installed Freelancer Rheinland pirate LIGHT FIGHTER rh_fighter_pir (model rh_pir_fighter). This is a successor to this specific light fighter.

REFERENCE PRIORITY:
Image 1 is the actual original cockpit photographed from three directions. It is the highest-priority immutable component. Preserve its exact blunt shape, scale, proportions, front and side window outlines, window divisions, sloping windshield, complete surrounding cabin shell, lower chin, frame thickness, material colours and narrow yellow/black glazing trim. Reuse this existing cabin visually. Do not invent, stretch, shrink, relocate, resculpt or replace it. The new airframe must meet the existing cabin at its existing attachment interface. Do not borrow the cockpit from the historical drawing.
Image 2 shows the CURRENT ship in FLIGHT, with its deployed wing geometry. Use it for family identity, relative cockpit scale and structural proportions. Image 3 gives its actual exterior material palette and panel vocabulary: aged pale grey/beige structural surfaces, restrained dark red replacement panels, darker recesses and local warning trim. Interpret the broad painted fields clearly; do not reproduce pixel noise as geometry. Image 4 is a historical family grammar reference only: the deep raised rear mechanical mass and single upright disc, connected to a compact low forward cabin. Its cockpit, weapons and motion arrows are not instructions to copy.

LOCKED DESIGN CONDITIONS:
Preserve the exact Image 1 cockpit; a compact LIGHT fighter role; a substantial upright rear disc/mechanical housing on a coherent narrow longitudinal body; one main rear exhaust as in Image 2; modest articulated wings shown fully deployed in the normal flight position. Keep the rear disc vertical in the longitudinal plane. Keep a clear design distinction from the larger twin-engine Rheinland elite. Build a connected load-bearing structure around the existing cockpit, with plausible thickness, purposeful recesses, inset grilles and a few large calm panel fields. The exposed cockpit must remain clearly visible.
The wings must be rigid parts with intelligible roots and space to stow at a base. Show only the FLIGHT pose in this image. Reserve real space for a later docking mechanism; no telescoping or shrinking of a solid wing, no interpenetration with cockpit/engines. The exact pivots and travel will be validated in a 3D blockout after concept selection.
Weapons are separate game assets: depict compact empty equipment mount pads with clearance, not integrated guns, barrels, missiles or turrets. Keep cargo access and cabin enclosure physically plausible. Exterior mechanical detail must use the ship's exterior palette. No ornamental rivet fields, random bolt-on boxes, spikes, skull decorations, dense greebles, extra bubble canopy or pointed jet nose. Keep authored angular tips sharp; do not round every edge with generic bevels.

PRESENTATION:
Early-2000s industrial science-fiction game design drawing informed by the supplied Freelancer assets, with clear graphite contours and restrained opaque marker colour. One complete ship, front three-quarter view, nose toward lower right and aft toward upper left, both deployed wings readable, mild perspective, neutral even lighting, off-white background. Entire silhouette within the frame with margin. Match the cockpit's apparent scale across the five variants. Moderate modelling detail, readable large volumes. No environment, stars, cinematic glow, motion blur, inset views, folded-state diagrams, text, logos or other ships.

THIS VARIANT:
'''
    directions = [
        ('A', 'Развитие исходника', 'Develop the existing compact proportions into a distinctly redesigned continuous stepped central shell and a newly arranged set of broad armour sectors around the single upright aft disc. Preserve its strong low-cabin/high-rear profile and clear family identity. The improvement is in coherent large volumes and the transitions to the wing roots, not extra surface decoration.'),
        ('B', 'Открытая несущая конструкция', 'Expose one substantial integrated load-bearing cradle around the upright aft mechanical housing, with two clear structural openings visible in silhouette. Connect the cradle firmly to the central hull and wing roots. The disc remains a substantial enclosed mechanism; the cockpit is fully enclosed. Use a restrained angular frame suitable for a LIGHT fighter, not the large near-complete octagonal frame or twin engines of the RH elite B.'),
        ('C', 'Вытянутый лёгкий рейдер', 'Make the airframe aft of the unchanged cockpit more longitudinal and lean, using a stretched connected spine, a moderately raised aft disc and slim swept articulated wing panels. Keep the original cabin fixed and full-sized; length comes from the redesigned rear structure. Maintain Rheinland vertical depth and a visible disc rather than turning the craft into a flat delta jet. Preserve one main rear exhaust.'),
        ('D', 'Компактный глубокий корпус', 'Concentrate the redesigned aft body into a shorter, deeper stepped mass around the vertical disc and single exhaust. Use broad recessed side fields, deeply seated wing roots and clean connected armour shoulders. Keep the cockpit exactly unchanged and clearly separated in silhouette. Achieve a compact tough light fighter through proportion and structural integration, not extra weapons or piles of armour plates.'),
        ('E', 'Разделённые бронесектора', 'Explore a bolder Rheinland light-fighter architecture: surround the upright disc with two unequal-in-length but bilaterally symmetric angular armour sectors, linked by a lower structural bed and one coherent central spine. Leave a large controlled upper/rear opening that changes the profile substantially. Integrate modest articulated wing roots into this bed. Preserve the exact forward cabin, one rear exhaust, enclosed main mechanism and strong high-rear/low-front family silhouette. All supports must meet real surfaces; no detached floating geometry.')]
    payload = dict(status='Prepared prompts only; no images generated and no target selected by the user',
                   target='rh_fighter_pir', source_cmp=row['model'], source_sha256=row['sha256'],
                   cockpit_rule='Original complete cabin is immutable and reused; image output still requires visual checking',
                   cockpit_reference_note='Manual camera framing on original geometry, not an automatically segmented cabin',
                   references=references,
                   variants=[dict(id=i, title_ru=title, prompt=base + text) for i, title, text in directions])
    (out / 'rh_fighter_prompts.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
    print('Prepared', len(directions), 'prompts and', cockpit)


if __name__ == '__main__':
    main()
