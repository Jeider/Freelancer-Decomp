# FLSharp.dll behaviour

**English** · [Русский](ru/flsharp.md)

[FLSharp](https://github.com/BC46/FLSharp) (BC46; MIT) is a client and server plugin that
patches retail `freelancer.exe`, `common.dll`, `server.dll`, `engbase.dll`, `alchemy.dll`,
`dalib.dll` and `gundll.dll` at hardcoded addresses, so the port cannot load it. Its fixes are
rewritten in the modules they patch, from its sources.

| Property (`src/Freelancer.Diagnostics.props`) | Define | Sheet default |
|---|---|---|
| `FreelancerFlsharp` | `FREELANCER_FLSHARP` (client, `Common.dll`, `Server.dll`, `EngBase.dll`, `alchemy.dll`, `DALib.dll`) | 1 |

`/p:FreelancerFlsharp=0` builds the retail behaviour.

## Settings

`FLSharp.ini` next to `freelancer.exe` (the port's `bin\`), the plugin's own file: every
`name = true/false` of every section. A missing key is on, as in the plugin. `Common.dll` reads
it (`FlsharpFeatureEnabled`, `src/include/common_flsharp.h`); `EngBase.dll`, `alchemy.dll` and
`DALib.dll` do not link `Common.dll` and read their key from `[FLSharp]` themselves.

## Ported

These are the fixes the mod's `FLSharp.ini` turns on.

| Key | Retail place | Port |
|---|---|---|
| `flight_controls_fix` | free at `0x0054b8b9` | `player_spawn.cpp`: on spawn the camera level toggle (third-person +0x13c) and the HUD auto-level state follow the ship's behaviour manager |
| `save_crash_fix` | `0x00487ebf`; server `.text:06d4766e` | `nn_load_save.cpp` (unknown ship shows ids 0), `Server/server_savegame.cpp` (save with an unknown ship skips the collision groups) |
| `blank_faction_fix` | Current Information | `nn_help.cpp`: `fc_uk_grp` (197510) reads "None" (3022) |
| `shield_capacity_fix` | shield stats | `dealer_equip_stats.cpp`: capacity minus `offline_threshold` |
| `waypoint_fixes` | HUD waypoint; nav map `0x00493a00` / `0x00493b21` | `hud_waypoint.cpp` (only waypoints of the current system are reached), `nn_navmap_input.cpp` (the player marker is no waypoint target) |
| `waypoint_name_fixes` | `0x004e4094`, `0x004755b8`, `0x00475676`, `0x004e8131`, `0x00475a6c`, `0x00475a94` | `hud_target*.cpp`, `nn_help.cpp`: waypoints are never "Unknown Object", mission waypoints are "Mission Waypoint", "PLAYER WAYPOINT n" with its own number, random mission objectives shown |
| `weapon_anim_fix` | `0x0661b83f` | `EngBase.cpp` binds the channel to the hull; `cli_projectile_fx.cpp` plays a `_`-prefixed animation on the ship |
| `flash_particle_fix` | launcher fx | `cli_projectile_fx.cpp`: the flash on every barrel |
| `print_rep_requirements` | `0x00480739`, `0x004b9010` / `0x004b9462` / `0x004b9545` | `nn_dealer.cpp`, `nn_ship_trader.cpp`: ids 1564 formatted with the required reputation in percent |
| `post_game_deadlock_fix` | DALib `0x065c2215` / `0x065c230c` / `0x065c27ac` / `0x065c598e`; gundll `+0x302ef` | `DALib`: `Close(DPNCLOSE_IMMEDIATE)`, gun release on the calling thread |
| `alchemy_crash_fix` | alchemy `+0x6fdd` / `+0x778d` / `+0x7f4c` | `alchemy_ramp.cpp`: the key scan stops one key earlier |
| `server_filter_crash_fix` | `0x00571592` | `page_server_select.cpp`: no table after the filter dialog -> nothing |
| `server_filter_speed_fix` | slot 13 at `0x005e2120` | `server_filter_dialog.cpp`: the frame timer ticks while the dialog runs |
| `freelancer_dll_crash_fix` | server `0x06d43d6b` / `0x06d43e6d` | `IServerImpl.cpp`: a controller DLL that does not load is skipped |
| `dealer_menu_open_fix` | `0x004417e7` / `0x00441862` | `nav_bar.cpp`: a camera move already running counts as started |
| `dealer_crash_fix` | `0x00441d28`, `0x0043ffb6`, `0x0043e9ca` | `nav_bar.cpp`: no ship dealer click during the room transition, no null `Current` |
| `ship_buy_kick_fix` | server `.text:06d4feeb` | `server_classes.cpp`: equipment of a ship package the base sells is not cheated |
| `hostile_group_formation` | Common `+0x6c37c` | `common_formationbehavior.cpp`: formation with a hostile player of the own group |
| `better_updates` | `0x0054b16d`, `0x0054158c`, `0x00541602`, `0x0054167c` | `client_objdb.cpp`, `player_spawn.cpp`: SPObjUpdate paced 40 ms .. 2 s (750 ms in a lane), on turn or engine kill, with the throttle |

## Not ported

- Keys the mod turns off: `projectiles_sound_fix`, `projectiles_server_fix`, `better_resolutions`,
  `more_test_sounds`, `trade_lane_lights_fix`, `copy_paste_feature`, `slide_ui_anim_fix`,
  `dynamic_solar_infocards`.
- FLSharp features newer than the mod's `FLSharp.dll` (`unhostile_group_members`,
  `group_member_attitude`, cursor and camera fixes, light limit, and the others registered after
  `hostile_group_formation`).

Compiled, not yet run.
