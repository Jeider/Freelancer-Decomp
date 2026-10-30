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

Guided missiles/torpedoes use hollow circles with height stems. Hostile launchers
produce red markers, friendly/own launchers green, unknown/neutral launchers pale
blue-white. A live missile targeting the player alternates red/yellow every 0.25 s
(two full cycles per second), regardless of launcher attitude or availability.
The phase advances with HUD frame time independently of sweep_speed. The actual
current target is read each draw, so retargeting/countermeasures stop the warning.
An independent missile-only object-database walk avoids the shared scanner cache's
256-entry limit. It respects targetability, alive/dying state, scanner range,
zoom and target interference, and retains at most max_contacts missile candidates.
Incoming missiles take priority, followed by the selected target and nearest
contacts, under the overall max_contacts limit. The same ship-relative markers
work in cockpit and external views. No projectile gameplay or lock-on changes.

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
from this radar without altering the shared scanner cache or other HUD lists. show_solars includes stations,
gates, holes, docking rings, platforms, depots, satellites, planets/moons and trade-lane
rings, not stars or asteroids. Missiles and loot are included independently of show_solars.
Loot uses the triangle marker, within the same scanner detection range.
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
Switching off removes contacts immediately and smoothly shrinks the disk and its
background while sliding them down below the viewport over 0.35 seconds. At the
end the model disappears completely; only the toggle remains. Sweep, player marker,
zoom controls and radar scanning stop immediately. Opening rises from below the
screen, expands to full size and only then starts scanning.
The quintic easing has zero endpoint velocity/acceleration and can reverse from
the current size. No additional setting or asset is required.
Plus zooms in (less range); minus zooms out. Limits disable the corresponding button;
circle size stays fixed. No target-picking controls yet. While radar is enabled,
special-mode captions and exit hints (mouse flight, turret/rear view, docking and
tradelane destination) are hidden; cruise charge/disruption remains above the disk.
Switching radar off restores native captions and their original positions, including
the cruise label at (-0.243, -0.263). Without an active Radar item the native layout
also remains in use. Caption restoration does not wait for a flight-mode change.
Backspace's temporary HUD hide does not affect Radar or its controls. NeuroNet, letterbox, transitions and hidden HUD suppress it.
Only its buttons intercept mouse input.

Two projection buttons at the front left use Targeting's HUD_target_view1/2 meshes.
Projection 1 keeps the existing oblique view. Projection 2 faces the screen as a
circle at half the original diameter, anchored at the bottom centre. Its controls
sit beside the circle above the status bars. Contacts and Solar wireframes use
the ship's heading in the ecliptic plane,
ignoring pitch and roll. Player position remains the origin; normal scanner range
checks still include relative height. Vertical flight uses the projected right
axis as a finite heading fallback. Zoom, frame, background, clipping and caption
anchor share the projection layout. The chosen mode persists in the global HUD
profile (bit 30); existing profiles default to projection 1.
Entering a trade lane or arriving in a new system returns the rim to its forward
direction using the nearest of its four identical arrows, capped at 8 degrees/second.
The return covers at most 45 degrees; previous turn direction is not remembered.
Weak turning (below 8% of the ship's maximum pitch/yaw rate) or releasing mouse
flight also returns the rim smoothly. Maneuvering above 14% interrupts that return;
the gap prevents flicker between the modes. Return decelerates near forward and
snaps angle and angular speed to zero when aligned, keeping the rim stopped.

Rendering uses the native late Win3D line batch, with its capacity flushing and
viewport-to-ortho conversion. There are no extra pipeline hooks or raw state writes.
Diagnostics use HUD_RADAR. enabled=false (or no section) creates no active radar.

Solar wireframe layer (v1)
-------------------------
[Solar] radar_wireframe = true opts an archetype into a separate architecture layer.
It defaults false, inherits, supports explicit false overrides and reloads. Its
metadata lives outside the retail Solar layout. Put it after nickname in solararch.ini.
The same archetype is opted in wherever used, including systems other than Lair.

Only existing native VMeshWire vertex/index data is drawn; no triangle-edge fallback.
All flagged solars are visited, including NON_TARGETABLE and parented objects,
independent of max_contacts, scanner cache/detection/interference, show_solars and
radar_hidden. Dying objects are skipped. Regular symbols are suppressed for flagged
solars; targetability and other HUD contact lists are unchanged.

Geometry is clipped segment by segment to the saucer's ellipse, including partially
visible models. Nothing extends into the rectangular corners outside the dish.
Wire line opacity is 25% of the configured radar opacity (20% at opacity=0.8).
In projection 2 the same clipping boundary becomes a circle.
Displayed zoom remains the
scale reference; raw scanner range (or 10 km without a scanner) is the fallback
when normal detection is suppressed entirely. No short-range filter exists in v1.
The layer follows the radar's existing visibility/toggle state.

Wire interfaces share decoded CPU geometry across instances. Live part transforms
are read every frame, including compound door motion. No scene instance pointer
survives a draw. Unused wire references, system changes and radar destruction clear
the cache. The existing HUD line batch draws geometry under contact markers.

stage_wireframe.py stages nine Solar flags for the models with VWireData in
UNIVERSE/SPECIAL/LAIR/lair.ini (43 objects); ten archetypes without wires stay intact.
It preserves all original INI bytes outside insertions and records input hashes.
check_wireframe.py verifies all 40 real wire parts, the production layer with 300
solars, live child transforms, cache cleanup, clipping and the real Common loader.
prepare_wireframe_install.py stages Common, client and solararch.ini, with backup,
input verification and rollback. Visual appearance still needs an in-game check.

Verification
------------
./tools/radar/build_check.ps1 -HudIni <active-or-staged-hud.ini> -GameBin <mod/bin>

Checks ship-local projection, detection filters, finite coordinates, offset and
wide viewports; runs the production ring/grid/contact emitters at three animation
phases and exports CSV previews. A hidden D3D9 draw/readback confirms the empty
frame renders from the native Common.dll INI reader (825/833/845 lines by range).
check_controls.py
exercises production parent filtering, zoom handlers, limits, button placement and
the enabled-only cruise anchor. tools/targeting_hud/check_hud_feedback.py checks
caption restoration across six flight modes and cruise position round-trips. This is not an
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
It also checks hollow missile circles, clipping and threat colors; it runs even
without -HudIni. python tools/radar/check_missiles.py extracts the production
collector and exercises live ownership/retargeting, missing owners, dead objects,
scanner/zoom limits, a 600-missile scene, priority and bounded storage with stubs.

Options > Miscellaneous selects manual,
any-contact, or hostile-contact auto-show, saved in interface bits 20..21.
Detection continues at 5 Hz while closed and uses the same scanner/range filters
as drawing. Incoming missiles count as hostile. Matching contacts disappearing
starts a 1.5-second hold before closing. A manual close is respected until those
contacts leave; manual opening pins the radar. Selecting an automatic mode unpins it.
check_controls.py exercises the production auto-show update, mode changes, delayed
close, manual override, save reload, disabled scanners and unavailable players.
