// Uses the resolved placement cache only: no procedural generation, zone queries,
// or pose interpolation here. Unchanged groups never lock their GPU buffers.
bool PrepareLocalLods(FFarField& F, double const* Camera, double Pixels)
{
    if(F.LodRevision==F.LocalMeshRevision && F.LodPixels==Pixels &&
       !std::memcmp(F.LodCamera,Camera,sizeof(F.LodCamera))) return true;
    auto* Ex=RenderEx::GetPipelineEx();if(!Ex)return false;
    for(int i=0;i<F.TexCount;++i){
        auto& M=F.Meshes[i];
        if(M.LodCellRevision!=F.LocalCellRevision){M.LastLod.clear();M.LodCellRevision=F.LocalCellRevision;}
        M.LastLod.resize(M.Instances.size(),3);
        for(auto& L:M.Lods)L.Scratch.clear();
        for(size_t j=0;j<M.Instances.size();++j){
            auto const& I=M.Instances[j];if(I.CentreRadius[3]<=0)continue;
            double d2=0;for(int k=0;k<3;++k){double d=I.CentreRadius[k]+F.Anchor[k]-Camera[k];d2+=d*d;}
            // Same finite reach as the shader; resident cells include a margin.
            if(d2>double(F.FarDist)*F.FarDist)continue;
            double rp=I.CentreRadius[3]*Pixels;
            unsigned lod=M.Lods[1].Geometry&&M.Lods[2].Geometry?AsteroidLod::Select(rp*rp,d2,M.LastLod[j]):0;
            M.LastLod[j]=static_cast<unsigned char>(lod);M.Lods[lod].Scratch.push_back(I);
        }
        for(auto& L:M.Lods){
            size_t bytes=L.Scratch.size()*sizeof(FMeshInstance);
            if(L.Scratch.size()==L.Instances.size() && (!bytes||!std::memcmp(L.Scratch.data(),L.Instances.data(),bytes)))continue;
            if(!L.Scratch.empty()){
                if(!L.Placement||L.Scratch.size()>L.Capacity){
                    size_t capacity=((L.Scratch.size()+511)/512)*512;
                    std::vector<FMeshInstance> data(capacity);
                    std::copy(L.Scratch.begin(),L.Scratch.end(),data.begin());
                    FRPExBuffer* buffer=nullptr;
                    if(Ex->CreateExVertexBuffer(unsigned(data.size()*sizeof(FMeshInstance)),data.data(),&buffer)!=GR_OK)return false;
                    if(L.Placement)Ex->DestroyExVertexBuffer(L.Placement);
                    L.Placement=buffer;L.Capacity=capacity;
                }else if(Ex->UpdateExVertexBuffer(L.Placement,0,unsigned(bytes),L.Scratch.data())!=GR_OK)return false;
            }
            L.Instances.swap(L.Scratch);
        }
    }
    F.LodRevision=F.LocalMeshRevision;F.LodPixels=Pixels;std::memcpy(F.LodCamera,Camera,sizeof(F.LodCamera));
    return true;
}
