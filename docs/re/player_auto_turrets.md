# Player auto-turrets under explicit orders

**English** · [Русский](../ru/re/player_auto_turrets.md)

Date: 2026-10-26. Historical static inspection of the working sources over `af086d9`; classes, modes and settings below were proposals at that time. The SP implementation was added on 2026-10-27: see [current behavior, controls and validation](../player_auto_turrets.md). Flight validation remains outstanding.

User goal: the player flies the ship while assigned turrets find suitable targets, aim and fire independently. Neither autopilot nor turret camera is required. **Automation only starts after an explicit player order through a dedicated mode.** An enemy appearing, incoming damage or switching autopilot does not authorise automatic energy expenditure.

Priority clarification: deliver a self-contained turret system first. Perks, skills and temporary boosters are outside the initial scope and are not prerequisites for enabling turrets.

Previously saved research: [new mission types and StoryLauncher](content_open_world_missions.md), [careers and faction experience](content_progression.md), [cargo contracts, scanning and smuggling](content_cargo_contracts.md). These are separate projects, not mandatory turret dependencies.

## Feasibility

Much of the mechanism already exists for NPCs: per-turret target selection, pointing constraints, lead calculation, line-of-fire checks and firing through ordinary launchers. The normal cycle explicitly excludes the player. Meanwhile manual control continually sets the aim point for every gun, so removing the `is_player()` exclusion alone causes conflicting control.

Use a dedicated player weapon controller that reuses verified Common mechanisms and the ordinary firing path, but owns explicit orders, target restrictions and energy budgeting. It does not steer the ship or activate an NPC pilot for the player.

## Verified mechanisms

| Mechanism | Sources | Consequence |
|---|---|---|
| Turret classification | `Gun::read`, `Gun::get_hp_type` in [common_archetype_weapons.cpp](../../src/Common/common_archetype_weapons.cpp) | `auto_turret` sets `bAutoTurret` and affects attachment type. It is not a player fire order |
| Player exclusion | `IBehaviorManager::UpdateBehaviorTick` in [common_behaviormanager.cpp](../../src/Common/common_behaviormanager.cpp) | Calls `ScanAutoTurretTargets` and `FireAutoTurrets` only for `!is_player()` |
| Target selection | `ScanAutoTurretTargets` in [common_sysmgr_gungroups.cpp](../../src/Common/common_sysmgr_gungroups.cpp) | Chooses the nearest eligible hostile per auto-turret using attack orders, distance and `can_point_at`; assigns each weapon separately |
| AI firing | `FireAutoTurrets` in [common_aifirecontrol.cpp](../../src/Common/common_aifirecontrol.cpp) | Checks timing, `AttackState`, target, firing eligibility and alignment; calculates lead and invokes `slot_34` for a specific weapon |
| AI cadence | `UpdateTimers`, `auto_turret_*` parameters in [common_sysmgr_gungroups.cpp](../../src/Common/common_sysmgr_gungroups.cpp), [PilotPersonalities.cpp](../../src/Content/PilotPersonalities.cpp) | AI has burst/interval policies; do not silently inherit them as player settings |
| Gun pointing | `CEGun::SetTarget`, `SetTargetPoint`, `Update`, `CanPointAt` in [common_cegun.cpp](../../src/Common/common_cegun.cpp) | Target watchers, joint limits and turn rates exist; a fresh manual aim point takes priority over object tracking |
| Manual aim | [space_camera_game.cpp](../../src/freelancer/Client/space_camera_game.cpp) | Every frame calls `SetTargetPoint(Aim)` on all guns; firing has explicit-list and no-list paths |
| Player target selection | `CliShipHandleEquipUpdate` in [cli_projectile_fx.cpp](../../src/freelancer/Client/cli_projectile_fx.cpp) | Some commands assign a target to every gun; ownership must be separated here too |
| Shots and presentation | `CliShipFireWeapons` in that file; [client_iclient_space.cpp](../../src/freelancer/Client/client_iclient_space.cpp) | Existing effects, requests and remote playback should be reused without creating duplicate projectiles |
| Resources and readiness | `CanFire`, `GetPowerDrawPerFire`, `ConsumeFireResources` in [common_celauncher.cpp](../../src/Common/common_celauncher.cpp) | Refire, energy, ammo and some restrictions are checked; cost includes barrel count |
| Server handling | `IServerImpl::FireWeapon` in [IServerImpl.cpp](../../src/Server/IServerImpl.cpp), `EqObj::slot_34` in [server_gameobject.cpp](../../src/Server/server_gameobject.cpp) | Client shots and server shots follow different paths; client requests use `fire_unchecked`. Sending a packet is not full server validation |

`ScanAutoTurretTargets` internally reads a player's target, but its normal caller excludes players. That internal branch does not establish a working player feature.

## Player orders

Start with three modes for the assigned turret group:

| Mode | Behaviour |
|---|---|
| **Manual** | The controller neither selects targets nor fires; normal manual control owns the weapons |
| **Attack designated target** | An explicit order fixes a target independent of the player's crosshair. Target destruction/loss does not authorise a replacement |
| **Engage hostiles** | An explicit standing order permits eligible enemy selection; each turret chooses within its own arc |

A separate **Cease automatic fire** command immediately cancels the order, clears automatic assignments and returns the group to manual control. Manual guns remain available through player input. Opening the scanner, selecting a map object or changing highlighted targets is not an attack order.

Designated-target orders refer to a specific object. Selecting another ship for scanning does not redirect turret fire; a new order is required. Initially exclude neutral ships from automatic attacks. Deliberate attacks on neutrals would need a separate explicit permission if later required.

Orders remain active without holding a button. Taking damage does not enable even a defensive mode; such a mode could only be added as another explicitly chosen order. There is no preventive energy expenditure.

### Orders versus temporary suspension

Store `order` separately from `suspension_reason`. A standing engage-hostiles order may pause for an energy reserve or lack of targets, then resume when conditions permit. Cancelling removes the order entirely, so recharging no longer resumes fire.

Initial policy: clear orders after docking, death, changing ships, loading saves and reconnecting. Save group/reserve preferences, not permission to fire. For the first prototype, clear targets and cancel orders on system jumps too; persistence of engage-hostiles across systems can become an explicit later setting.

Autopilot neither enables nor disables the order by itself. Cruise, trade lanes, docking, cutscenes and weapon-control exclusions suspend execution. Turrets must not disengage cruise to attack. Camera choice affects the view, not firing permission.

## Energy and ammunition

An optional initial reserve could be **35% weapon energy**, resuming at **45%**. Values are illustrative; separate thresholds prevent repeated toggling at one boundary.

Before each automatic shot:

```text
available budget = current energy - reserve - already scheduled spending
if full shot cost exceeds available budget: do not fire
otherwise reserve the cost, then invoke ordinary firing
```

Do not check the percentage once and allow every turret to fire: combined costs can cross the reserve. Use `GetPowerDrawPerFire`, including multiple barrels. Release a reservation if firing fails; only the ordinary launcher deducts actual energy.

Manual fire has priority. Account for manual requests in the step before allocating the remaining automatic budget. The reserve limits automatic consumption; players can still spend it manually. It is not a separate battery or a guarantee that every player action preserves that percentage.

Ammo-based turrets can later support an ammunition reserve. Exclude missiles, mines, countermeasures and cruise disruptors from the initial automatic group. Resource shortage shows a suspension reason instead of silently cancelling the order.

## Targeting and firing

Consider only detected objects available to the pilot in the same system. A live server object is not necessarily visible through interference/cloaking. Initially target ships only; exclude stations, neutral transports, loot and mission-protected actors. Missions can impose additional rules such as preserving a transport alive.

Check each turret's physical arc, its own projectile range and functionality. The NPC path uses grouped `GunRange`; mixed player loadouts require per-weapon range checks. Lead depends on target motion and projectile velocity. The turret must rotate into alignment rather than bypassing `turn_rate` through instantaneous orientation changes.

Engage-hostiles priorities favour eligible threats to the player and reachable targets. Retain a viable target unless a substantially better candidate justifies switching; do not jitter between almost equally distant ships every frame. Different turrets may attack different enemies, and a forward target outside a rear turret's arc must not block the whole ship.

Check the firing line before shooting. Existing `IsLineOfFireBlocked` is useful but not a complete guarantee: it uses caching, a bounded ray and object-class filters. Validate obstruction by the own hull, stations, friendlies and geometry. Projectiles travel over time; one raycast cannot guarantee no later friendly crossing. Conservative shot rejection reduces that risk.

Preserve refire, ammo, power, damage, disabled-weapon and flight restrictions. `CanFire` does not express all product-level restrictions, so the controller also checks player states. Automation does not increase base damage or rate of fire.

## Architecture and manual-input arbitration

Proposed components, not existing classes:

| Component | Responsibility |
|---|---|
| `FPlayerTurretController` | Explicit order, assigned weapons, targeting loop and suspension |
| `FWeaponControlArbiter` | Per-weapon ownership of aiming/firing: manual or automatic |
| `FTurretTargetPolicy` | Eligibility, hostility, visibility, priority and target retention |
| `FWeaponEnergyBudget` | Resource allocation with manual priority and a reserve |
| Weapon adapter | Existing gun/launcher aiming and client/server firing paths |

Do not store the mode in `Gun::bAutoTurret`: it is a shared archetype property already used for mounting/presentation. Use per-ship/group settings. Rebind mounts/equipment after loadout changes; runtime equip IDs are not permanent identities. Only explicitly supported turret guns qualify, not every weapon with a suggestive hardpoint name.

Three mandatory manual-path changes:

1. Exclude automatically owned weapons from cursor `SetTargetPoint`. It resets `TargetPointAge`, otherwise defeating object tracking.
2. Exclude them from commands that retarget all guns when the player selects an object.
3. Exclude them from manual fire-all, explicit lists, initial trigger frames and group commands. A manual takeover first transfers ownership explicitly.

Filtering needs a request origin: `Manual`, `Automatic`, or `NetworkReplay`. Do not globally remove automatic turrets from `CliShipFireWeapons`, which also serves their shots and remote playback. Automatic requests always contain a nonempty explicit weapon list: client `count == 0` means all active launchers, not no shots. The explicit-list path does not itself apply the general `IsActive` check, so the controller must enforce it.

Suggested step order: manual commands/cancellation → weapon ownership → target evaluation → aiming → shot eligibility/budget → normal fire. Animate rotation every frame; run full target selection less often, for example 5–10 times per second as an initial setting. Revalidate order, target and budget before every shot. Avoid rescanning every object for every turret on every frame.

## SP and MP

**Start with local control in SP.** Update the controller with local ship/weapons, not only turret camera. Fire selected equipment through normal `CliShipFireWeapons`. Keep the existing NPC cycle disabled for the player to avoid two decision sources. Reuse low-level mechanisms without running the whole NPC flight controller.

Existing shot transport helps MP but does not establish feature readiness. `EqObj::slot_34` uses `fire_unchecked` for a client source, so arrival at Server does not make the design server-validated.

For full MP, prefer the server as the single authority for automatic decisions. The client sends orders, weapon assignment and settings; the server validates and fires. Add mode acknowledgement, aim/energy synchronization and owner playback without resending the shot. MP transforms aim relative to the lock target: one `XFireWeaponInfo` has one aim point. Fire at distinct targets separately or introduce a suitable new batch format; do not combine unrelated targets under one point.

Never simultaneously run client automation, server AI firing and network playback as local firing: that creates duplicate projectiles/resource spending. Compatibility with unextended clients/servers needs a separate protocol assessment.

## UI and persistence

Minimum UI: assign turret group, order designated attack, toggle engage-hostiles, and a conspicuous cancel command. Show the current order, active turret count and reasons such as no target, outside arc, energy reserve, blocked line or disabled weapon.

A single explicit input must stop automation even with another HUD panel open. Register remappable commands after checking existing bindings; do not invent occupied keys. Distinguish enabled equipment from permission to fire automatically.

Save group preferences, permitted target classes and reserve in versioned state. Do not restore runtime pointers, targets or a live firing order automatically in the first version. Current energy and transient reservations remain simulation state, not separate progression resources.

## Milestones and acceptance

| Stage | Deliverable |
|---|---|
| 1 | One player turret tracks/fires at one ordered hostile while the player pilots; cancellation stops firing |
| 2 | Manual paths are separated; forward guns and an automatic turret can fire toward different points |
| 3 | Multiple turrets choose within their arcs; reserve and suspension reasons work |
| 4 | HUD/settings, state transitions, preference persistence and gameplay restrictions |
| 5 | Authoritative MP, capability agreement and no duplicate shots |

The SP prototype is moderate in scope because much weapon behaviour exists. Input/fire ownership is the main integration task. Reliable multi-turret MP is substantially broader than changing one conditional.

Future checks: incoming attack without an order causes no automatic fire; order/cancel in one frame; changing selection does not change the order; designated target destruction; targets ahead/behind; mixed arcs/ranges; friendly obstruction; energy just above salvo cost; concurrent manual fire; disabled/destroyed turret; depleted ammunition; first fire-all frame; cruise/trade lane/docking/cutscene; cockpit/turret cameras; loading/ship replacement; multiple clients and no double spending.

Follow [CONTRIBUTING](../../CONTRIBUTING.md): proposed `FREELANCER_PLAYER_AUTO_TURRETS` port feature, disabled by default with the ordinary path intact. The symbol is not added. This document preserves the research and explicit-order requirement; no gameplay code changed.

## Perks and boosters

Keep an effective-parameter calculation over base values with neutral default multipliers; never mutate a shared weapon archetype to buff one pilot. The subsequent [perks and boosters research](perks_and_boosters.md) covers turret efficiency, temporary effects, instant resource actions, critical hits and cooling. Baseline auto-turrets remain independent of progression.

That design separates full afterburner restoration, thrust increase, faster recharge and reduced drain. None of these effects issues a turret fire order. The effect and heat runtimes are proposed, not implemented.
