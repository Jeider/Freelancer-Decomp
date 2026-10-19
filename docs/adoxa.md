# adoxa's plugins

**English** · [Русский](ru/adoxa.md)

[Jason Hood (adoxa)](https://adoxa.altervista.org/freelancer/plugins.html) wrote dozens of
small Freelancer plugins. Each patches retail `freelancer.exe`, `common.dll`, `server.dll` or
`content.dll` at hardcoded addresses, so the port cannot load them; their behaviour is rewritten
here from the public sources (the newest versions), in the modules they patched.

| Property (`src/Freelancer.Diagnostics.props`) | Define | Sheet default |
|---|---|---|
| `FreelancerAdoxa` | `FREELANCER_ADOXA` (client, `Common.dll`, `Server.dll`, `Content.dll`) | 1 |

Each plugin is switched by its own key in `port.ini [Plugins]` (`src/include/port_plugins.h`
`PORT_PLUGIN_ON`); a missing key is off. The plugins' own data files stay where they were.

## Gameplay

| Key | Plugin | Port |
|---|---|---|
| `burn` | burn.dll: `atmosphere_burn_<ship type>` effects | `client_gameobj.cpp` (`0x005453f0`) |
| `chklootvol` | chklootvol.dll: NPCs skip loot that does not fit their hold | `LootBehavior::AcquireLootTarget` (`062ce8e8` / `062ce9d9`) |
| `ShieldOffline` | ShieldOffline.dll: shield stays offline while the owner has no hit points | `CEShield::IsActive` override (vtable `0639d510`) |
| `LaneSpeed` | LaneSpeed.dll: `[Solar] lane_speed` | `Solar::read`, `CShip::go_tradelane`, the lane's 2500 in `common_laneaction.cpp` |
| `JumpOutPt` | JumpOutPt.dll: `DATA\UNIVERSE\JumpOutPt.ini` arrival ellipse and angle | `Solar::ChooseSystemArrivalLocation` (`06d031a6`) |
| `criticalhit` | criticalhit.dll: `[Explosion] critical_hit = percent, multiplier` | `Explosion::read`; `EqObj::explosion_hit_hull` (`06ce964c`) |
| `DamagePerFire` | DamagePerFire.dll: launcher wear by `damage_per_fire` | `CELauncher::ConsumeFireResources` (`06299623`) queues it; `Ship::update` (`06d014bf`) applies it |
| `EquipDrag` | EquipDrag.dll: `linear_drag` on equipment | `Equipment::read`; `CShip::get_linear_drag` and `CShip::update` (`062b378c` / `062b0ee1`) |
| `dynastex` | dynastex.dll: dynamic asteroids with `hit_pts` (±10 %) and `mass` (±10 %) | archetype loader (`062fa1e4`), `CDynamicAsteroid::init_physics` (`062a2b2e`), `cli_asteroid_dynamic.cpp` (`0x005254d2`, `0x00525eec`, `0x0052610e`, destructor). Port extension `[dynastex] collision_damage = 1`: the asteroid reports collisions like every other gameobj (`Slot1ac`), so ramming one damages the ship |
| `healing` | healing.dll v2.00: negative damage repairs (zones, munitions, explosions) | `EqObj::damage_hull`, `damage_equip`, `damage_group`, `GameObject::damage_hull`, zone ticks, shield passes, explosion checks (`src/include/adoxa_healing.h`), `DamageList::add_damage_entry`, `ZONE::HasPhysicalEffect`, the weapon stats |
| `moors` | moors.dll: player ships use moors | `CEqObj::launch_pos`, `has_dock_hardpoints`, `Server_GetLaunchPosition`, the land byte in the system update, Content's terminal pick |
| `storyfactions` | storyfactions.dll: `DATA\storyfactions.ini` | `EnsureStoryFactionIds` |
| `dock_key` | dock_key.dll v1.01: `DATA\dock_key.ini` keys for locked docks | `CheckDockPermission` (`06f6c958`); the docking player's equipment (the plugin read the first player's for every ship) |
| `ammolimit` | AmmoLimit.dll: `ammo_limit = n \| *f \| /f` | `Projectile::read`; `CShip::get_ammo_capacity_remaining`, the dealer and inventory caps |
| `MatchJob` | MatchJob.dll: `DATA\MISSIONS\RankDiffSP.ini` job difficulty by rank | `LootProps.cpp` mission offers (`06f046eb`) |
| `MatchPlayer` | MatchPlayer.dll: encounter level raised to half the player's rank | `FZonePopulation::ParseValue` (`06ef9066`) |
| `callsign` | callsign.dll: the player's call sign (`port.ini [callsign] callsign = faction [formation [n][-][n]]`) | `Gcs.cpp`: `gcs_refer_faction_*`, `gcs_refer_formationdesig_*`, `gcs_misc_dash`, the two player numbers |
| `DisableAutoLevelToggle` | the exe patch `0xdbe10 94 -> 95` ("Disable auto-level toggling") | `HUD_Status::OnEvent` case `0x3e` |

## Interface

| Key | Plugin | Port |
|---|---|---|
| `TurretZoom` | TurretZoom.dll v1.41: zoom and move the turret camera | `space_camera_turret.cpp`, `hud_maneuvers.cpp` (wheel), `space_state.cpp` (toggle); optional `[TurretZoom]` keys `fast`, `inverse`, `max`, `shift`, `ctrl`, `alt`, `s+c`, `c+a`, `small`, `large`, `switch`, `adjust`, `interval` (the DLL's arguments) |
| `scroller` | scroller.dll: one scroll bar for the stats and values panes | `rich_text_win.cpp`, `nn_ship_trader.cpp` |
| `numeric` | numeric.dll (FL Hack's numeric damage) | `HudTargetableObjects::DrawOnScreenTarget` (`0x004ef771`, `0x004efd8e`) |
| `territory` | territory.dll v1.03: arrival texts and Nav Map house labels | `nn_modal.cpp`, `nn_navmap*.cpp`; the ini by language: `[Language.<code>] territory_ini` (default `territory.ini` in `DATA\UNIVERSE`), `territory_codepage` when the ini has no `[Settings] codepage` |
| `NoNavMap` | NoNavMap.dll: systems the Nav Map calls unavailable (`DATA\UNIVERSE\NoNavMap.ini`) | `nn_navmap*.cpp` |
| `engclass` | engclass.dll v2.02: typed and classed engines and powerplants (`hp_<fighter\|elite\|freighter>_<power\|engine>_special_N`, hp types `0x43..0x7e`; `hp_type = TYPE MAX, ...` in `[Ship]`) | `Ship::read`, `Power::read` / `Engine::read` and their `get_hp_type`, `CEqObj::add_equipped_item` (no "internal type to hardpoint" warning), the ship view's hardpoint tables, `nn_inventory.cpp`, `nn_dealer.cpp`. The strings (6 descriptions, 60 names) come from the plugin's own string DLL loaded as data: `[Language.<code>] engclass_resources` (default `engclass.dll`) |

WheelScroll is part of [flplusplus](flplusplus.md). HudShift and navmapxy are not ported.

## Deviations

All port-only; with the property off (or the key off) the behaviour is retail's. Where the port
differs from the plugin: `dock_key` checks the docking player, `JumpOutPt` keeps the double
radius default, `engclass` keeps the hp type in a table instead of byte `+0x6f` and reads its
strings without running the DLL, `healing`'s explosion checks test `|hull_damage|` (the plugin's byte patch let
every explosion through), `scroller` finds the stats pane by name, `NoNavMap` stops at 127
systems (the plugin overran its array).
