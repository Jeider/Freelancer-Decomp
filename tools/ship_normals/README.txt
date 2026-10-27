Automatic ship normals with glossy hull finish

In flight, opaque hull materials on the player ship, NPC CAPITAL / CRUISER / GUNBOAT / TRANSPORT objects
and nearby human stations receive normals derived from existing diffuse textures.
Solar battleships are included by their full hull model:
ships/.../*_battleship.cmp, *_dreadnought.cmp, *_osiris.cmp (case insensitive).
This includes pirate and Jack variants, and the utility mining/mining_with_panels
models used by Roid_Miner, Roid_Miner2 and rm_Roid_Miner.
Ordinary NPC fighters, freighters, asteroids, glass and emissive materials do not.
Content exceptions: transport_small.cmp (FIGHTER) and transport_armored_beta1.cmp
(FREIGHTER) are included as transports, without enabling ordinary fighters/freighters.
Models/materials containing nmd or nomad, plus models sharing those materials,
are excluded. Existing room materials remain independent.

Dark paint is interpreted as a recess. Smooth luminance gradients suppress pixel
noise; some broad lighting is removed, but painted shadows cannot be identified
perfectly. No model, UV, original texture or light edits are needed. Surface
normals change lighting/reflection only; geometry and silhouette do not move.

Active profile: original glossy hull finish restored; only the normal strength
is reduced. The clear coat, original specular lobes and authored environment
reflection/modulation are retained.
261 DXT5nm normal maps (up to 512 pixels, full mipchains), 649 material profiles
(457 ships + 192 human solars). Profiles are separate because some ship and solar
materials share names but have different textures. All normal maps preload at
device creation: about 56.8 MiB compressed GPU data plus
D3D9 managed system memory. No normal-map disk reads during object draws.
The previous 162 matte surface maps remain as inactive generated assets; the
renderer no longer loads or binds them, so they consume no GPU memory.
Generic instancing is bypassed for selected objects to retain per-material scope.
Actual FPS impact must be measured in gameplay.

[Render] in port.ini: ship_normals defaults to 1; ship_normal_strength defaults
to 0.25 (one quarter of strength 1; range 0..4). Slope is limited to
2 (about 63 degrees). The player retains the previous 2000..6000 metre fade.
NPC CAPITAL and solar battleship hulls fade at 320..400 metres.
NPC CRUISER/GUNBOAT/TRANSPORT (including trains), the transport model exceptions,
and solars with actual DockingSpheres fade at 160..200 metres;
other solars fade at 80..100 metres. STATION type alone does not imply a dock.
Exceptions: station_large_a/b, station_small_a/b (including b_lod_tgk) and
trading_outpost_lod fade at 400..500 metres; only these complete models qualify.
Distance is measured per surface pixel from the camera. A conservative object
sphere test disables the normal variant entirely when the whole object is outside
the range. Large objects crossing the boundary retain the variant, but distant
pixels skip the normal texture sample and tangent calculation.
The new shader uses slot s13 only in its own variant, separate from ice/Nomad/rooms.

solar_content.py audits the human library allowlist: dockable01/02/03, misc01/02,
tink, ring (jump gates), hole (human gate shell), TLR, space_dmg, space_tank,
shield (human metal caps), s_inv, co_base (artificial parts only), Freeport7.
Dyson, Nomad, lair, ast_* libraries are never catalogued. Rock/ice/vegetation
materials inside otherwise human libraries are also rejected, as is greenhouse
glazing. human_solars.txt restricts runtime solar models to the matching content.
Embedded stale copies of shared station textures use the remastered library
source; ambiguous sources are skipped. Original content and UVs remain untouched.

Generate: src/obj/asteroid_normals/venv/Scripts/python tools/ship_normals/generate.py
Compress: python tools/ship_normals/compress.py
Check: src/obj/asteroid_normals/venv/Scripts/python tools/ship_normals/check.py
Build: python tools/ship_normals/build.py (RP9 + equipment-enabled freelancer).
Warm: python tools/asteroid_normals/warm.py --game-root D:/work/Freelancer-Decomp
Stage: python tools/ship_normals/install.py
Install (game stopped): python tools/ship_normals/install.py --apply
Restore: python tools/ship_normals/install.py --restore <backup-directory>
Installer verifies original assets, backs up changed files, validates hashes,
and restores on copy failure. Source DATA is never changed. Optional --strength
changes only Render.ship_normal_strength; --with-equipment stages the matching
Common/Server DLLs when installing a client built with that feature enabled.

GPU check compares the nearby lighting output with src/obj/ship_normals/matte/before.hlsl
(the pre-matte local shader snapshot), at strengths 0, .25, 1 and 4. It also checks
both near-distance fades and object eligibility/cutoffs. On a fresh checkout,
supply that baseline explicitly for the visual regression.
