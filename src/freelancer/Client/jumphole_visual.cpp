#include "jumphole_visual.h"
#ifdef FREELANCER_RP9
#include "jumphole_visual_geometry.h"
#include "jumphole_visual_state.h"
#include "jumphole_visibility.h"
#include "tradelane_visual_noise.h"
#include "client_gameobj.h"
#include "client_cliobj.h"
#include "common_cobject.h"
#include "gate_tunnel.h"
#include "tradelane_visual_style.h"
#include "star_sys.h"
#include "cli_nebula.h"
#include "nebula_volume.h"
#include "effect_type_info.h"
#include "vis_effect_arch.h"
#include "perf_options.h"
#include "space_scene_obj_draw.h"
#include "jump_effect.h"
#include "space_camera.h"
#include "game_options.h"
#include "port_config.h"
#include "player_behavior.h"
#include "common_iface.h"
#include "render_ex.h"
#include "win3d_render.h"
#include "x86math.h"
#include "DALib.h"
#include "dacom_iids.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/IRPSceneCapture.h"
#include <cmath>
#include <vector>
#include <map>
#include <algorithm>

namespace
{
    struct FState
    {
        FClientSolarGameobj* Host = nullptr;
        FTransform World = {};
        FJumpHoleVisualPhase Phase;
        float Approach = 0;
        int EffectType = -1;
        float Palette[4] = {1,1,1,0};
        bool PaletteReady = false, HasIdle = false;
        bool Claimed = false, Fallback = false, LoggedDraw = false, LoggedFailure = false;
    };
    std::map<FClientSolarGameobj*, FState> G_States;
    FRPExProgram* G_Lens = nullptr;
    FRPExProgram* G_Glow = nullptr;
    FRPExProgram* G_Ingress = nullptr;
    FRPExProgram* G_OpticsWorld = nullptr;
    FRPExProgram* G_OpticsShip = nullptr;
    FJumpShipEffect const* G_Transit = nullptr;
    float G_TransitTime = 0;
    float G_TransitPalette[4] = {1,1,1,0};
    bool G_TransitLogged = false;
    FRPExBuffer* G_Mesh = nullptr;
    FRPExTexture* G_Noise = nullptr;
    FRPExTexture* G_Copy = nullptr;
    IRPSceneCapture* G_Capture = nullptr;
    bool G_Failed = false;

    void LogDrawFailure(FState& State,char const* Stage)
    {
        if (State.LoggedFailure) return;
        State.LoggedFailure = true;
        FDUMP(0x100002,"Jump-hole cloud %08x failed at %s.\n",State.Host->get_id(),Stage);
    }

    bool Eligible(FClientGameobj* Host)
    {
        unsigned Type = 0;
        return Host && PortConfigInt("Render", "jumphole_visual", 1) != 0 &&
            Host->ManagerKind == 2 &&
            Host->get_type(Type) == 0 && (Type & 0x800u) != 0;
    }
    void ReleaseResources()
    {
        auto* Ex = RenderEx::GetPipelineEx();
        if (Ex && G_Lens) Ex->DestroyExProgram(G_Lens);
        if (Ex && G_Glow) Ex->DestroyExProgram(G_Glow);
        if (Ex && G_Ingress) Ex->DestroyExProgram(G_Ingress);
        if (Ex && G_OpticsWorld) Ex->DestroyExProgram(G_OpticsWorld);
        if (Ex && G_OpticsShip) Ex->DestroyExProgram(G_OpticsShip);
        if (Ex && G_Mesh) Ex->DestroyExVertexBuffer(G_Mesh);
        if (Ex && G_Noise) Ex->DestroyExTexture(G_Noise);
        if (Ex && G_Copy) Ex->DestroyExTexture(G_Copy);
        if (G_Capture) G_Capture->Release();
        G_Lens = G_Glow = G_Ingress = nullptr; G_Mesh = nullptr;
        G_OpticsWorld = G_OpticsShip = nullptr;
        G_Noise = G_Copy = nullptr; G_Capture = nullptr;
    }
    bool Ready()
    {
        if (G_Failed || !RenderEx::IsAvailable()) return false;
        auto* Ex = RenderEx::GetPipelineEx();
        FRPExTexture* Depth = nullptr;
        unsigned long W = 0, H = 0;
        // Do not claim the original particles until all essential GPU facilities exist.
        if (Ex->GetSceneDepth(&Depth) != GR_OK || !Depth ||
            Ex->GetExTextureSize(Depth, &W, &H) != GR_OK || !W || !H) return false;
        if (G_Lens && G_Glow && G_Ingress && G_OpticsWorld && G_OpticsShip &&
            G_Mesh && G_Noise && G_Copy && G_Capture) return true;
        FRPExRenderTargetDesc Desc = {0,0,1.0f,RPExFormatA8R8G8B8};
        bool Ok = DALib::Pipeline->QueryInterface(Iids::RPSceneCapture,
            reinterpret_cast<void**>(&G_Capture)) == GR_OK && G_Capture;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumphole_lens.hlsl",
                                         "VSMain", "PSLens", &G_Lens) == GR_OK;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumphole_lens.hlsl",
                                         "VSMain", "PSGlow", &G_Glow) == GR_OK;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumphole_lens.hlsl",
                                         "VSIngress", "PSIngress", &G_Ingress) == GR_OK;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumphole_optics.hlsl",
                                         "VSOpticsWorld", "PSOpticsWorld", &G_OpticsWorld) == GR_OK;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\jumphole_optics.hlsl",
                                         "VSOpticsScreen", "PSOpticsShip", &G_OpticsShip) == GR_OK;
        if (Ok)
        {
            std::vector<FJumpHoleVertex> Mesh(JumpHoleVertexCount);
            BuildJumpHoleVisualGeometry(Mesh.data());
            Ok = Ex->CreateExVertexBuffer(static_cast<unsigned long>(Mesh.size()*sizeof(FJumpHoleVertex)),
                                          Mesh.data(), &G_Mesh) == GR_OK;
        }
        if (Ok)
        {
            std::vector<std::uint32_t> Noise(TradeLaneNoiseSize*TradeLaneNoiseSize*TradeLaneNoiseSize);
            BuildTradeLaneNoise(Noise.data());
            Ok = Ex->CreateExVolumeTexture(TradeLaneNoiseSize,TradeLaneNoiseSize,TradeLaneNoiseSize,
                                           RPExFormatA8R8G8B8,Noise.data(),&G_Noise) == GR_OK;
        }
        if (Ok) Ok = Ex->CreateExRenderTarget(&Desc,&G_Copy) == GR_OK;
        if (!Ok)
        {
            ReleaseResources(); G_Failed = true;
            FDUMP(0x100002,"Jump-hole lens unavailable; retaining attached ALE effects.\n");
        }
        return Ok;
    }
    FState& Track(FClientSolarGameobj* Host)
    {
        auto Insert=G_States.emplace(Host,FState());
        FState& State=Insert.first->second;
        if (!Insert.second) return State;
        State.Host=Host;
        Transform const& World=Host->get_transform();
        for(int R=0;R<3;++R) for(int C=0;C<3;++C)
            State.World.Rotation.D[R][C]=World.Rotation.E[R][C];
        State.World.Translation={World.Translation.x,World.Translation.y,World.Translation.z};
        if(Host->Field_0x204)
        {
            auto const* Gate=static_cast<FJumpGateEffect*>(Host->Field_0x204);
            State.Phase.Target=State.Phase.Opening=1;
            State.Phase.ActivationAge=(std::fmin)(JumpHoleActivationDuration,(std::fmax)(0.0f,Gate->Clock));
            if(Gate->bFire) State.Phase.Close();
        }
        return State;
    }
    void ResolvePalette(FState& State)
    {
        if(State.PaletteReady) return;
        float Hue[3]={.60f,.82f,1};
        FJumpEffectDesc const* Desc=JumpEffectFindDesc(State.Host->Field_0x200.Id);
        if(Desc) for(auto const* Tunnel:G_GateTunnels)
        {
            if(!Tunnel || Tunnel->Id.Id!=Desc->JumpTunnel.Id || Tunnel->LayerCount<1 || Tunnel->LayerCount>2) continue;
            FTradeLaneVisualStyle Style;
            FVector Zero={};
            FVector const& Layer1=Tunnel->LayerCount>1 ? Tunnel->Layers[1].Color : Zero;
            if(TradeLaneBuildPalette(Style,&Tunnel->Layers[0].Color.X,&Layer1.X,&Tunnel->MinRgb.X,&Tunnel->MaxRgb.X,0))
                for(int I=0;I<3;++I) Hue[I]=Style.Body[I];
            break;
        }
        // Resolve at first draw, after the system's nebulae and jump descriptors loaded.
        Vector const& Pos=State.Host->get_position();
        float Immersion=0;
        FNebulaEffect* Nebula=StarSysFindNebula(&Pos,&Immersion,nullptr);
        if(Nebula && Immersion>0)
        {
            float Fog[3]; Nebula->CopyFogRgb(Fog);
            if(TradeLaneNormalizePalette(Fog))
            {
                float Blend=.65f*JumpHoleSaturate(Immersion);
                for(int I=0;I<3;++I) Hue[I]=Hue[I]*(1-Blend)+Fog[I]*Blend;
            }
        }
        JumpHolePaletteMultiplier(Hue,State.Palette);
        State.PaletteReady=true;
    }
    bool Claim(FClientSolarGameobj* Host)
    {
        if(!Eligible(Host)) return false;
        FState& State=Track(Host);
        if(State.Fallback) return false;
        if(State.Claimed) return true;
        if(!Ready()) return false;
        FDUMP(0x100003,"Jump-hole lens claimed %08x.\n",Host->get_id());
        State.Claimed=true;
        return true;
    }
    void LogTransitFailure(char const* Stage)
    {
        if(G_TransitLogged) return;
        G_TransitLogged=true;
        FDUMP(0x100002,"Jump-hole ingress failed at %s.\n",Stage);
    }
    float WorldVisibility(FState const& State,FSpaceCamera* Camera,float const* ViewCentre,float Distance)
    {
        CObject const* Obj=State.Host->cobject();
        float Gain=1;
        if(Obj && (Obj->ObjectClass&CObject::ClassEqObj)==CObject::ClassEqObj)
            Gain*=1-JumpHoleSaturate(static_cast<CEqObj const*>(Obj)->CloakPercent);
        if(Gain<=0) return 0;
        if(Obj && Obj->Archetype)
        {
            float const Lod=Archetype::CliObjLodDistance(Obj->Archetype->Companion);
            if(std::isfinite(Lod) && Lod>0) Gain*=JumpHoleRangeVisibility(Distance,Lod);
        }
        int Type=State.EffectType;
        if(Type<0 || Type>=kEffectTypeCount) Type=EffectTypeIndexFromName("EFT_JUMP_EFFECTS");
        if(Type<0 || Type>=kEffectTypeCount) return 0;
        FEffectTypeInfo const* Info=EffectTypeInfoByIndex(Type);
        float const Perf=GetPerfGenericEffectPerf();
        if(Info->Priority<Perf) return 0;
        float const Limit=JumpHolePbubbleLimit(Info->PbubbleNear,Info->PbubbleFar,Perf);
        Gain*=JumpHoleRangeVisibility((std::fmax)(0.0f,-ViewCentre[2]-Info->Radius),Limit);
        if(GetGameOption(kGameOptAlchemyLod))
        {
            float Blend=1;
            // Blend is Alchemy's simulation detail, not opacity; only its cull is shared.
            if(!EffectTypeLodBlend(Type,AsCamera(Camera),-ViewCentre[2],&Blend)) return 0;
        }
        if(Gain<=0) return 0;
        if(GetGameOption(kGameOptNebula))
        {
            void* Field=GetSpaceFieldController();
            unsigned Enclosure=0;
            unsigned HostField=State.Host->Slot18c(&Enclosure);
            if(Field)
            {
                if(!HostField && GetSpaceFieldEnclosure()==2) return 0;
                if(HostField && HostField!=static_cast<unsigned>(reinterpret_cast<uintptr_t>(Field))) return 0;
                if(HostField && double(Distance)*Distance>GetSpaceFieldRadiusSq()) return 0;
            }
            float const Centre[]={State.World.Translation.X,State.World.Translation.Y,State.World.Translation.Z};
            Gain*=NebulaVolume::EffectVisibility(Camera->GetPosition(),Centre);
        }
        return Gain;
    }
    bool OpticsConstants(FSpaceCamera* Camera,float* P,float Time,float Opening,
                         float Activation,float Entry,float Gain)
    {
        auto* Ex=RenderEx::GetPipelineEx();
        FRPExTexture* DepthTexture=nullptr; unsigned long W=0,H=0;
        if (Ex->GetSceneDepth(&DepthTexture)!=GR_OK || !DepthTexture ||
            Ex->GetExTextureSize(DepthTexture,&W,&H)!=GR_OK || !W || !H) return false;
        int const* Vp=Camera->GetViewport();
        if (Vp[2]<Vp[0] || Vp[3]<Vp[1]) return false;
        P[0]=Time; P[1]=Opening; P[2]=Activation; P[3]=Entry;
        P[4]=1.0f/W; P[5]=1.0f/H; P[6]=.018f; P[7]=Gain;
        P[8]=(Vp[0]+.5f)/W; P[9]=(Vp[1]+.5f)/H;
        P[10]=(Vp[2]+.5f)/W; P[11]=(Vp[3]+.5f)/H;
        P[12]=Camera->GetZNear(); P[13]=Camera->GetZFar(); P[14]=0; P[15]=1;
        DALib::Pipeline->GetDepthRange(P+14,P+15);
        P[19]=145;
        P[20]=std::tan(Camera->GetHalfFovXDeg()*.01745329252f);
        P[21]=std::tan(Camera->GetFovYDeg()*.01745329252f);
        P[22]=600; P[23]=1;
        return std::isfinite(P[20]) && std::isfinite(P[21]) && P[20]>0 && P[21]>0;
    }
    bool DrawOptics(FSpaceCamera* Camera,FRPExProgram* Program,float const* P)
    {
        auto* Ex=RenderEx::GetPipelineEx();
        FRPExTexture* DepthTexture=nullptr;
        if (Ex->GetSceneDepth(&DepthTexture)!=GR_OK || !DepthTexture ||
            G_Capture->CaptureSceneColor(G_Copy)!=GR_OK) return false;
        int const* Vp=Camera->GetViewport();
        float const Width=float(Vp[2]-Vp[0]+1),Height=float(Vp[3]-Vp[1]+1);
        float const Remap[4]={Width*P[4],Height*P[5],(2*Vp[0]+Width)*P[4]-1,1-(2*Vp[1]+Height)*P[5]};
        FRPExSamplerState Linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
        FRPExSamplerState Point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
        FRPExSamplerState Noise={RPExFilterLinear,RPExMipNone,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
        FJumpHoleVertex const Quad[]={
            {{-1,1,0},0xffffffffu,{0,0}},{{1,1,0},0xffffffffu,{1,0}},
            {{-1,-1,0},0xffffffffu,{0,1}},{{1,-1,0},0xffffffffu,{1,1}}};
        FRPExPassDesc Pass={nullptr,0,0};
        if (Ex->BeginExPass(&Pass)!=GR_OK) return false;
        bool Ok=Ex->BindExProgram(Program)==GR_OK &&
            Ex->BindExTexture(0,G_Copy,&Linear)==GR_OK && Ex->BindExTexture(1,DepthTexture,&Point)==GR_OK &&
            Ex->BindExTexture(2,G_Noise,&Noise)==GR_OK && Ex->SetExVertexConstants(7,Remap,1)==GR_OK &&
            Ex->SetExPixelConstants(0,P,12)==GR_OK;
        if (Ok) Ok=RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,
            D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,Quad,4)==GR_OK;
        if (Ex->EndExPass()!=GR_OK) Ok=false;
        return Ok;
    }
    void DrawPlayerOptics(FSpaceCamera* Camera,FJumpShipEffect const* Effect,float Progress)
    {
        // This is reached only in the player-only tunnel rendering branch. Nearby
        // world geometry is never authorized merely by sharing a depth/ellipse.
        Vector Centre; float Radius=0,Projected[3]={};
        if (Effect->Ship->get_physical_radius(Radius,Centre)!=0 || !std::isfinite(Radius) || Radius<=0 ||
            Camera->ProjectVec(Projected,&Centre.x)==0 || !std::isfinite(Projected[2]) ||
            Projected[2]-Radius<=Camera->GetZNear()) return;
        float P[48]={};
        float const Envelope=JumpHoleIngressEnvelope(Effect->Field_0x70);
        if (!OpticsConstants(Camera,P,std::fmod(G_TransitTime+Effect->Field_0x70,96.0f),1,0,Envelope,1)) return;
        int const* Vp=Camera->GetViewport();
        float const RadiusScale=1.25f*Radius/(Projected[2]-Radius);
        P[36]=(Projected[0]+.5f)*P[4]; P[37]=(Projected[1]+.5f)*P[5];
        P[38]=RadiusScale*.5f*(Vp[2]-Vp[0]+1)*P[4]/P[20];
        P[39]=RadiusScale*.5f*(Vp[3]-Vp[1]+1)*P[5]/P[21];
        P[40]=Projected[2]; P[41]=Radius+2;
        P[42]=Envelope; P[43]=Progress;
        std::copy(G_TransitPalette,G_TransitPalette+4,P+44);
        if (!DrawOptics(Camera,G_OpticsShip,P)) LogTransitFailure("ship optics");
    }
}
#endif

bool JumpHoleVisualReplaceAttached(FClientGameobj* Host,unsigned EffectId)
{
#ifdef FREELANCER_RP9
    bool const Sparks=EffectId==CreateID("gf_wormsparks");
    bool const Body=EffectId==CreateID("gf_wormhole_01") || EffectId==CreateID("gf_wormhole_light") ||
        EffectId==CreateID("gf_wormhole_green") || EffectId==CreateID("gf_wormhole_orange") ||
        EffectId==CreateID("gf_wormhole_red") || EffectId==CreateID("gf_hole_01") || EffectId==CreateID("gf_hole_active_01") ||
        EffectId==CreateID("hole_center");
    if((!Sparks && !Body) || !Eligible(Host)) return false;
    auto* Solar=static_cast<FClientSolarGameobj*>(Host);
    FState& State=Track(Solar);
    State.HasIdle=true;
    if(Body) {
        FEffectArch const* Arch=FindEffectArch(&EffectId);
        if(Arch) State.EffectType=Arch->EffectType;
    }
    if(State.Fallback) return false;
    if(Claim(Solar)) return true;
    State.Fallback=true; // never mix an admitted original ALE with a later shader claim
#endif
    return false;
}
bool JumpHoleVisualReplaceActivation(FClientSolarGameobj* Host,unsigned EffectId)
{
#ifdef FREELANCER_RP9
    if(EffectId!=CreateID("gf_hole_01") && EffectId!=CreateID("wormholeactivation")) return false;
    if(!Claim(Host)) return false;
    FState& State=Track(Host);
    if(State.EffectType<0) {
        FEffectArch const* Arch=FindEffectArch(&EffectId);
        if(Arch) State.EffectType=Arch->EffectType;
    }
    return true;
#else
    return false;
#endif
}
void JumpHoleVisualTick(FClientSolarGameobj* Host,float Dt)
{
#ifdef FREELANCER_RP9
    auto It=G_States.find(Host);
    if(It==G_States.end() || !std::isfinite(Dt) || Dt<=0) return;
    FState& State=It->second;
    // Some authored anomalies spin; the entrance and its mirror follow the live solar.
    Transform const& World=Host->get_transform();
    for(int R=0;R<3;++R) for(int C=0;C<3;++C)
        State.World.Rotation.D[R][C]=World.Rotation.E[R][C];
    State.World.Translation={World.Translation.x,World.Translation.y,World.Translation.z};
    State.Phase.Tick(Dt);
    State.Approach=0;
    // Query the active docking behavior, not the selected target or mere proximity.
    auto* Player=static_cast<IObjRW*>(GetPlayerObjRW());
    IBehaviorManager* Behavior=Player ? GetBehaviorManager(Player) : nullptr;
    IObjRW const* Port=nullptr; int PortIndex=-1;
    if (State.Phase.Target>0 && Behavior && Behavior->get_docking_port(Port,PortIndex) &&
        Port && Port->get_id()==Host->get_id())
    {
        Vector const& Position=Player->get_position();
        float const Delta[3]={Position.x-State.World.Translation.X,
            Position.y-State.World.Translation.Y,Position.z-State.World.Translation.Z};
        float Local[3]={};
        for (int R=0;R<3;++R) for (int C=0;C<3;++C)
            Local[R]+=State.World.Rotation.D[C][R]*Delta[C];
        State.Approach=JumpHoleApproachStrength(true,Local[0],Local[1],Local[2]);
    }
#endif
}
void JumpHoleVisualEvent(FClientSolarGameobj* Host,int Sub)
{
#ifdef FREELANCER_RP9
    if (!Eligible(Host) || (Sub!=0 && Sub!=2 && Sub!=3)) return;
    FState& State=Track(Host);
    if (Sub==0) State.Phase.Open();
    else if (Sub==3) State.Phase.Target=0;
    else State.Phase.Close(); // solar subcode 2 closes the hole; it is not ship entry
#endif
}
void JumpHoleVisualForget(FClientSolarGameobj* Host)
{
#ifdef FREELANCER_RP9
    G_States.erase(Host);
#endif
}
#ifdef FREELANCER_RP9
static void DrawHole(FSpaceCamera* Camera,FState& State)
{
    if(!State.Claimed || !Eligible(State.Host)) return;
    float const Centre[3]={State.World.Translation.X,State.World.Translation.Y,State.World.Translation.Z};
    float ViewCentre[3];
    JumpHoleWorldToView(Camera->GetViewTransform(), Centre, ViewCentre);
    // The remaining funnel fits the original volume proxy.
    if (Camera->ClassifySphere(ViewCentre,920.0f)==1) return;
    float const* Eye=Camera->GetPosition();
    double DistanceSq=0;
    for(int I=0;I<3;++I) { double const D=double(Eye[I])-Centre[I]; DistanceSq+=D*D; }
    float const Distance=static_cast<float>(std::sqrt(DistanceSq));
    float Visibility=WorldVisibility(State,Camera,ViewCentre,Distance);
    if(Visibility<=0) return;
    int const* Vp=Camera->GetViewport();
    // Retail stores the vertical half-angle (SpaceCameraSetFovY takes tan directly).
    float const TanHalfFov=std::tan(Camera->GetFovYDeg()*0.01745329252f);
    float const PixelRadius=500.0f*(Vp[3]-Vp[1]+1)/
        ((std::fmax)(2.0f*TanHalfFov,0.01f)*(std::fmax)(Distance,1.0f));
    if (PixelRadius<=0.5f) return;
    float Gain=(std::fmin)(1.0f,(PixelRadius-0.5f)/3.5f);
    Gain=Gain*Gain*(3-2*Gain)*Visibility*JumpHoleExteriorVisibility(State.HasIdle,State.Phase.Opening);
    if(Gain<=0) return;
    ResolvePalette(State);
    if (!Ready()) return;
    auto* Ex=RenderEx::GetPipelineEx(); auto* Pipe=DALib::Pipeline;
    FRPExTexture* Depth=nullptr; unsigned long W=0,H=0;
    if (Ex->GetSceneDepth(&Depth)!=GR_OK || Ex->GetExTextureSize(Depth,&W,&H)!=GR_OK || !W || !H) return;
    Win3DApplyCamera(AsCamera(Camera));
    float V[52]={}; float const* View=Camera->GetViewTransform();
    float const Translation[3]={State.World.Translation.X,State.World.Translation.Y,State.World.Translation.Z};
    float LocalEye[3]={};
    for (int R=0;R<3;++R)
    {
        for (int C=0;C<3;++C)
        {
            V[R*4+C]=View[R*3+C]; V[32+R*4+C]=State.World.Rotation.D[R][C];
            LocalEye[R]+=State.World.Rotation.D[C][R]*(Eye[C]-Translation[C]);
        }
        V[R*4+3]=View[9+R]; V[35+R*4]=Translation[R];
    }
    if (Pipe->GetProjection(V+12)!=GR_OK) return;
    V[28]=float(Vp[2]-Vp[0]+1)/W; V[29]=float(Vp[3]-Vp[1]+1)/H;
    V[30]=2.0f*Vp[0]/W+V[28]-1; V[31]=1-2.0f*Vp[1]/H-V[29];
    V[44]=Camera->GetZNear(); V[45]=Camera->GetZFar();
    V[46]=0;V[47]=1;Pipe->GetDepthRange(V+46,V+47);
    float const Opening=JumpHoleSmooth(State.Phase.Opening);
    float P[32]={State.Phase.Time,Opening,State.Phase.Ripple,Gain,
        1.0f/W,1.0f/H,.018f,0,
        (Vp[0]+.5f)/W,(Vp[1]+.5f)/H,(Vp[2]+.5f)/W,(Vp[3]+.5f)/H,
        V[44],V[45],V[46],V[47],LocalEye[0],LocalEye[1],LocalEye[2],0,
        State.Phase.ActivationEnvelope(),State.Phase.ActivationAge/JumpHoleActivationDuration,
        State.Approach*.90f,State.Approach*.65f};
    std::copy(State.Palette,State.Palette+4,P+28);
    for(int I=0;I<4;++I) V[48+I]=P[I];
    if (G_Capture->CaptureSceneColor(G_Copy)!=GR_OK) { LogDrawFailure(State,"capture"); return; }
    FRPExSamplerState Linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState Point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState Noise={RPExFilterLinear,RPExMipNone,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
    unsigned SuccessfulDraws=0;
    for (int PassIndex=0;PassIndex<2;++PassIndex)
    {
        // Both passes sample scene depth and clamp the volume interval manually.
        FRPExPassDesc Pass={nullptr,0,0};
        if (Ex->BeginExPass(&Pass)!=GR_OK) { LogDrawFailure(State,"begin pass"); return; }
        bool Ok=Ex->BindExProgram(PassIndex ? G_Glow : G_Lens)==GR_OK &&
            Ex->BindExTexture(2,G_Noise,&Noise)==GR_OK &&
            Ex->SetExVertexConstants(0,V,13)==GR_OK && Ex->SetExPixelConstants(0,P,8)==GR_OK;
        Ok=Ok && Ex->BindExTexture(1,Depth,&Point)==GR_OK;
        if (!PassIndex) Ok=Ok && Ex->BindExTexture(0,G_Copy,&Linear)==GR_OK;
        else
        {
            Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE,1);
            Pipe->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
            Pipe->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
            Pipe->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
        }
        if (Ok) Ok=RenderEx::GetDrawEx()->DrawExVertexBuffer(G_Mesh,D3DPT_TRIANGLELIST,
            D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,sizeof(FJumpHoleVertex),0,
            JumpHoleVertexCount/3)==GR_OK;
        if (Ex->EndExPass()!=GR_OK) Ok=false;
        if (Ok) ++SuccessfulDraws;
        else LogDrawFailure(State,"bind/draw/end pass");
    }
    if (SuccessfulDraws==2 && !State.LoggedDraw)
    {
        State.LoggedDraw=true;
        FDUMP(0x100003,"Jump-hole cloud drawn %08x world=(%.1f %.1f %.1f) distance=%.1f near=%.1f far=%.1f open=%.3f.\n",
              State.Host->get_id(),Centre[0],Centre[1],Centre[2],Distance,V[44],V[45],Opening);
    }
    if (SuccessfulDraws==2)
    {
        float Optics[48]={};
        if (OpticsConstants(Camera,Optics,State.Phase.Time,Opening,
            State.Phase.ActivationEnvelope(),State.Approach*.90f,Gain))
        {
            for (int I=0;I<3;++I) Optics[16+I]=LocalEye[I];
            std::copy(State.Palette,State.Palette+4,Optics+44);
            JumpHoleCameraToLocal(View,&State.World.Rotation.D[0][0],Optics+24);
            if (!DrawOptics(Camera,G_OpticsWorld,Optics)) LogDrawFailure(State,"world optics");
        }
    }
}
#endif
void JumpHoleVisualDraw(FSpaceCamera* Camera)
{
#ifdef FREELANCER_RP9
    if(!Camera || !GetGameOption(kGameOptEffectsGroup) || !GetGameOption(kGameOptParticles)) return;
    std::vector<FState*> Ordered;
    for(auto& Pair:G_States) if(Pair.second.Claimed) Ordered.push_back(&Pair.second);
    float const* Eye=Camera->GetPosition();
    auto Dist=[&](FState const* S) {
        double X=S->World.Translation.X-Eye[0],Y=S->World.Translation.Y-Eye[1],Z=S->World.Translation.Z-Eye[2];
        return X*X+Y*Y+Z*Z;
    };
    std::sort(Ordered.begin(),Ordered.end(),[&](FState const* A,FState const* B){return Dist(A)>Dist(B);});
    for(FState* State:Ordered) DrawHole(Camera,*State);
#endif
}
void JumpHoleVisualBindTransit(FJumpShipEffect const* Effect,FClientSolarGameobj* Host)
{
#ifdef FREELANCER_RP9
    if (!Effect || !Effect->Ship ||
        static_cast<void*>(static_cast<IObjRW*>(Effect->Ship))!=GetPlayerObjRW() || !Claim(Host)) return;
    G_Transit=Effect;
    FState& State=Track(Host);
    ResolvePalette(State);
    G_TransitTime=State.Phase.Time;
    std::copy(State.Palette,State.Palette+4,G_TransitPalette);
    G_TransitLogged=false;
#endif
}
void JumpHoleVisualForgetTransit(FJumpShipEffect const* Effect)
{
#ifdef FREELANCER_RP9
    if (G_Transit==Effect) G_Transit=nullptr;
#endif
}
bool JumpHoleVisualDrawIngress(FSpaceCamera* Camera,FJumpShipEffect const* Effect)
{
#ifdef FREELANCER_RP9
    if (!Camera || !Effect || Effect!=G_Transit || !Effect->Ship ||
        PortConfigInt("Render","jumphole_visual",1)==0 || !GetGameOption(kGameOptEffectsGroup)) return false;
    int const State=Effect->Ship->Field_0x158;
    // Keep this instance's exterior approach, then carry the burst into state 2.
    // A hole's state 1 lasts at most one update; it cannot contain a timed buildup.
    if (State==1) return true;
    if (State!=2) return false;
    float const Elapsed=Effect->Field_0x70;
    if (!std::isfinite(Elapsed) || Elapsed<0) return false;
    if (Elapsed>=JumpHoleIngressDuration) return true;
    if (!Ready()) return false;
    auto* Ex=RenderEx::GetPipelineEx(); auto* Pipe=DALib::Pipeline;
    FRPExTexture* DepthTexture=nullptr; unsigned long W=0,H=0;
    if (Ex->GetSceneDepth(&DepthTexture)!=GR_OK || !DepthTexture ||
        Ex->GetExTextureSize(DepthTexture,&W,&H)!=GR_OK || !W || !H) return false;
    int const* Vp=Camera->GetViewport();
    float const Width=float(Vp[2]-Vp[0]+1),Height=float(Vp[3]-Vp[1]+1);
    if (Width<=0 || Height<=0) return false;
    float const Remap[4]={Width/W,Height/H,(2*Vp[0]+Width)/W-1,1-(2*Vp[1]+Height)/H};
    float DepthMin=0,DepthMax=1;
    Pipe->GetDepthRange(&DepthMin,&DepthMax);
    float const Progress=Elapsed/JumpHoleIngressDuration;
    float P[32]={std::fmod(G_TransitTime+Elapsed,96.0f),1,0,1,
        1.0f/W,1.0f/H,.018f,0,
        (Vp[0]+.5f)/W,(Vp[1]+.5f)/H,(Vp[2]+.5f)/W,(Vp[3]+.5f)/H,
        Camera->GetZNear(),Camera->GetZFar(),DepthMin,DepthMax,
        0,0,-360+760*JumpHoleSmooth(Progress),0,
        0,1,JumpHoleIngressEnvelope(Elapsed),Progress,
        std::tan(Camera->GetHalfFovXDeg()*.01745329252f),
        std::tan(Camera->GetFovYDeg()*.01745329252f),0,0};
    std::copy(G_TransitPalette,G_TransitPalette+4,P+28);
    if (G_Capture->CaptureSceneColor(G_Copy)!=GR_OK) { LogTransitFailure("ingress capture"); return false; }
    FRPExSamplerState Linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState Point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState Noise={RPExFilterLinear,RPExMipNone,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
    FJumpHoleVertex const Quad[]={
        {{-1,1,0},0xffffffffu,{0,0}},{{1,1,0},0xffffffffu,{1,0}},
        {{-1,-1,0},0xffffffffu,{0,1}},{{1,-1,0},0xffffffffu,{1,1}}};
    FRPExPassDesc Pass={nullptr,0,0};
    if (Ex->BeginExPass(&Pass)!=GR_OK) { LogTransitFailure("ingress begin"); return false; }
    bool Ok=Ex->BindExProgram(G_Ingress)==GR_OK &&
        Ex->BindExTexture(0,G_Copy,&Linear)==GR_OK && Ex->BindExTexture(1,DepthTexture,&Point)==GR_OK &&
        Ex->BindExTexture(2,G_Noise,&Noise)==GR_OK && Ex->SetExVertexConstants(7,Remap,1)==GR_OK &&
        Ex->SetExPixelConstants(0,P,8)==GR_OK;
    if (Ok) Ok=RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,
        D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,Quad,4)==GR_OK;
    if (Ex->EndExPass()!=GR_OK) Ok=false;
    if (!Ok) LogTransitFailure("ingress draw");
    else if (!G_TransitLogged)
    {
        G_TransitLogged=true;
        FDUMP(0x100003,"Jump-hole ingress drawn elapsed=%.3f.\n",Elapsed);
    }
    if (Ok) DrawPlayerOptics(Camera,Effect,Progress);
    return Ok;
#else
    return false;
#endif
}
void JumpHoleVisualRenderShutdown()
{
#ifdef FREELANCER_RP9
    ReleaseResources(); G_Failed=false; G_States.clear(); G_Transit=nullptr;
#endif
}
