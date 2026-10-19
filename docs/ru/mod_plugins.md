# Другие плагины мода

[English](../mod_plugins.md) · **Русский**

Плагины без исходников, которые загружает мод (The Nomad Legacy), и правки его пропатченного
`server.dll`, переписанные по дизассемблеру. Каждый включается в `port.ini` (`[Plugins]`,
`[ModServer]`, `[WingAnim]`).

| Свойство (`src/Freelancer.Diagnostics.props`) | Define | По умолчанию в листе |
|---|---|---|
| `FreelancerModPlugins` | `FREELANCER_MOD_PLUGINS` (клиент, `Common.dll`, `Server.dll`, `Content.dll`) | 1 |

## Плагины

| Ключ `[Plugins]` | Плагин | Порт |
|---|---|---|
| `MultiCruise` | MultiCruise.dll: `[Engine] cruise_speed` | `Engine::read` сохраняет значение (отдельная таблица); `CEEngine` берёт скорость своего двигателя там, где ретейл читает `CRUISING_SPEED` (`common_ceengine.cpp`; плагин переписывал этот глобал из `GetCruiseDrag`, поэтому все корабли делили одно значение, а в мультиплеере оно было 0). В характеристиках двигателя строка «Круизная скорость», как в jflp (`dealer_equip_stats.cpp`, ids 1703 / 1760) |
| `Invisibility` | Invisibility.dll: Ctrl + клавиша сбора лута включала маскировку | неиспользуемая команда раскладки `USER_CLOAK` (0x8e) в `HUD_Status::OnEvent`, переключение по реальному состоянию устройства через `CliShipActivateEquip`. Плагин переключал свой флаг (первое нажатие выключало) и вызывал локальный сервер напрямую (только одиночная игра). Назначьте `USER_CLOAK` в `keymap.ini` / `keylist.ini` |
| `Interceptor` | Interceptor.dll: `[Gun] interceptor = true` стреляет в круизе | `Gun::read`, `CEGun::CanFire`. Плагин читал только `DATA\EQUIPMENT\gun_equip.ini`; здесь читается каждый `[Gun]` |
| `PowerDamage` | PowerDamage.dll: `[Explosion] force_energy_damage = true` | `Explosion::read`; `EqObj::explosion_hit_power` пропускает такой взрыв мимо `no_energy_damage` |
| `WingAnim` | заменяет AnimKey.dll (`anim wings` консоли console.dll по Ctrl + клавиша круиза) | см. ниже |

## Анимация крыла (`WingAnim`)

`[InternalFX] use_animation_oneshot = <скрипт>` проигрывает скрипт один раз при создании
оборудования вместо цикла `use_animation` (конструктор `CEInternalFX`, `common_cefx.cpp`).
Корабль игрока с такой InternalFX (у мода — `launch_extend`) получает менеджер крыла
(`wing_anim.cpp`, вызывается из `UpdateSpaceDocking`):

- скрипт взлёта раскладывает крыло; затем тот же слот проигрывания занимает скрипт крыла
  (`[WingAnim] script`, по умолчанию `Sc_extend wing`: вперёд складывает, назад раскладывает);
- круиз включён — сложить; выключен — разложить;
- стыковка со станцией, базой или планетой (`get_docking_port`, не торговая линия, врата,
  туннель или шлюз) — сложить;
- `[WingAnim] key` / `modifiers` (код виртуальной клавиши; 1 Shift, 2 Ctrl, 4 Alt) — переключить;
- запрос во время движения крыла (включая взлёт) ставится в очередь и выполняется, когда
  движение закончится; побеждает последний запрос (раскладывается + стыковка: крыло сложится
  сразу после того, как разложится).

## `[ModServer]`: пропатченный server.dll мода

| Ключ | Место в ретейле | Действие |
|---|---|---|
| `no_energy_damage` | `damage_power` `RET 8` по `.text:06ceafc0` | энергетического урона нет (PowerDamage возвращает его отмеченным взрывам) |
| `full_explosion_hull_damage` | `JP +0x0c` -> `JP +0` по `06ce960c` | полоса урона взрыва по корпусу всегда 3 |
| `view_radius_sq_scale` | `.rdata:06d66aec` / `06d66af0` (6.25e6 / 2.5e7) x10 | на каком расстоянии объекты отправляются клиенту |
| `update_radius` | `.data:06d88af0` 10000 -> 100000 | сфера обновления вокруг каждого игрока |
| `plain_saves` | `"rt"` вместо `"wb"` в трёх перезаписях FLS1 | сейвы остаются обычным текстом |
| `account_folder` | `.data:06d8d204` `Accts` -> `Acct3` | папка сейвов одиночной игры |

## Отклонения

Всё есть только в порте; с выключенным свойством поведение как в ретейле.
