"""Exercise production map refinement and F2 planning around non-dockable objects."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'src/freelancer/Client'
OUT = ROOT / 'src/obj/route_autopilot/objects'
OUT.mkdir(parents=True, exist_ok=True)


def extract(source, signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


planner = (CLIENT / 'route_planner.cpp').read_text()
route = (CLIENT / 'player_route.cpp').read_text()
stub = r'''
#include <cassert>
#include <cstdio>
#include <deque>
using namespace RouteGeometry;
using Vector=V;
struct IObjRW {
    unsigned id=0,type=0x100;
    V position;
    float radius=1650,atmosphere=0;
    bool dockable=false;
    V get_position(){return position;}
    unsigned get_id(){return id;}
    void get_physical_radius(float& r,V& c){r=radius;c=position;}
    void get_atmosphere_range(float& r){r=atmosphere;}
} playerObject,fixtureTarget;
struct ObjDb {IObjRW* FindById(unsigned* id){return *id==fixtureTarget.id?&fixtureTarget:nullptr;}} fixtureDb;
ObjDb* GetClientObjDb(){return &fixtureDb;}
struct FPlayerWaypointRecord {V Pos;unsigned SystemId=55,ObjectId=0;int AutoId=0;};
std::vector<FPlayerWaypointRecord> waypoints;
int GetPlayerWaypointCountRetail(){return int(waypoints.size());}
FPlayerWaypointRecord* GetPlayerWaypointRetail(int i){return &waypoints[size_t(i)];}
unsigned GetPlayerStarSystemIdRetail(){return 55;}
void ResetPlayerWaypointsRetail(){waypoints.clear();}
void AddPlayerWaypointRetail(V p,unsigned sys,unsigned id){waypoints.push_back({p,sys,id,int(waypoints.size()+1)});}
int selected=-1;
void HudWaypointSelectPlayerWaypoint(int i){selected=i;}
namespace NavigationSettings {enum Setting{Autopilot};int Get(Setting){return 1;}}
namespace RoutePlanner {
V v(V p){return p;}
unsigned cachedSystem=55;
float margin=350;
std::vector<Sphere> hazards;
std::vector<Vertex> corridors;
bool BetaEnabled(){return true;}
void load(){}
void Invalidate(){}
bool clear(V a,V b){for(auto const& h:hazards)if(!sphereClear(a,b,h.center,h.radius))return false;return true;}
int dockPlans=0;
bool PlanDock(V,V,unsigned,float,std::vector<V>&){++dockPlans;return false;}
}
namespace PlayerRoute {
V v(V p){return p;}V vec(V p){return p;}
IObjRW* player(){return &playerObject;}
IObjRW* object(unsigned id){return id?fixtureDb.FindById(&id):nullptr;}
unsigned typeOf(IObjRW* obj){return obj?obj->type:0;}
IObjRW* dockingObject(IObjRW* obj){return obj&&obj->dockable?obj:nullptr;}
float dockingRange(unsigned){return 2000;}
struct Node {FPlayerWaypointRecord point;bool user=false,dock=false,laneExit=false;};
unsigned system=55;
bool refining=false;
std::deque<Node> route;
std::deque<V> leg;
void select(Node const&){}
int dockCalls=0;
bool dock(){++dockCalls;return true;}
bool gotoPoint(V point,bool){assert(RoutePlanner::clear(point,point));return true;}
}
'''
production = '\nnamespace RoutePlanner {\n' + ''.join(extract(planner, sig) for sig in
    ('bool plan(', 'bool Plan(', 'bool PlanApproach(')) + '}\n'
production += '\nnamespace PlayerRoute {\n' + ''.join(extract(route, sig) for sig in
    ('bool prepare()', 'static bool refineWaypoints()')) + '}\n'
checks = r'''
void followMap(V from){
    PlayerRoute::route.clear();
    for(auto const& point:waypoints)PlayerRoute::route.push_back({point,true});
    playerObject.position=from;
    while(!PlayerRoute::route.empty()){
        assert(PlayerRoute::prepare()&&!PlayerRoute::leg.empty());
        for(V p:PlayerRoute::leg){
            assert(RoutePlanner::clear(playerObject.position,p));
            playerObject.position=p;
        }
        PlayerRoute::route.pop_front();
    }
    assert(PlayerRoute::dockCalls==0&&RoutePlanner::dockPlans==0);
}
int main(){
    auto& target=fixtureTarget;
    // Installed ku_ksu_03 (Tokyo), solar_radius=1500, model odissey.cmp:
    // Level0 VMeshRef centre=(0,0,0), radius=1650. Dock's actual offset is
    // +1560 Z; its fixture uses a conservative 750 m guard. Not a live capture.
    target.id=321;target.position={-50000,0,-41560};
    unsigned count=0;
    for(float margin:{150.f,350.f,3000.f})for(V delta:{V{-12000,0,0},V{12000,0,0},V{0,0,12000},V{0,0,-12000}}){
        RoutePlanner::margin=margin;
        RoutePlanner::hazards={{target.position,1650+margin},{target.position+V{0,0,1560},750+margin}};
        V from=target.position+delta;playerObject.position=from;
        std::vector<V> path;
        assert(!RoutePlanner::Plan(from,target.position,path)); // Old map endpoint fails.
        waypoints={{target.position,55,target.id,1}};
        assert(PlayerRoute::refineWaypoints()&&selected==0&&waypoints.size()>=2);
        assert(waypoints.back().ObjectId==target.id&&length(waypoints.back().Pos-target.position)==0);
        followMap(from);
        assert(length(playerObject.position-target.position)>1650+margin);
        assert(RoutePlanner::PlanApproach(playerObject.position,target.id,path));
        assert(length(path.back()-playerObject.position)<.01f); // Arrival never sends us away again.
        ++count;
    }
    // Near-side approach is occupied. Search another side, retain all solids.
    RoutePlanner::margin=350;
    RoutePlanner::hazards={{target.position,2000},{target.position+V{-2500,0,0},800}};
    V from=target.position+V{-12000,0,0};playerObject.position=from;
    waypoints={{target.position,55,target.id,1},{target.position+V{10000,0,5000},55,0,2}};
    assert(PlayerRoute::refineWaypoints());followMap(from);
    assert(length(playerObject.position-(target.position+V{10000,0,5000}))<.01f);

    // Non-dockable planet: the atmosphere, not merely the mesh, bounds arrival.
    target.radius=6000;target.atmosphere=7000;
    RoutePlanner::hazards={{target.position,7350}};
    playerObject.position=from;waypoints={{target.position,55,target.id,1}};
    assert(PlayerRoute::refineWaypoints());followMap(from);
    assert(length(playerObject.position-target.position)>7350);

    // Never turn an impossible approach into a direct flight to the centre.
    RoutePlanner::hazards={{target.position,1000000}};
    playerObject.position=from;waypoints={{target.position,55,target.id,1}};
    assert(!PlayerRoute::refineWaypoints()&&waypoints.empty());
    std::vector<V> path;
    assert(!RoutePlanner::PlanApproach(from,999,path)&&path.empty());

    // Leave Tokyo from between overlapping component guards, then approach a
    // different object. Exercise both map refinement and the actual F2 planner.
    V tokyo=target.position;
    target.position=tokyo+V{25000,3000,19000};target.radius=800;target.atmosphere=0;
    RoutePlanner::hazards={{tokyo,2000},{tokyo+V{0,0,1560},1100},{target.position,1150}};
    from=tokyo+V{0,0,700};playerObject.position=from;
    waypoints={{target.position,55,target.id,1}};
    assert(PlayerRoute::refineWaypoints()&&waypoints.size()>=3);
    assert(RoutePlanner::clear(from,waypoints.front().Pos));
    followMap(from);
    assert(length(playerObject.position-target.position)>1150);
    printf("PASS: %u Tokyo core approaches through production map/F2 planners; alternate side, following waypoint, atmosphere and blocked destination; no Dock for non-dockable targets.\n",count);
    puts("PASS: map/F2 departure from overlapping Tokyo core/dock guards to another object.");
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
