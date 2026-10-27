ku_tgk dynamic asteroid normal maps (first version)

STATUS: disabled at the user's request on 2026-10-26. The visual gain was too small.
The runtime integration, extra generic-shader instructions, and generated MAT
texture are removed by player_shadow_quality. Scripts and measurements below
document the experiment; its GPU/route tests require the former implementation.

Scope: mat_ktgk_a/b/c, used by ast_ku_tgk_normal_a/b/c in the thirteen
ku_tgk asteroid fields. Other dynamic and static asteroid materials are unchanged.

generate.py reads rock3c.tga (DDS/DXT1 inside ast_ku_tgk.mat), removes broad
baked illumination and block noise, estimates relief, and generates a shared
1024-square linear RGB normal map. All 11 mip levels average and renormalize
vectors. Uncompressed BGRA8 costs about 5.33 MiB including mips and avoids
normal compression artifacts. Strength in the client is 0.65; no shiny finish.

The generator embeds ku_tgk_rock_normal.tga/MIPS in a separate staged MAT.
Every original leaf is verified byte-identical. Models need no patch: existing
normals/UVs supply a derivative tangent frame, including mirrored UVs; degenerate
UVs keep the geometric normal. No silhouette change and no parallax/displacement.
This is inferred relief from a lit diffuse texture, not a physically recovered scan.

The client resolves the normal through TextureLib and holds its record for the
draw scope. IRPNormalSurface is an optional separate RP9 interface; existing
retail interfaces and model layouts are unchanged. Reset happens before companion
effects, including on scope exit. Missing texture/interface keeps the native path.
Binding by the three explicit material names is intentionally a prototype; this
does not introduce a general-purpose normal-map material authoring format.

Normal surfaces accept native SRCALPHA/INVSRCALPHA fading, preserve fog, material
alpha and shadow ambient, and retain the same shader at each distance. s14 is
linear; c97 contains strength. Existing ice/cockpit/glass behavior is preserved.

Reproduce from repository root:
  python -m venv src/obj/asteroid_normals/venv
  src/obj/asteroid_normals/venv/Scripts/python -m pip install numpy pillow
  src/obj/asteroid_normals/venv/Scripts/python tools/asteroid_normals/generate.py
  Build Release Win32 client and RP9 with FreelancerRp9=1.
  python tools/asteroid_normals/check.py
  python tools/asteroid_normals/install.py
  python tools/asteroid_normals/install.py --apply

Install checks source hashes/processes, backs up all replaced files, verifies
copies, and rolls back on failure. --restore BACKUP restores the previous files.
After installation it warms the real game cache and verifies 10/10 cache hits.
GPU tests use an isolated cache and do not replace this step. To warm an already
installed version: python tools/asteroid_normals/warm.py
Generated assets, GPU previews and manifests are in src/obj/asteroid_normals.
Manual check: fly past rotating dynamic rocks in ku_tgk; check the sunlit edges,
fog entry/exit, distance fading, cockpit and third-person views. GPU fixtures
cover rendering mechanics but do not replace this in-game aesthetic check.

Performance measurement (2026-10-26, RTX 5080, i7-10700K, 1920x1080):
  python tools/asteroid_normals/benchmark.py
  bin/asteroid_normal_route_check.exe --benchmark
GPU fixture uses actual meshes, pretransformed and batched into one VB to isolate
GPU geometry/pixel work from per-object CPU submission. It alternates four modes
and records 13 valid samples of 30 repeated draws after warm-up. Depth is established
before timed draws; results are steady visible-surface cost, not an entire game frame.
One directional light, no scene shadows/postprocessing. Output in benchmark.txt.

GPU median (microseconds):             native    old PS   new PS off  new PS on
  90 small rocks (60 px bounds)          6.633    10.693      11.059     12.613
  90 large rocks (160 px bounds)        13.940    46.325      47.974     55.747
  Fullscreen textured quad stress       7.232    54.826      57.095     64.672
Thus native-to-normal GPU delta is about 0.006/0.042/0.057 ms in these fixtures.
Normal sampling/frame reconstruction alone adds about 14-16% to the pixel surface
pass; migration from native vertex lighting accounts for most of the total delta.
Normal-disabled new PS costs 3-4% more than the old no-shadow surface PS here;
this must not be generalized to all shader variants or whole-frame FPS.

CPU production route benchmark rotates the world matrix per object, invokes the
real ExSurfaceBegin/End and normal interface, with no draw or texture-library lookup.
Native eligibility: 0.029 us/object; normal route: 0.681 us/object (~0.061 ms/90).
This isolates route/state-upload cost, not total game CPU time. Texture lookup and
record ownership occur once per visible material group, not once per asteroid.
No installation/game rendering behavior changes are made by the benchmarks.
