#include "cloak_visual.h"
#ifdef FREELANCER_RP9
#include "cloak_geometry.h"
#include "client_gameobj.h"
#include "client_objdb.h"
#include "player_behavior.h"
#include "space_camera.h"
#include "globals.h"
#include "game_options.h"
#include "port_config.h"
#include "nebula_volume.h"
#include "render_ex.h"
#include "win3d_render.h"
#include "DALib.h"
#include "dacom_iids.h"
#include "engine/engbase.h"
#include "render/rendcomp.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/IRPSceneCapture.h"
#include <algorithm>
#include <map>

namespace
{
struct Mesh {
    FRPExBuffer* Buffer=nullptr;unsigned Count=0;bool Seen=false;
};
struct Draw {Mesh* Geometry;float Model[12],Centre[4],Cloak,Visibility,Phase;};
// VMeshPart facets are borrowed: AddRef/Release are no-ops and archetypes delete
// them directly on unload. Cache only owned GPU copies, keyed by copied content.
std::map<CloakGeometry::Key,Mesh> Meshes;
std::map<const void*,uint64_t> FrameLibraries;
std::vector<Draw> Draws;
FRPExProgram* Program=nullptr;FRPExTexture* Scene=nullptr;IRPSceneCapture* Capture=nullptr;
bool Failed=false;unsigned System=0,LastFrame=~0u;float Time=0;
float Clamp(float v,float a,float b){return (std::max)(a,(std::min)(b,v));}
void ClearMeshes()
{
    auto* ex=RenderEx::GetPipelineEx();
    for(auto& item:Meshes)if(ex&&item.second.Buffer)ex->DestroyExVertexBuffer(item.second.Buffer);
    Meshes.clear();Draws.clear();FrameLibraries.clear();
}
bool Ready()
{
    if(Failed||!RenderEx::IsAvailable())return false;
    if(Program&&Scene&&Capture)return true;
    auto* ex=RenderEx::GetPipelineEx();FRPExRenderTargetDesc desc={0,0,1,RPExFormatA8R8G8B8};
    if(DALib::Pipeline->QueryInterface(Iids::RPSceneCapture,reinterpret_cast<void**>(&Capture))==GR_OK&&Capture&&
       ex->CreateExProgram(RenderEx::GetExtraData(),"SHADERS\\cloak_refraction.hlsl","VSMain","PSMain",&Program)==GR_OK&&Program&&
       ex->CreateExRenderTarget(&desc,&Scene)==GR_OK&&Scene)return true;
    if(Program)ex->DestroyExProgram(Program);if(Scene)ex->DestroyExTexture(Scene);if(Capture)Capture->Release();
    Program=nullptr;Scene=nullptr;Capture=nullptr;Failed=true;
    FDUMP(0x100002,"Cloak refraction unavailable; native cloaking fade retained.\n");return false;
}
Mesh* Geometry(void* instance)
{
    // The native renderer skips fully cloaked ships. Query a valid LOD explicitly, then
    // restore the shared archetype's selection before returning (including failure paths).
    int old=0,count=0;
    if(DALib::Renderer->GetInstanceCurrentLod(instance,&old)<0||
       DALib::Renderer->GetInstanceLodCount(instance,&count)<0||count<=0||old<0||old>count)return nullptr;
    int selected=old>=0&&old<count?old:0;
    if(selected!=old&&DALib::Renderer->SetInstanceLod(instance,selected)<0)return nullptr;
    IVMeshPart* raw=nullptr;
    int result=DALib::Engine->QueryInstance(instance,Iids::VMeshLibrary,reinterpret_cast<void**>(&raw));
    if(selected!=old)DALib::Renderer->SetInstanceLod(instance,old);
    if(result<0||!raw)return nullptr;
    const auto* ref=raw->GetRef();const auto* data=raw->GetHeader();if(!ref||!data)return nullptr;
    CloakGeometry::Part part={ref->VertexStart,ref->VertexCount,ref->IndexStart,ref->IndexCount,ref->FacegroupStart,ref->FacegroupCount};
    size_t bytes=CloakGeometry::Bytes(data);
    auto library=FrameLibraries.find(data);
    if(library==FrameLibraries.end())library=FrameLibraries.emplace(data,CloakGeometry::Fingerprint(data,bytes)).first;
    const auto key=CloakGeometry::ContentKey(library->second,part);
    auto it=Meshes.find(key);
    if(it!=Meshes.end()){it->second.Seen=true;return &it->second;}
    if(Meshes.size()>=512)return nullptr;
    std::vector<CloakGeometry::Vertex> triangles;
    if(!CloakGeometry::Decode(data,bytes,part,triangles))return nullptr;
    Mesh mesh;mesh.Count=static_cast<unsigned>(triangles.size());mesh.Seen=true;
    if(RenderEx::GetPipelineEx()->CreateExVertexBuffer(mesh.Count*sizeof(triangles[0]),triangles.data(),&mesh.Buffer)!=GR_OK||!mesh.Buffer)return nullptr;
    return &Meshes.emplace(key,std::move(mesh)).first->second;
}
void AddPart(void* instance,const Vector& centre,const float* viewCentre,float radius,float cloak,float visibility,float phase)
{
    if(!instance||instance==G_InvalidEngineHandle||Draws.size()>=1024)return;
    const float* world=DALib::Engine->GetInstanceTransform(instance);if(!world)return;
    Mesh* mesh=Geometry(instance);if(!mesh)return;
    Draw draw={};draw.Geometry=mesh;draw.Cloak=cloak;draw.Visibility=visibility;draw.Phase=phase;
    for(int r=0;r<3;++r){
        for(int c=0;c<3;++c)draw.Model[r*4+c]=world[r*3+c];
        draw.Model[r*4+3]=world[9+r]-(&centre.x)[r];draw.Centre[r]=viewCentre[r];
    }
    draw.Centre[3]=radius;Draws.push_back(draw);
}
}
#endif

void CloakVisualDraw(FSpaceCamera* camera)
{
#ifdef FREELANCER_RP9
    if(!camera||!DALib::Engine||!DALib::Renderer||!RenderEx::IsAvailable()||
       !GetGameOption(kGameOptEffectsGroup)||!GetGameOption(kGameOptObjectsGroup)||!GetGameOption(kGameOptShips)||
       !PortConfigInt("Render","cloak_refraction",1))return;
    const float strength=Clamp(PortConfigFloat("Render","cloak_refraction_strength",1),0,3);
    if(!(strength>0))return;
    unsigned frame=GetClientFrameCount();
    if(frame!=LastFrame){
        LastFrame=frame;float dt=static_cast<float>(GetClientFrameTimeCapped());
        if(std::isfinite(dt)&&dt>0)Time=std::fmod(Time+Clamp(dt,0,.25f),96.f);
    }
    auto* player=static_cast<FClientGameobj*>(GetPlayerObjRW());
    if(!player||!player->GetObject())return;
    unsigned system=player->GetObject()->PhysicsSystemId;
    if(System!=system){ClearMeshes();System=system;}
    Draws.clear();FrameLibraries.clear();for(auto& item:Meshes)item.second.Seen=false;
    struct Candidate{FClientGameobj* Ship;float Distance;};std::vector<Candidate> ships;
    int kind=1;const float* eye=camera->GetPosition();const float* view=camera->GetViewTransform();
    for(auto* ship=ClientObjDb_GetKindHead(&kind);ship;ship=ship->ListNext){
        auto* obj=ship->GetObject();
        if(!obj||ship->is_dying()||(obj->ObjectClass&CObject::ClassShip)!=CObject::ClassShip||obj->PhysicsSystemId!=system)continue;
        float cloak=static_cast<CEqObj*>(obj)->CloakPercent;
        if(!std::isfinite(cloak)||cloak<=.001f||(ship==player&&camera==GetFirstPersonSpaceCamera()))continue;
        auto& p=ship->get_position();float x=p.x-eye[0],y=p.y-eye[1],z=p.z-eye[2];
        float dist=std::sqrt(x*x+y*y+z*z);if(!std::isfinite(dist)||dist>5000)continue;
        ships.push_back({ship,dist});
    }
    std::sort(ships.begin(),ships.end(),[](const Candidate& a,const Candidate& b){return a.Distance<b.Distance;});
    if(ships.size()>16)ships.resize(16);
    if(!ships.empty()&&!Ready())return;
    for(const auto& candidate:ships){
        auto* ship=candidate.Ship;auto& pos=ship->get_position();
        Vector sphere;float radius=ship->Slot178(sphere);if(!std::isfinite(radius)||radius<=0)continue;
        radius=Clamp(radius,1,2000);float vc[3]={},classify[3]={};
        float delta[]={pos.x-eye[0],pos.y-eye[1],pos.z-eye[2]};
        for(int r=0;r<3;++r)vc[r]=view[r*3]*delta[0]+view[r*3+1]*delta[1]+view[r*3+2]*delta[2];
        std::memcpy(classify,vc,sizeof(vc));if(camera->ClassifySphere(classify,radius*1.08f)==1)continue;
        vc[2]=-vc[2];
        float visibility=1-Clamp((candidate.Distance-3000)/2000,0,1);
        if(GetGameOption(kGameOptNebula))visibility*=NebulaVolume::EffectVisibility(eye,&pos.x);
        if(visibility<.005f)continue;
        float cloak=Clamp(static_cast<CEqObj*>(ship->GetObject())->CloakPercent,0,1);
        float phase=(ship->get_id()%4096)*(6.283185307f/4096);
        void* root=reinterpret_cast<void*>(static_cast<intptr_t>(ship->get_index()));
        if(!root||root==G_InvalidEngineHandle)continue;
        AddPart(root,pos,vc,radius,cloak,visibility,phase);
        void* child=G_InvalidEngineHandle;unsigned count=0;
        while((child=DALib::Engine->GetRelatedInstance(root,0,child))!=G_InvalidEngineHandle&&child&&count++<128)
            AddPart(child,pos,vc,radius,cloak,visibility,phase);
    }
    auto* ex=RenderEx::GetPipelineEx();auto* pipe=DALib::Pipeline;
    for(auto it=Meshes.begin();it!=Meshes.end();){
        if(!it->second.Seen){if(it->second.Buffer)ex->DestroyExVertexBuffer(it->second.Buffer);it=Meshes.erase(it);}else ++it;
    }
    if(Draws.empty())return;
    FRPExTexture* depth=nullptr;unsigned long w=0,h=0;
    if(ex->GetSceneDepth(&depth)!=GR_OK||!depth||ex->GetExTextureSize(depth,&w,&h)!=GR_OK||!w||!h)return;
    Win3DApplyCamera(camera);const auto* viewport=camera->GetViewport();float v[56]={};
    for(int r=0;r<3;++r)for(int c=0;c<3;++c)v[r*4+c]=view[r*3+c];
    if(pipe->GetProjection(v+12)!=GR_OK)return;
    v[28]=float(viewport[2]-viewport[0]+1)/w;v[29]=float(viewport[3]-viewport[1]+1)/h;
    v[30]=2.f*viewport[0]/w+v[28]-1;v[31]=1-2.f*viewport[1]/h-v[29];
    v[32]=camera->GetZNear();v[33]=camera->GetZFar();v[34]=0;v[35]=1;pipe->GetDepthRange(v+34,v+35);
    if(Capture->CaptureSceneColor(Scene)!=GR_OK)return;
    FRPExPassDesc pass={nullptr,RPExPassKeepDepth,0};if(ex->BeginExPass(&pass)!=GR_OK)return;
    pipe->SetRenderState(D3DRS_ZENABLE,0);pipe->SetRenderState(D3DRS_ZWRITEENABLE,0); // shader tests immutable scene depth
    pipe->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);pipe->SetRenderState(D3DRS_ALPHATESTENABLE,0);
    pipe->SetRenderState(D3DRS_ALPHABLENDENABLE,1);pipe->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
    pipe->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);pipe->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
    FRPExSamplerState point={RPExFilterPoint,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    FRPExSamplerState linear={RPExFilterLinear,RPExMipNone,RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
    if(ex->BindExProgram(Program)==GR_OK&&ex->BindExTexture(0,depth,&point)==GR_OK&&ex->BindExTexture(1,Scene,&linear)==GR_OK){
        for(const auto& draw:Draws){
            std::memcpy(v+36,draw.Model,48);std::memcpy(v+48,draw.Centre,16);
            v[52]=Time;v[53]=draw.Cloak;v[54]=strength;v[55]=draw.Phase;
            float p[]={Time,draw.Cloak,1.f/w,1.f/h,strength,draw.Visibility,draw.Centre[3],draw.Phase,
                v[32],v[33],v[34],v[35],(viewport[0]+.5f)/w,(viewport[1]+.5f)/h,(viewport[2]+.5f)/w,(viewport[3]+.5f)/h};
            if(ex->SetExVertexConstants(0,v,14)==GR_OK&&ex->SetExPixelConstants(0,p,4)==GR_OK)
                RenderEx::GetDrawEx()->DrawExVertexBuffer(draw.Geometry->Buffer,D3DPT_TRIANGLELIST,D3DFVF_XYZ|D3DFVF_NORMAL,
                    sizeof(CloakGeometry::Vertex),0,draw.Geometry->Count/3);
        }
    }
    ex->EndExPass();
#endif
}
void CloakVisualShutdown()
{
#ifdef FREELANCER_RP9
    ClearMeshes();auto* ex=RenderEx::GetPipelineEx();if(Program&&ex)ex->DestroyExProgram(Program);
    if(Scene&&ex)ex->DestroyExTexture(Scene);if(Capture)Capture->Release();
    Program=nullptr;Scene=nullptr;Capture=nullptr;Failed=false;System=0;LastFrame=~0u;Time=0;
#endif
}
