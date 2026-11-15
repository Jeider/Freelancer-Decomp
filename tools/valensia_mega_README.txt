Aggressive Valensia revision, 2026-11-13

Installed into D:/Games/FL_MOD (the game loads bin/Common.dll).
Pythonlancer universe generation was NOT run. Only its template source changed.

Seven semantic compounds per version:
  TOP includes the upper L5 ring and all TOP meshes/loadout panels.
  BOTTOM includes the lower L6 ring and all BOTTOM meshes/loadout panels.
  L1, L2, L3, L4 combine all industrial ring layers around each side core.
  WAIST combines paired L7/L8 ring sections.
Origins use the nearest existing sw_center planet; planets keep their own models.
Root/core, planets, working airlocks and the four central towers remain separate.

Current static station: 236 original objects -> 21 (previous pair revision: 180).
Two templates: 410 -> 19, and 292 -> 21.
Static station merged pieces: 1365 original near material groups -> 94 groups.
Triangles are batched by material AND original LOD range, with 16-bit chunk limits.
Every source triangle/LOD, normal/UV record and SUR terminal leaf was compared.
21 new CMP/SUR pairs were checked through the native Common/ReadFile loader.
The old source hulls have up to 0.317355 m convex-plane error; their topology is
retained, not replaced with convex station-wide shells. BVH wrap boxes are not solids.

Originals:
  valensiaOriginal.py and *Original classes: initial untouched design.
  valensiaPairsOriginal.py: preceding pair-component template.
  or_hqOriginal.ini: initial static system.
  or_hqPairsOriginal.ini: preceding pair-component system.
The corresponding old model archetypes are retained so these snapshots still work.

AI change (Common.dll):
  Large static solars with a SUR and longest extent >= 800 m are refined against
  terminal SUR triangles. Planets, ships, small solars and unsupported geometry
  keep the previous path. No external sidecar/capsule configuration is required.
  Near-wall deflection uses a local contact and ship-sized clearance, not the
  shell's whole enclosing capsule. Prediction sweeps the ship's radius against
  real walls before the centre-ahead and whole-radius gates.
  Internal BVH wrap ledges and detached parts are excluded. Traversal is bounded;
  an exhausted query conservatively falls back to the original coarse behavior.
  A nonzero capsule axis is retained for retail's ray/capsule solver.

Native regressions cover empty ring passages, walls, grazing clearance, detached
parts, the actual nominal/beta Nomad Lair surfaces and the merged station waist.
This is geometric validation, not a full in-game NPC route/performance test.

One minimal rollback set is kept at out/valensia_mega/rollback, about 22.69 MiB.
Its transaction manifest points to retained PairsOriginal files instead of making
additional copies of those same bytes. No timestamped full-tree backups are made.
After verified installation, generated staging was removed (90.94 MiB reclaimed).
Installed files, source originals, manifests, checks and rollback are retained.
Other tasks' backup histories and build products were only measured, not deleted.

Tools:
  valensia_mega.py: initial migration from the preceding pair revision.
  check_valensia_mega.py: staged visual/collision/source-reference comparison.
  check_valensia_mega_native.py: staged native SUR topology checks.
  physics/check_solar_avoidance.py: native geometry tests (staged or installed).
  train_courier/build.py Common: isolated engine build, no installation.
  install_valensia_mega.py: verified install, single rollback, no generator launch.
  valensia_storage.py: disk inventory; --clean-stage removes this task's generated
  payload only, using DataFolder for all staged DATA deletions.

The initial migration refuses to rebuild over its installed marker. For a later
revision, preserve the current template/system under a new Original snapshot and
review the migration; do not overwrite the retained original snapshots.
