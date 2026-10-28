Cockpit head look-ahead prototype

Cockpit free-look integration
-------------------------------
The person icon to the left of HUD_Maneuvers (in cockpit view) toggles cockpit
look. It follows the maneuver frame width, visibility and auto-hide hover area.
While enabled, a fresh left-button press outside HUD widgets captures
relative mouse movement for the head. Holding without movement retains the
target angle. Release restores the cursor and smoothly centres the head; the
icon remains enabled until clicked again. Its enabling click is never a drag.
The tooltip is available in Russian and English. State is session-only.

The entry Space mouse-flight toggle also selects hands-free cockpit look. If
already locked when look is enabled, capture starts after releasing the icon
click and moving outside HUD widgets. Mouse movement then turns the head without
LMB; releasing LMB does not centre it. Space unlocks, restores the cursor and
smoothly centres the head. Space can lock it again while look remains enabled.
Unlock before clicking the person icon to disable look. With the lock off, the
original hold/release behavior still applies. Menus and focus loss suspend capture.

The existing head_turn limits and rate-limited smoothing are shared with the
automatic look-ahead. Relative deltas use mouse speed/inversion and compensate
for render width; they are not multiplied by dt. Look-ahead does not add another
rotation while free look is active. Disabling it immediately hands the current
angles back to automatic look-ahead, without snapping or waiting for centring.

Flight continues: no throttle, engine, cruise or autopilot command is sent.
Mouse-flight production and its arming messages are suppressed while enabled.
Space changes the look lock temporarily; leaving look restores the flight lock
saved on entry, including after unlocking to click the icon. Automatic head look
regains ownership immediately on exit and smooths from the current angles.
Old hold/direction state is cleared at
handoff and a centred cursor when returning to locked mouse flight. Already-held
keyboard turning is resubmitted once on entry. Keyboard controls remain live:
only the cursor's rendering is hidden, not the shared gameplay input flag.

LMB press/release and drag moves are consumed before mouse key bindings, weak
point selection and unclaimed-click dispatch. Clicks on HUD widgets retain their
normal behavior. Other buttons and wheel are not remapped. Menu/focus/device
loss releases capture and requires release before a new drag. Cockpit load,
attach, deactivate, missing ship, tradelane, transitions and HUD destruction
reset the mode. HUD visibility is recomputed so Backspace does not permanently
hide the new button.

Implementation: Client/cockpit_free_look.{h,cpp}, cockpit_free_look_state.h;
hooks in input_manager, player_behavior, space_camera_first, space_camera_game
and hud_maneuvers. No game data or extra icon asset is required.

Verification: numerical head-motion checks, production input-handoff checks
and camera gating checks passed. Freelancer Release Win32 was rebuilt with v145.
These fixtures mock the engine/device boundaries; in-game input checks remain
necessary after installation.

Manual flight checklist after installation: toggle/drag/release; click every
HUD button; repeated quick LMB clicks; mouse lock on/off; holding steering keys
during entry; autopilot/cruise continuity; menu/chat, Alt-Tab and lost input;
camera changes, death/respawn, docking/jump/tradelane; Backspace and status
expand/collapse; cockpit meshes with custom/zero head_turn limits. Also check
entry with Space already locked, repeated Space on/off, LMB release while locked,
return from menus/Alt-Tab while locked, maneuver auto-hide and different resolutions.

Existing look-ahead checks and behavior
--------------------------------------

Run tools/cockpit/build_check.ps1 from PowerShell for numerical checks.
The script uses the same local MSVC/Windows SDK as tools/radar/build_check.ps1.
Run python tools/cockpit/check_scene_pass.py for production cockpit render-order
and tunnel-lighting checks (RP8 and RP9 branches, with recorded render boundaries).
The world weak-point wire must run before the cockpit clears scene depth. Tunnel
states 2/3 reuse FClientShipGameobj::Slot184 so the cabin gets both jump ambient
and the animated tunnel light, including the normal lighting-option handling.

[Cockpit] head_turn = horizontal_degrees, vertical_degrees
The formerly unused key now limits automatic head rotation during manual steering.
Defaults on each cockpit load: 30, 25. Each axis is clamped to 0..90 degrees;
non-finite/negative values disable that axis. head_turn = 0, 0 disables the effect.
No game INI files are changed by this implementation.

The camera reads the behavior manager's last player direction, maps right/down
input to pitch/yaw WITHOUT the ship steering sensitivity gain, and transforms it
into the resting eye frame relative to the ship. It does not follow axis throttle:
physics steering corrections must not pull the head back during a held command.
A 2.5% dead zone suppresses tiny commands. Exponential response time is
0.64 seconds while steering and 0.96 seconds on return (about 95% in 3 times that
for movements below the speed cap). Each axis is capped at 45 degrees/second while
turning and 30 degrees/second while returning. The rate-limited exponential is
integrated across the transition within a frame, retaining FPS independence.
Held input keeps a stable target angle. Mouse deflection scales the head angle
directly; changing ship steering sensitivity cannot amplify head movement.
Only eye orientation changes; existing cockpit mesh placement, head translation,
roll, shake, HUD rendering and ship steering mode are retained.

State lives outside the fixed-size first-person camera and is reset on construction,
attach, deactivate, load, release or missing ship. Blocked input, cinematic letterbox,
tradelane and disabled manual maneuvering suppress look input but preserve the current
angles, returning smoothly to forward with the same 0.96-second response and
30-degree/second cap as releasing the controls. Thus autopilot / jumpgate takeover
does not instantly centre a sideways view. With no user turning input it also returns
smoothly to forward. Mouse inversion and keyboard commands are already reflected
in the ship's steering command. A zero/invalid dt freezes the response; hitches are
limited to a 0.25-second response step.

Automated checks: 4/30/60/144/240 FPS response and reversal, settling after release,
angle limits, right/up axis signs, orthonormal rotation, pause, hitches, invalid
inputs and reset. These do not substitute for an in-game check of camera integration.
python tools/cockpit/check_head_gate.py exercises production UpdateHeadLook with
mocked engine boundaries: each blocking condition, blocked mouse input, pause,
gradual centring at 30/60/144 FPS and smooth resumption of manual look.

Flight checks: left/right/up/down and diagonals; mouse lock/hold/release; keyboard;
inverted mouse; gun aiming and target selection at large head angles; cockpit
on/off; third-person/turret/rear switching; docking, tradelane, jump and new ship;
several cockpit meshes for side gaps/clipping. Tune head_turn after restoring the
desired cockpit INIs. The third-person level-steering mode is not changed.

Regression check: python tools/cockpit/check_free_look_handoff.py runs the
production toggle/reset/mouse handlers with mocked engine boundaries. It checks
restoring the entry flight lock after Space unlock, immediate head handoff,
normal mouse events after exit and consuming a swallowed LMB release only once.
