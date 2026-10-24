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
#include <limits>
#include "../src/freelancer/Client/jumphole_visual_state.h"
#include "../src/freelancer/Client/jumphole_visual_geometry.h"
#include "../src/freelancer/Client/tradelane_visual_noise.h"

static const char* Out="src/obj/jumphole_check/";
static int W=1920,H=1080;
static IDirect3DDevice9* Dev;
static IDirect3DSurface9 *Target,*Cpu,*Depth;
static IDirect3DVertexShader9 *VS,*IngressVS;
static IDirect3DPixelShader9 *PS,*White,*Warp,*IngressPS;
static bool Ingress=false;
static int OpticsMode=0;static bool MockShip=false,CombinedOptics=false,MockOccluders=true;
static IDirect3DVertexShader9* OpticsVS[2]={};static IDirect3DPixelShader9* OpticsPS[2]={};
static float OC[48]={},OpticsBasis[12]={1,0,0,0,0,1,0,0,0,0,1,0};
static IDirect3DTexture9 *SceneColor,*SceneDepth;
static IDirect3DVertexBuffer9* VB;
static bool WarpEnabled=true,GlowEnabled=true,WallOnly=false,Beauty=false;
static float Letterbox=1,Clock=3,BlockerDepth=0;
static IDirect3DTexture9* Background;
static IDirect3DVolumeTexture9* Noise;
using Vertex = FJumpHoleVertex;
static std::vector<Vertex> Mesh;
static float Eye[3]={0,0,-1400};
static bool ActualWorld=false;
static void Check(HRESULT hr) {if(FAILED(hr)) {printf("FAIL HRESULT %08lx\n",hr);exit(2);}}
static void Require(bool ok,const char* s) {printf("%s: %s\n",ok?"PASS":"FAIL",s);if(!ok) exit(3);}
template<class T> static void Release(T*& p) {if(p) {p->Release();p=nullptr;}}
static void Compile() {
    for(int stage=0;stage<5;++stage) {
        ID3DXBuffer *code=nullptr,*error=nullptr,*dis=nullptr;
        HRESULT hr=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/jumphole_lens.hlsl",nullptr,nullptr,
            stage==4?"PSIngress":stage==3?"VSIngress":stage==2?"PSLens":stage?"PSGlow":"VSMain",(stage==0||stage==3)?"vs_3_0":"ps_3_0",0,&code,&error,nullptr);
        if(error) {puts((char*)error->GetBufferPointer());Release(error);}Check(hr);
        Check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&dis));
        std::string path=std::string(Out)+(stage==4?"ingress_ps.asm":stage==3?"ingress_vs.asm":stage==2?"warp.asm":stage?"ps.asm":"vs.asm");FILE* f=fopen(path.c_str(),"wb");
        fwrite(dis->GetBufferPointer(),1,strlen((char*)dis->GetBufferPointer()),f);fclose(f);Release(dis);
        if(stage==4) Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&IngressPS));
        else if(stage==3) Check(Dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&IngressVS));
        else if(stage==2) Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&Warp));
        else if(stage) Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&PS));
        else Check(Dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&VS));
        Release(code);
    }
    const char* text="float4 main():COLOR0{return float4(1,1,1,1);}";
    ID3DXBuffer* code=nullptr;Check(D3DXCompileShader(text,UINT(strlen(text)),nullptr,nullptr,"main","ps_3_0",0,&code,nullptr,nullptr));
    Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&White));Release(code);
}
static void CompileOptics() {
    const char* names[]={"VSOpticsWorld","PSOpticsWorld","VSOpticsScreen","PSOpticsShip"};
    for(int i=0;i<4;++i){ID3DXBuffer *code=nullptr,*error=nullptr,*dis=nullptr;HRESULT hr=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/jumphole_optics.hlsl",nullptr,nullptr,names[i],(i&1)?"ps_3_0":"vs_3_0",0,&code,&error,nullptr);if(error){puts((char*)error->GetBufferPointer());Release(error);}Check(hr);Check(D3DXDisassembleShader((DWORD*)code->GetBufferPointer(),FALSE,nullptr,&dis));std::string path=std::string(Out)+names[i]+".asm";FILE*f=fopen(path.c_str(),"wb");fwrite(dis->GetBufferPointer(),1,dis->GetBufferSize(),f);fclose(f);Release(dis);if(i&1)Check(Dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&OpticsPS[i/2]));else Check(Dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&OpticsVS[i/2]));Release(code);}
}
static bool ShipPixel(int x,int y) {
    float u=float(x)/W-.5f,v=float(y)/H-.52f;
    return (fabsf(u)<.018f&&fabsf(v)<.105f)||(fabsf(v)<.027f&&fabsf(u)<.105f)||(v>.02f&&v<.075f&&fabsf(u)<.065f);
}
static float ZForDistance(float distance){return .9f*(20000.f/19999.f-20000.f/(19999.f*distance));}
static void OpticsParams(float authorized=0,float clock=3,float gain=1) {
    float c[48]={clock,1,0,authorized,1.f/W,1.f/H,.018f,gain,.5f/W,(1-Letterbox)*.5f+.5f/H,1-.5f/W,(1+Letterbox)*.5f-.5f/H,1,20000,0,.9f,Eye[0],Eye[1],Eye[2],145,tanf(.523598775f)*float(W)/(H*Letterbox),tanf(.523598775f),600,.9f,1,0,0,0,0,1,0,0,0,0,1,0,.5f,.52f,.15f,.16f,90,20,authorized,.5f,1,1,1,0};memcpy(OC,c,sizeof(c));memcpy(OC+24,OpticsBasis,sizeof(OpticsBasis));
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
static void Camera(float yaw=0,float pitch=0,float distance=1400,float letterbox=1) {
    Letterbox=letterbox;Eye[0]=distance*sinf(yaw)*cosf(pitch);Eye[1]=distance*sinf(pitch);Eye[2]=-distance*cosf(yaw)*cosf(pitch);
    D3DXVECTOR3 eye(Eye[0],Eye[1],Eye[2]),at(0,0,0),up(0,1,0);
    if(ActualWorld){at=D3DXVECTOR3(-12000,0,-62000);eye=D3DXVECTOR3(at.x-Eye[0],at.y+Eye[1],at.z-Eye[2]);}
    D3DXMATRIX view,projection;D3DXMatrixLookAtLH(&view,&eye,&at,&up);
    for(int r=0;r<3;++r)for(int col=0;col<3;++col)OpticsBasis[r*4+col]=view.m[r][col]*(ActualWorld&&r!=1?-1.f:1.f);
    D3DXMatrixPerspectiveFovLH(&projection,1.04719755f,float(W)/(H*letterbox),1,20000);
    float c[48]={};for(int row=0;row<3;++row)for(int col=0;col<4;++col)c[row*4+col]=view.m[col][row]*(row==2?-1.f:1.f);
    for(int row=0;row<4;++row)for(int col=0;col<4;++col)c[12+row*4+col]=projection.m[col][row];
    c[28]=1;c[29]=letterbox;c[32]=c[37]=c[42]=1;c[44]=1;c[45]=20000;c[47]=.9f;
    if(ActualWorld) {
        c[32]=c[42]=-1;c[35]=at.x;c[39]=at.y;c[43]=at.z;
        float actualView[12],world[3]={at.x,at.y,at.z},centre[3];
        for(int r=0;r<3;++r){for(int k=0;k<3;++k)actualView[r*3+k]=c[r*4+k];actualView[9+r]=c[r*4+3];}
        JumpHoleWorldToView(actualView,world,centre);
        Require(fabsf(centre[0])<.03f&&fabsf(centre[1])<.03f&&fabsf(centre[2]+distance)<.03f,
            "production world-to-view helper places real rh_biz hole at expected camera-space distance");
        Require(-centre[2]-910<20000&&910-centre[2]>1,"real rh_biz hole intersects camera near/far range");
    }
    float helperView[12],rotation[9]={ActualWorld?-1.f:1.f,0,0,0,1,0,0,0,ActualWorld?-1.f:1.f},helperBasis[12];
    for(int r=0;r<3;++r){for(int k=0;k<3;++k)helperView[r*3+k]=c[r*4+k];helperView[9+r]=c[r*4+3];}
    JumpHoleCameraToLocal(helperView,rotation,helperBasis);
    bool equivalent=true;for(int k=0;k<12;++k)equivalent=equivalent&&fabsf(helperBasis[k]-OpticsBasis[k])<.00001f;
    if(!equivalent)Require(false,"production camera-to-local helper matches independently computed inverse camera");memcpy(OpticsBasis,helperBasis,sizeof(helperBasis));
    Check(Dev->SetVertexShaderConstantF(0,c,12));
}
static void Params(float active=0,float clock=3,float pulse=0,float gain=1,float activationEnvelope=0,float activationAge=0,float entryStrength=0,float entryAge=0) {
    float c[32]={clock,active,pulse,gain,1.f/W,1.f/H,.018f,0,.5f/W,(1-Letterbox)*.5f+.5f/H,1-.5f/W,(1+Letterbox)*.5f-.5f/H,1,20000,0,.9f,Eye[0],Eye[1],Eye[2],0,activationEnvelope,activationAge,entryStrength,entryAge,tanf(.523598775f)*float(W)/(H*Letterbox),tanf(.523598775f),0,0,1,1,1,0};
    Check(Dev->SetPixelShaderConstantF(0,c,8));Check(Dev->SetVertexShaderConstantF(12,c,1));
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
    if(OpticsMode) {
        Dev->SetDepthStencilSurface(nullptr);Dev->SetRenderState(D3DRS_ZENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);Dev->SetTexture(0,SceneColor);Dev->SetTexture(1,SceneDepth);
        for(int n=0;n<2;++n){Dev->SetSamplerState(n,D3DSAMP_MINFILTER,n?D3DTEXF_POINT:D3DTEXF_LINEAR);Dev->SetSamplerState(n,D3DSAMP_MAGFILTER,n?D3DTEXF_POINT:D3DTEXF_LINEAR);Dev->SetSamplerState(n,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Dev->SetSamplerState(n,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);}
        Vertex q[]={{{-1,-1,0},0xffffffff,{0,1}},{{1,-1,0},0xffffffff,{1,1}},{{-1,1,0},0xffffffff,{0,0}},{{1,1,0},0xffffffff,{1,0}}};
        Dev->SetVertexShader(OpticsVS[OpticsMode-1]);Dev->SetPixelShader(OpticsPS[OpticsMode-1]);Dev->SetPixelShaderConstantF(0,OC,12);Dev->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1);Check(Dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));Dev->SetTexture(0,nullptr);Dev->SetTexture(1,nullptr);Dev->SetDepthStencilSurface(Depth);return;
    }
    if(Ingress) {
        Dev->SetDepthStencilSurface(nullptr);Dev->SetRenderState(D3DRS_ZENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
        Dev->SetTexture(0,SceneColor);Dev->SetTexture(1,SceneDepth);
        for(int n=0;n<2;++n){Dev->SetSamplerState(n,D3DSAMP_MINFILTER,n?D3DTEXF_POINT:D3DTEXF_LINEAR);Dev->SetSamplerState(n,D3DSAMP_MAGFILTER,n?D3DTEXF_POINT:D3DTEXF_LINEAR);Dev->SetSamplerState(n,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Dev->SetSamplerState(n,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);}
        Vertex q[]={{{-1,-1,0},0xffffffff,{0,1}},{{1,-1,0},0xffffffff,{1,1}},{{-1,1,0},0xffffffff,{0,0}},{{1,1,0},0xffffffff,{1,0}}};
        Dev->SetVertexShader(IngressVS);Dev->SetPixelShader(IngressPS);Dev->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1);Check(Dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));
        Dev->SetTexture(0,nullptr);Dev->SetTexture(1,nullptr);Dev->SetDepthStencilSurface(Depth);return;
    }
    if(WarpEnabled&&!WallOnly) {
        Check(Dev->SetPixelShader(Warp));Dev->SetTexture(0,SceneColor);Dev->SetTexture(1,SceneDepth);
        for(int sampler=0;sampler<2;++sampler) {
            Dev->SetSamplerState(sampler,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Dev->SetSamplerState(sampler,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
            Dev->SetSamplerState(sampler,D3DSAMP_MINFILTER,sampler?D3DTEXF_POINT:D3DTEXF_LINEAR);
            Dev->SetSamplerState(sampler,D3DSAMP_MAGFILTER,sampler?D3DTEXF_POINT:D3DTEXF_LINEAR);
            Dev->SetSamplerState(sampler,D3DSAMP_MIPFILTER,D3DTEXF_NONE);
        }
        Dev->SetDepthStencilSurface(nullptr);Dev->SetRenderState(D3DRS_ZENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
        Geometry(JumpHoleLensVertexCount);Dev->SetTexture(0,nullptr);Dev->SetTexture(1,nullptr);
    }
    // Production cloud uses sampled depth in both passes; proxy Z must not produce a false pass.
    Dev->SetDepthStencilSurface(nullptr);Dev->SetRenderState(D3DRS_ZENABLE,FALSE);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    Dev->SetTexture(1,SceneDepth);Dev->SetSamplerState(1,D3DSAMP_MINFILTER,D3DTEXF_POINT);Dev->SetSamplerState(1,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
    if(GlowEnabled) {Check(Dev->SetPixelShader(PS));Geometry(WallOnly?JumpHoleLensVertexCount:JumpHoleVertexCount);}
    Dev->SetTexture(1,nullptr);Dev->SetDepthStencilSurface(Depth);
}
static void DepthTexture(bool blocker,bool cockpit) {
    D3DLOCKED_RECT r;Check(SceneDepth->LockRect(0,&r,nullptr,0));
    for(int y=0;y<H;++y)for(int x=0;x<W;++x) {
        float d=1.f;
        if(MockShip){if(ShipPixel(x,y))d=ZForDistance(90);if(MockOccluders&&x>W*.58f&&x<W*.64f&&y>H*.35f&&y<H*.65f)d=ZForDistance(35);if(MockOccluders&&y>H*.78f)d=.95f;}
        if(blocker&&x>=W/4&&x<W*3/4&&y>=H/4&&y<H*3/4)d=BlockerDepth;
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
        D3DRECT area={W/4,H/4,W*3/4,H*3/4};Check(Dev->Clear(1,&area,D3DCLEAR_ZBUFFER|(background?D3DCLEAR_TARGET:0),0xffff00ff,BlockerDepth,0));
    }
    if(cockpit&&background) {D3DRECT area={0,H*3/4+1,W,H};Check(Dev->Clear(1,&area,D3DCLEAR_TARGET,0xff00ff00,1,0));}
    Check(Dev->EndScene());CopyScene();Check(Dev->BeginScene());
    Draw();Check(Dev->EndScene());
    if(CombinedOptics){int saved=OpticsMode;OpticsMode=Ingress?2:1;CopyScene();Check(Dev->BeginScene());Draw();Check(Dev->EndScene());OpticsMode=saved;}
    Check(Dev->GetRenderTargetData(Target,Cpu));
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
    if(OpticsMode)printf("%dx%d: %.3f us scene copy + %s optics (2 UP triangles, isolated GPU)\n",W,H,times[times.size()/2],OpticsMode==1?"world":"ship");
    else if(Ingress)printf("%dx%d: %.3f us per scene copy + ingress (2 UP triangles, isolated GPU; not total frame)\n",W,H,times[times.size()/2]);
    else printf("%dx%d: %.3f us per scene copy + warp + glow (%u glow triangles + %u warp, static VB, isolated GPU; not total frame)\n",W,H,times[times.size()/2],JumpHoleVertexCount/3,JumpHoleLensVertexCount/3);
    Release(a);Release(b);Release(f);Release(d);return times[times.size()/2];
}

static void CheckFiniteFloatOutput(float activation=0,float activationAge=0,float entry=0,float entryAge=0) {
    IDirect3DSurface9 *target=nullptr,*cpu=nullptr;
    Check(Dev->CreateRenderTarget(W,H,D3DFMT_A32B32G32R32F,D3DMULTISAMPLE_NONE,0,FALSE,&target,nullptr));
    Check(Dev->CreateOffscreenPlainSurface(W,H,D3DFMT_A32B32G32R32F,D3DPOOL_SYSTEMMEM,&cpu,nullptr));
    // Use a valid colour snapshot, then inspect actual unquantized outputs of both production passes.
    Camera();Params(1,3,0,1,activation,activationAge,entry,entryAge);if(OpticsMode)OpticsParams(1);Render(nullptr,true);Check(Dev->SetRenderTarget(0,target));
    for(int pose=0;pose<3;++pose) {
        Camera(pose==1?3.14159265f:0,0,pose==2?80:1400);if(Ingress){Eye[0]=Eye[1]=0;Eye[2]=-360+pose*380;}Params(1,3,0,1,activation,activationAge,entry,entryAge);if(OpticsMode)OpticsParams(1);
        Check(Dev->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,1,0));Check(Dev->BeginScene());Draw();Check(Dev->EndScene());
        Check(Dev->GetRenderTargetData(target,cpu));D3DLOCKED_RECT r;Check(cpu->LockRect(&r,nullptr,D3DLOCK_READONLY));bool finite=true;
        for(int y=0;y<H;++y)for(int x=0;x<W*4;++x)finite=finite&&std::isfinite(((float*)((char*)r.pBits+y*r.Pitch))[x]);
        Check(cpu->UnlockRect());Require(finite,"front/back/inside FP32 render output contains no NaN or infinity");
    }
    Check(Dev->SetRenderTarget(0,Target));Release(target);Release(cpu);
}
static void CheckLifecycle() {
    FJumpHoleVisualPhase p;Require(p.ActivationEnvelope()==0&&p.Opening==0,"idle has no activation pulse");p.Open();p.Tick(.3f);Require(p.ActivationEnvelope()>.9f&&p.Opening>0,"open starts a distinct bright activation phase");
    auto paused=p;p.Tick(0);p.Tick(-1);p.Tick(std::numeric_limits<float>::quiet_NaN());Require(memcmp(&p,&paused,sizeof(p))==0,"zero/invalid timestep preserves all visual clocks");float age=p.ActivationAge;p.Open();Require(p.ActivationAge==age,"repeated open does not restart pulse");
    p.Close();p.Tick(2);Require(p.Opening==0&&p.ActivationEnvelope()==0,"close returns to idle without an entry trigger");p.Open();Require(p.ActivationAge==0,"new open after close restarts activation");p.Time=95.99f;p.Tick(.02f);Require(fabsf(p.Time-.01f)<.0001f,"production visual clock wraps at96 seconds");
    Require(JumpHoleApproachStrength(false,0,0,-28)==0,"nearby undocked player cannot trigger approach");Require(JumpHoleApproachStrength(true,0,0,-700)==0&&JumpHoleApproachStrength(true,400,0,-28)==0&&JumpHoleApproachStrength(true,0,0,150)==0,"approach excludes distant/lateral/backside positions");
    Require(JumpHoleApproachStrength(true,.146f,-.438f,-28)>.99f,"authored docking mount reaches approach peak");Require(JumpHoleApproachStrength(true,0,0,-330)<JumpHoleApproachStrength(true,0,0,-168),"approach grows along authored docking path");
    Require(JumpHoleIngressEnvelope(0)>.8f&&JumpHoleIngressEnvelope(.08f)>.99f,"entry is visible immediately despite zero JumpOutTime");Require(JumpHoleIngressEnvelope(-1)==0&&JumpHoleIngressEnvelope(JumpHoleIngressDuration)==0&&JumpHoleIngressEnvelope(std::numeric_limits<float>::quiet_NaN())==0,"entry ends at production duration and rejects invalid age");
}
int main(int argc,char**argv) {
    CheckLifecycle();if(argc>1&&strcmp(argv[1],"--lifecycle")==0)return 0;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);CreateDirectoryA("src/obj/jumphole_check",nullptr);
    HWND hwnd=CreateWindowA("STATIC","jumphole check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9 available");
    D3DADAPTER_IDENTIFIER9 adapter;Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s (not GTX1060; isolated GPU timings only)\n",adapter.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,hwnd,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&Dev));Compile();CreateNoise();Size(960,540);
    Mesh.resize(JumpHoleVertexCount);BuildJumpHoleVisualGeometry(Mesh.data());
    bool finite=true;for(auto const&v:Mesh)for(float f:v.Position)finite=finite&&std::isfinite(f);Require(finite,"finite mesh coordinates");
    Check(Dev->CreateVertexBuffer(UINT(Mesh.size()*sizeof(Vertex)),D3DUSAGE_WRITEONLY,0,D3DPOOL_MANAGED,&VB,nullptr));
    void* data=nullptr;Check(VB->Lock(0,0,&data,0));memcpy(data,Mesh.data(),Mesh.size()*sizeof(Vertex));Check(VB->Unlock());
    Dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);Dev->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);Dev->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
    Dev->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);Dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);Dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    Dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);Dev->SetRenderState(D3DRS_LIGHTING,FALSE);
    if(argc>1&&strcmp(argv[1],"--opticsbench")==0) {
        CompileOptics();for(int size=0;size<2;++size){Size(size?3840:1920,size?2160:1080);Camera();OpticsParams();OpticsMode=1;Benchmark();MockShip=true;OpticsMode=2;OpticsParams(1);Benchmark();MockShip=false;}return 0;
    }
    if(argc>1&&strcmp(argv[1],"--opticsqa")==0) {
        CompileOptics();
        const float palettes[][4]={{.65f,.85f,1.2f,0},{1.5f,.85f,.35f,0},{.45f,1.15f,.50f,0},{1.1f,.45f,1.25f,0}};
        const char* paletteNames[]={"palette_blue","palette_amber","palette_green","palette_purple"};
        auto delta=[](const std::vector<DWORD>&a,const std::vector<DWORD>&b){double sum=0;for(size_t i=0;i<a.size();++i)for(int k=0;k<3;++k)sum+=abs(int((a[i]>>(8*k))&255)-int((b[i]>>(8*k))&255));return sum;};
        Camera();GlowEnabled=false;WarpEnabled=false;auto gainBase=Render(nullptr,true);WarpEnabled=true;Params(1);auto fullLens=Render(nullptr,true);Params(1,3,0,.01f);Require(delta(gainBase,Render(nullptr,true))<delta(gainBase,fullLens)*.15,"world lens low gain fades without residual darkening");GlowEnabled=true;
        OpticsMode=1;OpticsParams();auto fullMirror=Render(nullptr,true);OpticsParams(0,3,.01f);Require(delta(gainBase,Render(nullptr,true))<delta(gainBase,fullMirror)*.15,"mirror low gain fades without residual darkening");OpticsMode=0;
        Camera();Params();auto neutral=Render(nullptr,true);
        for(int p=0;p<4;++p){Params();Dev->SetPixelShaderConstantF(7,palettes[p],1);auto tinted=Render(paletteNames[p],true);Require(Changes(neutral,tinted)>1000,"authored palette changes volumetric light");Params(0,3,0,0);Dev->SetPixelShaderConstantF(7,palettes[p],1);auto zero=Render(nullptr,true);WarpEnabled=GlowEnabled=false;Require(Changes(zero,Render(nullptr,true))==0,"palette with zero gain is exact identity");WarpEnabled=GlowEnabled=true;}
        OpticsMode=1;OpticsParams();auto neutralMirror=Render(nullptr,true);for(int p=0;p<4;++p){memcpy(OC+44,palettes[p],16);Require(Changes(neutralMirror,Render(nullptr,true))>20,"authored palette changes the subtle mirror glint");}OpticsMode=0;
        GlowEnabled=false;for(int view=0;view<3;++view){Camera(view==1?1.5707963f:view==2?3.14159265f:0);Params();WarpEnabled=false;auto bare=Render(nullptr,true);WarpEnabled=true;auto lens=Render(nullptr,true);int diff=Changes(bare,lens);printf("World lens differences view%d: %d pixels\n",view,diff);Require(view==0?diff>100:diff==0,"world refraction visible only through front entrance; side/back exact identity");}GlowEnabled=true;
        CombinedOptics=true;for(int pose=0;pose<5;++pose){Camera(pose==2?.7f:pose==3?1.5707963f:pose==4?3.14159265f:0,.08f);Params(pose?1:0);OpticsParams();OC[1]=pose?1:0;const char* names[]={"combined_idle","combined_active","combined_oblique","combined_side","combined_back"};Render(names[pose],true);}CombinedOptics=false;
        for(int angle=0;angle<2;++angle){ActualWorld=false;Camera(angle?.7f:0,.12f,1400);OpticsParams();OpticsMode=1;auto origin=Render(nullptr,true);ActualWorld=true;Camera(angle?.7f:0,.12f,1400);OpticsParams();auto translated=Render(nullptr,true);Require(Changes(origin,translated,2)<W*H/200,"production optics camera-to-local preserves translated180degree host and yaw");}ActualWorld=false;
        OpticsMode=1;for(int view=0;view<3;++view){Camera(view==1?1.5707963f:view==2?3.14159265f:0);OpticsParams();auto mirror=Render(nullptr,true);OC[23]=0;auto noMirror=Render(nullptr,true);int diff=Changes(mirror,noMirror);printf("Mirror-only differences view%d: %d pixels\n",view,diff);Require(view==0?diff>100:diff==0,"mirror visible from local minusZ front and absent exactly from side/back");}
        Camera();OpticsMode=1;OpticsParams(0,3,0);auto base=Render(nullptr,true);OpticsParams();auto world=Render("optics_world",true);Require(Changes(base,world)>1000,"world mirror and halo are visible");
        OC[23]=0;Require(Changes(base,Render(nullptr,true))==0,"no external smoke or outflow remains when mirror is disabled");OC[23]=.9f;
        OpticsMode=0;WarpEnabled=GlowEnabled=false;Require(Changes(base,Render(nullptr,true))==0,"world optics zero gain is exact scene identity");WarpEnabled=GlowEnabled=true;OpticsMode=1;
        OpticsParams(0,4);Require(Changes(world,Render(nullptr,true))>200,"world optics animates");OpticsParams();OC[23]=0;Require(Changes(world,Render(nullptr,true))>100,"mirror strength changes captured-space core");
        Camera(.7f,.15f);OpticsParams();Render("optics_oblique",true);Camera(3.14159265f);OpticsParams();Render("optics_back",true);Camera();OpticsParams();auto protectedWorld=Render("optics_protected",true,true,true);OpticsParams(0,3,0);auto protectedBase=Render(nullptr,true,true,true);int leaks=0;for(int y=0;y<H;++y)for(int x=0;x<W;++x)if((x>=W/4&&x<W*3/4&&y>=H/4&&y<H*3/4)||y>H*3/4)leaks+=protectedWorld[y*W+x]!=protectedBase[y*W+x];Require(leaks==0,"world optics protects foreground and cockpit");
        CheckFiniteFloatOutput();
        MockShip=true;D3DLOCKED_RECT lock;Check(Background->LockRect(0,&lock,nullptr,0));for(int y=0;y<H;++y)for(int x=0;x<W;++x){DWORD c=D3DCOLOR_XRGB(12+x%19,22+y%17,40);if(ShipPixel(x,y))c=D3DCOLOR_XRGB(150+((x/8+y/8)&1)*90,25,18);if(x>W*.58f&&x<W*.64f&&y>H*.35f&&y<H*.65f)c=0xffff00ff;if(y>H*.78f)c=0xff00ff00;((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=c;}Check(Background->UnlockRect(0));
        OpticsMode=2;Camera();OpticsParams(0);auto shipBase=Render("ship_unwarped",true);OpticsMode=0;WarpEnabled=GlowEnabled=false;auto noPass=Render(nullptr,true);WarpEnabled=GlowEnabled=true;OpticsMode=2;Require(Changes(shipBase,noPass)==0,"unauthorized entry is exact identity");
        OpticsParams(1,3,0);Require(Changes(shipBase,Render(nullptr,true))==0,"ship optics zero gain is exact identity");OpticsParams(1);auto shipWarp=Render("ship_warped",true);leaks=0;int outside=0,inside=0;for(int y=0;y<H;++y)for(int x=0;x<W;++x){DWORD a=shipBase[y*W+x],b=shipWarp[y*W+x];if(a==0xffff00ff||a==0xff00ff00)leaks+=a!=b;bool redA=((a>>16)&255)>100&&((a>>8)&255)<60&&(a&255)<60,redB=((b>>16)&255)>100&&((b>>8)&255)<60&&(b&255)<60;outside+=!redA&&redB;inside+=redA&&!redB;}
        printf("Ship silhouette gained %d pixels and lost %d pixels\n",outside,inside);Require(outside>20&&inside>20,"authorized entry deforms ship silhouette, not only internal texture");Require(leaks==0,"ship warp preserves nearer nonplayer occluder and cockpit exactly");
        Require(Changes(shipWarp,Render(nullptr,true))==0,"ship warp pause is pixel-exact");OC[0]=99;Require(Changes(shipWarp,Render(nullptr,true),2)<W*H/200,"ship warp clock repeats after96seconds");OC[0]=3;OC[40]=300;OC[41]=5;Require(Changes(shipBase,Render(nullptr,true))==0,"empty authorized depth band is exact identity");OpticsParams(1);OC[43]=0;Render("ship_entry_start",true);
        Camera(0,0,1400,.6f);OpticsParams(1);auto bars=Render("ship_letterbox",true);OpticsParams(0);auto bare=Render(nullptr,true);leaks=0;for(int y=0;y<H;++y)if(y<int(H*.2f)-2||y>int(H*.8f)+2)for(int x=0;x<W;++x)leaks+=bars[y*W+x]!=bare[y*W+x];Require(leaks==0,"ship optics respects viewport bars");
        OpticsMode=0;Ingress=true;CombinedOptics=true;Camera(0,0,180);Params(1,3,0,1,0,1,1,.5f);OpticsParams(1);Render("combined_ingress_ship",true);CombinedOptics=false;Ingress=false;OpticsMode=2;CheckFiniteFloatOutput();return 0;
    }
    if(argc>1&&strcmp(argv[1],"--phaseqa")==0) {
        BlockerDepth=.9f*(20000.f/19999.f-20000.f/(19999.f*100.f)); // physical 100m foreground, not merely depth zero
        for(int overlay=0;overlay<2;++overlay)for(int event=0;event<2;++event) {
            Ingress=overlay!=0;Camera(0,0,overlay?180:1400);float a=event?0.f:1.f,e=event?1.f:0.f;
            Params(1,3,0,0,a,.3f,e,.5f);auto bare=Render(nullptr,true,true,true);
            Params(1,3,0,1,a,.3f,e,.5f);auto actual=Render(nullptr,true,true,true);int leaks=0,pulls=0;
            for(int y=0;y<H;++y)for(int x=0;x<W;++x){bool protectedPixel=(x>=W/4&&x<W*3/4&&y>=H/4&&y<H*3/4)||y>H*3/4;DWORD c=actual[y*W+x];if(protectedPixel)leaks+=c!=bare[y*W+x];else pulls+=int((c>>16)&255)>int((c>>8)&255)+5&&int(c&255)>int((c>>8)&255)+30;}
            Require(leaks==0,"strong event/ingress preserves foreground and cockpit exactly");Require(pulls==0,"strong event/ingress rejects displaced foreground footprint");
            Require(Changes(actual,Render(nullptr,true,true,true))==0,"strong event/ingress pause is pixel-exact");
            if(!overlay)Require(Changes(actual,bare)>100,"strong world event remains visible around foreground");
            if(!overlay)CheckFiniteFloatOutput(a,.3f,e,.5f);
        }
        Ingress=true;Camera(0,0,180);Params(1,3,0,1,0,1,0,0);auto zero=Render(nullptr,true);Ingress=false;WarpEnabled=GlowEnabled=false;auto bareScene=Render(nullptr,true);WarpEnabled=GlowEnabled=true;Ingress=true;Require(Changes(zero,bareScene)==0,"zero ingress envelope preserves captured scene exactly");Params(1,3,0,0,0,1,1,.5f);Require(Changes(bareScene,Render(nullptr,true))==0,"zero ingress gain preserves captured scene exactly");
        Params(1,3,0,1,0,1,1,.5f);auto peak=Render("ingress_peak",true);Require(Changes(zero,peak)>W*H/4,"ingress peak visibly replaces tunnel with volumetric passage");
        Camera(0,0,180,.6f);Params(1,3,0,1,0,1,1,.5f);auto bars=Render("ingress_letterbox",true);Params(1,3,0,0,0,1,1,.5f);auto empty=Render(nullptr,true);int leaks=0;for(int y=0;y<H;++y)if(y<int(H*.2f)-2||y>int(H*.8f)+2)for(int x=0;x<W;++x)leaks+=bars[y*W+x]!=empty[y*W+x];Require(leaks==0,"ingress preserves letterbox exactly");CheckFiniteFloatOutput(0,1,1,.5f);
        return 0;
    }
    if(argc>1&&strcmp(argv[1],"--phasepreviews")==0) {
        const float phases[][4]={{0,0,0,0},{1,.25f,0,0},{.65f,.75f,0,0},{0,1,.6f,.25f},{0,1,1,.75f}};
        const char* names[]={"idle","activation_early","activation_late","entry_early","entry_late"};
        for(int phase=0;phase<5;++phase){Camera(.3f,.1f,1400);Params(phase?1.f:0.f,3,0,1,phases[phase][0],phases[phase][1],phases[phase][2],phases[phase][3]);char name[100];sprintf(name,"phase_%s",names[phase]);Render(name,true);}
        return 0;
    }
    if(argc>1&&strcmp(argv[1],"--funnelpreviews")==0) {
        const char* poses[]={"front","oblique","back","inside","side"};
        for(int pose=0;pose<5;++pose)for(int active=0;active<2;++active) {
            Camera(pose==1?.85f:pose==2?3.14159265f:pose==4?1.5707963f:0,pose==1?.18f:0,pose==3?46:1400);Params(float(active));
            char name[100];sprintf(name,"funnel_%s_%s",poses[pose],active?"active":"idle");Render(name,true);
        }
        return 0;
    }
    if(argc>1&&(strcmp(argv[1],"--nearorange")==0||strcmp(argv[1],"--cloudpreviews")==0)) {
        D3DLOCKED_RECT lock;Check(Background->LockRect(0,&lock,nullptr,0));
        for(int y=0;y<H;++y)for(int x=0;x<W;++x)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=0xff8c542c;
        Check(Background->UnlockRect(0));
        for(int pose=0;pose<2;++pose)for(int dim=0;dim<2;++dim) {
            Camera(0,0,pose?46:80);Params(0,3,0,dim?.25f:1.f);
            WarpEnabled=GlowEnabled=false;auto bare=Render(nullptr,true);WarpEnabled=GlowEnabled=true;
            char name[100];sprintf(name,"orange_%dm_idle_%s",pose?46:80,dim?"quartergain":"fullgain");auto a=Render(name,true);
            unsigned maxDelta=0;double mean=0;for(size_t i=0;i<a.size();++i)for(int k=0;k<3;++k){unsigned delta=abs(int((a[i]>>(k*8))&255)-int((bare[i]>>(k*8))&255));maxDelta=std::max(maxDelta,delta);mean+=delta;}
            printf("%s: changed=%d / %d pixels; maxRGBdelta=%u; mean channel delta=%.3f\n",name,Changes(a,bare),W*H,maxDelta,mean/(W*H*3));
            Require(Changes(a,bare)>100,"near orange idle remains rendered");
            if(!dim)Require(mean/(W*H*3)>=8,"near orange idle mean RGB difference is at least 8/255 (old lens was 3.6)");
        }
        for(int pose=0;pose<3;++pose)for(int active=0;active<2;++active)for(int orange=0;orange<2;++orange) {
            int distance=pose==0?1400:pose==1?80:46;Camera(.3f,.1f,float(distance));Params(float(active));char name[100];
            sprintf(name,"cloud_%s_%dm_%s",orange?"orange":"black",distance,active?"active":"idle");Render(name,orange!=0);
        }
        return 0;
    }
    if(argc>1&&strcmp(argv[1],"--video")==0) {
        CreateDirectoryA("src/obj/jumphole_check/video",nullptr);
        CompileOptics();CombinedOptics=true;MockOccluders=false;FJumpHoleVisualPhase phase;
        for(int n=0;n<270;++n){float t=n/30.f;if(n==30)phase.Open();if(n)phase.Tick(1.f/30);float travel=JumpHoleSmooth((t-3)/3.5f),distance=1500*(1-travel)+28*travel;
            float ingressAge=t-6.5f;Ingress=ingressAge>=0;
            if(n==195){MockShip=true;D3DLOCKED_RECT lock;Check(Background->LockRect(0,&lock,nullptr,0));for(int y=0;y<H;++y)for(int x=0;x<W;++x)if(ShipPixel(x,y))((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=D3DCOLOR_XRGB(150+((x/8+y/8)&1)*90,25,18);Check(Background->UnlockRect(0));}
            Camera(-.35f*(1-travel),.08f*(1-travel),distance);
            if(Ingress){Eye[0]=Eye[1]=0;Eye[2]=-360+760*JumpHoleSmooth(ingressAge/JumpHoleIngressDuration);Params(1,phase.Time,0,1,0,1,JumpHoleIngressEnvelope(ingressAge),JumpHoleSaturate(ingressAge/JumpHoleIngressDuration));}
            else{float approach=JumpHoleApproachStrength(t>=3,0,0,-distance);Params(JumpHoleSmooth(phase.Opening),phase.Time,phase.Ripple,1,phase.ActivationEnvelope(),phase.ActivationAge/JumpHoleActivationDuration,approach*.9f,approach*.65f);}
            OpticsParams(Ingress?JumpHoleIngressEnvelope(ingressAge):0,phase.Time);OC[1]=JumpHoleSmooth(phase.Opening);OC[2]=phase.ActivationEnvelope();
            char name[80];sprintf(name,"video/frame_%04d",n);Render(name,true);}
        puts("PASS 270 video frames960x540@30fps:9seconds idle,activation,confirmed approach,ingress using production timing helpers");return 0;
    }
    for(int distanceIndex=0;distanceIndex<2;++distanceIndex)for(int angle=0;angle<2;++angle) {
        float distance=distanceIndex?1400.f:46.f,yaw=angle?.7f:0;
        ActualWorld=false;Camera(yaw,.12f,distance);Params();auto origin=Render(nullptr,true);
        ActualWorld=true;Camera(yaw,.12f,distance);Params();auto world=Render(nullptr,true);
        int changed=Changes(origin,world,2);printf("Real-world transform comparison %.0fm yaw%.1f: %d pixels differ by >2 RGB units\n",distance,yaw,changed);
        Require(changed<W*H/100,"world translation and 180-degree host rotation preserve relative camera rendering");
    }
    ActualWorld=false;
    CheckX8Snapshot();Camera();Params();WarpEnabled=GlowEnabled=false;auto background=Render(nullptr,true);
    WarpEnabled=GlowEnabled=true;Params(1,3,0,0);Require(Changes(background,Render(nullptr,true))==0,"zero gain is exact scene identity");Params();auto idle=Render("idle",true);Require(Changes(idle,background)>5000,"idle exterior visibly affects background");
    Require(Changes(idle,Render(nullptr,true))==0,"paused idle is pixel-exact");Params(1);auto active=Render("active",true);
    Require(Changes(active,idle)>1000,"activation changes visible structure");Require(Changes(active,Render(nullptr,true))==0,"paused active is pixel-exact");
    Params(1,4);Require(Changes(active,Render(nullptr,true))>500,"active field evolves with time");
    for(int state=0;state<2;++state) {
        Params(float(state),0);auto atZero=Render(nullptr,true);Params(float(state),96);auto atWrap=Render(nullptr,true);
        Require(Changes(atZero,atWrap,2)<W*H/200,"idle/active clock 0 and 96 reproduce same funnel within quantization tolerance");
        Params(float(state),95.999f);auto beforeWrap=Render(nullptr,true);
        Require(Changes(atZero,beforeWrap,2)<W*H/200,"idle/active final millisecond approaches zero clock without a visual jump");
    }
    for(int pose=0;pose<4;++pose){Camera(pose==0?.8f:pose==1?3.14159265f:pose==2?1.5707963f:0,.12f,pose==3?80:1400);Params(1);const char* names[]={"turned","back","edge","inside"};auto a=Render(names[pose],true);Require(Changes(a,background)>100,"orbit/back/inside render succeeds and remains visible");}
    Camera();Params(1);GlowEnabled=WarpEnabled=false;auto blockedBase=Render(nullptr,true,true,true);WarpEnabled=true;auto blockedLens=Render("protected_lens",true,true,true);int leaks=0,magentaPull=0;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){bool blocked=(x>=W/4&&x<W*3/4&&y>=H/4&&y<H*3/4)||y>H*3/4;
        if(blocked)leaks+=blockedBase[y*W+x]!=blockedLens[y*W+x];
        else {DWORD c=blockedLens[y*W+x];magentaPull+=int((c>>16)&255)>int((c>>8)&255)+5&&int(c&255)>int((c>>8)&255)+30;}}
    Require(leaks==0,"foreground and cockpit lens pixels preserved exactly");Require(magentaPull==0,"displaced source sampling does not pull foreground magenta into lens");
    GlowEnabled=true;auto all=Render("protected_full",true,true,true);leaks=0;for(int y=H/4;y<H*3/4;++y)for(int x=W/4;x<W*3/4;++x)leaks+=all[y*W+x]!=0xffff00ff;
    Require(leaks==0,"volume manually respects near geometry depth with hardware Z disabled");
    leaks=0;for(int y=H*3/4+1;y<H;++y)for(int x=0;x<W;++x)leaks+=all[y*W+x]!=blockedBase[y*W+x];Require(leaks==0,"volume manually preserves cockpit depth pixels exactly");
    Camera(.3f,.1f,1000,.6f);Params(1);auto bars=Render("letterbox",true);WarpEnabled=GlowEnabled=false;auto bare=Render(nullptr,true);leaks=0;
    for(int y=0;y<H;++y)if(y<int(H*.2f)-2||y>int(H*.8f)+2)for(int x=0;x<W;++x)leaks+=bars[y*W+x]!=bare[y*W+x];Require(leaks==0,"lens and glow preserve cinematic bars");
    WarpEnabled=GlowEnabled=true;CheckFiniteFloatOutput();
    for(int size=0;size<2;++size){Size(size?3840:1920,size?2160:1080);Camera();for(int state=0;state<2;++state){Params(float(state));printf("%s ",state?"ACTIVE":"IDLE");Benchmark();}}
    Camera(0,0,46);Params(1);printf("INSIDE FULLSCREEN ACTIVE ");Benchmark();
    Ingress=true;Camera(0,0,180);Params(1,3,0,1,0,1,1,.5f);printf("INGRESS FULLSCREEN ");Benchmark();Ingress=false;
    puts("PASS all jumphole checks, including FP32 output finite checks");
    Dev->SetTexture(0,nullptr);Dev->SetTexture(1,nullptr);Dev->SetTexture(2,nullptr);Dev->SetStreamSource(0,nullptr,0,0);Release(VB);Release(Noise);Release(Background);Release(SceneColor);Release(SceneDepth);Release(Target);Release(Cpu);Release(Depth);Release(VS);Release(PS);Release(Warp);Release(White);Release(Dev);Release(api);DestroyWindow(hwnd);return 0;
}
