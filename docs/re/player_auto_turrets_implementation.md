# Player auto turret implementation plan

**English** · [Русский](../ru/re/player_auto_turrets_implementation.md)

Historical plan dated 2026-10-27. Implementation has now started and the SP controller, HUD and keyboard commands are in the source. See [implemented behavior, configuration and validation](../player_auto_turrets.md) before using this document: proposed API names, settings and future acceptance criteria below are not all implemented. The original plan is retained to preserve the research and remaining work.

## First implementation scope

The player pilots and fires the main guns while assigned turrets follow explicit orders. Commands sit **below the weapon groups**, using the beta Auto Turret button. Autopilot, turret camera, perks and internal equipment slots are not prerequisites.

Proposed first release: **SP, energy turrets firing unguided projectiles at ships**. Exclude ammunition-consuming guns, guided weapons, mines, countermeasures and the special `force_gun_ori` path until separately tested. MP is a separate release. Proposed component names, command names and configuration below are not existing APIs or working INI keys.

NPCs retain their existing AI. The player's controller does not enable NPC `ScanAutoTurretTargets/FireAutoTurrets`, control ship steering or modify shared weapon archetypes.

## Orders and transitions

| Action or condition | Behavior |
|---|---|
| Start, load, new ship | Manual; never restore permission to fire from preferences |
| Change preferred mode | Change a preference, do not start firing |
| Press Auto Turret while off | Issue the preferred order; target mode captures the currently detected hostile ship |
| Press Auto Turret while ordered or suspended | Stop immediately and return the turrets to manual ownership |
| Assigned target | Follow that object instance; subsequent selection changes do not change the order |
| Free fire | Each turret selects an eligible hostile in its own sector |
| Change mode during an order | Stop first; the new mode requires another explicit start |
| Stop command | Cancel even while waiting for energy, targets or a future MP acknowledgement |
| Change automatic-group membership | Cancel; newly included weapons do not inherit fire permission |
| Hide HUD or collapse weapon window | Presentation only; the controller remains independent of window visibility |
| Modal input, lost foreground focus, cruise, trade lane, docking, cinematic | Suspend the existing order until conditions permit it again |
| Death, landing, jump, ship/character change, load, disconnect | Cancel and clear targets and weapon references |

Default preferred mode: assigned target. Reject start with a clear reason if no valid target exists. Neutral/friendly targets are excluded even from explicit target orders in this release.

Destruction/removal of an assigned target cancels its order. Temporary loss of detection retains only its identity, stops aiming/firing and waits for detection of the same instance; do not use its hidden position for tracking. No targets in free-fire mode means waiting, not cancellation.

## Automatic membership and manual groups

Use a separate hardpoint-name list, independent of groups 1/2/3. Initially propose all eligible mounted energy turrets. An explicitly saved empty selection means no assigned turrets, not an implicit select-all.

Eligibility: CEGun, `bAutoTurret` or explicit `hp_turret/hp_turret_special_1..10`, a valid unguided non-ammunition projectile without `force_gun_ori`, valid barrels and connected geometry. Do not infer eligibility from a hardpoint nickname or an unrestricted fallback type list. [hud_vulnerable.cpp](../../src/freelancer/Client/hud_vulnerable.cpp) already distinguishes explicit turret types from that fallback.

Each weapon has exactly one aim/fire owner. An automatically owned turret stays excluded from manual fire during suspension; only Stop returns ownership. Individual user deactivation wins, and the controller never silently reactivates it.

While an order exists, `FWeaponGroups::Activate` skips automatically owned turrets when changing activation and aim. Selecting a main-gun group therefore does not disable automatic turrets. Preserve saved manual group membership. On Stop, reapply the current manual group to released turrets without rebuilding the group definitions.

Audit StoreActive, Activate, GetGroupEquipIds and individual toggles in [hud_weapon_groups.cpp](../../src/freelancer/Client/hud_weapon_groups.cpp) and [hud_status_core.cpp](../../src/freelancer/Client/hud_status_core.cpp). Filtering only the cursor aim path is insufficient.

Keep desired manual activation separately for automatically owned turrets. Capture it on handoff; group changes update that intent without changing live automatic activation. StoreActive reads that intent instead of the automatic state. Individual deactivation updates both states and records an explicit veto until the user enables the weapon again; it overrides intervening group changes. Stop restores the desired manual state with that veto. Saving a group therefore does not accidentally include every operating automatic turret, and Stop cannot reactivate an individually disabled weapon.

## Components and lifecycle

| Proposed component | Responsibility |
|---|---|
| PlayerTurretController | Order, ownership, membership, lifecycle, adapter orchestration |
| TurretPolicy | Eligibility, scoring, suspension and energy rules independent of HUD |
| TurretWeaponAdapter | Resolve live CEGun, assign target/point, geometry checks, normal fire |
| TurretHudViewModel | Read-only display snapshot and common button/key command entry |
| PlayerTurretPreferences | Versioned hardpoint selection, preferred mode and energy thresholds |

Store order, suspension reasons and preferred mode separately. A reason change cannot issue an order. Bind state to a live ship instance and session generation. Use object watchers: object IDs can be reused. Resolve equipment again by ID and hardpoint before action and verify its archetype; do not retain raw CEGun pointers across frames.

Track ship-wide and per-turret reasons. One firing turret plus one obstructed turret means an active order with an operating count, not global suspension. For a fully blocked group, display unavailable mode/world first, then control exclusion, missing scanner/turrets, energy restriction and no eligible targets. Normal refire delay is normal operation rather than a flickering pause; individual details remain available.

Persist preferences per character/hull with normalized hardpoint names and a schema version. Do not persist equip IDs, object pointers, targets, active orders, timers or live energy. Do not enlarge retail structures/vtables or extend the existing wg text format. Unsupported/corrupt preferences fall back to manual.

One destroyed turret removes that member. No eligible members left cancels the order with NoTurrets. Equipment replacement/loadout changes require a fresh start.

## SP update placement

Add one controller call inside the simulation branch of UpdateSpaceState, **after active-camera Update and before StarSysUpdate**. Commands change ownership synchronously when handled, so subsequent manual inputs already see it. Check pause, world readiness and current ship identity before every action.

Current order in [space_state.cpp](../../src/freelancer/Client/space_state.cpp): ClientObjDb_UpdateAll → AnimDB::Update → PhySys::Update → camera.Update → StarSysUpdate. The chosen point follows held manual fire and its energy consumption without being tied to one camera type.

Controller step:

1. Apply lifecycle/cancellation and control/device/scanner gates.
2. Resolve assigned turrets and obtain current detected contacts.
3. Validate current targets; acquire replacements on the search timer or invalidation.
4. Assign per-gun target, calculate lead and supply the automatic target point.
5. Check actual barrel alignment, individual range, obstacles and readiness.
6. Admit shots sequentially within the budget, rereading actual energy each time.
7. Publish a HUD snapshot.

Do not call CShip, CEGun, AnimDB or physics Update a second time. A new aim point affects joints on the next simulation step; that bounded latency is acceptable. Fire admission uses the actual current barrel direction. Never replay accumulated firing opportunities after a hitch/pause; at most one normal attempt per ready device per step.

## Aim handoff and shared fire path

SetTargetPoint has a two-second priority over object targeting. The chosen solution is a fresh **automatic target point each step**: assign object target, compute/check ComputeTgtLeadPosition, then SetTargetPoint. This replaces the old cursor point immediately while JointChannel::Tick still respects normal TurnRate. Do not directly modify joint angles, TargetPointAge or the shared archetype.

Use CanPointAt for mechanical reach, CanSeeTargetPoint for current alignment and GetMunitionRange for that gun. Aim and fire admission must use the same point. ComputeTgtLeadPosition can return true with the target's current position when no intercept solution exists; separately check intercept feasibility and projectile lifetime before wasting shots. Match the engine's relative-velocity convention.

Introduce an internal fire adapter with Manual, Automatic and NetworkReplay sources, preserving the external CliShipFireWeapons signature. Only the local player is filtered. Manual requests exclude automatically owned weapons; automatic requests name explicit devices; replay bypasses manual ownership filtering.

Required call sites:

- [space_camera_game.cpp](../../src/freelancer/Client/space_camera_game.cpp): all-gun cursor aim, first held-fire frame, later explicit lists.
- [hud_status_core.cpp](../../src/freelancer/Client/hud_status_core.cpp): individual/group/all fire; keep seeker/dropper commands outside automation.
- [cli_projectile_fx.cpp](../../src/freelancer/Client/cli_projectile_fx.cpp): CliShipLeadAimFire, broad target reassignment in CliShipHandleEquipUpdate, central fire adapter.
- [hud_weapon_groups.cpp](../../src/freelancer/Client/hud_weapon_groups.cpp): activation and retargeting.

**An empty filtered list returns without calling fire.** Local count=0 means all active launchers.

CliShipFireWeapons always returns 0. Collect a new internal FireReport from actual TryFire/FireBarrelAim results rather than treating the old return as success. Refire reset is not proof either: CELauncher::Fire resets its timer for some failures. Keep muzzle effects, sound, wear, resource consumption and ordinary SP shot transport in the existing path.

## Detection and target selection

Use CEScanner::Scans and scan_for_types. Never clear its shared cache for this controller; CEScanner::Update already refreshes it. No functioning scanner means no automatic targeting or fire, including when the new removable scanner is absent. ObjectDB existence is not detection.

A candidate must be another living targetable ship in the same system, detected by this scanner, not fully cloaked, hostile under current reputation and not explicitly vetoed by mission policy. Recheck before each shot. Exclude loot, missiles, bases, neutrals and dying ships.

A mission's desire to keep a target alive cannot be inferred reliably from reputation. Provide an explicit mission veto for ship/target. Until integrated, claim only the confirmed engine/control gates, not universal recognition of story-protected targets. Include capture/keep-alive objectives in integration tests.

Proposed tuning defaults: search at 5 Hz; retain a valid target for at least 0.75 s. Prefer enemies attacking the player. Otherwise retain a valid current target; switch within the same priority tier only after minimum dwell and when the replacement is at least 20% closer. Invalid targets clear immediately. Resolve ties by a stable ID within the current world generation. These are prototype values, not measured optima.

Different turrets can choose different targets. Target changes invalidate prior alignment/clear-line decisions.

## Obstacle checks

The NPC helper uses a cache, barrel zero, a ray from 20 to 2000 metres and limited blocker classes. Do not reuse those assumptions for player turrets.

Use PhySys::FindRayCollisions and, where needed, FindRayIntersect from each firing barrel toward its lead point, only after cheap eligibility/readiness checks. Include ships, stations and collidable geometry; do not ignore the entire own hull. A small muzzle epsilon must address numerical precision, not skip obstacles. One blocked barrel prevents the whole multi-barrel shot in the first release.

Unknown/not-ready physics, invalid geometry or ambiguous hit-buffer saturation means no shot. PhysicalSystem::FindRayCollisions currently returns nearest hits first but skips physics bodies without client objects; verify coverage against actual mod models. Test own-hull interception and muzzle placement explicitly.

A ray is not a guarantee against a friendly moving into a projectile's future path. The first release avoids firing through currently blocking geometry; perfect future friendly-fire prevention is out of scope.

## Energy and future effects

Proposed thresholds: 35% weapon-energy reserve, resume at 45%. Validate finite values, range and ordering. Cost comes from GetPowerDrawPerFire, including all barrels.

Run automatic shots sequentially after manual fire. Require E − cost ≥ reserve × Emax for each; reread E after the attempt. **Only ConsumeFireResources spends energy.** Do not subtract both an already consumed cost and a reservation for that same shot.

Leaving an energy pause requires the upper threshold, plus enough energy above reserve for the individual shot. Invalid E/Emax/cost suspends automatic fire. Manual input may consume the reserve.

Use a rotating stable hardpoint order to prevent low-index turrets monopolizing the remaining energy. Explain when a gun's cost cannot fit above reserve even at full capacity. Do not issue futile attempts every frame solely to obtain a rejection.

Later perks provide an immutable effective-parameter snapshot for decision delay, tracking quality, spread and cost. Actual turning speed/resource changes require per-instance Common adapters; a controller-only multiplier is insufficient. Estimated and consumed effective costs must agree. Booster expiration neither creates/cancels orders nor refills resources.

## Interface below weapon groups

Confirmed original: `D:/games/Freelancer Beta/DATA/INTERFACE/HUD/HUD_autoturreton.3db`, 9972 bytes. It contains VMesh, materials and HUD_autocannonon.tga/HUD_autocannonoff.tga textures. The checked FL_MOD interface directory lacks that file. No asset was copied or changed.

HUD_Health::BindHost currently creates the three group buttons. UpdateHostButtons positions them at x=0.255, y=-0.247/-0.271/-0.295. Treat this as the **anchor**, not immutable coordinates after the parallel HUD work.

```text
[ group 1     ]
[ group 2     ]
[ group 3     ]
[ Auto Turret ]  start / immediate stop
[ mode        ]  target / free fire; settings open to the left
```

Use two controls in the same column immediately beneath the last group. Initial centre estimates are y=-0.323 and -0.351; fit size to actual mesh extent and the viewport bottom. Open the settings panel leftward so it avoids weapon numbers; clamp it vertically to the viewport. Show detailed state and reserve in its panel/tooltips, not a long line squeezed into the narrow column.

Main button states: off/manual, active/order, amber/suspended, disabled/unavailable with a reason. Tooltips distinguish states without relying only on colour. Active/suspended clicks always Stop. Settings show mode, hardpoint membership, reserve, operating/assigned count and pause reason. Editing settings cannot start fire.

Follow the groups' parent, AttachPosition, scaling, visibility and lifecycle. Collapsing/animating the weapon panel hides both drawing and hit testing. A rebindable Stop command remains available while the panel is hidden when gameplay input is available. Rendering and HUD visibility never advance or stop the controller.

Add a separate PlayerTurretHud consuming an anchor from the group block rather than putting simulation in HUD_Health or adding fields to retail HUD_Status. Without that block, no widget is created; keyboard control remains. Supporting a different legacy HUD layout requires its own anchor.

Asset integration plan: load the original 3db through the normal model path; verify on/off materials without assuming a montage entry exists. Check the generic Material #92 name for collisions; if needed produce a derived copy with unique materials/textures and remapped VMesh references, preserving the source. Add RU/EN labels through the existing hud_interface_ids/staging process. Allocate actual IDS and command numbers only after concurrent changes are integrated. Do not commit retail/beta binaries or overwrite unrelated resources.

Proposed command names: AUTO_TURRET_TOGGLE, AUTO_TURRET_ATTACK_TARGET, AUTO_TURRET_FREE_FIRE, AUTO_TURRET_STOP, AUTO_TURRET_SETTINGS. Integrate with rebinding; no numeric IDs or default keys are allocated yet. Key auto-repeat must not repeatedly toggle/start the mode.

## Multiplayer follow-up

The first release refuses automation in MP with a visible reason. Existing transport is insufficient proof of validation: IServerImpl::FireWeapon → EqObj::slot_34 uses fire_unchecked for a client source.

Choose the **server as the single automatic decision authority** for the follow-up. Share policy logic, not simultaneous simulation ownership. Client sends orders/settings; server validates ship/equipment ownership, targets and resources; HUD displays acknowledged state. Disable client-issued automatic shots in this mode.

Extension contract: capability/version negotiation; Order(sessionEpoch, seq, ship, mode, hardpoints, target); Ack(seq, accepted, reason); assignments/suspension snapshots; unique shot events with explicit coordinate space. Stop advances seq; late acknowledgements/orders cannot re-arm the controller. Local Stop ends prediction immediately; server stops when the cancellation arrives, not retroactively across network latency.

Separate different-target shots or introduce a new packet format. XFireWeaponInfo has one aim point and the MP path transforms it relative to a lock target. Do not mix different targets or world/local coordinates. Owner replay must neither send FireWeapon again nor charge resources twice.

Shots already executed before Stop still replay exactly once even if delivered afterwards. Require event deduplication, ordering/loss handling and state recovery. Capability negotiation and transport are not implemented; precise wire layout/registration belong to the separate MP task. Test reconciliation with predicted manual fire consuming the same server-owned energy pool.

## Implementation sequence and acceptance

| Stage | Work | Exit criterion |
|---|---|---|
| 1 | State, ownership, adapters and policy tests | Stop/empty-list handling cannot become fire-all |
| 2 | One turret on one explicit target | Independent main-gun aim and player piloting |
| 3 | Multiple targets, scanner, obstacles, energy | No unauthorized/undetected shots; reserve respected |
| 4 | UI below groups, beta asset, RU/EN, keys, preferences | UI reflects real state; only preferences persist |
| 5 | World transitions, device failure, disabled configuration | No stale references or unintended legacy changes |
| Separate | MP, ammunition turrets, perks | Their own network/resource acceptance gates |

Proposed default-off build property/define: FreelancerPlayerAutoTurrets / FREELANCER_PLAYER_AUTO_TURRETS, following CONTRIBUTING. Runtime availability is not permission to fire. Define the actual preference format during implementation; do not advertise proposed keys as functional.

Required cases:

- Enemy presence/damage without an order produces zero automatic shots.
- Empty filtered manual list produces no low-level fire call.
- Same-step order/Stop, held-key repeat and cancellation during suspension.
- Front/rear sectors, different projectile speeds, real turn limits and fresh cursor-point handoff.
- Group switching, individual deactivation and simultaneous manual/automatic fire.
- Missing/destroyed scanner, interference, cloak and lost detection.
- Destroyed target with reused object ID.
- Multiple barrels, friendly/station/own-hull obstruction.
- Energy permitting exactly one shot above reserve; no double consumption or starvation.
- Low FPS, pause, lost focus, cinematic and return without queued bursts.
- Landing, jump, death, load, new ship and disconnect clearing live orders.
- 4:3, 16:9, ultrawide, HUD scaling, collapsed/animated panel and hidden hit regions.
- Build/runtime off preserving the existing behavior; MP v1 clearly unavailable.

Policy tests cover state/filter/budget/lifecycle. Native tests exercise real DLL adapters and preference serialization. In-game tests verify actual geometry, turn animation, fire and UI; successful compilation alone does not establish those properties. Use DebugASan for the new object ownership.

Architecture for the first SP implementation is specified. Remaining checks are implementation acceptance gates, particularly actual barrel/joint behavior, collision coverage, beta material states and final placement after the parallel HUD changes.
