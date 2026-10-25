// Production ice shader preview on a hidden D3D9 device; also warms RP9's exact shader cache.
#include "RP9ShaderCache.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include "nebula_noise_fixture.h"
#include "../src/freelancer/Client/nebula_faceted_noise.h"

static void Check(HRESULT hr) { if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);} }
static std::string Read(const std::string& path) {
    FILE* f=fopen(path.c_str(),"rb");if(!f){printf("Missing %s\n",path.c_str());exit(2);}
    std::string s;char b[4096];size_t n;while((n=fread(b,1,sizeof(b),f)))s.append(b,n);
    fclose(f);return s;
}
class Include final : public ID3DXInclude {
    STDMETHOD(Open)(D3DXINCLUDE_TYPE,LPCSTR name,LPCVOID,LPCVOID* data,UINT* size) override {
        auto s=Read(std::string("DATA_EXTRA/SHADERS/")+name);
        char* p=new char[s.size()];memcpy(p,s.data(),s.size());*data=p;*size=(UINT)s.size();return S_OK;
    }
    STDMETHOD(Close)(LPCVOID p) override {delete[] (const char*)p;return S_OK;}
};
static std::vector<unsigned char> Compile(const char* file,const char* entry,const char* profile) {
    Include inc;std::vector<unsigned char> code;std::string msg;bool hit=false,stored=false;
    Check(Rp9ShaderCache::Compile(Read(std::string("DATA_EXTRA/SHADERS/")+file),&inc,entry,profile,
        0,&code,&msg,&hit,&stored));
    printf("%s %s: %s (%zu bytes)\n",file,entry,hit?"HIT":stored?"stored":"uncached",code.size());
    if(!msg.empty())puts(msg.c_str());return code;
}
int main(int argc,char** argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
    const bool walker=argc>1 && !strcmp(argv[1],"--walker");
    std::vector<unsigned char> vs,ps,composite;
    for(const char* file : {"nebula_volume.hlsl","nebula_ice.hlsl","nebula_walker_ice.hlsl","nebula_composite.hlsl"}) {
        auto v=Compile(file,"VSMain","vs_3_0");
        auto p=Compile(file,strstr(file,"composite")?"PSComposite":"PSRaymarch","ps_3_0");
        if(!strcmp(file,walker?"nebula_walker_ice.hlsl":"nebula_ice.hlsl")){vs=v;ps=p;}
        if(strstr(file,"composite"))composite=p;
    }
    if(argc>1 && !strcmp(argv[1],"--warm-only"))return 0;
    const int W=768,H=480;
    HWND window=CreateWindowA("STATIC","ice preview",WS_POPUP,0,0,W,H,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    auto api=Direct3DCreate9(D3D_SDK_VERSION);IDirect3DDevice9* d=nullptr;
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
    IDirect3DVertexShader9* v=nullptr;IDirect3DPixelShader9* p=nullptr;
    Check(d->CreateVertexShader((DWORD*)vs.data(),&v));Check(d->CreatePixelShader((DWORD*)ps.data(),&p));
    IDirect3DPixelShader9* cp=nullptr;
    Check(d->CreatePixelShader((DWORD*)composite.data(),&cp));
    IDirect3DSurface9 *back=nullptr,*marchSurface=nullptr,*readback=nullptr;
    IDirect3DTexture9* marchTarget=nullptr;
    Check(d->GetRenderTarget(0,&back));
    Check(d->CreateTexture(W/2,H/2,1,D3DUSAGE_RENDERTARGET,D3DFMT_A16B16G16R16F,D3DPOOL_DEFAULT,&marchTarget,nullptr));
    Check(marchTarget->GetSurfaceLevel(0,&marchSurface));
    Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readback,nullptr));
    d->SetVertexShader(v);d->SetPixelShader(p);d->SetFVF(D3DFVF_XYZ|D3DFVF_TEX1);
    d->SetRenderState(D3DRS_ZENABLE,FALSE);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    IDirect3DTexture9 *depth=nullptr,*white=nullptr;
    Check(d->CreateTexture(1,1,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&depth,nullptr));
    D3DLOCKED_RECT lock;Check(depth->LockRect(0,&lock,nullptr,0));*(float*)lock.pBits=1;
    depth->UnlockRect(0);d->SetTexture(0,depth);
    Check(D3DXCreateTextureFromFileA(d,"src/obj/tau37_ice_reference/white_circle_rgb.png",&white));
    d->SetTexture(2,white);
    std::vector<unsigned long> noise;unsigned long hist[256];GenerateNoise(&noise,hist);
    IDirect3DVolumeTexture9* vol=nullptr;
    Check(d->CreateVolumeTexture(64,64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&vol,nullptr));
    D3DLOCKED_BOX box;Check(vol->LockBox(0,&box,nullptr,0));
    for(int z=0;z<64;++z)for(int y=0;y<64;++y)
        memcpy((char*)box.pBits+z*box.SlicePitch+y*box.RowPitch,&noise[(z*64+y)*64],64*4);
    vol->UnlockBox(0);d->SetTexture(1,vol);
    if(walker){
        std::vector<unsigned long> faceted;
        DWORD start=GetTickCount();NebulaFacetedNoise::Generate(noise,&faceted);
        memset(hist,0,sizeof(hist));for(auto px:faceted)++hist[(px>>16)&255];
        printf("Faceted noise bake: %lu ms\n",GetTickCount()-start);
        const int N=NebulaFacetedNoise::Size;IDirect3DVolumeTexture9* ice=nullptr;
        Check(d->CreateVolumeTexture(N,N,N,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&ice,nullptr));
        Check(ice->LockBox(0,&box,nullptr,0));
        for(int z=0;z<N;++z)for(int y=0;y<N;++y)
            memcpy((char*)box.pBits+z*box.SlicePitch+y*box.RowPitch,&faceted[(z*N+y)*N],N*4);
        ice->UnlockBox(0);d->SetTexture(3,ice);
        d->SetSamplerState(3,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);d->SetSamplerState(3,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
        for(auto a:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV,D3DSAMP_ADDRESSW})d->SetSamplerState(3,a,D3DTADDRESS_WRAP);
    }
    for(int s=0;s<3;++s) {
        d->SetSamplerState(s,D3DSAMP_MINFILTER,s?D3DTEXF_LINEAR:D3DTEXF_POINT);
        d->SetSamplerState(s,D3DSAMP_MAGFILTER,s?D3DTEXF_LINEAR:D3DTEXF_POINT);
        d->SetSamplerState(s,D3DSAMP_MIPFILTER,s==2?D3DTEXF_LINEAR:D3DTEXF_NONE);
        for(auto a:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV,D3DSAMP_ADDRESSW})
            d->SetSamplerState(s,a,s==1?D3DTADDRESS_WRAP:D3DTADDRESS_CLAMP);
    }
    float c[109][4]={};auto C=[&](int i,float x=0,float y=0,float z=0,float w=0){c[i][0]=x;c[i][1]=y;c[i][2]=z;c[i][3]=w;};
    // Same scale/palette as tau37_ice, a representative position in a 40km zone.
    C(0,1.00001f,-1.00001f,1);C(1,0,0,1,1);C(2,1.0f,.625f,.5f/W,.5f/H);
    C(3,1);C(4,0,1);C(5,0,0,1);C(7,1.f/40000);C(8,0,1.f/40000);C(9,0,0,1.f/40000);
    C(10,128,12000,1.2f,1);C(11,-logf(.22f)*.9f/3000,4.f*.9f/3000,200);
    C(12,0,1,0,.35f);C(13,.31f,.42f,.17f,1.f/19200);C(14,.6f,.1f,.4f,1.f/3200);C(15,.23f,.7f,.5f,1.f/9600);
    // Production histogram coverage remap.
    double above=0;int low=0,high=255;bool got=false;
    const float coverage=walker?.46f:.58f,softness=walker?.42f:.60f;
    const size_t histogramCount=walker?128*128*128:noise.size();
    for(int b=255;b>=0;--b){above+=hist[b];if(!got&&above>=coverage*(1-softness)*histogramCount){high=b;got=true;}
        if(above>=coverage*histogramCount){low=b;break;}}
    float lo=low/255.f,inv=1.f/std::max((high-low)/255.f,.01f);
    C(16,lo,inv,.12f,.12f);C(17,3840,80,650,1);C(18,.152f,.2888f,.38f,1);
    C(19,.0006f,.00114f,.0015f,1.f/200);C(20,.008f,.01625f,.018f,.25f);
    C(21,.0945f,.189f,.273f,.96f);C(22,.399f,.5985f,.651f,1.f/570);
    C(23,22.f/255*1.2f,22.f/255*1.2f,33.f/255*1.2f,.504f);C(24,0,810);
    const float n=sqrtf(.89f);C(25,.4f/n,.8f/n,-.3f/n,.32f);C(26,.48f*.85f,.70f*.85f,.78f*.85f,.2f);
    C(27,.4f/n,.8f/n*1.35f,-.3f/n,.2f);C(28,.12f,.5f,.5f,.25f);
    C(29,260,.36f);C(30,780,.72f);C(31,1820,1.44f);
    C(35,0,0,0,1);C(36,W/2,H/2,2);C(77,10000,1.f/60000,.5f,.7f);C(78,1,4.f/H,0,0);
    C(79,600,16,64535,0);C(80,0,1.f/3500);C(87,.3045f,.4095f,.378f);
    C(88,1.f/.35f,.04f,.61f,1);C(89,1.02f,50,.005f,1.1236f);C(90,.3f,.6f,.1f,3);C(91,0,.8f,.2f,lo+.5f/inv);
    for(int i=93;i<97;++i)C(i,0,0,0,1e30f);
    C(100,1,1,1);C(103,.65f,.15f,1.f/2800,1);C(104,0,0,1,1);C(105,.2f,.4f,.6f);
    C(106,400,1.f/3200);C(107,1.2f,.05f,0);
    if(walker){
        C(10,80,10000,1.4f,1);C(11,-logf(.18f)*.8f/3000,1.5f*.8f/3000,200);
        C(12,0,1,0,2);C(13,.31f,.42f,.17f,1.f/13200);C(14,.6f,.1f,.4f,1.f/3600);C(15,.23f,.7f,.5f,1.f/6600);
        C(16,lo,inv,.35f,.45f);C(17,924,120,1500,1);C(18,.6f,.70588f,.9f,1);
        C(19,.20f,.235294f,.30f,1.f/200);C(20,.066667f,.078431f,.10f,.12f);
        C(21,.95f,.95f,.95f,.36f);C(22,.95f,.95f,.95f,1.f/1380);C(87);
        C(23,22.f/255*2.4f,22.f/255*2.4f,33.f/255*2.4f,.088f);C(24,0,1650);
        C(25,.4f/n,.8f/n,-.3f/n,.45f);C(26,.44f,.60f,.68f,.15f);
        C(27,.4f/n,.8f/n*3,-.3f/n,.1f);C(28,0,.5f,.5f,.25f);
        C(29,550,.352f);C(30,2200,.704f);C(31);
        C(79,850,16,64535);C(80,0,1.f/4000);C(103);C(106,200,1.f/3000);C(107);
    }
    const float quad[4][5]={{-1-1.f/W,1+1.f/H,0,0,0},{1-1.f/W,1+1.f/H,0,1,0},
        {-1-1.f/W,-1+1.f/H,0,0,1},{1-1.f/W,-1+1.f/H,0,1,1}};
    double previousTransmission=1;
    for(int frame=0;frame<(walker?8:2);++frame) {
        if(frame){C(13,.54f,.42f,.17f,1.f/19200);C(15,.69f,.7f,.5f,1.f/9600);C(14,.98f,.1f,.4f,1.f/3200);C(105,1.77714f,.4f,.6f);}
        if(frame && walker){C(13,.54f,.42f,.17f,1.f/13200);C(15,.69f,.7f,.5f,1.f/6600);C(14,.44333f,.1f,.4f,1.f/3600);}
        if(walker && frame>=2){
            const float distances[]={600,3000,8000,15000,15000,15000};
            Check(depth->LockRect(0,&lock,nullptr,0));
            *(float*)lock.pBits=c[0][0]+c[0][1]/distances[frame-2];depth->UnlockRect(0);
            if(frame>=6){
                // Look through an exclusion from outside; then from its clear core.
                C(35,1,0,0,1);C(37,0,0,frame==6?-9000.f:0.f,5);
                C(45,1.f/3000,0,0,3000.f/14800-1);C(53,0,1.f/3000,0,3004);C(61,0,0,1.f/3000);
                if(frame==7)C(108,0,0,0,2400.f*2400);
            }
        }
        Check(d->SetTexture(1,vol));Check(d->SetRenderTarget(0,marchSurface));
        D3DVIEWPORT9 low={0,0,W/2,H/2,0,1},full={0,0,W,H,0,1};d->SetViewport(&low);
        d->SetPixelShader(p);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);d->SetRenderState(D3DRS_COLORWRITEENABLE,15);
        for(auto a:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV,D3DSAMP_ADDRESSW})d->SetSamplerState(1,a,D3DTADDRESS_WRAP);
        Check(d->SetPixelShaderConstantF(0,&c[0][0],109));
        float lowQuad[4][5];memcpy(lowQuad,quad,sizeof(quad));
        for(auto& q:lowQuad){q[0]-=1.f/W;q[1]+=1.f/H;}
        Check(d->BeginScene());Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,lowQuad,sizeof(lowQuad[0])));Check(d->EndScene());
        Check(d->SetRenderTarget(0,back));d->SetViewport(&full);d->SetPixelShader(cp);d->SetTexture(1,marchTarget);
        d->SetSamplerState(1,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);d->SetSamplerState(1,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
        float cc[24][4]={};memcpy(cc[0],c[0],16);
        float size[4]={W/2,H/2,2.f/W,2.f/H};memcpy(cc[1],size,16);
        cc[2][0]=.5f/W;cc[2][1]=.5f/H;cc[2][2]=.1f;
        cc[3][0]=1.05f;cc[3][1]=2;cc[3][2]=2;cc[3][3]=1.2f;
        memcpy(cc[4],c[1],16);memcpy(cc[5],c[2],16);memcpy(cc[6],c[3],48);
        memcpy(cc[14],c[93],64);cc[18][0]=4000;cc[18][1]=1.f/6000;cc[18][2]=1;
        memcpy(cc[19],c[6],64);cc[19][3]=1;cc[23][0]=.1f;cc[23][1]=.19f;cc[23][2]=.25f;cc[23][3]=1;
        if(walker){cc[3][0]=1.1f;cc[3][3]=1;cc[18][1]=0;cc[23][3]=0;}
        Check(d->SetPixelShaderConstantF(0,&cc[0][0],24));
        d->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
        d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_SRCALPHA);d->SetRenderState(D3DRS_COLORWRITEENABLE,7);
        std::vector<DWORD> first(W*H);
        for(int sky=0;sky<2;++sky){
            Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,sky?0xffffffff:0xff000000,1,0));
            Check(d->BeginScene());Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(quad[0])));Check(d->EndScene());
            Check(d->GetRenderTargetData(back,readback));Check(readback->LockRect(&lock,nullptr,D3DLOCK_READONLY));
            int leaks=0,clipped=0;double contrast=0;
            for(int y=0;y<H;++y)for(int x=0;x<W;++x){DWORD rgb=((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x];
                if(!sky)first[y*W+x]=rgb;else {
                    if(rgb!=first[y*W+x])++leaks;
                    for(int shift:{0,8,16})contrast+=int((rgb>>shift)&255)-int((first[y*W+x]>>shift)&255);
                }
                if((rgb&255)>245 && ((rgb>>8)&255)>245 && ((rgb>>16)&255)>245)++clipped;}
            readback->UnlockRect();
            if(sky){
                printf("Case %d: transmission pixels %d; clipped white pixels %d\n",frame,leaks,clipped);
                if((!walker && leaks)||(frame<2 && clipped))return 3;
                if(walker && frame>=2){
                    const double transmission=contrast/(W*H*3.*255.);
                    printf("Black/white object contrast remaining: %.5f\n",transmission);
                    if((frame<=5 && transmission>previousTransmission+.02) || (frame>=5 && transmission>.06))return 4;
                    previousTransmission=transmission;
                }
            }
        }
        char path[160];sprintf(path,"src/obj/nebula_ice_check/%s_%d.png",walker?"walker_ice":"ice",frame);
        if(frame<2){Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,back,nullptr,nullptr));printf("Rendered %s\n",path);}
    }
    return 0;
}
