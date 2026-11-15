#include "RP9ShaderStartup.h"
#include <cassert>

static unsigned Deactivations=0;
static LRESULT CALLBACK TestWindowProc(HWND H,UINT M,WPARAM W,LPARAM L) {
    if(M==WM_ACTIVATE && LOWORD(W)==WA_INACTIVE) ++Deactivations;
    return DefWindowProcA(H,M,W,L);
}

int main(int argc,char** argv) {
    if(argc!=3) return 2;
    const std::string Directory=argv[1];
    SetEnvironmentVariableA("FREELANCER_SHADER_CACHE_DIR",argv[2]);
    std::vector<Rp9Startup::FJob> Jobs;std::string Error;
    if(!Rp9Startup::Build(Directory,Jobs,Error)) {puts(Error.c_str());return 1;}
    IDirect3D9* D3d=Direct3DCreate9(D3D_SDK_VERSION);
    if(!D3d) return 1;
    WNDCLASSA Class={};Class.lpfnWndProc=TestWindowProc;Class.hInstance=GetModuleHandleA(nullptr);
    Class.lpszClassName="ShaderStartupRegression";assert(RegisterClassA(&Class));
    HWND Window=CreateWindowA(Class.lpszClassName,"Shader validation",WS_POPUP,0,0,32,32,nullptr,nullptr,Class.hInstance,nullptr);
    D3DPRESENT_PARAMETERS P={};P.Windowed=TRUE;P.SwapEffect=D3DSWAPEFFECT_DISCARD;
    P.hDeviceWindow=Window;P.BackBufferWidth=P.BackBufferHeight=32;P.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* Device=nullptr;
    if(FAILED(D3d->CreateDevice(0,D3DDEVTYPE_HAL,Window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&P,&Device))) return 1;
    D3DADAPTER_IDENTIFIER9 Ident={};D3d->GetAdapterIdentifier(0,0,&Ident);
    printf("GPU: %s\n",Ident.Description);
    ShowWindow(Window,SW_SHOW);SetActiveWindow(Window);
    assert(GetActiveWindow()==Window);
    const unsigned Before=Deactivations;
    IDirect3DSurface9* Depth=nullptr;
    assert(SUCCEEDED(Device->CreateDepthStencilSurface(32,32,D3DFMT_D24S8,D3DMULTISAMPLE_NONE,0,FALSE,&Depth,nullptr)));
    assert(SUCCEEDED(Device->SetDepthStencilSurface(Depth)));
    {
        Rp9Startup::Window Progress;
        assert(Progress.Get());
        assert(GetActiveWindow()==Window);
        assert(SendMessageW(Progress.Get(),WM_MOUSEACTIVATE,(WPARAM)Window,MAKELPARAM(HTCLIENT,WM_LBUTTONDOWN))==MA_NOACTIVATE);
        assert(Progress.Update(0,123));
        assert(Progress.Update(123,123));
        assert(GetActiveWindow()==Window);
    }
    assert(GetActiveWindow()==Window && Deactivations==Before);
    assert(SUCCEEDED(Device->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0)));
    Device->SetDepthStencilSurface(nullptr);Depth->Release();
    puts("PASS startup window preserves activation; mouse activation blocked; depth clear succeeds");
    unsigned Failed=0;
    for(unsigned Pass=0;Pass<2;++Pass) {
        std::vector<Rp9Startup::Result> Results;
        unsigned Previous=~0u;
        bool Completed=Rp9Startup::Prepare(Jobs,Directory,Results,[&](unsigned D,unsigned T) {
            if(D!=Previous) {printf("pass %u: %u/%u\n",Pass,D,T);fflush(stdout);Previous=D;}return true;
        });
        if(!Completed) return 1;
        unsigned Hits=0;
        for(size_t i=0;i<Jobs.size();++i) {
            HRESULT Hr=Rp9Startup::Validate(Device,Jobs[i],Results[i]);
            Hits+=Results[i].Hit;
            if(FAILED(Hr) || (Pass && !Results[i].Hit)) {
                printf("FAIL %s %s %s hr=%08lx hit=%d\n%s\n",Jobs[i].Name.c_str(),Jobs[i].Entry,Jobs[i].Profile,
                    (unsigned long)Hr,Results[i].Hit,Results[i].Message.c_str());++Failed;
            }
        }
        printf("pass %u: %zu shaders, %u cache hits, %u failures\n",Pass,Jobs.size(),Hits,Failed);
        if(Failed) break;
    }
    // Failure paths must never count as ready.
    Rp9Startup::FJob Bad{"this is not HLSL","main","ps_3_0",false,"invalid"};
    std::vector<unsigned char> Code;std::string Message;bool Hit=false;
    assert(FAILED(Rp9Startup::Compile(Bad,Directory,Code,Message,Hit)));
    std::string Blocked=std::string(argv[2])+"/not_a_directory";
    FILE* F=fopen(Blocked.c_str(),"wb");assert(F);fputs("occupied",F);fclose(F);
    SetEnvironmentVariableA("FREELANCER_SHADER_CACHE_DIR",Blocked.c_str());
    Rp9Startup::FJob Simple{"float4 main():COLOR{return 1;}","main","ps_3_0",false,"unwritable"};
    assert(FAILED(Rp9Startup::Compile(Simple,Directory,Code,Message,Hit)));
    std::vector<Rp9Startup::FJob> Missing;
    assert(!Rp9Startup::Build(Directory+"missing/",Missing,Error));
    puts("PASS compile failure, cache write failure, missing source block readiness");
    Device->Release();D3d->Release();DestroyWindow(Window);
    return Failed?1:0;
}
