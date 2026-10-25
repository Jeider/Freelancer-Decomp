"""Compile production toggled picking functions with recorded input/raycast/command boundaries."""
import os
import re
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
source = (repo / 'src/freelancer/Client/hud_vulnerable.cpp').read_text()
out = repo / 'src/obj/targeting_world_check'
out.mkdir(parents=True, exist_ok=True)


def function(signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


stub = r'''
#include <cassert>
#include <cstdio>
#include <cmath>
#include <initializer_list>
struct Vector {float x=0,y=0,z=0;};
struct Arch {bool bVulnerable=true;};
struct CArchGroup {
    Arch* Arch=nullptr; int State=1; float HitPts=100; long root=42;
    long GetRootIndex() const {return root;}
    unsigned short GetID() const {return 0x8002;}
};
struct CObject {unsigned ObjectClass=0x503;};
struct CEGun;
struct CEqObj:CObject {
    unsigned Id=123; float CloakPercent=0; unsigned short sub=0x8002;
    struct Groups {CArchGroup* group=nullptr; CArchGroup* FindByID(unsigned short) {return group;}} ArchGroups;
    struct Equip {CEGun* gun=nullptr; CEGun* FindByID(unsigned short) {return gun;}} EquipManager;
    unsigned short inst_to_subobj_id(long) {return sub;}
};
constexpr unsigned HpTypeTurret=13,HpTypeTurretSpecial1=25,HpTypeTurretSpecial10=34;
struct GunArchData {bool bAutoTurret=true;unsigned *HpGunTypesBegin=nullptr,*HpGunTypesEnd=nullptr;};
struct CEGun {
    GunArchData* arch=nullptr;CEqObj* owner=nullptr;long root=80;
    bool destroyed=false,connected=true,castable=true;float hp=100;
    static CEGun* cast(CEGun* g){return g&&g->castable?g:nullptr;}
    GunArchData* GunArch(){return arch;}
    CEqObj* GetOwner(){return owner;}
    bool IsDestroyed(){return destroyed;}
    bool IsConnected(){return connected;}
    float GetHitPoints(){return hp;}
    long GetRootIndex(){return root;}
};
struct CEScanner {
    float range=2500;
    static CEScanner const* cast(CEScanner* s) {return s;}
    float GetRadarRange() const {return range;}
};
struct CShip:CEqObj {
    struct Equip {CEScanner* scanner=nullptr; CEScanner* FindFirst(unsigned) {return scanner;}} EquipManager;
    Vector WorldPosition;
};
struct IObjRW {};
struct ICamera {};
struct FMouseEvent {struct {unsigned char Byte18=0;} Record; bool bMove=false; unsigned ButtonIndex=0;};
struct FSpaceCommand {unsigned Id=0,ObjectId=0;unsigned short SubObjectId=0;unsigned char Byte26=0;};
struct FCameraRayHit {CObject* Object=nullptr;long Instance=-1;Vector Point;float Distance=0;};
namespace SubObjectID {
bool IsArchGroupID(unsigned short id) {return id>=0x8000;}
bool IsEquipID(unsigned short id) {return id>1&&id<0x8000;}
}
struct Hover {CEqObj* object=nullptr;CArchGroup* group=nullptr;CEGun* turret=nullptr;long root=-1;unsigned short subId=0;};
struct {bool capturedLeft=false;void ClearWire(){}} state;
struct {void* window=reinterpret_cast<void*>(1);} g_client;
constexpr int kGameOptInterfaceGroup=6,kGameOptHud=10;
bool savedAutoselect=true;
bool GetSavedTargetingAutoselect(){return savedAutoselect;}
void SetSavedTargetingAutoselect(bool value){savedAutoselect=value;}
bool foreground=true,hud=true,blocked=false,letterbox=false,loading=false,focus=false,ui=false;
CShip playerShip;IObjRW player;ICamera camera;IObjRW* activePlayer=&player;
FCameraRayHit nextHit;FSpaceCommand lastCommand;unsigned sends=0,raycasts=0;
void* GetForegroundWindow(){return foreground?g_client.window:nullptr;}
int GetGameOption(int){return hud;}
bool HudIsMousePickBlocked(){return blocked;}
bool IsLetterboxVisible(){return letterbox;}
bool IsSpaceInitInProgress(){return loading;}
bool HudGetInputFocus(){return focus;}
void* Win3DGetHover(){return ui?g_client.window:nullptr;}
IObjRW* GetPlayerObjRW(){return activePlayer;}
CShip* HudShipOfObjRw(IObjRW* p){return p?&playerShip:nullptr;}
void GetClientSoftwareCursor(int* x,int* y,int* z){*x=100;*y=200;*z=0;}
void CameraRayPick(FCameraRayHit* hit,ICamera*,float x,float y,CObject const* ignore,bool skip){
    assert(x==100 && y==200 && ignore==&playerShip && skip);*hit=nextHit;++raycasts;
}
void* GetClientSoundListenerObject(){return &camera;}
void SpaceSendCommand(FSpaceCommand* c){lastCommand=*c;++sends;}
void PlayOrRewindUiSoundSlot(int sound){assert(sound==0x18);}
'''
checks = r'''
int main(){
    Arch arch;CArchGroup group;group.Arch=&arch;CEqObj target;target.ArchGroups.group=&group;
    CEScanner scanner;playerShip.EquipManager.scanner=&scanner;
    nextHit.Object=&target;nextHit.Instance=42;nextHit.Point.z=100;
    FMouseEvent down;down.Record.Byte18=1;FMouseEvent up;
    assert(VulnerableAutoselectEnabled());
    SetVulnerableAutoselect(false);
    assert(!VulnerableTargetingMouse(down) && sends==0);
    SetVulnerableAutoselect(true);assert(VulnerableAutoselectEnabled());
    assert(VulnerableTargetingMouse(down) && sends==1);
    assert(lastCommand.Id==0x1c && lastCommand.ObjectId==123 && lastCommand.SubObjectId==0x8002 && lastCommand.Byte26==1);
    SetVulnerableAutoselect(false);assert(!VulnerableAutoselectEnabled());
    assert(VulnerableTargetingMouse(up)); // Toggle disabled before the captured release.
    assert(!VulnerableTargetingMouse(up) && !VulnerableTargetingMouse(down));
    SetVulnerableAutoselect(true);
    // A repeated click sends the same exact target again, not just the first click.
    assert(VulnerableTargetingMouse(down) && sends==2);assert(VulnerableTargetingMouse(up));
    assert(lastCommand.ObjectId==123 && lastCommand.SubObjectId==0x8002);
    // Hull / obstruction, unmarked, killed, detached, cloaked and distant parts never select.
    for(int kind=0;kind<8;++kind){
        target.sub=0x8002;arch.bVulnerable=true;group.State=1;group.root=42;group.HitPts=100;
        target.CloakPercent=0;nextHit.Object=&target;nextHit.Point.z=100;
        switch(kind){case 0:target.sub=1;break;case 1:arch.bVulnerable=false;break;
        case 2:group.State=2;break;case 3:group.root=-1;break;case 4:group.HitPts=0;break;
        case 5:target.CloakPercent=1;break;case 6:nextHit.Point.z=3000;break;case 7:nextHit.Object=nullptr;break;}
        assert(!VulnerableTargetingMouse(down) && sends==2);assert(!VulnerableTargetingMouse(up));
    }
    nextHit.Object=&target;
    // Modal/HUD/focus gates leave ordinary input alone and do not raycast.
    for(bool* gate:{&blocked,&letterbox,&loading,&focus,&ui}){
        *gate=true;unsigned rays=raycasts;assert(!VulnerableTargetingMouse(down));
        assert(raycasts==rays);*gate=false;
    }
    foreground=false;assert(!VulnerableTargetingMouse(down));foreground=true;
    hud=false;assert(!VulnerableTargetingMouse(down));hud=true;
    activePlayer=nullptr;assert(!VulnerableTargetingMouse(down));activePlayer=&player;
    FMouseEvent right=down;right.ButtonIndex=1;assert(!VulnerableTargetingMouse(right));
    FMouseEvent move=down;move.bMove=true;assert(!VulnerableTargetingMouse(move));
    // Re-pick at click time, do not commit a hover from a destroyed part.
    group.State=1;assert(Pick(&camera).group==&group);group.State=3;
    assert(!VulnerableTargetingMouse(down) && sends==2);
    VulnerableTargetingReset();assert(!VulnerableTargetingMouse(up));
    assert(VulnerableAutoselectEnabled()); // Teardown/focus reset must not change saved preference.
    savedAutoselect=false;assert(!VulnerableAutoselectEnabled() && !VulnerableTargetingMouse(down));
    savedAutoselect=true;assert(VulnerableAutoselectEnabled()); // A newly loaded player's value is live.
    GunArchData gunArch;CEGun turret;turret.arch=&gunArch;turret.owner=&target;
    target.sub=18;target.EquipManager.gun=&turret;nextHit.Instance=81;
    auto picked=Pick(&camera);
    assert(picked.turret==&turret&&picked.group==nullptr&&picked.root==80&&picked.subId==18);
    assert(VulnerableTargetingMouse(down)&&sends==3);
    assert(lastCommand.ObjectId==123&&lastCommand.SubObjectId==18);assert(VulnerableTargetingMouse(up));
    assert(VulnerableTargetingMouse(down)&&sends==4);assert(VulnerableTargetingMouse(up));
    gunArch.bAutoTurret=false;
    assert(!Pick(&camera).object); // Empty explicit types must not inherit the all-types fallback.
    unsigned types[]={4,13};gunArch.HpGunTypesBegin=types;gunArch.HpGunTypesEnd=types+2;
    assert(Pick(&camera).turret==&turret);
    for(unsigned type=25;type<=34;++type){types[1]=type;assert(Pick(&camera).turret==&turret);}
    types[1]=24;assert(!Pick(&camera).object);types[1]=35;assert(!Pick(&camera).object);
    types[1]=25;
    for(int kind=0;kind<9;++kind){
        turret.arch=&gunArch;turret.owner=&target;turret.root=80;turret.destroyed=false;
        turret.connected=true;turret.hp=100;turret.castable=true;target.EquipManager.gun=&turret;
        target.CloakPercent=0;nextHit.Point.z=100;
        switch(kind){case 0:turret.arch=nullptr;break;case 1:turret.owner=&playerShip;break;
        case 2:turret.root=-1;break;case 3:turret.destroyed=true;break;case 4:turret.connected=false;break;
        case 5:turret.hp=0;break;case 6:turret.castable=false;break;case 7:target.CloakPercent=1;break;
        case 8:nextHit.Point.z=3000;break;}
        assert(!VulnerableTargetingMouse(down)&&sends==4);assert(!VulnerableTargetingMouse(up));
    }
    puts("PASS: turret equipment ID/root, repeated click, automatic/manual turret classes, empty-class fallback, destroyed/detached/non-gun/foreign/range/cloak rejection");
    puts("PASS: toggle on/off, repeated same-target click, owned release, ordinary input on misses/right-click, dead parts, range, modal/focus gates and fresh picking");
}
'''
for name in ('camera', 'player', 'playerShip'):
    stub = re.sub(r'\b' + name + r'\b', 'test_' + name, stub)
    checks = re.sub(r'\b' + name + r'\b', 'test_' + name, checks)
code = stub + '\n'.join(function(s) for s in ('bool Available()', 'bool VulnerableAutoselectEnabled()', 'void SetVulnerableAutoselect(', 'bool IsTurret(', 'Hover Pick(',
    'bool VulnerableTargetingMouse(', 'void VulnerableTargetingReset(')) + checks
(out / 'check.cpp').write_text(code)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include'] + [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] + [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)
