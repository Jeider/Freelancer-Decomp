// Port-only internal equipment classes. See docs/re/equipment_mount_classes.md.
#include "equipment_slots.h"
#include "common_archetype.h"
#include "common_goods.h"
#include "common_ini.h"
#include "common_misc.h"
#include "port_config.h"
#include "dacom.h"
#include <map>
#include <set>
#include <string>
#include <cstring>

namespace EquipmentSlots
{
    bool Enabled()
    {
#ifdef FREELANCER_EQUIPMENT_SLOTS
        // Classes and slot bindings cannot be hot-switched while a loadout is live.
        static bool const On = PortConfigInt("Equipment", "internal_classes", 0) != 0;
        return On;
#else
        return false;
#endif
    }

    namespace
    {
        std::map<Archetype::Root const*, unsigned>& Definitions()
        {
            static std::map<Archetype::Root const*, unsigned> Values;
            return Values;
        }
        std::map<CEquip const*, CacheString>& Bindings()
        {
            static std::map<CEquip const*, CacheString> Values;
            return Values;
        }
        using LegalSlots = std::vector<Archetype::LegalHpTypes>;
        std::map<Archetype::Root const*, LegalSlots>& SolarSlots()
        {
            static auto* Values = new std::map<Archetype::Root const*, LegalSlots>;
            return *Values;
        }
        int FamilyOf(Archetype::Equipment const& Arch)
        {
            switch (Arch.get_class_type())
            {
            case Archetype::AClassArmor: return 0;
            case Archetype::AClassScanner: return 1;
            case Archetype::AClassTractor: return 2;
            case Archetype::AClassRepairDroid:
            case Archetype::AClassGravityDevice:
            case Archetype::AClassCloakingDevice: return 3;
            case Archetype::AClassThruster: return 4;
            default: return -1;
            }
        }
        bool Same(char const* A, char const* B)
        {
            return A && B && _stricmp(A, B) == 0;
        }
        void AddLegal(Archetype::Root& Owner, LegalSlots& Slots, unsigned Type, char const* Name)
        {
            for (auto const& Entry : Slots)
                for (auto const& Hp : Entry.Hardpoints)
                    if (Same(Hp.Value, Name) && EquipmentClasses::Family(unsigned(Entry.Type)) != EquipmentClasses::Family(Type) &&
                        !(EquipmentClasses::Family(Type) == 4 && !EquipmentClasses::IsManaged(unsigned(Entry.Type))))
                    {
                        FDUMP(0x100001, "Conflicting family for internal slot %s on %s", Name, Owner.Nickname.get_string());
                        return;
                    }
            for (auto& Entry : Slots)
                if (unsigned(Entry.Type) == Type)
                {
                    for (auto const& Hp : Entry.Hardpoints)
                        if (Same(Hp.Value, Name)) return;
                    CacheString Hp;
                    Hp.Value = StringAlloc(Name, false);
                    Entry.Hardpoints.push_back(Hp);
                    return;
                }
            Archetype::LegalHpTypes Entry;
            Entry.Type = static_cast<HpAttachmentType>(Type);
            CacheString Hp;
            Hp.Value = StringAlloc(Name, false);
            Entry.Hardpoints.push_back(Hp);
            Slots.push_back(Entry);
        }
    }

    void ResetDefinition(Archetype::Root const& Arch)
    {
        if (Enabled()) { Definitions().erase(&Arch); SolarSlots().erase(&Arch); }
    }

    bool ReadEquipment(Archetype::Equipment const& Arch, INI_Reader& Ini)
    {
        if (!Enabled() || FamilyOf(Arch) < 0 || !Ini.is_value("hp_type")) return false;
        if (FamilyOf(Arch) == 4 && Same(Ini.get_value_string(0), "hp_thruster"))
        { Definitions().erase(&Arch); return true; }
        unsigned const Type = EquipmentClasses::Parse(Ini.get_value_string(0));
        bool const Valid = EquipmentClasses::IsType(Type) &&
                           EquipmentClasses::Family(Type) == FamilyOf(Arch);
        Definitions()[&Arch] = Valid ? Type : EquipmentClasses::Invalid;
        if (!Valid)
            FDUMP(0x100001, "Invalid internal equipment hp_type for %s", Arch.Nickname.get_string());
        return true;
    }

    void CopyDefinition(Archetype::Root const& To, Archetype::Root const& From)
    {
        if (!Enabled() || &To == &From) return;
        auto const It = Definitions().find(&From);
        if (It == Definitions().end()) Definitions().erase(&To);
        else Definitions()[&To] = It->second;
        auto const Slots = SolarSlots().find(&From);
        if (Slots == SolarSlots().end()) SolarSlots().erase(&To);
        else SolarSlots()[&To] = Slots->second;
    }

    unsigned GetType(Archetype::Equipment const& Arch)
    {
        if (Enabled())
        {
            auto const It = Definitions().find(&Arch);
            if (It != Definitions().end()) return It->second;
        }
        if (Arch.get_class_type() == Archetype::AClassThruster) return HpTypeThruster;
        if (Arch.get_class_type() == Archetype::AClassCloakingDevice) return HpTypeNone;
        return HpTypeInternal;
    }

    static bool ReadSlots(Archetype::Root& Owner, LegalSlots& Slots, INI_Reader& Ini)
    {
        if (!Enabled()) return false;
        if (Ini.is_value("equipment_slot"))
        {
            if (Ini.is_value_empty(0) || Ini.is_value_empty(1) || Ini.is_value_empty(2) || !Ini.is_value_empty(3))
            {
                FDUMP(0x100001, "equipment_slot needs name, family, maximum class on %s", Owner.Nickname.get_string());
                return true;
            }
            // INI_Reader reuses its value buffer on the next getter.
            std::string const SlotName = Ini.get_value_string(0);
            char const* Name = SlotName.c_str();
            int const Family = EquipmentClasses::FindFamily(Ini.get_value_string(1));
            int const Level = EquipmentClasses::ParseLevel(Ini.get_value_string(2));
            if (!Name || !*Name || Same(Name, EquipDesc::CARGO_BAY_HP_NAME.Value) ||
                !EquipmentClasses::IsType(EquipmentClasses::Type(Family, Level)))
            {
                FDUMP(0x100001, "Invalid equipment_slot for %s", Owner.Nickname.get_string());
                return true;
            }
            // One declaration per slot. Otherwise a duplicate could silently widen its class/family.
            for (auto const& Entry : Slots)
                for (auto const& Hp : Entry.Hardpoints)
                    if (Same(Hp.Value, Name))
                    {
                        FDUMP(0x100001, "Duplicate equipment_slot %s on %s", Name, Owner.Nickname.get_string());
                        return true;
                    }
            for (int I = 1; I <= Level; ++I) AddLegal(Owner, Slots, EquipmentClasses::Type(Family, I), Name);
            return true;
        }
        if (!Ini.is_value("hp_type")) return false;
        unsigned const Type = EquipmentClasses::Parse(Ini.get_value_string(0));
        if (!EquipmentClasses::IsType(Type)) return false; // retail/engclass reader retains its keys
        for (int I = 1; !Ini.is_value_empty(I); ++I)
        {
            char const* Name = Ini.get_value_string(I);
            if (Name && *Name && !Same(Name, EquipDesc::CARGO_BAY_HP_NAME.Value)) AddLegal(Owner, Slots, Type, Name);
        }
        return true;
    }

    bool ReadShip(Archetype::Ship& Ship, INI_Reader& Ini)
    { return ReadSlots(Ship, Ship.LegalHps, Ini); }

    bool ReadSolar(Archetype::Solar& Solar, INI_Reader& Ini)
    {
        if (!Enabled() || (!Ini.is_value("equipment_slot") && !Ini.is_value("hp_type"))) return false;
        return ReadSlots(Solar, SolarSlots()[&Solar], Ini);
    }

    static bool ValidateSlots(LegalSlots const* Slots, EquipDescList const& Items,
                              EquipDescList const* Existing = nullptr)
    {
        if (!Enabled()) return true;
        std::set<EquipDesc const*> Matched;
        for (auto const& Item : Items.Items)
        {
            if (!Item.bEquipped) continue;
            // Preserve authored mounts verbatim. Validate only additions/changes
            // during same-hull transactions; a full new-hull check passes no baseline.
            bool Unchanged = false;
            if (Existing)
                for (auto const& Previous : Existing->Items)
                    if (Previous.bEquipped && Previous.Id == Item.Id && Previous.ArchId == Item.ArchId &&
                        Previous.Count == Item.Count && Same(Previous.Hardpoint, Item.Hardpoint) &&
                        Matched.insert(&Previous).second)
                    { Unchanged = true; break; }
            if (Unchanged) continue;
            Archetype::Equipment const* Arch = Archetype::GetEquipment(Item.ArchId);
            unsigned const Type = Arch ? unsigned(Arch->get_hp_type()) : 0;
            bool const Managed = EquipmentClasses::IsManaged(Type);
            bool SlotManaged = false;
            bool Allowed = false;
            bool LegacyAllowed = false;
            bool PhysicalThrusterSlot = false, InternalSlot = false;
            if (Slots)
                for (auto const& Entry : *Slots)
                {
                    if (unsigned(Entry.Type) == Type)
                        for (auto const& Hp : Entry.Hardpoints)
                            if (Same(Hp.Value, Item.Hardpoint)) LegacyAllowed = true;
                    if (EquipmentClasses::IsType(unsigned(Entry.Type)))
                        for (auto const& Hp : Entry.Hardpoints)
                            if (Same(Hp.Value, Item.Hardpoint))
                            {
                                SlotManaged = true;
                                if (EquipmentClasses::Family(unsigned(Entry.Type)) == 4) PhysicalThrusterSlot = true;
                                else InternalSlot = true;
                                if (unsigned(Entry.Type) == Type) Allowed = true;
                            }
                }
            // Some authored hulls share a physical shield/gun mount with a thruster.
            // Keep that alternative legal, while a legacy thruster cannot bypass its class.
            if (!Managed && PhysicalThrusterSlot && !InternalSlot && LegacyAllowed && Arch &&
                Arch->get_class_type() != Archetype::AClassThruster) continue;
            if (!Managed && !SlotManaged) continue; // no new policy for legacy-only equipment
            if (!EquipmentClasses::IsType(Type) || !Allowed || Item.Count != 1 || !Arch ||
                FamilyOf(*Arch) != EquipmentClasses::Family(Type)) return false;
            for (auto const& Other : Items.Items)
            {
                if (&Other == &Item || !Other.bEquipped) continue;
                if (Same(Item.Hardpoint, Other.Hardpoint)) return false;
                // Hardware shares the slot family, but each device type is unique:
                // one cloak, one repair droid and one gravity device across all slots.
                Archetype::Equipment const* OtherArch = Archetype::GetEquipment(Other.ArchId);
                bool const QuestKey = OtherArch && OtherArch->get_class_type() == Archetype::AClassRepairDroid &&
                    !(static_cast<Archetype::RepairDroid const*>(OtherArch)->RepairRate > 0);
                if (OtherArch && !QuestKey && FamilyOf(*Arch) != 4 &&
                    OtherArch->get_class_type() == Arch->get_class_type()) return false;
            }
        }
        return true;
    }

    bool Validate(Archetype::Ship const* Ship, EquipDescList const& Items)
    { return ValidateSlots(Ship ? &Ship->LegalHps : nullptr, Items); }

    bool ValidateChange(Archetype::Ship const* Ship, EquipDescList const& Before, EquipDescList const& After)
    { return ValidateSlots(Ship ? &Ship->LegalHps : nullptr, After, &Before); }

    bool ValidateObject(Archetype::EqObj const* Object, EquipDescList const& Items)
    {
        if (Object && Object->get_class_type() == Archetype::AClassShip)
            return Validate(static_cast<Archetype::Ship const*>(Object), Items);
        auto const It = SolarSlots().find(Object);
        return ValidateSlots(It == SolarSlots().end() ? nullptr : &It->second, Items);
    }

    bool CanMount(Archetype::Ship const* Ship, EquipDescList const& Items,
                  EquipDesc const& Item, char const* Slot)
    {
        EquipDescList Candidate(Items);
        // Do not remove a resident item by id: transferred goods can have the same id as
        // the destination's equipment. An own item must be unmounted before mounting it.
        EquipDesc Mounted(Item);
        CacheString Hp;
        Hp.Value = StringAlloc(Slot, false);
        Mounted.set_hardpoint(Hp);
        Mounted.set_equipped(true);
        Mounted.set_count(1);
        Candidate.Items.push_back(Mounted);
        return ValidateChange(Ship, Items, Candidate);
    }

    void RestoreLoadout(Archetype::Ship const*, EquipDescList&)
    {
        // Compatibility export for older callers. Saved mounted/cargo state and
        // hardpoint names are authoritative; never relocate or unmount on load.
    }

    void Bind(CEquip const* Item, char const* Slot)
    {
        if (!Enabled()) return;
        CacheString Hp;
        Hp.Value = StringAlloc(Slot, false);
        Bindings()[Item] = Hp;
    }
    void CopyBinding(CEquip const* To, CEquip const* From)
    {
        if (!Enabled()) return;
        auto const It = Bindings().find(From);
        if (It != Bindings().end()) Bindings()[To] = It->second;
    }
    void Forget(CEquip const* Item)
    {
        if (Enabled()) Bindings().erase(Item);
    }
    bool RestoreBinding(CEquip const* Item, EquipDesc& Desc)
    {
        if (!Enabled()) return false;
        auto const It = Bindings().find(Item);
        if (It == Bindings().end()) return false;
        Desc.set_hardpoint(It->second);
        return true;
    }
}
