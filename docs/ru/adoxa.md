# Плагины adoxa

[English](../adoxa.md) · **Русский**

[Jason Hood (adoxa)](https://adoxa.altervista.org/freelancer/plugins.html) написал десятки
небольших плагинов для Freelancer. Каждый патчит `freelancer.exe`, `common.dll`, `server.dll`
или `content.dll` ретейла по жёстко заданным адресам, поэтому порт не может их загрузить; их
поведение переписано здесь по публичным исходникам (последним версиям) в тех модулях, которые
они патчили.

| Свойство (`src/Freelancer.Diagnostics.props`) | Define | По умолчанию в листе |
|---|---|---|
| `FreelancerAdoxa` | `FREELANCER_ADOXA` (клиент, `Common.dll`, `Server.dll`, `Content.dll`) | 1 |

Каждый плагин включается своим ключом в `port.ini [Plugins]` (`src/include/port_plugins.h`
`PORT_PLUGIN_ON`); без ключа он выключен. Собственные файлы данных плагинов остаются на месте.

## Игровые

| Ключ | Плагин | Порт |
|---|---|---|
| `burn` | burn.dll: эффекты `atmosphere_burn_<тип корабля>` | `client_gameobj.cpp` (`0x005453f0`) |
| `chklootvol` | chklootvol.dll: NPC не гонятся за лутом, который не влезает в трюм | `LootBehavior::AcquireLootTarget` (`062ce8e8` / `062ce9d9`) |
| `ShieldOffline` | ShieldOffline.dll: щит выключен, пока у владельца нет прочности | переопределение `CEShield::IsActive` (vtable `0639d510`) |
| `LaneSpeed` | LaneSpeed.dll: `[Solar] lane_speed` | `Solar::read`, `CShip::go_tradelane`, 2500 торговой линии в `common_laneaction.cpp` |
| `JumpOutPt` | JumpOutPt.dll: эллипс и угол точки выхода из `DATA\UNIVERSE\JumpOutPt.ini` | `Solar::ChooseSystemArrivalLocation` (`06d031a6`) |
| `criticalhit` | criticalhit.dll: `[Explosion] critical_hit = процент, множитель` | `Explosion::read`; `EqObj::explosion_hit_hull` (`06ce964c`) |
| `DamagePerFire` | DamagePerFire.dll: износ пусковых установок по `damage_per_fire` | `CELauncher::ConsumeFireResources` (`06299623`) копит его; `Ship::update` (`06d014bf`) применяет |
| `EquipDrag` | EquipDrag.dll: `linear_drag` у оборудования | `Equipment::read`; `CShip::get_linear_drag` и `CShip::update` (`062b378c` / `062b0ee1`) |
| `dynastex` | dynastex.dll: динамические астероиды с `hit_pts` (±10 %) и `mass` (±10 %) | загрузчик архетипов (`062fa1e4`), `CDynamicAsteroid::init_physics` (`062a2b2e`), `cli_asteroid_dynamic.cpp` (`0x005254d2`, `0x00525eec`, `0x0052610e`, деструктор). Расширение порта `[dynastex] collision_damage = 1`: астероид сообщает о столкновении, как любой другой gameobj (`Slot1ac`), и таран наносит урон кораблю |
| `healing` | healing.dll v2.00: отрицательный урон чинит (зоны, снаряды, взрывы) | `EqObj::damage_hull`, `damage_equip`, `damage_group`, `GameObject::damage_hull`, тики зон, урон по щитам, проверки взрывов (`src/include/adoxa_healing.h`), `DamageList::add_damage_entry`, `ZONE::HasPhysicalEffect`, характеристики оружия |
| `moors` | moors.dll: корабли игрока используют причалы | `CEqObj::launch_pos`, `has_dock_hardpoints`, `Server_GetLaunchPosition`, байт посадки в обновлении системы, выбор терминала в Content |
| `storyfactions` | storyfactions.dll: `DATA\storyfactions.ini` | `EnsureStoryFactionIds` |
| `dock_key` | dock_key.dll v1.01: ключи из `DATA\dock_key.ini` для запертых стыковок | `CheckDockPermission` (`06f6c958`); снаряжение стыкующегося игрока (плагин для любого корабля смотрел первого игрока) |
| `ammolimit` | AmmoLimit.dll: `ammo_limit = n \| *f \| /f` | `Projectile::read`; `CShip::get_ammo_capacity_remaining`, лимиты у торговца и в инвентаре |
| `MatchJob` | MatchJob.dll: сложность заданий по рангу из `DATA\MISSIONS\RankDiffSP.ini` | предложения миссий в `LootProps.cpp` (`06f046eb`) |
| `MatchPlayer` | MatchPlayer.dll: уровень встреч поднимается до половины ранга игрока | `FZonePopulation::ParseValue` (`06ef9066`) |
| `callsign` | callsign.dll: позывной игрока (`port.ini [callsign] callsign = фракция [формация [n][-][n]]`) | `Gcs.cpp`: `gcs_refer_faction_*`, `gcs_refer_formationdesig_*`, `gcs_misc_dash`, два номера игрока |
| `DisableAutoLevelToggle` | правка exe `0xdbe10 94 -> 95` («Disable auto-level toggling») | `HUD_Status::OnEvent`, case `0x3e` |

## Интерфейс

| Ключ | Плагин | Порт |
|---|---|---|
| `TurretZoom` | TurretZoom.dll v1.41: приближение и сдвиг камеры турели | `space_camera_turret.cpp`, `hud_maneuvers.cpp` (колесо), `space_state.cpp` (переключение); необязательные ключи `[TurretZoom]` `fast`, `inverse`, `max`, `shift`, `ctrl`, `alt`, `s+c`, `c+a`, `small`, `large`, `switch`, `adjust`, `interval` (аргументы DLL) |
| `scroller` | scroller.dll: одна полоса прокрутки для характеристик и значений | `rich_text_win.cpp`, `nn_ship_trader.cpp` |
| `numeric` | numeric.dll (числовой урон из FL Hack) | `HudTargetableObjects::DrawOnScreenTarget` (`0x004ef771`, `0x004efd8e`) |
| `territory` | territory.dll v1.03: тексты прибытия и подписи домов на навкарте | `nn_modal.cpp`, `nn_navmap*.cpp`; ini по языку: `[Language.<код>] territory_ini` (по умолчанию `territory.ini` в `DATA\UNIVERSE`), `territory_codepage`, если в ini нет `[Settings] codepage` |
| `NoNavMap` | NoNavMap.dll: системы, которые навкарта называет недоступными (`DATA\UNIVERSE\NoNavMap.ini`) | `nn_navmap*.cpp` |
| `engclass` | engclass.dll v2.02: двигатели и генераторы с типом и классом (`hp_<fighter\|elite\|freighter>_<power\|engine>_special_N`, типы точек `0x43..0x7e`; `hp_type = ТИП МАКС, ...` в `[Ship]`) | `Ship::read`, `Power::read` / `Engine::read` и их `get_hp_type`, `CEqObj::add_equipped_item` (без предупреждения «internal type to hardpoint»), таблицы точек вида корабля, `nn_inventory.cpp`, `nn_dealer.cpp`. Строки (6 описаний, 60 названий) берутся из собственной DLL строк плагина, загруженной как данные: `[Language.<код>] engclass_resources` (по умолчанию `engclass.dll`) |

WheelScroll входит в [flplusplus](flplusplus.md). HudShift и navmapxy не перенесены.

## Отклонения

Всё есть только в порте; с выключенным свойством (или ключом) поведение как в ретейле. Где
порт отличается от плагина: `dock_key` проверяет стыкующегося игрока, `JumpOutPt` сохраняет
радиус по умолчанию как double, `engclass` хранит тип точки в таблице вместо байта `+0x6f` и
читает строки, не запуская DLL, проверки взрывов `healing` смотрят на `|hull_damage|` (байтовая
правка плагина пропускала любой взрыв), `scroller` ищет панель характеристик по имени,
`NoNavMap` останавливается на 127 системах (плагин выходил за границу массива).
