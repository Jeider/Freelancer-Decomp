"""Current user brief: small RH cargo craft, five sheets with three flight views."""
import hashlib
import json
from pathlib import Path

from rh_redesign_paths import TOPIC

OUT = TOPIC / 'rh_freighter/concepts/round_02'


def main():
    source = json.loads((TOPIC / 'pirate_art/ships/rh_freighter_pir/source.json').read_text(encoding='utf8'))
    refs = [
        Path('H:/FL/EXP/EXTRA_ART/RH/R - Freighter.jpg'),
        OUT / 'references/cockpit_original.jpg',
        TOPIC / 'pirate_art/ships/rh_freighter_pir/flight_reference.jpg',
        TOPIC / 'pirate_art/ships/rh_freighter_pir/materials.jpg',
        OUT / 'references/side_cylinders_original.jpg',
    ]
    common = '''Use case: stylized-concept. Draw a NEW THREE-VIEW DESIGN SHEET of ONE SMALL PIRATE RHEINLAND FREIGHTER for Freelancer. The user specifically wants a compact little player cargo craft, NOT a heavy transport. The previous concepts were rejected for bloated width, huge vaulted holds and excessive mass. Start fresh. This is a small utility spacecraft with one modest enclosed cargo compartment and two small rear engine pods.

REFERENCE HIERARCHY:
IMAGE 1 is the user's chosen ORIGINAL FREIGHTER ART and the PRIMARY architectural reference. Follow its spare silhouette and sequence of distinct masses: a small low detached-looking forward cabin, a short narrow vertically developed cargo block, a small raised faceted roof cap, and compact circular rear propulsion nodes connected through a slender aft structure. Notice the simple stepped side panels and open neck/rear connections. Translate the character into a NEW compact design; do not inflate the central box into a broad warehouse or barrel.
IMAGE 2 is the EXACT IMMUTABLE CABIN from the user's current rh_pir_freighter. It overrides the differently drawn cabin in image 1. Preserve this complete cabin: blunt short faceted nose, original sloped dark-blue windshield and side windows, the same frame divisions, small flat brow, thin yellow-black trim, lower pale metal chin with the original small window strips, and small underside equipment block. CRITICAL: the lower cabin face is MOSTLY OPAQUE PALE METAL with small isolated rectangular blue window slots separated by broad vertical metal plates, NOT a continuous dark-blue wraparound lower windshield. Copy the cabin in image 2 faithfully in every view. Do not replace the cabin with a Rheinland elite/fighter cabin, change window count, scale it down, elongate it, turn it into a fighter canopy or add a bridge tower. The original cabin mesh will be reused in 3D.
IMAGE 3 is the actual current freighter: reference for cockpit attachment, separate rear engines and original parts only. You are explicitly reducing the surrounding airframe mass and width. Do NOT preserve its full bulk.
IMAGE 4 is the pirate surface palette: pale worn grey/beige structure, restrained dark red replacement panels, dark recesses, very limited hazard trim. Do not copy the green livery of image 1. Keep paint and wear subordinate to readable large forms.
IMAGE 5 shows the ORIGINAL retractable side cylinders: one large central unit and two smaller flanking units per side. Preserve this mechanism's identity. The user explicitly wants weighty integrated hull projections with these cylinders, NO WINGS.

SMALL-CARGO-CRAFT PROPORTIONS:
The existing cabin stays full-sized and visually significant. The enclosed main cargo box should be roughly twice the cabin's length and only about one-and-a-half cabin widths across; it may rise above the cabin but stays narrow. Total ship length including cabin, connection and modest rear pods is around four to five cabin lengths. Keep the front-to-back sequence of original RH masses. Read as a small personal cargo runabout, not a bulk hauler. The TOP VIEW must clearly demonstrate the narrow body. Two rear cylindrical engine pods each have a diameter smaller than the cabin width. A small raised roof cap is allowed, but NO giant barrel roof, long arched hangar, large twin cargo barges, massive external buttresses or long train of containers. Preserve vertical Rheinland character through a narrow tall-ish central block, not by ballooning its width. No wheels or ground-truck parts.

MECHANICS AND SHAPE:
A coherent enclosed freight body, real cargo hatch, complete cabin shell, two modest rear engines with exhausts facing AFT. The engines are a LEFT/RIGHT pair at the SAME HEIGHT, so in true SIDE PROFILE their silhouettes overlap; never draw a vertical stack of two engines in the side view. In TOP VIEW both engines appear distinctly side by side. NO WINGS, thin side plates, aerodynamic fins or flat equipment paddles. Instead, form two substantial stepped armoured cheeks continuously integrated into the cargo body. Each cheek contains THREE short retractable cylinders/faceted drums with closed end caps: a larger central one and two smaller flanking ones, following image 5. Axes are lateral; these are stout hull equipment units, not guns, thrusters or wheels. Show the same short outward FLIGHT extension in all three views, with recessed guide sleeves for withdrawal toward the body at a base. Keep the main hull compact and narrow; the short thick cheeks should not become broad barges. Preserve cargo access, original cabin and rear-engine clearance. Use purposeful recesses and inset vents, not decorative rivets, spikes or greeble noise. Empty small hardpoint sockets may be integrated flush into the cheek tops. Main geometry is bilaterally symmetric.

EXACT SHEET LAYOUT — THREE VIEWS OF ONE SHIP:
Landscape concept sheet on warm off-white paper. Large coloured front three-quarter perspective occupies the left two-thirds, nose toward lower right. At upper right place a clean true orthographic SIDE PROFILE, nose to the right. At lower right place a clean true orthographic TOP VIEW, nose pointing up. Reserve ample non-overlapping space for both small views and keep every ship outline inside the sheet. Exactly three views, no fourth diagram. ALL ARE FLIGHT with cylinders extended; no stowed-state inset. The side and top are usable shape guides, not loose unrelated thumbnails: same cabin, main-box length, roof cap, neck, engine positions, solid hull-cheek volumes and cylinder extension, same equipment count and panel divisions. No wings in any view. Check their correspondences before finishing. Small-view detail should be clear and restrained.
Style: hand-drawn early-2000s Freelancer industrial concept sheet, crisp graphite/ink construction outlines, restrained marker/gouache shading, lightly worn broad panel fields. Clear technical drawing with restrained colour. No cinematic space scene, glow, blur or photoreal warehouse render. Small-view labels only: "SIDE / FLIGHT" and "TOP / FLIGHT". Main title is given below.

THIS NEW DESIGN:
'''
    variants = [
        ('A', 'Компактный курьер', 'One compact rectangular cargo block with clipped corners and a small angular half-dome roof cap over its rear half. A short clean structural neck connects the unchanged low cabin. Use three broad stepped side panel fields with small circular functional attachment bosses inspired by the original art. Rear engines sit on a short tapered Y-like structural tail, separate from the cargo box. Thick compact hull cheeks and their three side cylinders sit just below the shoulder ledge. Keep the silhouette spare, narrow and clearly lighter than the source model.'),
        ('B', 'Лёгкая несущая скоба', 'A modest narrow cargo capsule embraced by two slim integrated longitudinal side rails and a small angled upper bridge. Leave one clear triangular structural gap per side behind the cabin connection. The actual cargo compartment stays closed and compact. Use an angular roof cap rather than a barrel vault. The two small rear engine pods sit on exposed short curved/angled brackets. The side rails merge into solid armoured cheeks holding the three retractable cylinders. Avoid a giant surrounding cage: structural members stay slender relative to the original full-sized cabin.'),
        ('C', 'Ступенчатая спина', 'A compact narrow stepped cargo body with a low forward shoulder and a small raised faceted aft roof cap. The upper silhouette climbs in two clear steps, while the bottom stays on a continuous slender structural sill. Preserve a clearly visible short neck to the unchanged cabin. Seat two small round engine pods just aft on separated short supports, with clear space between them. Three short cylinders extend from an integrated thick stepped cheek on each side. Introduce a few broad recessed vertical panel fields and a single useful grille, keeping the whole craft short and lightly built.'),
        ('D', 'Угловатый развозной грузовик', 'A small narrow angular cargo trunk with a sloping upper front and a squared stepped rear, under a shallow faceted cap. Its main distinction is a strong diagonal shoulder line and one large recessed rectangular side hatch, not extra armour mass. Keep the unchanged full-sized cockpit clearly forward on a short neck. The two modest aft engine cylinders are half-set into light rear collars with open gaps to the trunk. Angular thick side cheeks house the short source-style retractable cylinders. Read as a rugged little delivery craft, with a high narrow profile and no broad dome.'),
        ('E', 'Грузовой блок на тонкой раме', 'A small raised enclosed cargo pod rests on a slim lower longitudinal bed, with an intentional open gap under its forward shoulder. A small faceted dorsal cap and two short side service pods give the cargo body a distinctive stepped shape without widening it beyond the narrow proportion target. The unchanged cockpit attaches at the low front of the bed. Two compact spherical-to-cylindrical engine housings sit on a short exposed aft fork, echoing the original drawing. Solid hull protrusions rise from the bed and house the source-style side cylinders. All volumes and supports meet structurally; no floating cargo box and no bulky twin hulls.'),
    ]
    payload = dict(tool='built-in image_gen', target='rh_freighter_pir',
                   brief='Small cargo craft; three views; original cockpit immutable; NO WINGS, integrated hull protrusions with source-style side cylinders; prior five PNGs deleted',
                   source_cmp=source['model'], source_sha256=source['sha256'],
                   cockpit_sources=source['cockpit_sources'],
                   references=[dict(path=p.as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in refs],
                   variants=[dict(id=i, title_ru=title, prompt=common + desc + '\nMain title exactly: "RH FREIGHTER / ' + i + '".')
                             for i, title, desc in variants])
    (OUT / 'prompts.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
    print(OUT / 'prompts.json')


if __name__ == '__main__':
    main()
