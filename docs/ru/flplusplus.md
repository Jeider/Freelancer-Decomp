# Поведение flplusplus.dll

[English](../flplusplus.md) · **Русский**

[flplusplus](https://github.com/TheStarport/flplusplus) (TheStarport; BSD-2-Clause) — клиентский
плагин, который патчит retail `freelancer.exe`, `common.dll`, `soundmanager.dll` и
`soundstreamer.dll` по жёстко заданным адресам, поэтому порт загрузить его не может. Его поведение
переписано в модулях, которые он патчит, по его исходникам (master `d773ea8`, 2024-08-10), включая
встроенный в него WheelScroll от adoxa.

| Свойство (`src/Freelancer.Diagnostics.props`) | Define | По умолчанию в листе |
|---|---|---|
| `FreelancerFlplusplus` | `FREELANCER_FLPLUSPLUS` (клиент и `Common.dll`) | 1 |

`/p:FreelancerFlplusplus=0` собирает retail-поведение.

## Настройки

`flplusplus.ini` рядом с `freelancer.exe` (папка `bin\` порта), читает `Common.dll`
(`FlplusplusGetConfig`, `src/include/common_flplusplus.h`); ключи и значения по умолчанию как у
плагина:

```ini
[flplusplus]
lod_scale = 1                    ; дальности смены LOD и дальность прорисовки объектов (10000 м)
pbubble_scale = 1                ; дальности pbubble у эффектов
character_detail_scale = 1       ; дальности смены детализации частей персонажей
save_folder_name = Freelancer    ; Документы\My Games\<имя>
save_in_directory = false        ; true: EXE\..\SAVE
screenshots_folder_name = FreelancerShots ; Изображения\<имя>
screenshots_in_directory = false ; true: EXE\..\SCREENSHOTS
ship_preview_scrolling_speed = 2 ; зум колесом в превью корабля, 0..50 (0 — выкл.)
ship_preview_scrolling_inverse = false
```

Масштаб вне 1..1000000 оставляет retail-значение, как у плагина.

## Перенесено

| flplusplus | В retail | В порте |
|---|---|---|
| `lod_scale` (`patch_lodranges`) | чтение `LODranges` в `0x00402383`; `DAT_00613ec8` = 10000 | `client_cliobj.cpp` (дальности × масштаб), `space_scene_obj_draw.cpp` (радиус выборки объектов × масштаб) |
| `pbubble_scale` | два чтения в `0x004fd82c` / `0x004fd839` | `effect_type_info.cpp` |
| `character_detail_scale` | чтение `DetailSwitchTable` в Common `0x062fefb1` | `Common/common_costume.cpp` |
| Папка сохранений (обход `GetUserDataPath`) | `My Games\Freelancer` | `Common/common_misc.cpp` |
| Папка скриншотов (обход `GetScreenShotPath`) и PNG-скриншоты (`OnScreenshot`) | `Изображения\FreelancerShots\screenN.BMP` (`FUN_00425170`) | `common_misc.cpp`, `flplusplus.cpp`: `ГГГГ-ММ-ДД_ЧЧ-ММ-СС[_N].png`; кадр берётся через PrintScreen конвейера (GDI-копия рабочего стола у плагина не видит полноэкранную поверхность Direct3D) и перекодируется через GDI+ |
| Приватные шрифты, `DATA\FONTS\fonts.ini` `[FontFiles] path = …` | — | `flplusplus.cpp` (`AddFontResourceEx(FR_PRIVATE)` при запуске) |
| Метки времени в FLSpew (`patch_fdump`) | — | `flplusplus.cpp`: указатель `FDUMP` оборачивается после открытия лога |
| Замена шрифта по умолчанию «Vibrocentric» | Common `+0x143dc0` | `Common/common_textrender.cpp` |
| Исправление размера текстур (`0x0041ad6f`: `0x80` → `0x2000`) | группа текстур | `client_cliobj.cpp` |
| Отключён диалог неподдерживаемой видеокарты (`0x005b16fc`) | предупреждение о слабом компьютере | `engine_init.cpp` |
| Зум колесом в превью корабля (`ShipPreviewWindowScroll`, слот 18 у `0x005e4bcc`) | — | `ShipViewControl::Slot18`: камера +0x64 (кэш z вида) ± скорость |
| WheelScroll (adoxa): колесо мыши в списках и текстах (слот 18 у десяти vftable) | — | `Win3D::Slot18` ровно у этих классов → `FlplusplusWindowWheel`; `UiScroll::WheelStep` (два шага стрелки за щелчок) |

Колесо сравнивается по знаку (плагины сравнивают с ±1, поэтому несколько щелчков за кадр ничего
не делали).

## Не перенесено

- Патчи только для лога: «Failed to get start location» (`remove_start_location_warning`) и
  предупреждения MP3-кодека в SoundManager / SoundStreamer.
- `log_to_console` (окно консоли для лога).
- Режим THN-плеера (`-thn`).
- Экспорт поздних хуков плагина (`flplusplus_add_latehook`) для других плагинов.

Состояние: собрано (VS 2026, v145); в игре ещё не проверено. См.
[re/deviations.md](re/deviations.md) (FLPLUSPLUS).
