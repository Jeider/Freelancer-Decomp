# Ship, solar and asteroid archetypes, collision groups, asteroid fields

This page documents `[Ship]`, `[Solar]`, `[Asteroid]`, `[AsteroidMine]`, `[DynamicAsteroid]` and `[CollisionGroup]` sections of the archetype files, the system-file `[Object]` section read through the solar archetypes (`CSolar::ReadObj`), the object-reputation pass over the same sections, and the asteroid-field files read by Common.dll and the server. Keys of every record (`nickname`, `type`, `hit_pts`, ...) and the value notation are in [archetypes-and-equipment.md](archetypes-and-equipment.md); hardpoint-type names are in [archetypes-weapons.md](archetypes-weapons.md#hardpoint-type-names).

**File location / how it is found.** `freelancer.ini` `[Data]` keys ([freelancer-ini.md](freelancer-ini.md)): `ships` (dev ini: `ships\shiparch.ini` and `ships\rtc_shiparch.ini`) -> `Archetype::LoadShips`; `solar` (`solar\solararch.ini`) -> `LoadSolar`; `asteroids` (`solar\asteroidarch.ini`) -> `LoadAsteroids`. Asteroid-field files are named by the `[Asteroids] file =` key of each system file ([systems-and-bases.md](systems-and-bases.md)). The system `[Object]` sections are part of the per-system files listed in `universe.ini`.

Because `inherit` and `CollisionGroup` act on records that were just read, section order inside the file matters: a donor must be defined before the record that inherits it, and a `[CollisionGroup]` belongs to the nearest preceding `[Ship]` / `[Solar]`.

## Keys shared by `Ship` and `Solar` (`EqObj::read`)

Applied after the `Root` keys ([common_archetype_ships.cpp:720](../../src/Common/common_archetype_ships.cpp#L720)).

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `docking_camera` | bool | true | Camera behaviour while docking. | [L725](../../src/Common/common_archetype_ships.cpp#L725) |
| `docking_sphere` | `[0]` type name, `[1]` hardpoint, `[2]` float radius, optional `[3]` animation | none | One docking sphere per line; repeated keys **append**. `[0]`: `berth` (1), `moor_small` (3), `moor_medium` (4), `moor_large` (5), `ring` (6), `pad` (6), `jump` (7), `airlock` (8), case-insensitive; any other name gives type 0 (no message). `[1]` is lower-cased on read. `[3]` is the dock animation script name (stored only if present). | [L731](../../src/Common/common_archetype_ships.cpp#L731) |
| `fuse` | `[0]` fuse nickname (id), `[1]` float, `[2]` float | none | Damage fuse for the whole object; repeated keys **append**. In `Server.dll` the fuse is lit (with `[1]` as its start time argument) when the object's hit points are at or below `[2]`, and when damage makes the hit points cross `[2]` ([server_gameobject.cpp:1193](../../src/Server/server_gameobject.cpp#L1193), [:1455](../../src/Server/server_gameobject.cpp#L1455)); so `[2]` is the hit-point threshold and `[1]` the start time. The client reader names the two floats the other way round ([client_equip_fx.cpp:3410](../../src/freelancer/Client/client_equip_fx.cpp#L3410)); the two port modules disagree and this was not settled against the retail binary here. Fuse files: see [server.md](server.md#fuse-files). | [L757](../../src/Common/common_archetype_ships.cpp#L757) |
| `shield_link` | `[0]` shield archetype (id), `[1]` shield hardpoint, `[2..n]` generator hardpoints | none | Links a shield to the hardpoints of its generators; repeated keys **append**. Each line receives the next link id, counting up from 0xfff0. Parameters from `[2]` on are collected until the first empty one. | [L772](../../src/Common/common_archetype_ships.cpp#L772) |
| `nomad` | bool | false | Ship is a Nomad (used by AI/visual code). | [L797](../../src/Common/common_archetype_ships.cpp#L797) |

Example (synthetic):

```ini
[Ship]
nickname = demo_fighter
ids_name = 1100
ship_class = 0
mass = 40
hold_size = 50
steering_torque = 7000, 7000, 8000
angular_drag = 2, 2, 2
hp_type = hp_gun, HpWeapon01, HpWeapon02
hp_type = hp_fighter_shield_generator, HpShield01
shield_link = demo_shield_01, HpShield01, HpShield01
docking_sphere = berth, HpDockMountA, 2, Sc_open dock A
```

## `[Ship]`  ([common_archetype_ships.cpp:1003](../../src/Common/common_archetype_ships.cpp#L1003))

`Root` + `EqObj` keys plus the following. A ship also carries a *CommReferrable* part.

Optional port feature: with `FreelancerEquipmentSlots=1` and `[Equipment] internal_classes=1`,
`equipment_slot = Name, armor|scanner|tractor, MaximumClass` adds a logical internal slot
accepting classes 1 through MaximumClass (1..10). No CMP hardpoint is needed. Exact-class
`hp_type = hp_armor_special_N|hp_scanner_special_N|hp_tractor_special_N, Name` is also accepted.
See [equipment slots](../re/equipment_mount_classes.md) for examples and compatibility limits.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `inherit` | nickname | - | Handled by the loader before `read()`; copies the donor ship, see below. | [loader L298](../../src/Common/common_archetypeloader.cpp#L298) |
| `bay_door_anim` | cstr (whole value) | empty | Animation script for the bay door. | [L1011](../../src/Common/common_archetype_ships.cpp#L1011) |
| `HP_bay_surface` | cstr (whole value) | empty | Hardpoint on the bay surface. | [L1017](../../src/Common/common_archetype_ships.cpp#L1017) |
| `HP_bay_external` | cstr (whole value) | empty | External bay hardpoint. | [L1023](../../src/Common/common_archetype_ships.cpp#L1023) |
| `HP_tractor_source` | cstr (whole value) | `HpHeadlight` | Tractor beam origin hardpoint. | [L1029](../../src/Common/common_archetype_ships.cpp#L1029) |
| `num_exhaust_nozzles` | int | 9 | Number of engine exhaust nozzles; the maximum (`Ship::MAX_EXHAUST_NOZZLES` = 9) is not enforced here. | [L1035](../../src/Common/common_archetype_ships.cpp#L1035) |
| `hold_size` | float | 0.0 | Cargo capacity. | [L1041](../../src/Common/common_archetype_ships.cpp#L1041) |
| `linear_drag` | float | 100.0 | Linear drag. | [L1047](../../src/Common/common_archetype_ships.cpp#L1047) |
| `angular_drag` | float x3 (`[0]`,`[1]`,`[2]`) | 0.75, 0.75, 0.75 | Angular drag X, Y, Z. | [L1053](../../src/Common/common_archetype_ships.cpp#L1053) |
| `steering_torque` | float x3 | 2000, 2000, 2000 | Steering torque X, Y, Z. | [L1061](../../src/Common/common_archetype_ships.cpp#L1061) |
| `nudge_force` | float | 0.0 | Side-thrust ("nudge") force. | [L1069](../../src/Common/common_archetype_ships.cpp#L1069) |
| `strafe_force` | float | 0.0 | Strafe force. | [L1075](../../src/Common/common_archetype_ships.cpp#L1075) |
| `strafe_power_usage` | float | 0.0 | Power draw of strafing. | [L1081](../../src/Common/common_archetype_ships.cpp#L1081) |
| `ids_info1`, `ids_info2`, `ids_info3` | int | 0 | Extra infocard string ids. | [L1087](../../src/Common/common_archetype_ships.cpp#L1087), [L1093](../../src/Common/common_archetype_ships.cpp#L1093), [L1099](../../src/Common/common_archetype_ships.cpp#L1099) |
| `ship_class` | int | 0 | Ship class number; not validated. | [L1105](../../src/Common/common_archetype_ships.cpp#L1105) |
| `nanobot_limit` | int | -1 | Maximum number of nanobots; -1 = not set. | [L1111](../../src/Common/common_archetype_ships.cpp#L1111) |
| `shield_battery_limit` | int | -1 | Maximum number of shield batteries; -1 = not set. | [L1117](../../src/Common/common_archetype_ships.cpp#L1117) |
| `max_bank_angle` | float, degrees | 0.0 | Values above 180 are clamped to 180, then converted to radians. Negative values are not clamped. | [L1123](../../src/Common/common_archetype_ships.cpp#L1123) |
| `msg_id_prefix` | str (whole value, stored in a 64-char string) | empty | Prefix of the comm message ids of this ship (`CommReferrable`). | [common_watchable.cpp:75](../../src/Common/common_watchable.cpp#L75) |
| `hp_type` | `[0]` hardpoint-type name, `[1..n]` hardpoint names | none | Declares which hardpoints of the model accept equipment of that type (the "legal hardpoints"). One entry per line; repeated keys append new entries. `[0]` must be in the hardpoint-type table; an unknown name (or one with value 0) swallows the line silently. Names from `[1]` on are read until the first empty parameter. | [L1151](../../src/Common/common_archetype_ships.cpp#L1151) |

### Ship `inherit`

`inherit = <ship nickname>` ([common_archetypeloader.cpp:294](../../src/Common/common_archetypeloader.cpp#L294)): the donor is looked up (hash of the value) among the ships already loaded; a miss logs `ArchDB::Get(...) failed` and the warning "'inherit' failed. couldn't find %s" and the line is ignored. A hit overwrites the record being read with: all `Root` fields, the docking spheres, a clone of the donor's collision groups, `msg_id_prefix`, `bay_door_anim`, `HP_bay_surface`, `HP_bay_external`, `HP_tractor_source`, `ids_info1..3`, `ship_class`, `num_exhaust_nozzles`, `hold_size`, `linear_drag`, `angular_drag`, `steering_torque`, `nudge_force`, `strafe_force`, `strafe_power_usage`, `max_bank_angle`, the `hp_type` list, `nanobot_limit`, `shield_battery_limit`. The record's own nickname is kept. **Not copied:** `fuse`, `shield_link`, `nomad`, `docking_camera`. Everything read before the `inherit` line is lost; keys after it override.

## `[Solar]`  ([common_archetype_ships.cpp:892](../../src/Common/common_archetype_ships.cpp#L892))

`Root` + `EqObj` keys plus:

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `inherit` | nickname | - | Loader-level, as for ships but among the solars; a missing donor is silently ignored. Copies `Root` fields, docking spheres, collision groups, `destructible`, `solar_radius`, `toughness`, `open_anim`, `jump_out_hp`, `loadout`. | [loader L365](../../src/Common/common_archetypeloader.cpp#L365) |
| `toughness` | int | 0 | Toughness rank (also used as the reputation rank of solar objects). | [L900](../../src/Common/common_archetype_ships.cpp#L900) |
| `destructible` | bool | false | Solar can be destroyed. | [L906](../../src/Common/common_archetype_ships.cpp#L906) |
| `radar_wireframe` | bool | false | Draw existing model `VMeshWire` geometry at its actual world position/orientation/scale on the radar. Inherited and reloadable. Overrides normal radar contact count, targeting, parent, hidden and detection filters; only screen clipping applies. Parts without wires are skipped. | [implementation](../../src/freelancer/Client/radar_wireframe.h) |
| `open_anim` | cstr (whole value) | empty | Animation script that opens the solar. | [L912](../../src/Common/common_archetype_ships.cpp#L912) |
| `loadout` | id (whole value) | 0 | Default `[Loadout]` nickname for instances of this solar (see [goods-loadouts-constants.md](goods-loadouts-constants.md)). | [L918](../../src/Common/common_archetype_ships.cpp#L918) |
| `jump_out_hp` | cstr (whole value) | empty | Hardpoint ships jump out of. | [L924](../../src/Common/common_archetype_ships.cpp#L924) |
| `solar_radius` | float | 500.0 | Radius used for placement/atmosphere checks. | [L930](../../src/Common/common_archetype_ships.cpp#L930) |

Optional trade-lane ring activation animations (port):

```ini
[Solar]
nickname = Trade_Lane_Ring
left_ring_anim = Sc_activate left
right_ring_anim = Sc_activate right
```

Each value is an animation script name in the solar model. Missing or empty keys
disable the feature for that side; no archetype or animation names are hardcoded
in the client. Motion, duration and frame count come entirely from the asset.
The first server-accepted activation request (including the F3 docking command)
starts the entrance side once. Existing users on either side and ongoing animation
playback suppress further starts; requests are never queued. Cancellation or
departure does not interrupt playback. Removal of the solar or unloading the system
releases its handles. Activation messages are shared through the existing server
protocol; this does not add late-join playback/time snapshots.

For a stationary idle pose, remove any looping `use_animation` equipment or `anim`
on that loadout/object which moves the same joints. The original procedural
`TLR_Left`/`TLR_Right` spin is automatically skipped on configured sides.
Other equipment animations remain unchanged. Scripts must bind to the appropriate
joint; missing scripts or unbound channels are logged and skipped.

`tools/tradelane/prepare.py` prepares two separate scripts for the main installed
trade lane and removes `legal_tradelane_animation` only from `trade_lane_ring_main`.
The initial asset uses a six-second, one-turn motion sampled at 30 Hz (181 keys),
with smooth acceleration/deceleration. These are asset-generation defaults, not
runtime constants. Left maps to `tlr2_lod1`, right to `tlr1_lod1`, verified against
the model's lane hardpoints. Existing geometry, joints, LODs and other scripts are
preserved. `tools/tradelane/check.py` checks asset preservation, motion and runtime
playback lifecycle; `install.ps1` requires a closed game and verifies hashes/backups.

## `[Asteroid]`, `[AsteroidMine]`, `[DynamicAsteroid]`  ([common_archetype_misc.cpp:39](../../src/Common/common_archetype_misc.cpp#L39))

`[Asteroid]` and `[AsteroidMine]` are the same record type (object type preset to `ASTEROID`); `[DynamicAsteroid]` accepts only the `Root` keys. All three are loaded by `LoadAsteroids` from `solar\asteroidarch.ini`.

| Key | Type | Default | Meaning | Source |
|---|---|---|---|---|
| `inherit` | nickname | - | Loader-level; copies `Root` fields plus `detect_radius`, `explosion_offset`, `recharge_time`; a missing donor logs the 'inherit' warning. Not available in `[DynamicAsteroid]`. | [loader L408](../../src/Common/common_archetypeloader.cpp#L408) |
| `detect_radius` | float | 25.0 | Radius at which a mine detects ships. | [L45](../../src/Common/common_archetype_misc.cpp#L45) |
| `explosion_offset` | float | 0.0 | Offset of the explosion centre. | [L51](../../src/Common/common_archetype_misc.cpp#L51) |
| `recharge_time` | float | 1000.0 | Time before a mine can fire again. | [L57](../../src/Common/common_archetype_misc.cpp#L57) |

## `[CollisionGroup]` (after `[Ship]` or `[Solar]`)

Describes one destructible/detachable part of the nearest preceding record ([common_archetype_ships.cpp:495](../../src/Common/common_archetype_ships.cpp#L495)). Groups get consecutive 16-bit ids per record. A `[CollisionGroup]` with no preceding record is skipped silently in `ships`; in `solar` it logs "Attempt to load a solar group into a solar that wasn't loaded." In `ships` the 16-bit id counter running out logs "Exceeds maximum collision group". Unknown keys inside the section are ignored.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `obj` | cstr (whole value) | empty | Name of the model part (CMP object name). | [L502](../../src/Common/common_archetype_ships.cpp#L502) |
| `type` | group-type name (whole value) | 1 | Case-insensitive; names and values: `Fin` 0x2, `Top_Fin` 0x4, `Port_Fin` 0x8, `Starboard_Fin` 0x10, `Port_Wing` 0x20, `Starboard_Wing` 0x40, `Middle_Wing` 0x80, `Engine` 0x100, `Port_Engine` 0x200, `Middle_Engine` 0x400, `Starboard_Engine` 0x800, `Top_Engine` 0x1000, `Bottom_Engine` 0x2000, `Spoiler` 0x4000, `Tail` 0x8000, `Port_Side_Panel` 0x10000, `Starboard_Side_Panel` 0x20000, `Port_Arm` 0x40000, `Starboard_Arm` 0x80000. Any other value gives 1 without a message. | [L506](../../src/Common/common_archetype_ships.cpp#L506) |
| `hit_pts` | int | 0 | Hit points of the part. | [L512](../../src/Common/common_archetype_ships.cpp#L512) |
| `separable` | none | false | Presence alone makes the part separable; any value is ignored. | [L516](../../src/Common/common_archetype_ships.cpp#L516) |
| `destroy_parent` | bool, optional | false | `destroy_parent` with no value means true; with a value it is parsed as a bool. | [L520](../../src/Common/common_archetype_ships.cpp#L520) |
| `root_health_proxy` | bool | false | Damage to the part is applied to the root. | [L527](../../src/Common/common_archetype_ships.cpp#L527) |
| `vulnerable` | bool | false | Port extension: marks this group orange in the HUD wireframe even at full health. Real heavy damage still uses the red/critical colours. Does not deal damage, change damage multipliers or activate fuses. | `ReadCollisionGroup`, `HudTargetBase::ColourGroupParts` |
| `parent_impulse` | float | 0.0 | Impulse on the parent when the part breaks off. | [L531](../../src/Common/common_archetype_ships.cpp#L531) |
| `child_impulse` | float | 0.0 | Impulse on the detached part. | [L535](../../src/Common/common_archetype_ships.cpp#L535) |
| `mass` | float | 1.0 | Mass of the part. | [L539](../../src/Common/common_archetype_ships.cpp#L539) |
| `rotation_inertia` | float x3 | none | Inertia X, Y, Z. | [L543](../../src/Common/common_archetype_ships.cpp#L543) |
| `separation_explosion` | id (whole value) | 0 | Explosion when the part separates. | [L550](../../src/Common/common_archetype_ships.cpp#L550) |
| `debris_type` | id (whole value) | 0 | Debris archetype of the part. | [L554](../../src/Common/common_archetype_ships.cpp#L554) |
| `dmg_hp` | cstr (whole value) | - | Hardpoint damaged together with this part. **Pairs with `dmg_obj`** (see below). | [L196](../../src/Common/common_archetype_ships.cpp#L196) |
| `dmg_obj` | id (whole value) | - | Object (equipment archetype) damaged together with this part. | [L202](../../src/Common/common_archetype_ships.cpp#L202) |
| `group_dmg_hp` | cstr (whole value) | - | As `dmg_hp`, applied to the whole group. | [L208](../../src/Common/common_archetype_ships.cpp#L208) |
| `group_dmg_obj` | id (whole value) | - | As `dmg_obj`, for the group list. | [L214](../../src/Common/common_archetype_ships.cpp#L214) |
| `explosion_resistance` | float | 1.0 | Scale of explosion damage. | [L561](../../src/Common/common_archetype_ships.cpp#L561) |
| `fuse` | `[0]` fuse id, `[1]` float, `[2]` float | none | Group damage fuse, repeated keys append; same parameter semantics as the object-level `fuse` above. | [L565](../../src/Common/common_archetype_ships.cpp#L565) |
| `linked_equip` | `[0]` equipment-kind name, `[1]` float | kind 0, health 0.0 | Ties the part's health to an equipment class. `[0]` (case-insensitive): `scanner` 0x80000, `engine` 0x20000, `weapon` 0x80, `shield` 0x100, `thruster` 0x400, `power` 0x40000, `light` 0x1, `tractor` 0x100000, `attached_fx` 0x2, `internal_fx` 0x400000, `tradelane` 0x800000, `repairdroid` 0x200000, `cloaking_device` 0x1000, `armor` 0x1000000; any other value gives 0. | [L574](../../src/Common/common_archetype_ships.cpp#L574) |

**`dmg_hp` / `dmg_obj` pairing.** The two key pairs fill a list of (hardpoint, object) entries in order: a `dmg_hp` fills the hardpoint of the last entry if that entry has none yet, otherwise it starts a new entry; `dmg_obj` fills the object of the last entry if it has none, otherwise starts a new one. At the end of the section every entry that lacks the hardpoint or the object is "unmatched": a warning "Unmatched dmg_obj or dmg_hp values for Group[%s]. No damage objects will be attached." (resp. `group_dmg_*`) is logged and the **whole list is discarded**. The same applies independently to the `group_dmg_*` list.

## System-file `[Object]` sections through the solar archetypes (`CSolar::ReadObj`)

Every `[Object]` section of a system file (e.g. `universe\systems\<sys>\<sys>.ini`) is read by `CSolar::ReadObj` ([common_csolar.cpp:692](../../src/Common/common_csolar.cpp#L692)) when the solar is created, on the server in multiplayer ([server_classes.cpp:6932](../../src/Server/server_classes.cpp#L6947)) and by the client. The system file contains many more sections and keys that belong to other readers ([systems-and-bases.md](systems-and-bases.md), [world-data.md](world-data.md)); only the keys below are consumed here, other keys of the section are skipped.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `archetype` | solar nickname | none (object not created) | `[Solar]` archetype. Unknown name logs "Archetype \"%s\" not found while reading Solar object" and **stops reading the section**; the solar is not created. | [L710](../../src/Common/common_csolar.cpp#L710) |
| `nickname` | id (whole value) | none | Object nickname and object id. Missing nickname: error "Solar with Archetype(%s) missing nickname" and the object is not created. | [L734](../../src/Common/common_csolar.cpp#L734) |
| `pos` | float x3 | 0, 0, 0 | World position. | [L740](../../src/Common/common_csolar.cpp#L740) |
| `rotate` | float x3, degrees | identity | Euler angles (`EulerMatrix`, degrees). | [L746](../../src/Common/common_csolar.cpp#L746) |
| `spin` | float x3 | 0, 0, 0 | Angular velocity. | [L754](../../src/Common/common_csolar.cpp#L754) |
| `visit` | int (cast to 8 bits) | 0 | Visit flags of the object. | [L760](../../src/Common/common_csolar.cpp#L760) |
| `parent` | id (whole value) | 0 | Nickname of the parent object. | [L764](../../src/Common/common_csolar.cpp#L764) |
| `goto` | `[0]` system nickname, `[1]` gate nickname | none | Jump gate/hole destination: system id and the nickname of the target gate. A system that does not resolve logs "Jumpgate has invalid destination". Further parameters (tunnel effect) are not read here. | [L768](../../src/Common/common_csolar.cpp#L768) |
| `base` | base nickname (whole value) | none | Base this object leads to; unknown base logs "Could not find base %s for solar object." | [L780](../../src/Common/common_csolar.cpp#L780) |
| `dock_with` | base nickname (whole value) | none | Base the object docks with; unknown base logs an error. | [L791](../../src/Common/common_csolar.cpp#L791) |
| `loadout` | id (whole value) | the archetype's `loadout` | `[Loadout]` of the instance. A non-empty loadout that does not exist logs "Unable to find [Loadout] %s" (not fatal). | [L802](../../src/Common/common_csolar.cpp#L802) |
| `atmosphere_range` | float | 0.0 | Atmosphere radius; if smaller than the archetype's `solar_radius` an error is logged. | [L806](../../src/Common/common_csolar.cpp#L806) |
| `anim` | cstr (whole value) | none | Continuously played animation; repeated keys append. | [L812](../../src/Common/common_csolar.cpp#L812) |
| `prev_ring`, `next_ring` | id (whole value) | 0 | Neighbouring trade-lane rings. | [L820](../../src/Common/common_csolar.cpp#L820), [L824](../../src/Common/common_csolar.cpp#L824) |
| `tradelane_space_name` | int | 0 | String id of the trade-lane's name. | [L828](../../src/Common/common_csolar.cpp#L828) |
| `destructible` | bool | the archetype's | Overrides the archetype flag. | [L832](../../src/Common/common_csolar.cpp#L832) |
| `space_costume` | `[0]` head, `[1]` body, `[2..n]` accessories | none | Names of body parts from `bodyparts.ini`/`costumes.ini`. Unknown head/body logs "space costume head/body %s does not exist"; a missing body logs "space costume malformed". An unknown accessory name is not checked (retail dereferences null there). | [L837](../../src/Common/common_csolar.cpp#L837) |
| `voice` | id (whole value) | 0 | Voice id. | [L893](../../src/Common/common_csolar.cpp#L893) |
| `comm_appr` | costume nickname (whole value) | none | Whole costume looked up by name. | [L898](../../src/Common/common_csolar.cpp#L898) |

After the loop the object is rejected (error logged) when the archetype is missing, the nickname is empty, or the reputation entry for the nickname does not exist (see next section).

### Object reputation pass (`LoadObjectVibesFromSystemIni`)

Before objects are created, Common walks the `[Object]` sections of the system file once to create a reputation entry for each ([common_cobjdb.cpp:54](../../src/Common/common_cobjdb.cpp#L54), called from [common_universe.cpp:822](../../src/Common/common_universe.cpp#L822)). A section stops being read as soon as name, nickname and group are all known.

| Key | Type | Default | Meaning | Source |
|---|---|---|---|---|
| `nickname` | id (whole value) | none (section ignored) | Object nickname = reputation handle. | [L76](../../src/Common/common_cobjdb.cpp#L76) |
| `ids_name` | int | 0 | Display-name string id. | [L80](../../src/Common/common_cobjdb.cpp#L80) |
| `infocard_ids` or `ids_info` | int | 0 | Infocard string id (both spellings are accepted). | [L84](../../src/Common/common_cobjdb.cpp#L84) |
| `group` | str (whole value, truncated to 15 chars) | empty | Reputation (faction) group of the object, e.g. a group nickname defined in `initialworld.ini` ([saves-and-initial-world.md](saves-and-initial-world.md)). | [L88](../../src/Common/common_cobjdb.cpp#L88) |
| `archetype` | solar nickname | none | Looks up the solar archetype to take the rank (`toughness`) from. | [L107](../../src/Common/common_cobjdb.cpp#L107) |

## Asteroid field files (`CAsteroidField::load`)

A field file is named by the `file` key of an `[Asteroids]` section in the system file, together with a `zone` key naming the zone it fills. The Common loader `CAsteroidField::load` ([common_casteroidfield.cpp:74](../../src/Common/common_casteroidfield.cpp#L74)) is run by the server on the whole file ([server.md](server.md#asteroid-fields-on-the-server)) and by the client; the other sections of the file (`[Band]`, `[AsteroidBillboards]`, `[DynamicAsteroids]`, `[TexturePanels]`, `[properties]`) are client/visual and are documented in [world-data.md](world-data.md). Unrecognised sections are skipped.

### `[ServerDynamicAsteroids]` (port extension)

Opt-in moving rocks owned by the server. Define a `[Solar]` archetype in a loaded
solar archetype file with `type = SERVER_ASTEROID`, a mesh and matching `.sur`,
`mass`, `hit_pts`, `destructible = true`, material libraries and `explosion_arch`.
`SERVER_ASTEROID` objects are always non-targetable: they do not enter scanner
target lists and cannot be selected by mouse or target cycling. Keep
`type = SERVER_ASTEROID` so server physics and replication remain active.
Then reference it from the asteroid field file:

```ini
[ServerDynamicAsteroids]
asteroid = srv_ast_tau29_normal_a
spawn_mode = forward
count = 60
placement_radius = 3000
placement_offset = 2550
despawn_radius = 4500
max_velocity = 20
max_angular_velocity = 0.3
seed = 801
```

The system's existing `[Asteroids] file/zone` selects the field. The Sig8 preset
uses `spawn_mode = forward`: new rocks form only in the outer 15% of
`placement_radius`, with `placement_offset` plus rock size as an additional
minimum distance. A moving ship receives new rocks ahead of its velocity;
the camera is never consulted. Existing rocks keep their world positions and
motion. Creation is spread across updates (at most four new/restored objects
per 0.1 s across forward fields). Client instances fade in over 0.75 s using
material opacity, without changing gameplay cloak, collisions or network state.
The fade belongs to the object lifetime and is unaffected by camera changes.
After initial filling, new placement is
triggered by travelling 5% of the placement radius (minimum 100 m), not by
standing still while rocks drift away. In Sig8 this gives a 3 km formation
radius and a 4.5 km suspension radius. The preset migration takes the former
far `despawn_radius` from the INI as the new placement radius, preserving that
distance on subsequent runs. The target is 180 across this larger neighbourhood,
not 180 within 1 km. Multiplayer interest distance covers the suspension radius
so the native 2.5 km unowned-object cutoff does not delay distant creation.

With
`spawn_mode = player`, the server maintains a population within `placement_radius`
of the **ships**, using server positions rather than cameras. Overlapping player
neighbourhoods count the same rocks; separated players receive their own nearby
population. Placement stays inside the field, outside its `[Exclusion Zones]`,
outside physical objects and at least `placement_offset` plus the rock radius
from every player's ship. The Sig8 ruins' central 3000 m exclusion stays clear at
spawn. Rocks can subsequently drift into exclusions or outside the field.

In legacy `player` mode, every half-second the server can create/restore up to 24 rocks per system, up to
1024 active generated rocks (including any fixed-mode population). Rocks beyond
`despawn_radius` of **all** players are suspended in memory with their position,
orientation, velocity and remaining hull. Their distant simulation pauses; returning
restores them with a fresh network ID. Dead rocks remain dead and count toward the
local population, so shooting a rock does not immediately spawn its replacement.
Each section retains at most 8192 generated/dead records until system unload.
At capacity or near obstructions/exclusions, the visible population can be lower
than the target. Camera changes never create, remove or reposition these objects.

Omitting `spawn_mode` (or using `field`) retains the original finite mode: generate
`count` objects once around the zone centre when the system loads, without streaming.

| Key | Default | Meaning / limits |
|---|---|---|
| `asteroid` | required | Nickname of a **Solar** with `type = SERVER_ASTEROID`. |
| `spawn_mode` | `field` | `forward` forms distant rocks as ships travel; `player` refills a ship-centred sphere; `field` selects a fixed population at system load. |
| `count` | 0 | 0–256 per section: target in each player's neighbourhood, or total in fixed mode. |
| `placement_radius` | 3000 | Placement/counting radius in metres, 10–100000. Fixed mode additionally limits it to the zone radius. |
| `placement_offset` | 200 | Minimum spawning distance from ships, plus rock radius; clamped to 0–70% of placement radius in `player`, 0–90% in `forward`. Forward mode additionally excludes the inner 85%. |
| `despawn_radius` | twice placement radius (`player`), 1.5 times (`forward`) | Suspend only beyond this distance from every player; cannot be smaller than the mode's default, maximum 300000 m. |
| `max_velocity` | 10 | Maximum initial speed magnitude in m/s, 0–500. |
| `max_angular_velocity` | 0.1 | Maximum initial angular speed magnitude in radians/s, 0–10. |
| `seed` | 1 | Server random sequence, combined with zone ID. In player mode the result also depends on player movement/order. |

Multiple sections allow different meshes. All participants need matching updated
Common, Server and client binaries and matching archetype data. Existing object
creation, motion, hull-damage and destruction messages replicate these rocks;
explosion debris remains a local visual effect. Late joiners receive the surviving
objects at their current positions. Destruction lasts while the system is loaded;
unloading/reloading the system regenerates it. There is no save-file persistence.
This feature does not implement campaign co-op. Streamed server asteroids use
the field's existing `[LootableZone]` dynamic loot settings on actual destruction:
one server-side probability roll, authored container/commodity and quantity range,
at the rock's position. Named loot zones take precedence over the field fallback.
Suspension, unload and repeated death notifications never produce extra loot.

Player autopilot and NPC pathfinding use nearby physical rock sizes and velocities
to choose a detour and reduce approach speed. This supplements the existing
obstacle reactions; it is not a guarantee against collisions in a blocked corridor.

The old `[DynamicAsteroids]` type remains client-owned. In all five Sig8 test fields,
the three existing sections have `count = 0` so they retain mesh/material inputs
for the distant decorative `[FarRocks]` renderer without spawning duplicate local
rocks. Each field's three new server sections each target 60 rocks within 3000 m
of ships. `[FarRocks]`, `[AsteroidBillboards]`, dust, bands and exclusions are
unchanged. The global creation budget and 1024 active-object limit apply across
all five fields together. `tools/physics/prepare_sig8_asteroids.py`
prepares this preset and a hash-checked installer; it does not itself modify the game.

`python -B tools/physics/install_world_asteroids.py` extends this to active ordinary-world
fields (136 fields, 451 population sections, 29 systems and 29 models in the current mod).
`--apply` installs the staged configuration, PythonLancer patch and Server.dll/PDB with
SHA256 checks, backup and rollback on failure. Five existing Sig8 presets are unchanged;
all other fields retain their authored counts and speeds, using the forward formation
at `max(3000, original placement_radius)` and suspension at 1.5 times that distance.
Client counts become zero; mesh/material inputs and every other field section remain.
The original 1024-object system limit and four-creations-per-tick forward budget still apply.

Scope follows active universe references and excludes special/story/dungeon resources,
including shared fields, `om11`, `tau44`, `m8_tau44`, `sphere*`, and StorySystem classes
under SYSTEMS_MOD (`co_cad`, `omicron2`). Mine/static Cube fields without dynamic
populations and distant decorative FarRocks remain unchanged. The generator embeds
the same transformation with a system/model allowlist and story guard, preserving
the Sig8 count of 60 per model on regeneration. New models require preparing a new rollout.
Tau29 is explicitly excluded: its four ordinary fields and ring use their original client
populations. `tools/physics/restore_tau29_asteroids.py --baseline <rollout-backup>` stages
their exact pre-rollout files and the generator scope change; `--apply` installs with
hash checks and a new backup. Other systems' fields and binaries are not part of that payload.

The server clones retain the source mesh, collision SUR, all material libraries,
explosion, mass and hull. The effectively indestructible `ast_co_cur_x2` hull is capped
at 2,000,000,000 to fit the signed network creation/restoration field. Solar rendering
uses the original materials and solar lighting; legacy per-field dynamic `color_shift`
is retained for the decorative renderer but is not applied to server solars.
`band_thickness` in streamed server sections preserves a slab along the zone's local Y
axis and starts rocks with in-plane velocity; subsequent physical collisions can move
them out of that slab. Tau29's ring retains its original client-side slab setting instead.

Validation: `tools/physics/check_world_asteroids.py` audits the staged real-world
conversion and generator output; `check_server_asteroid_fields.py` exercises production
streaming, tilted rings and server mining with controlled engine fixtures.

Implementation: [server_asteroid_fields.cpp](../../src/Server/server_asteroid_fields.cpp),
[common_asteroid_avoidance.cpp](../../src/Common/common_asteroid_avoidance.cpp).

### `[Cube]`

The solid asteroids that fill every grid cube of the field. Constructor presets for the snap rotations are `0, 90, 180, 270` degrees on each axis.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `xaxis_rotation`, `yaxis_rotation`, `zaxis_rotation` | four floats, degrees (`[0]..[3]`) | 0, 90, 180, 270 | The four rotation angles a cube may be snapped to about that axis. All four are read (missing ones read as 0). | [L99](../../src/Common/common_casteroidfield.cpp#L99), [L104](../../src/Common/common_casteroidfield.cpp#L104), [L109](../../src/Common/common_casteroidfield.cpp#L109) |
| `asteroid` | `[0]` asteroid nickname, `[1]` x, `[2]` y, `[3]` z, `[4]` angle X, `[5]` angle Y, `[6]` angle Z, optional `[7]` flag | none | One rock placed in every cube; repeated keys add rocks. `[0]` must be a loaded `[Asteroid]` archetype (a miss is logged by the database and then dereferenced, as in retail). `[1]`-`[3]` are fractions of half the cube size and are clamped to [-1, 1]. `[4]`-`[6]` are rotation angles in degrees; if any of the three is missing the error "invalid rotation specified for an asteroid" is logged and all three are 0. `[7]` is compared exactly (case-sensitive): `mine` makes the rock a mine, `instant_kill` makes it kill on contact; any other text means neither. | [L114](../../src/Common/common_casteroidfield.cpp#L114) |

### `[Exclusion Zones]`

Keys apply to the **most recent** `exclusion` line of the section; `exclude_billboards`, `billboard_count`, `exclude_dynamic_asteroids` and `empty_cube_frequency` before any `exclusion` have no zone to act on (retail does not check this).

| Key | Type | Default | Meaning | Source |
|---|---|---|---|---|
| `exclusion` | zone nickname (`str[0]`) | none | A zone of the same system that carves a hole in the field. A missing zone logs "AsteroidField linked to missing Exclusion Zone (%s)". | [L255](../../src/Common/common_casteroidfield.cpp#L255) |
| `exclude_billboards` | int (truncated float) | not set | A value greater than 0 excludes billboards in the zone. | [L278](../../src/Common/common_casteroidfield.cpp#L278) |
| `billboard_count` | int (truncated float) | not set | If greater than 0, billboard count inside the zone. | [L285](../../src/Common/common_casteroidfield.cpp#L285) |
| `exclude_dynamic_asteroids` | int (truncated float) | not set | If greater than 0 **and** the zone is a sphere or ellipsoid, dynamic asteroids are excluded in the zone. | [L293](../../src/Common/common_casteroidfield.cpp#L293) |
| `empty_cube_frequency` | float | not set | Share of empty cubes inside the zone; negative values are ignored. | [L307](../../src/Common/common_casteroidfield.cpp#L307) |

### `[LootableZone]`

Dynamic-loot description attached to a zone. Defaults of a fresh entry: loot counts 1..1, asteroid difficulty 100, dynamic difficulty 1, ids 0. The entry is used only if `dynamic_loot_container` or `dynamic_loot_commodity` was given; it is attached to the zone named by `zone` (and remembered in the field's loot-zone list), else to the field's own zone, else the error "loot zone information attached to asteroid field (%s) that has no zone" is logged. The keys `asteroid_loot_container`, `asteroid_loot_commodity`, `asteroid_loot_count` and `asteroid_loot_difficulty` are tested by the retail code but have no effect.

| Key | Type | Default | Meaning / allowed values | Source |
|---|---|---|---|---|
| `dynamic_loot_container` | id (`str[0]`) | 0 | Loot crate archetype. | [L352](../../src/Common/common_casteroidfield.cpp#L352) |
| `dynamic_loot_commodity` | id (`str[0]`) | 0 | Commodity archetype. | [L358](../../src/Common/common_casteroidfield.cpp#L358) |
| `zone` | zone nickname (`str[0]`) | field's own zone | Zone the entry belongs to; a later `zone` line replaces an earlier one (an unknown name gives none). | [L364](../../src/Common/common_casteroidfield.cpp#L364) |
| `dynamic_loot_count` | int `[0]` min, int `[1]` max | 1, 1 | Both raised to at least 1; if max < min then min is set to max. | [L370](../../src/Common/common_casteroidfield.cpp#L370) |
| `dynamic_loot_difficulty` | int | 1 | Clamped to 1..100. | [L385](../../src/Common/common_casteroidfield.cpp#L385) |
