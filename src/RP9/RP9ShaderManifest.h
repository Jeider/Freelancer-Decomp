#pragma once
// One startup manifest for the game and the offline cache preparation tool.
#include "RP9ShaderCache.h"
#include "RP9BuiltinShaders.h"
#include "ColorGradeShader.h"
#include "RP9UserGraphics.h"
#include <set>
#include <cstdio>
namespace Rp9Startup {
inline std::string SurfaceQualityPrefix(int relief,int highlights) {
    // The full-quality source already defaults to 3/3. Keep its existing cache key.
    if(relief==3 && highlights==3) return {};
    return "#define SURFACE_RELIEF_QUALITY "+std::to_string(relief)+
        "\n#define SURFACE_HIGHLIGHT_QUALITY "+std::to_string(highlights)+"\n";
}
struct FJob {
    std::string Text; const char* Entry; const char* Profile;
    bool UseInclude=false; std::string Name; DWORD Flags=0;
};
    class DirectoryInclude final : public ID3DXInclude
    {
    public:
        explicit DirectoryInclude(const std::string& InDirectory) : Directory(InDirectory) {}
        STDMETHOD(Open)(D3DXINCLUDE_TYPE, LPCSTR FileName, LPCVOID, LPCVOID* OutData, UINT* OutBytes) override
        {
            std::string Text;
            FILE* File = fopen((Directory + FileName).c_str(), "rb");
            if (!File) return E_FAIL;
            char Buffer[4096]; size_t N;
            while ((N = fread(Buffer, 1, sizeof(Buffer), File)) != 0) Text.append(Buffer, N);
            fclose(File);
            char* Copy = new char[Text.size() + 1];
            if (!Text.empty()) memcpy(Copy, Text.data(), Text.size());
            Copy[Text.size()] = '\0';
            *OutData = Copy;
            *OutBytes = (UINT)Text.size();
            return S_OK;
        }
        STDMETHOD(Close)(LPCVOID Data) override { delete[] (const char*)(Data); return S_OK; }
    private:
        std::string Directory;
    };


inline bool Build(const std::string& Directory, std::vector<FJob>& Out, std::string& Error,
    int relief=(int)Rp9UserGraphics("space_relief_quality",3),
    int highlights=(int)Rp9UserGraphics("space_highlight_quality",3),
    int room=(int)Rp9UserGraphics("room_quality",3)) {
    auto ReadShader = [&](const std::string& Name) {
        std::string Text;
        FILE* File=fopen((Directory+Name).c_str(),"rb");
        if(File) {
            char Bytes[4096];size_t N;
            while((N=fread(Bytes,1,sizeof(Bytes),File))) Text.append(Bytes,N);
            if(ferror(File)) Text.clear();
            fclose(File);
        }
        if(Text.empty()) Error="Cannot read required shader: "+Directory+Name;
        return Text;
    };
    const std::string Source=ReadShader("surface_material.hlsl");
    if(Source.empty()) return false;
    std::vector<FJob> Jobs = {
        {Source, "VSMain", "vs_3_0"},
        {"#define SURFACE_INSTANCED 1\n" + Source, "VSMain", "vs_3_0"}};
    const char* Variants[3] = {"", "#define SURFACE_NO_SHADOW 1\n", "#define SURFACE_LOW_DETAIL 1\n"};
    for (const char* Variant : Variants)
        for (const char* Cube : {"", "#define SURFACE_ENV_CUBE 1\n"})
            Jobs.push_back({std::string(Variant) + Cube + Source, "PSMain", "ps_3_0"});
    if(Source.find("SURFACE_GREENHOUSE")!=std::string::npos)
        for(const char* Variant : {"", "#define SURFACE_NO_SHADOW 1\n"})
            for(const char* Cube : {"", "#define SURFACE_ENV_CUBE 1\n"})
                Jobs.push_back({std::string("#define SURFACE_GREENHOUSE 1\n")+Variant+Cube+Source,"PSMain","ps_3_0"});
    Jobs.push_back({std::string("#define SURFACE_NOMAD 1\n")+Source,"VSMain","vs_3_0"});
    Jobs.push_back({std::string("#define SURFACE_NOMAD 1\n#define SURFACE_NOMAD_LIGHT 1\n#define SURFACE_NO_SHADOW 1\n")+Source,"PSNomadDepth","ps_3_0"});
    for(const char* Detail:{"", "#define SURFACE_NOMAD_LIGHT 1\n", "#define SURFACE_BEAST 1\n"})
        for(const char* Shadow:{"", "#define SURFACE_NO_SHADOW 1\n"})
            Jobs.push_back({std::string("#define SURFACE_NOMAD 1\n")+Detail+Shadow+Source,"PSMain","ps_3_0"});
    for(const char* Shadow:{"", "#define SURFACE_NO_SHADOW 1\n"})
        for(const char* Cube:{"", "#define SURFACE_ENV_CUBE 1\n"})
            Jobs.push_back({std::string("#define SURFACE_SHIP_NORMALS 1\n")+Shadow+Cube+Source,"PSMain","ps_3_0"});
    // Asteroid / debris relief (IRPRockNormals): same variants as the ship normals.
    if(Source.find("SURFACE_ROCK")!=std::string::npos)
        for(const char* Shadow:{"", "#define SURFACE_NO_SHADOW 1\n"})
            for(const char* Cube:{"", "#define SURFACE_ENV_CUBE 1\n"})
                Jobs.push_back({std::string("#define SURFACE_ROCK 1\n")+Shadow+Cube+Source,"PSMain","ps_3_0"});



    // Everything else that compiles lazily, so it never stalls a frame: the other RP9 shaders (read
    // whole, as ExCompileShaderPair / the shadow, FXAA, SMAA and contact sites do) and the client's
    // programs (CreateExProgram: a #line header, #include resolved in the shader folder). The keys
    // are the expanded source, entry and profile, so a hit needs the text to match exactly.
    std::vector<FJob> Selected;
    for(auto& Job:Jobs) {
        Job.Name="surface_material.hlsl";
        if(std::strcmp(Job.Profile,"ps_3_0")) {Selected.push_back(Job);continue;}
        FJob Space=Job;Space.Text=SurfaceQualityPrefix(relief,highlights)+Job.Text;
        Selected.push_back(std::move(Space));
        if(room>0 && (room!=relief || room!=highlights)) {
            FJob Interior=Job;Interior.Text=SurfaceQualityPrefix(room,room)+Job.Text;
            Selected.push_back(std::move(Interior));
        }
    }
    Jobs=std::move(Selected);
    struct FPair { const char* File; const char* Vs; const char* Ps; };
    static const FPair Whole[] = {
        {"nomad_energy.hlsl","VSMain","PSMain"},
        {"beam_volume.hlsl","VSMain","PSMain"},
        {"code_beam.hlsl","VSMain","PSMain"}, {"planet_atmosphere.hlsl","VSMain","PSMain"},
        {"planet_surface.hlsl","VSMain","PSMain"}, {"planet_ring.hlsl","VSMain","PSMain"},
        {"room_material.hlsl","VSMain","PSMain"}, {"room_material.hlsl","VSSkin","PSMain"},
        {"room_shadow.hlsl","VSMain","PSMain"}, {"room_shadow.hlsl","VSSkin","ApplyPS"},
        {"local_shadow.hlsl","VSMain","PSMain"}, {"scene_fxaa.hlsl",nullptr,"PSMain"},
        {"room_contact.hlsl",nullptr,"PSMain"}};
    for (const FPair& Pair : Whole)
    {
        const std::string Text = ReadShader(Pair.File);
        if (Text.empty()) return false;
        if (Pair.Vs) Jobs.push_back({Text, Pair.Vs, "vs_3_0", false, Pair.File});
        if (Pair.Ps) Jobs.push_back({Text, Pair.Ps, "ps_3_0", false, Pair.File});
    }
    {
        const std::string Library = ReadShader("SMAA/SMAA.hlsl"), Entry = ReadShader("scene_smaa.hlsl");
        if (Library.empty() || Entry.empty()) return false;
        if (!Library.empty() && !Entry.empty())
        {
            const std::string Smaa = "float4 PixelSize : register(c0);\n#define SMAA_RT_METRICS PixelSize\n"
                "#define SMAA_HLSL_3 1\n#define SMAA_PRESET_HIGH 1\n" + Library + "\n" + Entry;
            for (const char* Name : {"EdgesPS", "WeightsPS", "BlendPS"})
                Jobs.push_back({Smaa, Name, "ps_3_0", false, "scene_smaa.hlsl"});
        }
    }
    static const FPair Programs[] = {
        {"black_hole.hlsl","VSMain","PSMain"}, {"black_hole.hlsl","VSMain","PSComposite"},
        {"cloak_refraction.hlsl","VSMain","PSMain"}, {"hud_tilt.hlsl","VSMain","PSMain"},
        {"debug_depth.hlsl","VSMain","PSMain"}, {"ship_warp.hlsl","VSMain","PSMain"},
        {"nebula_edge_fibre.hlsl","VSMain","PSRaymarch"}, {"nebula_alien.hlsl","VSMain","PSRaymarch"},
        {"engine_heat.hlsl","VSMain","PSMain"}, {"far_rocks.hlsl","VSMain","PSMain"},
        {"far_rocks.hlsl","VSMesh","PSMesh"}, {"field_dust.hlsl","VSMain","PSMarch"},
        {"field_dust.hlsl","VSMain","PSComposite"}, {"hyperspace_refraction.hlsl","VSMain","PSMain"},
        {"hyperspace_tunnel.hlsl","VSMain","PSMain"}, {"hyperspace_tunnel.hlsl","VSLaunch","PSLaunch"},
        {"jumpgate_aperture.hlsl","VSMain","PSMain"}, {"jumpgate_aperture.hlsl","VSMain","PSLens"},
        {"jumpgate_aperture.hlsl","VSInflow","PSInflow"}, {"jumpgate_aperture.hlsl","VSMain","PSDonuts"},
        {"jumphole_lens.hlsl","VSMain","PSLens"}, {"jumphole_lens.hlsl","VSMain","PSGlow"},
        {"jumphole_lens.hlsl","VSIngress","PSIngress"}, {"jumphole_optics.hlsl","VSOpticsWorld","PSOpticsWorld"},
        {"jumphole_optics.hlsl","VSOpticsScreen","PSOpticsShip"}, {"nebula_volume.hlsl","VSMain","PSRaymarch"},
        {"nebula_composite.hlsl","VSMain","PSComposite"}, {"nebula_ice.hlsl","VSMain","PSRaymarch"},
        {"nebula_walker_ice.hlsl","VSMain","PSRaymarch"}, {"solar_rays.hlsl","VSMain","PSMain"},
        {"solar_corona.hlsl","VSMain","PSMain"}, {"ship_warp.hlsl","VSMain","PSWarp"},
        {"space_haze.hlsl","VSMain","PSMain"}, {"tradelane_corridor.hlsl","VSMain","PSMain"},
        {"tradelane_corridor.hlsl","VSMain","PSWarp"}};
    for (const FPair& Pair : Programs)
    {
        const std::string Body = ReadShader(Pair.File);
        if (Body.empty()) return false;
        const std::string Text = std::string("#line 1 \"SHADERS/") + Pair.File + "\"\n" + Body;
        Jobs.push_back({Text, Pair.Vs, "vs_3_0", true, Pair.File});
        Jobs.push_back({Text, Pair.Ps, "ps_3_0", true, Pair.File});
    }

    Jobs.push_back({SoftParticleShader,"VSMain","vs_3_0",false,"soft_particles"});
    Jobs.push_back({SoftParticleShader,"PSMain","ps_3_0",false,"soft_particles"});
    Jobs.push_back({WindowedGammaShader,"PSMain","ps_3_0",false,"windowed_gamma"});
    Jobs.push_back({ColorGradeShader,"PSMain","ps_3_0",false,"color_grade"});
    Jobs.push_back({DriverWarmupShader,"main","vs_3_0",false,"driver_warmup"});
    Jobs.push_back({SupersampleShader,"main","ps_3_0",false,"supersample",D3DXSHADER_OPTIMIZATION_LEVEL3});
    std::set<std::string> Seen;
    for(auto& Job:Jobs)
        if(Seen.insert(Job.Text+'\0'+Job.Entry+'\0'+Job.Profile+'\0'+std::to_string(Job.Flags)).second) Out.push_back(std::move(Job));
    return !Out.empty();
}
inline HRESULT Compile(const FJob& Job, const std::string& Directory,
    std::vector<unsigned char>& Code, std::string& Messages, bool& Hit) {
    DirectoryInclude Include(Directory);bool Stored=false;
    return Rp9ShaderCache::Compile(Job.Text,Job.UseInclude?&Include:nullptr,Job.Entry,Job.Profile,
        Rp9ShaderCache::FlagsForSource(Job.Text)|Job.Flags,&Code,&Messages,&Hit,&Stored,true);
}
}
