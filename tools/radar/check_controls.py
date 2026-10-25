"""Exercise production radar parent filtering and zoom handlers/layout with engine stubs."""
import os
from pathlib import Path
import subprocess
repo=Path(__file__).resolve().parents[2]
out=repo/'src/obj/radar_controls_check'
out.mkdir(parents=True,exist_ok=True)
source=(repo/'src/freelancer/Client/hud_radar.cpp').read_text()
def function(signature):
    start=source.index(signature);end=source.index('{',start)+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
stub=r'''
#include <cassert>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include "../../freelancer/Client/radar_projection.h"
struct Id {unsigned value=0;bool IsEmpty()const{return value==0;}};
namespace Archetype {struct Solar {bool bRadarMining=false,bRadarHidden=false;};struct Scanner {float RadarRange=1000;};}
struct Vector {float x=0,y=0,z=0;};
struct CObject {enum{ClassSolar=0x303};unsigned ObjectClass=0;};
struct CSolar:CObject {Id parent;Archetype::Solar arch;Id const& GetParentNickname()const{return parent;}
Archetype::Solar const* solararch()const{return &arch;}};
struct CEScanner {Archetype::Scanner arch;Archetype::Scanner const* ScannerArch()const{return &arch;}};
struct IObjRW {CObject* object=nullptr;bool dying=false;float interference=0;Vector pos;
CObject* cobject(){return object;}bool is_dying(){return dying;}
float get_scanner_interference(){return interference;}Vector const& get_position(){return pos;}};
bool mouseBlocked=false;bool HudIsMousePickBlocked(){return mouseBlocked;}

constexpr unsigned kWin3DVisible=2;
struct WinControl {
    bool hidden=false;float offset[3]={},Offset[3]={},AttachPosition[3]={};
    unsigned Flags=2;WinControl* Parent=nullptr;
    virtual intptr_t SetProperty(int msg,uintptr_t a,uintptr_t){if(msg==1){hidden=a!=0;Flags=hidden?0:2;}return 0;}
    void SetOffset(float x,float y,float z){Offset[0]=offset[0]=x;Offset[1]=offset[1]=y;Offset[2]=offset[2]=z;}
    void SetOrientation(float const*){}
};
struct NnButtonControl:WinControl {
    unsigned char flags=2;
    void SetFlags331(unsigned char v){flags=v;}unsigned char GetFlags331(){return flags;}
};
struct Camera {
    int view[4]={0,0,1919,1079};
    float XScale=1200,YScale=-1200,ScreenCenterX=960,ScreenCenterY=540;
    int const* GetViewport(){return view;}
} fixtureCamera;
Camera* GetCamera=&fixtureCamera;
Camera* Win3DGetCamera(){return GetCamera;}
bool auxiliaryMinimized=false;
bool AreAuxiliaryHudWindowsMinimized(){return auxiliaryMinimized;}
bool overlay=false;bool G_bNnScreenUp=false;
constexpr int kGameOptInterfaceGroup=0,kGameOptHud=1;
bool GetGameOption(int){return true;}
bool IsLetterboxVisible(){return overlay;}
bool IsSpaceInitInProgress(){return false;}
bool GetClientMouseCursorDrawFlag(){return true;}
bool GetPlayerObjRW(){return true;}
unsigned savedRange=0;
unsigned GetSavedRadarRange(unsigned fallback){return savedRange?savedRange-1:fallback;}
void SetSavedRadarRange(unsigned v){savedRange=v+1;}
bool radarOn=false;
bool GetSavedRadarEnabled(){return radarOn;}
void SetSavedRadarEnabled(bool v){radarOn=v;}
struct HUD_Radar:WinControl {
    WinControl* toggleButton=nullptr;WinControl* background=nullptr;
    WinControl* zoomButtons[2]={};int rangeIndex=2;unsigned defaultRangeIndex=2;bool enabled=true;
    float centerX=.5f,centerY=.845f,radius=.30f,ellipse=.32f,elevation=.94f;
    bool CanShow()const;
    void UpdateButtons();intptr_t SetProperty(int,uintptr_t,uintptr_t)override;
};
'''
checks=r'''
int main(){
    CSolar solar;solar.ObjectClass=CObject::ClassSolar;
    assert(!IsParentedSolar(nullptr)&&!IsParentedSolar(&solar));
    solar.parent.value=123;assert(IsParentedSolar(&solar));
    solar.ObjectClass=0x503;assert(!IsParentedSolar(&solar)); // Ship is not a child solar.
    HUD_Radar radar;NnButtonControl plus,minus,toggle;WinControl bg;
    radar.zoomButtons[0]=&plus;radar.zoomButtons[1]=&minus;radar.toggleButton=&toggle;radar.background=&bg;
    radar.UpdateButtons();assert(plus.hidden&&minus.hidden&&bg.hidden&&!toggle.hidden);
    assert(toggle.Offset[0]==-.195f && toggle.Offset[1]==-.37f && toggle.Offset[2]==0);
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&plus),0);assert(radar.rangeIndex==2);
    assert(radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&toggle),0));assert(radarOn&&!bg.hidden&&bg.offset[2]==-1.f);
    radar.UpdateButtons();assert(!plus.hidden&&!minus.hidden&&(plus.flags&2)&&!(minus.flags&2));
    auxiliaryMinimized=true;radar.UpdateButtons();assert(!bg.hidden&&!toggle.hidden&&!plus.hidden);
    auxiliaryMinimized=false;radar.UpdateButtons();assert(!bg.hidden);
    overlay=true;radar.UpdateButtons();assert(bg.hidden&&toggle.hidden);
    overlay=false;radar.UpdateButtons();
    auto const originalRadius=radar.radius;
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&plus),0);assert(radar.rangeIndex==1);
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&plus),0);assert(radar.rangeIndex==0&&!(plus.flags&2));
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&plus),0);assert(radar.rangeIndex==0);
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&minus),0);assert(radar.rangeIndex==1);
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&minus),0);assert(radar.rangeIndex==2&&!(minus.flags&2));
    assert(radar.radius==originalRadius); // Range buttons never resize the circle.
    // Existing HUD restores another player's saved range and clears to its INI default.
    savedRange=1;radar.UpdateButtons();assert(radar.rangeIndex==0&&!(plus.flags&2));
    savedRange=0;radar.UpdateButtons();assert(radar.rangeIndex==2&&!(minus.flags&2));
    radar.SetProperty(0x26,0,0);assert(radar.rangeIndex==2);
    radar.enabled=false;radar.UpdateButtons();assert(plus.hidden&&minus.hidden);
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&plus),0);assert(radar.rangeIndex==2);
    radar.enabled=true;GetCamera=nullptr;radar.UpdateButtons();assert(plus.hidden);
    GetCamera=&fixtureCamera;
    for(int width:{1024,1920,3440}) {
        fixtureCamera.view[0]=50;fixtureCamera.view[1]=30;fixtureCamera.view[2]=width+49;fixtureCamera.view[3]=1109;
        fixtureCamera.ScreenCenterX=50+width*.5f;fixtureCamera.ScreenCenterY=570;
        radar.UpdateButtons();assert(!plus.hidden&&!minus.hidden);
        RadarProjection::Layout l;
        assert(RadarProjection::MakeLayout({50,30,width+49,1109},.5f,.845f,.30f,.32f,.94f,l));
        float const px=fixtureCamera.ScreenCenterX+plus.offset[0]*fixtureCamera.XScale;
        float const mx=fixtureCamera.ScreenCenterX+minus.offset[0]*fixtureCamera.XScale;
        float const y=fixtureCamera.ScreenCenterY+plus.offset[1]*fixtureCamera.YScale;
        float const tx=fixtureCamera.ScreenCenterX+toggle.offset[0]*fixtureCamera.XScale;
        assert(tx<l.x && px>l.x && mx>px);
        assert(std::fabs(y-(l.y+l.radius*l.ellipse))<.001f); // At the front rim.
    }
    radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&toggle),0);
    assert(!radarOn&&plus.hidden&&minus.hidden&&bg.hidden&&!toggle.hidden);
    mouseBlocked=true;radar.SetProperty(0x26,reinterpret_cast<uintptr_t>(&toggle),0);assert(!radarOn);
    mouseBlocked=false;radar.enabled=false;radar.UpdateButtons();assert(toggle.hidden);
    // Only tagged mining solars bypass the native targetability restriction.
    CSolar rock;rock.ObjectClass=CObject::ClassSolar;IObjRW contact;contact.object=&rock;
    contact.pos={100,0,0};CEScanner scanner;Vector origin;
    assert(!MiningInRange(&contact,&scanner,origin,1000)); // Decoration/cloud, no tag.
    rock.arch.bRadarMining=true;assert(MiningInRange(&contact,&scanner,origin,1000));
    assert(!MiningInRange(&contact,&scanner,origin,50)); // Zoom remains range-limited.
    contact.interference=.95f;assert(!MiningInRange(&contact,&scanner,origin,1000));
    contact.interference=0;rock.arch.bRadarHidden=true;assert(!MiningInRange(&contact,&scanner,origin,1000));
    rock.arch.bRadarHidden=false;rock.parent.value=1;assert(!MiningInRange(&contact,&scanner,origin,1000));
    rock.parent.value=0;contact.dying=true;assert(!MiningInRange(&contact,&scanner,origin,1000));
    contact.dying=false;rock.ObjectClass=0x503;assert(!MiningInRange(&contact,&scanner,origin,1000));
    assert(!MiningInRange(nullptr,&scanner,origin,1000));
    puts("PASS: mining opt-in/interference/parent filters, central toggle, input blocking, zoom handlers and constant circle size");
}
'''
code=stub+''.join(function(sig) for sig in ['bool IsParentedSolar(', 'Archetype::Solar const* SolarArch(',
    'bool MiningInRange(', 'bool HUD_Radar::CanShow() const', 'void HUD_Radar::UpdateButtons(', 'intptr_t HUD_Radar::SetProperty('])+checks
(out/'check.cpp').write_text(code)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(str(p) for p in [vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB']=';'.join(str(p) for p in [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,check=True)
