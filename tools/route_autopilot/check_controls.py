"""Run production input handlers against a recording behavior manager, without a game."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/route_autopilot/controls'
OUT.mkdir(parents=True, exist_ok=True)
CLIENT = ROOT / 'src/freelancer/Client'


def extract(source, signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


route = (CLIENT / 'player_route.cpp').read_text()
behavior = (CLIENT / 'player_behavior.cpp').read_text()
actions = (CLIENT / 'player_flight_actions.cpp').read_text()
hud = (CLIENT / 'hud_maneuvers.cpp').read_text()
spawn = (CLIENT / 'player_spawn.cpp').read_text()
face = (ROOT / 'src/Common/common_faceidea.cpp').read_text()
assert 'is_player() ? 0.1f : 1.0f' in face
assert 'NodeVelocity.x * leadSeconds' in face and 'NodeVelocity.z * leadSeconds' in face
assert 'Cancel(true)' not in extract(route, 'void RouteChanged()')
assert 'PlayerRoute::RouteChanged' not in extract(spawn, 'void RemovePlayerWaypointRetail(')
assert 'PlayerRoute::RouteChanged' not in extract(spawn, 'bool AddPlayerWaypointRetail(')
common = (ROOT / 'src/Common/common_behaviormanager.cpp').read_text()
replay = extract(common, 'if (ObjRwFromWatchable(WatchablePtr)->is_player())')

stub = r'''
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <deque>
#include <vector>
#include <limits>
using namespace FlightActionMath;
using RouteGeometry::passed;
using Vector=V;
struct POINT { int x=0,y=0; };
POINT cursor;
void GetCursorPos(POINT* p){*p=cursor;}
bool G_MouseFlightLocked=false,headLook=false,rearView=false,turretView=false;
bool HudStatusIsRearView(){return rearView;}
bool HudStatusIsTurretView(){return turretView;}
unsigned mouseButtons=0;
bool hover=false;
bool IsMouseFlightLocked(){return G_MouseFlightLocked&&!headLook;}
unsigned GetClientMouseButtons(){return mouseButtons;}
void* Win3DGetHover(){return hover?&hover:nullptr;}
bool IsLetterboxVisible(){return false;}
void NnVoiceEnqueueByName(char const*){}
void PlayOrRewindUiSoundSlot(int){}
namespace CockpitFreeLook { bool BlocksMouseFlight(){return headLook;} }
namespace FlightTelemetry { void Command(char const*,float,float=0,float=0){} }
namespace NavigationSettings { enum Setting {Generator,Autopilot,AutoDock}; int values[3]={1,1,1};int Get(Setting s){return values[s];} }
namespace pub::AI {
struct DirectiveGotoOp { int Field_0C=0,Field_1C=0,Field_58=0; V Destination; float Field_50=0; };
struct DirectiveDockOp { unsigned DockObjectId=0;int Field_10=0; };
}
constexpr int EvalSkip=2,SUBOBJ_ID_NONE=-1;
struct GotoBehavior {
    unsigned char Flag364=0,Flag365=1,Flag2ea=0;
    V destination;
    int targetMode=1,targetId=0;float stopRange=0;
    unsigned destinationUpdates=0;
    bool Slot10(void* value){auto* op=static_cast<pub::AI::DirectiveGotoOp*>(value);++destinationUpdates;Flag2ea=0;
        destination=op->Destination;targetMode=op->Field_0C;targetId=op->Field_1C;stopRange=op->Field_50;return true;}
} nativeGoto;
struct PlayerOwner { bool is_player(){return true;} } playerOwner;
PlayerOwner* ObjRwFromWatchable(void*){return &playerOwner;}
struct IBehaviorManager {
    int CurrentBehaviorIndex=2;
    GotoBehavior* BehaviorDispatchTable[3]={nullptr,nullptr,&nativeGoto};
    bool cruise=true;
    bool LockManeuversByte=false;
    unsigned char Opaque168[1]={1};
    Vector direction;
    Vector LastCommandedDirection;
    unsigned char UserTurningInputState=0;
    void* WatchablePtr=nullptr;
    unsigned directionWrites=0;
    float throttle=1;
    unsigned cruiseOff=0,directiveChanges=0;
    unsigned dockRequests=0;
    int external_player_evaluate(int){return 0;}
    void update_current_behavior_cruise(bool on){cruise=on;if(!on)++cruiseOff;}
    void update_current_behavior_throttle(float value){throttle=value;}
    void update_current_behavior_direction(Vector value){
        direction=LastCommandedDirection=value;++directionWrites;
        UserTurningInputState=length(value)!=0;
        // Point-target Go To sets the manual override even for a zero vector.
        nativeGoto.Flag2ea=1;
    }
    void replayPlayerDirection(){ REPLAY_PLAYER_DIRECTION }
    bool set_current_directive(int id,void* op){++directiveChanges;CurrentBehaviorIndex=id;if(id==2)nativeGoto.Slot10(op);if(id==7)++dockRequests;return true;}
} pilot;
IBehaviorManager* PlayerBehaviorManager(){return &pilot;}
bool GetPlayerEngineCruiseActive(){return pilot.cruise;}
bool G_MouseFlightEngaged=false,G_MouseFlightButtonTrigger=false;
float G_MouseFlightHoldTimer=0,G_MouseFlightOriginX=0,G_MouseFlightOriginY=0;
void ClearMouseFlightSteering();
void ResetPlayerBehaviorDirection(){pilot.update_current_behavior_direction({});}
struct Watchable {};
struct CObject { static constexpr int ClassSolar=1;int ObjectClass=ClassSolar; };
struct CSolar:CObject {unsigned DestSystem=66;struct Gate{unsigned Id=999;} DestGate;};
struct IObjRW:Watchable {
    unsigned id=999,type=0x200;
    V position;
    CSolar solar;
    IObjRW* selectedTarget=nullptr;
    IObjRW* get_target(){return selectedTarget;}
    void get_type(unsigned& out){out=type;}
    void set_target(IObjRW* target,int,unsigned){selectedTarget=target;}
    CObject* cobject(){return &solar;}
    V get_position(){return position;}
    unsigned get_id(){return id;}
    bool is_dying(){return false;}
    void get_physical_radius(float& radius,V& center){radius=10;center=position;}
};
struct CShip {
    IObjRW* target=nullptr;
    IObjRW* get_target(){return target;}
    bool is_using_tradelane(){return false;}
    bool is_launching(){return false;}
} hull;
IObjRW playerObject;
std::vector<IObjRW*> objects;
struct HUD_Maneuvers { bool RequestManeuver(int,bool); } maneuvers;
HUD_Maneuvers* GetHudManeuvers(){return &maneuvers;}
void PointAlongShipZ(IObjRW*,float distance,float* point){point[0]=point[1]=0;point[2]=distance;}
struct HUD_Waypoint {
    unsigned char bUser=1;
    int Id=0,Index=0;
    IObjRW* object=nullptr;
    IObjRW* GetWaypointObject(){return object;}
} hudWaypoint;
HUD_Waypoint* GetHudWaypoint(){return &hudWaypoint;}
struct FPlayerWaypointRecord { V Pos; unsigned SystemId=55,ObjectId=0; int AutoId=0; };
std::vector<FPlayerWaypointRecord> waypoints;
int GetPlayerWaypointCountRetail(){return static_cast<int>(waypoints.size());}
FPlayerWaypointRecord* GetPlayerWaypointRetail(int i){return &waypoints[static_cast<size_t>(i)];}
unsigned login=1;
unsigned GetPlayerConnectionId(){return login;}
unsigned GetPlayerStarSystemIdRetail(){return 55;}
int PortConfigInt(char const*,char const*,int fallback){return fallback;}
struct Request {V from,to;unsigned object,system;};
std::vector<Request> requests;
void RequestBestPathRetail(Vector const&,Vector const&,unsigned,unsigned);
void RemovePlayerWaypointRetail(int);
namespace RoutePlanner { void Invalidate(){} }
namespace PlayerFlightActions {
enum Kind { SpiralClockwise,ReverseTurn,ReverseStrafe,GotoWeave,Count,None };
Kind active=None;
POINT mouseStart;
struct Camera { bool holding(){return false;} } turnCamera;
void finish(bool){active=None;}
}
namespace PlayerRoute {
enum class State { Off,Flying,Docking,Lane,Jump };
State state=State::Flying;
bool internal=false,refining=false,cruiseRequested=true,issued=true,reissueAfterRemoval=false;
bool mouseOverride=false,replanAfterMouse=false;
bool haveGoal=false,rebuildOnStart=false,pendingStart=false,receivingPath=false;
FPlayerWaypointRecord savedGoal{};
unsigned goalConnection=0,connection=0,system=0,jumpSystem=0,exitGate=0;
struct Owner { Watchable* p=nullptr; void set(Watchable* value){p=value;} Watchable* target(){return p;} } owner;
V previous;
float bestDistance=0,stalled=0,elapsed=0;
struct Node { FPlayerWaypointRecord point; bool user=false,dock=false,laneExit=false; };
std::deque<Node> route(1);
std::deque<V> leg;
IObjRW* player(){return &playerObject;}
CShip* ship(){return &hull;}
IBehaviorManager* manager(){return &pilot;}
IObjRW* object(unsigned id){for(auto* obj:objects)if(obj->id==id)return obj;return nullptr;}
unsigned typeOf(IObjRW* p){return p?p->type:0;}
V v(V p){return p;} V vec(V p){return p;}
int directive(int id){return id;}
void notify(unsigned,int){}
struct Guard { bool old=internal; Guard(){internal=true;} ~Guard(){internal=old;} };
bool Active();
void Cancel(bool stop=false);
bool Start(HUD_Maneuvers*,bool rebuilt=false);
void PathRequested();
void RouteChanged();
void WaypointRemoved();
bool prepared=false,refineOK=true;
bool gotoPoint(V,bool);
// Geometry is tested separately. Exercise the real Go To directive update at
// the planner boundary, including its interaction with Common's input replay.
bool prepare(){prepared=true;if(route.empty())return false;leg={route.front().point.Pos};return gotoPoint(leg.front(),route.size()>1);}
bool dock();
bool refineWaypoints(){return refineOK;}
void fail(bool=false){Cancel(true);}
}
void RequestBestPathRetail(Vector const& a,Vector const& b,unsigned id,unsigned sys){
    PlayerRoute::PathRequested();requests.push_back({a,b,id,sys});
}
void RemovePlayerWaypointRetail(int i){waypoints.erase(waypoints.begin()+i);PlayerRoute::WaypointRemoved();}
void AddPlayerWaypointRetail(V p,unsigned sys,unsigned id){waypoints.push_back({p,sys,id,int(waypoints.size()+1)});}
'''.replace('REPLAY_PLAYER_DIRECTION', replay)

production = '\nnamespace PlayerFlightActions {\n' + ''.join(
    extract(actions, sig) for sig in ('bool locksInput(', 'void Cancel()', 'bool RequestCancel()', 'bool IsGotoWeaving()', 'bool BlockMouse()')) + '}\n'
production += '\nnamespace PlayerRoute {\n' + ''.join(
    extract(route, sig) for sig in ('bool Active()', 'int selectedRouteIndex(', 'bool rebuildRoute(',
                                    'void Cancel(', 'bool dock()', 'void consume()', 'bool BlockMouse()', 'bool MouseSteering(',
                                    'bool ReleaseMouseSteering()',
                                    'bool Keyboard(', 'void SetCruiseRequested(', 'void RouteChanged()', 'void WaypointRemoved()',
                                    'void PathRequested()', 'void BeginPathResponse()', 'bool gotoPoint(',
                                    'bool Start(', 'void Tick(', 'bool RefineWaypoints()')) + '}\n'
production += extract(behavior, 'void ClearMouseFlightSteering()')
production += extract(behavior, 'void ToggleMouseFlightLock()')
production += extract(behavior, 'void SetPlayerCruise(')
goto_start = hud.index('    case 2:', hud.index('bool HUD_Maneuvers::RequestManeuver('))
goto_case = hud[goto_start:hud.index('    case 0xa:', goto_start)]
production += '''bool HUD_Maneuvers::RequestManeuver(int id,bool){
    assert(id==2);PlayerRoute::Cancel();PlayerFlightActions::Cancel();
    auto* Ship=&playerObject;auto* Behavior=&pilot;int Info=id;bool bResult=false;
    switch(id){\n''' + goto_case + '''default:return false;}return bResult;}\n'''
cruise_case = hud[hud.index('    case 0x45:'):hud.index('    case 0x0f:')]
production += 'bool cruiseCommand(){switch(0x45){\n' + cruise_case + 'default:return false;}}\n'

checks = r'''
int main(){
    using namespace PlayerRoute;
    // Space/LMB allow real manual steering inside F2, except in camera look or
    // a transition. Merely preserving Active() while swallowing input is wrong.
    for(bool look:{false,true}) for(State mode:{State::Flying,State::Docking,State::Lane,State::Jump}) {
        headLook=look;state=mode;
        for(int i=0;i<20;++i){
            ToggleMouseFlightLock();
            mouseButtons=unsigned(i%2);cursor={i*37,i*-23};
            bool allowed=!look && mode==State::Flying && (G_MouseFlightLocked || mouseButtons!=0);
            assert(BlockMouse()==!allowed && Active());
            unsigned before=pilot.directionWrites;
            if(allowed){
                assert(MouseSteering(.6f,-.3f,0));
                assert(mouseOverride && nativeGoto.Flag2ea && pilot.directionWrites==before+1);
                assert(pilot.direction.x==.6f && pilot.direction.y==-.3f);
                G_MouseFlightEngaged=true;
            }
            assert(!Keyboard(0,0,0));
            assert(pilot.cruise && pilot.throttle==1 && pilot.CurrentBehaviorIndex==2);
        }
    }
    state=State::Flying;headLook=true;
    assert(BlockMouse() && !mouseOverride && replanAfterMouse && !nativeGoto.Flag2ea);
    assert(!G_MouseFlightEngaged && pilot.cruise);
    // Common replays the last nonzero player direction on every simulation
    // update. Releasing just Go To's flag (or reissuing F2) cannot stop that.
    assert(length(pilot.LastCommandedDirection)==0 && !pilot.UserTurningInputState);
    for(int frame=0;frame<120;++frame){
        pilot.replayPlayerDirection();
        assert(!nativeGoto.Flag2ea && !mouseOverride && Active());
        assert(pilot.cruise && pilot.throttle==1 && pilot.CurrentBehaviorIndex==2);
    }
    // Simulation must release the override without relying on a render/input
    // callback. Cover Space, held LMB, cockpit head look and entering the HUD.
    for(float hz:{30.f,60.f,144.f}) for(int release=0;release<4;++release){
        headLook=hover=false;G_MouseFlightLocked=release!=1;mouseButtons=release==1?1u:0u;
        route={{{{10000,0,0},55,0,0}}};leg.clear();
        connection=login;PlayerRoute::system=55;owner.set(&playerObject);previous=playerObject.position;
        state=State::Flying;replanAfterMouse=false;prepared=false;
        assert(MouseSteering(.6f,-.3f,0));G_MouseFlightEngaged=true;
        for(int frame=0;frame<10;++frame){
            Tick(1/hz,false);pilot.replayPlayerDirection();
            assert(mouseOverride && nativeGoto.Flag2ea && !prepared);
        }
        if(release==0)ToggleMouseFlightLock();
        if(release==1)mouseButtons=0;
        if(release==2){
            headLook=true;
            // A cleared client latch must not hide Common's cached input.
            G_MouseFlightEngaged=false;ClearMouseFlightSteering();
        }
        if(release==3)hover=true;
        for(int frame=0;frame<120;++frame){
            Tick(1/hz,false);pilot.replayPlayerDirection();
            assert(!mouseOverride && !nativeGoto.Flag2ea && Active());
            assert(length(pilot.LastCommandedDirection)==0 && !pilot.UserTurningInputState);
            assert(prepared && nativeGoto.destination.x==10000);
            assert(pilot.cruise && pilot.throttle==1 && pilot.CurrentBehaviorIndex==2);
        }
    }
    hover=false;
    state=State::Off;assert(!BlockMouse() && !MouseSteering(1,0,0));
    PlayerFlightActions::active=PlayerFlightActions::GotoWeave;
    headLook=false;G_MouseFlightLocked=true;mouseButtons=1;cursor={1000,500};
    assert(!PlayerFlightActions::BlockMouse() && PlayerFlightActions::IsGotoWeaving());

    // Cruise while weaving: remove only the weave, retaining F2, throttle and an
    // already-running cruise. Also engage it when the engine was not cruising.
    for(bool initialCruise:{false,true}){
        state=State::Flying;pilot.cruise=initialCruise;pilot.cruiseOff=0;
        PlayerFlightActions::active=PlayerFlightActions::GotoWeave;
        assert(cruiseCommand());
        assert(!PlayerFlightActions::IsGotoWeaving());
        assert(Active() && pilot.cruise && pilot.throttle==1 && pilot.cruiseOff==0);
        assert(pilot.CurrentBehaviorIndex==2);
        // A normal subsequent click can turn cruise off without stopping F2/thrust.
        assert(cruiseCommand() && !pilot.cruise && !cruiseRequested);
        assert(Active() && pilot.throttle==1);
        for(int i=0;i<3;++i) {
            assert(gotoPoint({float(i*1000),0,0},true));
            assert(Active() && !pilot.cruise && pilot.throttle==1);
        }
        assert(cruiseCommand() && pilot.cruise && cruiseRequested);
        assert(gotoPoint({5000,0,0},true) && pilot.cruise);
        assert(pilot.directiveChanges==0); // No exit/re-enter of Go To.
    }
    assert(Keyboard(1,0,0) && !Active());

    // Selected free-space waypoint 2 has no ObjectId. Its HUD solar id is
    // unrelated, and its cached Index may be stale after removing earlier points.
    pilot.cruise=true;pilot.throttle=1;pilot.CurrentBehaviorIndex=2;
    waypoints={{{1000,0,0},55,0,21},{{9000,0,0},55,0,22},{{30000,0,0},55,321,23}};
    IObjRW marker;marker.id=777;marker.position={9000,0,0};
    hull.target=&marker;hudWaypoint.object=&marker;hudWaypoint.bUser=1;hudWaypoint.Id=22;hudWaypoint.Index=0;
    assert(selectedRouteIndex(&marker)==1);
    pilot.update_current_behavior_direction({-.7f,.2f,0});G_MouseFlightEngaged=false;
    assert(Start(nullptr) && route.front().point.AutoId==22);
    pilot.replayPlayerDirection();
    assert(length(pilot.LastCommandedDirection)==0 && !pilot.UserTurningInputState && !nativeGoto.Flag2ea);
    // Deleting the selected map marker leaves the active copied route and native
    // Go To directive untouched. A later F2 reads the updated waypoint list.
    RemovePlayerWaypointRetail(1);
    assert(Active() && route.front().point.AutoId==22 && pilot.CurrentBehaviorIndex==2);
    assert(reissueAfterRemoval);
    V removedTarget=leg.front();prepared=false;
    hull.target=nullptr;pilot.CurrentBehaviorIndex=0x13; // Native Go To loses its selected target.
    Tick(1/60.f,false);
    assert(Active() && route.front().point.AutoId==22 && pilot.CurrentBehaviorIndex==2);
    assert(!reissueAfterRemoval && !prepared && leg.front().x==removedTarget.x);
    assert(nativeGoto.destination.x==removedTarget.x && pilot.cruise && pilot.throttle==1);
    // Internal route refinement/removal must not schedule a redundant reissue.
    internal=true;WaypointRemoved();internal=false;
    refining=true;WaypointRemoved();refining=false;
    receivingPath=true;WaypointRemoved();receivingPath=false;
    assert(!reissueAfterRemoval && Active() && pilot.CurrentBehaviorIndex==2);

    // Building a different waypoint route must not cancel or brake the route
    // already flying. Cover map reset, request and server response separately.
    unsigned mapEditCruiseOff=pilot.cruiseOff;
    RouteChanged();
    assert(Active() && route.front().point.AutoId==22 && reissueAfterRemoval);
    assert(pilot.cruise && pilot.throttle==1 && pilot.cruiseOff==mapEditCruiseOff);
    pilot.CurrentBehaviorIndex=0x13;Tick(1/60.f,false);
    assert(Active() && pilot.CurrentBehaviorIndex==2 && !prepared && leg.front().x==removedTarget.x);
    PathRequested();
    assert(Active() && route.front().point.AutoId==22 && pilot.CurrentBehaviorIndex==2);
    BeginPathResponse();
    assert(Active() && receivingPath && reissueAfterRemoval && pilot.CurrentBehaviorIndex==2);
    RouteChanged(); // The response's map replacement must not cancel the flight.
    assert(RefineWaypoints() && Active() && !receivingPath && !prepared);
    assert(route.front().point.AutoId==22 && leg.front().x==removedTarget.x);
    pilot.CurrentBehaviorIndex=0x13;Tick(1/60.f,false);
    assert(Active() && pilot.CurrentBehaviorIndex==2 && !prepared && leg.front().x==removedTarget.x);
    assert(pilot.cruise && pilot.throttle==1 && pilot.cruiseOff==mapEditCruiseOff);

    hull.target=nullptr; // Resume the saved route independently of the deleted marker.
    haveGoal=true;savedGoal=waypoints.back();goalConnection=login;
    AddPlayerWaypointRetail({45000,0,0},55,0);
    assert(Active() && route.front().point.AutoId==22 && pilot.CurrentBehaviorIndex==2);
    internal=true;RemovePlayerWaypointRetail(int(waypoints.size()-1));internal=false;
    assert(!reissueAfterRemoval && Active() && pilot.CurrentBehaviorIndex==2);
    Cancel(); // Freeflight switches directive separately, keeping cruise/throttle.
    pilot.CurrentBehaviorIndex=0x13;
    assert(rebuildOnStart && !Active() && pilot.cruise && pilot.throttle==1);
    playerObject.position={12000,300,2000};prepared=false;
    assert(Start(nullptr) && pendingStart && !prepared && requests.size()==1);
    assert(length(requests.back().from-playerObject.position)==0);
    assert(length(requests.back().to-V{30000,0,0})==0 && requests.back().object==321);
    assert(route.empty() && pilot.cruise && pilot.throttle==1);
    assert(Start(nullptr) && requests.size()==1); // Held F2 cannot queue duplicate requests.
    BeginPathResponse();RouteChanged();assert(pendingStart);
    waypoints={{{15000,500,3000},55,0,1},savedGoal};
    assert(RefineWaypoints() && Active() && prepared && !pendingStart);
    assert(route.front().point.Pos.x==15000 && route.front().point.AutoId==1);
    assert(pilot.cruise && pilot.throttle==1); // No return to old waypoint 1 or 2.

    // Cancel during the request: its eventual reply may update the map but
    // must not take flight control back. A new user map request also invalidates it.
    Cancel();hull.target=nullptr;assert(Start(nullptr) && pendingStart);
    Cancel();assert(!pendingStart);prepared=false;
    BeginPathResponse();assert(RefineWaypoints() && !Active() && !prepared);
    pendingStart=true;PathRequested();assert(!pendingStart && !haveGoal && !rebuildOnStart);
    BeginPathResponse();assert(RefineWaypoints() && !Active());
    goalConnection=login;rebuildOnStart=true;++login;
    assert(!rebuildRoute(true));

    // A selected mission/object target without a user waypoint stays entirely
    // on native F2; no one-node route or safe-path preflight is created.
    haveGoal=rebuildOnStart=false;hudWaypoint.bUser=0;hull.target=&marker;
    assert(selectedRouteIndex(&marker)==-1);
    prepared=false;assert(!Start(nullptr) && !Active() && !prepared && route.empty());
    // Without base-docking permission, the final checked approach must hand off
    // to the native F2 object command, never stop at the preceding waypoint.
    Cancel();headLook=false;G_MouseFlightLocked=false;mouseButtons=0;
    for(unsigned type:{0x100u,0x20u,0x40u,0x800u,0x80u}) for(int autoDock:{0,1}){
        IObjRW destination;destination.id=321;destination.type=type;
        objects={&destination};hull.target=&destination;playerObject.selectedTarget=&destination;
        waypoints={{{30000,0,0},55,321,1}};
        route={{waypoints.front(),true,true}};leg={playerObject.position};
        state=State::Flying;issued=true;mouseOverride=replanAfterMouse=false;
        haveGoal=true;savedGoal=waypoints.front();goalConnection=connection=login;PlayerRoute::system=55;
        owner.set(&playerObject);previous=playerObject.position;
        pilot.CurrentBehaviorIndex=2;pilot.cruise=true;pilot.throttle=1;
        NavigationSettings::values[NavigationSettings::AutoDock]=autoDock;
        auto before=pilot.dockRequests;
        auto cruiseOffBefore=pilot.cruiseOff;
        Tick(1/60.f,false);
        assert(waypoints.size()==1&&waypoints.front().ObjectId==321&&playerObject.selectedTarget==&destination);
        bool const travel=type==0x40u || type==0x800u || type==0x80u;
        if(autoDock || travel){
            assert(Active()&&state==State::Docking&&pilot.CurrentBehaviorIndex==7&&pilot.dockRequests==before+1);
        }else{
            assert(!Active()&&pilot.dockRequests==before&&pilot.CurrentBehaviorIndex==2);
            assert(nativeGoto.targetMode==0&&nativeGoto.targetId==321&&nativeGoto.stopRange==100);
            assert(pilot.cruise&&pilot.throttle==1&&rebuildOnStart&&pilot.cruiseOff==cruiseOffBefore);
        }
        Cancel();
    }
    objects.clear();hull.target=nullptr;haveGoal=rebuildOnStart=false;
    NavigationSettings::values[NavigationSettings::Autopilot]=0;
    assert(!Start(nullptr)&&!Active()); // Native F2 gets control back.
    NavigationSettings::values[NavigationSettings::Autopilot]=1;
    assert(Start(nullptr)&&Active());
    pilot.cruise=true;pilot.throttle=1;
    NavigationSettings::values[NavigationSettings::Autopilot]=0;
    Tick(1/60.f,false);
    assert(!Active()&&pilot.cruise&&pilot.throttle==1); // Applying settings does not brake.
    puts("PASS: native single-object F2; waypoint deletion/addition preserves active route; lane/gate/hole travel, docking, mouse resume, cruise, replans and stale-response cancellation.");
}
'''
(OUT / 'check.cpp').write_text('#include "' + (CLIENT / 'route_geometry.h').as_posix() + '"\n'
                               + stub + production + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc / 'include'] + [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')]))
env['LIB'] = ';'.join(map(str, [vc / 'lib/x86'] + [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')]))
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
subprocess.run([str(OUT / 'check.exe')], cwd=OUT, check=True)
