# VR and spatial HUD implementation plan

Design dated 30 October 2026. Implementation has not started. The detailed working plan is available [in Russian](ru/vr_spatial_hud_plan.md).

The design introduces seated cockpit VR and a shared HUD surface system. Desktop players can use inward-facing panels with perspective and restrained motion independently of VR. Crysis 2 is a visual reference, not a claim about its implementation.

Each panel renders existing models, text, radar lines and ShipView into a transparent surface. Placement drives both rendering and inverse pointer mapping, including hover, click, wheel and capture. World markers and aiming remain separate. Existing deployment animations and visibility settings operate in panel-local coordinates.

VR temporarily overrides the camera without rewriting the per-save desktop preference. Third-person, rear, turret and debug chase viewpoints are unavailable as immersive views. Scripted cameras, death, bases and movies continue on a virtual screen. Loading another save updates the underlying preference restored when VR ends.

OpenXR integration first requires a hardware prototype validating Win32 runtime compatibility and GPU texture sharing between RP9 and D3D11. A D3D9Ex path requires a resource/reset audit. A separate x64 bridge is a contingency. Simulation and input run independently of the number of eyes; each eye uses runtime projections and poses for the same display time.

Implementation order: one desktop HUD surface with accurate input; desktop panels and settings; VR transport validation; stereo cockpit and camera policy; VR UI and transitions; performance qualification. Desktop HUD can ship independently. VR configuration belongs to the device profile; forced cockpit view must not overwrite character saves.

The [detailed plan](ru/vr_spatial_hud_plan.md) defines integration points, session transitions, tracking loss, aiming, rendering ownership, settings and acceptance checks.
