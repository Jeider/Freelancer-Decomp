Vector Radar
============

[Radar] in the active hud.ini creates HUD_Radar (hud_radar.cpp/.h). The previous
prototype name is removed from source, project registration and the installed INI.
The radar sits at center = 0.50, 0.845, radius = 0.30 of viewport height, above the
central core HUD. It stays centered on widescreen and ultrawide displays.

The segmented rim is the original Freelancer Beta HUD_RadarRing.3db geometry:
208 referenced vertices, 304 native VWireData edges. tools/export_radar_ring.py
extracts and normalizes those exact edges into radar_ring_geometry.h, recording
the source SHA256. The Beta source file is read only; no shared VMS/material or
texture needs to be installed. This is a vector rendering of the original model,
not a replacement ellipse. radar_frame.h adds an oblique circular-clipped lattice.
The original HUD_radar.3db is a small textured quad; that texture is not used by
this vector implementation.

The rim responds to the player's actual local pitch/yaw angular velocity, normalized
by the ship's native full-steering angular speed per axis. Rate is proportional to
turn strength, capped at the original 8 degrees/second, with a small rest dead zone
and a 0.16-second exponential response. Dominant yaw sets left/right direction;
mostly vertical turns use pitch direction. Roll alone and moving the camera/cursor
without turning the ship do not spin the rim. Ship replacement resets this transient
state. The grid turns with the rim; contacts retain their normal ship-local coordinates.
sweep_speed = 45 independently turns two opposing scan fans
inside the rim (degrees/second); 0 freezes the light. The fans fade behind their
leading edge and soften toward the center/rim. Simulation pause stops the animation.
Height stems fade into the plane. ellipse = 0.32 sets the plane foreshortening;
elevation = 0.94 sets the height scale. opacity controls the whole radar.

Ship contacts are filled vector triangles with vertical stems down to the plane.
Red = hostile, green = friendly, pale blue-white = neutral. The current target has
yellow brackets. Included solars use outlined diamonds. Below-plane contacts draw
before the frame; above-plane contacts draw after it. Tall stems are clipped at the
viewport safe bounds so contact markers remain visible. A native textured disk
uses the existing HUD backgroundpattern.tga with opacity 0.25 at HUD depth -1.
make_assets.py generates standalone disk and button meshes without changing shared VMS.

Ordinary contacts come from the native CEScanner cache and its interference-adjusted
range. Dead, self, untargetable and out-of-range contacts are rejected.
An explicit [Solar] radar_mining = true opts a mining solar into triangle navigation
markers, including NON_TARGETABLE archetypes. A separate bounded spatial query within
the displayed scanner range applies target interference and parent/death filters.
It never adds these objects to the shared scanner cache or makes them targetable.
Unmarked decorative rocks and the sig13_mineable_gas_static inner clouds stay hidden.
radar_hidden = true excludes a solar even when selected or also tagged for mining.
Both flags default false, inherit and reload with the archetype, and use Solar's
existing alignment padding without changing the native ABI.
stage_solars.py stages the vetted 24 mining / 8 hidden archetypes, audits the 40 active
main systems and preserves every other byte in solararch.ini. The hidden archetypes
are docking_fixture*, tr_point_* parked transports and their cargo, not flying ships. Solar objects with
nonempty CSolar::GetParentNickname() (the system [Object] parent key) are excluded
from this radar without altering the shared scanner cache or other HUD lists. Selected then
nearest contacts win at the max_contacts limit. show_solars includes stations,
gates, holes, docking rings, platforms, depots, satellites, planets/moons and trade-lane
rings, not stars, asteroids or projectiles. Loot is included independently of show_solars
and uses the triangle marker, within the same scanner detection range.
Without a scanner the empty frame dims.
No engine object pointer is retained between frames or across system changes.

range_scales = 0.25, 0.50, 1.00 and range_index = 2 select fractions of effective
scanner range; the grid shows the scale with large sparse squares nearby and
smaller dense squares at long range. Separate range marks are hidden. Real native +/-
buttons at the front right use NavMap's zoom meshes without their separate backgrounds
and retain the localized tooltip IDs. A Beta HUD_radar toggle belongs to the central
Radar root at (-.195,-.37), between Targeting and HUD_Core's 100% indicator, and remains available with
the contact list collapsed. TargetTradeButton is raised to y=-.325. Yellow means on. Save interface bit 17 persists its state; legacy/new saves default off.
Bits 18..19 store range index + 1, with zero falling back to the hud.ini range_index.
Both settings are restored on save loads, including while the HUD remains alive.
Only the toggle remains when off, and no scanner work occurs.
Plus zooms in (less range); minus zooms out. Limits disable the corresponding button;
circle size stays fixed. No target-picking controls yet. The mouse-flight caption
and its cancel hint are temporarily hidden (other mode warnings remain native).
Backspace's temporary HUD hide does not affect Radar or its controls. NeuroNet, letterbox, transitions and hidden HUD suppress it.
Only its buttons intercept mouse input. Cruise charge/disruption countdowns sit
above the disk; trade-lane destination captions are hidden.
Entering a trade lane or arriving in a new system returns the rim to its forward
arrow by retracing the last manual turn, capped at 8 degrees/second. The return
heading is latched: it does not switch to a closer arrow after half a turn.
A new manual direction replaces that preference on the next return.
Weak turning (below 8% of the ship's maximum pitch/yaw rate) or releasing mouse
flight also returns the rim smoothly. Maneuvering above 14% interrupts that return;
the gap prevents flicker between the modes. Return decelerates near forward.

Rendering uses the native late Win3D line batch, with its capacity flushing and
viewport-to-ortho conversion. There are no extra pipeline hooks or raw state writes.
Diagnostics use HUD_RADAR. enabled=false (or no section) creates no active radar.

Verification
------------
./tools/radar/build_check.ps1 -HudIni <active-or-staged-hud.ini> -GameBin <mod/bin>

Checks ship-local projection, detection filters, finite coordinates, offset and
wide viewports; runs the production ring/grid/contact emitters at three animation
phases and exports CSV previews. A hidden D3D9 draw/readback confirms the empty
frame renders from the native Common.dll INI reader (825/833/845 lines by range).
check_controls.py
exercises production parent filtering, zoom handlers, limits and button placement. This is not an
in-game flight capture. tools/export_radar_ring.py validates original wire indices
and leaves the source asset unchanged.
check_solars.ps1 exercises the real newly built Common.dll loader and metadata inheritance/reload.

Large contacts use the original Beta VWireData extracted by tools/export_radar_symbols.py:
planet/moon -> HUD_radarplanet; gunboat/cruiser/capital -> HUD_radarcapship;
transport/mining -> HUD_radartransport; weapons platform -> HUD_radarweaponplat;
trade-lane ring -> HUD_radarTLR; other supported solars -> HUD_radardockable.
Fighters, freighters and loot retain triangles. Glyphs face the viewer for readability.
Planets use their physical world centre/radius and the actual radar scale, including
surface intersections when their centre is outside range. Their original silhouette
has translucent fill and only the outside contour, with no internal wire edges.
Friendly planets use the neutral colour. Height stems stop at the surface.
Other glyphs use a fixed readable size. Large symbols are clipped
to the contact area; the scanner cache and interference rules still determine detection.
test_symbols.cpp covers these mappings, zoom/radius scaling, clipping and bounded work.
