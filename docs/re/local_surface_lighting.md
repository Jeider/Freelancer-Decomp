# Local surface lighting and shadows on RP9

The reflective surface profile, solar visibility and equipment/muzzle light fixes
are implemented. Experimental local shadows are connected to the game frame
after explicit user approval. See [validation status](local_shadows_validation.md).

## What the current port provides

RP9Ex provides SM3 programs, FP16/R32F targets, INTZ scene depth, explicit
constants, texture bindings and pass state restoration. Its extended draw API
currently exposes fullscreen quads and UP primitives. Ordinary ship/station
meshes still use the existing material/mesh pipeline, with the optional surface
profile described below. They are not shaded by the nebula shaders.
`flmaterials/MaterialImpl.cpp` exposes legacy
diffuse, specular colour/power, opacity, emissive and texture parameters.
The experimental shadow-map backend scopes receivers around eligible object draws.
A fullscreen darkening effect cannot reliably
implement the requested planet exclusions.

## Implemented reflective surface profile

`port.ini`, `[Render] surface_shaders = 1` enables
`DATA_EXTRA/SHADERS/surface_material.hlsl`. Set it to `0` to restore the legacy
material path. The default when the setting is absent is disabled. Restart the
client after changing the setting or shader. Deploy the shader alongside RP9.dll.

An active camera-space reflection envmap selects the profile automatically;
there are no ship/station name checks. This also admits supported reflective
asteroids and preserves their authored envmap texture and transform. Both ordinary
2D envmaps (MIP0/MIPS) and native DDS cubemaps (CUBE) are supported. The backend
selects a separate samplerCUBE pixel shader for cube textures; it retains all
three reflection-vector components and supports disabled/COUNT3 cube transforms.
The texture entry's name or TGA suffix does not determine its actual GPU type.
Supported
geometry is opaque, lit, rigid XYZ/NORMAL with one, two or three ordinary UV sets,
with an envmap alone or a standard diffuse stage followed by the envmap.
Transparent, unlit, skinned, RHW and unsupported multi-stage materials retain
their legacy path. A missing shader or compilation failure also falls back.

The shader uses per-pixel GGX/Schlick specular, bounded roughness from authored
specular power, a broader secondary gloss lobe, existing diffuse/emissive/ambient inputs, and up to eight enabled
directional, point or spot lights. Native linear/exp/exp2 fog is applied in the
surface shader. Rendering stays in the existing legacy colour pipeline; this
is not a complete linear/HDR PBR conversion. No normal maps are inferred and
no shadow pass is added. The profile replaces shading during the existing mesh
draw, rather than drawing the mesh a second time.

The envmap's authored SELECTARG1/MODULATE/MODULATE2X/MODULATE4X/ADD colour
operation is retained on the diffuse lighting. In particular native mid-grey
MODULATE2X maps retain their bright moving bands instead of being reduced to
a tiny Fresnel-only additive term. An artistic reflection layer remains visible
face-on and strengthens towards grazing angles. Direct highlights and emissive
details are composed separately so dark envmap regions do not erase them.
The staged version additionally reduces the envmap's constant fill on the unlit
side and applies a soft shoulder to added highlights, without remapping the
authored diffuse or emissive texture. These changes accompany the shadow build.

The lit-face finish now layers a tighter clear-coat highlight over a brushed
anisotropic lobe and a deliberately stylised wide satin sweep. The brushing axis
comes from screen derivatives of the authored UVs and view-space position, with
a safe tangent fallback for degenerate UVs. Texture luminance gently varies
roughness and finish strength, without deriving bump normals or using animated
noise. Normal variance broadens sharp lobes to reduce specular undersampling.
The layers use the existing directional/point/cone lights and their attenuation;
the solar layers respect the existing local shadow visibility. Plain diffuse
shadow receivers do not acquire the reflective profile. Added gloss is compressed
towards a 0.94 shoulder; emission is added afterwards. The authored diffuse/env
operation remains intact, so this is still an artistic legacy-colour finish,
not an HDR or normal-mapped material replacement.

`[Render]` controls (restart required): `surface_highlights=1.35` scales direct
gloss (0..4), `surface_clearcoat=0.9` controls the bright tight accent (0..3), and
`surface_brushed=0.8` controls the broad elongated finish/sweep (0..3). These
defaults apply to all supported envmapped hulls: ships, capitals, stations and
other opted-in geometry. They do not identify object names or replace envmaps.
The three settings are uploaded through PS register c75; the optional material
interface and retail vtables remain unchanged.

The material GPU readback checks layered frontal gloss against the original
lobes, the broad off-axis finish against its disabled state, roughness response,
fog, cone lights and emissive preservation. A rendered before/after test sphere
also uses the original envmapbasic DDS cube. These tests do not replace review
of actual hulls in game. The source-bytecode cache naturally invalidates the
modified shader and the prepared 2D/cube records can be deployed with it.

`IDAComponent::QueryInterface("RP9_IRPSurfaceShader_v1", ...)` exposes the
independent `IRPSurfaceShader` interface without changing retail/RP9Ex vtables.
`SetSurfaceShader(RPSurfaceReflective, roughness, environmentStrength)` can
override the automatic profile. Reset with
`SetSurfaceShader(RPSurfaceAuto, 0, -1)` after the material's draws; use
`RPSurfaceLegacy` for a material-specific opt-out. Positive roughness is clamped
to 0.28..1; nonpositive uses the material power. Negative environment strength
uses 1.0; explicit strength is clamped to 0..2. Future ice-specific profiles can
extend the profile enum through the same entry point.

Validation: the actual D3D9 backend route was exercised on HAL, including UP and
indexed UP draws, light feed, shader teardown/recreation, stage/sampler restoration
and unsupported-material fallback. A separate GPU readback checked light,
roughness, fog and spot cone responses. These checks do not establish visual
quality or frame cost in a populated game scene.
Cube validation also loaded the exact 64x64, six-face DDS payload from the mod's
`DATA/FX/envmapbasic.mat`, compared reflection-on/off GPU readback, and exercised
COUNT3, env-only stage 0, transitions back to 2D, and shader resource teardown.

## Recommended surface shader

Use a per-pixel specular/glossiness model with a GGX specular lobe and Schlick
Fresnel. Preserve the mod's diffuse textures and authored Sc/Sp where present;
convert gloss to bounded roughness and supply conservative defaults when absent.
Do not make every painted hull a mirror or infer metallic material from brightness.
Preserve emissive windows, navigation lights and existing environment maps.

Normal mapping should be optional per material, with a flat normal fallback.
Use authored normal maps where available. Do not globally turn colour textures
into height: paint, markings and lighting baked into them are not geometric relief.
Derive a tangent frame from mesh tangents or pixel derivatives for legacy meshes,
and test mirrored UVs before enabling it broadly. Work in linear colour inside
the shader, with a conversion boundary that avoids double gamma on legacy assets.

Use the same per-pixel lighting function for the sun, point lights, spotlights
and animated muzzle lights. Spotlights must include full hardpoint transform,
range attenuation, inner/outer cone interpolation and falloff. The nebula ambient
must feed the indirect term; self emission must remain visible in a shadow.
Stage rollout on one player hull and one station before opting in other materials.

Reference: [Filament material documentation](https://google.github.io/filament/Materials.md.html)
documents normal inputs, specular/glossiness and roughness; the proposal is an
SM3 adaptation, not a port of Filament. The likely OpenGL reference is
Schmackbolzen's Advanced Renderer, but its Starport release page was inaccessible
during this review; no claims about its internal shaders have been verified.

## Exact shadow participation rules

| Caster | Receiver | Proposed range |
| --- | --- | --- |
| Ship | Ship, including itself | Local 15 km neighbourhood |
| Ship | Station | Local 15 km neighbourhood |
| Station | Ship | Local 15 km neighbourhood |
| Station | Station | Local 15 km neighbourhood |
| Ship or station | Planet / atmosphere / cloud shell | Never |
| Planet | Ship | Up to 20 km above the planet surface |

The planet distance is receiver-to-surface, not receiver-to-centre. Planets,
atmospheres and their cloud layers must have an explicit `receive_local_shadow=0`
classification before entering either surface or shadow passes. HUD, sky,
nebulae, transparent effects and asteroid fields stay outside the first rollout.

### Ship and station shadows

Use a directional sun shadow map with a small high-resolution near region and
a coarser outer region, rather than one 15 km map that loses fighter wing detail.
A starting quality preset is a 2048 map covering the nearest 1--2 km and a
second map covering out to 15 km. The exact outer resolution needs measurement;
it must not be advertised as a performance result before testing.

Clip receiver eligibility to the local region with a smooth last 2 km fade.
Select casters by bounds and light frustum, not centre alone, so large stations
can shadow a nearby ship correctly. Apply the receiver mask before sampling.
Use manual 3x3 PCF on SM3, slope/normal bias and texel-snapped projections.
Render depth for hulls with the same alpha-test cutouts, animation and hardpoint
transforms as the visible mesh. Update moving ships each frame; cache static
station casters only after invalidation for camera/light/LOD/system changes exists.

### Planet shadows on ships

Do not place the entire planet in the local ship shadow map. For eligible ships,
intersect the receiver-to-sun segment with the planet's bounding sphere in
camera-relative coordinates. Use the sun's angular size to smooth the eclipse
edge. Multiply only direct solar lighting by this visibility; keep nebula ambient,
equipment lights and emissive surfaces. Fade the contribution near the 20 km
surface-distance limit. A non-spherical planet would need a dedicated silhouette
representation; the first version can use the existing spherical planet model.

### Required engine work and checks

The scene must pass object class, owner and shadow participation into mesh draws.
RP9 needs a material shader path for indexed legacy vertex formats and a depth
replay path with independent shadow depth attachments; the current fullscreen
Ex interface alone is insufficient. Evolve the extension with capability/version
checks so RP8, old DLLs and shader failure retain the legacy path.

Validate: ship self shadow; a station eclipse on the player; a ship shadow on a
station; every planet surface unaffected by nearby ships/stations; a planet
eclipsing a ship at less than 20 km surface distance; all contributions fading
without popping at range limits; multiple suns; transparency; docked/animated
parts; device reset; no extra geometry submissions when disabled.

Reference: [Microsoft's cascaded shadow map overview](https://learn.microsoft.com/en-us/windows/desktop/DxTechArts/cascaded-shadow-maps)
explains partitioning, stability and PCF. This proposal uses manual comparisons
for D3D9, not a dependency on newer comparison sampler APIs.

## Implemented compatibility fixes

`port.ini [Render] sun_field_spines=1` implements the intent of adoxa's retail
0x111BA5 and 0x111C80 74->EB patches: ignore lane/ordinary field suppression,
but keep nebula intersection suppression unless the separate burn-through switch is enabled.
The inspected original executable
has byte 74 at both offsets. `sun_attached_effect_occlusion=1` gates geometry
submission for attached solar ALE effects using the sun's corona visibility,
zone occlusion and intensity. Simulation keeps ticking while hidden; it does
not misuse ALE outer-time (`SetIntensity`) as render alpha. Quality 0 uses a
centre collision ray without reading the uninitialised projection scale.

`sun_nebula_burnthrough=1` removes both binary sun suppression gates: the camera-to-sun
nebula intersection and the fully enclosed field branch. Occlusion instead targets
`1 - SunLightScale(camera)`, which smoothly blends the authored
`sun_burnthrough_intensity` with zone immersion. Without active volumes the controller's
original enclosure/intensity supplies the fallback. Physical object occlusion remains.
An explicit solar billboard node in the far bucket works even when retail drops distant
solars from the field's object queue. It shares the descending distance sort with far
solars and nebula exteriors; later mesh callbacks and the controller do not add another
sprite. `sun_burnthrough_scaler` smoothly changes sprite size with the same solar fade weight, as in
the original burn-through draw, rather than multiplying light intensity.

The full-resolution volume composite permits a 0.25 transmission floor only within
the already intensity-scaled solar glow footprint. Depth-writing objects and depthless
far planet spheres reject the correction; no extra solar image is overlaid on them.
The ray marcher keeps its original register/instruction budget. This correction does
not add a render pass. Setting the new switch to 0 restores the previous nebula sun gates.

Finite ring companions with `backdrop_radius` now render immediately above the sky,
before solar sprites, all far solars/local exteriors and opaque scene objects. Their
per-frame drawn flag prevents a second late volume draw. The original llight cloud
puffs still use their existing path. Ordinary nebulae retain their depth-aware volume pass.

Crow explicitly selects `real_background=1` in its style, including when the runtime
global defaults to 0. Keeping the same sky behind the integrated fog prevents the
retail full-enclosure switch from replacing a dimmed sky with a brighter fog clear
colour at entry/exit. Controller background policy is selected independently of the
effect's cached `bInside`: controller selection and cached immersion can cross their
thresholds on different frames. Other styles and the explicit legacy option retain
their existing policy.

Crow uses `background_scale=1`: the separate sky dimming quad is inactive, so entry/exit
does not change the system sky's colour or luminance independently of volumetric fog.
`SunLightScale` ignores finite backdrop profiles (`backdrop_radius > 1`). Their source
zones include the empty system interior, even when the rendered cloud shell is hollow;
using source immersion there incorrectly attenuated the ordinary system sun. With only
the backdrop active the function returns the original-path sentinel (-1). Local nebulae
still blend their authored burn-through intensity with camera immersion.

The crow haze ramp now starts at 1 km and grows over 7 km of ray distance. Solar
immersion additionally ramps over 10.5 km of camera penetration, starting 1 km into
the zone, and is limited by the zone's own immersion/exclusions. This delays both
solar intensity loss and sprite size changes without changing ordinary space.
The metric uses the ellipsoid's normalized radius and shortest semiaxis.

For active volumes replacing object fog, object submission bypasses the retail
enclosure-only drop gates (outside, partial and fully enclosed). Far solars also bypass
the full-enclosure/foreign-zone rejection. Actual mesh LODs, scene range, clipping and
opaque occlusion remain. The depth-aware volume, including its partial exterior fade,
now owns visibility instead of double-fogging an object until volume strength is exactly 1.

When that controller replaces object fog, full enclosure also keeps the ordinary scene
far plane and enqueues the far asteroid/texture-panel helpers. After retail controller
selection, restore missing non-controller nebula nodes: retail clears the background
queue and stops its nebula walk on the first fully enclosed field. Existing nodes are
retained and deduplicated, unloaded effects skipped, and restored exteriors use the
original surface-distance sort before the solar sprite sort. The source controller
selection and legacy rendering when volumes are unavailable remain unchanged.

Crow `visibility_fade_start=1500` / `visibility_fade_end=4000` now selects ordinary
linear distance fog towards the authored `[Fog] color`. The previous opacity-based
radiance rescaling and smooth silhouette closure have been removed: they could amplify
bright scattering on asteroid silhouettes. Ray length is still clipped to the scene
surface or depthless planet and to the real nebula zone. A clear/excluded sample remains
clear. The colour interpolation stays between the original ray radiance and the fog
colour; it never divides by current opacity. The sun's existing occlusion-aware
burn-through follows the fog. Backdrop shells and debug views skip this correction.
Other styles default to disabled (end <= start).

Crow now selects `replace_fog_overlay=0`, `replace_object_fog=0` and disables the
extra visibility fade. The native current-zone fog quad covers the exterior scene,
with ordinary per-object fog on interior geometry. External background restoration
and the enlarged scene range are consequently inactive for this style. Volumetric
interior clouds remain. While a volume is active and the native quad is selected,
it is submitted every frame: retail's one-time opaque-quad cache assumes no sky or
extra backdrop layers are being drawn. The source immersion controls cover alpha.
Solar sprites are emitted by the original post-overlay burn-through while enclosed;
the sorted sprite path remains for open space, preventing double solar drawing.


Grouped projectile-colour surface reflections are documented in
[weapon_glints.md](weapon_glints.md). They share this opaque material route,
including plain hull receivers when local shadows are off, and preserve the
accepted solar finish. New pixel constants occupy c77-c93; zero active groups
retain the previous material output.

## Cockpit and glass material profiles

Optional RP9_IRPSurfaceContext_v1 scopes cockpit and glass draws without changing
retail interface vtables. Pixel constant c94 carries the material profile.
Cockpit rendering uses a restrained satin finish and receives projectile accents;
emissive instruments retain their authored output. Rigid lit cockpit routes can
use a material colour alone or ordinary textures, with or without an envmap.

Glass selection follows the actual flmaterials glass type after DACOM.ini
material overrides. In particular, ^r_glass$ = HighGlassMaterial reaches the
shared KindGlass submission path. There is no material-name heuristic and no
Shading.dll change in this update. GlassMaterial and GFGlassMaterial share the
same native glass route. The native opaque/back-face pass is retained; the
profile applies to the SRCALPHA/INVSRCALPHA glass pass. Unsupported routes fall
back to the original material.

Glass adds sharp highlights, angle-dependent Fresnel reflection and opacity.
Authored envmaps are reused when present; colour-only r_glass also works, using
a smooth synthetic reflection band. This is not scene refraction or a capture
of surrounding geometry. Untextured glass needs no UV set. Missing glass normals
use screen derivatives of view position for a geometric face normal; ordinary
hull material requirements remain unchanged. No new reflection textures or
render passes are allocated.

port.ini [Render], restart required (surface_shaders must be enabled):

| Key | Default | Meaning |
| --- | --- | --- |
| cockpit_shader | 1 | Enable the cockpit surface profile |
| cockpit_finish | 0.65 | Satin/specular finish strength, 0..2 |
| glass_shader | 1 | Enable the native glass surface profile |
| glass_reflections | 1.5 | Glass reflection/highlight strength, 0..4 |

Release Win32 builds of client, RP9, Alchemy and flmaterials pass. Both SM3
surface variants compile and are prewarmed. The real HAL harness checks cockpit
TEX3 with no envmap receiving green accents, emissive instruments, colour-only
glass with no UVs/normals, native glass pass exclusions, alpha blending and
context restoration. Existing hull/shadow/glint/AF/FXAA regressions pass.
Actual cockpit and ship appearance remains subject to in-game evaluation.

## Solar optics and attached ALE fade

The native LensFlareDraw path already renders authored lens ghosts. Runtime
stararch.ini contains both hexagon and circle flare definitions; the selected
sun archetype controls the shape. The native centre-of-screen fade is retained.
Ghost size and alpha now also follow the existing smoothed corona visibility,
so a physically eclipsed sun does not retain independent camera ghosts.

The previous partial-eclipse halo in DrawBillboard was only another glow sprite,
restricted to active volumetric nebula settings. It was not a light-shaft pass.
A new solar_rays.hlsl pass now runs from DrawFlare after world/cockpit geometry
and before FXAA/HUD. It integrates a procedural solar disc through 64 scene-depth
samples along each radial direction, with deterministic diffraction spokes.
Scene depth masks both the solar source and opaque output pixels. Full occlusion
removes the rays; partial silhouettes cut their respective directions. No real
light sources, physical refraction or offscreen shadow geometry are added.
INTZ/SM3 and enabled native sun effects are required. Transparent glass and
sky/background objects without scene depth do not cast this screen-space mask.
The existing Ex pass restores render state; its shader is disk-cached.

Attached solar ALE now uses optional Alchemy_IRenderOpacity_v1, independent of
ALE outer time, animation, particle emission and simulation. A per-sun 0.15 s
opacity ramp follows corona/zone visibility. Alpha-blended appearances scale
vertex alpha; source-ONE additive appearances scale RGB as well. The four
appearance queues retain each node's opacity until FillBatchedGeometry, then
restore the scope. BeginDraw clears stale queue entries. Non-solar effects use
opacity 1. No retail component vtables or node layouts change.

port.ini [Render]: sun_rays=1, sun_ray_strength=1.5 (0..4),
sun_effect_fade=0.15 seconds (0.03..1). Restart after changing these values.
The previous sun_attached_effect_occlusion=1 switch remains authoritative.

Validation: Release Win32 client/Alchemy builds pass. A real D3D9 HAL fixture
compiles and executes both solar SM3 stages against synthetic depth silhouettes;
partial obstruction halves integrated output, full eclipse produces zero, and
opaque output pixels stay unchanged. ALE tests verify independent deferred
batch opacity, source-alpha/additive packing, reset, and the existing actual
Rheinland colour curves. Appearance in the real scene still needs evaluation.

## Restrained solar optics (2026-10-21)

[Render] sun_optics_strength=0.5 now scales solar optics independently of actual
system lights. Billboards scale RGB because their source-ONE/screen blending
ignores vertex alpha. Corona source-ONE vertices also scale radiance; ordinary
source-alpha corona, spines and lens ghosts scale their added intensity. The
new radial rays retain sun_ray_strength=1.5, multiplied by the common 0.5 gain.
Attached solar ALE follows the same gain through its existing render-opacity
service and 0.15 s fade. Engine and other non-solar ALE remain unaffected.

Current controller immersion, gated by nonzero field enclosure, suppresses
structured optics with (1-immersion)^2. At full immersion no spines, corona,
lens ghosts, depth rays or attached solar ALE remain. The authored star/glow
billboards crossfade into the existing round glow2 shape at
sun_nebula_halo=0.12 of the reduced gain. At defaults that is 0.06 of original
sprite radiance. Cached controller immersion preserves exclusions and the
existing entry/exit ramp; a distant background cloud alone does not select
this policy. Star texture assets and physical lighting are unchanged.

## Larger core and strict nebula occlusion (2026-10-21)

Keep sun_optics_strength=0.5 and the current halo, spines, corona and ray gains.
The new [Render] sun_core_size=1.5 enlarges only the authored star_center disc
(1..3 clamp). Copy the descriptor for the draw; do not modify shared star data.
Glow bounds and the nebula's noted sprite extent include the enlarged centre.
The solar ray radius retains its current value.

The previous burn-through override replaced an actual camera-to-sun nebula hit
with SunLightScale(camera). Outside the cloud that scale is 1, so a nebula in
front of the sun could incorrectly reveal it. li_cal has space_farclip=50000,
but this bug is independent of far clipping: the registered nebula zones and
the full finite sightline already exist outside the visible volume list.

A nebula segment hit now always occludes the sun. Apply the same gate to every
billboard entry point (including controller burn-through), corona/spines, lens
ghosts and depth rays, and the target opacity of attached solar ALE. The latter
retains its short existing fade. This strict rule also hides the direct solar
sprite while inside a nebula whose zone the sightline intersects; it supersedes
the earlier round burn-through halo for those intersections. Physical system
lighting and the paused engine work are unchanged. No HLSL changes or new cache
compilation are needed.

Validation: a source-extracted C++ fixture runs the real sphere/ellipsoid clip
functions and solar zone gate on all five actual rotated li_cal nebulae. It
checks blockage beyond the 50 km clip distance, a sun in front of the cloud,
a clear direction, an observer inside the cloud, core bounds/clamping and
preservation of the source descriptor. All solar rendering entry points are
checked for the common gate. The Win32 RP9 client builds successfully. Visual
verification in the real li_cal scene remains to be done.

## Restore the authored solar centre (2026-10-21)

The preceding optical-gain wrapper also processed star_center: this dimmed the
solar disc and could replace its shape with a faint round halo. The requested
behaviour is the original disc alongside the new optics. Draw star_center with
its unmodified descriptor and the retail A*A alpha, bypassing ApplyOptics.
Its texture/shape, scale, inner/outer colour and native alpha/screen blend now
remain as authored. Keep the reduced 0.5 gain on the outer glow/rays/corona.
Remove sun_core_size and restore the original culling/volume-note bounds; no
texture or stararch assets are replaced. Strict nebula sightline occlusion still
applies to the disc and all optical effects. The engine task stays paused.

## Solar occluder depth and viewport borders (2026-10-21)

The solar-ray shader previously treated every non-sky depth sample as an
occluder, so geometry behind a nearby sun could cut its rays. It also treated
samples outside the viewport as blocked. Record the actual scene near/far and
depth viewport range when the opaque pass begins, then project the solar front
surface into the same depth convention. The SM3 ray pass now blocks only depth
in front of that source. The cockpit's separate depth partition still blocks
rays, and cleared sky remains visible. Out-of-viewport samples are unobstructed
and never sample clamped geometry along the texture border.

The native corona probes now unproject off-screen samples and test real rays
instead of fading those samples to zero. Both physical occluder paths reject
hit points outside the finite camera-to-sun segment. Core rendering, gain and
nebula visibility are unchanged.

Validation: real D3D9/SM3 execution checks foreground silhouettes, full eclipse,
geometry behind the source (pixel-identical to clear sky), the cockpit partition,
and matched ray pixels with a source inside versus outside the viewport
(pixel-identical). Source-extracted native probe tests cover foreground,
background, endpoint and camera-border cases. The Win32 client builds. The
updated solar PS uses the existing disk cache; no engine changes are included.

## Static megabase shadow cache (2026-10-22)

`[Render] shadow_static_cache=1` (default) enables a far-cascade static-depth
cache and component-level near-cascade caster culling for layered stations.
`0` restores the former full-station shadow submission path. The main colour
pass, surface shader filtering, shadow resolution and 200 m reach are unchanged.

The client walks each eligible solar's Engine hierarchy. A component becomes
cacheable after 500 ms of unchanged world transform and archetype, with no
missing observation frames. Moving turrets/attachments remain live independently
of fixed panels on the same root. Ships and dynamic asteroids are always live.
Continuous solar animations and active gate scripts remain live. The signature
includes the system, component handles, archetypes and transforms; additions,
removals, motion and mesh replacement invalidate the static set immediately.
Trees are bounded to 64 levels and stale tracking entries are discarded each frame.

At least 32 stable components are required before enabling the GPU cache. It
stores one additional far-cascade R32F map (256 MiB at 8192, 64 MiB at 4096),
allocated lazily. Allocation/restore-shader failure falls back to ordinary draws.
Near shadows stay live; their component bounding spheres are conservatively
culled against the near light volume, including upstream casters and transform
scale. Neither path uses the main camera's frustum to reject shadow casters.
Depth-only components can share a batch flush; this is not hardware instancing
and does not merge the base's main-pass draw calls.

The far cache uses a world-anchored light frame. Camera translation/rotation
rebase its matrix without shifting the cached shadows. It rebuilds after movement
exceeds 5% of the far radius, sunlight rotation exceeds a half-texel angular
tolerance, the geometry signature changes, or one second elapses. The age limit
also bounds changes to material state/LOD which are not represented by transforms.
On reuse a fullscreen pass restores both R32F colour and hardware Z before live
casters draw. This avoids frozen ships, ghost shadows, and live geometry behind
a station overwriting its nearer static depth. Device reset releases all cache
resources. Logs report `static shadow cache: builds ..., reused ...`.

Validation uses source-extracted production functions, not copies of the cache
algorithm. `tools/build_shadow_cache_check.py` generates a D3D9 fixture that
checks every pixel of cached/static plus live depth, camera translation/rotation,
removal of live shadows, key/region/sun/age invalidation, cache-off fallback and
resource release. `tools/build_shadow_component_check.py` checks independent
panel/turret tracking, mesh replacement, reappearance and near-volume culling.
Both fixtures and Release Win32 client/RP9 builds pass. Actual megabase FPS and
the cost of the full-map depth restore still require an in-game comparison.

### Uncapped performance comparison

RP9 `[Render] vsync=0` selects `D3DPRESENT_INTERVAL_IMMEDIATE` when creating or
resetting the device. `[Render] fps_limit=0` removes the client's software frame
wait, including the default 200 FPS ceiling. Positive `fps_limit` values impose
that cap; absent/-1 preserves the retail performance-slider/console cap. VSync
defaults to the existing mode behaviour. Both settings require a restart for a
controlled comparison. External driver/overlay frame limiters remain independent.

## Renderer-only megabase optimisations (2026-10-22)

No mesh, material-library, texture, collision or LOD assets are regenerated or
modified. The additional instance buffer contains only per-draw transforms.

- `state_cache=1` (default) mirrors actual D3D9 material, FVF, transform,
  render-state, texture, sampler and shader calls. Exact duplicate requests are
  omitted. Float shader constants upload only the changed leading/trailing
  register range. State-block Apply/device reset invalidates this mirror;
  it is separate from the existing retail logical state queues. `0` disables
  deduplication for comparison while retaining correct device validation.
- Surface normal matrices are reused for identical world-view transforms.
  Orthonormal transforms use their rotation directly; scaled/sheared transforms
  retain inverse-transpose handling. Light descriptors in view space are cached
  by the active light data and view transform. Directional-light positions are
  canonical zero and their view translations are irrelevant. Active-light
  iteration is rebuilt when enable states/deletions/reset change, preserving
  original handle order and the eight-light limit without walking disabled lights
  for every material.
- `surface_instancing=1` (default) groups repeated static-buffer indexed opaque
  draws during consecutive solar-object rendering, including attached components.
  Keys include geometry/ranges, material pixel constants, projection/environment
  constants, textures, samplers, render states and viewport. World-view and normal
  matrices form a second per-instance stream. The first occurrence draws normally;
  unique meshes allocate no state block. Repeated groups use hardware SM3
  instancing, with ordinary per-instance draws as a failure fallback. Software
  vertex-processing devices retain ordinary rendering.
- A queue is bounded to 128 groups/1024 pending instances. It flushes at bucket
  boundaries, ships/non-solar draws, transparent/unsupported draws, clear,
  viewport/depth partition changes, shadow/postprocess passes and scene end.
  Both native state and stream frequencies are restored. Different lighting or
  projectile-glint selections remain distinct groups. Instancing also operates
  when local shadows are disabled; bit 2 of SetLocalShadowReceiver enables the
  grouping scope independently of bit 0 (shadow receiving).
- Directional shading avoids point-light distance/attenuation calculations.
  Zero-contribution lights skip the BRDF lobes. Reflection, ambient, emission,
  shadow filtering and authored material inputs remain intact.
- `render_stats=1` logs averaged FPS, ordinary/shadow draw calls, state calls
  sent/skipped, uploaded constant vectors and instanced draw/instance counts every
  two seconds. Counters do not issue GPU readbacks or blocking visibility queries.

Validation: Release Win32 client/RP9 builds; real D3D9 material/state/constant
cache tests; source-extracted normal/light and active-light-list tests; real
hardware instancing compared pixel-for-pixel with regular rendering of overlapping
objects, multiple materials and nonzero base/index offsets (24 draws become 8 in
the fixture), including forced fallback and stream restoration. The surface GPU
regression captures 229376 bytes across the existing light/gloss/fog/emission
cases: all bytes match the original shader. Static shadow cache GPU/component
tests still pass. Surface VS, instanced VS, 2D-env PS and cube-env PS are prewarmed
in the persistent bytecode cache before installation.

Actual FPS changes for or_hq/ku_tgk require the same-camera in-game comparison.
Hardware visibility queries and generated/merged mesh LODs are not part of this
change; the existing frustum and LOD paths remain in place.

### Static surface distance tiers (2026-10-22)

After an in-game performance regression report, surface_instancing and state_cache
now default to 0 and the installed profile disables both plus render_stats.
The instancing fixture remains opt-in; its reduced draw count is not an FPS claim.

Static solar root scopes select materials using squared camera distance against
bounding-sphere radius plus the configured thresholds. Full materials within
surface_static_full_distance (default 2000 m); separately compiled
SURFACE_LOW_DETAIL diffuse/envmap-only shaders up to surface_static_off_distance
(default 20000 m); native fixed-function materials beyond that. Scope bits 3/4
carry the tier without changing the extension vtable. Reset at bucket boundaries
and per-object selection prevents the tier leaking to ships/cockpits. Large root
bounds conservatively retain detail for attached equipment near the camera.
Low-detail PS has no PCSS/planet shadow sampling, layered gloss/clearcoat/brushed
finish or glints; diffuse/point/spot lighting, authored envmap, emission/alpha/fog
remain. Full shaders and shadow-map generation are unchanged. Low tier uploads
52 PS registers instead of 95 and does not bind shadow samplers.

Validation: both Win32 Release projects build; all six shader variants compile.
Existing full material GPU captures match HEAD pixel-for-pixel (229376 bytes).
Low-tier real D3D9 tests verify lit/ambient/point/spot/fog/emission and independence
from expensive finish controls. Source-extracted receiver tests verify low/native
selection and reset before ship/ordinary scopes. No live-game FPS measurement.

### Medium-distance gloss refinement (2026-10-22)

Full static surface material now defaults to 4000 m (was 2000 m). The 4-20 km
SURFACE_LOW_DETAIL variant retains diffuse/envmap and adds one inexpensive
Blinn highlight, using fixed powers 16/64 formed by multiplication, material
roughness for width/strength, source specular colour and bounded rational
highlight addition. No PCSS, tangent/derivative finish, GGX, coat, extra textures
or passes. The same 52 PS registers suffice. Beyond 20 km stays native.
Experimental instancing/device-call cache remain disabled. GPU material tests
verify medium gloss responds to roughness, layered finish controls stay absent,
and fog/ambient/point/spot/emission still work. Full material captures unchanged.

## Shadow cost, NPC ship tiers and retained surface state (2026-10-22)

Shader (`surface_material.hlsl`, `local_shadow.hlsl`):
- Near and far maps have their own resolution (`shadow_near_resolution`,
  `shadow_far_resolution`, default 4096, falling back to `shadow_resolution`); the far texel
  size is c95.x. Sample defaults are 16 search / 32 filter taps (were 64 / 192).
- The blocker-search and filter spirals rotate the previous tap direction by the golden
  angle instead of evaluating sincos per tap.
- A pixel facing away from the sun, or a receiver in the simple tier (c95.z), takes one
  bilinear comparison instead of PCSS.
- `SURFACE_NO_SHADOW` compiles the full material without the shadow code; RP9 selects it for
  any receiver without shadows this frame.
- Casters drawn after `SetLocalShadowCaster(1)` store a negative depth. `ShadowDepth`
  decodes it; such texels shadow only c95.y metres (`shadow_npc_ship_length`, 100) behind
  the caster, with the usual fade over the last 20 %. The static-cache restore writes the
  absolute value to Z.
- Samplers: the environment map is s10 and the shadow maps s8/s9 (were s1, s2/s3).

NPC ships (client, `space_scene_obj_draw.cpp`): `SetLocalShadowReceiver` bits 5..6 carry a
tier by the camera's distance to the hull: full filter to 100 m, a fixed 8/8 filter to 300 m
(c76), the simple comparison to 500 m; beyond 500 m the ship is neither a receiver nor a
caster. The player's ship (`IsPlayerShipId`) always uses the full filter and full length.

RP9 keeps the surface route's shaders, samplers 8..10 and pixel constant blocks between
draws (docs/re/rp9.md, "Surface route between draws"). The static far cache is rebuilt after
`shadow_static_cache_seconds` (10) instead of every second.

Validation: `surface_bench` (RTX 5080, 1080p, full-screen receiver): the same settings
match the previous shader within 1/255; one layer costs 3.73 ms before, 0.49 ms with the
new defaults, 0.07 ms on surfaces facing away from the sun (was 2.20 ms). Short-reach
casters 150 m above a receiver leave it lit and 60 m above it shadow it exactly like normal
casters. The real-RP9 route check (`src/obj/surface_route_check.cpp` adapted) passes with
the device-call cache on and off: a repeated surface draw sends one device call, a
fixed-function draw afterwards runs without shaders, cube env maps reflect from s10, NPC
tier constants reach the shader, and both FXAA modes filter edges.

### Separate station map in the far cascade (2026-10-22)

A first-depth shadow map keeps only the caster nearest the sun. With the cached station depth
copied into the far map and ships drawn over it, a ship more than its shadow reach above a
station replaced the station's depth: receivers found only the out-of-reach ship and the
station's own shadow showed a lit, ship-shaped hole at far range (the near map's limited depth
range hid this up close). The station map is now sampled directly (s11, c95.w) beside the far
map, which holds only moving casters; each tap takes the larger occlusion of the two. The
per-frame full-map copy (and its restore shader) is gone, and any fixed component uses the
cache (the 32-component threshold is removed). `surface_bench`: the composite lost the station
shadow at 1.59 M of 2.07 M pixels, the separate maps at 0; cost unchanged (2.45 / 2.47 ms).

Surfaces facing away from the sun skip the shadow lookup, and shadow dims the environment
reflection in proportion to NoL, so unlit or grazing sides show no caster silhouettes.

The near cascade had the same first-depth problem: "near/far" in the report was the ship's
distance above the station, not the camera's. Ships and asteroids near the camera are now drawn
into their own map (cascade 2, `ShadowMaps[2]`, near resolution, sampler s12, c62.y) before the
near map, which then holds only station geometry; the shader takes the larger occlusion of the
two. If that map cannot be allocated, the casters share the near map as before. Real-RP9 route
check: a ship 300 m above a station shadow left the receiver lit (ffffffff) with one map and
shadowed (ff060606) with the separate map. The far static cache now tolerates a sun-direction
change of one far texel over the longest shadow (it was one texel over the whole 5 km depth
span), which had caused most rebuilds while flying.

## Authored suns first (2026-10-23)

The depth rays had a fixed spoke pattern of their own (8 broad + 14 thin spokes, the same for
every star, no motion) on top of every sun, and sun_optics_strength=0.5 halved the authored
spines, corona, lens ghosts and attached solar ALE. Stars authored without [spines]
(red_giant_sun, sm_red_sun, green_giant_sun) thus gained hard spokes they never had.

Now solar_rays.hlsl has no spokes: a soft glow plus shafts where geometry covers the disc, its
reach growing with the disc (0.45 + 4 x radius of the screen height; the radius clamp is now
0.012..0.12), so giants glow wide and soft. The spikes are the star's own [spines] again, and
sun_optics_strength defaults to 1 (authored strength).

Halo restrained: reach 0.35 + 3 x disc radius, quadratic falloff, gain 0.5 -- between the first version (read as bloom) and a minimal one (cubic, 0.35) under which the shafts cut by geometry hardly showed.

Alive suns ([Render] sun_alive, 1; 0 = still as retail, up to 2), all on the authored elements
(star_sphere.cpp, SolarWobble: two sines at incommensurate rates, a per-sun phase from the
sphere's address, client elapsed time): the crown turns 0.004 rad/s and sways +-0.035 rad, but
the star's frame keeps its authored angle -- spines on the screen axes (horizontal, vertical)
and the longest ones (>= 0.9 of the longest) never turn or sway; the others turn and sway +-0.012 rad; every spine breathes +-9% in length and +-15% in brightness on its own phase;
the corona breathes +-6%; the star_glow billboard +-2.5% in size and +-5% in alpha (the stars
without spines move through it).

The sun's corona in place of its ALE ([Render] sun_corona, 1): the suns' attached ALE effects
(fx\mod\*_sun.ale, planetflare/sarma) were heavy and, hanging on a hardpoint in the world, never
matched the screen-space spines and glow. With sun_corona on, FParticleEffect::TickDraw and
BuildGeometry skip an effect watched by a listed sun (StarSphereReplacesAttachedEffect): it is
neither simulated nor drawn. FStarSphere::DrawFlare instead draws solar_corona.hlsl
(RenderEx::DrawSolarCorona, an additive fullscreen Ex pass like the rays, hidden by geometry in
front of the sun through the scene depth): streamers of 3D value noise over the direction around
the disc (no angular seam) and log radius, flowing outwards and evolving, under broad lobes that
turn over minutes; growing out of the visible core (half the rays' disc scale) with no gap, falling off to sun_corona_reach (3) disc radii;
tinted by the star_glow inner colour, per-sun seed, clocked by sun_alive. Keys:
sun_corona_strength (0.35), sun_corona_reach (3), sun_corona_contrast (1.8).
(Two earlier attempts -- turning the spines with the world, then giving the ALE the camera's
orientation -- were removed.)

## Sun halo over nebulae and ship haze aura (2026-10-23)

Sun halo (star_sphere.cpp `StarSphereDrawNebulaHalo`, called from space_scene_obj_draw.cpp right after
`NebulaVolume::DrawHybridClouds`). The sun sprites are drawn with the scene, before the nebula composite, which
attenuates them by the nebula's transmittance, so the sun vanished in and behind nebulae. Retail drew its burn-through
over the fog. Now, while the volume drew this frame (`NebulaVolume::IsFrameActive`, valid after `Draw` ended the frame)
and the camera is immersed or `SolarNebulaBlocked`, one screen-blend `glow2` billboard is drawn at each sun, over the
composite, no depth: colour = the star glow's inner colour, strength = `SunNebulaHalo(sun_blocked_halo)` x the sun disc
visibility (`SunBodyComputeCoronaFactor`) x (1 - ZoneOcclusion) x the ring transmittance, size = radius x star glow
scale x `sun_blocked_halo_size`. The in-scene crossfaded halo of `StarGlowDrawBillboard` stays out while this one is
active (the authored sprite's fade-out is kept).

How much nebula lies toward the sun: `Through = exp(-Sigma * L)`, L the metres of the first 40 km of camera -> sun inside
nebula zones (24 evenly spaced samples, `NebulaVolume::SegmentNebulaLength`; a sample counts when a registered nebula,
ring companions excluded, has immersion there), Sigma = -ln(0.25)/3000 (75% lost per 3 km). The halo is scaled by
`max(sun_halo_floor, Through)`: weaker behind more nebula, never gone. Cached per sun, frame time and camera position.

Smooth exit: the hard `SolarNebulaBlocked` returns in `DrawBillboard`, `Draw`, `DrawFlare` and the attached-effect
visibility are gone; they scale by `smoothstep(Through)` (absent at <= 0.15, whole at >= 0.6) instead, so the sprite,
spines, corona, flare and the ALE fade in as the ship nears the nebula edge. (`SolarNebulaBlocked` remains as the
"L > 0" shortcut: a crossing thinner than the sampling, or a camera inside, counts one sample.) For the same reason
`StarZoneOcclusionFactor` no longer returns 1 for a nebula hit (its slow fade made the sun leak and pop; asteroid
fields still occlude as before). The halo is multiplied by `1 - fade` so it gives way as the authored sun returns.

Ship haze aura (`NebulaShipAuraDraw`, right after the sun halo): with the camera inside a drawn nebula, one `glow2`
billboard centred on the player's ship (`Slot178` centre/radius), half size radius x `ship_haze_aura_size`, colour =
fog colour x2 (clamped) x `ship_haze_aura` x immersion (+0x294) x (0.6 + 0.4 * `SolarSunlitAt(centre)`), screen blend,
no depth test. Skipped in the first-person camera.

Keys, port.ini `[Render]`: `sun_blocked_halo` 0.25, `sun_blocked_halo_size` 0.6, `sun_halo_floor` 0.25,
`ship_haze_aura` 0.18, `ship_haze_aura_size` 2.5. volumetric.ini styles: `ship_haze_aura`, `ship_haze_aura_size`
(-1 = port.ini); `sun_nebula_halo` also overrides `sun_blocked_halo`.

### Easing the sun back in (2026-10-23)
`SolarNebulaThrough` eases its result per sun: it rises at most `1 / sun_nebula_fade_seconds` per second
([Render], default 3; 0 = at once) and falls four times faster. Leaving a nebula the line to the sun clears
in a frame or two, so without this the sun popped in. A frame gap over 0.5 s snaps to the measured value.
