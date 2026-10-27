# Perks, temporary boosters and overheating

**English** · [Русский](../ru/re/perks_and_boosters.md)

Research: 2026-10-26–27, static inspection of the working sources over `af086d9`. Existing mechanisms and proposed architecture are distinguished below. No general perk/temporary-effect runtime was found in the inspected gameplay subsystems. Services, effect properties and balancing examples below are proposals, not supported INI keys. No gameplay validation of this architecture was performed.

Related: [progression](content_progression.md), [auto-turrets](player_auto_turrets.md), [cargo contracts](content_cargo_contracts.md), [independent missions](content_open_world_missions.md), [equipment slots](equipment_mount_classes.md).

## Assessment

Perks can modify most calculated ship characteristics and content eligibility. Temporary boosters can use the same modifiers with expiry. Instant resource restoration is a separate operation: it must not be implemented as a continuously applied multiplier or replayed when restoring a save.

Effects belong to a character, ship or mounted equipment instance. Mutating a shared `Archetype` changes other instances, including NPC equipment. Many calculations read archetype fields directly, so modifying an accessor alone misses actual simulation paths.

Perks never issue auto-turret orders. The player explicitly enables a mode and supplies the task; modifiers improve its execution. Incoming damage, a level-up or booster activation cannot independently authorize automatic energy expenditure. Baseline auto-turrets must work without a skill tree.

## Existing implementation

| Mechanism | Inspected source | Consequence |
|---|---|---|
| Two energy pools | [CEPower::Update](../../src/Common/common_cepower.cpp), [CShip](../../src/Common/common_cship.cpp) | `Power/MaxPower` and `ThrustPower/MaxThrustPower` are independent |
| Thruster cost and impulse | [CEThruster::do_simulation_controller](../../src/Common/common_cethruster.cpp) | Direct reads of `PowerUsage` and `MaxThrust`; cost and force are distinct |
| Firing admission and resource debit | [CELauncher](../../src/Common/common_celauncher.cpp) | `GetPowerDrawPerFire`, `DrawPower`, `RefireDelayElapsed`, `DrawAmmoFromCargo` are separate; cost includes barrel count |
| Gun rotation and dispersion | [CEGun](../../src/Common/common_cegun.cpp) | `TurnRate`, `DispersionAngle`, `MuzzleVelocity`; no universal pilot accuracy statistic |
| Shield | [CEShieldGenerator::Update / CEShield](../../src/Common/common_ceshield.cpp) | Regeneration, constant/rebuild energy costs, capacity and offline time differ; Update computes its own elapsed global time |
| Hull, armor and explosions | [server_gameobject.cpp](../../src/Server/server_gameobject.cpp) | Armor divides damage by `HitPtsScale`; hull, shields, equipment, groups and energy have separate paths |
| Consumables | `EqObj::slot_58`, `use_repair_kits`, `use_shield_batteries` in that file | Only RepairKit and ShieldBattery are accepted. Repair kits mend hull, batteries select a damaged shield; no generic booster item |
| Movement | [CEEngine](../../src/Common/common_ceengine.cpp), CShip | Thrust, drag, cruise charging and energy costs exist; the physics controller also reads fields directly |
| Scanning | [CEScanner](../../src/Common/common_cescanner.cpp) | Radar/cargo range, interference and power cost exist; cargo scanning is not a timed survey |
| Tractor | [CETractor](../../src/Common/common_cetractor.cpp), [TractorArm](../../src/Common/common_tractorarm.cpp) | `MaxLength` and `ReachSpeed`; zero range bypasses the range limit |
| Commodity decay | [CECargo::GetDecayDamagePerSecond](../../src/Common/common_cecargo.cpp), server decay pass | Real integration point for refrigeration/preservation; an open player trade already suspends the server pass |
| Adoxa critical explosions | [Explosion::read](../../src/Common/common_archetype_misc.cpp), `EqObj::explosion_hit_hull` | `[Explosion] critical_hit = percent, multiplier` already exists |
| XP, attitude and transactions | [progression](content_progression.md), [contracts](content_cargo_contracts.md) | Career awards, faction relationships and committed economic transactions need distinct handlers |

`CShip::set_thrust_power` simply assigns a value. It does not independently clamp, authenticate ownership, consume an item, synchronize or persist the action. Ship/power initialization fills resources to maximum; do not call it to apply a perk. Shield capacity is also cached.

## Capability catalogue

**A**: an existing calculation can accept a modifier. **B**: multiple paths, caches or protocol must agree. **C**: new gameplay mechanics. Even A requires a new effect layer. P = perk, T = temporary booster, I = instant action. Numerical examples are prototype inputs, not balanced recommendations.

| Area | Candidate | Form | Scope and constraint |
|---|---|---|---|
| Weapons | Lower shot energy cost | P/T | A: admission, debit, HUD and turret budgets must agree |
| Weapons | Faster refire | P/T | A: positive minimum delay; more shots increase cost and workload |
| Weapons | Less dispersion | P/T | A: zero-dispersion guns have no dispersion to improve |
| Weapons | Projectile speed/range | P/T | B: launch, lead, lifetime, AI range and client simulation |
| Weapons | Hull/shield damage bonus | P/T | B: separate channels, healing plugins and explosion paths; avoid duplicate multiplication |
| Missiles | Critical chance/strength | P/T | B: existing criticalhit does not know the firing pilot's perks |
| Missiles | Lock, maneuvering, countermeasure resistance | P/T | B/C: guided-projectile audit still needed; damage is not guidance |
| Turrets | Rotation speed | P/T | A: effective TurnRate, preserving physical arcs |
| Turrets | Faster acquisition/retargeting | P/T | B: proposed order controller; bounded scans and target hysteresis |
| Turrets | Efficient salvos | P/T | B: share a resource budget with manual fire |
| Turrets | Point defense/convoy protection | P | C: target selection and fire rules, not a generic accuracy multiplier |
| Power | Recharge rate | P/T | A: CEPower::Update, not only its getter |
| Power | Maximum capacity | P/T | B: cached maximum; activation does not also fill it |
| Power | Instant refill | I | B: validated, once-only resource transaction |
| Afterburner | Lower drain/faster recharge | P/T | A: distinct thruster and powerplant fields |
| Afterburner | Larger reserve | P/T | B: recompute maximum without ship reinitialization |
| Afterburner | Full restoration | I | B: assign effective maximum once on successful activation |
| Afterburner | More thrust | P/T | B: physics controller; +20% force is not exactly +20% speed |
| Engine | Thrust, reverse thrust, efficiency | P/T | B: drag and flight modes |
| Maneuvering | Turn/strafe performance | P/T | B: torque, angular drag, mass; no global constant changes for one pilot |
| Cruise | Faster charging | P/T | B: physics, HUD and prediction |
| Cruise | Higher cruise speed | P/T | B: separate path and plugin compatibility; not trade-lane speed |
| Shield | Regeneration/power efficiency | P/T | A: distinguish constant and regeneration costs |
| Shield | Capacity/offline recovery | P/T | B: cached maxima and offline state; ShieldBatteryBoost is not ordinary regen |
| Repair | More repair per kit/battery | P/T | B: change both needed item count and healing result |
| Defense | Damage-type resistance | P/T | B: normalized damage context and source attribution |
| Hull | More durability | P | B: current/max HP and persistence; reinstalling cannot heal |
| Environment | Radiation/anomaly resistance | P/T | B/C: identify the damage source; general invulnerability suppresses everything |
| Heat | Capacity, cooling, heat efficiency | P/T | C: new Heat simulation |
| Cooling | Instant heat discharge | I | C: a charge/consumable, separate from Power restoration |
| Scanner | Radar/cargo scan range | P/T | A/B: align all checks, including NPC patrols |
| Scanner | Lower cost/interference tolerance | P/T | A/B: retain verified scan success |
| Survey | Faster detailed analysis | P/T | C: timed surveys require new gameplay |
| Smuggling | Hidden compartments/false manifest | P/T | C: ScanService/CargoLawPolicy, not an empty successful scan |
| Smuggling | Reduced detectability/inspection delay | P/T | C: detection and patrol policies, not a reputation adjustment |
| Tractor | Range/reach speed | P/T | A: maintain cargo-space and item limits |
| Mining/salvage | Yield/rarity | P/T | C: loot generation and ownership; a faster tractor creates no goods |
| Cargo | Less commodity decay | P/T | A/B: server decay and docking/save policy |
| Cargo | Hold/kit/battery limits | P | B: purchases, tractor, persistence and ship replacement; defer temporary holds |
| Trade | Purchase discount/sale bonus | P/T | B: committed server transaction, not just UI prices |
| Services | Repair/rearm discount | P/T | B: committed operation, scoped to base/faction |
| Contracts | Better reward/lower deposit | P/T | C: new controllers and agreement terms fixed at acceptance |
| Contracts | Special offers | P | C: authored mission eligibility; no generator or GenericMission needed |
| Faction | Licenses/access/services | P | C: qualification and faction attitude checked independently |
| Experience | Career-specific XP bonus | P/T | C: proposed AwardService on verified outcomes |
| Reputation | Bonus to earned attitude change | P/T | B: apply once before reward; do not temporarily add/subtract real reputation |
| Exploration | Maps/hints/cargo information | P | C: information disclosure, not merely radar range |
| Support | Ally repair/cooling aura | P/T | C: new ability, distance, ownership and target permission |

## Effect architecture

Separate `ProgressionService` (earned XP), `PerkLoadout` (owned/selected perks), `EffectRuntime` (active effects), `EffectiveStats` (parameter resolution), and `AbilityService` (validated commands). Equipment supplies base characteristics and its own effects; consumables activate the same runtime. Missions can award effects through this API. StoryLauncher is not needed to tick boosters.

An effect definition has a stable ID/version, scope, typed modifiers, conditions, stacking group, reapplication rule, duration and cooldown. An instance records its owner, source, unique activation ID, time, stacks and ship/equipment binding. Conditions can select ship/weapon family, equipment role, active mode, resource threshold, faction or contract. Do not make arbitrary executable INI code the initial API.

A permanent perk is an unexpired effect source, potentially conditional. Emergency defense at low shields needs a threshold-crossing event, hysteresis and cooldown, not a free battery every tick. Damage/death/reward events need identity, ownership and object generation. Redelivery cannot repeat an action or award; effects cannot recursively retrigger themselves through their own damage/healing.

Preserve cross-DLL layouts/vtables unless all consumers change together. An external instance-state store can avoid altering retail structures, but must use generation-aware identity and lifecycle cleanup. Neither a reusable object ID nor a raw pointer alone is sufficient. Archetype metadata and personal effects are different stores.

### Mathematics and application timing

Proposed formula: `effective = clamp((base + sum(flat)) * (1 + sum(additivePercent)) * product(groupMultipliers), min, max)`. Each parameter declares permitted operations and caps. Probabilities stay within 0..1, costs are nonnegative, and refire delay has a positive floor.

For example, +10% and +20% perks form ×1.30; an explicitly independent ×1.25 booster produces ×1.625. Identical boosters refresh duration by default instead of multiplying again, without resetting cooldown. Other groups can select the strongest contribution. These policies belong in definitions, not insertion order.

Recalculate from base values. Expiry never subtracts an old bonus from an already modified value. Equipment changes invalidate caches. Increasing a maximum preserves the current resource; decreasing it clamps current to the new maximum. Capacity activation/expiry must not heal or create energy. Defer temporary cargo holds until an overflow policy exists; never delete cargo on expiry.

Snapshot outgoing bonuses into the shot context; evaluate target defense at impact. Changing weapons after launching a missile must not change its bonus. The context survives the shooter disappearing. Direct impact and explosion cannot accidentally apply the same multiplier twice. Delayed explosions, beams and mines need explicit timing rules.

Admission, debit, HUD prediction and turret budgeting use the same effective price. Changing `GetPowerDrawPerFire` alone is insufficient because `DrawPower` directly reads the archetype. Thrusters, shields, scanner and gun turning likewise need actual calculation hooks.

## Concrete afterburner boosters

| Booster | Proposed action | Constraint |
|---|---|---|
| Emergency reserve | Fill ThrustPower once to effective maximum | Alive owned ship and functioning system; full reserve rejects without consuming |
| Efficient afterburner | Illustratively ×0.65 drain for 15 seconds | Does not improve thrust or refill weapon power |
| Accelerated recharge | Illustratively ×1.5 ThrustChargeRate for 20 seconds | Does not restore a destroyed powerplant |
| Thrust overdrive | Illustratively ×1.2 force, ×1.3 drain for 10 seconds | Speed still depends on drag; add a heat cost once Heat exists |

Activation: validate ownership/state/item/cooldown → compute outcome → atomically apply, consume and record cooldown/receipt → acknowledge. Repeating a request returns the original outcome. Failure or a useless refill does not consume an item. Existing SPRequestUseItem is not a complete generic ownership/effect validator.

## Adoxa critical hits and personal extensions

With `FREELANCER_ADOXA` and `[Plugins] criticalhit = 1`, the existing reader accepts:

```ini
[Explosion]
critical_hit = 15, 2
```

This is a 15% chance of ×2. Percent is converted to a fraction and capped at 100%. `AdoxaCriticalHitMultiplier` uses `rand()` during explosion hull-damage processing. The inspected path combines the multiplier with distance band and explosion resistance. It belongs to the explosion, not exclusively to missiles, and does not automatically multiply shields, equipment, energy damage or direct impact. Each hull-processing call rolls separately; a multi-target explosion has no precomputed shared critical outcome.

Proposed personal `CriticalPolicy`: base explosion chance plus pilot/conditional bonuses, separate strength, server RNG and damage-event identity. Initially choose one roll per explosion–target pair, reused for the explicitly eligible damage channels of that pair. This is a new policy, not Adoxa's existing behavior. A whole-missile roll can be a separate policy rather than an accidental mixture.

Examples: +5 percentage points changes 15% to 20%; +0.25 strength changes ×2 to ×2.25. Both need caps. Expected multiplier is `1 + chance * (multiplier - 1)`: 15% at ×2 gives 1.15; 20% gives 1.20. Negative healing damage, environmental damage and self-inflicted heat damage are excluded by default. MP clients display the confirmed outcome instead of rolling independently.

## Overheating and cooling equipment

Heat is a third resource, independent of power and afterburner reserve. Begin with one ship thermal loop; split weapons/engine loops only if needed. Firing and afterburning together increase its load. Energy is not implicitly heat: content assigns explicit sources.

Store accumulated heat `H`, capacity `C`, passive cooling `P` and active cooling `A`; HUD fill is `H/C`. Proposed update: `H_next = max(0, H + heatFromCommittedActions + continuousHeat * dt - cooling * dt)`. A successful shot adds heat once after resource debit/shot creation; rejected fire does not. Continuous propulsion heat follows actual work. Ability cooldown and heat are separate state.

States: Normal → Warning → Overheated, with a lower threshold for recovery. Prototype thresholds: warn at 80%, stop sources at 100%, recover at 60%. Initially block new heat-producing shots and enhanced afterburner while retaining normal control and cooling. Existing missiles remain. Auto-turrets pause with an overheating reason and retain the player's order; recovery cannot restore a canceled order.

Capacity changes preserve absolute H. If capacity falls below H, remain overheated; clamping H to the new capacity would provide free cooling. Destroying a cooler removes its contribution. Reinstalling equipment cannot reset heat. Docking/repair can offer explicit cooling service, not an incidental load reset.

| Device | Function | Tradeoff |
|---|---|---|
| Passive radiator | More continuous dissipation | Slot, mass/cost; no consumable |
| Active cooler | Commanded cooling consuming Power | Competes with weapons/shields; no power means no active contribution |
| Thermal accumulator | More capacity | Longer before overheat, longer to cool from full; no reduction in generation |
| Ejectable heat sink | Instantly removes heat | Charges, cooldown, player command |
| Weapon cooler | Less heat per shot for a group | Family/group filter; not universal free cooling |
| Cargo refrigerator | Less decay for selected goods | Cargo preservation is separate from the ship's thermal loop |

Perks can improve dissipation, generation efficiency, capacity and active-cooler cost. Boosters can add temporary cooling, instant discharge or a hot overdrive. Start with clear inhibition and HUD, without automatic ship explosion or hidden random failures. Thermal detectability, component damage, fires and environmental cooling are later systems.

`engine_heat_visual.cpp`, introduced by `b4c4a72` (Warp effects, 2026-10-25), renders exhaust refraction. Its `Heat` controls visual intensity and is not the simulation above. The user requested that effect remain disabled. Gameplay Heat must not depend on RP9, camera or graphics settings.

## Persistence, networking and UI

SP durations default to simulation time: pause/offline do not consume them; persist remaining duration and cooldown. MP expiry and offline policy come from the server. System transitions cannot create another effect or replay instant actions. Characters own perk selections, ships own resources/Heat; every definition declares whether effects bind to pilot, ship or equipment.

Initially, death removes ship temporary effects but retains character perks. Ship replacement rebuilds modifiers without carrying instant healing. Turret orders reset on load independently of perks. Docked timing and reapplication policies must be explicit. Old saves yield neutral defaults; unavailable effect definitions do not execute.

MP requires authoritative activation, inventory, cooldown, critical outcomes and Heat, plus protocol/version capability negotiation. Existing FireWeapons/UseItem messages do not establish readiness. Prediction uses the same formulas and reconciles with server snapshots. The client-originated fire_unchecked path cannot bypass new restrictions. Remote visual replay must not debit energy or add heat again.

HUD shows effects, remaining time, cooldown, effective values and rejection reasons. Heat needs load/threshold/cooling state; turrets need order/pause reason. Market discounts shown before confirmation match actual payment. Contract terms lock at acceptance; XP bonuses use an explicit reward-time policy.

## Delivery order and verification

1. Equipment slots/classes and independent effective-stat runtime with neutral defaults; baseline auto-turrets stay independent.
2. Instant afterburner refill, reduced afterburner drain and power recharge: activate, consume, save, restore without replay.
3. Turret, scanner/tractor and cargo-preservation perks; consistent cost/range checks.
4. Shared Heat, passive/active cooler and heat sink; then personal critical hits.
5. Damage/defense, economy/faction effects and contract-backed inspection/smuggling rights.

Future acceptance cases: two pilots using the same archetype; stacking/expiry; equipment destruction/replacement; duplicate request; full resource; save/load around consumption; death/dock/system change; multiple barrels; manual and automatic fire together; multi-target critical explosion; negative healing damage; rejected/network-replayed shots producing no heat; capacity swapping without cooling; different frame rates; server reconciliation; unsupported clients rejected.

Under [CONTRIBUTING](../../CONTRIBUTING.md), new gameplay features use separate default-off `FREELANCER_*` switches with retail paths preserved. Suggested `FREELANCER_PLAYER_EFFECTS` and `FREELANCER_GAMEPLAY_HEAT` are design names only, not added defines. This document does not claim implemented perks, boosters or overheating.
