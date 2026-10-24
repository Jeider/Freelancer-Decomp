#include "ship_warp_visual.h"
#ifdef FREELANCER_RP9
#include "ship_warp_state.h"
#include "jumphole_visibility.h"
#include "client_gameobj.h"
#include "client_objdb.h"
#include "common_cobject.h"
#include "jump_effect.h"
#include "gate_tunnel.h"
#include "tradelane_visual.h"
#include "tradelane_visual_style.h"
#include "space_camera.h"
#include "player_behavior.h"
#include "nebula_volume.h"
#include "effect_type_info.h"
#include "vis_effect_arch.h"
#include "perf_options.h"
#include "game_options.h"
#include "port_config.h"
#include "render_ex.h"
#include "win3d_render.h"
#include "DALib.h"
#include "dacom_iids.h"
#include "engine/engbase.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/IRPSceneCapture.h"
#include <map>
#include <string>

namespace
{
using namespace ShipWarpMesh;
struct FTrail {std::string Name;FShipWarpHistory History;};
struct FState
{
    FClientGameobj* Ship=nullptr;
    long Instance=-1;
    unsigned System=0;
    int EffectType=-1;
    FJumpShipEffect const* Jump=nullptr;
    FShipWarpClock Clock;
    FTradeLaneVisualStyle Style;
    std::string Nose;
    std::vector<FTrail> Trails;
    FShipWarpPoint LastPosition={};
    float Radius=10;
    bool Sampled=false;
};
std::map<unsigned,FState> G_Ships;
std::vector<FShipWarpVertex> G_Vertices;
struct FDraw {unsigned First,Count,RefractionCount;float Params[20];};
std::vector<FDraw> G_Draws;
FRPExProgram* G_Program=nullptr;
FRPExProgram* G_WarpProgram=nullptr;
FRPExTexture* G_SceneCopy=nullptr;
IRPSceneCapture* G_Capture=nullptr;
bool G_Failed=false;
bool G_WarpTried=false;

bool WarpReady()
{
    if(G_WarpTried) return G_WarpProgram&&G_SceneCopy&&G_Capture;
    G_WarpTried=true;
    auto* Ex=RenderEx::GetPipelineEx();
    FRPExRenderTargetDesc Desc={0,0,1.f,RPExFormatA8R8G8B8};
    if(DALib::Pipeline->QueryInterface(Iids::RPSceneCapture,reinterpret_cast<void**>(&G_Capture))==GR_OK&&G_Capture&&
        Ex->CreateExProgram(RenderEx::GetExtraData(),"SHADERS\\ship_warp.hlsl","VSMain","PSWarp",&G_WarpProgram)==GR_OK&&
        Ex->CreateExRenderTarget(&Desc,&G_SceneCopy)==GR_OK) return true;
    if(G_WarpProgram) Ex->DestroyExProgram(G_WarpProgram);
    if(G_SceneCopy) Ex->DestroyExTexture(G_SceneCopy);
    if(G_Capture) G_Capture->Release();
    G_WarpProgram=nullptr;G_SceneCopy=nullptr;G_Capture=nullptr;
    FDUMP(0x100002,"Ship warp refraction unavailable; retaining travel glow.\n");
    return false;
}

bool Ready()
{
    if(G_Failed||!RenderEx::IsAvailable()||!PortConfigInt("Render","ship_warp_visual",1)) return false;
    // Do not suppress NPC particles on a device without the sampled scene depth.
    FRPExTexture* Depth=nullptr;unsigned long W=0,H=0;
    auto* Ex=RenderEx::GetPipelineEx();
    if(Ex->GetSceneDepth(&Depth)!=GR_OK||!Depth||Ex->GetExTextureSize(Depth,&W,&H)!=GR_OK||!W||!H) return false;
    if(G_Program) return true;
    if(RenderEx::GetPipelineEx()->CreateExProgram(RenderEx::GetExtraData(),"SHADERS\\ship_warp.hlsl",
        "VSMain","PSMain",&G_Program)!=GR_OK || !G_Program)
    {
        G_Failed=true;
        FDUMP(0x100002,"Ship warp shader unavailable; keeping original NPC travel particles.\n");
        return false;
    }
    G_Vertices.reserve(20000);
    return true;
}
FShipWarpPoint Point(Vector const& V) {return {V.x,V.y,V.z};}
bool Anchor(FClientGameobj* Ship,std::string const& Name,FShipWarpPoint& Out)
{
    Vector P;Matrix R;
    if(Name.empty()||Ship->get_hardpoint(Name.c_str(),&P,&R)!=0) return false;
    Out=Point(P);return Finite(Out); // HardpointPosition returns WORLD space, including moving children.
}
void __cdecl Collect(char const* Name,void* Context)
{
    if(!Name) return;
    auto& S=*static_cast<FState*>(Context);
    if(_stricmp(Name,"HpHeadLight")==0) {S.Nose=Name;return;}
    if(!ShipWarpTrailName(Name)||S.Trails.size()>=32) return;
    for(auto const& Trail:S.Trails) if(_stricmp(Name,Trail.Name.c_str())==0) return;
    FTrail Trail;Trail.Name=Name;S.Trails.push_back(Trail);
}
bool Init(FState& S,FClientGameobj* Ship,unsigned EffectId,FJumpShipEffect const* Jump)
{
    if(!Ship||Ship->ManagerKind!=1||!Ship->GetObject()||!DALib::Engine||!DALib::Hardpoint) return false;
    S=FState();S.Ship=Ship;S.Instance=Ship->get_index();S.System=Ship->GetObject()->PhysicsSystemId;S.Jump=Jump;
    if(S.Instance==-1) return false;
    Vector Centre;
    if(Ship->get_physical_radius(S.Radius,Centre)!=0||!std::isfinite(S.Radius)) S.Radius=10;
    S.Radius=(std::max)(2.f,(std::min)(S.Radius,500.f));
    auto Add=[&](long Instance) {
        auto Arch=DALib::Engine->GetInstanceArchetype(reinterpret_cast<void*>(Instance));
        if(Arch && Arch!=G_InvalidEngineHandle) {
            DALib::Hardpoint->EnumerateHardpoints(&Collect,Arch,&S);
            DALib::Engine->ReleaseHandle(Arch);
        }
    };
    Add(S.Instance);
    for(auto Child=DALib::Engine->GetRelatedInstance(reinterpret_cast<void*>(S.Instance),0,G_InvalidEngineHandle);
        Child && Child!=G_InvalidEngineHandle;
        Child=DALib::Engine->GetRelatedInstance(reinterpret_cast<void*>(S.Instance),0,Child))
        Add(reinterpret_cast<long>(Child));
    FShipWarpPoint P;
    if(!Anchor(Ship,S.Nose,P)) S.Nose.clear();
    S.Trails.erase(std::remove_if(S.Trails.begin(),S.Trails.end(),[&](FTrail const& T){return !Anchor(Ship,T.Name,P);}),S.Trails.end());
    if(S.Nose.empty()&&S.Trails.empty()) return false;
    if(auto* Arch=FindEffectArch(&EffectId)) S.EffectType=Arch->EffectType;
    if(Jump&&Jump->Tunnel&&Jump->Tunnel->LayerCount>=1&&Jump->Tunnel->LayerCount<=2) {
        auto const* Tunnel=Jump->Tunnel;
        FVector Zero={};auto const& Layer1=Tunnel->LayerCount>1?Tunnel->Layers[1].Color:Zero;
        TradeLaneBuildPalette(S.Style,&Tunnel->Layers[0].Color.X,&Layer1.X,&Tunnel->MinRgb.X,&Tunnel->MaxRgb.X,0);
    }
    FDUMP(0x100003,"Ship warp %08x: mode=%s nose=%s trails=%u radius=%.1f.\n",
        Ship->get_id(),Jump?"jump":"lane",S.Nose.c_str(),static_cast<unsigned>(S.Trails.size()),S.Radius);
    return true;
}
bool Live(unsigned Id,FState const& S)
{
    auto* Ship=ClientObjDb_FindObject(Id,1);
    return Ship && Ship==S.Ship && Ship->GetObject() && Ship->get_index()==S.Instance &&
        Ship->GetObject()->PhysicsSystemId==S.System;
}
void Tick(FState& S,float Dt)
{
    if(!std::isfinite(Dt)||Dt<=0) return;
    S.Clock.Tick(Dt);
    auto Pos=Point(S.Ship->get_position());
    auto D=Sub(Pos,S.LastPosition);
    // A long step/system teleport starts a fresh path, never a line across the system.
    float Limit=(std::max)(5000.f,S.Radius*20);
    if(!Finite(Pos)||Dt>.5f||(S.Sampled&&Dot(D,D)>Limit*Limit))
        for(auto& T:S.Trails) T.History.Clear();
    S.LastPosition=Pos;S.Sampled=Finite(Pos);
    for(auto& T:S.Trails) {
        FShipWarpPoint P;
        if(Anchor(S.Ship,T.Name,P)) T.History.Tick(P,Dt);else T.History.Clear();
    }
}
float Visibility(FState const& S,FSpaceCamera* Camera,float const* ViewCentre,bool Tunnel)
{
    float Gain=1;
    auto const* Obj=S.Ship->GetObject();
    if((Obj->ObjectClass&CObject::ClassEqObj)==CObject::ClassEqObj)
        Gain*=1-(std::max)(0.f,(std::min)(1.f,static_cast<CEqObj const*>(Obj)->CloakPercent));
    if(!Tunnel && S.EffectType>=0 && S.EffectType<kEffectTypeCount)
    {
        auto* Info=EffectTypeInfoByIndex(S.EffectType);
        float Perf=GetPerfGenericEffectPerf();
        if(Info->Priority<Perf) return 0;
        Gain*=JumpHoleRangeVisibility((std::max)(0.f,-ViewCentre[2]-Info->Radius),
            JumpHolePbubbleLimit(Info->PbubbleNear,Info->PbubbleFar,Perf));
        float Blend=1;
        // Alchemy's Blend controls simulation detail, not opacity; share its cull only.
        if(GetGameOption(kGameOptAlchemyLod)&&!EffectTypeLodBlend(S.EffectType,Camera,-ViewCentre[2],&Blend)) return 0;
    }
    if(!Tunnel && Gain>0 && GetGameOption(kGameOptNebula)) {
        auto Pos=Point(S.Ship->get_position());
        Gain*=NebulaVolume::EffectVisibility(Camera->GetPosition(),&Pos.X);
    }
    return Gain;
}
}
#endif

bool ShipWarpVisualStartLane(FClientGameobj* Ship,unsigned EffectId,unsigned RouteId)
{
#ifdef FREELANCER_RP9
    if(!Ship||!Ready()) return false;
    FTransform Lane={};auto const& Pos=Ship->get_position();Lane.Translation={Pos.x,Pos.y,Pos.z};
    auto Style=TradeLaneVisualResolveStyle(Lane,RouteId);
    auto It=G_Ships.find(Ship->get_id());
    if(It!=G_Ships.end()&&Live(It->first,It->second)&&!It->second.Jump) {
        It->second.Style=Style;It->second.Clock.Resume();return true;
    }
    FState S;if(!Init(S,Ship,EffectId,nullptr)) return false;
    S.Style=Style;
    G_Ships[Ship->get_id()]=std::move(S);
    return true;
#else
    return false;
#endif
}
void ShipWarpVisualStopLane(FClientGameobj* Ship)
{
#ifdef FREELANCER_RP9
    if(!Ship) return;
    auto It=G_Ships.find(Ship->get_id());
    if(It!=G_Ships.end()&&It->second.Ship==Ship&&!It->second.Jump) It->second.Clock.Stop();
#endif
}
void ShipWarpVisualTickLanes(float Dt)
{
#ifdef FREELANCER_RP9
    for(auto It=G_Ships.begin();It!=G_Ships.end();) {
        auto& S=It->second;
        if(!Live(It->first,S)) {It=G_Ships.erase(It);continue;}
        if(S.Jump) {++It;continue;}
        auto* Obj=S.Ship->GetObject();
        if((Obj->ObjectClass&CObject::ClassShip)!=CObject::ClassShip) {It=G_Ships.erase(It);continue;}
        if(!static_cast<CShip*>(Obj)->is_using_tradelane()&&S.Clock.Age>.25f) S.Clock.Stop();
        Tick(S,Dt);
        if(S.Clock.Stopping&&S.Clock.Intensity<=0) It=G_Ships.erase(It);else ++It;
    }
#endif
}
void ShipWarpVisualTickJump(FJumpShipEffect const* Effect,float Dt)
{
#ifdef FREELANCER_RP9
    if(!Effect||!Effect->Ship||Effect->Ship!=GetPlayerObjRW()) return;
    auto* Ship=Effect->Ship;int Mode=Ship->Field_0x158;
    if(Mode!=2&&Mode!=3&&Mode!=4) {ShipWarpVisualForgetJump(Effect);return;}
    auto It=G_Ships.find(Ship->get_id());
    if(It==G_Ships.end()||It->second.Jump!=Effect||!Live(It->first,It->second)) {
        if(Mode==4||!Ready()) return;
        FState S;if(!Init(S,Ship,0,Effect)) return;
        It=G_Ships.insert_or_assign(Ship->get_id(),std::move(S)).first;
    }
    if(Mode==4) It->second.Clock.Stop();
    Tick(It->second,Dt);
    if(It->second.Clock.Stopping&&It->second.Clock.Intensity<=0) G_Ships.erase(It);
#endif
}
void ShipWarpVisualForgetJump(FJumpShipEffect const* Effect)
{
#ifdef FREELANCER_RP9
    for(auto It=G_Ships.begin();It!=G_Ships.end();) {
        if(It->second.Jump==Effect) It=G_Ships.erase(It);else ++It;
    }
#endif
}
void ShipWarpVisualReset()
{
#ifdef FREELANCER_RP9
    G_Ships.clear();G_Vertices.clear();G_Draws.clear();
#endif
}
void ShipWarpVisualDraw(FSpaceCamera* Camera,FClientShipGameobj* TunnelShip)
{
#ifdef FREELANCER_RP9
    if(!Camera||G_Ships.empty()||!GetGameOption(kGameOptEffectsGroup)||!GetGameOption(kGameOptParticles)||!Ready()) return;
    auto* Ex=RenderEx::GetPipelineEx();auto* Pipe=DALib::Pipeline;
    FRPExTexture* Depth=nullptr;unsigned long W=0,H=0;
    if(Ex->GetSceneDepth(&Depth)!=GR_OK||!Depth||Ex->GetExTextureSize(Depth,&W,&H)!=GR_OK||!W||!H) return;
    Win3DApplyCamera(Camera);
    float V[36]={};auto const* View=Camera->GetViewTransform();auto const* Vp=Camera->GetViewport();
    for(int R=0;R<3;++R) {for(int C=0;C<3;++C) V[R*4+C]=View[R*3+C];V[R*4+3]=View[9+R];}
    if(Pipe->GetProjection(V+12)!=GR_OK) return;
    V[28]=float(Vp[2]-Vp[0]+1)/W;V[29]=float(Vp[3]-Vp[1]+1)/H;
    V[30]=2.f*Vp[0]/W+V[28]-1;V[31]=1-2.f*Vp[1]/H-V[29];
    V[32]=Camera->GetZNear();V[33]=Camera->GetZFar();V[34]=0;V[35]=1;Pipe->GetDepthRange(V+34,V+35);
    auto const* Eye=Camera->GetPosition();
    G_Vertices.clear();G_Draws.clear();
    bool HasRefraction=false;
    for(auto const& Entry:G_Ships)
    {
        auto const& S=Entry.second;
        if(!Live(Entry.first,S)||S.Clock.Intensity<=0) continue;
        if(TunnelShip) {if(S.Ship!=TunnelShip||!S.Jump) continue;}
        else if(S.Jump && !S.Clock.Stopping) continue;
        if(S.Ship==GetPlayerObjRW()&&Camera==GetFirstPersonSpaceCamera()) continue;
        auto Pos=Point(S.Ship->get_position());float Centre[3]={};
        for(int R=0;R<3;++R) Centre[R]=View[R*3]*Pos.X+View[R*3+1]*Pos.Y+View[R*3+2]*Pos.Z+View[9+R];
        // Conservative sphere encloses all capped trails, including a turn.
        if(Camera->ClassifySphere(Centre,S.Radius*10)==1) continue;
        float Gain=S.Clock.Intensity*Visibility(S,Camera,Centre,TunnelShip!=nullptr);
        if(Gain<.001f) continue;
        auto const& Rot=S.Ship->get_orientation();
        FShipWarpPoint Right={Rot.E[0][0],Rot.E[1][0],Rot.E[2][0]},Up={Rot.E[0][1],Rot.E[1][1],Rot.E[2][1]},Back={Rot.E[0][2],Rot.E[1][2],Rot.E[2][2]};
        unsigned First=static_cast<unsigned>(G_Vertices.size());FShipWarpPoint Head;
        if(Anchor(S.Ship,S.Nose,Head))
            BuildShipWarpNose(G_Vertices,Add(Head,Mul(Back,-(std::max)(2.f,(std::min)(15.f,S.Radius*.12f)))),
                Right,Up,Back,(std::max)(2.f,(std::min)(14.f,S.Radius*.16f)),S.Clock.Time,2.f);
        unsigned RefractionCount=static_cast<unsigned>(G_Vertices.size())-First;
        HasRefraction=HasRefraction||RefractionCount!=0;
        unsigned TrailIndex=0;
        for(auto const& T:S.Trails) {
            if(Anchor(S.Ship,T.Name,Head)) {
                FShipWarpPoint Path[33];
                // Build the original full path: the shader crops the lane tail so its
                // knots, taper and refraction keep their original spatial scale.
                unsigned Count=T.History.Path(Head,Back,S.Jump?S.Radius*14:0,S.Radius*8,Path);
                BuildShipWarpTrail(G_Vertices,Path,Count,{Eye[0],Eye[1],Eye[2]},
                    (std::max)(.35f,(std::min)(3.f,S.Radius*.045f))*(S.Jump?1.f:.7f),S.Clock.Time,TrailIndex*.173f);
            }
            ++TrailIndex;
        }
        unsigned Count=static_cast<unsigned>(G_Vertices.size())-First;
        if(!Count) continue;
        FDraw Draw={First,Count,RefractionCount,{S.Clock.Time,Gain,1.f/W,1.f/H,S.Style.Body[0],S.Style.Body[1],S.Style.Body[2],S.Jump?1.f:0,
            V[32],V[33],V[34],V[35],(Vp[0]+.5f)/W,(Vp[1]+.5f)/H,(Vp[2]+.5f)/W,(Vp[3]+.5f)/H,
            S.Style.Accent[0],S.Style.Accent[1],S.Style.Accent[2],S.Style.Enabled}};
        G_Draws.push_back(Draw);
    }
    if(G_Draws.empty()) return;
    // Snapshot once for every ship, before emission, and reuse geometry for both passes.
    bool Refract=HasRefraction&&WarpReady()&&G_Capture->CaptureSceneColor(G_SceneCopy)==GR_OK;
    for(int PassIndex=Refract?0:1;PassIndex<2;++PassIndex) {
            FRPExPassDesc Pass={nullptr,RPExPassKeepDepth,0};
            if(Ex->BeginExPass(&Pass)!=GR_OK) continue;
            Pipe->SetRenderState(D3DRS_ZENABLE,1);Pipe->SetRenderState(D3DRS_ZWRITEENABLE,0);
            Pipe->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);Pipe->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
            Pipe->SetRenderState(D3DRS_ALPHATESTENABLE,0);Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE,1);
            Pipe->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
            Pipe->SetRenderState(D3DRS_DESTBLEND,PassIndex?D3DBLEND_ONE:D3DBLEND_INVSRCALPHA);
            Pipe->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
            FRPExSamplerState Sampler={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
            FRPExSamplerState Linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
            bool Ok=Ex->BindExProgram(PassIndex?G_Program:G_WarpProgram)==GR_OK&&Ex->BindExTexture(0,Depth,&Sampler)==GR_OK&&
                Ex->SetExVertexConstants(0,V,9)==GR_OK;
            if(Ok&&!PassIndex) Ok=Ex->BindExTexture(1,G_SceneCopy,&Linear)==GR_OK;
            if(Ok) for(auto const& Draw:G_Draws) {
                unsigned Count=PassIndex?Draw.Count:Draw.RefractionCount;
                if(!Count) continue;
                if(Ex->SetExPixelConstants(0,Draw.Params,5)==GR_OK)
                    RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLELIST,D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,
                        G_Vertices.data()+Draw.First,Count);
            }
            Ex->EndExPass();
    }
#endif
}
void ShipWarpVisualRenderShutdown()
{
#ifdef FREELANCER_RP9
    if(G_Program&&RenderEx::GetPipelineEx()) RenderEx::GetPipelineEx()->DestroyExProgram(G_Program);
    if(G_WarpProgram&&RenderEx::GetPipelineEx()) RenderEx::GetPipelineEx()->DestroyExProgram(G_WarpProgram);
    if(G_SceneCopy&&RenderEx::GetPipelineEx()) RenderEx::GetPipelineEx()->DestroyExTexture(G_SceneCopy);
    if(G_Capture) G_Capture->Release();
    G_Program=nullptr;G_Failed=false;G_WarpProgram=nullptr;G_SceneCopy=nullptr;G_Capture=nullptr;G_WarpTried=false;
    ShipWarpVisualReset();
#endif
}
