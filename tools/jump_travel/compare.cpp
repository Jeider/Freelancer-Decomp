// Material comparison on a shared test path, NOT a capture of the running game.
#define NOMINMAX
#define main ExistingHyperspaceChecks
#include "../check_hyperspace_render.cpp"
#undef main
#include <io.h>
#include <fcntl.h>
#include <fstream>
#include "classic_mesh.h"
#include "../../src/freelancer/Client/jump_cloud_path.h"
#include "../../src/RP9/RP9ShaderCache.h"

static ID3DXBuffer* CompileCloud(char const* entry,char const* profile,bool diagnostic=false){
    std::ifstream file("DATA_EXTRA/SHADERS/jump_cloud.hlsl",std::ios::binary);
    std::string source((std::istreambuf_iterator<char>(file)),{});
    if(source.empty()){fprintf(stderr,"Missing cloud shader\n");exit(14);}
    // Exact game preprocessing/flags and compiler identity. The GPU check also
    // prepares the persistent game cache before installation, avoiding a long
    // first-load compile after every art edit. No preview-only defines normally.
    source="#line 1 \"SHADERS/jump_cloud.hlsl\"\n"+source;
    if(diagnostic)source="#define JUMP_CLOUD_DIAGNOSTIC 1\n"+source;
    std::vector<unsigned char> bytes,verified;std::string errors;bool hit=false,stored=false;
    DWORD flags=Rp9ShaderCache::FlagsForSource(source);
    HRESULT hr=Rp9ShaderCache::Compile(source,nullptr,entry,profile,flags,&bytes,&errors,&hit,&stored,true);
    if(!errors.empty())fprintf(stderr,"%s",errors.c_str());Check(hr);
    bool secondHit=false;
    Check(Rp9ShaderCache::Compile(source,nullptr,entry,profile,flags,&verified,&errors,&secondHit,&stored,true));
    if(!secondHit||verified!=bytes){fprintf(stderr,"FAIL: cloud disk cache reload\n");exit(15);}
    fprintf(stderr,"PASS: game shader cache %s %s, reload HIT\n",entry,hit?"HIT":"stored");
    ID3DXBuffer* result=nullptr;Check(D3DXCreateBuffer(static_cast<DWORD>(bytes.size()),&result));
    memcpy(result->GetBufferPointer(),bytes.data(),bytes.size());return result;
}

static std::vector<Vertex> Wall(int layer,float time) {
    std::vector<Vertex> result;
    float start=.6f,end=.49f,span=.11f,step=-1.f/200;
    auto point=[&](float t,int angle) {
        float f=fminf(1,fabsf(t-.5f)/span),s=(t-.5f)/.1f;
        float radius=(75+20*sinf(t*19+time*.2f))*(layer?1:1.5f)*(1-f);
        float alpha=powf(fminf(1,fabsf(t-start)/span+.05f)*(layer?1:.8f),3);
        float bend=.7f+.25f*sinf(time*.21f);
        float x=130*(1-cosf(s*1.4f))*bend,y=60*s*s*sinf(s+time*.13f);
        float a=angle*6.283185307f/12;
        DWORD rgb=layer?D3DCOLOR_XRGB(0,150,191):D3DCOLOR_XRGB(0,0,150);
        return Vertex{x+radius*cosf(a),y+radius*sinf(a),-s*2000,
            (DWORD(alpha*255)<<24)|(rgb&0xffffff),angle/12.f+(layer?.5f-time*.2f:time*.1f),
            t*(layer?15:10)+(layer?.33f+time*.1f:time*.07f)};
    };
    for(float t=start;t>end;) {
        step*=1.1f;float next=fmaxf(end,t+step);
        for(int a=0;a<12;++a){Vertex p=point(t,a),q=point(next,a),r=point(t,a+1),s=point(next,a+1);result.insert(result.end(),{p,q,r,r,q,s});}
        t+=step;
    }
    return result;
}
int main(int argc,char** argv) {
    bool diagnostic=false;
    for(int i=1;i<argc;++i)diagnostic|=strcmp(argv[i],"--cloud-diagnostic")==0;
    bool video=false,classic=false,solo=false,energy=false,matter=false,matterFast=false,matterTextured=false,matterParallax=false,matterLight=false,cloudReference=false;
    for(int i=1;i<argc;++i){video|=strcmp(argv[i],"--video")==0;classic|=strcmp(argv[i],"--classic")==0;solo|=strcmp(argv[i],"--solo")==0;energy|=strcmp(argv[i],"--energy")==0;}
    for(int i=1;i<argc;++i)matter|=strcmp(argv[i],"--matter")==0;
    for(int i=1;i<argc;++i)matterFast|=strcmp(argv[i],"--matter-fast")==0;
    for(int i=1;i<argc;++i)matterTextured|=strcmp(argv[i],"--matter-textured")==0;
    for(int i=1;i<argc;++i)matterParallax|=strcmp(argv[i],"--matter-parallax")==0;
    for(int i=1;i<argc;++i)matterLight|=strcmp(argv[i],"--matter-light")==0;
    for(int i=1;i<argc;++i)cloudReference|=strcmp(argv[i],"--cloud-reference")==0;
    matterParallax|=matterLight||cloudReference;
    matter|=matterFast||matterTextured||matterParallax;
    energy|=matter;classic|=energy;
    if(video)_setmode(_fileno(stdout),_O_BINARY);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    HWND window=CreateWindowA("STATIC","Tunnel material comparison",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
    auto* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 1;
    D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=960;pp.BackBufferHeight=540;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
    IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
    IDirect3DSurface9* target=nullptr;Check(d->GetRenderTarget(0,&target));
    auto* code=Compile("VSMain","vs_3_0");IDirect3DVertexShader9* vs=nullptr;Check(d->CreateVertexShader((DWORD*)code->GetBufferPointer(),&vs));code->Release();
    code=Compile("PSMain","ps_3_0");IDirect3DPixelShader9* cloud=nullptr;Check(d->CreatePixelShader((DWORD*)code->GetBufferPointer(),&cloud));code->Release();
    IDirect3DVertexShader9* energyVS=nullptr;IDirect3DPixelShader9* energyPS=nullptr;
    if(energy){
        for(int stage=0;stage<2;++stage){ID3DXBuffer* errors=nullptr;
            const D3DXMACRO defines[]={{"MATTER_PARALLAX","1"},{"MATTER_LIGHT",matterLight?"1":"0"},{"JUMP_CLOUD_DIAGNOSTIC",diagnostic?"1":"0"},{nullptr,nullptr}};
            HRESULT hr=S_OK;
            if(cloudReference)code=CompileCloud(stage?"PSMain":"VSMain",stage?"ps_3_0":"vs_3_0",diagnostic);
            else hr=D3DXCompileShaderFromFileA(matter?"tools/jump_travel/matter_tunnel.hlsl":"tools/jump_travel/energy_tunnel.hlsl",matterParallax?defines:nullptr,nullptr,stage?"PSMain":"VSMain",stage?"ps_3_0":"vs_3_0",D3DXSHADER_OPTIMIZATION_LEVEL3,&code,&errors,nullptr);
            if(errors){fprintf(stderr,"%s",(char*)errors->GetBufferPointer());errors->Release();}Check(hr);
            if(stage)Check(d->CreatePixelShader((DWORD*)code->GetBufferPointer(),&energyPS));else Check(d->CreateVertexShader((DWORD*)code->GetBufferPointer(),&energyVS));code->Release();}
    }
    const char* base="sampler2D T:register(s0);float4 main(float4 C:COLOR0,float2 UV:TEXCOORD0):COLOR0{return tex2D(T,UV)*C;}";
    Check(D3DXCompileShader(base,UINT(strlen(base)),nullptr,nullptr,"main","ps_3_0",0,&code,nullptr,nullptr));IDirect3DPixelShader9* original=nullptr;Check(d->CreatePixelShader((DWORD*)code->GetBufferPointer(),&original));code->Release();
    IDirect3DTexture9* textures[2];Check(D3DXCreateTextureFromFileA(d,"out/jump_travel/comparison/jumptube.dds",&textures[0]));Check(D3DXCreateTextureFromFileA(d,"out/jump_travel/comparison/jumptube5.dds",&textures[1]));
    IDirect3DTexture9* modulation=nullptr;
    if(cloudReference)Check(D3DXCreateTextureFromFileA(d,"DATA_EXTRA/FX/JUMP_CLOUD/modulation.png",&modulation));
    IDirect3DTexture9* splinePath=nullptr;
    if(cloudReference){
        Check(D3DXCreateTextureFromFileA(d,"DATA_EXTRA/FX/JUMP_CLOUD/path.dds",&splinePath));
        d->SetSamplerState(2,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);d->SetSamplerState(2,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    }
    IDirect3DVolumeTexture9* noise=nullptr;Check(d->CreateVolumeTexture(32,32,32,1,0,D3DFMT_L8,D3DPOOL_MANAGED,&noise,nullptr));D3DLOCKED_BOX box;Check(noise->LockBox(0,&box,nullptr,0));
    unsigned seed=0x48595045;for(int z=0;z<32;++z)for(int y=0;y<32;++y)for(int x=0;x<32;++x){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;((unsigned char*)box.pBits)[z*box.SlicePitch+y*box.RowPitch+x]=seed>>24;}noise->UnlockBox(0);
    D3DXMATRIX proj;D3DXMatrixPerspectiveFovLH(&proj,1.04719755f,960.f/540,1,10000);
    float vc[32]={};vc[0]=vc[5]=vc[10]=1;vc[28]=vc[29]=1;for(int r=0;r<4;++r)for(int c=0;c<4;++c)vc[12+r*4+c]=proj.m[c][r];
    d->SetVertexShader(vs);d->SetVertexShaderConstantF(0,vc,8);d->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1);d->SetTexture(1,noise);
    d->SetRenderState(D3DRS_ZENABLE,FALSE);d->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
    d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);d->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);
    for(int s=0;s<3;++s){d->SetSamplerState(s,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);d->SetSamplerState(s,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);d->SetSamplerState(s,D3DSAMP_MIPFILTER,s==1?D3DTEXF_NONE:D3DTEXF_LINEAR);}
    std::vector<Vertex> classicWalls[2];std::vector<DWORD> frozenFrame;
    if(cloudReference){
        float previous[4]={},low=1,high=-1;
        for(int i=0;i<1200;++i){
            float z=(3+i/60.f*JumpCloud::TravelSpeed)*2.6f,frame[16],destination[4];
            JumpCloud::Camera(z,frame);JumpCloud::Destination(z,frame,destination);
            if(!std::isfinite(destination[0])||!std::isfinite(destination[1])||fabsf(destination[0])>.4f||fabsf(destination[1])>.4f)return 9;
            // Stronger authored turns remain continuous: under 0.7 degrees/frame.
            if(i&&(fabsf(destination[0]-previous[0])>.012f||fabsf(destination[1]-previous[1])>.012f))return 10;
            low=fminf(low,destination[0]);high=fmaxf(high,destination[0]);
            memcpy(previous,destination,sizeof(previous));
        }
        if(high-low<.06f)return 11;
        fprintf(stderr,"PASS: visible continuous bends, destination horizontal span %.3f (20 seconds)\n",high-low);
    }
    for(int frame=0;frame<(video?480:cloudReference?4:energy?3:1);++frame){float time=3+(video?frame:frame==2?1:0)/60.f;std::vector<DWORD> halves[2];auto walls0=Wall(0,time),walls1=Wall(1,time);
        if(classic){ClassicTravel::Build(classicWalls[0],0,time);ClassicTravel::Build(classicWalls[1],1,time);}
        if(energy)for(int l=0;l<2;++l)for(auto& v:classicWalls[l]){
            // Recover unscrolled cylindrical coordinates; the new material owns
            // its motion and does not sample either of the old tunnel textures.
            v.u-=l?.5f-time*.2f:time*.1f;
            v.v=((v.v-(l?.33f+time*.1f:time*.07f))/(l?15:10)-.5f)*25;
        }
        for(int mode=0;mode<2;++mode){Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0xff00001a,1,0));Check(d->BeginScene());
            d->SetVertexShader(energy&&mode?energyVS:vs);
            if(matter&&mode){
                Vertex quad[6]={{-1,1,0,0xffffffff,0,0},{1,1,0,0xffffffff,1,0},{-1,-1,0,0xffffffff,0,1},{-1,-1,0,0xffffffff,0,1},{1,1,0,0xffffffff,1,0},{1,-1,0,0xffffffff,1,1}};
                // Same starting pose, exact simulation speed multiplier; every
                // output frame is rendered afresh at 60 Hz (no video retiming).
                float speed=cloudReference?JumpCloud::MaterialSpeed:matterParallax?8.f:matterTextured?4.f:matterFast?2.f:1.f;
                float p[4]={0,3+(time-3)*speed,matterParallax?3.f:matterTextured?2.f:matterFast?1.f:0.f,matterParallax?2.f:1.f};d->SetPixelShaderConstantF(0,p,1);d->SetPixelShader(energyPS);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
                // Prove cloud deformation still advances with camera locked.
                if(cloudReference&&!video&&frame==3){p[1]+=2;d->SetPixelShaderConstantF(0,p,1);}
                // User slowed only camera travel by 30%; material advection and
                // deformation retain their previous rates, independently.
                float travelParams[4]={3+(time-3)*(cloudReference?JumpCloud::TravelSpeed:matterParallax?8.f*.7f:speed),0,0,0};d->SetPixelShaderConstantF(1,travelParams,1);
                if(cloudReference){
                    float z=travelParams[0]*2.6f;
                    float camera[16];JumpCloud::Camera(z,camera);
                    Check(d->SetPixelShaderConstantF(2,camera,4));
                    float view[4]={960.f/540,1.1547005f,0,0};Check(d->SetPixelShaderConstantF(6,view,1));
                    float palette[8]={0,0,200.f/255,0,100.f/255,200.f/255,1,0};Check(d->SetPixelShaderConstantF(7,palette,2));
                    float destination[4];JumpCloud::Destination(z,camera,destination);Check(d->SetPixelShaderConstantF(9,destination,1));
                }
                d->SetTexture(0,cloudReference?modulation:textures[1]);d->SetTexture(2,cloudReference?splinePath:textures[0]);
                Check(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,quad,sizeof(Vertex)));d->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);
            }else for(int pass=0;pass<=(classic?0:mode);++pass){d->SetPixelShader(energy&&mode?energyPS:(pass?cloud:original));
                for(int l=0;l<2;++l){auto const& wall=classic&&mode?classicWalls[l]:(l?walls1:walls0);float p[4]={float(l),time,0,0};d->SetPixelShaderConstantF(0,p,1);d->SetTexture(0,textures[l]);d->SetRenderState(D3DRS_SRCBLEND,l?D3DBLEND_ONE:D3DBLEND_SRCALPHA);Check(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(wall.size()/3),wall.data(),sizeof(Vertex)));}}
            Check(d->EndScene());halves[mode]=Read(d,target);
            if(!video&&frame==0){
                const char* directory=cloudReference?"cloud_reference":matterLight?"matter_light":matterParallax?"matter_parallax":matterTextured?"matter_textured":matterFast?"matter_fast":matter?"matter":energy?"energy":classic?"classic":"comparison";
                char filename[256];snprintf(filename,sizeof(filename),"out/jump_travel/%s/%s.png",directory,mode?(classic?"new":"current"):"base");
                Check(D3DXSaveSurfaceToFileA(filename,D3DXIFF_PNG,target,nullptr,nullptr));
            }
        }
        if(energy&&!video){
            if(frame==0)frozenFrame=halves[1];
            if(frame==1&&frozenFrame!=halves[1]){fprintf(stderr,"FAIL: paused time changed image\n");return 2;}
            if(frame==2&&frozenFrame==halves[1]){fprintf(stderr,"FAIL: advancing time did not animate\n");return 3;}
            if(frame==2)fprintf(stderr,"PASS: paused frame pixel-identical; advancing simulation time animates\n");
            if(frame==3&&frozenFrame==halves[1]){fprintf(stderr,"FAIL: clouds frozen with camera locked\n");return 4;}
            if(frame==3)fprintf(stderr,"PASS: cloud shape changes independently with fixed camera\n");
        }
        if(video)for(int y=0;y<540;++y){if(!solo)fwrite(halves[0].data()+y*960,4,960,stdout);fwrite(halves[1].data()+y*960,4,960,stdout);}
    }
    if(cloudReference&&!video&&!diagnostic){
        // Exercise the game's half-resolution pass and viewport compositor with
        // the shipped shader/assets. Preserve borders and draw foreground after it.
        IDirect3DVertexShader9* compositeVS=nullptr;IDirect3DPixelShader9* compositePS=nullptr;
        for(int stage=0;stage<2;++stage){ID3DXBuffer* errors=nullptr;
            code=CompileCloud(stage?"PSComposite":"VSComposite",stage?"ps_3_0":"vs_3_0");
            HRESULT hr=S_OK;
            if(errors){fprintf(stderr,"%s",(char*)errors->GetBufferPointer());errors->Release();}Check(hr);
            if(stage)Check(d->CreatePixelShader((DWORD*)code->GetBufferPointer(),&compositePS));
            else Check(d->CreateVertexShader((DWORD*)code->GetBufferPointer(),&compositeVS));code->Release();
        }
        IDirect3DTexture9* half=nullptr;IDirect3DSurface9* halfSurface=nullptr;
        Check(d->CreateTexture(480,270,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&half,nullptr));
        Check(half->GetSurfaceLevel(0,&halfSurface));
        Vertex quad[4]={{-1,1,0,0xffffffff,0,0},{1,1,0,0xffffffff,1,0},
            {-1,-1,0,0xffffffff,0,1},{1,-1,0,0xffffffff,1,1}};
        Check(d->SetRenderTarget(0,halfSurface));Check(d->BeginScene());
        d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
        d->SetVertexShader(energyVS);d->SetPixelShader(energyPS);
        d->SetTexture(0,modulation);d->SetTexture(1,noise);d->SetTexture(2,splinePath);
        Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Vertex)));
        Check(d->SetRenderTarget(0,target));
        const DWORD sentinel=0xff79003b;
        Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,sentinel,1,0));
        d->SetVertexShader(compositeVS);d->SetPixelShader(compositePS);d->SetTexture(0,half);
        d->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);d->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
        float remap[4]={.75f,.75f,0,0};Check(d->SetVertexShaderConstantF(7,remap,1));
        Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Vertex)));Check(d->EndScene());
        auto composite=Read(d,target);size_t changed=0;
        for(int y=0;y<540;++y)for(int x=0;x<960;++x){
            bool border=x<118||x>842||y<65||y>474;
            if(border&&composite[y*960+x]!=sentinel){fprintf(stderr,"FAIL: composite touched viewport border\n");return 6;}
            if(!border&&composite[y*960+x]!=sentinel)++changed;
        }
        if(changed<280000){fprintf(stderr,"FAIL: cloud composite missing\n");return 7;}
        Check(D3DXSaveSurfaceToFileA("out/jump_travel/cloud_reference/game_composite.png",D3DXIFF_PNG,target,nullptr,nullptr));
        // Stand-in for a subsequent native ship draw. Its pixels must stay sharp
        // and must not be replaced by another full-screen cloud composite.
        D3DRECT marker={450,370,510,400};Check(d->Clear(1,&marker,D3DCLEAR_TARGET,0xff00ff00,1,0));
        auto foreground=Read(d,target);
        for(int y=370;y<400;++y)for(int x=450;x<510;++x)
            if(foreground[y*960+x]!=0xff00ff00)return 8;
        fprintf(stderr,"PASS: half-resolution cloud composite, viewport borders and subsequent foreground\n");
        d->SetTexture(0,nullptr);halfSurface->Release();half->Release();compositeVS->Release();compositePS->Release();
        std::ifstream palettes("out/jump_travel/cloud_reference/palettes.txt");
        std::string name;float colours[8]={};int count=0;std::vector<DWORD> previous;
        while(palettes>>name>>colours[0]>>colours[1]>>colours[2]>>colours[4]>>colours[5]>>colours[6]){
            Check(d->BeginScene());d->SetVertexShader(energyVS);d->SetPixelShader(energyPS);
            d->SetTexture(0,modulation);d->SetTexture(1,noise);d->SetTexture(2,splinePath);
            d->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_WRAP);d->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_WRAP);
            Check(d->SetPixelShaderConstantF(7,colours,2));
            Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Vertex)));Check(d->EndScene());
            auto pixels=Read(d,target);if(pixels==previous)return 12;previous=pixels;
            std::string filename="out/jump_travel/cloud_reference/palette_"+name+".png";
            Check(D3DXSaveSurfaceToFileA(filename.c_str(),D3DXIFF_PNG,target,nullptr,nullptr));++count;
        }
        if(count<2)return 13;
        fprintf(stderr,"PASS: rendered %d authored tunnel palettes\n",count);
    }
    if(energyVS)energyVS->Release();if(energyPS)energyPS->Release();
    d->SetTexture(0,nullptr);d->SetTexture(1,nullptr);d->SetTexture(2,nullptr);if(modulation)modulation->Release();if(splinePath)splinePath->Release();textures[0]->Release();textures[1]->Release();noise->Release();vs->Release();cloud->Release();original->Release();target->Release();d->Release();api->Release();DestroyWindow(window);return 0;
}
