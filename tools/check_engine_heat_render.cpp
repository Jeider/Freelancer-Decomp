// Reuse the D3D9 scene/depth fixture; test the production heat shader and mesh.
#define main ShipWarpFixtureMain
#include "check_ship_warp_render.cpp"
#undef main
#include "../src/freelancer/Client/engine_heat_mesh.h"

static void HeatCompile()
{
    Compile();
    for(int I=0;I<2;++I) {
        ID3DXBuffer *Code=nullptr,*Error=nullptr,*Asm=nullptr;
        HRESULT R=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/engine_heat.hlsl",nullptr,nullptr,
            I?"PSMain":"VSMain",I?"ps_3_0":"vs_3_0",0,&Code,&Error,nullptr);
        if(Error){puts((char*)Error->GetBufferPointer());Error->Release();}Check(R);
        Check(D3DXDisassembleShader((DWORD*)Code->GetBufferPointer(),FALSE,nullptr,&Asm));
        FILE* F=fopen(I?"src/obj/engine_heat_check/ps.asm":"src/obj/engine_heat_check/vs.asm","wb");
        fwrite(Asm->GetBufferPointer(),1,Asm->GetBufferSize(),F);fclose(F);Asm->Release();
        if(I){Warp->Release();Check(D->CreatePixelShader((DWORD*)Code->GetBufferPointer(),&Warp));}
        else {VS->Release();Check(D->CreateVertexShader((DWORD*)Code->GetBufferPointer(),&VS));}
        Code->Release();
    }
}
static void HeatGeometry()
{
    Mesh.clear();
    for(int S=-1;S<=1;S+=2)
        BuildEngineHeatVolume(Mesh,{S*12.f,-3,20},{1,0,0},{0,1,0},{0,0,1},3,52,S<0?.13f:.63f);
}
static void HeatCamera(int Kind)
{
    Camera(Kind==1);
    if(Kind!=2)return;
    D3DXVECTOR3 E(0,18,160),At(0,0,30),Up(0,1,0);Eye={E.x,E.y,E.z};D3DXMATRIX V;
    D3DXMatrixLookAtLH(&V,&E,&At,&Up);
    for(int R=0;R<3;++R)for(int C=0;C<4;++C)VC[R*4+C]=V.m[C][R]*(R==2?-1.f:1.f);
}
int main()
{
    CreateDirectoryA("src/obj/engine_heat_check",nullptr);CreateDirectoryA("src/obj/ship_warp_check",nullptr);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    auto* API=Direct3DCreate9(D3D_SDK_VERSION);Require(API!=nullptr,"D3D9 available");
    HWND Window=CreateWindowA("STATIC","engine heat check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    D3DPRESENT_PARAMETERS PP={};PP.Windowed=TRUE;PP.SwapEffect=D3DSWAPEFFECT_DISCARD;
    PP.BackBufferWidth=64;PP.BackBufferHeight=64;PP.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(API->CreateDevice(0,D3DDEVTYPE_HAL,Window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&PP,&D));HeatCompile();
    Check(D->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&RT,nullptr));
    Check(D->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&CPU,nullptr));
    Check(D->CreateDepthStencilSurface(W,H,D3DFMT_D24S8,D3DMULTISAMPLE_NONE,0,TRUE,&DS,nullptr));
    Check(D->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&Z,nullptr));
    Check(D->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&SceneCopy,nullptr));
    ShipGeometry();HeatGeometry();WarpOn=true;GlowOn=false;PatternOn=true;
    bool Finite=true;for(auto const& V:Mesh)for(float P:V.Position)Finite=Finite&&std::isfinite(P);
    Require(Finite&&Mesh.size()==2*12*16*6,"two finite bounded exhaust volumes");
    for(int Partition=0;Partition<2;++Partition)for(int Kind=0;Kind<3;++Kind) {
        HeatCamera(Kind);VC[34]=PC[10]=Partition?.1f:0;VC[35]=PC[11]=Partition?1.f:.9f;
        auto Base=Render(nullptr,0),Heat=Render(Kind==2?"engine_heat_rear":Kind==1?"engine_heat_side":"engine_heat_front");
        Require(Changes(Base,Heat)>20,"heat distorts the scene from front, side and rear");
        Require(Changes(Heat,Render(nullptr))==0,"pause freezes thermal eddies exactly");
        PC[0]=3.2f;Require(Changes(Heat,Render(nullptr))>20,"heat advects with simulation time");PC[0]=3;
        Require(Changes(Base,Render(nullptr,1,0))==0,"foreground depth hides heat completely");
        if(!Partition)Require(Changes(Base,Render(nullptr,1,.95f))==0,"cockpit depth partition stays protected");
        auto Bars=Render(nullptr,1,1,true);int Leaks=0;
        for(int Y=0;Y<H;++Y)if(Y<H*.2f-2||Y>H*.8f+2)for(int X=0;X<W;++X)Leaks+=Bars[Y*W+X]!=Base[Y*W+X];
        Require(Leaks==0,"heat respects viewport bars");
        PC[0]=0;auto Zero=Render(nullptr);PC[0]=96;Require(Changes(Zero,Render(nullptr))<20,"heat time wrap is continuous");PC[0]=3;
        int MaxDelta=-1;for(int I=0;I<W*H;++I){int Delta=abs(int(Heat[I]&255)-int(Base[I]&255));if(Delta>MaxDelta){MaxDelta=Delta;Marker=I%W;}}
        auto MarkedBase=Render(nullptr,0),Marked=Render(nullptr);int Smear=0,Changed=0;
        auto Magenta=[](DWORD C){return int((C>>16)&255)>int((C>>8)&255)+30&&int(C&255)>int((C>>8)&255)+30;};
        for(size_t I=0;I<Marked.size();++I){if(Magenta(MarkedBase[I]))Changed+=Marked[I]!=MarkedBase[I];else Smear+=Magenta(Marked[I]);}
        Require(Changed==0&&Smear==0,"heat does not drag nearer hull colours into the exhaust");
        Marker=-1;
    }
    HeatCamera(1);PC[0]=3;PatternOn=false;
    auto Base=Render("engine_heat_base",0),Heat=Render("engine_heat_plain");int Added=0;
    for(size_t I=0;I<Base.size();++I)for(int C=0;C<3;++C)Added+=abs(int((Base[I]>>(C*8))&255)-int((Heat[I]>>(C*8))&255))>1;
    Require(Added==0,"heat adds no smoke, glow or tint to a uniform scene");
    puts("PASS all engine heat checks");return 0;
}
