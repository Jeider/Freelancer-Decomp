// Exercise the production upsampler on depth silhouettes at multiple resolutions.
// Volume colours identify the two sides of the depth edge; no raymarch approximation
// is involved in deciding whether filtering has crossed that edge.
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void Check(HRESULT hr) { if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);} }
static ID3DXBuffer* Compile(const char* entry,const char* profile,
                          const char* file="DATA_EXTRA/SHADERS/nebula_composite.hlsl") {
    ID3DXBuffer *code=nullptr,*errors=nullptr;
    HRESULT hr=D3DXCompileShaderFromFileA(file,
        nullptr,nullptr,entry,profile,0,&code,&errors,nullptr);
    if(errors){puts((char*)errors->GetBufferPointer());errors->Release();}
    Check(hr);return code;
}
static const int W=384,H=256;
static const DWORD Fog=0xff80a0c0,Clear=0xff000000;
static bool Solid(int x,int y,int shift) {
    float dx=float(x-93-shift),dy=float(y-100);
    // Curved asteroid and thin ship wings/body, with sub-low-texel translation.
    return dx*dx+dy*dy<47*47 ||
        (abs(x-270-shift)<9 && abs(y-160)<55) ||
        (abs(x-270-shift)<48 && abs(y-160)<6);
}
static bool LowSolid(int x,int y,int lw,int lh,int shift) {
    x=(std::max)(0,(std::min)(lw-1,x));y=(std::max)(0,(std::min)(lh-1,y));
    // Same full-resolution point depth tap as PSRaymarch, including its half texel.
    int sx=(int)std::floor((x+.5f)*W/lw+.51f),sy=(int)std::floor((y+.5f)*H/lh+.51f);
    return Solid((std::min)(W-1,sx),(std::min)(H-1,sy),shift);
}
int main() {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","nebula composite check",WS_POPUP,0,0,W,H,
        nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* dev=nullptr;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&dev));
    auto march=Compile("PSRaymarch","ps_3_0","DATA_EXTRA/SHADERS/nebula_volume.hlsl");
    IDirect3DPixelShader9* marchPs=nullptr;
    Check(dev->CreatePixelShader((DWORD*)march->GetBufferPointer(),&marchPs));
    marchPs->Release();march->Release();
    march=Compile("PSRaymarch","ps_3_0","DATA_EXTRA/SHADERS/nebula_ice.hlsl");
    Check(dev->CreatePixelShader((DWORD*)march->GetBufferPointer(),&marchPs));
    marchPs->Release();march->Release();
    puts("PASS default and ice raymarch shaders compile and create on D3D9");
    march=Compile("PSRaymarch","ps_3_0","DATA_EXTRA/SHADERS/nebula_walker_ice.hlsl");
    Check(dev->CreatePixelShader((DWORD*)march->GetBufferPointer(),&marchPs));
    marchPs->Release();march->Release();
    puts("PASS walker ice shader compiles and creates on D3D9");
    auto code=Compile("VSMain","vs_3_0");IDirect3DVertexShader9* vs=nullptr;
    Check(dev->CreateVertexShader((DWORD*)code->GetBufferPointer(),&vs));code->Release();
    code=Compile("PSComposite","ps_3_0");IDirect3DPixelShader9* ps=nullptr;
    Check(dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&ps));code->Release();
    Check(dev->SetVertexShader(vs));Check(dev->SetPixelShader(ps));
    Check(dev->SetFVF(D3DFVF_XYZ|D3DFVF_TEX1));
    dev->SetRenderState(D3DRS_ZENABLE,FALSE);dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    for(int s=0;s<2;++s) {
        dev->SetSamplerState(s,D3DSAMP_MINFILTER,s?D3DTEXF_LINEAR:D3DTEXF_POINT);
        dev->SetSamplerState(s,D3DSAMP_MAGFILTER,s?D3DTEXF_LINEAR:D3DTEXF_POINT);
        dev->SetSamplerState(s,D3DSAMP_MIPFILTER,D3DTEXF_NONE);
        dev->SetSamplerState(s,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);
        dev->SetSamplerState(s,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    }
    IDirect3DTexture9* depth=nullptr;
    Check(dev->CreateTexture(W,H,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&depth,nullptr));
    Check(dev->SetTexture(0,depth));
    IDirect3DSurface9 *target=nullptr,*cpu=nullptr;
    Check(dev->GetRenderTarget(0,&target));
    Check(dev->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&cpu,nullptr));
    const float quad[4][5]={{-1-1.f/W,1+1.f/H,0,0,0},{1-1.f/W,1+1.f/H,0,1,0},
        {-1-1.f/W,-1+1.f/H,0,0,1},{1-1.f/W,-1+1.f/H,0,1,1}};
    int total=0;
    for(float scale : {.25f,.35f,.5f,1.f}) {
        int lw=int(W*scale),lh=int(H*scale);
        IDirect3DTexture9* volume=nullptr;
        Check(dev->CreateTexture(lw,lh,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&volume,nullptr));
        Check(dev->SetTexture(1,volume));
        for(int shift=0;shift<4;++shift) {
            D3DLOCKED_RECT lock;Check(depth->LockRect(0,&lock,nullptr,0));
            for(int y=0;y<H;++y)for(int x=0;x<W;++x)
                ((float*)((char*)lock.pBits+y*lock.Pitch))[x]=Solid(x,y,shift)?.99f:.9999f;
            Check(depth->UnlockRect(0));Check(volume->LockRect(0,&lock,nullptr,0));
            for(int y=0;y<lh;++y)for(int x=0;x<lw;++x)
                ((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=LowSolid(x,y,lw,lh,shift)?Clear:Fog;
            Check(volume->UnlockRect(0));
            for(float blur : {0.f,1.f,2.f}) {
                float params[96]={1,-1,1,0,float(lw),float(lh),1.f/lw,1.f/lh,
                    .5f/W,.5f/H,.1f,0,1,0,1,blur};
                Check(dev->SetPixelShaderConstantF(0,params,24));
                Check(dev->BeginScene());Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(quad[0])));
                Check(dev->EndScene());Check(dev->GetRenderTargetData(target,cpu));
                Check(cpu->LockRect(&lock,nullptr,D3DLOCK_READONLY));
                int leaks=0,holes=0;
                for(int y=2;y<H-2;++y)for(int x=2;x<W-2;++x) {
                    bool solid=Solid(x,y,shift),match=false;
                    int bx=(int)std::floor((x+.5f)*lw/W-.5f+.0001f),by=(int)std::floor((y+.5f)*lh/H-.5f+.0001f);
                    for(int j=0;j<2;++j)for(int i=0;i<2;++i)
                        match|=LowSolid(bx+i,by+j,lw,lh,shift)==solid;
                    if(!match)continue; // no low-resolution sample represents this thin feature
                    DWORD got=((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x];
                    DWORD expected=solid?Clear:Fog;
                    bool bad=false;for(int c=0;c<24;c+=8)
                        bad|=abs(int((got>>c)&255)-int((expected>>c)&255))>2;
                    if(bad){if(solid)++leaks;else ++holes;}
                }
                Check(cpu->UnlockRect());total+=leaks+holes;
                printf("scale %.2f shift %d blur %.0f: foreground halos %d, background holes %d\n",scale,shift,blur,leaks,holes);
            }
        }
        Check(dev->SetTexture(1,nullptr));volume->Release();
    }
    // Ice horizon closes the sky behind scattering; finite geometry must keep its own
    // integrated fog, including the clear parts of exclusion zones.
    IDirect3DTexture9* flat=nullptr;
    Check(dev->CreateTexture(4,4,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&flat,nullptr));
    D3DLOCKED_RECT fl;Check(flat->LockRect(0,&fl,nullptr,0));
    for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)fl.pBits+y*fl.Pitch))[x]=0x80283c50;
    flat->UnlockRect(0);dev->SetTexture(1,flat);
    for(int test=0;test<3;++test){
        float params[24][4]={};auto C=[&](int i,float x=0,float y=0,float z=0,float w=0){
            params[i][0]=x;params[i][1]=y;params[i][2]=z;params[i][3]=w;};
        C(0,1.00001f,-1.00001f,1);C(1,4,4,.25f,.25f);C(2,.5f/W,.5f/H,.1f);
        C(3,1,0,2,0);C(4,0,0,1,1);C(5,1,1);C(6,1);C(7,0,1);C(8,0,0,1);
        for(int i=14;i<18;++i)C(i,0,0,0,1e30f);
        if(test==2)C(14,0,0,-2000,2000*2000-300*300);
        C(18,100,1.f/900,1);C(19,0,0,0,1);C(20,.0001f);C(21,0,.0001f);C(22,0,0,.0001f);
        C(23,.1f,.19f,.25f,1);
        Check(depth->LockRect(0,&fl,nullptr,0));
        for(int y=0;y<H;++y)for(int x=0;x<W;++x)
            ((float*)((char*)fl.pBits+y*fl.Pitch))[x]=test==1?1.00001f*(1-1.f/2000):1.f;
        depth->UnlockRect(0);Check(dev->SetPixelShaderConstantF(0,&params[0][0],24));
        Check(dev->BeginScene());Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(quad[0])));Check(dev->EndScene());
        Check(dev->GetRenderTargetData(target,cpu));Check(cpu->LockRect(&fl,nullptr,D3DLOCK_READONLY));
        DWORD pixel=((DWORD*)((char*)fl.pBits+(H/2)*fl.Pitch))[W/2];cpu->UnlockRect();
        DWORD expected=test==0?0x00355470:0x80283c50;
        bool bad=false;for(int ch=0;ch<32;ch+=8)bad|=abs(int((pixel>>ch)&255)-int((expected>>ch)&255))>2;
        printf("Ice horizon %s: %s (%08lx expected %08lx)\n",test==0?"sky":test==1?"opaque object":"depthless planet",bad?"FAIL":"PASS",pixel,expected);
        total+=bad;
    }
    printf("%s: depth-edge filtering and ice horizon (%d errors)\n",total?"FAIL":"PASS",total);
    return total?3:0;
}
