# Переключение языка

[English](../language.md) · **Русский**

Ретейл — один язык на установку. Переведённый мод либо заменяет файлы, либо, как The Nomad
Legacy, держит второй пропатченный `Freelancer_en.exe` (он открывает `Freelan_en.ini` вместо
`Freelancer.ini` и `resour_en.dll` вместо `resources.dll`) и лаунчер, который перед каждым
запуском копирует данные языка поверх `DATA` и меняет DLL плагинов. Порт берёт язык из
`port.ini`, поэтому одна сборка работает на любом языке.

| Свойство (`src/Freelancer.Diagnostics.props`) | Define | По умолчанию в листе |
|---|---|---|
| `FreelancerLanguage` | `FREELANCER_LANGUAGE` (клиент, `Common.dll`) | 1 |

`/p:FreelancerLanguage=0` собирает поведение ретейла.

## Настройки

`port.ini` рядом с `freelancer.exe` (`src/Common/port_config.cpp`, `src/include/port_config.h`):

```ini
[Language]
language = ru            ; ключ командной строки -lang:en важнее

[Language.ru]
freelancer_ini = freelancer.ini
resources = resources.dll

[Language.en]
freelancer_ini = freelan_en_port.ini
resources = ..\EXE\resour_en.dll
```

Язык озвучки выбирается отдельно (см. [Язык озвучки](#язык-озвучки)).

| Ключ | Что заменяет | Порт |
|---|---|---|
| `freelancer_ini` | литерал `"Freelancer.ini"` (`FUN_005621a0`) | `startup_config.cpp`; за ним следует всё, что перечислено в ini клиента: ресурсные DLL, звуки и озвучка, эффекты |
| `resources` | `LoadLibraryA("resources.dll")` в `WinMain` | `main.cpp` |
| `skip_any_cutscene` | устаревшая правка exe | Больше не используется: Esc показывает подтверждение, Enter пропускает сюжетную сцену независимо от языка |

За языком следуют и тексты плагинов: `engclass_resources` (DLL строк engclass) и
`territory_ini` ([adoxa.md](adoxa.md)). Без `[Language] language` каждый ключ берёт имя ретейла.

## Язык озвучки

Язык интерфейса (`[Language] language`: ресурсы, тексты, строки плагинов) и язык озвучки независимы:
можно играть с русским текстом и английскими голосами. Всё настраивается в `port.ini`:

```ini
[Language]
language = ru       ; язык интерфейса; -lang:xx важнее
voice =             ; язык озвучки, пусто = как language; -voice:xx важнее
difficulty = normal ; easy / normal / hard, подставляется в {difficulty}; -difficulty:xx важнее

[Voice]
codes = ru,en       ; суффиксы имён файлов, считающиеся кодами языка

[Voice.en]
data_overlay = ..\BUILDS\EN_{difficulty}\DATA
```

| Ключ | Действие |
|---|---|
| `[Language] voice` | Язык озвучки. Управляет обоими механизмами ниже. |
| `[Voice] codes` | ini в папке `audio` вида `<stem>_<code>.ini` (`sounds_mod_ru.ini`, `voices_static_en.ini`, `story_sounds_gen_ru.ini`) читается как `<stem>_<voice>.ini`, если такой файл есть. В ini клиента может стоять любой язык: отдельный `Freelan_en.ini` ради звука не нужен. |
| `[Voice.<code>] data_overlay` | Папки, устроенные как `DATA` (через запятую, относительно exe; `{difficulty}` превращается в `EASY`/`NORMAL`/`HARD`). ini из `..\DATA\`, который есть в одной из них, читается оттуда. В `BUILDS\<ЯЗЫК>_<СЛОЖНОСТЬ>\DATA` лежат миссии, системы и лодауты с именами реплик (`echo_m01_en`, `voice = ...`): без них английские звуки загружаются, но сюжет всё равно играет русские реплики. `[Language.<code>] data_overlay` читается, если в `[Voice.<code>]` его нет. |

Реализовано в `port_config.cpp` и `INI_Reader::open` (`common_ini.cpp`). Не охвачено:
`BUILDS\<ЯЗЫК>_<СЛОЖНОСТЬ>\EXE` (`newplayer.fl`, `subtitles.xml`, `dacom.ini`) и текстовые файлы вроде
`fx\mod\titles\titles_<code>_ale.ini`, которые следуют за `freelancer_ini`.

## Отклонения

Всё перечисленное есть только в порте; с выключенным свойством клиент как в ретейле.
