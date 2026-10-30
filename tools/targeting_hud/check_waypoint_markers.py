"""Exercise production waypoint identity/caption decisions, independent of rendering."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'src/freelancer/Client/hud_targetable_objects.cpp').read_text()
OUT = ROOT / 'src/obj/waypoint_marker_check'
OUT.mkdir(parents=True, exist_ok=True)


def extract(signature):
    start = SOURCE.index(signature)
    end = SOURCE.index('{', start) + 1
    depth = 1
    while depth:
        depth += (SOURCE[end] == '{') - (SOURCE[end] == '}')
        end += 1
    return SOURCE[start:end] + '\n'


stub = r'''
#include <cassert>
#include <cstdio>
struct Vector {float x=0,y=0,z=0;};
struct IObjRW {
    unsigned id=42; Vector position;
    unsigned get_id(){return id;}
    Vector get_position(){return position;}
};
struct FHudContactRecord {
    unsigned char bValid=1,bIsWaypoint=0;
    unsigned ObjectId=0; Vector World;
};
struct FPlayerWaypointRecord {int AutoId=7;} first;
bool haveFirst=true;
FPlayerWaypointRecord* GetPlayerWaypointRetail(int){return haveFirst?&first:nullptr;}
struct HUD_Waypoint {
    unsigned char bUser=1;int Index=0,Id=7;IObjRW* object=nullptr;
    IObjRW* GetWaypointObject(){return object;}
} waypoint;
HUD_Waypoint* active=&waypoint;
HUD_Waypoint* GetHudWaypoint(){return active;}
'''
checks = r'''
int main(){
    IObjRW solar;waypoint.object=&solar;
    FHudContactRecord player,mission;
    player.World={12000,0,-50000};mission.World=player.World;
    solar.position={12000.25f,.5f,-50000.5f};
    // Exact-coordinate classification produced two markers and a mission
    // caption for this single reused player waypoint Solar.
    assert(MatchesWaypointContact(&solar,player,true));
    assert(IsPlayerWaypointContact(&solar,player));
    assert(!MatchesWaypointContact(&solar,mission,false));
    waypoint.Index=4; // Stale index after preceding points were consumed.
    assert(MatchesWaypointContact(&solar,player,true));
    waypoint.Id=8; // Deliberately target a later point: retain the first marker.
    assert(!MatchesWaypointContact(&solar,player,true));
    assert(IsPlayerWaypointContact(&solar,player));
    haveFirst=false;
    assert(!MatchesWaypointContact(&solar,player,true));haveFirst=true;
    waypoint.bUser=0;waypoint.Index=0;
    assert(!MatchesWaypointContact(&solar,player,true));
    assert(MatchesWaypointContact(&solar,mission,false));
    assert(!IsPlayerWaypointContact(&solar,mission));
    waypoint.Index=1;assert(!MatchesWaypointContact(&solar,mission,false));
    // Object-bound routes use identity, including moving objects.
    waypoint.object=nullptr;player.ObjectId=42;
    assert(MatchesWaypointContact(&solar,player,true));
    player.ObjectId=99;solar.position=player.World;
    assert(!MatchesWaypointContact(&solar,player,true));
    player.ObjectId=0;
    assert(MatchesWaypointContact(&solar,player,true)); // Native positional fallback.
    player.bValid=0;assert(!MatchesWaypointContact(&solar,player,true));
    assert(!MatchesWaypointContact(nullptr,player,true));
    active=nullptr;player.bIsWaypoint=1;
    assert(IsPlayerWaypointContact(&solar,player));
    puts("PASS: selected route point has one identity and route caption; position drift, consumed indices, later selections and independent mission points remain distinct.");
}
'''
(OUT / 'check.cpp').write_text(stub + extract('bool MatchesWaypointContact(') +
                              extract('bool IsPlayerWaypointContact(') + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc / 'include'] + [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')]))
env['LIB'] = ';'.join(map(str, [vc / 'lib/x86'] + [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')]))
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
subprocess.run([str(OUT / 'check.exe')], cwd=OUT, check=True)
