#pragma once
#include "gravity_field.h"
struct CSolar;
struct CShip;
class CEquip;
namespace Archetype { struct Equipment; struct Root; }
class INI_Reader;
class IVP_Core;
class IVP_Event_Sim;
template<class T> class IVP_U_Vector;

namespace CmnGravity
{
struct ObjectSettings
{
    bool enabled=false;
    GravityField::Settings field;
};
bool ReadObjectValue(INI_Reader& reader, ObjectSettings& settings);
void RegisterSolar(CSolar* solar);
void UnregisterSolar(CSolar* solar);
bool ReadEquipmentValue(Archetype::Equipment& arch, INI_Reader& reader);
void ForgetDefinition(Archetype::Root const* arch);
void CopyDefinition(Archetype::Equipment const& target, Archetype::Equipment const& donor);
void RegisterEquipment(CEquip* equip);
void UnregisterEquipment(CEquip* equip);
void Apply(CShip& ship, IVP_Event_Sim* event, IVP_U_Vector<IVP_Core>* cores);
}
