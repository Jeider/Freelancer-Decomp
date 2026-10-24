// Standalone production-shader validation/preview on D3D9 HAL, not an in-game capture.
#define NOMINMAX
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include "../src/freelancer/Client/tradelane_visual_mesh.h"
#include "../src/freelancer/Client/tradelane_visual_noise.h"
#include "../src/freelancer/Client/tradelane_visual_style.h"
static const char* Out="src/obj/tradelane_check/";
static int W=1920,H=1080;
static IDirect3DDevice9* Dev;
static IDirect3DSurface9 *Target,*Cpu,*Depth;
static IDirect3DVertexShader9* VS;
static IDirect3DPixelShader9 *PS,*White,*Warp;
static IDirect3DTexture9 *SceneColor,*SceneDepth;
static IDirect3DVertexBuffer9* VB;
static bool WarpEnabled=true,GlowEnabled=true,WallOnly=false,Beauty=false;
static float Letterbox=1,Clock=3;
static IDirect3DTexture9* Background;
static IDirect3DVolumeTexture9* Noise;
using Vertex = FTradeLaneVertex;
static std::vector<Vertex> Mesh;
static FTradeLaneVisualStyle Style;
static void Check(HRESULT hr) {if(FAILED(hr)) {printf("FAIL HRESULT %08lx\n",hr);exit(2);}}
static void Require(bool ok,const char* s) {printf("%s: %s\n",ok?"PASS":"FAIL",s);if(!ok) exit(3);}
template<class T> static void Release(T*& p) {if(p) {p->Release();p=nullptr;}}
static void Compile() {
    for(int stage=0;stage<3;++stage) {
        ID3DXBuffer *code=nullptr,*error=nullptr,*dis=nullptr;
        HRESULT hr=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/tradelane_corridor.hlsl",nullptr,nullptr,
            stage==2?"PSWarp":stage?"PSMain":"VSMain",stage?"ps_3_0":"vs_3_0",0,&code,&error,nullptr);
        if(error) {puts((char*)error->GetBufferPointer());Release(error);}Check(hr);
        Check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&dis));
        std::string path=std::string(Out)+(stage==2?"warp.asm":stage?"ps.asm":"vs.asm");FILE* f=fopen(path.c_str(),"wb");
        fwrite(dis->GetBufferPointer(),1,strlen((char*)dis->GetBufferPointer()),f);fclose(f);Release(dis);
        if(stage==2) Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&Warp));
        else if(stage) Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&PS));
        else Check(Dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&VS));
        Release(code);
    }
    const char* text="float4 main():COLOR0{return float4(1,1,1,1);}";
    ID3DXBuffer* code=nullptr;Check(D3DXCompileShader(text,UINT(strlen(text)),nullptr,nullptr,"main","ps_3_0",0,&code,nullptr,nullptr));
    Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&White));Release(code);
}
static void CreateNoise() {
    unsigned const N=TradeLaneNoiseSize;
    std::vector<std::uint32_t> data(N*N*N);BuildTradeLaneNoise(data.data());
    Check(Dev->CreateVolumeTexture(N,N,N,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&Noise,nullptr));
    D3DLOCKED_BOX box;Check(Noise->LockBox(0,&box,nullptr,0));
    for(unsigned z=0;z<N;++z)for(unsigned y=0;y<N;++y)
        memcpy((char*)box.pBits+z*box.SlicePitch+y*box.RowPitch,data.data()+(z*N+y)*N,N*4);
    Check(Noise->UnlockBox(0));
}
static void Size(int width,int height) {
    Release(Target);Release(Cpu);Release(Depth);Release(Background);Release(SceneColor);Release(SceneDepth);W=width;H=height;
    Check(Dev->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&Target,nullptr));
    Check(Dev->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&Cpu,nullptr));
    Check(Dev->CreateDepthStencilSurface(W,H,D3DFMT_D24S8,D3DMULTISAMPLE_NONE,0,TRUE,&Depth,nullptr));
    Check(Dev->SetRenderTarget(0,Target));Check(Dev->SetDepthStencilSurface(Depth));
    D3DVIEWPORT9 vp={0,0,DWORD(W),DWORD(H),0,1};Check(Dev->SetViewport(&vp));
    Check(Dev->CreateTexture(W,H,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&Background,nullptr));
    Check(Dev->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&SceneColor,nullptr));
    Check(Dev->CreateTexture(W,H,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&SceneDepth,nullptr));
    D3DLOCKED_RECT r;Check(Background->LockRect(0,&r,nullptr,0));unsigned seed=8121;
    for(int y=0;y<H;++y) for(int x=0;x<W;++x) {
        seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;
        float u=float(x)/W,v=float(y)/H;
        float glow=expf(-powf((v-.25f-u*.35f)*5.f,2));
        int star=(seed%1800==0)?(48+int((seed>>17)%160)):0;
        int red=5+int(10*glow)+star,green=7+int(12*glow)+star,blue=14+int(22*glow)+star;
        float px=(u-.72f)*float(W)/H,py=v-.43f;
        if(!Beauty&&px*px+py*py<.16f*.16f) {float light=.35f+.65f*sqrtf(std::max(0.f,1-(px*px+py*py)/(.16f*.16f)));red=int(110*light);green=int(145*light);blue=int(185*light);}
        if(!Beauty&&u<.24f&&v>.26f&&v<.74f) {int grid=((x/16)^(y/16))&1;red=grid?70:14;green=grid?85:20;blue=grid?105:28;}
        ((DWORD*)((char*)r.pBits+y*r.Pitch))[x]=D3DCOLOR_XRGB(red,green,blue);
    }Check(Background->UnlockRect(0));
}
static void Camera(float yaw=0,float pitch=0,float roll=0,float letterbox=1,float origin=0) {
    Letterbox=letterbox;
    D3DXMATRIX view,projection,rotation;
    D3DXMatrixRotationYawPitchRoll(&rotation,yaw,pitch,roll);view=rotation;
    view._41=-origin*(view._11+view._21+view._31);
    view._42=-origin*(view._12+view._22+view._32);
    view._43=-origin*(view._13+view._23+view._33);
    D3DXMatrixPerspectiveFovLH(&projection,1.04719755f,float(W)/(H*letterbox),1,20000);
    float c[44]={};for(int row=0;row<3;++row) for(int col=0;col<4;++col)c[row*4+col]=view.m[col][row];
    for(int row=0;row<4;++row) for(int col=0;col<4;++col)c[12+row*4+col]=projection.m[col][row];
    c[28]=1;c[29]=letterbox;c[32]=c[37]=c[42]=1;c[35]=c[39]=c[43]=origin;
    Check(Dev->SetVertexShaderConstantF(0,c,11));
}
static void Params(float phase=0,float envelope=1,float pulse=0,float clock=3,float age=2,float exitProgress=0,bool stopping=false) {
    Clock=clock;float c[32]={phase,clock,envelope,pulse,.10f,.38f,.65f,0,
        1.f/W,1.f/H,.055f,0,.5f/W,(1-Letterbox)*.5f+.5f/H,1-.5f/W,(1+Letterbox)*.5f-.5f/H,
        1,20000,0,.9f,age,exitProgress,stopping?1.f:0.f,1};
    for(int i=0;i<3;++i) {c[4+i]=Style.Body[i];c[24+i]=Style.Accent[i];}
    c[7]=Style.Enabled;c[27]=Style.Mode;for(int i=0;i<4;++i)c[28+i]=Style.Seed[i];
    Check(Dev->SetPixelShaderConstantF(0,c,8));Check(Dev->SetVertexShaderConstantF(11,c,1));
    Check(Dev->SetVertexShaderConstantF(12,c+16,1));
}
static void Geometry(unsigned count) {
    Check(Dev->SetVertexShader(VS));Check(Dev->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1));
    Check(Dev->SetStreamSource(0,VB,0,sizeof(Vertex)));Check(Dev->DrawPrimitive(D3DPT_TRIANGLELIST,0,count/3));
}
static void CopyScene() {
    Dev->SetTexture(0,nullptr);Dev->SetTexture(1,nullptr);
    IDirect3DSurface9* snapshot=nullptr;Check(SceneColor->GetSurfaceLevel(0,&snapshot));
    Check(Dev->StretchRect(Target,nullptr,snapshot,nullptr,D3DTEXF_NONE));Release(snapshot);
}
static void Draw() {
    Check(Dev->SetTexture(2,Noise));
    Dev->SetSamplerState(2,D3DSAMP_ADDRESSU,D3DTADDRESS_WRAP);
    Dev->SetSamplerState(2,D3DSAMP_ADDRESSV,D3DTADDRESS_WRAP);
    Dev->SetSamplerState(2,D3DSAMP_ADDRESSW,D3DTADDRESS_WRAP);
    Dev->SetSamplerState(2,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);
    Dev->SetSamplerState(2,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
    Dev->SetSamplerState(2,D3DSAMP_MIPFILTER,D3DTEXF_NONE);
    if(WarpEnabled&&!WallOnly) {
        Check(Dev->SetPixelShader(Warp));Dev->SetTexture(0,SceneColor);Dev->SetTexture(1,SceneDepth);
        for(int sampler=0;sampler<2;++sampler) {
            Dev->SetSamplerState(sampler,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Dev->SetSamplerState(sampler,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
            Dev->SetSamplerState(sampler,D3DSAMP_MINFILTER,sampler?D3DTEXF_POINT:D3DTEXF_LINEAR);
            Dev->SetSamplerState(sampler,D3DSAMP_MAGFILTER,sampler?D3DTEXF_POINT:D3DTEXF_LINEAR);
            Dev->SetSamplerState(sampler,D3DSAMP_MIPFILTER,D3DTEXF_NONE);
        }
        Dev->SetRenderState(D3DRS_ZENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
        Geometry(TradeLaneCorridorVertexCount);Dev->SetTexture(0,nullptr);Dev->SetTexture(1,nullptr);
    }
    Dev->SetRenderState(D3DRS_ZENABLE,TRUE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    if(GlowEnabled) {Check(Dev->SetPixelShader(PS));Geometry(WallOnly?TradeLaneCorridorVertexCount:TradeLaneVertexCount);}
}
static void DepthTexture(bool blocker,bool cockpit) {
    D3DLOCKED_RECT r;Check(SceneDepth->LockRect(0,&r,nullptr,0));
    for(int y=0;y<H;++y)for(int x=0;x<W;++x) {
        float d=1.f;
        if(blocker&&x>=W/4&&x<W*3/4&&y>=H/4&&y<H*3/4)d=0;
        if(cockpit&&y>H*3/4)d=.95f;
        ((float*)((char*)r.pBits+y*r.Pitch))[x]=d;
    }Check(SceneDepth->UnlockRect(0));
}
static void Backdrop() {
    struct Screen {float x,y,z,rhw,u,v;};
    Screen q[]={{-.5f,-.5f,.999f,1,0,0},{W-.5f,-.5f,.999f,1,1,0},
        {-.5f,H-.5f,.999f,1,0,1},{W-.5f,H-.5f,.999f,1,1,1}};
    Dev->SetVertexShader(nullptr);Dev->SetPixelShader(nullptr);Dev->SetFVF(D3DFVF_XYZRHW|D3DFVF_TEX1);
    Dev->SetRenderState(D3DRS_ZENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    Dev->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);Dev->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);
    Dev->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_DISABLE);Dev->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
    Dev->SetTexture(0,Background);Check(Dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Screen)));
    Dev->SetTexture(0,nullptr);Dev->SetRenderState(D3DRS_ZENABLE,TRUE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
}
static void CheckX8Snapshot() {
    IDirect3DSurface9 *source=nullptr,*sourceCpu=nullptr,*snapshot=nullptr;
    Check(Dev->CreateRenderTarget(W,H,D3DFMT_X8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&source,nullptr));
    Check(Dev->CreateOffscreenPlainSurface(W,H,D3DFMT_X8R8G8B8,D3DPOOL_SYSTEMMEM,&sourceCpu,nullptr));
    Check(Dev->SetRenderTarget(0,source));Check(Dev->BeginScene());Backdrop();Check(Dev->EndScene());
    Check(SceneColor->GetSurfaceLevel(0,&snapshot));
    Check(Dev->StretchRect(source,nullptr,snapshot,nullptr,D3DTEXF_NONE));
    Check(Dev->GetRenderTargetData(source,sourceCpu));Check(Dev->GetRenderTargetData(snapshot,Cpu));
    D3DLOCKED_RECT a,b;Check(sourceCpu->LockRect(&a,nullptr,D3DLOCK_READONLY));Check(Cpu->LockRect(&b,nullptr,D3DLOCK_READONLY));
    int differences=0;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x)
        differences+=((((DWORD*)((char*)a.pBits+y*a.Pitch))[x]^((DWORD*)((char*)b.pBits+y*b.Pitch))[x])&0xffffff)!=0;
    Check(sourceCpu->UnlockRect());Check(Cpu->UnlockRect());Check(Dev->SetRenderTarget(0,Target));
    Require(differences==0,"X8R8G8B8 render-target copy to A8R8G8B8 preserves all RGB pixels");
    Release(source);Release(sourceCpu);Release(snapshot);
}
static std::vector<DWORD> Render(const char* name=nullptr,bool background=false,bool blocker=false,bool cockpit=false,float clearDepth=1) {
    DepthTexture(blocker,cockpit);
    Check(Dev->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,clearDepth,0));Check(Dev->BeginScene());
    if(background) Backdrop();
    if(blocker) {
        D3DRECT area={W/4,H/4,W*3/4,H*3/4};Check(Dev->Clear(1,&area,D3DCLEAR_ZBUFFER|(background?D3DCLEAR_TARGET:0),0xffff00ff,0,0));
    }
    if(cockpit&&background) {D3DRECT area={0,H*3/4+1,W,H};Check(Dev->Clear(1,&area,D3DCLEAR_TARGET,0xff00ff00,1,0));}
    Check(Dev->EndScene());CopyScene();Check(Dev->BeginScene());
    Draw();Check(Dev->EndScene());Check(Dev->GetRenderTargetData(Target,Cpu));
    if(name) {std::string file=std::string(Out)+name+".png";Check(D3DXSaveSurfaceToFileA(file.c_str(),D3DXIFF_PNG,Cpu,nullptr,nullptr));}
    D3DLOCKED_RECT r;Check(Cpu->LockRect(&r,nullptr,D3DLOCK_READONLY));std::vector<DWORD> a(W*H);
    for(int y=0;y<H;++y)memcpy(a.data()+y*W,(char*)r.pBits+y*r.Pitch,W*4);Check(Cpu->UnlockRect());return a;
}
static int Changes(const std::vector<DWORD>& a,const std::vector<DWORD>& b,int tolerance=0) {
    int count=0;for(size_t i=0;i<a.size();++i) {int peak=0;for(int k=0;k<3;++k)
        peak=std::max(peak,abs(int((a[i]>>(k*8))&255)-int((b[i]>>(k*8))&255)));count+=peak>tolerance;}return count;
}
template<class T> static void Query(IDirect3DQuery9* q,T& value) {
    HRESULT hr;ULONGLONG start=GetTickCount64();while((hr=q->GetData(&value,sizeof(value),D3DGETDATA_FLUSH))==S_FALSE) {
        if(GetTickCount64()-start>15000) {puts("GPU query timeout");exit(2);}Sleep(0);
    }Check(hr);
}
static double Benchmark() {
    IDirect3DQuery9 *a=nullptr,*b=nullptr,*f=nullptr,*d=nullptr;Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&a));
    Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&b));Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&f));
    Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&d));std::vector<double> times;Render();
    for(int n=0;n<7;++n) {
        Check(d->Issue(D3DISSUE_BEGIN));Check(f->Issue(D3DISSUE_END));Check(a->Issue(D3DISSUE_END));
        for(int j=0;j<40;++j) {CopyScene();Check(Dev->BeginScene());Draw();Check(Dev->EndScene());}
        Check(b->Issue(D3DISSUE_END));Check(d->Issue(D3DISSUE_END));
        UINT64 t0,t1,freq;BOOL disjoint;Query(a,t0);Query(b,t1);Query(f,freq);Query(d,disjoint);
        if(!disjoint&&freq)times.push_back(double(t1-t0)*1e6/double(freq)/40);
    }
    Require(!times.empty(),"valid GPU timestamps");std::sort(times.begin(),times.end());
    printf("%dx%d: %.3f us per scene copy + warp + glow (%u glow triangles + %u warp, static VB, isolated GPU; not total frame)\n",W,H,times[times.size()/2],TradeLaneVertexCount/3,TradeLaneCorridorVertexCount/3);
    Release(a);Release(b);Release(f);Release(d);return times[times.size()/2];
}
static FTradeLaneVisualStyle ConfigStyle(unsigned mode) {
    // Actual active FL_MOD gate_tunnel.ini Layer0, Layer1, min_rgb, max_rgb (RGB8).
    const float colors[5][4][3]={
        {{100,150,100},{100,255,100},{0,30,0},{0,100,0}},
        {{200,200,200},{100,150,255},{0,0,30},{0,0,100}},
        {{100,100,150},{200,200,220},{30,30,30},{100,100,100}},
        {{150,80,0},{255,150,0},{30,20,0},{100,80,0}},
        {{35,35,35},{75,75,75},{30,30,30},{50,50,50}}};
    float normalized[4][3];for(int j=0;j<4;++j)for(int k=0;k<3;++k)normalized[j][k]=colors[mode-1][j][k]/255.f;
    FTradeLaneVisualStyle result;Require(TradeLaneBuildPalette(result,normalized[0],normalized[1],normalized[2],normalized[3],mode),"actual gate palette is valid");
    TradeLaneSeedStyle(result,0x12340000+mode,0x2387);return result;
}
static void CheckStyles() {
    Size(960,540);double worstTime=0;unsigned worstMode=1;
    const char* names[]={"neutral","edge","crow","barrier","walker","dark"};
    for(unsigned mode=1;mode<=5;++mode) {
        Style=ConfigStyle(mode);printf("STYLE %s\n",names[mode]);Camera();Params(.3125f);
        char name[80];sprintf(name,"style_%s",names[mode]);auto base=Render(name,true);auto pause=Render(nullptr,true);
        Require(Changes(base,pause)==0,"style pause remains pixel-exact");
        Params(.3125f,1,0,99);auto clock=Render(nullptr,true);
        Require(Changes(base,clock,2)<W*H/200,"style clock repeats after 96 seconds");
        Params(.3125f,1,0,95.99f);auto edge=Render(nullptr,true);
        Params(.3125f,1,0,191.99f);auto edgeWrap=Render(nullptr,true);
        Require(Changes(edge,edgeWrap,2)<W*H/200,"style surge near clock boundary repeats continuously");
        Params(1024.3125f);auto phase=Render(nullptr,true);
        Require(Changes(base,phase,2)<W*H/200,"style phase repeats after 1024 cycles");
        Params(.3125f);auto depth=Render(nullptr,false,true);int leaks=0;
        for(int y=H/4;y<H*3/4;++y)for(int x=W/4;x<W*3/4;++x)leaks+=(depth[y*W+x]&0xffffff)!=0;
        Require(leaks==0,"style respects foreground depth");
        GlowEnabled=false;WarpEnabled=false;auto protectedBase=Render(nullptr,true,true,true);
        WarpEnabled=true;auto protectedWarp=Render(nullptr,true,true,true);leaks=0;
        for(int y=0;y<H;++y)for(int x=0;x<W;++x)
            if((x>=W/4&&x<W*3/4&&y>=H/4&&y<H*3/4)||y>H*3/4)
                leaks+=protectedBase[y*W+x]!=protectedWarp[y*W+x];
        Require(leaks==0,"style warp preserves near geometry and cockpit exactly");GlowEnabled=true;
        Camera(.4f,.1f,0,.6f);Params(.3125f);auto bars=Render(nullptr,true);
        Params(.3125f,0);auto empty=Render(nullptr,true);leaks=0;
        for(int y=0;y<H;++y)if(y<int(H*.2f)-2||y>int(H*.8f)+2)for(int x=0;x<W;++x)leaks+=bars[y*W+x]!=empty[y*W+x];
        Require(leaks==0,"style stays within cinematic viewport");
        Camera();Params(.3125f);double us=Benchmark();if(us>worstTime){worstTime=us;worstMode=mode;}
    }
    printf("Worst style at 960x540: %s; full-resolution measurements follow\n",names[worstMode]);
    Style=ConfigStyle(worstMode);Size(1920,1080);Camera();Params(.3125f);Benchmark();
    Size(3840,2160);Camera();Params(.3125f);Benchmark();Style=FTradeLaneVisualStyle();
}
int main(int argc,char** argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);CreateDirectoryA("src/obj/tradelane_check",nullptr);
    HWND hwnd=CreateWindowA("STATIC","tradelane check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 1;
    D3DADAPTER_IDENTIFIER9 adapter;Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s\n",adapter.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,hwnd,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&Dev));
    Compile();CreateNoise();Size(1920,1080);
    Mesh.resize(TradeLaneVertexCount);BuildTradeLaneVisualMesh(Mesh.data());
    Check(Dev->CreateVertexBuffer(UINT(Mesh.size()*sizeof(Vertex)),D3DUSAGE_WRITEONLY,0,D3DPOOL_MANAGED,&VB,nullptr));
    void* vertices=nullptr;Check(VB->Lock(0,0,&vertices,0));memcpy(vertices,Mesh.data(),Mesh.size()*sizeof(Vertex));Check(VB->Unlock());
    Dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);Dev->SetRenderState(D3DRS_ZENABLE,TRUE);
    Dev->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);Dev->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
    Dev->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    Dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);Dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    Dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);Dev->SetRenderState(D3DRS_LIGHTING,FALSE);
    if(argc>1&&strcmp(argv[1],"--video")==0) {
        CreateDirectoryA("src/obj/tradelane_check/video",nullptr);Beauty=true;Size(960,540);Camera();
        Params(.3125f,1,0,3,2);Render("beauty_preview",true);
        for(int frame=0;frame<120;++frame) {
            float time=frame/30.f;char name[80];sprintf(name,"video/frame_%04d",frame);
            float exitProgress=std::max(0.f,(time-3.35f)/.65f);
            auto Smooth=[](float value) {value=std::max(0.f,std::min(1.f,value));return value*value*(3-2*value);};
            float intensity=Smooth(time/.30f)*(1-Smooth(exitProgress));
            Params(time*.7f,intensity,0,time,std::min(time,2.f),exitProgress,exitProgress>0);Render(name,true);
        }
        puts("PASS 120 video source frames, 960x540, 30 fps, 4 seconds");
        goto cleanup;
    }
    {
    CheckX8Snapshot();
    Camera();Params(.3125f);auto initial=Render("forward",true);auto lit=Render();
    for(int pose=0;pose<5;++pose) {
        Camera(0,0,pose*3.14159265f/48.f);auto saved=PS;PS=White;WallOnly=true;auto mask=Render(pose==0?"coverage":nullptr);PS=saved;WallOnly=false;
        int holes=0;for(int y=0;y<H;++y)for(int x=0;x<W;++x)
            if((x-W/2)*(x-W/2)+(y-H/2)*(y-H/2)>30*30)holes+=!(mask[y*W+x]&0xffffff);
        printf("Geometry pose %d cracks: %d pixels\n",pose,holes);Require(holes==0,"cylinder has no cracks outside its open end");}
    Camera();
    Params(.6f);auto next=Render("moving",true);Require(Changes(initial,next)>W*H/10,"flow responds to travelled distance");
    Params(.3125f,0);auto off=Render();Require(std::all_of(off.begin(),off.end(),[](DWORD p){return !(p&0xffffff);}),"zero envelope is fully invisible");
    Params(.3125f);auto same=Render();Require(Changes(lit,same)==0,"paused phase is stable");
    Params(1024.3125f);auto wrap=Render();printf("wrap: %d pixels differ by >2/255\n",Changes(lit,wrap,2));
    Require(Changes(lit,wrap,2)<W*H/200,"phase wrap is visually continuous");
    Params(.3125f);Camera(.65f,.1f,.05f);auto rotated=Render("turned",true);
    Require(Changes(initial,rotated)>W*H/5,"camera turning changes corridor perspective");
    Camera(3.14159265f);Render("rear",true);
    Camera();Params(.3125f,1,1);Render("entry",true);
    Params(.3125f);auto blocked=Render(nullptr,false,true);int leaks=0,hidden=0;
    for(int y=H/4;y<H*3/4;++y)for(int x=W/4;x<W*3/4;++x){leaks+=(blocked[y*W+x]&0xffffff)!=0;hidden+=(lit[y*W+x]&0xffffff)!=0;}
    Require(leaks==0&&hidden>1000,"foreground depth occludes corridor");
    WarpEnabled=false;Params(.3125f);float missingWarp[4]={0,0,0,0};
    Check(Dev->SetPixelShaderConstantF(2,missingWarp,1));auto missingDepth=Render();
    int fallbackLit=0;for(DWORD pixel:missingDepth)fallbackLit+=(pixel&0xffffff)!=0;
    Require(fallbackLit>1000,"missing scene-depth dimensions retain visible glow fallback");
    Params(.3125f);WarpEnabled=true;
    WarpEnabled=false;auto fullDepth=Render();auto partitionDepth=Render(nullptr,false,false,false,.95f);
    Require(Changes(fullDepth,partitionDepth)==0&&hidden>1000,"world max .9 glow remains visible against depth .95");
    auto partitionNear=Render(nullptr,false,true,false,.95f);int partitionLeaks=0;
    for(int y=H/4;y<H*3/4;++y)for(int x=W/4;x<W*3/4;++x)partitionLeaks+=(partitionNear[y*W+x]&0xffffff)!=0;
    Require(partitionLeaks==0,"world-depth remap retains near-depth zero occlusion");WarpEnabled=true;
    Camera(.4f,.1f,0,.6f);Params(.3125f);auto bars=Render("letterbox",true);Params(.3125f,0);auto empty=Render(nullptr,true);
    leaks=0;for(int y=0;y<H;++y)if(y<int(H*.2f)-2||y>int(H*.8f)+2)for(int x=0;x<W;++x)leaks+=bars[y*W+x]!=empty[y*W+x];
    Require(leaks==0,"effect stays inside cinematic viewport");
    Camera();Params(.3125f);GlowEnabled=false;WarpEnabled=false;
    auto unwarped=Render("warp_off",true);WarpEnabled=true;auto warped=Render("warp_on",true);
    int warpChanges=Changes(unwarped,warped,2);printf("Warp changed pixels: %d\n",warpChanges);
    Require(warpChanges>W*H/1000,"scene refraction visibly changes copied background");
    Params(.3125f,0);auto warpZero=Render(nullptr,true);
    Require(Changes(unwarped,warpZero)==0,"zero warp envelope is pixel-exact identity");
    Params(.3125f);WarpEnabled=false;auto protectedBase=Render(nullptr,true,true,true);
    WarpEnabled=true;auto protectedWarp=Render("warp_protected",true,true,true);int protectedLeaks=0,rimLeaks=0;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x) {
        bool nearObject=x>=W/4&&x<W*3/4&&y>=H/4&&y<H*3/4;
        bool cockpit=y>H*3/4;
        if(nearObject||cockpit)protectedLeaks+=protectedBase[y*W+x]!=protectedWarp[y*W+x];
        if(!nearObject&&!cockpit) {DWORD rgb=protectedWarp[y*W+x];
            int r=(rgb>>16)&255,g=(rgb>>8)&255,b=rgb&255;
            rimLeaks+=(r>190&&b>190&&g<40)||(g>190&&r<40&&b<40);
        }
    }
    Require(protectedLeaks==0,"near geometry and cockpit are pixel-exact through warp");
    Require(rimLeaks==0,"protected colors are not pulled across silhouettes by bilinear sampling");
    Params(.3125f);auto clockBase=Render(nullptr,true);auto clockPause=Render(nullptr,true);
    Require(Changes(clockBase,clockPause)==0,"paused warp clock is stable");
    Params(.3125f,1,0,99);auto clockWrap=Render(nullptr,true);
    Require(Changes(clockBase,clockWrap,2)<W*H/200,"warp clock 96-second wrap is continuous");
    Params(.3125f,1,0,3.2f);auto clockNext=Render(nullptr,true);
    Require(Changes(clockBase,clockNext,2)>100,"refraction responds to time");
    GlowEnabled=true;Params(.3125f);auto combined=Render("sheath_forward",true);
    Params(.3125f,1,0,99);auto sheathWrap=Render(nullptr,true);
    Require(Changes(combined,sheathWrap,2)<W*H/200,"sheath and glow clock wrap is continuous");
    Params(.3125f,1,0,3.2f);auto sheathNext=Render("sheath_moving",true);
    Require(Changes(combined,sheathNext,2)>1000,"sheath animates without CPU mesh updates");
    Camera(.65f,.1f,.05f);Params(.3125f);Render("sheath_turned",true);
    Camera(.4f,.1f,0,.6f);Params(.3125f);auto warpedBars=Render(nullptr,true);
    WarpEnabled=false;GlowEnabled=false;auto cleanBars=Render(nullptr,true);int barLeaks=0;
    for(int y=0;y<H;++y)if(y<int(H*.2f)-2||y>int(H*.8f)+2)
        for(int x=0;x<W;++x)barLeaks+=warpedBars[y*W+x]!=cleanBars[y*W+x];
    Require(barLeaks==0,"refraction and glow preserve cinematic bars exactly");
    WarpEnabled=GlowEnabled=true;
    Camera();
    const float previewPhases[]={0,.5f,1,2};
    const float previewTimes[]={3,6,9};
    for(float phase:previewPhases)for(float time:previewTimes) {
        char name[80];sprintf(name,"sheath_phase_%g_time_%g",double(phase),double(time));
        Params(phase,1,0,time);Render(name,true);
    }
    Camera();
    for(float age:{.20f,.45f,.75f}) {
        char name[80];sprintf(name,"entry_age_%.2f",double(age));Params(.3125f,1,0,3,age);Render(name,true);
    }
    for(float progress:{.25f,.6f}) {
        char name[80];sprintf(name,"exit_progress_%.2f",double(progress));
        Params(.3125f,1-progress,0,3,2,progress,true);Render(name,true);
    }
    Camera();Params(.3125f);Benchmark();Size(2560,1440);Camera();Params(.3125f);Benchmark();Size(3840,2160);Camera();Params(.3125f);Benchmark();
    CheckStyles();
    puts("PASS tradelane GPU checks; previews in src/obj/tradelane_check (synthetic background)");
    }
cleanup:
    Release(Noise);Release(VB);Release(SceneColor);Release(SceneDepth);Release(Warp);Release(Background);Release(White);Release(VS);Release(PS);Release(Target);Release(Cpu);Release(Depth);Release(Dev);Release(api);DestroyWindow(hwnd);
}

