#include "tradelane_visual.h"
#include "tradelane_visual_style.h"

#ifdef FREELANCER_RP9
#include "tradelane_visual_mesh.h"
#include "tradelane_visual_noise.h"
#include "client_gameobj.h"
#include "client_objdb.h"
#include "gate_tunnel.h"
#include "jump_effect.h"
#include "star_sys.h"
#include "DALib.h"
#include "dacom.h"
#include "dacom_iids.h"
#include "game_options.h"
#include "render_ex.h"
#include "space_camera.h"
#include "win3d_render.h"
#include "x86math.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/IRPSceneCapture.h"
#include <cmath>
#include <vector>

namespace
{
    struct FTravelState
    {
        FMatrix Rotation = {};
        float Previous[3] = {};
        double Phase = 0;
        float Time = 0, Age = 0, Intensity = 0, ExitAge = 0, ExitIntensity = 0;
        bool Active = false, Stopping = false;
        FTradeLaneVisualStyle Style;
    };
    FTravelState G_Travel;
    FTradeLaneVertex G_Vertices[TradeLaneVertexCount];
    bool G_GeometryReady = false, G_ProgramTried = false;
    FRPExProgram* G_Program = nullptr;
    FRPExProgram* G_WarpProgram = nullptr;
    FRPExBuffer* G_Buffer = nullptr;
    FRPExTexture* G_SceneCopy = nullptr;
    FRPExTexture* G_Noise = nullptr;
    IRPSceneCapture* G_Capture = nullptr;

    bool SupportedTunnel(unsigned Id, unsigned& Mode)
    {
        static unsigned const Named[] = {CreateID("gate_tunnel_edge"), CreateID("gate_tunnel_crow"),
            CreateID("gate_tunnel_barrier"), CreateID("gate_tunnel_walker"), CreateID("gate_tunnel_dark")};
        for (unsigned I = 0; I < 5; ++I)
            if (Id == Named[I]) { Mode = I + 1; return true; }
        static unsigned const Retail[] = {CreateID("gate_tunnel_bretonia"), CreateID("gate_tunnel_liberty"),
            CreateID("gate_tunnel_br"), CreateID("gate_tunnel_ku"), CreateID("gate_tunnel_rh")};
        for (unsigned Candidate : Retail)
            if (Id == Candidate) { Mode = 0; return true; }
        return false;
    }

    FTradeLaneVisualStyle ResolveStyle(FTransform const& Lane, unsigned RouteId)
    {
        std::vector<FTradeLaneStyleCandidate> Candidates;
        int const Kind = 2;
        for (FClientGameobj* Object = ClientObjDb_GetKindHead(&Kind); Object; Object = Object->ListNext)
        {
            // Actual jump gates only: holes, anomalies and arbitrary solars do not vote.
            unsigned Type = 0;
            if (Object->get_type(Type) != 0 || (Type & 0x40u) == 0) continue;
            auto const* Solar = static_cast<FClientSolarGameobj const*>(Object);
            FJumpEffectDesc const* Desc = JumpEffectFindDesc(Solar->Field_0x200.Id);
            unsigned Mode = 0;
            if (!Desc || !SupportedTunnel(Desc->JumpTunnel.Id, Mode)) continue;
            FGateTunnel const* Tunnel = nullptr;
            for (FGateTunnel const* Candidate : G_GateTunnels)
                if (Candidate && Candidate->Id.Id == Desc->JumpTunnel.Id) { Tunnel = Candidate; break; }
            if (!Tunnel || Tunnel->LayerCount < 1 || Tunnel->LayerCount > 2) continue;
            FTradeLaneStyleCandidate Candidate;
            FVector const Zero = {};
            FVector const& Layer1 = Tunnel->LayerCount > 1 ? Tunnel->Layers[1].Color : Zero;
            if (!TradeLaneBuildPalette(Candidate.Style, &Tunnel->Layers[0].Color.X, &Layer1.X,
                                       &Tunnel->MinRgb.X, &Tunnel->MaxRgb.X, Mode)) continue;
            Candidate.TunnelId = Tunnel->Id.Id;
            Candidate.GateId = Object->get_id();
            Vector const& Position = Object->get_position();
            double const X = double(Position.x) - Lane.Translation.X;
            double const Y = double(Position.y) - Lane.Translation.Y;
            double const Z = double(Position.z) - Lane.Translation.Z;
            Candidate.DistanceSq = X * X + Y * Y + Z * Z;
            Candidates.push_back(Candidate);
        }
        FTradeLaneVisualStyle Result;
        std::size_t const Best = TradeLaneSelectStyleCandidate(Candidates.data(), Candidates.size());
        if (Best != Candidates.size()) Result = Candidates[Best].Style;
        TradeLaneSeedStyle(Result, StarSysGetActiveSystemId(), RouteId);
        return Result;
    }

    void ReleaseResources()
    {
        IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
        if (Ex && G_Program) Ex->DestroyExProgram(G_Program);
        if (Ex && G_WarpProgram) Ex->DestroyExProgram(G_WarpProgram);
        if (Ex && G_Buffer) Ex->DestroyExVertexBuffer(G_Buffer);
        if (Ex && G_SceneCopy) Ex->DestroyExTexture(G_SceneCopy);
        if (Ex && G_Noise) Ex->DestroyExTexture(G_Noise);
        if (G_Capture) G_Capture->Release();
        G_Program = G_WarpProgram = nullptr;
        G_Buffer = nullptr;
        G_SceneCopy = G_Noise = nullptr;
        G_Capture = nullptr;
    }

    float Smooth(float T)
    {
        T = T < 0 ? 0 : T > 1 ? 1 : T;
        return T * T * (3.0f - 2.0f * T);
    }

    void BuildGeometry()
    {
        if (G_GeometryReady) return;
        BuildTradeLaneVisualMesh(G_Vertices);
        G_GeometryReady = true;
    }

    bool EnsureProgram()
    {
        if (G_Program && G_Buffer && G_Noise) return true;
        if (G_ProgramTried || !RenderEx::IsAvailable()) return false;
        G_ProgramTried = true;
        IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
        if (Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\tradelane_corridor.hlsl",
                                "VSMain", "PSMain", &G_Program) != GR_OK)
        {
            ReleaseResources();
            FDUMP(0x100002, "Trade lane corridor shader unavailable; player travel sound remains active.\n");
            return false;
        }
        BuildGeometry();
        if (Ex->CreateExVertexBuffer(sizeof(G_Vertices), G_Vertices, &G_Buffer) != GR_OK)
        {
            ReleaseResources();
            return false;
        }
        std::vector<std::uint32_t> Noise(TradeLaneNoiseSize * TradeLaneNoiseSize * TradeLaneNoiseSize);
        BuildTradeLaneNoise(Noise.data());
        if (Ex->CreateExVolumeTexture(TradeLaneNoiseSize, TradeLaneNoiseSize, TradeLaneNoiseSize,
                                     RPExFormatA8R8G8B8, Noise.data(), &G_Noise) != GR_OK)
        {
            ReleaseResources();
            FDUMP(0x100002, "Trade lane volume noise unavailable; player travel sound remains active.\n");
            return false;
        }
        // Optional capture interface: old RP9 builds retain the procedural glow.
        if (DALib::Pipeline->QueryInterface(Iids::RPSceneCapture,
                reinterpret_cast<void**>(&G_Capture)) == GR_OK && G_Capture)
        {
            FRPExRenderTargetDesc Target = {0, 0, 1.0f, RPExFormatA8R8G8B8};
            if (Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\tradelane_corridor.hlsl",
                    "VSMain", "PSWarp", &G_WarpProgram) != GR_OK)
            {
                if (G_WarpProgram) Ex->DestroyExProgram(G_WarpProgram);
                G_WarpProgram = nullptr;
            }
            if (G_WarpProgram && Ex->CreateExRenderTarget(&Target, &G_SceneCopy) != GR_OK)
            {
                if (G_SceneCopy) Ex->DestroyExTexture(G_SceneCopy);
                G_SceneCopy = nullptr;
            }
        }
        if (!G_WarpProgram || !G_SceneCopy)
        {
            if (G_WarpProgram) Ex->DestroyExProgram(G_WarpProgram);
            if (G_SceneCopy) Ex->DestroyExTexture(G_SceneCopy);
            if (G_Capture) G_Capture->Release();
            G_WarpProgram = nullptr;
            G_SceneCopy = nullptr;
            G_Capture = nullptr;
        }
        return true;
    }
}
#endif

FTradeLaneVisualStyle TradeLaneVisualResolveStyle(FTransform const& Lane, unsigned RouteId)
{
#ifdef FREELANCER_RP9
    return ResolveStyle(Lane, RouteId);
#else
    return FTradeLaneVisualStyle();
#endif
}

void TradeLaneVisualStart(FTransform const& Lane, unsigned RouteId)
{
#ifdef FREELANCER_RP9
    // Crossings keep the original straight-lane basis and scroll phase.
    if (G_Travel.Active && !G_Travel.Stopping) return;
    G_Travel = FTravelState();
    G_Travel.Active = true;
    G_Travel.Rotation = Lane.Rotation;
    G_Travel.Style = TradeLaneVisualResolveStyle(Lane, RouteId);
    G_Travel.Previous[0] = Lane.Translation.X;
    G_Travel.Previous[1] = Lane.Translation.Y;
    G_Travel.Previous[2] = Lane.Translation.Z;
#endif
}

void TradeLaneVisualStop()
{
#ifdef FREELANCER_RP9
    if (!G_Travel.Active || G_Travel.Stopping) return;
    G_Travel.Stopping = true;
    G_Travel.ExitAge = 0;
    G_Travel.ExitIntensity = G_Travel.Intensity;
#endif
}

void TradeLaneVisualTick(float Dt, float X, float Y, float Z)
{
#ifdef FREELANCER_RP9
    if (!G_Travel.Active || !std::isfinite(Dt) || Dt <= 0) return;
    float const Position[3] = {X, Y, Z};
    double Distance = 0;
    // Freelancer travels along local -Z (LaneAction::Update advances along -column 2).
    for (int I = 0; I < 3; ++I)
    {
        Distance -= (double(Position[I]) - G_Travel.Previous[I]) * G_Travel.Rotation.D[I][2];
        G_Travel.Previous[I] = Position[I];
    }
    G_Travel.Phase = std::fmod(G_Travel.Phase + Distance / 1600.0, 1024.0);
    if (G_Travel.Phase < 0) G_Travel.Phase += 1024.0;
    // Keep the clock bounded; shader time harmonics repeat over 96 seconds.
    G_Travel.Time = std::fmod(G_Travel.Time + Dt, 96.0f);
    G_Travel.Age += Dt;
    if (G_Travel.Age > 2.0f) G_Travel.Age = 2.0f;
    if (G_Travel.Stopping)
    {
        G_Travel.ExitAge += Dt;
        G_Travel.Intensity = G_Travel.ExitIntensity * (1.0f - Smooth(G_Travel.ExitAge / 0.65f));
        if (G_Travel.ExitAge >= 0.65f) TradeLaneVisualReset();
    }
    else G_Travel.Intensity = Smooth(G_Travel.Age / 0.30f);
#endif
}

void TradeLaneVisualReset()
{
#ifdef FREELANCER_RP9
    G_Travel = FTravelState();
#endif
}

void TradeLaneVisualDraw(FSpaceCamera* Camera)
{
#ifdef FREELANCER_RP9
    if (!G_Travel.Active || G_Travel.Intensity <= 0 || !Camera ||
        !GetGameOption(kGameOptEffectsGroup) ||
        (Camera != GetFirstPersonSpaceCamera() && Camera != GetThirdPersonSpaceCamera() &&
         Camera != GetTurretSpaceCamera() && Camera != GetRearViewSpaceCamera()) || !EnsureProgram()) return;
    Win3DApplyCamera(AsCamera(Camera));
    float V[44] = {};
    float const* View = Camera->GetViewTransform();
    float const* Position = Camera->GetPosition();
    for (int Row = 0; Row < 3; ++Row)
    {
        for (int Col = 0; Col < 3; ++Col)
        {
            V[Row * 4 + Col] = View[Row * 3 + Col];
            V[32 + Row * 4 + Col] = G_Travel.Rotation.D[Row][Col];
        }
        V[Row * 4 + 3] = View[9 + Row];
        V[32 + Row * 4 + 3] = Position[Row];
    }
    IRenderPipeline* const Pipe = DALib::Pipeline;
    if (Pipe->GetProjection(V + 12) != GR_OK) return;
    V[28] = V[29] = 1.0f;
    int const* Vp = Camera->GetViewport();
    FRPExTexture* Depth = nullptr;
    unsigned long W = 0, H = 0;
    IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
    // Ex passes reset the viewport to the full target, even without sampled depth.
    // The full-size scene copy also provides dimensions on devices without INTZ.
    if (Ex->GetSceneDepth(&Depth) != GR_OK) Depth = nullptr;
    if (!Depth || Ex->GetExTextureSize(Depth, &W, &H) != GR_OK) W = H = 0;
    if ((!W || !H) && G_SceneCopy && Ex->GetExTextureSize(G_SceneCopy, &W, &H) != GR_OK)
        W = H = 0;
    // Unknown target dimensions cannot safely preserve a cinematic/sub-view viewport.
    if (!W || !H) return;
    V[28] = float(Vp[2] - Vp[0] + 1) / W; V[29] = float(Vp[3] - Vp[1] + 1) / H;
    V[30] = 2.0f * Vp[0] / W + V[28] - 1.0f;
    V[31] = 1.0f - 2.0f * Vp[1] / H - V[29];
    float const Pulse = G_Travel.Stopping ? 0.0f :
        Smooth(G_Travel.Age / 0.12f) * (1.0f - Smooth((G_Travel.Age - 0.12f) / 0.38f));
    float DepthMin = 0.0f, DepthMax = 1.0f;
    Pipe->GetDepthRange(&DepthMin, &DepthMax);
    FTradeLaneVisualStyle const& Style = G_Travel.Style;
    float const P[32] = {float(G_Travel.Phase), G_Travel.Time, G_Travel.Intensity, Pulse,
                        Style.Body[0], Style.Body[1], Style.Body[2], Style.Enabled,
                        W ? 1.0f / W : 0, H ? 1.0f / H : 0, 0.055f, 0,
                        W ? (Vp[0] + 0.5f) / W : 0, H ? (Vp[1] + 0.5f) / H : 0,
                        W ? (Vp[2] + 0.5f) / W : 1, H ? (Vp[3] + 0.5f) / H : 1,
                        Camera->GetZNear(), Camera->GetZFar(), DepthMin, DepthMax,
                        G_Travel.Age, G_Travel.Stopping ? G_Travel.ExitAge / 0.65f : 0.0f,
                        G_Travel.Stopping ? 1.0f : 0.0f, 1.0f,
                        Style.Accent[0], Style.Accent[1], Style.Accent[2], Style.Mode,
                        Style.Seed[0], Style.Seed[1], Style.Seed[2], Style.Seed[3]};
    FRPExSamplerState NoiseSampler = {RPExFilterLinear, RPExMipNone,
        RPExAddressWrap, RPExAddressWrap, RPExAddressWrap};
    // Snapshot once before our glow. HUD is drawn later. The depth-aware warp protects
    // nearby hulls and the cockpit, including the displaced sample's filtering footprint.
    if (G_WarpProgram && G_SceneCopy && G_Capture && Depth && W && H &&
        G_Capture->CaptureSceneColor(G_SceneCopy) == GR_OK)
    {
        FRPExPassDesc WarpPass = {nullptr, 0, 0};
        if (Ex->BeginExPass(&WarpPass) == GR_OK)
        {
            FRPExSamplerState Linear = {RPExFilterLinear, RPExMipNone,
                RPExAddressClamp, RPExAddressClamp, RPExAddressClamp};
            FRPExSamplerState Point = {RPExFilterPoint, RPExMipNone,
                RPExAddressClamp, RPExAddressClamp, RPExAddressClamp};
            if (Ex->BindExProgram(G_WarpProgram) == GR_OK &&
                Ex->BindExTexture(0, G_SceneCopy, &Linear) == GR_OK &&
                Ex->BindExTexture(1, Depth, &Point) == GR_OK &&
                Ex->BindExTexture(2, G_Noise, &NoiseSampler) == GR_OK &&
                Ex->SetExVertexConstants(0, V, 11) == GR_OK &&
                Ex->SetExVertexConstants(11, P, 1) == GR_OK &&
                Ex->SetExVertexConstants(12, P + 16, 1) == GR_OK &&
                Ex->SetExPixelConstants(0, P, 8) == GR_OK)
                RenderEx::GetDrawEx()->DrawExVertexBuffer(G_Buffer, D3DPT_TRIANGLELIST,
                    D3DFVF_XYZ | D3DFVF_DIFFUSE | D3DFVF_TEX1, sizeof(FTradeLaneVertex),
                    0, TradeLaneCorridorVertexCount / 3);
            Ex->EndExPass();
        }
    }
    FRPExPassDesc Pass = {nullptr, RPExPassKeepDepth, 0};
    if (Ex->BeginExPass(&Pass) != GR_OK) return;
    Pipe->SetRenderState(D3DRS_ZENABLE, 1);
    Pipe->SetRenderState(D3DRS_ZWRITEENABLE, 0);
    Pipe->SetRenderState(D3DRS_ZFUNC, D3DCMP_LESSEQUAL);
    Pipe->SetRenderState(D3DRS_CULLMODE, D3DCULL_NONE);
    Pipe->SetRenderState(D3DRS_ALPHATESTENABLE, 0);
    Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 1);
    Pipe->SetRenderState(D3DRS_SRCBLEND, D3DBLEND_ONE);
    Pipe->SetRenderState(D3DRS_DESTBLEND, D3DBLEND_INVSRCALPHA);
    Pipe->SetRenderState(D3DRS_BLENDOP, D3DBLENDOP_ADD);
    if (Ex->BindExProgram(G_Program) == GR_OK &&
        Ex->BindExTexture(2, G_Noise, &NoiseSampler) == GR_OK &&
        Ex->SetExVertexConstants(0, V, 11) == GR_OK &&
        Ex->SetExVertexConstants(11, P, 1) == GR_OK &&
        Ex->SetExVertexConstants(12, P + 16, 1) == GR_OK &&
        Ex->SetExPixelConstants(0, P, 8) == GR_OK)
        RenderEx::GetDrawEx()->DrawExVertexBuffer(G_Buffer, D3DPT_TRIANGLELIST,
            D3DFVF_XYZ | D3DFVF_DIFFUSE | D3DFVF_TEX1, sizeof(FTradeLaneVertex),
            0, TradeLaneVertexCount / 3);
    Ex->EndExPass();
#endif
}

void TradeLaneVisualRenderShutdown()
{
#ifdef FREELANCER_RP9
    ReleaseResources();
    G_ProgramTried = false;
#endif
}
