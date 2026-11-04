"""Exercise production graphics preferences and widgets using real INI files.

Runs fresh processes to check startup snapshots, migration, persistence and invalid
input. UI/device dependencies are narrow stubs; the policy and UI methods are real.
"""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/graphics_settings_check'
out.mkdir(parents=True, exist_ok=True)
common = (root/'src/Common/graphics_settings.cpp').read_text().replace('#include "common_misc.h"', '')
ui = (root/'src/freelancer/Client/nn_preferences_graphics.cpp').read_text()
ui = ui[ui.index('namespace\n{'):]
assert 'Russian()' not in ui and 'PortLanguage' not in ui
perf = (root/'src/freelancer/Client/perf_options.cpp').read_text()
save = perf[perf.index('void SavePerfOptions('):]
stub = r'''
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _CRT_SECURE_NO_WARNINGS
#define COMMON_EXPORTS
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include "graphics_policy.h"
#include "hud_interface_ids.h"
bool GetUserDataPath(char* p){return GetCurrentDirectoryA(MAX_PATH,p)!=0;}
char const* PortLanguage(){return "ru";}
void GetIdsStringWWithRawFallback(unsigned id,wchar_t* text,int count){
 swprintf_s(text,count,L"IDS%u",id);
}
namespace HudTilt {float ConfiguredAngle(){return 24.f;}}
constexpr unsigned kOptionCount=36;
bool G_bSkipMachineWarnings=false;
struct Option {char Name[32];float Applied=1;} G_Options[kOptionCount];
struct {int width=1920,height=1080,color_bpp=32,depth_bpp=24;} g_display;
constexpr unsigned kWin3DPickable=4,kWin3DVisible=2;
unsigned G_NnPaletteArgb_679b94=1,G_NnPaletteArgb_679bb0=2,G_NnPaletteArgb_679ba4=3;
struct Win3D {virtual ~Win3D()=default;unsigned Flags=2;};
struct WinControl:Win3D {
 float position[3]={},extents[3]={};bool mockHidden=false;
 virtual intptr_t SetProperty(int msg,uintptr_t a,uintptr_t){if(msg==1){mockHidden=a!=0;Flags=mockHidden?0:2;}return 0;}
};
struct NnTextControl:WinControl {unsigned TextColour=0;float width=0;std::wstring text;void SetText(wchar_t const* s){text=s;}};
struct NnButtonControl:WinControl {
 unsigned char Colour[4]={};int state=1;
 intptr_t SetProperty(int msg,uintptr_t a,uintptr_t b)override{if(msg==0x30)state=a==0?1:0;return WinControl::SetProperty(msg,a,b);}
};
struct WireButtonControl:WinControl {};
struct FPrefMiscCell {NnTextControl* Label=nullptr;NnTextControl* Value=nullptr;NnButtonControl* Toggle=nullptr;WireButtonControl* Choice=nullptr;};
struct NnDropdownPopup:WinControl {
 bool open=false;std::vector<std::wstring> choices;
 bool Open(float,float,float,std::vector<std::wstring> const& c,int selected){assert(selected>=0 && selected<int(c.size()));choices=c;open=true;return true;}
 void Close(){open=false;}void Draw(){}bool IsOpen()const{return open;}
};
void DrawNnDropdownCaret(WireButtonControl*){}
struct NnPreferences:WinControl {
 FPrefMiscCell GraphicsCells[GraphicsSettings::Count];
 int GraphicsValues[GraphicsSettings::Count]={},GraphicsOriginal[GraphicsSettings::Count]={};
 std::vector<WinControl*> GraphicsWidgets,owned;
 NnTextControl* GraphicsHint=nullptr;NnDropdownPopup* GraphicsDropdown=nullptr;
 NnDropdownPopup video;NnDropdownPopup* VideoModeDropdown=&video;
 int GraphicsDropdownRow=-1,CurPage=1;float Anim=1;
 bool bInGame=false,bFlipping=false,bConfirmMode=false,bVideoConfirm=false,bDirty=false;
 WireButtonControl defaults;WireButtonControl* DefaultsButton=&defaults;
 ~NnPreferences(){for(auto* control:owned)delete control;}
 template<class T>T* Own(T* c){owned.push_back(c);return c;}
 NnTextControl* CreateTextControl(char const*,char const*,float const* at,char const*,float width,float,float,unsigned,int,int,unsigned char){
  auto* c=Own(new NnTextControl);memcpy(c->position,at,sizeof(c->position));c->width=width;return c;
 }
 template<class... T>WinControl* CreateToggleButtonControl(char const*,char const*,char const*,char const*,void*,float const* at,void*,float const* half,T...){
  auto* c=Own(new NnButtonControl);memcpy(c->position,at,sizeof(c->position));memcpy(c->extents,half,sizeof(c->extents));return c;
 }
 template<class... T>WinControl* CreateWireButtonControl(char const*,char const*,float const* at,float const* half,T...){
  auto* c=Own(new WireButtonControl);memcpy(c->position,at,sizeof(c->position));memcpy(c->extents,half,sizeof(c->extents));return c;
 }
 void UpdateDirty(int,float){bDirty=GraphicsDirty();}
 bool CreateGraphicsRows();void SetGraphicsHidden(bool);void RefreshGraphicsRows();
 void SnapshotGraphics();void CommitGraphics();void RevertGraphics();bool GraphicsDirty()const;
 bool GraphicsProperty(int,Win3D*,uintptr_t);void DrawGraphicsDropdown();
};
NnDropdownPopup* CreateNnDropdownPopup(NnPreferences* p){return p->Own(new NnDropdownPopup);}
'''
checks = r'''
void Write(char const* file,char const* text){FILE* f=fopen(file,"w");assert(f);fputs(text,f);fclose(f);}
void Select(NnPreferences& p,int row,int value){
 assert(p.GraphicsProperty(0x26,p.GraphicsCells[row].Choice,0));assert(p.GraphicsDropdown->open);
 p.GraphicsProperty(0x3e,p.GraphicsDropdown,uintptr_t(value));assert(!p.GraphicsDropdown->open);
}
int main(int argc,char** argv){
 using namespace GraphicsSettings;
 assert(argc==2);
 if(!strncmp(argv[1],"legacy",6)){
  std::string ini="[Graphics]\nfps_limit="+std::string(argv[1]+6)+"\n";Write("PerfOptions.ini",ini.c_str());
  assert(Get(FpsLimit)==8 && PortGraphicsRenderValue("fps_limit",0)==180);
  puts("PASS: old unlimited/240/360 settings migrate to 180 FPS");return 0;
 }
 if(!strcmp(argv[1],"reload")){
  for(int i=0;i<Count;++i)assert(Get(i)==Maximum(i)-Default(i));
  assert(!RestartRequired());puts("PASS: fresh process loads all configured values");return 0;
 }
 Write("port.ini","[Render]\nvsync=0\nfps_limit=144\nanisotropy=8\n");
 Write("PerfOptions.ini","[Graphics]\nshadows=garbage\nrelief=-1\nhighlights=4\nreflections=1junk\nantialiasing=2\nnebulae=2\nfps_limit=999999999999999999999999999999\n");
 assert(Get(Shadows)==3 && Get(Relief)==1 && Get(Highlights)==1 && Get(Reflections)==1);
 assert(Get(Antialiasing)==2 && Get(Nebulae)==2 && Get(VSync)==0 && Get(FpsLimit)==6 && Get(Anisotropy)==3);
 assert(PortGraphicsRenderValue("anisotropy",16)==8);
 assert(PortGraphicsRenderValue("smaa",0)==1 && PortGraphicsRenderValue("fxaa",1)==0);
 assert(PortGraphicsRenderValue("nebula_resolution_scale",1)==.5f);
 int all[Count];for(int i=0;i<Count;++i)all[i]=Default(i);
 all[Shadows]=all[Relief]=all[Highlights]=all[Reflections]=all[Nebulae]=0;
 for(char const* key:{"local_shadows","rock_shadows","room_object_shadows","room_contact_shadows","planet_terrain_shadows",
  "ship_normals","rock_relief","cockpit_relief","planet_relief","room_normal_strength","nomad_relief","dyson_relief","beast_relief",
  "surface_highlights","weapon_glints","room_specular_strength","environment_maps","nebula_enabled"})assert(RenderValue(all,key,1)==0);
 assert(RenderValue(all,"unrelated_artistic_density",.7f)==.7f);
 for(int aa=0;aa<=2;++aa){all[Antialiasing]=aa;assert(RenderValue(all,"smaa",1)==float(aa==2));assert(RenderValue(all,"fxaa",1)==float(aa==1));}
 for(int tier=1;tier<=3;++tier){all[Shadows]=all[Nebulae]=tier;
  assert(RenderValue(all,"shadow_near_resolution",4096)==float(1<<(tier+9)));
  assert(RenderValue(all,"nebula_steps",128)==float(1<<(tier+4)));
  assert(RenderValue(all,"nebula_enabled",0)==0);
 }
 Set(-1,5);Set(Count,5);Set(Shadows,999);assert(!RestartRequired());
 NnPreferences p;assert(p.CreateGraphicsRows());p.SnapshotGraphics();p.SetGraphicsHidden(false);
 for(int i=0;i<Count;++i){auto& c=p.GraphicsCells[i];assert(!c.Label->mockHidden);
  wchar_t expected[32];swprintf_s(expected,L"IDS%u",238251+i);assert(c.Label->text==expected);
  assert(c.Label->position[1]>.22f-12*.035f && c.Label->position[1]<.22f-2*.035f);
  assert(c.Label->position[0]+c.Label->width<.181f);
  assert((c.Toggle!=nullptr)==Toggle(i));assert((c.Choice!=nullptr)!=Toggle(i));
 }
 NnPreferences flight;flight.bInGame=true;assert(flight.CreateGraphicsRows());
 assert(std::fabs(flight.GraphicsCells[0].Label->position[1]-p.GraphicsCells[0].Label->position[1]+.01f)<.00001f);
 int active=Get(Shadows);Select(p,Shadows,0);assert(p.bDirty&&Get(Shadows)==active&&Get(Shadows,true)==active);
 p.RevertGraphics();assert(!p.GraphicsDirty()&&Get(Shadows,true)==active);
 Select(p,Shadows,1);p.CommitGraphics();assert(Get(Shadows)==active&&Get(Shadows,true)==1&&RestartRequired());
 p.SnapshotGraphics();assert(!p.GraphicsDirty());Select(p,Shadows,2);p.RevertGraphics();assert(p.GraphicsValues[Shadows]==1);
 auto* toggle=p.GraphicsCells[Relief].Toggle;
 int before=p.GraphicsValues[Relief];toggle->state=1-toggle->state;
 p.GraphicsProperty(0x30,toggle,uintptr_t(toggle->state));assert(p.GraphicsValues[Relief]!=before);
 p.bConfirmMode=true;Select(p,FpsLimit,0); // blocked messages cannot change state
 return 0;
}
'''
# Guarded events must be checked without Select(), which expects a popup to open.
checks = checks.replace('p.bConfirmMode=true;Select(p,FpsLimit,0); // blocked messages cannot change state', r'''
 p.bConfirmMode=true;assert(!p.GraphicsProperty(0x26,p.GraphicsCells[FpsLimit].Choice,0));assert(!p.GraphicsDropdown->open);p.bConfirmMode=false;
 p.GraphicsProperty(0x26,p.GraphicsCells[FpsLimit].Choice,0);assert(p.GraphicsDropdown->choices.size()==8);
 p.GraphicsProperty(0x3e,p.GraphicsDropdown,0);assert(p.GraphicsValues[FpsLimit]==1);
 Select(p,FpsLimit,7);assert(p.GraphicsValues[FpsLimit]==8);
 for(int index=0;index<=Maximum(FpsLimit);++index)assert(Fps(index)>0 && Fps(index)<=180);
 assert(p.GraphicsHint->position[1]<p.GraphicsCells[FpsLimit].Label->position[1]-.03f);
 assert(p.GraphicsHint->position[1]-.027f>-.26f);
 p.SetGraphicsHidden(true);assert(!p.GraphicsDropdown->open && p.GraphicsDropdownRow==-1);
 p.SetGraphicsHidden(false);Select(p,Shadows,999);assert(p.GraphicsValues[Shadows]==1);
 p.GraphicsProperty(0x26,p.DefaultsButton,0);for(int i=0;i<Count;++i)assert(p.GraphicsValues[i]==Default(i));
 for(int i=0;i<Count;++i)Set(i,Maximum(i)-Default(i));
 for(unsigned i=0;i<kOptionCount;++i)sprintf_s(G_Options[i].Name,"legacy_%u",i);
 SavePerfOptions("PerfOptions.ini");
 char path[MAX_PATH];GetFullPathNameA("PerfOptions.ini",MAX_PATH,path,nullptr);
 assert(GetPrivateProfileIntA("PerfCount","count",0,path)==36);
 assert(GetPrivateProfileIntA("HUD","hud_tilt_degrees",0,path)==24);
 assert(GetPrivateProfileIntA("Display","color_bpp",0,path)==32);
 puts("PASS: migration, invalid input, render gates, quality caps, UI staging/cancel/apply/defaults, persistence");
''')
(out/'check.cpp').write_text(stub+common+save+ui+checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',f'/I{root/"src/include"}',f'/I{root/"src/freelancer/Client"}','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
for mode in ('legacy0','legacy9','legacy10','exercise','reload'):
    subprocess.run([str(out/'check.exe'),mode],cwd=out,check=True)
