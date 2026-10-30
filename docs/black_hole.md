# Black hole (port-only, RP9)

## Physical attraction

`Common.dll` now applies point gravity to locally simulated ships through
`CShip::do_simulation_controller`, at IVP's fixed physical step. The existing
ship controller stays active with the engine off; normal flight, thrusters,
cruise and AI steering retain their forces and receive gravity in addition.
Static sources are enabled and configured in their `[Object]` sections in the system
INI. The normal `ReadSystemFileObject` universe loader reads these keys into the
owning `SYSTEM::GravityObjects` table, keyed by object nickname. It is copied and
released with that system. Solar initialisation/destruction registers/removes the
live source. There is no archetype whitelist, separate config scan, or `port.ini`
Gravity switch. Objects without `gravity = true` or mounted generator equipment have no attraction.

For `om13`, `universe.ini` selects `SYSTEMS_MOD/OMEGA13/om13.ini`. Its existing
`om13_bh` object receives the settings below; **om13_alt is not enabled or edited**.
Restart after editing system data. The obsolete `[Gravity]` section is removed
from `port.ini` during migration.

```ini
[Object]
nickname = om13_bh
archetype = BlackHoleCore
; Other existing object keys stay here.
gravity = true
gravity_radius = 20000
gravity_reference_radius = 5000
gravity_acceleration = 60
gravity_softening = 650
gravity_max_acceleration = 300
gravity_edge_fraction = 0.2
```

| Key | Default | Meaning |
|---|---|---|
| `gravity` | false | Enable attraction for this named object only. |
| `gravity_radius` | 20000 | Outer field radius, metres; clamped to 1..1000000. |
| `gravity_reference_radius` | 5000 | Reference distance before fade/cap, metres; 1..1000000. |
| `gravity_acceleration` | 60 | Acceleration at the reference distance, m/s^2; 0..10000. |
| `gravity_softening` | 650 | Soft core radius, metres; 1..1000000. |
| `gravity_max_acceleration` | 300 | Maximum acceleration from this source, m/s^2; 0..10000. |
| `gravity_edge_fraction` | 0.2 | Outer radius fraction fading to zero; 0.001..1. |
| `gravity_mode` | attract | `attract`, `repel`, or `suppress`. Unknown names retain the previous/default mode. |
| `gravity_suppression` | 1 | For `suppress`: fraction of gravity cancelled inside the field, 0..1, with the same outer fade. |

Non-finite numeric values leave the previous/default value intact. Key order is
irrelevant; a missing nickname cannot inherit the previous object's gravity.
Different objects and systems can use different strengths and radii. Fields add
as vectors, with each source capped independently. On multiplayer clients, static
solar snapshots omit the nickname field, so their object ID (the same nickname
hash) resolves the system setting. No new network packet layout is needed.

Source eligibility compares universe/physics system IDs rather than object
database addresses. In SP, `StarSysEnter` reconnects the shared player ship to
the client database while solars retain the server database; requiring equal
database pointers silently discarded the entire field for the player. The
regression fixture models these two databases in one system and verifies both
player and server-NPC impulses, while retaining remote-copy exclusion.

The field follows a softened inverse-square law: `a = mu * delta / (r²+s²)^(3/2)`.
`mu` is normalised from the reference acceleration; a smoothstep fades the outer
edge and acceleration tends continuously to zero at the exact centre. Acceleration
does not depend on ship mass. It is added to the same pending velocity accumulator
as engine impulses and committed by the existing IVP gravity pass. It introduces
no direct position changes, torque, damage, cruise cancellation or changes to drag.

Remote/golem-controlled copies and scripted golem motion are excluded, as are
ships in trade lanes and immovable bodies. Multiplayer uses the existing ownership:
the local player simulates its own ship and the server simulates NPCs; remote
snapshots carry the resulting motion. All clients and the server need the same
Common build and system INI data; there is no new configuration negotiation or
server validation protocol. AI is subject to the force but does not yet plan routes
around gravity wells or estimate gravitational acceleration in navigation queries.
Solars, projectiles, loot and debris are not pulled by this first implementation.

The physics is independent of `[Render] black_hole_*`, `damage`, `interference`
and `drag_modifier`. Turning off the visual does not turn off attraction. The
existing damage and drag zones are independent of these per-object fields.

Validation: `python tools/physics/check_gravity.py` compiles the production field,
native system-object reader, registry, ship callback, IVP gravity pass and velocity commit with a zero-damping
fixture. It checks the reference acceleration, centre/edge/cap, multiple sources,
mass independence, exclusions, source lifecycle, system/database changes and
identical fixed-step trajectories grouped into 30/60/144 FPS. Config-off, missing,
zero-strength, NaN and clamped settings are covered, together with per-object
strengths, nickname key order, multiplayer ID fallback, system copying and an
unconfigured system with the same object nickname. `check_zone_drag.py` retains
the independent drag regression. Release Common builds; actual flight and a
multi-machine multiplayer session still require in-game validation.

Installed the per-object loader and the `om13_bh` settings into FL_MOD, removed the
obsolete global Gravity section, and verified all four installed files by SHA256.
`om13_alt.ini` retained its original hash. Backup:
`D:/games/FL_MOD/BACKUP/codex_gravity_system_20261029_162716_807`.


`src/freelancer/Client/black_hole_visual.cpp` + `DATA_EXTRA/SHADERS/black_hole.hlsl` replace the ALE
effects `gf_bhring` (disc) and `gf_neutronstar` (core glow) on solars whose archetype is listed in
`black_hole_archetypes` (default `BlackHoleCore`, system om13_alt). `bh_chunks` and `gf_bh_splash_new`
stay ALE and draw over the black hole.

A full-screen pass ray-marches each pixel through a Schwarzschild field (r_s = 1 horizon radius), bends
the ray (Cartesian photon equation), and lenses the already rendered opaque scene and background. The
accretion disc (local XZ plane, spin axis +Y) has a Novikov-Thorne-like temperature profile, Keplerian
Doppler beaming, gravitational redshift, differential rotation with noise filaments and spiral arms,
plus polar jets, a photon ring and a glow. Nearer opaque objects stop the ray (scene depth); if the
renderer cannot initialise, the retail ALE effects stay.

Base rooms (the main-menu intro, `mod_intro.thn`): the PSYS entities bound to `Intro_volcanoplanet_sun`
(the drawable disc instance, positioned by its Thorn frame) and `gf_neutronstar` (suppressed) are claimed in
`FThornPsys::BindVisEffect`; drawn from `RoomControl` after translucent room geometry and before the
Alchemy particle pass. If the room has no captured scene depth, every pixel is treated as sky.

## Gravity equipment and mission sources

Equipment accepts the same `gravity*` field keys, plus `gravity_compensation = 0..1`
for personal protection. Definitions are held separately from the native archetype
layout, support `inherit`, and are released with the archetype. No exported object
layout or network packet layout changes. Only mounted equipment enters the device
registry; cargo does not. Runtime checks require functioning equipment and a live
owner. Unmount/destruction removes the registry entry. Standalone devices use `[GravityDevice]` (`Archetype::GravityDevice`, class 0x23;
`CEGravityDevice`, type bit 0x02000000). They activate when mounted, including on a
solar, and have no repair-droid behavior. Existing gravity keys on legacy equipment
remain supported. Their hit points, cargo state and named slot survive save/load.

`DATA/EQUIPMENT/gravity_devices.ini` supplies five loadout-ready prototypes:

| Nickname | Effect |
|---|---|
| `gravity_generator` | Attract nearby ships; 5 km radius, 10 m/s² at 1 km, capped at 40 m/s². |
| `gravity_repulsor` | Same field geometry, outward acceleration. |
| `gravity_suppressor` | Cancel gravity for ships within 5 km, fading over the outer 20%. |
| `gravity_compensator_70` | Cancel 70% of gravity acting on the owner. |
| `gravity_compensator_full` | Cancel all gravity acting on the owner. |

The client data configuration registers this equipment file. These are passive
devices without an energy cost, separate activation UI, shop entries or localized
infocards. Add `ids_name`, `ids_info`, goods and markets when making retail items.
They are not automatically added to any ship or mission. To add an emitter, extend
the NPC's or solar's existing loadout, retaining its other equipment:

```ini
[Loadout]
nickname = your_existing_loadout
; Existing equipment remains here.
equip = gravity_generator, HpHardware01
```

For player installation through the equipment UI, declare compatible slots on
`[Ship]` (or on `[Solar]` for tools using its slot rules):

```ini
equipment_slot = HpHardware01, hardware, 10
```

A device declares `hp_type = hp_hardware_special_N`, with N from 1 to 10. The UI
accepts classes up to the slot ceiling; exact `hp_type` hull declarations work too.
`HpHardware01` is only an example name. Authored loadouts and saves may mount a
device on any name, including `HpRoot`, without declaring it as a UI slot. Runtime
creation trusts the descriptor's mounted flag and preserves its hardpoint. No CMP
attachment/model is created for internal hardware. Cargo remains inert regardless
of its archetype or any leftover hardpoint text.

Class/family/occupancy checks run at player mount requests, not while loading
existing equipment. Unchanged authored mounts do not block unrelated transactions.
New mounts and relocations must satisfy shiparch; transfer to a new hull validates
the whole transferred loadout. Loading never relocates devices or converts them to
cargo based on current class limits.

For story solars, reference this loadout with the existing `[MsnSolar] loadout =`
key, then use ordinary `Act_SpawnSolar = solar_nickname`. No static system `[Object]`
entry is needed. Native save equipment descriptors retain the installed device;
mission solar restoration recreates its loadout. Settings come from the equipment
INI on load, so tuning definitions affects existing saves. A recreated functioning
standalone device starts enabled; a transient script/API deactivation is not a new
saved preference. Native `ActivateEquip` can control the equipped device by ID.

Ship emitters follow physical positions. Remote emitter copies use replicated world
positions; duplicate SP server/client devices are counted once, preferring local
physics. Emitters do not pull or repel themselves; suppression also protects its
own owner. Only ships receive forces, retaining the existing remote/golem/tradelane
exclusions. The strongest personal compensator and strongest local suppression field
are used, rather than summing identical devices. Final acceleration is:
`sum(attract/repel vectors) * (1 - compensation) * (1 - suppression)`.
Cancellation does not remove existing velocity, change engine thrust or affect drag.

Validation: `check_gravity.py` retains static-field/IVP regressions;
`check_gravity_devices.py` exercises devices, cargo, moving sources, self-exclusion,
death/disable/unmount/reload, inheritance, suppression and duplicate/remote sources.
`check_gravity_devices_native.ps1` loads the actual equipment file through the built
Common.dll and verifies all five devices on real CShip/CSolar objects, including
native save-descriptor restoration, damage deactivation and cargo handling.
Live mission and multi-machine multiplayer acceptance remain to be performed;
all peers need matching Common.dll and equipment definitions.

## port.ini [Render]

| Key | Default | Meaning |
|---|---|---|
| `black_hole_visual` | 1 | 0 restores the ALE effects (reload) |
| `black_hole_archetypes` | BlackHoleCore | comma-separated solar archetype nicknames |
| `black_hole_horizon` | 650 | horizon radius, metres |
| `black_hole_lens_extent` | 40 | lensing volume radius, horizon radii |
| `black_hole_steps` | 180 | max march steps |
| `black_hole_exposure` | 1.6 | tone-map exposure |
| `black_hole_lens` | 1.0 | lensing strength |
| `black_hole_disk_inner` / `_outer` | 3 / 14 | disc radii, horizon radii |
| `black_hole_disk_opacity` | 0.9 | disc opacity |
| `black_hole_spin` | 1.0 | disc rotation speed |
| `black_hole_heat` | 1.0 | disc temperature scale |
| `black_hole_doppler` | 1.0 | Doppler beaming strength |
| `black_hole_jet` | 0.6 | polar jets (0 = off) |
| `black_hole_glow` | 1.0 | photon ring and bloom |
| `black_hole_brightness` | 1.4 | overall brightness |
| `black_hole_tint_r/g/b` | 1 | colour tint |
