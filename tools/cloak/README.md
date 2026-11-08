# Configurable cloaking

Add these keys to a `[CloakingDevice]` equipment definition (seconds):

```ini
default_state = false
cloak_duration = 30
cooldown_time = 20
toggle_cooldown = 0.3
```

Any of these keys opts the device into the new behavior. Defaults for an opted-in
device are visible, unlimited duration (`-1`), zero recharge and a 0.3-second
minimum toggle interval. Devices without any new keys retain retail behavior,
including starting cloaked and allowing animation reversal for story scripts.

`default_state = true` starts fully cloaked. `cloak_duration = -1` is unlimited;
`0` immediately starts revealing once the cloak animation completes.
`cooldown_time = 0` permits reuse after revealing and the toggle interval finish.
The existing animation lengths/effects remain unchanged. In the legacy engine's
terminology `cloakout_time` is the disappearing animation, `cloakin_time` is the
appearing animation. Manual commands are ignored during either animation.

The duration starts only when fully cloaked. Manual deactivation and expiration
both start a complete recharge **after** fully revealing. Rejected requests do
not start effects or restart timers. Device destruction overrides all locks.
Health shows seconds remaining under the cloak icon, `...` during transitions
and infinity for an unlimited active cloak. The icon is disabled while locked.

Cooldowns are saved as `cloak_cooldown = archetype_id, seconds` in `[Player]`.
A load during active cloaking restores visibility and the full reveal/recharge
liability. A load during recharge restores its remaining time. The state is per
character, not a HUD preference. When the device is absent (e.g. docked), its
remaining cooldown is retained; offline time does not consume it. Use one
cloaking device per ship; persisted recharge is keyed by device archetype.

Single-player's shared ship is ticked once by Common, not once again by the
server wrapper. Multiplayer validates requests on the server and broadcasts
the accepted state, including automatic expiry and corrections to the sender.
Periodic state announcements also cover newly observing clients. Both peers
must use matching equipment configuration and updated binaries. The existing
wire protocol carries on/off state, not a timer snapshot: remote countdowns
are estimates, especially after reconnecting with a saved cooldown. The server
still refuses activation until the actual recharge completes.

`prepare.py` stages matching Common/Server/client binaries and adds the four
keys above to the game's existing `pl_cloak_slow` and `pl_cloak_fast` definitions
(preserving existing values if already configured). Other cloak definitions,
animation durations, loadouts and saves are not edited by installation.

Validation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/health_equipment/build.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/cloak/check.ps1 -GameBin src/obj/health_equipment/bin
python -B tools/cloak/prepare.py
```

The prepared installer verifies binary imports and original file hashes, requires
the game/server to be closed, backs up every replaced file and rolls back errors.

## Ship refraction (RP9)

The client now draws moving background refraction over the actual hull and child
meshes while cloaking. Three travelling waves also displace the visual silhouette.
The transition is stronger than the residual ripple at full cloak; native opacity,
cloak timers, targeting, radar and collisions retain their existing behavior.
Own-ship refraction is omitted in first-person view. Scene depth rejects foreground
objects both at the destination pixel and over the displaced sampling footprint.

Optional settings in `bin/port.ini` (these defaults apply when absent):

```ini
[Render]
cloak_refraction = 1
cloak_refraction_strength = 1.0
```

Strength ranges from 0 to 3 and scales refraction plus silhouette deformation.
Setting the switch or strength to zero restores the native fade. At most 16 nearby
ships, 128 children per ship and 512 cached meshes participate; distance attenuation
runs from 3 to 5 km and nebula visibility further reduces the effect. Animation
uses pause-gated simulation time. One scene snapshot is shared by all cloak draws.
RP8 and unavailable shader/capture paths keep the native rendering. Uniform space
has little visible refraction by design; stars, clouds and structures reveal it.

```powershell
python tools/cloak/check_visual.py
python tools/cloak/check_lifetime.py
python tools/cloak/build_visual.py
python tools/cloak/install_visual.py
python tools/cloak/install_visual.py --apply
```

The checker decodes installed CMP part/LOD records using the production decoder
and renders the production shader on D3D9 HAL. It checks pause, time wrap, both
depth partitions, foreground colour leakage (with a negative control), viewport
bounds and exact identity outside the deformed mesh. PNG frames and a diagnostic
animation are written to `src/obj/cloak_visual`; this is a test scene, not an
in-game capture. The isolated client build retains the installed `field_fog`
baseline's other link inputs, including the earlier ASF/Sphere2 fixes.

VMeshPart facets are borrowed and are deleted directly during archetype unload;
their AddRef/Release methods do not extend their lifetime. The cloak cache owns
only GPU vertex copies and uses geometry content plus part ranges as keys. Library
fingerprints are memoized only for the current draw. The lifetime regression runs
the production cache functions against a freed, inaccessible engine facet and
checks same-address model replacement, hidden-LOD restoration and repeated teardown.
The original 2026-11-05 implementation reproduces the unload access violation in
the negative control; the fixed implementation makes no Release calls on facets.

## Player configuration and mission conditions

`restore_config.py` restores `pl_cloak_slow` and `pl_cloak_fast` in both installed
`DATA/EQUIPMENT/weapon_equip.ini` and the Pythonlancer template
`Assets/Pythonlancer/templates/hardcoded_inis/static_content/weapon_equip.ini`.
Default state is off, duration 30 seconds, recharge 20 seconds, toggle lock 0.3 seconds.
Duration starts after the fade out; recharge starts after the fade in.
`check_installed.py` renders Easy/Normal/Hard templates and exercises the installed Common.dll.

The port adds `Cnd_CloakState = <ship>, <bool>` (current active-device state) and
`Cnd_ActCloak = <ship>, <bool>` (a subsequent accepted switch), where true means
enabled and false means disabled. See the [mission reference](../../docs/ini/missions-conditions.md).
The server queues native equipment notifications and dispatches copied values after
physics update, avoiding mission actions inside equipment iteration. An event sequence
prevents old queued transitions from firing newly armed conditions. No class layouts
or existing network packets change; multiplayer delivery uses the existing server controller.

```powershell
python tools/cloak/restore_config.py
python tools/cloak/check_installed.py
python tools/cloak/restore_config.py --apply
python tools/cloak/build_mission.py
python tools/cloak/check_mission.py
python tools/cloak/check_mission_load.py
python tools/cloak/install_mission.py
python tools/cloak/install_mission.py --apply
```

The mission test executes production condition and queue methods with actual native
INI parsing, CShip objects and CECloakingDevice transitions. Mission labels and controller
delivery are test fixtures; this is not a complete in-game or multiplayer session test.
Installation stages Server/Content and matching PDBs, checks baseline/source hashes,
requires the game closed, and backs up all replaced files with rollback on copy failure.
