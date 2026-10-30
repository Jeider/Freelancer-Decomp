#include "player_action_counters.h"
#include "player_behavior.h"
#include "player_spawn.h"
#include "player_route.h"
#include "player_flight_actions.h"
#include "game_options.h"
#include "globals.h"
#include "input_manager.h"
#include "hud_command_dispatch.h"
#include "nn_modal.h"
#include "nn_arrival_text.h"
#include "space_camera.h"
#include "space_letterbox.h"
#include "star_sys.h"
#include "client_objdb.h"
#include "client_gameobj.h"
#include "common_archetype.h"
#include "common_cequip.h"
#include "common_cobject.h"
#include "common_iface.h"
#include "common_misc.h"
#include "common_net.h"
#include "port_config.h"
#include <algorithm>
#include <map>
#include <windows.h>

namespace PlayerActionCounters {
namespace {
using namespace PlayerActionStats;
State state;
Tracker tracker;
unsigned revision=~0u,system=0,ship=0;
unsigned long long epoch=0,frame=0;
bool ready=false,paused=false,announced=false;
float dt=0;
struct Projectile {
    V relative;
    float lifetime=0;
    unsigned long long seen=0;
    bool hit=false,passedClose=false,incoming=false,closeCounted=false,evaded=false;
};
std::map<CObject*,Projectile> projectiles;
V Vec(Vector const& p){return {p.x,p.y,p.z};}
V Sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
BridgeFn BridgeFunction() {
    if(!SinglePlayer())return nullptr;
    auto module=GetModuleHandleW(L"Server.dll");
    return module ? reinterpret_cast<BridgeFn>(GetProcAddress(module,BridgeExport)) : nullptr;
}
void ResetTransient() {tracker.Reset();projectiles.clear();system=0;ship=0;}
bool Sync() {
    auto fn=BridgeFunction();if(!fn)return ready=false;
    unsigned now=GetGameSessionLoadRevision();
    if(!ready || revision!=now) {
        Bridge packet;packet.player=GetPlayerConnectionId();
        if(!fn(&packet))return ready=false;
        state=packet.state;epoch=packet.epoch;revision=now;ready=true;ResetTransient();
        announced=state.Get(Counter::InertiaSeconds)>=1000;
    }
    return true;
}
bool Flush() {
    if(!ready)return false;
    auto fn=BridgeFunction();if(!fn)return ready=false;
    Bridge packet;packet.player=GetPlayerConnectionId();packet.operation=1;packet.epoch=epoch;packet.state=state;
    if(!fn(&packet)){ready=false;ResetTransient();return false;}
    // Server-only changes never overwrite a pending client increment.
    double repairsBefore=state.Get(Counter::Nanobots)+state.Get(Counter::Batteries);
    state=packet.state;
    if(tracker.combat && state.Get(Counter::Nanobots)+state.Get(Counter::Batteries)>repairsBefore)tracker.repaired=true;
    return true;
}
CProjectile* ProjectileOf(CObject* object) {
    if(!object)return nullptr;
    if(object->ObjectClass==CObject::ClassBeam || object->ObjectClass==CObject::ClassGuided ||
        object->ObjectClass==CObject::ClassMine)return static_cast<CProjectile*>(object);
    return nullptr;
}
Projectile& Observe(CProjectile* object) {
    auto& p=projectiles[object];
    if(p.seen+1<frame || object->Lifetime>p.lifetime+.01f)p=Projectile();
    p.seen=frame;p.lifetime=object->Lifetime;return p;
}
void TrackProjectiles(IObjRW* player) {
    float radius=0;Vector center;player->get_physical_radius(radius,center);
    double close=(std::max)(0.f,radius)+50;
    for(int kind=3;kind<=4;++kind)for(auto* go=ClientObjDb_GetKindHead(&kind);go;go=go->ListNext) {
        auto* object=ProjectileOf(go->Object);
        if(!object || object->get_owner()==player->get_id() || !object->is_alive())continue;
        V relative=Sub(Vec(go->get_position()),Vec(player->get_position()));
        double distance=Length(relative);if(!std::isfinite(distance) || distance>3000)continue;
        auto& p=Observe(object);
        V velocity=Sub(Vec(go->get_velocity()),Vec(player->get_velocity()));
        if(object->ObjectClass==CObject::ClassGuided &&
            static_cast<CGuided*>(object)->get_target()==player && distance<1500)p.incoming=true;
        // Closest point on this frame's relative-motion segment, never across gaps.
        V previous=p.relative;
        if(Length(previous)>0) {
            V segment=Sub(relative,previous);double length2=Dot(segment,segment);
            double t=length2>0 ? (std::max)(0.,(std::min)(1.,-Dot(previous,segment)/length2)) : 0;
            V nearest={previous.x+t*segment.x,previous.y+t*segment.y,previous.z+t*segment.z};
            if(Length(nearest)<close)p.passedClose=true;
        }
        p.relative=relative;
        if(!p.hit && p.passedClose && !p.closeCounted && distance>close+100 && Dot(relative,velocity)>0) {
            state.Add(Counter::ClosePasses);p.closeCounted=true;
        }
        if(!p.hit && p.incoming && !p.evaded && distance>750 && Dot(relative,velocity)>0 &&
            (p.passedClose || (object->ObjectClass==CObject::ClassGuided && static_cast<CGuided*>(object)->get_target()!=player))) {
            state.Add(Counter::MissilesEvaded);p.evaded=true;
        }
    }
    for(auto i=projectiles.begin();i!=projectiles.end();) {
        if(i->second.seen+1<frame)i=projectiles.erase(i);else ++i;
    }
}
}
void BeginFrame(float delta,bool isPaused) {
    dt=delta;paused=isPaused;++frame;Sync();
}
void EndFrame(bool docking) {
    if(!Sync())return;
    auto* player=static_cast<IObjRW*>(GetPlayerObjRW());
    auto* object=static_cast<CShip*>(GetPlayerShipObject());
    if(!player || !object || player->is_dying()){ResetTransient();Flush();return;}
    unsigned currentSystem=StarSysGetActiveSystemId();
    if(system && system!=currentSystem)ResetTransient();
    if(ship && ship!=player->get_id())ResetTransient();
    system=currentSystem;ship=player->get_id();
    Flight f;f.dt=dt;
    f.valid=!paused && !docking && !IsLetterboxVisible() && ClientInputIsActive() &&
        !G_bNnScreenUp && !HudGetInputFocus() && !object->is_launching();
    auto* behavior=GetBehaviorManager(player);
    f.manual=behavior && behavior->CurrentBehaviorIndex==0x13 && !PlayerRoute::Active() &&
        std::strcmp(PlayerFlightActions::TelemetryAction(),"none")==0;
    f.engine=GetPlayerEngineIsActive();player->are_thrusters_active(f.boost);
    player->is_cruise_active(f.cruise,f.lane);
    f.cockpit=IsFirstPersonCameraCurrent();
    StrafeDir strafe=static_cast<StrafeDir>(0);player->get_strafe_dir(strafe);f.strafe=static_cast<int>(strafe);
    f.thrust=object->MaxThrustPower>0 ? object->ThrustPower/object->MaxThrustPower : 1;
    f.velocity=Vec(player->get_velocity());
    auto const& rotation=player->get_orientation();f.forward={-rotation.E[0][2],-rotation.E[1][2],-rotation.E[2][2]};
    float hp=0,maxHp=0;player->get_status(hp,maxHp);f.critical=maxHp>0 && hp/maxHp<=.1;
    IObjRW* target=nullptr;player->get_target(target);
    if(target && !target->is_dying()) {
        f.target=target->get_id();unsigned short sub=0;player->get_subtarget(sub);f.subtarget=sub;
        float attitude=0;target->get_attitude_towards(attitude,player);f.targetHostile=attitude<-.55f;
        IObjRW* targetTarget=nullptr;target->get_target(targetTarget);f.targetingUs=targetTarget==player;
        V relative=Sub(Vec(target->get_position()),Vec(player->get_position()));f.distance=Length(relative);
        if(f.distance>0) {
            f.aimDot=Dot(relative,f.forward)/f.distance;
            f.closing=-Dot(relative,Sub(Vec(target->get_velocity()),f.velocity))/f.distance;
        }
    }
    tracker.Step(state,f);
    if(f.valid && f.manual)TrackProjectiles(player);else projectiles.clear();
    if(Flush() && !announced && state.Get(Counter::InertiaSeconds)>=1000) {
        announced=true;
        NnArrivalTextShowCaption(std::strcmp(PortLanguage(),"ru")==0 ?
            L"\u0414\u043e\u0441\u0442\u0438\u0436\u0435\u043d\u0438\u0435: \u041c\u0430\u0441\u0442\u0435\u0440 \u0438\u043d\u0435\u0440\u0446\u0438\u0438!" :
            L"Achievement: Master of Inertia!");
    }
}
void LeaveSpace(){Flush();ResetTransient();}
void Shot(unsigned owner,unsigned short equipment,bool automatic) {
    if(!Sync() || owner!=GetPlayerShipId())return;
    state.Add(automatic ? Counter::AutoShots : Counter::ManualShots);
    if(!automatic) {
        if(tracker.inertia)state.Add(Counter::InertiaShots);
        if(tracker.reverse)state.Add(Counter::ReverseShots);
        if(tracker.strafing)state.Add(Counter::StrafeShots);
    }
    auto* ship=static_cast<CShip*>(GetPlayerShipObject());
    auto* equip=ship ? ship->EquipManager.FindByID(equipment) : nullptr;
    auto* arch=equip ? equip->EquipArch() : nullptr;
    if(arch) {
        auto kind=arch->get_class_type();
        if(kind==Archetype::AClassMineDropper)state.Add(Counter::Mines);
        else if(kind==Archetype::AClassCounterMeasureDropper)state.Add(Counter::Countermeasures);
        else if(auto* launcher=CELauncher::cast(equip)) {
            auto const* munition=launcher->Projectile;
            if(munition && munition->get_class_type()==Archetype::AClassMunition &&
                static_cast<Archetype::Munition const*>(munition)->Seeker!=0)state.Add(Counter::Missiles);
        }
    }
    auto* player=static_cast<IObjRW*>(GetPlayerObjRW());IObjRW* target=nullptr;
    if(player)player->get_target(target);
    float attitude=0;
    if(target && target->get_attitude_towards(attitude,player)==0 && attitude<-.55f)tracker.Combat(state);
}
void Damage(unsigned object,DamageList const& damage) {
    if(!Sync() || damage.Entries.empty())return;
    if(object==GetPlayerShipId()) {
        if(damage.is_destroyed()){tracker.Reset();return;}
        if(damage.get_cause()!=DamageCause::Collision && damage.get_inflictor_id())tracker.Combat(state);
        if(tracker.combat)tracker.damaged=true;
    } else if(damage.get_inflictor_owner_player()==GetPlayerConnectionId())tracker.Combat(state);
}
void Collision(CObject* a,CObject* b) {
    if(!ready)return;
    auto* player=static_cast<CShip*>(GetPlayerShipObject());if(!player)return;
    auto* pa=ProjectileOf(a);auto* pb=ProjectileOf(b);
    auto hit=[&](CProjectile* projectile,CObject* other) {
        auto& p=Observe(projectile);
        if(p.hit)return;
        p.hit=true;
        if(projectile->get_owner()==GetPlayerShipId() && other!=player)state.Add(Counter::ProjectileHits);
        else if(other==player)state.Add(Counter::ProjectileHitsReceived);
    };
    if(pa)hit(pa,b);if(pb)hit(pb,a);
    if(!pa && !pb && (a==player || b==player))state.Add(Counter::Collisions);
}
bool Snapshot(PlayerActionStats::State& result) {
    if(!Sync() || !Flush())return false;
    result=state;return true;
}
}
