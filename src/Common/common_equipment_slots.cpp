// Port-only internal equipment classes. See docs/re/equipment_mount_classes.md.
#include "equipment_slots.h"
#include "common_archetype.h"
#include "common_goods.h"
#include "common_ini.h"
#include "common_misc.h"
#include "port_config.h"
#include "dacom.h"
#include <map>
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
        int FamilyOf(Archetype::Equipment const& Arch)
        {
            switch (Arch.get_class_type())
            {
            case Archetype::AClassArmor: return 0;
            case Archetype::AClassScanner: return 1;
            case Archetype::AClassTractor: return 2;
            default: return -1;
            }
        }
        bool Same(char const* A, char const* B)
        {
            return A && B && _stricmp(A, B) == 0;
        }
        void AddLegal(Archetype::Ship& Ship, unsigned Type, char const* Name)
        {
            for (auto const& Entry : Ship.LegalHps)
                for (auto const& Hp : Entry.Hardpoints)
                    if (Same(Hp.Value, Name) && EquipmentClasses::Family(unsigned(Entry.Type)) != EquipmentClasses::Family(Type))
                    {
                        FDUMP(0x100001, "Conflicting family for internal slot %s on %s", Name, Ship.Nickname.get_string());
                        return;
                    }
            for (auto& Entry : Ship.LegalHps)
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
            Ship.LegalHps.push_back(Entry);
        }
    }

    void ResetDefinition(Archetype::Root const& Arch)
    {
        if (Enabled()) Definitions().erase(&Arch);
    }

    bool ReadEquipment(Archetype::Equipment const& Arch, INI_Reader& Ini)
    {
        if (!Enabled() || FamilyOf(Arch) < 0 || !Ini.is_value("hp_type")) return false;
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
    }

    unsigned GetType(Archetype::Equipment const& Arch)
    {
        if (Enabled())
        {
            auto const It = Definitions().find(&Arch);
            if (It != Definitions().end()) return It->second;
        }
        return HpTypeInternal;
    }

    bool ReadShip(Archetype::Ship& Ship, INI_Reader& Ini)
    {
        if (!Enabled()) return false;
        if (Ini.is_value("equipment_slot"))
        {
            if (Ini.is_value_empty(0) || Ini.is_value_empty(1) || Ini.is_value_empty(2) || !Ini.is_value_empty(3))
            {
                FDUMP(0x100001, "equipment_slot needs name, family, maximum class on %s", Ship.Nickname.get_string());
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
                FDUMP(0x100001, "Invalid equipment_slot for %s", Ship.Nickname.get_string());
                return true;
            }
            // One declaration per slot. Otherwise a duplicate could silently widen its class/family.
            for (auto const& Entry : Ship.LegalHps)
                for (auto const& Hp : Entry.Hardpoints)
                    if (Same(Hp.Value, Name))
                    {
                        FDUMP(0x100001, "Duplicate equipment_slot %s on %s", Name, Ship.Nickname.get_string());
                        return true;
                    }
            for (int I = 1; I <= Level; ++I) AddLegal(Ship, EquipmentClasses::Type(Family, I), Name);
            return true;
        }
        if (!Ini.is_value("hp_type")) return false;
        unsigned const Type = EquipmentClasses::Parse(Ini.get_value_string(0));
        if (!EquipmentClasses::IsType(Type)) return false; // retail/engclass reader retains its keys
        for (int I = 1; !Ini.is_value_empty(I); ++I)
        {
            char const* Name = Ini.get_value_string(I);
            if (Name && *Name && !Same(Name, EquipDesc::CARGO_BAY_HP_NAME.Value)) AddLegal(Ship, Type, Name);
        }
        return true;
    }

    bool Validate(Archetype::Ship const* Ship, EquipDescList const& Items)
    {
        if (!Enabled()) return true;
        for (auto const& Item : Items.Items)
        {
            if (!Item.bEquipped) continue;
            Archetype::Equipment const* Arch = Archetype::GetEquipment(Item.ArchId);
            unsigned const Type = Arch ? unsigned(Arch->get_hp_type()) : 0;
            bool const Managed = EquipmentClasses::IsManaged(Type);
            bool SlotManaged = false;
            bool Allowed = false;
            if (Ship)
                for (auto const& Entry : Ship->LegalHps)
                    if (EquipmentClasses::IsType(unsigned(Entry.Type)))
                        for (auto const& Hp : Entry.Hardpoints)
                            if (Same(Hp.Value, Item.Hardpoint))
                            {
                                SlotManaged = true;
                                if (unsigned(Entry.Type) == Type) Allowed = true;
                            }
            if (!Managed && !SlotManaged) continue; // no new policy for legacy-only equipment
            if (!EquipmentClasses::IsType(Type) || !Allowed || Item.Count != 1 || !Arch ||
                FamilyOf(*Arch) != EquipmentClasses::Family(Type)) return false;
            for (auto const& Other : Items.Items)
            {
                if (&Other == &Item || !Other.bEquipped) continue;
                if (Same(Item.Hardpoint, Other.Hardpoint)) return false;
                // These three runtime systems have a single active device, including legacy built-ins.
                Archetype::Equipment const* OtherArch = Archetype::GetEquipment(Other.ArchId);
                if (OtherArch && FamilyOf(*OtherArch) == FamilyOf(*Arch)) return false;
            }
        }
        return true;
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
        return Validate(Ship, Candidate);
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
