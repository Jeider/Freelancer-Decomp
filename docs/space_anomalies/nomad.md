# Nomad Lair / Dyson surface implementation

### DDS mip loading fix (supersedes the alpha/depth experiments)

The earlier depth/alpha-state hypotheses did not fix the actual ripple. They are
removed; native membrane depth, alpha testing and culling are restored. D3DX9 saved
the web DDS files with dwPitchOrLinearSize=0. TextureLibrary used that field to
advance its mip cursor, so mip 1 started at byte 128 instead of 1048704. Later
levels sampled unrelated block bytes, visibly corrupting RGB and alpha.

`DdsMipCursor.h` now derives compressed level sizes from the DXT block grid and
clamps the tiny mip dimensions to one. TextureLibrary uses the same shared cursor
as the GPU regression. The test uploads both web DDS files through production RP9
SetTextureLevelData to DXT5 and RGBA8 targets and compares every pixel of all 11
levels against D3DX reference decoding. Before the fix, mip 1 showed maximum alpha
error 255 on 190346 pixels of the outer web. After the fix, all 44 comparisons
have exactly zero RGB and alpha error. Artwork and mip payloads remain unchanged.
Install using `install_dds.py` (Shading DLL and symbols only).

## Current membrane artwork: webs and overgrowth, 30 October 2026

At the user's explicit request, the two membrane textures now use generated
cobweb/root artwork. `assets/nomad_membranes/web-outer-v1.png` is pale silk and
violet roots; `web-inner-v1.png` is denser warm root overgrowth woven with silk.
The built-in image_gen prompts are recorded in `web-prompts.json`. Source PNGs
were subsequently edited by the user to clean up the alpha edges; the current
workspace PNGs and installed DDS contain those user edits, not the raw generation.
Source images
are 1254 square; the installed assets are 1024-square DXT5 with all 11 mip levels.
True alpha holes occupy approximately 48% and 32% of the compressed textures.
Material Oc is now 0.8, keeping the strands readable while holes remain clear.
The previous stationary membrane behaviour and fibre sheen remain in effect.

`build_membrane.py --web` converts only these two assets and renders a two-by-two
WRAP repetition preview using native alpha blending. Preview inspection showed
open holes and connected-looking repeated growth; it is not an in-game capture.
`check_web_assets.py` checks alpha coverage before/after compression and DDS mips.
`install_web.py` stages only four MAT banks from current game files; it verifies
that only the membrane texture payload and Oc change in each bank. All energy,
other texture/material leaves and addressing remain byte-identical. Run it without
arguments to stage, then with `--apply` for verified backup/install/cache warmup.

## Membrane and energy effects, 30 October 2026

The texture repaint was rejected. `install_energy.py` rebuilds all four Nomad MAT
banks from backup `codex_nomad_surfaces_20261030_004735_658987`, changing only the
two membranes' material `Oc` to 0.28. Every texture payload and other material leaf
is verified unchanged: original RGB/alpha and WRAP addressing remain. Generated
PNGs remain archived in `assets/nomad_membranes`; the old installer permits restore
only, so they cannot accidentally replace the artwork again.

`NomadEnergyPolicy.h` matches explicit material/texture pairs in beta and retail
libraries. Profiles 15/16 retain the native base draw and add one surface pass:
energy uses a wet organic coat derived from the original texture's height gradient,
with a gentler underlying glow. Existing energy MaterialAnim drives both layers;
there is no second clock or procedural scrolling. The two membranes skip creation
of MaterialAnim instances, retain the base UVs, and use lower opacity with a faint
stationary fibre sheen weighted by the fourth power of authored alpha. This opens
the gaps while retaining the denser strands. The pass samples the original texture
six times (five blurred glow taps plus centre alpha), with no added image assets,
parallax search or geometry changes. This is surface glow, not screen-space bloom
outside the mesh silhouette. Shared Dyson skin materials are excluded.

The overlay preserves native texture transforms, addressing, alpha holes and cull
mode, tests scene depth, never writes depth or framebuffer alpha, fades in fog,
and restores all captured D3D state and invalidates shader mirrors after drawing.
Missing/disabled shaders leave the original base visible. The new pair is included
in startup bytecode warmup, system driver warmup and offline cache preparation.

Optional `[Render]` settings in `EXE/port.ini`: `nomad_energy_fx = 1` (enable),
`nomad_energy_glow = 0.7` (strength, range 0..2). Existing `surface_shaders` and
`nomad_shader` also gate the effect. Stone/organic relief and ice shaders are unchanged.

`python tools/nomad_surfaces/check_energy.py` exercises the production RP9 shader
and routing on D3D9 hardware: identity selection, independence from a second clock,
alpha holes, opaque
energy alpha semantics, occlusion, authored UV transforms, fog, state restoration
and device release. It is a controlled GPU fixture, not an in-game visual capture.
Deploy with `python tools/nomad_surfaces/install_energy.py`, then `--apply`.

## Current state: original look restored, 30 October 2026

At the user's request, the Nomad shader block is restored exactly from
`src/obj/nomad_lair_revision/baseline/surface_material.hlsl`: 12-step parallax
occlusion, the original `nomad_layers.dds` fold/normal/height/vascular atlas,
and original organic motion, roughness and glow. The material identity policy
again selects exterior/interior profiles 5/7, so authored bone masks are no longer
bound to those materials. The recent ice finish is retained. The restoration
installer is `tools/nomad_surfaces/install_original.py`; it verifies backups and
warms the installed shader cache. The GPU fixture compares all four original
Nomad variants byte for byte, checks the original atlas routing, and renders the
restored materials. The later sections below describe the preceding experiments.

The subsequent close-up continuity fix retains this original material, but replaces
the full Lair shader's absolute derivative cutoffs (`1e-10` UV determinant and
`1e-12` tangent length squared) with the asteroid shader's relative projected-frame
check. A valid tiny tangent is normalized without the old absolute length clamp.
This prevents proximity/resolution-dependent jumps to flat shading. The lightweight
Dyson branch is unchanged. GPU regression tests scale the derivative frame and zoom
the UV chart, reproduce both original cutoffs, and require relief to remain present
with the fix. Deploy using `tools/nomad_surfaces/install_transition.py`.

### GPU cost assessment, 30 October 2026

`python tools/nomad_surfaces/benchmark.py` measures the installed shader with GPU
timestamps on an RTX 5080, original textures, eight interleaved retained samples
and eight repeated draws per sample. Full-screen median milliseconds:

| Material workload | 1920x1080 | 3840x2160 |
| --- | ---: | ---: |
| Original 12-step relief, one light, no shadow receiver | 0.141 | 0.578 |
| Same material, no parallax search (experimental control) | 0.058 | 0.239 |
| Six parallax steps (experimental control) | 0.107 | 0.443 |
| Twelve steps, eight lights, no shadow receiver | 0.188 | 0.832 |
| Twelve steps, lit shadow-map receiver, 16/32 search/filter | 0.217 | 0.950 |
| Twelve steps, blocked shadow-map receiver, 16/32 | 0.541 | 2.302 |
| Same blocked receiver, 4/4 shadow budget | 0.214 | 0.922 |

These are isolated, hot-cache material costs, not frame times or captured game FPS.
The shadow maps are synthetic 1024-square depth maps with one cascade and no dual
map, whereas the game can use larger maps, dual maps, cascade blends, overdraw and
shadow-map generation. All those costs, other scene rendering, and CPU submissions
are outside this benchmark. The shader sources used for the six/zero-step controls
exist only in benchmark memory; production settings are unchanged. Logs are in
`src/obj/nomad_surfaces/benchmark_1920.txt` and `benchmark_3840.txt`.

Assessment: no urgent need to reduce close-up relief on this GPU. Prioritize shadow
receiver cost if a real frame capture confirms it is limiting performance; next
consider smoothly reducing parallax work for distant/small surfaces. Nomad currently
retains the full material at every distance. Six steps save about 23% of the tested
unshadowed material cost, but image quality must be reviewed before deployment.

RP9 implementation, 27 October 2026. [Русский](../ru/space_anomalies/nomad.md).

Installed into `D:/games/FL_MOD` at 00:09 MSK; all eight payload files verified by SHA-256. Backup: `D:/games/FL_MOD/BACKUP/codex_nomad_surfaces_20261027_000906_769977`. No in-game flight was performed.

[Actual GPU gallery](nomad_previews/report.html). These are original mod textures on a curved material sample, not screenshots from the mission.

Lair materials now share coarse asteroid relief for the stone hull. The shader samples the
same `RockDetail` texture and strength settings as asteroids; it does not create a
separate family of procedural styles. Exterior rock, interior stone and the black
regions of ET textures remain rigid and matte.

Organic tissue is selected only by the authored ET/additive emission. Six submerged
texture samples have different view-dependent offsets, similar to ice, and compose
front to back with luminance-dependent opacity. Relative to the two-layer version,
depth is 1.67x and tissue normal strength is 1.5x. This remains one material draw;
there is no extra vascular overlay. A 16-second contraction moves only the emissive
region. The wetter finish uses roughness 0.15, stronger narrow and broad coat
highlights, and authored emission scaled by 1.20 plus a 0.18 pulse. Original alpha
is retained. Black ET pixels receive no time-dependent displacement, normals,
wet coat or added emission. Non-ET materials remain stone/bone.

Five 512-square RG-normal/B-height/A-mask maps separate the authored horns from
stone: `lair_rock_dtl01` through `04`, and `lair_skin02`. UV silhouettes are traced
in `tools/nomad_surfaces/lair_bones.py`; normals are derived from a smoothed version
of the original bone shading. They describe rounded bone relief, not new mesh
geometry. Existing diffuse/emission textures, materials, silhouettes and collisions
are unchanged. The five material IDs select masks for the same shader and finish.
Transparent membranes and energy surfaces retain their native routes.

Dyson retains its previous lightweight shader. The GPU fixture compares its compiled
bytecode to the pre-change snapshot. The ice material separately has a smoother
clear coat and stronger coloured reflection. Authored envmaps retain their palette;
DcDt ice without an envmap uses a blue/cyan/violet/pearl directional sky approximation,
not a scene reflection or another render pass. Submerged cracks remain visible.

Sphere's `solar/asteroids_mod/dyson/sphere_field.ini` uses an opaque camera-depth prepass and depth-equal material pass with the same vertex shader. Fully hidden fragments avoid material work; geometry is still submitted. Fading boundary cubes retain normal alpha/depth behaviour and are excluded from opaque occlusion. The scope pins native fallback while asynchronous shader warm-up is unfinished. Render states are restored afterwards. **Cube fields were not added to shadow-caster lists.**

Near-field frustum culling now uses a sphere containing the actual merged vertices, including each rock's offset, and expands cell enumeration accordingly. This applies to all static near fields, including Om11 large-asteroid fields. Sphere's approximately 2000-unit boxes exceed its 1650-unit cell width. Far billboards and dynamic-rock recycling are unchanged. In-game reproduction in Om11 and full-field performance still need a flight check.

`bin/port.ini`, `[Render]`: `surface_shaders=1`, `nomad_shader=1`, `nomad_relief=1.15` (0–2), `nomad_glow=0.32` (0–1). Disabling added glow does not remove authored illumination. Disabling the Nomad shader retains the culling fix. Restart after changing settings.

The 1024² packed atlas has RG normal XY, B height and A vein mask, a full renormalized mip chain, and occupies approximately 5.33 MiB. Code and reproducible generation/build/GPU/route/deployment tools are in `tools/nomad_surfaces`. The installer stages exact files, checks hashes and running processes, backs up originals and supports rollback; it does not modify game MATs or system INIs.

Validation covers Release Win32 builds, 200,000 conservative frustum witness cases, production SM3 variants, unchanged unrelated surface bytecode against the pre-change working-tree snapshot, visible relief, retained illumination in darkness, fog, exact prepass output, finite float HDR with degenerate/mirrored UV and grazing normals, real RP9 stage routing and device-resource reset. See the gallery logs for the actual run results. Screenshots do not establish in-game frame rate or eliminate unrelated sources of asteroid disappearance.

Further art work: geometric folds on doors or separate Dyson damage masks would require additional authored data; these are not part of this change.

29 October lair revision: build RP9 and Shading only; the executable is not part of
this deployment. `tools/nomad_surfaces/install_lair.py` stages the two DLLs/PDBs,
shared shader and five masks with hash checks and backups. The verification snapshot
is `src/obj/nomad_lair_revision/baseline/surface_material.hlsl`. The ice fixture can
use it through `ICE_SURFACE_BASELINE`. GPU previews are laboratory renders of the
original mod textures, not screenshots from a flight.

The subsequent six-layer revision changes only the shared shader. Set
`NOMAD_PREVIOUS_SHADER=src/obj/nomad_lair_volume/before.hlsl` when running the GPU
fixture to compare against the two-layer snapshot: black ET hull pixels must remain
identical and the emissive tissue must visibly change. Installation warms the real
game shader cache and requires every job to hit that cache on a second pass.

### BEAST single-layer Dyson bump (30 October 2026)

`tools/nomad_surfaces/install_beast.py` gives `beast.cmp` the private material
identity `beast_dyson_recess` (retained for compatibility) on its 28 groups across
three LODs. Vertices, indices, UVs and embedded 4096 atlas remain unchanged.
Other models using the original `dyson_surface_atlas` name are unaffected.

The initial POM16 version was replaced after the user reported 30 FPS near BEAST.
Profile 17 now uses one static bump layer in the existing colour pass: four fixed
filtered height samples plus the original diffuse lookup. No ray march, UV shift,
organic atlas, tissue animation or GGX coat. Normals have reduced strength and a
soft mineral highlight. Bump fades at subpixel scale and near atlas cell borders.
PCSS shadow reception is disabled for this profile, as for inexpensive rock
surfaces; the ordinary scene lighting and fog remain. This does not change the
model's geometry or shadow casting policy.

Optional `[Render] beast_relief = 1.0` in `bin/port.ini` controls bump strength
(0..2, restart required); 0 removes bump while keeping the material finish.
`nomad_shader` and `surface_shaders` disable the entire custom route.

Validation: `python tools/nomad_surfaces/check.py --beast-benchmark` tests actual
RP9 routing and real GPU output, disassembles the shader to verify exactly five
texture reads and only the lighting loop, checks identical bytecode for both
shadow variants, unchanged unlit diffuse coordinates, opacity and subpixel fade.
The production bump PS is 5788 bytes, compared with 9724 for the previous POM
without local shadows. On RTX 5080 at 1920x1080, interleaved GPU timestamp medians
were 0.0383 ms for bump versus 0.0638 ms for previous POM16. These are isolated
fullscreen material timings without local shadows, not a prediction of game FPS.
The comparison source is saved in `src/obj/beast_relief/before_bump.hlsl`.

`src/obj/nomad_surfaces/beast_bump.png` is a GPU fixture, not an in-game screenshot.
Build RP9, prepare with `install_beast.py`, then apply using `--apply` with the game
closed. The installer verifies hashes, creates a backup and checks that every
shader job hits the real game cache on the second warmup pass.


### Native Dyson comparison (30 October 2026)

For the earlier FPS comparison, all Dyson surface shaders were disabled. Materials in
`dyson_`, `detailmap_dyson_`, `asteroid_dyson`, and the private BEAST material select
Legacy. The same override applies to any material with a `dyson_` diffuse texture,
including aliases and transparent variants. RP9 also maps a direct Dyson profile
request from the cube field to Legacy, keeping its depth and colour transforms
on the same native path. Nomad Lair and other material families remain enabled.
The shader implementations are retained for comparison, but these materials no
longer select them. Install with `tools/nomad_surfaces/install_dyson_disable.py`.

### BEAST medium-quality normals restored (30 October 2026)

The private `beast_dyson_recess` material now selects profile 17 again, including
when its diffuse texture has a `dyson_` name. This explicit exception does not
re-enable the other Dyson materials, their texture aliases or cube-field shaders.

BEAST uses one colour pass with an eight-neighbour Sobel height gradient plus the
original diffuse sample (nine fixed texture reads). Compared with the simple
four-neighbour bump, the perpendicular smoothing gives steadier diagonal edges,
the height range is wider, the normal strength is moderate and the mineral highlight
slightly more pronounced. Original atlas UVs and alpha are unchanged. Atlas-border
and subpixel fades remain; no parallax march, organic layers or PCSS reception.
`[Render] beast_relief` still controls strength (default 1, range 0..2).

`check.py --beast-benchmark` passed routing/isolation, exact texture-read count,
identical shadow/no-shadow variants, visible relief, stationary UVs, original
opacity and distant fade. The PS is 6444 bytes. Interleaved timestamp medians on
RTX 5080 at 1920x1080 were 0.0438 ms for this variant, 0.0382 ms for simple bump,
and 0.0638 ms for the former POM16. These are isolated fullscreen material costs,
not in-game frame times. The five-read comparison snapshot is
`src/obj/beast_relief/before_medium.hlsl`.

Install with `tools/nomad_surfaces/install_beast.py` after rebuilding Shading.
The existing private material identity and all geometry/UV/texture data are retained.

### One-layer Dyson brick normals (30 October 2026)

The rest of the Dyson family now selects the lightweight Dyson profile again:
`dyson_`, `detailmap_dyson_`, `asteroid_dyson` materials, aliases with a `dyson_`
diffuse texture (including path/suffix variants), and the direct asteroid cube-field
profile. BEAST's explicit `beast_dyson_recess` identity retains its separate Sobel
profile and `beast_relief` value.

In executable-adjacent `port.ini`:

```ini
[Render]
dyson_shader = 1
dyson_relief = 1.0
```

`dyson_relief` ranges from 0 to 2, default 1; zero removes normal perturbation.
`dyson_shader = 0` restores native rendering, including both cube-field passes.
Restart after changing either setting. Dyson is independent of `nomad_shader`;
the common `surface_shaders` switch still applies.

The normal comes from four filtered neighbouring height samples of the original
texture. Sampling steps use its actual dimensions. Dark joints read as grooves,
and footprint filtering fades subpixel bump instead of switching the entire
material by distance. The shader preserves diffuse UVs, opacity and authored
detail/emission combinations. It adds no extra draw pass: the field's existing
depth prepass still uses the same vertex transform as colour rendering. Unsupported
blend/layout combinations (including additive energy) retain the native renderer.

There are no parallax steps, organic layers or PCSS samples. The compiled PS has
six texture instructions: four height reads, diffuse, and optional authored detail;
plain materials skip the detail branch. The shader is 6196 bytes. Lair and BEAST
pixel bytecode are unchanged by this revision.

Validation: `python tools/nomad_surfaces/check.py --dyson-only` exercises production
RP9 depth/colour/fade routing, feature disable, texture dimensions, independent
strength, aliases and BEAST isolation, and real GPU output for the brick texture,
opacity, UVs, detail/emission, near/far stability and texture-read bounds.
Build RP9 and Shading, then prepare/install with `install_dyson.py`; the installer
preserves other INI settings, backs up changes and warms the game shader cache.

### BEAST simplified to four-neighbour bump (30 October 2026)

BEAST now uses four cardinal height samples instead of the eight-neighbour Sobel
filter. With diffuse, that is five fixed texture reads in its single colour pass.
The separate atlas-border protection, filtered height, distant fade, restrained
highlight and `beast_relief` control remain. The installed setting stays at 2.0;
this revision simplifies the sampling rather than lowering relief strength.

`check.py --beast-benchmark` passed the GPU checks at normal and maximum strength,
opacity/UV preservation, stationary appearance and subpixel fade. It also verified
identical Lair/Dyson pixel bytecode against `before_simplify.hlsl`. The BEAST PS is
5748 bytes. At 1920x1080 on RTX 5080, strength 2, interleaved GPU timestamp medians
were 0.0381 ms for the simplified shader and 0.0441 ms for the previous Sobel
shader, roughly 14% less isolated material time. This is not a whole-scene FPS
measurement. Install with `install_beast.py`; only the shared shader source needs
replacement when the preceding runtime build is already installed.

### ANM material coverage audit (30 October 2026)

`tools/nomad_surfaces/audit_system.py` resolves the active ANM system's solar
archetypes, model VMesh material CRCs, embedded/external material libraries and
diffuse names; its JSON inventory is in `src/obj/dyson_bump/anm_audit.json`.
The ordinary Dyson classifier already covered the city (1 instance), generators
(5), platforms (17) and Nomad gate (1), using `detailmap_dyson_*`/`dyson_*`.

The 60 `trade_lane_ring_anomaly_dyson` objects were missed: `virt_dyson.mat` uses
`virt_tlr_root2`, `virt_tlr_mid2`, `virt_tlr_out2` with diffuse aliases `vdyson1`,
`vdyson3`, `vdyson2`. These three exact texture identities are now recognized,
including case/path variants. Their actual BtDetailMapMaterial layout with two UV
sets and MODULATE2X marble detail passed the production RP9 route fixture.

The experimental `nomad_land_v2`, `nomad_land_v2_1` surfaces, alien spheres,
NomadMaterial ships and `alien_lv` remain outside the Dyson classifier. No assets
or INI settings changed. `install_dyson_aliases.py` installs only Shading DLL/PDB.
