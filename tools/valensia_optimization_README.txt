Valensia component optimization

This workflow does not run Pythonlancer's universe generator and does not build
or replace engine binaries. The user runs Pythonlancer generation themselves.

Preparation (before installing, from the original game files):
  python -B tools/valensia_optimize.py
  python -B tools/check_valensia.py
  python -B tools/check_valensia_native.py
  python -B tools/install_valensia.py
  python -B tools/install_valensia.py --apply

The installer verifies source/payload hashes and successful checks. It preserves
backups in out/valensia_optimization/backups and rolls back a failed transaction.
Do not rebuild from an already optimized solararch.ini; use the preserved inputs.
Only manifest-listed outputs are installed (older staging files are ignored).
DATA staging, installation, backup and failure rollback use DataFolder.

Preservation:
  Pythonlancer/templates/dockable/valensiaOriginal.py: byte-for-byte original file.
  ValensiaOutsideOriginal and ValensiaOutsideTwoOriginal: original template classes.
  ValensiaOutside and ValensiaOutsideTwo: optimized templates under existing names.
  DATA/UNIVERSE/SPECIAL/ORDER_HQ/or_hqOriginal.ini: byte-for-byte original system,
  inactive in universe.ini. or_hq.ini keeps its own layout, not the template layout.

Selection:
  Only decorative industrial 3DBs without loadouts/gameplay properties are grouped.
  Same semantic nickname segment, archetype and parent; up to eight neighbours.
  Capsule radius <= 150 m and <= twice the source radius, longest extent <= 600 m.
  Pairwise connection to an existing member requires a bounding-box gap <= 120 m.
  Do not join entire rings, wings, or all TOP/BOTTOM objects into one obstacle.
  Source objects referenced as parents are retained.

Geometry:
  Original mesh bytes, mesh CRCs, hardpoints, materials and LODs are retained.
  Keeping mesh CRCs permits existing mesh-buffer sharing across components.
  Correct Common EulerMatrix and EngBase fixed-joint matrix convention are used.
  Original SUR terminal leaves, adjacency, opposite faces and point positions are
  retained, including the original double-sided triangle leaves. Only rigid
  transforms/part IDs change. No collision is invented across the gaps.
  The structural SUR broadphase wrapper is a kind-5 box, not a terminal solid.

Validation:
  check_valensia.py verifies preserved originals, unaffected system blocks,
  transformed positions, mesh/LOD/hardpoint bytes, leaf topology, bounds and
  references to removed nicknames in DATA/Pythonlancer INI/Python files.
  check_valensia_native.py builds only a standalone verification program and loads
  the new surfaces through the installed Common.dll and ReadFile.dll. It checks
  tree bounds, indices, adjacency, winding and convexity. Imported industrial01a
  surfaces have up to 0.033894 m plane error already; the leaf tolerance is 0.035 m.
  New structural wrappers retain the stricter 0.002 m tolerance.

Expected effect and remaining in-game validation:
  Fewer solar objects and physics owners. Mesh/triangle counts are not reduced,
  and this does not claim a measured FPS improvement. Some grouped objects cross
  the AI's 100 m ignore threshold, but each remains a small local obstacle instead
  of a station-wide one. Flight, docking and NPC routes need an in-game test after
  restart. No automatic game restart or Pythonlancer regeneration is performed.
