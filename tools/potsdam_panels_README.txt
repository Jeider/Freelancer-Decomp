Potsdam solar rotors, 2026-11-13

FOLLOW-UP: whole solar plants now rotate, including their central hubs.
tools/potsdam_full_rotors.py moved all seven source visual pieces and seven
collision leaves into each Rotor. Root has no visible geometry and only a
2 cm physics anchor enclosed inside the middle hub for every rotation angle.
Moving collision leaves: 21. Draw groups: 9. Animation and joint transforms
are unchanged. Native animation and SUR checks passed again. CMP/SUR installed;
active archetype and Pythonlancer template already refer to these same files.
Original stationary-hub implementation below is historical.

Installed pdm_top_rotating in place of the static pdm_top object. Three axles
are baked into Root; each original six-panel assembly is a separate Rotor01/02/03
Rev joint. Pivots/placement retain original Potsdam solar-plant transforms.
Rotation is local X, one revolution per 90 seconds, driven by InternalFX and
Sc_potsdam_solar_rotation, with five quarter-turn keys. No solar spin setting.
Rotor-center hardpoints belong to the moving parts. Draw groups: 10 versus
3 for the prior completely static TOP, still below the original TOP's 57.

SUR contains Root (three original axle leaves) and three independent !fxd
rotors (six original panel leaves each, in local coordinates). No stationary
duplicate of moving panel collision. CSolar uses physics type 1; PhySys creates
separate bodies for !fxd parts and AnimDB updates their golem targets from the
animated transforms. No engine code/binary changes were required.

Validation: exact local mesh/LOD records and original leaf topology; Common.dll
loaded all four SUR parts. Native EngBase.dll created the actual CMP and played
the actual clip through MixerWalk for 723 steps at 0.125 s, crossing the loop
seam. All three world orientations matched expected local-X rotation, centers
stayed fixed, and step sizes remained constant. This checks animation and SUR
loading, not an in-game ship collision/contact simulation.

Pythonlancer active template now selects the animated archetype. Generation
was not run. Prior template: potsdamStaticOriginal.py. Prior system:
rh_berPanelsOriginal.ini. Original static models remain for old snapshots.
One minimal rollback set under out/potsdam_panels/rollback, with aliases to
those snapshots instead of duplicate copies. Staging removed after install.
Native animation log/stamps, manifests, installed hashes retained in that output.

Tools: potsdam_panels.py, check_potsdam_animation.cpp/.py,
install_potsdam_panels.py. Native SUR check reuses check_valensia_mega_native
with valensia_mega.OUT assigned to potsdam_panels.OUT before import.
