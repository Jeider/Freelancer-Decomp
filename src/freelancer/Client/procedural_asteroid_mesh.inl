// Shared geometry and placement buffers persist. A pose change patches its slot;
// only crossing a camera cell (or replacing a snapshot) enumerates the field.
bool UpdateLocalMeshes(FCliAsteroid const* Field,FFarField& F,double const* Camera)
{
    namespace P=ProceduralAsteroids;
    int Cell[3];for(int k=0;k<3;++k)Cell[k]=P::Cell(float(Camera[k]));
    F.ZoneId=Field->Zone->GetId();unsigned Seed=0,Models=0,Revision=0;
    if(!ProceduralAsteroidClientRecipe(F.ZoneId,Seed,Models,Revision)||Models!=unsigned(F.TexCount))return false;
    ProceduralAsteroidClientCommitVisuals();
    bool full=!F.bLocalCellValid||Revision!=F.LocalRevision||std::memcmp(Cell,F.LocalCell,sizeof(Cell));
    std::vector<P::Key> changes;ProceduralAsteroidClientChanges(changes);
    if(!full&&changes.empty())return !F.bFailed;
    RuntimeHitchScope hitch("render_prepare",full?"procedural asteroid cell build":"procedural asteroid changed poses");
    if(full){
        ++F.LocalCellRevision;
        ProceduralAsteroidClientRenderer(F.ZoneId,false);F.LocalSlots.clear();F.LocalSlots.reserve(10000);
        for(int i=0;i<F.TexCount;++i){F.Meshes[i].Instances.clear();F.Meshes[i].RockIndices.clear();}
        F.RockCount=0;
    }
    float Radii[3];ZoneRadii(Field->Zone,Radii);
    float Edge=(std::min)(Radii[0],(std::min)(Radii[1],Radii[2]));double Axes[3][3];
    for(int k=0;k<3;++k)ZoneAxis(Field->Zone,k,Axes[k]);
    size_t First[4]={SIZE_MAX,SIZE_MAX,SIZE_MAX,SIZE_MAX},Last[4]={};
    auto dirty=[&](int model,size_t index){First[model]=(std::min)(First[model],index);Last[model]=(std::max)(Last[model],index+1);};
    auto apply=[&](P::Rock rock){
        auto old=F.LocalSlots.find(rock.key);
        bool exists=old!=F.LocalSlots.end();
        if(!ProceduralAsteroidClientResolve(F.ZoneId,rock)||ProceduralAsteroidClientNativeVisual(rock.key)){
            if(exists){auto const& slot=old->second;auto& instance=F.Meshes[slot.model].Instances[slot.index];
                if(instance.CentreRadius[3]!=0){instance.CentreRadius[3]=0;dirty(slot.model,slot.index);}}
            ProceduralAsteroidClientHide(rock.key);return;
        }
        // A hidden proxy must recover its radius even when the native body was
        // culled/suspended at the exact same position.
        if(exists&&F.Meshes[old->second.model].Instances[old->second.index].CentreRadius[3]>0&&
           !std::memcmp(old->second.position,rock.position,12)){
            auto const& slot=old->second;auto& instance=F.Meshes[slot.model].Instances[slot.index];
            unsigned colour=(instance.Colour&~255u)|(rock.colour&255u);
            if(std::memcmp(instance.Rotation,rock.rotation,16)||instance.Colour!=colour){
                std::memcpy(instance.Rotation,rock.rotation,16);instance.Colour=colour;dirty(slot.model,slot.index);
            }
            return;
        }
        Vector world{rock.position[0],rock.position[1],rock.position[2]};auto& mesh=F.Meshes[rock.model];
        float radius=mesh.SourceRadius;double distance2=0;
        for(int k=0;k<3;++k){double d=rock.position[k]-Camera[k];distance2+=d*d;}
        bool visible=distance2<8000.0*8000.0&&Field->Zone->GetImmersion(world)>0&&!CliAsteroidExcludesLocalMesh(Field,world,radius);
        double q2=0;for(int k=0;k<3;++k){double q=0;for(int a=0;a<3;++a)q+=(rock.position[a]-F.Anchor[a])*Axes[k][a];q/=Radii[k];q2+=q*q;}
        float fade=float(Clamp01(((1-std::sqrt(q2))*Edge-radius)/250.0));visible=visible&&fade>0;
        if(!visible&&!exists)return;
        if(!exists){FFarField::LocalSlot slot={int(rock.model),mesh.Instances.size(),{}};
            old=F.LocalSlots.emplace(rock.key,slot).first;mesh.Instances.push_back({});mesh.RockIndices.push_back(F.RockCount++);}
        auto& slot=old->second;std::memcpy(slot.position,rock.position,12);auto& instance=mesh.Instances[slot.index];
        for(int k=0;k<3;++k)instance.CentreRadius[k]=float(rock.position[k]-F.Anchor[k]);
        instance.CentreRadius[3]=visible?radius:0;std::memcpy(instance.Rotation,rock.rotation,16);
        instance.Colour=rock.colour|(unsigned(fade*255)<<8);dirty(slot.model,slot.index);
        if(visible)ProceduralAsteroidClientVisible(rock.key);else ProceduralAsteroidClientHide(rock.key);
    };
    if(full){
        float centre[3];for(int k=0;k<3;++k)centre[k]=(Cell[k]+.5f)*P::CellSize;
        P::Around(centre,P::View+867,Seed,Models,apply);
        std::vector<P::Rock> extra;ProceduralAsteroidClientExtras(F.ZoneId,extra);
        for(auto const& rock:extra)if(!F.LocalSlots.count(rock.key))apply(rock);
    }else for(auto key:changes)apply(P::Generate(key,Seed,Models));
    auto* ex=RenderEx::GetPipelineEx();if(!ex)return false;
    for(int i=0;i<F.TexCount;++i){auto& mesh=F.Meshes[i];if(First[i]==SIZE_MAX)continue;
        if(mesh.Instances.size()>mesh.PlacementCapacity||!mesh.Placement){
            if(mesh.Placement)ex->DestroyExVertexBuffer(mesh.Placement);mesh.Placement=nullptr;
            size_t capacity=((mesh.Instances.size()+511)/512)*512;std::vector<FMeshInstance> data(capacity);
            std::copy(mesh.Instances.begin(),mesh.Instances.end(),data.begin());
            if(ex->CreateExVertexBuffer(unsigned(data.size()*sizeof(FMeshInstance)),data.data(),&mesh.Placement)!=GR_OK){
                F.bFailed=true;ProceduralAsteroidClientRenderer(F.ZoneId,false);return false;}
            mesh.PlacementCapacity=capacity;
        }else if(ex->UpdateExVertexBuffer(mesh.Placement,unsigned(First[i]*sizeof(FMeshInstance)),
                     unsigned((Last[i]-First[i])*sizeof(FMeshInstance)),mesh.Instances.data()+First[i])!=GR_OK){
            F.bFailed=true;ProceduralAsteroidClientRenderer(F.ZoneId,false);return false;
        }
    }
    F.Classes.clear();F.Classes.push_back({F.RockCount,F.MaxRockRadius});
    std::memcpy(F.LocalCell,Cell,sizeof(Cell));F.bLocalCellValid=true;F.LocalRevision=Revision;
    if(full||First[0]!=SIZE_MAX||First[1]!=SIZE_MAX||First[2]!=SIZE_MAX||First[3]!=SIZE_MAX)++F.LocalMeshRevision;
    ProceduralAsteroidClientRenderer(F.ZoneId,true);return true;
}
