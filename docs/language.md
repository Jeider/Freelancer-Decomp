# Language switch

**English** · [Русский](ru/language.md)

Retail ships one language per installation. A translated mod either replaces the files or, like
The Nomad Legacy, keeps a second byte-patched `Freelancer_en.exe` (it opens `Freelan_en.ini`
instead of `Freelancer.ini` and `resour_en.dll` instead of `resources.dll`) and a launcher that
copies per-language data over `DATA` and swaps plugin DLLs before each start. The port reads
the language from `port.ini`, so one build runs every language.

| Property (`src/Freelancer.Diagnostics.props`) | Define | Sheet default |
|---|---|---|
| `FreelancerLanguage` | `FREELANCER_LANGUAGE` (client, `Common.dll`) | 1 |

`/p:FreelancerLanguage=0` builds the retail behaviour.

## Settings

`port.ini` next to `freelancer.exe` (`src/Common/port_config.cpp`, `src/include/port_config.h`):

```ini
[Language]
language = ru            ; -lang:en on the command line wins

[Language.ru]
freelancer_ini = freelancer.ini
resources = resources.dll

[Language.en]
freelancer_ini = freelan_en_port.ini
resources = ..\EXE\resour_en.dll
```

The voice-over language is chosen separately (see [Voice-over language](#voice-over-language)).

| Key | What it replaces | Port |
|---|---|---|
| `freelancer_ini` | the `"Freelancer.ini"` literal (`FUN_005621a0`) | `startup_config.cpp`; everything the client ini lists follows it: resource DLLs, sounds and voices, effects |
| `resources` | `LoadLibraryA("resources.dll")` in `WinMain` | `main.cpp` |
| `skip_any_cutscene` | obsolete executable patch | Ignored: active story scenes now use Esc to show confirmation and Enter to skip, independently of language |

Plugin texts follow the language too: `engclass_resources` (the engclass string DLL) and
`territory_ini` ([adoxa.md](adoxa.md)). Without `[Language] language` every key falls back to
retail's name.

## Voice-over language

The interface language (`[Language] language`: resources, text, plugin strings) and the voice-over
language are independent, so Russian text with English voices works. Everything is in `port.ini`:

```ini
[Language]
language = ru       ; interface language; -lang:xx wins
voice =             ; voice-over language, empty = same as language; -voice:xx wins
difficulty = normal ; easy / normal / hard, fills {difficulty} below; -difficulty:xx wins

[Voice]
codes = ru,en       ; file-name suffixes treated as language codes

[Voice.en]
data_overlay = ..\BUILDS\EN_{difficulty}\DATA
```

| Key | Effect |
|---|---|
| `[Language] voice` | The voice-over language. It drives both mechanisms below. |
| `[Voice] codes` | An ini under an `audio` folder named `<stem>_<code>.ini` (`sounds_mod_ru.ini`, `voices_static_en.ini`, `story_sounds_gen_ru.ini`) is read as `<stem>_<voice>.ini` when that file exists. The client ini may list either language: no separate `Freelan_en.ini` is needed for sound. |
| `[Voice.<code>] data_overlay` | Folders laid out like `DATA` (comma separated, relative to the exe; `{difficulty}` becomes `EASY`/`NORMAL`/`HARD`). An ini under `..\DATA\` that exists in one of them is read from there. The launcher's `BUILDS\<LANG>_<DIFFICULTY>\DATA` carries the missions, systems and loadouts that name the voice lines (`echo_m01_en`, `voice = ...`), so without it English sounds load but the story still plays Russian lines. A `[Language.<code>] data_overlay` is still read when `[Voice.<code>]` has none. |

Implemented in `port_config.cpp` and `INI_Reader::open` (`common_ini.cpp`). Not covered:
`BUILDS\<LANG>_<DIFFICULTY>\EXE` (`newplayer.fl`, `subtitles.xml`, `dacom.ini`), and text-side files such as
`fx\mod\titles\titles_<code>_ale.ini`, which follow `freelancer_ini`.

## Deviations

All of the above is port-only; with the property off the client is retail's.
