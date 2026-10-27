# Standalone anomaly shader lab

See the [implementation report](../../docs/space_anomalies/shaders.md), [Russian report](../../docs/ru/space_anomalies/shaders.md) and [image gallery](../../docs/space_anomalies/previews/report.html).

This folder does not install anything or launch Freelancer. `build.py` compiles a hidden-window D3D9 HAL fixture and writes images under `src/obj/space_anomalies`. `presets.json` holds eight theatrical studies; `presets.realistic.json` holds the new quality-first studies. HLSL lives in `DATA_EXTRA/SHADERS/ANOMALIES`. The two report scripts accept actual rendered images only; they require Pillow.

The new default is **realistic / epic / 3840×2160**, using a separate executable/header/output folder `src/obj/space_anomalies/realistic`. [Realistic implementation](../../docs/space_anomalies/realistic.md) · [Русский](../../docs/ru/space_anomalies/realistic.md).

The user authorized standalone preview generation. Build only this fixture; it does not compile or install the game. Independent source/math checks:

```powershell
python tools/space_anomalies/check_realism.py
```

Reproduce the captures with the commands below. `--no-build` skips C++ compilation but still compiles changed HLSL. The isolated shader cache is keyed by expanded source, compiler identity, entry point, profile and flags.

```powershell
python tools/space_anomalies/build.py --style realistic --quality epic --output src/obj/space_anomalies/realistic/final
python tools/space_anomalies/build.py --style realistic --quality epic --no-build --width 960 --height 540 --checks --output src/obj/space_anomalies/realistic/checks
python tools/space_anomalies/report_realistic.py
```

The real GPU report is not generated until these renders and checks exist. Quiet black holes need not animate. `sensor` in the presets explicitly distinguishes optical-looking effects from radiation composites for pulsar/magnetar readability. `--quality ultra` is a lower sampling alternative; `epic` is the selected maximum-quality profile.

To reproduce the previous theatrical studies:

```powershell
python tools/space_anomalies/build.py --style theatrical --output src/obj/space_anomalies/final
python tools/space_anomalies/build.py --style theatrical --no-build --width 640 --height 360 --checks --output src/obj/space_anomalies/checks
python tools/space_anomalies/report.py
```

The shader lab targets SM3 but does not claim legacy-GPU performance. The fixture uses an HDR panorama instead of a captured game scene and has no game-depth integration. Final output is an opaque composition, not a ready-to-layer transparent texture. Read the report before integrating it.
