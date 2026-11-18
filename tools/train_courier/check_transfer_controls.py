"""Exercise real ship binding/control setup and return docking permission offline."""
from pathlib import Path
import subprocess
import sys
from check_transfer_docking import block

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/train_courier/evacuation/checks'
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def controls():
    source = (ROOT/'src/freelancer/Client/player_spawn.cpp').read_text(encoding='utf-8')
    helper = block(source, 'static void InitializePlayerShipControls(CShip* Ship)\n{')
    bind = block(source, 'bool BindPreparedPlayerShip(')
    assert 'InitializePlayerShipControls(Ship);' in block(source, 'FClientShipGameobj* SpawnPlayerShip(')
    return r'''
#include <cassert>
#include <cstdio>
#define FREELANCER_FLSHARP
#define FREELANCER_ADOXA
bool sp=true, disableLevel=true, flightFix=true, hudAutoLevel=false;
#define PORT_PLUGIN_ON(name) (disableLevel)
bool SinglePlayer(){return sp;}
bool FlsharpFeatureEnabled(char const*){return flightFix;}
struct Watchable{}; struct IObjRW:Watchable{};
struct CObject{enum{ClassShip=1};int ObjectClass=ClassShip;};
struct CShip:CObject{unsigned OwnerPlayer=1;};
struct System{struct{int bAutoLevel=1;}Thrust;};
struct IBehaviorManager{
    System* Sys;unsigned char LevelCameraFlag=1;
    void update_level_camera(bool value){LevelCameraFlag=value;}
};
struct FClientShipGameobj:IObjRW{
    CObject* Object;unsigned id;IBehaviorManager* manager;
    unsigned get_id(){return id;}
};
unsigned G_PlayerCharacterId=10,G_PlayerShipCharMirror=10;
FClientShipGameobj* registered=nullptr;
struct{Watchable const* ptr=nullptr;void set(Watchable const* p){ptr=p;}}G_PlayerShipWatcher;
struct{struct{unsigned char bCameraLevelEnabled=0;}ThirdPerson;}G_SpaceApp;
unsigned GetPlayerConnectionId(){return 1;}
FClientShipGameobj* ClientObjDb_FindObject(unsigned id,int){return registered && registered->id==id?registered:nullptr;}
IObjRW* GetPlayerObjRW(){return static_cast<IObjRW*>(const_cast<Watchable*>(G_PlayerShipWatcher.ptr));}
IBehaviorManager* GetBehaviorManager(IObjRW* object){return static_cast<FClientShipGameobj*>(object)->manager;}
void HudStatusSetAutoLevelState(bool value){hudAutoLevel=value;}
CShip* resetShip=nullptr;
void ClientObjDb_FlsharpResetUpdates(CShip* ship){resetShip=ship;}
''' + helper + '\n' + bind + r'''
int main(){
    System system;CShip fighter,loco,restored;
    IBehaviorManager first{&system},second{&system},third{&system};
    FClientShipGameobj objects[3];
    CShip* ships[]={&fighter,&loco,&restored};IBehaviorManager* managers[]={&first,&second,&third};
    // Each replacement has default level=1; the persistent camera has level=0.
    // Board -> evacuate -> reboard must apply policy before mouse input each time.
    for(unsigned i=0;i<3;++i){
        auto& go=objects[i];go.Object=ships[i];go.id=20+i;go.manager=managers[i];registered=&go;
        assert(managers[i]->LevelCameraFlag==1);
        assert(BindPreparedPlayerShip(&go));
        assert(G_PlayerCharacterId==20+i && G_PlayerShipCharMirror==20+i);
        assert(GetPlayerObjRW()==&go && !G_SpaceApp.ThirdPerson.bCameraLevelEnabled);
        assert(!managers[i]->LevelCameraFlag && hudAutoLevel && resetShip==ships[i]);
    }
    auto& go=objects[2];
    // Retail leveling remains available when the port option is off.
    disableLevel=false;third.LevelCameraFlag=1;system.Thrust.bAutoLevel=0;
    assert(BindPreparedPlayerShip(&go));assert(G_SpaceApp.ThirdPerson.bCameraLevelEnabled==1 && !hudAutoLevel);
    third.LevelCameraFlag=0;system.Thrust.bAutoLevel=1;
    assert(BindPreparedPlayerShip(&go));assert(!G_SpaceApp.ThirdPerson.bCameraLevelEnabled && hudAutoLevel);
    // adoxa policy also works with FLSharp's optional fix disabled.
    flightFix=false;disableLevel=true;third.LevelCameraFlag=1;
    assert(BindPreparedPlayerShip(&go));assert(!third.LevelCameraFlag);
    auto saved=G_PlayerShipWatcher.ptr;sp=false;assert(!BindPreparedPlayerShip(&go));
    sp=true;restored.OwnerPlayer=2;assert(!BindPreparedPlayerShip(&go));restored.OwnerPlayer=1;
    registered=nullptr;assert(!BindPreparedPlayerShip(&go));assert(!BindPreparedPlayerShip(nullptr));
    assert(G_PlayerShipWatcher.ptr==saved);
    puts("PASS real client binding: repeated transfers synchronize camera/steering, HUD auto-level, plugin combinations, invalid/MP isolation");
}
'''


def docking():
    source = (ROOT/'src/Content/DockQueues.cpp').read_text(encoding='utf-8')
    method = block(source, 'int __cdecl CheckDockPermission(')
    return r'''
#include <cassert>
#include <cstdio>
#include <vector>
#include <cmath>
#define FREELANCER_RPG_WORLD
#define FREELANCER_ADOXA
#define PORT_PLUGIN_ON(name) false
enum{DOCK_HOST_RESPONSE_0,DOCK_HOST_RESPONSE_1,DOCK_HOST_RESPONSE_2,DOCK_HOST_RESPONSE_3,DOCK_HOST_RESPONSE_4,DOCK_HOST_RESPONSE_5};
bool sp=true, returnAllowed=true, parked=true, mayDock=true, locked=false, playerPresent=true;
float attitude=1,speed=0;int terminalResponse=4;unsigned messages=0;
float GDockHostileAttitude=-.6f;
struct Vector{float x=0,y=0,z=0;};
struct FContentPlayerState{
    unsigned PlayerId=1;bool CanDockAt(unsigned){return mayDock;}int GetLiveMission(){return 1;}
}player;
FContentPlayerState* FindContentPlayerStateByShip(unsigned const*){return playerPresent?&player:nullptr;}
bool TrainCourierCanReboard(unsigned p,unsigned target){return returnAllowed && p==1 && target==33;}
void TrainCourierAccessDenied(unsigned){++messages;}
bool IsGateLockedForShip(unsigned,unsigned){return locked;}
bool DockKeyUnlocks(unsigned,FContentPlayerState*){return false;}
namespace TrainCourier{
enum class Operation{IsParkedSolar};char const* BridgeExport="bridge";
struct Packet{unsigned player=0,launchSolar=0;Operation operation;int result=0;};
using BridgeFn=int(*)(Packet*);
}
int bridge(TrainCourier::Packet* p){p->result=parked;return 1;}
using HMODULE=void*;
HMODULE GetModuleHandleA(char const*){return reinterpret_cast<void*>(1);}
void* GetProcAddress(void*,char const*){return reinterpret_cast<void*>(&bridge);}
namespace pub{
bool SinglePlayer(){return sp;}
unsigned GetNicknameId(char const*){return 1;}
namespace Player{void SendNNMessage(unsigned,unsigned){++messages;}}
namespace SpaceObj{
struct TerminalInfo{unsigned Value=6;};
void GetType(unsigned,unsigned& type){type=0;}
void GetRep(unsigned,int& rep){rep=5;}
void GetTerminalInfo(unsigned,int,TerminalInfo&){}
int GetMotion(unsigned,Vector& linear,Vector& angular){linear.x=speed;angular={};return 0;}
}
namespace Reputation{void GetAttitude(int,int,float& out){out=attitude;}}
}
void DropPlayersLockedOutOfGate(unsigned const*,unsigned const*){}
int ChooseDockTerminal(std::vector<unsigned>const*,unsigned const*,Vector const*,int* index){*index=0;return terminalResponse;}
''' + method + r'''
int main(){
    unsigned ship=2,target=33;int rep=1,index=-1;std::vector<unsigned> classes{1};Vector position;
    auto check=[&](){return CheckDockPermission(&classes,&rep,&ship,&position,&target,&index);};
    // Mission ownership wins over station hostility/locks only for this locomotive.
    locked=true;mayDock=false;attitude=-.9f;
    assert(check()==4 && index==0 && !messages);
    terminalResponse=2;assert(check()==2);terminalResponse=3;assert(check()==3);terminalResponse=4;
    speed=1;assert(check()==3);speed=0;assert(check()==4);
    // Grace expired / destroyed / other owner: closed parked train remains denied.
    returnAllowed=false;assert(check()==1);
    returnAllowed=true;target=99;assert(check()==1);target=33;
    // Ordinary station access and MP/NPC requests keep their original restrictions.
    parked=false;returnAllowed=false;assert(check()==1);
    locked=false;mayDock=true;assert(check()==0);attitude=0;assert(check()==4);
    sp=false;returnAllowed=true;attitude=-.9f;assert(check()==0);
    sp=true;playerPresent=false;assert(check()==0);
    puts("PASS real dock permission: owner return, hostile employer/locks, berth/queue/motion checks, expiry/other target, ordinary station and MP isolation");
}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    compiler, env = compiler_env()
    for name, code in [('controls', controls()), ('return_docking', docking())]:
        (OUT/(name+'.cpp')).write_text(code, encoding='utf-8')
        subprocess.run([str(compiler/'cl.exe'), '/nologo', '/EHsc', '/std:c++17',
                        name+'.cpp', '/Fe:'+name+'.exe'], cwd=OUT, env=env, check=True)
        subprocess.run([str(OUT/(name+'.exe'))], cwd=OUT, check=True, timeout=10)


if __name__ == '__main__':
    main()
