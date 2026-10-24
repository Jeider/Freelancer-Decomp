# Asteroid fields from afar (port-only, RP9)

How the port draws an asteroid field beyond the near field (cubes, billboards, dynamic asteroids). Retail
draws a vertical textured ribbon (`[Band]`, `BandBuildExclusionRings` / `CliAsteroidDrawFarPiece`) lit once
into vertex colours and hidden when you look along it. Every FL_MOD field zone is a thick ellipsoid, so a
cylinder wall around a blob reads wrong, and at Freelancer's scale (fields 15-25 km across, seen from 5-70 km)
the big rocks are resolvable points: 100 m at 20 km is about 10 px.

## Far rocks ([FarRocks], 2026-10-24, v3)

Code: `Client/far_rocks.cpp`, shader `DATA_EXTRA/SHADERS/far_rocks.hlsl`, hooks in `cli_asteroid.cpp`
(parse, forget, band skip, `CliAsteroidGetFarInfo`), `space_scene_obj_draw.cpp` (draw), `render_ex.cpp`
(shutdown). A fixed per-field set of camera-facing quads fills the zone ellipsoid, clumpy. Each rock is drawn as a
lit lumpy sphere (outline from two sine harmonics, sphere normal with a bump) and wears the diffuse texture of one
of the field's dynamic asteroids, so from afar the rocks look like the ones that fly inside the field. Lit as a
whole field (sun N.L at the impostor normal plus system ambient), alpha blended and depth tested against the
scene. It fades in where the billboards end and out where the band fades out.

History: v1 was the procedural lumpy sphere (glints, spin, screen-door fade, depth write, no texture). v2 replaced
it with the billboards' texture on flat sprites (no flicker, cross-fade with the billboards) but the flat sprites
were rejected. v3 is v1's shape with v2's fixes: no `clip` / dither (outline and fades are alpha), no spin (a
static per-rock turn from the seed), no depth write, per-field lighting, the dynamic asteroids' texture and tint.

Switches (`bin/port.ini [Render]`): `far_rocks = 1` (master), `far_rocks_auto = 0` (1 = every field with a
`[Band]` and no `[FarRocks]` gets a default one that replaces the band; for testing without data edits),
`far_rocks_max_total = 24000` (rocks drawn per frame over all fields, nearest field first),
`far_rocks_static_vb = 1` (each field's rocks in a static GPU vertex buffer, uploaded once; 0 = sent every frame
with `DrawExPrimitiveUp`). Also off with the Effects option off, the Asteroids option off, or Asteroid Ext
outside 1..2 (the band's own gates), and on RP8.

### Data

`[FarRocks]` in a field ini (any order against the other sections); every key is optional, the defaults come
from the field's other sections and are read when the rocks are built.

| key | default | meaning |
|---|---|---|
| `count` | 8000 | rocks generated for the field (500..20000) |
| `size` | 15, 250 | min, max rock radius in metres (the quad's half size) |
| `size_power` | 2.6 | slope q of the radius pdf r^-q (q > 1): many small, few big |
| `edge_softness` | 1.5 | exponent e of the ellipsoid profile `(1 - \|q\|^2)^e` |
| `thickness` | max dynamic `band_thickness` (0 = none) | half-height of a slab about the zone's local XZ plane |
| `clump_size` | 0.35 * largest zone radius | the clump field's scale, metres |
| `clump_coverage`, `clump_softness`, `clump_amount` | 0.45, 0.15, 0.7 | weight `profile * ((1 - amount) + amount * clump)` |
| `start_dist` | billboards: `max(Float04, Float04 + Float00 - Float2C)` (below); no billboards: `max(1.1 * placement_radius, fill + 1.25 * cube, 1500)` | inner edge: rocks fade in from here |
| `start_fade` | 0.2 * start_dist | length of the fade-in beyond `start_dist` |
| `far_dist`, `far_fade` | band: `fade[3]`, `fade[3] - fade[2]` (fades times height; sig8 68 km, 8 km); no band: 70000, 10000 | outer edge: alpha fade |
| `color` | with textures: each dynamic asteroid's tinted diffuse; without: band color_shift (else billboard, else 0.55, 0.5, 0.45) times the field's diffuse tint | tint, r,g,b 0..255; multiplies the texture (replacing the dynamic asteroid's tint) or, with no texture, is the rock colour |
| `dynamic_texture` | 1 | 0 = do not look for the dynamic asteroids' textures: plain tint-coloured rocks |
| `texture_scale` | 1.0 | repeats of the texture over a rock's face (the texture wraps) |
| `lump` | 0.25 | how far the outline departs from a circle (0 = round) |
| `bump` | 0.5 | surface normal bumpiness |
| `brightness` | 1.0 | gain of the sun term |
| `ambient` | 1.0 | scale of the system ambient term |
| `min_pixels` | 1.5 | smallest drawn radius in pixels (smaller rocks keep it and lose alpha by area) |
| `replace_band` | 1 | skip the retail band (and the field's exclusion bands) while the rocks draw |

Removed (ignored if present): `shape` (v2), `color_b`, `spin`, `surge`, `sparkle`, `sparkle_strength` (v1 extras).

### The hand-over from the billboards

`BillboardDraw` (`asteroid_billboard.cpp`) keeps every rock inside `Float04 + Float00` of the camera, where
`Float00 = R` (the fade radius) and `Float04 = R + A` (the distance of the rock sphere's centre ahead,
`cli_asteroid.cpp` ~612, `FUN_0054de10`): the sphere mode puts rocks within `R` of a point `Float04` ahead (so no
farther than `Float04 + R`), the port's band mode (`BandFar = Float04 + Float00`, ~943) spreads them over the
annulus up to that distance. Alpha is 1 inside and falls to 0 at that edge over `Float2C = R * fade_dist_percent`
(band mode, ~1201: `FarRamp = (BandFar - dist) / Float2C`; sphere mode narrows the band with depth, ~1220).
The rocks therefore start at

    start_dist = max(Float04, Float04 + Float00 - Float2C)

(`far_rocks.cpp` `BuildField`, read through `CliAsteroidGetFarInfo`: `BillboardCentre`, `BillboardRadius`,
`BillboardFade`) and come in over `start_fade` = 20% of it, so the billboards' last `Float2C` metres and the
rocks' first 20% cross-fade with no gap. sig8: `Float04 = 3667`, `R` about 2570, `Float2C` about 770 gives
`start_dist` about 5460, full rocks at about 6550, billboards gone at about 6230. A field without billboards
keeps the old default (cubes and placement radius).

### Placement (once per field)

Built the first frame the field is known, all fields at once (`FarRocksDrawAll` walks the registry; the frame's
budget is 100 ms, the rest follow the next frame; a log line gives the count, classes, cells, start distance and
texture per field and the running total). The band is already hidden by then: `FarRocksReplacesBand` is true
whenever the feature and the program are on, the field has `replace_band` and did not fail to build, and the field
is not fog-blocked, built or not. (v1 hid the band only once the field was built, one field per frame, so a field
popped between the band and the rocks as the camera turned.) Size classes `J = clamp(ceil(log2(max/min)), 1, 6)`
with geometric edges; each class gets its share of `count` from the power law. A class walks cells of its own size
`c = max(cbrt(1.5 / n), 2 * r_hi, box / 48)` in the zone-local frame, takes `floor(E + u)` rocks per cell from
the expected number (at most 12), places each at a hashed offset, keeps it with probability `w(p) / w_cell`
(the profile bound of the cell, the clump at its centre), gives it a radius by the class's inverse CDF and
rejects it inside any exclusion zone of the field (`InZone(pos, radius)`) or outside the ellipsoid. Per rock it
stores the offset from the zone centre, radius, a seed (0..1; the shader derives the turn of the lumps and the
texture, the lump hashes and the texture offset from it), a texture index (a hash pick among the field's dynamic
textures) and a brightness jitter byte. Rocks are sorted biggest class first (seed order inside a class) and
expanded to 6 vertices (FVF `XYZ | DIFFUSE | TEX1`, 24 bytes): diffuse A texture index * 85, R jitter (the shader
maps it to 0.85..1.1), G / B the corner; tex = radius, seed.

### The dynamic asteroids' texture

Retail path, followed in the port: `[DynamicAsteroids] asteroid = <nickname>` is parsed by
`CliDynamicAsteroidParseIni` (`cli_asteroid_dynamic.cpp`, FUN_00525800): `Archetype::GetDynamicAsteroid` ->
`Arch->load()`, then `QueryEngineComponent(Arch->EngineIndex, Iids::Mesh)` -> `IMesh::OpenFaceGroup(0, 1)` ->
`GetFaceGroupMaterial(&Dyn->Material)` (`FCliDynamicAsteroid::Material`, +0xA8). That `IMaterial` is what
`CliDynamicAsteroidDraw` binds (`Material->Bind`) for every rock. Its diffuse texture is the string parameter
`Dt_name` of the material (`Shading/Material.cpp`, e.g. the DcDt schema: `Dc` colour, `Dt_name` texture name);
`FSwappedMaterial::CaptureOriginal` (`swapped_material.cpp`) reads it the same way: `GetParameterCount`,
`GetParameterDescriptor(i).Name == "Dt_name"`, `GetParameterValue(i)` with `Type == 7` and the string in
`Payload0`. `CliAsteroidGetFarInfo` does this for every manager of the field (`MaterialDiffuseTexture`), drops
`(None)` and duplicates (at most 4) and hands out the name with the manager's `TintedDiffuse0..2` (the field's
diffuse tint times the manager's `color_shift`, clamped to 1). `BuildField` resolves each name with
`TextureRefLoad` (TextureLib `FindTextureByCrc` + a playback reference, the field holds it until forgotten or
shutdown) and every draw asks `TexShapeGetGpuHandle(ref, 0)` for the GPU handle (so a device reset needs nothing)
and binds it to sampler i (linear, linear mips, wrap). A rock picks its texture by a hash at build time.

Mapping (pixel shader, one fetch per pixel): `uv = rot(N.xy) * 0.5 * texture_scale + (h4, h5)`, N the bumped
impostor sphere normal, `rot` the rock's turn from its seed, `(h4, h5)` hashes of the seed; sampled with
`tex2Dgrad` (the pick differs between rocks, so the fetch is not in uniform flow), times the manager's tint,
times jitter. A texture that cannot be reached (no `Dt_name`, name not in the texture library, handle not bound)
leaves that rock on the tint colour (`Fallback`: band / billboard colour times the diffuse tint, or `color`); a
field without dynamic asteroids has no textures: the same tint-coloured rocks. The texture's average colour is
not computed (the texture is reached; no CPU lock of a mip).

### Lighting (once per field, not per rock)

`UpdateLighting` on the CPU: the unit sun direction from the zone's centre (`FindSystemSunSphere`), the sun's
colour there (`FindSunLightColour`), one planet-shadow factor at the centre (`SolarSunlitAt`), refreshed every 16
frames (the sun does not move, the planets barely), and the system ambient every frame
(`EngineLightGetAmbientRgbBytes` / 255 times `ambient_intensity` times the field's ambient tint, as
`BillboardComputeLighting` forms it, times `ambient`). Per draw the CPU turns the sun direction into view space
(the view rotation rows) and sends it with the sun colour * sunlit * `brightness` and the ambient as pixel
constants. The pixel shader lights the impostor normal:

    lit    = 0.7 * mu0 + 0.3 * mu0 / (mu0 + mu + eps)        // mu0 = N.L, mu = N.z (limb darkening, Lommel-Seeliger)
    colour = albedo * jitter * (sun * lit * phase + ambient)
    phase  = 0.85 + 0.5 * pow(L.z, 6)                          // opposition surge

A rock under 2 px radius uses the sunlit share of a Lambert sphere at its phase angle instead of a normal. With no
sun the rocks are flat lit with a fill of 0.6. No per-rock shadow (v1 baked one per rock).

### Per frame and draw order

`FarRocksDrawAll` runs right after the opaque bucket (`DrainBucket(Cam, 0, false)`) in both paths of
`DrainMeshAndAsteroids`, before the rings, the haze, the sprite layers and the near field. The band's bucket-2
pieces are drawn earlier in the frame, which is why the band skip (`FarRocksReplacesBand`, called by
`CliAsteroidDrawFarPiece`) is a predicate with no distance test.

For each field in reach (`|cam - centre| - largest radius <= far_dist`, nearest first) the CPU picks the size
classes whose projected radius is at least a quarter of `min_pixels` (`r_hi * PxPerUnit / dNear`) and draws that
prefix (cut by the remaining `far_rocks_max_total`): one `DrawExVertexBuffer` call per field from the field's
static buffer (`far_rocks_static_vb`), or `DrawExPrimitiveUp` in batches of at most 8192 rocks. One Ex pass for
all fields, scene depth kept, `ZENABLE 1, ZWRITEENABLE 0, ZFUNC LESSEQUAL`, alpha blend SRCALPHA / INVSRCALPHA, no
culling. The dynamic textures are bound on samplers 0..3 (`BindExPipelineTexture`, linear, linear mips, wrap) from
`TexShapeGetGpuHandle(ref, 0)`.

The shader (vs_3_0 / ps_3_0) makes the quad in view space (1.2 radii or `1.2 * min_pixels` wide), with alpha
`cover * nearFade * farFade` (cover = area ratio under `min_pixels`; the fades are smoothsteps of the distance)
times the pixel shader's outline coverage (`saturate((edge - r) / fwidth(r))`), so a rock fades in alpha and never
pops: no `clip` dither, no interleaved-gradient dissolve, no spin (its wrap was a pop), no depth write.

### The depth decision

The rocks draw inside the scene with the scene depth buffer bound for the test (not a manual INTZ compare): an Ex
pass cannot sample INTZ and depth-test at once (`ExSelectTarget` unbinds the sampler when the depth surface is
kept), the scene's far plane in FL_MOD is mostly 50-100 km (`space_farclip`, sig8 = 60000) so most rocks lie
inside it, and real depth gives correct occlusion against stations, planets and ships. v2 does not write depth
(blended impostors): the space haze, the field dust and the nebula volume after it no longer see the rocks in the
depth buffer. Rocks beyond the scene far plane are not clipped: the vertex shader clamps their clip z to
`w * (1 - 2^-22)`, just in front of the cleared depth, so they draw over the sky only, behind everything the scene
drew. Far-bucket solars beyond the far plane write no depth and may be overdrawn by beyond-far rocks (accepted,
rare).

### Fog

A field with `contains_fog_zone`, or with a nebula at its zone centre (retail's lookup, `FCliAsteroid::ZeroD4`),
draws rocks only while `NebulaVolume::IsActiveFor(thatNebula)` (the volume fogs them by depth); otherwise it
keeps the band. Inside a field enclosure rocks draw only with `NebulaVolume::IsActive()`.

### The static vertex buffer (CPU cost)

`IRenderPipelineEx::CreateExVertexBuffer(bytes, data, &buffer)` / `DestroyExVertexBuffer` and
`IRPDrawEx::DrawExVertexBuffer(buffer, prim, fvf, stride, firstVertex, primitiveCount)` (appended at the end of
each interface; RP9Ex.cpp). A `D3DPOOL_MANAGED` buffer, so it survives a Reset; the bytes are kept and the GPU
buffer re-created after a device re-creation (the same as the managed volume textures). The draw goes through the
stream cache like `DrawExPrimitiveUp` (select the FVF, `FlushDrawState`, then stream 0 = the buffer, and none
again afterwards). It is on `IRPDrawEx` because it is a draw with the same preconditions as
`DrawExPrimitiveUp` (inside an Ex pass, a program bound). Fields upload once when built; a draw that fails falls
back to the upload path for that field.

### Costs

6 vertices (24 bytes each, 144 bytes) a rock, no index buffer: 8000 rocks are 48000 vertices, 1.15 MB, 24000
rocks 3.5 MB. With the static buffer that is uploaded once per field (when it is built or after a device
re-creation) and nothing per frame but 8 vertex and 8 pixel constants, up to 4 texture binds and one draw call per field; the
upload path (`far_rocks_static_vb = 0`) copies up to 1.15 MB per field per frame (about 0.1-0.2 ms CPU for 8000).
GPU: 16-48k triangles, mostly 1-4 px, blended without depth write, about 0.1-0.2 ms. Lighting: three small
`FindSun*` / `SolarSunlitAt` calls per field every 16 frames. Memory 1.15 MB per built field in the client plus
the same in the pipeline's copy and the GPU buffer. Build once per field: about 14k coarse-grid weights plus about
60k cell bounds for an 8000-rock field, a few tens of ms (see the log line). Shader (v3): vs 59 instruction slots, ps 288 (4 texture
slots, one fetch per pixel; the arithmetic is the sphere normal, outline, atan2 and the lighting), more per pixel
than v2's 18, but the rocks are mostly 1-4 px, so the fill cost stays small.

## Field dust ([FieldDust], 2026-10-24)

Far rocks give a field discrete, resolvable rocks; between them a real belt shows the unresolved small debris.
The field dust is that: a faint, clumpy lit haze filling the zone ellipsoid, brighter on its sun side, glowing
when you look toward the sun through it, cut by a planet's shadow. `field_dust.cpp`, `field_dust.hlsl`; port.ini
`[Render] field_dust` (1), `field_dust_auto` (0: 1 = every field with a `[Band]` and no `[FieldDust]` gets the
defaults, for testing), `field_dust_resolution` (0.5, 0.25..1: scale of the march target).

### The model

One analytic volume per field, no real ray march. The view ray against the zone ellipsoid (the zone radii as
`nebula_volume.cpp` `ZoneRadii`, the ray in the zone's unit space by `NebulaZoneSpan`), clamped by the scene
depth (the INTZ depth; the far rocks write none since v2). The density profile is `(1 - |q|^2)` (q = the point in
unit space) whose chord integral is closed form; taken about the chord midpoint `Tm` with half length `H` it is
`2 H (1 - |Pm|^2) - 2 A H^3 / 3` (A = |L|^2 the squared length of the direction in unit space; the odd terms drop
out, nothing cancels badly at long range). The exact optical depth is `tau = sigma * I * mean`, where `mean`
is a ratio estimator over `steps` stratified jittered samples (`sum(p m) / sum(p)`, p the profile, m the
modulation: `p^(edge_softness - 1)`, the slab, the clump noise, the clear zone round the camera), so the
profile's exact shape stays smooth and the noise only modulates it. With steps = 0 (beyond `lod_distance` of the
zone surface) it is the closed form times the clear zone at the midpoint. `sigma` comes from `opacity`: the
1 - transmittance straight through the centre along the shortest axis (the chord integral of `1 - r^2` there is
`4/3 R`). Alpha per field is `min(1 - exp(-tau), max_opacity) * strength`, strength the far fade
(`far_dist` / `far_fade`, the band's fade[3] / fade[3] - fade[2] by default, as the far rocks).

Lighting is single scattering with the light constant along the ray, taken at the chord midpoint M: the sun's
colour at the zone centre (`FindSunLightColour`) times the Henyey-Greenstein phase (`forward`, blended with an
isotropic term by `forward_weight`) plus an opposition term `back * pow(saturate(-cos), 6)` (the sun behind the
camera), times `exp(-sigma * l * 0.5)` for the dust the sunlight crosses (l = the distance from M to the zone
edge toward the sun), times the planets' shadow, plus `ambient` of the sun colour as fill. The shadow is the
ring shader's `SphereShadow` (penumbra from the sun's size) for the two nearest casters of
`SolarShadowCasters`, which returns the planets `SolarSunlitAt` uses with the same reach (`shadow_max_length`,
the ring reach, the `planet_eclipses` reach); each is cut off beyond its reach exactly like `SolarSunlitAt`,
smoothed over the last 20% of it. So a field only sits in a planet's shadow where the ships would. The noise is the
space haze's shared 32^3 tileable volume (`SpaceHazeEnsureNoise`), world-anchored to the zone (the zone's
position decides its offset in the tile).

### Passes and cost

Pass 1 marches at `field_dust_resolution` into an own render target (FP16 when `bFloat16Target`, else
A8R8G8B8: premultiplied rgb, 1 - transmittance), pass 2 composites it depth-aware (four low-res texels, relative
depth threshold 0.1, the best match across a depth edge: `nebula_composite.hlsl`'s upsample) with ONE / INVSRCALPHA.
Both cover only the union of the fields' screen rectangles (the bounding sphere's exact perspective extent);
nothing on screen is no pass. Up to 4 fields per pass, nearest first, front to back. Drawn in `SpaceObjDrawPass`
after the opaque scene and the far rocks, before `NebulaVolume::Draw`: the space haze and the sprite layers
(drawn earlier) lie under the dust, the nebula over it. Known limit: a nebula BEHIND a dust field on screen dims
the dust slightly (its march does not know the dust). Estimate at 1080p, one field covering the screen: march
0.52 Mpx x (1 depth read + 6 noise reads + ~120 ALU) about 0.08-0.15 ms, composite about 0.1 ms; a field seen
from afar covers a small rectangle (about 0.02 ms). 4 MB FP16 target. Shader: march ps_3_0 about 1530 slots
(10 texture), 14 temporaries (the fields unrolled, the steps a loop); composite 80 slots, 8 temporaries.

### Not drawn

A field with `contains_fog_zone` or a nebula at its zone centre (`StarSysFindNebula`, looked up once): the
nebula is the medium there (li_cal's fields). Everything while `G_FieldEnclosure == 2`. The effects option off,
asteroids off, no scene depth.

### Data

`[FieldDust]` in the field ini, all keys optional:

| key | default | meaning |
| --- | --- | --- |
| `opacity` | 0.22 | 1 - transmittance through the centre along the shortest axis (sets sigma) |
| `max_opacity` | 0.35 | cap of a field's alpha per pixel |
| `color` | band (else billboard) color_shift x field diffuse, else 0.6, 0.55, 0.5 | r, g, b 0..255 |
| `ambient` | 0.12 | share of the sun colour as fill |
| `brightness` | 0.8 | the sunlit part |
| `forward`, `forward_weight` | 0.55, 0.5 | HG g, blend of isotropic and HG |
| `back` | 0.25 | opposition term (sun behind the camera) |
| `noise_scale` | 4000 | metres of one tile of the noise |
| `coverage`, `softness`, `clump` | 0.45, 0.25, 0.7 | `f = (1 - clump) + clump * 2 * smoothstep(coverage - softness, coverage + softness, n)` |
| `edge_softness` | 1.5 | exponent of the edge profile (ratio estimator) |
| `thickness` | max dynamic `band_thickness` (0 = none) | slab about the zone's XZ plane |
| `clear_radius` | billboard Float04, else 2000 | density x `smoothstep(0.5 r, r, t)` along the ray |
| `steps` | 6 | noise samples per field per pixel (0..8) |
| `lod_distance` | 25000 | beyond this from the zone surface only the closed form |
| `far_dist`, `far_fade` | band fade[3], fade[3] - fade[2], else 70000, 10000 | the whole field's strength `saturate((far_dist - d) / far_fade)` |
