# Asteroid and debris relief normals (RP9)

Not in the original game. Part of the Direct3D 9 renderer (`FreelancerRp9`); switched at run time by
`port.ini` `[Render]`, all keys restart-required:

```ini
rock_normals = 1          ; master switch
rock_relief = 2.4         ; shared rock detail strength, 0..4
rock_macro_relief = 3.0   ; relief read from the authored texture, 0..4
rock_lod_full = 300       ; no effect since the first tier took the second tier's look
rock_lod_macro = 700      ; metres: the texture's own relief stops here
rock_lod_coarse = 1000    ; metres: from here only large lumps (one cheap sample)
rock_lod_end = 2000       ; metres: large lumps only out to here
rock_lod_far = 5000       ; metres: the simplest normals out to here, then fading out
rock_asteroid_gloss = 0.12 ; 0 dull dust .. 1 polished
rock_debris_gloss = 0.55   ; scrap finish
rock_shadows = 1          ; 0 = rocks take no local ship / hull shadows
rock_parallax = 0         ; deepest parallax shift in metres (0 = none)
rock_pits = 0             ; 1 = the same relief inside out
rock_debug = 0            ; 1 = Diagnostics\rock_debug.txt
```

## Quality by distance

The shader drops work with distance, never abruptly (each tier crossfades into the next over +-20 %). Up close
there is one look: a single scale of detail plus the texture's own relief and crevice darkening (the earlier
two-scale first tier is gone; `rock_lod_full` is kept as a key but changes nothing).

| Distance | What is drawn |
|---|---|
| up to `rock_lod_macro` (700 m) | one scale of detail, the texture's own relief, crevice darkening |
| to `rock_lod_coarse` (1000 m) | one scale of detail (the texture's relief has faded out) |
| to `rock_lod_end` (2000 m) | large lumps only: one cheap sample at a coarse scale |
| to `rock_lod_far` (5000 m) | the simplest normals: one sample of very large lumps |
| beyond | fading to nothing over the next 30 % |

Big rocks (radius over 250 m) scale every limit by radius / 250 (up to 8x), so an Arch chunk keeps its relief from
far away. The far rocks (`far_rocks`) and the billboards are separate and unchanged.

## What it does

Every asteroid and every piece of debris gets strong relief lighting, with no per-material profile and no
authored normal map:

- **Macro relief.** The material's own texture is read as height (dark = recess, bright = ridge) and its slope
  over the surface tilts the normal. The height scales with the object's size, so a boulder and a moon chunk
  both read.
- **Shared detail.** One 512x512 tiling map, built in code at device creation (about 5 MiB with mips, no file),
  holds lumps, chips, grit and ridged fractures. It is sampled at up to three scales (see below).
- **Crevices.** Cavity darkening from the detail map and the texture's dark spots.
- **Finish.** Rock is dusty and rough; scrap is harder, steeper and a little glossier. The authored shininess is
  ignored.

Slopes are strong on purpose (capped near 67 degrees, never flipped).

## Scope

| Object | Where the scope opens |
|---|---|
| Dynamic, medium and solar asteroids, debris objects | `DrainBucket` (`space_scene_obj_draw.cpp`), per node |
| The rocks of an asteroid field (the merged cube mesh) | `CliAsteroidDrawNearField` (`cli_asteroid.cpp`), per field |

Debris is recognised by the object kind, or by "debris" in the model or field name.

**Left alone:** nomad, lair, dyson (their own surface profiles), and ice (`ast_icecrystal*`, `*_ice_*`, fields
named `*_ice*`): they keep the ice shader. The far rocks (`far_rocks.hlsl`) and the billboards are not
changed.

## Implementation

- `IRPRockNormals` (`include/render/IRPRockNormals.h`, IID `RP9_IRPRockNormals_v1`): `SetRockNormalScope(class,
  radius)`. Separate from `IRPShipNormals`; no retail or RP9Ex vtable changed.
- `RP9RockNormals.inl`: scope state, the procedural map, settings.
- `RP9Ex.cpp` `ExSurfaceBegin`: opaque lit materials of the object in scope take the surface shader's
  `SURFACE_ROCK` variant (4 pixel shaders: shadow receiver or not, cube environment or not). Sampler `s13`,
  constants `c97` and `c98`.
- `surface_material.hlsl` `RockReliefNormal`: explicit gradients, so the samples can sit in a branch. The
  derivative frame needs no tangent channel and respects mirrored UVs. Sun shadows still use the geometric
  normal.
- Two-pass detail materials (`DcDtBt`) draw their base pass through this path; the multiplied detail pass is a
  blended draw and is unchanged.

## Cost

The variant is smaller than the ordinary surface shader (the ice and cockpit branches are removed). It adds 4
texture reads (2 detail, 2 for the macro slope) per pixel inside the fade range and none beyond it. No GPU
timing has been taken yet.

## Not covered (yet)

- `far_rocks` (thousands of far lit rocks) and the asteroid billboards.
- Materials with an environment cube and a second stage that the surface shader already refuses.
- Per-model tuning (a hand-authored height or normal for hero asteroids).
