# Player auto turret configuration

**English** · [Русский](../ru/ini/player-auto-turrets.md)

Port-only player turret control. Requires `FreelancerPlayerAutoTurrets=1` in Common and freelancer; the build default is 0. See [controls and implementation](../player_auto_turrets.md).

**File location:** `port.ini` next to `freelancer.exe`, read through `PortConfigInt`. Runtime enablement is cached on first use; restart after editing. Missing configuration is disabled. This feature operates only in single player.

## `[AutoTurrets]`

| Key | Type | Default | Meaning / accepted values | Source |
|---|---|---|---|---|
| `enabled` | integer boolean | `0` | `0` disables; any nonzero integer enables the SP controller and UI. Does not issue an order. | [Enabled](../../src/freelancer/Client/player_auto_turrets.cpp) |
| `reserve_percent` | integer | `35` | Initial weapon-power floor, clamped to `0..90`. The value in the current game save takes precedence. UI arrows adjust it by 5 percentage points; resume threshold is floor + 10. | [BehaviorFor / SetReservePercent](../../src/freelancer/Client/player_auto_turrets.cpp) |

Keys are single-valued. There are no `engclass`, scanner-class, perk or booster settings required by this controller.

## User preferences

**File location:** `GetUserDataPath()` + `\auto_turrets.ini`, normally `Documents\My Games\Freelancer\auto_turrets.ini`. This is separate from game saves and `UserKeyMap.ini`. It uses the Windows profile APIs, not the game BINI reader. Writes occur when UI preferences change.

Sections are `v1.<character-name UTF-16 hex>.<hull-archetype-id hex>`. At most 24 character-name code units are encoded, matching the character-name buffer. No names become filesystem path components. The version is part of the section name.

| Key | Type | Default | Meaning / accepted values | Source |
|---|---|---|---|---|
| `enabled` | profile integer boolean | `0` | Legacy fallback only when the current save has no explicit master value. Options > Miscellaneous writes the native save on Apply instead. | [LoadPreferences](../../src/freelancer/Client/player_auto_turrets.cpp) |
| mounted hardpoint name, e.g. `HpTurret01` | profile integer boolean | `1` | Membership in automatic control; `0` excluded, nonzero included. Restored for newly discovered eligible guns, regardless of the global master switch. | [SavedSelection / ToggleMember](../../src/freelancer/Client/player_auto_turrets.cpp) |

Old profile `mode` and `reserve_percent` entries are no longer read. Individual hardpoint choices still use this INI; the global master and reserve use the native save `interface` word (bits 22..28). Missing character identity skips per-hardpoint persistence. A failed profile write leaves the live selection usable and emits a diagnostic. Targets, cooldowns and energy are transient.

## Keyboard and resources

The checkbox and reserve arrows are on the native Options > Miscellaneous page, available after loading a game. Per-gun buttons remain beside weapon rows. The native camera command `USER_AUTO_TURRET` is unchanged.

HUD text uses the private virtual IDS range `0x7fee0000..0x7fee000b` and `0x7fee0020..0x7fee0023`; `PortLanguage() == ru` selects Russian, otherwise English. The optional staged icon has a fixed path `interface\hud\HUD_player_auto_turret.3db`; without it the existing targeted-object icon is used. These are implementation constants, not INI keys.
