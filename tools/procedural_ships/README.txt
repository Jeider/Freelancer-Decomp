General model material rule
===========================
The metal texture family (metal03.tga, metal03D, metal03DK, etc.) is reserved
for the baydoor/cargo-bay interior in every model. Exterior hulls, frames,
engines, joints and other mechanical detail must use exterior materials.
Validate texture references, not only material names. See AGENTS.md.

RH concept B / finished model
============================
Output: out/ship_design/rh_elite/prototypes/concept_b/final_v1/.
See that folder's README.md for the sequential build, bake, damage/SUR,
Blender presentation, independent verification and packaging commands.
rh_concept_b_final.py assembles accepted revision 08; the final_* helpers
finish LODs, animations, hardpoints and damage. Never installs or launches.

RH concept B / earlier revision 02
==============================
python -B tools/procedural_ships/rh_concept_b_detail.py
Blender background: --python tools/procedural_ships/rh_concept_b_render.py -- --video
python -B tools/procedural_ships/check_rh_concept_b_rig.py
Blender background: --python tools/procedural_ships/check_rh_concept_b_rig.py -- --blender-check
python -B tools/procedural_ships/rh_concept_b_detail.py --package-only

Output: out/ship_design/rh_elite/prototypes/concept_b/revision_02/.
Only Level0 is authored. The initial 4542-triangle art budget was relaxed by
the user; 16-bit CMP/index/draw ranges remain checked. No game launch/install.
The cockpit geometry/normals/UVs are preserved. Its old metal material IDs
are remapped to the existing dark exterior material to follow the global rule.
Two native revolute joints per wing replace the earlier single-pivot fold.
Native script names and durations are retained. The Blender rig is checked
against CMP samples; panel/body intersections are checked separately.

li_elite: Medium / maximum texture-derived recess experiment
==========================================================

Run from the repository root with Python, numpy and Pillow:
  python tools/procedural_ships/li_elite.py
  python tools/procedural_ships/li_elite.py --inspect
  python tools/procedural_ships/li_elite.py --depth 0.15
  python tools/procedural_ships/li_elite.py --no-previews
  python tools/procedural_ships/check.py

Source (read-only):
  D:/games/FL_MOD/DATA/SHIPS/LIBERTY/LI_ELITE/li_elite.cmp
  D:/games/FL_MOD/DATA/SHIPS/LIBERTY/li_playerships.mat

Output (separate from the game):
  src/obj/procedural_ships/li_elite_medium/
    DATA/SHIPS/LIBERTY/LI_ELITE/li_elite.cmp
    comparison.jpg          original / Medium, textured and untextured
    hull_closeup.jpg        untextured close-up and wireframe comparison
    depth_masks.jpg         actual texture-to-recess maps
    original.obj            assembled construct zero pose for DCC inspection
    li_elite_medium.obj     same pose with refined geometry
    *.mtl, *.png            OBJ materials and original diffuse texture exports
    report.json             hashes, triangle counts, per-part displacement
    checks.json             staged asset verification
    li_elite_medium_max_recess.zip  CMP, reports, README and comparison images

For the full ship/model/animation/art study, start at docs/ru/ship_design/README.md.
Read-only survey tools: full_ship_audit.py, ship_collision_audit.py,
ship_motion_preview.py, art_catalog.py. Output: out/ship_design/analysis/full_models.
These tools do not install assets or start the game.

The source is THIS installation's li_elite, including its animated wing sections.
It has not been authenticated as an unmodified retail asset.
This generator never installs or changes the game, renderer, HUD or shaders.

Geometry
--------
Medium uses the same triangle budget as two subdivision steps: 16 times the
original count for each selected component, 1315 -> 17305 triangles overall.
Conforming longest-edge splits distribute this budget more evenly than regular
subdivision of the original long, thin triangles. Original triangle/material
boundaries and barycentric UVs are retained. Protected materials receive only
the splits needed by the part grid; their positions are not displaced.

Only the hull, two engines and spoiler receive geometric relief. Glass, the
single-sheet animated wing skins, doors and tiny hinge placeholders stay as-is.
The weaponplate material remains undeformed. Hardpoints, construction records,
animation scripts, all original mesh libraries and VMeshWire leaves remain
byte-identical. Four Level0 references point to new private mesh libraries.
All other original UTF leaves, including lower LOD references, are unchanged.

Darkness and local dark contrast in the original diffuse texture produce inward
displacement. Default maximum depth is 0.30 MODEL UNITS (not an asserted metre
conversion). This is an intentionally exaggerated diagnostic preset, not the
mathematically deepest possible deformation. Sharp edges, open edges, material/
UV seams and the immediate area around hardpoints are protected. Depth also
depends on triangle scale and is limited to 35% of the nearest original-surface
hit along an inward ray. Local displacement is reduced if triangles fold.
Recomputed geometric normal changes are added to the authored shading normals.
No PN smoothing of the overall hull and no new normal-map shader are applied.

RH concept B revision 03
------------------------
rh_concept_b_form.py builds the art-led LOD0 with a closed cabin/cargo interior
and horizontal forward/inward wing hinges. It preserves revision_02 assets.
rh_concept_b_render.py --revision 3 --video runs inside background Blender.
check_rh_concept_b_form.py compares the saved rig against native CMP samples,
checks panel clearances and front-facing cabin/cargo surfaces.
rh_concept_b_report.py assembles actual-render comparisons and the Markdown report.
Artifacts: out/ship_design/rh_elite/prototypes/concept_b/revision_03/README.md.

RH B revision 04: selected SIDE and TOP art views
-----------------------------------------------
rh_concept_b_profile.py builds the new silhouette around the unchanged glazing.
Sharp wing tips, forward-leaning shoulders, a variable-section aft frame,
recessed side/roof/wing fields, and checked forward/inward folding.
rh_concept_b_render.py --revision 4 --video renders/exports the animated blend.
check_rh_concept_b_form.py --revision 4 validates that revision's actual CMP.
rh_concept_b_profile_report.py creates the interactive art/model comparison.
Artifacts: out/ship_design/rh_elite/prototypes/concept_b/revision_04/README.md.
No installation or game launch. Revisions 02 and 03 remain available.

RH B revision 06: python -B tools/procedural_ships/rh_concept_b_attachments.py
Shortened solid cabin transition, aligned underside, closer native pirate engines,
removed diagonal brace, deliberate pirate atlas placement and distinct border UVs.
rh_concept_b_render.py --revision 6 --prototype makes static review images only.
Artifacts: out/ship_design/rh_elite/prototypes/concept_b/revision_06/README.md.
Keeps the existing animation tracks. Does not install or launch the game.

RH B revision 07: python -B tools/procedural_ships/rh_concept_b_compact.py
Lower tail, original engine-axis spacing, closer wings, constant-width neck,
actual native body weapon pylons with matching hardpoints, closed engine shells,
and orthonormal UV charts. The proposed roof-to-tail beam is explicitly deferred.
python tools/blender_workspace.py --topic ship_design --script tools/procedural_ships/rh_concept_b_render.py -- --revision 7 --prototype
python tools/blender_workspace.py --topic ship_design --script tools/procedural_ships/check_rh_concept_b_attachments.py -- --revision 7
Artifacts: out/ship_design/rh_elite/prototypes/concept_b/revision_07/README.md.
No game launch, installation or animation retiming.

RH B revision 08: python -B tools/procedural_ships/rh_concept_b_sockets.py
Native-width pirate neck, aft body pylons, centered wing pads, swept wings in
plain U sockets, continuous engine shells, separate sill trim UVs, front recesses
and a full-size native drum UV layout recessed inside the preserved rim, with
five parallel recesses. Pale lamellae removed at user request.
check_rh_concept_b_seams.py checks coplanar floor and mounting-lip intersections.
The shared Blender render/verification commands above accept --revision 8.
Artifacts: out/ship_design/rh_elite/prototypes/concept_b/revision_08/README.md.
No new animation keys; flight, folded clearance, SUR and distant LODs deferred.

Validation
----------
The generator round-trips the UTF, resolves ALL original and new VMeshRefs,
checks index/vertex limits and material IDs, compares generated vertices/UVs
with the decoded output, checks finite unit normals and reference AABB/sphere,
and verifies unchanged unrelated leaves and source hashes. Mesh names are
content-derived. Output should be byte-identical on an unchanged repeat run.

Limits of this experiment
------------------------
Diffuse darkness is not physical depth: paint, baked shadows and insignia can
be interpreted as recesses. Strong relief can make metal look dented. The maps
need artistic review before this can be considered a finished hull upgrade.
The Medium budget cannot reproduce every fine line in the source textures.

Collision SUR and separate damage caps are unchanged. No in-game flight,
animation, destruction, collision or FPS check has been performed. Ray-thickness
and face-fold tests are not a complete self-intersection/cross-part collision
test. Detailed LOD0 may visibly transition to the original distant LODs.

Previews use identical cameras and simple lighting in the construct zero pose;
they are not game screenshots. They omit engine glass blending, effects,
environment reflections and the existing ship normal-map shader. Tiny "none"
hinge placeholders (8 triangles total) are omitted only from previews/OBJs;
the actual CMP retains them and its original animation data.

The CMP replacement needs this installation's original material libraries and
textures. Before any later installation, back up the original CMP and check the
source hashes in report.json. No modified texture or SUR is needed for the CMP.
