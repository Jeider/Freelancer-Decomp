Automatic interior/character materials (RP9)
============================================

Only DrawClientLocation opens the room scope. Original DATA assets, room lights,
THN scripts, UVs, geometry and animation are never rewritten. Existing multilayer
diffuse/emissive maps retain their stage operations and UV transforms.

Implemented:
- Per-pixel lighting from the existing active room lights, derivative tangent frame.
- Packed sidecars: normal XY, micro-roughness, skin mask; all mip levels, linear RGBA8.
- Conservative interior/cloth/skin/eye/teeth profiles, bounded GGX highlights.
- Skin profiles now use the native material/vertex-lighting path; generated
  normals, wrap and new specular shading are excluded from faces.
- Rigid/CPU-deformed vertices and four-weight indexed palettes up to 64 matrices.
- Short-range deterministic contact AO on opaque environment depth. Characters
  (including scripted deformables), their original shadows, translucent objects,
  effects and UI are drawn afterwards. Character self-AO is excluded.
- GPU state restored, standalone room shaders, no asteroid/flight shader additions.

Deliberate fallback: unknown/conflicting materials; missing maps; nonstandard FVF,
palettes over 64 matrices; transparent passes, environment-vector materials,
unsupported texture-stage operations or more than two active layers. Unsupported
depth format skips AO. No speculative global material replacement.
Native reflections and existing eye highlights are retained. This version does
not create reflection probes, physical SSS, GI/lightmaps, POM or new geometry.
These need further scene/material authoring or separate rendering work.

Maps are an estimate from diffuse, not recovered physical relief. Broad baked
lighting and compression noise are removed before differentiating. Roughness
classification uses names/family and conservative defaults; never brightness alone.
Base/body maps capped at 256, face maps 512. Original diffuse resolution unchanged.
Unused GPU sidecars expire after 120 room frames (checked every 120 frames).

Optional port.ini [Render] overrides (installer does not edit configuration):
  room_materials = 0          disables room materials AND contact AO
  room_contact_shadows = 0    disables AO only (default 0.32, range 0..0.6)
Restart the game after changing these overrides.

Stronger finish revision (shader-only, same maps and sample counts):
- Interior/cloth tangent normal components x3; skin x1.6, bounded to keep Z positive.
- Direct highlights x3; skin x1.6, with separate bounded highlight ceilings.
- Roughness contrast x1.45 about matte cloth; modest skin micro-variation.
- Skin wrap width 0.30, blend 0.60 (still an approximation, not physical SSS).
- Contact radius x1.35 (0.54), strength x1.75 (default effective 0.56, capped 0.65).
  room_contact_shadows remains the base strength; zero still disables it.
No additional texture reads, extra light sources or changes to model UVs.

Maximum-interior / native-face revision (superseded clothing/AO values below):
- Runtime scope in profile field 4: -1 environment, 0 clothing/eyes, 1 native skin.
  Old profiles with 0 retain the previous x3 finish. Shared character materials
  select the milder scope; scope flags do not change DDS files or UVs.
- Environment normal amplitude x12 relative to the first version, bounded to an
  approximately 80-degree bend; clothing remains x3. This is a strong preset,
  not a claim that relief can be recovered beyond the diffuse's information.
- Skin entirely bypasses the room shader, restoring its native vertex lighting.
- AO: 32 depth taps, 0.8-unit radius, full default strength (base setting x3.125,
  capped at 1). Only the environment receives it; no reconstructed face shadows.
- Room rendering keeps layer order within environment/character groups and depth
  testing between them; native character shadows still draw on the environment.
- Existing GPU checks additionally cover native-skin routing and unmodified
  character colour/alpha when composited after maximum contact AO.

Current maximum-clothing / restrained-contact revision:
- Scope -.25 selects character clothing only; eyes/teeth remain 0, skin remains 1
  and bypasses the new shader entirely. Environment remains -1, unchanged.
- Clothing normal amplitude x12, bounded at approximately 80 degrees; direct
  highlight gain x12 with a .65 ceiling, roughness contrast x3 about .82.
  This is the maximum artistic preset, not a hardware or physical maximum.
- Environment AO retains 32 samples, radius reduced from .8 to .4 units, projected
  radius capped at 32 pixels, default maximum darkening reduced from 100% to 32%.
  Occlusion normalization /8 instead of /4 further reduces sparse dark patches.
  Configured base strength is capped at .45; zero still disables contact AO.
- GPU checks cover separate clothing normal/highlight response and bounded AO.

Object silhouettes:
- Current policy: characters use their original native blob shadows again.
  The client excludes them from silhouette generation and native-blob suppression.
  Player and dealer room ships still use the new vertical silhouette maps.
  Clothing relief is now x3 (another 50% reduction from x6); highlights and
  roughness contrast remain unchanged. Characters remain excluded from contact AO.
- Optional IRPRoomShadows v2, separate from the existing material interface.
- The player's room ship and dealer display ships cast downward
  silhouettes onto opaque environment depth before those actors are drawn.
  They do not receive these shadows, so faces retain native lighting.
- One reusable 1024 R32F map + D24X8 depth (~8 MiB total), 9 weighted PCF samples,
  .45 darkening, distance fade. Original UVs, geometry and light scripts untouched.
- Both rigid/CPU-deformed geometry and indexed bone palettes supported; legacy
  modelview-precomposed and separate world/view routes are handled explicitly.
- Alpha-tested cutouts supported; blended effects/glass excluded. Original LOD
  selection and engine visibility rules remain; this is not full scene GI.
- Failed/empty passes, unavailable INTZ, disabled SHADOWS or room_object_shadows=0
  retain native blob fallback. New shadows are independent of room_materials/AO.
- Installed shader warm-up now includes 22 variants. Release/reset frees the map.
- GPU fixture covers rigid/skinned shadows, both transform paths, above/below
  receiver rejection, transparent exclusion, state/alpha restoration, flight scope.

Previous character readability experiment (character silhouettes now disabled):
- Clothing normal amplitude reduced from x12 to x6. Highlights and roughness
  contrast unchanged; interior relief remains x12 and faces stay native.
- Character shadow rays slant downward by approximately 28 degrees in a fixed
  world direction (.45,-1,.30), separating the projections of head/body/feet.
  Strict zenith projection naturally collapses a standing figure into a small
  head/shoulder footprint. Ships retain strictly vertical projection.
- Character shadow bounds widened by 1.5 to fit the slanted volume; GPU fixture
  verifies the height-dependent extension and the unchanged ship projection.

Forbes/Columbia apron correction:
- detailmap_Coldeck|pad.tga021206172714 has generated normal strength set to zero.
  Its large diffuse atlas contains painted building shadows and markings, which
  the x12 height estimate incorrectly emphasizes. Original diffuse/detail maps
  (including their authored shadows) and other room relief remain unchanged.

Apply scopes to existing generated assets without regenerating maps:
  python tools/room_materials/update_scopes.py
New generate.py runs already emit these scopes.

Preparation:
  src/obj/asteroid_normals/venv/Scripts/python.exe tools/room_materials/generate.py
Build Release Win32 RP9, Shading, Deformable2 and freelancer with the repository's
usual SDK/toolset settings. No retail component layout or existing vtable changes.
  python tools/room_materials/check.py
  python tools/player_shadow_quality/check.py
  python tools/build_ice_surface_check.py
  python tools/room_materials/install.py
  python tools/room_materials/install.py --apply
Installer refuses a running game/server, verifies every input/output, backs up
replaced binaries, can restore the backup, and warms all 22 shader variants in the
actual game cache with a second-pass HIT verification.

RP9 spotlight compatibility:
- The native device and room/surface shader collection use the same translated
  COPY of each light. Original engine pointers and direct-light cache stay intact.
- Ordinary spotlights use d3d8to9's inner-angle /1.75 correction. Equal half-angle
  cosines use theta=0, falloff=1e-6, following FLHDE/fl-lighting-bug-fix, to avoid
  the modern fixed-function division by zero while preserving a hard cone.
- Both shaders retain that tiny positive exponent. Point/directional lights,
  scene files, light colours/positions, UVs and material strengths are unchanged.
- check.py exercises direct/queued lights, repeated updates, source preservation,
  near-equal angles, and real GPU core/penumbra/outside samples. Hard cones match
  FFP within 3 levels; soft inner cores retain the native D3D9 overshoot (the
  observed fixture delta is 10), whereas the material shader clamps attenuation.
- This fixes the known compatibility case; confirmation in the reported bar
  camera still requires an in-game comparison.

Generated files/reports live in src/obj/room_materials (not committed).
Room transparency ordering:
- The environment's DrawOpaque also queues blended meshes (including lamp shades).
  RP9 keeps that alpha bin across environment AO and the deferred actor pass,
  then sorts and flushes environment and actor transparency together.
- Room ship shadow capture temporarily makes alpha submissions immediate; blended
  casters are rejected by RP9 without consuming the pending room alpha records.
  The original per-record tags retain object lighting. Native renderer order is
  unchanged. Verify lamp/character overlap and showroom shadows in game.
The installer uses the generated manifest, not a directory-wide copy.
  python tools/room_materials/install.py --restore D:/games/FL_MOD/BACKUP/codex_room_materials_...

GPU fixture verifies exact one/two-layer native baseline when additions are zero,
normal/highlight response, indexed bone translation, transparent/env fallback,
flight isolation, actual INTZ contact shading, flat-plane preservation, alpha and
depth/blend restoration. These checks do not replace visual review of every room.
