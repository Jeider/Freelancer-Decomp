// Included by ship_cache.cpp: reuse its private cache records without exposing
// ownership of those records across DLLs. The multiplayer path never enters here.
#include "player_ship_transfer.h"
#include "server_cobject.h"
#include "server_gameobject.h"
#include "server_sysdb.h"
#include "server_createinfo.h"
#include "../Common/common_train.h"
#include <windows.h>
#include <cmath>

namespace {
struct SpaceTransfer {
    PlayerShipTransfer::State state;
    PlayerShipTransfer::Packet request;
    ShipCacheRecord original;
    ShipCacheRecord slotData;
    std::vector<ShipCacheRecord> committedCache;
    bool clientReady = false;
    bool rejected = false;
};
SpaceTransfer GSpaceTransfer;

PlayerShipTransfer::Mission SpaceTransferMission() {
    auto module = GetModuleHandleA("Content.dll");
    return module ? reinterpret_cast<PlayerShipTransfer::Mission>(
        GetProcAddress(module, "TrainCourierShipTransfer")) : nullptr;
}
CShip* SpaceTransferShip(unsigned id) {
    auto* go = Server_LookupLiveObject(id);
    return go && go->Object && go->Object->ObjectClass == CObject::ClassShip ?
        static_cast<CShip*>(go->Object) : nullptr;
}
bool SpaceTransferAllowed(PlayerSlot const& slot, CShip const* ship) {
    return ship && ship->OwnerPlayer == slot.client_id && slot.current_base == 0 &&
        ship->BodyPtr && ship->PhysicsSystemId == slot.system_id && ship->get_hit_pts() > 0 &&
        !ship->is_jumping() && !ship->is_using_tradelane() && !ship->is_cruise_active() &&
        !CmnTrain::Trailer(ship);
}
bool SpaceTransferClear(StarSystem& system, CShip const& candidate, unsigned source, unsigned anchor) {
    float radius = candidate.get_radius();
    if (!std::isfinite(radius) || radius <= 0 || !std::isfinite(candidate.WorldPosition.x) ||
        !std::isfinite(candidate.WorldPosition.y) || !std::isfinite(candidate.WorldPosition.z)) return false;
    auto clear = [&](FSystemListNode* node) {
        for (; node; node = node->Next) {
            auto* go = node->Data;
            if (!go || go->get_id() == source || go->get_id() == anchor ||
                go->get_id() == candidate.Id || !go->Object || !go->Object->BodyPtr) continue;
            auto const& a = candidate.WorldPosition;
            auto const& b = go->Object->WorldPosition;
            float distance2 = (a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z);
            float separation = radius + go->Object->get_radius() + 5.f;
            if (!std::isfinite(distance2) || distance2 < separation*separation) return false;
        }
        return true;
    };
    return clear(system.Ships.Head) && clear(system.Solars.Head);
}
bool QueueSpaceTransfer(PlayerShipTransfer::Packet& p) {
    auto callback = SpaceTransferMission();
    PlayerSlot* slot = nullptr;
    if (!SinglePlayer() || IsMPServer() || !GSpaceTransfer.clientReady || !callback ||
        !ValidPlayer(p.player, slot) || !SpaceTransferAllowed(*slot, SpaceTransferShip(slot->ship_object_id)) ||
        GSpaceTransfer.state.blocksSave()) return false;
    p.source = slot->ship_object_id; p.system = slot->system_id;
    if (!callback(&p, 0)) return false;
    if (!GSpaceTransfer.state.begin(true, p.player, p.system, p.source)) return false;
    p.generation = GSpaceTransfer.state.generation;
    GSpaceTransfer.request = p;
    FDUMP(0x100001,"ShipTransfer: queued player=%u source=%u system=%u return=%u",
          p.player,p.source,p.system,p.returning?1u:0u);
    return true;
}
}

bool PlayerShipTransferDock(unsigned player, unsigned anchor, unsigned base) {
#ifdef FREELANCER_RPG_WORLD
    if (!SinglePlayer() || IsMPServer()) return false;
    auto const& pending = GSpaceTransfer;
    if (pending.state.blocksSave() && pending.state.player == player &&
        ((anchor && pending.request.anchor == anchor) ||
         (!anchor && base && pending.request.base == base))) return true;
    PlayerShipTransfer::Packet p;
    p.player = player; p.anchor = anchor; p.base = base;
    PlayerSlot* slot = nullptr;
    auto callback = SpaceTransferMission();
    if (!ValidPlayer(player, slot) || !callback) return false;
    p.source = slot->ship_object_id; p.system = slot->system_id;
    if (!callback(&p, 0)) return false; // ordinary docking
    FDUMP(0x100001,"ShipTransfer: dock intercepted player=%u anchor=%u base=%u clientReady=%u",
          player,p.anchor,base,GSpaceTransfer.clientReady?1u:0u);
    if (!QueueSpaceTransfer(p)) {
        // Authorized transfer failures must not become a hidden-base landing.
        GSpaceTransfer.request = p;
        GSpaceTransfer.rejected = true;
    }
    return true;
#else
    return false;
#endif
}

void PlayerShipTransferReset(unsigned player) {
    auto& t = GSpaceTransfer;
    if (player && t.state.player && player != t.state.player) return;
    t.state.resetSession();
    t.clientReady = false;
    t.rejected = false;
    t.request = PlayerShipTransfer::Packet();
    t.original = ShipCacheRecord();
    t.slotData = ShipCacheRecord();
    t.committedCache.clear();
}

extern "C" __declspec(dllexport) int __cdecl PlayerShipTransferBridge(PlayerShipTransfer::Packet* p) {
#ifndef FREELANCER_RPG_WORLD
    return 0;
#else
    using namespace PlayerShipTransfer;
    // Check the execution mode before dereferencing a caller's packet. No MP
    // player slot, cache, object list or physics state is touched by this API.
    if (!SinglePlayer() || IsMPServer()) return 0;
    if (!p || p->size != sizeof(*p) || p->version != 1) return 0;
    p->result = 0;
    PlayerSlot* slot = nullptr;
    if (!ValidPlayer(p->player, slot)) return 1;
    auto& t = GSpaceTransfer;
    if (p->operation == Operation::ClearLocomotive) {
        if (t.state.blocksSave() && (t.request.purpose!=Purpose::Reboard || t.state.phase==Phase::Committed)) return 1;
        auto& records=GCaches[slot->client_id].Ships;
        for(auto it=records.begin();it!=records.end();)
            if(_stricmp(it->Name,"train_courier_locomotive")==0)it=records.erase(it);else ++it;
        p->result=1;return 1;
    }
    if (p->operation == Operation::QueueReturn) {
        if (!t.clientReady) { p->result = -1; return 1; }
        p->returning = true; p->result = QueueSpaceTransfer(*p) ? 1 : 0; return 1;
    }
    if (p->operation == Operation::Poll) {
        t.clientReady = true;
        if (t.rejected && t.request.player == p->player) {
            *p = t.request; p->result = -2; t.rejected = false; return 1;
        }
        if (t.state.phase == Phase::Preparing && t.state.player == p->player) {
            *p = t.request; p->result = 1;
        }
        return 1;
    }
    if (!t.state.matches(p->generation, p->player)) return 1;
    if (p->operation == Operation::Cancel) {
        p->result = t.state.cancel(p->generation, p->player) ? 1 : 0;
        FDUMP(0x100001,"ShipTransfer: cancel player=%u generation=%llu result=%d",p->player,p->generation,p->result);
        if (p->result) if (auto callback = SpaceTransferMission()) callback(&t.request, 2);
        return 1;
    }
    CShip* old = SpaceTransferShip(t.state.source);
    if (p->operation == Operation::Prepare) {
        if (t.state.phase != Phase::Preparing || slot->ship_object_id != t.state.source ||
            slot->system_id != t.state.system || !SpaceTransferAllowed(*slot, old)) return 1;
        auto authorize=SpaceTransferMission();
        if(!authorize || !authorize(&t.request,0))return 1;
        CShipCreateInfo info;
        CShipCreateInfo_Fill(&info, old);
        bool const evacuating=t.request.purpose==Purpose::Evacuate || t.request.purpose==Purpose::Emergency;
        bool const reboarding=t.request.purpose==Purpose::Reboard;
        Snapshot(*slot, evacuating?"train_courier_locomotive":"train_courier_ship", t.original);
        t.original.RelativeHealth = old->get_hit_pts() / old->get_max_hit_pts();
        t.original.Groups = info.CollisionGroups;
        t.original.Equipment.Items.clear();
        for (auto* item = info.Equipment.Begin; item != info.Equipment.End; ++item)
            t.original.Equipment.Items.push_back(*item);
        auto& cache = GCaches[slot->client_id];
        auto* saved = FindByName(cache, "train_courier_ship");
        ShipCacheRecord target;
        if (t.request.returning) {
            if (!saved || saved->Parking) return 1;
            target = *saved;
            if(evacuating)t.request.locomotiveHealth=t.original.RelativeHealth;
        } else if(reboarding) {
            auto* locomotive=FindByName(cache,"train_courier_locomotive");
            if(saved || !locomotive || locomotive->Parking ||
               !std::isfinite(t.request.locomotiveHealth) || t.request.locomotiveHealth<=.05f ||
               t.request.locomotiveHealth>1.f)return 1;
            target=*locomotive;
            target.RelativeHealth=(std::min)(target.RelativeHealth,t.request.locomotiveHealth);
        } else {
            // Never overwrite the original ship on a retried boarding request.
            if (saved) return 1;
            target.ShipArchetype = CreateID("ge_train_loco_player");
            EquipDescVector loadout;
            if (pub::GetLoadout(loadout, CreateID("tc_locomotive")) != 0) return 1;
            SubObjectID::EquipIdMaker ids;
            for (auto* item = loadout.Begin; item != loadout.End; ++item) {
                EquipDesc copy(*item); copy.set_id(ids.CreateEquipID());
                target.Equipment.Items.push_back(copy);
            }
        }
        if (!Archetype::GetShip(target.ShipArchetype) || !CFLIDMaker::GetInstance()) return 1;
        unsigned id = CFLIDMaker::GetInstance()->AllocateObjectID();
        // Allocate/copy all cache and equipment storage before committing any
        // player identity. Commit below only swaps already prepared containers.
        t.committedCache = cache.Ships;
        if (t.request.returning) {
            for (auto it = t.committedCache.begin(); it != t.committedCache.end(); ++it)
                if (_stricmp(it->Name, "train_courier_ship") == 0) { t.committedCache.erase(it); break; }
        } else t.committedCache.push_back(t.original);
        if(evacuating || reboarding) {
            for(auto it=t.committedCache.begin();it!=t.committedCache.end();)
                if(_stricmp(it->Name,"train_courier_locomotive")==0)it=t.committedCache.erase(it);else ++it;
            if(evacuating)t.committedCache.push_back(t.original);
        }
        t.slotData = target;
        if (!t.state.ready(p->generation, p->player, id)) return 1;
        t.request.ship = target; t.request.target = id;
        *p = t.request; p->result = 1; return 1;
    }
    if (p->operation == Operation::Commit) {
        if (t.state.phase != Phase::Ready || slot->ship_object_id != t.state.source ||
            slot->system_id != t.state.system || !SpaceTransferAllowed(*slot, old)) return 1;
        // The minute can expire or the parked hull can be destroyed while a
        // candidate is prepared. Reauthorize before changing either identity.
        if(t.request.purpose==Purpose::Reboard) {
            auto callback=SpaceTransferMission();
            if(!callback || !callback(&t.request,0))return 1;
        }
        auto* candidate = static_cast<CShip*>(CObject::Find(t.state.target, CObject::ClassShip));
        auto* system = SysDB_LookupSystem(t.state.system);
        if (!candidate || !system || candidate->OwnerPlayer != p->player ||
            candidate->get_archetype()->get_id() != t.request.ship.ShipArchetype) return 1;
        if(t.request.purpose==Purpose::Reboard) {
            t.request.ship.RelativeHealth=(std::min)(t.request.ship.RelativeHealth,t.request.locomotiveHealth);
            candidate->set_hit_pts(t.request.ship.RelativeHealth*candidate->get_max_hit_pts());
        }
        if (t.request.returning && !SpaceTransferClear(*system, *candidate, t.state.source, t.request.anchor)) return 1;
        FShipCreateRequest req;
        CShipCreateInfo_Fill(&req, candidate);
        req.EquipStateData = nullptr; req.MarkPlayerId = 0;
        auto* created = system->create_ship(req);
        if (!created) return 1;
        // All fallible preparation precedes this point. No simulation or message
        // pumping is permitted between Commit and Finish on the client.
        t.state.commit(p->generation, p->player, slot->system_id, slot->ship_object_id);
        slot->ship_object_id = t.state.target;
        slot->created_ship_id = t.state.target;
        slot->ship_archetype = t.request.ship.ShipArchetype;
        slot->relative_health = t.request.ship.RelativeHealth;
        slot->equipment.Items.swap(t.slotData.Equipment.Items);
        slot->collision_groups.swap(t.slotData.Groups);
        slot->weapon_group_name.swap(t.slotData.WeaponGroups);
        GCaches[slot->client_id].Ships.swap(t.committedCache);
        p->ship.RelativeHealth=t.request.ship.RelativeHealth;
        p->result = 1; return 1;
    }
    if (p->operation == Operation::Finish) {
        if (t.state.phase != Phase::Committed || slot->ship_object_id != t.state.target) return 1;
        auto* system = SysDB_LookupSystem(t.state.system);
        auto* previous = Server_LookupLiveObject(t.state.source);
        if (!system) return 1;
        if (previous) {
            system->remove_ship(previous, nullptr);
            delete previous;
        }
        if (auto* current = SpaceTransferShip(t.state.target)) current->enable_collisions_r(true);
        SendWeaponGroups(slot->client_id, slot->weapon_group_name);
        auto notification = t.request;
        t.state.finish(p->generation, p->player);
        if (auto callback = SpaceTransferMission()) callback(&notification, 1);
        FDUMP(0x100001,"ShipTransfer: finished player=%u old=%u new=%u system=%u world=%p loaded=%u",
              p->player,notification.source,notification.target,notification.system,system,unsigned(system->bLoaded));
        p->result = 1; return 1;
    }
    return 1;
#endif
}
