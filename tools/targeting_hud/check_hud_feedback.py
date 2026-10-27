"""Exercise production caption toggles, cruise placement and ship-part tooltip scopes."""
import os
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/hud_feedback_check'
out.mkdir(parents=True, exist_ok=True)
client = repo / 'src/freelancer/Client'

def function(file, signature):
    text = (client / file).read_text()
    start = text.index(signature); end = text.index('{', start) + 1; depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}'); end += 1
    return text[start:end]

stub = r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cwchar>
#include <string>
#include <initializer_list>
#define FREELANCER_WIDESCREEN_SUPPORT
struct TextControl {unsigned Flags=3,ids=0;float x=0,y=0,z=0;std::wstring text;
 void SetProperty(int msg,uintptr_t a,uintptr_t){
  if(msg==1)Flags=a?Flags&~3u:Flags|3u;
  if(msg==0x1e)ids=unsigned(a);
  if(msg==0x1d)text=reinterpret_cast<wchar_t const*>(a);
 }
 void SetOffset(float a,float b,float c){x=a;y=b;z=c;}
 bool visible()const{return (Flags&2)!=0;}
};
bool radar=false,unlocked=false,held=false;
bool RadarIsEnabled(){return radar;}
bool RadarMessageAnchor(float& x,float& y){if(!radar)return false;x=.1f;y=-.12f;return true;}
bool IsMouseFlightUnlocked(){return unlocked;}bool IsMouseFlightHoldThresholdReached(){return held;}
struct CObject{unsigned ObjectClass=3;};
struct CSimple:CObject{unsigned TypeBits=0x80;};
struct IObjRW{CSimple object;CObject* cobject(){return &object;}};
struct IBehaviorManager{unsigned char Opaque168[1]={1};int DockingPortStatus=0,CurrentBehaviorIndex=0;};
struct CShip{bool lane=false;IBehaviorManager behavior;IObjRW target;
 bool is_using_tradelane(){return lane;}IBehaviorManager* get_behavior_interface(){return &behavior;}
 IObjRW* get_target(){return &target;}} ship;
IObjRW player;IObjRW* GetPlayerObjRW(){return &player;}
CShip* HudShipOfObjRw(IObjRW*){return &ship;}
struct Watchable{};struct Watcher{Watchable const* target(){return nullptr;}};
IObjRW* ObjRwFromWatchable(Watchable*){return nullptr;}
unsigned GetGameSessionLoadRevision(){return 0;}bool TestGameSessionFlags(int){return false;}
unsigned G_StatusSavedStateRevision=0;
unsigned char G_StatusLastMouseFlightUnlocked=0,G_StatusLastMouseFlightHoldReached=0;
bool G_StatusLastRadarEnabled=false;
wchar_t G_StatusScratchFormat[4096],G_StatusScratchLine[4096];constexpr int G_NnTextScratchCapacity=4096;
struct CaptionData{wchar_t const* Text=L"Destination";};
bool HudBuildObjectCaption(CSimple*,CaptionData*,int,bool){return true;}
int GetIdsStringWWithRawFallback(unsigned,wchar_t* out,int){wcscpy(out,L"%s");return 2;}
struct FKeyBindingLookup{};bool KeyMapFindActiveBinding(unsigned,FKeyBindingLookup*){return false;}
void KeyMapFormatBindingName(FKeyBindingLookup*,wchar_t*,int){}
struct HUD_Status{
 TextControl main,cancel;TextControl* SpecialModeText=&main;TextControl* SpecialModeTextCancel=&cancel;
 Watcher ViewObject;CaptionData Caption;int Byte500=0,Byte5cc=0,Byte5cd=0,bExpanded=0,bTurretView=0,bRearView=0;
 void Slot12(){}void Update();void UpdateSpecialModeCaptions();
};
float shift=0,expectedPickShift=0;
struct FWidescreenHudShiftScope{float previous;
 FWidescreenHudShiftScope(float value,bool):previous(shift){shift=value;}
 ~FWidescreenHudShiftScope(){shift=previous;}};
struct FToolTipHoverInfo {int Ids=0,IdsAlt=0,AuxField=0,bLive=0;wchar_t* CaptionW=nullptr;unsigned CaptionCapacity=0;
 ~FToolTipHoverInfo(){free(CaptionW);}};
bool mouseBlocked=false;bool HudIsMousePickBlocked(){return mouseBlocked;}
void GetClientSoftwareCursor(int* x,int* y,int* z){*x=1440;*y=900;*z=0;}
int feeds=0,fedId=0,fedAlt=0;bool fedCaption=false;
void NnToolTipFeedHover(FToolTipHoverInfo const* info){assert(shift==0);assert(info->bLive==0);
 ++feeds;fedId=info->Ids;fedAlt=info->IdsAlt;fedCaption=info->CaptionW!=nullptr;}
constexpr unsigned short SUBOBJ_ID_NONE=0;
struct HudTargetBase{unsigned short SubTargetId=0;unsigned ids=1234;int count=1;
 unsigned PickSubTarget(int x,int y,unsigned short* id,int* n){
  assert(shift==expectedPickShift&&x==1440&&y==900);*id=7;*n=count;return ids;}
 void UpdateSubTargetToolTip(bool showTooltip=true);
};
'''
update = function('hud_status_core.cpp', 'void HUD_Status::Update()')
update = update[:update.index('// 0x004db554..')] + '}\n'
cruise = (client / 'hud_cruise_progress.cpp').read_text()
placement = cruise[cruise.index('    float anchorX=0,anchorY=0;'):cruise.index('    wchar_t Line[0x3c]')]
checks = r'''
int main(){
 HUD_Status status;
 for(int mode=0;mode<6;++mode){
  ship={};status.bTurretView=mode==2;status.bRearView=mode==3;
  unlocked=mode==1;held=mode==1;
  if(mode==4){ship.behavior.Opaque168[0]=0;ship.behavior.DockingPortStatus=1;}
  if(mode==5)ship.lane=true;
  radar=false;status.UpdateSpecialModeCaptions();status.Update();
  bool const mainVisible=status.main.visible(),cancelVisible=status.cancel.visible();
  auto const mainIds=status.main.ids;auto const cancelText=status.cancel.text;
  if(mode==0)assert(mainVisible&&cancelVisible&&mainIds==0x62c);
  if(mode==1)assert(mainVisible&&!cancelVisible);
  if(mode==2)assert(mainVisible&&mainIds==0x633);
  if(mode==3)assert(mainVisible&&mainIds==0x62b);
  if(mode==4)assert(mainVisible&&mainIds==0x63b&&cancelVisible&&cancelText==L"Destination");
  if(mode==5)assert(!mainVisible&&cancelVisible&&cancelText==L"Destination");
  for(int repeat=0;repeat<3;++repeat){
   radar=true;status.Update();assert(!status.main.visible()&&!status.cancel.visible());
   status.UpdateSpecialModeCaptions();status.Update();assert(!status.main.visible()&&!status.cancel.visible());
   radar=false;status.Update();
   assert(status.main.visible()==mainVisible&&status.cancel.visible()==cancelVisible);
   if(mainVisible)assert(status.main.ids==mainIds);
   if(cancelVisible)assert(status.cancel.text==cancelText);
  }
 }
 TextControl cruise;
 for(int repeat=0;repeat<3;++repeat){
  radar=true;PlaceCruise(&cruise);assert(cruise.x==.1f-.2425f&&cruise.y==-.12f);
  radar=false;PlaceCruise(&cruise);assert(cruise.x==-.243f&&cruise.y==-.263f&&cruise.z==0);
 }
 for(float pixels:{-560.f,-240.f,0.f,240.f,560.f})for(int count:{1,2}){
  shift=expectedPickShift=pixels;HudTargetBase panel;panel.count=count;int const before=feeds;
  panel.UpdateSubTargetToolTip();assert(feeds==before+1&&shift==pixels&&panel.SubTargetId==7);
  assert(fedId==7&&fedCaption==(count>1));if(count==1)assert(fedAlt==1234);
  panel.UpdateSubTargetToolTip(false);assert(feeds==before+1&&shift==pixels);
  panel.ids=0;panel.UpdateSubTargetToolTip();assert(feeds==before+1&&panel.SubTargetId==0);
  mouseBlocked=true;panel.UpdateSubTargetToolTip();assert(feeds==before+1&&shift==pixels);mouseBlocked=false;
 }
 puts("PASS: radar toggles restore six native caption modes, cruise position round-trips, shifted ship-part tooltips use screen coordinates");
}
'''
code = stub + update + function('hud_status_core.cpp', 'void HUD_Status::UpdateSpecialModeCaptions()')
code += '\nvoid PlaceCruise(TextControl* Text){\n' + placement + '}\n'
code += function('hud_target.cpp', 'void HudTargetBase::UpdateSubTargetToolTip(') + checks
(out / 'check.cpp').write_text(code)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT',
                '/D_CRT_SECURE_NO_WARNINGS', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out/'check.exe')], cwd=out, check=True)
