# Nomad Lair / Dyson surface implementation

RP9 implementation, 27 October 2026. [Русский](../ru/space_anomalies/nomad.md).

Installed into `D:/games/FL_MOD` at 00:09 MSK; all eight payload files verified by SHA-256. Backup: `D:/games/FL_MOD/BACKUP/codex_nomad_surfaces_20261027_000906_769977`. No in-game flight was performed.

[Actual GPU gallery](nomad_previews/report.html). These are original mod textures on a curved material sample, not screenshots from the mission.

The interior profile adds strong wet relief: twelve-step parallax occlusion, normals derived from the original diffuse plus a periodic fold atlas, roughness variation, a tight wet coat, and a restrained vascular accent. Authored illumination textures remain separate emissive inputs. Accepted second stages preserve colour operations, UV selection, tiling and alpha multiplication; unsupported layouts retain native rendering. The height estimate is artistic and includes lighting baked into the diffuse texture. Geometry, silhouettes and collisions are unchanged.

ET animation update: interior ADD/ET materials now use the authored emission as a tissue envelope for a 16-second contraction cycle, up to 0.0045 UV motion, ±20% relief breathing, and approximately 90–120% original emission. Both tunnel CMPs use `detailmap_lair_skin02`; its dim ET luminance requires envelope thresholds 0.006–0.065. Alpha masks remain fixed. This is local UV motion, not a continuous world-space wave through the entire tunnel. Exterior, Dyson and Bt detail are excluded.

**Compilation was stopped at the user's request.** The final animation is not GPU-validated; the gallery and successful logs refer to the previous static version. Future motion/alpha/clock-wrap/exclusion checks are included in the fixture. `tools/nomad_surfaces/install_animation.py` deploys only the HLSL source and never builds/copies EXE or DLL files. RP9 compiles the modified source on the next game startup.

Seven explicitly named exterior `detailmap_lair_rock*` materials use a rough stone/bone finish without the wet coat or vascular pulse. Named Dyson materials use the cheaper normal-relief profile without parallax marching or shadow-map sampling. Material identities are listed in `src/include/render/NomadSurfacePolicy.h`; transparent membranes and energy materials are excluded.

Sphere's `solar/asteroids_mod/dyson/sphere_field.ini` uses an opaque camera-depth prepass and depth-equal material pass with the same vertex shader. Fully hidden fragments avoid material work; geometry is still submitted. Fading boundary cubes retain normal alpha/depth behaviour and are excluded from opaque occlusion. The scope pins native fallback while asynchronous shader warm-up is unfinished. Render states are restored afterwards. **Cube fields were not added to shadow-caster lists.**

Near-field frustum culling now uses a sphere containing the actual merged vertices, including each rock's offset, and expands cell enumeration accordingly. This applies to all static near fields, including Om11 large-asteroid fields. Sphere's approximately 2000-unit boxes exceed its 1650-unit cell width. Far billboards and dynamic-rock recycling are unchanged. In-game reproduction in Om11 and full-field performance still need a flight check.

`bin/port.ini`, `[Render]`: `surface_shaders=1`, `nomad_shader=1`, `nomad_relief=1.15` (0–2), `nomad_glow=0.32` (0–1). Disabling added glow does not remove authored illumination. Disabling the Nomad shader retains the culling fix. Restart after changing settings.

The 1024² packed atlas has RG normal XY, B height and A vein mask, a full renormalized mip chain, and occupies approximately 5.33 MiB. Code and reproducible generation/build/GPU/route/deployment tools are in `tools/nomad_surfaces`. The installer stages exact files, checks hashes and running processes, backs up originals and supports rollback; it does not modify game MATs or system INIs.

Validation covers Release Win32 builds, 200,000 conservative frustum witness cases, production SM3 variants, unchanged unrelated surface bytecode against the pre-change working-tree snapshot, visible relief, retained illumination in darkness, fog, exact prepass output, finite float HDR with degenerate/mirrored UV and grazing normals, real RP9 stage routing and device-resource reset. See the gallery logs for the actual run results. Screenshots do not establish in-game frame rate or eliminate unrelated sources of asteroid disappearance.

Further art work: authored bone/stone masks on the exterior; sparse vessels following tunnel UVs; reactor pulses between bone arches; geometric folds on doors; separate masks for intact Dyson plates, broken seams and invading tissue. These are design proposals, not implemented features.
