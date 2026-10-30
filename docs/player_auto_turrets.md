# Player auto turrets

**English** · [Русский](ru/player_auto_turrets.md)

Implemented on 2026-10-27 for single player. The player flies normally; selected turret guns aim and fire through the existing client weapon path after an explicit order. This is separate from the native turret camera and from NPC automatic turrets.

## Enabling and controls

Build Common and freelancer with `/p:FreelancerPlayerAutoTurrets=1`. The default build switch remains off. In `port.ini` beside the executable:

```ini
[AutoTurrets]
enabled = 1
reserve_percent = 35
```

Restart the game after changing `port.ini`. The reserve in the current save overrides the `port.ini` default. See the [configuration reference](ini/player-auto-turrets.md).

Open **Options > Miscellaneous** to change the global auto-turret checkbox and energy reserve (left/right arrows, 0..90 percent in steps of 5). The native table also contains radar auto-show, automatic opening of enemy/ship status panels, and the original Miscellaneous preferences. Apply commits HUD changes to the current save state; Cancel discards them. HUD settings are available after loading a game.

The global switch overrides automatic firing without clearing individual gun selections or changing their activation. Small buttons beside the weapon rows select which eligible guns belong to automatic control, including while the global switch is off. The large master icon has been removed from HUD_Status. Configuration is retained when switching the master off and back on.

Automatic targeting selects detected hostile ships independently for each turret, subject to its arc and projectile interception limits. Losing focus suspends fire and clears current attacks; returning focus permits fresh acquisition when the saved master setting is enabled. Native `USER_AUTO_TURRET` retains its camera function.

The master setting and energy reserve are stored in the native save `interface` word. Individual hardpoint selections remain in `auto_turrets.ini` by character and hull. Loading another save restores that save's master and reserve. Legacy saves without a master value use the previous INI enabled preference; without a reserve value they use `port.ini`.

## Beta icon

The beta asset is not committed. To prepare a private copy from an existing installation:

```powershell
python tools/player_auto_turrets/stage_beta_icon.py 'D:/games/Freelancer Beta/DATA/INTERFACE/HUD/HUD_autoturreton.3db'
```

Output: `src/obj/player_auto_turrets/stage/DATA/INTERFACE/HUD/HUD_player_auto_turret.3db`, with a SHA-256 manifest alongside it. Mesh, material and texture names and their references are remapped to avoid global resource collisions. The script only writes under this workspace's `src/obj`; it does not install anything. The destination in a game data directory is `INTERFACE/HUD/HUD_player_auto_turret.3db`.

The staged icon's material names retain the `UI_` prefix for UI colouring. Per-weapon controls belong to HUD_Status. The former HUD configurator background and maneuver-bar gear are no longer used; preferences use the game's existing button, checkbox and arrow assets. In-game visual verification remains necessary after UI layout changes.

## Firing and ownership

`player_auto_turrets.cpp` owns port-only state outside the retail ship/equipment layouts. Equipment is resolved by ID and identity through the live ship manager. The player and assigned target use native watchers. Newly discovered eligible guns restore their saved hardpoint selection.

`UpdateSpaceState` reconciles ownership before simulation and ticks automatic firing after the camera's manual-fire update. Each shot uses `CliShipFireAutomatic` → the same internal implementation as `CliShipFireWeapons` → launcher `TryFire` → the normal local-server fire message. Resource consumption, projectile creation, damage-per-fire plugins and sounds remain in that path. The adapter reports actual `TryFire` success; neither the legacy constant return value nor a changed refire timer is treated as proof of firing.

Manual cursor aim, manual per-gun target changes and all manual fire variants exclude owned turrets. The native zero-ID-count meaning, “all active launchers”, is preserved: filtering happens inside both native loops, so an empty automatic assignment can never accidentally become an all-weapons fire request. Network replay and NPC fire are not filtered by the player's assignment.

Weapon groups retain a separate desired manual-active state for assigned turrets. Switching a group does not turn automatic guns on/off or redirect their aim. Removing a gun from automatic control restores that manual state; an individual OFF wins. The global master switch preserves ownership and activation while blocking automatic shots. Individual activation changes update the desired state. Saving a weapon group records the manual state rather than the automatic assignment.

The controller accepts only functioning, connected guns identified by `auto_turret` or explicit native turret hardpoint classes, with valid barrels, unguided ammunition-free projectiles and finite positive muzzle speed/lifetime. `force_gun_ori`, missiles, mines and countermeasures are excluded. It requires a functioning scanner, a targetable live hostile ship in the active physics system, a valid intercept within projectile lifetime, a mechanically reachable point and actual barrel alignment. Joint slew remains the native gun/animation update; no instant rotations or shared archetype edits are used.

Cruise, trade lanes, docking, letterboxing, modal NN screens, weapon-control exclusion and cloaking suspend automatic fire. Before each ready shot every bound barrel is ray-tested to the intercept. Other physical objects, including the shooter's hull, block fire; the shooter's shield is excluded from this obstruction check. A saturated hit buffer blocks the shot. This checks current obstruction, not the future path of a friendly ship.

The energy check includes the **entire volley**, using `GetPowerDrawPerFire()`, after manual weapons have spent their energy. A shot must leave the configured percentage of maximum power. After an energy stop the controller waits until reserve + 10 percentage points is reached, then reevaluates cost. A rotating starting turret prevents a fixed traversal order from permanently favoring the first gun. Invalid capacity/cost values fail closed.

## Scope and verification

Implemented scope is **SP energy turrets against ships**. MP server ownership/protocol, ammunition budgets, solar targets, missile interception, threat-based prioritization, mission veto callbacks, perks, boosters and overheating remain separate work. The retained [implementation plan](re/player_auto_turrets_implementation.md) describes further intended work; this page describes the implemented behavior and actual API/configuration.

Validation performed:

- Release client/Common with the feature enabled; separate Release client build with the feature disabled.
- Enabled/disabled client export-name comparison: identical sets of 70 exports in the current workspace.
- `tools/player_auto_turrets/check.ps1`: native Common intercept tests, full-volley reserve boundary, manual expenditure, hysteresis, malformed numeric inputs and a sweep of reserve/power combinations. The fixture also passes with `-ASan` against instrumented Common.
- Beta UTF staging, internal resource-reference remapping and leaf round-trip verification.
- Full DebugASan client/Common build. A duplicate ushort-vector instantiation in `dbg_options.cpp` was resolved by importing Common's existing explicit template declaration before use, following the existing projectile-FX pattern; no linker error suppression was used.

Live investigation on 2026-10-27 captured armed free fire with `NoTarget`, active guns, sufficient energy and elapsed refire delays. Code review found that hostility used the reverse relation from HUD enemy selection and excluded the exact -0.6 boundary. The controller now calls the same `GetAttitudeClass(player, contact)` helper as the HUD: the contact's attitude towards the player must be <= -0.6. Relations can be asymmetric. The screenshot also exposed an offscreen status caption; ON/OFF and status now sit above the panel options. The Release client was rebuilt and installed in FL_MOD with a backup; the native interception/energy fixture passed. Post-fix firing and the new caption position still require a flight check.

A follow-up live capture still reported `NoTarget`. It showed seven ships on the player scanner, all with the same `PhysicsSystemId` (2279025414) as the player, but a different `ObjectDb` pointer. The database-identity guard rejected every ship before testing hostility. It was replaced with an active physics-system ID check for both player and contact. The rebuilt Release EXE was installed with a backup; firing after this second fix remains to be confirmed in flight.

`tools/player_auto_turrets/inspect_live.py` reads controller state and gun timers without attaching a debugger, suspending threads or writing memory. It requires the matching local Release EXE/PDB, the process ID and runtime image base. Keep the game focused while capturing: focus loss cancels the order.

Before distribution, exercise simultaneous manual/automatic fire; every group and individual weapon toggle; blocked muzzle and friendly crossing; scanner loss and target destruction; reserve exhaustion/recovery; pause/STOP and focus loss; save/load, docking and system transitions; HUD collapse, scaling and different aspect ratios. The build and native fixtures do not substitute for those checks.
