"""Exercise production service/panel transitions with fake controls and animation clocks."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def method(path, signature):
    source=(ROOT/path).read_text(encoding='utf-8-sig')
    start=source.index(signature)
    body=source.index('{',start)
    depth=1; end=body+1
    while depth:
        depth += (source[end]=='{')-(source[end]=='}')
        end+=1
    return source[start:end]+'\n'

stub=r'''
#include <cassert>
#include <cstdint>
#include <list>
#include <cstdio>
struct WinControl {
    unsigned char Flags=0;
    float HomeOffset[3]={};
    void SetProperty(int,uintptr_t,uintptr_t) {}
    void Slot23(int,int,int) {}
};
using Win3D=WinControl;
struct ButtonMover {
    bool active=false; int starts=0;
    bool IsActive() const { return active; }
    void Start(float) { active=true; ++starts; }
    void AddButton(WinControl*,const float*,const float*) {}
    void Finish() { active=false; }
};
struct ButtonScaler {
    bool active=false; int starts=0;
    bool IsActive() const { return active; }
    void Start(float) { active=true; ++starts; }
    void AddButton(WinControl*,float,float) {}
};
float kAnimSeconds=.2f;
void PlayOrRewindUiSoundSlot(int) {}
float NnFloatBits(unsigned) { return 0; }
bool G_bNnScreenUp=false;
struct Trade : WinControl {};
Trade* G_NnTrade=nullptr;
struct Server { void TerminateTrade(int,int) {} } server;
Server* G_Server=&server;
int GetPlayerConnectionId() { return 1; }
int NnPanelSlot(int id) { return id==0x66 ? 1 : 0; }
const char* NnPanelWindowName(int) { return "panel"; }
Win3D* Win3DFindByName(const char*) { return nullptr; }
void Win3DDeleteTree(WinControl*) {}
void HudPushCancelHandler(void*,int) {}
struct FNavBarButton { int bRoomSwitch=0,bOpen=1; unsigned Type=13; };
struct NavBar : ButtonMover,ButtonScaler {
    std::list<FNavBarButton> Buttons{FNavBarButton{}};
    FNavBarButton *ClosingButton=nullptr,*QueuedClose=nullptr;
    WinControl* ScaledBackground=nullptr;
    bool IsAnimating() const { return ButtonMover::IsActive() || ButtonScaler::IsActive(); }
    void CloseService(FNavBarButton*);
    void MakeServiceBackground(unsigned,float) {}
    float ServiceScale(unsigned) { return .05f; }
    static void NotifyServiceWindows();
} nav;
bool serviceWindow=true;
NavBar* FindNavBar() { return &nav; }
bool IsServiceType(unsigned) { return true; }
bool NavBarIsAnimating() { return nav.IsAnimating(); }
void NavBarCloseService(bool);
void NavBar::NotifyServiceWindows() {
    if (serviceWindow) { NavBarCloseService(false); serviceWindow=false; }
}
struct NN_MainButton : ButtonMover,ButtonScaler {
    WinControl *QueuedButton=nullptr,*OpenButton=nullptr,*ClosingButton=nullptr,*ScaledBackground=nullptr;
    int QueuedPanelId=0,OpenPanelId=0,ClosingPanelId=0,SavedToolTipIds=0,ClosingToolTipIds=0;
    bool bWaitingForServiceClose=false;
    unsigned char bInfoCardLayout=0;
    float OpenTarget[7][3]={},ClosingStart[3]={},PanelScale[7]={};
    void OpenPanel(WinControl*,int);
    void ResumeAfterServiceClose();
    void ClosePanel();
    void ResetPanel();
    void UpdateRootHighlights() {}
    void MakeScaledBackground(float) {}
    void* AsHudCmdHandler() { return this; }
};
void finishService() {
    nav.ButtonScaler::active=false;
    nav.ButtonMover::active=false;
    nav.Buttons.front().bOpen=0;
    nav.ClosingButton=nullptr;
}
void resetService() { nav=NavBar{}; serviceWindow=true; }
'''

tests=r'''
int main() {
    WinControl map,inventory;
    NN_MainButton panel;
    panel.OpenPanel(&map,0x63);
    assert(!serviceWindow && nav.IsAnimating());
    assert(nav.ButtonScaler::starts==1 && nav.QueuedClose==nullptr);
    assert(panel.OpenButton==nullptr && panel.ButtonMover::starts==0);
    for(int frame=0;frame<10;++frame) panel.ResumeAfterServiceClose();
    assert(panel.OpenButton==nullptr && panel.QueuedButton==&map);
    // Repeated requests must not restart or enqueue the closing service.
    panel.OpenPanel(&map,0x63);
    assert(nav.ButtonScaler::starts==1 && nav.QueuedClose==nullptr);
    finishService();
    panel.ResumeAfterServiceClose();
    assert(panel.OpenButton==&map && panel.ButtonMover::starts==1);
    assert(panel.QueuedButton==nullptr && !panel.bWaitingForServiceClose);
    panel.ResumeAfterServiceClose();
    assert(panel.ButtonMover::starts==1);

    resetService(); NN_MainButton latest;
    latest.OpenPanel(&map,0x63);
    latest.OpenPanel(&inventory,0x66);
    finishService(); latest.ResumeAfterServiceClose();
    assert(latest.OpenButton==&inventory && latest.OpenPanelId==0x66);

    resetService(); NN_MainButton cancelled;
    cancelled.OpenPanel(&map,0x63);
    cancelled.ClosePanel();
    finishService(); cancelled.ResumeAfterServiceClose();
    assert(cancelled.OpenButton==nullptr && cancelled.QueuedButton==nullptr);

    resetService(); NN_MainButton reset;
    reset.OpenPanel(&map,0x63); reset.ResetPanel();
    finishService(); reset.ResumeAfterServiceClose();
    assert(reset.OpenButton==nullptr && reset.QueuedButton==nullptr);

    // A new click after service completion replaces an unconsumed request.
    resetService(); NN_MainButton replaced;
    replaced.OpenPanel(&map,0x63); finishService();
    replaced.OpenPanel(&inventory,0x66);
    assert(replaced.OpenButton==&inventory && !replaced.bWaitingForServiceClose);
    assert(replaced.QueuedButton==nullptr);

    // Closing while the parking tab is still opening queues exactly once.
    resetService(); nav.ButtonMover::active=true;
    NavBarCloseService(true);
    assert(nav.QueuedClose==&nav.Buttons.front());
    nav.ButtonMover::active=false;
    nav.CloseService(&nav.Buttons.front());
    assert(nav.QueuedClose==nullptr && nav.ButtonScaler::starts==1);
    NavBarCloseService(true);
    assert(nav.QueuedClose==nullptr && nav.ButtonScaler::starts==1);
    puts("PASS: service closes before panel animation; duplicate close, queued open, replacement, cancel and reset");
}
'''

out=ROOT/'src/obj/ship_parking/window_transition'
out.mkdir(parents=True,exist_ok=True)
source=stub
for name in ('CloseService',''):
    signature='void NavBar::CloseService(' if name else 'void NavBarCloseService('
    source+=method('src/freelancer/Client/nav_bar.cpp',signature)
for name in ('OpenPanel','ResumeAfterServiceClose','ClosePanel','ResetPanel'):
    source+=method('src/freelancer/Client/nn_main_button.cpp','void NN_MainButton::'+name+'(')
source+=tests
(out/'test.cpp').write_text(source,encoding='utf-8')
compiler,env=compiler_env()
subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/W4','/MT',
                str(out/'test.cpp'),'/Fe:'+str(out/'test.exe'),'/Fo:'+str(out/'test.obj')],
               cwd=out,env=env,check=True)
subprocess.run([str(out/'test.exe')],cwd=out,check=True)
