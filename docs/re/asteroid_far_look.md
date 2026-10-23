# Asteroid fields from afar (port-only, RP9)

How the port draws an asteroid field beyond the near field (cubes, billboards, dynamic asteroids). Retail
draws a vertical textured ribbon (`[Band]`, `BandBuildExclusionRings` / `CliAsteroidDrawFarPiece`) lit once
into vertex colours and hidden when you look along it. Every FL_MOD field zone is a thick ellipsoid, so a
cylinder wall around a blob reads wrong, and at Freelancer's scale (fields 15-25 km across, seen from 5-70 km)
the big rocks are resolvable points: 100 m at 20 km is about 10 px.

## Far rocks ([FarRocks], 2026-10-24)

Code: `Client/far_rocks.cpp`, shader `DATA_EXTRA/SHADERS/far_rocks.hlsl`, hooks in `cli_asteroid.cpp`
(parse, forget, band skip, `CliAsteroidGetFarInfo`), `space_scene_obj_draw.cpp` (draw), `render_ex.cpp`
(shutdown). A fixed per-field set of camera-facing impostor quads fills the zone ellipsoid, clumpy, lit per
pixel by the sun (dark and bright sides, planet shadow), depth-tested against the scene, fading in where the
near field ends and out where the band fades out.

Switches (`bin/port.ini [Render]`): `far_rocks = 1` (master), `far_rocks_auto = 0` (1 = every field with a
`[Band]` and no `[FarRocks]` gets a default one that replaces the band; for testing without data edits),
`far_rocks_max_total = 24000` (rocks drawn per frame over all fields, nearest field first). Also off with the
Effects option off, the Asteroids option off, or Asteroid Ext outside 1..2 (the band's own gates), and on RP8.

### Data

`[FarRocks]` in a field ini (any order against the other sections); every key is optional, the defaults come
from the field's other sections and are read when the rocks are built.

| key | default | meaning |
|---|---|---|
| `count` | 8000 | rocks generated for the field (500..20000) |
| `size` | 15, 250 | min, max rock radius in metres |
| `size_power` | 2.6 | slope q of the radius pdf r^-q (q > 1): many small, few big |
| `edge_softness` | 1.5 | exponent e of the ellipsoid profile `(1 - \|q\|^2)^e` |
| `thickness` | max dynamic `band_thickness` (0 = none) | half-height of a slab about the zone's local XZ plane |
| `clump_size` | 0.35 * largest zone radius | the clump field's scale, metres |
| `clump_coverage`, `clump_softness`, `clump_amount` | 0.45, 0.15, 0.7 | weight `profile * ((1 - amount) + amount * clump)` |
| `start_dist` | billboards: their sphere centre `R + A` (sig8 3667 m); else `max(1.1 * placement_radius, fill + 1.25 * cube, 1500)` | inner edge: rocks fade in (dither) from here |
| `start_fade` | 0.3 * start_dist | length of the dither ramp |
| `far_dist`, `far_fade` | band: `fade[3]`, `fade[3] - fade[2]` (fades times height; sig8 68 km, 8 km); no band: 70000, 10000 | outer edge: alpha fade |
| `color` | band color_shift (else billboard, else 0.55, 0.5, 0.45) times the field's diffuse tint | albedo, r,g,b 0..255 |
| `color_b` | color * 0.65 | the other end of the per-rock albedo mix |
| `brightness`, `ambient` | 1.0, 0.08 | sun gain; fill light as a fraction of the sun colour |
| `min_pixels` | 1.0 | smallest drawn radius in pixels (smaller rocks keep it and lose alpha by area) |
| `lump`, `bump`, `spin` | 0.25, 0.5, 4 | outline lumpiness, surface bump, max spin deg/s per rock |
| `surge`, `sparkle`, `sparkle_strength` | 0.5, 0.06, 1.5 | opposition brightening, share of rocks with a glint, glint gain |
| `replace_band` | 1 | skip the retail band (and the field's exclusion bands) while the rocks draw |

### Placement (once per field)

Built lazily the first frame the field is within reach (at most one field per frame; a log line gives the
count, classes, cells and milliseconds). Size classes `J = clamp(ceil(log2(max/min)), 1, 6)` with geometric
edges; each class gets its share of `count` from the power law. A class walks cells of its own size
`c = max(cbrt(1.5 / n), 2 * r_hi, box / 48)` in the zone-local frame, takes `floor(E + u)` rocks per cell from
the expected number (at most 12), places each at a hashed offset, keeps it with probability `w(p) / w_cell`
(the profile bound of the cell, the clump at its centre), gives it a radius by the class's inverse CDF and
rejects it inside any exclusion zone of the field (`InZone(pos, radius)`) or outside the ellipsoid. Per rock
it stores the offset from the zone centre, radius, a seed, an albedo mix and the planet-shadow fraction
`SolarSunlitAt(world)` baked once (planets do not move), so the rocks match ships, billboards and dynamic
asteroids. Rocks are sorted biggest class first (seed order inside a class) and expanded to 6 vertices
(FVF `XYZ | DIFFUSE | TEX1`, 24 bytes): diffuse A sunlit, R / G the corner, B the albedo mix; tex = radius, seed.

### Per frame and draw order

`FarRocksDrawAll` runs right after the opaque bucket (`DrainBucket(Cam, 0, false)`) in both paths of
`DrainMeshAndAsteroids`, before the rings, the haze, the sprite layers and the near field, so all of them
depth-test against the rocks. The band's bucket-2 pieces are drawn earlier in the frame, which is why the
band skip (`FarRocksReplacesBand`, called by `CliAsteroidDrawFarPiece`) is a predicate: gates pass, the
field's rocks are built, `replace_band`, and not blocked by fog. There is no distance test in it.

For each field in reach (`|cam - centre| - largest radius <= far_dist`, nearest first) the CPU picks the size
classes whose projected radius is at least a quarter of `min_pixels` (`r_hi * PxPerUnit / dNear`) and uploads
that prefix (cut by the remaining `far_rocks_max_total`) with `DrawExPrimitiveUp`, in batches of at most 8192
rocks. One Ex pass for all fields, scene depth kept, `ZENABLE 1, ZWRITEENABLE 1, ZFUNC LESSEQUAL`, alpha
blend SRCALPHA / INVSRCALPHA, no culling.

The shader (vs_3_0 / ps_3_0) makes the quad in view space at least `min_pixels` wide, fades by distance
(near edge: a screen-door dither, since the rocks are big there; far edge: alpha, since they are tiny), and
shades a procedural lumpy sphere: an outline from two sine harmonics of the angle, a sphere normal with a
bump, per-rock hashed albedo, Lambert with a limb term, a phase factor with an opposition surge, and a glint
on a few rocks. Below 2 px a rock is lit by the Lambert sphere phase integral. An offline-baked impostor
atlas is the production follow-up; the procedural look needs no assets.

### The depth decision

The rocks draw inside the scene with the scene depth buffer bound (not a manual INTZ compare): an Ex pass
cannot sample INTZ and depth-test at once (`ExSelectTarget` unbinds the sampler when the depth surface is
kept), the scene's far plane in FL_MOD is mostly 50-100 km (`space_farclip`, sig8 = 60000) so most rocks lie
inside it, and real depth gives correct occlusion against stations, planets and ships, between rocks without
sorting, and lets the later passes (space haze, nebula volume, soft particles) see the rocks. Rocks beyond the
scene far plane are not clipped: the vertex shader clamps their clip z to `w * (1 - 2^-22)`, just in front of
the cleared depth, so they draw over the sky only, behind everything the scene drew. Far-bucket solars beyond
the far plane write no depth and may be overdrawn by beyond-far rocks (accepted, rare).

### Fog

A field with `contains_fog_zone`, or with a nebula at its zone centre (retail's lookup, `FCliAsteroid::ZeroD4`),
draws rocks only while `NebulaVolume::IsActiveFor(thatNebula)` (the volume fogs them by depth); otherwise it
keeps the band. Inside a field enclosure rocks draw only with `NebulaVolume::IsActive()`.

### Costs

Upload 144 bytes per rock: 8000 rocks 1.15 MB (about 0.1-0.2 ms), 24000 rocks 3.5 MB (about 0.4 ms). GPU:
16-48k triangles, mostly 1-4 px, about 0.1-0.2 ms. Memory 1.15 MB per built field. Build once per field:
about 14k coarse-grid weights plus about 60k cell bounds for an 8000-rock field, a few tens of ms (see the
log line). Shader: vs 72 instruction slots, 4 temporaries; ps 260 slots, 7 temporaries.

## Field dust ([FieldDust], 2026-10-24)

Far rocks give a field discrete, resolvable rocks; between them a real belt shows the unresolved small debris.
The field dust is that: a faint, clumpy lit haze filling the zone ellipsoid, brighter on its sun side, glowing
when you look toward the sun through it, cut by a planet's shadow. `field_dust.cpp`, `field_dust.hlsl`; port.ini
`[Render] field_dust` (1), `field_dust_auto` (0: 1 = every field with a `[Band]` and no `[FieldDust]` gets the
defaults, for testing), `field_dust_resolution` (0.5, 0.25..1: scale of the march target).

### The model

One analytic volume per field, no real ray march. The view ray against the zone ellipsoid (the zone radii as
`nebula_volume.cpp` `ZoneRadii`, the ray in the zone's unit space by `NebulaZoneSpan`), clamped by the scene
depth (the INTZ depth, which holds the far rocks too). The density profile is `(1 - |q|^2)` (q = the point in
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
