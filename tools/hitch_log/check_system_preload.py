"""Exercise production system-field preload: deduplication, failures and reference balance."""
import os
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/physics'))
from check_gravity import function

code=r'''
#include <algorithm>
#include <cassert>
#include <cstring>
#include <list>
#include <map>
#include <string>
#include <vector>
#include <cstdio>
struct RuntimeHitchScope{RuntimeHitchScope(char const*,char const*){}};
struct ID_String{unsigned Id=0;};
unsigned CreateID(char const* n){unsigned h=0;while(*n)h=h*31+*n++;return h;}
struct Section{std::string name;std::vector<std::pair<std::string,std::string>> values;};
std::map<std::string,std::vector<Section>> files;
struct INI_Reader{
 std::vector<Section>* data=nullptr;int header=-1,value=-1;
 bool open(char const* p,bool){auto i=files.find(p);if(i==files.end())return false;data=&i->second;return true;}
 bool read_header(){value=-1;return ++header<int(data->size());}
 bool is_header(char const* n){return (*data)[header].name==n;}
 bool read_value(){return ++value<int((*data)[header].values.size());}
 bool is_value(char const* n){return (*data)[header].values[value].first==n;}
 char const* get_value_string(){return (*data)[header].values[value].second.c_str();}
 int get_value_int(int){return std::stoi(get_value_string());}
};
namespace DALib{void* Data=nullptr;}
void GetFileSysPath(char* out,char const* in,void*){strcpy(out,in);}
namespace Archetype{
struct Companion{int calls=0;void Load(int){++calls;}};
struct Root{int refs=0;bool loaded=true;Companion companion;Archetype::Companion* Companion=&companion;
 bool load(){++refs;return false;}bool is_loaded(){return loaded;}void Release(){--refs;}};
std::map<unsigned,Root> roots;
Root* GetSolarByName(ID_String n){auto i=roots.find(n.Id);return i==roots.end()?nullptr:&i->second;}
}
std::list<Archetype::Root*> G_PreloadArchetypes;
'''
code+=function('src/freelancer/Client/star_sys.cpp','void PreloadFieldObjectArchetypes(')
code+=r'''
int main(){
 auto& a=Archetype::roots[CreateID("a")];auto& bad=Archetype::roots[CreateID("bad")];bad.loaded=false;
 files["field"]={{"ServerDynamicAsteroids",{{"count","60"},{"asteroid","a"}}},
 {"ServerDynamicAsteroids",{{"asteroid","a"},{"count","60"}}},
 {"ServerDynamicAsteroids",{{"asteroid","bad"},{"count","60"}}},
 {"ServerDynamicAsteroids",{{"asteroid","missing"},{"count","1"}}},
 {"DynamicAsteroids",{{"asteroid","a"},{"count","60"}}}};
 for(int i=0;i<5;++i)PreloadFieldObjectArchetypes("field");
 assert(a.refs==1&&a.companion.calls==1&&bad.refs==0&&G_PreloadArchetypes.size()==1);
 for(auto* p:G_PreloadArchetypes)p->Release();G_PreloadArchetypes.clear();assert(a.refs==0);
 files["zero"]={{"ServerDynamicAsteroids",{{"asteroid","a"},{"count","0"}}}};
 PreloadFieldObjectArchetypes("zero");PreloadFieldObjectArchetypes("missing");assert(a.refs==0);
 PreloadFieldObjectArchetypes("field");assert(a.refs==1&&a.companion.calls==2);
 puts("PASS: all-system field preloading, five-field deduplication, preloaded root, disabled/invalid archetypes, failure release and system reload");
}
'''
out=root/'src/obj/system_preload_check';out.mkdir(parents=True,exist_ok=True)
(out/'check.cpp').write_text(code)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(str(p) for p in [vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB']=';'.join(str(p) for p in [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/wd4996','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,check=True)
