Potsdam / rh_ber semantic optimization, 2026-11-13

Installed ten shared compounds: MAIN, SH, IND_LVL1, IND_LVL2, IND_LVL3,
IND_NRG, HILL, DOCK (static scenery only), TOP, STOR. Component origins are
local centers of the member placements, not the station-wide root.
110 static objects -> 10; total station objects 115 -> 15. Original root,
working shipping dock and all three battleships remain byte-identical in the
live system, preserving docking and animation. 741 -> 86 near draw groups
for the baked portion. No measured in-game FPS claim.

SH retains all 128 original blinking lights on uniquely renamed hardpoints,
with equipment types and world transforms preserved. Original geometry,
UVs, normals, material assignments and LOD cohorts are retained. Source SUR
terminal hull topology and points are preserved; no station-wide solid hull.

Template and live system had identical relative geometry, offset 38000,0,18000,
so both use the same model set. Existing Potsdam class retained as
PotsdamOriginal, active Potsdam inherits it with the new TEMPLATE.
Byte-exact snapshots: templates/dockable/potsdamOriginal.py and
DATA/UNIVERSE/SYSTEMS_MOD/RH_BERLIN/rh_berPotsdamOriginal.ini.
Pythonlancer generation was not run; no engine binaries changed.

Checks: every baked triangle/LOD/material/vertex, exact SUR leaves, all light
mounts, template/live equivalence, unchanged unrelated live blocks, preserved
source template, existing solar/loadout definitions, global nested filename
CRCs against other optimized models. Installed Common.dll loaded all ten SURs.
Removed nicknames appear only as definitions in inactive rh_mod/rh_ber_tracks/
rh_ber_3d variants, with no external references found in DATA ini/thn files.
Dock approach and visual behavior still need the player's in-game check.

One minimal rollback in out/potsdam_mega/rollback (1.96 MiB plus retained
Original snapshots); stage payload removed after byte-verified installation.
Manifest/checks/native log/installed hashes retained under out/potsdam_mega.
Build: python -B tools/potsdam_mega.py (initial migration only).
Native check: set valensia_mega.OUT to potsdam_mega.OUT, then import
check_valensia_mega_native. Install: tools/install_potsdam_mega.py --apply.
