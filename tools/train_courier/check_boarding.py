"""Exercise the production empty-objective notification and docking boundary."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def function(path,name):
    source=path.read_text(encoding='utf-8')
    start=source.index(name);brace=source.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

PREFIX=r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <list>
#include <vector>
#include <cstdint>
#include <map>
struct FCharacterEncounter {unsigned MissionTextId=0;};
struct FStoryMissionListNode_0x2f4 {
    char Path[128]{};unsigned PathLength=0;int Field_0x8c=-1;
    FCharacterEncounter* Field_0x90=nullptr;int Field_0x94=0,Field_0x95=0;
};
struct FContentBase {unsigned BaseId=42;void RemoveBarScene(int,void*){}};
struct PlayerStateType {
    void* ShipObject=nullptr;unsigned LocationId=0;FContentBase base;
    FContentBase* GetBaseRecord(){return &base;}
} playerState;
PlayerStateType* FindContentPlayerState(unsigned){return &playerState;}
struct FMissionObjective {struct {unsigned Type=2;} Objective;};
struct FMissionPlayer {
    struct {FMissionObjective* first=nullptr;FMissionObjective* GetFront(){return first;}} Objectives;
    bool flagged=false;unsigned sends=0;
    void SetField25(bool flag){flagged=flag;}
    void SendObjectives(){assert(flagged && Objectives.first->Objective.Type==0x32);++sends;}
};
struct FMissionScript {
    unsigned PlayerId=1,ControllerId=2;PlayerStateType* PlayerState=&playerState;
    std::list<FStoryMissionListNode_0x2f4> List_0x2f4;
    FMissionPlayer player;bool hasPlayer=true;
    FMissionPlayer* FindPlayer(unsigned){return hasPlayer?&player:nullptr;}
    void StartRtcScript(FStoryMissionListNode_0x2f4*){assert(false);}
    void OnMessage100b(void const*);
};
unsigned dockedBase=42;
struct Vector {float x=1,y=2,z=3;};
struct Matrix {float data[9]{};};
struct Quaternion {float data[4]{};};
using FMatrix=Matrix;using FVector=Vector;using FQuaternion=Quaternion;
using EquipDescVector=std::vector<int>;
unsigned liveAnchor=0,liveArch=0,spawnCount=0,cacheCount=0,restoreCount=0;
bool swapWorks=true,spawnWorks=true,bridgeWorks=true,physicsReady=false;
unsigned CreateID(char const* name){return !std::strcmp(name,"spawn_point")?99:(!std::strcmp(name,"tc_parked_locomotive")?98:17);}
#define FDUMP(...) ((void)0)
namespace pub {
void GetLoadout(EquipDescVector&,unsigned){}
namespace Player {
void GetBase(unsigned,unsigned& base){base=dockedBase;}
int GetSystem(unsigned,unsigned& system){system=7;return 0;}
int CacheShipAndSetLoadout(unsigned,char const*,unsigned,EquipDescVector&){++cacheCount;return swapWorks?0:-1;}
int RestoreCachedShip(unsigned,char const*){++restoreCount;return 0;}
}
namespace SpaceObj {int GetSystem(unsigned id,unsigned& system){system=7;return id==liveAnchor && id?0:-1;}}
}
enum class Stage {Boarding,TransferIn,TransferOut,Pickup};
enum class Operation {Transfer,LaunchSolar};
struct Packet {unsigned player=0,base=0,system=0,launchSolar=0;Operation operation;Vector position;Matrix orientation;int result=0;};
struct Courier {
    struct Retired {unsigned system;Vector position;};
    bool transfer=false;unsigned base=0,system=0,solar=0;Vector position;Matrix orientation;
    std::map<unsigned,Retired> parked;
};
using ServerCourier=Courier;
std::map<unsigned,ServerCourier> couriers;
struct Dock {
    Vector WorldPosition;
    bool launch_pos(Vector& position,Matrix&,int index){assert(index==0);position={11,35,3};return true;}
} liveDock;
Dock* parkedSolar(unsigned id){return id && id==liveAnchor && liveArch==98?&liveDock:nullptr;}
bool validPose(Vector const&,Matrix const&){return true;}
int PrepareServerTransfer(Packet* p);
bool bridgeMock(Packet* p){if(bridgeWorks)PrepareServerTransfer(p);return true;}
void Server_MatrixToQuat(Quaternion&,Matrix const&){}
struct Solar {unsigned BaseId=0,SystemId=0,ArchetypeId=0,SpaceObjId=0;Vector Position;Matrix Orientation;float Radius=1;int bSpawned=1;};
bool SpawnMissionSolarRecord(Solar* s){assert(physicsReady);++spawnCount;if(!spawnWorks)return false;assert((s->ArchetypeId==99 || s->ArchetypeId==98) && s->Radius==0 && s->bSpawned==0);liveArch=s->ArchetypeId;s->SpaceObjId=liveAnchor=100+spawnCount;return true;}
struct CourierMission {
    bool ready=true,bPendingDestroy=false,swapped=false,transferInSpace=false;
    unsigned transferBase=42,PlayerId=1,boarding=50;
    PlayerStateType* PlayerState=&playerState;
    struct {Stage stage=Stage::Boarding;} state;
    Solar anchor;Solar* solar(){return &anchor;}
    unsigned system(){return 7;}
    Vector transferPosition;Matrix transferOrientation;
    std::vector<unsigned> RespawnSolars{50};
    bool (*bridge)(Packet*)=bridgeMock;
    bool prepareTransfer();bool onDocked();bool prepareBaseTransfer(unsigned,bool);void onPlayerLaunch(unsigned);
};
CourierMission* active=nullptr;
using DWORD=uint32_t;using LONG=int32_t;
DWORD clockMs=1000,G_CourierTransferRetry=0;
unsigned G_CourierTransferBase=0,baseEntries=0,frameDraws=0;
DWORD GetTickCount(){return clockMs;}
bool CourierBaseTransfer(unsigned base,bool prepare){return active && active->prepareBaseTransfer(base,prepare);}
void SetClientLocationBase(unsigned base){assert(base==42);++baseEntries;dockedBase=base;playerState.base.BaseId=base;}
void RoomControlSetLandingPending(int value){assert(value==0);}
void SetFadeImmediate(float value){assert(value==1);}
void SetFadeTarget(float value,float rate){assert(value==1 && rate==0);}
bool G_bLocationInTransition=true,G_bLocationPendingAudio=true,G_bNnScreenUp=false,paused=false;
unsigned G_LocationCurrentBase=42,G_LocationCurrentRoom=0,G_LocationPendingRoom=0,baseExits=0;
void* G_LocationCurrentBaseEntry=nullptr;void* G_LocationCurrentRoomEntry=nullptr;
float G_LocationPendingElapsed=1,G_LocationPendingDelay=1;
bool IsClientLocationInTransition(){return G_bLocationInTransition;}
bool IsClientServerTickPaused(){return paused;}
int GetClientMouseCursorDrawFlag(){return 1;}
unsigned GetPlayerBaseIdRetail(){return dockedBase;}
void* GetPlayerObjRW(){return &playerState;}
void LeaveClientLocationBase(){assert(G_LocationCurrentBase==42);++baseExits;dockedBase=0;G_LocationCurrentBase=0;}
void SetPlayerBaseIdRetail(unsigned id){dockedBase=id;}
void SetPlayerFactionScratchRetail(unsigned){}
namespace RtcSlider {int get_default_fps_cap(){return 60;}}
void SetClientFpsCap(int){}
struct {void Shutdown(){}} G_GfScriptManager;
void ReleaseSharedCharacterLod(){} void ResetCharacterScripts(){} void StopAllClientSounds(){}
void UnloadClientSoundArchesByCategory(int){} void ReleaseFlashlightTextures(){} void ResetEngineInstanceCache(){}
struct FServerLaunchInfo {unsigned Field_0x00=10,Field_0x04=0,Field_0x08=0;Quaternion Orientation;Vector Position;};
unsigned dockLookups=0,beams=0,dockLaunches=0;bool acknowledged=false;
bool SinglePlayer(){return true;}
struct Math {
    void QuaternionToMatrix(Matrix&,Quaternion const&){}
    void TransformMatrix(Vector& out,Matrix const&,Vector const& in){out=in;}
} mathEngine;
Math* GIServerSMathEngine=&mathEngine;
Math* Server_Acquire3DMathEngine(){return &mathEngine;}
Math* IClientSMath(){return &mathEngine;}
void Server_GetLaunchPosition(unsigned,unsigned* object,int* kind,Vector* pos,Quaternion*) {
    ++dockLookups;*object=123;*kind=1;*pos={10,0,0};
}
struct FClientShipGameobj {
    void LaunchFromDock(void* dock,int index){assert(dock && index==0);++dockLaunches;}
    void beam_object(Vector const& pos,Matrix const&,bool){assert(pos.x==1 && pos.y==2 && pos.z==3);++beams;}
} clientShip,clientDock;
FClientShipGameobj* ClientObjDb_FindObject(unsigned id,int){return id==10?&clientShip:(id && id==liveAnchor?&clientDock:nullptr);}
FClientShipGameobj* NarrowGameobj(FClientShipGameobj* p,int){return p;}
void SetPlayerLaunchAcknowledged(bool value){acknowledged=value;}
struct IClientImpl {void SendServerLaunch(unsigned,FServerLaunchInfo const&);};
'''
MAIN=r'''
int main(){
    FMissionScript mission;unsigned cleared=0;
    // Exact empty-objective condition in the user's Content.dll+47b9d crash.
    mission.OnMessage100b(&cleared);
    assert(mission.player.sends==0);
    FMissionObjective objective;mission.player.Objectives.first=&objective;
    mission.OnMessage100b(&cleared);
    assert(mission.player.sends==1 && objective.Objective.Type==2 && !mission.player.flagged);
    mission.hasPlayer=false;mission.OnMessage100b(&cleared);
    CourierMission courier;active=&courier;
    assert(!EnterCourierTransferBase(123) && !baseEntries && !cacheCount);
    dockedBase=0;assert(!courier.prepareBaseTransfer(42,true) && !cacheCount);
    // The room remains unopened, including after skipping the docking cinematic.
    playerState.LocationId=0;
    assert(EnterCourierTransferBase(42) && baseEntries==1 && cacheCount==0);
    // SpaceExit cleared the solar AND shut down physics. No spawn is legal on
    // the hidden base; bridge retries must not overwrite the personal ship.
    bridgeWorks=false;
    assert(UpdateGameflowBaseFrame()==0 && cacheCount==1 && courier.swapped);
    unsigned attempts=spawnCount;
    assert(UpdateGameflowBaseFrame()==0 && spawnCount==attempts);
    bridgeWorks=true;clockMs+=250;
    assert(UpdateGameflowBaseFrame()==2 && spawnCount==attempts && cacheCount==1);
    assert(playerState.LocationId==0 && frameDraws==0);
    assert(!spawnCount && !courier.transferInSpace);
    // BaseEnter's transition latch normally clears on room entry. We skip the
    // room: reproduce the stuck HUD before leaving, then run the real teardown.
    assert(HudIsMousePickBlocked());
    LeaveGameflowBase();
    assert(baseExits==1 && !G_CourierTransferBase && !G_bLocationInTransition);
    assert(!HudIsMousePickBlocked());
    paused=true;assert(HudIsMousePickBlocked());paused=false;
    G_bNnScreenUp=true;assert(HudIsMousePickBlocked());G_bNnScreenUp=false;
    // This is switcher.ini's PlayerLaunch boundary, after StarSysEnter.
    dockedBase=0;physicsReady=true;
    courier.onPlayerLaunch(123);assert(!spawnCount);
    courier.onPlayerLaunch(42);assert(spawnCount==1 && liveAnchor && courier.RespawnSolars.empty());
    FServerLaunchInfo launch=MakeLaunchPacket();
    assert(!launch.Field_0x04 && !dockLookups && !couriers[1].transfer);
    assert(launch.Position.x==1 && launch.Position.y==2 && launch.Position.z==3);
    // Execute the real client handler with NO dock object in the client DB.
    IClientImpl client;client.SendServerLaunch(1,launch);
    assert(beams==1 && acknowledged);
    launch=MakeLaunchPacket(); // a second/unrelated launch uses the normal path
    assert(dockLookups==1 && launch.Field_0x04==123 && launch.Position.x==5);
    // Parking restores the original ship once, even if the bridge needs a retry.
    dockedBase=42;physicsReady=false;courier.state.stage=Stage::TransferOut;bridgeWorks=false;
    assert(!courier.prepareBaseTransfer(42,true) && restoreCount==1 && !courier.swapped);
    bridgeWorks=true;
    assert(courier.prepareBaseTransfer(42,true) && restoreCount==1);
    physicsReady=true;dockedBase=0;liveAnchor=0;spawnWorks=false;
    courier.onPlayerLaunch(42);assert(!courier.boarding);
    // Even a failed visual anchor cannot send a null CEqObj to CShip::launch.
    launch=MakeLaunchPacket();assert(!launch.Field_0x04 && dockLookups==1);
    client.SendServerLaunch(1,launch);assert(beams==2);
    // Retry the final transfer: native dock launch, HpMount compensation and
    // an anchor retained by the server after the mission controller is gone.
    dockedBase=42;physicsReady=false;spawnWorks=true;
    assert(courier.prepareBaseTransfer(42,true) && restoreCount==1);
    physicsReady=true;dockedBase=0;
    courier.onPlayerLaunch(42);assert(liveAnchor && liveArch==98);
    launch=MakeLaunchPacket();
    assert(launch.Field_0x04==liveAnchor && launch.Field_0x08==0 && dockLookups==1);
    assert(launch.Position.x==6 && launch.Position.y==35 && launch.Position.z==3);
    client.SendServerLaunch(1,launch);assert(dockLaunches==1 && beams==2);
    assert(couriers[1].parked.count(liveAnchor)==1);
    // Returning to the personal ship runs the same roomless base teardown.
    G_CourierTransferBase=42;G_LocationCurrentBase=42;G_bLocationInTransition=true;
    LeaveGameflowBase();assert(baseExits==2 && !HudIsMousePickBlocked());
    courier.state.stage=Stage::Pickup;
    assert(!courier.prepareBaseTransfer(42,false));
    G_CourierTransferBase=0;
    assert(UpdateGameflowBaseFrame()==9 && frameDraws==1);
    puts("PASS: roomless transfer releases HUD input after BaseExit; pause/modal gates preserved; no solar while physics is down; PlayerLaunch respawn; exact free-space launch; cache preserved; normal launch unchanged");
}
'''

compiler,env=compiler_env();out=ROOT/'src/obj/train_courier/boarding';out.mkdir(parents=True,exist_ok=True)
notification=function(ROOT/'src/Content/MissionScript.cpp','void FMissionScript::OnMessage100b(')
content=ROOT/'src/Content/TrainCourier.cpp';client=ROOT/'src/freelancer/Client/gameflow.cpp'
transfer='\n'.join(function(content,'bool '+name+'(').replace('bool '+name+'(', 'bool CourierMission::'+name+'(',1)
                   for name in ['prepareTransfer','onDocked','prepareBaseTransfer'])
transfer+='\n'+function(content,'void onPlayerLaunch(').replace('void onPlayerLaunch(', 'void CourierMission::onPlayerLaunch(',1)
server=ROOT/'src/Server/server_train_yard.cpp'
bridge=server.read_text(encoding='utf-8')
bridge=bridge[bridge.index('        if(!validPose(p->position,p->orientation))'):bridge.index('    } else if(p->operation==Op::ClearTransfer)')]
bridge='int PrepareServerTransfer(Packet* p) {using Op=Operation;unsigned currentSystem=7;auto& state=couriers[p->player];if(p->operation==Op::Transfer){\n'+bridge+'}\nreturn 1;\n}'
launch=function(server,'bool TrainCourierLaunchPose(')
launch_source=function(ROOT/'src/Server/IServerImpl.cpp','void IServerImpl::PlayerLaunch(')
launch_source=launch_source[launch_source.index('        unsigned int LaunchObjId = 0;'):launch_source.index('        // .text:06cefd1e')]
launch+='\nFServerLaunchInfo MakeLaunchPacket(){unsigned session_id=1;FServerLaunchInfo Req;Vector HpPos{5,0,0};\n'+launch_source+'Req.Field_0x04=LaunchObjId;Req.Field_0x08=LaunchKind;return Req;\n}'
launch+='\n'+function(ROOT/'src/freelancer/Client/client_iclient_space.cpp','void IClientImpl::SendServerLaunch(')
flow=function(ROOT/'src/freelancer/Client/menu_universe_base.cpp','void ResetClientLocationController(')
flow+='\n'+function(ROOT/'src/freelancer/Client/hud_target.cpp','bool HudIsMousePickBlocked(')
flow+='\n'+'\n'.join(function(client,name) for name in ['bool EnterCourierTransferBase(', 'int UpdateCourierTransferBase(', 'void LeaveGameflowBase('])
frame=function(client,'int UpdateGameflowBaseFrame(')
frame=frame[:frame.index('        // 0x00558c19')]+ '++frameDraws;return 9;\n}'
source=out/'boundary.cpp';source.write_text('#define FREELANCER_RPG_WORLD\n'+PREFIX+notification+'\n'+bridge+'\n'+transfer+'\n'+launch+'\n'+flow+'\n'+frame+MAIN,encoding='utf-8')
exe=out/'boundary.exe'
subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',str(source),
                '/Fo'+str(out/'boundary.obj'),'/Fe'+str(exe)],env=env,cwd=out,check=True)
subprocess.run([str(exe)],cwd=out,check=True)
