Procedural Freelancer asteroid prototype
========================================

Run from the repository root with Python, numpy and Pillow:

  python tools/procedural_asteroids/refine.py D:/games/FL_MOD/DATA/SOLAR/ASTEROIDS/MODELS/ast_rock_60.3db

Output: src/obj/procedural_asteroids/rock60/
  comparison.png             same lighting/cameras/scale, without textures
  original.obj               original geometry for DCC comparison
  ast_rock_60_medium.3db      480-triangle alternative (default settings)
  ast_rock_60_high.3db        1920-triangle alternative (default settings)
  corresponding .obj files   primary UV only; .3db retains both UV channels
  report.json                hashes, geometry/budget metrics and parameters

The input is never overwritten. No game installation, executable, configuration,
HUD file, collision mesh, field, billboard or LOD selection is modified.
The two .3db files are alternative prototypes, not an installed LOD chain.
They use the original material IDs and therefore need the original material library.
For a later controlled replacement, use the original model filename in a backed-up
game data directory. Do not distribute proprietary source/model data from src/obj.

Algorithm
---------
Weld geometric positions across UV seams, derive area-weighted normals, evaluate
cubic PN triangle patches, interpolate each UV channel barycentrically, and add
seeded 3D noise, narrow depressions and broad shallow impact scallops. Shared edges
use identical positions/normals even where UVs differ. Original corners and the
authored bounding box stay fixed. Deviation from a corresponding point on the
original triangle is capped at --max-deviation times the source bounding radius.
This cap also bounds distance to the original surface; it is not a guarantee of
identical collision clearance, volume or silhouette.

Defaults: --subdivisions 3 --smooth 0.35 --relief 0.045 --max-deviation 0.06
--seed 6028 is deterministic. A different seed makes another relief pattern.
Medium uses one fewer subdivision. Each subdivision multiplies triangle count by 4.

Supported input is deliberately narrow: one rigid mesh, one material, FVF 0x112,
0x212 or 0x252 (including interpolated vertex colors), full root VMeshPart,
consistently oriented geometry and a native VMeshWire. Handles are preserved;
the batch path also preserves authored open boundary edges. Unsupported meshes
are rejected rather than guessed at. Exact attribute-identical, same-winding
duplicate faces are removed, while opposite-facing sheets/UV overlays are retained.
Geometry-level topology validation does not constitute a full self-intersection test.

Packing and validation
----------------------
Retain the original vertex prefix and wire indices for the sparse HUD wireframe.
Append the detailed face vertices with exact-attribute welding. Assign a private,
content-derived mesh-library name, update both mesh and wire CRCs, recompute bounds,
and preserve unrelated UTF leaves and material IDs. Verify 16-bit limits, closed
edges, consistent winding, triangle orientation, UTF round-trip, references,
wireframe vertices/indices, deterministic output and the unchanged source hash.

Remaining integration work
--------------------------
Flight review of silhouette/textures and old SUR clearance; profiling dense fields;
selecting a field-wide vertex budget; automatic LOD integration and matching far
representations. The report's homogeneous block ceiling is an arithmetic upper
bound for a block containing only this mesh, not a recommended field density.
No live in-game rendering or collision validation has been performed by this tool.

Medium batch
------------
  python tools/procedural_asteroids/batch.py D:/games/FL_MOD/DATA/SOLAR/ASTEROIDS/MODELS

Output: src/obj/procedural_asteroids/retail_medium/
  DATA/SOLAR/ASTEROIDS/MODELS/  replacements under their original filenames
  asteroids_medium.zip        those replacements, manifest, summary and this readme
  review_01.jpg ...           paired geometry previews of every processed asteroid
  manifest.json               per-file source/output hashes, profile and validation
  summary.json                counts and field vertex-budget audit

The source directory defines the candidate set; the files have not been
authenticated against a pristine retail distribution. Debris, mines, loot and
belt surfaces are explicitly excluded even though they share this folder.

Rock uses the reviewed Medium settings. Ice has milder displacement. Faceted
ice/beryl and Nomad models have low displacement and retain authored shading
discontinuities. Original open boundaries stay fixed. For folded output faces,
strength is reduced and revalidated; the manifest records this adjustment.

Up to two subdivision steps are used, capped at 1280 triangles per model by
default. Thus a 30-triangle asteroid becomes 480, while already denser large
models use fewer steps. The field audit resolves Cube entries in ASTEROIDS and
ASTEROIDS_MOD through asteroid archetype INIs and conservatively sums the new
vertex counts. Unresolved references are reported, not treated as passing.
This checks 16-bit addressing, not GPU frame time or all runtime data overlays.

Before installing, back up the matching game files and verify the manifest's
source hashes. Old SUR meshes and far billboards are not included in the pack;
their compatibility and collision clearance still need in-game review. The tool
never installs, launches or rebuilds the game, and never resumes paused HUD work.
