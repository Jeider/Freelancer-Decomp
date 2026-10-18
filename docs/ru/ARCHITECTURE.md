# Обзор архитектуры

[English](../ARCHITECTURE.md) · **Русский**

Карта порта на одну страницу для того, кто только что склонировал репозиторий: из чего он
состоит, как запускается, как части общаются между собой и где читать дальше. Здесь — сводка
модульных документов из [re/](re/); при расхождении прав модульный документ.

## Общая картина

Freelancer — это не одна программа, а `freelancer.exe` плюс около тридцати DLL, которые находят
друг друга во время работы. Порт пересобирает каждую из них из `src/` в `bin\`, сохраняя
retail-имена модулей, экспорты и раскладку интерфейсов, чтобы каждый модуль можно было
сравнивать с его retail-аналогом отдельно.

```
                       freelancer.exe  (src/freelancer — меню, космос, HUD, UI)
                              │
         ┌────────────────────┼─────────────────────────────┐
         │ линкуется с        │ интерфейсы DACOM            │ IServer / IClient
         ▼ Common.lib         ▼                             ▼
   Common.dll           движковые DLL                rpclocal.dll (SP)  ── или ──  RemoteServer.dll (MP)
   (+ IVP, qhull)       dacom → DALib → ReadFile,          │                            │ DirectPlay 8
   объекты, INI,        x86math, EngBase, system,          ▼                            ▼
   физика, сеть         RP8/RP9, Shading, RendComp,    Server.dll ◄── Content.dll    FLServer.exe
                        alchemy, Thorn, Deformable2,   (логика мира)  (миссии, ИИ,   + RemoteClient.dll
                        SoundManager, SoundStreamer…                   популяторы)
```

Плюс ресурсные DLL (`resources`, `InfoCards`, `MiscText`, … — таблицы строк и HTML-инфокарты,
собираются `rc.exe` из `src/Resources/`).

## Слои

| Слой | Модули | Что даёт | Читать |
|------|--------|----------|--------|
| Ядро компонентов | `dacom`, `DALib` | `COManager`: COM-подобный реестр именованных компонентов, загрузчик библиотек по `bin\DACOM.INI`, встроенный INI-парсер, журнал (`FDUMP`) | [dacom](re/dacom.md), [dalib](re/dalib.md) |
| Платформенные сервисы | `ReadFile`, `x86math`, `system`, `zlib` | файловая система и пути поиска, 3D-математика, системный контейнер | [readfile](re/readfile.md), [x86math](re/x86math.md), [system](re/system.md) |
| Сцена и анимация | `EngBase`, `Deformable2`, `Thorn` | архетипы, хардпойнты, каналы анимации, скиннинг; скрипты роликов `.thn` на Lua 3.2 | [engbase](re/engbase.md), [deformable2](re/deformable2.md), [thorn](re/thorn.md) |
| Рендер | `RP8` (D3D8), `RP9` (необязательный D3D9), `Shading`, `RendComp`, `alchemy`, `ximage`, `flmaterials` | устройство и конвейер, текстуры и материалы, меши, частицы | [render](re/render.md), [shading](re/shading.md), [alchemy](re/alchemy.md), [rp9](re/rp9.md) |
| Звук и медиа | `SoundManager`, `SoundStreamer`, `movie`, `imeui` | эффекты DirectSound, потоковая музыка и речь, вступительное видео, IME | [audio](re/audio.md), [movie](re/movie.md), [imeui](re/imeui.md) |
| Общий игровой рантайм | `Common` (+ физика `IVP`, `qhull`) | ~3,9 тыс. экспортов: игровые объекты, архетипы, чтение INI, поведения ИИ, сетевые примитивы | [common](re/common.md), [common_archetype](re/common_archetype.md), [common_physys](re/common_physys.md) |
| Игровая логика | `Server`, `Content` | симуляция мира; миссии, ИИ, встречи и популяторы поверх `pub::*` | [server](re/server.md), [content](re/content.md) |
| Транспорт | `rpclocal`, `RemoteServer`, `RemoteClient`, `RemoteCommon` | вызовы `IServer`/`IClient` — внутри процесса в одиночной игре или по DirectPlay в сетевой | [rpclocal](re/rpclocal.md), [server](re/server.md) |
| Фронтенд | `freelancer.exe`, `FLServer.exe` | клиентский UI и игровой цикл; MFC-оболочка выделенного сервера | [freelancer](re/freelancer.md), [winmain](re/winmain.md) |

Полная таблица модулей с указанием, какую retail-DLL заменяет каждая папка, —
[re/dll_inventory.md](re/dll_inventory.md).

## Как модули находят друг друга

- **Компоненты DACOM.** Движковые DLL регистрируют именованные фабрики в `COManager`, когда
  загрузчик поднимает их из списка `[Libraries]` в `bin\DACOM.INI`. Потребители запрашивают
  интерфейсы по имени (`IRenderer`, `IAlchemy`, `IFileSystem`, …) и вызывают их через vtable.
  `DllPath = .\` гарантирует, что грузятся только DLL порта из `bin\`.
- **Обычные импорты.** `Common.dll`, `Server.dll` и ещё несколько — обычные C++-DLL с тысячами
  декорированных экспортов; потребители линкуются с их import-библиотеками.
- **Общие заголовки.** Каждый тип, пересекающий границу DLL, объявлен один раз в `src/include/`
  (`<module>.h`, `common_*.h`, `server_*.h`). Порядок виртуальных методов там и *есть* ABI — как
  опознавать и записывать слоты, описано в [re/cross_dll_protocol.md](re/cross_dll_protocol.md).
- **Content-модули.** `Content.dll` загружается несколько раз в разных ролях (`GameSupport`,
  `SpaceSupport`, `BaseSupport`, `SpacePop`, …) из `[Initial SP DLLs]` / `[Initial MP DLLs]` в
  `bin\freelancer.ini`.

## Запуск вкратце

1. `WinMain` (`src/freelancer/Client/main.cpp`): мьютекс единственного экземпляра, переход в
   папку exe, проверка `..\DATA`, EULA (`..\EBUEula.dll`).
2. `freelancer.ini`, параметры экрана, создание окна.
3. `InitializeEngine`: `DALib::Startup` грузит `[Libraries]`, проверяется наличие обязательных
   компонентов, затем таймеры, конвейер рендера и `DataConfig::startup` (архетипы, вселенная,
   товары).
4. Начало игры поднимает `Server.dll` через `rpclocal.dll` (одиночная игра) или подключается через
   `RemoteServer.dll` (сетевая); сервер загружает Content-модули.
5. Игровой цикл чередует `UpdateClientTiming` и обработку сообщений.

Подробности и retail-адреса: [re/winmain.md](re/winmain.md).

## Одиночная игра — это клиент/сервер

Даже офлайн клиент не трогает мир напрямую: каждое действие идёт через `IServer` (клиент →
сервер, 92 метода), каждое обновление возвращается через `IClient` (сервер → клиент, 126 слотов).
В одиночной игре `rpclocal.dll` сериализует эти вызовы в пакеты и очереди внутри процесса; в
сетевой те же вызовы идут по DirectPlay. Обратите внимание на путаные retail-имена:
`RemoteServer.dll` грузит *клиент*, `RemoteClient.dll` — *сервер*.

## Дерево исходников

Примерный объём рукописного кода (`.cpp/.h/.c`, без вендорного), октябрь 2026 — всего около
775 тыс. строк:

| Папка | тыс. строк | Папка | тыс. строк |
|-------|-----:|-------|-----:|
| `freelancer` | 234 | `Shading` | 11 |
| `Common` | 106 | `RP9` | 11 |
| `Content` | 79 | `EngBase` | 10 |
| `include` (общий ABI) | 57 | `RendComp` | 10 |
| `IVP` | 50 | `Deformable2` | 9 |
| `Server` | 40 | `RP8` | 9 |
| `rpclocal` | 28 | `luaprofile` | 8 |
| `Thorn` | 26 | `FLServer` | 7 |
| `alchemy` | 25 | остальные | < 6 каждая |
| `movie` | 15 | | |

В `src/Resources/` лежат тексты ресурсных DLL (≈5 000 файлов `.txt`: строки и инфокарты).

## Система сборки

- Одно решение `src/Freelancer.sln`, по одному `.vcxproj` на модуль, всё `Win32`, toolset v143,
  C++17.
- Общие настройки — в `src/Directory.Build.props` / `.targets`: папки вывода, пути к DirectX SDK
  (`Dx8SdkDir`, `Dx9SdkDir`) и **x87-арифметика** (`/arch:IA32`), чтобы побитово совпадать с
  retail-модулями, собранными VC6.
- Возможности порта — свойства MSBuild в `src/Freelancer.Diagnostics.props`, превращаемые в
  define'ы `FREELANCER_*` (широкий экран, ходьба, RP9, надпись Beta, профайлер кадра).
- Конфигурации: `Release` → `bin\`, `Debug` → `bin_debug\`, `DebugASan` → `binasan\`. Debug и ASan
  копируют INI-файлы из `bin\` (`src/copy_dev_ini.py`); править их нужно в `bin\`.

## Правила верности оригиналу одним абзацем

Порт следует retail-дизассемблеру функция за функцией; комментарии содержат retail-адреса
(`FUN_005b2f50`, `.text:06d06bb4`). Всё, что порт делает иначе, — *отклонение* и должно быть
записано в [re/deviations.md](re/deviations.md) с причиной и условием снятия. Код, который
«доводит картинку» механизмом, которого в retail нет, — *подмена*, и она считается долгом, а не
прогрессом ([re/substitutions.md](re/substitutions.md)). Возможности, которых нет в оригинале,
остаются за переключателями сборки.

## Что читать дальше

- [ini/README.md](ini/README.md) — все INI-файлы, секции и ключи, которые читает код.
- [re/crt_compat.md](re/crt_compat.md) — современные CRT/STL против retail-рантайма VC6.
- [re/refactoring.md](re/refactoring.md) — правила рефакторинга читаемости.
- [memory_diagnostics.md](memory_diagnostics.md) — поиск утечек памяти.
- [../../CONTRIBUTING.ru.md](../../CONTRIBUTING.ru.md) — как внести изменение.
