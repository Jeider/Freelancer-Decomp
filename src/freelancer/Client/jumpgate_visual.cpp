#include "jumpgate_visual.h"
#ifdef FREELANCER_RP9
#include "jumpgate_visual_state.h"
#include "jumpgate_visual_geometry.h"
#include "jumphole_visual_geometry.h"
#include "jumphole_visibility.h"
#include "tradelane_visual_noise.h"
#include "client_gameobj.h"
#include "common_cobject.h"
#include "common_goods.h"
#include "jump_effect.h"
#include "gate_tunnel.h"
#include "space_env_fx.h"
#include "space_camera.h"
#include "nebula_volume.h"
#include "game_options.h"
#include "port_config.h"
#include "render_ex.h"
#include "win3d_render.h"
#include "DALib.h"
#include "dacom_iids.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/IRPSceneCapture.h"
#include <map>
#include <vector>
#include <chrono>

namespace
{
    struct FState {
        FJumpGateVisualPhase Phase;
        float Portal[4] = {}; // authored jump-out hardpoint in solar-local space; radius
        float PortalRows[12] = {}; // solar-local -> hardpoint-local rotation
        float Plasma[4] = {}; // jg_bubble attachment + authored emitter translation
        float Inflow[4] = {}; // mod_jumpgate_tunnel attachment; enable
        float Tint[4] = {1,1,1,0}; // upcoming tunnel palette; recolour enable
        float Donut[4] = {}; // shooter HP + parent/child ALE translations; enable
        bool Claimed = false, Fallback = false, Logged = false;
    };
    std::map<FClientSolarGameobj*, FState> G_States;
    FRPExProgram* G_Program = nullptr;
    FRPExProgram* G_Lens = nullptr;
    FRPExProgram* G_Inflow = nullptr;
    FRPExProgram* G_Donuts = nullptr;
    FRPExTexture* G_Copy = nullptr;
    FRPExTexture* G_Noise = nullptr;
    IRPSceneCapture* G_Capture = nullptr;
    bool G_Failed = false;
    FJumpShipEffect const* G_Transit = nullptr;
    std::vector<FJumpHoleVertex> G_Trails;

    bool KnownEffect(unsigned Id)
    {
        return Id == CreateID("mod_jumpgate_tunnel") || Id == CreateID("jg_bubble") ||
            Id == CreateID("jg_sphere") || Id == CreateID("jumpgate_end") ||
            Id == CreateID("big_jumpgate_tunnel") || Id == CreateID("jg_donutshooter");
    }
    bool Eligible(FClientSolarGameobj* Host)
    {
        unsigned Type = 0;
        if (!Host || !PortConfigInt("Render", "jumpgate_visual", 1) ||
            Host->get_type(Type) != 0 || !(Type & 0x40u)) return false;
        CObject const* Obj = Host->cobject();
        if (!Obj || !Obj->Archetype || Obj->Archetype->get_id() != CreateID("jumpgate")) return false;
        FJumpEffectDesc const* Desc = JumpEffectFindDesc(Host->Field_0x200.Id);
        if (!Desc || Desc->RingCount < 1 || Desc->RingCount > 5) return false;
        // Claim the whole authored group or none of it; other gate types/presets keep ALE.
        bool Tunnel = false, Big = false, Donut = false, Bubble = false;
        for (int I = 0; I < Desc->RingCount; ++I) {
            if (!KnownEffect(Desc->Rings[I].Effect.Id)) return false;
            Tunnel |= Desc->Rings[I].Effect.Id == CreateID("mod_jumpgate_tunnel");
            Big |= Desc->Rings[I].Effect.Id == CreateID("big_jumpgate_tunnel");
            Donut |= Desc->Rings[I].Effect.Id == CreateID("jg_donutshooter");
            Bubble |= Desc->Rings[I].Effect.Id == CreateID("jg_bubble");
        }
        return (Tunnel && !Big && !Donut) || (Big && Donut && !Tunnel && !Bubble);
    }
    void Release()
    {
        auto* Ex = RenderEx::GetPipelineEx();
        if (Ex && G_Program) Ex->DestroyExProgram(G_Program);
        if (Ex && G_Lens) Ex->DestroyExProgram(G_Lens);
        if (Ex && G_Inflow) Ex->DestroyExProgram(G_Inflow);
        if (Ex && G_Donuts) Ex->DestroyExProgram(G_Donuts);
        if (Ex && G_Copy) Ex->DestroyExTexture(G_Copy);
        if (Ex && G_Noise) Ex->DestroyExTexture(G_Noise);
        if (G_Capture) G_Capture->Release();
        G_Program = G_Lens = G_Inflow = G_Donuts = nullptr; G_Copy = G_Noise = nullptr; G_Capture = nullptr;
        std::vector<FJumpHoleVertex>().swap(G_Trails);
    }
    bool Prepared()
    {
        return G_Program && G_Lens && G_Inflow && G_Copy && G_Noise && G_Capture;
    }
    void Prepare()
    {
        if (G_Failed || Prepared() || !RenderEx::IsAvailable()) return;
        auto Start=std::chrono::steady_clock::now();
        auto* Ex = RenderEx::GetPipelineEx();
        // RP9 can compile bytecode and retain texture data before device creation.
        // Do this at renderer startup, never in a solar activation or draw callback.
        FRPExRenderTargetDesc Desc = {0,0,1.f,RPExFormatA8R8G8B8};
        bool Ok = DALib::Pipeline->QueryInterface(Iids::RPSceneCapture,
            reinterpret_cast<void**>(&G_Capture)) == GR_OK && G_Capture;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumpgate_aperture.hlsl",
            "VSMain", "PSMain", &G_Program) == GR_OK;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumpgate_aperture.hlsl",
            "VSMain", "PSLens", &G_Lens) == GR_OK;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumpgate_aperture.hlsl",
            "VSInflow", "PSInflow", &G_Inflow) == GR_OK;
        // Failure of the alternate shader must not disable the ordinary gate.
        if (Ok && Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumpgate_aperture.hlsl",
            "VSMain", "PSDonuts", &G_Donuts) != GR_OK) {
            if(G_Donuts)Ex->DestroyExProgram(G_Donuts);
            G_Donuts=nullptr;
            FDUMP(0x100002,"Alternate jump-gate donuts unavailable; retaining its ALE.\n");
        }
        auto Compiled=std::chrono::steady_clock::now();
        if (Ok) Ok = Ex->CreateExRenderTarget(&Desc, &G_Copy) == GR_OK;
        if (Ok) {
            std::vector<std::uint32_t> Noise(TradeLaneNoiseSize*TradeLaneNoiseSize*TradeLaneNoiseSize);
            BuildTradeLaneNoise(Noise.data());
            Ok = Ex->CreateExVolumeTexture(TradeLaneNoiseSize,TradeLaneNoiseSize,TradeLaneNoiseSize,
                RPExFormatA8R8G8B8,Noise.data(),&G_Noise) == GR_OK;
        }
        if (Ok) {
            G_Trails.reserve(JumpGateInflowVertices);
            FDUMP(0x100003,"Jump-gate startup preparation: shaders %.1f ms, textures/buffers %.1f ms.\n",
                std::chrono::duration<double,std::milli>(Compiled-Start).count(),
                std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-Compiled).count());
        } else {
            Release(); G_Failed = true;
            FDUMP(0x100002,"Jump-gate aperture unavailable; retaining original ALE.\n");
        }
    }
    bool Ready()
    {
        if(G_Failed || !Prepared() || !RenderEx::IsAvailable())return false;
        FRPExTexture* Depth=nullptr;
        return RenderEx::GetPipelineEx()->GetSceneDepth(&Depth)==GR_OK && Depth;
    }
    void DrawGate(FSpaceCamera* Camera, FClientSolarGameobj* Host, FState& State)
    {
        if (!State.Claimed || State.Phase.Gain <= 0 || !Eligible(Host) || !Ready()) return;
        Transform const& World = Host->get_transform();
        float Centre[3] = {World.Translation.x,World.Translation.y,World.Translation.z};
        float ViewCentre[3];
        JumpHoleWorldToView(Camera->GetViewTransform(),Centre,ViewCentre);
        if (Camera->ClassifySphere(ViewCentre,State.Donut[3]>0?750.f:650.f) == 1) return;
        float const* Eye = Camera->GetPosition();
        float Rotation[9], LocalEye[3] = {};
        double DistSq = 0;
        for (int R=0; R<3; ++R) {
            DistSq += double(Eye[R]-Centre[R])*(Eye[R]-Centre[R]);
            for (int C=0; C<3; ++C) {
                Rotation[R*3+C] = World.Rotation.E[R][C];
                LocalEye[R] += World.Rotation.E[C][R]*(Eye[C]-Centre[C]);
            }
        }
        float Gain = State.Phase.Gain * JumpHoleRangeVisibility(float(std::sqrt(DistSq)),25000.f);
        CObject const* Obj = Host->cobject();
        if (Obj && (Obj->ObjectClass & CObject::ClassEqObj) == CObject::ClassEqObj)
            Gain *= 1-(std::max)(0.f,(std::min)(1.f,static_cast<CEqObj const*>(Obj)->CloakPercent));
        if (GetGameOption(kGameOptNebula)) Gain *= NebulaVolume::EffectVisibility(Eye,Centre);
        if (Gain <= 0) return;
        auto* Ex = RenderEx::GetPipelineEx();
        FRPExTexture* Depth = nullptr; unsigned long W=0,H=0;
        if (Ex->GetSceneDepth(&Depth)!=GR_OK || !Depth ||
            Ex->GetExTextureSize(Depth,&W,&H)!=GR_OK || !W || !H) return;
        int const* Vp = Camera->GetViewport();
        if (Vp[2]<Vp[0] || Vp[3]<Vp[1]) return;
        float P[68+4*JumpGateDonutPulseCount] = {State.Phase.Time,State.Phase.Age,Gain,1,
            1.f/W,1.f/H,.022f,0,
            (Vp[0]+.5f)/W,(Vp[1]+.5f)/H,(Vp[2]+.5f)/W,(Vp[3]+.5f)/H,
            Camera->GetZNear(),Camera->GetZFar(),0,1,
            LocalEye[0],LocalEye[1],LocalEye[2],0};
        Win3DApplyCamera(AsCamera(Camera));
        float Projection[16];
        if (DALib::Pipeline->GetProjection(Projection)!=GR_OK ||
            !JumpGateProjectionRayParams(Projection,P+20)) return;
        std::copy(State.Portal,State.Portal+4,P+36);
        std::copy(State.PortalRows,State.PortalRows+12,P+40);
        std::copy(State.Plasma,State.Plasma+4,P+52);
        P[56]=130; P[57]=190; P[58]=.5235987756f; P[59]=-.3926990817f;
        std::copy(State.Tint,State.Tint+4,P+60);
        std::copy(State.Donut,State.Donut+4,P+64);
        BuildJumpGateDonutPulses(State.Phase.Time,State.Phase.Age,State.Donut[2],P+68);
        DALib::Pipeline->GetDepthRange(P+14,P+15);
        JumpHoleCameraToLocal(Camera->GetViewTransform(),Rotation,P+24);
        float const Width=float(Vp[2]-Vp[0]+1),Height=float(Vp[3]-Vp[1]+1);
        float const Remap[4]={Width/W,Height/H,(2*Vp[0]+Width)/W-1,1-(2*Vp[1]+Height)/H};
        FJumpHoleVertex const Quad[]={
            {{-1,1,0},0xffffffffu,{0,0}},{{1,1,0},0xffffffffu,{1,0}},
            {{-1,-1,0},0xffffffffu,{0,1}},{{1,-1,0},0xffffffffu,{1,1}}};
        FRPExSamplerState Linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
        FRPExSamplerState Point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
        FRPExSamplerState Noise={RPExFilterLinear,RPExMipNone,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
        if (G_Capture->CaptureSceneColor(G_Copy)!=GR_OK) return;
        BuildJumpGateInflow(State.Phase.Time,State.Inflow,State.Portal,State.PortalRows,LocalEye,G_Trails);
        bool Ok=true;
        for(int PassIndex=0;PassIndex<3;++PassIndex) {
            FRPExPassDesc Pass={nullptr,0,0};
            if (Ex->BeginExPass(&Pass)!=GR_OK) return;
            bool Bound=Ex->BindExProgram(PassIndex==2?G_Inflow:PassIndex?(State.Donut[3]>0?G_Donuts:G_Program):G_Lens)==GR_OK && Ex->BindExTexture(0,G_Copy,&Linear)==GR_OK &&
                Ex->BindExTexture(1,Depth,&Point)==GR_OK && Ex->BindExTexture(2,G_Noise,&Noise)==GR_OK &&
                Ex->SetExVertexConstants(7,Remap,1)==GR_OK && Ex->SetExPixelConstants(0,P,17+JumpGateDonutPulseCount)==GR_OK;
            if(PassIndex) {
                DALib::Pipeline->SetRenderState(D3DRS_ALPHABLENDENABLE,1);
                DALib::Pipeline->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
                DALib::Pipeline->SetRenderState(D3DRS_DESTBLEND,PassIndex==2?D3DBLEND_ONE:D3DBLEND_INVSRCALPHA);
                DALib::Pipeline->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
            }
            if(PassIndex==2) {
                Bound=Bound && Ex->SetExVertexConstants(0,P,15)==GR_OK && Ex->SetExVertexConstants(16,Remap,1)==GR_OK;
                if(Bound && !G_Trails.empty()) Bound=RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLELIST,
                    D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,G_Trails.data(),unsigned(G_Trails.size()))==GR_OK;
            } else if (Bound) Bound=RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,
                D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,Quad,4)==GR_OK;
            if (Ex->EndExPass()!=GR_OK) Bound=false;
            Ok=Ok&&Bound;
        }
        if (!State.Logged) {
            FDUMP(0x100003,"Jump-gate aperture %08x draw=%d age=%.2f.\n",Host->get_id(),Ok,State.Phase.Age);
            State.Logged=true;
        }
    }
}
#endif

bool JumpGateVisualReplaceActivation(FClientSolarGameobj* Host,unsigned EffectId)
{
#ifdef FREELANCER_RP9
    if (!KnownEffect(EffectId) || !Eligible(Host)) return false;
    FState& S=G_States[Host];
    if (S.Fallback) return false;
    if (!S.Claimed) {
        auto const* Arch=static_cast<Archetype::Solar const*>(Host->cobject()->Archetype);
        HardpointInfo Hp; long Handle=0;
        if (!FindHardpoint_PS(Host->get_index(),Arch->JumpOutHp.Value,Handle,Hp)) {
            S.Fallback=true; return false;
        }
        if (!Ready()) { S.Fallback=true; return false; }
        S.Portal[0]=Hp.Position.x;
        S.Portal[1]=Hp.Position.y;
        S.Portal[2]=Hp.Position.z;
        S.Portal[3]=195.f;
        for(int R=0;R<3;++R) for(int C=0;C<3;++C)
            S.PortalRows[R*4+C]=Hp.Orient.E[C][R];
        auto const* Desc=JumpEffectFindDesc(Host->Field_0x200.Id);
        if(auto const* Tunnel=GateTunnelFind(&Desc->JumpTunnel)) {
            GateTunnelGetTint(Tunnel,S.Tint);
            S.Tint[3]=1;
        }
        for(int I=0;I<Desc->RingCount;++I) if(Desc->Rings[I].Effect.Id==CreateID("mod_jumpgate_tunnel") ||
            Desc->Rings[I].Effect.Id==CreateID("big_jumpgate_tunnel")) {
            HardpointInfo FlowHp;
            if(!FindHardpoint_PS(Host->get_index(),Desc->Rings[I].Hp.Value,Handle,FlowHp)) {
                S.Fallback=true; return false;
            }
            S.Inflow[0]=FlowHp.Position.x; S.Inflow[1]=FlowHp.Position.y;
            S.Inflow[2]=FlowHp.Position.z; S.Inflow[3]=1;
            break;
        }
        for(int I=0;I<Desc->RingCount;++I) if(Desc->Rings[I].Effect.Id==CreateID("jg_donutshooter")) {
            HardpointInfo DonutHp;
            if(!G_Donuts || !FindHardpoint_PS(Host->get_index(),Desc->Rings[I].Hp.Value,Handle,DonutHp)) {
                S.Fallback=true; return false;
            }
            // Nested ALE: cube shooter at -40.796 Z and child ring at -550 Z.
            // Activation attachments and child particles both use identity rotation.
            S.Donut[0]=DonutHp.Position.x; S.Donut[1]=DonutHp.Position.y;
            S.Donut[2]=DonutHp.Position.z+JumpGateDonutEmitterOffsetZ; S.Donut[3]=1;
            break;
        }
        for(int I=0;I<Desc->RingCount;++I) if(Desc->Rings[I].Effect.Id==CreateID("jg_bubble")) {
            HardpointInfo RingHp;
            if(!FindHardpoint_PS(Host->get_index(),Desc->Rings[I].Hp.Value,Handle,RingHp)) {
                S.Fallback=true; return false;
            }
            // Retail attaches activation effects at HP position with identity rotation.
            // Both gf_jumpgate_bubble shell cone nodes translate (0,0,8), rotate X=90,
            // and emit at spread 90: their circular planes are solar-local XY.
            S.Plasma[0]=RingHp.Position.x; S.Plasma[1]=RingHp.Position.y;
            S.Plasma[2]=RingHp.Position.z+8; S.Plasma[3]=1;
            break;
        }
        S.Claimed=true;
        if (!S.Phase.Open) S.Phase.Activate();
        FDUMP(0x100003,"Jump-gate aperture claimed %08x at jump-out HP=(%.3f %.3f %.3f).\n",
            Host->get_id(),S.Portal[0],S.Portal[1],S.Portal[2]);
    }
    return true;
#else
    return false;
#endif
}
void JumpGateVisualEvent(FClientSolarGameobj* Host,int Sub)
{
#ifdef FREELANCER_RP9
    if (Sub==3) { G_States.erase(Host); return; }
    if (!Eligible(Host)) return;
    if (Sub==0) G_States[Host].Phase.Activate();
    else if (Sub==2) {
        auto It=G_States.find(Host);
        if (It!=G_States.end()) It->second.Phase.Open=false;
    }
#endif
}
void JumpGateVisualTick(FClientSolarGameobj* Host,float Dt)
{
#ifdef FREELANCER_RP9
    auto It=G_States.find(Host);
    if (It!=G_States.end()) It->second.Phase.Tick(Dt);
#endif
}
void JumpGateVisualForget(FClientSolarGameobj* Host)
{
#ifdef FREELANCER_RP9
    G_States.erase(Host);
#endif
}
void JumpGateVisualDraw(FSpaceCamera* Camera)
{
#ifdef FREELANCER_RP9
    if (!Camera || !GetGameOption(kGameOptEffectsGroup) || !GetGameOption(kGameOptParticles)) return;
    std::vector<FClientSolarGameobj*> Ordered;
    for (auto const& Pair:G_States) if (Pair.second.Claimed) Ordered.push_back(Pair.first);
    auto Distance=[&](FClientSolarGameobj* Host) {
        auto const& P=Host->get_position(); auto const* E=Camera->GetPosition();
        return double(P.x-E[0])*(P.x-E[0])+double(P.y-E[1])*(P.y-E[1])+double(P.z-E[2])*(P.z-E[2]);
    };
    std::sort(Ordered.begin(),Ordered.end(),[&](FClientSolarGameobj* A,FClientSolarGameobj* B){return Distance(A)>Distance(B);});
    for (auto* Host:Ordered) DrawGate(Camera,Host,G_States.at(Host));
#endif
}
void JumpGateVisualRenderStartup()
{
#ifdef FREELANCER_RP9
    if(PortConfigInt("Render","jumpgate_visual",1))Prepare();
#endif
}
void JumpGateVisualRenderShutdown()
{
#ifdef FREELANCER_RP9
    G_States.clear(); Release(); G_Failed=false; G_Transit=nullptr;
#endif
}
void JumpGateVisualBindTransit(FJumpShipEffect const* Effect,FClientSolarGameobj* Host)
{
#ifdef FREELANCER_RP9
    // Called only for the player by the existing transit constructor branch.
    auto It=G_States.find(Host);
    if (Effect && Eligible(Host) && It!=G_States.end() && It->second.Claimed)
        G_Transit=Effect;
#endif
}
void JumpGateVisualForgetTransit(FJumpShipEffect const* Effect)
{
#ifdef FREELANCER_RP9
    if (G_Transit==Effect) G_Transit=nullptr;
#endif
}
bool JumpGateVisualMatchesTransit(FJumpShipEffect const* Effect)
{
#ifdef FREELANCER_RP9
    // The ordinary gate's vortex and launch stars share the upcoming tunnel palette.
    // The full launch flash is retained alongside the stars and world-space portal.
    return Effect && G_Transit==Effect && Effect->Ship &&
        PortConfigInt("Render","jumpgate_visual",1) && GetGameOption(kGameOptParticles) &&
        (Effect->Ship->Field_0x158==1 || Effect->Ship->Field_0x158==2);
#else
    return false;
#endif
}
