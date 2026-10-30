"""Run the production Misc page against native-widget and persistence stubs."""
from pathlib import Path
import os
import re
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/misc_settings_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/nn_preferences_misc.cpp').read_text(encoding='ascii')
source = source[source.index('namespace\n{'):]
header = (repo / 'src/freelancer/Client/nn_preferences.h').read_text()
rows = header[header.index('struct FPrefOption\n'):header.index('// One key map row')]
options = (repo / 'src/freelancer/Client/game_options.cpp').read_text()
options = options[options.index('namespace\n{'):]
preferences = (repo / 'src/freelancer/Client/nn_preferences.cpp').read_text()
start = preferences.index('    if (!bSeedMode)\n', preferences.index('// The original Interface "Miscellaneous"'))
move = preferences[start:preferences.index('    if (bSeedMode != 0)', start)]
# The native confirmation and transitions must reach the new page handlers.
assert 'if (CurPage == 7 && !CommitMisc())' in preferences
for fragment in ('case 7: EnterMiscPage(); return;', 'case 7: LeaveMiscPage(); break;',
                 'if (CurPage == 7) { RevertMisc(); return; }',
                 'if (CurPage == 7) { SetMiscHidden(bHide); return; }'):
    assert fragment in preferences
assert preferences.count('case 7: EnterMiscPage(); break;') == 2  # In-game and main-menu flip.
scroll_source = (repo / 'src/freelancer/Client/ui_scroll.cpp').read_text(encoding='utf-8')
def function(signature):
    start = scroll_source.index(signature)
    end = scroll_source.index('\n}', start) + 2
    return scroll_source[start:end] + '\n'
scroll_methods = function('void UiScroll::ClampValues()') + function('void UiScroll::WheelStep(bool bUp)') + function('bool UiScroll::SetStep(float Step)')
start = scroll_source.index('    case 0x37:', scroll_source.index('UiScroll::SetProperty('))
scroll_cases = scroll_source[start:scroll_source.index('    default:', start)]

stub = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <map>
#include "hud_tilt.h"
#define FREELANCER_RP9
#define FREELANCER_WIDESCREEN_SUPPORT
#define FREELANCER_PLAYER_AUTO_TURRETS
#define FREELANCER_PLAYER_FLIGHT_ACTIONS
struct Server { unsigned word=0,sends=0; void SetInterfaceState(unsigned,unsigned char* p,int size) {
    assert(size==4);memcpy(&word,p,4);++sends;
}} server;
Server* G_Server=&server;
unsigned GetPlayerConnectionId(){return 1;}
constexpr int MAX_PATH=260;
bool GetUserDataPath(char* out){strcpy_s(out,MAX_PATH,"mock-user");return true;}
std::map<std::string,std::string> navigationIni;
std::string hudProfile;
unsigned hudWrites=0;
unsigned navigationWrites=0;bool failNavigationWrite=false;
unsigned GetLastError(){return 5;}
#define FDUMP(...) ((void)0)
unsigned GetPrivateProfileStringA(char const*,char const* key,char const* fallback,char* out,unsigned size,char const* path){
    if(strcmp(path,"mock-user\\hud_preferences.ini")==0){strcpy_s(out,size,hudProfile.c_str());return unsigned(hudProfile.size());}
    auto it=navigationIni.find(key);strcpy_s(out,size,it==navigationIni.end()?fallback:it->second.c_str());return unsigned(strlen(out));
}
bool WritePrivateProfileStringA(char const*,char const* key,char const* value,char const* path){
    if(strcmp(path,"mock-user\\hud_preferences.ini")==0){hudProfile=value;++hudWrites;return true;}
    assert(strcmp(path,"mock-user\\navigation.ini")==0);
    if(failNavigationWrite)return false;
    navigationIni[key]=value;++navigationWrites;return true;
}
'''
controls = r'''
constexpr unsigned kWin3DPickable=8,kWin3DVisible=2;
constexpr unsigned long G_NnPaletteArgb_679bb0=1,G_NnPaletteArgb_679b94=2,G_NnPaletteArgb_679ba4=3;
struct Win3D { virtual ~Win3D()=default; };
struct WinControl:Win3D {
    bool mockHidden=true;unsigned Flags=kWin3DPickable;float offset[3]={};
    virtual intptr_t SetProperty(int msg,uintptr_t a,uintptr_t) {if(msg==1){mockHidden=a==1;Flags=mockHidden?(Flags&~3u):(Flags|3u);}return 0;}
    void SetOffset(float x,float y,float z){offset[0]=x;offset[1]=y;offset[2]=z;}
};
struct NnTextControl:WinControl {
    std::wstring caption;float width=0,height=0;unsigned long TextColour=0;
    void SetText(wchar_t const* t){caption=t;}void SetWidth(float v){width=v;}
};
struct NnButtonControl:WinControl {
    unsigned char ButtonBits2=2;unsigned char Colour[4]={};int toggleState=0;
    void SetMontageMode(int){}
    intptr_t SetProperty(int msg,uintptr_t a,uintptr_t b)override {
        if(msg==0x30)toggleState=a==0?1:0;
        return WinControl::SetProperty(msg,a,b);
    }
};
struct WireStaticControl:WinControl {float half[3]={};unsigned char WireState=0,Colour[4]={};};
struct WireButtonControl:WireStaticControl {unsigned char ButtonState=4;bool bUseColour=false;};
struct NnDropdownPopup:WinControl {
    bool open=false;int selected=0;std::vector<std::wstring> choices;
    bool Open(float,float,float,std::vector<std::wstring> const& values,int value){choices=values;selected=value;open=true;return true;}
    void Close(){open=false;}bool IsOpen(){return open;}void Draw(){}
};
void DrawNnDropdownCaret(WireButtonControl const*){}
NnDropdownPopup* CreateNnDropdownPopup(WinControl*);
struct UiScroll:WinControl {
    float RangeMin_=0,RangeMax_=0,Value_=0,Page_=0,DefaultPage_=0,Step_=1,width=0,height=0;
    bool bStepMode_=false,horizontal=false;
    void SetStepMode(bool v){bStepMode_=v;}void SetPageField(float v){Page_=v;}
    void ClampValues();void WheelStep(bool);bool SetStep(float);void Relayout(){}void NotifyParent(){}
    intptr_t SetProperty(int Msg,uintptr_t A,uintptr_t B)override;
};
int callbacks=0;
void Applied(float){++callbacks;}
struct FPerfOption {int Id;float Value,Applied;void (*Apply)(float);};
std::vector<FPerfOption> perf;
FPerfOption* FindPerfOptionByIds(int id){for(auto& p:perf)if(p.Id==id)return &p;return nullptr;}
char const* PortLanguage(){return "ru";}
int PortConfigInt(char const* section,char const*,int fallback){return strcmp(section,"AutoTurrets")==0?35:fallback;}
unsigned PortConfigString(char const*,char const*,char const* fallback,char* out,unsigned size){strcpy_s(out,size,fallback);return unsigned(strlen(out));}
bool singlePlayer=true;bool SinglePlayer(){return singlePlayer;}
void GetIdsStringWWithRawFallback(unsigned id,wchar_t* text,int count){
    swprintf_s(text,count,L"IDS%u",id);
}
namespace PlayerAutoTurrets {
    bool feature=true;enum class Mode{Manual,Hostiles};
    bool Enabled(){return feature;}void Reconcile(){}
    Mode GetMode(){return GetSavedAutoTurretsEnabled(false)?Mode::Hostiles:Mode::Manual;}
    unsigned ReservePercent(){return GetSavedAutoTurretReserve(35);}
    void SetMode(Mode m){SetSavedAutoTurretsEnabled(m==Mode::Hostiles);}
    void SetReservePercent(unsigned value){SetSavedAutoTurretReserve(value);}
}
'''
page = r'''
FPrefOption BlankOption(){FPrefOption p={};p.Id=p.InfoIds=p.Default=p.Min=p.Max=-1;return p;}
struct NnPreferences:WinControl {
    bool bSeedMode=false,bInGame=true,bFlipping=false,bDirty=false,bConfirmMode=false;
    int CurPage=1,MiscTop=0;static constexpr int MiscVisibleRows=11;
    int MiscTab=0;bool MiscSaveFailed=false;
    WireButtonControl* MiscTabButtons[2]={};NnTextControl* MiscTabTexts[2]={};
    NnTextControl* MiscSaveHint=nullptr;std::vector<int> MiscRowIndices;
    NnButtonControl* MiscButton=nullptr;NnTextControl* MiscText=nullptr;
    std::vector<FPrefOption> OptionsA,MiscOptions;std::vector<FPrefMiscRow> MiscRows;
    std::vector<WinControl*> MiscWidgets,owned;FPrefMiscCell MiscCells[MiscVisibleRows];
    UiScroll* MiscScroll=nullptr;
    NnDropdownPopup* MiscDropdown=nullptr;int MiscDropdownRow=-1;
    NnTextControl title,cancelText,defaultsText;
    WireButtonControl cancel,defaults;
    NnTextControl *Title=&title,*CancelText=&cancelText,*DefaultsText=&defaultsText;
    WireButtonControl *CancelButton=&cancel,*DefaultsButton=&defaults;
    ~NnPreferences(){for(auto* c:owned)delete c;}
    template<class T>T* Own(T* c){owned.push_back(c);return c;}
    template<class... T>WinControl* CreateButtonControl(char const*,T...){return Own(new NnButtonControl);}
    NnTextControl* CreateTextControl(char const*,char const*,float const* at,char const*,float w,float h,float,unsigned,int,int,unsigned char corner){
        assert(corner==1);auto* c=Own(new NnTextControl);memcpy(c->offset,at,sizeof(c->offset));c->width=w;c->height=h;return c;
    }
    template<class... T>WinControl* CreateToggleButtonControl(char const*,char const* checked,char const* unchecked,T...){
        assert(strstr(checked,"check.3db")&&strstr(unchecked,"repairblackbox.3db"));return Own(new NnButtonControl);
    }
    template<class... T>WinControl* CreateWireStaticControl(char const*,float const* at,float const* half,T...){
        auto* c=Own(new WireStaticControl);memcpy(c->offset,at,sizeof(c->offset));memcpy(c->half,half,sizeof(c->half));return c;
    }
    template<class... T>WinControl* CreateWireButtonControl(char const*,char const*,float const* at,float const* half,T...){
        auto* c=Own(new WireButtonControl);memcpy(c->offset,at,sizeof(c->offset));memcpy(c->half,half,sizeof(c->half));return c;
    }
    UiScroll* CreateUICycle(char const*,float const* at,float w,float h,int lo,int hi,int size,unsigned char horizontal){
        auto* c=Own(new UiScroll);memcpy(c->offset,at,sizeof(c->offset));c->width=w;c->height=h;
        c->horizontal=horizontal!=0;
        c->RangeMin_=float(lo);c->RangeMax_=float(hi);c->DefaultPage_=c->Page_=float(size);return c;
    }
    UiScroll* CreateUIScroll(char const* name,float const* at,float w,float h,int lo,int hi,int size,unsigned char horizontal){
        return CreateUICycle(name,at,w,h,lo,hi,size,horizontal);
    }
    void ShowConfirmDialog(bool show){bConfirmMode=show;SetMiscHidden(show);}
    bool CreateMiscPage(float,float,float);
    void EnterMiscPage();void LeaveMiscPage();void SetMiscHidden(bool);void RefreshMiscRows();
    void SnapshotMisc();bool CommitMisc();void RevertMisc();bool MiscProperty(int,Win3D*,uintptr_t);
    void CloseMiscDropdown();void DrawMiscDropdown();
    void MoveOptions();
};
NnDropdownPopup* CreateNnDropdownPopup(WinControl* owner){return static_cast<NnPreferences*>(owner)->Own(new NnDropdownPopup);}
'''
checks = r'''
FPrefOption Option(int id,bool header=false){auto p=BlankOption();p.Id=id;p.bHeader=header;p.Default=1;return p;}
void Globals(NnPreferences& p){
    p.OptionsA={Option(1894,true),Option(1334),Option(1897,true)};
    for(int id:{1400,1401,1495,1555,1498})p.OptionsA.push_back(Option(id));
    p.OptionsA.push_back(Option(1898,true));p.OptionsA.push_back(Option(777));
    p.MoveOptions();
    assert(p.MiscOptions.size()==5&&p.OptionsA.size()==15&&p.OptionsA[0].Id==1334&&p.OptionsA[1].Id==1898&&p.OptionsA[2].Id==777);
}
void Enter(NnPreferences& p){p.EnterMiscPage();assert(p.CurPage==7&&p.bFlipping);p.EnterMiscPage();p.bFlipping=false;}
void Toggle(NnPreferences& p,int slot){
    auto* c=p.MiscCells[slot].Toggle;
    auto const before=p.MiscRows[p.MiscRowIndices[p.MiscTop+slot]].Value;
    p.MiscProperty(0x26,c,0);assert(before==p.MiscRows[p.MiscRowIndices[p.MiscTop+slot]].Value);
    c->toggleState=1-c->toggleState;
    p.MiscProperty(0x30,c,c->toggleState);
}
void Select(NnPreferences& p,int slot,unsigned value){
    float const before=p.MiscRows[p.MiscRowIndices[p.MiscTop+slot]].Value;
    p.MiscProperty(0x26,p.MiscCells[slot].Choice,0);
    assert(p.MiscDropdown->IsOpen()&&p.MiscRows[p.MiscRowIndices[p.MiscTop+slot]].Value==before);
    assert(value<p.MiscDropdown->choices.size());
    p.MiscProperty(0x3e,p.MiscDropdown,value);
    assert(!p.MiscDropdown->IsOpen());
}
int main(){
    for(int id:{1400,1401,1495,1555,1498})perf.push_back({id,1,1,Applied});
    NnPreferences p;Globals(p);assert(p.CreateMiscPage(-.3f,.205f,.077f));
    AssignGameSessionFlags(3);SetSavedRadarAutoMode(2);SetSavedAutoTurretsEnabled(true);SetSavedAutoTurretReserve(35);
    auto const baseline=server.word,writes=server.sends;
    Enter(p);assert(!p.bDirty&&p.MiscRows.size()==15&&p.MiscRowIndices.size()==10&&p.MiscScroll->mockHidden);
    assert(p.MiscRowIndices[0]==2); // The two help options moved to Navigation.
    for(int i=0;i<8;++i){auto& c=p.MiscCells[i];assert(!c.Label->mockHidden&&!c.Value->mockHidden);
        assert(c.Label->offset[2]==0&&c.ValueRule->offset[2]==0&&c.Cycle->offset[2]==-1);
        assert(c.Label->offset[0]+c.Label->width<c.ValueRule->offset[0]-c.ValueRule->half[0]);
        assert(c.Value->offset[0]>=c.ValueRule->offset[0]-c.ValueRule->half[0]);
        assert(c.Value->offset[0]+c.Value->width<=c.ValueRule->offset[0]+c.ValueRule->half[0]);
        assert(c.Cycle->mockHidden==(i!=7)&&c.Toggle->mockHidden==(i==3||i==7));
        assert(c.Choice->mockHidden==(i!=3));
        assert(c.Cycle->width==.012f&&c.Cycle->height==.025f);
        assert(c.Cycle->offset[0]>=c.ArrowRule->offset[0]-c.ArrowRule->half[0]);
        assert(c.Cycle->offset[0]+c.Cycle->width<=c.ArrowRule->offset[0]+c.ArrowRule->half[0]);
    }
    assert(p.MiscCells[10].ValueRule->mockHidden&&p.MiscCells[10].Cycle->mockHidden);
    // Tilt is a degree selector on General, not a navigation toggle or save flag.
    assert(p.MiscRows[13].Setting==8 && p.MiscRows[13].Tab==0);
    assert(!p.MiscCells[8].Cycle->mockHidden && p.MiscCells[8].Toggle->mockHidden);
    assert(HudTilt::ConfiguredAngle()==0);
    // One upper/lower arrow step must increase/decrease the numeric value.
    for(int slot:{7,8}){
        auto* cycle=p.MiscCells[slot].Cycle;
        int const row=p.MiscRowIndices[slot];float const initial=p.MiscRows[row].Value;
        cycle->WheelStep(true);p.MiscProperty(0x3e,cycle,cycle->SetProperty(0x3b,0,0));
        assert(p.MiscRows[row].Value==initial+(slot==8?2:5));
        cycle->WheelStep(false);p.MiscProperty(0x3e,cycle,cycle->SetProperty(0x3b,0,0));
        assert(p.MiscRows[row].Value==initial);
    }
    for(bool up:{false,true}){
        auto* cycle=p.MiscCells[8].Cycle;
        for(int i=0;i<60;++i){cycle->WheelStep(up);p.MiscProperty(0x3e,cycle,cycle->SetProperty(0x3b,0,0));}
        assert(p.MiscRows[13].Value==(up?50:0));
    }
    p.MiscProperty(0x3e,p.MiscCells[8].Cycle,12);
    assert(p.MiscRows[13].Value==12 && HudTilt::ConfiguredAngle()==0);
    p.MiscProperty(0x26,p.MiscTabButtons[1],0);
    p.MiscProperty(0x26,p.MiscTabButtons[0],0);
    assert(p.MiscRows[13].Value==12);
    p.RevertMisc();assert(p.MiscRows[13].Value==0);
    p.MiscProperty(0x3e,p.MiscCells[8].Cycle,99);
    assert(p.MiscRows[13].Value==50);
    assert(p.CommitMisc());p.SnapshotMisc();p.RefreshMiscRows();
    assert(HudTilt::ConfiguredAngle()==50 && server.sends==writes && navigationWrites==0);
    p.MiscProperty(0x26,p.DefaultsButton,0);
    assert(p.MiscRows[13].Value==0 && HudTilt::ConfiguredAngle()==50);
    p.RevertMisc();assert(p.MiscRows[13].Value==50);
    p.MiscProperty(0x3e,p.MiscCells[8].Cycle,0);
    assert(p.CommitMisc());p.SnapshotMisc();p.RefreshMiscRows();
    assert(HudTilt::ConfiguredAngle()==0);
    // Exercise the real native clamp and arrow step, including both end values.
    for(int slot:{7}){
        auto* cycle=p.MiscCells[slot].Cycle;
        for(bool up:{false,true}){
            for(int i=0;i<30;++i){cycle->WheelStep(up);p.MiscProperty(0x3e,cycle,cycle->SetProperty(0x3b,0,0));}
            assert(p.MiscRows[slot+2].Value==(up?90:0));
        }
    }
    p.RevertMisc();assert(server.sends==writes);
    Toggle(p,0);assert(perf[2].Applied==0&&callbacks==1);
    Select(p,3,1);Toggle(p,4);Toggle(p,5);Toggle(p,6);
    p.MiscProperty(0x3e,p.MiscCells[7].Cycle,18);
    assert(p.bDirty&&server.word==baseline&&server.sends==writes);
    p.EnterMiscPage();assert(p.MiscRows[5].Value==1); // Frame updates do not reset edits.
    p.LeaveMiscPage();assert(p.bConfirmMode&&p.MiscCells[0].Label->mockHidden);
    p.RevertMisc();p.ShowConfirmDialog(false);p.LeaveMiscPage();
    assert(!p.bDirty&&perf[2].Applied==1&&callbacks==2&&server.sends==writes);
    p.CurPage=1;Enter(p);
    Toggle(p,0);Select(p,3,1);Toggle(p,5);Toggle(p,6);
    p.MiscProperty(0x3e,p.MiscCells[7].Cycle,18);
    p.CommitMisc();p.SnapshotMisc();p.RefreshMiscRows();
    assert(!p.bDirty&&GetSavedRadarAutoMode()==1&&GetSavedHealthWindowLocked());
    assert(!GetSavedAutoTurretsEnabled(true)&&GetSavedAutoTurretReserve(0)==90);
    auto const committed=server.word,acceptedWrites=server.sends;
    p.MiscProperty(0x26,p.DefaultsButton,0);assert(p.bDirty&&server.sends==acceptedWrites);
    assert(p.MiscRows[5].Value==0&&p.MiscRows[7].Value==1&&p.MiscRows[9].Value==35);
    p.MiscProperty(0x26,p.CancelButton,0);
    assert(!p.bDirty&&server.word==committed&&server.sends==acceptedWrites&&perf[2].Applied==0);
    p.LeaveMiscPage();AssignGameSessionFlags(3);p.CurPage=1;Enter(p);
    assert(p.MiscRows[5].Value==1&&p.MiscRows[7].Value==0&&p.MiscRows[9].Value==90);
    NnPreferences main;main.bInGame=false;Globals(main);assert(main.CreateMiscPage(-.33f,.21f,.085f));Enter(main);
    auto const mainWrites=server.sends;
    assert(!main.MiscCells[8].Cycle->mockHidden);
    assert(!main.MiscCells[3].Choice->mockHidden && !main.MiscCells[4].Toggle->mockHidden);
    assert(!main.MiscCells[5].Toggle->mockHidden && !main.MiscCells[9].Toggle->mockHidden);
    Toggle(main,9);assert(GetShowWeaponGroups());
    main.CommitMisc();main.SnapshotMisc();main.RefreshMiscRows();
    assert(!main.bDirty && !GetShowWeaponGroups() && server.sends==mainWrites);
    main.MiscProperty(0x26,main.DefaultsButton,0);assert(perf[2].Applied==1);main.RevertMisc();assert(perf[2].Applied==0);
    // Navigation edits survive tab switches, remain staged until Apply, persist
    // across a fresh settings load and are available in the main menu too.
    p.MiscProperty(0x26,p.MiscTabButtons[1],0);
    assert(p.MiscTab==1&&p.MiscRowIndices.size()==5&&p.MiscRowIndices[0]==0&&p.MiscRowIndices[1]==1);
    assert(p.MiscRowIndices[2]==10&&p.MiscRows[10].Value==1);
    assert(!p.MiscCells[2].Choice->mockHidden&&p.MiscCells[2].Cycle->mockHidden&&p.MiscCells[5].Label->mockHidden);
    for(bool up:{true,false}) {
        Select(p,2,up?0:1);
        assert(p.MiscRows[10].Value==(up?0.f:1.f));
    }
    Toggle(p,0);Select(p,2,0);Toggle(p,3);Toggle(p,4);
    assert(navigationWrites==0&&NavigationSettings::Get(NavigationSettings::Autopilot)==1);
    p.MiscProperty(0x26,p.MiscTabButtons[0],0);assert(p.bDirty);
    p.MiscProperty(0x26,p.MiscTabButtons[1],0);assert(p.MiscRows[10].Value==0);
    p.RevertMisc();assert(navigationWrites==0&&perf[0].Applied==1);
    Select(p,2,0);Toggle(p,3);Toggle(p,4);
    failNavigationWrite=true;assert(!p.CommitMisc()&&p.MiscSaveFailed&&p.bDirty);
    assert(navigationWrites==0&&NavigationSettings::Get(NavigationSettings::Generator)==1);
    failNavigationWrite=false;assert(p.CommitMisc());p.SnapshotMisc();p.RefreshMiscRows();
    assert(!p.bDirty&&navigationWrites==3&&navigationIni["route_generator"]=="retail");
    NavigationSettings::loaded=false;for(auto& value:NavigationSettings::values)value=-1;
    assert(!NavigationSettings::Get(NavigationSettings::Generator)&&!NavigationSettings::Get(NavigationSettings::Autopilot)&&!NavigationSettings::Get(NavigationSettings::AutoDock));
    main.MiscProperty(0x26,main.MiscTabButtons[1],0);
    for(int i=0;i<5;++i)assert(!main.MiscCells[i].Label->mockHidden);
    assert(!main.MiscCells[2].Choice->mockHidden&&!main.MiscCells[3].Toggle->mockHidden);
    p.MiscProperty(0x26,p.DefaultsButton,0);assert(p.bDirty&&p.MiscRows[10].Value==1&&p.MiscRows[11].Value==1&&p.MiscRows[12].Value==1);
    assert(navigationWrites==3&&perf[2].Applied==0); // Defaults only affect the selected tab.
    p.RevertMisc();assert(p.MiscRows[10].Value==0);
    // Opening/cancelling a list changes nothing; tab changes discard its owner
    // so a stale choice notification cannot edit the newly visible row.
    p.MiscProperty(0x26,p.MiscCells[2].Choice,0);assert(p.MiscDropdown->IsOpen());
    p.MiscProperty(0x26,p.MiscTabButtons[0],0);assert(!p.MiscDropdown->IsOpen());
    float const generator=p.MiscRows[10].Value;
    p.MiscProperty(0x3e,p.MiscDropdown,1);assert(p.MiscRows[10].Value==generator);
    for(int i=0;i<15;++i)p.MiscRows.push_back(p.MiscRows[2]);
    p.RefreshMiscRows();assert(!p.MiscScroll->mockHidden);
    for(bool up:{false,true}){
        for(int i=0;i<30;++i){
            auto* s=p.MiscScroll;s->SetProperty(0x38,int(s->Value_)+(up?-2:2),0);
            p.MiscProperty(0x3e,s,s->SetProperty(0x3b,0,0));
        }
        assert(p.MiscTop==(up?0:14));
    }
    p.MiscProperty(0x3e,p.MiscScroll,999);assert(p.MiscTop==14&&p.MiscScroll->Value_==14);
    NnPreferences seed;seed.bSeedMode=true;seed.OptionsA={Option(1897,true),Option(1400)};seed.MoveOptions();
    assert(seed.OptionsA.size()==2&&seed.MiscOptions.empty());
    puts("PASS: General/Navigation tabs; help migration; generator/F2/autodock persistence, Apply/Cancel/defaults and write failure; main-menu access; native widgets, HUD save isolation and page lifecycle");
}
'''
navigation = re.sub(r'^#include[^\n]*\n', '', (repo / 'src/freelancer/Client/navigation_settings.cpp').read_text(), flags=re.M)
navigation_header = (repo / 'src/freelancer/Client/navigation_settings.h').read_text().replace('#pragma once','')
(out / 'check.cpp').write_text(stub + options + controls + navigation_header + navigation + scroll_methods +
    'intptr_t UiScroll::SetProperty(int Msg,uintptr_t A,uintptr_t B){switch(Msg){\n' + scroll_cases +
    'default:return WinControl::SetProperty(Msg,A,B);}}\n' + rows + page +
    'void NnPreferences::MoveOptions(){\n' + move + '}\n' + source + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB'] = ';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',f'/I{repo/"src/freelancer/Client"}','check.cpp',str(repo/'src/freelancer/Client/hud_tilt.cpp'),'/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,check=True)
