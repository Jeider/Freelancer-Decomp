#include "MissionCnd.h"
#include "common_cequip.h"
#include "common_cobject.h"
#include "dacom.h"
#include <cassert>
#include <cstring>
#include <functional>
#include <mutex>
#include <vector>

using pub::Controller::EMessage;
using pub::Controller::CloakActivation;
struct FMissionScript {
    unsigned player=101,npc=102;
    unsigned GetLabelShipId(TString<0x30> const* label) {
        if(!_stricmp(label->Data,"Player"))return player;
        if(!_stricmp(label->Data,"escort"))return npc;
        return 0;
    }
};
template<unsigned N> void InitEmpty(TString<N>& value){value.Length=0;value.Data[0]=0;}
struct EqObj {
    CShip* ship;
    void* OwnerSystem=this;
    bool destroyed=false;
    bool is_destroyed(){return destroyed;}
    CShip* ceqobj(){return ship;}
    unsigned get_id(){return ship->Id;}
};
std::vector<CloakActivation> delivered;
std::function<void(const CloakActivation&)> onDeliver;
int __cdecl pub::Controller::_SendMessage(const unsigned& id,EMessage msg,const void* data){
    assert(id==0&&msg==EMessage::CloakActivated);
    auto event=*static_cast<const CloakActivation*>(data);
    delivered.push_back(event);
    if(onDeliver)onDeliver(event);
    return 0;
}
// PRODUCTION_QUEUE
struct ServerEquip : INotify {
    CEquip* Equip;
    EqObj* Owner;
    ServerEquip(CEquip* equip,EqObj* owner):Equip(equip),Owner(owner){Equip->ConnectServerEquip(this);}
    ~ServerEquip(){if(Equip)Equip->NotifyDisconnecting(this);}
    void notify(Event code,void*) override {
        if(code==EquipDestroying){Equip->NotifyDisconnecting(this);Equip=nullptr;}
    }
};
struct SrvCloak:ServerEquip {
    using ServerEquip::ServerEquip;
    void notify(Event code,void* param) override;
};
// PRODUCTION_OBSERVER
// PRODUCTION_CONDITIONS

void ParseCondition(Cnd& c,const char* text){
    std::string ini="[Trigger]\ncondition=";ini+=text;ini+='\n';
    INI_Reader reader;assert(reader.open_memory(ini.data(),unsigned(ini.size())));
    assert(reader.read_header()&&reader.read_value());c.Parse(reader);c.OnActivate();
}
void ParseArch(Archetype::CloakingDevice& a,const char* text){
    INI_Reader r;assert(r.open_memory(text,unsigned(strlen(text)))&&r.read_header());
    while(r.read_value())assert(a.read(r));
}
void __cdecl QuietDump(int,const char*,...){}
bool State(Cnd& c){return c.Matches(EMessage::Heartbeat,nullptr);}
bool Event(Cnd& c,const CloakActivation& e){return c.Matches(EMessage::CloakActivated,&e);}
int main(){
    FDUMP=QuietDump;assert(LoadLibraryA("x86math.dll"));
    FMissionScript mission;
    auto* ship=static_cast<CShip*>(CObject::Alloc(CObject::ClassShip));
    ship->Id=101;ship->PhysicsSystemId=5;ship->OwnerPlayer=1;
    EqObj owner{ship};
    Archetype::CloakingDevice arch;
    ParseArch(arch,"[CloakingDevice]\nhit_pts=100\nhp_type=hp_hardware_special_1\ndefault_state=false\ncloak_duration=3\ncooldown_time=4\ntoggle_cooldown=0.3\ncloakin_time=2\ncloakout_time=1\n");
    CndCloakState yes(&mission),no(&mission),missing(&mission);
    ParseCondition(yes,"Player, true");ParseCondition(no,"Player, false");
    ParseCondition(missing,"missing, false");
    assert(!State(yes)&&State(no)&&!State(missing)); // no device, and missing object
    auto* device=new CECloakingDevice(nullptr,1,&arch,false);
    ship->EquipManager.AddNewEquipment(device);
    SrvCloak observer(device,&owner);
    CndActCloak on(&mission),off(&mission),npc(&mission);
    ParseCondition(on,"pLaYeR, TRUE");ParseCondition(off,"Player, false");ParseCondition(npc,"escort, true");
    assert(!on.Matches(static_cast<EMessage>(-1),nullptr)&&!off.Matches(EMessage::Heartbeat,nullptr));
    assert(no.Matches(static_cast<EMessage>(-1),nullptr));
    device->Activate(true);
    assert(State(yes)&&!State(no)&&device->cloak_percent()==0); // active before fade
    assert(delivered.empty()); // no actions inside Activate
    ServerFlushCloakEvents();assert(delivered.size()==1);
    assert(Event(on,delivered[0])&&!Event(off,delivered[0])&&!Event(npc,delivered[0]));
    assert(ship->RefCount==1);
    device->Activate(true); // duplicate SP/network activation
    device->Activate(false); // rejected during fade
    ServerFlushCloakEvents();assert(delivered.size()==1);
    device->Update(1,0);device->Activate(false);
    assert(State(no)&&!State(yes)&&device->cloak_percent()==1); // inactive before appearing
    ServerFlushCloakEvents();assert(delivered.size()==2&&Event(off,delivered.back()));
    device->Update(2,0);device->Activate(true);ServerFlushCloakEvents();assert(delivered.size()==2);
    device->Update(4,0);device->Activate(true);
    CndActCloak late(&mission);ParseCondition(late,"Player, true");
    ServerFlushCloakEvents();assert(Event(on,delivered.back())&&!Event(late,delivered.back()));
    on.OnActivate();assert(!Event(on,delivered.back())); // rearm must not replay
    device->Update(4,0);ServerFlushCloakEvents();assert(Event(off,delivered.back())); // expiry
    assert(State(no));
    for(const char* text:{"Player","Player, maybe","Player, false, extra"," , false"}){
        CndCloakState invalid(&mission);ParseCondition(invalid,text);assert(!State(invalid));
    }
    ParseCondition(no,"Player, 0");assert(State(no));
    mission.player=0;assert(!State(no));mission.player=101;
    for(int i=0;i<10000;++i)assert(State(no));assert(ship->RefCount==1);
    // Rapid on/off events are retained; controller actions enqueue for the next flush.
    auto count=delivered.size();QueueCloakEvent(&owner,true);QueueCloakEvent(&owner,false);
    onDeliver=[&](const CloakActivation& e){if(e.Active)QueueCloakEvent(&owner,false);};
    ServerFlushCloakEvents();assert(delivered.size()==count+2);
    onDeliver={};ServerFlushCloakEvents();assert(delivered.size()==count+3);
    QueueCloakEvent(&owner,true);ship->PhysicsSystemId=6;ServerFlushCloakEvents();assert(delivered.size()==count+3);
    QueueCloakEvent(&owner,true);ship->OwnerPlayer=2;ServerFlushCloakEvents();assert(delivered.size()==count+3);
    QueueCloakEvent(&owner,true);owner.destroyed=true;QueueCloakEvent(&owner,true);
    ship->Release(); // queued payload has no dangling object/equipment pointers
    assert(!observer.Equip);ServerFlushCloakEvents();assert(delivered.size()==count+3);
    // Legacy/NPC cloaks still notify without gameplay extensions.
    Archetype::CloakingDevice legacy;
    ship=static_cast<CShip*>(CObject::Alloc(CObject::ClassShip));ship->Id=102;
    owner.ship=ship;owner.destroyed=false;
    CECloakingDevice old(nullptr,2,&legacy,false);SrvCloak oldObserver(&old,&owner);
    old.Activate(false);old.Activate(true);ServerFlushCloakEvents();assert(Event(npc,delivered.back()));
    ship->Release();
    puts("PASS native cloak on/off conditions, fades, cooldown rejection, expiry, duplicate commands, NPCs, rearm, stale events, deferred actions, lifetimes and reference balance");
}
