# Contributing

**English** · [Русский](CONTRIBUTING.ru.md)

Thank you for your interest in Freelancer Decomp. The project's goal is fidelity to the retail
game ([docs/MISSION.md](docs/MISSION.md)), so a change is judged first by whether it matches the
original, and only then by whether it looks right on screen.

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the layout of the code.

## Before you start

- Build `Release|Win32` once as described in [README.md](README.md) and make sure the game starts
  from `bin\` with your own `DATA`.
- Reverse-engineering work needs your own retail Freelancer 1.1 binaries as a reference. The
  documents refer to them as `EXE\<module>` and to disassembly listings as
  `EXE\Disasm\<module>.txt`; neither is in the repository, and the port never loads them.
- Some documents mention **decomp-tracker**, the maintainers' per-function status database. It is
  not public; when a document sends you there, use the retail listing and the source instead, and
  describe your findings in the pull request.

## Kinds of changes

| Change | What is expected |
|--------|------------------|
| Porting or fixing a function | The body follows the retail listing: same branches, order of side effects, error paths. Put the retail address in a comment (`// FUN_005b2f50`). |
| Behaviour that differs from retail | Allowed only when unavoidable, and recorded in [docs/re/deviations.md](docs/re/deviations.md): retail behaviour, port behaviour, reason, removal condition. |
| A port-only feature | Behind a build switch in `src/Freelancer.Diagnostics.props` (`FREELANCER_*` define), off by default unless agreed otherwise; documented, with the retail path intact when the switch is off. |
| Readability refactoring | Follows [docs/re/refactoring.md](docs/re/refactoring.md): no change of behaviour, ownership or layout; renamed exports checked with `dumpbin -exports`. |
| Data / INI behaviour | Update the matching page in [docs/ini/](docs/ini/README.md). |

What not to do:

- Do not "make it work" with a mechanism retail does not have (private gates, stub vtables returning
  success, proxy objects) — see [docs/re/substitutions.md](docs/re/substitutions.md).
- Do not add defensive checks or incidental modernisation to ported code; if you find a real
  defect, fix it in a separate change.
- Do not change a type or the order of virtual methods in `src/include/` without updating every
  consumer in the same change — it is the cross-DLL ABI
  ([docs/re/cross_dll_protocol.md](docs/re/cross_dll_protocol.md)).
- Do not commit retail binaries, listings or game data (`.gitignore` already excludes them).

## Code style

Match the surrounding code: naming, comment density, idiom. Comments state contracts, ownership,
units and non-obvious ordering; long address-level proofs belong in the pull request description.
Keep the floating-point model and other settings in `src/Directory.Build.props` unchanged — they
reproduce the VC6 runtime behaviour.

## Checking a change

There is no automated test suite yet. Before opening a pull request:

1. Build `Release|Win32` without new warnings; for memory-related changes also `DebugASan`
   ([docs/memory_diagnostics.md](docs/memory_diagnostics.md)).
2. Run the game from `bin\` and exercise the affected path (menu, single-player start, docking,
   the screen you changed…).
3. If you touched a feature switch, build with the switch both on and off.

## Documentation

Documentation is in English in `docs\`, with a Russian translation in `docs\ru\`. Update both when
you can; if you cannot, update the English page and say so in the pull request. Link new pages
from [docs/README.md](docs/README.md).

## Pull requests

Keep one logical change per pull request and describe: what was ported or changed, the retail
functions involved (addresses), how you checked it, and any new entry in `deviations.md`.

By contributing you agree that your contribution is released into the public domain under
[The Unlicense](LICENSE).
