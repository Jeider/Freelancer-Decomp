"""Exercise the production UI selection and live-part highlight without game assets."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/targeting_selected_part';OUT.mkdir(parents=True,exist_ok=True)
def extract(file,signature):
    text=(ROOT/'src/freelancer/Client'/file).read_text()
    start=text.index(signature);end=text.index('{',start)+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
stub=r'''
#include <cassert>
#include <cstdio>
constexpr unsigned short SUBOBJ_ID_NONE=0;
namespace SubObjectID {bool IsArchGroupID(unsigned short id){return id>=100;} bool IsEquipID(unsigned short id){return id>0&&id<100;}}
struct CObject {unsigned ObjectClass=0x503;};
struct Arch {bool bVulnerable=true;};
struct CArchGroup {Arch* Arch;int State=1;float HitPts=1;long root=42;long GetRootIndex(){return root;}};
struct CEqObj;
struct CEGun {CEqObj* owner=nullptr;bool destroyed=false,connected=true;float health=1;long root=77;
 static CEGun* cast(CEGun*p){return p;} CEqObj* GetOwner(){return owner;} bool IsDestroyed(){return destroyed;}
 float GetHitPoints(){return health;} bool IsConnected(){return connected;} long GetRootIndex(){return root;}};
template<class T> struct Manager {T* item=nullptr;unsigned short id=0;T* FindByID(unsigned short key){return key==id?item:nullptr;}};
struct CEqObj:CObject {Manager<CArchGroup> ArchGroups;Manager<CEGun> EquipManager;};
struct IObjRW {unsigned id=0;unsigned get_id(){return id;}};
struct Ship {IObjRW* target=nullptr;unsigned short sub=0;IObjRW* get_target(){return target;}unsigned short get_sub_target(){return sub;}};
Ship testPlayer;IObjRW playerRW;bool hasPlayer=true,autoOn=true,owns=true;
IObjRW* GetPlayerObjRW(){return hasPlayer?&playerRW:nullptr;}
Ship* HudShipOfObjRw(IObjRW*p){return p?&testPlayer:nullptr;}
IObjRW* WatchedObjRw(IObjRW*p){return p;}
bool VulnerableAutoselectEnabled(){return autoOn;}
struct HudTarget {IObjRW* ViewObject=nullptr;bool cruiser=true;bool TargetingIsCruiser()const{return cruiser;}unsigned short TargetingSelectedPart()const;};
bool TargetingOwnsContent(HudTarget const*){return owns;}
struct HudTargetBase {CObject* viewedObject=nullptr;int PartCache=0;CObject* GetViewCObject(){return viewedObject;}void HighlightSelectedViewPart(unsigned short);};
long InstanceFromIndex(long root){return root;}
int calls=0;long drawn=0;bool recurse=false;unsigned colour=0;
void PartCacheActivatePart(int*,long root,bool r,unsigned c){++calls;drawn=root;recurse=r;colour=c;}
'''
checks=r'''
int main(){
 IObjRW a{1},b{2};HudTarget hud;hud.ViewObject=&a;testPlayer.target=&a;testPlayer.sub=101;
 assert(hud.TargetingSelectedPart()==101);
 for(int frame=0;frame<100;++frame)assert(hud.TargetingSelectedPart()==101); // No cursor or flash timer dependency.
 autoOn=false;assert(hud.TargetingSelectedPart()==0);autoOn=true;
 testPlayer.target=&b;assert(hud.TargetingSelectedPart()==0);testPlayer.target=&a;
 testPlayer.sub=102;assert(hud.TargetingSelectedPart()==102);testPlayer.sub=0;assert(hud.TargetingSelectedPart()==0);testPlayer.sub=101;
 hud.cruiser=false;assert(hud.TargetingSelectedPart()==0);hud.cruiser=true;
 owns=false;assert(hud.TargetingSelectedPart()==0);owns=true;
 hasPlayer=false;assert(hud.TargetingSelectedPart()==0);hasPlayer=true;
 testPlayer.target=nullptr;assert(hud.TargetingSelectedPart()==0);testPlayer.target=&a;
 hud.ViewObject=nullptr;assert(hud.TargetingSelectedPart()==0);
 Arch arch;CArchGroup group{&arch};CEqObj object;object.ArchGroups={&group,101};
 HudTargetBase view;view.viewedObject=&object;view.HighlightSelectedViewPart(101);
 assert(calls==1&&drawn==42&&!recurse&&colour==0xffffe060u);
 calls=0;view.HighlightSelectedViewPart(0);view.HighlightSelectedViewPart(102);assert(!calls);
 group.State=0;view.HighlightSelectedViewPart(101);assert(!calls);group.State=1;
 group.HitPts=0;view.HighlightSelectedViewPart(101);assert(!calls);group.HitPts=1;
 group.root=-1;view.HighlightSelectedViewPart(101);assert(!calls);group.root=42;
 arch.bVulnerable=false;view.HighlightSelectedViewPart(101);assert(!calls);arch.bVulnerable=true;
 CEGun gun;gun.owner=&object;object.EquipManager={&gun,5};view.HighlightSelectedViewPart(5);
 assert(calls==1&&drawn==77&&recurse&&colour==0xffffe060u);calls=0;
 gun.destroyed=true;view.HighlightSelectedViewPart(5);assert(!calls);gun.destroyed=false;
 gun.connected=false;view.HighlightSelectedViewPart(5);assert(!calls);gun.connected=true;
 gun.health=0;view.HighlightSelectedViewPart(5);assert(!calls);gun.health=1;
 gun.owner=nullptr;view.HighlightSelectedViewPart(5);assert(!calls);
 view.viewedObject=nullptr;view.HighlightSelectedViewPart(101);assert(!calls);
 puts("PASS: persistent UI selection, toggle/target changes, no player, live group/turret checks and steady highlight");
}
'''
code=stub+extract('hud_target_panel.cpp','unsigned short HudTarget::TargetingSelectedPart() const')
code+=extract('hud_target.cpp','void HudTargetBase::HighlightSelectedViewPart(')+checks
(OUT/'check.cpp').write_text(code)
build=OUT/'check.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
 'if errorlevel 1 exit /b 1\ncl /nologo /EHsc /std:c++17 /W4 /WX check.cpp /Fecheck.exe\n')
subprocess.run(['cmd','/c',str(build)],cwd=OUT,check=True)
subprocess.run([str(OUT/'check.exe')],cwd=OUT,check=True)
