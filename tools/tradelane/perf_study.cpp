// Offline cost study. No game installation or game process required.
#define main ExistingTradeLaneChecks
#include "../check_tradelane_render.cpp"
#undef main
#include "../../src/freelancer/Client/jump_cloud_path.h"
#include <functional>

static double Measure(std::function<void()> draw) {
    IDirect3DQuery9 *a=nullptr,*b=nullptr,*f=nullptr,*d=nullptr;
    Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&a));Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&b));
    Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&f));Check(Dev->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&d));
    for(int i=0;i<12;++i)draw();
    std::vector<double> times;
    for(int n=0;n<5;++n){
        Check(d->Issue(D3DISSUE_BEGIN));Check(f->Issue(D3DISSUE_END));Check(a->Issue(D3DISSUE_END));
        for(int i=0;i<16;++i)draw();
        Check(b->Issue(D3DISSUE_END));Check(d->Issue(D3DISSUE_END));
        UINT64 x,y,freq;BOOL disjoint;Query(a,x);Query(b,y);Query(f,freq);Query(d,disjoint);
        if(!disjoint&&freq)times.push_back(double(y-x)*1e3/double(freq)/16);
    }
    Require(!times.empty(),"GPU timestamps valid");std::sort(times.begin(),times.end());
    Release(a);Release(b);Release(f);Release(d);return times[times.size()/2];
}
static std::vector<unsigned char> CloudCode(const char* path,const char* entry,const char* profile){
    std::ifstream file(path,std::ios::binary);std::string source((std::istreambuf_iterator<char>(file)),{});
    source="#line 1 \"SHADERS/jump_cloud.hlsl\"\n"+source;
    std::vector<unsigned char> bytes;std::string errors;bool hit=false,stored=false;
    HRESULT hr=Rp9ShaderCache::Compile(source,nullptr,entry,profile,Rp9ShaderCache::FlagsForSource(source),&bytes,&errors,&hit,&stored,true);
    if(!errors.empty())puts(errors.c_str());Check(hr);return bytes;
}
int main(int argc,char**argv){
    if(argc!=6)return 1; // kind, shader, internal width, internal height, output folder
    bool jump=strcmp(argv[1],"jump")==0;
    Out=argv[5];ShaderSource=argv[2];int width=atoi(argv[3]),height=atoi(argv[4]);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","Tunnel cost study",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 2;
    D3DADAPTER_IDENTIFIER9 adapter;Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s\n",adapter.Description);
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=64;pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&Dev));
    Dev->SetRenderState(D3DRS_ZENABLE,FALSE);Dev->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
    Dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);Dev->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);
    Dev->SetRenderState(D3DRS_LIGHTING,FALSE);Dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
    Dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);Dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
    if(!jump){
        Compile();CreateNoise();Size(width,height);WarpEnabled=false;Beauty=true;
        Mesh.resize(TradeLaneVertexCount);BuildTradeLaneVisualMesh(Mesh.data());
        Check(Dev->CreateVertexBuffer(UINT(Mesh.size()*sizeof(Vertex)),D3DUSAGE_WRITEONLY,0,D3DPOOL_MANAGED,&VB,nullptr));
        void* vertices=nullptr;Check(VB->Lock(0,0,&vertices,0));memcpy(vertices,Mesh.data(),Mesh.size()*sizeof(Vertex));Check(VB->Unlock());
        Camera();DepthTexture(false,false);Style=ConfigStyle(4);
        for(float t:{0.5f,3.f,8.f,15.f,30.f}){
            Params(t*.9f,1,0,t);
            double ms=Measure([](){Check(Dev->BeginScene());Draw();Check(Dev->EndScene());});
            printf("RESULT lane %.1f %dx%d %.6f ms\n",t,width,height,ms);fflush(stdout);
        }
        Params(2.25f,1,0,2.5f);Render("preview",true);
    }else{
        auto code=CloudCode(argv[2],"VSMain","vs_3_0");Check(Dev->CreateVertexShader((DWORD*)code.data(),&VS));
        code=CloudCode(argv[2],"PSMain","ps_3_0");Check(Dev->CreatePixelShader((DWORD*)code.data(),&PS));
        IDirect3DVertexShader9* compositeVS=nullptr;IDirect3DPixelShader9* compositePS=nullptr;
        code=CloudCode(argv[2],"VSComposite","vs_3_0");Check(Dev->CreateVertexShader((DWORD*)code.data(),&compositeVS));
        code=CloudCode(argv[2],"PSComposite","ps_3_0");Check(Dev->CreatePixelShader((DWORD*)code.data(),&compositePS));
        IDirect3DTexture9 *modulation=nullptr,*path=nullptr,*cloud=nullptr;
        Check(D3DXCreateTextureFromFileA(Dev,"DATA_EXTRA/FX/JUMP_CLOUD/modulation.png",&modulation));
        Check(D3DXCreateTextureFromFileA(Dev,"DATA_EXTRA/FX/JUMP_CLOUD/path.dds",&path));
        Check(Dev->CreateTexture(width,height,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&cloud,nullptr));
        IDirect3DSurface9 *cloudSurface=nullptr;Check(cloud->GetSurfaceLevel(0,&cloudSurface));
        Check(Dev->CreateRenderTarget(1920,1080,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&Target,nullptr));
        Check(Dev->SetDepthStencilSurface(nullptr));
        Check(Dev->CreateVolumeTexture(32,32,32,1,0,D3DFMT_L8,D3DPOOL_MANAGED,&Noise,nullptr));
        D3DLOCKED_BOX box;Check(Noise->LockBox(0,&box,nullptr,0));unsigned seed=0x48595045;
        for(int z=0;z<32;++z)for(int y=0;y<32;++y)for(int x=0;x<32;++x){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;((unsigned char*)box.pBits)[z*box.SlicePitch+y*box.RowPitch+x]=seed>>24;}
        Check(Noise->UnlockBox(0));
        for(int s=0;s<3;++s){
            Dev->SetSamplerState(s,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);Dev->SetSamplerState(s,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
            Dev->SetSamplerState(s,D3DSAMP_MIPFILTER,s==0?D3DTEXF_LINEAR:D3DTEXF_NONE);
            Dev->SetSamplerState(s,D3DSAMP_ADDRESSU,s==2?D3DTADDRESS_CLAMP:D3DTADDRESS_WRAP);
            Dev->SetSamplerState(s,D3DSAMP_ADDRESSV,s==2?D3DTADDRESS_CLAMP:D3DTADDRESS_WRAP);
            Dev->SetSamplerState(s,D3DSAMP_ADDRESSW,D3DTADDRESS_WRAP);
        }
        const Vertex quad[]={{{-1,1,0},0xffffffff,{0,0}},{{1,1,0},0xffffffff,{1,0}},{{-1,-1,0},0xffffffff,{0,1}},{{1,-1,0},0xffffffff,{1,1}}};
        float remap[4]={1,1,0,0};Dev->SetVertexShaderConstantF(7,remap,1);
        Dev->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1);Dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
        auto draw=[&](){
            Check(Dev->BeginScene());Dev->SetTexture(0,nullptr);Check(Dev->SetRenderTarget(0,cloudSurface));
            Dev->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_WRAP);Dev->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_WRAP);
            Dev->SetSamplerState(0,D3DSAMP_MIPFILTER,D3DTEXF_LINEAR);
            Dev->SetVertexShader(VS);Dev->SetPixelShader(PS);Dev->SetTexture(0,modulation);Dev->SetTexture(1,Noise);Dev->SetTexture(2,path);
            Check(Dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Vertex)));
            Check(Dev->SetRenderTarget(0,Target));Dev->SetVertexShader(compositeVS);Dev->SetPixelShader(compositePS);Dev->SetTexture(0,cloud);
            Dev->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Dev->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
            Dev->SetSamplerState(0,D3DSAMP_MIPFILTER,D3DTEXF_NONE);
            Check(Dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Vertex)));Check(Dev->EndScene());
        };
        for(float t:{0.5f,3.f,8.f,15.f,30.f}){
            float a[4]={0,3+t*JumpCloud::MaterialSpeed,3,2},travel[4]={3+t*JumpCloud::TravelSpeed,0,0,0};
            float frame[16];JumpCloud::Camera(travel[0]*2.6f,frame);
            float view[4]={1920.f/1080,1.1547005f,0,0},palette[8]={0,0,200.f/255,0,100.f/255,200.f/255,1,0};
            Dev->SetPixelShaderConstantF(0,a,1);Dev->SetPixelShaderConstantF(1,travel,1);Dev->SetPixelShaderConstantF(2,frame,4);
            Dev->SetPixelShaderConstantF(6,view,1);Dev->SetPixelShaderConstantF(7,palette,2);
            double ms=Measure(draw);printf("RESULT jump %.1f %dx%d %.6f ms\n",t,width,height,ms);fflush(stdout);
            if(t==3.f){std::string filename=std::string(Out)+"preview.png";Check(D3DXSaveSurfaceToFileA(filename.c_str(),D3DXIFF_PNG,Target,nullptr,nullptr));}
        }
    }
    // One process per variant: the OS releases the isolated D3D device/resources.
    return 0;
}
