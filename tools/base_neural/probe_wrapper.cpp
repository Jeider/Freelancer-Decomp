// Runs the exact D3D9 EndScene -> DX11 adapter -> D3D9 UI seam on a hidden window.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <wrl/client.h>
#include <cstdio>
#include "base_neural_bridge.h"
#include "BaseNeuralSupersample.h"
#include <vector>
using Microsoft::WRL::ComPtr;
struct Vertex { float x,y,z,w; DWORD color; };

int main(int argc, char** argv)
{
    unsigned mode=argc>1?static_cast<unsigned>(atoi(argv[1])):1;
    unsigned width=argc>2?atoi(argv[2]):512, height=argc>3?atoi(argv[3]):512;
    unsigned timeout=argc>4?atoi(argv[4]):50;
    bool strengthCycle=false,supersample=false,checker=false;
    for(int i=5;i<argc;i++){strengthCycle|=!strcmp(argv[i],"--strength-cycle");supersample|=!strcmp(argv[i],"--supersample");checker|=!strcmp(argv[i],"--checker");}
    if(width<16||height<16||width>4096||height>4096)return 30;
    WNDCLASSW wc={};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"BaseNeuralProbe";
    RegisterClassW(&wc);
    HWND window=CreateWindowW(wc.lpszClassName,L"Base NR GPU probe",WS_POPUP,0,0,width,height,nullptr,nullptr,wc.hInstance,nullptr);
    HMODULE library=LoadLibraryW(L"D3D9.dll");
    auto create=reinterpret_cast<IDirect3D9*(WINAPI*)(UINT)>(GetProcAddress(library,"Direct3DCreate9"));
    if(!create)return 2;
    ComPtr<IDirect3D9> d3d;d3d.Attach(create(D3D_SDK_VERSION));
    D3DPRESENT_PARAMETERS pp={};pp.BackBufferWidth=width;pp.BackBufferHeight=height;pp.BackBufferFormat=D3DFMT_X8R8G8B8;
    pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.Windowed=TRUE;
    pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
    ComPtr<IDirect3DDevice9> device;
    HRESULT hr=d3d->CreateDevice(D3DADAPTER_DEFAULT,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device);
    if(FAILED(hr)){printf("D3D9 device failed %08lx\n",hr);return 3;}
    BaseNeuralBridge::Api const* api=nullptr;
    ComPtr<IDirect3DSurface9> target,readback;
    device->GetRenderTarget(0,&target);
    if(FAILED(device->CreateOffscreenPlainSurface(width,height,D3DFMT_X8R8G8B8,D3DPOOL_SYSTEMMEM,&readback,nullptr)))return 4;
    unsigned applied=0;int last=-99;ULONGLONG deadline=GetTickCount64()+120000;
    double applied_ms=0,max_ms=0;LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);
    BaseNeuralSupersample ss;
    if(supersample){
        device->BeginScene();
        if(ss.Begin(device.Get(),1.f)!=S_FALSE||ss.Active())return 35;
        if(ss.Begin(device.Get(),NAN)!=S_FALSE||ss.Active())return 36;
        if(ss.Begin(device.Get(),1.5f)!=S_OK)return 37;
        ss.Reset(); // aborted frame/device-reset path must restore the native target.
        ComPtr<IDirect3DSurface9> restored;device->GetRenderTarget(0,&restored);D3DVIEWPORT9 v;device->GetViewport(&v);
        if(restored.Get()!=target.Get()||v.Width!=width||v.Height!=height||ss.Active())return 38;
        device->EndScene();
    }
    for(unsigned n=0;GetTickCount64()<deadline&&applied<8;n++)
    {
        MSG msg;while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessageW(&msg);}
        device->BeginScene();
        if(supersample&&ss.Begin(device.Get(),1.5f)!=S_OK){puts("FAIL supersample Begin");return 31;}
        D3DVIEWPORT9 viewport={};device->GetViewport(&viewport);
        unsigned renderW=supersample?width*3/2:width,renderH=supersample?height*3/2:height;
        if(viewport.Width!=renderW||viewport.Height!=renderH)return 32;
        device->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,1,0);
        DWORD color=D3DCOLOR_XRGB(n%256,127,241);
        Vertex vertices[]={{-.5f,-.5f,.5f,1,color},{renderW-.5f,-.5f,.5f,1,color},
                           {-.5f,renderH-.5f,.5f,1,color},{renderW-.5f,renderH-.5f,.5f,1,color}};
        device->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE);device->SetRenderState(D3DRS_LIGHTING,FALSE);
        device->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);device->SetTexture(0,nullptr);
        device->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices,sizeof(Vertex));
        if(checker){
            device->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0);
            std::vector<D3DRECT> stripes;for(unsigned x=0;x<renderW;x+=2)stripes.push_back({LONG(x),0,LONG(x+1),LONG(renderH)});
            device->Clear(UINT(stripes.size()),stripes.data(),D3DCLEAR_TARGET,0xffffffff,1,0);
        }
        device->EndScene();
        if(!api)
        {
            HMODULE addon=GetModuleHandleW(L"fl_base_neural.addon32");
            if(addon){auto get=reinterpret_cast<BaseNeuralBridge::GetApi>(GetProcAddress(addon,"FlBaseNeuralGetApi"));if(get)api=get(BaseNeuralBridge::Version);}
        }
        int result=0;
        float strength=strengthCycle ? (applied%3==0?0.f:applied%3==1?.5f:1.f) : 1.f;
        if(api)
        {
            BaseNeuralBridge::Frame f={sizeof(f),BaseNeuralBridge::Version,n+1,1,1,renderW,renderH,mode,applied==0,timeout,1};
            f.strength=strength;
            LARGE_INTEGER begin,end;QueryPerformanceCounter(&begin);
            result=api->process(&f);
            QueryPerformanceCounter(&end);
            if(result==BaseNeuralBridge::Applied){double ms=1000.0*(end.QuadPart-begin.QuadPart)/frequency.QuadPart;applied_ms+=ms;if(ms>max_ms)max_ms=ms;}
        }
        if(result!=last){printf("frame %u: result %d, addon=%s\n",n,result,api?"loaded":"absent");fflush(stdout);last=result;}
        if(result<0){api->stop();return 5;}
        if(supersample){
            device->BeginScene();HRESULT resolved=ss.End(true);device->EndScene();
            if(FAILED(resolved)){printf("FAIL resolve %08lx\n",resolved);return 33;}
            ComPtr<IDirect3DSurface9> restored;device->GetRenderTarget(0,&restored);device->GetViewport(&viewport);
            if(restored.Get()!=target.Get()||viewport.Width!=width||viewport.Height!=height||ss.Active())return 34;
        }
        if(result==BaseNeuralBridge::Applied)
        {
            // UI is drawn after neural processing and must stay pixel-exact too.
            device->BeginScene();D3DRECT rect={0,0,16,16};device->Clear(1,&rect,D3DCLEAR_TARGET,0xffff00ff,1,0);device->EndScene();
            if(FAILED(device->GetRenderTargetData(target.Get(),readback.Get()))){api->stop();return 6;}
            D3DLOCKED_RECT locked={};readback->LockRect(&locked,nullptr,D3DLOCK_READONLY);bool ok=true;
            for(unsigned y=0;y<height;y++)for(unsigned x=0;x<width;x++)
            {
                DWORD pixel=*reinterpret_cast<DWORD*>(static_cast<BYTE*>(locked.pBits)+y*locked.Pitch+4*x)&0xffffff;
                if(x<16&&y<16){if(pixel!=0xff00ff)ok=false;}
                else if((mode==1||strength==0)){
                    if(checker){
                        double lo=x*1.5,hi=lo+1.5,white=0;
                        for(int sx=int(floor(lo));sx<int(ceil(hi));sx++)if(sx%2==0)white+=fmax(0.,fmin(hi,sx+1.)-fmax(lo,double(sx)));
                        double linear=white/1.5;int expected=int(lround(255*(linear<=.0031308?linear*12.92:1.055*pow(linear,1./2.4)-.055)));
                        for(unsigned shift=0;shift<24;shift+=8)if(abs(int((pixel>>shift)&255)-expected)>2)ok=false;
                    }else if(pixel!=(color&0xffffff))ok=false;
                }
            }
            readback->UnlockRect();if(!ok){puts("FAIL pixels/UI changed or stale");api->stop();return 7;}
            applied++;
            if(strengthCycle)printf("PASS strength %.0f%%, pixels/UI checked\n",strength*100);
        }
        device->Present(nullptr,nullptr,nullptr,nullptr);Sleep(16);
    }
    if(api)api->stop();
    ss.Reset();
    if(applied!=8){puts("FAIL adapter never completed eight frames");return 8;}
    puts("PASS D3D9->DX11->host->DX11->D3D9, eight frames, UI preserved, session stopped");
    printf("Process latency: mean %.2f ms, max %.2f ms; deadline %u ms\n",applied_ms/applied,max_ms,timeout);
    readback.Reset();target.Reset();device.Reset();d3d.Reset();DestroyWindow(window);
    return 0;
}
