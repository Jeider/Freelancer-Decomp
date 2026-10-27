// Pre-compiles every surface / local-shadow shader variant RP9 builds at run time into the RP9
// shader cache (%LOCALAPPDATA%\Freelancer-Decomp\RP9\ShaderCache, or FREELANCER_SHADER_CACHE_DIR),
// one worker thread per variant, as RP9's own warm-up at device creation does. The cache key
// covers the expanded source, entry, profile and the d3dx9_43 / d3dcompiler_43 contents, not
// the working directory or the calling module, so the game finds these entries.
// Run from the game root (the folder holding DATA_EXTRA).
#include "RP9ShaderCache.h"
#include <cstdio>
#include <thread>

static bool ReadText(const char* Path, std::string* Out)
{
    FILE* File=fopen(Path,"rb");if(!File) return false;
    char Buffer[4096];size_t N;
    while((N=fread(Buffer,1,sizeof(Buffer),File))) Out->append(Buffer,N);
    fclose(File);return true;
}

struct FJob {std::string Name,Text;const char* Entry;const char* Profile;
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
    std::string Beam;
    if(ReadText("DATA_EXTRA/SHADERS/code_beam.hlsl", &Beam))
    {
        Add("code beam VS",Beam,"VSMain","vs_3_0");
        Add("code beam PS",Beam,"PSMain","ps_3_0");
    }
    std::vector<std::thread> Threads;
    for(FJob& J:Jobs) Threads.emplace_back([&J](){
        std::vector<unsigned char> Code;const ULONGLONG T=GetTickCount64();
        J.Hr=Rp9ShaderCache::Compile(J.Text,nullptr,J.Entry,J.Profile,0,&Code,&J.Messages,&J.Hit,&J.Stored);
        J.Size=Code.size();J.Ms=GetTickCount64()-T;});
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
