"""Exercise production registration, permissions and exclusion classification without a GPU."""
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[2]
out=root/'src/obj/nebula_control';out.mkdir(parents=True,exist_ok=True)
source=(root/'src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
def block(start,struct=False):
    a=source.index(start);b=source.index('{',a);depth=1;i=b+1
    while depth:
        depth+=(source[i]=='{')-(source[i]=='}');i+=1
    return source[a:i]+(';' if struct else '')+'\n'

prefix=r'''
#include <cassert>
#include <cstring>
#include <cstdio>
#include <vector>
#include <cmath>
#include <limits>
#include <string>
struct Vector{float x,y,z;};
struct Zone{Vector Center{0,0,0};float Radius=10;
 double GetImmersion(Vector p)const{float x=p.x-Center.x,y=p.y-Center.y,z=p.z-Center.z;return x*x+y*y+z*z<Radius*Radius?1:0;}};
struct Exclusion{Zone* ZonePtr;};
struct Manager{std::vector<Exclusion*> Zones;};
struct FNebulaEffect{Manager* ExclusionMgr=nullptr;::Zone* Zone=nullptr;int FlagLoaded=1;};
struct FNebulaVolumeExclusionAccess{
 static int Count(Manager const* m){return (int)m->Zones.size();}
 static Exclusion const* At(Manager const* m,int i){return m->Zones[i];}};
struct FNebulaVolumeSettings{float Enabled=1;};
struct FNebulaOverride{char File[64]={},Style[32]={};FNebulaVolumeSettings Settings;};
FNebulaVolumeSettings GSettings;
std::vector<FNebulaOverride> GOverrides,GStyles;
void ApplyPatch(FNebulaVolumeSettings* s,FNebulaOverride const& p){*s=p.Settings;}
void DetectNebulaStyle(char* p,size_t size,const char*){strcpy_s(p,size,"edge");}
void BaseName(char* p,size_t size,const char* file){strcpy_s(p,size,file);}
namespace NebulaVolume{void RegisterNebula(FNebulaEffect*,const char*,bool=true);bool ShadowsDisabledAt(float const*);}
// Minimal INI adapter: the key/section decisions below come from production ReadNebulaShadows.
const int MAX_PATH=260;
namespace DALib{const int Data=0;}
void GetFileSysPath(char* out,const char* file,int){strcpy_s(out,MAX_PATH,file);}
struct IniSection{const char* Header;std::vector<std::pair<const char*,bool>> Values;};
std::vector<IniSection> IniSections;
struct INI_Reader{
 int H=-1,V=-1;
 bool open(const char*,bool){return true;}
 bool read_header(){V=-1;return ++H<(int)IniSections.size();}
 bool read_value(){return ++V<(int)IniSections[H].Values.size();}
 bool is_header(const char* s){return !_stricmp(s,IniSections[H].Header);}
 bool is_value(const char* s){return !_stricmp(s,IniSections[H].Values[V].first);}
 bool get_value_bool(unsigned){return IniSections[H].Values[V].second;}
};
'''
tests=r'''
int main(){
 FNebulaEffect a,b;NebulaVolume::RegisterNebula(&a,"shared.ini",false);NebulaVolume::RegisterNebula(&b,"shared.ini");
 FNebulaOverride forced;strcpy_s(forced.File,"shared.ini");forced.Settings.Enabled=1;GOverrides.push_back(forced);
 FNebulaOverride style;strcpy_s(style.File,"edge");style.Settings.Enabled=1;GStyles.push_back(style);
 assert(SettingsFor(&a).Enabled==0 && SettingsFor(&b).Enabled==1);
 puts("PASS per-instance false cannot be re-enabled by style or existing override; omitted flag defaults true");
 Zone inside,outside;outside.Center.x=100;Exclusion e{&inside},away{&outside};Manager manager;
 manager.Zones.assign(8,&away);manager.Zones.push_back(nullptr);Exclusion invalid{nullptr};manager.Zones.push_back(&invalid);manager.Zones.push_back(&e);
 a.ExclusionMgr=&manager;float center[3]={0,0,0},edge[3]={10,0,0},far[3]={200,0,0};
 assert(CameraInsideNebulaExclusion(&a,center));assert(!CameraInsideNebulaExclusion(&a,edge));assert(!CameraInsideNebulaExclusion(&a,far));
 assert(!CameraInsideNebulaExclusion(nullptr,center));assert(!CameraInsideNebulaExclusion(&a,nullptr));assert(!CameraInsideNebulaExclusion(&b,center));
 puts("PASS full exclusion list beyond GPU limit, boundaries, outside, absent manager and null entries");
 NebulaVolume::RegisterNebula(&a,"shared.ini");assert(GNebulae.size()==2);
 GNebulae[0].CameraExcluded=CameraInsideNebulaExclusion(&a,center);assert(SettingsFor(&a).Enabled==0 && SettingsFor(&b).Enabled==1);
 GNebulae[0].CameraExcluded=CameraInsideNebulaExclusion(&a,far);assert(SettingsFor(&a).Enabled==1);
 NebulaVolume::RegisterNebula(&a,"shared.ini",false);assert(SettingsFor(&a).Enabled==0);
 puts("PASS entering/leaving exclusion, independent overlapping nebula and instance reload/reset");
 assert(ReadNebulaShadows("test.ini"));
 IniSections={{"Fog",{{"shadows",false}}}};assert(ReadNebulaShadows("test.ini"));
 IniSections={{"NebulaLight",{{"shadows",false}}}};assert(!ReadNebulaShadows("test.ini"));
 NebulaVolume::RegisterNebula(&a,"shared.ini",false);assert(!GNebulae[0].Shadows);
 a.Zone=&inside;b.Zone=&outside;
 auto Off=NebulaVolume::ShadowsDisabledAt;
 assert(Off(center));assert(!Off(edge));assert(!Off(far));assert(!Off(nullptr));
 GNebulae[0].CameraExcluded=true;assert(Off(center));
 a.FlagLoaded=0;assert(!Off(center));a.FlagLoaded=1;
 GNebulae[0].RingOwner=&a;assert(!Off(center));GNebulae[0].RingOwner=nullptr;
 float bad[3]={std::numeric_limits<float>::quiet_NaN(),0,0};assert(!Off(bad));
 IniSections={{"NebulaLight",{{"shadows",true}}}};NebulaVolume::RegisterNebula(&a,"shared.ini");assert(!Off(center));
 puts("PASS nebula.ini shadow permission, defaults, entry/exit, volume-off and exclusion independence, reload and invalid positions");
}
'''
code=prefix+block('struct FRegisteredNebula',True)+'std::vector<FRegisteredNebula> GNebulae;\n'
code+=block('FNebulaVolumeSettings SettingsFor(')+block('bool ReadNebulaShadows(')+block('void NebulaVolume::RegisterNebula(')
code+=block('bool CameraInsideNebulaExclusion(')+block('bool NebulaVolume::ShadowsDisabledAt(')+tests
cpp=out/'check.cpp';cpp.write_text(code)
vc=sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/Community/VC/Tools/MSVC/*'))[-1]
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version=sorted(p.name for p in (sdk/'Include').iterdir() if (p/'um/Windows.h').exists())[-1]
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include',sdk/f'Include/{version}/ucrt',sdk/f'Include/{version}/shared',sdk/f'Include/{version}/um']))
env['LIB']=';'.join(map(str,[vc/'lib/x86',sdk/f'Lib/{version}/ucrt/x86',sdk/f'Lib/{version}/um/x86']))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/O2','/std:c++17','/EHsc','/MT',str(cpp),f'/Fe{out/"check.exe"}'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=root,check=True)
