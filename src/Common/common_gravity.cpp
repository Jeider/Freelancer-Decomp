// Port-only point gravity for locally simulated ships, at the fixed IVP step.
#include "common_gravity.h"
#include "gravity_field.h"
#include "common_cobject.h"
#include "common_cobjdb.h"
#include "common_universe_internal.h"
#include "common_ini.h"
#include "common_cequip.h"
#include "common_archetype.h"
#include "../IVP/ivp_physics/ivp_core.h"
#include "../IVP/ivp_physics/ivp_real_object.h"
#include "../IVP/ivp_physics/ivp_controller.h"
#include <algorithm>
#include <vector>
#include <map>
#include <cstring>

namespace
{
struct Source
{
    CSolar* solar;
    GravityField::Settings field;
};

std::vector<Source>& Sources()
{
    static std::vector<Source> sources;
    return sources;
}

struct DeviceSettings
{
    CmnGravity::ObjectSettings source;
    double compensation=0;
};
struct Device { CEquip* equip; DeviceSettings settings; };
// Archetypes can be destroyed by DLL/static teardown; registries must outlive them.
std::map<Archetype::Root const*,DeviceSettings>& Definitions()
{
    static auto* definitions=new std::map<Archetype::Root const*,DeviceSettings>;
    return *definitions;
}
std::vector<Device>& Devices()
{
    static auto* devices=new std::vector<Device>;
    return *devices;
}
bool SameObject(CEqObj const* a, CEqObj const* b)
{
    return a==b || (a->Id && a->Id==b->Id && a->PhysicsSystemId==b->PhysicsSystemId);
}
bool Remote(CEqObj const* owner)
{
    return owner->BodyPtr && owner->BodyPtr->core && (owner->BodyPtr->core->Flags&0x300u)!=0;
}
bool Working(CEquip const* equip)
{
    auto* owner=equip->GetOwner();
    return owner && owner->get_hit_pts()>0 && equip->IsFunctioning();
}
bool DuplicateDevice(size_t index)
{
    auto const& devices=Devices();
    auto* equip=devices[index].equip;
    auto* owner=equip->GetOwner();
    // SP may hold server and client copies. Prefer local physics; MP clients
    // still use remote emitter copies when no authoritative copy is present.
    for (size_t i=0;i<devices.size();++i) {
        auto* other=devices[i].equip;
        if (i==index || !Working(other) || other->GetID()!=equip->GetID() ||
            !SameObject(owner,other->GetOwner())) continue;
        bool remote=Remote(owner), otherRemote=Remote(other->GetOwner());
        if ((!otherRemote && remote) || (remote==otherRemote && i<index)) return true;
    }
    return false;
}
GravityField::Vector SourcePosition(CEqObj const& source)
{
    if (source.BodyPtr && source.BodyPtr->core && !Remote(&source)) {
        auto const& p=source.BodyPtr->core->MWorldFCore.vv;
        return {p.k[0],p.k[1],p.k[2]};
    }
    auto const& p=source.WorldPosition;
    return {p.x,p.y,p.z};
}
}

bool CmnGravity::ReadObjectValue(INI_Reader& reader, ObjectSettings& settings)
{
    if (reader.is_value("gravity")) {
        settings.enabled=reader.get_value_bool(0);
        return true;
    }
    if (reader.is_value("gravity_mode")) {
        char const* value=reader.get_value_string(0);
        if (!_stricmp(value,"attract")) settings.field.mode=GravityField::Mode::Attract;
        else if (!_stricmp(value,"repel")) settings.field.mode=GravityField::Mode::Repel;
        else if (!_stricmp(value,"suppress")) settings.field.mode=GravityField::Mode::Suppress;
        return true;
    }
    struct Field { char const* key; double GravityField::Settings::* member; double low, high; };
    static Field const fields[] = {
        {"gravity_radius",&GravityField::Settings::radius,1,1000000},
        {"gravity_reference_radius",&GravityField::Settings::referenceRadius,1,1000000},
        {"gravity_acceleration",&GravityField::Settings::acceleration,0,10000},
        {"gravity_softening",&GravityField::Settings::softening,1,1000000},
        {"gravity_max_acceleration",&GravityField::Settings::maxAcceleration,0,10000},
        {"gravity_edge_fraction",&GravityField::Settings::edgeFraction,.001,1},
        {"gravity_suppression",&GravityField::Settings::suppression,0,1}
    };
    for (auto const& field:fields) {
        if (!reader.is_value(field.key)) continue;
        double value=reader.get_value_float(0);
        if (std::isfinite(value))
            settings.field.*(field.member)=(std::max)(field.low,(std::min)(value,field.high));
        return true;
    }
    return false;
}

bool CmnGravity::ReadEquipmentValue(Archetype::Equipment& arch, INI_Reader& reader)
{
    auto& definitions=Definitions();
    auto found=definitions.find(&arch);
    DeviceSettings settings=found==definitions.end() ? DeviceSettings{} : found->second;
    if (reader.is_value("gravity_compensation")) {
        double value=reader.get_value_float(0);
        if (std::isfinite(value)) settings.compensation=std::clamp(value,0.,1.);
    } else if (!ReadObjectValue(reader,settings.source)) return false;
    definitions[&arch]=settings;
    return true;
}
void CmnGravity::ForgetDefinition(Archetype::Root const* arch) { Definitions().erase(arch); }
void CmnGravity::CopyDefinition(Archetype::Equipment const& target, Archetype::Equipment const& donor)
{
    if (target.get_class_type()!=donor.get_class_type()) return;
    auto found=Definitions().find(&donor);
    if (found==Definitions().end()) Definitions().erase(&target);
    else Definitions()[&target]=found->second;
}
void CmnGravity::UnregisterEquipment(CEquip* equip)
{
    auto& devices=Devices();
    devices.erase(std::remove_if(devices.begin(),devices.end(),
        [equip](Device const& device){return device.equip==equip;}),devices.end());
}
void CmnGravity::RegisterEquipment(CEquip* equip)
{
    UnregisterEquipment(equip);
    if (!equip || equip->GetType()==EquipTypeCargo || !equip->GetOwner()) return;
    auto found=Definitions().find(equip->EquipArch());
    if (found!=Definitions().end() && (found->second.source.enabled || found->second.compensation>0)) {
        // Passive devices also activate on solars. Keep old zero-repair definitions compatible.
        if ((equip->GetType()==EquipTypeGravityDevice || equip->GetType()==EquipTypeRepairDroid) &&
            equip->GetHitPoints()>0) equip->Activate(true);
        Devices().push_back({equip,found->second});
    }
}

void CmnGravity::UnregisterSolar(CSolar* solar)
{
    auto& sources=Sources();
    sources.erase(std::remove_if(sources.begin(),sources.end(),
        [solar](Source const& source){return source.solar==solar;}),sources.end());
}

void CmnGravity::RegisterSolar(CSolar* solar)
{
    UnregisterSolar(solar); // Reinitialisation must not duplicate an old source.
    if (!solar || !solar->ObjectDb) return;
    auto const* system=dynamic_cast<CmnUniverse::SYSTEM const*>(solar->ObjectDb->GetZoneDb());
    if (!system) return;
    // MP solar snapshots omit NicknameSrc, but static solars retain the nickname
    // hash as their object id. Both resolve to the same native system entry.
    unsigned nickname=solar->Nickname.Id ? solar->Nickname.Id : solar->Id;
    auto found=system->GravityObjects.find(nickname);
    if (found!=system->GravityObjects.end())
        Sources().push_back({solar,found->second});
}

void CmnGravity::Apply(CShip& ship, IVP_Event_Sim* event, IVP_U_Vector<IVP_Core>* cores)
{
    if ((Sources().empty() && Devices().empty()) || !event || !cores ||
        !(event->delta_time>0) || !std::isfinite(event->delta_time) ||
        !ship.ObjectDb || !ship.BodyPtr || ship.GolemController || ship.bUsingTradelane)
        return;
    // RC copies are moved by remote snapshots; golem-driven animations also
    // own their position. Neither may receive a second local gravity impulse.
    IVP_Core* core=ship.BodyPtr->core;
    if (!core || core->Environment!=event->environment || (core->Flags&0x300u)!=0 ||
        !(core->InvMass>0) || !std::isfinite(core->InvMass)) return;
    bool affected=false;
    for (unsigned i=0;i<cores->n_elems;++i) if (cores->elems[i]==core) affected=true;
    if (!affected) return;
    auto const* system=ship.ObjectDb->GetZoneDb();
    if (!system || system->GetId()!=ship.PhysicsSystemId) return;

    // Read the current PSI centre, not the render/interpolated object transform.
    GravityField::Vector position{core->MWorldFCore.vv.k[0],core->MWorldFCore.vv.k[1],
                                  core->MWorldFCore.vv.k[2]};
    GravityField::Vector total;
    double compensation=0,suppression=0;
    auto accumulate=[&](GravityField::Settings const& field, GravityField::Vector centre) {
        auto a=GravityField::Sample(field,centre,position);
        total.x+=a.x;total.y+=a.y;total.z+=a.z;
        suppression=(std::max)(suppression,GravityField::Suppression(field,centre,position));
    };
    for (Source const& entry:Sources()) {
        CSolar const* source=entry.solar;
        // In SP the shared player reconnects to the client database on entry,
        // while solars retain the server database. Compare system identity, not
        // database addresses; remote ship copies are excluded above already.
        if (!(source->get_hit_pts()>0) || !source->ObjectDb || source->PhysicsSystemId!=ship.PhysicsSystemId)
            continue;
        auto const* sourceSystem=source->ObjectDb->GetZoneDb();
        if (!sourceSystem || sourceSystem->GetId()!=system->GetId()) continue;
        accumulate(entry.field,SourcePosition(*source));
    }
    for (size_t i=0;i<Devices().size();++i) {
        auto const& device=Devices()[i];
        if (!Working(device.equip)) continue;
        auto const* owner=device.equip->GetOwner();
        if (!owner->ObjectDb || owner->PhysicsSystemId!=ship.PhysicsSystemId) continue;
        auto const* ownerSystem=owner->ObjectDb->GetZoneDb();
        if (!ownerSystem || ownerSystem->GetId()!=system->GetId()) continue;
        bool self=SameObject(owner,&ship);
        if (!self && !device.settings.source.enabled) continue;
        if (DuplicateDevice(i)) continue;
        if (self) compensation=(std::max)(compensation,device.settings.compensation);
        if (device.settings.source.enabled && (!self || device.settings.source.field.mode==GravityField::Mode::Suppress))
            accumulate(device.settings.source.field,SourcePosition(*owner));
    }
    double multiplier=(1-compensation)*(1-suppression);
    total.x*=multiplier;total.y*=multiplier;total.z*=multiplier;
    if (!GravityField::Finite(total)) return;
    // Acceleration is independent of ship mass. Use the same pending velocity
    // accumulator as engine impulses; the existing IVP gravity pass commits it.
    core->SpeedChange.x+=static_cast<float>(total.x*event->delta_time);
    core->SpeedChange.y+=static_cast<float>(total.y*event->delta_time);
    core->SpeedChange.z+=static_cast<float>(total.z*event->delta_time);
}
