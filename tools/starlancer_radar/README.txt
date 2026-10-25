Starlancer-style radar foundation (Freelancer-Decomp, not the Beta patch)

Integration
-----------
hud_starlancer_radar.cpp registers HUDFACTORY("StarlancerRadar") and is compiled
by freelancer.vcxproj. There is no second HUD, camera hook or RP9 modification.
The radar is a native WinControl drawn in the late Win3DDrawAll UI pass, sharing
its normal final line-batch flush. It does not flush/reset the batch itself.
Append hud_block.ini once to the active DATA\INTERFACE\hud.ini. In FL_MOD the
source of that path is bin\freelancer.ini, HUD = interface\hud.ini
(currently line 290). Keep the BEGIN/END markers so installers can replace the
block idempotently. The block is disabled by default; enabled = true plus a
game restart activates it. enabled = false restores the unchanged normal HUD.
No section at all also means no radar instance, scans or rendering overhead.

Prototype behavior
------------------
Player ship axes, independent of view/camera: -Z is forward/up on the ellipse,
+X is right, +Y is height. A vertical stem connects the contact to its projected
position on the ship's horizontal plane. Contacts below draw first, then the
ellipse/grid, then contacts above. Diamonds are ships, squares are selected
solar types. Red = hostile, green = friendly, blue = neutral; the current target
has pale brackets. The player's arrow sits in the center.

The source is the real CEScanner cache; its interference filter is preserved.
No world-wide enumeration, invisible-object reveal or extended range. Self,
dead/untargetable contacts, out-of-range objects and invalid coordinates are
excluded. Planets, stars, asteroids, lane rings, loot and projectiles are omitted.
show_solars includes stations, jump gates/holes, docking rings, platforms,
depots and satellites. When max_contacts is reached, selected then nearest
contacts win. Engine object pointers are never retained between frames.
Without a scanner or with suppressed/zero range the empty frame remains visible
at reduced opacity; no contacts are queried or revealed.

Configuration
-------------
center = x,y: viewport fractions, left/top = 0. radius is viewport-height
fraction. The layout stays inside inclusive viewport bounds with margins,
including stems/high contacts. Geometry scales with height, preserving shape
on 4:3, widescreen and ultrawide. ellipse controls the horizontal plane tilt;
elevation controls stem scale. opacity is 0..1. All geometry inputs are clamped
and invalid float values fall back to defaults.

range_index = 0,1,2 selects one of range_scales. Defaults represent quarter,
half and full EFFECTIVE scanner range. Values cannot exceed the scanner range.
Three short bars below the radar indicate the selected scale. This foundation
does not yet add a keyboard binding, live range button, numerical range label
or target selection hit-testing.

Beta visual assets
------------------
The local Beta has interface\hud\HUD_radar.3db, HUD_RadarRing.3db,
HUD_radarcircle.3db, HUD_radarbox.3db, HUD_radarminize.3db and contact blips.
These are candidates for the next artwork pass, not a recovered radar engine.
This first foundation uses the existing native HUD line batch instead of
loading those uninstalled meshes/materials. It has no Beta asset dependency
and does not copy assets into the current game.

Verification
------------
build_check.ps1 compiles and runs the independent projection/filter tests.
Optional integration fixture (requires an enabled radar block and installed DLLs):
  ./tools/starlancer_radar/build_check.ps1 -HudIni 'D:/games/FL_MOD/DATA/INTERFACE/hud.ini' -GameBin 'D:/games/FL_MOD/bin'
It reads the actual configuration through native Common.dll INI_Reader, emits
the production frame geometry, and checks visible pixels after a hidden D3D9
draw/readback with no scanner/contacts. It does not launch Freelancer or emulate
native Win3D scheduling. FLSpew diagnostics prefixed STARLANCER_RADAR report
Init (including actual config path), first UI draw, and each skip reason once.
The full EXE build checks factory/API/link integration. Real flight and final
placement have not been visually validated; the shipped block stays disabled.
