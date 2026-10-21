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
