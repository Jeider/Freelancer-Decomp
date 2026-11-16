// Included by gate_tunnel.cpp. Opt-in independent renderer, no retail strips.
#include "port_config.h"
#include "tradelane_visual_noise.h"
namespace {
FRPExProgram* G_JumpPrototype=nullptr;
FRPExProgram* G_JumpPrototypeTransition=nullptr;
FRPExTexture* G_JumpPrototypeNoise=nullptr;
bool G_JumpPrototypeTried=false;
std::vector<std::uint32_t> G_JumpPrototypeNoiseData;
bool JumpPrototypeEnabled(FGateTunnel const* T) {
    return T && T->bHyperspaceClouds && PortConfigInt("Render","jump_travel_prototype",0)!=0;
}
void PrepareJumpPrototype() {
    if(!PortConfigInt("Render","jump_travel_prototype",0)||G_JumpPrototypeTried||!RenderEx::IsAvailable())return;
    FRPExCaps Caps={};if(!RenderEx::GetCaps(&Caps))return;
    G_JumpPrototypeTried=true;
    auto* Ex=RenderEx::GetPipelineEx();
    if(Ex->CreateExProgram(RenderEx::GetExtraData(),"SHADERS\\jump_travel_prototype.hlsl","VSMain","PSMain",&G_JumpPrototype)!=GR_OK)return;
    if(Ex->CreateExProgram(RenderEx::GetExtraData(),"SHADERS\\jump_travel_prototype.hlsl","VSMain","PSTransition",&G_JumpPrototypeTransition)!=GR_OK)return;
    if(G_JumpPrototypeNoiseData.empty()) {
        G_JumpPrototypeNoiseData.resize(TradeLaneNoiseSize*TradeLaneNoiseSize*TradeLaneNoiseSize);
        BuildTradeLaneNoise(G_JumpPrototypeNoiseData.data());
    }
    Ex->CreateExVolumeTexture(TradeLaneNoiseSize,TradeLaneNoiseSize,TradeLaneNoiseSize,
        RPExFormatA8R8G8B8,G_JumpPrototypeNoiseData.data(),&G_JumpPrototypeNoise);
}
bool JumpPrototypeReady(FGateTunnel const* T) {
    return JumpPrototypeEnabled(T)&&G_JumpPrototype&&G_JumpPrototypeTransition&&G_JumpPrototypeNoise;
}
bool DrawJumpPrototype(FSpaceCamera* Camera,float Clock,int Phase,float Progress) {
    if(!Camera||!std::isfinite(Clock)||!std::isfinite(Progress))return false;
    auto* Ex=RenderEx::GetPipelineEx();auto* Pipe=DALib::Pipeline;
    FRPExTexture* DepthTexture=nullptr;unsigned long W=0,H=0;
    if(Ex->GetSceneDepth(&DepthTexture)!=GR_OK||!DepthTexture||Ex->GetExTextureSize(DepthTexture,&W,&H)!=GR_OK||!W||!H)return false;
    int const* Vp=Camera->GetViewport();float Width=float(Vp[2]-Vp[0]+1),Height=float(Vp[3]-Vp[1]+1);
    if(Width<=1||Height<=1)return false;
    float Remap[4]={Width/W,Height/H,(2*Vp[0]+Width)/W-1,1-(2*Vp[1]+Height)/H};
    float Min=0,Max=1;Pipe->GetDepthRange(&Min,&Max);
    float P[12]={Clock,Width/Height,float(Phase),Progress,1.f/W,1.f/H,Camera->GetZNear(),Camera->GetZFar(),Min,Max,Phase==1?0.f:1.f,0};
    FGateTunnelVertex const Quad[]={{{-1,1,0},0xffffffff,{0,0}},{{1,1,0},0xffffffff,{1,0}},
        {{-1,-1,0},0xffffffff,{0,1}},{{1,-1,0},0xffffffff,{1,1}}};
    FRPExPassDesc Pass={nullptr,0,0};if(Ex->BeginExPass(&Pass)!=GR_OK)return false;
    Pipe->SetRenderState(D3DRS_ZENABLE,0);Pipe->SetRenderState(D3DRS_ZWRITEENABLE,0);
    Pipe->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);Pipe->SetRenderState(D3DRS_ALPHATESTENABLE,0);
    Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE,Phase!=1);
    Pipe->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);Pipe->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    Pipe->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
    FRPExSamplerState Noise={RPExFilterLinear,RPExMipNone,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
    FRPExSamplerState Point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    bool Ok=Ex->BindExProgram(Phase==1?G_JumpPrototype:G_JumpPrototypeTransition)==GR_OK &&
        Ex->BindExTexture(0,G_JumpPrototypeNoise,&Noise)==GR_OK &&
        Ex->BindExTexture(1,DepthTexture,&Point)==GR_OK &&
        Ex->SetExVertexConstants(7,Remap,1)==GR_OK && Ex->SetExPixelConstants(0,P,3)==GR_OK &&
        RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,Quad,4)==GR_OK;
    Ex->EndExPass();return Ok;
}
void ReleaseJumpPrototype() {
    auto* Ex=RenderEx::GetPipelineEx();
    if(Ex&&G_JumpPrototype)Ex->DestroyExProgram(G_JumpPrototype);
    if(Ex&&G_JumpPrototypeTransition)Ex->DestroyExProgram(G_JumpPrototypeTransition);
    if(Ex&&G_JumpPrototypeNoise)Ex->DestroyExTexture(G_JumpPrototypeNoise);
    G_JumpPrototype=G_JumpPrototypeTransition=nullptr;G_JumpPrototypeNoise=nullptr;G_JumpPrototypeTried=false;
}
}
