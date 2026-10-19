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
skip_any_cutscene = 1

[Language.en]
freelancer_ini = freelan_en_port.ini
resources = ..\EXE\resour_en.dll
data_overlay = ..\BUILDS\EN_NORMAL\DATA
```

| Key | What it replaces | Port |
|---|---|---|
| `freelancer_ini` | the `"Freelancer.ini"` literal (`FUN_005621a0`) | `startup_config.cpp`; everything the client ini lists follows it: resource DLLs, sounds and voices, effects |
| `resources` | `LoadLibraryA("resources.dll")` in `WinMain` | `main.cpp` |
| `data_overlay` | the launcher's copy over `DATA` | `INI_Reader::open` (`common_ini.cpp`): an ini under `..\DATA\` that exists in one of the listed folders (comma separated, relative to the exe) is read from there |
| `skip_any_cutscene` | the Russian exe's `EB 0C` at `0x0045685f` | `gf_script_object.cpp` `FGfScriptManager::OnEvent`: the skip key skips every letterboxed scene |

Plugin texts follow the language too: `engclass_resources` (the engclass string DLL) and
`territory_ini` ([adoxa.md](adoxa.md)). Without `[Language] language` every key falls back to
retail's name.

## Deviations

All of the above is port-only; with the property off the client is retail's.
