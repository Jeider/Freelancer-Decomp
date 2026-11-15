"""Run the production zone selector against synthetic overlapping zones."""
from pathlib import Path
import os
import subprocess

root=Path(__file__).resolve().parents[2]
out=root/'src/obj/nebula_objects_check'
out.mkdir(parents=True,exist_ok=True)
source=(root/'src/freelancer/Client/nebula_volume.cpp').read_text()
selector=source.split('bool NebulaVolume::SimplifyObjectsAt',1)[1].split('bool NebulaVolume::ShadowsDisabledAt',1)[0]
scene=(root/'src/freelancer/Client/space_scene_obj_draw.cpp').read_text()
distance=scene.split('    bool NativeNebulaObject(',1)[1].split('    // -1 no shadow',1)[0]
stub=r'''
#include <cmath>
#include <cassert>
#include <vector>
#include <cstdio>
struct Vector {float x,y,z;};
struct Zone {float center,radius;double GetImmersion(Vector p)const{return 1-std::fabs(p.x-center)/radius;}};
struct Exclusion {Zone* ZonePtr;};
struct Manager {std::vector<Exclusion*> zones;};
struct Nebula {int FlagLoaded;Zone* Zone;Manager* ExclusionMgr;};
struct Entry {Nebula* Nebula;void* RingOwner;};
std::vector<Entry> GNebulae;
struct FNebulaVolumeExclusionAccess {
 static int Count(Manager const* m){return int(m->zones.size());}
 static Exclusion const* At(Manager const*m,int i){return m->zones[i];}
};
namespace NebulaVolume {bool SimplifyObjectsAt(float const*,bool);}
bool G_SimplifyNebulaObjects=true;
struct ICamera {float Eye[3]={};float const* GetPosition(){return Eye;}};
struct FClientGameobj {
 int ManagerKind=1,Id=2;Vector Center={};float Radius=20;
 int get_id(){return Id;}float Slot178(Vector& out){out=Center;return Radius;}
};
bool IsPlayerShipId(int id){return id==1;}
int PortConfigInt(char const*,char const*,int value){return value;}
'''
tests=r'''
int main(){
 ICamera camera;FClientGameobj ship;
 for(int kind:{1,9}) {
  ship.ManagerKind=kind;ship.Center.x=320;assert(!NativeNebulaObject(&ship,&camera));
  ship.Center.x=520;assert(!NativeNebulaObject(&ship,&camera));
  ship.Center.x=521;assert(NativeNebulaObject(&ship,&camera));
 }
 ship.ManagerKind=1;ship.Id=1;assert(!NativeNebulaObject(&ship,&camera));ship.Id=2;
 G_SimplifyNebulaObjects=false;assert(!NativeNebulaObject(&ship,&camera));G_SimplifyNebulaObjects=true;
 ship.ManagerKind=2;ship.Center.x=4020;assert(!NativeNebulaObject(&ship,&camera));
 ship.Center.x=4021;assert(NativeNebulaObject(&ship,&camera));
 assert(!NativeNebulaObject(nullptr,&camera));
 puts("PASS: close ships/rocks, 500m hull boundary, player, open space, original static range");
 Zone zone{0,100},clear{0,10};Exclusion exclusion{&clear};Manager manager{{&exclusion}};
 Nebula cloud{1,&zone,&manager};GNebulae={{&cloud,nullptr}};
 float p[]={50,0,0};assert(NebulaVolume::SimplifyObjectsAt(p,false));
 p[0]=0;assert(!NebulaVolume::SimplifyObjectsAt(p,true));
 p[0]=9.9f;assert(!NebulaVolume::SimplifyObjectsAt(p,true));
 p[0]=85;assert(!NebulaVolume::SimplifyObjectsAt(p,false));assert(NebulaVolume::SimplifyObjectsAt(p,true));
 p[0]=95;assert(!NebulaVolume::SimplifyObjectsAt(p,true));
 p[0]=110;assert(!NebulaVolume::SimplifyObjectsAt(p,false));
 Nebula second{1,&zone,nullptr};GNebulae.insert(GNebulae.begin(),{&second,nullptr});
 p[0]=0;assert(!NebulaVolume::SimplifyObjectsAt(p,true));
 GNebulae={{&cloud,&cloud}};p[0]=50;assert(!NebulaVolume::SimplifyObjectsAt(p,false));
 GNebulae={{&cloud,nullptr}};cloud.FlagLoaded=0;assert(!NebulaVolume::SimplifyObjectsAt(p,false));
 cloud.FlagLoaded=1;p[0]=NAN;assert(!NebulaVolume::SimplifyObjectsAt(p,true));
 assert(!NebulaVolume::SimplifyObjectsAt(nullptr,true));
 GNebulae.clear();p[0]=50;assert(!NebulaVolume::SimplifyObjectsAt(p,true));
 puts("PASS: fog, exclusion edge, overlapping zones, outer hysteresis, rings, unload and invalid camera");
}
'''
(out/'check.cpp').write_text(stub+'bool NebulaVolume::SimplifyObjectsAt'+selector+'bool NativeNebulaObject('+distance+tests)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,check=True)
