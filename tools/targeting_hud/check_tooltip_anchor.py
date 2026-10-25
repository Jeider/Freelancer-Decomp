"""Run the actual button tooltip feed against mesh/camera/tooltip recording stubs."""
import os
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/hud_tooltip_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/nn_button_control.cpp').read_text()
function = source[source.index('void NnButtonControl::ShowToolTip()'):source.index('intptr_t NnButtonControl::SetProperty(')]
fixture = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <initializer_list>
#define FREELANCER_WIDESCREEN_SUPPORT
struct FToolTipHoverInfo {
    int Ids=0,IdsAlt=0,AuxField=0,bLive=0;
    float WorldPos[3]={},HalfExtents[3]={};
};
struct NnButtonControl {
    int ToolTipIds=238200,CommandId=0x91;
    struct {float* EngineInstance=nullptr;} MeshHolder;
    float Position[3]={},Offset[3]={},HalfExtents[3]={.014f,.014f,0};
    float shift=0;
    void ShowToolTip();
};
bool HasInstance(NnButtonControl* b){return b->MeshHolder.EngineInstance!=nullptr;}
struct EngineStub {float* GetInstanceTransform(float* instance){return instance;}} engine;
namespace DALib {EngineStub* Engine=&engine;}
struct Camera {float XScale=1200;} camera;
Camera* GetWin3DSceneCamera(){return &camera;}
float currentShift=0;
float WidescreenHudShiftPixelsFor(NnButtonControl* b){return b->shift;}
struct FWidescreenHudShiftScope {
    float previous;
    FWidescreenHudShiftScope(float value,bool):previous(currentShift){currentShift=value;}
    ~FWidescreenHudShiftScope(){currentShift=previous;}
};
FToolTipHoverInfo fed;
void NnToolTipFeedHover(FToolTipHoverInfo const* info){assert(currentShift==0);fed=*info;}
'''
checks = r'''
int main(){
    unsigned cases=0;
    for(float width:{1440.f,1920.f,2560.f})for(float side:{-1.f,0.f,1.f})
    for(float depth:{1.f,1.5f})for(bool mesh:{false,true})for(bool nested:{false,true}) {
        NnButtonControl b;
        b.shift=side*(width-1440.f)/2.f;
        b.Position[2]=-1;
        b.Offset[0]=side*.31f*depth;b.Offset[1]=-.17f*depth;b.Offset[2]=1.f-depth;
        float transform[12]={};
        for(int i=0;i<3;++i)transform[9+i]=b.Position[i]+b.Offset[i];
        if(mesh)b.MeshHolder.EngineInstance=transform;
        currentShift=nested?b.shift:0;
        auto const before=currentShift;
        b.ShowToolTip();
        assert(currentShift==before);
        assert(fed.Ids==b.ToolTipIds&&fed.IdsAlt==b.ToolTipIds&&fed.AuxField==b.CommandId&&fed.bLive==1);
        float const screenX=width/2.f+camera.XScale*fed.WorldPos[0]/depth;
        float const expected=width/2.f+camera.XScale*transform[9]/depth+b.shift;
        assert(std::abs(screenX-expected)<.001f); // No lost shift or double application.
        assert(fed.WorldPos[1]==transform[10]&&fed.WorldPos[2]==transform[11]);
        assert(fed.HalfExtents[0]==b.HalfExtents[0]&&fed.HalfExtents[1]==b.HalfExtents[1]);
        ++cases;
    }
    printf("PASS: %u tooltip anchors across 4:3/16:9/ultrawide, both sides, mesh/montage, depths and nested shifts; IDS and shortcut preserved\n",cases);
}
'''
(out / 'check.cpp').write_text(fixture + function + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include'] + [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] + [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)
