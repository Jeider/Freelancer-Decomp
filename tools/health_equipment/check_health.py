"""Run Health's production button creation, visibility and dispatch with native-control doubles."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'src/obj/health_equipment_tests'
OUT.mkdir(parents=True, exist_ok=True)
source=(ROOT/'src/freelancer/Client/hud_health.cpp').read_text()
def method(signature):
    start=source.index(signature); end=source.index('\n}',start)+2
    return source[start:end]
creation=source[source.index('    // A single row across Health'):source.index('    ViewPanel->Flags &=')]
code=r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <cstring>
#include <vector>
#include <cmath>
#include <algorithm>
#include "hud_interface_ids.h"
constexpr unsigned kWin3DPickable=8, kWin3DVisible=2, kWin3DActive=1;
constexpr unsigned G_NnPaletteArgb_679ba4=1,G_NnPaletteArgb_679bb0=2;
constexpr unsigned SUBOBJ_ID_NONE=0xffff;
struct WinControl {
    unsigned Flags=kWin3DPickable; bool mockSelected=false, spin=true; unsigned tip=0;
    std::string mockMesh;float x=0,y=0,hx=0,hy=0;
    virtual ~WinControl()=default;
    virtual intptr_t SetProperty(int msg,uintptr_t a,uintptr_t){
        if(msg==1)Flags=a?Flags&~kWin3DVisible:Flags|kWin3DVisible;
        if(msg==0xc)mockSelected=a!=0; if(msg==0x36)spin=a!=0;if(msg==3)tip=unsigned(a);return 0;
    }
};
struct NnButtonControl:WinControl {
    unsigned char flags331=2;
    unsigned char GetFlags331(){return flags331;}void SetFlags331(unsigned char f){flags331=f;}
};
struct NnTextControl:WinControl {unsigned TextColour=0;std::wstring text;void SetText(wchar_t const* t){text=t;}};
struct CEquip {bool destroyed=false,active=false;float hp=10,maxHp=10;bool IsDestroyed(){return destroyed;}bool IsActive(){return active;}
    float GetHitPoints(){return hp;}float GetMaxHitPoints(){return maxHp;}
    bool IsFunctioning(){return active&&!destroyed&&hp>0;}unsigned short GetID(){return 40;}};
struct CERepairDroid:CEquip {};
struct CECloakingDevice:CEquip {
    struct Arch {struct Settings {bool enabled=false;};Settings GetSettings(){return {};}} arch;
    int FadeTarget=0,BaselineState=0;
    bool CanToggle(){return !destroyed;}
    Arch* CloakArch(){return &arch;}
    float GetDurationRemaining(){return -1;}float GetCooldownRemaining(){return 0;}
};
struct IObjAffect{};struct IObjRW:IObjAffect{};IObjRW mockPlayer;
void* GetPlayerObjRW(){return &mockPlayer;}unsigned GetPlayerConnectionId(){return 1;}
int repairToggle=-1;
void CliShipActivateEquip(IObjAffect*,unsigned short const*,unsigned char on,int){repairToggle=on;}
CERepairDroid* mockDroid=nullptr;
constexpr unsigned EquipTypeCloak=1;
struct CObject {unsigned ObjectClass=0x503;};
struct CEqObj:CObject {struct {CEquip* cloak=nullptr;CEquip* FindFirst(unsigned){return cloak;}} EquipManager;};
CERepairDroid* FindRepairDroid(CObject* object){return object?mockDroid:nullptr;}
struct Host {unsigned command=0;bool OnEvent(unsigned id){command=id;return true;}};
struct {int current=0;int GetCurrent(){return current;}} G_WeaponGroups;
bool groupsVisible=true;
bool GetShowWeaponGroups(){return groupsVisible;}
bool WingAnimAvailable(){return true;}bool WingAnimPaused(){return false;}bool WingAnimCruiseLocked(){return false;}
int WingAnimDisplayState(){return 0;}bool WingAnimCanPause(){return true;}
void WingAnimRequestToggle(){}void WingAnimTogglePause(){}void WingAnimSetCruiseLocked(bool){}void SetSavedHealthViewLeft(bool){}
struct HUD_Health:WinControl {
    bool show=true,open=true,animating=false,bExpanded=false,viewLeft=false;
    unsigned SubTargetId=SUBOBJ_ID_NONE;
    Host host; CEqObj mockObject;
    struct {bool present=true;void* target(){return present?this:nullptr;}} ViewObject;
    struct {float X=.152f,Y=-.300f;} center;
    static constexpr float PanelHalfWidth=.0923861f;
    std::vector<WinControl*> owned;
    WinControl* toolbar[5]={};WinControl* weaponGroups[3]={};
    WinControl* repairDroidButton=nullptr;WinControl* cloakButton=nullptr;NnButtonControl slide;WinControl* slideIcon=&slide;
    WinControl* cloakTimerText=nullptr;int cloakTimerValue=-999;
    WinControl* repairDroidReserveText=nullptr;int repairDroidReserveValue=-1;
    struct ButtonMover {static bool IsActive(){return false;}};
    HUD_Health(){for(auto& c:toolbar){c=new NnButtonControl;owned.push_back(c);}}
    ~HUD_Health(){for(auto* c:owned)delete c;}
    Host* Source(){return &host;}bool CanShow(){return show;}bool IsAnimating(){return animating;}
    CObject* GetViewCObject(){return ViewObject.present?&mockObject:nullptr;}
    void UpdateHostButtons(){}
    void NormalizeIcon(WinControl*,int,float){}
    WinControl* CreateWireButtonControl(char const*,char const*,float const* pos,float const* half,int,int,int,int,int){
        auto* c=new NnButtonControl;c->x=pos[0];c->y=pos[1];c->hx=half[0];c->hy=half[1];owned.push_back(c);return c;
    }
    WinControl* CreateTextControl(char const*,char const*,float const*,void*,float,float,float,int,int,int,int){
        auto* c=new NnTextControl;owned.push_back(c);return c;
    }
    WinControl* CreateButtonControl(char const*,char const* mesh,void*,char const*,void*,float const* pos,void*,float const* half,int,int,int,int,int,int,int){
        auto* c=CreateWireButtonControl("","",pos,half,0,0,0,0,0); c->mockMesh=mesh; return c;
    }
    bool Create();void UpdateVisibility();intptr_t SetProperty(int,uintptr_t,uintptr_t)override;
};
'''
code+='bool HUD_Health::Create(){\n'+creation+'return true;\n}\n'
code+=method('void HUD_Health::UpdateVisibility()')+'\n'+method('intptr_t HUD_Health::SetProperty(')
code+=r'''
int main(){
    HUD_Health panel;assert(panel.Create());
    assert(!panel.cloakButton->spin);
    for(int i=0;i<3;++i){
        auto* c=panel.weaponGroups[i];
        char expected[80];sprintf_s(expected,"interface\\hud\\HUD_weaponsgroup%d.3db",i+1);
        assert(c->mockMesh==expected);
        assert(c->y==panel.cloakButton->y);
        assert(c->x-c->hx>=panel.center.X-panel.PanelHalfWidth);
        assert(panel.cloakButton->x+panel.cloakButton->hx<c->x-c->hx);
        assert(c->x+c->hx<panel.repairDroidButton->x-panel.repairDroidButton->hx);
        if(i)assert(panel.weaponGroups[i-1]->x+panel.weaponGroups[i-1]->hx<c->x-c->hx);
    }
    CECloakingDevice cloak;
    for(bool show:{false,true})for(bool open:{false,true})for(bool anim:{false,true})
    for(bool present:{false,true})for(bool groups:{false,true})for(bool hasCloak:{false,true}){
        panel.show=show;panel.open=open;panel.animating=anim;panel.ViewObject.present=present;
        groupsVisible=groups;panel.mockObject.EquipManager.cloak=hasCloak?&cloak:nullptr;
        panel.UpdateVisibility();
        bool const visible=show&&open&&!anim;
        assert(bool(panel.cloakButton->Flags&kWin3DVisible)==(visible&&present&&hasCloak));
        for(int i=0;i<3;++i){
            assert(bool(panel.weaponGroups[i]->Flags&kWin3DVisible)==(visible&&present&&groups));
            panel.host.command=0;
            panel.SetProperty(0x26,reinterpret_cast<uintptr_t>(panel.weaponGroups[i]),0);
            assert(panel.host.command==((visible&&groups)?unsigned(0x91+i):0));
        }
    }
    panel.show=panel.open=panel.ViewObject.present=true;panel.animating=false;groupsVisible=true;
    panel.mockObject.EquipManager.cloak=&cloak;
    for(bool destroyed:{false,true})for(bool active:{false,true}){
        cloak.destroyed=destroyed;cloak.active=active;panel.UpdateVisibility();
        assert(panel.cloakButton->mockSelected==active);
        assert(bool(static_cast<NnButtonControl*>(panel.cloakButton)->GetFlags331()&2)==!destroyed);
    }
    for(int i=0;i<6;++i){
        G_WeaponGroups.current=i;panel.UpdateVisibility();
        for(int j=0;j<3;++j)assert(panel.weaponGroups[j]->mockSelected==(i==j));
    }
    panel.SetProperty(0x26,reinterpret_cast<uintptr_t>(panel.cloakButton),0);assert(panel.host.command==0x8e);
    CERepairDroid droid;mockDroid=&droid;
    assert(panel.cloakButton->x<panel.center.X&&panel.repairDroidButton->x>panel.center.X);
    assert(panel.weaponGroups[2]->x+panel.weaponGroups[2]->hx<panel.repairDroidButton->x-panel.repairDroidButton->hx);
    for(bool destroyed:{false,true})for(bool active:{false,true})for(float hp:{0.f,10.f}){
        droid.destroyed=destroyed;droid.active=active;droid.hp=hp;panel.UpdateVisibility();
        assert(panel.repairDroidButton->Flags&kWin3DVisible);
        assert(panel.repairDroidButton->mockSelected==droid.IsFunctioning());
        repairToggle=-1;panel.SetProperty(0x26,reinterpret_cast<uintptr_t>(panel.repairDroidButton),0);
        assert(repairToggle==(!destroyed&&hp>0?int(!active):-1));
    }
    auto* reserve=static_cast<NnTextControl*>(panel.repairDroidReserveText);
    assert(!(reserve->Flags&(kWin3DPickable|kWin3DActive)));
    droid.destroyed=false;droid.active=false;droid.maxHp=10000;
    for(auto sample: {std::pair<float,wchar_t const*>{10000.f,L"100"}, {9900.f,L"99"},
                     {5000.f,L"50"}, {0.f,L"0"}, {20000.f,L"100"}, {-10.f,L"0"}}){
        droid.hp=sample.first;panel.UpdateVisibility();
        assert(reserve->Flags&kWin3DVisible);assert(reserve->text==sample.second);
    }
    droid.maxHp=0;panel.UpdateVisibility();assert(reserve->text==L"0");
    for(bool show:{false,true})for(bool open:{false,true})for(bool anim:{false,true})
    for(bool present:{false,true}){
        panel.show=show;panel.open=open;panel.animating=anim;panel.ViewObject.present=present;
        panel.UpdateVisibility();
        assert(bool(reserve->Flags&kWin3DVisible)==(show&&open&&!anim&&present));
    }
    panel.show=panel.open=panel.ViewObject.present=true;panel.animating=false;
    mockDroid=nullptr;panel.UpdateVisibility();assert(!(panel.repairDroidButton->Flags&kWin3DVisible));
    assert(!(reserve->Flags&kWin3DVisible));
    puts("PASS: opposite-side activators, non-overlapping group controls, repair reserve percentages and visibility; existing repair/cloak activation and depletion");
}
'''
(OUT/'health.cpp').write_text(code)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10'); ver='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/ver/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/ver/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',f'/I{ROOT/"src/freelancer/Client"}','health.cpp','/Fehealth.exe'],cwd=OUT,env=env,check=True)
subprocess.run([str(OUT/'health.exe')],cwd=OUT,check=True)
