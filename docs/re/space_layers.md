# Space layers (port-only, RP9)

World-anchored layers of camera-facing sprites, each in its own distance shell around the camera, so open
space has parallax between the star sphere and the ship. One mechanism serves faint far veils (3-30 km),
near dust and debris (30-400 m), a sparse star-point layer, etc. Code: `Client/space_layers.cpp`.

Switch: `port.ini [Render] space_layers = 1`; also off with the Effects game option off. Drawn once per
frame right after `TexturePanelsDrawAll` in the no-field-enclosure path (not inside a nebula).

## Data

`[SpaceLayer]` sections of a system ini (parsed in `star_sys.cpp` next to `[Dust]`), at most 8 per system.
Layers are cleared on system load and in `StarSysLeave`. A layer with no resolvable shape is dropped.

| key | default | meaning |
|---|---|---|
| `shapes` | - | texture-shape ini loaded into the layer's own `FShapeDB` |
| `shape` | - | shape name, repeatable (up to 8); each sprite picks one by hash |
| `color`, `color_b` | 255,255,255 / = color | 0..255; per-sprite blend between them |
| `alpha` | 0.06 | base opacity |
| `size` | 800, 2500 | min, max half-size in metres |
| `near_distance`, `far_distance` | 3000, 30000 | the shell, metres |
| `near_fade`, `far_fade` | 0.3, 0.3 | fractions of the shell over which alpha ramps in / out |
| `cell` | max(far/12, size max) | grid cell, metres |
| `density` | 1.5 | sprites per full cell (0..4) |
| `clump_size`, `clump_coverage`, `clump_softness` | far*0.4, 0.45, 0.1 | the clump field (as the nebula puff layer) |
| `count` | 300 | most sprites drawn, nearest first |
| `blend` | alpha | `alpha` or `additive` |
| `lit` | 1 | colour by `SolarSunlitAt` (planet shadows) and forward scatter toward the sun |
| `ambient_floor`, `forward` | 0.35, 1.5 | shadow floor; forward-scatter gain (`1 + forward * max(0, dot)^8`) |
| `spin`, `rotation_step` | 2, 0 | deg/s per sprite (times hash in -1..1); 0 = free angle |
| `wind` | 0,0,0 | m/s, the whole layer drifts |

## Placement

Cells of size `cell` in a grid evaluated at `Q = camera - wind*T`; only cells whose box meets the shell are
visited (cell enlarged so no axis exceeds 24 cells). A cell holds `min(4, ceil(clump*density*2 - 0.25))`
sprites from a splitmix64 hash of (i, j, k, n, layer); a sprite is kept with probability
clump(X)/clump(cell centre). Nothing is stored per sprite.

Judgement call: the cell walk (the expensive part, a 3-octave noise per cell) is cached per layer and redone
only when Q has moved half a cell; the cache covers the shell widened by that margin and the per-frame pass
filters exactly (distance, behind-camera, `count` nearest). Results are identical to a per-frame walk.

## Drawing

View-space quads (identity modelview), rotated by the sprite angle, UVs from the shape rectangle, batched per
texture, alpha layers sorted far to near. Depth test on, depth write off, cull none, lighting off; SRCALPHA /
INVSRCALPHA (or ONE for additive). RP9 soft particles (`RPExSoftClouds`) with fade `(size min + size max)/4`.

## Space haze (2026-10-23)

Big alpha sprites are expensive (overdraw), so the cheap depth cue is one fullscreen pass instead:
`space_haze.cpp` / `DATA_EXTRA/SHADERS/space_haze.hlsl`. Per pixel it reads the scene depth once and
samples a world-anchored, tileable 3D noise (32^3, generated once on the CPU: R = 4-octave value fBm
normalised to its 2nd..98th percentile, G = an independent 3-octave fBm for the colour mix) at 2..4
fixed distances ("shells") along the view ray, front to back. The sample point of a shell is
`(camera - drift * time) / scale + dir * distance / scale` in tile units, so near shells slide faster
than far ones when flying (parallax). The camera part is wrapped in double precision on the CPU (period
100 tiles, a multiple of 10 so the 2.7x detail lookup is continuous across the wrap), keeping floats small.

Per shell: `n = (noise(Q).r + detail * noise(Q * 2.7 + 17.3).r) / (1 + detail)`,
`c = smoothstep(coverage - softness, coverage + softness, n)`, `a = alpha * c * visibility`,
`visibility = saturate((sceneDistance - D) / (D * occlusion_softness))` (sky = depth 1.0 sees every shell),
colour `lerp(color, color_b, noise.g) * light`, `light = ambient + (1 - ambient) * (0.5 + 0.5 cosSun) +
forward * pow(saturate(cosSun), forward_power)` (1 with no sun). Output is premultiplied
(`rgb`, `1 - transmittance`), blended ONE / INVSRCALPHA with no depth test. Cost: 1 depth read + 2 noise
reads per shell, about 228 ps_3_0 slots, 16 pixel constant registers (c0 ProjZ, c1 ViewRect, c2 ProjInv,
c3..c5 camera rows, c6..c9 shell origin + D/scale, c10 shell metres, c11/c12 colours, c13 coverage
params, c14 lighting, c15 sun direction + shell count).

Drawn in `SpaceObjDrawPass` right before `SpaceLayersDraw`, only without a field enclosure.
Gate: `[Render] space_haze` (bin/port.ini, default 1), the effects game option, a parsed
`[SpaceHaze]` in the current system ini (the last one wins) and `RenderEx::IsAvailable()`.

`[SpaceHaze]` keys (all optional): `color` r,g,b 0..255 [120,150,200]; `color_b` [= color];
`alpha` [0.15]; `shell` = distance_m, scale_m (repeatable, up to 4, sorted nearest first; none ->
2500/2000, 9000/6000, 30000/18000); `coverage` [0.55]; `softness` [0.2]; `detail` [0.35];
`drift` = x,y,z m/s [0,0,0]; `ambient` [0.45]; `forward` [2.0]; `forward_power` [6];
`occlusion_softness` [0.1].
