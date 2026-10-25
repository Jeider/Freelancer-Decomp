Freelancer Beta: experimental Evade / DrasticEvade player patch

Start exe\beta_evade_launcher.exe. The launcher starts this Beta with -w.
Normal Freelancer.exe / Freelancer.bat launch remains completely unmodified.
Do not start a second Beta while one is already running.

In space, select an enemy ship and click the existing Evade HUD button.
Evade uses the original Beta AI with a short, scoped player-only dodge/break
profile (2.4 seconds dodge, 1 second break). NPC profiles are not changed.
DrasticEvade applies a rightward local nudge for 0.45 seconds; its strength
depends on the ship's existing nudge force. The original icon is gray even
when enabled. Click FreeFlight to cancel. Existing mission/maneuver locks
still apply. Start from FreeFlight; docking, lanes and other autopilot modes
block these commands. The target must be a ship. There are no new global
keyboard assignments. The launcher does not enable the separate -t cheat.

DrasticEvade clears its nudge at completion and on normal behavior exit.
No game binaries, physical parameters, HUD resources or NPC data are edited.
The original SetManeuver notification path is retained.

Status: built and ABI checked against this exact Beta; in-game operation and
multiplayer behavior require play testing. This is a prototype, not a claim
that the original developers' intended player maneuver design was recovered.
Diagnostics: exe\beta_evade_patch.log (created on patched launch/use).

Disable: exit Beta and launch the normal Freelancer.exe or Freelancer.bat.
Uninstall from the repository:
  powershell -ExecutionPolicy Bypass -File tools\beta_evade_patch\install.ps1 -Mode Restore
This removes only hash-verified patch files. The audited backup remains in
Beta's beta_evade_backup folder; original EXE/Common.dll were never changed.

Only the exact SHA256-verified Beta build is accepted. The launcher does not
attach to or terminate other game processes. Initialization failure rolls
back its memory hooks and resumes the newly started game without the patch.
