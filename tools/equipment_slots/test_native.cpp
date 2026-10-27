// Integration checks against the real Common.dll, its INI readers and CE equipment.
#include "equipment_slots.h"
#include "common_archetype.h"
#include "common_cequip.h"
#include "common_cobject.h"
#include "common_goods.h"
#include "common_ini.h"
#include "common_misc.h"
#include "dacom.h"
#include <cassert>
#include <cstdarg>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <new>

struct BeamFixture : Archetype::Munition
{
    // This fixture has no renderer or beam equipment. Skip the loader's unrelated
    // CreateCompoundArchetype("BEAM_ARCH") tail, restore its sentinel before cleanup.
    static void Set(long Value) { BEAM_ARCH_INDEX = Value; }
};

static void __cdecl TestDump(int, char const* Format, ...)
{
    va_list Args;
    va_start(Args, Format);
    std::vfprintf(stderr, Format, Args);
    std::fputc('\n', stderr);
    va_end(Args);
}

static void Parse(Archetype::Root& Arch, char const* Text)
{
    INI_Reader Ini;
    assert(Ini.open_memory(Text, unsigned(std::strlen(Text))));
    assert(Ini.read_header());
    while (Ini.read_value()) Arch.read(Ini);
}

static EquipDesc Item(char const* Nickname, char const* Slot, unsigned short Id = 40)
{
    EquipDesc Result;
    Result.set_id(Id);
    Result.set_arch_id(CreateID(Nickname));
    Result.set_count(1);
    Result.set_status(1.f);
    Result.set_equipped(true);
    CacheString Hp;
    Hp.Value = StringAlloc(Slot, false);
    Result.set_hardpoint(Hp);
    return Result;
}

int main(int argc, char** argv)
{
    _set_error_mode(_OUT_TO_STDERR);
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
    FDUMP = TestDump; // invalid-definition tests must log, never open DACOM's default dialog
    assert(argc == 3);
    bool const On = std::strcmp(argv[2], "on") == 0;
    assert(EquipmentSlots::Enabled() == On);
    assert(EquipmentClasses::Parse("hp_armor_special_1") == EquipmentClasses::First);
    assert(EquipmentClasses::Level(EquipmentClasses::Parse("HP_TRACTOR_SPECIAL_10")) == 10);
    for (char const* Bad : { "hp_armor_special_0", "hp_armor_special_11", "hp_armor_special_01",
                            "hp_armor_special_+1", "hp_scanner_special_3junk", "hp_engine_special_1" })
        assert(!EquipmentClasses::IsType(EquipmentClasses::Parse(Bad)));

    BeamFixture::Set(0);
    assert(Archetype::LoadEquipment(argv[1], false, nullptr) == 9);
    auto* Armor = static_cast<Archetype::Armor*>(Archetype::GetEquipment(CreateID("slot_test_armor3")));
    auto* Scanner = static_cast<Archetype::Scanner*>(Archetype::GetEquipment(CreateID("slot_test_scanner2")));
    auto* Tractor = static_cast<Archetype::Tractor*>(Archetype::GetEquipment(CreateID("slot_test_tractor3")));
    assert(Armor && Scanner && Tractor);
    assert(unsigned(Armor->get_hp_type()) == (On ? EquipmentClasses::Type(0, 3) : unsigned(HpTypeInternal)));
    assert(unsigned(Scanner->get_hp_type()) == (On ? EquipmentClasses::Type(1, 2) : unsigned(HpTypeInternal)));
    assert(unsigned(Tractor->get_hp_type()) == (On ? EquipmentClasses::Type(2, 3) : unsigned(HpTypeInternal)));
    assert(Scanner->RadarRange == 7000 && Tractor->MaxLength == 2200);

    Archetype::Ship Hull(nullptr);
    Parse(Hull, "[Ship]\nnickname=slot_test_ship\nequipment_slot=HpSlot_Armor01,armor,4\n"
                "equipment_slot=HpSlot_Scanner01,scanner,3\nequipment_slot=HpSlot_Tractor01,tractor,3\n");
    assert(Hull.LegalHps.size() == (On ? 10u : 0u));
    if (On)
    {
        Archetype::Armor LateNickname(nullptr);
        Parse(LateNickname, "[Armor]\nhp_type=hp_armor_special_3\nnickname=slot_test_late_name\n");
        assert(unsigned(LateNickname.get_hp_type()) == EquipmentClasses::Type(0, 3));
        Archetype::Ship InvalidHull(nullptr);
        Parse(InvalidHull, "[Ship]\nnickname=slot_test_invalid_ship\n"
              "equipment_slot=Broken,armor\nequipment_slot=Broken,armor,1.5\n"
              "equipment_slot=Broken,armor,11\nequipment_slot=Broken,unknown,1\n"
              "equipment_slot=Good,armor,1\nequipment_slot=Good,scanner,3\n");
        assert(InvalidHull.LegalHps.size() == 1);
        Parse(InvalidHull, "[Ship]\nhp_type=hp_scanner_special_2,Good\n");
        assert(InvalidHull.LegalHps.size() == 1);
        Archetype::Ship ExactHull(nullptr);
        Parse(ExactHull, "[Ship]\nnickname=slot_test_exact_ship\nhp_type=hp_armor_special_3,Exact\n");
        EquipDescList ExactLoadout;
        ExactLoadout.Items.push_back(Item("slot_test_armor3", "Exact"));
        assert(EquipmentSlots::Validate(&ExactHull, ExactLoadout));
        ExactLoadout.Items.front().ArchId = CreateID("slot_test_armor1");
        assert(!EquipmentSlots::Validate(&ExactHull, ExactLoadout));
        EquipDescList Loadout;
        Loadout.Items.push_back(Item("slot_test_armor3", "HpSlot_Armor01"));
        Loadout.Items.push_back(Item("slot_test_scanner2", "HpSlot_Scanner01", 41));
        Loadout.Items.push_back(Item("slot_test_tractor3", "HpSlot_Tractor01", 42));
        assert(EquipmentSlots::Validate(&Hull, Loadout));
        auto Bad = Loadout;
        Bad.Items.front().ArchId = CreateID("slot_test_armor5");
        assert(!EquipmentSlots::Validate(&Hull, Bad));
        Bad = Loadout;
        Bad.Items.front().ArchId = CreateID("slot_test_scanner_invalid");
        assert(!EquipmentSlots::Validate(&Hull, Bad));
        Bad = Loadout;
        Bad.Items.front().Hardpoint = StringAlloc("HpSlot_Scanner01", false);
        assert(!EquipmentSlots::Validate(&Hull, Bad));
        Bad = Loadout;
        Bad.Items.push_back(Item("slot_test_armor1", "HpSlot_Armor01", 43));
        assert(!EquipmentSlots::Validate(&Hull, Bad));
        Bad = Loadout;
        auto Legacy = Item("slot_test_scanner_legacy", "", 44);
        Legacy.make_internal();
        Bad.Items.push_back(Legacy);
        assert(!EquipmentSlots::Validate(&Hull, Bad));
        Bad.Items.back().set_equipped(false);
        assert(EquipmentSlots::Validate(&Hull, Bad));
        assert(!EquipmentSlots::CanMount(&Hull, Loadout, Loadout.Items.front(), "HpSlot_Armor01"));
        auto New = Item("slot_test_armor1", "HpSlot_Armor01", SUBOBJ_ID_NONE);
        assert(!EquipmentSlots::CanMount(&Hull, Loadout, New, "HpSlot_Armor01"));
        EquipDescList Empty;
        assert(EquipmentSlots::CanMount(&Hull, Empty, New, "hpslot_armor01"));
        assert(!EquipmentSlots::CanMount(&Hull, Empty, New, "HpMissing"));
        assert(!EquipmentSlots::Validate(nullptr, Loadout));
        Bad = Loadout;
        Bad.Items.front().Count = 2;
        assert(!EquipmentSlots::Validate(&Hull, Bad));

        // Exercise the real runtime installation gate and cargo accounting without graphics.
        Hull.HoldSize = 100;
        Armor->Volume = 5;
        {
            CShip Ship;
            Ship.Archetype = &Hull;
            assert(Ship.add_item(Loadout.Items.front()));
            assert(!Ship.add_item(Loadout.Items.front()));
            assert(Ship.get_cargo_hold_remaining() == 100);
            auto Cargo = Loadout.Items.front();
            Cargo.set_id(60);
            Cargo.set_equipped(false);
            Cargo.set_count(2);
            Cargo.make_internal();
            assert(Ship.add_item(Cargo));
            assert(Ship.get_cargo_hold_remaining() == 90);
            assert(Ship.add_item(Item("slot_test_scanner2", "HpSlot_Scanner01", 41)));
            assert(!Ship.add_item(Legacy)); // legacy built-in cannot bypass the family limit
            Ship.clear_equip_and_cargo();
            assert(Ship.get_cargo_hold_remaining() == 100);
            assert(Ship.next_enemy() == nullptr);
            assert(Ship.previous_enemy() == nullptr);
            assert(Ship.next_target(false) == nullptr);
            assert(Ship.add_item(Legacy));
            assert(!Ship.add_item(Item("slot_test_scanner2", "HpSlot_Scanner01", 41)));
        }

        // The actual CInternalEquip serialization and its copy constructor retain a logical slot.
        CEArmor Live(nullptr, 40, Armor, false);
        EquipmentSlots::Bind(&Live, "HpSlot_Armor01");
        EquipDesc Serialized;
        assert(Live.GetEquipDesc(Serialized));
        assert(std::strcmp(Serialized.Hardpoint, "HpSlot_Armor01") == 0 && Serialized.bEquipped);
        CEArmor Copied(Live);
        assert(Copied.GetEquipDesc(Serialized) && std::strcmp(Serialized.Hardpoint, "HpSlot_Armor01") == 0);
        EquipmentSlots::Forget(&Copied);
        assert(Copied.GetEquipDesc(Serialized) && Serialized.is_internal());
        CEScanner LiveScanner(nullptr, 41, Scanner, false);
        EquipmentSlots::Bind(&LiveScanner, "HpSlot_Scanner01");
        assert(LiveScanner.GetEquipDesc(Serialized) && std::strcmp(Serialized.Hardpoint, "HpSlot_Scanner01") == 0);
        CETractor LiveTractor(nullptr, 42, Tractor, false);
        EquipmentSlots::Bind(&LiveTractor, "HpSlot_Tractor01");
        assert(LiveTractor.GetEquipDesc(Serialized) && std::strcmp(Serialized.Hardpoint, "HpSlot_Tractor01") == 0);

        auto* Inherited = Archetype::GetEquipment(CreateID("slot_test_scanner_inherited"));
        assert(Inherited->get_hp_type() == Scanner->get_hp_type());
        Archetype::Scanner Copy(*Scanner);
        assert(Copy.get_hp_type() == Scanner->get_hp_type());
        Archetype::Scanner Plain(nullptr);
        Copy.redefine(Plain);
        assert(Copy.get_hp_type() == HpTypeInternal);
        // Reusing an address must not resurrect metadata from the destroyed archetype.
        alignas(Archetype::Scanner) unsigned char Storage[sizeof(Archetype::Scanner)];
        auto* Temporary = new (Storage) Archetype::Scanner(*Scanner);
        assert(Temporary->get_hp_type() == Scanner->get_hp_type());
        Temporary->~Scanner();
        Temporary = new (Storage) Archetype::Scanner(nullptr);
        assert(Temporary->get_hp_type() == HpTypeInternal);
        Temporary->~Scanner();

        auto* Reload = Archetype::GetEquipment(CreateID("slot_test_scanner_reload"));
        std::ofstream("reload.ini") << "[Scanner]\nnickname=slot_test_scanner_reload\nhp_type=hp_scanner_special_3\n";
        Archetype::LoadEquipment("reload.ini", false, nullptr);
        assert(unsigned(Reload->get_hp_type()) == EquipmentClasses::Type(1, 2));
        Archetype::LoadEquipment("reload.ini", true, nullptr);
        assert(unsigned(Reload->get_hp_type()) == EquipmentClasses::Type(1, 3));
        std::ofstream("reload.ini") << "[Scanner]\nnickname=slot_test_scanner_reload\nrange=1000\n";
        Archetype::LoadEquipment("reload.ini", true, nullptr);
        assert(Reload->get_hp_type() == HpTypeInternal);
    }
    BeamFixture::Set(-1);
    // Records are released by process teardown; no engine resource initialization in this fixture.
    std::printf("PASS: internal equipment classes %s (native Common.dll)\n", On ? "on" : "off");
    return 0;
}
