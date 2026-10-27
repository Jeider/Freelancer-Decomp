#pragma once

#include "common_exports.h"
#include "equipment_class_rules.h"

class INI_Reader;
class EquipDescList;
class CEquip;
struct EquipDesc;
namespace Archetype { struct Root; struct Equipment; struct Ship; }

namespace EquipmentSlots
{
    COMMON_API bool Enabled();
    COMMON_API void ResetDefinition(Archetype::Root const& Arch);
    COMMON_API bool ReadEquipment(Archetype::Equipment const& Arch, INI_Reader& Ini);
    COMMON_API void CopyDefinition(Archetype::Root const& To, Archetype::Root const& From);
    COMMON_API unsigned GetType(Archetype::Equipment const& Arch);
    COMMON_API bool ReadShip(Archetype::Ship& Ship, INI_Reader& Ini);
    COMMON_API bool Validate(Archetype::Ship const* Ship, EquipDescList const& Items);
    COMMON_API bool CanMount(Archetype::Ship const* Ship, EquipDescList const& Items,
                            EquipDesc const& Item, char const* Slot);
    COMMON_API void Bind(CEquip const* Item, char const* Slot);
    COMMON_API void CopyBinding(CEquip const* To, CEquip const* From);
    COMMON_API void Forget(CEquip const* Item);
    COMMON_API bool RestoreBinding(CEquip const* Item, EquipDesc& Desc);
}
