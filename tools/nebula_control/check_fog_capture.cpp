#include "RP9FogCapture.h"
#include <cstdlib>

static void Check(HRESULT hr) {if(FAILED(hr)){printf("FAIL HRESULT=%08lx\n",hr);exit(1);}}
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    SetEnvironmentVariableA("LOCALAPPDATA",argv[1]);
    HWND window=CreateWindowA("STATIC","Fog capture check",WS_OVERLAPPEDWINDOW,0,0,64,64,nullptr,nullptr,GetModuleHandleA(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 3;
    D3DPRESENT_PARAMETERS p={};p.Windowed=TRUE;p.SwapEffect=D3DSWAPEFFECT_DISCARD;
    p.hDeviceWindow=window;p.BackBufferWidth=p.BackBufferHeight=64;p.BackBufferFormat=D3DFMT_X8R8G8B8;
    IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&p,&d));
    IDirect3DSurface9 *scene=nullptr,*low=nullptr;
    Check(d->GetRenderTarget(0,&scene));
    Check(d->CreateRenderTarget(16,16,D3DFMT_X8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&low,nullptr));
    Rp9FogCapture::Scope(512);
    if(Rp9FogCapture::Get().Enabled)return 4; // default off with no port.ini
    Rp9FogCapture::BeforeVolume(scene);Rp9FogCapture::Present(d);
    if(Rp9FogCapture::Get().Count!=0)return 5;
    Rp9FogCapture::Get().Enabled=true;
    Rp9FogCapture::Get().Armed=true; // substitute for the explicit user hotkey
    for(int frame=0;frame<3;++frame) {
        Rp9FogCapture::Scope(512);Rp9FogCapture::Get().Due=0;
        Check(d->BeginScene());Check(d->SetRenderTarget(0,scene));
        Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0xffff0000,1,0));
        Check(d->SetRenderTarget(0,low));Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0xffffff00,1,0));
        Check(d->SetRenderState(D3DRS_CULLMODE,D3DCULL_CW));
        Rp9FogCapture::BeforeVolume(scene);
        IDirect3DSurface9* current=nullptr;Check(d->GetRenderTarget(0,&current));
        if(current!=low)return 6;current->Release();
        DWORD cull=0;Check(d->GetRenderState(D3DRS_CULLMODE,&cull));if(cull!=D3DCULL_CW)return 7;
        Check(d->SetRenderTarget(0,scene));Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0xff00ff00,1,0));
        Rp9FogCapture::AfterVolume(scene);
        Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0xff0000ff,1,0));Check(d->EndScene());
        Rp9FogCapture::Present(d);
    }
    if(Rp9FogCapture::Get().Count!=2)return 8;
    low->Release();scene->Release();d->Release();api->Release();DestroyWindow(window);
    puts("PASS default off, two frames only, render target and render state preserved");
}
