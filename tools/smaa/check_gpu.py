"""Compile/exercise the production SMAA pass on D3D9 in a hidden test window."""
import os
from pathlib import Path
import shutil
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/smaa/check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/RP9/RP9Ex.cpp').read_text()
start = source.index('GENRESULT FDirectX9::ExApplySmaa()')
end = source.index('// The finished frame through one pixel shader', start)
method = source[start:end]
state_source = (repo / 'src/RP9/RP9Ex.h').read_text()
state = state_source[state_source.index('    bool bQualityConfigRead'):state_source.index('    float ShadowBiasScale')]
stub = r'''
#define NOMINMAX
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <d3d9.h>
#include <d3dx9.h>
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include "RP9DeviceCallCache.h"
using GENRESULT=HRESULT;
constexpr HRESULT GR_GENERIC=E_FAIL;
struct FRp9GpuTimers {enum {AaBegin,AaEnd};};
struct FRp9ExState { STATE };
void FlushDrawState(IDirect3DDevice9*){}
struct FDirectX9 {
    IDirect3DDevice9* Device_=nullptr;FRp9ExState* Ex_=nullptr;
    void ExSurfaceRelease(){}
    void ExGpuMark(unsigned){}
    GENRESULT ExApplySmaa();
};
int compiles=0;
bool CompileStage(std::string const& source,std::string const&,ID3DXInclude*,
                  std::string const& entry,char const* profile,std::vector<unsigned char>* code){
    ID3DXBuffer* output=nullptr;ID3DXBuffer* errors=nullptr;
    HRESULT hr=D3DXCompileShader(source.c_str(),(UINT)source.size(),nullptr,nullptr,
                                entry.c_str(),profile,0,&output,&errors,nullptr);
    if(errors){printf("%s: %s\n",entry.c_str(),(char*)errors->GetBufferPointer());errors->Release();}
    if(FAILED(hr))return false;
    auto* begin=(unsigned char*)output->GetBufferPointer();
    code->assign(begin,begin+output->GetBufferSize());output->Release();++compiles;return true;
}
char const* modulePath=nullptr;
DWORD TestModulePath(HMODULE,char* out,DWORD size){strncpy_s(out,size,modulePath,_TRUNCATE);return (DWORD)strlen(out);}
#define GetModuleFileNameA TestModulePath
'''.replace('STATE', state)
checks = r'''
#undef GetModuleFileNameA
void Check(HRESULT hr){if(FAILED(hr)){printf("FAILED HRESULT %08lx\n",hr);fflush(stdout);abort();}}
void Release(FRp9ExState& e){
    for(auto*& p:e.QualitySmaaPs){if(p)p->Release();p=nullptr;}
    for(auto*& p:e.QualitySmaaLookup){if(p)p->Release();p=nullptr;}
    for(auto*& p:e.QualitySmaaTargets){if(p)p->Release();p=nullptr;}
    if(e.QualitySceneCopy)e.QualitySceneCopy->Release();e.QualitySceneCopy=nullptr;
    if(e.QualitySavedState)e.QualitySavedState->Release();e.QualitySavedState=nullptr;
}
std::vector<DWORD> Read(IDirect3DDevice9* d,IDirect3DSurface9* rt,UINT w,UINT h){
    IDirect3DSurface9* copy=nullptr;
    Check(d->CreateOffscreenPlainSurface(w,h,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&copy,nullptr));
    Check(d->GetRenderTargetData(rt,copy));D3DLOCKED_RECT lock={};Check(copy->LockRect(&lock,nullptr,D3DLOCK_READONLY));
    std::vector<DWORD> result(w*h);
    for(UINT y=0;y<h;++y)memcpy(result.data()+y*w,(char*)lock.pBits+y*lock.Pitch,w*4);
    Check(copy->UnlockRect());copy->Release();return result;
}
int main(int argc,char** argv){
    assert(argc==2);modulePath=argv[1];
    HWND window=CreateWindowExA(0,"STATIC","SMAA check",WS_OVERLAPPEDWINDOW,0,0,320,240,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    assert(window); // Intentionally never shown.
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);assert(api);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.hDeviceWindow=window;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=320;pp.BackBufferHeight=240;pp.BackBufferFormat=D3DFMT_X8R8G8B8;
    pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
    IDirect3DDevice9* d=nullptr;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&d));
    FRp9ExState state;FDirectX9 pipe;pipe.Device_=d;pipe.Ex_=&state;
    IDirect3DSurface9* back=nullptr;Check(d->GetRenderTarget(0,&back));
    for(UINT width:{128u,191u,1920u})for(bool inside:{false,true}){
        UINT height=width==128?96:width==191?107:1080;
        IDirect3DSurface9* rt=nullptr;IDirect3DSurface9* depth=nullptr;
        Check(d->CreateRenderTarget(width,height,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&rt,nullptr));
        Check(d->CreateDepthStencilSurface(width,height,D3DFMT_D24S8,D3DMULTISAMPLE_NONE,0,TRUE,&depth,nullptr));
        Check(d->SetRenderTarget(0,rt));Check(d->SetDepthStencilSurface(depth));
        std::vector<DWORD> pixels(width*height);
        for(UINT y=0;y<height;++y)for(UINT x=0;x<width;++x)
            pixels[y*width+x]=x>y*3/5+width/4?0xffffffff:0xff000000;
        Check(D3DXLoadSurfaceFromMemory(rt,nullptr,nullptr,pixels.data(),D3DFMT_A8R8G8B8,width*4,nullptr,
                                       &RECT{0,0,(LONG)width,(LONG)height},D3DX_FILTER_NONE,0));
        D3DVIEWPORT9 view={3,4,width-7,height-9,.2f,.8f};Check(d->SetViewport(&view));
        Check(Rp9SetRenderState(d,D3DRS_ZENABLE,TRUE));Check(Rp9SetRenderState(d,D3DRS_ALPHABLENDENABLE,TRUE));
        Check(Rp9SetSamplerState(d,0,D3DSAMP_MINFILTER,D3DTEXF_POINT));
        float constants[4]={11,22,33,44};Check(Rp9SetPixelConstants(d,0,constants,1));
        if(inside){Check(d->BeginScene());state.bInScene=true;}
        Check(pipe.ExApplySmaa());assert(state.bInScene==inside);
        D3DVIEWPORT9 restored={};Check(d->GetViewport(&restored));assert(!memcmp(&view,&restored,sizeof(view)));
        DWORD value=0;Check(d->GetRenderState(D3DRS_ZENABLE,&value));assert(value==TRUE);
        Check(d->GetRenderState(D3DRS_ALPHABLENDENABLE,&value));assert(value==TRUE);
        Check(d->GetSamplerState(0,D3DSAMP_MINFILTER,&value));assert(value==D3DTEXF_POINT);
        float actual[4]={};Check(d->GetPixelShaderConstantF(0,actual,1));assert(!memcmp(actual,constants,sizeof(actual)));
        IDirect3DSurface9* bound=nullptr;Check(d->GetRenderTarget(0,&bound));assert(bound==rt);bound->Release();
        Check(d->GetDepthStencilSurface(&bound));assert(bound==depth);bound->Release();
        if(inside){Check(d->EndScene());state.bInScene=false;}
        auto filtered=Read(d,rt,width,height);unsigned changed=0,intermediate=0;
        for(size_t i=0;i<pixels.size();++i){changed+=pixels[i]!=filtered[i];DWORD gray=filtered[i]&255;intermediate+=gray>0&&gray<255;}
        assert(changed>20&&intermediate>20);assert(filtered[width*height-1]==0xffffffff&&filtered[0]==0xff000000);
        Check(D3DXSaveSurfaceToFileA("smaa.png",D3DXIFF_PNG,rt,nullptr,nullptr));
        printf("PASS: %ux%u inside=%d: %u changed, %u blended; state/depth/viewport restored\n",width,height,inside,changed,intermediate);
        // No edges on the next frame: discarded edge pixels must not keep old values.
        std::fill(pixels.begin(),pixels.end(),0xff686868);
        Check(D3DXLoadSurfaceFromMemory(rt,nullptr,nullptr,pixels.data(),D3DFMT_A8R8G8B8,width*4,nullptr,
                                       &RECT{0,0,(LONG)width,(LONG)height},D3DX_FILTER_NONE,0));
        Check(pipe.ExApplySmaa());assert(Read(d,rt,width,height)==pixels);
        Check(d->SetDepthStencilSurface(nullptr));Check(d->SetRenderTarget(0,back));depth->Release();rt->Release();
    }
    assert(compiles==3);puts("PASS: all three SM3 shaders reused; resize and flat frame without stale edges");
    Release(state);back->Release();
    Check(d->Reset(&pp));Rp9DeviceCalls().Invalidate();
    Check(pipe.ExApplySmaa());assert(compiles==6);puts("PASS: device reset recreates SMAA resources");
    Release(state);modulePath="Z:\\missing\\bin\\test.exe";
    assert(FAILED(pipe.ExApplySmaa()));puts("PASS: missing assets report failure for the FXAA fallback");
    d->Release();api->Release();DestroyWindow(window);
}
'''
# Avoid taking an address of a temporary RECT under conformant C++.
checks = checks.replace('        std::vector<DWORD> pixels(width*height);',
                        '        RECT area={0,0,(LONG)width,(LONG)height};\n        std::vector<DWORD> pixels(width*height);')
checks = checks.replace('&RECT{0,0,(LONG)width,(LONG)height}', '&area')
(out / 'check.cpp').write_text(stub + method + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
dx = Path('C:/DXSDK_Jun10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include', repo / 'src/RP9'] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')] + [dx / 'Include'])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
shutil.copy2(repo / 'bin/d3dx9_43.dll', out / 'd3dx9_43.dll')
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W3', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe', '/link', 'user32.lib', 'd3d9.lib',
                str(dx / 'Lib/x86/d3dx9.lib')], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe'), str(repo / 'bin/freelancer.exe')], cwd=out, check=True, timeout=120)
