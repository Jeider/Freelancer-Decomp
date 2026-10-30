# Equipment classes: internal devices and thrusters

**English** · [Русский](../ru/re/equipment_mount_classes.md)

Implemented in the working tree on 2026-10-27, over `af086d9`. This is an optional port feature; the diagnostics build enables it; runtime activation uses the switch below. Earlier research proposed `mount_family`/`mount_class`: the implementation instead uses `hp_type`, consistent with the existing equipment format. Those proposed keys and `equipment_slot_hardpoint` are **not supported**.

## Enable

Build **Common, Server and freelancer** with MSBuild property `/p:FreelancerEquipmentSlots=1` (defines `FREELANCER_EQUIPMENT_SLOTS`). In the executable's `port.ini`:

```ini
[Equipment]
internal_classes = 1
```

Restart after changing this option: the setting is cached on first use. This feature works independently of the Adoxa engclass plugin and has its own English/Russian slot captions. Client and server need matching builds, settings and content. There is no network capability negotiation. Loading a player save relocates classed cloaks into a compatible hardware slot and retains incompatible classed equipment in cargo. Do not disable the feature for saves/content that already use the new classes.

## Content

These are fragments to merge into complete equipment, ship and loadout definitions:

```ini
[Armor]
nickname = armor_plate_class3
hp_type = hp_armor_special_3
hit_pts_scale = 1.20

[Scanner]
nickname = survey_scanner_class2
hp_type = hp_scanner_special_2
range = 7000
cargo_scan_range = 1800

[Tractor]
nickname = salvage_tractor_class3
hp_type = hp_tractor_special_3
max_length = 2200
reach_speed = 500

[Ship]
; Stable slot name, family, maximum supported class.
equipment_slot = HpSlot_Armor01, armor, 4
equipment_slot = HpSlot_Scanner01, scanner, 3
equipment_slot = HpSlot_Tractor01, tractor, 3

[Loadout]
equip = armor_plate_class3, HpSlot_Armor01
equip = survey_scanner_class2, HpSlot_Scanner01
equip = salvage_tractor_class3, HpSlot_Tractor01
```

Each family supports classes **1..10**. Class 3 fits an armor slot with maximum 4; class 5 or a scanner does not. The class controls compatibility, not performance: range, hull scaling and tractor speed still come from the equipment's normal fields. Define ordinary equipment goods, icons, IDS names/infocards and market entries separately to sell these devices; a class declaration does not create a good.

Slot names are case-insensitive and must be unique on the hull, including ordinary hardpoints. Do not reuse the cargo-bay name. Unknown families, malformed levels and duplicate `equipment_slot` declarations log an error and are ignored. A malformed equipment `hp_type` remains invalid and cannot be installed; it does not silently become a legacy built-in.

The exact-class form also works:

```ini
[Ship]
hp_type = hp_armor_special_3, HpSlot_Armor01
```

This permits class **3 only**. It does not mean classes 1–3: list each accepted type explicitly, or use `equipment_slot` for a ceiling. Do not mix both formats for the same slot. The UI displays the highest accepted class; exact-class declarations with gaps still enforce those gaps.

Armor, scanner, tractor and hardware slots are **logical internal slots**, requiring no new CMP hardpoint. Thruster slots use the existing physical CMP hardpoints. They appear as inventory rows and use the mount/unmount controls; they have no clickable external mesh. Tractor beam origin remains the ship's existing `hp_tractor_source`. Declaring a slot does not create that geometric source.

## Behavior and limits

- One installed armor, one scanner and one tractor per ship. Legacy built-ins of the same family also count when installing a new classed device. Extra devices can remain unmounted in cargo.
- An installed device occupies its slot; its volume is charged to the hold when unmounted. Removing it uses the normal cargo-capacity check.
- Empty slots are allowed. With no scanner, next/previous enemy selection returns no target; automatic countermeasure threat detection skips its scan. Ordinary target cycling already handles a missing scanner. Without a tractor, collection is unavailable.
- A classed device remains `CEArmor`, `CEScanner` or `CETractor`; no new combat formulas, healing, scanner modes, cooling, skills or booster effects are introduced.
- A named binding survives `CInternalEquip::GetEquipDesc` and equipment copying. Runtime destruction removes the binding. Archetype inheritance, copying, redefinition and destruction maintain class metadata; a reloaded definition without `hp_type` becomes legacy again.
- The inventory uses the complete loadout to find occupied slots, not visible model attachments. Purchasing, mounting and ship-transfer paths handle the new internal families. Buying without a compatible free slot stores the device in cargo, subject to capacity.
- Server add/modify/load requests validate a candidate list before replacing equipment. Rejection retains the previous equipment and resends it to the client. Runtime installation also checks compatibility, including a legacy device added after a classed one.
- Ship purchase checks the destination hull before changing stock/cash, then sends the destination archetype before its loadout so server validation uses the correct ship. Existing trade messages remain separate: this is **not** an atomic economy transaction or a complete anti-cheat implementation.

Equipment without the new `hp_type` keeps its legacy internal behavior. Existing ships do not acquire slots automatically. For rollout, use new device nicknames and explicitly authored ship/loadout definitions. Converting an existing built-in nickname to a classed device requires migrating old loadouts/saves first; player save restoration moves incompatible classed devices into cargo without deleting them.

## Implementation map

| Layer | Source and responsibility |
|---|---|
| Rules | [equipment_class_rules.h](../../src/include/equipment_class_rules.h): three ten-class families, IDs `0x7f..0x9c`, after retail and engclass; `0x9d` is invalid |
| Shared service | [common_equipment_slots.cpp](../../src/Common/common_equipment_slots.cpp): INI, metadata, candidate validation, instance bindings |
| Archetypes | [common_archetype_equipment.cpp](../../src/Common/common_archetype_equipment.cpp), [common_archetype_ships.cpp](../../src/Common/common_archetype_ships.cpp), [common_archetype.cpp](../../src/Common/common_archetype.cpp): readers and lifecycle |
| Live equipment | [common_ceqobj.cpp](../../src/Common/common_ceqobj.cpp), [common_cequip.cpp](../../src/Common/common_cequip.cpp): installation and descriptor serialization |
| Hold / absent scanner | [common_cship.cpp](../../src/Common/common_cship.cpp), [common_cedroppers.cpp](../../src/Common/common_cedroppers.cpp) |
| Inventory / merchant | [nn_inventory.cpp](../../src/freelancer/Client/nn_inventory.cpp), [nn_dealer.cpp](../../src/freelancer/Client/nn_dealer.cpp), [ship_view_control.cpp](../../src/freelancer/Client/ship_view_control.cpp) |
| Labels | [equipment_slot_text.h](../../src/freelancer/Client/equipment_slot_text.h), ids_strings/ids_rdl: private virtual IDS, English/Russian |
| Server | [server_classes.cpp](../../src/Server/server_classes.cpp): PlayerData add/modify/load gates |

Existing archetype/equipment layouts, virtual tables and descriptor wire formats are unchanged. Definitions are keyed by archetype address with copy/destruction handling, so discarded duplicate nickname records cannot modify a live definition. Runtime bindings are keyed by equipment address with copy/destruction handling. No parallel equipment inventory or new generic runtime class is introduced.

## Verification and remaining integration checks

[Native fixture](../../tools/equipment_slots/README.md) exercises the real Common.dll: strict INI parsing, family/class/occupancy limits, legacy coexistence, CShip installation and hold accounting, empty-scanner target selection, descriptor preservation, inheritance, copying, metadata cleanup and reload. Separate processes check runtime on/off; compile-off has its own check mode.

Verified locally: Release/Win32 builds of Common, Server and freelancer with the build switch
on and off; native checks with runtime on/off and compile-off; Common DebugASan build and the
same native checks under AddressSanitizer. No sanitizer errors were reported. Build logs are
in the ignored workspace directory `src/obj/equipment_slots_*`; commands are in the fixture README.

Building and native checks do not replace an interactive game test. Still exercise the equipment dealer, empty/occupied rows and RU/EN labels, ship purchase, launch → dock → save → reload, SP/MP synchronization, and flight with each device removed using actual mod assets. No installed-game content rollout or interactive validation is claimed here.

## Future extensions

Cooling devices can use the same logical-slot approach, but need their own runtime component and Heat model; they must not masquerade as armor or weapons. Multiple armor plates require damage distribution rules, multiple scanners need selection/aggregation, and multiple tractors need emitter/arm management. Those semantics are deliberately absent from this first implementation.

Perks and temporary boosters should modify effective device properties while leaving installation class stable by default. See [perks and boosters](perks_and_boosters.md). A richer family registry, slot tags, removal policies, migration tool, structured rejection reasons and negotiated multiplayer capability remain future work.

## Hardware and thrusters (2026-10-30)

`hp_hardware_special_1` through `_10` describe special internal equipment, cloaking devices and dedicated `[GravityDevice]` archetypes. `HpHardware01` is a logical slot; the device is listed on **Internal**, has no rotating external attachment, and emits its activation effect from the ship. Scripted NPC cloak archetypes keep their original attachment behavior.

```ini
[CloakingDevice]
nickname = player_cloak
hp_type = hp_hardware_special_1

[Thruster]
nickname = thruster_class7
hp_type = hp_thruster_special_7

[Ship]
equipment_slot = HpHardware01, hardware, 1
equipment_slot = HpThruster01, thruster, 6
```

This hull accepts a class 6 thruster but rejects class 7. Multiple physical thruster slots may be occupied simultaneously. Thrusters remain on the external equipment tab and retain their physical meshes/effects. Exact `hp_type` declarations can share a physical mount with an authored shield/gun alternative; simultaneous occupation is rejected.

The installed content maps numbered thrusters to their existing level and hull ceilings to their engine class (or gun/shield ceiling for hulls without classed engines). Named Order/Nomad thrusters are class 10. Player loadout, purchases and mount requests are checked on the server. Authored NPC thrusters retain the native loadout exception, like NPC weapons/shields, so the rollout does not remove equipment from existing encounters. Armor/scanner/tractor/hardware validation remains in effect.

`tools/health_equipment/prepare.py` prepares the live INIs and both PythonLancer shiparch generators with hash-checked installation and backups. `build.ps1`, `check_health.py`, the global preferences/Misc checks and `tools/equipment_slots/check.ps1` cover the matching binaries and UI/controller behavior. The native equipment fixture exercises logical cloak activation, serialization/copying and destruction without a renderer.

Gravity hardware uses all ten classes. Declare `equipment_slot = HpHardware02, hardware, 10`
on a `[Ship]` or `[Solar]`, then `equip = gravity_generator, HpHardware02` in its
loadout. Player installation allows at most one `CloakingDevice`, one positive-rate
`RepairDroid` and one `GravityDevice`, regardless of model or class. Different types
occupy separate hardware slots: one slot permits one device, two slots any two
different types, and three slots all three. Unmounted cargo copies do not count;
unmounting a device allows a different model of that type to be installed.
All saved bindings are retained as authored; class checks apply to new player
mount requests, not runtime creation or save restoration. `HpRoot` and other names
are valid for mounted loadout devices without a corresponding UI slot declaration.
See [gravity equipment](../black_hole.md) for the five prototypes in `DATA/EQUIPMENT/gravity_devices.ini`.


### Runtime state and player mount requests

`CEqObj::add_item` selects the runtime device solely from `bEquipped`: mounted
items become their equipment type, unmounted items become `CECargo`. Named internal
bindings are preserved without a model attachment. Authoritative scripts/loadouts
and saves are not checked against player installation limits. `RestoreLoadout` is
a compatibility no-op; loading must not relocate or unmount authored equipment.

`CanMount` and `ValidateChange` check new/changed player mounts while retaining
unchanged authored mounts. Full `Validate` checks transfers to a new hull. The
server enforces these rules in `ReqAddItem`, `ReqModifyItem`, and `ReqEquipment`,
with full validation after a player-requested hull change. Authoritative
`PlayerData_*` mutations remain usable by missions and save restoration.
