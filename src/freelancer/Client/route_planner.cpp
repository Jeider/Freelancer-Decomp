#include "route_planner.h"
#include "navigation_settings.h"
#ifdef FREELANCER_PLAYER_FLIGHT_ACTIONS
#include "client_objdb.h"
#include "player_behavior.h"
#include "character_select_equip.h"
#include "common_universe.h"
#include "common_server_asteroid.h"
#include "port_config.h"
#include <algorithm>
#include <map>
#include <string>
#include <cstring>

namespace RoutePlanner {
namespace {
using namespace RouteGeometry;
V v(Vector const& p) { return {p.x,p.y,p.z}; }
Vector vec(V p) { return {p.x,p.y,p.z}; }
struct Hazard { V center; float radius; unsigned object=0; Universe::IZone const* zone=nullptr; bool atmosphere=false; bool dynamic=false; };
std::vector<Hazard> hazards;
std::vector<Vertex> corridors;
unsigned cachedSystem=0;
float margin=300;

bool friendly(Universe::IZone const* z) {
    auto p=static_cast<IObjRW*>(GetPlayerObjRW());
    for(int i=0;p && i<z->GetPopulationCount();++i) {
        unsigned faction=0; float weight=0,feeling=0;
        if(z->GetPopulationEntry(i,faction,weight) && weight>0 &&
           p->get_reputation(feeling,faction)==0 && feeling<-.2f) return false;
    }
    return true;
}
void load() {
    unsigned system=GetPlayerStarSystemIdRetail();
    if(cachedSystem==system) return;
    hazards.clear(); corridors.clear(); cachedSystem=system;
    float setting=PortConfigFloat("Navigation","clearance",300);
    margin=std::isfinite(setting) ? std::clamp(setting,150.f,3000.f):300.f;
    if(auto p=static_cast<IObjRW*>(GetPlayerObjRW())) {
        float radius=0; Vector center; p->get_physical_radius(radius,center);
        if(std::isfinite(radius)) margin+=(std::max)(radius,0.f);
    }
    IObjDB* db=GetClientObjDb();
    auto sys=db ? db->GetZoneDb():nullptr;
    if(!sys || sys->GetId()!=system) { cachedSystem=0; return; }
    uintptr_t iter[3]={0,0,0xfdff};
    while(auto obj=db->GetNext(iter)) {
        unsigned type=0; obj->get_type(type);
        if(type==0x200u || type==0x80u || IsServerAsteroidType(type)) continue;
        float radius=0,atmosphere=0; Vector center;
        obj->get_physical_radius(radius,center);
        obj->get_atmosphere_range(atmosphere);
        radius=(std::max)(radius,atmosphere);
        if(radius>10 && std::isfinite(radius)) hazards.push_back({v(center),radius,obj->get_id(),nullptr,atmosphere>0});
    }
    std::map<std::string,std::vector<CorridorSegment>> paths;
    INI_Reader ini;
    char filename[1024];
    // System files are relative to Universe's directory, including mod systems.
    Universe::get_filename(filename,sys->GetFile());
    bool opened=ini.open(filename,false);
    for(auto const& entry:*sys->GetZones()) {
        auto z=entry.Zone;
        // Radiation, damage volumes, and zones explicitly marked dangerous.
        // 0x10000/0x20000 are exclusion flags, not hazards.
        if(z->GetDamage()>0 || (z->GetProperties()&0x20u)!=0)
            hazards.push_back({v(z->GetPos()),z->GetRadius(),0,z});
        if(!opened || !z->HasPathLabel() || !friendly(z)) continue;
        ini.set_state(entry.State);
        while(ini.read_value()) if(ini.is_value("path_label")) {
            std::string label=ini.get_value_string(0);
            auto const& m=z->GetOrientation();
            V offset=V{m.E[0][1],m.E[1][1],m.E[2][1]}*(z->GetSize().y*.5f);
            for(unsigned i=1;i<32 && !ini.is_value_empty(i);++i)
                paths[label].push_back({ini.get_value_int(i),v(z->GetPos())+offset,v(z->GetPos())-offset});
        }
    }
    // Beta Path ctor 06EAB2E0: ordered zone ends, nearest-end joints,
    // and close-loop midpoint within 5000 m. Reconstructed from the user's DLL.
    int id=0;
    for(auto& path:paths) {
        auto points=betaPath(path.second);
        for(size_t i=0;i<points.size();++i) corridors.push_back({points[i],id,static_cast<int>(i)});
        ++id;
    }
}
void refreshDynamicHazards() {
    // Static solids and zones stay cached for the loaded system. Server rocks
    // move, so retaining their old spheres would create ghosts and miss their
    // current positions. Rebuild only this small dynamic subset per new plan;
    // local PathfindManager avoidance owns changes while a leg is being flown.
    hazards.erase(std::remove_if(hazards.begin(),hazards.end(),
        [](Hazard const& h){return h.dynamic;}),hazards.end());
    IObjDB* db=GetClientObjDb();
    if(!db) return;
    uintptr_t iter[3]={0,0,0xfdff};
    while(auto obj=db->GetNext(iter)) {
        unsigned type=0; obj->get_type(type);
        if(!IsServerAsteroidType(type)) continue;
        float radius=0; Vector center;
        obj->get_physical_radius(radius,center);
        if(radius>10 && std::isfinite(radius))
            hazards.push_back({v(center),radius,obj->get_id(),nullptr,false,true});
    }
}
bool clear(V from,V to,unsigned dockTarget=0,float dockRange=0) {
    for(auto const& h:hazards) {
        // ONLY for validating the native Dock handoff: its collision avoidance
        // owns nearby solid components. Atmospheres and damage zones stay hard
        // constraints, even next to the destination. Cruise legs skip nothing.
        if(dockTarget && !h.zone && !h.atmosphere &&
           (h.object==dockTarget || length(h.center-to)<=dockRange)) continue;
        if(segmentDistance(h.center,from,to)>h.radius+margin) continue;
        if(!h.zone) {
            if(!sphereClear(from,to,h.center,h.radius+margin)) return false;
            continue;
        }
        Vector hit;
        bool escaping=h.zone->InZone(vec(from),margin);
        if(h.zone->InZone(vec(to),margin)) return false;
        if(!escaping && (h.zone->InZone(vec(from),0) ||
           h.zone->Intersect(vec(from),vec(to),hit))) return false;
        // Native intersection protects even very thin volumes. Sampling the
        // expanded shape adds clearance, without treating a ring's hole as solid.
        float distance=length(to-from);
        int count=static_cast<int>(std::ceil(distance/(margin*.5f)));
        count=(std::max)(count,1);
        double lastDistance=h.zone->GetDistance(vec(from));
        bool outside=false;
        for(int i=0;i<=count;++i) {
            V p=from+(to-from)*(static_cast<float>(i)/count);
            bool inside=length(p-h.center)<=h.radius+margin && h.zone->InZone(vec(p),margin);
            if(inside) {
                if(!escaping || outside) return false;
                double d=h.zone->GetDistance(vec(p));
                if(d<lastDistance-.1) return false;
                lastDistance=d;
            } else outside=true;
        }
    }
    return true;
}
bool plan(V from,V to,std::vector<V> const& goals,std::vector<V>& result) {
    std::vector<Sphere> bounds;
    for(auto const& h:hazards) bounds.push_back({h.center,h.radius+margin});
    return planVisibility(from,to,goals,BetaEnabled()?corridors:std::vector<Vertex>{},bounds,
                          [](V a,V b){return clear(a,b);},result);
}
}
bool BetaEnabled() {
    return NavigationSettings::Get(NavigationSettings::Generator)!=0;
}
void Invalidate() { cachedSystem=0; hazards.clear(); corridors.clear(); }
bool Plan(V from,V to,std::vector<V>& result) {
    load(); result.clear();
    if(!cachedSystem) return false;
    refreshDynamicHazards();
    if(!std::isfinite(length(from)) || !std::isfinite(length(to))) return false;
    if(length(to-from)<1) {result.push_back(to);return true;}
    return plan(from,to,{to},result);
}
bool PlanApproach(V from,unsigned destination,std::vector<V>& result) {
    load(); result.clear();
    auto db=GetClientObjDb();
    auto target=db && destination ? db->FindById(&destination):nullptr;
    if(!cachedSystem || !target || !std::isfinite(length(from))) return false;
    refreshDynamicHazards();
    float radius=0,atmosphere=0; Vector physicalCenter;
    target->get_physical_radius(radius,physicalCenter);
    target->get_atmosphere_range(atmosphere);
    V center=v(physicalCenter);
    if(!std::isfinite(radius) || !std::isfinite(atmosphere) || !std::isfinite(length(center))) return false;
    float range=(std::max)((std::max)(radius,atmosphere),0.f)+margin+500.f;
    // Try alternate sides if other station components cover the near side.
    // Unlike Dock, no segment into the target is needed or exempted from checks.
    auto goals=dockingGoals(from,center,range,[](V point){return clear(point,point);});
    return plan(from,center,goals,result);
}
bool PlanDock(V from,V center,unsigned destination,float range,std::vector<V>& result) {
    load(); result.clear();
    if(!cachedSystem || !destination || !std::isfinite(length(from)) ||
       !std::isfinite(length(center)) || !std::isfinite(range) || range<=0) return false;
    refreshDynamicHazards();
    // Keep the arrival sphere beyond the target's guard even for large ships
    // or a user clearance larger than the usual 2000 m docking distance.
    for(auto const& h:hazards) if(h.object==destination)
        range=(std::max)(range,length(h.center-center)+h.radius+margin+500.f);
    auto goals=dockingGoals(from,center,range,[&](V point) {
        return clear(point,point) && clear(point,center,destination,range*2);
    });
    return plan(from,center,goals,result);
}
}
#endif
