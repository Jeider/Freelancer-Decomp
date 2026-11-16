// Actual SM3 shader preview. Synthetic space and a simple reference craft, no game capture.
#define NOMINMAX
#include <windows.h>
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>
#include "../../src/freelancer/Client/tradelane_visual_noise.h"
static IDirect3DDevice9* D;
static IDirect3DSurface9 *Target,*Cpu;
static IDirect3DVertexShader9* VS;
static IDirect3DPixelShader9 *Flight,*Transition,*Space;
static IDirect3DVolumeTexture9* Noise;
static IDirect3DTexture9* SceneDepth;
static int W=1280,H=720;
struct V {float x,y,z;DWORD c;float u,v;};
static V Quad[]={{-1,1,0,~0u,0,0},{1,1,0,~0u,1,0},{-1,-1,0,~0u,0,1},{1,-1,0,~0u,1,1}};
static void Check(HRESULT hr){if(FAILED(hr)){fprintf(stderr,"FAIL %08lx\n",hr);exit(1);}}
static void Require(bool v,char const* text){fprintf(stderr,"%s %s\n",v?"PASS":"FAIL",text);if(!v)exit(2);}
static void Compile(char const* entry, bool vertex=false) {
    ID3DXBuffer *code=nullptr,*error=nullptr,*assembly=nullptr;
    auto hr=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/jump_travel_prototype.hlsl",nullptr,nullptr,entry,vertex?"vs_3_0":"ps_3_0",0,&code,&error,nullptr);
    if(error){fprintf(stderr,"%s\n",(char*)error->GetBufferPointer());error->Release();}Check(hr);
    Check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&assembly));
    char path[256];sprintf(path,"out/jump_travel/%s.asm",entry);FILE* f=fopen(path,"wb");
    fwrite(assembly->GetBufferPointer(),1,assembly->GetBufferSize(),f);fclose(f);assembly->Release();
    if(vertex)Check(D->CreateVertexShader((DWORD*)code->GetBufferPointer(),&VS));
    else Check(D->CreatePixelShader((DWORD*)code->GetBufferPointer(),strcmp(entry,"PSMain")==0?&Flight:strcmp(entry,"PSTransition")==0?&Transition:&Space));
    code->Release();
}
static void Size(int width,int height) {
    if(Target)Target->Release();if(Cpu)Cpu->Release();W=width;H=height;
    Check(D->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&Target,nullptr));
    Check(D->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&Cpu,nullptr));
    Check(D->SetRenderTarget(0,Target));D3DVIEWPORT9 vp={0,0,DWORD(W),DWORD(H),0,1};Check(D->SetViewport(&vp));
}
static void Params(float t,float letterbox=1,bool protect=false) {
    float stage=t<2?0:t<8?1:2,progress=t<2?t/2:t<8?1:std::min(1.f,(t-8)/1.5f);
    float p[12]={t,float(W)/(H*letterbox),stage,progress,1.f/W,1.f/H,1,20000,0,.9f,protect?1.f:0.f,0};
    float remap[4]={1,letterbox,0,0};Check(D->SetVertexShaderConstantF(7,remap,1));Check(D->SetPixelShaderConstantF(0,p,3));
}
static void Layer(IDirect3DPixelShader9* ps,bool blend) {
    Check(D->SetVertexShader(VS));Check(D->SetPixelShader(ps));Check(D->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1));
    D->SetRenderState(D3DRS_ALPHABLENDENABLE,blend);D->SetTexture(0,Noise);D->SetTexture(1,SceneDepth);
    Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Quad,sizeof(V)));
}
static void Ship(float time) {
    // A deliberately simple stable reference silhouette, not a replacement game asset.
    struct S{float x,y,z,rhw;DWORD color;};
    auto point=[](float x,float y,DWORD c){return S{W*(.5f+x),H*(.70f+y),0,1,c};};
    std::vector<S> v;
    float pulse=.5f+.5f*sin(time*1.1f);
    auto tri=[&](float ax,float ay,float bx,float by,float cx,float cy,int red,int green,int blue){
        DWORD c=D3DCOLOR_XRGB(red,green+int(pulse*7),blue+int(pulse*12));
        v.push_back(point(ax,ay,c));v.push_back(point(bx,by,c));v.push_back(point(cx,cy,c));};
    tri(0,-.12f,-.018f,.065f,0,.09f,36,49,65);tri(0,-.12f,0,.09f,.018f,.065f,60,76,91);
    tri(-.012f,-.012f,-.105f,.09f,-.018f,.065f,31,43,58);tri(.012f,-.012f,.018f,.065f,.105f,.09f,43,57,73);
    tri(-.018f,.065f,-.105f,.09f,-.035f,.10f,17,24,37);tri(.018f,.065f,.035f,.10f,.105f,.09f,26,35,48);
    tri(-.009f,-.065f,.009f,-.065f,0,-.10f,12,25,42);
    tri(-.013f,.074f,-.006f,.103f,-.002f,.074f,100,173,222);tri(.002f,.074f,.006f,.103f,.013f,.074f,100,173,222);
    D->SetVertexShader(nullptr);D->SetPixelShader(nullptr);D->SetTexture(0,nullptr);D->SetTexture(1,nullptr);
    D->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE);D->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    D->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);D->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);
    D->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
    Check(D->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(v.size()/3),v.data(),sizeof(S)));
}
static void Render(float t,bool ship=false,float letterbox=1,bool protect=false) {
    Check(D->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0));Check(D->BeginScene());Params(t,letterbox,protect);
    if(t>=2 && t<8)Layer(Flight,false);
    else {Layer(Space,false);Layer(Transition,true);}
    if(ship)Ship(t);
    Check(D->EndScene());
}
static std::vector<DWORD> Read() {
    Check(D->GetRenderTargetData(Target,Cpu));D3DLOCKED_RECT r;Check(Cpu->LockRect(&r,nullptr,D3DLOCK_READONLY));
    std::vector<DWORD> pixels(W*H);for(int y=0;y<H;++y)memcpy(pixels.data()+y*W,(char*)r.pBits+y*r.Pitch,W*4);
    Check(Cpu->UnlockRect());return pixels;
}
static void Save(char const* name) {Read();char path[256];sprintf(path,"out/jump_travel/%s.png",name);Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,Cpu,nullptr,nullptr));}
template<class T>static void Query(IDirect3DQuery9* q,T& value) {
    HRESULT hr;ULONGLONG start=GetTickCount64();while((hr=q->GetData(&value,sizeof(value),D3DGETDATA_FLUSH))==S_FALSE){if(GetTickCount64()-start>15000)exit(3);Sleep(0);}Check(hr);
}
static void Benchmark() {
    IDirect3DQuery9 *a,*b,*freq,*dis,*visible;Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&a));Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&b));
    Check(D->CreateQuery(D3DQUERYTYPE_OCCLUSION,&visible));
    Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&freq));Check(D->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&dis));
    for(float time:{1.7f,5.f,8.5f}) {
        std::vector<double> times;Render(time);
        for(int n=0;n<7;++n){Check(dis->Issue(D3DISSUE_BEGIN));Check(freq->Issue(D3DISSUE_END));Check(a->Issue(D3DISSUE_END));Check(visible->Issue(D3DISSUE_BEGIN));
            // No per-iteration Clear: drivers can discard unobserved overwritten
            // frames, which would under-report opaque-flight cost.
            for(int i=0;i<60;++i){Check(D->BeginScene());Params(time);if(time>=2&&time<8)Layer(Flight,false);else {Layer(Space,false);Layer(Transition,true);}Check(D->EndScene());}
            Check(visible->Issue(D3DISSUE_END));Check(b->Issue(D3DISSUE_END));Check(dis->Issue(D3DISSUE_END));UINT64 x,y,hz;BOOL bad;DWORD samples;
            Query(a,x);Query(b,y);Query(freq,hz);Query(dis,bad);Query(visible,samples);
            Require(samples>=DWORD(W*H*60),"timed passes rasterize the full target");
            if(!bad&&hz)times.push_back(double(y-x)*1000/hz/60);}
        Require(!times.empty(),"valid GPU timing");std::sort(times.begin(),times.end());
        fprintf(stderr,"GPU %dx%d phase %.1fs %.4f ms\n",W,H,time,times[times.size()/2]);
    }
    a->Release();b->Release();freq->Release();dis->Release();visible->Release();
}
int main(int argc,char** argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","Jump prototype GPU",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
    D3DADAPTER_IDENTIFIER9 adapter;api->GetAdapterIdentifier(0,0,&adapter);fprintf(stderr,"GPU %s\n",adapter.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&D));
    Compile("VSMain",true);Compile("PSMain");Compile("PSTransition");Compile("PSSpace");Size(1280,720);
    std::vector<std::uint32_t> data(64*64*64);BuildTradeLaneNoise(data.data());
    Check(D->CreateVolumeTexture(64,64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&Noise,nullptr));
    D3DLOCKED_BOX box;Check(Noise->LockBox(0,&box,nullptr,0));for(int z=0;z<64;++z)for(int y=0;y<64;++y)memcpy((char*)box.pBits+z*box.SlicePitch+y*box.RowPitch,data.data()+(z*64+y)*64,256);Noise->UnlockBox(0);
    Check(D->CreateTexture(1,1,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&SceneDepth,nullptr));D3DLOCKED_RECT rect;
    Check(SceneDepth->LockRect(0,&rect,nullptr,0));*(float*)rect.pBits=0;SceneDepth->UnlockRect(0);
    D->SetRenderState(D3DRS_ZENABLE,FALSE);D->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);D->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    D->SetRenderState(D3DRS_LIGHTING,FALSE);D->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);D->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);D->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    for(int i=0;i<2;++i){D->SetSamplerState(i,D3DSAMP_MINFILTER,i?D3DTEXF_POINT:D3DTEXF_LINEAR);D->SetSamplerState(i,D3DSAMP_MAGFILTER,i?D3DTEXF_POINT:D3DTEXF_LINEAR);D->SetSamplerState(i,D3DSAMP_MIPFILTER,D3DTEXF_NONE);}
    if(argc>1&&strcmp(argv[1],"--video")==0) {
        _setmode(_fileno(stdout),_O_BINARY);
        for(int frame=0;frame<600;++frame){Render(frame/60.f,true);auto p=Read();fwrite(p.data(),4,p.size(),stdout);}
    } else {
        Render(.8f,true);Save("charge");Render(1.65f,true);Save("breach");Render(4.f,true);Save("flight");Render(8.45f,true);Save("exit");
        Render(4.f);auto a=Read();Render(4.f);Require(a==Read(),"pause is pixel-exact");
        Render(4.05f);Require(a!=Read(),"continuous clock drives motion");
        Render(0);auto space=Read();Render(10);Require(space==Read(),"entry starts and exit ends on unchanged space");
        Render(1.6f,false,1,true);Require(space==Read(),"foreground depth completely protects craft from transition");
        Render(5,false,.6f);a=Read();int leaks=0;for(int y=0;y<H;++y)if(y<H*.2f-2||y>H*.8f+2)for(int x=0;x<W;++x)leaks+=(a[y*W+x]&0xffffff)!=0;
        Require(leaks==0,"cinematic bars stay black");Size(1920,1080);Benchmark();
    }
    D->SetTexture(0,nullptr);D->SetTexture(1,nullptr);Noise->Release();SceneDepth->Release();VS->Release();Flight->Release();Transition->Release();Space->Release();Target->Release();Cpu->Release();D->Release();api->Release();DestroyWindow(window);
    return 0;
}
