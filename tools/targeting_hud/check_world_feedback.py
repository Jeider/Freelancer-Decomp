"""Exercise production transforms and five-pixel world-wire geometry without the game."""
import os
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/targeting_feedback_check'
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


stub = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <list>
#include <vector>
#include "menu_keymap_config.h"
#include "targeting_window_state.h"
struct FVector {float X,Y,Z;};
struct FPartCacheVertex {float X,Y,Z;unsigned Tag;};
constexpr unsigned Orange=0xffff8040u;
constexpr float kViewWireDim=0.7f;
unsigned char G_HudChromeColorRgba[4]={32,160,255,255};
unsigned long G_NnPaletteArgb_679b98=0xffe0c080u;
struct CEquip {double health=1;double GetRelativeHealth(){return health;}};
float phase=0;
unsigned char pulseDirection=0;
unsigned hoverPulseCalls=0;
bool HudIsMousePickBlocked(){return false;}
float NnUiPulsePhaseNorm(){return phase;}
unsigned char NnUiPulseDirection(){return pulseDirection;}
void NnUiPulseBlendFromArgb(unsigned long* out,unsigned long base){++hoverPulseCalls;*out=base;}
struct GroupArch {bool bVulnerable=true;};
struct CArchGroup {
    GroupArch* Arch;float health=1;
    float GetRelativeHealth(){return health;}
};
struct CObject {unsigned ObjectClass=0;};
struct CSolar:CObject {unsigned TypeBits=0;bool is_waypoint() const;};
struct IObjInspect {
    float attitude=0;int queryResult=0;
    int get_attitude_towards(float& out,IObjInspect const*)const{out=attitude;return queryResult;}
};
struct IObjRW:IObjInspect {CObject* object=nullptr;unsigned id=0;unsigned get_id(){return id;}};
IObjRW player;
IObjRW* playerPointer=&player;
IObjRW* GetPlayerObjRW(){return playerPointer;}
struct HudTarget {IObjRW* ViewObject=nullptr;unsigned TargetingObjectId() const;bool TargetingIsHostileShip() const;};
IObjRW* WatchedObjRw(IObjRW* const& rw){return rw;}
CObject* CObjectOfObjRw(IObjRW* rw){return rw?rw->object:nullptr;}
bool IsClass(CObject* object,unsigned mask){return (object->ObjectClass&mask)==mask;}
'''
checks = r'''
int main(){
    CheckWireTransforms();
    HudTarget target;
    assert(target.TargetingObjectId()==0);
    CSolar solar;solar.ObjectClass=0x303;
    IObjRW selection;selection.object=&solar;selection.id=42;target.ViewObject=&selection;
    assert(target.TargetingObjectId()==42);
    solar.TypeBits=0x200;assert(target.TargetingObjectId()==42); // Native waypoint diamond is renderable.
    selection.attitude=-1;assert(!target.TargetingIsHostileShip()); // Waypoints never trigger hostile auto-open.
    TargetingWindowState waypointWindow;
    waypointWindow.Observe(target.TargetingObjectId(),target.TargetingIsHostileShip());
    assert(waypointWindow.targetId==42&&!waypointWindow.open);
    waypointWindow.ToggleOpen();assert(waypointWindow.open); // Manual opening renders the native model.
    waypointWindow.SetLocked(true);waypointWindow.Observe(0,false);assert(waypointWindow.open);
    waypointWindow.Observe(target.TargetingObjectId(),false);assert(waypointWindow.open&&waypointWindow.targetId==42);
    solar.ObjectClass=0x503;assert(target.TargetingObjectId()==42); // Ship, not a waypoint solar.
    selection.object=nullptr;assert(target.TargetingObjectId()==0);
    puts("PASS: target eligibility accepts native waypoint models, ships and other solars; handles missing objects");
    assert(!target.TargetingIsHostileShip());
    selection.object=&solar;
    for(unsigned objectClass:{0x303u,0x503u}) for(float attitude:{-1.f,-.6f,-.5999f,0.f,.6f,1.f}) {
        solar.ObjectClass=objectClass;selection.attitude=attitude;
        assert(target.TargetingIsHostileShip()==(objectClass==0x503&&attitude<=-.6f));
    }
    solar.ObjectClass=0x503;selection.attitude=-1;
    playerPointer=nullptr;assert(!target.TargetingIsHostileShip());playerPointer=&player;
    selection.queryResult=1;assert(!target.TargetingIsHostileShip());selection.queryResult=0;
    target.ViewObject=nullptr;assert(!target.TargetingIsHostileShip());target.ViewObject=&selection;
    puts("PASS: production ship/solar filter and native hostility threshold; missing player, target and failed attitude query reject auto-open");
    TargetingWindowState window;
    assert(!window.open&&!window.locked);
    window.ToggleOpen();assert(!window.open); // No target cannot open manually.
    window.Observe(10, true);assert(window.open);
    window.ToggleOpen();window.Observe(10, true);assert(!window.open); // Manual close stays closed.
    window.Observe(11, true);assert(window.open);
    window.ToggleLock();assert(window.locked&&window.open); // Lock does not force a close.
    window.Observe(12, true);assert(window.open);
    window.Observe(0, false);assert(window.open); // Lock preserves empty panel / waypoint.
    window.Observe(13, true);assert(window.open);
    window.ToggleOpen();assert(!window.open);
    window.ToggleOpen();assert(window.open); // Manual override while locked.
    window.Observe(0, false);assert(window.open);
    window.ToggleOpen();assert(!window.open); // Empty locked panel can be closed manually.
    window.Observe(14, true);assert(!window.open);
    window.ToggleLock();assert(window.open&&!window.locked);
    window.Observe(0, false);window.Observe(15, true);window.Observe(0, false);assert(!window.open);
    window.Observe(16, true);assert(window.open); // Rapid changes retain latest desired state.
    window.SetLocked(true);window.Observe(0, false);window.Observe(17, true);assert(window.open);
    window.SetLocked(false);assert(window.open); // Loaded unlocked state is immediately applied.
    window.ToggleOpen();window.SetLocked(false);assert(!window.open); // Reading a save bit cannot reopen every frame.
    puts("PASS: auto-hide/open, manual override, lock/unlock and rapid target changes");
    window = {};
    window.Observe(20,false);assert(!window.open); // Friendly/neutral/solar: manual only.
    window.SetLocked(true);window.SetLocked(false);assert(!window.open);
    window.ToggleOpen();assert(window.open); // Manual opening still works.
    window.Observe(21,false);assert(window.open); // Only opening is restricted.
    window.ToggleOpen();window.Observe(22,false);assert(!window.open);
    window.Observe(23,true);assert(window.open);
    window.ToggleOpen();window.Observe(23,true);assert(!window.open);
    window.Observe(24,false);window.Observe(24,true);assert(!window.open); // No reselect.
    window.Observe(25,true);assert(window.open);
    window.Restore(true,false);
    window.Observe(26,false);assert(!window.open&&window.restorePending);
    window.Observe(27,false);assert(!window.open&&window.restorePending);
    window.Observe(28,true);assert(window.open&&!window.restorePending);
    window.Restore(false,false);window.Observe(29,false);window.Observe(30,true);assert(!window.open);
    window.Observe(31,true);assert(window.open);
    window.Restore(true,true);window.Observe(0,false);assert(window.open&&!window.restorePending);
    window.Observe(32,false);assert(window.open);
    window.ToggleOpen();assert(!window.open&&!window.restorePending);
    window.Observe(0,false);window.Observe(33,true);assert(!window.open); // Locked manual close persists.
    window.Observe(0,false);window.ToggleOpen();assert(window.open); // Reopen empty locked panel.
    window.SetLocked(false);assert(!window.open); // Unlock empty panel restores normal hiding.
    puts("PASS: hostile-only auto-open/unlock/restore, manual non-hostile opening, retained open state and selection changes");
    GroupArch arch;CArchGroup group={&arch,1};
    unsigned const orange=HudCollisionGroupWireColor(&group,false);
    assert((orange&0xffffffu)==0xb2592cu);
    group.health=.8f;assert(HudCollisionGroupWireColor(&group,false)==orange);
    group.health=.5f;unsigned const red=HudCollisionGroupWireColor(&group,false);
    assert((red&0xffffffu)==0xb22c2cu);
    group.health=.25f;assert(HudCollisionGroupWireColor(&group,false)==red);
    group.health=.1f;phase=0;
    assert((HudCollisionGroupWireColor(&group,false)&0xffffffu)==0);
    phase=.5f;unsigned const critical=HudCollisionGroupWireColor(&group,false);
    assert(((critical>>16)&255)>(critical&255));
    phase=.25f;unsigned const first=HudCollisionGroupWireColor(&group,false);
    phase=.75f;assert(first!=HudCollisionGroupWireColor(&group,false));
    pulseDirection=1;assert(first==HudCollisionGroupWireColor(&group,false));
    assert(hoverPulseCalls==0); // World hover must retain the damage hue/pulse.
    HudCollisionGroupWireColor(&group,true);assert(hoverPulseCalls==1);
    puts("PASS: shared healthy/light-damage orange, red thresholds, critical pulse and phase direction");
    CEquip turret;
    assert(HudEquipmentDamageWireColor(&turret)==0xff80c0e0u);
    turret.health=.9;assert(HudEquipmentDamageWireColor(&turret)==0xff20a0ffu);
    turret.health=.75;assert(HudEquipmentDamageWireColor(&turret)==0xffff8040u);
    turret.health=.5;assert(HudEquipmentDamageWireColor(&turret)==0xffff4040u);
    turret.health=.25;assert(HudEquipmentDamageWireColor(&turret)==0xffff4040u);
    turret.health=.1;phase=0;pulseDirection=0;
    assert(HudEquipmentDamageWireColor(&turret)==0xff000000u);
    phase=.25f;unsigned const turretPulse=HudEquipmentDamageWireColor(&turret);
    assert(((turretPulse>>16)&255)>(turretPulse&255));
    phase=.75f;assert(HudEquipmentDamageWireColor(&turret)!=turretPulse);
    pulseDirection=1;assert(HudEquipmentDamageWireColor(&turret)==turretPulse);
    assert(hoverPulseCalls==1);
    puts("PASS: turret health palette, damage thresholds and critical pulse without hover override");
    FPartCacheVertex v[6];unsigned cases=0;
    for(float scale:{320.f,960.f,1920.f})for(float depth:{3.f,100.f,10000.f})
    for(int direction=0;direction<3;++direction){
        FVector a={0,0,-depth};
        FVector b={direction==1?0.f:depth*.1f,direction==0?0.f:depth*.2f,-depth*2};
        assert(BuildWireQuad(a,b,3,scale,-scale,Orange,v));
        auto width=[&](int p,int q){
            double dx=scale*(v[p].X/-v[p].Z-v[q].X/-v[q].Z);
            double dy=-scale*(v[p].Y/-v[p].Z-v[q].Y/-v[q].Z);
            return std::sqrt(dx*dx+dy*dy);
        };
        assert(std::abs(width(0,1)-5)<.001&&std::abs(width(2,5)-5)<.001);
        assert(v[0].Z==a.Z&&v[2].Z==b.Z&&v[0].Tag==Orange);++cases;
    }
    assert(BuildWireQuad({1,0,1},{0,1,-10},3,960,-960,Orange,v));
    assert(v[0].Z==-3&&v[2].Z==-10);
    assert(BuildWireQuad({0,1,-10},{1,0,1},3,960,-960,Orange,v));
    assert(v[0].Z==-10&&v[2].Z==-3);
    assert(!BuildWireQuad({1,0,1},{0,1,2},3,960,-960,Orange,v));
    assert(!BuildWireQuad({0,0,-10},{0,0,-20},3,960,-960,Orange,v));
    assert(!BuildWireQuad({0,0,-10},{1,0,-20},3,0,-960,Orange,v));
    assert(BuildWireQuad({0,0,-10},{1,0,-20},3,960,-960,critical,v));
    for(auto const& vertex:v)assert(vertex.Tag==critical);
    printf("PASS: %u projected width cases, near clipping and degenerates\n",cases);
}
'''
transform_stub = r'''
#define DACOM_API
using GENRESULT=int;
constexpr int GR_OK=0;
struct FRp9TransformCache {
    float Values[16]={}; unsigned char bCommitted=0,bApplyMarker=0;
    void StoreAffine(float const*);
};
struct FDirectX9 {
    struct {FRp9TransformCache World,View;} Transforms_;
    int combined=1;
    int NeedDeviceLifetime(char const*,int){return GR_OK;}
    int PipelineStateValue(int id){assert(id==7);return combined;}
    void GetPipelineState(int id,int* value){*value=PipelineStateValue(id);}
    void MulZFlip12(float* out,float const* in){
        float tmp[12];std::memcpy(tmp,in,sizeof(tmp));
        for(int i:{6,7,8,11})tmp[i]=-tmp[i];
        std::memcpy(out,tmp,sizeof(tmp));
    }
    GENRESULT SetWorld(float const*);
    GENRESULT SetView(float const*);
    GENRESULT SetModelview(float const*);
    float DeviceZ(float z){
        float worldZ=Transforms_.World.Values[10]*z+Transforms_.World.Values[14];
        return Transforms_.View.Values[10]*worldZ+Transforms_.View.Values[14];
    }
};
using IRenderPipeline=FDirectX9;
'''
code = stub + transform_stub
for signature in ('void FRp9TransformCache::StoreAffine(',
                  'GENRESULT DACOM_API FDirectX9::SetWorld(',
                  'GENRESULT DACOM_API FDirectX9::SetView(',
                  'GENRESULT DACOM_API FDirectX9::SetModelview('):
    code += '\n' + function('../../RP9/RP9.cpp', signature)
code += function('hud_vulnerable.cpp', 'void ApplyWireViewSpace(')
code += r'''
void CheckWireTransforms(){
    float const identity[12]={1,0,0,0,1,0,0,0,1,0,0,0};
    // Reproduce the vanished overlay using the actual RP9 setters/cache:
    // Win3DApplyCamera primes the combined-view marker, then the old draw
    // overwrote View before SetModelview, leaving two Z flips.
    FDirectX9 broken;
    broken.SetModelview(identity);
    broken.SetWorld(identity);broken.SetView(identity);broken.SetModelview(identity);
    assert(broken.DeviceZ(-100)==-100); // behind the D3D camera
    for(int mode:{0,1})for(int pending:{0,1}){
        FDirectX9 pipe;pipe.combined=mode;
        if(mode)pipe.SetModelview(identity);
        else {pipe.SetWorld(identity);pipe.SetView(identity);}
        pipe.Transforms_.View.bApplyMarker=static_cast<unsigned char>(pending);
        ApplyWireViewSpace(&pipe);
        for(float z:{-3.f,-100.f,-10000.f})assert(pipe.DeviceZ(z)==-z);
        ApplyWireViewSpace(&pipe); // repeated setup must remain stable
        assert(pipe.DeviceZ(-100)==100);
    }
    puts("PASS: reproduced double-Z-flip regression with production RP9 setters; fixed path stays in front of camera in both pipeline modes");
}
'''
code += function('hud_vulnerable.cpp', 'bool BuildWireQuad(')
code += function('../../Common/common_csolar.cpp', 'bool CSolar::is_waypoint() const')
code += function('hud_target_panel.cpp', 'unsigned HudTarget::TargetingObjectId() const')
code += function('star_sys.cpp', 'int GetAttitudeClass(')
code += function('hud_target_panel.cpp', 'bool HudTarget::TargetingIsHostileShip() const')
for signature in ('int ClampByte(', 'int DimChromeByte(', 'unsigned PackPartTag(',
                  'unsigned long ChromeColourArgb()', 'unsigned long* HudDamageColorArgb(',
                  'unsigned HudCollisionGroupWireColor(', 'unsigned long EquipmentHealthColor(',
                  'unsigned HudEquipmentDamageWireColor('):
    code += '\n' + function('hud_target.cpp', signature)
(out / 'check.cpp').write_text(code + checks)
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
