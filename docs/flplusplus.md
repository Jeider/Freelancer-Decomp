# flplusplus.dll behaviour

**English** · [Русский](ru/flplusplus.md)

[flplusplus](https://github.com/TheStarport/flplusplus) (TheStarport; BSD-2-Clause) is a client
plugin that patches retail `freelancer.exe`, `common.dll`, `soundmanager.dll` and
`soundstreamer.dll` at hardcoded addresses, so the port cannot load it. Its behaviour is
rewritten in the modules it patches, from its sources (master `d773ea8`, 2024-08-10), including
adoxa's WheelScroll that it bundles.

| Property (`src/Freelancer.Diagnostics.props`) | Define | Sheet default |
|---|---|---|
| `FreelancerFlplusplus` | `FREELANCER_FLPLUSPLUS` (client and `Common.dll`) | 1 |

`/p:FreelancerFlplusplus=0` builds the retail behaviour.

## Settings

`flplusplus.ini` next to `freelancer.exe` (the port's `bin\`), read by `Common.dll`
(`FlplusplusGetConfig`, `src/include/common_flplusplus.h`) with the plugin's keys and defaults:

```ini
[flplusplus]
lod_scale = 1                    ; LOD switch ranges and object render distance (10000 m)
pbubble_scale = 1                ; effect pbubble ranges
character_detail_scale = 1       ; body part detail switch distances
save_folder_name = Freelancer    ; Documents\My Games\<name>
save_in_directory = false        ; true: EXE\..\SAVE
screenshots_folder_name = FreelancerShots ; Pictures\<name>
screenshots_in_directory = false ; true: EXE\..\SCREENSHOTS
ship_preview_scrolling_speed = 2 ; wheel zoom in ship previews, 0..50 (0 disables)
ship_preview_scrolling_inverse = false
```

A scale outside 1..1000000 keeps the retail value, as in the plugin.

## Ported

| flplusplus | Retail place | Port |
|---|---|---|
| `lod_scale` (`patch_lodranges`) | `LODranges` read at `0x00402383`; `DAT_00613ec8` = 10000 | `client_cliobj.cpp` (ranges × scale), `space_scene_obj_draw.cpp` (object query radius × scale) |
| `pbubble_scale` | the two reads at `0x004fd82c` / `0x004fd839` | `effect_type_info.cpp` |
| `character_detail_scale` | `DetailSwitchTable` read at Common `0x062fefb1` | `Common/common_costume.cpp` |
| Save folder (`GetUserDataPath` detour) | `My Games\Freelancer` | `Common/common_misc.cpp` |
| Screenshot folder (`GetScreenShotPath` detour) and PNG screenshots (`OnScreenshot`) | `Pictures\FreelancerShots\screenN.BMP` (`FUN_00425170`) | `common_misc.cpp`, `flplusplus.cpp`: `YYYY-MM-DD_HH-MM-SS[_N].png`; the frame comes from the pipeline's PrintScreen (the plugin's GDI desktop copy does not see a fullscreen Direct3D surface) and is re-encoded with GDI+ |
| Private fonts, `DATA\FONTS\fonts.ini` `[FontFiles] path = …` | — | `flplusplus.cpp` (`AddFontResourceEx(FR_PRIVATE)` at start-up) |
| FLSpew timestamps (`patch_fdump`) | — | `flplusplus.cpp`: the `FDUMP` pointer wrapped after the spew log opens |
| "Vibrocentric" default font replaced | Common `+0x143dc0` | `Common/common_textrender.cpp` |
| Texture size fix (`0x0041ad6f`: `0x80` → `0x2000`) | texture group override | `client_cliobj.cpp` |
| Unsupported video dialog disabled (`0x005b16fc`) | low-machine warning dialog | `engine_init.cpp` |
| Ship preview wheel zoom (`ShipPreviewWindowScroll`, slot 18 of `0x005e4bcc`) | — | `ShipViewControl::Slot18`: camera +0x64 (cached view z) ± speed |
| WheelScroll (adoxa): mouse wheel in lists and texts (slot 18 of ten vftables) | — | `Win3D::Slot18` for exactly those classes → `FlplusplusWindowWheel`; `UiScroll::WheelStep` (two held-arrow steps per notch) |

The wheel value is compared by its sign (the plugins compare with ±1, so a multi-notch value
did nothing).

## Not ported

- Log-only patches: "Failed to get start location" (`remove_start_location_warning`) and the MP3
  codec warnings of SoundManager / SoundStreamer.
- `log_to_console` (a console window for the spew).
- THN player mode (`-thn`).
- The plugin's late-hook export (`flplusplus_add_latehook`) for other plugins.

Status: compiled (VS 2026, v145); not yet tested in game. See [re/deviations.md](re/deviations.md)
(FLPLUSPLUS).
