# Trading station part: two additional visible LODs

Installed 2026-10-22 into FL_MOD. Shared asset used by the sixteen
`space_trade_station_part` objects around ku_tgk_01 and by other systems.
Runtime backup (original model and complete solararch.ini):
`D:/games/FL_MOD/DATA/SOLAR/MISC/.before_trade_station_lods_20261022_110538`.

| Level | Distance | Vertices | Triangles | Material groups |
| --- | --- | ---: | ---: | ---: |
| Original Level0 | 0-1800 m | 3967 | 2180 | 47 |
| New Level1 | 1800-4500 m | 3065 | 1912 | 7 |
| New Level2 | 4500-8000 m | 2684 | 1684 | 7 |
| Original empty level, now Level3 | 8000-27000 m | 3 | 1 | 1 |

The last visibility distance follows the previous configuration: the old model
already switched to its tiny hidden triangle at 8000 m. Adding distant visible
geometry would increase rendering cost, so that behavior is preserved.

Attribute-aware quadric simplification accounts for normals, UVs and a strongly
weighted material tag. Retained vertices keep their original position/normal/UV
records. All seven opaque DcDt material types were checked in Solar_mat_tink.mat;
coarse levels combine matching groups. Thin structural bars and flat caps are
protected after visual previews showed excessive simplification could erase them.
This limits reduction; the target triangle ratios are goals, not achieved counts.
No runtime simplification or new rendering dependency is introduced.

`geometry_comparison.png` shows Level0/1/2 left to right from two views using a
hidden-window D3D9 fixture. Colors identify materials; it is an untextured geometry
preview, not an in-game screenshot. The game appearance, transition visibility
and FPS benefit still require an in-game check.

Verified: original Level0 mesh/reference and all hardpoint/other UTF leaves are
byte-identical, all new indices/ranges/materials and CRC references are valid,
the old hidden reference is unchanged at Level3, no complete material group was
lost, and no degenerate new triangles were emitted. Output and runtime files
were SHA256 checked. `space_trade_station_part.report.json` contains the hashes
and per-material counts. `solararch.block.ini` is the changed archetype block.

Generator: `tools/generate_station_lods.py SOURCE OUTPUT`. Requires x64 Python
and `bin/lod_meshopt.dll`, built with x64 MSVC from `tools/lod_simplify.cpp`,
`tools/vendor/meshoptimizer/{allocator,simplifier,vcacheoptimizer}.cpp`.
Meshoptimizer sources are MIT licensed, pinned to the revision in REVISION.txt,
from [the official repository](https://github.com/zeux/meshoptimizer).
The original file must be supplied as input; do not reprocess the generated model.
