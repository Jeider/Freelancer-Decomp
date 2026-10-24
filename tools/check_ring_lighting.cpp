// Standalone D3D9 HAL check of the unchanged production planet-ring shader.
#define NOMINMAX
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
static IDirect3DDevice9* D;
static IDirect3DSurface9 *RT,*CPU;
static IDirect3DVertexShader9* VS;
static IDirect3DPixelShader9* PS;
static IDirect3DTexture9* Texture;
static constexpr unsigned Size=256;
static void Check(HRESULT h){if(FAILED(h)){printf("FAIL HRESULT %08lx\n",h);exit(2);}}
static void Require(bool b,const char* name){printf("%s: %s\n",b?"PASS":"FAIL",name);if(!b)exit(3);}
template<class T>static void Release(T*& p){if(p){p->Release();p=nullptr;}}
static void Compile(){
    for(unsigned stage=0;stage<2;++stage){
        ID3DXBuffer *code=nullptr,*error=nullptr,*dis=nullptr;
        HRESULT hr=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/planet_ring.hlsl",nullptr,nullptr,
            stage?"PSMain":"VSMain",stage?"ps_3_0":"vs_3_0",0,&code,&error,nullptr);
        if(error){puts((char*)error->GetBufferPointer());Release(error);}Check(hr);
        if(stage)Check(D->CreatePixelShader((DWORD*)code->GetBufferPointer(),&PS));
        else Check(D->CreateVertexShader((DWORD*)code->GetBufferPointer(),&VS));
        Check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&dis));
        FILE* f=fopen(stage?"src/obj/ring_check/ps.asm":"src/obj/ring_check/vs.asm","wb");
        fwrite(dis->GetBufferPointer(),1,dis->GetBufferSize(),f);fclose(f);Release(dis);Release(code);
    }
}
struct Params{
    float c[10][4]={{0,0,10,1},{0,0,-1,4},{0,0,-100,3},{0,0,0,0},
        {0,0,0,1},{1,1,1,1},{0,1,0,1},{0,0,0,.5f},{1,.4f,1,0},{0,0,0,0}};
};
static std::vector<DWORD> Render(Params const& p,const char* name=nullptr){
    Check(D->SetPixelShaderConstantF(0,p.c[0],10));
    struct Vertex{float x,y,z;DWORD color;float u,v,u1,v1;};
    Vertex q[]={{-4.2f,-4.2f,10,0xffffffff,0,0,0,0},{4.2f,-4.2f,10,0xffffffff,1,0,1,0},
        {-4.2f,4.2f,10,0xffffffff,0,1,0,1},{4.2f,4.2f,10,0xffffffff,1,1,1,1}};
    Check(D->Clear(0,nullptr,D3DCLEAR_TARGET,0,1,0));Check(D->BeginScene());
    Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));Check(D->EndScene());
    Check(D->GetRenderTargetData(RT,CPU));
    if(name){char path[180];sprintf(path,"src/obj/ring_check/%s.png",name);Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,CPU,nullptr,nullptr));}
    D3DLOCKED_RECT r;Check(CPU->LockRect(&r,nullptr,D3DLOCK_READONLY));std::vector<DWORD> out(Size*Size);
    for(unsigned y=0;y<Size;++y)memcpy(out.data()+y*Size,(char*)r.pBits+y*r.Pitch,Size*4);
    Check(CPU->UnlockRect());return out;
}
static unsigned Changes(std::vector<DWORD>const&a,std::vector<DWORD>const&b,DWORD mask){
    unsigned n=0;for(unsigned i=0;i<a.size();++i)n+=((a[i]^b[i])&mask)!=0;return n;
}
int main(){
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);CreateDirectoryA("src/obj/ring_check",nullptr);
    HWND window=CreateWindowA("STATIC","ring check",WS_POPUP,0,0,32,32,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9 available");
    D3DADAPTER_IDENTIFIER9 adapter;Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s\n",adapter.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=32;pp.BackBufferHeight=32;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&D));Compile();
    Check(D->CreateRenderTarget(Size,Size,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&RT,nullptr));
    Check(D->CreateOffscreenPlainSurface(Size,Size,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&CPU,nullptr));Check(D->SetRenderTarget(0,RT));
    D3DVIEWPORT9 vp={0,0,Size,Size,0,1};Check(D->SetViewport(&vp));
    Check(D->CreateTexture(8,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&Texture,nullptr));
    D3DLOCKED_RECT lock;Check(Texture->LockRect(0,&lock,nullptr,0));
    for(unsigned y=0;y<64;++y)for(unsigned x=0;x<8;++x)
        ((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=D3DCOLOR_ARGB(65+y*2,170+y,115+y,65+y);
    Check(Texture->UnlockRect(0));Check(D->SetTexture(0,Texture));
    D->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);D->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
    D->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);D->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    D3DXMATRIX world,projection;D3DXMatrixIdentity(&world);D3DXMatrixOrthoLH(&projection,10,10,1,100);
    Check(D->SetVertexShaderConstantF(0,(float*)&world,4));Check(D->SetVertexShaderConstantF(4,(float*)&projection,4));
    float centre[4]={0,0,10,1},normal[4]={0,0,-1,2.5f};Check(D->SetVertexShaderConstantF(8,centre,1));Check(D->SetVertexShaderConstantF(9,normal,1));
    D->SetRenderState(D3DRS_ZENABLE,FALSE);D->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    // Raw premultiplied shader output lets the alpha contract be checked independently.
    D->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);D->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);
    Check(D->SetVertexShader(VS));Check(D->SetPixelShader(PS));Check(D->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX2));
    Params unlit;auto baseline=Render(unlit,"unlit");unsigned visible=0,translucent=0;
    for(DWORD p:baseline){visible+=(p&0xffffff)!=0;unsigned a=p>>24;translucent+=a>0&&a<255;}
    Require(visible>10000&&translucent>10000,"unlit band is visible and retains fractional alpha");
    Params changed=unlit;changed.c[2][0]=60;changed.c[2][1]=-30;changed.c[2][2]=30;
    changed.c[9][0]=2;changed.c[9][2]=5;changed.c[9][3]=2;
    auto noLight=Render(changed,"unlit_changed_sun_and_caster");
    Require(Changes(baseline,noLight,0xffffffff)==0,"zero SunColour and unit Ambient ignore sun position and neighbouring shadows exactly");
    Params lit=unlit;lit.c[4][0]=1;lit.c[4][1]=.8f;lit.c[4][2]=.6f;
    lit.c[5][0]=lit.c[5][1]=lit.c[5][2]=.05f;auto litBase=Render(lit,"lit");
    lit.c[9][0]=2;lit.c[9][2]=5;lit.c[9][3]=2;auto shadow=Render(lit,"lit_shadow");
    Require(Changes(litBase,shadow,0xffffff)>500,"ordinary lighting still responds to caster shadow");
    Require(Changes(litBase,shadow,0xff000000)==0&&Changes(baseline,litBase,0xff000000)==0,"lighting and shadows leave optical alpha unchanged");
    Params actualShadow=unlit;actualShadow.c[9][0]=2;actualShadow.c[9][2]=5;actualShadow.c[9][3]=2;
    Require(Changes(baseline,Render(actualShadow),0xffffffff)==0,"the validated neighbouring shadow disappears completely in unlit mode");
    Params hostShadow=unlit;hostShadow.c[3][0]=2;hostShadow.c[3][2]=-5;hostShadow.c[3][3]=2;
    Require(Changes(baseline,Render(hostShadow),0xffffffff)==0,"host planet shadow does not darken unlit ring when host is behind camera");
    Params coloured=lit;coloured.c[9][3]=0;coloured.c[4][0]=.1f;coloured.c[4][2]=1;
    Require(Changes(litBase,Render(coloured),0xffffff)>10000,"ordinary lighting still responds to sunlight colour");
    Params fade=unlit;fade.c[7][0]=20;fade.c[7][1]=5;auto fading=Render(fade,"unlit_fade");
    unsigned reduced=0;for(unsigned i=0;i<baseline.size();++i)reduced+=(baseline[i]>>24)>(fading[i]>>24);
    Require(reduced>10000,"approach fade remains active when lighting is disabled");
    fade.c[7][1]=20;fade.c[7][0]=30;auto gone=Render(fade);
    Require(std::all_of(gone.begin(),gone.end(),[](DWORD p){return p==0;}),"near fade fully removes unlit band");
    Params occluded=unlit;occluded.c[3][0]=1;occluded.c[3][2]=5;occluded.c[3][3]=1;auto hidden=Render(occluded,"unlit_host_occlusion");
    unsigned clipped=0,retained=0;for(unsigned i=0;i<baseline.size();++i){clipped+=(baseline[i]>>24)>0&&hidden[i]==0;retained+=baseline[i]==hidden[i]&&(hidden[i]>>24)>0;}
    Require(clipped>500&&retained>500,"host planet still clips covered pixels while leaving exposed unlit ring unchanged");
    Release(Texture);Release(VS);Release(PS);Release(RT);Release(CPU);Release(D);Release(api);DestroyWindow(window);
    puts("PASS ring lighting GPU checks; synthetic previews in src/obj/ring_check");
}
