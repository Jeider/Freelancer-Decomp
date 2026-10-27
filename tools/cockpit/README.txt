Cockpit head look-ahead prototype

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
