#include "RP9ShaderManifest.h"
#include <fstream>
#include <sstream>
#include <map>
#include <stdexcept>

struct Stage {std::string file,entry,profile;bool include;};
static std::map<std::string,std::string> Memo;
static std::string Key(const Rp9Startup::FJob& Job,const std::string& Directory) {
    const DWORD Flags=Rp9ShaderCache::FlagsForSource(Job.Text)|Job.Flags;
    std::string Request=Job.Text+'\0'+Job.Entry+'\0'+Job.Profile+'\0'+std::to_string(Flags);
    auto Found=Memo.find(Request);if(Found!=Memo.end())return Found->second;
    Rp9Startup::DirectoryInclude Include(Directory);
    ID3DXBuffer *Expanded=nullptr,*Errors=nullptr;
    HRESULT Hr=D3DXPreprocessShader(Job.Text.data(),(UINT)Job.Text.size(),nullptr,Job.UseInclude?&Include:nullptr,&Expanded,&Errors);
    if(Errors) {fprintf(stderr,"%s\n",(char*)Errors->GetBufferPointer());Errors->Release();}
    if(FAILED(Hr)||!Expanded)throw std::runtime_error("preprocessing failed");
    std::string Text((char*)Expanded->GetBufferPointer());Expanded->Release();
    // Same canonicalization as RP9ShaderCache::Compile, without compiling/storing.
    for(size_t At=Text.find("#line");At!=std::string::npos;At=Text.find("#line",At+5)) {
        size_t End=Text.find('\n',At),Quote=Text.find('"',At);
        if(Quote!=std::string::npos && (End==std::string::npos || Quote<End))
            Text.erase(Quote,(End==std::string::npos?Text.size():End)-Quote);
    }
    std::string Result=Rp9ShaderCache::Key(Text,Job.Entry,Job.Profile,Flags);
    if(Result.empty())throw std::runtime_error("empty compiler identity");
    Memo.emplace(Request,Result);return Result;
}
static std::string Read(const std::string& Path) {
    std::ifstream F(Path,std::ios::binary);return std::string(std::istreambuf_iterator<char>(F),{});
}
int main(int argc,char** argv) {
    if(argc!=3)return 2;
    try {
        const std::string Directory=argv[1],Surface=Read(Directory+"surface_material.hlsl");
        std::vector<Stage> Stages;std::ifstream Input(argv[2]);std::string Line;
        while(std::getline(Input,Line)) {
            std::stringstream S(Line);Stage Stage;std::string Flag;
            std::getline(S,Stage.file,'\t');std::getline(S,Stage.entry,'\t');std::getline(S,Stage.profile,'\t');
            std::getline(S,Flag);Stage.include=Flag=="1";Stages.push_back(Stage);
        }
        for(int R=0;R<=3;++R)for(int H=0;H<=3;++H)for(int Room=0;Room<=3;++Room) {
            std::vector<Rp9Startup::FJob> Jobs;std::string Error;
            if(!Rp9Startup::Build(Directory,Jobs,Error,R,H,Room))throw std::runtime_error(Error);
            std::set<std::string> Keys;for(auto& J:Jobs)Keys.insert(Key(J,Directory));
            if(R==3&&H==3&&Room==3) {
                printf("manifest\t3\t3\t3\t%zu stages\n",Jobs.size());
                const Rp9Startup::FJob Builtins[]={
                    {Rp9Startup::SoftParticleShader,"VSMain","vs_3_0",false,"soft_particles"},
                    {Rp9Startup::SoftParticleShader,"PSMain","ps_3_0",false,"soft_particles"},
                    {Rp9Startup::WindowedGammaShader,"PSMain","ps_3_0",false,"windowed_gamma"},
                    {ColorGradeShader,"PSMain","ps_3_0",false,"color_grade"},
                    {Rp9Startup::DriverWarmupShader,"main","vs_3_0",false,"driver_warmup"},
                    {Rp9Startup::SupersampleShader,"main","ps_3_0",false,"supersample",D3DXSHADER_OPTIMIZATION_LEVEL3}};
                for(auto& J:Builtins)if(!Keys.count(Key(J,Directory)))throw std::runtime_error("missing built-in stage");
                std::string Smaa="float4 PixelSize : register(c0);\n#define SMAA_RT_METRICS PixelSize\n"
                    "#define SMAA_HLSL_3 1\n#define SMAA_PRESET_HIGH 1\n"+Read(Directory+"SMAA/SMAA.hlsl")+"\n"+Read(Directory+"scene_smaa.hlsl");
                for(const char* Entry:{"EdgesPS","WeightsPS","BlendPS"}) {
                    Rp9Startup::FJob J{Smaa,Entry,"ps_3_0",false,"scene_smaa.hlsl"};
                    if(!Keys.count(Key(J,Directory)))throw std::runtime_error("missing SMAA stage");
                }
                printf("covered_builtins_and_smaa\t9\n");
                for(auto& S:Stages) {
                    auto Body=Read(Directory+S.file);
                    if(Body.empty()) {printf("missing_file\t3\t3\t3\t%s:%s\n",S.file.c_str(),S.entry.c_str());continue;}
                    auto Text=S.include?"#line 1 \"SHADERS/"+S.file+"\"\n"+Body:Body;
                    Rp9Startup::FJob J{Text,S.entry.c_str(),S.profile.c_str(),S.include,S.file};
                    if(!Keys.count(Key(J,Directory)))printf("missing_stage\t3\t3\t3\t%s:%s\n",S.file.c_str(),S.entry.c_str());
                }
            }
            // Reachable surface compile predicates from ExSurfaceBeginImpl:
            // regular: full/no-shadow/low; greenhouse/ship/rock: full/no-shadow;
            // nomad: full/no-shadow; Dyson/Beast forcibly disable shadows.
            const char* Kinds[]={"standard","greenhouse","ship","rock","nomad","dyson","beast","dyson_depth"};
            const char* Prefix[]={"","#define SURFACE_GREENHOUSE 1\n","#define SURFACE_SHIP_NORMALS 1\n",
                "#define SURFACE_ROCK 1\n","#define SURFACE_NOMAD 1\n",
                "#define SURFACE_NOMAD 1\n#define SURFACE_NOMAD_LIGHT 1\n",
                "#define SURFACE_NOMAD 1\n#define SURFACE_BEAST 1\n",
                "#define SURFACE_NOMAD 1\n#define SURFACE_NOMAD_LIGHT 1\n"};
            for(unsigned K=0;K<8;++K)for(unsigned V=0;V<(K==0?3u:2u);++V)for(unsigned Cube=0;Cube<2;++Cube) {
                if(K>=5 && V==0)continue;
                for(unsigned IsRoom=0;IsRoom<2;++IsRoom) {
                    if(IsRoom && (!Room || K==2 || K==3 || V==0 || K==7))continue;
                    const int Relief=IsRoom?Room:R,Highlight=IsRoom?Room:H;
                    std::string P=Rp9Startup::SurfaceQualityPrefix(Relief,Highlight)+Prefix[K]+(V==2?"#define SURFACE_LOW_DETAIL 1\n":V==1?"#define SURFACE_NO_SHADOW 1\n":"")+
                        (Cube?"#define SURFACE_ENV_CUBE 1\n":"");
                    Rp9Startup::FJob J{P+Surface,K==7?"PSNomadDepth":"PSMain","ps_3_0",false,"surface_material.hlsl"};
                    if(!Keys.count(Key(J,Directory)))printf("missing_variant\t%d\t%d\t%d\t%s,variant=%u,cube=%u,room=%u\n",R,H,Room,Kinds[K],V,Cube,IsRoom);
                }
            }
        }
        printf("preprocessed_unique\t%zu\n",Memo.size());
        return 0;
    } catch(const std::exception& E) {fprintf(stderr,"%s\n",E.what());return 1;}
}
