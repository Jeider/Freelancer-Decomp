# Renderer performance

Install Freelancer.exe, RP9.dll, Common.dll and the shaders (`surface_material.hlsl`,
`local_shadow.hlsl`) together: the shader's sampler slots and constants changed with RP9.
Model files and their LODs are unchanged.

## Shadows (2026-10-22)

Measured on an RTX 5080, 1920x1080, one full-screen sun-facing receiver layer with a
checkerboard of casters inside the full-quality distance (`surface_bench`, D3D9 timestamp
queries). Output with identical settings matches the previous shader within 1/255.

| Configuration | GPU ms per layer |
|---|---|
| Before: 8192 maps, 64 search / 192 filter taps | 3.73 |
| 4096 maps, 64 / 192 | 2.41 |
| **4096 maps, 16 / 32 (new defaults)** | **0.49** |
| NPC moderate tier (8 / 8) | 0.20 |
| NPC simple tier (one bilinear comparison) | 0.08 |
| Surface facing away from the sun: before / now | 2.20 / 0.07 |
| Receiver without shadow (`SURFACE_NO_SHADOW` variant) | 0.06 |

- `shadow_near_resolution` / `shadow_far_resolution` (default 4096; the old
  `shadow_resolution` is the fallback). Video memory at 4096: 256 MiB (two R32F maps, the
  static cache and the D24X8 depth surface) instead of 1 GiB at 8192.
- `shadow_search_samples` / `shadow_filter_samples` default 16 / 32 (were 64 / 192).
  Penumbras at 16/32 and 64/192 are visually equivalent in the comparison captures.
- Surfaces facing away from the sun take one bilinear comparison instead of PCSS: their
  visibility only scales the faint reflection on the unlit side.
- Receivers without a shadow this frame use a pixel shader compiled without the shadow code.
- The far map's static station cache is rebuilt every `shadow_static_cache_seconds` (10)
  instead of every second when nothing changed.

### NPC ships (the player's ship is unchanged)

By camera distance to the hull: up to `shadow_npc_full_distance` (100 m) the full filter,
to `shadow_npc_moderate_distance` (300 m) a fixed 8 / 8 filter, to
`shadow_npc_simple_distance` (500 m) a single bilinear comparison; beyond that the ship
neither receives nor casts a shadow. NPC ship shadows reach `shadow_npc_ship_length`
(100 m) behind the hull; stations, asteroids and the player keep `shadow_max_length`. The
caster's reach is stored as the sign of its shadow-map depth, so it costs nothing extra.

## Per-draw CPU work

The surface route keeps its device state between draws: the environment map is on sampler 10
and the shadow maps on 8/9 (fixed function never uses them), shaders stay bound until a
fixed-function draw, and pixel constants are re-sent per block only when they changed. A
repeated surface draw now issues one device call (its vertex constants) where it used to
issue about forty (shader bind/unbind, stage 1-3 save/restore, all 95 constant registers).
Shadow-map and antialiasing passes re-capture one state block instead of creating a
D3DSBT_ALL block each time. `port.ini` values are cached (re-read when the file changes)
instead of parsed by `GetPrivateProfileString` on every call, about 20 times per frame.

## Antialiasing

`fxaa = 1` now filters the whole frame at SwapBuffers, HUD and target wireframes included;
`fxaa = 2` keeps the old scene-only pass before the HUD; `fxaa = 0` is off.

## Measuring

`render_stats = 1` logs `render perf:` every two seconds: FPS, GPU milliseconds per frame
with the shadow-map, Ex-pass (nebula, sun rays) and FXAA shares, and draw/state counts.

## Unchanged, by decision

- `surface_instancing` and `state_cache` stay off (a reported in-game regression).
- Opaque objects keep the retail back-to-front order: transparent parts of a node are drawn
  with that node, so front-to-back sorting would draw far opaque hulls over near glass.
- The shadow maps keep an R32F colour target: its sign carries the NPC caster reach, which a
  depth-only (INTZ) map cannot store.

Shader bytecode for all surface/shadow variants is pre-built in `ShaderCache` (a cold surface
compile takes about 18 s); `tools/warm_surface_cache.cpp` regenerates it.
