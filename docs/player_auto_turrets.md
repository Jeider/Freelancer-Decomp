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

Restart the game after changing `port.ini`. The initial reserve is overridden by preferences previously saved for the character and hull. See the [configuration reference](ini/player-auto-turrets.md).

The current HUD's `Health` component places two buttons **below weapon groups**, at offsets `(0.255, -0.323)` and `(0.255, -0.351)` with the same attachment as the group buttons. They follow HUD visibility, expansion and movement.

1. The upper button starts the preferred order or immediately stops an existing order.
2. The lower button uses the inventory `equipmenticon.3db` gear and opens the panel at the upper right edge, beneath the NeuroNet toolbar. Choose selected-target or hostile-free-fire mode, set the energy floor, and include/exclude individual turrets. Six turret rows per page; an additional button pages larger loadouts. The panel shows an ON/OFF header; diagnostic status is hidden. Options and guns are clickable text rows without icons, hardpoint names or +/- markers. Selected modes and included guns are yellow; other rows are cyan. Hover uses the native weapon-list pulse, including the energy reserve row. Extra spacing separates the reserve from modes and guns. Its background is a privately named copy of the beta `player_inventory_center.cmp`, scaled to the panel; both main buttons remain beneath the weapon groups.
3. Changing the preferred mode or membership **cancels the order**. Press the upper button again to arm the turrets. An inactive weapon remains inactive; enable it through the ordinary weapon controls.

Selected-target mode captures the current **hostile ship instance**. Selecting something else later does not retarget the order. Losing scanner contact suspends fire; destruction of the captured instance cancels the order. Free fire selects detected hostile ships independently for each turret, subject to its arc and projectile interception limits. Valid targets are held for at least 0.75 seconds; subsequent replacement requires a target at least 20% closer. Search retries/reconsideration are limited to 5 Hz per turret, while an acquired target is revalidated each simulation tick.

Four commands are added to the ordinary key-binding screen; they have **no forced default bindings**:

| Nickname | Action |
|---|---|
| `USER_PLAYER_AUTO_TURRET` | Toggle the preferred order |
| `USER_PLAYER_AUTO_TURRET_TARGET` | Explicit order against the currently selected hostile ship |
| `USER_PLAYER_AUTO_TURRET_FREE` | Explicit free-fire order |
| `USER_PLAYER_AUTO_TURRET_STOP` | Revoke the order |

The bound keyboard STOP is checked before the normal pause/menu input-focus filter. Other commands cannot start fire through a modal input focus. Native `USER_AUTO_TURRET` retains its camera function. Loading, changing ships/systems, leaving space and losing application focus cancel the order. Returning focus never rearms it.

## Beta icon

The beta asset is not committed. To prepare a private copy from an existing installation:

```powershell
python tools/player_auto_turrets/stage_beta_icon.py 'D:/games/Freelancer Beta/DATA/INTERFACE/HUD/HUD_autoturreton.3db'
```

Output: `src/obj/player_auto_turrets/stage/DATA/INTERFACE/HUD/HUD_player_auto_turret.3db`, with a SHA-256 manifest alongside it. Mesh, material and texture names and their references are remapped to avoid global resource collisions. The script only writes under this workspace's `src/obj`; it does not install anything. The destination in a game data directory is `INTERFACE/HUD/HUD_player_auto_turret.3db`.

The staged icon's material names retain the `UI_` prefix for UI colouring. Without the staged icon, the main control uses `HUD_targetedobject.3db`; the settings button uses the installed inventory gear. Stage the background with the same script using `--prefix player_auto_turret_panel --background --output src/obj/player_auto_turrets/stage/DATA/INTERFACE/HUD/HUD_player_auto_turret_panel.cmp` and the beta inventory CMP as its source. Button selection, captions and tooltips indicate the state. The HUD controls depend on the current `Health` HUD component that owns the relocated weapon-group buttons; keyboard commands also work without that component. The revised layout is built and installed, but still needs visual verification in flight.

## Firing and ownership

`player_auto_turrets.cpp` owns port-only state outside the retail ship/equipment layouts. Equipment is resolved by ID and identity through the live ship manager. The player and assigned target use native watchers. A replaced loadout entry is not armed during an existing order.

`UpdateSpaceState` reconciles ownership before simulation and ticks automatic firing after the camera's manual-fire update. Each shot uses `CliShipFireAutomatic` → the same internal implementation as `CliShipFireWeapons` → launcher `TryFire` → the normal local-server fire message. Resource consumption, projectile creation, damage-per-fire plugins and sounds remain in that path. The adapter reports actual `TryFire` success; neither the legacy constant return value nor a changed refire timer is treated as proof of firing.

Manual cursor aim, manual per-gun target changes and all manual fire variants exclude owned turrets. The native zero-ID-count meaning, “all active launchers”, is preserved: filtering happens inside both native loops, so an empty automatic assignment can never accidentally become an all-weapons fire request. Network replay and NPC fire are not filtered by the player's assignment.

Weapon groups retain a separate desired manual-active state for assigned turrets. Switching a group does not turn automatic guns on/off or redirect their aim. STOP restores that manual state; an individual OFF wins. Individual activation changes update the desired state. Saving a weapon group records the manual state rather than the automatic assignment.

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
