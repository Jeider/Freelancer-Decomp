Detailed player and nearby station shadows; experimental asteroid normals disabled.

The current game config already has shadow_near_resolution=8192 and
shadow_far_resolution=4096. No FPS/config edit is made by this installer.
The player ship (ship bit + bit 7) samples the two high-resolution near maps.
Static receivers now also sample these existing maps close to the camera, so
the player's nose/wings remain visible in its shadow on a nearby station.
Detailed static sampling fades from 0.8 to 1.0 times shadow_near_radius
(120..150 metres with the installed radius 150), as well as at cascade edges.
Farther station surfaces and NPC hulls retain the shared far map/static cache.
The far map covers the entire local scene and cannot retain small ship details.
Do not describe this as a separate 4096-square map allocated for every NPC.

The player's filter budget stays unchanged (currently 64 search / 192 filter).
Other receivers are capped at shadow_world_search_samples=16 and
shadow_world_filter_samples=32. These optional port.ini keys default to those
values. Existing lower user settings, adaptive distance quality, NPC moderate and
simple tiers remain respected. Near maps still render all relevant casters so
their shadows fall on the player's hull. This saves receiver work, not all near
map generation cost/memory. 8192 means pixels, not 8 MiB: R32F is 256 MiB/map.

Asteroid normal-map experiment: runtime hook/interface/shader work removed,
ku_tgk_rock_normal.tga removed from MAT. Every other MAT leaf is byte-preserved.
The generated texture/tooling remain archived in the workspace; near and far
asteroid render paths return to their pre-experiment behavior.

Validation: production RP9 receiver flags/constants/sampler routing, actual GPU
pixels distinguishing dark near / lit far maps, world shadow preservation,
NPC tiers, lower filter settings, static radial fade, soft-filtered nose/wing/gap
silhouette samples, scope reset/cleanup. Existing ice GPU fixture
covers all shader variants and unchanged cockpit/glass/ice behavior.

Install: build Release Win32 client + RP9 (FreelancerRp9=1), run prepare_assets.py,
then install.py (stage) and install.py --apply after the game is closed.
Backups and file hashes are verified. Installation warms the real game shader
cache. Current installs use tools/room_materials/install.py (stage, then --apply)
and require all 18 surface/shadow/room variants to HIT on a second pass.
