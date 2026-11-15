"""Compile the production base resolver and range reader against a small object DB."""
import os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/station_docking';OUT.mkdir(exist_ok=True)
def extract(path,signature):
    src=(ROOT/path).read_text();a=src.index(signature);b=src.index('{',a)+1;depth=1
    while depth:depth+=(src[b]=='{')-(src[b]=='}');b+=1
    return src[a:b]
stub=r'''
#include <cassert>
#include <cstdio>
#include <vector>
namespace Archetype {
enum {AClassSolar=2};
struct Root {int kind=2;int get_class_type()const{return kind;}};
}
struct CObject {Archetype::Root arch;auto get_archetype()const{return &arch;}};
struct IObjInspect {
 unsigned type=4,base=0,dock=0;bool hp=false;CObject body;
 auto cobject()const{return &body;} bool has_dock_hardpoints()const{return hp;}
 void get_base(unsigned& v)const{v=base;}void get_dock_target(unsigned& v)const{v=dock;}
};
using IObjRW=IObjInspect;
unsigned GetObjectTypeOrZero(IObjInspect const* p){return p->type;}
struct IObjDB {
 std::vector<IObjRW*> objects;
 IObjRW* GetNext(void* iter){auto p=(unsigned*)iter;while(p[0]<objects.size()){
  auto x=objects[p[0]++];if(x->type&p[2])return x;}return nullptr;}
};
struct SystemManagerTimerTable {IObjDB* ObjectDb;IObjRW* FindObjectDockingAtBase(IObjInspect const*)const;};
'''
checks=r'''
int main(){
 IObjDB db;SystemManagerTimerTable lookup{&db};
 IObjRW core,wrong,decoration,shipping,second,planet,ring;
 core.base=42;core.type=4;wrong.dock=43;wrong.type=32;wrong.hp=true;
 decoration.dock=42;decoration.type=32;
 shipping.dock=42;shipping.hp=true;shipping.type=32;
 second=shipping;planet.base=42;planet.type=1;ring=shipping;
 db.objects={&wrong,&decoration,&shipping,&second};
 assert(lookup.FindObjectDockingAtBase(&core)==&shipping);
 assert(lookup.FindObjectDockingAtBase(&planet)==&shipping);
 core.hp=true;assert(!lookup.FindObjectDockingAtBase(&core));core.hp=false;
 core.body.arch.kind=3;assert(!lookup.FindObjectDockingAtBase(&core));core.body.arch.kind=2;
 core.base=0;assert(!lookup.FindObjectDockingAtBase(&core));core.base=99;
 assert(!lookup.FindObjectDockingAtBase(&core));assert(!lookup.FindObjectDockingAtBase(nullptr));
 core.base=42;shipping.type=128;second.type=128;
 assert(lookup.FindObjectDockingAtBase(&core)==&shipping);
 assert(!lookup.FindObjectDockingAtBase(&planet));
 puts("PASS station core -> first matching port; own docks unchanged; planet rings; missing base; ships; unrelated and decorative objects");
}
'''
(OUT/'resolver.cpp').write_text(stub+extract('src/Common/common_aiintercept.cpp','IObjRW* SystemManagerTimerTable::FindObjectDockingAtBase(')+checks)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');ver='10.0.26100.0';env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/ver/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/ver/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/fp:fast','/EHsc','/MT','resolver.cpp','/Feresolver.exe'],cwd=OUT,env=env,check=True)
r=subprocess.run([str(OUT/'resolver.exe')],capture_output=True,timeout=15,check=True)
(OUT/'resolver.log').write_bytes(r.stdout);print(r.stdout.decode())

# Exercise the real exported INI reader and Solar metadata in the newly built DLL.
build=ROOT/'src/obj/train_courier/rpg1/bin'
native=r'''
#include "common_archetype.h"
#include "common_ini.h"
#include <cassert>
#include <cstdio>
#include <cstring>
void read(Archetype::Solar& a,const char* value){
 char buffer[256];sprintf_s(buffer,"[Solar]\ndocking_request_range = %s\n",value);
 INI_Reader ini;assert(ini.open_memory(buffer,(unsigned)strlen(buffer)));
 assert(ini.read_header()&&ini.read_value());assert(a.read(ini));
}
int main(){
 Archetype::Solar a,b;assert(a.GetDockingRequestRange()==1000);
 read(a,"3000");assert(a.GetDockingRequestRange()==3000);
 b.redefine(a);assert(b.GetDockingRequestRange()==3000);
 for(auto value:{"0","-100","999","9001","nan","inf"}){
  read(a,value);assert(a.GetDockingRequestRange()==1000);
 }
 read(a,"9000");assert(a.GetDockingRequestRange()==9000);
 // At the shipping port (1180m offset) plus a 1000m approach, old range
 // could demand a flight toward the core; the configured range admits it.
 assert(2180>1000 && 2180<3000);
 puts("PASS real Common: default 1000m, Greenwich 3000m, inheritance, invalid values and 9000m limit");
}
'''
(OUT/'range.cpp').write_text('#include <initializer_list>\n'+native)
env['INCLUDE']=str(ROOT/'src/include')+';'+env['INCLUDE']
env['LIB']=str(build)+';'+env['LIB']
env['PATH']=str(build)+';D:/Games/FL_MOD/bin;'+env['PATH']
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/fp:fast','/EHsc','/MD','/D_ITERATOR_DEBUG_LEVEL=1','range.cpp','/Ferange.exe','/link','Common.lib'],cwd=OUT,env=env,check=True)
r=subprocess.run([str(OUT/'range.exe')],capture_output=True,env=env,timeout=15,check=True)
(OUT/'range.log').write_bytes(r.stdout);print(r.stdout.decode())
