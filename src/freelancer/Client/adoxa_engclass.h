// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only, adoxa's engclass.dll v2.02 (docs/adoxa.md): the client half of classed, mountable
// engines and powerplants. Common.dll gives Power / Engine the hp types 0x43..0x7e
// (hp_<fighter|elite|freighter>_<power|engine>_special_<1..10>); the inventory, dealer and ship
// view treat such internal equipment (filter mode 3) as mountable, like weapons (mode 0).

#if defined(FREELANCER_ADOXA) || defined(FREELANCER_EQUIPMENT_SLOTS)

#include "port_plugins.h"

#include "common_archetype.h"
#ifdef FREELANCER_EQUIPMENT_SLOTS
#include "equipment_slots.h"
#endif

// engclass.c HP_TYPE and the end of its six ten-class families.
enum
{
    ENGCLASS_HP_TYPE = 0x43,
    ENGCLASS_HP_TYPE_END = 0x7f
};

inline bool EngclassOn()
{
#ifdef FREELANCER_ADOXA
    return PORT_PLUGIN_ON("engclass");
#else
    return false;
#endif
}

inline bool MountableInternalsOn()
{
#ifdef FREELANCER_EQUIPMENT_SLOTS
    if (EquipmentSlots::Enabled()) return true;
#endif
    return EngclassOn();
}

// The test every engclass.c hook inlines: GetEquipment(id) (import 0x5c603c), get_hp_type
// (vt+0x18) >= HP_TYPE. A missing archetype is internal.
inline bool EngclassIsMountable(unsigned ArchId)
{
    Archetype::Equipment* const Arch = Archetype::GetEquipment(ArchId);
    if (Arch == nullptr)
        return false;
    unsigned const Type = unsigned(Arch->get_hp_type());
#ifdef FREELANCER_EQUIPMENT_SLOTS
    if (EquipmentSlots::Enabled() && EquipmentClasses::IsType(Type)) return true;
#endif
    return EngclassOn() && Type >= ENGCLASS_HP_TYPE && Type < ENGCLASS_HP_TYPE_END;
}

// InvIcon_Hook / Inv_Hook / InvSell_Hook / Dealer_Hook / DealerSelected_Hook / Mount_Hook: a
// filter mode of 3 (internal) for a mountable item reads as 0 (weapons, mounted on a hardpoint).
inline int EngclassFilterMode(int Mode, unsigned ArchId)
{
    if (Mode != 3 || !MountableInternalsOn())
        return Mode;
    return EngclassIsMountable(ArchId) ? 0 : 3;
}

// The ids base the plugin's strings were shifted by (ResDll_Hook: (module count - 1) << 16,
// added by Adjust_Resources): its local ids 0..5 are the six hardpoint descriptions, 6..65 the
// hardpoint names of hp types 0x43..0x7e. Set by dataconfig_progress.cpp when the language's
// engclass resource DLL is registered.
inline unsigned& EngclassIdsBase()
{
    static unsigned S_Base = 0;
    return S_Base;
}

#endif
