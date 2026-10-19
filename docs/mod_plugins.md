# Other mod plugins

**English** · [Русский](ru/mod_plugins.md)

Closed-source plugins a mod (The Nomad Legacy) loads, and the changes its patched `server.dll`
makes, rewritten from their disassembly. Each is switched in `port.ini` (`[Plugins]`,
`[ModServer]`, `[WingAnim]`).

| Property (`src/Freelancer.Diagnostics.props`) | Define | Sheet default |
|---|---|---|
| `FreelancerModPlugins` | `FREELANCER_MOD_PLUGINS` (client, `Common.dll`, `Server.dll`, `Content.dll`) | 1 |

## Plugins

| `[Plugins]` key | Plugin | Port |
|---|---|---|
| `MultiCruise` | MultiCruise.dll: `[Engine] cruise_speed` | `Engine::read` keeps it (side table); `CEEngine` uses the engine's own speed where retail reads `CRUISING_SPEED` (`common_ceengine.cpp`; the plugin rewrote that global from `GetCruiseDrag`, so all ships shared it, and its default was 0 in multiplayer). The engine stats show "Cruise Speed" as jflp did (`dealer_equip_stats.cpp`, ids 1703 / 1760) |
| `Invisibility` | Invisibility.dll: Ctrl + the collect-loot key toggled the cloak | the unused keymap command `USER_CLOAK` (0x8e) in `HUD_Status::OnEvent`, toggled from the device's real state through `CliShipActivateEquip`. The plugin flipped a private flag (its first press switched off) and called the local server directly (single player only). Bind `USER_CLOAK` in `keymap.ini` / `keylist.ini` |
| `Interceptor` | Interceptor.dll: `[Gun] interceptor = true` fires in cruise | `Gun::read`, `CEGun::CanFire`. The plugin read only `DATA\EQUIPMENT\gun_equip.ini`; every `[Gun]` is read |
| `PowerDamage` | PowerDamage.dll: `[Explosion] force_energy_damage = true` | `Explosion::read`; `EqObj::explosion_hit_power` lets it through `no_energy_damage` |
| `WingAnim` | replaces AnimKey.dll (console.dll `anim wings` on Ctrl + the cruise key) | see below |

## The wing animation (`WingAnim`)

`[InternalFX] use_animation_oneshot = <script>` plays the script once when the equipment is
created, instead of `use_animation`'s loop (`CEInternalFX` ctor, `common_cefx.cpp`). A player
ship with such an InternalFX (the mod's `launch_extend`) gets the wing manager
(`wing_anim.cpp`, ticked from `UpdateSpaceDocking`):

- the launch script extends the wing; then the wing script (`[WingAnim] script`, default
  `Sc_extend wing`: forward folds, reverse extends) takes over the same playback slot;
- cruise engaged: fold; cruise off: extend;
- docking with a station, base or planet (`get_docking_port`, not a trade lane, gate, hole or
  airlock): fold;
- `[WingAnim] key` / `modifiers` (virtual-key code; 1 Shift, 2 Ctrl, 4 Alt): toggle;
- a request made while the wing moves (the launch included) is queued and runs when the move
  ends; the last request wins (extending + docking: the wing folds right after it is out).

## `[ModServer]`: the mod's patched server.dll

| Key | Retail place | Effect |
|---|---|---|
| `no_energy_damage` | `damage_power` `RET 8` at `.text:06ceafc0` | no energy damage (PowerDamage re-enables forced explosions) |
| `full_explosion_hull_damage` | `JP +0x0c` -> `JP +0` at `06ce960c` | the hull band of an explosion is always 3 |
| `view_radius_sq_scale` | `.rdata:06d66aec` / `06d66af0` (6.25e6 / 2.5e7) x10 | how far objects are sent to a client |
| `update_radius` | `.data:06d88af0` 10000 -> 100000 | the update sphere around each player |
| `plain_saves` | `"rt"` instead of `"wb"` at the three FLS1 rewrites | saves stay plain text |
| `account_folder` | `.data:06d8d204` `Accts` -> `Acct3` | the single-player save folder |

## Deviations

All port-only; with the property off the behaviour is retail's.
