"""Exercise production maneuver layouts without a renderer."""
import json,hashlib,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/flight_actions'))
from check_hotkeys import extract
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
OUT=ROOT/'src/obj/train_coupling_hud/check';OUT.mkdir(parents=True,exist_ok=True)
client=ROOT/'src/freelancer/Client'
actions=(client/'player_flight_actions.cpp').read_text()
train=(client/'player_train.cpp').read_text()
hud=(client/'hud_maneuvers.cpp').read_text()
stub=r'''
#include <cassert>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <cstdio>
bool extra=true,isTrain=false,target=true;
struct Arch{bool GetExtraManeuvers(){return extra;}} arch;
struct Ship{Arch* shiparch(){return &arch;}bool get_target(){return target;}} ship;
using CShip=Ship;
struct IObjRW{} object;
IObjRW* GetPlayerObjRW(){return &object;}
CShip* HudShipOfObjRw(IObjRW*){return &ship;}
namespace CmnTrain{bool IsLocomotive(CShip*){return isTrain;}}
struct WinControl{
    float pos[3]{};bool hidden=true;int MeshHolder=0;unsigned char flags=0;
    void SetProperty(int msg,uintptr_t a,uintptr_t){
        if(msg==1)hidden=a!=0;
        if(msg==6)std::memcpy(pos,reinterpret_cast<void*>(a),sizeof(pos));
        if(msg==7)std::memcpy(reinterpret_cast<void*>(a),pos,sizeof(pos));
    }
    void SetFlags331(unsigned char f){flags=f;}unsigned char GetFlags331(){return flags;}
};
using NnButtonControl=WinControl;
void WinControlHalfExtentsFromMesh(float*,int*){}
bool GetPlayerEngineCruiseActive(){return false;}
char const* kTabMesh="default";
struct HUD_Maneuvers{
    WinControl* Buttons[4];WinControl* Tab;WinControl* CruiseButton;
    int bTabMeshReset=0;float TabHalfExtents[3]{};
    void UpdateTabAndCruise(int);
};
namespace PlayerTrain{
HUD_Maneuvers* panel;WinControl* button;
bool bridge(){return true;}
bool HasButton(int);
void Update(HUD_Maneuvers*,int current){button->SetProperty(1,HasButton(current)?0:1,0);}
}
namespace PlayerFlightActions{
enum Kind{SpiralClockwise,ReverseTurn,ReverseStrafe,GotoWeave,Count,None};
HUD_Maneuvers* panel;WinControl* buttons[Count];Kind active=None;
struct Camera{bool holding(){return false;}} turnCamera;
bool enabled(){return true;}IObjRW* player(){return &object;}
bool valid(IObjRW*,Kind){return true;}bool supported(Kind,CShip*){return true;}
}
'''
code=stub+'\nnamespace PlayerFlightActions{\n'+''.join(extract(actions,s) for s in ['bool allowed(','bool HasButtons(','void Layout('])+'}\n'
code+='namespace PlayerTrain{\n'+extract(train,'bool HasButton(')+extract(train,'void Layout(')+'}\n'
code+=extract(hud,'void HUD_Maneuvers::UpdateTabAndCruise(')
code+=r'''
int main(){
    WinControl anchors[4],tab,cruise,coupling,extras[4];HUD_Maneuvers hud;
    for(int i=0;i<4;++i){anchors[i].pos[0]=-.06f+.04f*i;hud.Buttons[i]=&anchors[i];PlayerFlightActions::buttons[i]=&extras[i];}
    hud.Tab=&tab;hud.CruiseButton=&cruise;PlayerTrain::panel=PlayerFlightActions::panel=&hud;PlayerTrain::button=&coupling;
    hud.UpdateTabAndCruise(0x13);assert(hud.bTabMeshReset==3 && coupling.hidden);
    for(int i=0;i<3;++i)assert(!extras[i].hidden);assert(extras[3].hidden);
    hud.UpdateTabAndCruise(2);assert(hud.bTabMeshReset==2 && !extras[3].hidden);
    extra=false;
    for(int mode:{0x13,2}){hud.UpdateTabAndCruise(mode);assert(hud.bTabMeshReset==1 && !cruise.hidden && coupling.hidden);for(auto& e:extras)assert(e.hidden);}
    isTrain=true;
    for(int mode:{0x13,2}){
        hud.UpdateTabAndCruise(mode);assert(hud.bTabMeshReset==2 && !cruise.hidden && !coupling.hidden);
        for(auto& e:extras)assert(e.hidden);
        float anchor=anchors[mode==2?1:0].pos[0]*2;
        assert(std::abs(cruise.pos[0]-anchor)<1e-6 && std::abs(coupling.pos[0]-anchor-.032f)<1e-6);
        assert(std::abs(coupling.pos[1]-.297f)<1e-6);
        hud.UpdateTabAndCruise(mode);assert(std::abs(coupling.pos[0]-anchor-.032f)<1e-6);
    }
    for(int mode:{7,10,-1}){hud.UpdateTabAndCruise(mode);assert(coupling.hidden);for(auto& e:extras)assert(e.hidden);}
    isTrain=false;extra=true;hud.UpdateTabAndCruise(0x13);assert(hud.bTabMeshReset==3 && !extras[0].hidden);
    puts("PASS: fighter actions, capital cruise-only bar, train cruise/coupling pair, F2, hiding and ship/mode transitions");
}
'''
code=code.replace('#include <cassert>','#include <cassert>\n#include <initializer_list>')
(OUT/'check.cpp').write_text(code)
compiler,env=compiler_env()
subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/W4','check.cpp','/Fecheck.exe'],cwd=OUT,env=env,check=True)
subprocess.run([str(OUT/'check.exe')],cwd=OUT,check=True)
files=[Path(__file__)]+[client/n for n in ['hud_maneuvers.cpp','player_flight_actions.cpp','player_train.cpp']]
(OUT/'checked.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
