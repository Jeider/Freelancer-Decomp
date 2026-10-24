#include "engine_heat_visual.h"
#ifdef FREELANCER_RP9
#include "engine_heat_mesh.h"
#include "client_gameobj.h"
#include "common_cobject.h"
#include "common_cequip.h"
#include "common_goods.h"
#include "player_behavior.h"
#include "space_camera.h"
#include "game_options.h"
#include "port_config.h"
#include "nebula_volume.h"
#include "render_ex.h"
#include "win3d_render.h"
#include "DALib.h"
#include "dacom_iids.h"
#include "engine/engbase.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/IRPSceneCapture.h"

namespace
{
using namespace ShipWarpMesh;
struct FHeatState {
    FClientGameobj* Host=nullptr;CEEngine const* Engine=nullptr;
    unsigned Id=0,System=0;long Instance=-1;float Time=0,Heat=0;
} G_Heat;
FRPExProgram* G_Program=nullptr;FRPExTexture* G_Scene=nullptr;
IRPSceneCapture* G_Capture=nullptr;bool G_Failed=false;
std::vector<FShipWarpVertex> G_Vertices;

bool Ready()
{
    if(G_Failed||!RenderEx::IsAvailable())return false;
    if(G_Program)return true;
    auto* Ex=RenderEx::GetPipelineEx();FRPExRenderTargetDesc Desc={0,0,1.f,RPExFormatA8R8G8B8};
    if(DALib::Pipeline->QueryInterface(Iids::RPSceneCapture,reinterpret_cast<void**>(&G_Capture))==GR_OK&&G_Capture&&
        Ex->CreateExProgram(RenderEx::GetExtraData(),"SHADERS\\engine_heat.hlsl","VSMain","PSMain",&G_Program)==GR_OK&&G_Program&&
        Ex->CreateExRenderTarget(&Desc,&G_Scene)==GR_OK&&G_Scene)return true;
    if(G_Program)Ex->DestroyExProgram(G_Program);if(G_Scene)Ex->DestroyExTexture(G_Scene);
    if(G_Capture)G_Capture->Release();G_Program=nullptr;G_Scene=nullptr;G_Capture=nullptr;G_Failed=true;
    FDUMP(0x100002,"Engine heat unavailable; original exhaust particles remain active.\n");return false;
}
float Clamp(float X,float A,float B){return (std::max)(A,(std::min)(B,X));}
// Engine transforms use a row-major rotation and trailing world translation.
FShipWarpPoint Rotate(float const* M,FShipWarpPoint P)
{return {M[0]*P.X+M[1]*P.Y+M[2]*P.Z,M[3]*P.X+M[4]*P.Y+M[5]*P.Z,M[6]*P.X+M[7]*P.Y+M[8]*P.Z};}
}
#endif

void EngineHeatVisualUpdate(FClientGameobj* Host,CEEngine const* Engine,float Intensity,float Dt)
{
#ifdef FREELANCER_RP9
    if(!Host||Host!=GetPlayerObjRW()||!Host->GetObject()||!Engine||!std::isfinite(Dt)||Dt<=0)return;
    auto* Obj=Host->GetObject();
    if(G_Heat.Host!=Host||G_Heat.Engine!=Engine||G_Heat.Id!=Host->get_id()||
        G_Heat.Instance!=Host->get_index()||G_Heat.System!=Obj->PhysicsSystemId) {
        G_Heat=FHeatState();G_Heat.Host=Host;G_Heat.Engine=Engine;G_Heat.Id=Host->get_id();
        G_Heat.Instance=Host->get_index();G_Heat.System=Obj->PhysicsSystemId;
    }
    G_Heat.Time=Clock(G_Heat.Time+Dt);
    float Target=Engine->IsActive()&&std::isfinite(Intensity)? .10f+.90f*std::sqrt(Clamp(Intensity,0,1)):0;
    G_Heat.Heat+=(Target-G_Heat.Heat)*(1-std::exp(-Clamp(Dt,0,.25f)*6));
#endif
}
void EngineHeatVisualForget(FClientGameobj* Host,CEEngine const* Engine)
{
#ifdef FREELANCER_RP9
    if(G_Heat.Host==Host&&G_Heat.Engine==Engine)G_Heat=FHeatState();
#endif
}
void EngineHeatVisualDraw(FSpaceCamera* Camera)
{
#ifdef FREELANCER_RP9
    if(!Camera||Camera==GetFirstPersonSpaceCamera()||!G_Heat.Host||G_Heat.Heat<.005f||
        !GetGameOption(kGameOptEffectsGroup)||!GetGameOption(kGameOptParticles)||
        !PortConfigInt("Render","engine_heat_visual",1)||!RenderEx::IsAvailable())return;
    // Check the live player before touching cached pointers (death, respawn, docking).
    if(GetPlayerObjRW()!=G_Heat.Host)return;
    auto* Host=G_Heat.Host;auto* Obj=Host->GetObject();
    if(!Obj||(Obj->ObjectClass&CObject::ClassShip)!=CObject::ClassShip||
        Host->get_id()!=G_Heat.Id||Host->get_index()!=G_Heat.Instance||Obj->PhysicsSystemId!=G_Heat.System)return;
    auto* Ship=static_cast<CShip*>(Obj);
    auto* Engine=static_cast<CEEngine const*>(Ship->EquipManager.FindFirst(EquipTypeEngine));
    if(!Engine||Engine!=G_Heat.Engine||Engine->NozzleInfos().empty()||!DALib::Engine)return;
    auto* Ex=RenderEx::GetPipelineEx();auto* Pipe=DALib::Pipeline;
    FRPExTexture* Depth=nullptr;unsigned long W=0,H=0;
    if(Ex->GetSceneDepth(&Depth)!=GR_OK||!Depth||Ex->GetExTextureSize(Depth,&W,&H)!=GR_OK||!W||!H)return;
    float Gain=G_Heat.Heat*(1-Clamp(Ship->CloakPercent,0,1));
    if(GetGameOption(kGameOptNebula)) {
        auto const& Pos=Host->get_position();float P[]={Pos.x,Pos.y,Pos.z};
        Gain*=NebulaVolume::EffectVisibility(Camera->GetPosition(),P);
    }
    if(Gain<.005f)return;
    float Radius=10;Vector Centre;if(Host->get_physical_radius(Radius,Centre)!=0||!std::isfinite(Radius))Radius=10;
    float Width=Clamp(Radius*.055f,.65f,6.f),Length=Width*(10+18*G_Heat.Heat);
    auto const* View=Camera->GetViewTransform();
    G_Vertices.clear();unsigned Index=0;
    for(auto const& Nozzle:Engine->NozzleInfos()) {
        if(Index++>=32)break;Transform Local={};
        if(Nozzle.ParentInstance==-1||!Nozzle.GetHardpointOffset_NS(Local))continue;
        auto const* M=DALib::Engine->GetInstanceTransform(reinterpret_cast<void*>(Nozzle.ParentInstance));
        if(!M)continue;
        auto Origin=Add(Rotate(M,{Local.Translation.x,Local.Translation.y,Local.Translation.z}),{M[9],M[10],M[11]});
        auto const& R=Local.Rotation.E;
        auto Right=Rotate(M,{R[0][0],R[1][0],R[2][0]}),Up=Rotate(M,{R[0][1],R[1][1],R[2][1]}),Back=Rotate(M,{R[0][2],R[1][2],R[2][2]});
        auto Mid=Add(Origin,Mul(Unit(Back,{0,0,1}),Width*.15f+Length*.5f));float ViewMid[3]={};
        for(int Row=0;Row<3;++Row)ViewMid[Row]=View[Row*3]*Mid.X+View[Row*3+1]*Mid.Y+View[Row*3+2]*Mid.Z+View[9+Row];
        if(Camera->ClassifySphere(ViewMid,std::sqrt(Length*Length*.25f+Width*Width))==1)continue;
        BuildEngineHeatVolume(G_Vertices,Origin,Right,Up,Back,Width,Length,std::fmod(Nozzle.Index*.173f+.13f,1.f));
    }
    if(G_Vertices.empty()||!Ready())return;
    Win3DApplyCamera(Camera);float V[36]={};auto const* Vp=Camera->GetViewport();
    for(int R=0;R<3;++R){for(int C=0;C<3;++C)V[R*4+C]=View[R*3+C];V[R*4+3]=View[9+R];}
    if(Pipe->GetProjection(V+12)!=GR_OK)return;
    V[28]=float(Vp[2]-Vp[0]+1)/W;V[29]=float(Vp[3]-Vp[1]+1)/H;
    V[30]=2.f*Vp[0]/W+V[28]-1;V[31]=1-2.f*Vp[1]/H-V[29];
    V[32]=Camera->GetZNear();V[33]=Camera->GetZFar();V[34]=0;V[35]=1;Pipe->GetDepthRange(V+34,V+35);
    float P[]={G_Heat.Time,Gain,1.f/W,1.f/H,0,0,0,0,V[32],V[33],V[34],V[35],
        (Vp[0]+.5f)/W,(Vp[1]+.5f)/H,(Vp[2]+.5f)/W,(Vp[3]+.5f)/H};
    if(G_Capture->CaptureSceneColor(G_Scene)!=GR_OK)return;
    FRPExPassDesc Pass={nullptr,RPExPassKeepDepth,0};if(Ex->BeginExPass(&Pass)!=GR_OK)return;
    Pipe->SetRenderState(D3DRS_ZENABLE,1);Pipe->SetRenderState(D3DRS_ZWRITEENABLE,0);
    Pipe->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);Pipe->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    Pipe->SetRenderState(D3DRS_ALPHATESTENABLE,0);Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE,1);
    Pipe->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);Pipe->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
    Pipe->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
    FRPExSamplerState Point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState Linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    if(Ex->BindExProgram(G_Program)==GR_OK&&Ex->BindExTexture(0,Depth,&Point)==GR_OK&&
        Ex->BindExTexture(1,G_Scene,&Linear)==GR_OK&&Ex->SetExVertexConstants(0,V,9)==GR_OK&&
        Ex->SetExPixelConstants(0,P,4)==GR_OK)
        RenderEx::GetDrawEx()->DrawExPrimitiveUp(D3DPT_TRIANGLELIST,D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1,G_Vertices.data(),static_cast<unsigned>(G_Vertices.size()));
    Ex->EndExPass();
#endif
}
void EngineHeatVisualShutdown()
{
#ifdef FREELANCER_RP9
    auto* Ex=RenderEx::GetPipelineEx();if(G_Program&&Ex)Ex->DestroyExProgram(G_Program);
    if(G_Scene&&Ex)Ex->DestroyExTexture(G_Scene);if(G_Capture)G_Capture->Release();
    G_Program=nullptr;G_Scene=nullptr;G_Capture=nullptr;G_Failed=false;G_Heat=FHeatState();G_Vertices.clear();
#endif
}
