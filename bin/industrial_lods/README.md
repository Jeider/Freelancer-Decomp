# Industrial model LOD batch

Installed 19 custom single-LOD models. Original files: `D:\games\FL_MOD\DATA\.before_industrial_lods_20261022_114327`.

Each model now has the original Level0 plus two generated levels. Standard
switches are 1800 m and 4500 m. All 53 archetype references were updated:
34 in SOLAR/solararch.ini and 19 in EQUIPMENT/select_equip.ini. Existing far
visibility distances are preserved. Short-range references use proportional
switches: 600/1300 m for 2000 m, 900/1950 m for 3000 m, and 1500/3250 m for 5000 m.

| Model | Original vertices | LOD1 | LOD2 |
| --- | ---: | ---: | ---: |
| space_industrial01a | 543 | 422 | 331 |
| space_industrial01a_alt | 543 | 422 | 331 |
| space_industrial01b | 543 | 410 | 327 |
| space_industrial01c | 202 | 163 | 132 |
| space_industrial01d | 410 | 346 | 276 |
| space_industrial01e | 410 | 346 | 276 |
| space_industrial01f | 410 | 346 | 276 |
| space_industrial01g | 410 | 346 | 276 |
| space_industrial01h | 410 | 346 | 276 |
| space_industrial01i | 410 | 346 | 276 |
| space_industrial01j | 410 | 346 | 276 |
| space_industrial02a | 565 | 506 | 325 |
| space_industrial02b | 565 | 502 | 326 |
| space_industrial02d | 575 | 539 | 376 |
| space_industrial03 | 637 | 379 | 324 |
| space_industriala | 409 | 349 | 329 |
| space_industriala_alt | 409 | 349 | 329 |
| space_industriala_alt2 | 409 | 349 | 329 |
| space_industrialc | 283 | 263 | 235 |

Across one of each model: vertices 8553 -> 7075 / 5626 (17.3% / 34.2% less).
Triangles 5520 -> 4857 / 3866. These are geometry counts, not measured FPS gains.
Most input models already had one group per material, so this batch does not
reproduce the trading-part reduction from 47 draws to 7.

Preservation and validation:

- Original near mesh/reference bytes, material/texture data, bounds, hardpoints and all seven HUD wire archives are preserved. The root VMeshPart is relocated intact into MultiLevel/Level0.
- Retained position/normal/UV records are copied from original vertices. Coarse triangles account for normal/UV/material error. Small material islands are kept if simplification would remove them entirely.
- Long thin structural pieces are protected. Industrial03 parameters were corrected after a preview showed a thin pole collapsing.
- Every generated index and VMeshRef/CRC is checked after serialization; 38 new CRC keys are unique. All 14 rendered materials resolve to opaque DcDt, including industrial03 embedded materials.
- All 19 models were drawn at all 3 LODs from two directions in the hidden-window D3D9 preview. All staged and installed files were SHA256 checked. Only 53 LODranges lines changed in the two INIs.
- Retail industrial models already having multiple LODs, retail cargo models and NN icons are excluded. Internal mesh names were audited; the discovery list is included.

`previews/` contains geometry comparisons, with Level0/1/2 left to right.
These use material colors rather than authored textures. They are not in-game
screenshots; texture appearance, transitions and actual FPS still need an in-game check.

`manifest.json` records source/output hashes and per-material geometry statistics.
`archetype_changes.ini` lists the changed archetype blocks. `installation.json`
records the backup location. The backup contains all 19 original models and both
complete original INIs, preserving relative paths.

Generator: tools/generate_industrial_lods.py, using the pinned MIT meshoptimizer
sources/wrapper from the previous trading-part task. It writes a review bundle;
tools/install_industrial_lods.ps1 performs guarded install with complete backups
and rollback if replacement fails. No runtime DLL or renderer setting changed.
Generation requires original single-LOD inputs; running it on installed models
is intentionally rejected. Discovery/material/reference audits are included.
