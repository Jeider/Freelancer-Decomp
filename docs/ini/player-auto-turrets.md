# Player auto turret configuration

**English** · [Русский](../ru/ini/player-auto-turrets.md)

Port-only player turret control. Requires `FreelancerPlayerAutoTurrets=1` in Common and freelancer; the build default is 0. See [controls and implementation](../player_auto_turrets.md).

**File location:** `port.ini` next to `freelancer.exe`, read through `PortConfigInt`. Runtime enablement is cached on first use; restart after editing. Missing configuration is disabled. This feature operates only in single player.

## `[AutoTurrets]`

| Key | Type | Default | Meaning / accepted values | Source |
|---|---|---|---|---|
| `enabled` | integer boolean | `0` | `0` disables; any nonzero integer enables the SP controller and UI. Does not issue an order. | [Enabled](../../src/freelancer/Client/player_auto_turrets.cpp) |
| `reserve_percent` | integer | `35` | Initial weapon-power floor, clamped to `0..90`. Saved character/hull preferences take precedence. UI cycles `0 → 20 → 35 → 50 → 0`; resume threshold is floor + 10 percentage points. | [Reconcile / CycleReserve](../../src/freelancer/Client/player_auto_turrets.cpp) |

Keys are single-valued. There are no `engclass`, scanner-class, perk or booster settings required by this controller.

## User preferences

**File location:** `GetUserDataPath()` + `\auto_turrets.ini`, normally `Documents\My Games\Freelancer\auto_turrets.ini`. This is separate from game saves and `UserKeyMap.ini`. It uses the Windows profile APIs, not the game BINI reader. Writes occur when UI preferences change.

Sections are `v1.<character-name UTF-16 hex>.<hull-archetype-id hex>`. At most 24 character-name code units are encoded, matching the character-name buffer. No names become filesystem path components. The version is part of the section name.

| Key | Type | Default | Meaning / accepted values | Source |
|---|---|---|---|---|
| `reserve_percent` | unsigned profile integer | clamped `port.ini` value | Clamped above to 90. A malformed negative profile integer is read unsigned and therefore clamps to 90. UI writes only the preset values. | [LoadPreferences](../../src/freelancer/Client/player_auto_turrets.cpp) |
| `mode` | profile integer | `2` | `1`: selected target; every other value: hostile free fire. Preference only, never armed state. | [LoadPreferences / SetPreferredMode](../../src/freelancer/Client/player_auto_turrets.cpp) |
| mounted hardpoint name, e.g. `HpTurret01` | profile integer boolean | `1` | Membership of that hardpoint in the automatic group; `0` excluded, nonzero included. Applies to eligible equipment. New equipment appearing during an order is excluded until a subsequent explicit selection/start cycle. | [SavedSelection / ToggleMember](../../src/freelancer/Client/player_auto_turrets.cpp) |

No target, current order, firing permission, cooldown or energy is persisted. Missing/unavailable character identity skips persistence. Failed writes produce an `Auto turrets: could not save preferences` diagnostic; the live selection remains usable.

## Keyboard and resources

The four `USER_PLAYER_AUTO_TURRET*` commands are registered by the client, appended to the cockpit accelerator group and shown in the ordinary keyboard preferences without modifying `KeyMap.ini` or `keylist.ini`. Bindings are stored through the normal `UserKeyMap.ini` mechanism. No default keys are imposed. The native camera command `USER_AUTO_TURRET` is unchanged.

HUD text uses the private virtual IDS range `0x7fee0000..0x7fee000b` and `0x7fee0020..0x7fee0023`; `PortLanguage() == ru` selects Russian, otherwise English. The optional staged icon has a fixed path `interface\hud\HUD_player_auto_turret.3db`; without it the existing targeted-object icon is used. These are implementation constants, not INI keys.
