# High-benefit station component LODs and local repairs

Installed 10 LOD models, 2 standalone repaired models and 29 LODrange entries
across solararch.ini/select_equip.ini. Full original files and the manifest are
backed up at `D:\games\FL_MOD\DATA\.before_component_lods_20261022_124307`.

| Model | Original vertices | LOD1 | LOD2 | Groups before/after |
| --- | ---: | ---: | ---: | --- |
| space_control_tower | 2425 | 1541 | 1142 | 11 / 5 / 5 |
| space_medium_control_tower | 1435 | 949 | 664 | 11 / 4 / 4 |
| space_production | 6997 | 4623 | 2876 | 11 / 8 / 8 |
| space_large_production | 6412 | 4679 | 2918 | 11 / 8 / 8 |
| shipyard_small | 2956 | 1920 | 1674 | 5 / 5 / 5 |
| shipyard_medium | 3099 | 1906 | 1642 | 5 / 5 / 5 |
| space_domea | 1161 | 850 | 746 | 7 / 7 / 7 |
| space_domeb | 1161 | 870 | 788 | 7 / 7 / 7 |
| space_small_control_block | 792 | 492 | 458 | 6 / 6 / 6 |
| space_windows | 972 | 618 | 448 | 9 / 3 / 3 |

Aggregate one-of-each geometry: 27410 -> 18448 / 13356 vertices (32.7% / 51.3%
fewer). Triangles 13988 -> 9229 / 6512. Material groups 83 -> 58 in both coarse
levels. These counts are not measured game FPS gains.

Switches are normally 1800 / 4500 m; existing far visibility distances remain.
Short-range archetypes receive proportional thresholds through the same policy
as the previously installed industrial LODs. Model fallback end distance remains
1000000 m. The existing root VMeshPart/reference is relocated into Level0.

Local repairs:

- Medium control tower: reverse winding on exactly four thin horizontal panel triangles. Vertex records, including authored normals and UVs, are unchanged. Repair is applied before generating the coarse LODs.
- Long large arch: replace exactly one zero normal with the normalized area-weighted normal of its two adjacent faces. Only 12 vertex bytes change; geometry, UVs and indices are unchanged.
- Dyson detail block: remove 755 exact same-material/same-winding duplicate triangles and compact identical/unused vertex records. Vertices 12667 -> 10532; triangles 6056 -> 5301. Opposite winding faces are retained. Rendered position/normal/UV triangle sets are verified equivalent.

Preservation:

- Near meshes remain byte-identical except the explicitly scoped winding/normal/Dyson repairs. Hardpoints, bounds, wireframe data, materials and textures are preserved.
- Alpha-mask geometry on both shipyards and domes is preserved with original attributes and triangle order. Matching positions are locked during simplification to preserve their joins.
- Small control block aerial material is preserved intact after a preview showed bending.
- Original production/medium-shipyard mesh payloads have two zero alignment bytes. They remain unchanged in Level0; simplification parses the declared geometry range.
- Big tower had an empty MultiLevel container containing only a default Switch2 leaf. This unused container is replaced by the valid three-level hierarchy.

Validation:

- tools/validate_component_lods.py and --installed: original leaves, 20 new mesh CRC references, all index/range/bounds data, protected alpha/aerial groups and 29 changed configuration lines.
- Hidden-window D3D9 previews of all 10 LOD models and both standalone repairs from two viewpoints. previews contains untextured material-color comparisons, not in-game screenshots.
- Dyson before/after geometry images rendered in identical viewport positions match exactly (PNG hashes equal). Comparing separate side-by-side viewport locations alone produced two raster-rounding pixel differences, so same-viewport captures were used for this check.
- All 14 originals backed up and hash-verified before replacing any runtime file. Installed model/config hashes verified; guarded installer restores originals if installation fails.
- Runtime game visual appearance, transitions and FPS still need an in-game check. Rendering DLLs, shader settings and previously installed industrial/trading LOD files were not changed.

Build: python tools/build_component_lods.py (requires original single-LOD inputs
and the existing offline meshoptimizer wrapper). Review manifest.json and
archetype_changes.ini; install with tools/install_component_lods.ps1 while the
game is closed. Validation can compare installed files against installation.json
backups. Re-running generation against installed models is rejected.
