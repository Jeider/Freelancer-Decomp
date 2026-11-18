"""RH freighter round 04: structural Junker conversions around the native cabin."""
import hashlib
import json
from pathlib import Path

from rh_redesign_paths import TOPIC

OUT = TOPIC / 'rh_freighter/concepts/round_04'
PREVIOUS = TOPIC / 'rh_freighter/concepts/round_03'

COMMON = '''Use case: precise-object-edit. Create a materially redesigned PIRATE / JUNKER RH FREIGHTER three-view concept sheet. This is an outlaw scavenger ship in the Freelancer universe. The user rejected the last concepts for looking like a clean civilian freighter with different paint. The new variant must visibly change OUTER STRUCTURE, ARMOUR GEOMETRY, FIXED ATTACHMENTS and SILHOUETTE: improvised but credible shipyard work made from scavenged spacecraft. Show a dangerous, work-worn, ruthless machine belonging to scrap dealers and raiders. A colour swap, added dirt or a skull decal alone does not satisfy the request. Retain the identifiable original freighter underneath these pirate conversions.

INPUT ROLES AND PRIORITY:
IMAGE 1 is the edit target: the previous three-view concept. Keep the overall vessel scale, original cabin, large hump, two aft engines and retractable cylinder mechanism. Freely redesign its overly tidy outer hull plating and bracing in the direction specified below. Meaningful pirate modifications must read at thumbnail size.
IMAGE 2 is the ACTUAL SOURCE RH pirate freighter in perspective, side and top views, authoritative for the ship/cabin proportions and the characteristic high curved dorsal hump. Source flight bounds: width 9.465, height 11.463, length 23.722. Do not miniaturize or broaden it into a giant transport. The enclosed central hull stays tall and relatively narrow. Match approximately this overall envelope; modifications sit mostly within it, with limited purposeful projection.
IMAGE 3 is the ORIGINAL CABIN, the immutable component. Reproduce its COMPLETE shell faithfully at original size: sloping dark blue upper glazing with original metal divisions, mostly opaque pale lower face with small separate rectangular blue window slots, narrow worn yellow/black trim, original chin and underside equipment block. Preserve the cabin position relative to the source body. No added armour on the cabin, no new visor, cage, window bar, spikes, skull or continuous blue lower glass band. Fit the new body to the cabin. Never redesign the cabin to look pirate. In the future model this entire component must be reused unchanged.
IMAGE 4 shows the ORIGINAL RETRACTABLE SIDE CYLINDERS. Preserve EXACTLY THREE short closed-ended drums on EACH side: one large central drum and a smaller drum fore and aft, in one longitudinal row. Their supporting cheeks are thick protrusions of the HULL, never wings. All three views show these cylinders extended laterally in FLIGHT. Their roots need visible sliding sleeves and free travel into their hull housings; do not weld braces or armour across that travel. No extra row, fourth drum, wheels, tyres, side-facing engine exhaust or gun barrels.

PIRATE FORM LANGUAGE:
Retain a pressure-tight cargo body, but replace selected outer panels with cut sections of other spacecraft: differently shaped thick armour with stepped edges, a few obvious overlapping repair joints and large weld seams. Use deliberate broad panels, a handful of load-bearing diagonal struts and substantial functional attachment points. At least one substantial hull zone has lost its factory outer fairing and shows a recessed load-bearing frame, protected pipes or a service recess above an intact inner wall. Show two or three specific donor constructions with visibly different contour/edge treatments, not random checkerboard texture. Restrained asymmetry is welcome in FIXED replacement panels and repair structures; primary body, cockpit, retracting mechanisms and the paired engine positions remain coherent. Keep a clearly engineered load path. Design an integrated silhouette with a slightly hostile posture, not a pile of small decorations or loose trash glued onto a box. Hull structure, donor armour and salvage attachments should identify the faction even in greyscale.

PRESERVE THE HUMP:
The upper silhouette must retain the prominent rounded/faceted ARCH of the source. In SIDE profile it rises over the hold and falls toward front and rear, taking roughly the upper third of the body height. In TOP view it is a narrow longitudinal roof volume. It is an enclosed raised cargo roof with an arched outline, not an open RH elite wheel, giant circular disc, low trapezoid, flat cap, exposed cable reel or fin. Pirate reinforcement may follow this arch, repair portions of its skin or reveal recessed roof framing, but never flatten or conceal the identifying hump. Keep the same large mass ratio in all views.

OTHER HARD CONSTRAINTS:
No wings, aerodynamic fins, sails or flags. No enormous external containers. No added cabin. TWO main engines at the AFT end, left and right at the SAME HEIGHT. They overlap in a true side projection and separate in top view. Donor engine shrouds and replacement mounting struts are allowed around the paired original-sized engine forms. No third engine, vertical engine stack or giant thruster bells. This is a freighter, not a fighter or capital ship. Keep the unmodified original cockpit small relative to the full-size hold. Equipment weapons remain separately fitted game assets: empty rugged hardpoint pads are allowed, but do not draw integrated guns, barrels, missiles or turrets. No decorative spike forest, bone trophies, loose chains, rivet fields, dense tiny greebles or turbine-blade ornament. Convey the outlaw faction through actual salvage construction.

MATERIAL AND ART:
Use worn pale grey/beige original hull, dark red salvage armour, exposed charcoal steel frames, occasional faded olive donor panel and tiny remnants of industrial hazard trim. Give parts a history through cut edges, welded metal transitions, rubbed corners, soot near the aft engines, irregular repair seams and subdued rust. Keep clear readable surfaces and shape; do not bury everything in uniform brown noise. Original source cabin remains its existing material/glazing. Small crude painted ownership mark on ONE hull panel may supplement the construction, never replace it. Freelancer early-2000s industrial spacecraft concept art, confident ink/graphite edges, marker and gouache shading on off-white paper. Crisp designed volumes with rich depth, not a toy, photoreal cinematic scene or sterile modern product rendering.

SHEET:
Landscape with exactly THREE complete views of the SAME ship: large front-side 3/4 perspective on the LEFT, true SIDE / FLIGHT at upper right nose pointing right, true TOP / FLIGHT at lower right nose up. One variant on the page. Use the same hull proportions, dominant hump, immutable cabin, cylinder count and physical attachments in every view. Transfer any asymmetric repair to the correct physical side in top view. Make both smaller views large and legible enough to build from. All views in flight, all parts uncropped with margins. No fourth diagram. Add only the short title specified below and the two view labels; no explanatory paragraphs.

VARIANT-SPECIFIC CONVERSION (make this the dominant visible change):
'''

VARIANTS = [
    ('A', 'Сварной панцирь', '''A4 / SCRAP ARMOUR. A ruthless patch-built armoured cargo ship. Replace the smooth factory cheeks and lower side wall with TWO OR THREE LARGE irregular donor armour slabs interlocked into a strong external belly cradle. Their genuinely thick cut edges, partly overlapping stepped corners and deeply recessed seams change the silhouette. Fit a long angled salvage beam running from the lower forward shoulder back into the engine support, with a believable interrupted/open section below the cylinder row; do not obstruct the drums. Break the regular front hull corners into blunt angular armoured shoulders behind the untouched cabin. On the hump, show broad mismatched curved replacement sectors held by two strong arched steel edge frames. Leave a readable service gap with a few major pipes at the rear. A substantial dark red scavenged side plate dominates one area, while other surfaces retain pale original material. The result is a dangerous welded shell around a recognizable RH freighter, not an identical box with rust.'''),
    ('B', 'Сборщик трофеев', '''B4 / SALVAGE CLAMPS. A pirate salvage hauler that physically seizes and carries stolen material. Give the lower hull a strong welded longitudinal cradle with TWO compact, thick opposed mechanical C-shaped cargo jaws seated against the forward lower shoulders, BEHIND AND BELOW the unmodified cabin, not in front of its windows. These are blunt industrial locking jaws with visible pivots and hydraulic linkage, not long arms, wings, guns, spikes or ground landing gear. Keep the outer jaw silhouette close to the hull within the source-size envelope; show clear gaps in their grasping mouths. Add deep recessed tie-down sockets and load-bearing beams connecting this cradle to the rear engine frame. One side shoulder uses a salvaged ribbed structural panel, the opposite has overlapping flat repair plates. Preserve all six original side drums with completely clear retraction paths above the cargo cradle. A short protected cable run and one recessed towing fixture convey salvage machinery; avoid additional circular modules resembling extra drums. Retain the large arched hump with irregular roof skin repairs. The new cargo grip silhouette is prominent and consistent in all three views.'''),
    ('C', 'Грузовик налётчиков', '''C4 / RAIDER BASTION. The most threatening variant, a cargo ship converted for carrying a raiding crew and stolen goods. Build massive SLANTED hull shoulders behind the untouched small cabin and give the lower forward hull a blunt wedge-shaped impact beam, split around the cabin's existing support rather than covering it. Make the front of the main cargo body and side cheeks visibly deeper, angled and hostile, but stay inside roughly the original scale and keep the arched hump taller than the shoulders. Two or three thick overlapping salvaged armour plates form offset side barriers around the cylinder housings; keep the three drums on each side exposed and free to retract. Rear engine struts become a heavy welded forked frame. Include a large recessed armoured side access shutter under the drum row, asymmetrically repaired, and two empty flush equipment hardpoints at the shoulders. Hump arch has one broad dark donor sector and a cut-back outer fairing revealing a structural rib, always above a sealed inner shell. More mass in authored planes and negative spaces, not a pile of tiny plates. Menacing freighter, not fighter; no built-in weapons and no armour/cage added to the cabin.'''),
    ('D', 'Раздетый каркас', '''D4 / BONEYARD FRAME. The strongest scavenger identity: remove substantial portions of the smooth outer SIDE fairing and expose a single coherent dark welded structural frame around a recessed sealed inner cargo wall. Show one large diagonal load strut below and behind the cylinder row, connected to the lower bed and rear engine mounts. Recess two large protected conduit runs inside this structure. Recovered thick pale and dull red shell plates cover only selected broad bays, so the ship reads as an improvised reconstruction rather than a complete factory shell. Keep the hull solid and inhabitable: no open void through the pressure compartment. Frame and panel thickness must change the side profile and create deep shadows. The high arched hump survives, with some outer roof sectors replaced by ridged donor panels and a clearly repaired arch rim; the top is still largely closed. Paired engines have repaired mounting collars attached into the same frame. Maintain restrained broad geometry; no tiny machinery clutter, random dangling scrap or decorative grille pasted on a plain box. Cabin remains the exact original.'''),
    ('E', 'Корабль из доноров', '''E4 / STOLEN PARTS. A recognizably reconstructed freighter assembled from several salvaged ships, with coherent LARGE-SCALE asymmetry in fixed outer shell parts. One shoulder uses a battered angular dark-red military armour casing with a cut-off original mounting flange; the other has an industrial ribbed grey replacement casing of equal structural size. Each still carries exactly the original three sliding side drums. Show different donor cut lines and mounting seams, not just colours. The intact cargo hold sits on one continuous reinforced keel and is surrounded by irregular deep side recesses with a broad diagonal welded repair bridge near the stern. The two engines stay matched in position and function but have different repaired OUTER shrouds, one with a partly missing outer panel revealing a protected dark collar (not a different third engine). Keep the arched hump prominent, enclosed and recognizable; repair it with a few broad curved donor sections and one major welded splice, not a row of identical decorative ribs. Include a small scavenger ownership mark over a crudely obscured old registration. This is a feared junkyard owner-operated outlaw ship: strong asymmetric industrial shapes, not a neat military repaint or an incoherent garbage heap. Preserve exact original cabin and source overall size.'''),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = json.loads((PREVIOUS / 'prompts.json').read_text(encoding='utf8'))
    references = [PREVIOUS / 'references/original_scale_hump.jpg',
                  TOPIC / 'rh_freighter/concepts/round_02/references/cockpit_original.jpg',
                  TOPIC / 'rh_freighter/concepts/round_02/references/side_cylinders_original.jpg']
    variants = []
    for ident, title, direction in VARIANTS:
        target = PREVIOUS / f'rh_freighter_{ident}3_sheet.png'
        label = ident + '4'
        variants.append(dict(id=ident, label=label, title_ru=title,
                             target_image=target.as_posix(), target_sha256=sha(target),
                             prompt=COMMON + direction + '\nMain title exactly: "RH JUNKER FREIGHTER / ' + label + '".'))
    payload = dict(tool='built-in image_gen', target='rh_freighter_pir',
                   latest_brief='Structural Junker/pirate identity; native scale; prominent original hump; immutable native cabin; three flight views; wingless hull cheeks with three sliding drums per side',
                   source_cmp=(Path('D:/Games/FL_MOD/DATA') / source['source_cmp']).as_posix(), source_sha256=source['source_sha256'],
                   native_flight_dimensions_xyz=source['native_flight_dimensions_xyz'],
                   references=[dict(path=p.as_posix(), sha256=sha(p)) for p in references],
                   variants=variants)
    path = OUT / 'prompts.json'
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
    print(path)


if __name__ == '__main__':
    main()
