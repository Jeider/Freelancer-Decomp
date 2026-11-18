"""Exercise the production evacuation controller with deterministic world I/O.

Includes the real inl, state, reputation calculator and hull interception. Does
not start either game executable. Geometry/real docking still need a user run.
"""
from pathlib import Path
import subprocess
import sys
from check_orders import function
from stage_evacuation import OUT,PACKAGE,EVENTS,EMPLOYERS
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

PRE=r'''
#include "train_evacuation.h"
#include "train_courier_state.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <vector>
#include <string>
#define FDUMP(...) ((void)0)
struct Vector{float x=0,y=0,z=0;};struct Matrix{float E[3][3];};
unsigned CreateID(char const*){return 42;}
enum DestroyType {DESTROY_NORMAL,DESTROY_TYPE1};enum class MissionMessageType{Warning=2};
struct FmtStr{
    void begin_mad_lib(unsigned){}void end_mad_lib(){}void append_string(unsigned){}
    void append_int(unsigned){}void append_rep_group(unsigned){}void append_fmt_str(FmtStr const&){}
};
bool solarAlive=false,spawnOk=true,queueOk=true,prepareOk=true;float solarHealth=1;
unsigned destructions=0,clears=0,queued=0,retired=0,failures=0,notices=0,releaseCount=0;
unsigned currentShip=1,currentSystem=77;
enum {FactionEventTrainDeliveryLate=4,FactionEventTrainCargoLoss,FactionEventTrainLocomotiveLoss,FactionEventCount};
struct FFactionEmpathyRate{unsigned Group;float Rate;};
struct FFactionEmpathy{std::vector<FFactionEmpathyRate> EmpathyRates;float EventRates[FactionEventCount]{};};
using FFactionEmpathyMap=std::map<unsigned,FFactionEmpathy>;FFactionEmpathyMap GFactionEmpathy;
std::map<unsigned,float> reputation;
namespace pub {
namespace Player{
int GetRep(unsigned,int& rep){rep=1;return 0;}
void DisplayMissionMessage(unsigned,FmtStr const&,MissionMessageType,bool){++notices;}
int PopUpDialog(unsigned,FmtStr const&,FmtStr const&,unsigned buttons){assert(buttons==3);return 0;}
}
namespace SpaceObj{
int GetLocation(unsigned,Vector& p,Matrix& m){p={12,13,14};m={1,0,0,0,1,0,0,0,1};return 0;}
int GetRelativeHealth(unsigned id,float& hp){if(id!=33 || !solarAlive)return -1;hp=solarHealth;return 0;}
void SetRelativeHealth(unsigned,float hp){solarHealth=hp;}
void Destroy(unsigned,DestroyType type){solarAlive=false;if(type==DESTROY_TYPE1)++destructions;}
}
namespace Reputation{
void GetReputation(int,unsigned g,float& r){r=reputation[g];}
void SetReputation(int,unsigned g,float r){reputation[g]=r;}
}
}
namespace Universe{
struct System{char const* GetNickname()const{return "rh_biz";}}world;
System* get_system(unsigned){return &world;}bool get_base(unsigned){return true;}
}
namespace PlayerShipTransfer{
enum class Purpose{Normal,Evacuate,Emergency,Reboard};enum class Operation{ClearLocomotive,QueueReturn};
struct Packet{unsigned player=1,system=77,source=1,target=2,anchor=0,base=0;bool returning=false;
 Purpose purpose=Purpose::Normal;Operation operation;float locomotiveHealth=1;Vector position;Matrix orientation;
 struct {unsigned ShipArchetype=0;}ship;int result=0;};
using Bridge=int(__cdecl*)(Packet*);
}
int transfer(PlayerShipTransfer::Packet* p){
 if(p->operation==PlayerShipTransfer::Operation::ClearLocomotive){++clears;p->result=1;}
 else{++queued;p->result=queueOk?1:0;}return 1;
}
void* GetModuleHandleA(char const*){return reinterpret_cast<void*>(1);}
void* GetProcAddress(void*,char const*){return reinterpret_cast<void*>(&transfer);}
struct SystemInfo{std::vector<unsigned> objects;auto* GetMissionObjects(){return &objects;}};
std::map<unsigned,SystemInfo> systems{{77,{}}};auto* GetSystemInfos(){return &systems;}
'''

MISSION=r'''
using namespace TrainCourier;
int bridgeCall(Packet* p){p->result=1;
 if(p->operation==Operation::PrepareEvacuation)p->result=prepareOk;
 if(p->operation==Operation::Restore)p->trailer=20;
 return 1;
}
struct Mission{
    bool ready=true,bPendingDestroy=false,swapped=true,failed=false,cargoPending=false,restoreCargo=false;
    bool jumping=false,restoreObjective=false;unsigned PlayerId=1,boarding=0,trailer=20,transferBase=9,objectiveObject=0;
    State state;CargoSnapshot savedCargo;BridgeFn bridge=bridgeCall;
    struct Point{unsigned faction=5,systemId=77;Vector position;}source;
    struct {unsigned recover=30;}config;
    struct Solar{unsigned ArchetypeId=0,SystemId=0,BaseId=0,Faction=0,SpaceObjId=0;Vector Position;Matrix Orientation;
        float Radius=0;int bSpawned=0;}record;
    std::vector<unsigned> MissionSolars,RespawnSolars;
    struct {void Reset(){}}NnPath;
    struct Ship{bool RebindShip(unsigned,unsigned){return true;}}shipRecord;
    struct Player{Ship* ShipObject;}playerRecord{&shipRecord};Player* PlayerState=&playerRecord;
    std::vector<std::string> speech;
    unsigned ship(){return currentShip;}unsigned system(){return currentSystem;}
    Solar* solar(){return &record;}
    bool SpawnMissionSolarRecord(Solar* s){if(!spawnOk)return false;s->bSpawned=1;s->SpaceObjId=33;solarAlive=true;return true;}
    bool activeOrder(){return (state.stage==Stage::Pickup || state.stage==Stage::Deliver) && !state.retired;}
    bool request(Operation op,unsigned=0){if(op==Operation::Retire)++retired;if(op==Operation::Release)++releaseCount;return true;}
    bool resumeJump(){return false;}
    void observeLoss(CargoSnapshot const&){}
    void say(char const* family){speech.emplace_back(family);}
    void objectObjective(unsigned,Point const&,unsigned id,char const* =nullptr){objectiveObject=id;}
    void OnMissionFail(){++failures;}
#include "TrainCourierEvacuation.inl"
};
Mission fresh(bool cargo=true){
    solarAlive=false;spawnOk=queueOk=prepareOk=true;solarHealth=1;currentShip=1;currentSystem=77;
    destructions=clears=queued=retired=failures=notices=releaseCount=0;reputation.clear();
    Mission m;m.employer=5;m.state.stage=cargo?Stage::Deliver:Stage::Parking;m.state.pickedUp=cargo;
    m.evacSystem=77;return m;
}
void leave(Mission& m,bool emergency=false){
    m.evac.phase=emergency?TrainEvacuation::Phase::Emergency:TrainEvacuation::Phase::Leaving;
    assert(m.tickEvacuation(.1f) && queued==1);
    assert(m.speech.empty()); // No evacuation lecture before the actual transfer.
    PlayerShipTransfer::Packet p;p.returning=true;p.purpose=emergency?PlayerShipTransfer::Purpose::Emergency:PlayerShipTransfer::Purpose::Evacuate;
    assert(m.evacuationTransfer(&p,0)==1);p.locomotiveHealth=.6f;
    currentShip=2;assert(m.evacuationTransfer(&p,1)==1);
}
int main(){
    using namespace TrainEvacuation;
    auto& rep=GFactionEmpathy[5];rep.EmpathyRates={{6,1.f},{7,.25f},{8,-.5f}};
    rep.EventRates[FactionEventTrainDeliveryLate]=-.01f;rep.EventRates[FactionEventTrainCargoLoss]=-.1f;
    rep.EventRates[FactionEventTrainLocomotiveLoss]=-.2f;
    auto near=[](float a,float b){return std::fabs(a-b)<.00001f;};
    // Opening/cancelling never evacuates or starts a timer. Duplicate prompts are rejected.
    {auto m=fresh();Status s;assert(m.evacuationCommand(Command::Confirm,&s)==1);
     assert(m.evacuationCommand(Command::Confirm,&s)==0);m.answerEvacuation(2);
     assert(m.evac.phase==Phase::Onboard && !m.evac.remaining && reputation.empty());
     assert(m.speech.empty());
     assert(m.evacuationCommand(Command::Confirm,&s));m.answerEvacuation(1);assert(m.evac.phase==Phase::Leaving);}
    // Voluntary return preserves hull damage, order, and employer; no penalties.
    {auto m=fresh();leave(m);assert(!m.swapped && m.evac.remaining==60 && solarAlive);
     assert(m.canReboard(33) && !m.canReboard(0) && !m.canReboard(34));
     currentSystem=88;assert(!m.canReboard(33));currentSystem=77;
     m.bPendingDestroy=true;assert(!m.canReboard(33));m.bPendingDestroy=false;
     solarHealth=.05f;assert(!m.canReboard(33));solarHealth=.6f;
     m.tickEvacuation(31);assert(m.evac.remaining==29 && m.evac.warned30);
     PlayerShipTransfer::Packet p;p.anchor=33;assert(m.evacuationTransfer(&p,0));
     assert(p.purpose==PlayerShipTransfer::Purpose::Reboard && near(p.locomotiveHealth,.6f));
     currentShip=3;assert(m.evacuationTransfer(&p,1));assert(m.swapped && m.evac.phase==Phase::Onboard);
     assert(reputation.empty() && m.state.stage==Stage::Pickup && m.objectiveObject==20);}
    // Exact boundary: a prepared return cannot commit at or after sixty seconds.
    {auto m=fresh();leave(m);PlayerShipTransfer::Packet p;p.anchor=33;assert(m.evacuationTransfer(&p,0));
     m.tickEvacuation(60);assert(m.evac.phase==Phase::Closed && failures==1 && !destructions);
     assert(!m.canReboard(33));
     assert(!m.evacuationTransfer(&p,0));assert(near(reputation[5],-.3f)&&near(reputation[6],-.3f));
     assert(near(reputation[7],-.075f)&&near(reputation[8],.15f));
     m.loseLocomotive(true);assert(failures==1 && near(reputation[5],-.3f) && retired==1 && releaseCount==1);}
    // Empty locomotive, emergency escape, repeated damage, and a lethal hit.
    for(bool cargo:{false,true}){auto m=fresh(cargo);leave(m,true);
     assert(m.evac.phase==Phase::Closed && !m.swapped && destructions==1 && failures==1);
     assert(near(reputation[5],cargo?-.3f:-.2f));}
    // Damage to an already abandoned locomotive closes the grace period immediately.
    {auto m=fresh();leave(m);solarHealth=.05f;m.tickEvacuation(.1f);
     assert(m.evac.phase==Phase::Closed && destructions==1 && failures==1);}
    // Failures before safe transfer cannot lose the player, cargo, or reputation.
    {auto m=fresh();m.evac.phase=Phase::Leaving;prepareOk=false;m.tickEvacuation(10);
     assert(!queued && m.swapped && !m.evac.remaining && reputation.empty());
     PlayerShipTransfer::Packet p;p.purpose=PlayerShipTransfer::Purpose::Evacuate;
     m.evacuationTransfer(&p,2);assert(m.evac.phase==Phase::Onboard && !m.evac.remaining);}
    // Emergency destruction is retried if its world representation could not be created.
    {auto m=fresh();spawnOk=false;leave(m,true);assert(m.evacDestroyPending && !failures);
     spawnOk=true;m.tickEvacuation(.1f);assert(failures==1 && destructions==1);}
    // One late event, one cargo event, one equipment event; original empathy and clamps.
    {auto m=fresh();assert(m.applyCourierReputation(Late));assert(!m.applyCourierReputation(Late));
     leave(m);m.tickEvacuation(60);assert(near(reputation[5],-.31f)&&near(reputation[6],-.31f));}
    {auto m=fresh();reputation[5]=reputation[6]=-.85f;m.applyCourierReputation(LocomotiveLost);
     assert(near(reputation[5],-.9f)&&near(reputation[6],-.9f));}
    {auto m=fresh();rep.EventRates[FactionEventTrainLocomotiveLoss]=-.07f;m.applyCourierReputation(LocomotiveLost);
     assert(near(reputation[5],-.07f));rep.EventRates[FactionEventTrainLocomotiveLoss]=0;
     m=fresh();m.applyCourierReputation(LocomotiveLost);assert(reputation.empty());}
    puts("PASS: production evacuation confirm/cancel, return, exact timeout, failure rollback, damage, deferred destruction, reputation once, empathy and configurable zero");
}
'''

def main():
    source=(ROOT/'src/Content/FactionProps.cpp').read_text(encoding='utf-8')
    # Use the actual retail reputation clamp and propagation code.
    methods='\n'.join(function(source,s) for s in ('float ClampFactionReputation(',
        'void __cdecl ApplyFactionReputationChange(','float __cdecl GetFactionEventRate('))
    bridge=(ROOT/'src/include/train_courier_bridge.h').read_text().replace('#pragma once','').replace('#include "common_csys.h"','')
    out=OUT/'checks';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'evacuation.cpp';cpp.write_text(PRE+bridge+methods+MISSION,encoding='utf-8')
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',
        '/I'+str(ROOT/'src/include'),'/I'+str(ROOT/'src/Content'),str(cpp),
        '/Fo'+str(out/'evacuation.obj'),'/Fe'+str(out/'evacuation.exe')],cwd=out,env=env,check=True)
    subprocess.run([str(out/'evacuation.exe')],cwd=out,check=True)
    damage_test(compiler,env,out)
    from export import sections,one
    points=[s for k,s in sections(PACKAGE/'DATA/MISSIONS/TrainCourier/catalog.ini') if k=='courierpoint']
    assert points and all(one(p,'employer')==EMPLOYERS[one(p,'faction')] for p in points)
    factions=[s for k,s in sections(PACKAGE/'DATA/MISSIONS/empathy.ini') if k=='repchangeeffects']
    for faction in factions:
        events={line.split(',')[0].strip():float(line.split(',')[1]) for line in faction['event']}
        assert all(events[k]==v for k,v in EVENTS.items()) and 'train_delivery_success' not in events
    rh=next(f for f in factions if one(f,'group')=='tr_grp_rh')
    assert any(line.split(',')[0].strip()=='rh_grp' and float(line.split(',')[1])==1 for line in rh['empathy_rate'])
    from evacuation_script import rows
    from evacuation_texts import rows as ui
    import xml.etree.ElementTree as ET
    assert len(rows())==128
    for key,number,ru,en in ui():
        for text in (ru,en):
            if text.startswith('<?xml'):ET.fromstring(text)
    print('PASS: staged employer mappings, 3 empathy events, Rheinland propagation, 128 paired script lines and valid RU/EN RDL')

def damage_test(compiler,env,out):
    server=(ROOT/'src/Server/server_train_yard.cpp').read_text(encoding='utf-8')
    objects=(ROOT/'src/Server/server_gameobject.cpp').read_text(encoding='utf-8')
    code=r'''
#include "train_evacuation.h"
#include <cassert>
#include <cstdio>
#include <vector>
#define FREELANCER_RPG_WORLD 1
#define HEALING_ON() false
bool single=true,managed=true;unsigned rescued=0;
bool SinglePlayer(){return single;}
struct CObject{enum{ClassShip=3};unsigned ObjectClass=ClassShip;bool train=true;};
struct CShip:CObject{unsigned OwnerPlayer=1,Id=12;float hp=1000,maximum=1000;
 struct{float HitPts=1000;}arch;
 float get_hit_pts(){return hp;}float get_max_hit_pts(){return maximum;}auto* get_archetype(){return &arch;}
};
namespace CmnTrain{bool IsLocomotive(CObject* o){return o->train;}}
int protect(unsigned player,TrainEvacuation::Command command,TrainEvacuation::Status* p){
 assert(player==1 && command==TrainEvacuation::Command::Critical && p->ship==12);
 if(!managed)return 0;++rescued;return 1;
}
void* GetModuleHandleA(char const*){return reinterpret_cast<void*>(1);}
void* GetProcAddress(void*,char const*){return reinterpret_cast<void*>(&protect);}
enum{SUBOBJ_ID_ROOT=1};
struct DamageEntry{enum class SubObjFate{None,Destroy};unsigned SubObjId;float HitPts;SubObjFate Fate;};
struct DamageList{std::vector<DamageEntry> Entries;bool bDestroyed=false;
 float get_hit_pts_left(unsigned id){for(auto const& e:Entries)if(e.SubObjId==id)return e.HitPts;return -1;}
 void add_damage_entry(unsigned id,float hp,DamageEntry::SubObjFate f){
  for(auto& e:Entries)if(e.SubObjId==id){e.HitPts=hp;return;}Entries.push_back({id,hp,f});}
};
struct GameObject{CShip* Object;CShip* csimple(){return Object;}bool is_damage_blocked(DamageList&){return false;}
 float get_invincible_timer(){return 0;}bool damage_hull(float,DamageList&);};
'''+function(server,'bool TrainCourierProtectHull(')+function(objects,'bool GameObject::damage_hull(')+r'''
int main(){
 CShip ship;GameObject object{&ship};
 for(float amount:{950.f,999.f,1000.f,1000000.f}){
  DamageList damage;rescued=0;
  assert(!object.damage_hull(amount,damage));
  assert(!damage.bDestroyed && damage.get_hit_pts_left(1)==50.f && rescued==1);
  object.damage_hull(1000000.f,damage);assert(!damage.bDestroyed && damage.get_hit_pts_left(1)==50.f);
 }
 {DamageList damage;rescued=0;object.damage_hull(949.f,damage);assert(!rescued && damage.get_hit_pts_left(1)==51.f);}
 for(int mode:{0,1,2,3}){
  single=mode!=0;managed=mode!=1;ship.train=mode!=2;ship.OwnerPlayer=mode==3?0:1;
  DamageList damage;assert(object.damage_hull(1000000.f,damage));assert(damage.bDestroyed);
 }
 puts("PASS: actual damage_hull + protection: 5 percent threshold, lethal single hit, repeated hits, unmanaged/NPC/MP exclusion");
}
'''
    cpp=out/'damage.cpp';cpp.write_text(code,encoding='utf-8')
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',
        '/I'+str(ROOT/'src/include'),str(cpp),'/Fo'+str(out/'damage.obj'),'/Fe'+str(out/'damage.exe')],cwd=out,env=env,check=True)
    subprocess.run([str(out/'damage.exe')],cwd=out,check=True)

if __name__=='__main__':main()
