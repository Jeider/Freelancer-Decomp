// All deformable draw entry points meet here: room actors, cutscenes, portraits.
// The optional pipeline scope distinguishes colour/shadow/UI without guessing FVF.
static float CharacterScreenSize(FDeformInstance* instance,ICamera* camera)
{
    if(!camera || instance->PartCount<=0)return -1;
    float radius=0,center[3]={};
    auto& first=instance->PartArray[0];
    if(first.MeshCount<=0 || !PartBoundSphere(&first,&radius,center))return -1;
    for(int i=1;i<instance->PartCount;++i){
        float r=0,p[3]={};auto& part=instance->PartArray[i];
        if(part.MeshCount<=0 || !PartBoundSphere(&part,&r,p))continue;
        float x=p[0]-center[0],y=p[1]-center[1],z=p[2]-center[2];
        radius=(std::max)(radius,std::sqrt(x*x+y*y+z*z)+r);
    }
    float x=0,y=0,depth=0;
    if(!camera->Project(&x,&y,&depth,center))return -1;
    auto* viewport=camera->GetViewport();
    if(!viewport)return -1;
    float nearPlane=camera->GetZNear();
    return CharacterQuality::ScreenSize(radius,depth,nearPlane,
        float(camera->GetYScaleOverNear()*nearPlane),float(viewport[3]-viewport[1]+1));
}

struct FCharacterQualityScope
{
    IRPCharacterQuality* Pipeline=nullptr;
    float Previous=1;
    FCharacterQualityScope(FDeformInstance* instance,ICamera* camera)
    {
        if(!G_QualityPipeline)return;
        auto it=G_CharacterQuality.find(instance);
        if(it==G_CharacterQuality.end())return;
        auto& q=it->second;unsigned pass=G_QualityPipeline->CharacterQualityPass();
        int tier=0;
        if(pass==1){
            float pixels=CharacterScreenSize(instance,camera);
            int level=int(CharacterRenderValue("character_detail_quality",3.f));
            FCharacterViewQuality* view=nullptr;
            for(auto& v:q.Views)if(v.Camera==camera && camera){view=&v;break;}
            bool reset=!view;
            if(!view){view=&q.Views[q.NextView++%2];*view=FCharacterViewQuality{};view->Camera=camera;}
            tier=CharacterQuality::Update(view->State,pixels,level,reset);
            Pipeline=G_QualityPipeline;Previous=Pipeline->SetCharacterQuality(CharacterQuality::Strength(pixels,level));
        }else if(pass==2){
            // Reuse the colour-camera decision: the shadow camera must not advance
            // hysteresis or repeatedly switch buffers back to the nearest mesh.
            tier=q.AppliedTier;
        }
        q.AppliedTier=tier;
        for(int i=0;i<instance->PartCount;++i){
            auto& part=instance->PartArray[i];auto& meta=q.Parts[i];
            int pick=CharacterQuality::Pick(meta.Requested,part.MeshCount,meta.Native,tier);
            if(SelectPartLod(&part,pick))MarkPartSkinDirty(&part);
        }
    }
    ~FCharacterQualityScope(){if(Pipeline)Pipeline->SetCharacterQuality(Previous);}
};
