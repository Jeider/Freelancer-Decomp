"""Exercise production PerfOptions load/save and HUD configuration using real fixture files.

INI_Reader is replaced by a narrow Win32 INI adapter; rendering is disabled.
The native option registry is represented by 36 distinct entries.
"""
from pathlib import Path
import os
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/hud_tilt_settings_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/perf_options.cpp').read_text()
production = source[source.index('bool LoadPerfOptions('):]
stub = r'''
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include "hud_tilt.h"
#define COMMON_EXPORTS
#include "graphics_settings.h"
int GraphicsSettings::Get(int setting,bool){return Default(setting);}
struct FPerfDisplaySettings { int Width=0,Height=0,ColorBpp=0,DepthBpp=0; };
struct FPerfOption { char Name[32];float Value,Applied; };
constexpr unsigned kOptionCount=36;
constexpr int kPerfSlotCount=7;
FPerfOption G_Options[kOptionCount]={};float G_Slots[kPerfSlotCount]={};
bool G_bSkipMachineWarnings=false;
struct {int width=1920,height=1080,color_bpp=32,depth_bpp=24;} g_display;
int Ftol(float value){return int(value);}
void GetUserDataPath(char* path){GetCurrentDirectoryA(MAX_PATH,path);}
FPerfOption* FindPerfOption(char const* name){
    for(auto& option:G_Options)if(strcmp(option.Name,name)==0)return &option;
    return nullptr;
}
void ApplyChangedPerfOptions(){for(auto& option:G_Options)option.Applied=option.Value;}
#define FDUMP(...) ((void)0)
struct INI_Reader {
    char path[MAX_PATH]={};std::vector<std::string> headers,entries;
    size_t header=0,entry=0;std::string name,value;
    bool open(char const* file,bool){
        GetFullPathNameA(file,MAX_PATH,path,nullptr);
        if(GetFileAttributesA(path)==INVALID_FILE_ATTRIBUTES)return false;
        char names[4096]={};GetPrivateProfileSectionNamesA(names,sizeof(names),path);
        for(char const* n=names;*n;n+=strlen(n)+1)headers.emplace_back(n);
        return true;
    }
    bool read_header(){
        if(header==headers.size())return false;
        entries.clear();entry=0;
        char data[8192]={};GetPrivateProfileSectionA(headers[header++].c_str(),data,sizeof(data),path);
        for(char const* n=data;*n;n+=strlen(n)+1)entries.emplace_back(n);
        return true;
    }
    bool is_header(char const* s){return _stricmp(headers[header-1].c_str(),s)==0;}
    bool read_value(){
        if(entry==entries.size())return false;
        auto const& line=entries[entry++];auto split=line.find('=');
        name=line.substr(0,split);value=line.substr(split+1);
        while(!name.empty()&&name.back()==' ')name.pop_back();
        return true;
    }
    bool is_value(char const* s){return _stricmp(name.c_str(),s)==0;}
    char const* get_name_ptr(){return name.c_str();}
    float get_value_float(int){return strtof(value.c_str(),nullptr);}
    bool get_value_bool(int){return value=="TRUE";}
    int get_value_int(int index){return atoi(value.c_str()+(index?value.find(',')+1:0));}
    void close(){}
};
'''
checks = r'''
std::string Read(char const* path){std::ifstream f(path);return {std::istreambuf_iterator<char>(f),{}};}
void Write(std::string const& text){std::ofstream f("PerfOptions.ini");f<<text;}
int main(){
    for(unsigned i=0;i<kOptionCount;++i){
        auto& o=G_Options[i];sprintf(o.Name,"existing_option_%u",i);o.Value=o.Applied=float(i)/100;
    }
    assert(HudTilt::ConfiguredAngle()==0);
    SavePerfOptions("PerfOptions.ini");auto flat=Read("PerfOptions.ini");
    assert(flat.find("[PerfCount]\ncount=36")!=std::string::npos);
    auto legacy=flat.substr(0,flat.find("\n[HUD]"));
    HudTilt::SetConfiguredAngle(13);Write(legacy);
    FPerfDisplaySettings display;
    assert(LoadPerfOptions("PerfOptions.ini",&display));
    assert(HudTilt::ConfiguredAngle()==0&&display.Width==1920&&display.Height==1080);
    for(unsigned i=0;i<kOptionCount;++i)assert(G_Options[i].Applied==float(i)/100);
    for(int degrees:{0,2,12,20,30,46,50}){
        HudTilt::SetConfiguredAngle(float(degrees));SavePerfOptions("PerfOptions.ini");
        HudTilt::SetConfiguredAngle(7);assert(LoadPerfOptions("PerfOptions.ini",nullptr));
        assert(HudTilt::ConfiguredAngle()==degrees);
    }
    for(auto const& sample:std::vector<std::pair<char const*,int>>{{"-5",0},{"200",50},{"12.6",12},{"45",46},{"1",2},{"nan",0},{"inf",0}}){
        Write(legacy+"\n[HUD]\nhud_tilt_degrees = "+sample.first+"\n");
        assert(LoadPerfOptions("PerfOptions.ini",nullptr));assert(HudTilt::ConfiguredAngle()==sample.second);
    }
    HudTilt::SetConfiguredAngle(10);HudTilt::SetAngle(18);SavePerfOptions("PerfOptions.ini");
    assert(Read("PerfOptions.ini").find("hud_tilt_degrees = 10")!=std::string::npos);
    assert(!LoadPerfOptions("absent.ini",nullptr)&&HudTilt::ConfiguredAngle()==0);
    puts("PASS: default zero, legacy PerfCount/settings/display preserved, file save/reload, clamping and configured/runtime separation");
}
'''
(out/'check.cpp').write_text(stub+production+checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',f'/I{repo/"src/freelancer/Client"}',f'/I{repo/"src/include"}','check.cpp',str(repo/'src/freelancer/Client/hud_tilt.cpp'),'/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,check=True)
