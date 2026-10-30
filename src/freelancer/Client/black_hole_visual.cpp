#include "black_hole_visual.h"
#ifdef FREELANCER_RP9
#include "jumphole_visual_geometry.h"
#include "tradelane_visual_noise.h"
#include "client_gameobj.h"
#include "common_cobject.h"
#include "gf_thorn_psys.h"
#include "space_camera.h"
#include "game_options.h"
#include "port_config.h"
#include "render_ex.h"
#include "win3d_render.h"
#include "x86math.h"
#include "DALib.h"
#include "dacom_iids.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/IRPSceneCapture.h"
#include <cmath>
#include <cstring>
#include <vector>
#include <map>
#include <algorithm>
#include <cstdio>
#include <windows.h>

namespace
{
    struct FState
    {
        FClientSolarGameobj* Host = nullptr;
        FThornPsys* Thorn = nullptr;
        FTransform World = {};
        float Time = 0;
        bool Claimed = false, Fallback = false, LoggedDraw = false, LoggedFailure = false;
    };
    std::map<FClientSolarGameobj*, FState> G_States;
    std::map<FThornPsys*, FState> G_Thorn;
    FRPExProgram* G_Program = nullptr;
    FRPExProgram* G_Composite = nullptr; // PSComposite: the reduced-resolution march brought up to the screen
    FRPExTexture* G_Half = nullptr;      // that march target (port.ini black_hole_resolution)
    bool G_HalfTried = false;
    FRPExTexture* G_Noise = nullptr;
    FRPExTexture* G_Copy = nullptr;
    FRPExTexture* G_Ring = nullptr; // the mod's own disc picture (DATA_EXTRA/TEXTURES/bh_ring.tga)
    bool G_RingTried = false;
    IRPSceneCapture* G_Capture = nullptr;
    bool G_Failed = false;
    int G_DebugMode = 0; // console "bh": bits that switch parts of the shader off

    unsigned StateId(FState const& State)
    {
        return State.Host ? static_cast<unsigned>(State.Host->get_id())
                          : static_cast<unsigned>(reinterpret_cast<uintptr_t>(State.Thorn));
    }
    void LogDrawFailure(FState& State,char const* Stage)
    {
        if (State.LoggedFailure) return;
        State.LoggedFailure = true;
        FDUMP(0x100002,"Black hole %08x failed at %s.\n",StateId(State),Stage);
    }
    // Archetype nicknames from [Render] black_hole_archetypes, parsed once.
    std::vector<unsigned> const& Archetypes()
    {
        static std::vector<unsigned> Ids;
        static bool Parsed = false;
        if (Parsed) return Ids;
        Parsed = true;
        char Buffer[512] = {};
        PortConfigString("Render","black_hole_archetypes","BlackHoleCore",Buffer,sizeof(Buffer));
        char* Context = nullptr;
        for (char* Token = strtok_s(Buffer,",",&Context); Token; Token = strtok_s(nullptr,",",&Context))
        {
            while (*Token==' ' || *Token=='\t') ++Token;
            char* End = Token + std::strlen(Token);
            while (End>Token && (End[-1]==' ' || End[-1]=='\t' || End[-1]=='\r' || End[-1]=='\n')) *--End = 0;
            if (*Token) Ids.push_back(CreateID(Token));
        }
        return Ids;
    }
    bool Eligible(FClientGameobj* Host)
    {
        if (!Host || PortConfigInt("Render","black_hole_visual",1)==0 || Host->ManagerKind!=2) return false;
        CObject const* Obj = Host->cobject();
        if (!Obj || !Obj->Archetype) return false;
        unsigned const Id = Obj->Archetype->get_id();
        for (unsigned Wanted : Archetypes()) if (Wanted==Id) return true;
        return false;
    }
    void ReleaseResources()
    {
        auto* Ex = RenderEx::GetPipelineEx();
        if (Ex && G_Program) Ex->DestroyExProgram(G_Program);
        if (Ex && G_Composite) Ex->DestroyExProgram(G_Composite);
        if (Ex && G_Half) Ex->DestroyExTexture(G_Half);
        G_Composite = nullptr; G_Half = nullptr; G_HalfTried = false;
        if (Ex && G_Noise) Ex->DestroyExTexture(G_Noise);
        if (Ex && G_Copy) Ex->DestroyExTexture(G_Copy);
        if (Ex && G_Ring) Ex->DestroyExTexture(G_Ring);
        if (G_Capture) G_Capture->Release();
        G_Program = nullptr; G_Noise = G_Copy = G_Ring = nullptr; G_Capture = nullptr; G_RingTried = false;
    }
    // NeedDepth is false for base rooms, where the scene depth may not exist yet at spawn.
    bool Ready(bool NeedDepth = true)
    {
        if (G_Failed || !RenderEx::IsAvailable()) return false;
        auto* Ex = RenderEx::GetPipelineEx();
        if (NeedDepth)
        {
            FRPExTexture* Depth = nullptr;
            unsigned long W = 0, H = 0;
            // Do not claim the original particles until all essential GPU facilities exist.
            if (Ex->GetSceneDepth(&Depth) != GR_OK || !Depth ||
                Ex->GetExTextureSize(Depth, &W, &H) != GR_OK || !W || !H) return false;
        }
        if (G_Program && G_Noise && G_Copy && G_Capture) return true;
        FRPExRenderTargetDesc Desc = {0,0,1.0f,RPExFormatA8R8G8B8};
        bool Ok = DALib::Pipeline->QueryInterface(Iids::RPSceneCapture,
            reinterpret_cast<void**>(&G_Capture)) == GR_OK && G_Capture;
        if (Ok) Ok = Ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\black_hole.hlsl",
                                         "VSMain", "PSMain", &G_Program) == GR_OK;
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
            FDUMP(0x100002,"Black hole renderer unavailable; retaining attached ALE effects.\n");
        }
        return Ok;
    }
    // The disc picture of the retail-mod ring effect (bhflash.txm "bhring", 1024 mip), a top-down
    // view: black hole, white-hot rim, red spiral bands with dark slits between them. Loaded as a
    // one-slice volume texture (the Ex interface has no plain 2D textures). Optional: without the
    // file the shader keeps its own disc.
    void LoadRing()
    {
        if (G_RingTried) return;
        G_RingTried = true;
        char Path[MAX_PATH] = {};
        if (!GetModuleFileNameA(nullptr,Path,MAX_PATH)) return;
        char* Slash = std::strrchr(Path,'\\');
        if (!Slash) return;
        Slash[1] = 0;
        std::string const File = std::string(Path)+"..\\DATA_EXTRA\\TEXTURES\\bh_ring.tga";
        FILE* F = std::fopen(File.c_str(),"rb");
        if (!F) return;
        unsigned char Header[18] = {};
        std::vector<std::uint32_t> Texels;
        unsigned W = 0, H = 0;
        if (std::fread(Header,1,18,F)==18 && Header[2]==2 && Header[16]==32)
        {
            W = Header[12] | (Header[13]<<8); H = Header[14] | (Header[15]<<8);
            std::fseek(F,18+Header[0],SEEK_SET);
            Texels.resize(size_t(W)*H);
            if (!W || !H || std::fread(Texels.data(),4,Texels.size(),F)!=Texels.size()) Texels.clear();
        }
        std::fclose(F);
        if (Texels.empty()) return;
        if (!(Header[17]&0x20)) // bottom-up rows: make the first row the top one
            for (unsigned Y=0;Y<H/2;++Y)
                std::swap_ranges(Texels.begin()+size_t(Y)*W,Texels.begin()+size_t(Y+1)*W,Texels.begin()+size_t(H-1-Y)*W);
        auto* Ex = RenderEx::GetPipelineEx();
        if (Ex->CreateExVolumeTexture(W,H,1,RPExFormatA8R8G8B8,Texels.data(),&G_Ring)!=GR_OK) G_Ring = nullptr;
        FDUMP(0x100003,"Black hole disc picture %s (%ux%u).\n",G_Ring ? "loaded" : "failed",W,H);
    }
    void CopyTransform(FState& State,FClientSolarGameobj* Host)
    {
        Transform const& World=Host->get_transform();
        for(int R=0;R<3;++R) for(int C=0;C<3;++C)
            State.World.Rotation.D[R][C]=World.Rotation.E[R][C];
        State.World.Translation={World.Translation.x,World.Translation.y,World.Translation.z};
    }
    // The PSYS frame Thorn set (the same one the ALE effect would be ticked with).
    void CopyThornTransform(FState& State)
    {
        Csys const& Local=State.Thorn->Local;
        for(int R=0;R<3;++R) for(int C=0;C<3;++C)
            State.World.Rotation.D[R][C]=Local.Orient.E[R][C];
        State.World.Translation={Local.Pos.x,Local.Pos.y,Local.Pos.z};
    }
    FState& Track(FClientSolarGameobj* Host)
    {
        auto Insert=G_States.emplace(Host,FState());
        FState& State=Insert.first->second;
        if (!Insert.second) return State;
        State.Host=Host;
        CopyTransform(State,Host);
        return State;
    }
    bool Claim(FClientSolarGameobj* Host)
    {
        if(!Eligible(Host)) return false;
        FState& State=Track(Host);
        if(State.Fallback) return false;
        if(State.Claimed) return true;
        if(!Ready()) return false;
        FDUMP(0x100003,"Black hole claimed %08x.\n",Host->get_id());
        State.Claimed=true;
        return true;
    }
    float Cfg(char const* Key,float Default) { return PortConfigFloat("Render",Key,Default); }
}
#endif

bool BlackHoleVisualReplaceAttached(FClientGameobj* Host,unsigned EffectId)
{
#ifdef FREELANCER_RP9
    if(!Eligible(Host)) return false;
    if(EffectId!=CreateID("gf_bhring") && EffectId!=CreateID("gf_neutronstar"))
    {
        // The other attachments the old look needed (debris, splash): left out while the shader runs.
        static std::vector<unsigned> const Hidden=[] {
            std::vector<unsigned> Ids;
            char Buffer[512]={};
            PortConfigString("Render","black_hole_hide_effects","bh_chunks, gf_bh_splash_new, gf_blackhole_splash",Buffer,sizeof(Buffer));
            char* Context=nullptr;
            for(char* Token=strtok_s(Buffer,", ",&Context);Token;Token=strtok_s(nullptr,", ",&Context)) Ids.push_back(CreateID(Token));
            return Ids;
        }();
        if(std::find(Hidden.begin(),Hidden.end(),EffectId)==Hidden.end()) return false;
        return Ready();
    }
    auto* Solar=static_cast<FClientSolarGameobj*>(Host);
    FState& State=Track(Solar);
    if(State.Fallback) return false;
    if(Claim(Solar)) return true;
    State.Fallback=true; // never mix an admitted original ALE with a later shader claim
#endif
    return false;
}
void BlackHoleVisualTick(FClientSolarGameobj* Host,float Dt)
{
#ifdef FREELANCER_RP9
    auto It=G_States.find(Host);
    if(It==G_States.end() || !std::isfinite(Dt) || Dt<=0) return;
    FState& State=It->second;
    // The disc keeps the orientation it was claimed with and turns only by its own gas: the
    // solar's spin would carry it round over the ring zone it sits in (port.ini
    // black_hole_follow_spin = 1 restores that).
    static int const FollowSpin=PortConfigInt("Render","black_hole_follow_spin",0);
    if (FollowSpin)
        CopyTransform(State,Host);
    else
    {
        Transform const& World=Host->get_transform();
        State.World.Translation={World.Translation.x,World.Translation.y,World.Translation.z};
    }
    State.Time=std::fmod(State.Time+Dt,3600.0f);
#endif
}
void BlackHoleVisualForget(FClientSolarGameobj* Host)
{
#ifdef FREELANCER_RP9
    G_States.erase(Host);
#endif
}
bool BlackHoleVisualThornHides(char const* TemplateName)
{
#ifdef FREELANCER_RP9
    // The old core sphere and the flute (and the listed particle effects) stand inside the new picture (and the lens would pick
    // their image up again), so a cutscene leaves them out while the shader can run.
    if(!TemplateName || PortConfigInt("Render","black_hole_visual",1)==0) return false;
    static std::vector<unsigned> const Hidden=[] {
        std::vector<unsigned> Ids;
        char Buffer[512]={};
        PortConfigString("Render","black_hole_intro_hide","BlackHoleCore, BlackHoleFluteSmall, bh_chunks, gf_blackhole_splash",Buffer,sizeof(Buffer));
        char* Context=nullptr;
        for(char* Token=strtok_s(Buffer,", ",&Context);Token;Token=strtok_s(nullptr,", ",&Context)) Ids.push_back(CreateID(Token));
        return Ids;
    }();
    unsigned const Id=CreateID(TemplateName);
    if(std::find(Hidden.begin(),Hidden.end(),Id)==Hidden.end()) return false;
    return Ready(false);
#else
    return false;
#endif
}
bool BlackHoleVisualThornClaim(FThornPsys* Psys,char const* EffectName)
{
#ifdef FREELANCER_RP9
    if(!Psys || !EffectName || PortConfigInt("Render","black_hole_visual",1)==0) return false;
    bool const Ring=_stricmp(EffectName,"Intro_volcanoplanet_sun")==0;
    if(!Ring && BlackHoleVisualThornHides(EffectName)) return true; // listed sparks and chunks
    if(!Ring && _stricmp(EffectName,"gf_neutronstar")!=0) return false;
    if(!Ready(false)) return false;
    if(Ring)
    {
        FState& State=G_Thorn[Psys];
        State.Thorn=Psys; State.Claimed=true;
        CopyThornTransform(State);
        FDUMP(0x100003,"Black hole thorn instance claimed %p (%s).\n",static_cast<void*>(Psys),EffectName);
    }
    return true;
#else
    return false;
#endif
}
void BlackHoleVisualThornTick(FThornPsys* Psys,float Dt)
{
#ifdef FREELANCER_RP9
    auto It=G_Thorn.find(Psys);
    if(It==G_Thorn.end()) return;
    CopyThornTransform(It->second);
    if(std::isfinite(Dt) && Dt>0) It->second.Time=std::fmod(It->second.Time+Dt,3600.0f);
#endif
}
void BlackHoleVisualThornForget(FThornPsys* Psys)
{
#ifdef FREELANCER_RP9
    G_Thorn.erase(Psys);
#endif
}
#ifdef FREELANCER_RP9
static void DrawHole(ICamera* Camera,FState& State)
{
    if(!State.Claimed || (State.Host && !Eligible(State.Host))) return;
    // A cutscene frames the hole far closer than space does (the intro camera sits 11 km
    // out), so Thorn instances take their own, smaller horizon.
    static float const RhSpace=(std::fmax)(1.0f,Cfg("black_hole_horizon",650.0f));
    static float const RhThorn=(std::fmax)(1.0f,Cfg("black_hole_intro_horizon",100.0f));
    float const Rh=State.Thorn ? RhThorn : RhSpace;
    static float const RbSpace=(std::fmax)(2.0f,Cfg("black_hole_lens_extent",40.0f));
    static float const RbThorn=(std::fmax)(2.0f,Cfg("black_hole_intro_lens_extent",80.0f));
    // The lens volume need reach little past the disc (and the vortices, 0.9 of its radius): a
    // tighter sphere covers far fewer pixels.
    static float const OuterSpace=Cfg("black_hole_disk_outer",14.0f);
    static float const OuterThorn=Cfg("black_hole_intro_disk_outer",65.0f);
    float const Rb=(std::fmin)(State.Thorn ? RbThorn : RbSpace,(State.Thorn ? OuterThorn : OuterSpace)*1.25f);
    float const Centre[3]={State.World.Translation.X,State.World.Translation.Y,State.World.Translation.Z};
    float ViewCentre[3];
    JumpHoleWorldToView(Camera->GetViewTransform(), Centre, ViewCentre);
    if (Camera->ClassifySphere(ViewCentre,Rb*Rh)==1) return;
    float const* Eye=Camera->GetPosition();
    double DistanceSq=0;
    for(int I=0;I<3;++I) { double const D=double(Eye[I])-Centre[I]; DistanceSq+=D*D; }
    if (std::sqrt(DistanceSq)<1.05*Rh) return;
    if (!Ready(State.Host!=nullptr)) return;
    LoadRing();
    auto* Ex=RenderEx::GetPipelineEx(); auto* Pipe=DALib::Pipeline;
    FRPExTexture* Depth=nullptr; unsigned long W=0,H=0;
    float NoDepth=0;
    if (Ex->GetSceneDepth(&Depth)!=GR_OK || !Depth || Ex->GetExTextureSize(Depth,&W,&H)!=GR_OK || !W || !H)
    {
        // Rooms without a captured depth: treat every pixel as sky (still lensed correctly).
        if (State.Host) return;
        Depth=G_Copy; NoDepth=1;
        if (Ex->GetExTextureSize(Depth,&W,&H)!=GR_OK || !W || !H) return;
    }
    int const* Vp=Camera->GetViewport();
    if (Vp[2]<Vp[0] || Vp[3]<Vp[1]) return;
    Win3DApplyCamera(Camera);
    float const* View=Camera->GetViewTransform();
    float Rot[3][3];
    for (int R=0;R<3;++R)
        for (int C=0;C<3;++C)
            Rot[R][C]=State.World.Rotation.D[R][C];
    static float const Tilt=Cfg("black_hole_intro_tilt",35.0f)*.01745329252f;
    if (State.Thorn && Tilt!=0)
    {
        // A cutscene camera may sit almost in the disc's plane; the startup-screen look wants the
        // vortex seen from above, so the disc's axis turns towards the eye by black_hole_intro_tilt.
        float const N[3]={Rot[0][1],Rot[1][1],Rot[2][1]};
        float E[3]={float(Eye[0]-Centre[0]),float(Eye[1]-Centre[1]),float(Eye[2]-Centre[2])};
        float K[3]={N[1]*E[2]-N[2]*E[1],N[2]*E[0]-N[0]*E[2],N[0]*E[1]-N[1]*E[0]};
        float const KLength=std::sqrt(K[0]*K[0]+K[1]*K[1]+K[2]*K[2]);
        if (KLength>1e-3f)
        {
            for (float& Value:K) Value/=KLength;
            // Turn the face the eye sees towards it: with the axis pointing away, turn it further away.
            float const Facing=N[0]*E[0]+N[1]*E[1]+N[2]*E[2]<0 ? -Tilt : Tilt;
            float const Cs=std::cos(Facing),Sn=std::sin(Facing);
            for (int C=0;C<3;++C)
            {
                float const V[3]={Rot[0][C],Rot[1][C],Rot[2][C]};
                float const KV=K[0]*V[0]+K[1]*V[1]+K[2]*V[2];
                float const X[3]={K[1]*V[2]-K[2]*V[1],K[2]*V[0]-K[0]*V[2],K[0]*V[1]-K[1]*V[0]};
                for (int R=0;R<3;++R) Rot[R][C]=V[R]*Cs+X[R]*Sn+K[R]*KV*(1-Cs);
            }
        }
    }
    float LocalEye[3]={};
    for (int R=0;R<3;++R)
        for (int C=0;C<3;++C)
            LocalEye[R]+=Rot[C][R]*float(double(Eye[C])-Centre[C]);
    static int const Debug=PortConfigInt("Render","black_hole_debug",0);
    if (Debug)
    {
        static DWORD LastLog=0;
        DWORD const Now=GetTickCount();
        if (Now-LastLog>2000)
        {
            LastLog=Now;
            int const* V=Camera->GetViewport();
            FDUMP(0x100003,"Black hole debug %s: eye=(%.0f %.0f %.0f) centre=(%.0f %.0f %.0f) viewcentre=(%.0f %.0f %.0f) "
                  "fwd=(%.3f %.3f %.3f) localeye=(%.0f %.0f %.0f) tan=(%.3f %.3f) vp=(%d %d %d %d).\n",
                  State.Thorn ? "room" : "space",Eye[0],Eye[1],Eye[2],Centre[0],Centre[1],Centre[2],
                  ViewCentre[0],ViewCentre[1],ViewCentre[2],View[6],View[7],View[8],
                  LocalEye[0],LocalEye[1],LocalEye[2],std::tan(Camera->GetHalfFovXDeg()*.01745329252f),
                  std::tan(Camera->GetFovYDeg()*.01745329252f),V[0],V[1],V[2],V[3]);
        }
    }
    static float const Exposure=Cfg("black_hole_exposure",1.6f);
    static float const Steps=Cfg("black_hole_steps",180.0f);
    static float const Lens=Cfg("black_hole_lens",1.0f);
    static float const LensThorn=Cfg("black_hole_intro_lens",0.7f);
    static float const DiskInner=Cfg("black_hole_disk_inner",3.0f);
    static float const DiskOuter=Cfg("black_hole_disk_outer",14.0f);
    static float const DiskOuterThorn=Cfg("black_hole_intro_disk_outer",65.0f);
    static float const DiskInnerThorn=Cfg("black_hole_intro_disk_inner",5.0f);
    static float const DiskOpacity=Cfg("black_hole_disk_opacity",0.9f);
    static float const Spin=Cfg("black_hole_spin",1.0f);
    static float const Heat=Cfg("black_hole_heat",1.0f);
    static float const Doppler=Cfg("black_hole_doppler",1.0f);
    static float const Jet=Cfg("black_hole_jet",0.6f);
    static float const Glow=Cfg("black_hole_glow",1.0f);
    static float const Bright=Cfg("black_hole_brightness",0.5f);
    static float const Style=Cfg("black_hole_style",1.0f);
    static float const Texture=Cfg("black_hole_texture",0.0f);
    static float const Redness=Cfg("black_hole_redness",0.0f);
    static float const Swirl=Cfg("black_hole_swirl",0.0f);
    static float const RingSpace=Cfg("black_hole_ring_picture",0.0f);
    static float const RingThorn=Cfg("black_hole_intro_ring_picture",0.0f);
    static float const ThickSpace=Cfg("black_hole_thickness",0.0f);
    static float const ThickThorn=Cfg("black_hole_intro_thickness",0.04f);
    static float const HazeSpace=Cfg("black_hole_haze",0.0f);
    static float const HazeThorn=Cfg("black_hole_intro_haze",0.5f);
    static float const SpiralSpace=Cfg("black_hole_spiral",0.0f);
    static float const SpiralThorn=Cfg("black_hole_intro_spiral",1.0f);
    static float const ParticlesSpace=Cfg("black_hole_particles",0.0f);
    static float const ParticlesThorn=Cfg("black_hole_intro_particles",1.0f);
    static float const BeamSideSpace=Cfg("black_hole_beam_side",0.0f);
    static float const BeamSideThorn=Cfg("black_hole_intro_beam_side",-1.0f);
    static float const JetWidth=(std::fmax)(0.05f,Cfg("black_hole_jet_width",1.0f));
    static float const TintR=Cfg("black_hole_tint_r",1.0f);
    static float const TintG=Cfg("black_hole_tint_g",1.0f);
    static float const TintB=Cfg("black_hole_tint_b",1.0f);
    float P[80]={};
    // Fewer steps for a hole small on the screen (its projected radius in pixels).
    float const Dist=float(std::sqrt(DistanceSq));
    float const RadiusPx=Dist>Rb*Rh ? Rb*Rh/Dist/(std::fmax)(std::tan(Camera->GetFovYDeg()*.01745329252f),.05f)*.5f*float(Vp[3]-Vp[1]+1) : 1e6f;
    float const StepsLod=(std::fmin)(Steps,48.0f+RadiusPx*.25f);
    // In space the disc fades out close to the eye, as a planetary ring's band does (port.ini
    // black_hole_near_fade = gone, whole: metres from the eye); the ring's own puffs show there.
    static float NearFade[4]={0,0,0,0};
    static bool const NearRead=[] {
        char Buffer[64]={};
        PortConfigString("Render","black_hole_near_fade","1000, 3500, 0.33, 300",Buffer,sizeof(Buffer));
        std::sscanf(Buffer,"%f , %f , %f , %f",&NearFade[0],&NearFade[1],&NearFade[2],&NearFade[3]);
        return true;
    }();
    (void)NearRead;
    float const Visible=1;
    P[0]=State.Time; P[1]=Exposure; P[2]=StepsLod; P[3]=State.Thorn ? LensThorn : Lens;
    P[4]=1.0f/W; P[5]=1.0f/H; P[6]=Rb;
    P[8]=(Vp[0]+.5f)/W; P[9]=(Vp[1]+.5f)/H;
    P[10]=(Vp[2]+.5f)/W; P[11]=(Vp[3]+.5f)/H;
    P[12]=Camera->GetZNear(); P[13]=Camera->GetZFar(); P[14]=0; P[15]=1;
    Pipe->GetDepthRange(P+14,P+15);
    for (int I=0;I<3;++I) P[16+I]=LocalEye[I]/Rh;
    P[19]=Rh;
    // The ray fan from the projection the scene was actually drawn with: the camera's own FOV
    // values do not carry the viewport's aspect (a 4:3 pair on a 16:9 screen put the hole off its
    // object and let it slide as the view turned).
    float Proj[16]={};
    if (Pipe->GetProjection(Proj)!=GR_OK || Proj[0]==0 || Proj[5]==0) return;
    P[20]=1.0f/std::fabs(Proj[0]);
    P[21]=1.0f/std::fabs(Proj[5]);
    P[23]=-ViewCentre[2];
    if (!std::isfinite(P[20]) || !std::isfinite(P[21]) || P[20]<=0 || P[21]<=0) return;
    JumpHoleCameraToLocal(View,&Rot[0][0],P+24);
    P[36]=State.Thorn ? DiskInnerThorn : DiskInner; P[37]=State.Thorn ? DiskOuterThorn : DiskOuter; P[38]=DiskOpacity; P[39]=Spin;
    P[40]=Heat; P[41]=Doppler; P[42]=Jet; P[43]=Glow;
    P[44]=TintR; P[45]=TintG; P[46]=TintB; P[47]=Bright;
    static float const MeshRadius=Cfg("black_hole_mesh_radius",650.0f);
    P[48]=(std::fmax)(1.25f,MeshRadius*1.15f/Rh); P[49]=NoDepth; P[50]=Style; P[51]=JetWidth; P[52]=Texture; P[53]=Redness; P[54]=Swirl;
    P[55]=G_Ring ? (State.Thorn ? RingThorn : RingSpace) : 0;
    P[56]=State.Thorn ? ThickThorn : ThickSpace; P[57]=State.Thorn ? HazeThorn : HazeSpace; P[58]=State.Thorn ? SpiralThorn : SpiralSpace; P[59]=State.Thorn ? ParticlesThorn : ParticlesSpace;
    P[60]=State.Thorn ? BeamSideThorn : BeamSideSpace; P[61]=Visible; P[62]=State.Thorn ? 0 : NearFade[0]/Rh; P[63]=State.Thorn ? 0 : NearFade[1]/Rh;
    for (int I=0;I<5;++I) P[I<4 ? 64+I : 68]=(G_DebugMode>>I)&1 ? 1.0f : 0.0f;
    P[69]=(std::fmin)(1.0f,(std::fmax)(0.0f,NearFade[2])); P[70]=State.Thorn ? 0 : NearFade[3]/Rh;
    static float const SlabStrength=Cfg("black_hole_slab",1.0f);
    static float const SlabHeight=(std::fmax)(1.0f,Cfg("black_hole_slab_height",400.0f));
    static float const SlabRange=(std::fmax)(1.0f,Cfg("black_hole_slab_range",6000.0f));
    P[76]=State.Thorn ? 0 : SlabStrength; P[77]=SlabHeight/Rh; P[78]=SlabRange/Rh; // c19
    float const Width=float(Vp[2]-Vp[0]+1),Height=float(Vp[3]-Vp[1]+1);
    float const Remap[4]={Width*P[4],Height*P[5],(2*Vp[0]+Width)*P[4]-1,1-(2*Vp[1]+Height)*P[5]};
    if (G_Capture->CaptureSceneColor(G_Copy)!=GR_OK) { LogDrawFailure(State,"capture"); return; }
    FRPExSamplerState Linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState Point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState Noise={RPExFilterLinear,RPExMipNone,RPExAddressWrap,RPExAddressWrap,RPExAddressWrap};
    FJumpHoleVertex const Quad[]={
        {{-1,1,0},0xffffffffu,{0,0}},{{1,1,0},0xffffffffu,{1,0}},
        {{-1,-1,0},0xffffffffu,{0,1}},{{1,-1,0},0xffffffffu,{1,1}}};
    // Reduced resolution (port.ini black_hole_resolution, default 0.5 per side): the march goes
    // to a smaller target cleared to alpha 0, then PSComposite brings it up depth-aware.
    static float const Resolution=(std::fmin)(1.0f,(std::fmax)(0.25f,Cfg("black_hole_resolution",0.5f)));
    if (Resolution<1 && !G_HalfTried)
    {
        G_HalfTried=true;
        FRPExRenderTargetDesc Desc={0,0,Resolution,RPExFormatA8R8G8B8};
        if (Ex->CreateExRenderTarget(&Desc,&G_Half)!=GR_OK) G_Half=nullptr;
        if (G_Half && Ex->CreateExProgram(RenderEx::GetExtraData(),"SHADERS\\black_hole.hlsl","VSMain","PSComposite",&G_Composite)!=GR_OK)
        {
            Ex->DestroyExTexture(G_Half); G_Half=nullptr; G_Composite=nullptr;
        }
        FDUMP(0x100003,"Black hole reduced-resolution march %s (%.2f).\n",G_Half ? "on" : "unavailable",Resolution);
    }
    unsigned long HW=0,HH=0;
    bool const bHalf=G_Half && G_Composite && Ex->GetExTextureSize(G_Half,&HW,&HH)==GR_OK && HW && HH;
    bool Ok=true;
    if (bHalf)
    {
        float const Low[4]={float(HW),float(HH),1.0f/HW,1.0f/HH};
        float PHalf[80];
        std::copy(P,P+80,PHalf);
        PHalf[4]=1.0f/HW; PHalf[5]=1.0f/HH;
        FRPExPassDesc Pass={G_Half,RPExPassClearColor,0};
        Ex->BindExTexture(4,nullptr,&Point); // never sampled while it is the target
        if (Ex->BeginExPass(&Pass)!=GR_OK) { LogDrawFailure(State,"begin pass"); return; }
        Ok=Ex->BindExProgram(G_Program)==GR_OK &&
            Ex->BindExTexture(0,G_Copy,&Linear)==GR_OK && Ex->BindExTexture(1,Depth,&Point)==GR_OK &&
            Ex->BindExTexture(2,G_Noise,&Noise)==GR_OK && Ex->BindExTexture(3,G_Ring ? G_Ring : G_Noise,&Linear)==GR_OK &&
            Ex->SetExVertexConstants(7,Remap,1)==GR_OK && Ex->SetExPixelConstants(0,PHalf,20)==GR_OK;
        if (Ok) Ok=RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,
            D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,Quad,4)==GR_OK;
        if (Ok) Ok=Ex->SetExRenderTarget(nullptr,0)==GR_OK && Ex->BindExProgram(G_Composite)==GR_OK &&
            Ex->BindExTexture(1,Depth,&Point)==GR_OK && Ex->BindExTexture(4,G_Half,&Point)==GR_OK &&
            Ex->SetExVertexConstants(7,Remap,1)==GR_OK && Ex->SetExPixelConstants(0,P,20)==GR_OK &&
            Ex->SetExPixelConstants(18,Low,1)==GR_OK;
        if (Ok) Ok=RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,
            D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,Quad,4)==GR_OK;
        Ex->BindExTexture(4,nullptr,&Point);
        if (Ex->EndExPass()!=GR_OK) Ok=false;
    }
    else
    {
        FRPExPassDesc Pass={nullptr,0,0};
        if (Ex->BeginExPass(&Pass)!=GR_OK) { LogDrawFailure(State,"begin pass"); return; }
        Ok=Ex->BindExProgram(G_Program)==GR_OK &&
            Ex->BindExTexture(0,G_Copy,&Linear)==GR_OK && Ex->BindExTexture(1,Depth,&Point)==GR_OK &&
            Ex->BindExTexture(2,G_Noise,&Noise)==GR_OK && Ex->BindExTexture(3,G_Ring ? G_Ring : G_Noise,&Linear)==GR_OK &&
            Ex->SetExVertexConstants(7,Remap,1)==GR_OK &&
            Ex->SetExPixelConstants(0,P,20)==GR_OK;
        if (Ok) Ok=RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP,
            D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,Quad,4)==GR_OK;
        if (Ex->EndExPass()!=GR_OK) Ok=false;
    }
    if (!Ok) { LogDrawFailure(State,"bind/draw/end pass"); return; }
    if (!State.LoggedDraw)
    {
        State.LoggedDraw=true;
        FDUMP(0x100003,"Black hole drawn %08x%s world=(%.1f %.1f %.1f) distance=%.1f Rh=%.1f extent=%.1f.\n",
              StateId(State),State.Thorn ? " (room)" : "",Centre[0],Centre[1],Centre[2],
              float(std::sqrt(DistanceSq)),Rh,Rb);
    }
}
#endif
void BlackHoleVisualDraw(FSpaceCamera* Camera)
{
#ifdef FREELANCER_RP9
    if(!Camera || !GetGameOption(kGameOptEffectsGroup)) return;
    std::vector<FState*> Ordered;
    for(auto& Pair:G_States) if(Pair.second.Claimed) Ordered.push_back(&Pair.second);
    if(Ordered.empty()) return;
    float const* Eye=Camera->GetPosition();
    auto Dist=[&](FState const* S) {
        double X=S->World.Translation.X-Eye[0],Y=S->World.Translation.Y-Eye[1],Z=S->World.Translation.Z-Eye[2];
        return X*X+Y*Y+Z*Z;
    };
    std::sort(Ordered.begin(),Ordered.end(),[&](FState const* A,FState const* B){return Dist(A)>Dist(B);});
    // om13_alt stacks two solars on one spot (om13alt_bh and its child om13alt_bh2); a second
    // pass would lens the first one's picture again, so one hole per place.
    std::vector<FState*> Drawn;
    for(FState* State:Ordered)
    {
        bool Duplicate=false;
        for(FState const* Other:Drawn)
        {
            double X=State->World.Translation.X-Other->World.Translation.X;
            double Y=State->World.Translation.Y-Other->World.Translation.Y;
            double Z=State->World.Translation.Z-Other->World.Translation.Z;
            if(X*X+Y*Y+Z*Z<100.0*100.0) { Duplicate=true; break; }
        }
        if(Duplicate) continue;
        Drawn.push_back(State);
        DrawHole(Camera,*State);
    }
#endif
}
void BlackHoleVisualDrawRoom(ICamera* Camera)
{
#ifdef FREELANCER_RP9
    if(!Camera || G_Thorn.empty() || !GetGameOption(kGameOptEffectsGroup)) return;
    for(auto& Pair:G_Thorn) DrawHole(Camera,Pair.second);
#endif
}
bool BlackHoleVisualShipImmersion(float const* WorldPos,float* OutStrength,float* OutToCentre,float* OutDistance)
{
#ifdef FREELANCER_RP9
    // How deep a point sits in a space black hole's disc gas: 1 inside the slab of the disc
    // (port.ini black_hole_slab_height, metres either side of the plane) between its inner and
    // outer radius, fading out over a slab height above it and towards the edges.
    static float const Rh=(std::fmax)(1.0f,Cfg("black_hole_horizon",650.0f));
    static float const Inner=Cfg("black_hole_disk_inner",3.0f)*Rh;
    static float const Outer=Cfg("black_hole_disk_outer",14.0f)*Rh;
    static float const Slab=(std::fmax)(1.0f,Cfg("black_hole_slab_height",400.0f));
    float Best=0;
    for(auto& Pair:G_States)
    {
        FState const& State=Pair.second;
        if(!State.Claimed) continue;
        float const D[3]={WorldPos[0]-State.World.Translation.X,WorldPos[1]-State.World.Translation.Y,WorldPos[2]-State.World.Translation.Z};
        float Local[3]={};
        for(int R=0;R<3;++R) for(int C=0;C<3;++C) Local[R]+=State.World.Rotation.D[C][R]*D[C];
        float const Rho=std::sqrt(Local[0]*Local[0]+Local[2]*Local[2]);
        float const Distance=std::sqrt(D[0]*D[0]+D[1]*D[1]+D[2]*D[2]);
        auto Smooth=[](float A,float B,float X){float U=(std::fmin)(1.0f,(std::fmax)(0.0f,(X-A)/(B-A)));return U*U*(3-2*U);};
        float const Strength=(1-Smooth(Slab,Slab*2,std::fabs(Local[1])))*Smooth(Inner*.7f,Inner,Rho)*(1-Smooth(Outer*.8f,Outer,Rho));
        if(Strength<=Best) continue;
        Best=Strength;
        if(OutToCentre) for(int I=0;I<3;++I) OutToCentre[I]=Distance>0 ? -D[I]/Distance : 0;
        if(OutDistance) *OutDistance=Distance;
    }
    if(OutStrength) *OutStrength=Best;
    return Best>0;
#else
    if(OutStrength) *OutStrength=0;
    return false;
#endif
}
void BlackHoleVisualSetDebug(int Mode)
{
#ifdef FREELANCER_RP9
    G_DebugMode=Mode;
#endif
}
void BlackHoleVisualRenderShutdown()
{
#ifdef FREELANCER_RP9
    ReleaseResources(); G_Failed=false; G_States.clear(); G_Thorn.clear();
#endif
}
