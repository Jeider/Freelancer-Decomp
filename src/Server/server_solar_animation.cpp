#include "server_solar_animation.h"
#include "solar_animation.h"
#include "door_state.h"
#include "server_sysdb.h"
#include "server_gameobject.h"
#include "common_cobject.h"
#include "rpc_iclient.h"
#include "rpc_iclient_args.h"
#include "dacom.h"
#include <algorithm>
#include <map>
#include <set>
#include <cmath>
#include <cstring>

extern IClient* g_pClientInterface;

namespace {
struct Entry {
    CSolar* Object = nullptr;
    SolarAnimationCommand Command;
    float Duration = 0;
    ProximityDoor::State Door;
    bool Initialized = false, Invalid = false, Manual = false, Scripted = false;
    bool Finished() const { return Command.Reverse ? Command.Time <= 0 : Command.Time >= Duration; }
};
struct Manager { std::map<unsigned, Entry> Objects; float ScanTime = .1f; };
std::map<StarSystem*, Manager> Managers;
unsigned Serial = 0;
void Send(StarSystem& sys, unsigned id, Entry const& e, unsigned player = 0, bool snapshot = false)
{
    FPayloadServerActivateObject packet{};
    packet.ObjectId = id; packet.bActivate = 2; packet.Animation = e.Command;
    if (snapshot) packet.Animation.Sound = 0;
    if (player) { g_pClientInterface->SendServerActivateObject(player, packet); return; }
    auto* head = static_cast<SystemPlayerNode*>(sys.PlayerListHead);
    for (auto* n = head->Next; n != head; n = n->Next)
        g_pClientInterface->SendServerActivateObject(n->View.PlayerId, packet);
}
bool Start(StarSystem& sys, unsigned id, Entry& e, char const* name, float time, bool reverse, unsigned sound)
{
    float duration = SolarAnimation::Duration(e.Object, name);
    if (duration <= 0 || strlen(name) >= sizeof(e.Command.Name)) return false;
    SolarAnimationCommand cmd;
    strcpy_s(cmd.Name, name); cmd.Time = time; cmd.Reverse = reverse; cmd.Sound = sound;
    if (++Serial == 0) ++Serial;
    cmd.Serial = Serial;
    if (!SolarAnimation::Play(e.Object, cmd)) return false;
    e.Command = cmd; e.Duration = duration;
    Send(sys, id, e);
    return true;
}
}

void UpdateSolarAnimations(StarSystem& sys, float dt)
{
    if (!std::isfinite(dt) || dt <= 0) return;
    auto& manager = Managers[&sys];
    for (auto& pair : manager.Objects) {
        auto& e = pair.second;
        e.Command.Time = e.Command.Reverse ? (std::max)(0.0f, e.Command.Time - dt)
            : (std::min)(e.Duration, e.Command.Time + dt);
    }
    manager.ScanTime += dt;
    bool scan = manager.ScanTime >= .1f;
    if (!scan) return;
    float scanDt = manager.ScanTime;
    if (scan) manager.ScanTime = 0;
    std::set<unsigned> live;
    for (auto* n = sys.Solars.Head; n; n = n->Next) {
        auto* go = n->Data;
        if (!go || go->is_destroyed()) continue;
        auto* obj = static_cast<CSolar*>(go->cobj());
        if (!obj) continue;
        unsigned id = go->get_id();
        SolarAnimation::Config config;
        bool automatic = SolarAnimation::GetConfig(obj->Archetype, config);
        auto it = manager.Objects.find(id);
        if (!automatic && it == manager.Objects.end()) continue;
        live.insert(id);
        auto& e = manager.Objects[id];
        if (e.Object != obj) { e = Entry{}; e.Object = obj; }
        if (!e.Initialized) {
            e.Initialized = true;
            if (automatic) {
                e.Duration = SolarAnimation::Duration(obj, config.Close);
                e.Invalid = e.Duration <= 0 || SolarAnimation::Duration(obj, config.Open) <= 0;
                if (e.Invalid) FDUMP(0x100001, "proximity door %u requires finite anim_open and anim_close", id);
                strcpy_s(e.Command.Name, config.Close); e.Command.Time = e.Duration;
            }
        }
        if (e.Scripted && !e.Finished()) continue;
        e.Scripted = false;
        if (!scan || !automatic || e.Invalid || e.Manual) continue;
        bool inside = false, retained = false;
        // Ships only, including NPCs. Include hull radius so a large ship's tail
        // keeps the door open. Debris/projectiles/asteroids cannot trigger it.
        Vector const& p = go->get_position();
        for (auto* ship = sys.Ships.Head; ship; ship = ship->Next) {
            auto* other = ship->Data;
            if (!other || other->is_destroyed() || !other->cobj()) continue;
            Vector const& q = other->get_position();
            float dx=p.x-q.x, dy=p.y-q.y, dz=p.z-q.z;
            float hull = (std::max)(0.0f, other->cobj()->get_radius());
            float enterRadius = config.Radius + hull, leaveRadius = config.ReleaseRadius + hull;
            float d2 = dx*dx+dy*dy+dz*dz;
            inside |= d2 <= enterRadius*enterRadius; retained |= d2 <= leaveRadius*leaveRadius;
        }
        auto previous = e.Door;
        auto decision = e.Door.Scan(inside, retained, scanDt, config.CloseDelay, e.Finished());
        bool ok = true;
        using ProximityDoor::Decision;
        if (decision == Decision::Open) ok = Start(sys,id,e,config.Open,0,false,config.OpenSound);
        if (decision == Decision::Close) ok = Start(sys,id,e,config.Close,0,false,config.CloseSound);
        if (decision == Decision::ReverseClose) {
            // Reverse the SAME closing clip at its current time: no pose jump,
            // even when the separately authored opening trajectory is different.
            ok = Start(sys,id,e,config.Close,e.Command.Time,true,config.OpenSound);
        }
        if (!ok) { e.Door = previous; e.Invalid = true; }
    }
    for (auto it = manager.Objects.begin(); it != manager.Objects.end(); )
        if (!live.count(it->first)) it = manager.Objects.erase(it); else ++it;
}
bool StartSolarAnimation(unsigned id, char const* name)
{
    if (!name || !name[0]) return false;
    GameObject* go = nullptr; StarSystem* sys = nullptr;
    if (!Server_FindLiveObject(id, go, sys) || !sys || !go->cobj() ||
        (static_cast<unsigned>(go->cobj()->ObjectClass) & 0x303u) != 0x303u) return false;
    auto& e = Managers[sys].Objects[id];
    auto* obj = static_cast<CSolar*>(go->cobj());
    if (e.Object != obj) { e = Entry{}; e.Object = obj; }
    // No restart and no accumulating queue while a clip is running.
    if (!e.Finished()) return false;
    if (e.Door.Current == ProximityDoor::Phase::Opening) e.Door.Current = ProximityDoor::Phase::Open;
    if (e.Door.Current == ProximityDoor::Phase::Closing) e.Door.Current = ProximityDoor::Phase::Closed;
    SolarAnimation::Config c;
    bool automatic = SolarAnimation::GetConfig(obj->Archetype, c);
    bool open = automatic && _stricmp(c.Open,name) == 0;
    bool close = automatic && _stricmp(c.Close,name) == 0;
    if (automatic && e.Initialized && ((open && e.Door.Current == ProximityDoor::Phase::Open) ||
        (close && e.Door.Current == ProximityDoor::Phase::Closed))) return false;
    if (!Start(*sys,id,e,name,0,false,open ? c.OpenSound : close ? c.CloseSound : 0)) return false;
    e.Initialized = true; e.Invalid = false;
    e.Scripted = true;
    e.Manual = automatic && !open && !close;
    if (open) e.Door.Current = ProximityDoor::Phase::Opening;
    if (close) e.Door.Current = ProximityDoor::Phase::Closing;
    return true;
}
void SendSolarAnimations(StarSystem& sys, unsigned player)
{
    auto it = Managers.find(&sys);
    if (it == Managers.end()) return;
    for (auto const& pair : it->second.Objects) {
        auto* obj = Server_LookupGameObject(pair.first);
        if (obj && !obj->is_destroyed() && obj->cobj() == pair.second.Object && pair.second.Command.Name[0])
            Send(sys,pair.first,pair.second,player,true);
    }
}
void ForgetSolarAnimations(StarSystem& sys) { Managers.erase(&sys); }
