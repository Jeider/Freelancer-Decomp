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
