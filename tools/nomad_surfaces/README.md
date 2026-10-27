# Nomad / Dyson laboratory and integration

See [implementation](../../docs/space_anomalies/nomad.md) and [Russian report](../../docs/ru/space_anomalies/nomad.md).

Run from the repository root, Windows / MSVC 2026 / DX8 + June 2010 SDK:

```powershell
src/obj/asteroid_normals/venv/Scripts/python.exe tools/nomad_surfaces/generate.py
python tools/nomad_surfaces/build.py
python tools/nomad_surfaces/check.py --build-only
python tools/nomad_surfaces/check.py --no-build
src/obj/asteroid_normals/venv/Scripts/python.exe tools/nomad_surfaces/report.py
python tools/nomad_surfaces/install.py
python tools/nomad_surfaces/install.py --apply
```

`generate.py` requires NumPy/Pillow and reads original mod textures from `D:/games/FL_MOD`. It does not edit them. `build.py` preserves the current enabled FL_MOD compile-time feature set. GPU checks require a desktop-capable D3D9 HAL. `NOMAD_QUICK=1` skips only the expensive unrelated-bytecode regression while tuning; omit it for final validation. The baseline for that check is the pre-edit working-tree shader in `src/obj/nomad_surfaces/baseline/DATA_EXTRA/SHADERS/surface_material.hlsl`; on a fresh checkout, provide the intended pre-change baseline explicitly instead of silently substituting another revision.

Installation preparation is read-only for the game. `--apply` requires it and verifies that neither staged nor installed files changed meanwhile. Rollback: `python tools/nomad_surfaces/install.py --restore PATH_TO_BACKUP`. Executables are builds of the shared working tree, including other ongoing changes; no branch or commit is created. Game MATs, missions, system INIs and `port.ini` are unchanged. Installation status is recorded separately from the shader test results.

ET animation source-only update (no compiler invocation, no binaries copied):

```powershell
python tools/nomad_surfaces/install_animation.py
python tools/nomad_surfaces/install_animation.py --apply
```

Final animation GPU verification was deferred at the user's explicit request not to compile while another task is building. The new temporal assertions and 96-frame capture loop are ready for a later authorized check. Existing published gallery images/logs describe the prior static version.
