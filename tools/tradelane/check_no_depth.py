"""Exercise the production draw caller and all four shaders without INTZ; never launch the game."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/tradelane_depth/no_intz'
GAME_SHADER = Path('D:/Games/FL_MOD/DATA_EXTRA/SHADERS/tradelane_corridor.hlsl')
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

STUB = r'''
#define FREELANCER_RP9
#define NOMINMAX
#include <windows.h>
#include <d3d9.h>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <algorithm>
#include "tradelane_visual_mesh.h"
#include "tradelane_visual_style.h"
constexpr int GR_OK=0, RPExPassKeepDepth=1, RPExFilterLinear=1, RPExFilterPoint=0,
 RPExMipNone=0, RPExAddressWrap=1, RPExAddressClamp=0, kGameOptEffectsGroup=1;
constexpr bool kTradeLaneRefractionEnabled=false;
struct FRPExTexture {};
struct FRPExPassDesc {FRPExTexture* target;unsigned long flags,color;};
struct FRPExSamplerState {int filter,mip,u,v,w;};
struct FSpaceCamera {
 float view[12]={1,0,0,0,1,0,0,0,1},pos[3]={};int vp[4]={0,0,2559,1439};
 float const* GetViewTransform(){return view;}float const* GetPosition(){return pos;}
 int const* GetViewport(){return vp;}float GetZNear(){return 1;}float GetZFar(){return 20000;}
} camera;
FSpaceCamera* GetFirstPersonSpaceCamera(){return &camera;}
FSpaceCamera* GetThirdPersonSpaceCamera(){return nullptr;}
FSpaceCamera* GetTurretSpaceCamera(){return nullptr;}
FSpaceCamera* GetRearViewSpaceCamera(){return nullptr;}
FSpaceCamera* AsCamera(FSpaceCamera* c){return c;}void Win3DApplyCamera(FSpaceCamera*){}
bool GetGameOption(int){return true;}bool EnsureProgram(){return true;}
float Smooth(float t){t=std::clamp(t,0.f,1.f);return t*t*(3-2*t);}
struct {bool Active=true,Stopping=false;float Intensity=1,Age=2,ExitAge=0,Time=3;double Phase=.3125;
 struct {float D[3][3]={{1,0,0},{0,1,0},{0,0,1}};} Rotation;FTradeLaneVisualStyle Style;} G_Travel;
void *G_Program=nullptr,*G_WarpProgram=nullptr,*G_Buffer=nullptr;
FRPExTexture *G_SceneCopy=nullptr,*G_Noise=nullptr;
struct Capture {int CaptureSceneColor(FRPExTexture*){assert(false);return -1;}};Capture* G_Capture=nullptr;
struct IRenderPipeline {
 bool failWindow=false;int width=2560,height=1440,windowCalls=0;unsigned z=9;
 int GetProjection(float* v){v[0]=v[5]=v[10]=v[15]=1;return 0;}
 int GetWindow(HWND*,int*,int*,int* w,int* h){++windowCalls;*w=width;*h=height;return failWindow?-1:0;}
 int GetDepthRange(float* a,float* b){*a=0;*b=.9f;return 0;}
 int SetRenderState(unsigned s,unsigned v){if(s==D3DRS_ZENABLE)z=v;return 0;}
} pipe;
namespace DALib {IRenderPipeline* Pipeline=&pipe;}
struct IRenderPipelineEx {
 bool depth=false,badSize=false,failPass=false,inPass=false;int draws=0,begins=0,ends=0;
 unsigned long flags=0;float vertex[52]={},pixel[32]={};FRPExTexture depthTexture;
 int GetSceneDepth(FRPExTexture** p){*p=depth?&depthTexture:nullptr;return depth?0:-1;}
 int GetExTextureSize(FRPExTexture*,unsigned long* w,unsigned long* h){*w=2560;*h=1440;return badSize?-1:0;}
 int BeginExPass(FRPExPassDesc* p){++begins;if(failPass)return -1;assert(!inPass);inPass=true;flags=p->flags;return 0;}
 int EndExPass(){assert(inPass);inPass=false;++ends;return 0;}
 int BindExProgram(void*){assert(inPass);return 0;}
 int BindExTexture(int,FRPExTexture*,FRPExSamplerState*){assert(inPass);return 0;}
 int SetExVertexConstants(int start,float const* p,int count){std::copy(p,p+count*4,vertex+start*4);return 0;}
 int SetExPixelConstants(int start,float const* p,int count){std::copy(p,p+count*4,pixel+start*4);return 0;}
 int DrawExVertexBuffer(void*,unsigned,unsigned,unsigned,unsigned,unsigned){assert(inPass);++draws;return 0;}
} ex;
namespace RenderEx {IRenderPipelineEx* GetPipelineEx(){return &ex;}IRenderPipelineEx* GetDrawEx(){return &ex;}}
'''

TEST = r'''
void reset(){pipe=IRenderPipeline();ex=IRenderPipelineEx();camera=FSpaceCamera();}
void closeValue(float a,float b){assert(std::abs(a-b)<.00001f);}
int main(){
 reset();TradeLaneVisualDraw(&camera);
 assert(ex.draws==1&&ex.begins==1&&ex.ends==1&&pipe.windowCalls==1);
 assert(ex.flags==RPExPassKeepDepth&&pipe.z==1&&ex.pixel[11]==0);
 closeValue(ex.vertex[28],1);closeValue(ex.vertex[29],1);closeValue(ex.pixel[8],1.f/2560);
 puts("PASS production draw: no INTZ + no scene copy still submits the corridor");
 camera.vp[0]=128;camera.vp[1]=144;camera.vp[2]=2431;camera.vp[3]=1295;
 TradeLaneVisualDraw(&camera);assert(ex.draws==2);closeValue(ex.vertex[28],.9f);closeValue(ex.vertex[29],.8f);
 closeValue(ex.vertex[30],0);closeValue(ex.vertex[31],0);closeValue(ex.pixel[12],128.5f/2560);closeValue(ex.pixel[13],144.5f/1440);
 pipe.width=1920;pipe.height=1080;camera.vp[0]=0;camera.vp[1]=0;camera.vp[2]=1919;camera.vp[3]=1079;
 TradeLaneVisualDraw(&camera);closeValue(ex.vertex[28],1);closeValue(ex.vertex[29],1);closeValue(ex.pixel[8],1.f/1920);
 puts("PASS camera sub-viewport and changed render resolution");
 reset();ex.depth=true;pipe.failWindow=true;TradeLaneVisualDraw(&camera);
 assert(ex.draws==1&&pipe.windowCalls==0&&ex.flags==0&&pipe.z==0&&ex.pixel[11]==1);
 reset();ex.depth=true;ex.badSize=true;TradeLaneVisualDraw(&camera);assert(ex.draws==1&&pipe.windowCalls==1);
 puts("PASS original sampled-depth path and size-query fallback");
 reset();pipe.failWindow=true;TradeLaneVisualDraw(&camera);assert(ex.draws==0&&ex.begins==0);
 reset();pipe.width=0;TradeLaneVisualDraw(&camera);assert(ex.draws==0&&ex.begins==0);
 reset();pipe.height=-1;TradeLaneVisualDraw(&camera);assert(ex.draws==0&&ex.begins==0);
 reset();ex.failPass=true;TradeLaneVisualDraw(&camera);assert(ex.draws==0&&ex.ends==0);
 puts("PASS unavailable dimensions/device fail without submitting invalid draws");
}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/freelancer/Client/tradelane_visual.cpp'
    text = source.read_text()
    draw = text[text.index('void TradeLaneVisualDraw('):text.index('void TradeLaneVisualRenderShutdown(')]
    (OUT / 'caller.cpp').write_text(STUB + draw + TEST)
    compiler, env = compiler_env()
    dx = Path('C:/DXSDK_Jun10')
    env['INCLUDE'] += ';' + str(dx / 'Include')
    env['FREELANCER_SHADER_CACHE_DIR'] = str(OUT / 'cache')
    common = [str(compiler / 'cl.exe'), '/nologo', '/std:c++17', '/O2', '/EHsc', '/MT',
              '/D_CRT_SECURE_NO_WARNINGS', '/I' + str(ROOT / 'src/freelancer/Client')]
    def run(args, name, cwd=OUT):
        result = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (OUT / (name + '.log')).write_text(result.stdout)
        print(result.stdout, end='', flush=True)
        result.check_returncode()
    run(common + ['caller.cpp', '/Fecaller.exe'], 'caller_build')
    run([str(OUT / 'caller.exe')], 'caller')
    run(common + [str(ROOT / 'tools/check_tradelane_render.cpp'), '/Fegpu.exe', '/link',
                  'd3d9.lib', str(dx / 'Lib/x86/d3dx9.lib'), 'user32.lib'], 'gpu_build')
    run([str(OUT / 'gpu.exe'), '--no-depth', str(GAME_SHADER)], 'gpu', ROOT)
    paths = [source, GAME_SHADER, ROOT / 'tools/check_tradelane_render.cpp', Path(__file__)]
    (OUT / 'verified.json').write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, indent=2))


if __name__ == '__main__':
    main()
