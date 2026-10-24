"""Compile production visibility helpers and extracted lifecycle code against engine mocks.

No duplicate implementation of Track/Claim/Event/Forget/BindTransit is maintained here.
The shader/GPU checker separately validates depth fades and constant uploads.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/obj/jumphole_visibility_check"
SOURCE = ROOT / "src/freelancer/Client/jumphole_visual.cpp"


def extract(text, signature):
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text(encoding="utf-8-sig")
    prelude = r'''
#define FREELANCER_RP9
#define FDUMP(...) ((void)0)
#include <algorithm>
#include <map>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include "jumphole_visibility.h"
#include "jumphole_visual_state.h"
struct Vec { float x=0,y=0,z=0; };
struct FVector { float X=0,Y=0,Z=0; };
struct Transform { struct { float E[3][3]={{1,0,0},{0,1,0},{0,0,1}}; } Rotation; Vec Translation; };
struct FTransform { struct { float D[3][3]; } Rotation; FVector Translation; };
using Vector=Vec;
struct IObjRW { Vec Position;unsigned get_id()const{return 0;} Vec const& get_position(){return Position;} };
struct IBehaviorManager { bool get_docking_port(IObjRW const*&,int&){return false;} };
IBehaviorManager* GetBehaviorManager(IObjRW*){return nullptr;}
struct MockShip : IObjRW {};
struct FJumpShipEffect { MockShip* Ship=nullptr; };
struct FJumpGateEffect { float Clock=0; bool bFire=false; };
struct MockArch { void* Companion=nullptr; };
struct CObject { enum { ClassEqObj=1 }; unsigned ObjectClass=1; MockArch* Archetype=nullptr; };
struct CEqObj:CObject { float CloakPercent=0; };
float LodDistance=1000,Perf=0,FogVisibility=1;bool LodVisible=true;
namespace Archetype { float CliObjLodDistance(void*){return LodDistance;} }
struct FSpaceCamera { float Pos[3]={};float const* GetPosition(){return Pos;} };
FSpaceCamera* AsCamera(FSpaceCamera* C){return C;}
enum { kGameOptAlchemyLod,kGameOptNebula };
bool GetGameOption(int){return true;}
constexpr int kEffectTypeCount=16;
struct FEffectTypeInfo { float Priority=1,PbubbleNear=100,PbubbleFar=1000,Radius=0; } Info;
int EffectTypeIndexFromName(char const*){return 7;}
FEffectTypeInfo const* EffectTypeInfoByIndex(int){return &Info;}
float GetPerfGenericEffectPerf(){return Perf;}
bool EffectTypeLodBlend(int,FSpaceCamera*,float,float*){return LodVisible;}
void* GetSpaceFieldController(){return nullptr;}
unsigned GetSpaceFieldEnclosure(){return 0;}
float GetSpaceFieldRadiusSq(){return 1e9f;}
namespace NebulaVolume { float EffectVisibility(float const*,float const*){return FogVisibility;} }
struct FClientGameobj {
    int ManagerKind=2; unsigned Type=0x800,Id=1; int TypeStatus=0;
    int get_type(unsigned& T){T=Type;return TypeStatus;}
    unsigned get_id(){return Id;}
};
struct FClientSolarGameobj : FClientGameobj {
    void* Field_0x204=nullptr; Transform World;
    CEqObj Object;CObject const* cobject()const{return &Object;}
    unsigned Slot18c(unsigned*){return 0;}
    Transform const& get_transform(){return World;}
};
unsigned CreateID(char const* s){unsigned h=2166136261u;while(*s)h=(h^unsigned(*s++))*16777619u;return h;}
bool Enabled=true,ResourcesReady=true;int ReadyCalls=0;
int PortConfigInt(char const*,char const*,int){return Enabled;}
bool Ready(){++ReadyCalls;return ResourcesReady;}
struct FEffectArch { int EffectType=7; };
FEffectArch const* FindEffectArch(unsigned const*){static FEffectArch A;return &A;}
void* Player=nullptr;void* GetPlayerObjRW(){return Player;}
void Check(bool Good,char const* Message){printf("%s: %s\n",Good?"PASS":"FAIL",Message);if(!Good)std::exit(2);}
bool Near(float A,float B){return std::fabs(A-B)<.0001f;}
'''
    state = extract(source, "struct FState") + ";\n"
    globals_ = r'''
std::map<FClientSolarGameobj*,FState> G_States;
FJumpShipEffect const* G_Transit=nullptr;float G_TransitTime=0;
float G_TransitPalette[4]={1,1,1,0};bool G_TransitLogged=false;
void ResolvePalette(FState& S){S.PaletteReady=true;} // palette resolution is separately tested below
'''
    signatures = ["bool Eligible(", "FState& Track(", "bool Claim(", "float WorldVisibility(",
                  "bool JumpHoleVisualReplaceAttached(", "bool JumpHoleVisualReplaceActivation(",
                  "void JumpHoleVisualTick(", "void JumpHoleVisualEvent(", "void JumpHoleVisualForget(",
                  "void JumpHoleVisualBindTransit(", "void JumpHoleVisualForgetTransit("]
    tests = r'''
int main(){
    Check(JumpHoleRangeVisibility(900,1000)==1 && Near(JumpHoleRangeVisibility(950,1000),.5f) && JumpHoleRangeVisibility(1000,1000)==0 && JumpHoleRangeVisibility(1100,1000)==0,"authored range fades only in last tenth and never extends limit");
    Check(JumpHoleRangeVisibility(1,0)==0 && JumpHoleRangeVisibility(NAN,1000)==0 && JumpHoleRangeVisibility(1,INFINITY)==0,"invalid visibility input is culled");
    Check(JumpHolePbubbleLimit(100,1000,0)==1000 && JumpHolePbubbleLimit(100,1000,1)==100 && JumpHolePbubbleLimit(100,1000,2)==100 && JumpHolePbubbleLimit(100,1000,-1)==1000,"pbubble follows performance and clamps its endpoints");
    Check(JumpHoleRangeVisibility(100,JumpHolePbubbleLimit(100,1000,1))==0,"pbubble endpoint contributes exactly zero visibility");
    float hue[3]={.2f,.8f,.4f},out[4]={};Check(JumpHolePaletteMultiplier(hue,out),"finite authored palette accepted");
    Check(out[1]>out[0] && out[1]>out[2] && out[3]==0,"green authored hue stays dominant with finite shadow floor");
    float scaled[3]={2,8,4},other[4];JumpHolePaletteMultiplier(scaled,other);Check(Near(out[0],other[0])&&Near(out[1],other[1])&&Near(out[2],other[2]),"palette is exposure-scale invariant");
    float black[3]={},bad[3]={NAN,1,1};Check(!JumpHolePaletteMultiplier(black,out)&&!JumpHolePaletteMultiplier(bad,out),"black and nonfinite palettes reject without poisoning output");
    FClientSolarGameobj A,B;A.Id=11;B.Id=22;A.World.Translation.x=100;B.World.Translation.x=-200;
    Check(Claim(&A)&&Claim(&B)&&G_States.size()==2,"two different real holes can independently claim shared GPU resources");
    int calls=ReadyCalls;Check(Claim(&A)&&ReadyCalls==calls,"duplicate claim does not restart state or resource readiness");
    JumpHoleVisualEvent(&A,0);G_States[&A].Phase.Tick(.4f);
    Check(G_States[&A].Phase.Opening>0&&G_States[&B].Phase.Opening==0&&G_States[&B].Phase.Time==0,"opening and clocks do not leak between holes");
    A.World.Translation.x=333;A.World.Rotation.E[0][0]=0;A.World.Rotation.E[0][1]=-1;JumpHoleVisualTick(&A,.1f);
    Check(G_States[&A].World.Translation.X==333&&G_States[&A].World.Rotation.D[0][1]==-1&&G_States[&B].World.Translation.X==-200&&G_States[&B].World.Rotation.D[0][0]==1,"live spinning transform updates only the ticked host");
    B.World.Translation.x=-444;JumpHoleVisualTick(&B,.1f);Check(G_States[&B].World.Translation.X==-444&&G_States[&A].World.Translation.X==333,"second host updates independently");A.World.Translation.x=100;
    JumpHoleVisualEvent(&B,0);JumpHoleVisualEvent(&A,2);Check(G_States[&A].Phase.Target==0&&G_States[&B].Phase.Target==1,"closing one hole leaves another opening");
    G_States[&A].Palette[0]=.3f;G_States[&A].Phase.Time=17;
    MockShip ship;Player=static_cast<IObjRW*>(&ship);FJumpShipEffect transit;transit.Ship=&ship;
    JumpHoleVisualBindTransit(&transit,&A);G_States[&A].Palette[0]=2;
    JumpHoleVisualForget(&A);Check(G_States.size()==1&&G_States.count(&B)&&G_States[&B].Phase.Target==1,"deleting one hole preserves the other instance");
    Check(G_Transit==&transit&&G_TransitPalette[0]==.3f&&G_TransitTime==17,"transit palette and clock snapshot survive source mutation and deletion");
    FJumpShipEffect different;JumpHoleVisualForgetTransit(&different);Check(G_Transit==&transit,"unrelated transit deletion preserves active snapshot");JumpHoleVisualForgetTransit(&transit);Check(!G_Transit,"matching transit deletion clears pointer");
    Check(Track(&A).Phase.Time==0&&Track(&A).World.Translation.X==100,"pointer reuse after Forget starts fresh state");
    FSpaceCamera camera;float view[3]={0,0,-50};auto& visible=Track(&A);
    Check(WorldVisibility(visible,&camera,view,50)==1,"visible host passes production visibility composition");
    FogVisibility=0;Check(WorldVisibility(visible,&camera,view,50)==0,"zero fog transmittance produces exactly zero draw gain");FogVisibility=.25f;Check(Near(WorldVisibility(visible,&camera,view,50),.25f),"fractional fog transmittance scales the draw gain");FogVisibility=1;
    A.Object.CloakPercent=1;Check(WorldVisibility(visible,&camera,view,50)==0,"fully cloaked host has zero draw gain");A.Object.CloakPercent=0;
    MockArch arch;A.Object.Archetype=&arch;Check(WorldVisibility(visible,&camera,view,1000)==0,"authored archetype LOD distance culls host");A.Object.Archetype=nullptr;
    view[2]=-1000;Check(WorldVisibility(visible,&camera,view,1000)==0,"production pbubble endpoint culls host");view[2]=-50;
    LodVisible=false;Check(WorldVisibility(visible,&camera,view,50)==0,"Alchemy LOD cull is respected");LodVisible=true;
    Info.Priority=.1f;Perf=.5f;Check(WorldVisibility(visible,&camera,view,50)==0,"effect performance priority culls host");Info.Priority=1;Perf=0;
    FClientSolarGameobj fallback;ResourcesReady=false;Check(!JumpHoleVisualReplaceAttached(&fallback,CreateID("gf_wormhole_light")),"unavailable resources admit original ALE");ResourcesReady=true;Check(!JumpHoleVisualReplaceActivation(&fallback,CreateID("gf_hole_01"))&&Claim(&B),"fallback latch prevents mixed ALE/shader on one host without blocking others");
    char const* aliases[]={"gf_wormhole_01","gf_wormhole_light","gf_wormhole_green","gf_wormhole_orange","gf_wormhole_red","gf_hole_01","gf_hole_active_01","hole_center"};
    for(auto alias:aliases){FClientSolarGameobj h;h.Id=999;Check(JumpHoleVisualReplaceAttached(&h,CreateID(alias)),alias);JumpHoleVisualForget(&h);}
    FClientSolarGameobj scope;scope.Type=0x40;Check(!JumpHoleVisualReplaceAttached(&scope,CreateID(aliases[0])),"jump gates are excluded despite recognized effect name");scope.Type=0x800;scope.ManagerKind=1;Check(!Claim(&scope),"non-solar objects excluded");scope.ManagerKind=2;Enabled=false;Check(!Claim(&scope),"disabled option excludes claims");Enabled=true;Check(!JumpHoleVisualReplaceAttached(&scope,CreateID("mission_custom_effect")),"unrecognized attached effect is never globally suppressed");
    Check(JumpHoleVisualReplaceAttached(&scope,CreateID("gf_wormsparks")),"sparks companion is scoped to eligible hole");JumpHoleVisualForget(&scope);
    FJumpGateEffect arriving;arriving.Clock=.5f;scope.Field_0x204=&arriving;Check(Track(&scope).Phase.Opening==1&&Track(&scope).Phase.ActivationAge==.5f,"arrival with existing activation initializes its current phase");
    Check(JumpHoleExteriorVisibility(false,0)==0&&JumpHoleExteriorVisibility(false,.5f)==.5f&&JumpHoleExteriorVisibility(false,1)==1,"activation-only hosts never retain idle anomaly after closing");
    Check(JumpHoleExteriorVisibility(true,0)==1,"authored idle remains visible when not activated");
    puts("PASS all production visibility and extracted lifecycle checks");
}
'''
    cpp = OUT / "check.cpp"
    cpp.write_text(prelude + state + globals_ + "\n".join(extract(source, sig) for sig in signatures) + tests)
    vcvars = Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat")
    command = f'call "{vcvars}" > nul && cl /nologo /EHsc /O2 /std:c++17 /I src\\freelancer\\Client "{cpp}" /Fo"{OUT / "check.obj"}" /Fe"{OUT / "check.exe"}"'
    build = OUT / "build.cmd"
    build.write_text("@echo off\n" + command + "\n")
    subprocess.run(["cmd.exe", "/d", "/c", str(build)], cwd=ROOT, check=True)
    result = subprocess.run([str(OUT / "check.exe")], cwd=ROOT, capture_output=True, text=True)
    (OUT / "results.txt").write_text(result.stdout + result.stderr)
    print(result.stdout, end="")
    result.check_returncode()


if __name__ == "__main__":
    main()
