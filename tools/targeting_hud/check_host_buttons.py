"""Run host layout through production button attachment/position methods."""
import os
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/targeting_host_check'
out.mkdir(parents=True, exist_ok=True)


def function(file, signature):
    source = (repo / 'src/freelancer/Client' / file).read_text()
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


code = r'''
#include "../../freelancer/Client/hud_interface_ids.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <initializer_list>
struct WinControl;
struct Win3D {
    float Position[3]={};
    Win3D *Parent=nullptr,*ChildHead=nullptr,*NextSibling=nullptr;
    virtual void SetPosition(float const* p){std::memcpy(Position,p,sizeof(Position));}
    virtual WinControl* AsWinControl(){return nullptr;}
};
struct WinControl:Win3D {
    float Offset[3]={},AttachPosition[3]={};
    unsigned PositionFlags=1,bAttached=0;
    struct {void* EngineInstance=nullptr;} MeshHolder;
    WinControl* AsWinControl()override{return this;}
    void SetPosition(float const*)override;
    void GetAttachPosition(float*);
    void SetOffset(float,float,float);
    void AddAttachOffset(float const* p){for(int i=0;i<3;++i)AttachPosition[i]+=p[i];}
    bool hidden=false,selected=false;
    void SetProperty(int msg,int value,int){if(msg==1)hidden=value!=0;if(msg==0xc)selected=value!=0;}
};
struct NnButtonControl:WinControl {
    float Field2e0[3]={};
    void SetPosition(float const*)override;
};
bool HasInstance(WinControl* p){return p->MeshHolder.EngineInstance!=nullptr;}
struct EngineStub {
    void SetInstancePosition(void* instance,float const* p){std::memcpy(instance,p,3*sizeof(float));}
    void UpdateInstance(void*,int,void*){}
} engine;
namespace DALib {EngineStub* Engine=&engine;}
void SetInstancePositionAndUpdate(void* instance,float const* p){engine.SetInstancePosition(instance,p);}
struct ButtonMover {bool active=false;bool IsActive(){return active;}};
struct ButtonScaler {bool active=false;bool IsActive(){return active;}};
struct HudTarget:WinControl,ButtonMover,ButtonScaler {
    bool bExpanded=true;
    WinControl *ContactListButton=nullptr,*TargetButton=nullptr,*ScanButton=nullptr,*FormationButton=nullptr;
};
struct HUD_Targeting {
    HudTarget* owner=nullptr;
    WinControl *windowButton=nullptr,*lockButton=nullptr;
    struct {bool open=true,locked=false;} windowState;
    HudTarget* Source(){return owner;}
    bool CanShow(){return true;}
    void UpdateHostButtons();
};
struct HUD_Status:WinControl,ButtonMover,ButtonScaler {
    bool bExpanded=true;
    WinControl *RepairButton=nullptr,*RepairCountText=nullptr,*UseBatteryButton=nullptr,*BatteryCountText=nullptr;
};
struct {int current=0;int GetCurrent(){return current;}} G_WeaponGroups;
bool healthLocked=false;
bool GetSavedHealthWindowLocked(){return healthLocked;}
struct HUD_Health {
    HUD_Status* owner=nullptr;
    WinControl *hostButton=nullptr,*lockButton=nullptr,*groups[3]={};
    struct {bool open=true;} windowState;
    bool canShow=true;
    HUD_Status* Source(){return owner;}
    bool CanShow(){return canShow;}
    void UpdateHostButtons();
};
'''
for file, signature in (
    ('wincontrol_base.cpp', 'void WinControl::GetAttachPosition('),
    ('wincontrol_base.cpp', 'void WinControl::SetPosition('),
    ('wincontrol_base.cpp', 'void WinControl::SetOffset('),
    ('nn_button_control.cpp', 'void NnButtonControl::SetPosition('),
    ('hud_targeting.cpp', 'void HUD_Targeting::UpdateHostButtons('),
    ('hud_health.cpp', 'void HUD_Health::UpdateHostButtons('),
):
    code += '\n' + function(file, signature)
code += r'''
int main(){
    for(bool expanded:{false,true})for(bool mesh:{false,true}){
        HudTarget host;host.bExpanded=expanded;
        host.Position[0]=.07f;host.Position[1]=.03f;
        NnButtonControl anchor,oldTarget,scan,formation,window,lock;
        float windowInstance[3]={},lockInstance[3]={};
        for(auto* p:{&anchor,&oldTarget,&scan,&formation,&window,&lock}){
            p->Parent=&host;p->AttachPosition[0]=.01f;p->AttachPosition[1]=.02f;p->AttachPosition[2]=-1;
        }
        if(mesh){window.MeshHolder.EngineInstance=windowInstance;lock.MeshHolder.EngineInstance=lockInstance;}
        host.ContactListButton=&anchor;host.TargetButton=&oldTarget;host.ScanButton=&scan;host.FormationButton=&formation;
        anchor.SetOffset(expanded?-.295f:-.343f,expanded?-.171f:-.37f,0);
        scan.SetOffset(expanded?-.397f:-.411f,anchor.Offset[1],0);
        HUD_Targeting panel;panel.owner=&host;panel.windowButton=&window;panel.lockButton=&lock;
        panel.UpdateHostButtons();
        // Reproduce the old double attach after an otherwise correct layout.
        window.SetPosition(anchor.Position);
        assert(window.Position[2]==-2);
        for(int frame=0;frame<3;++frame){
            panel.UpdateHostButtons();
            for(int i=0;i<3;++i){
                assert(window.Position[i]==anchor.Position[i]);
                assert(lock.Position[i]==anchor.Position[i]);
                assert(window.Offset[i]==anchor.Offset[i]);
                if(mesh){
                    assert(windowInstance[i]==anchor.Position[i]+anchor.Offset[i]);
                    assert(lockInstance[i]==lock.Position[i]+lock.Offset[i]);
                }
            }
            assert(std::abs(lock.Offset[0]-anchor.Offset[0]+.034f)<.000001f);
            assert(lock.Offset[1]==anchor.Offset[1]&&lock.Offset[2]==anchor.Offset[2]);
        }
    }
    puts("PASS: reproduced double-attachment depth error; host buttons match anchor position/depth in both layouts and mesh/montage paths, stable across frames");
    for(bool expanded:{false,true}){
        HUD_Status host;host.bExpanded=expanded;host.Position[0]=.07f;host.Position[1]=.03f;
        NnButtonControl health,lock,repair,repairCount,battery,batteryCount,g1,g2,g3;
        float instances[4][3]={};
        HUD_Health panel;panel.owner=&host;panel.hostButton=&health;panel.lockButton=&lock;
        panel.groups[0]=&g1;panel.groups[1]=&g2;panel.groups[2]=&g3;
        host.RepairButton=&repair;host.RepairCountText=&repairCount;
        host.UseBatteryButton=&battery;host.BatteryCountText=&batteryCount;
        for(auto* p:{&health,&lock,&repair,&repairCount,&battery,&batteryCount,&g1,&g2,&g3}){
            p->Parent=&host;p->AttachPosition[0]=.01f;p->AttachPosition[1]=.02f;p->AttachPosition[2]=-1;
        }
        health.MeshHolder.EngineInstance=instances[0];
        for(int i=0;i<3;++i)panel.groups[i]->MeshHolder.EngineInstance=instances[i+1];
        for(int current=0;current<6;++current){
            G_WeaponGroups.current=current;
            for(int frame=0;frame<3;++frame){
                panel.UpdateHostButtons();
                assert(!health.hidden&&health.selected);
                assert(health.Position[2]==-1);
                assert(health.Offset[0]<repair.Offset[0]&&repair.Offset[0]<repairCount.Offset[0]);
                assert(repairCount.Offset[0]+.034f<battery.Offset[0]);
                assert(battery.Offset[0]<batteryCount.Offset[0]);
                assert(batteryCount.Offset[0]+.034f<.513f);
                assert(lock.Offset[0]>health.Offset[0] && lock.Offset[0]+.01556f<repair.Offset[0]-.015f);
                assert(!lock.hidden && lock.Position[2]==-1);
                assert(std::abs(lock.Offset[0]-health.Offset[0]-.034f)<.000001f);
                assert(g1.Offset[0]==g2.Offset[0]&&g2.Offset[0]==g3.Offset[0]);
                assert(g1.Offset[0]+.013f<.270f); // Native weapon numbers start here.
                assert(g1.Offset[1]<-.205f && g3.Offset[1]-.014f>-.385f);
                assert(std::abs((g1.Offset[1]-g2.Offset[1])-.024f)<.000001f);
                assert(std::abs((g1.Offset[1]-g2.Offset[1])-(g2.Offset[1]-g3.Offset[1]))<.000001f);
                if(expanded)assert(batteryCount.Offset[0]+.034f<.49f);
                for(int i=0;i<3;++i){
                    auto* p=panel.groups[i];assert(p->selected==(current==i)&&p->hidden==!expanded);
                    for(int axis=0;axis<3;++axis){
                        assert(p->Position[axis]==health.Position[axis]);
                        assert(instances[i+1][axis]==p->Position[axis]+p->Offset[axis]);
                    }
                    assert(p->Offset[1]<repair.Offset[1] || !expanded);
                }
            }
        }
        // A live native animation owns its positions; custom controls hide until it ends.
        host.ButtonMover::active=true;repair.SetOffset(.1f,-.4f,0);panel.UpdateHostButtons();
        assert(health.hidden&&g1.hidden&&g2.hidden&&g3.hidden&&repair.Offset[0]==.1f);
        host.ButtonMover::active=false;panel.windowState.open=false;panel.UpdateHostButtons();
        assert(!health.hidden&&!health.selected);
        healthLocked=true;panel.UpdateHostButtons();assert(lock.selected);
        healthLocked=false;panel.UpdateHostButtons();assert(!lock.selected);
        panel.canShow=false;panel.UpdateHostButtons();assert(health.hidden&&g1.hidden);
        panel.owner=nullptr;panel.UpdateHostButtons();
    }
    puts("PASS: Health/lock order, right-aligned consumables, vertical groups and collapsed hiding, count clearance, mesh placement, six-group selection sync, animation ownership and HUD gates in both layouts");
}
'''
(out / 'check.cpp').write_text(code)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include'] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)
