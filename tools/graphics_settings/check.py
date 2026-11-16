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
common = common.split('#include "common_reputation.h"')[0]  # unrelated costume implementation
common = common.replace('#include "graphics_adapter.h"', '')
common = common.replace('client ? GraphicsAdapter::Detect() : GraphicsAdapter::Info{}', 'GraphicsAdapter::Detect()')
common = common.replace('bool const client=executable && _strnicmp(executable+1,"freelancer",10)==0;', '(void)executable;')
grade = (root/'src/freelancer/Client/color_grade_preferences.cpp').read_text().replace('#include "common_misc.h"','').replace('#include "port_config.h"','')
ui = (root/'src/freelancer/Client/nn_preferences_graphics.cpp').read_text()
ui = ui[ui.index('namespace\n{'):]
assert 'Russian()' not in ui and 'PortLanguage' not in ui
perf = (root/'src/freelancer/Client/perf_options.cpp').read_text()
save = perf[perf.index('void SavePerfOptions('):]
room_scope = 'float G_Slots[8]={};bool G_PerfRoomScope=false;\n'+perf[perf.index('float GetPerfOptionSlot('):perf.index('void ApplyChangedPerfOptions(')]
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
#include "travel_quality.h"
#include "hud_interface_ids.h"
#include "color_grade_preferences.h"
int __cdecl PortConfigInt(char const* section,char const*,int fallback){return !strcmp(section,"ColorGrade")?3:fallback;}
bool GetUserDataPath(char* p){return GetCurrentDirectoryA(MAX_PATH,p)!=0;}
char const* PortLanguage(){return "ru";}
void GetIdsStringWWithRawFallback(unsigned id,wchar_t* text,int count){
 swprintf_s(text,count,L"IDS%u",id);
}
namespace NativeSubtitles { bool enabled=true;bool CutsceneEnabled(){return enabled;}void SetCutsceneEnabled(bool value){enabled=value;} void WritePreferences(FILE* f){fprintf(f,"\n[Subtitles]\ncutscenes = %d\n",enabled?1:0);} }
namespace HudTilt {float ConfiguredAngle(){return 24.f;}}
namespace GraphicsAdapter {
 enum Kind {Unknown,Integrated,Discrete};
 struct Info {Kind Type=Unknown;char Key[96]={};char Name[512]={};};
 Info Detect(){Info info;char text[32]={};GetEnvironmentVariableA("TEST_GPU_TYPE",text,sizeof(text));
 if(!strcmp(text,"integrated"))info.Type=Integrated;
 if(!strcmp(text,"discrete"))info.Type=Discrete;
 if(info.Type!=Unknown){strcpy_s(info.Key,text);strcpy_s(info.Name,text);}return info;}
}
constexpr unsigned kOptionCount=36;
bool G_bSkipMachineWarnings=false;
struct Option {char Name[32];float Applied=1;} G_Options[kOptionCount];
struct {int width=1920,height=1080,color_bpp=32,depth_bpp=24;} g_display;
constexpr unsigned kWin3DPickable=4,kWin3DVisible=2;
unsigned G_NnPaletteArgb_679b94=1,G_NnPaletteArgb_679bb0=2,G_NnPaletteArgb_679ba4=3;
struct Win3D {virtual ~Win3D()=default;unsigned Flags=2;};
struct WinControl:Win3D {
 float position[3]={},anchor[3]={},Offset[3]={},extents[3]={};bool mockHidden=false;
 // Retail controls store their creation coordinates in Offset. SetPosition
 // moves the parent anchor, and drawing/hit testing adds Offset to that anchor.
 virtual void SetPosition(float const* p){for(int i=0;i<3;++i){anchor[i]=p[i];position[i]=anchor[i]+Offset[i];}}
 virtual void SetOffset(float x,float y,float z){Offset[0]=x;Offset[1]=y;Offset[2]=z;float parent[3]={};SetPosition(parent);}
 virtual intptr_t SetProperty(int msg,uintptr_t a,uintptr_t){if(msg==1){mockHidden=a!=0;Flags=mockHidden?0:2;}return 0;}
};
struct NnTextControl:WinControl {unsigned TextColour=0;float width=0;std::wstring text;void SetText(wchar_t const* s){text=s;}};
struct NnButtonControl:WinControl {
 unsigned char Colour[4]={},ButtonBits2=2;int state=1;
 intptr_t SetProperty(int msg,uintptr_t a,uintptr_t b)override{if(msg==0x30)state=a==0?1:0;return WinControl::SetProperty(msg,a,b);}
};
struct WireButtonControl:WinControl {};
struct UiScroll:WinControl {int value=0,page=0;bool stepMode=false;void SetStepMode(bool b){stepMode=b;} void SetPageField(float){} void SetActiveField(bool){} intptr_t SetProperty(int msg,uintptr_t a,uintptr_t b)override{
 if(msg==0x38)value=int(a);return WinControl::SetProperty(msg,a,b);}};
struct FPrefMiscCell {NnTextControl* Label=nullptr;NnTextControl* Value=nullptr;NnButtonControl* Toggle=nullptr;WireButtonControl* Choice=nullptr;};
struct NnDropdownPopup:WinControl {
 bool open=false;float left=0;std::vector<std::wstring> choices;
 bool Open(float x,float,float,std::vector<std::wstring> const& c,int selected){left=x;assert(selected>=0 && selected<int(c.size()));choices=c;open=true;return true;}
 void Close(){open=false;}void Draw(){}bool IsOpen()const{return open;}
};
void DrawNnDropdownCaret(WireButtonControl*){}
struct NnPreferences:WinControl {
 FPrefMiscCell SubtitleCells[2];bool SubtitlesValue=true,SubtitlesOriginal=true;
 FPrefMiscCell ColorGradeCell;
 int ColorGradeValue=0,ColorGradeOriginal=0;
 FPrefMiscCell GraphicsCells[GraphicsSettings::Count];
 int GraphicsValues[GraphicsSettings::Count]={},GraphicsOriginal[GraphicsSettings::Count]={};
 std::vector<WinControl*> GraphicsWidgets,owned;
 NnTextControl* GraphicsHint=nullptr;NnDropdownPopup* GraphicsDropdown=nullptr;
 NnDropdownPopup video;NnDropdownPopup* VideoModeDropdown=&video;
  int GraphicsDropdownRow=-1,CurPage=2,GraphicsTab=0;float Anim=1;
  WireButtonControl* GraphicsTabButtons[2]={};NnTextControl* GraphicsTabTexts[2]={};
  WireButtonControl* GraphicsPresetButtons[4]={};NnTextControl* GraphicsPresetTexts[4]={};
  UiScroll* GraphicsScroll=nullptr;int GraphicsFirstRow=0;
  WinControl* GraphicsInteriorSeparator=nullptr;
  void SetOptionRowsHidden(bool){}
  void ApplyGraphicsTab();
 bool bInGame=false,bFlipping=false,bConfirmMode=false,bVideoConfirm=false,bDirty=false;
 WireButtonControl defaults,cancel;WireButtonControl* DefaultsButton=&defaults;WireButtonControl* CancelButton=&cancel;
 NnTextControl defaultsText,cancelText;NnTextControl* DefaultsText=&defaultsText;NnTextControl* CancelText=&cancelText;
 ~NnPreferences(){for(auto* control:owned)delete control;}
 template<class T>T* Own(T* c){owned.push_back(c);return c;}
 UiScroll* CreateUIScroll(char const*,float const* at,float,float,int,int,int page,int){auto* c=Own(new UiScroll);c->SetOffset(at[0],at[1],at[2]);c->page=page;return c;}
 WinControl* CreateWireStaticControl(char const*,float const* at,float const* half,unsigned char,unsigned char,int,int){auto* c=Own(new WinControl);c->SetOffset(at[0],at[1],at[2]);memcpy(c->extents,half,sizeof(c->extents));return c;}
 NnTextControl* CreateTextControl(char const*,char const*,float const* at,char const*,float width,float,float,unsigned,int,int,unsigned char){
  auto* c=Own(new NnTextControl);c->SetOffset(at[0],at[1],at[2]);c->width=width;return c;
 }
 template<class... T>WinControl* CreateToggleButtonControl(char const*,char const*,char const*,char const*,void*,float const* at,void*,float const* half,T...){
  auto* c=Own(new NnButtonControl);c->SetOffset(at[0],at[1],at[2]);memcpy(c->extents,half,sizeof(c->extents));return c;
 }
 template<class... T>WinControl* CreateWireButtonControl(char const*,char const*,float const* at,float const* half,T...){
  auto* c=Own(new WireButtonControl);c->SetOffset(at[0],at[1],at[2]);memcpy(c->extents,half,sizeof(c->extents));return c;
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
 if(!strncmp(argv[1],"gpu_",4)){
  char path[MAX_PATH];GetFullPathNameA("PerfOptions.ini",MAX_PATH,path,nullptr);
  bool const first=!strcmp(argv[1],"gpu_first");
  bool const discrete=!strcmp(argv[1],"gpu_discrete");
  bool const unknown=!strcmp(argv[1],"gpu_unknown");
  SetEnvironmentVariableA("TEST_GPU_TYPE",unknown?"unknown":discrete?"discrete":"integrated");
  if(first)Write("PerfOptions.ini","[Graphics]\nanomalies=3\nweapon_lights=1\nfps_limit=2\nvsync=0\n");
  if(!strcmp(argv[1],"gpu_manual"))WritePrivateProfileStringA("Graphics","anomalies","2",path);
  int expected=discrete?3:first?0:2;
  assert(Get(Anomalies)==expected);
  assert(Get(WeaponLights)==(discrete?1:0));
  assert(Get(FpsLimit)==2 && Get(VSync)==0);
  if(first)assert(GetFileAttributesA("PerfOptions.ini.before_gpu_profile.bak")!=INVALID_FILE_ATTRIBUTES);
  SavePerfOptions("PerfOptions.ini");
  assert(GetPrivateProfileIntA("Graphics","auto_profile_version",0,path)==1);
  puts("PASS: GPU first-run migration, manual override, unknown adapter or adapter change");return 0;
 }
 if(!strncmp(argv[1],"legacy",6)){
  std::string ini="[Graphics]\nfps_limit="+std::string(argv[1]+6)+"\n";Write("PerfOptions.ini",ini.c_str());
  assert(Get(FpsLimit)==8 && PortGraphicsRenderValue("fps_limit",0)==180);
  puts("PASS: old unlimited/240/360 settings migrate to 180 FPS");return 0;
 }
 if(!strcmp(argv[1],"room_scope")){
  Write("PerfOptions.ini","[Graphics]\nreflections=0\nshadows=0\nrelief_quality=0\nhighlight_quality=0\ninteriors=3\n");
  G_Slots[0]=1;assert(GetPerfOptionSlot(0)==0);
  SetPerfRoomScope(true);assert(GetPerfOptionSlot(0)==1);
  assert(PortGraphicsRenderValue("room_normal_strength",1)==1);
  assert(PortGraphicsRenderValue("room_specular_strength",1)==1);
  assert(PortGraphicsRenderValue("room_object_shadows",1)==1);
  SetPerfRoomScope(false);assert(GetPerfOptionSlot(0)==0);return 0;
 }
 if(!strcmp(argv[1],"old_effects")){
  Write("PerfOptions.ini","[Graphics]\nrelief=1\nhighlights=0\n");
  assert(Get(Relief)==3 && Get(Highlights)==0);return 0;
 }
 if(!strcmp(argv[1],"quality_effects")){
  Write("PerfOptions.ini","[Graphics]\nrelief=1\nhighlights=0\nrelief_quality=1\nhighlight_quality=2\n");
  assert(Get(Relief)==1 && Get(Highlights)==2);return 0;
 }
 if(!strcmp(argv[1],"reload")){
  assert(ColorGrade::ConfiguredPreset()==3);
  for(int i=0;i<Count;++i)assert(Get(i)==(Maximum(i)-Default(i)));
  assert(!RestartRequired());puts("PASS: fresh process loads all configured values");return 0;
 }
 Write("port.ini","[Render]\nvsync=0\nfps_limit=144\nanisotropy=8\n");
 Write("PerfOptions.ini","[Graphics]\nshadows=garbage\nrelief=-1\nhighlights=4\nreflections=1junk\nantialiasing=2\nnebulae=2\nfps_limit=999999999999999999999999999999\n");
 assert(Get(Shadows)==3 && Get(Relief)==3 && Get(Highlights)==3 && Get(Reflections)==1);
 assert(Get(Antialiasing)==2 && Get(Nebulae)==2 && Get(VSync)==0 && Get(FpsLimit)==6 && Get(Anisotropy)==3);
 assert(PortGraphicsRenderValue("anisotropy",16)==8);
 assert(PortGraphicsRenderValue("smaa",0)==1 && PortGraphicsRenderValue("fxaa",1)==0);
 assert(PortGraphicsRenderValue("nebula_resolution_scale",1)==.5f);
 assert(PortGraphicsRenderValue("character_hair",0)==3);
 PortCharacterPortraitScope(1);PortCharacterPortraitScope(1);
 assert(PortGraphicsRenderValue("character_hair",3)==0 && PortGraphicsRenderValue("character_hair_motion",1)==0);
 assert(PortGraphicsRenderValue("anisotropy",16)==8);
 PortCharacterPortraitScope(0);assert(PortGraphicsRenderValue("character_hair",3)==0);
 PortCharacterPortraitScope(0);assert(PortGraphicsRenderValue("character_hair",0)==3);
 int all[Count];for(int i=0;i<Count;++i)all[i]=Default(i);
 for(int tier=0;tier<4;++tier){all[Hair]=tier;assert(RenderValue(all,"character_hair",3)==tier);
  assert(RenderValue(all,"character_hair_motion",1)==(tier<2?0.f:tier==2?.55f:1.f));}all[Hair]=Default(Hair);
 all[Shadows]=all[Relief]=all[Highlights]=all[Reflections]=all[Nebulae]=0;
 for(char const* key:{"local_shadows","rock_shadows","planet_terrain_shadows",
  "ship_normals","rock_relief","cockpit_relief","planet_relief","nomad_relief","dyson_relief","beast_relief",
  "surface_highlights","weapon_glints","environment_maps","nebula_enabled"})assert(RenderValue(all,key,1)==0);
 assert(RenderValue(all,"unrelated_artistic_density",.7f)==.7f);
 // Interior quality must gate real room paths, without changing space policy.
 int rooms[Count];for(int i=0;i<Count;++i)rooms[i]=Default(i);
 for(int tier=0;tier<=3;++tier){
  rooms[Interiors]=tier;
  assert(RenderValue(rooms,"room_quality",3)==tier);
  assert(RenderValue(rooms,"room_materials",1)==float(tier!=0));
  assert(RenderValue(rooms,"room_contact_shadows",.32f)==(tier==3?.32f:0.f));
  assert(RenderValue(rooms,"room_object_shadows",1)==float(tier>=2));
  assert(RenderValue(rooms,"room_light_count",8)==(tier<=1?2.f:tier==2?4.f:8.f));
  assert(RenderValue(rooms,"room_shadow_resolution",1024)==(tier<3?512.f:1024.f));
  assert(RenderValue(rooms,"room_procedural_relief",1)==float(tier>=2));
  assert(RenderValue(rooms,"room_finish",1)==float(tier>=2));
  for(char const* key:{"surface_shaders","ship_normals","environment_maps","local_shadows","black_hole_steps"})
   assert(RenderValue(rooms,key,1)==1);
 }
 rooms[Highlights]=rooms[Relief]=rooms[Shadows]=0;
 for(char const* key:{"room_procedural_relief","room_finish","room_object_shadows","room_contact_shadows","room_normal_strength","room_specular_strength"})
  assert(RenderValue(rooms,key,1)==1);
 all[WeaponLights]=0;assert(RenderValue(all,"weapon_lights",1)==0);
 all[WeaponLights]=1;assert(RenderValue(all,"weapon_lights",1)==1);
 all[Anomalies]=0;
 assert(RenderValue(all,"black_hole_visual",0)==0 && RenderValue(all,"jumphole_visual",0)==0);
 all[Nebulae]=3;
 assert(RenderValue(all,"nebula_enabled",1)==1 && RenderValue(all,"black_hole_visual",1)==0);
 all[Nebulae]=0;all[Anomalies]=1;
 assert(RenderValue(all,"black_hole_resolution",1)==.25f && RenderValue(all,"black_hole_steps",180)==64);
 assert(RenderValue(all,"jumphole_steps",64)==24 && RenderValue(all,"nebula_enabled",1)==0);
 all[Anomalies]=2;
 assert(RenderValue(all,"black_hole_resolution",1)==.5f && RenderValue(all,"black_hole_steps",180)==112);
 assert(RenderValue(all,"jumphole_steps",64)==40);
 all[Anomalies]=3;
 assert(RenderValue(all,"black_hole_steps",180)==180 && RenderValue(all,"jumphole_steps",64)==64);
 for(int aa=0;aa<=2;++aa){all[Antialiasing]=aa;assert(RenderValue(all,"smaa",1)==float(aa==2));assert(RenderValue(all,"fxaa",1)==float(aa==1));}
 for(int tier=1;tier<=3;++tier){all[Shadows]=all[Nebulae]=tier;
  assert(RenderValue(all,"shadow_near_resolution",4096)==float(1<<(tier+9)));
  assert(RenderValue(all,"nebula_steps",128)==float(1<<(tier+4)));
  assert(RenderValue(all,"nebula_enabled",0)==0);
 }
 Set(-1,5);Set(Count,5);Set(Shadows,999);assert(!RestartRequired());
 NnPreferences p;assert(p.CreateGraphicsRows());p.SnapshotGraphics();p.SetGraphicsHidden(false);
 for(int i=0;i<Count;++i){auto& c=p.GraphicsCells[i];assert(c.Label->mockHidden==(i==VSync || i==FpsLimit || i==Interiors || i==Hair));
  unsigned id=i==TradeLane?PreferenceIds::GraphicsTradeLane:i==Hyperspace?PreferenceIds::GraphicsHyperspace:i==WeaponLights?PreferenceIds::GraphicsWeaponLights:i==Anomalies?PreferenceIds::GraphicsAnomalies:i==Interiors?PreferenceIds::GraphicsInteriors:238251+i;
  wchar_t expected[32];swprintf_s(expected,L"IDS%u",id);assert(i==Hair ? c.Label->text==L"\u0412\u041e\u041b\u041e\u0421\u042b \u041f\u0415\u0420\u0421\u041e\u041d\u0410\u0416\u0415\u0419" : c.Label->text==expected);
   if(!c.Label->mockHidden)assert(c.Label->position[1]>-.20f && c.Label->position[1]<.18f);
  assert(c.Label->position[0]+c.Label->width<(i==VSync || i==FpsLimit?.181f:.151f));
  assert((c.Toggle!=nullptr)==Toggle(i));assert((c.Choice!=nullptr)!=Toggle(i));
 }
 assert(!p.GraphicsScroll->mockHidden);
 assert(!p.GraphicsScroll->stepMode && p.GraphicsScroll->page==11);
 assert(std::fabs(p.GraphicsScroll->position[0]-.408f)<.0001f);
 assert(p.GraphicsInteriorSeparator->mockHidden);
 for(int repeat=0;repeat<3;++repeat){
  p.ApplyGraphicsTab();
  assert(std::fabs(p.GraphicsCells[Shadows].Label->position[0]+.11f)<.0001f);
  assert(std::fabs(p.GraphicsCells[Shadows].Label->position[1]-.165078125f)<.0001f);
  assert(std::fabs(p.GraphicsCells[Shadows].Choice->position[0]-.272f)<.0001f);
 }
 assert(p.GraphicsCells[Anomalies].Label->position[1]>p.GraphicsCells[TradeLane].Label->position[1]);
 assert(p.GraphicsCells[TradeLane].Label->position[1]>p.GraphicsCells[Hyperspace].Label->position[1]);
 Select(p,TradeLane,0);Select(p,Hyperspace,3);
 assert(p.GraphicsValues[TradeLane]==0 && p.GraphicsValues[Hyperspace]==3);
 assert(p.GraphicsCells[TradeLane].Value->text==L"IDS238411");
 p.GraphicsProperty(0x26,p.GraphicsCells[TradeLane].Choice,0);assert(p.GraphicsDropdown->open);
 assert(std::fabs(p.GraphicsDropdown->left-.151f)<.0001f);
 p.GraphicsProperty(0x3e,p.GraphicsScroll,3);
 assert(p.GraphicsFirstRow==3 && !p.GraphicsDropdown->open);
 assert(p.GraphicsCells[Shadows].Label->mockHidden && !p.GraphicsCells[Hair].Label->mockHidden);
 assert(p.GraphicsCells[Hair].Label->position[1]>p.GraphicsHint->position[1]+.027f);
 assert(!p.GraphicsScroll->stepMode && p.GraphicsScroll->page==11);
 assert(!p.GraphicsInteriorSeparator->mockHidden);
 assert(p.GraphicsInteriorSeparator->position[1]>p.GraphicsCells[Interiors].Label->position[1]);
 assert(p.GraphicsInteriorSeparator->position[1]<p.GraphicsCells[Hyperspace].Choice->position[1]-.0145f);
 assert(p.GraphicsInteriorSeparator->position[1]-p.GraphicsCells[Interiors].Label->position[1]>.020f);
 assert(p.GraphicsCells[Hyperspace].Choice->position[1]-.0145f-p.GraphicsInteriorSeparator->position[1]>.020f);
 Select(p,Interiors,1);assert(p.GraphicsValues[TradeLane]==0 && p.GraphicsValues[Hyperspace]==3);
 p.GraphicsProperty(0x3e,p.GraphicsScroll,999);assert(p.GraphicsFirstRow==3);
 p.GraphicsProperty(0x3e,p.GraphicsScroll,0);assert(p.GraphicsFirstRow==0);
 assert(p.GraphicsInteriorSeparator->mockHidden);
 p.RevertGraphics();
 assert(!strcmp(TravelQuality::TradeLaneEntry(0),"PSStandard"));
 assert(!strcmp(TravelQuality::TradeLaneEntry(1),"PSLow"));
 assert(!strcmp(TravelQuality::TradeLaneEntry(2),"PSMedium"));
 assert(!strcmp(TravelQuality::TradeLaneEntry(3),"PSMain"));
 assert(TravelQuality::HyperspaceScale(0)==0 && TravelQuality::HyperspaceScale(1)==.25f);
 assert(TravelQuality::HyperspaceScale(2)==1.f/3 && TravelQuality::HyperspaceScale(3)==.5f);
 // Both monitor rows are hidden on Details; only the cutscene row is interactive.
 assert(p.SubtitleCells[0].Label->mockHidden && p.SubtitleCells[1].Label->mockHidden);
 p.CurPage=1;p.SetGraphicsHidden(false);
 assert(!p.SubtitleCells[0].Label->mockHidden && !p.SubtitleCells[1].Label->mockHidden);
 assert(!(p.SubtitleCells[1].Toggle->ButtonBits2&2));
 assert(p.SubtitlesValue && NativeSubtitles::CutsceneEnabled());
 p.GraphicsProperty(0x30,p.SubtitleCells[0].Toggle,1);
 assert(!p.SubtitlesValue && p.GraphicsDirty() && NativeSubtitles::CutsceneEnabled());
 p.RevertGraphics();assert(p.SubtitlesValue && !p.GraphicsDirty());
 p.GraphicsProperty(0x30,p.SubtitleCells[0].Toggle,1);p.CommitGraphics();p.SnapshotGraphics();
 assert(!NativeSubtitles::CutsceneEnabled() && !p.SubtitlesValue && !p.GraphicsDirty());
 p.GraphicsProperty(0x30,p.SubtitleCells[1].Toggle,0);assert(!p.SubtitlesValue);
 p.GraphicsProperty(0x26,p.DefaultsButton,0);assert(p.SubtitlesValue);
 p.CommitGraphics();p.SnapshotGraphics();p.CurPage=2;p.SetGraphicsHidden(false);
 NnPreferences flight;flight.bInGame=true;assert(flight.CreateGraphicsRows());
  assert(std::fabs(flight.GraphicsCells[0].Label->position[1]-p.GraphicsCells[0].Label->position[1]+.009765625f)<.0001f);
 for(int q=0;q<=3;++q){Select(p,Relief,q);Select(p,Highlights,q);
  assert(p.GraphicsValues[Relief]==q && p.GraphicsValues[Highlights]==q);}
 assert(p.DefaultsButton->mockHidden && p.CancelButton->mockHidden);
 int const vsync=p.GraphicsValues[VSync],fps=p.GraphicsValues[FpsLimit],grade=p.ColorGradeValue;
 for(int preset=0;preset<4;++preset){
  assert(!p.GraphicsPresetButtons[preset]->mockHidden);
  assert(p.GraphicsProperty(0x26,p.GraphicsPresetButtons[preset],0));
  assert(p.GraphicsValues[VSync]==vsync && p.GraphicsValues[FpsLimit]==fps && p.ColorGradeValue==grade);
  assert(p.GraphicsValues[Anomalies]==preset && p.GraphicsValues[Interiors]==preset);
  assert(p.GraphicsValues[TradeLane]==preset && p.GraphicsValues[Hyperspace]==preset);
  assert(p.GraphicsValues[Shadows]==preset && p.GraphicsValues[Relief]==preset && p.GraphicsValues[Highlights]==preset);
  assert(p.GraphicsValues[WeaponLights]==int(preset>=2));
  assert(p.GraphicsValues[Antialiasing]==(preset<2?preset:2));
  assert(p.GraphicsValues[Anisotropy]==(preset<2?preset:preset==2?3:4));
 }
 p.CurPage=1;p.ApplyGraphicsTab();
 assert(std::fabs(p.GraphicsCells[VSync].Label->position[0]+.11f)<.0001f);
 assert(std::fabs(p.GraphicsCells[VSync].Label->position[1]-(.205f-3*.035f+.0135f))<.0001f);
 assert(std::fabs(p.GraphicsCells[FpsLimit].Choice->position[0]-.302f)<.0001f);
 assert(!p.GraphicsCells[VSync].Label->mockHidden && !p.GraphicsCells[FpsLimit].Label->mockHidden);
 assert(p.GraphicsCells[Relief].Label->mockHidden && p.GraphicsPresetButtons[0]->mockHidden);
 assert(!p.DefaultsButton->mockHidden && !p.CancelButton->mockHidden);
 assert(p.GraphicsCells[VSync].Label->position[1]>p.GraphicsCells[FpsLimit].Label->position[1]);
 assert(p.GraphicsCells[FpsLimit].Label->position[1]>p.ColorGradeCell.Label->position[1]);
 p.CurPage=2;p.GraphicsTab=1;p.ApplyGraphicsTab();
 assert(!p.DefaultsButton->mockHidden && !p.CancelButton->mockHidden && p.GraphicsPresetButtons[0]->mockHidden);
 p.GraphicsTab=0;p.ApplyGraphicsTab();
 int active=Get(Shadows);Select(p,Shadows,0);assert(p.bDirty&&Get(Shadows)==active&&Get(Shadows,true)==active);
 assert(ColorGrade::DefaultPreset()==0); // even when authored port.ini requests preset 3
 p.GraphicsProperty(0x26,p.GraphicsCells[Anomalies].Choice,0);
 assert(p.GraphicsDropdown->choices.size()==4);
 p.GraphicsProperty(0x3e,p.GraphicsDropdown,0);assert(p.GraphicsValues[Anomalies]==0);
 p.GraphicsProperty(0x26,p.GraphicsCells[Interiors].Choice,0);
 assert(p.GraphicsDropdown->choices.size()==4);
 p.GraphicsProperty(0x3e,p.GraphicsDropdown,0);assert(p.GraphicsValues[Interiors]==0);
 assert(std::fabs(p.ColorGradeCell.Label->position[1]-(.205f-5*.035f))<.0001f);
 p.RevertGraphics();assert(!p.GraphicsDirty()&&Get(Shadows,true)==active);
 Select(p,Shadows,1);p.CommitGraphics();assert(Get(Shadows)==active&&Get(Shadows,true)==1&&RestartRequired());
 p.SnapshotGraphics();assert(!p.GraphicsDirty());Select(p,Shadows,2);p.RevertGraphics();assert(p.GraphicsValues[Shadows]==1);
 auto* toggle=p.GraphicsCells[Reflections].Toggle;
 int before=p.GraphicsValues[Reflections];toggle->state=1-toggle->state;
 p.GraphicsProperty(0x30,toggle,uintptr_t(toggle->state));assert(p.GraphicsValues[Reflections]!=before);
 p.bConfirmMode=true;Select(p,FpsLimit,0); // blocked messages cannot change state
 return 0;
}
'''
# Guarded events must be checked without Select(), which expects a popup to open.
checks = checks.replace('p.bConfirmMode=true;Select(p,FpsLimit,0); // blocked messages cannot change state', r'''
 p.CurPage=1;p.ApplyGraphicsTab();
 p.bConfirmMode=true;assert(!p.GraphicsProperty(0x26,p.GraphicsCells[FpsLimit].Choice,0));assert(!p.GraphicsDropdown->open);p.bConfirmMode=false;
 p.GraphicsProperty(0x26,p.GraphicsCells[FpsLimit].Choice,0);assert(p.GraphicsDropdown->choices.size()==8);
 p.GraphicsProperty(0x3e,p.GraphicsDropdown,0);assert(p.GraphicsValues[FpsLimit]==1);
 Select(p,FpsLimit,7);assert(p.GraphicsValues[FpsLimit]==8);
 for(int index=0;index<=Maximum(FpsLimit);++index)assert(Fps(index)>0 && Fps(index)<=180);
 assert(p.GraphicsHint->position[1]<p.GraphicsCells[FpsLimit].Label->position[1]-.03f);
 assert(p.GraphicsHint->position[1]-.027f>-.26f);
 p.SetGraphicsHidden(true);assert(!p.GraphicsDropdown->open && p.GraphicsDropdownRow==-1);
 p.CurPage=2;p.SetGraphicsHidden(false);Select(p,Shadows,999);assert(p.GraphicsValues[Shadows]==1);
 p.GraphicsProperty(0x26,p.DefaultsButton,0);assert(p.GraphicsValues[Shadows]==1);
 p.CurPage=1;p.ApplyGraphicsTab();p.GraphicsProperty(0x26,p.DefaultsButton,0);
 assert(p.GraphicsValues[VSync]==Default(VSync) && p.GraphicsValues[FpsLimit]==Default(FpsLimit));
 assert(p.GraphicsValues[Shadows]==1);
 assert(ColorGrade::Preset()==0);
 p.bInGame=true;p.Anim=-2;p.CurPage=1;
 p.GraphicsProperty(0x26,p.ColorGradeCell.Choice,0);assert(p.GraphicsDropdown->choices.size()==4);
 p.GraphicsProperty(0x3e,p.GraphicsDropdown,2);assert(ColorGrade::Preset()==2&&ColorGrade::ConfiguredPreset()==0);
 SavePerfOptions("PerfOptions.ini");p.RevertGraphics();assert(ColorGrade::Preset()==0);
 p.GraphicsProperty(0x26,p.ColorGradeCell.Choice,0);p.GraphicsProperty(0x3e,p.GraphicsDropdown,3);
 p.CommitGraphics();p.SnapshotGraphics();assert(ColorGrade::ConfiguredPreset()==3&&!p.GraphicsDirty());
 for(int i=0;i<Count;++i)Set(i,Maximum(i)-Default(i));
 for(unsigned i=0;i<kOptionCount;++i)sprintf_s(G_Options[i].Name,"legacy_%u",i);
 SavePerfOptions("PerfOptions.ini");
 char path[MAX_PATH];GetFullPathNameA("PerfOptions.ini",MAX_PATH,path,nullptr);
 assert(GetPrivateProfileIntA("PerfCount","count",0,path)==36);
 assert(GetPrivateProfileIntA("HUD","hud_tilt_degrees",0,path)==24);
 assert(GetPrivateProfileIntA("Display","color_bpp",0,path)==32);
 puts("PASS: migration, invalid input, render gates, quality caps, UI staging/cancel/apply/defaults, persistence");
''')
(out/'check.cpp').write_text(stub+common+grade+save+room_scope+ui+checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',f'/I{root/"src/include"}',f'/I{root/"src/freelancer/Client"}','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
for mode in ('legacy0','legacy9','legacy10','room_scope','old_effects','quality_effects','exercise','reload'):
    subprocess.run([str(out/'check.exe'),mode],cwd=out,check=True)
for mode in ('gpu_first','gpu_manual','gpu_unknown','gpu_discrete'):
    subprocess.run([str(out/'check.exe'),mode],cwd=out,check=True)
