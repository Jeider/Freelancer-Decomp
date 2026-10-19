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
skip_any_cutscene = 1

[Language.en]
freelancer_ini = freelan_en_port.ini
resources = ..\EXE\resour_en.dll
data_overlay = ..\BUILDS\EN_NORMAL\DATA
```

| Ключ | Что заменяет | Порт |
|---|---|---|
| `freelancer_ini` | литерал `"Freelancer.ini"` (`FUN_005621a0`) | `startup_config.cpp`; за ним следует всё, что перечислено в ini клиента: ресурсные DLL, звуки и озвучка, эффекты |
| `resources` | `LoadLibraryA("resources.dll")` в `WinMain` | `main.cpp` |
| `data_overlay` | копирование лаунчером поверх `DATA` | `INI_Reader::open` (`common_ini.cpp`): ini из `..\DATA\`, который есть в одной из перечисленных папок (через запятую, относительно exe), читается оттуда |
| `skip_any_cutscene` | `EB 0C` русского exe по `0x0045685f` | `gf_script_object.cpp` `FGfScriptManager::OnEvent`: клавиша пропуска пропускает любую сцену с полосами |

За языком следуют и тексты плагинов: `engclass_resources` (DLL строк engclass) и
`territory_ini` ([adoxa.md](adoxa.md)). Без `[Language] language` каждый ключ берёт имя ретейла.

## Отклонения

Всё перечисленное есть только в порте; с выключенным свойством клиент как в ретейле.
