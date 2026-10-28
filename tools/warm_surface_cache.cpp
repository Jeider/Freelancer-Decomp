// Pre-compiles every surface / local-shadow shader variant RP9 builds at run time into the RP9
// shader cache (%LOCALAPPDATA%\Freelancer-Decomp\RP9\ShaderCache, or FREELANCER_SHADER_CACHE_DIR),
// one worker thread per variant, as RP9's own warm-up at device creation does. The cache key
// covers the expanded source, entry, profile and the d3dx9_43 / d3dcompiler_43 contents, not
// the working directory or the calling module, so the game finds these entries.
// Run from the game root (the folder holding DATA_EXTRA).
#include "RP9ShaderCache.h"
#include <atomic>
#include <algorithm>
#include <cstdio>
#include <thread>

static bool ReadText(const char* Path, std::string* Out)
{
    FILE* File=fopen(Path,"rb");if(!File) return false;
    char Buffer[4096];size_t N;
    while((N=fread(Buffer,1,sizeof(Buffer),File))) Out->append(Buffer,N);
    fclose(File);return true;
}

// The shader folder on disk, as RP9's warm-up threads resolve #include.
class FDirInclude final : public ID3DXInclude
{
public:
    explicit FDirInclude(std::string D) : Dir(std::move(D)) {}
    STDMETHOD(Open)(D3DXINCLUDE_TYPE,LPCSTR Name,LPCVOID,LPCVOID* Data,UINT* Bytes) override
    {
        std::string T;if(!ReadText((Dir+Name).c_str(),&T)) return E_FAIL;
        char* C=new char[T.size()+1];memcpy(C,T.data(),T.size());C[T.size()]=0;*Data=C;*Bytes=(UINT)T.size();return S_OK;
    }
    STDMETHOD(Close)(LPCVOID Data) override {delete[] (const char*)Data;return S_OK;}
private:
    std::string Dir;
};

struct FJob {std::string Name,Text;const char* Entry;const char* Profile;bool UseInclude=false;
             HRESULT Hr=E_FAIL;bool Hit=false,Stored=false;size_t Size=0;ULONGLONG Ms=0;std::string Messages;};

int main()
{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
    std::string Surface,Shadow;
    if(!ReadText("DATA_EXTRA/SHADERS/surface_material.hlsl",&Surface) ||
       !ReadText("DATA_EXTRA/SHADERS/local_shadow.hlsl",&Shadow)) {puts("run from the game root");return 1;}
    // The exact source prefixes ExSurfaceBegin / ExFlushSurfaceInstances / BeginLocalShadowMap use.
    std::vector<FJob> Jobs;
    auto Add=[&](const char* Name,std::string Text,const char* Entry,const char* Profile)
    {FJob J;J.Name=Name;J.Text=std::move(Text);J.Entry=Entry;J.Profile=Profile;Jobs.push_back(std::move(J));};
    Add("surface VS",Surface,"VSMain","vs_3_0");
    Add("surface VS instanced","#define SURFACE_INSTANCED 1\n"+Surface,"VSMain","vs_3_0");
    const char* Variants[3]={"","#define SURFACE_NO_SHADOW 1\n","#define SURFACE_LOW_DETAIL 1\n"};
    const char* Names[3]={"full","no shadow","low detail"};
    for(unsigned I=0;I<3;++I)
        for(unsigned C=0;C<2;++C)
        {
            char Name[64];sprintf(Name,"surface PS %s%s",Names[I],C ? " cube" : "");
            Add(Name,std::string(Variants[I])+(C ? "#define SURFACE_ENV_CUBE 1\n" : "")+Surface,"PSMain","ps_3_0");
        }
    Add("local shadow VS",Shadow,"VSMain","vs_3_0");
    if(Surface.find("SURFACE_GREENHOUSE")!=std::string::npos)
        for(unsigned S=0;S<2;++S)for(unsigned C=0;C<2;++C)
        {
            std::string Name=std::string("greenhouse PS")+(S ? " no shadow":" full")+(C ? " cube":"");
            Add(Name.c_str(),std::string("#define SURFACE_GREENHOUSE 1\n")+
                (S ? "#define SURFACE_NO_SHADOW 1\n":"")+(C ? "#define SURFACE_ENV_CUBE 1\n":"")+Surface,"PSMain","ps_3_0");
        }
    Add("local shadow PS",Shadow,"PSMain","ps_3_0");
    if(Surface.find("SURFACE_SHIP_NORMALS")!=std::string::npos)
        for(unsigned S=0;S<2;++S)for(unsigned C=0;C<2;++C)
        {
            std::string Name=std::string("ship normal PS")+(S ? " no shadow":" full")+(C ? " cube":"");
            Add(Name.c_str(),std::string("#define SURFACE_SHIP_NORMALS 1\n")+
                (S ? "#define SURFACE_NO_SHADOW 1\n":"")+(C ? "#define SURFACE_ENV_CUBE 1\n":"")+Surface,"PSMain","ps_3_0");
        }
    if(Surface.find("SURFACE_NOMAD")!=std::string::npos)
    {
        Add("nomad VS","#define SURFACE_NOMAD 1\n"+Surface,"VSMain","vs_3_0");
        Add("nomad depth PS","#define SURFACE_NOMAD 1\n#define SURFACE_NOMAD_LIGHT 1\n#define SURFACE_NO_SHADOW 1\n"+Surface,"PSNomadDepth","ps_3_0");
        for(unsigned L=0;L<2;++L)for(unsigned S=0;S<2;++S)
        {
            std::string Name=std::string("nomad PS")+(L?" light":" full")+(S?" no shadow":" shadow");
            Add(Name.c_str(),std::string("#define SURFACE_NOMAD 1\n")+(L?"#define SURFACE_NOMAD_LIGHT 1\n":"")+
                (S?"#define SURFACE_NO_SHADOW 1\n":"")+Surface,"PSMain","ps_3_0");
        }
    }
    std::string Room;
    if(ReadText("DATA_EXTRA/SHADERS/room_material.hlsl", &Room))
    {
        Add("room VS",Room,"VSMain","vs_3_0");
        Add("room VS skinned",Room,"VSSkin","vs_3_0");
        Add("room PS",Room,"PSMain","ps_3_0");
    }
    std::string Contact;
    if(ReadText("DATA_EXTRA/SHADERS/room_contact.hlsl", &Contact))
        Add("room contact PS",Contact,"PSMain","ps_3_0");
    std::string RoomShadow;
    if(ReadText("DATA_EXTRA/SHADERS/room_shadow.hlsl", &RoomShadow))
    {
        Add("room shadow VS",RoomShadow,"VSMain","vs_3_0");
        Add("room shadow skin VS",RoomShadow,"VSSkin","vs_3_0");
        Add("room shadow PS",RoomShadow,"PSMain","ps_3_0");
        Add("room shadow apply PS",RoomShadow,"ApplyPS","ps_3_0");
    }
    const ULONGLONG Start=GetTickCount64();
    // Asteroid / debris relief (IRPRockNormals).
    if(Surface.find("SURFACE_ROCK")!=std::string::npos)
        for(unsigned S=0;S<2;++S)for(unsigned C=0;C<2;++C)
        {
            std::string Name=std::string("rock PS")+(S ? " no shadow":" full")+(C ? " cube":"");
            Add(Name.c_str(),std::string("#define SURFACE_ROCK 1\n")+
                (S ? "#define SURFACE_NO_SHADOW 1\n":"")+(C ? "#define SURFACE_ENV_CUBE 1\n":"")+Surface,"PSMain","ps_3_0");
        }
    std::string Beam;
    if(ReadText("DATA_EXTRA/SHADERS/code_beam.hlsl", &Beam))
    {
        Add("code beam VS",Beam,"VSMain","vs_3_0");
        Add("code beam PS",Beam,"PSMain","ps_3_0");
    }
    // The rest of RP9's warm-up: whole-file shaders and the client's CreateExProgram programs.
    struct FPair {const char* File;const char* Vs;const char* Ps;};
    static const FPair Whole[]={
        {"planet_atmosphere.hlsl","VSMain","PSMain"},{"planet_surface.hlsl","VSMain","PSMain"},
        {"planet_ring.hlsl","VSMain","PSMain"},{"scene_fxaa.hlsl",nullptr,"PSMain"}};
    for(const FPair& P:Whole)
    {
        std::string T;if(!ReadText((std::string("DATA_EXTRA/SHADERS/")+P.File).c_str(),&T)) continue;
        if(P.Vs) Add((std::string(P.File)+" "+P.Vs).c_str(),T,P.Vs,"vs_3_0");
        if(P.Ps) Add((std::string(P.File)+" "+P.Ps).c_str(),T,P.Ps,"ps_3_0");
    }
    {
        std::string Lib,Entry;
        if(ReadText("DATA_EXTRA/SHADERS/SMAA/SMAA.hlsl",&Lib) && ReadText("DATA_EXTRA/SHADERS/scene_smaa.hlsl",&Entry))
        {
            const std::string Smaa="float4 PixelSize : register(c0);\n#define SMAA_RT_METRICS PixelSize\n"
                "#define SMAA_HLSL_3 1\n#define SMAA_PRESET_HIGH 1\n"+Lib+"\n"+Entry;
            for(const char* N:{"EdgesPS","WeightsPS","BlendPS"}) Add((std::string("smaa ")+N).c_str(),Smaa,N,"ps_3_0");
        }
    }
    static const FPair Programs[]={
        {"engine_heat.hlsl","VSMain","PSMain"},{"far_rocks.hlsl","VSMain","PSMain"},{"far_rocks.hlsl","VSMesh","PSMesh"},
        {"field_dust.hlsl","VSMain","PSMarch"},{"field_dust.hlsl","VSMain","PSComposite"},
        {"hyperspace_refraction.hlsl","VSMain","PSMain"},{"hyperspace_tunnel.hlsl","VSMain","PSMain"},
        {"hyperspace_tunnel.hlsl","VSLaunch","PSLaunch"},{"jumpgate_aperture.hlsl","VSMain","PSMain"},
        {"jumpgate_aperture.hlsl","VSMain","PSLens"},{"jumpgate_aperture.hlsl","VSInflow","PSInflow"},
        {"jumpgate_aperture.hlsl","VSMain","PSDonuts"},{"jumphole_lens.hlsl","VSMain","PSLens"},
        {"jumphole_lens.hlsl","VSMain","PSGlow"},{"jumphole_lens.hlsl","VSIngress","PSIngress"},
        {"jumphole_optics.hlsl","VSOpticsWorld","PSOpticsWorld"},{"jumphole_optics.hlsl","VSOpticsScreen","PSOpticsShip"},
        {"nebula_volume.hlsl","VSMain","PSRaymarch"},{"nebula_composite.hlsl","VSMain","PSComposite"},
        {"nebula_ice.hlsl","VSMain","PSRaymarch"},{"nebula_walker_ice.hlsl","VSMain","PSRaymarch"},
        {"solar_rays.hlsl","VSMain","PSMain"},{"solar_corona.hlsl","VSMain","PSMain"},{"ship_warp.hlsl","VSMain","PSWarp"},
        {"space_haze.hlsl","VSMain","PSMain"},{"tradelane_corridor.hlsl","VSMain","PSMain"},
        {"tradelane_corridor.hlsl","VSMain","PSWarp"}};
    for(const FPair& P:Programs)
    {
        std::string Body;if(!ReadText((std::string("DATA_EXTRA/SHADERS/")+P.File).c_str(),&Body)) continue;
        const std::string T=std::string("#line 1 \"SHADERS/")+P.File+"\"\n"+Body;
        Add((std::string(P.File)+" "+P.Vs).c_str(),T,P.Vs,"vs_3_0");Jobs.back().UseInclude=true;
        Add((std::string(P.File)+" "+P.Ps).c_str(),T,P.Ps,"ps_3_0");Jobs.back().UseInclude=true;
    }
    // A pool, not a thread per job: a cold compile is heavy.
    std::atomic<size_t> Next{0};
    std::vector<std::thread> Threads;
    const unsigned Workers=(std::max)(2u,std::thread::hardware_concurrency()-1);
    for(unsigned W=0;W<Workers;++W) Threads.emplace_back([&](){
        for(size_t I;(I=Next.fetch_add(1))<Jobs.size();)
        {
            FJob& J=Jobs[I];
            std::vector<unsigned char> Code;const ULONGLONG T=GetTickCount64();
            FDirInclude Include("DATA_EXTRA/SHADERS/");
            J.Hr=Rp9ShaderCache::Compile(J.Text,J.UseInclude ? &Include : nullptr,J.Entry,J.Profile,0,&Code,&J.Messages,&J.Hit,&J.Stored);
            J.Size=Code.size();J.Ms=GetTickCount64()-T;
        }});
    for(std::thread& T:Threads) T.join();
    bool Ok=true;
    for(FJob const& J:Jobs)
    {
        if(FAILED(J.Hr)) {printf("%s: FAILED\n%s\n",J.Name.c_str(),J.Messages.c_str());Ok=false;continue;}
        printf("%-30s %s, %zu bytes, %llu ms\n",J.Name.c_str(),J.Hit ? "HIT" : J.Stored ? "stored" : "not stored",
               J.Size,(unsigned long long)J.Ms);
    }
    printf("total %llu ms\n",(unsigned long long)(GetTickCount64()-Start));
    return Ok ? 0 : 2;
}
