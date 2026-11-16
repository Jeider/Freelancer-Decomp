// Flight-only cloud background. Included after FGateTunnelVertex is defined.
#include "port_config.h"
#include "jump_cloud_path.h"
#include "graphics_settings.h"
#include "travel_quality.h"
#include <cstdint>
namespace {
FRPExProgram* G_JumpCloud=nullptr;
FRPExProgram* G_JumpCloudComposite=nullptr;
FRPExTexture* G_JumpCloudNoise=nullptr;
FRPExTexture* G_JumpCloudTarget=nullptr;
void* G_JumpCloudModulation=nullptr;
void* G_JumpCloudPath=nullptr;
bool G_JumpCloudTried=false;
bool G_JumpCloudLogged=false;
std::vector<unsigned char> G_JumpCloudNoiseBytes;

void ReleaseJumpCloud() {
    auto* ex=RenderEx::GetPipelineEx();auto* pipe=DALib::Pipeline;
    if(ex&&G_JumpCloud)ex->DestroyExProgram(G_JumpCloud);
    if(ex&&G_JumpCloudComposite)ex->DestroyExProgram(G_JumpCloudComposite);
    if(ex&&G_JumpCloudNoise)ex->DestroyExTexture(G_JumpCloudNoise);
    if(ex&&G_JumpCloudTarget)ex->DestroyExTexture(G_JumpCloudTarget);
    if(pipe&&G_JumpCloudModulation)pipe->DestroyTexture(G_JumpCloudModulation);
    if(pipe&&G_JumpCloudPath)pipe->DestroyTexture(G_JumpCloudPath);
    G_JumpCloud=G_JumpCloudComposite=nullptr;G_JumpCloudNoise=G_JumpCloudTarget=nullptr;
    G_JumpCloudModulation=G_JumpCloudPath=nullptr;G_JumpCloudTried=G_JumpCloudLogged=false;
}
void PrepareJumpCloud() {
    if(GraphicsSettings::Get(GraphicsSettings::Hyperspace)==0)return;
    if(!PortConfigInt("Render","jump_cloud_tunnel",0)||G_JumpCloudTried||!RenderEx::IsAvailable())return;
    G_JumpCloudTried=true;
    auto* ex=RenderEx::GetPipelineEx();auto* fs=RenderEx::GetExtraData();
    IRPTexture* loader=nullptr;
    bool ok=DALib::Pipeline->QueryInterface(Iids::RPTexture,reinterpret_cast<void**>(&loader))==GR_OK&&loader;
    if(ok)ok=ex->CreateExProgram(fs,"SHADERS\\jump_cloud.hlsl","VSMain","PSMain",&G_JumpCloud)==GR_OK;
    if(ok)ok=ex->CreateExProgram(fs,"SHADERS\\jump_cloud.hlsl","VSComposite","PSComposite",&G_JumpCloudComposite)==GR_OK;
    if(ok)ok=loader->LoadTexture(fs,"FX\\JUMP_CLOUD\\modulation.png",&G_JumpCloudModulation)==GR_OK;
    if(ok)ok=loader->LoadTexture(fs,"FX\\JUMP_CLOUD\\path.dds",&G_JumpCloudPath)==GR_OK;
    if(loader)loader->Release();
    if(G_JumpCloudNoiseBytes.empty()){
        G_JumpCloudNoiseBytes.resize(32*32*32);std::uint32_t seed=0x48595045;
        for(auto& b:G_JumpCloudNoiseBytes){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;b=static_cast<unsigned char>(seed>>24);}
    }
    if(ok)ok=ex->CreateExVolumeTexture(32,32,32,RPExFormatL8,G_JumpCloudNoiseBytes.data(),&G_JumpCloudNoise)==GR_OK;
    float const scale=TravelQuality::HyperspaceScale(GraphicsSettings::Get(GraphicsSettings::Hyperspace));
    FRPExRenderTargetDesc desc={0,0,scale,RPExFormatA8R8G8B8};
    if(ok)ok=ex->CreateExRenderTarget(&desc,&G_JumpCloudTarget)==GR_OK;
    if(!ok){ReleaseJumpCloud();G_JumpCloudTried=true;FDUMP(0x100002,"Jump cloud preparation failed; retaining previous tunnel.\n");}
    else FDUMP(0x100002,"Jump cloud prepared: cached assets, resolution scale %.3f.\n",scale);
}
bool JumpCloudReady(FGateTunnel const* tunnel) {
    return GraphicsSettings::Get(GraphicsSettings::Hyperspace)>0&&tunnel&&tunnel->bHyperspaceClouds&&GetGameOption(kGameOptEffectsGroup)&&
        PortConfigInt("Render","jump_cloud_tunnel",0)&&G_JumpCloud&&G_JumpCloudComposite&&
        G_JumpCloudNoise&&G_JumpCloudTarget&&G_JumpCloudModulation&&G_JumpCloudPath;
}
bool DrawJumpCloud(FSpaceCamera* camera,FGateTunnel const* tunnel) {
    if(!camera||!JumpCloudReady(tunnel)||!std::isfinite(tunnel->SpeedClock)||tunnel->SpeedClock<0)return false;
    auto* ex=RenderEx::GetPipelineEx();auto* pipe=DALib::Pipeline;
    FRPExTexture* depth=nullptr;unsigned long w=0,h=0;
    if(ex->GetSceneDepth(&depth)!=GR_OK||!depth||ex->GetExTextureSize(depth,&w,&h)!=GR_OK||!w||!h)return false;
    int const* vp=camera->GetViewport();float width=float(vp[2]-vp[0]+1),height=float(vp[3]-vp[1]+1);
    if(width<2||height<2)return false;
    float animation[4]={0,3+tunnel->SpeedClock*JumpCloud::MaterialSpeed,3,2};
    float travel[4]={3+tunnel->SpeedClock*JumpCloud::TravelSpeed,0,0,0};
    float frame[16];JumpCloud::Camera(travel[0]*2.6f,frame);
    float destination[4];JumpCloud::Destination(travel[0]*2.6f,frame,destination);
    float palette[8]={0,0,200.f/255,0,100.f/255,200.f/255,1,0};
    for(int i=0;i<2&&i<tunnel->LayerCount;++i){
        auto const& c=tunnel->Layers[i].Color;
        palette[i*4]=c.X;palette[i*4+1]=c.Y;palette[i*4+2]=c.Z;
    }
    if(tunnel->LayerCount==1)for(int i=0;i<3;++i)palette[4+i]=palette[i];
    // Match the approved 60-degree preview vertically, correct for live aspect.
    float view[4]={width/height,1.1547005f,0,0};
    float remap[4]={width/w,height/h,(2*vp[0]+width)/w-1,1-(2*vp[1]+height)/h};
    FGateTunnelVertex const quad[]={{{-1,1,0},0xffffffff,{0,0}},{{1,1,0},0xffffffff,{1,0}},
        {{-1,-1,0},0xffffffff,{0,1}},{{1,-1,0},0xffffffff,{1,1}}};
    FRPExSamplerState wrap={RPExFilterLinear,RPExMipLinear,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
    FRPExSamplerState volume={RPExFilterLinear,RPExMipNone,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
    FRPExSamplerState clamp={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExPassDesc pass={G_JumpCloudTarget,0,0};
    if(ex->BeginExPass(&pass)!=GR_OK)return false;
    pipe->SetRenderState(D3DRS_ZENABLE,0);pipe->SetRenderState(D3DRS_ZWRITEENABLE,0);
    pipe->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);pipe->SetRenderState(D3DRS_ALPHATESTENABLE,0);
    pipe->SetRenderState(D3DRS_ALPHABLENDENABLE,0);
    auto draw=[&](){return RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,quad,4)==GR_OK;};
    bool ok=ex->BindExProgram(G_JumpCloud)==GR_OK&&
        ex->BindExPipelineTexture(0,G_JumpCloudModulation,&wrap)==GR_OK&&
        ex->BindExTexture(1,G_JumpCloudNoise,&volume)==GR_OK&&
        ex->BindExPipelineTexture(2,G_JumpCloudPath,&clamp)==GR_OK&&
        ex->SetExPixelConstants(0,animation,1)==GR_OK&&ex->SetExPixelConstants(1,travel,1)==GR_OK&&
        ex->SetExPixelConstants(2,frame,4)==GR_OK&&ex->SetExPixelConstants(6,view,1)==GR_OK&&
        ex->SetExPixelConstants(7,palette,2)==GR_OK&&ex->SetExPixelConstants(9,destination,1)==GR_OK&&draw();
    if(ok)ok=ex->SetExRenderTarget(nullptr,0)==GR_OK&&ex->BindExProgram(G_JumpCloudComposite)==GR_OK&&
        ex->BindExTexture(0,G_JumpCloudTarget,&clamp)==GR_OK&&ex->SetExVertexConstants(7,remap,1)==GR_OK&&draw();
    ex->EndExPass();
    if(ok&&!G_JumpCloudLogged){FDUMP(0x100002,"Jump cloud active: quality %d, background before ship; simulation clock.\n",GraphicsSettings::Get(GraphicsSettings::Hyperspace));G_JumpCloudLogged=true;}
    return ok;
}
}
