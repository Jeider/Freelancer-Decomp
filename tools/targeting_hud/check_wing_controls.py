"""Exercise the actual WingAnim controller with a deterministic playback/ship backend."""
import os
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/wing_controls_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/wing_anim.cpp').read_text()
source = source[source.index('namespace\n{'):source.rindex('#endif')]
stub = r'''
#define FREELANCER_MOD_PLUGINS
#include "wing_anim.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <cstdio>
#include <algorithm>
constexpr unsigned WM_KEYDOWN=0x100,VK_SHIFT=0x10,VK_CONTROL=0x11,VK_MENU=0x12;
short GetKeyState(unsigned){return 0;}
bool enabled=true,cruise=false;
#define PORT_PLUGIN_ON(name) enabled
void PortConfigString(char const*,char const*,char const* value,char* out,unsigned size){strncpy_s(out,size,value,_TRUNCATE);}
int PortConfigInt(char const*,char const* key,int){return std::strcmp(key,"key")==0?86:0;}
struct IObjRW {unsigned type=0x10;void get_type(unsigned& out)const{out=type;}};
struct IBehaviorManager {
    bool docking=false;IObjRW port;
    bool get_docking_port(IObjRW const*& out,int& index)const{out=&port;index=0;return docking;}
};
struct CEqObj {unsigned ObjectClass=0x503;int handle=1;IBehaviorManager behavior;
    IBehaviorManager* get_behavior_interface(){return &behavior;}} ship;
struct PlayerHolder {char pad[16]={};CEqObj* ship=nullptr;} player;
void* GetPlayerObjRW(){return player.ship?&player:nullptr;}
bool GetPlayerEngineCruiseActive(){return cruise;}
void* AsOpaqueDword(float value){unsigned bits;std::memcpy(&bits,&value,4);return reinterpret_cast<void*>(bits);}
struct Playback {float time=0,total=1;bool reverse=false,running=true;};
struct Animation {
    Playback slots[8];int starts=0,stops=0;
    unsigned long EvalPlayback(unsigned long id,unsigned long flags,float time,float speed,void*,void*,void*,void*){
        assert(id<8&&speed==1);auto& p=slots[id];++starts;
        if(time!=-2)p.time=time;
        p.reverse=(flags&1)!=0;p.running=p.reverse?p.time>0:p.time<p.total;
        return 0;
    }
    unsigned long StopPlayback(unsigned long id){++stops;slots[id].running=false;return 0;}
    float GetStoredDuration(unsigned long id){return slots[id].time;}
    float GetScriptDuration(void* id){return slots[reinterpret_cast<uintptr_t>(id)].total;}
    void Advance(float dt){for(auto& p:slots)if(p.running){p.time=std::clamp(p.time+(p.reverse?-dt:dt),0.f,p.total);if(p.time==0||p.time==p.total)p.running=false;}}
} animation;
namespace DALib {Animation* Anim=&animation;}
namespace AnimDB {void Add(int){}}
int ModShipOneShotAnim(CEqObj* s){return s?s->handle:-1;}
int ModSwapShipOneShotAnim(CEqObj* s,char const*){s->handle=2;animation.slots[2]={};return 2;}
'''
checks = r'''
void Reset(bool finishLaunch=true){
    player.ship=nullptr;WingAnimTick();
    animation={};ship={};cruise=false;enabled=true;player.ship=&ship;WingAnimTick();
    assert(WingAnimAvailable());
    if(finishLaunch){animation.Advance(1);WingAnimTick();assert(WingAnimDisplayState()==3);}
}
void Step(float dt){animation.Advance(dt);WingAnimTick();}
void Pause(){assert(WingAnimTogglePause());WingAnimTick();assert(WingAnimPaused());}
void Play(){assert(WingAnimRequestToggle());WingAnimTick();}
int main(){
    Reset();assert(!WingAnimCanPause()&&!WingAnimTogglePause());
    // HUD play and the original key share one toggle path; pause retains phase.
    Play();Step(.3f);Pause();float t=animation.slots[2].time;
    Step(.4f);assert(animation.slots[2].time==t);
    assert(WingAnimHandleKey(WM_KEYDOWN,86));WingAnimTick();
    assert(!WingAnimPaused()&&!animation.slots[2].reverse&&animation.slots[2].time==t);
    Step(.2f);Pause();t=animation.slots[2].time;
    assert(WingAnimTogglePause());WingAnimTick();assert(!WingAnimPaused()&&animation.slots[2].time==t);
    Step(1);assert(WingAnimDisplayState()==1);
    Play();Step(.2f);Pause();t=animation.slots[2].time;Play();
    assert(animation.slots[2].reverse&&animation.slots[2].time==t);Step(1);assert(WingAnimDisplayState()==3);
    puts("PASS: manual key/HUD start, pause hold, both resume controls and reverse continuation");
    // Cruise exits while paused mid-fold: finish the fold, then extend.
    Reset();cruise=true;WingAnimTick();Step(.3f);Pause();t=animation.slots[2].time;
    cruise=false;WingAnimTick();assert(!WingAnimPaused()&&animation.slots[2].time==t&&!animation.slots[2].reverse);
    Step(1);assert(animation.slots[2].reverse);Step(1);assert(WingAnimDisplayState()==3);
    // Automatic resume and a queued manual resume in one tick cannot reverse twice.
    Reset();Play();Step(.2f);Pause();WingAnimRequestToggle();cruise=true;WingAnimTick();
    Step(1);assert(WingAnimDisplayState()==1&&!animation.slots[2].running);
    puts("PASS: automatic resume, opposite pending destination, same-frame resume race");
    Reset();WingAnimSetCruiseLocked(true);assert(WingAnimCruiseLocked());
    int starts=animation.starts;cruise=true;WingAnimTick();assert(animation.starts==starts);
    Play();Step(.2f);Pause();cruise=false;WingAnimTick();assert(WingAnimPaused());
    WingAnimSetCruiseLocked(false);WingAnimTick();assert(WingAnimPaused());
    cruise=true;WingAnimTick();assert(!WingAnimPaused());Step(1);assert(WingAnimDisplayState()==1);
    // Lock cancels only a pending cruise request, never a manual one/current move.
    Reset();Play();Step(.2f);cruise=true;WingAnimTick();cruise=false;WingAnimTick();
    WingAnimSetCruiseLocked(true);Step(1);assert(WingAnimDisplayState()==1);
    Reset();Play();Step(.2f);Play();WingAnimSetCruiseLocked(true);Step(1);
    assert(animation.slots[2].reverse);Step(1);assert(WingAnimDisplayState()==3);
    puts("PASS: cruise lock, no stale replay on unlock, paused/current/manual motion preserved");
    // Launch and docking are independent of the cruise-only lock.
    Reset(false);Step(.2f);Pause();float launchTime=animation.slots[1].time;
    WingAnimSetCruiseLocked(true);ship.behavior.docking=true;WingAnimTick();
    assert(!WingAnimPaused()&&animation.slots[1].time==launchTime);
    Step(1);assert(ship.handle==2&&animation.slots[2].running);Step(1);assert(WingAnimDisplayState()==1);
    Reset();Play();Step(.2f);Pause();ship.handle=-1;WingAnimTick();
    assert(!WingAnimAvailable()&&!WingAnimPaused()&&!WingAnimRequestToggle());
    Reset();assert(!WingAnimPaused()&&!WingAnimCruiseLocked());
    enabled=false;assert(!WingAnimAvailable()&&!WingAnimTogglePause());
    puts("PASS: launch/docking resume, missing handle, ship reset and disabled plugin");
}
'''
(out / 'check.cpp').write_text(stub + source + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include', repo / 'src/freelancer/Client'] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)
