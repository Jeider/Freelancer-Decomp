# Particle improvements (FREELANCER_PARTICLE_FX)

Not in the original game. Build flag `FreelancerParticleFx` (client and `alchemy.dll`); the
soft particles themselves live in `RP9.dll` and need the Direct3D 9 pipeline with an INTZ scene
depth. Everything is switched in `port.ini`:

```ini
[Render]
soft_particles_effects = 6   ; metres; 0 = off
soft_particles_clouds = 60   ; metres; 0 = off
cloud_sort = 1
cloud_smooth_fade = 1
```

The block above is an opt-in example. The workspace `bin/port.ini` has
`soft_particles_effects = 0`. On 2026-10-27 the user's installed configuration was
also set to 0 at their request, disabling this added fade for explosion/fire/smoke
particles, including appearances using `XP_HERM`. Original ALE/texture data remain
unchanged. This is depth fading, not heat refraction; restart the game after changing it.

## Soft particles

Retail particles are flat sprites with a hard depth test: where an explosion, a fire or a
nebula puff passes through a ship, a station or an asteroid, it is cut along a sharp line.

`IRenderPipelineEx::SetSoftParticles(kind)` asks RP9 to draw the following fixed-function draws
through a built-in shader (`RP9Ex.cpp`, no `DATA_EXTRA` needed). The shader repeats what the
fixed-function pipeline did (transform, stage 0 select / modulate of texture and diffuse, fog)
and multiplies the alpha (for additive `ONE` blends also the colour) by
`saturate((scene depth - particle depth) / fade distance)`. The depth test becomes that fade, so
the scene depth (INTZ) can be sampled.

A draw qualifies only when it looks like a particle draw: `XYZ | DIFFUSE | TEX` vertices, alpha
blending with `SRCALPHA` or `ONE` as the source factor, depth test on, depth write off, lighting
off, stage 0 a select or modulate of texture and diffuse, stage 1 disabled. Anything else draws
exactly as before.

Users:
- `alchemy.dll`: the draws of `FxBasicAppearance` (explosions such as `XP_HERM`, fire, smoke),
  `FxRectAppearance`, `FxPerpAppearance` and `FxOrientedAppearance` (kind `effects`);
- the nebula interior puffs, `TexturePanelDrawClouds` (kind `clouds`).

## Nebula puffs

- `cloud_sort`: the puffs are drawn farthest first, so overlapping translucent puffs blend
  in the right order instead of flickering.
- `cloud_inside_only`: the puffs are drawn only while the camera is inside the nebula zone,
  and only those inside the zone, so the puff sphere is not seen from outside.
- `cloud_smooth_fade`: the fade at the edge of the puff sphere and the near fade
  (`near_fade_distance`) use smoothstep instead of a linear ramp, so puffs do not pop.

## Per-cloud keys in `[Clouds]`

Optional keys in a `[Clouds]` section (a nebula's, or a ring's such as a system-wide light
cloud); the original game ignores them. They apply only with `FreelancerParticleFx`.

```ini
[Clouds]
puff_facing = individual   ; each puff faces the camera point with its own stable angle
puff_spin = 0.5            ; degrees per second of slow rotation (0 = none)
soft_fade = 2000           ; soft particle distance in metres for this cloud (0 = port.ini's)
far_fade = 0.55, 1.0       ; smooth far fade between these fractions of the puff sphere radius
depth_tint = 20, 40, 110, 0.6     ; aerial perspective: colour (0..255) and strength (0..1)
depth_tint_range = 11000, 22000   ; metres from the camera where the tint starts and is full
sun_scatter = 1.2, 0.6            ; light scattering: strength, forward bias (-0.9..0.9)
```

- `depth_tint`: far puffs lean towards the given colour (smoothstep over `depth_tint_range`),
  the way distant air turns bluish; the eye reads it as distance.
- `sun_scatter`: the light is the centre of the zone that owns the clouds (for a ring round a
  sun, the sun). A puff the camera sees towards the light gets brighter and a little denser
  (Henyey-Greenstein phase, normalised to its forward peak), one lit from behind the camera
  dims to 0.6. In a nebula the light is the nebula zone centre, so it is meant for rings.

- `puff_facing = individual`: retail turns every puff by one shared up axis that follows the
  camera and keeps the quads parallel to the screen, so very large puffs swim and turn when the
  camera turns. Here each quad faces the camera point and keeps its own angle.
- `far_fade`: replaces retail's linear fade between 0.7 and 1.0 of the sphere radius
  (squared distances) with a smoothstep between the two given fractions.

## Engine flame material batching and end-on footprint (2026-10-21)

Audited FCliEngineEquipFx::Update against Freelancer.exe.txt 00528020..00528228:
engine kill targets zero, normal thrust maps to MAX_ENGINE_FX_THROTTLE (0.9),
and IFxEffect::Slot6 forwards the throttle to node outer time. Zero is an ALE
curve input, not render opacity. The native Alchemy state block and authored
BasicApp_BlendInfo remain unchanged. Liberty flame uses SRCALPHA/ONE (5,2).

A fixture loads the actual gf_li_smallengine01_fire.ale node-library payload
through ReadNodeLibProperties. Its beam emitter has nonzero idle frequency
98.0946/s, full-throttle frequency 149.5533/s, lifetime 0.069722 s and initial
alpha 0.765257. A synthetic 60 Hz emission/integration fixture retains live
particles at both outer time 0 and 0.9. No engine names/colours or ALE assets
are overridden by the fix.

The previous four appearance queues collected every node of a family and drew
all geometry using only the head's texture, blend pair and transform. The port
now flushes contiguous compatible runs: same family, authored texture CRC,
resolved GPU texture, blend pair and flags. Non-basic families additionally
require identical node world transforms; basic vertices already bake their
individual transforms. This preserves submission order and coalesces compatible
nozzles without applying another effect's material to the engine core. The
comparison is an internal C++ method, with no component ABI/layout change.
Per-node solar opacity remains captured through deferred geometry filling.

Basic motion-blur billboards also retain a camera-facing footprint when their
projected streak axis is zero (view exactly along exhaust or zero velocity).
The old cross products produced a zero-area quad. Nondegenerate streaks keep
the traced retail arithmetic. The engine fixture verifies nonzero geometry at
idle and full throttle viewed along the exhaust, material isolation and retained
compatible runs; colour and solar-fade regressions pass. These checks do not
replace user evaluation of the actual ship/nozzle assets in-game.

## Cockpit weapon and shield brightness (2026-10-29)

The first-person camera draws weapon effects at 33% brightness and shield effects
at 20%. Muzzle flashes/lights, projectile particles and code beams, hull impact
effects and RP9 weapon glints use the weapon factor. Shield collisions, munition
hits (including their splash) and collapse effects use the shield factor.

`cockpit_effect_brightness` records the category when an effect or light is created
and erases it on destruction. Shield creation scopes take precedence over nested
weapon scopes. Classification follows the live instance, including effects detached
into world space, without altering retail object layouts or shared archetypes.

Each draw uses its actual camera: external, rear, turret and HUD views use full
brightness even if the effect was born in the cockpit. ALE uses render opacity
(RGB for ONE source blending, alpha for SRCALPHA); code beams dim final vertex RGB
before copying animated geometry. Light uploads scale diffuse/specular/ambient RGB
and restore the CPU descriptor, preserving radius and animation. RP9 weapon glint
colours receive the same weapon factor. Other effects, simulation, damage, sound,
particle emission and effect duration are unchanged.

`python tools/cockpit/check_effect_brightness.py` exercises the production draw
functions with captured particle, beam and light boundaries in RP8/RP9 builds:
camera switching, repeated draws, nested shield splashes, recycled addresses,
alpha/additive blending, solar opacity composition and light descriptor restoration.
Release client compilation is also required; these checks do not replace an in-game
visual check of the player's weapon and shield assets.

## Nozzle overlay reverted (2026-10-21)

Remove the optional nozzle-glow interface, geometry scope, enlarged stationary
core, camera depth displacement and three additive layers. The added overlay
produced an excessive red glow on another player ship. Ordinary engines now
render only their authored ALE particles. Keep the earlier compatible material
batching and degenerate streak-axis fixes, solar ALE opacity, and all subsequent
solar-core, nebula and ray-depth/border corrections.

## Camera-facing FLBeamAppearance (2026-10-30)

Ordinary ALE beams now use one camera-facing ribbon and the existing material
batcher. In executable-adjacent `port.ini`, `[Render] beam_camera_facing = 1`
is the default; `0` restores the original two crossed ribbons. Particle endpoint
selection, width/colour/opacity ramps and animated atlas coordinates are retained.
The ribbon uses two triangles per span, or four when the authored centre-vertex
flag is set (the original cross uses four/eight). A stable camera-axis fallback
handles the undefined facing direction when viewed along the beam. Like any flat
ribbon, its projected length contracts in an exactly axial view; it is not a tube.

The expensive tube renderer remains available for explicitly selected effects:

```ini
[Render]
beam_camera_facing = 1
beam_volume = 1
beam_volume_nodes =
```

An empty node list (also the code default) selects no volume beams and avoids
compiling their shaders. For a special effect, set `beam_volume_nodes` to its ALE
node name, or a comma-separated list. Matching remains case-insensitive substring
matching; `*` explicitly selects all compatible additive nodes and is expensive.
The selection refers to the appearance node instance name, not the weapon INI
nickname. `beam_volume = 0` disables the volume path regardless of the list.
Changes require restarting the game.

The single-ribbon path also honours the existing `beam_volume_trail_nodes`
(default `trail`) and `beam_volume_trail_fade` (default `10`, metres, `0` disables)
settings, independently of `beam_volume`. Compatible additive trail nodes fade
near the current camera; unrelated laser nodes and the distant trail stay visible.
As in the volume path, selection is by node name and camera depth, not ownership.
The lightweight path applies the smoothstep fade to vertex colours, including
centre vertices, and interpolates across the existing triangles. It scales RGB
for ONE/ONE and alpha for SRCALPHA/ONE, preserving prior opacity/brightness factors.
It adds no geometry, shaders or draw calls and retains material batching. Unlike
the volume shader's per-pixel fade, its approximation depends on particle spacing.

The tube has 24 sides: 48 triangles per straight span, 384 per subdivided curved
span, plus 48 triangles for its two end caps. It also builds geometry on the CPU
and enters/exits an RP9 pass per node instead of using ALE material batching.
Those are geometry counts, not measured frame-time multipliers.

Validation: `python tools/beam_volume/check_ribbon.py` compiles the actual ALE
ribbon-emission method with a captured draw context and checks topology, atlas
coordinates, colour, width, bends, camera orbit and axial fallback.
`python tools/beam_volume/check.py` retains D3D9 coverage of the optional tube
shader and actual RP9 route. In-game appearance and FPS still need gameplay checks.
