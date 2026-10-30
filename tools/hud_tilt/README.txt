Desktop HUD tilt prototype

RP9 and FREELANCER_WIDESCREEN_SUPPORT are required. The default is 0 (flat).
Options > Miscellaneous > General > HUD tilt uses native arrows, 0..50 degrees
in steps of 2. Apply saves to user PerfOptions.ini, [HUD] hud_tilt_degrees;
Cancel discards edits and Defaults selects 0. Available before loading a save.
The separate section preserves the original PerfCount and existing settings.
Configured angles round to the nearest 2 degrees; legacy 45 becomes 46.
Upper/lower arrows increase/decrease HUD tilt and auto turret reserve,
including hold-repeat and mouse wheel input; reserve keeps its 5% step.
The old experimental port.ini [Render] angle is retired.
Console: hud_tilt 0..50 changes the angle for the current process, without saving.

The side roots HUD_Status, HUD_Health, HUD_Target, HUD_Targeting and HUD_ContactList
are rendered as complete surfaces, including text and ShipView. Centered loot/trade
and special mode children are routed to the original target. The radar, bottom bar,
top menu, world markers, crosshair and modal windows retain their current layout.
There is no dynamic sway in this prototype and no VR dependency.

A full-resolution target is reused between panels. RP9 preserves normal alpha and
additive light separately; the final shader composites premultiplied RGB. Pointer
coordinates use the inverse of the same perspective transform. Capture and wheel
keep the original Win3D dispatch. Tooltip anchors follow the visible panel.

Run tools/hud_tilt/check.ps1: projection/inverse at multiple resolutions, angles,
symmetry and off-panel capture; non-RP9 compilation; actual VS/PS compilation.
Run python tools/hud_tilt/check_settings.py for PerfOptions file persistence,
legacy defaults, existing settings, range and invalid-value handling.
Run python tools/targeting_hud/check_misc_settings.py for the native settings
page, staged edits, arrow endpoints, Apply/Cancel/Defaults and main-menu access.
Run python tools/hud_tilt/check_font_routing.py for the deferred font queue:
panel text and numbers flush before target switches, centred children remain flat,
and no panel glyphs remain for the final screen overlay. The old code is rejected.
Build Release Win32 client and RP9. Install both binaries and the shader together.
After building RP9, python tools/hud_tilt/gpu.py runs a hidden hardware check against
its actual object files: capture state, normal/additive alpha, the production shader
composite and state restoration. The test does not launch or alter the game.
An older RP9 does not advertise bHudSurface, so the client leaves the HUD flat.

Live acceptance: open and collapsed panels, target and health ship views, turret
icons and weapon toggles, scrolling, hover/tooltips, modal capture, resize/Alt-Tab,
10/20/50/0 degrees, unchanged center markers and the flat HUD at 0 degrees.
Visual acceptance on the player's running game is still required.
