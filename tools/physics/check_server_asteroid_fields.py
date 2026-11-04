"""Exercise the production field loader/spawner with controlled engine/INI fixtures."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/server_asteroid_fields_check'
STUB = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <memory>
#include <random>
#include <string>
#include <vector>
#include "common_server_asteroid.h"
#define FDUMP(...) ((void)0)
struct RuntimeHitchScope { RuntimeHitchScope(char const*, char const*) {} };
struct Vector {float x=0,y=0,z=0;};
struct Quaternion {float w=1,x=0,y=0,z=0;};
struct Matrix {float E[3][3]={{1,0,0},{0,1,0},{0,0,1}};};
void Server_MatrixToQuat(Quaternion&, Matrix const&){}
float length(Vector v){return std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z);}
unsigned CreateID(char const* s){unsigned h=0;while(*s)h=h*31+static_cast<unsigned char>(*s++);return h;}
struct Section {std::string name;std::vector<std::pair<std::string,std::string>> values;};
std::map<std::string,std::vector<Section>> files;
class INI_Reader {
    std::vector<Section>* sections=nullptr;int header=-1,value=-1;
public:
    bool open(char const* p,bool){auto it=files.find(p);if(it==files.end())return false;sections=&it->second;return true;}
    bool read_header(){value=-1;return ++header<static_cast<int>(sections->size());}
    bool is_header(char const* s){return _stricmp((*sections)[header].name.c_str(),s)==0;}
    bool read_value(){return ++value<static_cast<int>((*sections)[header].values.size());}
    bool is_value(char const* s){return _stricmp((*sections)[header].values[value].first.c_str(),s)==0;}
    char const* get_value_string(){return (*sections)[header].values[value].second.c_str();}
    float get_value_float(int){return std::strtof(get_value_string(),nullptr);}
    int get_value_int(int){return std::atoi(get_value_string());}
};
namespace CmnAsteroid {
struct LootableZoneEntry {
    struct Identifier {unsigned Id=0;} DynamicLootContainerId,DynamicLootCommodityId;
    int DynamicLootCountMin=1,DynamicLootCountMax=1,DynamicLootDifficulty=1;
};
}
namespace Universe {
struct IZone {
    float radius=6000;Vector pos{};unsigned id=7;Matrix orientation;
    Matrix const& GetOrientation()const{return orientation;}
    CmnAsteroid::LootableZoneEntry* loot=nullptr;
    CmnAsteroid::LootableZoneEntry* GetLootableInfo()const{return loot;}
    unsigned GetId()const{return id;}unsigned GetSystem()const{return 1;}
    float GetRadius()const{return radius;}Vector const& GetPos()const{return pos;}
    bool InZone(Vector p,float margin)const{return length({p.x-pos.x,p.y-pos.y,p.z-pos.z})<radius+margin;}
    float GetImmersion(Vector p)const{return InZone(p,0)?1.f:0.f;}
} zone,excluded;
struct System {char const* GetFile(){return "system";}unsigned GetId(){return 1;}};
IZone const* get_zone(unsigned,char const* name){if(!strcmp(name,"zone"))return &zone;if(!strcmp(name,"excluded"))return &excluded;return nullptr;}
void get_filename(char* out,char const* file){strcpy(out,file);}
}
namespace DALib {
struct EngineStub {
    void GetInstanceExtent(void*,int,float* radius,float*){*radius=50;}
    void DestroyInstance(void*){}
} engine;
EngineStub* Engine=&engine;void* Data=nullptr;
}
void GetFileSysPath(char* out,char const* file,void*){strcpy(out,file);}
namespace Archetype {
struct Solar {
    unsigned ObjectType=SERVER_ASTEROID_TYPE;bool loaded=true,fail=false;int refs=0;
    struct {unsigned Id=0;} Loadout;
    bool load(){++refs;if(loaded || fail)return false;loaded=true;return true;}
    bool is_loaded(){return loaded;}void Release(){--refs;}
    long create_instance(void*){return 1;}
    void get_undamaged_collision_group_list(int&){}
} arch;
Solar* GetSolar(unsigned id){return id==CreateID("rock")?&arch:nullptr;}
}
struct CFLIDMaker {unsigned next=0;static CFLIDMaker* GetInstance(){static CFLIDMaker i;return &i;}unsigned AllocateObjectID(){return ++next;}};
struct CSolarCreateInfo {
    unsigned Field_0xb4=999,Field_0xbc=999,ObjId=0,ArchetypeNickname=0,Field_0x6c=0;
    struct {unsigned Id=0;} Field_0xb8;
    Vector Position;Quaternion Orientation;
    int HitPts=0,Field_0xac=0,Field_0xad=0,CollisionGroups=0;
};
struct CObject {Vector pos,velocity,spin;unsigned PhysicsSystemId=1;};
struct CSolar:CObject {Matrix Orientation;float hp=4000;Vector get_velocity(){return velocity;}float get_hit_pts(){return hp;}};
struct GameObject {
    unsigned id=0;bool destroyed=false;CSolar raw;
    CObject* cobj(){return &raw;}bool is_destroyed(){return destroyed;}
    Vector get_position(){return raw.pos;}Vector get_velocity(){return raw.velocity;}bool destroy(int,unsigned){destroyed=true;return true;}
};
struct Solar:GameObject {};
std::map<unsigned,GameObject*> objectsById;
GameObject* Server_LookupGameObject(unsigned id){auto it=objectsById.find(id);return it==objectsById.end()?nullptr:it->second;}
struct SystemPlayerNode {SystemPlayerNode* Next=this;struct {unsigned PlayerId=1;} View;};
struct Player {unsigned ship_object_id=0;} Players[4];
class StarSystem {
    Universe::System info;
public:
    Universe::System* SystemInfo=&info;std::vector<Solar*> objects,tracked;
    struct LootDrop {Vector pos;unsigned container,commodity;int count;};
    std::vector<LootDrop> drops;
    void spawn_mined_loot(Vector const& p,unsigned container,unsigned commodity,int count){drops.push_back({p,container,commodity,count});}
    SystemPlayerNode head;void* PlayerListHead=&head;
    ~StarSystem(){clear();}
    void clear(){for(auto* o:objects){objectsById.erase(o->id);delete o;}objects.clear();tracked.clear();}
    Solar* create_solar(CSolarCreateInfo const& ci){
        assert(ci.Field_0xb4==0&&ci.Field_0xbc==0&&ci.ObjId&&ci.ObjId==ci.Field_0xb8.Id);
        assert(ci.Field_0xac==1&&ci.Field_0xad==1&&ci.Orientation.w==1);
        auto* s=new Solar;s->raw.pos=ci.Position;s->id=ci.ObjId;s->raw.hp=ci.HitPts<0?4000.f:static_cast<float>(ci.HitPts);
        objectsById[s->id]=s;objects.push_back(s);return s;
    }
    void remove_from_list_d4(Solar* s){tracked.erase(std::remove(tracked.begin(),tracked.end(),s),tracked.end());}
    void add_to_list_d4(Solar* s){tracked.push_back(s);}
};
namespace PhySys {
bool blocked=false;
int FindSphereCollisions(unsigned,Vector,float,CObject**,int){return blocked?1:0;}
void AddToVelocity(CObject* o,Vector v){o->velocity=v;}
void AddToAngularVelocityOS(CObject* o,Vector v){o->spin=v;}
Vector GetAngularVelocityOS(CObject const* o){return o->spin;}
}
'''
CHECK = r'''
int main(){
    files["system"]={{"Asteroids",{{"file","field"},{"zone","zone"}}}};
    Section settings{"ServerDynamicAsteroids",{{"asteroid","rock"},{"count","10"},{"placement_radius","4500"},
        {"max_velocity","20"},{"max_angular_velocity","0.3"},{"seed","8"}}};
    Universe::excluded.radius=3000;
    // Exclusions follow the spawn section; a preloaded arch returns false from load().
    files["field"]={settings,{"Exclusion Zones",{{"exclusion","excluded"}}}};
    StarSystem system;LoadServerAsteroidFields(system);
    assert(system.objects.size()==20&&system.tracked.size()==20&&Archetype::arch.refs==0);
    std::vector<Vector> positions;
    for(auto* s:system.objects){
        positions.push_back(s->raw.pos);
        assert(length(s->raw.pos)>3050&&length(s->raw.pos)<=4500);
        assert(length(s->raw.velocity)<=20.001f&&length(s->raw.spin)<=.30001f);
    }
    system.clear();LoadServerAsteroidFields(system);
    for(size_t i=0;i<positions.size();++i)
        assert(length({positions[i].x-system.objects[i]->raw.pos.x,positions[i].y-system.objects[i]->raw.pos.y,positions[i].z-system.objects[i]->raw.pos.z})==0);
    system.clear();PhySys::blocked=true;LoadServerAsteroidFields(system);assert(system.objects.empty());PhySys::blocked=false;
    Universe::excluded.radius=10000;LoadServerAsteroidFields(system);assert(system.objects.empty());
    Archetype::arch.ObjectType=0x10;LoadServerAsteroidFields(system);assert(system.objects.empty());Archetype::arch.ObjectType=SERVER_ASTEROID_TYPE;
    Archetype::arch.loaded=false;Archetype::arch.fail=true;LoadServerAsteroidFields(system);assert(system.objects.empty()&&Archetype::arch.refs==0);Archetype::arch.fail=false;
    files["field"]={settings};LoadServerAsteroidFields(system);assert(system.objects.size()==20&&Archetype::arch.refs==0);system.clear();
    // Counts are bounded per section and per system. NaN uses finite defaults.
    settings.values={{"asteroid","rock"},{"count","999999"},{"placement_radius","nan"},{"max_velocity","nan"},{"max_angular_velocity","-5"}};
    files["field"]={settings,settings,settings,settings,settings};LoadServerAsteroidFields(system);
    assert(system.objects.size()==1024&&system.tracked.size()==1024);
    for(auto* s:system.objects)assert(length(s->raw.pos)<=3000&&length(s->raw.velocity)<=10.001f&&length(s->raw.spin)==0);
    system.clear();files["field"]={{"DynamicAsteroids",{{"asteroid","rock"},{"count","30"}}}};
    LoadServerAsteroidFields(system);assert(system.objects.empty());
    puts("PASS: production field loader, preloaded model, exclusions, blocked placement, deterministic seed, limits, legacy opt-out");

    settings.values={{"asteroid","rock"},{"count","30"},{"spawn_mode","player"},{"placement_radius","1000"},
        {"placement_offset","200"},{"despawn_radius","3000"},{"max_velocity","20"},{"seed","801"}};
    files["field"]={settings};LoadServerAsteroidFields(system);
    assert(system.objects.empty()); // no player -> no population on load
    UpdatePlayerFields(system,{},.5f);assert(system.objects.empty());
    // Two co-located players share the doubled 60-rock population. Creation is
    // bounded per tick, and ordinary fields now replenish every 0.25 seconds.
    std::vector<Vector> players{{4000,0,0},{4000,0,0}};
    UpdatePlayerFields(system,players,.5f);assert(system.objects.size()==24);
    UpdatePlayerFields(system,players,.1f);assert(system.objects.size()==24);
    UpdatePlayerFields(system,players,.1f);assert(system.objects.size()==24);
    UpdatePlayerFields(system,players,.05f);assert(system.objects.size()==48);
    UpdatePlayerFields(system,players,.25f);assert(system.objects.size()==60);
    auto& field=Populations.at(&system).fields[0];
    assert(field.rocks.size()==60);
    for(auto const& state:field.rocks){
        assert(DistanceSquared(state.pos,players[0])<=1000000);
        assert(DistanceSquared(state.pos,players[0])>=250*250);
    }
    auto first=field.rocks[0].id;
    objectsById[first]->raw.hp=1234;
    // One pilot leaving does not suspend the other pilot's population.
    players[0]={-4000,0,0};UpdatePlayerFields(system,players,.5f);
    assert(field.rocks[0].id==first&&!objectsById[first]->destroyed);
    UpdatePlayerFields(system,players,.5f);assert(field.rocks.size()==108);
    UpdatePlayerFields(system,players,.25f);assert(field.rocks.size()==120);
    // Actual death is remembered, and does not refill the hole immediately.
    auto killed=field.rocks[1].id;objectsById[killed]->destroy(1,0);
    size_t total=field.rocks.size();
    UpdatePlayerFields(system,players,.5f);
    assert(field.rocks[1].dead&&field.rocks[1].id==0&&field.rocks.size()==total);
    // A camera turn has no input into the population at all; stationary updates
    // preserve existing IDs, and a full leave/return restores HP and transform.
    UpdatePlayerFields(system,players,.5f);assert(field.rocks[0].id==first);
    Vector before=field.rocks[0].pos, velocity=field.rocks[0].velocity;
    UpdatePlayerFields(system,{},.5f);
    assert(field.rocks[0].id==0&&!field.rocks[0].dead&&objectsById[first]->destroyed);
    players={{4000,0,0}};
    UpdatePlayerFields(system,players,.5f);UpdatePlayerFields(system,players,.5f);
    auto restored=field.rocks[0].id;
    assert(restored&&restored!=first&&objectsById[restored]->raw.hp==1234);
    assert(DistanceSquared(objectsById[restored]->get_position(),before)==0);
    assert(DistanceSquared(objectsById[restored]->raw.velocity,velocity)==0);
    assert(field.rocks[1].dead&&field.rocks[1].id==0&&field.rocks.size()==total);
    UnloadServerAsteroidFields(system);assert(Populations.count(&system)==0);system.clear();
    // The public tick uses server ship positions and ignores ships in another world.
    LoadServerAsteroidFields(system);GameObject ship;ship.id=99999;ship.raw.pos={4000,0,0};
    objectsById[ship.id]=&ship;Players[1].ship_object_id=ship.id;
    SystemPlayerNode node;system.head.Next=&node;node.Next=&system.head;
    ship.raw.PhysicsSystemId=2;UpdateServerAsteroidFields(system,.5f);assert(system.objects.empty());
    ship.raw.PhysicsSystemId=1;UpdateServerAsteroidFields(system,.5f);assert(system.objects.size()==24);
    UnloadServerAsteroidFields(system);system.clear();system.head.Next=&system.head;objectsById.erase(ship.id);
    assert(Archetype::arch.refs==0);
    // Partially overlapping bubbles stay below the count in each neighbourhood.
    LoadServerAsteroidFields(system);players={{4000,0,0},{4100,0,0}};
    for(int tick=0;tick<5;++tick)UpdatePlayerFields(system,players,.5f);
    auto const& overlapping=Populations.at(&system).fields[0].rocks;
    assert(overlapping.size()>=60&&overlapping.size()<120);
    for(auto p:players){unsigned count=0;for(auto const& r:overlapping)if(DistanceSquared(p,r.pos)<=1000000)++count;assert(count<=60);}
    UnloadServerAsteroidFields(system);system.clear();
    LoadServerAsteroidFields(system);Populations.at(&system).fixedCount=1020;
    UpdatePlayerFields(system,players,.5f);UpdatePlayerFields(system,players,.5f);
    assert(system.objects.size()==4);UnloadServerAsteroidFields(system);system.clear();assert(Archetype::arch.refs==0);
    // The Sig8 density increase doubles three sections of 60 to 120, still budgeted over ticks.
    settings.values={{"asteroid","rock"},{"count","60"},{"spawn_mode","player"},{"placement_radius","1000"}};
    files["field"]={settings,settings,settings};LoadServerAsteroidFields(system);
    for(int tick=0;tick<15;++tick)UpdatePlayerFields(system,{{4000,0,0}},.5f);
    assert(system.objects.size()==360);
    for(auto const& f:Populations.at(&system).fields)assert(f.rocks.size()==120);
    UnloadServerAsteroidFields(system);system.clear();assert(Archetype::arch.refs==0);
    puts("PASS: player anchors, overlapping/separated players, spawn budget, death memory, camera independence, suspend/restore HP and velocity, unload");

    Universe::zone.radius=20000;
    settings.values={{"asteroid","rock"},{"count","12"},{"spawn_mode","forward"},{"placement_radius","3000"},
        {"placement_offset","2550"},{"despawn_radius","4500"},{"max_velocity","20"}};
    files["field"]={settings};LoadServerAsteroidFields(system);
    players={{0,0,0}};std::vector<Vector> velocities{{100,0,0}};std::vector<unsigned> ids{41};
    assert(ServerAsteroidViewRadius(system)==4500);
    for(unsigned tick=1;tick<=6;++tick){
        UpdatePlayerFields(system,players,.1f,velocities,ids);
        assert(system.objects.size()==tick*4);
    }
    auto& distant=Populations.at(&system).fields[0];
    for(auto const& r:distant.rocks){assert(length(r.pos)>=2600&&length(r.pos)<=3000&&r.pos.x>0);}
    // Nearby second player, reordered network IDs and changed view cannot duplicate the field.
    UpdatePlayerFields(system,{{0,0,0},{0,0,0}},.1f,{{100,0,0},{100,0,0}},{77,41});
    assert(system.objects.size()==24);
    for(auto const& r:distant.rocks)objectsById[r.id]->raw.pos={4000,0,0};
    for(int tick=0;tick<5;++tick)UpdatePlayerFields(system,players,.1f,velocities,ids);
    assert(system.objects.size()==24); // drifting away does not refill around a stationary ship
    players[0]={200,0,0};UpdatePlayerFields(system,players,.1f,velocities,ids);
    assert(system.objects.size()==28);
    for(size_t i=24;i<28;++i){
        auto const& r=distant.rocks[i];float d=std::sqrt(DistanceSquared(r.pos,players[0]));
        assert(d>=2600&&d<=3000&&r.pos.x>players[0].x);
    }
    UnloadServerAsteroidFields(system);system.clear();assert(ServerAsteroidViewRadius(system)==0);
    LoadServerAsteroidFields(system);PhySys::blocked=true;
    UpdatePlayerFields(system,players,.1f,velocities,ids);assert(system.objects.empty());
    PhySys::blocked=false;UpdatePlayerFields(system,players,.1f,velocities,ids);assert(system.objects.empty());
    players[0].x+=200;UpdatePlayerFields(system,players,.1f,velocities,ids);assert(system.objects.size()==4);
    UnloadServerAsteroidFields(system);system.clear();assert(Archetype::arch.refs==0);
    puts("PASS: far shell only, forward velocity, four-object batches, travel-triggered formation, stable player IDs, exclusion retry after travel, distant replication radius");
    // A translated, tilted ring must stay in its own plane, including initial drift.
    settings.values.push_back({"band_thickness","100"});files["field"]={settings};
    Universe::zone.pos={1000,2000,3000};
    Universe::zone.orientation.E[0][1]=.6f;Universe::zone.orientation.E[1][1]=.8f;
    LoadServerAsteroidFields(system);players={Universe::zone.pos};velocities={{0,0,100}};
    for(int tick=0;tick<20;++tick)UpdatePlayerFields(system,players,.1f,velocities,ids);
    assert(system.objects.size()==24);
    for(auto const& r:Populations.at(&system).fields[0].rocks){
        assert(std::fabs((r.pos.x-1000)*.6f+(r.pos.y-2000)*.8f)<=100.01f);
        assert(std::fabs(r.velocity.x*.6f+r.velocity.y*.8f)<.001f);
        assert(DistanceSquared(r.pos,players[0])<=3000*3000 && r.pos.z>3000);
    }
    UnloadServerAsteroidFields(system);system.clear();
    puts("PASS: translated tilted ring placement, shell distance, forward hemisphere and planar drift");
    // Use loaded Common loot records. A death rolls once, outside-zone deaths never drop.
    CmnAsteroid::LootableZoneEntry loot;
    loot.DynamicLootContainerId.Id=12;loot.DynamicLootCommodityId.Id=34;
    loot.DynamicLootCountMin=2;loot.DynamicLootCountMax=4;
    Universe::zone.loot=&loot;
    files["field"].push_back({"LootableZone",{}});
    LoadServerAsteroidFields(system);
    for(int tick=0;tick<20;++tick)UpdatePlayerFields(system,players,.1f,velocities,ids);
    auto& mined=Populations.at(&system).fields[0];
    assert(mined.rocks.size()==24 && system.drops.empty());
    unsigned minedId=mined.rocks[0].id;Vector death=mined.rocks[0].pos;
    OnServerAsteroidKilled(system,minedId,death);
    assert(system.drops.size()==1 && mined.rocks[0].dead && !mined.rocks[0].id);
    assert(system.drops[0].container==12 && system.drops[0].commodity==34);
    assert(system.drops[0].count>=2 && system.drops[0].count<=4);
    assert(DistanceSquared(system.drops[0].pos,death)==0);
    OnServerAsteroidKilled(system,minedId,death);assert(system.drops.size()==1);
    OnServerAsteroidKilled(system,mined.rocks[1].id,{999999,0,0});assert(system.drops.size()==1);
    Universe::zone.loot=nullptr;
    OnServerAsteroidKilled(system,mined.rocks[2].id,death);assert(system.drops.size()==1);
    UnloadServerAsteroidFields(system);system.clear();
    // A named loot zone takes precedence at its own position, not at the camera.
    Universe::excluded.pos=Universe::zone.pos;Universe::excluded.radius=10000;Universe::excluded.loot=&loot;
    files["field"].back()={"LootableZone",{{"zone","excluded"}}};
    LoadServerAsteroidFields(system);
    for(int tick=0;tick<20;++tick)UpdatePlayerFields(system,players,.1f,velocities,ids);
    auto& named=Populations.at(&system).fields[0];assert(named.rocks.size()==24);
    OnServerAsteroidKilled(system,named.rocks[0].id,named.rocks[0].pos);assert(system.drops.size()==2);
    // Suspension is not a death and must never roll loot.
    UpdatePlayerFields(system,{},.1f);assert(system.drops.size()==2);
    UnloadServerAsteroidFields(system);system.clear();
    puts("PASS: server mining, authored container/commodity/quantity, one roll per death, named/outside zones, no loot on suspension");
}
'''


def main():
    source_text = (ROOT/'src/Server/server_asteroid_fields.cpp').read_text()
    assert 'f.count = (std::min)(512, f.count * 2);' in source_text
    assert 'forwardMode ? 0.05f : 0.25f' in source_text
    OUT.mkdir(parents=True, exist_ok=True)
    source = '\n'.join(line for line in source_text.splitlines() if not line.startswith('#include'))
    (OUT/'check.cpp').write_text(STUB+source+CHECK)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include', ROOT/'src/include'] +
                              [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')])
    env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                    '/wd4996', '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'check.exe')], cwd=OUT, check=True)


if __name__ == '__main__':
    main()
