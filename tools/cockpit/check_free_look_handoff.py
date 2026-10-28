"""Run production free-look input transitions with mocked device/HUD boundaries."""
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/cockpit_handoff_check'
out.mkdir(parents=True, exist_ok=True)
source = (root / 'src/freelancer/Client/cockpit_free_look.cpp').read_text()

def function(signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]

stub = r'''
#include "../../freelancer/Client/cockpit_free_look_state.h"
#include <cassert>
#include <cstdio>
using CockpitFreeLook::State;
State Look;
bool Captured=false,LockedCapture=false,OwnLeftButton=false,EatReleaseFrame=false,EatMoveFrame=false,SavedFlightLock=false;
int SavedX=0,SavedY=0,x=100,y=200;
bool camera=true,input=true,hover=false,flightLock=false;
unsigned buttons=0;
int clears=0;
int G_RenderSurfaceWidth=800,G_RenderSurfaceHeight=600,kGameOptInverseMouse=0;
float G_CockpitHeadTurnX=30,G_CockpitHeadTurnY=25;
struct FMouseEvent {bool bMove=false;int ButtonIndex=0;struct {int Byte18=0;} Record;};
bool CameraAvailable(){return camera;}
bool InputAvailable(){return input;}
void GetClientSoftwareCursor(int* a,int* b,int* c){*a=x;*b=y;*c=0;}
void SetClientSoftwareCursor(int a,int b){x=a;y=b;}
unsigned GetClientMouseButtons(){return buttons;}
bool IsMouseFlightLockRequested(){return flightLock;}
bool IsMouseFlightLocked(){return flightLock && !Look.enabled;}
void SetMouseFlightLockRequested(bool value){flightLock=value;}
int GetGameOption(int){return 0;}
void ClearMouseFlightSteering(){++clears;}
bool CanBeginAtCursor(){return Look.enabled && !Look.waitingForRelease && input && !hover;}
void Reset();
'''
checks = r'''
int main(){
    for(bool initialLock : {false,true}) for(bool exitByReset : {false,true}){
        Look={};Captured=LockedCapture=OwnLeftButton=EatReleaseFrame=EatMoveFrame=false;
        camera=input=true;hover=true;buttons=0;flightLock=initialLock;
        Toggle();assert(Look.enabled && SavedFlightLock==initialLock);
        MouseFrame(true,0,0);hover=false;
        flightLock=true;MouseFrame(true,10,0);assert(Captured && LockedCapture);
        // Space releases the cursor to click the icon. It must not alter the
        // flight mode that the player had before entering cockpit look.
        flightLock=false;MouseFrame(true,0,0);assert(!Captured);
        Look.currentYaw=.2f;
        if(exitByReset)Reset();else Toggle();
        assert(!Look.enabled && !Captured && flightLock==initialLock);
        CockpitHeadMotion::State head;head.yaw=.2f;
        assert(!Look.Step(head,30,25,1.f/60));assert(head.yaw==.2f);
        assert(!MouseFrame(true,7,3));
        FMouseEvent move;move.bMove=true;assert(!ConsumeMouseEvent(move));
        FMouseEvent press;press.Record.Byte18=1;assert(!ConsumeMouseEvent(press));
        FMouseEvent release;assert(!ConsumeMouseEvent(release));
        if(initialLock)assert(x==400 && y==300);
    }
    // Lost camera during a swallowed LMB press: consume its matching release
    // once, then let fresh presses/movement reach normal steering.
    Look={};flightLock=false;buttons=0;hover=false;
    Toggle();MouseFrame(true,0,0);
    FMouseEvent down;down.Record.Byte18=1;buttons=1;
    assert(ConsumeMouseEvent(down));assert(Captured && OwnLeftButton);
    camera=false;MouseFrame(true,0,0);assert(!Look.enabled && !Captured);
    buttons=0;MouseFrame(true,0,0);FMouseEvent up;assert(ConsumeMouseEvent(up));
    camera=true;MouseFrame(true,0,0);
    assert(!ConsumeMouseEvent(down));assert(!ConsumeMouseEvent(up));
    puts("PASS: production free-look toggle/reset, Space lock restoration, immediate camera handoff, mouse release ownership");
}
'''
body = '\n'.join(function(s) for s in ('void ReleaseCursor()', 'void EndDrag()',
    'void BeginDrag(', 'void Toggle()', 'void Reset()', 'void Suspend()',
    'bool MouseFrame(', 'bool ConsumeMouseEvent('))
(out / 'check.cpp').write_text(stub + body + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT',
                'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out/'check.exe')], cwd=out, check=True)
