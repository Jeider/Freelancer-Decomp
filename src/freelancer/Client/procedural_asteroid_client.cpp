#include "procedural_asteroid_client.h"
#include "procedural_asteroid_replica.h"
#include "far_rocks.h"
#include "client_gameobj.h"
#include "client_objdb.h"
#include "common_server.h"
#include "common_id.h"
#include "common_csys.h"
#include "login_mgr.h"
#include "player_spawn.h"
#include "globals.h"
#include "x86math.h"
#include <windows.h>
#include <set>
#include <unordered_set>

namespace {
namespace P=ProceduralAsteroids;
P::Replica State;
unsigned System=0,Serial=0,Revision=0;
double Clock=0;
DWORD Sent=0;
bool Rendering=false;
std::map<unsigned,P::Key> Objects;
std::map<unsigned,FClientGameobj*> Bodies;
struct SpatialState {Vector position;float radius=0;bool valid=false;};
std::map<unsigned,SpatialState> Spatial;
std::map<P::Key,P::Rock> Live;
std::unordered_set<P::Key> Changes,FreeSpin;
std::set<P::Key> Visible;
std::set<unsigned> Retired;
std::set<P::Key> NativeVisuals,DrawnVisuals;
bool VisualsCommitted=false;
unsigned Zone(){static unsigned id=CreateID("Zone_om15_ast1_asteroids");return id;}
bool RegularSpin(P::Entry const& e){return std::fabs(e.spin[0])<1e-5f&&std::fabs(e.spin[2])<1e-5f&&std::fabs(e.spin[1]-P::SpinRate)<1e-5f;}
void Track(P::Key key){
    auto const& e=State.entries.at(key);
    if(e.object)Objects[e.object]=key;
    if(!(e.flags&(P::Dead|P::Active))&&!RegularSpin(e))FreeSpin.insert(key);else FreeSpin.erase(key);
    if(!(e.flags&P::Active))Live.erase(key);Changes.insert(key);
}
void Index(){
    auto old=std::move(Objects);Objects.clear();FreeSpin.clear();Live.clear();Changes.clear();
    for(auto const& item:State.entries)Track(item.first);
    for(auto const& item:Objects)if(!Bodies.count(item.first)){
        auto* body=ClientObjDb_FindObject(item.first,0);if(body)Bodies.emplace(item.first,body);
    }
    for(auto const& item:old)if(!Objects.count(item.first)&&Bodies.count(item.first))Retired.insert(item.first);
    ++Revision;
}
}
void ProceduralAsteroidClientEnter(unsigned system) {
    System=system;State=P::Replica{};Sent=0;Rendering=false;Objects.clear();Bodies.clear();Visible.clear();Retired.clear();++Revision;
    Spatial.clear();Changes.clear();FreeSpin.clear();Live.clear();Clock=0;
    NativeVisuals.clear();DrawnVisuals.clear();VisualsCommitted=false;
}
void ProceduralAsteroidClientTick(unsigned system) {
    if(system!=System)ProceduralAsteroidClientEnter(system);
    if(System!=CreateID("om15"))return;
    double dt=GetClientFrameTimeRaw();if(std::isfinite(dt)&&dt>0)Clock+=dt;
    DWORD now=GetTickCount();
    if((!State.ready||State.refresh||State.receiving)&&G_ChatServer&&(!Sent||now-Sent>=2500)){
        P::Packet p;p.header.kind=P::Request;p.header.system=System;p.header.zone=Zone();
        if(!++Serial)++Serial;State.token=Serial;p.header.token=Serial;Sent=now;
        static_cast<IChatServer*>(G_ChatServer)->SubmitChat(CHAT_ID(GetPlayerConnectionId()&0xffffu),P::Bytes(p),&p,CHAT_ID(P::Channel),-1);
    }
    // Follow the replicated body, including collision movement. Static rocks do
    // not dirty the instance buffers; active moving rocks update their own pose.
    static auto* Math=Acquire3DMathEngine();
    for(auto const& item:Objects){
        auto found=Bodies.find(item.first);auto* obj=found==Bodies.end()?nullptr:found->second;
        if(!obj||obj->Slot154()||!Math){if(dt>0)Changes.insert(item.second);continue;}
        auto previous=Live.find(item.second);
        auto rock=previous==Live.end()?P::Generate(item.second,State.recipe.seed,State.recipe.models):previous->second;
        auto const& pos=obj->get_position();std::memcpy(rock.position,&pos.x,sizeof(rock.position));
        Quaternion q;Math->MatrixToQuaternion(reinterpret_cast<FQuaternion&>(q),reinterpret_cast<FMatrix const&>(obj->get_orientation()));
        rock.rotation[0]=q.x;rock.rotation[1]=q.y;rock.rotation[2]=q.z;rock.rotation[3]=q.w;
        if(previous==Live.end()||std::memcmp(previous->second.position,rock.position,12)||std::memcmp(previous->second.rotation,rock.rotation,16))
            {Live[item.second]=rock;Changes.insert(item.second);}
    }
    if(dt>0)for(auto key:FreeSpin)Changes.insert(key);
}
bool ProceduralAsteroidClientReceive(unsigned sender,unsigned size,void const* bytes) {
    if(sender!=P::Channel)return false;
    P::Packet p;
    if(!P::Decode(bytes,size,p)||p.header.system!=System||p.header.zone!=Zone())return true;
    std::vector<unsigned> old;
    if(p.header.kind==P::Delta)for(unsigned i=0;i<p.header.count;++i){
        auto found=State.entries.find(p.entries[i].key);old.push_back(found==State.entries.end()?0:found->second.object);
    }
    if(State.Accept(p)){
        // Keep the field clock tied to simulation (including pause). Ordinary
        // network latency below a frame does not repeatedly jerk the distant spin.
        if(p.header.kind==P::End||std::fabs(Clock-p.header.clock)>.1)Clock=p.header.clock;
        if(p.header.kind==P::End)Index();
        else for(unsigned i=0;i<p.header.count;++i){
            auto const& e=p.entries[i];
            if(old[i]&&old[i]!=e.object){Objects.erase(old[i]);if(Bodies.count(old[i]))Retired.insert(old[i]);}
            Track(e.key);
        }
    }
    return true;
}
bool ProceduralAsteroidClientRecipe(unsigned zone,unsigned& seed,unsigned& models,unsigned& revision) {
    if(!State.ready||zone!=Zone())return false;
    seed=State.recipe.seed;models=State.recipe.models;revision=Revision;return true;
}
bool ProceduralAsteroidClientResolve(unsigned zone,P::Rock& rock) {
    if(!State.ready||zone!=Zone())return false;
    auto found=State.entries.find(rock.key);
    if(found!=State.entries.end()){
        auto const& e=found->second;if(e.flags&P::Dead)return false;
        std::memcpy(rock.position,e.position,sizeof(e.position));std::memcpy(rock.rotation,e.rotation,sizeof(e.rotation));
        if(e.flags&P::Active){
            auto live=Live.find(rock.key);
            if(live!=Live.end())rock=live->second;
            else P::Spin(rock.rotation,e.spin,float(Clock)-e.stamp);
            rock.colour&=~255u;return true;
        }
        if(!RegularSpin(e)){
            P::Spin(rock.rotation,e.spin,float(Clock)-e.stamp);rock.colour&=~255u;return true;
        }
        P::Spin(rock.rotation,-e.stamp); // anchor for GPU spin at shared clock
    }
    rock.colour|=255u;
    return true;
}
void ProceduralAsteroidClientExtras(unsigned zone,std::vector<P::Rock>& rocks) {
    if(!State.ready||zone!=Zone())return;
    for(auto const& item:State.entries)if(!(item.second.flags&P::Dead)){
        auto rock=P::Generate(item.first,State.recipe.seed,State.recipe.models);
        if(ProceduralAsteroidClientResolve(zone,rock))rocks.push_back(rock);
    }
}
void ProceduralAsteroidClientRenderer(unsigned zone,bool available) {
    if(zone==Zone()){Rendering=available;if(!available)Visible.clear();}
}
void ProceduralAsteroidClientVisible(P::Key key){Visible.insert(key);}
void ProceduralAsteroidClientHide(P::Key key){Visible.erase(key);}
float ProceduralAsteroidClientClock(){return float(Clock);}
void ProceduralAsteroidClientChanges(std::vector<P::Key>& keys){keys.assign(Changes.begin(),Changes.end());Changes.clear();}
bool ProceduralAsteroidClientOwns(FClientGameobj* object) {
    // Only a stale body awaiting the engine's destroy packet is suppressed.
    // Active bodies must enter the ordinary solar renderer (rock relief/shadows).
    return object&&Retired.count(object->get_id())!=0;
}
bool ProceduralAsteroidClientPhysical(FClientGameobj* object) {
    return State.ready&&object&&Objects.count(object->get_id())!=0;
}
void ProceduralAsteroidClientBeginVisuals() {
    DrawnVisuals.clear();VisualsCommitted=false;
}
void ProceduralAsteroidClientDrawn(FClientGameobj* object) {
    if(!State.ready||!object)return;
    auto found=Objects.find(object->get_id());
    if(found!=Objects.end())DrawnVisuals.insert(found->second);
}
void ProceduralAsteroidClientCommitVisuals() {
    if(VisualsCommitted)return;
    // A body culled by the native queue keeps its proxy. Suppress a proxy only
    // after its matching body actually reached the native draw this frame.
    for(auto key:NativeVisuals)if(!DrawnVisuals.count(key))Changes.insert(key);
    for(auto key:DrawnVisuals)if(!NativeVisuals.count(key))Changes.insert(key);
    NativeVisuals.swap(DrawnVisuals);VisualsCommitted=true;
}
bool ProceduralAsteroidClientNativeVisual(P::Key key) {
    return NativeVisuals.count(key)!=0;
}
void ProceduralAsteroidClientObserve(FClientGameobj* object) {
    if(object&&object->get_id())Bodies[object->get_id()]=object;
}
bool ProceduralAsteroidClientSpatialUpdate(FClientGameobj* object,Vector const& position,float radius){
    auto& last=Spatial[object->get_id()];
    if(last.valid&&last.radius==radius&&!std::memcmp(&last.position.x,&position.x,12))return false;
    last.position=position;last.radius=radius;last.valid=true;return true;
}
void ProceduralAsteroidClientForget(FClientGameobj* object) {
    // Authoritative death/suspension comes through the protocol. Losing an
    // observer's body alone must never delete the persistent visual rock.
    for(auto it=Bodies.begin();it!=Bodies.end();) {
        if(it->second!=object){++it;continue;}
        Retired.erase(it->first);Spatial.erase(it->first);
        auto key=Objects.find(it->first);if(key!=Objects.end()){
            Live.erase(key->second);Changes.insert(key->second);NativeVisuals.erase(key->second);DrawnVisuals.erase(key->second);
        }
        it=Bodies.erase(it);
    }
}
