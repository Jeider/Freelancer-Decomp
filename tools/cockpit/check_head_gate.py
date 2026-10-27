"""Exercise production cockpit input gating across autopilot/jump takeover."""
import os
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/cockpit_gate_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/space_camera_first.cpp').read_text()

def function(signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]

stub = r'''
#include "../../freelancer/Client/cockpit_head_motion.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
struct Vector {float x=1,y=-1,z=0;};
struct FVector {float X,Y,Z;};
struct FMatrix {float values[9];};
struct FFirstPersonCamera {float OrientationC[9]={},OrientationA[9]={},HeadOrientation[9]={};int bFlag1A0=0;};
struct IObjRW {bool lane=false;void is_using_tradelane(bool* out){*out=lane;}};
struct IBehaviorManager {unsigned char Opaque168[1]={1};bool turning=true;int reads=0;
    Vector LastCommandedDirection;
    bool get_user_turning_input_state(){++reads;return turning;}};
bool letterbox=false,blocked=false;
bool IsLetterboxVisible(){return letterbox;}
bool HudIsMousePickBlocked(){return blocked;}
FMatrix const& AsMatrix(float const* p){return *reinterpret_cast<FMatrix const*>(p);}
struct Math {void MulMatrix(FMatrix&,FMatrix const&,FMatrix const&){}
    void TransposeTransform(FVector& out,FMatrix const&,FVector const& in){out=in;}} math;
Math* FirstPersonMathEngine(){return &math;}
CockpitHeadMotion::State G_CockpitHeadMotion;
float G_CockpitHeadTurnX=30,G_CockpitHeadTurnY=25;
// Retain the old helper in the fixture so a regression to hard reset compiles and fails.
void ResetHeadLook(FFirstPersonCamera* cam){G_CockpitHeadMotion.Reset();G_CockpitHeadMotion.WriteOrientation(cam->OrientationC);}
'''
checks = r'''
int main(){
    constexpr float rad=CockpitHeadMotion::DegreesToRadians;
    for(int fps:{30,60,144}) for(int gate=0;gate<7;++gate){
        FFirstPersonCamera cam;IObjRW ship;IBehaviorManager manager;auto* active=&manager;
        letterbox=blocked=false;
        G_CockpitHeadMotion.pitch=15*rad;G_CockpitHeadMotion.yaw=-25*rad;
        switch(gate){
        case 0:manager.Opaque168[0]=0;break; // Autopilot takes the ship.
        case 1:letterbox=true;break; // Jump sequence.
        case 2:blocked=true;break; // HUD blocks control during transition.
        case 3:ship.lane=true;break;
        case 4:active=nullptr;break;
        case 5:cam.bFlag1A0=1;break;
        case 6:manager.turning=false;break;
        }
        auto const original=G_CockpitHeadMotion;
        UpdateHeadLook(&cam,&ship,active,0);
        assert(G_CockpitHeadMotion.pitch==original.pitch && G_CockpitHeadMotion.yaw==original.yaw);
        UpdateHeadLook(&cam,&ship,active,1.f/fps);
        assert(G_CockpitHeadMotion.yaw<0 && G_CockpitHeadMotion.yaw>original.yaw);
        assert(G_CockpitHeadMotion.pitch>0 && G_CockpitHeadMotion.pitch<original.pitch);
        assert(G_CockpitHeadMotion.yaw-original.yaw<=CockpitHeadMotion::MaxReturnRate/fps+.000001f);
        assert(std::fabs(cam.OrientationC[6]+std::sin(G_CockpitHeadMotion.yaw))<.000001f);
        for(int i=1;i<fps;++i) UpdateHeadLook(&cam,&ship,active,1.f/fps);
        assert(std::fabs(G_CockpitHeadMotion.yaw-original.yaw*std::exp(-1.f/.96f))<.00002f);
        if(gate<6) assert(manager.reads==0); // Blocked mouse input never reaches the head.
        auto const before=G_CockpitHeadMotion;
        letterbox=blocked=false;ship.lane=false;cam.bFlag1A0=0;
        manager.Opaque168[0]=1;manager.turning=true;
        UpdateHeadLook(&cam,&ship,&manager,1.f/fps);
        assert(G_CockpitHeadMotion.yaw<before.yaw);
        assert(before.yaw-G_CockpitHeadMotion.yaw<=CockpitHeadMotion::MaxTurnRate/fps+.000001f);
        manager.Opaque168[0]=0;
        for(int i=0;i<12*fps;++i) UpdateHeadLook(&cam,&ship,&manager,1.f/fps);
        assert(G_CockpitHeadMotion.yaw==0 && G_CockpitHeadMotion.pitch==0);
        assert(cam.OrientationC[0]==1 && cam.OrientationC[4]==1 && cam.OrientationC[8]==1);
    }
    puts("PASS: autopilot/jump/blocked input/tradelane/null manager, pause, smooth centring and resume at 30/60/144 FPS");
}
'''
(out / 'check.cpp').write_text(stub + function('void UpdateHeadLook(') + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT',
                'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out/'check.exe')], cwd=out, check=True)
