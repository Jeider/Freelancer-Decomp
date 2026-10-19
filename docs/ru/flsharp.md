# Поведение FLSharp.dll

[English](../flsharp.md) · **Русский**

[FLSharp](https://github.com/BC46/FLSharp) (BC46; MIT) — плагин клиента и сервера. Он патчит
retail `freelancer.exe`, `common.dll`, `server.dll`, `engbase.dll`, `alchemy.dll`, `dalib.dll` и
`gundll.dll` по жёстко заданным адресам, поэтому порт не может его загрузить. Его исправления
переписаны в тех модулях, которые он патчит, по его исходникам.

| Свойство (`src/Freelancer.Diagnostics.props`) | Define | По умолчанию в листе |
|---|---|---|
| `FreelancerFlsharp` | `FREELANCER_FLSHARP` (клиент, `Common.dll`, `Server.dll`, `EngBase.dll`, `alchemy.dll`, `DALib.dll`) | 1 |

`/p:FreelancerFlsharp=0` собирает поведение retail.

## Настройки

`FLSharp.ini` рядом с `freelancer.exe` (`bin\` порта) — собственный файл плагина: каждая
строка `name = true/false` любой секции. Отсутствующий ключ значит «включено», как в плагине.
Файл читает `Common.dll` (`FlsharpFeatureEnabled`, `src/include/common_flsharp.h`);
`EngBase.dll`, `alchemy.dll` и `DALib.dll` не линкуются с `Common.dll` и читают свой ключ из
`[FLSharp]` сами.

## Перенесено

Это исправления, которые включает `FLSharp.ini` мода.

| Ключ | Место в retail | Порт |
|---|---|---|
| `flight_controls_fix` | освобождение на `0x0054b8b9` | `player_spawn.cpp`: при появлении корабля переключатель выравнивания камеры (third-person +0x13c) и автовыравнивание в HUD берутся из менеджера поведения корабля |
| `save_crash_fix` | `0x00487ebf`; сервер `.text:06d4766e` | `nn_load_save.cpp` (неизвестный корабль — ids 0), `Server/server_savegame.cpp` (сейв с неизвестным кораблём пропускает группы столкновений) |
| `blank_faction_fix` | Current Information | `nn_help.cpp`: `fc_uk_grp` (197510) показывается как «None» (3022) |
| `shield_capacity_fix` | характеристики щита | `dealer_equip_stats.cpp`: ёмкость за вычетом `offline_threshold` |
| `waypoint_fixes` | путевая точка HUD; карта `0x00493a00` / `0x00493b21` | `hud_waypoint.cpp` (достигаются только точки текущей системы), `nn_navmap_input.cpp` (свой маркер не цель путевой точки) |
| `waypoint_name_fixes` | `0x004e4094`, `0x004755b8`, `0x00475676`, `0x004e8131`, `0x00475a6c`, `0x00475a94` | `hud_target*.cpp`, `nn_help.cpp`: путевые точки не «Unknown Object», миссионные называются «Mission Waypoint», «PLAYER WAYPOINT n» с собственным номером, цель случайной миссии показывается |
| `weapon_anim_fix` | `0x0661b83f` | `EngBase.cpp` привязывает канал к корпусу; `cli_projectile_fx.cpp` проигрывает анимацию с `_` в начале на корабле |
| `flash_particle_fix` | эффекты пусковой | `cli_projectile_fx.cpp`: вспышка на каждом стволе |
| `print_rep_requirements` | `0x00480739`, `0x004b9010` / `0x004b9462` / `0x004b9545` | `nn_dealer.cpp`, `nn_ship_trader.cpp`: ids 1564 форматируется требуемой репутацией в процентах |
| `post_game_deadlock_fix` | DALib `0x065c2215` / `0x065c230c` / `0x065c27ac` / `0x065c598e`; gundll `+0x302ef` | `DALib`: `Close(DPNCLOSE_IMMEDIATE)`, освобождение gun на вызывающем потоке |
| `alchemy_crash_fix` | alchemy `+0x6fdd` / `+0x778d` / `+0x7f4c` | `alchemy_ramp.cpp`: поиск ключа останавливается на ключ раньше |
| `server_filter_crash_fix` | `0x00571592` | `page_server_select.cpp`: нет таблицы после диалога фильтра — ничего не делается |
| `server_filter_speed_fix` | слот 13 на `0x005e2120` | `server_filter_dialog.cpp`: таймер кадра тикает, пока открыт диалог |
| `freelancer_dll_crash_fix` | сервер `0x06d43d6b` / `0x06d43e6d` | `IServerImpl.cpp`: незагрузившаяся DLL контроллера пропускается |
| `dealer_menu_open_fix` | `0x004417e7` / `0x00441862` | `nav_bar.cpp`: уже идущий пролёт камеры считается начатым |
| `dealer_crash_fix` | `0x00441d28`, `0x0043ffb6`, `0x0043e9ca` | `nav_bar.cpp`: клик по продавцу кораблей во время перехода между комнатами не запоминается, нет обращения к нулевому `Current` |
| `ship_buy_kick_fix` | сервер `.text:06d4feeb` | `server_classes.cpp`: снаряжение из пакета корабля, продаваемого базой, не считается читом |
| `hostile_group_formation` | Common `+0x6c37c` | `common_formationbehavior.cpp`: строй с враждебным игроком своей группы |
| `better_updates` | `0x0054b16d`, `0x0054158c`, `0x00541602`, `0x0054167c` | `client_objdb.cpp`, `player_spawn.cpp`: SPObjUpdate не чаще 40 мс и не реже 2 с (750 мс в торговом пути), при повороте и engine kill, с тягой |

## Не перенесено

- Ключи, выключенные в моде: `projectiles_sound_fix`, `projectiles_server_fix`,
  `better_resolutions`, `more_test_sounds`, `trade_lane_lights_fix`, `copy_paste_feature`,
  `slide_ui_anim_fix`, `dynamic_solar_infocards`.
- Функции FLSharp новее `FLSharp.dll` мода (`unhostile_group_members`, `group_member_attitude`,
  исправления курсора и камеры, лимит источников света и остальные, зарегистрированные после
  `hostile_group_formation`).

Собрано, не запускалось.
