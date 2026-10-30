"""Compile production gravity, ship callback and IVP impulse commit; no game writes."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/gravity_check'


def function(path, signature):
    source = (ROOT / path).read_text(encoding='utf-8-sig')
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


STUB = r'''
#include <cassert>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <map>
#include <string>
#include <vector>
#include "gravity_field.h"
#include "common_gravity.h"
class INI_Reader {
public:
    std::vector<std::pair<std::string,std::string>> lines;
    int index=-1;
    bool read_value(){return ++index<static_cast<int>(lines.size());}
    bool is_value(char const* key){return _stricmp(lines[index].first.c_str(),key)==0;}
    bool get_value_bool(unsigned){return _stricmp(lines[index].second.c_str(),"true")==0 || lines[index].second=="1";}
    float get_value_float(unsigned){return std::strtof(lines[index].second.c_str(),nullptr);}
    int get_value_int(unsigned){return std::atoi(lines[index].second.c_str());}
    char const* get_value_string(unsigned=0){return lines[index].second.c_str();}
};
unsigned CreateID(char const* text){unsigned h=0;while(*text)h=h*31+static_cast<unsigned char>(*text++);return h;}
struct Vector {float x=0,y=0,z=0;};
struct ID_String {unsigned Id=0;};
namespace Universe {
struct ISystem {unsigned id=1;virtual ~ISystem(){};virtual unsigned GetId()const{return id;}};
struct IBase {int GetStridName(){return 0;}void SetSpaceObjectId(unsigned){}void SetSpaceObjectVisit(unsigned char){}};
struct FSystemConnection {unsigned GotoSystemId,ObjectId;ID_String Object;Vector Pos;unsigned char Visit;unsigned GateType;};
constexpr unsigned SolarGateNone=0;
}
namespace CmnUniverse {
struct SYSTEM:Universe::ISystem {
    std::map<unsigned,GravityField::Settings> GravityObjects;
    std::vector<Universe::FSystemConnection> Connections;
};
}
using CmnUniverse::SYSTEM;
struct IObjDB {Universe::ISystem* system;Universe::ISystem* GetZoneDb(){return system;}};
struct BASE:Universe::IBase {};
struct FUniverseLoadCarry {unsigned ObjectNickname=0;};
std::map<unsigned,BASE> GBases;
std::map<unsigned,unsigned> GGateSystems;
unsigned LookupObjectBaseId(char const* text){return CreateID(text);}
bool IdIsValid(unsigned id){return id!=0;}
namespace Archetype {struct Solar {unsigned ObjectType=0;};Solar* GetSolarByName(ID_String const&){return nullptr;}}
unsigned SolarGateTypeFromObjectType(unsigned t){return t;}
#define FDUMP(...) ((void)0)
struct Point {float k[4]={};};
class IVP_Core {
public:
    void* Environment=nullptr;unsigned Flags=0;float InvMass=.01f;
    struct {Point vv;} MWorldFCore;
    Vector Speed,SpeedChange,RotSpeed,RotSpeedChange;
    void commit_speed_changes();
    void damp_velocities(float){} // This fixture has zero damping.
};
class IVP_Event_Sim {public:float delta_time=.025f;void* environment=nullptr;};
template<class T> class IVP_U_Vector {public:unsigned short n_elems=0;T** elems=nullptr;};
struct Body {IVP_Core* core=nullptr;};
struct CEqObj {
    IObjDB* ObjectDb=nullptr;Body* BodyPtr=nullptr;unsigned PhysicsSystemId=1,Id=0;
    Vector WorldPosition;float health=1;
    float get_hit_pts()const{return health;}
};
struct CSolar:CEqObj {ID_String Nickname;};
struct CShip:CEqObj {
    void* GolemController=nullptr;bool bUsingTradelane=false;
    void do_simulation_controller(IVP_Event_Sim*,IVP_U_Vector<IVP_Core>*);
};
namespace Archetype {
struct Root {};
struct Equipment:Root {int kind=1;int get_class_type()const{return kind;}};
}
constexpr unsigned EquipTypeCargo=0x10000,EquipTypeGravityDevice=0x2000000, EquipTypeRepairDroid=0x200000;
class CEquip {
public:
    CEqObj* owner=nullptr;Archetype::Equipment* arch=nullptr;
    unsigned type=EquipTypeGravityDevice;unsigned short id=1;
    bool active=false,destroyed=false,disabled=false;float health=1;
    CEqObj* GetOwner()const{return owner;}unsigned short GetID()const{return id;}
    unsigned GetType()const{return type;}auto EquipArch()const{return arch;}
    bool IsFunctioning()const{return active&&!destroyed&&!disabled;}
    float GetHitPoints()const{return health;}void Activate(bool on){active=on;}
};
class IVP_Standard_Gravity_Controller {
public:Vector grav_vec;
    void do_simulation_controller(IVP_Event_Sim*,IVP_U_Vector<IVP_Core>*);
};
'''

CHECK = r'''
bool near(double a,double b,double epsilon=.0001){return std::fabs(a-b)<epsilon;}
int main(int argc,char** argv){
    std::string mode=argc>1?argv[1]:"normal";
    SYSTEM system,otherSystem;otherSystem.id=2;
    // SP keeps solars on the server database but reconnects the shared player
    // ship to the client database. Both databases reference the same system.
    IObjDB db{&system},clientDb{&system},otherDb{&otherSystem};int environment=0;
    INI_Reader reader;
    if(mode!="absent")reader.lines.push_back({"gravity",mode=="disabled"?"false":"true"});
    reader.lines.push_back({"nickname","om13_bh"}); // settings preceding nickname are supported
    if(mode=="invalid")for(auto key:{"radius","reference_radius","acceleration","softening","max_acceleration","edge_fraction"})
        reader.lines.push_back({std::string("gravity_")+key,"nan"});
    if(mode=="zero")reader.lines.push_back({"gravity_acceleration","0"});
    if(mode=="clamp"){
        reader.lines.push_back({"gravity_radius","-1"});reader.lines.push_back({"gravity_reference_radius","0"});
        reader.lines.push_back({"gravity_softening","0"});reader.lines.push_back({"gravity_edge_fraction","0"});
        reader.lines.push_back({"gravity_max_acceleration","-10"});
    }
    FUniverseLoadCarry carry;
    ReadSystemFileObject(reader,system,carry);
    unsigned id=CreateID("om13_bh");
    bool enabled=mode!="absent" && mode!="disabled";
    assert(system.GravityObjects.count(id)==(enabled?1u:0u));
    if(mode=="clamp"){
        auto const& c=system.GravityObjects.at(id);
        assert(c.radius==1 && c.referenceRadius==1 && c.softening==1);
        assert(c.edgeFraction==.001 && c.maxAcceleration==0);
        puts("PASS: native per-object numeric limits");return 0;
    }
    CSolar source;source.Id=id;source.ObjectDb=&db;source.Nickname.Id=id;
    CmnGravity::RegisterSolar(&source);CmnGravity::RegisterSolar(&source);
    assert(Sources().size()==(enabled?1u:0u));
    IVP_Core core;core.Environment=&environment;core.MWorldFCore.vv.k[0]=5000;
    Body body{&core};CShip ship;ship.ObjectDb=&clientDb;ship.BodyPtr=&body;
    IVP_Core* pointers[]={&core,&core};IVP_U_Vector<IVP_Core> cores;cores.n_elems=1;cores.elems=pointers;
    IVP_Event_Sim event;event.environment=&environment;
    ship.do_simulation_controller(&event,&cores);
    if(mode=="absent" || mode=="disabled" || mode=="zero"){
        assert(core.SpeedChange.x==0);puts("PASS: disabled/zero field");return 0;
    }
    assert(near(core.SpeedChange.x,-1.5) && core.SpeedChange.y==0 && core.SpeedChange.z==0);
    // Production IVP gravity/commit consumes the pending impulse exactly once,
    // alongside an independent engine impulse; orientation is unaffected.
    core.SpeedChange.y=2;IVP_Standard_Gravity_Controller standard;
    standard.do_simulation_controller(&event,&cores);
    assert(near(core.Speed.x,-1.5) && core.Speed.y==2 && core.SpeedChange.x==0);
    standard.do_simulation_controller(&event,&cores);assert(near(core.Speed.x,-1.5));
    auto sample=[&]{core.SpeedChange={};ship.do_simulation_controller(&event,&cores);return core.SpeedChange.x;};
    ship.ObjectDb=&db;assert(near(sample(),-1.5)); // authoritative server NPC
    ship.ObjectDb=&clientDb;assert(near(sample(),-1.5)); // SP player, same world / different DB
    for(float inverseMass:{1.f,.01f,.00001f}){core.InvMass=inverseMass;assert(near(sample(),-1.5));}
    cores.n_elems=2;assert(near(sample(),-1.5));cores.n_elems=1;
    ship.GolemController=&db;assert(sample()==0);ship.GolemController=nullptr;
    ship.bUsingTradelane=true;assert(sample()==0);ship.bUsingTradelane=false;
    core.Flags=0x100;assert(sample()==0);core.Flags=0x200;assert(sample()==0);core.Flags=0;
    core.InvMass=0;assert(sample()==0);core.InvMass=.01f;
    ship.PhysicsSystemId=2;assert(sample()==0);ship.PhysicsSystemId=1;
    ship.ObjectDb=&otherDb;assert(sample()==0);ship.ObjectDb=&clientDb;
    event.environment=&otherDb;assert(sample()==0);event.environment=&environment;
    cores.n_elems=0;assert(sample()==0);cores.n_elems=1;
    ship.BodyPtr=nullptr;assert(sample()==0);ship.BodyPtr=&body;
    for(float dt:{0.f,-1.f,std::numeric_limits<float>::quiet_NaN()}){event.delta_time=dt;assert(sample()==0);}
    event.delta_time=.025f;
    CmnGravity::UnregisterSolar(&source);assert(sample()==0);
    CmnGravity::RegisterSolar(&source);assert(near(sample(),-1.5));
    // Removal/reinitialisation and an unrelated archetype cannot leave a stale source.
    source.Nickname.Id=123;CmnGravity::RegisterSolar(&source);assert(sample()==0);
    source.Nickname.Id=0;CmnGravity::RegisterSolar(&source);assert(near(sample(),-1.5)); // MP Id fallback
    source.Nickname.Id=id;
    // Same object nickname in a different system does not inherit settings.
    CSolar unconfigured=source;unconfigured.ObjectDb=&otherDb;
    CmnGravity::RegisterSolar(&unconfigured);assert(Sources().size()==1);
    otherSystem.GravityObjects[id]=system.GravityObjects.at(id);
    CSolar second=source;second.ObjectDb=&otherDb;CmnGravity::RegisterSolar(&second);
    assert(near(sample(),-1.5)); // source in a different system
    second.ObjectDb=&db;assert(near(sample(),-3)); // two real sources sum
    // Distinct object settings coexist, including different field strengths.
    unsigned secondId=CreateID("other_hole");
    INI_Reader secondReader;secondReader.lines={{"nickname","other_hole"},{"gravity_acceleration","30"},{"gravity","true"}};
    ReadSystemFileObject(secondReader,system,carry);
    second.Id=secondId;second.Nickname.Id=secondId;CmnGravity::RegisterSolar(&second);
    assert(near(sample(),-2.25));
    second.Id=id;second.Nickname.Id=id;CmnGravity::RegisterSolar(&second);
    second.WorldPosition.x=10000;assert(near(sample(),0)); // equal opposing fields
    second.WorldPosition.x=0;core.MWorldFCore.vv.k[0]=1500;
    assert(near(sample(),-2*system.GravityObjects.at(id).maxAcceleration*event.delta_time));
    CmnGravity::UnregisterSolar(&second);
    GravityField::Settings s;
    using GravityField::Sample;using GravityField::Length;
    assert(near(Length(Sample(s,{},{5000,0,0})),60));
    assert(Length(Sample(s,{},{10000,0,0}))<16);
    assert(Length(Sample(s,{},{20000,0,0}))==0);
    assert(Length(Sample(s,{},{21000,0,0}))==0);
    assert(Length(Sample(s,{},{19999,0,0}))<.00001);
    assert(Length(Sample(s,{},{0,0,0}))==0);
    assert(Length(Sample(s,{},{1e-10,0,0}))<1e-6);
    assert(Length(Sample(s,{},{std::numeric_limits<double>::infinity(),0,0}))==0);
    for(double r=1;r<20000;r+=17){
        auto a=Sample(s,{},{r,0,0});assert(a.x<=0 && a.y==0 && a.z==0);
        assert(GravityField::Finite(a) && Length(a)<=s.maxAcceleration+.000001);
        auto b=Sample(s,{100,200,300},{100,200+r,300});assert(near(a.x,b.y));
    }
    // Same fixed physics ticks grouped into 30/60/144 render frames: identical
    // trajectories. No engine callback is involved in the motion.
    auto trajectory=[&](int fps){
        core.Speed={};core.SpeedChange={};core.MWorldFCore.vv.k[0]=8000;
        double time=0;int ticks=0;
        for(int frame=0;frame<fps*10;++frame){
            time+=1.0/fps;
            while(time+1e-9>=.025){
                ship.do_simulation_controller(&event,&cores);
                standard.do_simulation_controller(&event,&cores);
                core.MWorldFCore.vv.k[0]+=core.Speed.x*.025f;
                time-=.025;++ticks;
            }
        }
        assert(ticks==400 && core.MWorldFCore.vv.k[0]<8000);
        return core.MWorldFCore.vv.k[0];
    };
    float p30=trajectory(30);assert(p30==trajectory(60) && p30==trajectory(144));
    CmnGravity::UnregisterSolar(&source);assert(Sources().empty());
    // A later object/disabled entry cannot inherit the previous object's field.
    INI_Reader disabled;disabled.lines={{"nickname","om13_bh"},{"gravity","false"}};
    ReadSystemFileObject(disabled,system,carry);CmnGravity::RegisterSolar(&source);assert(Sources().empty());
    INI_Reader unnamed;unnamed.lines={{"gravity","true"}};
    ReadSystemFileObject(unnamed,system,carry);assert(!system.GravityObjects.count(0));
    INI_Reader plain;plain.lines={{"nickname","plain_solar"}};
    ReadSystemFileObject(plain,system,carry);assert(!system.GravityObjects.count(CreateID("plain_solar")));
    SYSTEM copied=system;assert(copied.GravityObjects.at(secondId).acceleration==30);
    system.GravityObjects.clear();assert(copied.GravityObjects.at(secondId).acceleration==30);
    puts("PASS: native Object INI loading, key order, individual fields, MP object ID and system isolation");
    puts("PASS: field falloff/cap/centre, mass independence, fixed-step engine-off motion, IVP commit, remote/lane/static exclusions, systems and source lifecycle");
}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    production=(ROOT/'src/Common/common_gravity.cpp').read_text()
    production='\n'.join(line for line in production.splitlines() if not line.startswith('#include'))
    code=STUB+production
    code+=function('src/Common/common_universe.cpp','void ReadSystemFileObject(')
    code+=function('src/Common/common_cship.cpp','void CShip::do_simulation_controller(')
    code+=function('src/IVP/ivp_physics/ivp_core.cpp','void IVP_Core::commit_speed_changes(')
    code+=function('src/IVP/ivp_physics/ivp_environment.cpp','void IVP_Standard_Gravity_Controller::do_simulation_controller(')
    # Also verify that real solar lifecycle entry points invoke the registry.
    assert 'CmnGravity::RegisterSolar(this)' in function('src/Common/common_csolar.cpp','void CSolar::init(')
    assert 'CmnGravity::UnregisterSolar(this)' in function('src/Common/common_csolar.cpp','CSolar::~CSolar(')
    assert 'CmnGravity::RegisterEquipment(Equip)' in function('src/Common/common_cequip.cpp','bool CEquipManager::AddNewEquipment(')
    assert 'CmnGravity::UnregisterEquipment(this)' in function('src/Common/common_cequip.cpp','CEquip::~CEquip(')
    (OUT/'check.cpp').write_text(code+CHECK)
    vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
    env=dict(os.environ)
    env['INCLUDE']=';'.join(str(p) for p in [vc/'include',ROOT/'src/Common']+
                            [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
    env['LIB']=';'.join(str(p) for p in [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc',
                    '/MT','check.cpp','/Fecheck.exe'],cwd=OUT,env=env,check=True)
    for mode in ('normal','absent','disabled','invalid','zero','clamp'):
        subprocess.run([str(OUT/'check.exe'),mode],cwd=OUT,check=True)


if __name__=='__main__':
    main()
