Black-hole optimization, 2026-11-13

Preserved: full resolution, step budget, integration strides, noise volume,
disc/spiral/smoke, haze, nearby gas, polar funnels, lensing and colour parameters.

Changes:
- Hoist ray-constant disc-layer and camera immersion calculations out of the march.
- Reuse angular momentum cross product and planar radius.
- Use multiplies for positive R^5 and accumulate squared glow distance (sqrt once).
- Skip gas shading only when its near-fade contribution is exactly zero.
- Check polar height bounds before evaluating the expensive funnel envelope.

Compiler investigation:
FXC /O3 failed with SM3 temporary register limit exceeded.
Production D3DX9_43 flags=0 compilation was cancelled after several minutes.
Do not remove RP9_SKIP_OPTIMIZATION based on this experiment. Flags=4 remains;
baseline/candidate compile with production compiler in about 1.1-1.3 seconds.

GPU comparison: real D3D9 HAL, RTX 5080, 1920x1080, isolated PSMain.
Identical constants/textures, deterministic production 64^3 noise, background
pattern and foreground depth occluder. Five poses include elevated, edge-on,
near/inside gas and layered disc, two simulation times. Alternating A/B order,
warmup and median of seven samples (eight draws per sample), disjoint timestamps
discarded. Copies/composite and the rest of the game are excluded.

Final measured median milliseconds (baseline -> candidate):
elevated:       0.923 -> 0.884 (1.044x)
edge-on:       1.665 -> 1.553 (1.072x)
near gas:      3.558 -> 3.281 (1.085x)
inside gas:    4.088 -> 3.687 (1.109x)
layered disc:  2.130 -> 1.967 (1.083x)

All five RGB image comparisons: maximum difference 1/255, zero pixels with error
over 2/255. These are controlled comparisons, not in-game screenshots or a test
on GTX 1060. Do not extrapolate total game FPS directly from these ratios.

Reproduce from repository root:
python tools/black_hole_opt/compile.py tools/black_hole_opt/baseline.hlsl src/obj/black_hole_opt/baseline 4
python tools/black_hole_opt/compile.py DATA_EXTRA/SHADERS/black_hole.hlsl src/obj/black_hole_opt/candidate 4
python tools/black_hole_opt/compile.py tools/black_hole_opt/baseline.hlsl src/obj/black_hole_opt/vertex 4 VSMain
python tools/black_hole_opt/build.py
src/obj/black_hole_opt/bench.exe src/obj/black_hole_opt/baseline.cso src/obj/black_hole_opt/candidate.cso

Install with tools/black_hole_opt/install.py --apply. Restart the game to reload
the shader; RP9's source-based cache key changes automatically. The installer
does not change port.ini, DATA, binaries or the user's selected quality level.
