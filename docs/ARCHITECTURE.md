# Architecture overview

**English** · [Русский](ru/ARCHITECTURE.md)

A one-page map of the port for someone who has just cloned the repository: what the pieces are, how
they start up and talk to each other, and where to read further. Facts here are a summary of the
module documents in [re/](re/); when they disagree, the module document is right.

## The big picture

Freelancer is not one program but `freelancer.exe` plus about thirty DLLs that find each other at
run time. The port rebuilds every one of them from `src/` into `bin\`, keeping the retail module
names, exports and interface layouts, so that each module can be compared with its retail
counterpart on its own.

```
                       freelancer.exe  (src/freelancer — menus, space, HUD, UI)
                              │
         ┌────────────────────┼─────────────────────────────┐
         │ links Common.lib   │ DACOM interfaces            │ IServer / IClient
         ▼                    ▼                             ▼
   Common.dll           engine DLLs                  rpclocal.dll (SP)  ── or ──  RemoteServer.dll (MP)
   (+ IVP, qhull)       dacom → DALib → ReadFile,          │                            │ DirectPlay 8
   objects, INI,        x86math, EngBase, system,          ▼                            ▼
   physics, net         RP8/RP9, Shading, RendComp,    Server.dll ◄── Content.dll    FLServer.exe
                        alchemy, Thorn, Deformable2,   (world logic)  (missions, AI,  + RemoteClient.dll
                        SoundManager, SoundStreamer…                   populators)
```

Plus the resource-only DLLs (`resources`, `InfoCards`, `MiscText`, … — string tables and HTML
infocards, built by `rc.exe` from `src/Resources/`).

## Layers

| Layer | Modules | What it provides | Read |
|-------|---------|------------------|------|
| Component core | `dacom`, `DALib` | `COManager`: a COM-like registry of named components, the library loader driven by `bin\DACOM.INI`, the built-in INI parser, logging (`FDUMP`) | [dacom](re/dacom.md), [dalib](re/dalib.md) |
| Platform services | `ReadFile`, `x86math`, `system`, `zlib` | file system and search paths, 3D math, system container | [readfile](re/readfile.md), [x86math](re/x86math.md), [system](re/system.md) |
| Scene and animation | `EngBase`, `Deformable2`, `Thorn` | archetypes, hardpoints, animation channels, skinning; `.thn` cut-scene scripts on Lua 3.2 | [engbase](re/engbase.md), [deformable2](re/deformable2.md), [thorn](re/thorn.md) |
| Rendering | `RP8` (D3D8), `RP9` (optional D3D9), `Shading`, `RendComp`, `alchemy`, `ximage`, `flmaterials` | device and pipeline, textures and materials, meshes, particles | [render](re/render.md), [shading](re/shading.md), [alchemy](re/alchemy.md), [rp9](re/rp9.md) |
| Audio and media | `SoundManager`, `SoundStreamer`, `movie`, `imeui` | DirectSound SFX, streamed music/voice, intro video, IME | [audio](re/audio.md), [movie](re/movie.md), [imeui](re/imeui.md) |
| Shared game runtime | `Common` (+ `IVP` physics, `qhull`) | ~3.9k exports: game objects, archetypes, INI readers, AI behaviours, networking primitives | [common](re/common.md), [common_archetype](re/common_archetype.md), [common_physys](re/common_physys.md) |
| Game logic | `Server`, `Content` | the world simulation; missions, AI, encounters and populators on top of `pub::*` | [server](re/server.md), [content](re/content.md) |
| Transport | `rpclocal`, `RemoteServer`, `RemoteClient`, `RemoteCommon` | the `IServer`/`IClient` calls, in-process for single player or over DirectPlay for multiplayer | [rpclocal](re/rpclocal.md), [server](re/server.md) |
| Front end | `freelancer.exe`, `FLServer.exe` | client UI and game loop; MFC dedicated server shell | [freelancer](re/freelancer.md), [winmain](re/winmain.md) |

The full module table, with the retail DLL each directory replaces, is
[re/dll_inventory.md](re/dll_inventory.md).

## How the modules find each other

- **DACOM components.** Engine DLLs register named factories with `COManager` when the loader
  brings them up from the `[Libraries]` list of `bin\DACOM.INI`. Consumers ask for interfaces by
  name (`IRenderer`, `IAlchemy`, `IFileSystem`, …) and call them through vtables. `DllPath = .\`
  makes sure only the port's DLLs in `bin\` are loaded.
- **Ordinary imports.** `Common.dll`, `Server.dll` and a few others are plain C++ DLLs with
  thousands of decorated exports; consumers link against their import libraries.
- **Shared headers.** Every type that crosses a DLL boundary is declared once in `src/include/`
  (`<module>.h`, `common_*.h`, `server_*.h`). The order of virtual methods there *is* the ABI — see
  [re/cross_dll_protocol.md](re/cross_dll_protocol.md) for how slots are identified and recorded.
- **Content modules.** `Content.dll` is loaded several times under different roles
  (`GameSupport`, `SpaceSupport`, `BaseSupport`, `SpacePop`, …) from `[Initial SP DLLs]` /
  `[Initial MP DLLs]` in `bin\freelancer.ini`.

## Start-up, in brief

1. `WinMain` (`src/freelancer/Client/main.cpp`): single-instance mutex, change to the exe
   directory, check for `..\DATA`, EULA gate (`..\EBUEula.dll`).
2. `freelancer.ini`, display options, window creation.
3. `InitializeEngine`: `DALib::Startup` loads `[Libraries]`, the mandatory components are checked,
   then timing, the render pipeline and `DataConfig::startup` (archetypes, universe, goods).
4. Starting a game brings up `Server.dll` through `rpclocal.dll` (single player) or connects
   through `RemoteServer.dll` (multiplayer); the server loads the Content modules.
5. The game loop alternates `UpdateClientTiming` and message pumping.

Details and retail addresses: [re/winmain.md](re/winmain.md).

## Single player is client/server

Even offline, the client never touches the world directly: every action goes through `IServer`
(client → server, 92 methods) and every update comes back through `IClient` (server → client, 126
slots). In single player `rpclocal.dll` serialises these calls into packets and queues inside the
process; in multiplayer the same calls go over DirectPlay. Note the confusing retail names:
`RemoteServer.dll` is loaded by the *client*, `RemoteClient.dll` by the *server*.

## Source tree

Approximate size of hand-written source (`.cpp/.h/.c`, vendored code excluded), October 2026 —
about 775k lines in total:

| Directory | kLOC | Directory | kLOC |
|-----------|-----:|-----------|-----:|
| `freelancer` | 234 | `Shading` | 11 |
| `Common` | 106 | `RP9` | 11 |
| `Content` | 79 | `EngBase` | 10 |
| `include` (shared ABI) | 57 | `RendComp` | 10 |
| `IVP` | 50 | `Deformable2` | 9 |
| `Server` | 40 | `RP8` | 9 |
| `rpclocal` | 28 | `luaprofile` | 8 |
| `Thorn` | 26 | `FLServer` | 7 |
| `alchemy` | 25 | the rest | < 6 each |
| `movie` | 15 | | |

`src/Resources/` holds the text of the resource DLLs (≈5 000 `.txt` files: strings and infocards).

## Build system

- One solution, `src/Freelancer.sln`, one `.vcxproj` per module, all `Win32`, toolset v143, C++17.
- Shared settings live in `src/Directory.Build.props` / `.targets`: output directories, the DirectX
  SDK paths (`Dx8SdkDir`, `Dx9SdkDir`), and **x87 floating point** (`/arch:IA32`) to match the
  VC6-built retail modules bit for bit.
- Port-only features are MSBuild properties in `src/Freelancer.Diagnostics.props`, turned into
  `FREELANCER_*` preprocessor defines (widescreen, walk mode, RP9, beta label, tick profiler).
- Configurations: `Release` → `bin\`, `Debug` → `bin_debug\`, `DebugASan` → `binasan\`. Debug and
  ASan copy the runtime INI files from `bin\` (`src/copy_dev_ini.py`); edit them in `bin\`.

## Fidelity rules in one paragraph

The port follows the retail disassembly function by function; comments carry the retail addresses
(`FUN_005b2f50`, `.text:06d06bb4`). Anything the port does differently is a *deviation* and must be
written down in [re/deviations.md](re/deviations.md) with the reason and the condition for
removing it. Code that "makes the picture right" with a mechanism retail does not have is a
*substitution* and counts as debt, not progress — [re/substitutions.md](re/substitutions.md).
Port-only features stay behind build switches.

## Further reading

- [ini/README.md](ini/README.md) — every INI file, section and key the code reads.
- [re/crt_compat.md](re/crt_compat.md) — the modern CRT/STL against the retail VC6 runtime.
- [re/refactoring.md](re/refactoring.md) — rules for readability changes.
- [memory_diagnostics.md](memory_diagnostics.md) — leak hunting.
- [../CONTRIBUTING.md](../CONTRIBUTING.md) — how to make a change.
