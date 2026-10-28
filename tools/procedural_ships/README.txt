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
