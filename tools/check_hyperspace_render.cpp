// Hidden D3D9 camera parity test and original-texture preview (not an in-game capture).
#include <windows.h>
#include <d3dx9.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void Check(HRESULT hr)
{
    if (FAILED(hr)) { std::printf("D3D9 error %08lx\n", hr); std::exit(1); }
}
static ID3DXBuffer* Compile(const char* entry, const char* profile)
{
    ID3DXBuffer *code = nullptr, *errors = nullptr;
    HRESULT hr = D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/hyperspace_tunnel.hlsl",
        nullptr, nullptr, entry, profile, 0, &code, &errors, nullptr);
    if (errors) { std::puts(static_cast<const char*>(errors->GetBufferPointer())); errors->Release(); }
    Check(hr); return code;
}
struct Vertex { float x,y,z; DWORD color; float u,v; };
static std::vector<DWORD> Read(IDirect3DDevice9* dev, IDirect3DSurface9* target)
{
    IDirect3DSurface9* cpu = nullptr;
    Check(dev->CreateOffscreenPlainSurface(960,540,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&cpu,nullptr));
    Check(dev->GetRenderTargetData(target,cpu));
    D3DLOCKED_RECT lock; Check(cpu->LockRect(&lock,nullptr,D3DLOCK_READONLY));
    std::vector<DWORD> result(960*540);
    for (int y=0;y<540;++y)
        memcpy(&result[y*960],static_cast<const char*>(lock.pBits)+y*lock.Pitch,960*4);
    cpu->UnlockRect(); cpu->Release(); return result;
}
int main()
{
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","hyperspace check",WS_POPUP,0,0,960,540,
                              nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    IDirect3D9* api=Direct3DCreate9(D3D_SDK_VERSION);
    if (!api) return 1;
    D3DPRESENT_PARAMETERS pp={}; pp.Windowed=TRUE; pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth=960; pp.BackBufferHeight=540; pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* dev=nullptr;
    Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&dev));
    IDirect3DSurface9* target=nullptr; Check(dev->GetRenderTarget(0,&target));
    ID3DXBuffer* code=Compile("VSMain","vs_3_0"); IDirect3DVertexShader9* vs=nullptr;
    Check(dev->CreateVertexShader(static_cast<const DWORD*>(code->GetBufferPointer()),&vs)); code->Release();
    code=Compile("PSMain","ps_3_0"); IDirect3DPixelShader9* ps=nullptr;
    Check(dev->CreatePixelShader(static_cast<const DWORD*>(code->GetBufferPointer()),&ps)); code->Release();
    Check(dev->SetVertexShader(vs)); Check(dev->SetPixelShader(ps));
    Check(dev->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1));
    IDirect3DVolumeTexture9* noise=nullptr;
    Check(dev->CreateVolumeTexture(32,32,32,1,0,D3DFMT_L8,D3DPOOL_MANAGED,&noise,nullptr));
    D3DLOCKED_BOX box; Check(noise->LockBox(0,&box,nullptr,0));
    unsigned rng=0x48595045;
    for(int z=0;z<32;++z) for(int y=0;y<32;++y) for(int x=0;x<32;++x)
    {
        rng^=rng<<13; rng^=rng>>17; rng^=rng<<5;
        static_cast<unsigned char*>(box.pBits)[z*box.SlicePitch+y*box.RowPitch+x]=rng>>24;
    }
    noise->UnlockBox(0); Check(dev->SetTexture(1,noise));
    IDirect3DTexture9* textures[2]={};
    Check(D3DXCreateTextureFromFileA(dev,"src/obj/jumptube.texture",&textures[0]));
    Check(D3DXCreateTextureFromFileA(dev,"src/obj/jumptube5.texture",&textures[1]));
    for(int sampler=0;sampler<2;++sampler) {
        dev->SetSamplerState(sampler,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);
        dev->SetSamplerState(sampler,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
        dev->SetSamplerState(sampler,D3DSAMP_MIPFILTER,sampler==0?D3DTEXF_LINEAR:D3DTEXF_NONE);
        for(int s=D3DSAMP_ADDRESSU;s<=D3DSAMP_ADDRESSW;++s)
            dev->SetSamplerState(sampler,static_cast<D3DSAMPLERSTATETYPE>(s),D3DTADDRESS_WRAP);
    }
    dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    dev->SetRenderState(D3DRS_ZENABLE,FALSE); dev->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
    dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);
    dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    D3DXMATRIX projection;
    D3DXMatrixPerspectiveFovLH(&projection,1.04719755f,960.f/540,1.f,10000.f);
    auto camera=[&](D3DXMATRIX const& view) {
        float c[32]={};
        for(int row=0;row<3;++row) for(int col=0;col<4;++col) c[row*4+col]=view.m[col][row];
        for(int row=0;row<4;++row) for(int col=0;col<4;++col) c[12+row*4+col]=projection.m[col][row];
        c[28]=c[29]=1.f;
        Check(dev->SetVertexShaderConstantF(0,c,8));
    };
    // Same geometry under legacy fixed-function and the production VS must occupy the
    // same pixels, including nontrivial rotation and translation (the user's regression).
    char const* white="float4 main():COLOR0{return float4(1,1,1,1);}";
    ID3DXBuffer* whiteCode=nullptr;
    Check(D3DXCompileShader(white,static_cast<UINT>(strlen(white)),nullptr,nullptr,"main","ps_3_0",0,&whiteCode,nullptr,nullptr));
    IDirect3DPixelShader9* flat=nullptr;
    Check(dev->CreatePixelShader(static_cast<const DWORD*>(whiteCode->GetBufferPointer()),&flat)); whiteCode->Release();
    Vertex marker[6]={{-90,-65,-350,0xffffffff,0,0},{70,-40,-300,0xffffffff,1,0},
        {15,80,-420,0xffffffff,0,1},{120,-60,-600,0xffffffff,0,0},
        {220,70,-640,0xffffffff,1,0},{110,100,-700,0xffffffff,0,1}};
    dev->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    dev->SetRenderState(D3DRS_LIGHTING,FALSE);
    dev->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);
    dev->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);
    dev->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
    for(int pose=0;pose<3;++pose) {
        D3DXMATRIX view,flip,identity,legacy;
        D3DXVECTOR3 eye(pose*11.f,pose*-7.f,pose*4.f),at(eye.x+pose*.1f,eye.y+pose*.04f,eye.z-1),up(0,1,0);
        D3DXMatrixLookAtRH(&view,&eye,&at,&up); D3DXMatrixScaling(&flip,1,1,-1);
        D3DXMatrixIdentity(&identity); legacy=view*flip; camera(view);
        dev->SetTransform(D3DTS_WORLD,&identity); dev->SetTransform(D3DTS_VIEW,&legacy); dev->SetTransform(D3DTS_PROJECTION,&projection);
        std::vector<DWORD> reference;
        for(int mode=0;mode<2;++mode) {
            dev->SetVertexShader(mode?vs:nullptr); dev->SetPixelShader(mode?flat:nullptr);
            Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0)); Check(dev->BeginScene());
            Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,marker,sizeof(Vertex))); Check(dev->EndScene());
            auto pixels=Read(dev,target);
            if(!mode) reference=pixels;
            else {
                unsigned differences=0,coverage=0;
                for(size_t i=0;i<pixels.size();++i) { differences+=pixels[i]!=reference[i]; coverage+=(pixels[i]&0xffffff)!=0; }
                std::printf("camera pose %d: %u differing pixels, %u covered\n",pose,differences,coverage);
                if(differences>16 || coverage<1000) return 6;
            }
        }
    }
    flat->Release(); dev->SetVertexShader(vs); dev->SetPixelShader(ps);
    // A large wall crosses the original frustum. Remapping alone would spill into bars;
    // production PS clipping must keep every pixel outside the camera rectangle untouched.
    {
        D3DXMATRIX view; D3DXMatrixIdentity(&view); camera(view);
        float remap[4]={1,.6f,0,0}; Check(dev->SetVertexShaderConstantF(7,remap,1));
        float layer[4]={0,0,0,0}; Check(dev->SetPixelShaderConstantF(0,layer,1));
        Check(dev->SetTexture(0,textures[0]));
        Vertex wall[6]={{-30,-30,-10,0xffffffff,0,0},{-30,30,-10,0xffffffff,0,1},
            {30,30,-10,0xffffffff,1,1},{-30,-30,-10,0xffffffff,0,0},
            {30,30,-10,0xffffffff,1,1},{30,-30,-10,0xffffffff,1,0}};
        Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,0xffff0000,1,0)); Check(dev->BeginScene());
        Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,wall,sizeof(Vertex))); Check(dev->EndScene());
        auto pixels=Read(dev,target); unsigned leaked=0,filled=0;
        for(int y=0;y<540;++y) for(int x=0;x<960;++x) {
            bool changed=(pixels[y*960+x]&0xffffff)!=0xff0000;
            if(y<107 || y>433) leaked+=changed;
            if(y>109 && y<431) filled+=changed;
        }
        std::printf("cinema viewport: %u leaked pixels, %u interior pixels\n",leaked,filled);
        if(leaked || filled!=321*960) return 7;
    }
    dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    std::vector<DWORD> baseline;
    for(int frame=0;frame<4;++frame)
    {
        D3DXMATRIX view; D3DXMatrixRotationY(&view,frame==3?.35f:0.f); camera(view);
        Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,0xff001800,1,0)); Check(dev->BeginScene());
        for(int shell=0;shell<2;++shell)
        {
            float layerParams[4]={static_cast<float>(shell),0,0,0};
            Check(dev->SetPixelShaderConstantF(0,layerParams,1));
            Check(dev->SetTexture(0,textures[shell]));
            dev->SetRenderState(D3DRS_SRCBLEND,shell==0?D3DBLEND_SRCALPHA:D3DBLEND_ONE);
            std::vector<Vertex> vertices;
            auto point=[&](int ring,int angular) {
                float a=angular*6.283185307f/12;
                float phaseOffset=.1f-ring*(.11f/64);
                float distance=phaseOffset*20000.f;
                float radius=80.f*(shell==0?1.5f:1.f)*(1.f-fminf(1.f,fabsf(phaseOffset)/.11f));
                float fade=powf(fminf(1.f,ring/64.f+.05f)*(shell==0?.8f:1.f),3);
                float time=frame==2?4.f:3.f;
                DWORD colour=(static_cast<DWORD>(fade*255)<<24)|(shell==0?0x649664:0x64ff64);
                return Vertex{radius*cosf(a),radius*sinf(a),-distance,colour,
                    angular/12.f+(shell==0?time*.1f:.5f-time*.2f),
                    (.5f+phaseOffset)*(shell==0?10.f:15.f)+(shell==0?time*.07f:.33f+time*.1f)};
            };
            for(int ring=0;ring<64;++ring) for(int angular=0;angular<12;++angular)
            {
                Vertex a=point(ring,angular), b=point(ring+1,angular);
                Vertex c=point(ring,angular+1), d=point(ring+1,angular+1);
                vertices.insert(vertices.end(),{a,b,c,c,b,d});
            }
            Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,static_cast<UINT>(vertices.size()/3),vertices.data(),sizeof(Vertex)));
        }
        Check(dev->EndScene());
        auto pixels=Read(dev,target);
        unsigned bright=0,white=0; double energy=0;
        for(DWORD px:pixels) {
            unsigned r=(px>>16)&255,g=(px>>8)&255,b=px&255;
            energy+=r+g+b; bright+=(r+g+b)>90; white+=(r>245&&g>245&&b>245);
        }
        std::printf("frame %d: mean channel %.2f, lit %u, clipped white %u\n",frame,energy/(pixels.size()*3),bright,white);
        if(bright<pixels.size()/100 || white>pixels.size()/4) return 2;
        if(frame==0) baseline=pixels;
        if(frame==1 && pixels!=baseline) { std::puts("Static frame is unstable"); return 3; }
        if(frame>=2 && pixels==baseline) { std::puts("Time/camera has no effect"); return 4; }
        if(frame!=1) {
            char path[128]; sprintf_s(path,"src/obj/hyperspace_preview_%d.png",frame);
            Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,target,nullptr,nullptr));
        }
    }
    // The cloud material must transmit the underlying tunnel and follow its palette.
    {
        D3DXMATRIX view; D3DXMatrixIdentity(&view); camera(view);
        Check(dev->SetVertexShader(vs)); Check(dev->SetPixelShader(ps));
        dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);
        dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
        float layer[4]={0,0,0,0}; Check(dev->SetPixelShaderConstantF(0,layer,1));
        Vertex wall[6]={{-30,-30,-10,0xffffffff,0,0},{-30,30,-10,0xffffffff,0,1},
            {30,30,-10,0xffffffff,1,1},{-30,-30,-10,0xffffffff,0,0},
            {30,30,-10,0xffffffff,1,1},{30,-30,-10,0xffffffff,1,0}};
        DWORD tints[]={0xffff2020,0xff20ff20,0xff2020ff};
        for(int tint=0;tint<3;++tint) {
            std::vector<DWORD> dark;
            for(auto& vertex:wall) vertex.color=tints[tint];
            for(int background=0;background<2;++background) {
                Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,background?0xff404040:0xff000000,1,0));
                Check(dev->BeginScene()); Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,wall,sizeof(Vertex))); Check(dev->EndScene());
                auto pixels=Read(dev,target); double channels[3]={},transmission=0;
                for(size_t i=0;i<pixels.size();++i) for(int channel=0;channel<3;++channel) {
                    int shift=16-channel*8; int value=(pixels[i]>>shift)&255;
                    channels[channel]+=value;
                    if(background) transmission+=value-int((dark[i]>>shift)&255);
                }
                if(!background) {
                    dark=pixels;
                    if(channels[tint]<2*channels[(tint+1)%3] || channels[tint]<2*channels[(tint+2)%3]) return 12;
                } else {
                    double pass=transmission/(pixels.size()*3*64);
                    std::printf("palette %d: background transmission %.3f\n",tint,pass);
                    if(pass<.50 || pass>.60) return 13;
                }
            }
        }
    }
    // Entry shader uses no textures; verify inactive endpoints, repeatability,
    // visible buildup/burst, recession, and clipping to the cinematic viewport.
    {
        code=Compile("VSLaunch","vs_3_0"); IDirect3DVertexShader9* launchVS=nullptr;
        Check(dev->CreateVertexShader(static_cast<const DWORD*>(code->GetBufferPointer()),&launchVS)); code->Release();
        code=Compile("PSLaunch","ps_3_0"); IDirect3DPixelShader9* launchPS=nullptr;
        Check(dev->CreatePixelShader(static_cast<const DWORD*>(code->GetBufferPointer()),&launchPS)); code->Release();
        Check(dev->SetVertexShader(launchVS)); Check(dev->SetPixelShader(launchPS));
        dev->SetTexture(0,nullptr); dev->SetTexture(1,nullptr);
        dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA); dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_ONE);
        float remap[4]={1,.6f,0,0}; Check(dev->SetVertexShaderConstantF(7,remap,1));
        Vertex quad[6]={{-1,-1,0,0xffffffff,0,1},{-1,1,0,0xffffffff,0,0},
            {1,1,0,0xffffffff,1,0},{-1,-1,0,0xffffffff,0,1},
            {1,1,0,0xffffffff,1,0},{1,-1,0,0xffffffff,1,1}};
        float style[4]={0,1,1,1}; Check(dev->SetPixelShaderConstantF(1,style,1));
        float phases[][4]={{0,0,960.f/324,0},{.55f,0,960.f/324,0},
            {.96f,.8f,960.f/324,0},{1,1,960.f/324,0},
            {1,.5f,960.f/324,.5f},{1,0,960.f/324,1}, {.96f,.8f,960.f/324,0}};
        double energies[7]={}; std::vector<DWORD> repeat;
        for(int phase=0;phase<7;++phase) {
            Check(dev->SetPixelShaderConstantF(0,phases[phase],1));
            Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0)); Check(dev->BeginScene());
            Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,quad,sizeof(Vertex))); Check(dev->EndScene());
            auto pixels=Read(dev,target); unsigned count=0, leaked=0,white=0;
            for(int y=0;y<540;++y) for(int x=0;x<960;++x) {
                DWORD pixel=pixels[y*960+x]; bool lit=(pixel&0xffffff)!=0;
                count+=lit; if(y<107 || y>433) leaked+=lit;
                unsigned r=(pixel>>16)&255,g=(pixel>>8)&255,b=pixel&255;
                energies[phase]+=r+g+b; white+=r>245&&g>245&&b>245;
            }
            std::printf("entry phase %d: %u lit, %u leaked, %u white, energy %.0f\n",phase,count,leaked,white,energies[phase]);
            if(leaked || white>pixels.size()/20) return 8;
            if((phase==0 || phase==5) ? count!=0 : count<500) return 9;
            if(phase==2) repeat=pixels;
            if(phase==6 && pixels!=repeat) return 10;
            if(phase>0 && phase<5) {
                char path[128]; sprintf_s(path,"src/obj/hyperspace_entry_%d.png",phase);
                Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,target,nullptr,nullptr));
            }
        }
        if(energies[2]<=energies[1] || energies[3]<energies[2] || energies[4]>=energies[3]) return 11;
        // Stars are visible at 3% of jump-out, where the old delayed buildup was absent.
        {
            float early[4]={.03f,0,960.f/324,0}; Check(dev->SetPixelShaderConstantF(0,early,1));
            Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0)); Check(dev->BeginScene());
            Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,quad,sizeof(Vertex))); Check(dev->EndScene());
            auto pixels=Read(dev,target); unsigned count=0;
            for(auto pixel:pixels) count+=(pixel&0xffffff)!=0;
            std::printf("early jump stars: %u lit pixels\n",count);
            if(count<100) return 14;
        }
        style[0]=1; style[1]=.3f; style[2]=.7f; style[3]=1;
        Check(dev->SetPixelShaderConstantF(1,style,1));
        double previousRadius=0;
        for(int phase=0;phase<6;++phase) {
            float progress[]={0,.08f,.3f,.6f,.9f,1};
            float exitParams[4]={progress[phase],0,960.f/324,0};
            Check(dev->SetPixelShaderConstantF(0,exitParams,1));
            Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET,0xff000000,1,0)); Check(dev->BeginScene());
            Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,quad,sizeof(Vertex))); Check(dev->EndScene());
            auto pixels=Read(dev,target); unsigned count=0,leaked=0,white=0;
            double energy=0,weightedRadius=0;
            for(int y=0;y<540;++y) for(int x=0;x<960;++x) {
                DWORD pixel=pixels[y*960+x]; bool lit=(pixel&0xffffff)!=0; count+=lit;
                if(y<107 || y>433) leaked+=lit;
                unsigned r=(pixel>>16)&255,g=(pixel>>8)&255,b=pixel&255;
                white+=r>245&&g>245&&b>245;
                double radius=std::sqrt(double((x-480)*(x-480)+(y-270)*(y-270)))/324;
                energy+=r+g+b; weightedRadius+=radius*(r+g+b);
            }
            double radius=energy>0?weightedRadius/energy:0;
            std::printf("exit phase %.2f: %u lit, %u leaked, %u white, mean radius %.3f\n",progress[phase],count,leaked,white,radius);
            if(leaked || white>pixels.size()/20) return 15;
            if((phase==0 || phase==5) ? count!=0 : count<100) return 16;
            if(phase>0 && phase<5) {
                if(radius<=previousRadius) return 17;
                previousRadius=radius;
                char path[128]; sprintf_s(path,"src/obj/hyperspace_exit_%d.png",phase);
                Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,target,nullptr,nullptr));
            }
        }
        launchPS->Release(); launchVS->Release();
    }
    std::puts("PASS: legacy camera parity, cinematic clipping, clouds, early stars and entry/exit lifecycles.");
    textures[0]->Release(); textures[1]->Release();
    noise->Release(); ps->Release(); vs->Release(); target->Release(); dev->Release(); api->Release();
    DestroyWindow(window); return 0;
}
