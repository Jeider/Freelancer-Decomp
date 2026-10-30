// Exercises the production RP9 pass/state code on a hidden D3D9 window.
#include "RP9Ex.h"
#include "../../src/freelancer/Client/hud_tilt_math.h"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>
static void Need(bool b,const char* s) { if(!b) { std::printf("FAIL: %s\n",s);std::exit(1); } }
static void Check(HRESULT h) { if(FAILED(h)) {std::printf("HRESULT %08lx\n",h);std::exit(2);} }
static std::vector<unsigned char> Load(char const* path)
{
    std::ifstream f(path,std::ios::binary);
    return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};
}
int main()
{
    setvbuf(stdout,nullptr,_IONBF,0);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
    HWND w=CreateWindowA("STATIC","HUD tilt check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    auto* api=Direct3DCreate9(D3D_SDK_VERSION);Need(api!=nullptr,"D3D9");
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
    auto* p=new FDirectX9();p->Device_=d;p->DeviceReady_=1;
    p->Ex_->BackBufferWidth=p->Ex_->BackBufferHeight=64;
    p->ViewportCache_={0,0,64,64,0,1};p->bViewportRectValid_=p->bDepthRangeValid_=1;
    FRPExTexture* target=nullptr;FRPExRenderTargetDesc td={64,64,1,RPExFormatA8R8G8B8};Check(p->CreateExRenderTarget(&td,&target));
    auto rs=[&](unsigned s,unsigned v){p->RenderStates_.MarkDirty(s,v);};
    rs(D3DRS_ZENABLE,0);rs(D3DRS_ZWRITEENABLE,0);rs(D3DRS_LIGHTING,0);rs(D3DRS_CULLMODE,D3DCULL_NONE);
    rs(D3DRS_ALPHABLENDENABLE,1);rs(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);rs(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    rs(D3DRS_COLORWRITEENABLE,15);rs(D3DRS_BLENDOP,D3DBLENDOP_ADD);
    p->FlushDrawState(d);
    d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);
    d->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);d->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_DIFFUSE);
    d->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
    Check(d->BeginScene());
    const FRPExPassDesc capture={target,RPExPassClearColor|RPExPassHudSurface,0};Check(p->BeginExPass(&capture));
    Need(p->RenderStates_.Entries[D3DRS_ALPHABLENDENABLE].Pending==1,"capture preserves legacy blend state");
    struct V {float x,y,z,rhw;DWORD colour;};
    auto draw=[&](DWORD colour) {
        V q[4]={{-.5f,-.5f,0,1,colour},{63.5f,-.5f,0,1,colour},{-.5f,63.5f,0,1,colour},{63.5f,63.5f,0,1,colour}};
        p->FlushDrawState(d);Check(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));
        Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));
    };
    draw(0x8000ff00); // 50% green coverage
    rs(D3DRS_DESTBLEND,D3DBLEND_ONE);draw(0x80ff0000); // red light adds colour, not coverage
    Check(p->EndExPass());Need(!p->Ex_->bHudSurfacePass,"capture flag restored");
    Need(p->RenderStates_.Entries[D3DRS_DESTBLEND].Pending==D3DBLEND_INVSRCALPHA,"blend state restored");
    Check(d->EndScene());
    IDirect3DSurface9* read=nullptr;Check(d->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
    auto pixel=[&](IDirect3DSurface9* source) {
        Check(d->GetRenderTargetData(source,read));D3DLOCKED_RECT l={};Check(read->LockRect(&l,nullptr,D3DLOCK_READONLY));
        DWORD v=*reinterpret_cast<DWORD*>(static_cast<unsigned char*>(l.pBits)+32*l.Pitch+32*4);read->UnlockRect();return v;
    };
    DWORD c=pixel(target->Surface);std::printf("Captured ARGB: %08lx\n",c);
    Need(((c>>24)&255)>=127 && ((c>>24)&255)<=129,"coverage alpha is not squared or increased by additive light");
    Need(((c>>16)&255)>=127 && ((c>>8)&255)>=127,"premultiplied colour and additive light retained");
    FRPExProgram shader={};auto vs=Load("src/obj/hud_tilt_checks/VSMain.bin"),ps=Load("src/obj/hud_tilt_checks/PSMain.bin");
    Need(!vs.empty()&&!ps.empty(),"compiled production shader");
    Check(d->CreateVertexShader(reinterpret_cast<DWORD*>(vs.data()),&shader.Vs));
    Check(d->CreatePixelShader(reinterpret_cast<DWORD*>(ps.data()),&shader.Ps));
    Check(d->BeginScene());FRPExPassDesc composite={nullptr,RPExPassClearColor,0xff000050};Check(p->BeginExPass(&composite));
    Check(p->BindExProgram(&shader));FRPExSamplerState sampler={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    Check(p->BindExTexture(0,target,&sampler));auto t=HudTiltTransform::Make(64,64,-1,10);
    const float panel[]={t.PivotX,t.PivotY,t.Cos,t.K},size[]={64,64,1.f/64,1.f/64};
    p->SetExPixelConstants(0,panel,1);p->SetExPixelConstants(1,size,1);
    rs(D3DRS_ALPHABLENDENABLE,1);rs(D3DRS_SRCBLEND,D3DBLEND_ONE);rs(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);rs(D3DRS_SEPARATEALPHABLENDENABLE,0);
    Check(p->DrawFullscreenQuad());Check(p->EndExPass());Check(d->EndScene());
    IDirect3DSurface9* back=nullptr;Check(d->GetRenderTarget(0,&back));c=pixel(back);std::printf("Composited ARGB: %08lx\n",c);
    Need((c&255)>=39 && (c&255)<=41,"scene transmitted through 50% panel coverage");
    Need(((c>>16)&255)>=127 && ((c>>8)&255)>=127,"shader preserves panel light");
    back->Release();read->Release();shader.Vs->Release();shader.Ps->Release();p->DestroyExTexture(target);
    p->Device_=nullptr;p->DeviceReady_=0;delete p;d->Release();api->Release();DestroyWindow(w);
    puts("PASS: production capture, transparency, additive light, shader composite and pass restore");
}
