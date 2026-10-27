// Included by RP9Ex.cpp. Maps are prepared at device creation, never generated or loaded during a draw.
static std::string ShipNormalPath(const char* File)
{
    char Path[MAX_PATH]={};GetModuleFileNameA(nullptr,Path,MAX_PATH);
    char* Slash=strrchr(Path,'\\');if(!Slash)return {};Slash[1]=0;
    return std::string(Path)+"../DATA_EXTRA/SHIP_NORMALS/"+File;
}

GENRESULT DACOM_API FDirectX9::SetShipNormalScope(unsigned long Enabled, const char* Model)
{
    auto* E=Ex_;if(!E)return GR_GENERIC;
    // Scopes are object boundaries, so queued draws cannot inherit the next object's profile.
    ExFlushSurfaceInstances();
    E->bShipNormalScope=Enabled!=0;E->ShipNormalCurrent=nullptr;
    E->bSolarNormalScope=false;
    E->ShipNormalRange=Enabled>1 ? float(Enabled) : 0.0f;
    if(Model && E->bShipNormalScope)
    {
        std::string Key=LowerString(Model);std::replace(Key.begin(),Key.end(),'\\','/');
        E->bSolarNormalScope=Key.compare(0,6,"solar/")==0;
        if(Key.find("nmd")!=std::string::npos || Key.find("nomad")!=std::string::npos ||
            E->ShipNormalExcludedModels.count(Key) ||
            (Key.compare(0,6,"solar/")==0 && !E->ShipNormalHumanSolars.count(Key))) E->bShipNormalScope=false;
    }
    return GR_OK;
}

void FDirectX9::ExShipNormalsPrepare()
{
    auto* E=Ex_;if(!E || !Device_ || E->bShipNormalsPrepared)return;
    E->bShipNormalsPrepared=true;
    E->ShipNormalStrength=ReadShadowSetting("ship_normal_strength",0.25f,0,4);
    if(ReadShadowSetting("ship_normals",1,0,1)<.5f || E->ShipNormalStrength<=0)return;
    char Line[1800],Map[65],Key[1536];
    if(FILE* F=fopen(ShipNormalPath("human_solars.txt").c_str(),"rb"))
    {
        while(fgets(Line,sizeof(Line),F)){Line[strcspn(Line,"\r\n")]=0;E->ShipNormalHumanSolars.insert(LowerString(Line));}
        fclose(F);
    }
    if(FILE* F=fopen(ShipNormalPath("excluded_models.txt").c_str(),"rb"))
    {
        while(fgets(Line,sizeof(Line),F)){Line[strcspn(Line,"\r\n")]=0;E->ShipNormalExcludedModels.insert(LowerString(Line));}
        fclose(F);
    }
    for(const char* ProfileFile : {"profiles.txt","solar_profiles.txt"})
    if(FILE* F=fopen(ShipNormalPath(ProfileFile).c_str(),"rb"))
    {
        while(fgets(Line,sizeof(Line),F))
        {
            if(sscanf(Line,"%64s %1535[^\r\n]",Map,Key)!=2 || strlen(Map)!=36 ||
                strspn(Map,"0123456789abcdef")!=32 || strcmp(Map+32,".dds"))continue;
            std::string Identity=LowerString(Key);
            if(Identity.find("nmd")!=std::string::npos || Identity.find("nomad")!=std::string::npos)continue;
            auto& Profiles=ProfileFile[0]=='s' ? E->SolarNormalProfiles : E->ShipNormalProfiles;
            Profiles[Identity]=&E->ShipNormalMaps[Map];
        }
        fclose(F);
    }
    unsigned Ready=0;
    for(auto& Item:E->ShipNormalMaps)
    {
        RuntimeHitchScope Hitch("ship_normal_preload",Item.first.c_str());
        HRESULT Hr=D3DXCreateTextureFromFileExA(Device_,ShipNormalPath(Item.first.c_str()).c_str(),D3DX_DEFAULT,D3DX_DEFAULT,
            D3DX_DEFAULT,0,D3DFMT_UNKNOWN,D3DPOOL_MANAGED,D3DX_FILTER_NONE,D3DX_FILTER_NONE,0,nullptr,nullptr,&Item.second.Texture);
        if(SUCCEEDED(Hr) && Item.second.Texture){Item.second.Texture->PreLoad();++Ready;}

    }
    ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"ship normals: %u/%u maps preloaded, %u profiles, strength %.2f (player; nearby human solars/capitals/cruisers)",
        Ready,(unsigned)E->ShipNormalMaps.size(),(unsigned)(E->ShipNormalProfiles.size()+E->SolarNormalProfiles.size()),double(E->ShipNormalStrength));
}

void FDirectX9::ExShipNormalsRelease()
{
    auto* E=Ex_;if(!E)return;
    E->ShipNormalCurrent=nullptr;E->bShipNormalScope=false;
    for(auto& Item:E->ShipNormalMaps)
    {
        if(Item.second.Texture)Item.second.Texture->Release();
    }
    for(auto*& Ps:E->ShipNormalPs)if(Ps){Ps->Release();Ps=nullptr;}
    E->ShipNormalProfiles.clear();E->ShipNormalMaps.clear();E->ShipNormalExcludedModels.clear();E->bShipNormalsPrepared=false;
    E->ShipNormalHumanSolars.clear();E->ShipNormalRange=0;
    E->SolarNormalProfiles.clear();E->bSolarNormalScope=false;
}
