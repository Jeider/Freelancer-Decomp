"""Run production mode enumeration, dropdown routing and apply/revert against device stubs."""
from pathlib import Path
import os
import subprocess

root=Path(__file__).resolve().parents[2]
client=root/'src/freelancer/Client'
out=root/'src/obj/video_modes_check'
out.mkdir(parents=True,exist_ok=True)
text=(client/'nn_preferences.cpp').read_text()
def block(start):
    body=text.index('{',start);end=body+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]+'\n'
def function(signature):return block(text.index(signature))
mode_case=block(text.index('        case 0x536:',text.index('void NnPreferences::SetSliderOption(')))
stub=r'''
#define FREELANCER_WIDESCREEN_SUPPORT
#define _CRT_SECURE_NO_WARNINGS
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cwchar>
#include <string>
#include <vector>
constexpr int kPrefVideoResolutionCount=24,kPrefVideoModeCount=48;
struct FPrefVideoMode {int Width,Height,Bpp;};
struct FPipelineDisplayMode {int Index,Width,Height,RefreshRate,Format,Field14;};
struct DisplaySettings {int pad[2]={},width=1920,height=1080,color_bpp=32,depth_bpp=24,tail[4]={};} g_display;
static_assert(sizeof(DisplaySettings)==0x28);
struct {void* window=nullptr;} g_client;
struct PixelDesc {int Bpp;};
PixelDesc const* PixelFormatGetDesc(int format){static PixelDesc d;d.Bpp=format;return &d;}
int PixelFormatFromD3D(int){return 0;}
void WidescreenGetDesktopSize(int* w,int* h){*w=1920;*h=1080;}
struct Pipeline {
    std::vector<FPipelineDisplayMode> modes;
    void GetDisplayModeCount(unsigned* n){*n=unsigned(modes.size());}
    int GetDisplayModeEnum(unsigned i,FPipelineDisplayMode* m){*m=modes[i];return 0;}
    void QueryDeviceAbility(int,unsigned long* out){*out=8*1024*1024;} // no legacy VRAM gate for 32-bit UI
} pipeline;
namespace DALib {auto* Pipeline=&pipeline;}
unsigned applies=0;
void ResetGameflowRoomLetterbox(){}
void SetRenderModeWithFallback(void*,DisplaySettings* m){g_display=*m;++applies;}
struct Win3D {unsigned Flags=3;};
struct WireButtonControl:Win3D {};
struct UiScroll:Win3D {unsigned value=0;intptr_t SetProperty(int msg,uintptr_t a,uintptr_t){if(msg==0x38)value=unsigned(a);return 0;}};
struct NnTextControl:Win3D {std::wstring text;intptr_t SetProperty(int,uintptr_t a,uintptr_t){text=reinterpret_cast<wchar_t const*>(a);return 0;}};
struct NnDropdownPopup:Win3D {
    bool open=false;int selected=-1;std::vector<std::wstring> choices;
    bool Open(float,float,float,std::vector<std::wstring> const& c,int s){open=true;choices=c;selected=s;return true;}
    void Close(){open=false;}
};
struct NnPreferences {
    FPrefVideoMode Modes[kPrefVideoModeCount]={};int CycleIndex[kPrefVideoModeCount]={};
    unsigned char bModeAvail[kPrefVideoModeCount]={},bBigVram=0,bInGame=0,bCur32=1,bSel32=1;
    int ModeCount=0,CurPage=1,CurWidth=1920,SelWidth=1920;double ConfirmCountdown=0;
    bool bFlipping=false,bClosingAnim=false,bConfirmMode=false,bVideoConfirm=false;
    WireButtonControl choiceControl;UiScroll cycle;NnTextControl caption;NnDropdownPopup popup;
    WireButtonControl* VideoModeChoice=&choiceControl;UiScroll* VideoModeCycle=&cycle;
    NnTextControl* VideoModeText=&caption;NnDropdownPopup* VideoModeDropdown=&popup;
    float VideoModeAnchorTop=.15f;
    NnDropdownPopup* GraphicsDropdown=nullptr;int GraphicsDropdownRow=-1;
    struct Row {int Id=-1;} OptionsA[14];
    void RefreshRows(int id){assert(id==0x57e);}
    bool FindVideoMode(DisplaySettings*,int,int,int)const;
    void ProbeModes(int);
    bool VideoModeProperty(int,Win3D*,uintptr_t);
    bool TryApplyVideoMode(int,unsigned char);
    void SetSliderOption(int Id,int Value,int Row);
};
'''
production='\n'.join(function(s) for s in (
    'void BuildWidescreenModeTable(', 'bool NnPreferences::FindVideoMode(',
    'void NnPreferences::ProbeModes(', 'bool NnPreferences::VideoModeProperty(',
    'bool NnPreferences::TryApplyVideoMode('))
production+='void NnPreferences::SetSliderOption(int Id,int Value,int Row){wchar_t Text[64];switch(Id){'+mode_case+'default:assert(false);}}\n'
checks=r'''
void Add(int w,int h,int bpp,int hz=60){pipeline.modes.push_back({0,w,h,hz,bpp,0});}
int main(){
    Add(1920,1080,32);Add(800,600,32);Add(1280,960,16);Add(1280,720,32);
    Add(1280,720,32,144);Add(1920,1080,16);Add(1024,768,16);Add(640,480,32);
    NnPreferences p;p.OptionsA[2].Id=0x536;
    BuildWidescreenModeTable(p.Modes);p.ProbeModes(-1);
    assert(p.ModeCount==3); // 16-bit-only and unsupported tiny modes are absent.
    for(int i=0;i<kPrefVideoResolutionCount;++i)assert(p.CycleIndex[i]==-1);
    assert(p.VideoModeProperty(0x26,p.VideoModeChoice,0));
    assert((p.popup.choices==std::vector<std::wstring>{L"800 x 600",L"1280 x 720",L"1920 x 1080"}));
    assert(p.popup.selected==2&&applies==0);
    p.VideoModeProperty(0x3e,p.VideoModeDropdown,1);
    assert(!p.popup.open&&p.SelWidth==1280&&p.bSel32&&p.cycle.value==1&&p.caption.text==L"1280 x 720"&&applies==0);
    assert(p.TryApplyVideoMode(p.SelWidth,p.bSel32));
    assert(g_display.width==1280&&g_display.height==720&&g_display.color_bpp==32&&p.ConfirmCountdown==10);
    assert(p.TryApplyVideoMode(p.CurWidth,p.bCur32)); // same rollback path as timeout/Cancel
    assert(g_display.width==1920&&g_display.height==1080&&g_display.color_bpp==32);
    p.VideoModeProperty(0x3e,p.VideoModeDropdown,999);assert(p.SelWidth==1280);
    p.bVideoConfirm=true;p.VideoModeProperty(0x3e,p.VideoModeDropdown,0);assert(p.SelWidth==1280);
    p.bVideoConfirm=false;p.CurPage=7;p.VideoModeProperty(0x26,p.VideoModeChoice,0);assert(!p.popup.open);
    // A 16-bit session can still be restored internally, although it is not listed.
    g_display.color_bpp=16;p.CurPage=1;
    assert(p.TryApplyVideoMode(1280,1));assert(p.TryApplyVideoMode(p.CurWidth,p.bCur32));
    assert(g_display.width==1920&&g_display.color_bpp==16);
    // Device order and refresh variants never affect the ascending list.
    pipeline.modes.clear();
    for(int i=23;i>=0;--i){Add(800+80*i,600+60*i,32);Add(800+80*i,600+60*i,32,120);}
    BuildWidescreenModeTable(p.Modes);p.ProbeModes(-1);assert(p.ModeCount==24);
    p.VideoModeProperty(0x26,p.VideoModeChoice,0);assert(p.popup.choices.size()==24);
    assert(p.popup.choices.front()==L"800 x 600"&&p.popup.choices.back()==L"2640 x 1980");
    pipeline.modes.clear();p.ProbeModes(-1);p.popup.Close();
    p.VideoModeProperty(0x26,p.VideoModeChoice,0);assert(!p.popup.open);
    puts("PASS: ascending 32-bit-only choices, refresh deduplication, 24 modes, staged selection, apply/rollback, legacy rollback and invalid/stale input");
}
'''
(out/'check.cpp').write_text(stub+production+checks)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');v='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/v/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/v/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,check=True)
