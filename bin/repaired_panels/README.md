# ku_tgk_01 panel normals

Direct repairs of FL_MOD's `DATA/SOLAR/MISC` models, without a MilkShape re-export.
Applied to the runtime models on 2026-10-22. Original files were backed up to
`D:/games/FL_MOD/DATA/SOLAR/MISC/.before_panel_normals_20261022_002831`.

The exported main meshes shared 28 vertices across non-coplanar faces; stored
normals deviated from face normals by up to 103.69 degrees. Split triangle
corners and assigned geometric face normals for planar shading, including LODs.
Main meshes have 240 vertices instead of 85; LOD meshes have 96 instead of 33.
Triangle counts and rendered geometry are unchanged.

Files: `space_panel_rotated.3db`, `space_panel45.3db`, `space_panel_Z90.3db`.
These are shared assets: other stations using them also receive the correction.

Tool: `tools/repair_panel_normals.py SOURCE.3db DESTINATION.3db`.
It verifies triangle positions, UVs, material groups, normals, and unchanged
non-mesh UTF leaves. Hardpoints, bounds, mesh identifiers and references are
preserved; reference vertex counts are updated. New mesh payloads are appended
to preserve unrelated archive data. Installed files were SHA256-verified.
In-game appearance still needs visual confirmation.

## or_hq terraforming panels

Also repaired `space_panel.3db`, used by `attached_solarpnl` in
`terraform_new_root` on `or_hq_terra_1/2/3`. Installed on 2026-10-22; original:
`D:/games/FL_MOD/DATA/SOLAR/MISC/.before_or_hq_panel_normals_20261022_103115`.
The main mesh had 85 vertices, 80 triangles and 80 corners with normals deviating
by more than 5 degrees (maximum 103.687 degrees). Repaired mesh: 240 vertices,
same 80 triangles. Positions, UVs, material groups, references and other UTF
leaves verified by the repair tool. Shared asset: all users receive the fix.

Original SHA256: `7ecdd27ceaec7e993d7332408a065e2d524677089e0df58937537bc4254cb1f5`.
Installed SHA256: `de86c16e945fa6c7df6392d86250a841edc4332bc10578a5e3cbf7cdb3aaa19c`.
