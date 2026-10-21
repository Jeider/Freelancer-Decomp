# Local shadow validation

Status: experimental source on `work/local-shadow-validation-20261021`.
The user explicitly approved game-frame integration. The client now connects
the builder and receiver scopes described below. Both client and RP9 builds and
the isolated GPU regression checks pass. Visual quality and frame cost in a
populated game scene still require an in-game check.

## Implemented and checked in isolation

- Independent `IRPLocalShadows` interface; no retail-interface vtable changes.
- Two 8192-square R32F shadow maps, with a shared D24X8 depth surface.
  Device caps limit resolution; allocation failure retries at half resolution.
- A 300 m wide near region and a 10 km wide outer region, centred on the camera.
- Camera-relative calculations, world-anchored texel snapping, contact-hardening
  PCSS filtering, receiver-plane depth correction, smooth cascade transition,
  and camera-range fade between 4.5 and 5 km.
- Actual opaque mesh draws, not bounding-sphere ship shadows or a screen overlay.
  Common GREATER/GREATEREQUAL alpha-test cutouts are supported; blended geometry
  and non-rigid vertex formats do not enter the map.
- Shadow participation is explicit. Surface shaders also admit supported plain
  diffuse materials when marked as shadow receivers. Unmarked objects do not
  sample shadow maps.
- Only the matching directional sun term is shadowed. Ambient, emissive and
  other light sources remain. Planet eclipses use a separate analytic sphere
  test. Both geometric and analytic shadows now reach at most 200 metres behind
  the casting surface along the light ray, fading from 160 to 200 metres.
- The inactive shadow draw hook returns true without changing native draws.
  A map must be successfully opened after a valid frame descriptor to intercept
  draws. Targets, depth surface, viewport, material, transforms, render-state
  caches, texture-stage caches, stream cache and base vertex are restored.

The HAL readback harness loaded the real cubemap from `envmapbasic.mat`, checked
2D/cube transitions and ordinary UP/indexed UP drawing, then rendered a mesh
into both shadow maps. A receiver behind it changed from `ffffffff` lit to
`ff060606` shadowed; disabling receiver participation restored the light.
Plain diffuse receivers worked too. Empty maps preserved illumination, a nearby
planet eclipsed the receiver, a planet beyond 200 metres did not, and receiver opt-out
prevented eclipse darkening. Device-resource teardown/recreation also passed.
The test suppresses Windows crash dialogs and reports failures to the console.

Both SM3 shader stages compile with D3DX9. The surface GPU test additionally
checks fog, spot cones, roughness, unlit reflection reduction and preservation
of emissive colour under a black envmap. This is not an in-game performance or
visual acceptance result.

## Client integration

`BuildLocalShadows` in `space_scene_obj_draw.cpp` runs before ordinary scene draws
when `[Render] local_shadows = 1` and `surface_shaders = 1`.
It enumerates the existing ship/solar lists, keeps frame-local pointers, rejects
invalid radii/positions and cloaked objects, excludes planets/moons/stars,
waypoints/jump holes/trade lanes and NON_TARGETABLE decorative helpers as local receivers/casters, and limits geometry
to 128 nearest hulls intersecting the configured scene neighbourhood (default 5 km). The near map further
filters by perpendicular distance to the sun direction.

Dynamic asteroids have a separate budget of 64 nearest active, fully opaque
instances, respecting the dynamic-asteroid game option. Their copied mesh is
submitted through `DrawIndexedPrimitiveVb`, with no effect sweeps, ambient-light
updates or simulation. Fading instances do not cast abruptly appearing silhouettes.
They remain on their original material path as receivers.

Shadow edges use a stable disk blocker search, penumbra estimation from average
blocker separation and light angular diameter, and disk depth comparisons.
The structure follows [NVIDIA PCSS](https://developer.download.nvidia.com/assets/gamedev/docs/PCSS_Integration.pdf),
adapted to an orthographic sun. Receiver-plane derivatives correct depth across
the filter, while a small texel bias limits self-shadow acne. A sub-texel contact
footprint smooths aliasing. Zero light angle selects hard comparison instead.
Planet eclipses also have a soft silhouette and the same 200 metre reach.
Eclipses use the authored
solid `SolarRadius` and object position instead of a render extent that may
include atmosphere/rings. In rh_biz, NON_TARGETABLE planet-circle helpers have
50 km authored radii and are now excluded from hull shadow participation.
These changes target false darkening without altering system ambient colours.

It calls the existing geometry-only `IRenderer2::RenderInstance`, rather than
GameObject Slot188, so it does not replay effect-list sweeps or simulation.
Flag 0x100 bypasses camera-frustum culling for off-screen casters and flag 0x8
retains distance LOD selection. No object pointers survive the function.

The connection is:

1. With `[Render] local_shadows = 1` and `surface_shaders = 1`, call the builder
   after object collection/sorting and before ordinary scene drawing.
2. In `DrainBucket`, mark only eligible GameObject nodes as receivers, keep that
   scope through their material-batcher flush, then immediately clear it.
3. After `DrainMeshAndAsteroids`, clear receiver state, release the interface and
   null the frame-local interface pointer before nebula/particle/HUD passes.
4. Deploy the matching client, RP9.dll and both HLSL files together; preserve
   backups and enable the option for an experimental game check. To disable
   local shadows only, set `[Render] local_shadows = 0` and restart the client.

Expected extra storage is approximately 768 MiB at 8192, or 192 MiB at 4096, for
two R32F maps and one shared 32-bit depth surface, excluding driver overhead.
Two local geometry passes and up to 64 search plus 192 filter taps per cascade
add work. The actual game-frame
cost has not been measured. Supported opaque rigid hulls are the initial scope;
skinned and complex multi-stage receiver materials retain their previous path.

The HAL harness also exercises the indexed-VB shadow path used by dynamic
asteroids. It compares a hard edge (`ff060606`) with a partially lit soft edge,
checks that strength zero restores illumination, and confirms a caster beyond
200 metres does not occlude. It also checks the 80-200 metre fade. The user has
confirmed the rh_biz fix; the new soft profile still needs in-game visual review.

## Configuration (port.ini, [Render], restart required)

| Key | Default | Meaning |
| --- | --- | --- |
| local_shadows | 1 | Master switch; also requires surface_shaders=1 |
| shadow_resolution | 8192 | Per-map size: 1024/2048/4096/8192 |
| shadow_near_radius | 150 | High-detail camera region radius, metres (100..1500) |
| shadow_scene_radius | 5000 | Outer camera region radius, metres (up to 15000) |
| shadow_max_length | 200 | Reach behind caster, metres (1..200); last 20% fades |
| shadow_strength | 0.85 | Directional shadow intensity (0..1) |
| shadow_light_angle | 2 | Light angular diameter, degrees (0..10); zero = hard |
| shadow_search_samples | 64 | Blocker search taps (8..64) |
| shadow_filter_samples | 192 | Penumbra filter taps (16..192), four depth comparisons each |
| shadow_bias | 0.5 | Bias in world texels (0.05..4) |
| shadow_adaptive_quality | 1 | Distance-adaptive PCSS filtering; 0 restores full budget everywhere |
| shadow_static_quality_distance | 500 | Full filtering through this camera-to-surface distance, metres (50..5000) |
| shadow_ship_quality_distance | 150 | Same threshold for ships including capitals, metres (25..2000) |
| shadow_low_search_samples | 4 | Distant blocker search taps (2..16) |
| shadow_low_filter_samples | 4 | Distant filter taps (2..16), four comparisons each |

The 200 metre rule is an artistic distance limit, not camera draw distance.
It also replaces the previous planet eclipse band of 20 km. Planet receivers
remain excluded; ambient/emissive and unrelated lights remain lit.

A shadow map stores only the closest surface to the sun. If that layer is beyond
200 metres, it may hide a closer layer that should cast a local shadow. That
closer shadow can be missing; resolution and PCSS cannot remove this limitation
of single-depth maps. Mesh LOD, finite map coverage and unsupported receiver
materials also limit quality. This implementation does not promise exact shadows.

Three UV sets are now accepted in the rigid material route. The real sig8_01
station model, station_large_a_lod.cmp, has FVF 0x312 (XYZ/NORMAL/TEX3), which
the previous TEX1/TEX2 admission rule rejected as a receiver. Its shadow-map
caster route did not have that restriction. The HAL harness now checks a TEX3
plain receiver with and without ship occlusion. Mesh normals remain authored.
The user plans to revise this station's old OpenGL test geometry separately.

`anisotropy=16` enables hardware-capped anisotropic minification and linear mip
interpolation when mip filtering is active; native magnification is preserved.
The sampler cache retains the effective values. Shadow depths and FXAA use
their own samplers. `fxaa=1` applies spatial edge AA to the completed space scene
before the HUD through the optional IRPFrameQuality interface. It copies scene
colour outside BeginScene/EndScene, resumes the scene, and restores device
state after the fullscreen pass. Targets, depth and native cache ownership
remain intact; resources are released on reset. FXAA does not use history and
does not promise elimination of temporal shimmer. The HAL test filters a
diagonal while preserving flat colours and checks AF 16x.

MSAA remains disabled: the existing INTZ texture is a single-sample depth
surface, shared by the volumetric/soft-particle paths. This update preserves
that depth path. Before this update RP9 requested no MSAA and had no FXAA pass.
The executable's 32-bit address space does not change shader depth precision
or filter quality; it can constrain resource allocation. Shadow depths remain
R32F irrespective of executable bitness.

The near map now uses a 150 m radius (about 3.7 cm per texel at 8192).
Soft disk taps bilinearly interpolate four depth comparisons, never raw depth.
A central blocker-search tap protects thin casters; the minimum filter covers
1.25 shadow texels and half a screen pixel to limit subpixel flicker.
Each map also restricts depth to its radius plus shadow reach plus 50 m per
side, rather than a 60 km slab. This improves depth precision and excludes
remote station surfaces from the close-range first-depth map. It reduces,
but does not eliminate, the documented hidden-layer limitation.


## Distance-adaptive filtering

Static receivers retain full PCSS through 500 m and smoothly reach the low
budget at 1000 m. Ships, including capitals, retain full filtering through
150 m and reach the low budget at 300 m. Distance is evaluated per surface
pixel relative to the camera, so a nearby section of a large station remains
detailed. Receiver flag 1 denotes a static hull; flag 3 denotes a ship;
0 still disables receiving. The optional interface vtable is unchanged.

Both blocker-search and penumbra budgets interpolate continuously, with a
fractional final tap. This is spatial quality adaptation, not a frame-time
controller. High budgets remain configurable at 64/192 by default. Low
budgets never exceed the configured high budgets. Setting
shadow_adaptive_quality=0 disables distance adaptation.

Only the applicable cascade is sampled; both are sampled in the existing
0.80-0.98 near-map transition band. Receiver derivatives are computed before
these branches. In a fully blocked soft-shadow region, the default distant
budget needs at most 4 + 1 + 4*4 = 21 depth texture reads per selected map,
versus 64 + 1 + 192*4 = 833 at full quality. Previously both maps were sampled
even outside their transition. These are shader lookup budgets, not measured
FPS gains; early-outs, GPU divergence and scene coverage affect actual cost.

Map resolution, allocation (two 8192 maps), geometry submission, map updates,
coverage and 200 m caster-to-receiver reach are unchanged. This optimization
reduces filtering work, not shadow memory or the cost of drawing casters.
The HAL harness validates class-specific constants, low-budget occlusion,
full-quality override and fractional filtering, alongside existing range,
soft-edge, original cube, TEX3 receiver, AF and FXAA regressions. In-game
performance and distant-edge stability still require visual evaluation.
