#include "train_yard_bridge.h"
#include "train_courier_bridge.h"
#include "server_train_courier.h"
#include "train_courier_state.h"
#include "server_cobject.h"
#include "../Common/common_train.h"
#include "common_server.h"
#include "common_misc.h"
#include "common_id.h"
#include "server_gameobject.h"
#include "server_sysdb.h"
#include "server_createinfo.h"
#include "DALib.h"
#include "x86math.h"
#include <map>
#include <cstdio>
#include <set>
#include <cstring>

namespace {
struct Yard {unsigned revision=0,locomotive=0,trailer=0;bool spawned=false;};
std::map<unsigned,Yard> yards;
struct Courier {
    unsigned trailer=0,base=0,system=0,solar=0;
    bool transfer=false;
    Vector position{};Matrix orientation{};
    struct Retired {unsigned system;Vector position;};
    std::map<unsigned,Retired> delivered;
    std::map<unsigned,Retired> parked;
    float cleanupDistance=25000.f;
    bool finished=false,inTransit=false;
    unsigned transitSystem=0,transitOwner=0;
    float transitHitpoints=0;
    int transitStatus=0;
};
std::map<unsigned,Courier> couriers;
bool validPose(Vector const& position,Matrix const& orientation) {
    if(!std::isfinite(position.x) || !std::isfinite(position.y) || !std::isfinite(position.z))return false;
    for(int a=0;a<3;++a)for(int b=a;b<3;++b) {
        float dot=0;
        for(int i=0;i<3;++i) {
            if(!std::isfinite(orientation.E[i][a]) || !std::isfinite(orientation.E[i][b]))return false;
            dot+=orientation.E[i][a]*orientation.E[i][b];
        }
        if(std::abs(dot-(a==b?1.f:0.f))>.01f)return false;
    }
    return true;
}
CShip* ship(unsigned id) {
    auto* object=Server_LookupLiveObject(id);
    return object && object->Object && object->Object->ObjectClass==CObject::ClassShip ? static_cast<CShip*>(object->Object):nullptr;
}
bool suspendCourierCargo(Courier& state,CShip* loco,unsigned targetSystem) {
    auto* tail=ship(state.trailer);
    if(!tail || !loco || CmnTrain::Trailer(loco)!=tail || state.inTransit)return false;
    Vector position=tail->WorldPosition;Matrix orientation=tail->Orientation;
    const unsigned owner=tail->OwnerPlayer;
    const float hitpoints=tail->get_hit_pts();
    if(!std::isfinite(hitpoints) || hitpoints<=0)return false;
    if(!CmnTrain::Uncouple(loco))return false;
    unsigned transit=0;
    if(pub::SpaceObj::Relocate(state.trailer,transit,position,orientation)!=0) {
        CmnTrain::RestoreCoupling(loco,tail);return false;
    }
    state.transitOwner=owner;state.transitHitpoints=hitpoints;
    state.inTransit=true;state.transitSystem=targetSystem;state.transitStatus=0;
    return true;
}
int resumeCourierCargo(Courier& state,CShip* loco,unsigned currentSystem) {
    auto* tail=ship(state.trailer);
    if(!state.inTransit)return loco && tail && CmnTrain::Trailer(loco)==tail?1:0;
    // SystemSwitchOutComplete changes the player's system before the jump-in
    // animation/client world are ready. Publishing the tail then can leave it
    // in the client world that is about to be discarded.
    if(!loco || !currentSystem || loco->is_launching() || loco->is_jumping() || !loco->BodyPtr ||
       loco->PhysicsSystemId!=currentSystem)return -1;
    if(state.transitSystem && state.transitSystem!=currentSystem)return -2;
    if(!tail)return -3;
    unsigned tailSystem=0;pub::SpaceObj::GetSystem(state.trailer,tailSystem);
    if(tailSystem==currentSystem && CmnTrain::Trailer(loco)==tail) {
        state.inTransit=false;return 1;
    }
    // A previous attempt may have relocated the object before coupling failed.
    // Rebuild missing physics through transit, not a same-system beam.
    if(tailSystem==currentSystem && (!tail->BodyPtr || tail->PhysicsSystemId!=currentSystem)) {
        unsigned transit=0;
        if(pub::SpaceObj::Relocate(state.trailer,transit,loco->WorldPosition,loco->Orientation)!=0)return -4;
        tailSystem=0;
    }
    if(tailSystem!=currentSystem) {
        // SP DESTROYOBJECT temporarily gives the shared CShip to the client to
        // retire its visual wrapper. That ownership survives the old ObjDB's
        // teardown. Restore it BEFORE add_ship: otherwise enter_system skips
        // connecting the NPC to its world and CreateShipForPlayer mistakes the
        // wagons for the player's own ship, suppressing their create packet.
        tail->SetOwnerPlayer(state.transitOwner);
        // FClientSimpleGameobj::Slot19c also zeroes the shared hull for type 0
        // (visual removal). This is transit, not damage: keep the exact hull
        // recorded before removal, including any real pre-jump damage.
        tail->set_hit_pts(state.transitHitpoints);
        if(pub::SpaceObj::Relocate(state.trailer,currentSystem,loco->WorldPosition,loco->Orientation)!=0)return -4;
    }
    tail=ship(state.trailer);
    if(!tail || !CmnTrain::RestoreCoupling(loco,tail))return -5;
    state.inTransit=false;return 1;
}
CEqObj* parkedSolar(unsigned id) {
    auto* object=Server_LookupLiveObject(id);
    if(!object || !object->Object || object->Object->ObjectClass!=CObject::ClassSolar)return nullptr;
    auto* solar=static_cast<CEqObj*>(object->Object);
    return solar->get_archetype()->Nickname.Id==CreateID("tc_parked_locomotive")?solar:nullptr;
}
unsigned spawn(CShip* loco,unsigned player) {
    unsigned system=0;
    if(pub::SpaceObj::GetSystem(loco->Id,system)!=0)return 0;
    auto* world=SysDB_LookupSystem(system);
    auto* arch=Archetype::GetShip(CreateID("ge_train_wagons"));
    auto* pod=Archetype::GetEquipment(CreateID("cargopod_grey"));
    auto* gun=Archetype::GetEquipment(CreateID("co_train_turret01_mark01"));
    if(!world || !arch || !pod || !gun || !CFLIDMaker::GetInstance())return 0;
    FShipCreateRequest request;
    request.EquipStateData=nullptr;request.MarkPlayerId=player;
    request.ObjId=CFLIDMaker::GetInstance()->AllocateObjectID();
    request.ArchetypeNickname=arch->Nickname.Id;
    request.Position=loco->WorldPosition;
    // Clear the locomotive hull on load, inside the enlarged capture distance.
    float offset=25.1456f+.22488f+TrainYard::SpawnPinGap;
    request.Position.x+=loco->Orientation.E[0][2]*offset;
    request.Position.y+=loco->Orientation.E[1][2]*offset;
    request.Position.z+=loco->Orientation.E[2][2]*offset;
    Server_MatrixToQuat(request.Orientation,loco->Orientation);
    request.Velocity=loco->get_velocity();
    FmtStr name,empty;name.begin_mad_lib(237055);name.end_mad_lib();
    int reputation=-1;
    if(pub::Reputation::Alloc(reputation,empty,name)!=0)return 0;
    pub::Reputation::SetAttitude(reputation,loco->VibeId,1.f);
    pub::Reputation::SetAttitude(loco->VibeId,reputation,1.f);
    request.HitPts=-1;request.VibeGroupId=reputation;
    arch->get_undamaged_collision_group_list(request.CollisionGroups);
    auto equip=[&](Archetype::Equipment* equipment,char const* hp) {
        EquipDesc item;
        item.set_id(request.EquipIds.CreateEquipID());
        item.set_arch_id(equipment->Nickname.Id);item.set_equipped(1);
        CacheString hardpoint={StringAlloc(hp,false)};item.set_hardpoint(hardpoint);
        request.Equipment.add_equipment_item(item,false);
    };
    for(unsigned i=1;i<=40;++i) {
        char hp[32];std::snprintf(hp,sizeof(hp),"HpCargo%02u",i);
        equip(pod,hp);
    }
    equip(gun,"HpTurret06");
    auto* created=world->create_ship(request);
    if(!created)pub::Reputation::Free(reputation);
    return created ? created->get_id():0;
}
}
// Local SP bridge, called between simulation updates just like the existing
// player action bridge. No transport RPC or multiplayer authorization surface.
extern "C" __declspec(dllexport) int __cdecl TrainYardBridge(TrainYard::Packet* p) {
    if(!p || p->size!=sizeof(*p) || p->version!=2 || !SinglePlayer())return 0;
    unsigned id=0;
    if(pub::Player::GetShip(p->player,id)!=0)return 0;
    CShip* loco=ship(id);
    if(!CmnTrain::IsLocomotive(loco))return 0;
    auto& yard=yards[p->player];
    auto managed=couriers.find(p->player);
    if(managed!=couriers.end()) {
        yard.trailer=managed->second.trailer;yard.spawned=true;
        yard.revision=p->revision;yard.locomotive=id;
    } else if(yard.revision!=p->revision || yard.locomotive!=id) {
        yard={};yard.revision=p->revision;yard.locomotive=id;
    }
    if(p->operation==1 && !yard.spawned) {
        yard.trailer=spawn(loco,p->player);
        yard.spawned=yard.trailer!=0;
    }
    auto* tail=ship(yard.trailer);
    p->trailer=yard.trailer;p->result=-10;
    if(tail) {
        if(p->operation==2)p->result=CmnTrain::BeginCouple(loco,tail);
        else if(p->operation==4)p->result=CmnTrain::CancelCoupling(loco)?1:-2;
        else if(p->operation==3) {
            p->result=(loco->is_using_tradelane() || loco->is_cruise_active() || loco->is_launching()) ? -7 :
                (CmnTrain::Uncouple(loco)?1:-2);
        } else p->result=CmnTrain::CanCouple(loco,tail,&p->distance);
    }
    p->coupled=CmnTrain::Trailer(loco)!=nullptr;
    p->approaching=CmnTrain::IsCoupling(loco);
    return 1;
}

extern "C" __declspec(dllexport) int __cdecl TrainCourierBridge(TrainCourier::Packet* p) {
#ifndef FREELANCER_RPG_WORLD
    (void)p;return 0;
#else
    if(!p || p->size!=sizeof(*p) || p->version!=1 || !SinglePlayer())return 0;
    unsigned currentSystem=0;
    if(pub::Player::GetSystem(p->player,currentSystem)!=0)return 0;
    using Op=TrainCourier::Operation;
    p->result=0;
    // Archetype check survives mission teardown and does not depend on ownership.
    if(p->operation==Op::IsParkedSolar){p->result=parkedSolar(p->launchSolar)?1:0;return 1;}
    if(p->operation==Op::Register) {
        if(!std::isfinite(p->cleanupDistance) || p->cleanupDistance<1000.f)return 1;
        if(p->trailer && (!ship(p->trailer) || !CmnTrain::IsTrailer(ship(p->trailer))))return 1;
        for(auto const& entry:couriers)if(entry.second.delivered.count(p->trailer))return 1;
        auto& state=couriers[p->player];
        if(state.delivered.count(p->trailer))return 1;
        state.trailer=p->trailer;state.finished=false;state.inTransit=false;state.cleanupDistance=p->cleanupDistance;p->result=1;
    }
    auto found=couriers.find(p->player);
    if(found==couriers.end())return 1;
    auto& state=found->second;
    unsigned locoId=0;pub::Player::GetShip(p->player,locoId);
    auto* loco=ship(locoId);
    if(p->operation==Op::Retire) {
        if(p->trailer!=state.trailer || !p->trailer || !ship(p->trailer) ||
           CmnTrain::IsDriven(ship(p->trailer)))return 1;
        auto* tail=ship(p->trailer);
        unsigned system=0;
        if(pub::SpaceObj::GetSystem(p->trailer,system)!=0)return 1;
        CmnTrain::SetCouplable(p->trailer,false);
        state.delivered.emplace(p->trailer,Courier::Retired{system,tail->WorldPosition});
        state.trailer=0;p->result=1;p->retired=1;
    } else if(p->operation==Op::Release) {
        if(p->trailer) {
            // Releasing a job must never make its delivered group reusable.
            if(state.delivered.count(p->trailer) || p->trailer!=state.trailer)return 1;
            if(state.trailer==p->trailer)state.trailer=0;
            p->result=1;
        } else {
            state.trailer=0;state.transfer=false;state.finished=true;
            // Cleanup survives mission completion until the player leaves.
            yards.erase(p->player);p->result=1;return 1;
        }
    } else if(p->operation==Op::Snapshot) {
        auto* tail=ship(state.trailer);if(!tail || state.inTransit)return 1;
        CShipCreateInfo info;CShipCreateInfo_Fill(&info,tail);
        if(info.Equipment.End-info.Equipment.Begin>TrainCourier::CargoSnapshot::MaxEquipment ||
           info.CollisionGroups.size()>TrainCourier::CargoSnapshot::MaxGroups)return 1;
        auto& c=p->cargo;c={};
        c.arch=info.ArchetypeNickname;c.hitpoints=info.HitPts;
        pub::SpaceObj::GetSystem(state.trailer,c.system);
        c.position=tail->WorldPosition;c.orientation=tail->Orientation;
        c.coupled=loco && CmnTrain::Trailer(loco)==tail;
        for(auto* e=info.Equipment.Begin;e!=info.Equipment.End;++e) {
            auto& out=c.equipment[c.equipmentCount++];out.arch=e->get_arch_id();out.count=e->get_count();
            out.health=e->get_status();out.mounted=e->is_equipped();
            char const* hp=e->get_hardpoint().Value;
            if(hp)std::snprintf(out.hardpoint,sizeof(out.hardpoint),"%s",hp);
        }
        for(auto const& g:info.CollisionGroups)c.groups[c.groupCount++]={g.Id,g.Health};
        p->result=1;
    } else if(p->operation==Op::Restore) {
        auto const& c=p->cargo;
        if(!loco || loco->is_launching() || !loco->BodyPtr || loco->PhysicsSystemId!=currentSystem)return 1;
        if(state.trailer || c.system!=currentSystem || c.equipmentCount>TrainCourier::CargoSnapshot::MaxEquipment ||
           c.groupCount>TrainCourier::CargoSnapshot::MaxGroups || c.hitpoints<=0 || !validPose(c.position,c.orientation))return 1;
        auto* arch=Archetype::GetShip(c.arch);
        bool known=false;for(unsigned n=2;n<=20;++n){char nick[32];std::snprintf(nick,sizeof(nick),"tc_wagons_%02u",n);if(CreateID(nick)==c.arch)known=true;}
        auto* world=SysDB_LookupSystem(currentSystem);
        if(!known || !arch || !world || !CFLIDMaker::GetInstance())return 1;
        FShipCreateRequest req;req.EquipStateData=nullptr;req.MarkPlayerId=p->player;
        req.ObjId=CFLIDMaker::GetInstance()->AllocateObjectID();req.ArchetypeNickname=c.arch;
        req.Position=c.position;Server_MatrixToQuat(req.Orientation,c.orientation);req.HitPts=c.hitpoints;
        for(unsigned i=0;i<c.equipmentCount;++i) {
            auto const& e=c.equipment[i];
            if(!Archetype::GetEquipment(e.arch) || e.count<1 || !std::isfinite(e.health) || e.health<0 || e.health>1 || !std::memchr(e.hardpoint,0,64))return 1;
            EquipDesc desc;desc.set_id(req.EquipIds.CreateEquipID());desc.set_arch_id(e.arch);desc.set_count(e.count);
            desc.set_status(e.health);desc.set_equipped(static_cast<unsigned char>(e.mounted!=0));
            CacheString hp={StringAlloc(e.hardpoint,false)};desc.set_hardpoint(hp);req.Equipment.add_equipment_item(desc,false);
        }
        for(unsigned i=0;i<c.groupCount;++i) {
            auto const& g=c.groups[i];
            if(g.id>65535 || !std::isfinite(g.health) || g.health<0 || g.health>1)return 1;
            req.CollisionGroups.push_back({static_cast<unsigned short>(g.id),0,g.health});
        }
        FmtStr name,empty;name.begin_mad_lib(237055);name.end_mad_lib();
        if(pub::Reputation::Alloc(req.VibeGroupId,empty,name)!=0)return 1;
        if(loco){pub::Reputation::SetAttitude(req.VibeGroupId,loco->VibeId,1.f);pub::Reputation::SetAttitude(loco->VibeId,req.VibeGroupId,1.f);}
        auto* created=world->create_ship(req);
        if(!created){pub::Reputation::Free(req.VibeGroupId);return 1;}
        state.trailer=created->get_id();state.inTransit=false;
        if(c.coupled && (!loco || !CmnTrain::RestoreCoupling(loco,ship(state.trailer)))) {
            unsigned failed=state.trailer;state.trailer=0;pub::SpaceObj::Destroy(failed,DESTROY_NORMAL);return 1;
        }
        p->result=1;
    } else if(p->operation==Op::SuspendCargo) {
        if(!suspendCourierCargo(state,loco,p->system))return 1;
        p->result=1;
        FDUMP(0x100001,"TrainCourier: suspended player=%u trailer=%u target=%u",p->player,state.trailer,state.transitSystem);
    } else if(p->operation==Op::ResumeCargo) {
        int status=resumeCourierCargo(state,loco,currentSystem);
        if(status!=state.transitStatus) {
            FDUMP(0x100001,"TrainCourier: resume player=%u trailer=%u system=%u status=%d",p->player,state.trailer,currentSystem,status);
            state.transitStatus=status;
        }
        p->result=status==1?1:0;
    } else if(p->operation==Op::Transfer) {
        if(!validPose(p->position,p->orientation))return 1;
        unsigned base=0;pub::Player::GetBase(p->player,base);
        if(!base || base!=p->base || currentSystem!=p->system)return 1;
        // BaseEnter runs while the SP physics world is shut down. Arm only the
        // saved pose; Content restores its solar on PlayerLaunch, not here.
        state.base=base;state.system=currentSystem;state.solar=0;
        state.position=p->position;state.orientation=p->orientation;state.transfer=true;p->result=1;
    } else if(p->operation==Op::LaunchSolar) {
        unsigned solarSystem=0;
        auto* solar=parkedSolar(p->launchSolar);
        Vector position;Matrix orientation;
        if(!state.transfer || !solar || pub::SpaceObj::GetSystem(p->launchSolar,solarSystem)!=0 ||
           solarSystem!=state.system || solarSystem!=currentSystem ||
           !solar->launch_pos(position,orientation,0))return 1;
        state.solar=p->launchSolar;p->result=1;
    } else if(p->operation==Op::ClearTransfer) {state.transfer=false;p->result=1;}
    else if(p->operation==Op::Query) p->result=1;
    p->trailer=state.trailer;
    p->inTransit=state.inTransit;
    p->launchSolar=state.solar;
    p->coupled=loco && CmnTrain::Trailer(loco) &&
        static_cast<CShip*>(CmnTrain::Trailer(loco))->Id==state.trailer;
    return 1;
#endif
}

bool TrainCourierLaunchPose(unsigned player,Vector& position,Quaternion& orientation,unsigned& solar,int& dockIndex) {
    auto found=couriers.find(player);
    if(found==couriers.end() || !found->second.transfer)return false;
    auto& state=found->second;
    unsigned system=0;
    if(pub::Player::GetSystem(player,system)!=0 || system!=state.system)return false;
    // Entry resumes at the exact saved pose with dock ID zero. The final
    // transfer instead uses the verified visible solar and its native berth.
    position=state.position;Server_MatrixToQuat(orientation,state.orientation);solar=0;
    if(auto* dock=parkedSolar(state.solar)) {
        Matrix rotation;
        if(dock->launch_pos(position,rotation,0)) {
            Server_MatrixToQuat(orientation,rotation);solar=state.solar;dockIndex=0;
            // Server owns the temporary solar after launch, including after the
            // mission controller has gone. Never delete a live launch anchor.
            state.parked.emplace(solar,Courier::Retired{system,dock->WorldPosition});
        }
    }
    state.transfer=false;return true;
}

void TrainCourierTick() {
#ifdef FREELANCER_RPG_WORLD
    std::vector<unsigned> remove,removeSolars;
    for(auto& entry:couriers) {
        unsigned system=0,id=0;
        if(pub::Player::GetSystem(entry.first,system)!=0 || !system)continue;
        pub::Player::GetShip(entry.first,id);
        auto* playerShip=ship(id);
        auto& state=entry.second;
        unsigned base=0;pub::Player::GetBase(entry.first,base);
        TrainCourier::Rules rules;rules.cleanupDistance=state.cleanupDistance;
        for(auto it=state.delivered.begin();it!=state.delivered.end();) {
            auto const& record=it->second;
            float distance=0;
            if(playerShip) {
                Vector delta={playerShip->WorldPosition.x-record.position.x,
                              playerShip->WorldPosition.y-record.position.y,
                              playerShip->WorldPosition.z-record.position.z};
                distance=std::sqrt(delta.x*delta.x+delta.y*delta.y+delta.z*delta.z);
            }
            if(!ship(it->first) || TrainCourier::cleanupRetired(record.system,system,distance,rules)) {
                remove.push_back(it->first);it=state.delivered.erase(it);
            } else ++it;
        }
        for(auto it=state.parked.begin();it!=state.parked.end();) {
            auto const& record=it->second;
            float distance=0;
            if(playerShip) {
                Vector delta={playerShip->WorldPosition.x-record.position.x,
                              playerShip->WorldPosition.y-record.position.y,
                              playerShip->WorldPosition.z-record.position.z};
                distance=std::sqrt(delta.x*delta.x+delta.y*delta.y+delta.z*delta.z);
            }
            bool leaving=!state.transfer &&
                ((base && !playerShip) || TrainCourier::cleanupRetired(record.system,system,distance,rules));
            if(!parkedSolar(it->first) || (leaving && (!playerShip || !playerShip->is_launching()))) {
                removeSolars.push_back(it->first);it=state.parked.erase(it);
            } else ++it;
        }
    }
    // Destroy sends callbacks: never hold an iterator into courier state here.
    for(unsigned id:remove) {
        if(ship(id))pub::SpaceObj::Destroy(id,DESTROY_NORMAL); // Act_Destroy SILENT
        CmnTrain::SetCouplable(id,true);
    }
    for(unsigned id:removeSolars)if(parkedSolar(id)) {
        int reputation=-1;pub::SpaceObj::GetRep(id,reputation);
        pub::SpaceObj::Destroy(id,DESTROY_NORMAL);
        // This solar was detached from FSystemInfo's mission list, whose normal
        // RemoveMissionObject would have released its allocated reputation.
        if(reputation!=-1)pub::Reputation::Free(reputation);
    }
    for(auto it=couriers.begin();it!=couriers.end();) {
        if(it->second.finished && it->second.delivered.empty() && it->second.parked.empty())it=couriers.erase(it);
        else ++it;
    }
#endif
}

void TrainCourierReset(unsigned player) {
    // Loading/logout destroys the old world separately; forget its ID tombstones.
    for(auto it=couriers.begin();it!=couriers.end();) {
        if(!player || it->first==player) {
            for(auto const& entry:it->second.delivered)CmnTrain::SetCouplable(entry.first,true);
            yards.erase(it->first);it=couriers.erase(it);
        } else ++it;
    }
}
