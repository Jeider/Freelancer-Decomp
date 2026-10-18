# jflp.dll behaviour

**English** · [Русский](ru/jflp.md)

Jason Hood's `jflp.dll` (the code part of Jason's Freelancer Patch) patches retail
`freelancer.exe`, `common.dll`, `rendcomp.dll` and `thorn.dll` in memory at hardcoded addresses,
so the port cannot load it (see [re/dll_inventory.md](re/dll_inventory.md)). Its behaviour is
rewritten as C++ in the functions it patches, from the author's published source (`jflp.c`,
v1.27) checked against the retail listing; the installed v1.25 DLL has the same patches except
the v1.26–1.27 additions marked below.

| Property (`src/Freelancer.Diagnostics.props`) | Define | Sheet default |
|---|---|---|
| `FreelancerJflp` | `FREELANCER_JFLP` (client and `Common.dll`) | 1 |

`src/Directory.Build.props` sets 0 for projects without the sheet; `/p:FreelancerJflp=0` builds
the retail behaviour.

## Ported

| jflp | Retail place | Port |
|---|---|---|
| Stats for Powerplants, Engines, Scanners, Tractor Beams, Armor (`Stats`, jump tables at `0x0047c21f` / `0x004840c9`) | `FUN_0047c0xx` info card, `FUN_00484090` | `nn_inventory.cpp` (two-column card for the five classes), `dealer_equip_stats.cpp` (`BuildJflpStats`); a name with a non-breaking space (Alt+0160) shows "n/a" |
| Blank line after "Stats" (`0x0047c355` / `0x0047c501` → `L"\n\n"`) | info card panes 2 and 3 | `nn_inventory.cpp` |
| Sector letter first, "Sector C4" (`ADDR_LETTER1..3`) | `FUN_0048dc10`, `%Z` in `FUN_0041c9xx` and `FUN_004ba9xx` | `hud_target.cpp`, `misc_util.cpp`, `ids_strings.cpp` |
| En dash in the trade lane / chat arrow (`DAT_005cef58`) | `L"->"` | `L"–>"`: `hud_target.cpp`, `chat_text_input.cpp` |
| Alt+Enter: `USER_FULLSCREEN` toggles windowed mode (`ToggleFullScreen`) | registered, never handled (`0x005b2497`) | `main_command_handler.cpp`: the mode with the fullscreen flag flipped through `FUN_004249c0` |
| Roll during mouse flight (`Roll_Hook`) | mouse flight sends roll 0 (`0x004c7f10`) | `player_behavior.cpp`: the roll of the roll keys (keyboard direction `(-0, -0, z)`) is sent |
| 8-way strafe (`SetStrafe`, table at `0x062bb9b6`) | `CStrafeEngine` left / right / up / down | `common_csteering.cpp`: a second key across the held one gives a diagonal (5..8), pushed as up/down plus left/right for one power drain |
| Server info of other versions (`Connect_Hook`, `ConnectDbl_Hook`, `0x005711a1`) | rows of another version not selectable | `page_server_select.cpp`: every row selectable, Connect disabled and double click ignored for another version |
| First weapon group active on entering space (v1.26) | `0x004db66c..0x004db6b9` | `hud_status_core.cpp`: group 0 made current and activated |
| `fovx` in `cameras.ini` ignored unless it ends in `!` (`Fovx_Hook`) | `atof` of the value (`0x0040f617`) | `space_camera.cpp`: 54.432 for `[WinCamera]`, 70 for the other cameras; `fovx = 80!` keeps 80. The value is the 4:3 angle; the Hor+ mode widens it (jflp's `calc_fovx`) |
| LOD ranges for the widened FOV (v1.27, `FOVX_LOD`) | `DAT_005c7410` = tan 35° | `client_cliobj.cpp`: times the Hor+ factor (with `FreelancerWidescreenSupport`) |

## Not ported

- **The rest of jflp's widescreen** (fonts, mouse, Nav Map, ticker, crosshair, contact list
  clipping, cinematic ratio, thorn `fovh`, desktop resolution). The port has its own Hor+ mode,
  `FreelancerWidescreenSupport` ([hd_edition.md](hd_edition.md)), which covers the same
  (fonts are chosen by the 4:3 width of the same height) and replaces HudShift. The option
  `nofovx` does not exist.
- **Log-only patches**: the FLSpew warnings "couldnt find material 163618903", "get_zone(N)
  failed", "FATE_UNKNOWN", "Used Hostile Pick Assistance", "ArchDB::Get", "cockpit aspect", and
  the `Deform::start_aim` timestamp.
- **MultiCruise cruise speed** in the engine stats: MultiCruise.dll cannot be loaded either; the
  line stays blank as jflp leaves it without that DLL.
- **Options** `nostats`, `no4way`, `no8way` (read from the `dacom.ini` line): the port uses the
  defaults (stats on, 8-way strafe); build with `FreelancerJflp=0` for retail.

## Data

The IDS strings the stats use (945, 1695–1699, 1703, 1745, 1753, 1755, 1758–1764) are in the port's
`resources.dll`. The JFLP data fixes (`DATA\…`, the text DLLs) are data: install them into
your `DATA` / point `[Resources]` at them as with the original game.

Status: compiled (VS 2026, v145); not yet tested in game. See
[re/deviations.md](re/deviations.md) (JFLP).
