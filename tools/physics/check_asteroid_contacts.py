"""Run the production HUD contact rebuild against spatial, large and watched rocks."""
import os
from pathlib import Path
import subprocess

from check_gravity import function

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/asteroid_contacts_check'
SOURCE = 'src/freelancer/Client/hud_contact_list.cpp'

STUB = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <list>
#include <vector>
#include "common_server_asteroid.h"
struct Vector {float x=0,y=0,z=0;};
struct IObjRW;
using Watchable=IObjRW;
struct BaseWatcher {IObjRW* value=nullptr;Watchable* target() const{return value;}};
IObjRW* ObjRwFromWatchable(Watchable* p){return p;}
struct CObject {
    unsigned ObjectClass=0x303;Vector WorldPosition;
    float get_physical_radius_r(Vector& center) const{center=WorldPosition;return 10;}
};
struct CSimple:CObject {unsigned TypeBits=0x10,Id=1;};
struct CEqObj:CSimple {float CloakPercent=0;unsigned VibeId=0;};
struct CSolar:CEqObj {
    struct Nick {bool IsEmpty() const{return true;}};
    Nick GetParentNickname() const{return {};}
};
struct CShip:CEqObj {
    int bIsPlayer=0;BaseWatcher FormationLeader;
    struct Follower {IObjRW* get() const{return nullptr;}};
    std::vector<Follower> FormationFollowers;IObjRW* current=nullptr;
    IObjRW* get_target() const{return current;}
};
bool IsClass(CObject const* p,unsigned mask){return (p->ObjectClass&mask)==mask;}
CSimple const* AsSimple(CObject const* p){return p?static_cast<CSimple const*>(p):nullptr;}
CShip const* AsShip(CObject const* p){return p&&IsClass(p,0x503)?static_cast<CShip const*>(p):nullptr;}
bool IsNomadEqObj(CSimple const*){return false;}
int OtherPlayerKind(CShip const*){return 0;}
struct IObjRW {
    CSimple* body=nullptr;IObjRW* ListNext=nullptr;bool large=false;int attitude=0;
    CObject* cobject() const{return body;}
    unsigned get_id() const{return body->Id;}
    Vector const& get_position() const{return body->WorldPosition;}
    int GetCachedAttitude() const{return attitude;}
    bool is_targetable() const{return !IsServerAsteroidType(body->TypeBits);}
};
using FClientGameobj=IObjRW;
CObject* InlineCObjectOf(IObjRW* p){return p->cobject();}
CShip playerShip;IObjRW player{&playerShip};
IObjRW* GetPlayerObjRW(){return &player;}
bool ShouldSkipLocalServerTick(){return false;}
bool SinglePlayer(){return true;}
unsigned RetailU32QueueSize(){return 0;}
unsigned RetailU32QueueAt(unsigned){return 0;}
namespace Reputation {namespace Vibe {int GetAffiliation(int,unsigned& g,bool){g=0;return 0;}}}
struct CEScanner {float range=2500;float GetRadarRange() const{return range;}};
struct HudTarget {int mode=0;int GetMode(bool) const{return mode;}} panel;
HudTarget* G_HudTargetPanel=&panel;
Vector G_ContactPlayerPos;unsigned G_ContactTargetId=0;unsigned char G_bContactTargetListed=0;
constexpr float kDefaultRadarRange=2500,kUnlimitedRange=1e30f,kNearRangeSq=196000000,kSpatialQueryRadius=14000;
std::vector<IObjRW*> largeObjects,spatialObjects;std::list<BaseWatcher> watched;
IObjRW* ClientObjDb_GetKindHead(int const*){return nullptr;}
IObjRW* ClientObjDb_LargeSolarFirst(size_t* index){*index=0;return largeObjects.empty()?nullptr:largeObjects[0];}
IObjRW* ClientObjDb_LargeSolarNext(size_t* index){return ++*index<largeObjects.size()?largeObjects[*index]:nullptr;}
IObjRW* ClientObjDb_FindObject(unsigned id,int){
    for(auto* p:largeObjects)if(p->get_id()==id)return p;
    for(auto* p:spatialObjects)if(p->get_id()==id)return p;
    return nullptr;
}
bool IsLargeSolarCandidate(IObjRW* p){return p->large;}
bool HudIsUnvisitedSolar(CSimple const*){return false;}
struct ISpatialPartition {} spatial;
struct DB {void* GetBucket(unsigned){return &spatial;}} db;
DB* GetClientObjDb(){return &db;}
namespace Geometry {struct Sphere {Vector Center;float Radius;};}
struct FSpatialQueryResult {unsigned Capacity=0,Count=0;void* Items[2048]={};};
int SpatialFill(ISpatialPartition*,Geometry::Sphere*,FSpatialQueryResult* result){
    for(auto* p:spatialObjects)result->Items[result->Count++]=p;return 1;
}
std::list<BaseWatcher> const& GameobjWatchList(){return watched;}
void GameobjWatchListRemove(void*){}
struct FBestPathWaypoint {};
int BestPathGetWaypointCount(){return 0;}
FBestPathWaypoint* BestPathGetWaypoint(int){return nullptr;}
IObjRW* BestPathWaypointResolveObject(FBestPathWaypoint*){return nullptr;}
bool BestPathWaypointResolvePosition(FBestPathWaypoint*,Vector*,unsigned*){return false;}
struct FPlayerWaypointRecord {unsigned SystemId=1;};
int GetPlayerWaypointCountRetail(){return 1;}
FPlayerWaypointRecord* GetPlayerWaypointRetail(int){static FPlayerWaypointRecord r;return &r;}
unsigned GetPlayerStarSystemIdRetail(){return 1;}
namespace Universe {
struct ISystem {unsigned GetId() const{return 1;}} system;
ISystem* get_system(unsigned){return &system;}
}
unsigned selected=0;int selectedWaypoint=-1;
void HudWaypointSelectPlayerWaypoint(int i){selectedWaypoint=i;}
void HudWaypointSelectBestPath(int){}
void SendSelectTarget(unsigned id){selected=id;}
struct FHudContactEntry {
    int Kind;IObjRW* object;float Distance;unsigned Id;int Index;unsigned char bWatchListed=0;
    FHudContactEntry(int k,IObjRW* p,float d,unsigned id,int i):Kind(k),object(p),Distance(d),Id(p?p->get_id():id),Index(i){}
    IObjRW* Object() const{return object;}
};
struct HUD_ContactList {
    std::list<FHudContactEntry> Contacts;CEScanner* Scanner=nullptr;int FilterMode=0;
    int ClassifyContact(CSimple const*);
    void AddShipEntry(CShip const*,FClientGameobj*);
    void RebuildContacts();void SelectEntry(int);
};
'''

CHECK = r'''
int main(){
    playerShip.ObjectClass=0x503;playerShip.Id=99;
    CSolar rock,ordinary;rock.TypeBits=SERVER_ASTEROID_TYPE;rock.Id=1;ordinary.Id=2;
    rock.WorldPosition.x=100;ordinary.WorldPosition.x=150;
    IObjRW rockView{&rock},ordinaryView{&ordinary};
    HUD_ContactList hud;CEScanner scanner;hud.Scanner=&scanner;
    assert(hud.ClassifyContact(&rock)==-1);
    assert(hud.ClassifyContact(&ordinary)==0xc);
    // Both direct-DB routes, all five filters, normal and reduced scan range,
    // hostile/neutral rocks, plus simultaneous watch-list and target reinsertion.
    for(bool large:{false,true})for(float range:{2500.f,1000.f})for(int attitude:{0,-1}){
        scanner.range=range;rockView.large=ordinaryView.large=large;rockView.attitude=attitude;
        largeObjects=large?std::vector<IObjRW*>{&rockView,&ordinaryView}:std::vector<IObjRW*>{};
        spatialObjects={&rockView,&ordinaryView};
        for(bool tracked:{false,true}){
            watched.clear();playerShip.current=nullptr;
            if(tracked){watched.push_back({&rockView});playerShip.current=&rockView;}
            for(int mode=0;mode<5;++mode){
                hud.FilterMode=mode;hud.RebuildContacts();bool foundOrdinary=false,foundWaypoint=false;
                for(auto const& entry:hud.Contacts){
                    assert(entry.Id!=rock.Id);
                    foundOrdinary|=entry.Id==ordinary.Id;foundWaypoint|=entry.Kind==4;
                }
                assert(foundOrdinary==(mode==2||mode==4));
                assert(foundWaypoint==(mode==0||mode==4));
            }
        }
    }
    // An old row cannot send a target-selection command; ordinary rows and
    // position-only waypoints still work through the same production method.
    hud.Contacts.clear();hud.Contacts.emplace_back(0xc,&rockView,0.f,0,0);
    hud.SelectEntry(0);assert(selected==0);
    hud.Contacts.clear();hud.Contacts.emplace_back(0xc,&ordinaryView,0.f,0,0);
    hud.SelectEntry(0);assert(selected==ordinary.Id);
    hud.Contacts.clear();hud.Contacts.emplace_back(4,nullptr,0.f,0,7);
    hud.SelectEntry(0);assert(selectedWaypoint==7);
    puts("PASS: production HUD rebuild excludes server rocks from large/spatial/watch/target routes in all filters");
    puts("PASS: ordinary solars and waypoints preserved, stale asteroid row cannot select target");
}
'''


def main():
    production = ''.join(function(SOURCE, signature) for signature in (
        'int HUD_ContactList::ClassifyContact(',
        'void HUD_ContactList::AddShipEntry(',
        'void HUD_ContactList::RebuildContacts()',
        'void HUD_ContactList::SelectEntry('))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'check.cpp').write_text(STUB+production+CHECK)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10')
    version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include', ROOT/'src/include'] +
                              [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
    env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] +
                          [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                    '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'check.exe')], cwd=OUT, check=True)


if __name__ == '__main__':
    main()
