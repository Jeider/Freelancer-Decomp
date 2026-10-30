Flight telemetry recorder (schema 1)
===================================

Status: implemented, dormant. No hotkey, menu, INI option, automatic start,
default output directory or caller of Start is installed. The activation policy
is intentionally deferred. It does not modify saved games or train NPCs yet.

Integration API: src/freelancer/Client/flight_telemetry.h
Call only from the client/game thread:
    FlightTelemetry::Start(L"D:\\captures\\unique-flight.jsonl");
    FlightTelemetry::IsRecording();
    FlightTelemetry::Stop("requested");
    FlightTelemetry::LastError();

The directory must already exist. Start requires a live player ship and creates
a NEW file exclusively, never replacing an existing one. Do not call Start every
frame. A failed Start/Stop returns false; LastError reports the reason. A repeated
Start while active returns false and leaves the existing recording untouched.
After asynchronous failure, IsRecording becomes false; call Stop to close the
file, then Start with a new path if desired. An empty stop reason is permitted.

The recorder stops on leaving space, loss/change of player ship, connection or
system, or a change in save-load revision. These are recording boundaries, not
activation triggers. Pausing freezes simulation time; focus loss invalidates the
held-input baseline. Regaining focus produces a fresh baseline.

Format: UTF-8 JSON Lines, one object per line, native game distance units, seconds,
radians. Header identifies schema, executable build time, ship/system/archetype,
mass, ship control constants, equipment IDs/archetypes and coordinate conventions.
No character names, chat text, OS-wide keyboard events or account credentials.
Archetype IDs do not fingerprint mod assets: retain the mod/config version alongside
a future dataset. Header equipment is the STARTING loadout; damage reports carry
subsequent equipment destruction. No full deterministic replay is promised.

Event envelope: type, sequence (0-based), wall_us (monotonic since Start),
simulation_s (accumulated nonpaused frame dt), frame, data. Sequence orders ties.
The simulation timestamp is a frame boundary, not a subframe simulation clock.
wall_us captures the time the client observes the event, not hardware timestamps.

Records:
- input_baseline: held mapped command IDs 0..255, validity; start and focus changes.
  Binding-level observation, not synthesized presses. Beyond this ID range there
  is no baseline; live mapped events still retain their actual IDs.
- mapped_input: command ID, event kind, down/repeat, modifiers and input context.
  Hooked at KeyMap dispatch BEFORE handler filtering; an event may be rejected by
  the HUD. Logical input events are kept between samples, including short taps.
  Raw mouse motion and untranslated key releases are not an OS input log.
- steering_input: processed flight direction from keyboard or normalized mouse
  steering, before the direction gate. Keyboard is emitted when its command is
  resubmitted, mouse on engaged flight updates. This is not raw cursor delta or
  cockpit-camera look. Initial held state and current actuator snapshots supplement
  change-driven events; lack of an event does not mean zero input.
- behavior_command: forwarded player behavior commands and input origin
  (mapped_input, keyboard_steering, mouse_steering, synthetic, unknown). This records
  delivery to the behavior manager, NOT proof that its behavior accepted a command.
  Direct writes by Common/autopilot are represented by actuator state in snapshots;
  do not treat every command or nonautomatic shot as human training input.
- snapshot: initial state and up to 30 observations per simulation second, after
  physics and control processing, before object reap. Contains ship world position,
  orientation, velocities, health/shields, energy, engine/thruster/cruise state,
  throttle, axis throttle, nudge, strafe, selected target and relative local vectors,
  distance/closing speed, target attitude, subtarget, and control context.
  The initial phase is marked separately; docking state there is unknown/null.
  Context includes pause, input/UI focus, letterbox, route, native behavior and
  scripted flight action, mouse flight and cockpit look. Separate direction from
  velocity when interpreting engine-kill boosting; engine_off is not zero speed.
  Up to 16 nearest live entries from the EXISTING scanner cache are included.
  Scanner cache count and truncation are explicit. The recorder never refreshes
  scans or changes filters: this is neither a full threat list nor an obstacle map.
  Low frame rate yields fewer real observations and missed_sample_intervals;
  no repeated states are invented to fill a stall. Pause/focus transitions can
  generate additional snapshots. Missing/non-finite numeric values are null.
- shot: successful local launcher fires, equipment ID, automatic flag, optional
  world aim point. The flag distinguishes the auto-turret firing path. Failed
  attempts are not shots. Barrel-aim fire has a null aim point.
- damage_report: all server damage reports received by the client, object,
  inflictor/owner, cause, destruction, subobject remaining_hp and fate. remaining_hp
  is NOT damage amount. Cause 4 is collision damage, not a log of every physical
  contact. These reports do not establish a one-to-one shot/hit relationship.
- collision: resolved local physics contacts (including beam hits), before their
  dispatch to both objects, with object/subobject IDs, world contact point, normal
  and relative velocity as delivered to side B (side A receives negated vectors).
  One record per dispatched pair; repeated physical contacts remain separate.
  A contact does not prove damage, and local projectile IDs may not be unique or
  network-assigned. Correlate with damage_report; do not invent shot attribution.

World orientation is stored as row arrays of a local-to-world matrix, with its
columns the local axes; forward is -Z. Local relative velocity is the world
velocity difference expressed in player axes, without a rotating-frame derivative.

Persistence and completeness:
- 4 MiB bounded queue; worker thread only receives serialized strings, never game
  object pointers. Disabled hooks do not collect state, traverse scans or open files.
- Start writes the header; Stop drains/joins/closes. Steady-state disk I/O and
  one-second stdio flushes occur in the worker. Start/Stop can block on disk.
- Queue overflow/allocation/I/O failure disables recording. No silent sampling or
  event dropping is used to disguise overload. LastError remains available.
- Footer: complete, reason, records. Require complete=true, a full final newline,
  valid JSON and contiguous sequences before accepting a session for training.
  A crash/disk failure may leave a partial final line or no footer. Recovering a
  valid prefix is possible but does not make it a complete demonstration.
- fflush/fclose are checked; this is ordinary buffered persistence, not a guarantee
  against power failure. A terminal close error is also exposed through LastError.

Verification (no game or recording activation required):
    python tools/flight_telemetry/check.py
The production writer is compiled and its output parsed independently with Python.
Checks cover idle/start/stop/restart, Unicode paths, no overwrite, short input taps,
drain/order/timestamps, overflow, shutdown, locale/nulls and paused/stalled sampling.
The production game adapter also runs against a deterministic world facade; JSON
checks validate target-relative vectors, engine-off boosting, health/energy, nested
command origins, successful-shot records, damage semantics, pause/focus resync and
save/system/ship boundaries. Actual in-game capture/performance remains untested
until an activation policy is chosen.
