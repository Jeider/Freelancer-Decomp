// Included by RP9Ex.cpp: shares the compiler/cache and legacy state helpers.
#include "RP9FullHairMaterials.h"

static std::string RoomDataPath(const char* Relative)
{
    char Module[MAX_PATH] = {}; GetModuleFileNameA(nullptr, Module, MAX_PATH);
    char* Slash = strrchr(Module, '\\'); if (!Slash) return {};
    Slash[1] = 0; return std::string(Module) + "../DATA_EXTRA/ROOM_MATERIALS/" + Relative;
}

struct RoomFinishRule
{
    std::string Section;
    bool Prefix = false;
    bool Global = false;
    std::string Pattern;
    float Kind = 0;
};

static std::vector<RoomFinishRule> GRoomFinishRules;
static std::map<std::string, FRp9ExState::RoomProfile*> GRoomByTexture;
static bool GRoomFinishLoaded = false;

static float RoomFinishKind(char const* Text)
{
    if (Text == nullptr)
        return 0;
    if (_stricmp(Text, "marble") == 0 || _stricmp(Text, "granite") == 0 || _stricmp(Text, "stone") == 0)
        return 1;
    if (_stricmp(Text, "glass") == 0 || _stricmp(Text, "bottle") == 0)
        return 2;
    if (_stricmp(Text, "weapon") == 0 || _stricmp(Text, "gun") == 0 || _stricmp(Text, "rifle") == 0 ||
        _stricmp(Text, "metal") == 0)
        return 3;
    if (_stricmp(Text, "wood") == 0)
        return 4;
    return 0;
}

static void RoomFinishTrim(char* Text)
{
    char* Start = Text;
    while (*Start == ' ' || *Start == '\t')
        ++Start;
    if (Start != Text)
        memmove(Text, Start, strlen(Start) + 1);
    size_t Length = strlen(Text);
    while (Length > 0 && (Text[Length - 1] == ' ' || Text[Length - 1] == '\t' ||
                          Text[Length - 1] == '\r' || Text[Length - 1] == '\n'))
        Text[--Length] = 0;
}

static void RoomFinishLoad()
{
    if (GRoomFinishLoaded)
        return;
    GRoomFinishLoaded = true;
    FILE* File = fopen(RoomDataPath("finishes.ini").c_str(), "rb");
    if (File == nullptr)
        return;
    char Line[512];
    std::string Section = "*";
    bool Prefix = false;
    while (fgets(Line, sizeof(Line), File))
    {
        RoomFinishTrim(Line);
        if (Line[0] == 0 || Line[0] == ';' || Line[0] == '#')
            continue;
        if (Line[0] == '[')
        {
            char* End = strchr(Line, ']');
            if (End == nullptr)
                continue;
            *End = 0;
            RoomFinishTrim(Line + 1);
            Section = LowerString(Line + 1);
            Prefix = !Section.empty() && Section.back() == '*';
            if (Prefix)
                Section.pop_back();
            if (Section.empty())
                Section = "*";
            continue;
        }
        char* Eq = strchr(Line, '=');
        if (Eq == nullptr)
            continue;
        *Eq = 0;
        RoomFinishTrim(Line);
        RoomFinishTrim(Eq + 1);
        float Kind = RoomFinishKind(Eq + 1);
        if (Line[0] == 0 || Kind == 0)
            continue;
        RoomFinishRule Rule;
        Rule.Section = Section;
        Rule.Prefix = Prefix;
        Rule.Global = Section == "props";
        Rule.Pattern = LowerString(Line);
        Rule.Kind = Kind;
        GRoomFinishRules.push_back(Rule);
    }
    fclose(File);
}

static float RoomFinishMatch(std::string const& Base, std::string const& Key)
{
    float Kind = 0;
    int Score = -1;
    for (size_t I = 0; I < GRoomFinishRules.size(); ++I)
    {
        RoomFinishRule const& Rule = GRoomFinishRules[I];
        bool SectionOk = Rule.Global || Rule.Section == "*" || Rule.Section == Base ||
                         (Rule.Prefix && Base.compare(0, Rule.Section.size(), Rule.Section) == 0);
        if (!SectionOk || Rule.Pattern.empty() || Key.find(Rule.Pattern) == std::string::npos)
            continue;
        int Next = static_cast<int>(Rule.Pattern.size());
        if (Rule.Global)
            Next += 3000;
        else if (Rule.Section != "*")
            Next += Rule.Prefix ? 1000 : 2000;
        if (Next >= Score)
        {
            Score = Next;
            Kind = Rule.Kind;
        }
    }
    return Kind;
}

GENRESULT DACOM_API FDirectX9::SetRoomProp(unsigned long Prop)
{
    auto* E = Ex_;
    if (!E)
        return GR_GENERIC;
    E->bRoomProp = Prop != 0;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetRoomBase(char const* Nickname)
{
    auto* E = Ex_;
    if (!E)
        return GR_GENERIC;
    std::string Raw = Nickname != nullptr ? LowerString(Nickname) : std::string();
    std::string RoomFile;
    size_t Sep = Raw.find('|');
    if (Sep != std::string::npos)
    {
        RoomFile = Raw.substr(Sep + 1);
        Raw.resize(Sep);
    }
    E->RoomBase = Raw;
    // Every visitable base room. PetalDB marks those meshes as room, not prop.
    E->bRoomPolish = !Raw.empty();
    E->bRoomBar = false;
    E->bRoomBrick = false;
    if (!RoomFile.empty())
    {
        size_t Slash = RoomFile.find_last_of("/\\");
        std::string Name = Slash == std::string::npos ? RoomFile : RoomFile.substr(Slash + 1);
        size_t Dot = Name.rfind('.');
        if (Dot != std::string::npos)
            Name.resize(Dot);
        E->bRoomBar = Name.size() >= 4 && Name.compare(Name.size() - 4, 4, "_bar") == 0;
        if (Name.find("havana") != std::string::npos || Name.find("bw_02_bar") != std::string::npos ||
            Name.find("co_cad_01_bar") != std::string::npos || Name.find("co_och_01_bar") != std::string::npos ||
            Name.find("ku06_01_bar") != std::string::npos)
            E->bRoomBrick = true;
        else
        {
            char Module[MAX_PATH] = {};
            GetModuleFileNameA(nullptr, Module, MAX_PATH);
            char* ModuleSlash = strrchr(Module, '\\');
            if (ModuleSlash)
            {
                ModuleSlash[1] = 0;
                std::string Path = std::string(Module) + "..\\DATA\\" + RoomFile;
                for (char& Ch : Path)
                    if (Ch == '/')
                        Ch = '\\';
                FILE* File = fopen(Path.c_str(), "rb");
                if (File)
                {
                    char Buf[4096];
                    size_t N = fread(Buf, 1, sizeof(Buf) - 1, File);
                    fclose(File);
                    Buf[N] = 0;
                    for (size_t I = 0; I < N; ++I)
                        Buf[I] = (char)tolower((unsigned char)Buf[I]);
                    E->bRoomBrick = strstr(Buf, "bw_02_bar") != nullptr || strstr(Buf, "hi_havana") != nullptr;
                }
            }
        }
    }
    {
        char LogPath[MAX_PATH] = {};
        if (GetEnvironmentVariableA("LOCALAPPDATA", LogPath, MAX_PATH))
        {
            strcat(LogPath, "\\Freelancer-Decomp\\Diagnostics\\room_bar.txt");
            if (FILE* Log = fopen(LogPath, "wb"))
            {
                fprintf(Log, "base=%s brick=%d file=%s\n", E->RoomBase.c_str(), (int)E->bRoomBrick, RoomFile.c_str());
                fclose(Log);
            }
        }
    }
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetRoomMaterialFrame(unsigned long Enabled)
{
    auto* E = Ex_; if (!E) return GR_GENERIC;
    ExFlushSurfaceInstances(); ExSurfaceEnd(); ExSurfaceRelease();
    E->RoomCurrent = nullptr; E->bRoomFrame = Enabled != 0; if (!Enabled) E->bRoomProp = false;
    if (!Enabled && Device_) Rp9SetTexture(Device_,14,nullptr);
    if (Enabled && !E->bRoomRead)
    {
        E->bRoomRead = true;
        E->bRoomEnabled = ReadShadowSetting("room_materials", 1, 0, 1) > .5f;
        if (!E->bRoomEnabled) return GR_OK;
        FILE* File = fopen(RoomDataPath("profiles.txt").c_str(), "rb");
        if (File)
        {
            char Line[2048], Map[65], Key[1536];
            while (fgets(Line, sizeof(Line), File))
            {
                FRp9ExState::RoomProfile P;
                if (sscanf(Line, "%f %f %f %f %64s %1535[^\r\n]", &P.Normal, &P.Roughness,
                           &P.Specular, &P.Skin, Map, Key) != 6) continue;
                // Only generated hexadecimal filenames; no paths from a profile.
                if (strlen(Map) != 36 || strspn(Map, "0123456789abcdef") != 32 || strcmp(Map+32,".dds")) continue;
                if (!std::isfinite(P.Normal) || !std::isfinite(P.Roughness) || !std::isfinite(P.Specular) || !std::isfinite(P.Skin) ||
                    P.Normal < 0 || P.Normal > 1 || P.Roughness < .16f || P.Roughness > 1 ||
                    P.Specular < 0 || P.Specular > 2 || P.Skin < -1 || P.Skin > 1) continue;
                P.Normal=Rp9UserGraphics("room_normal_strength",P.Normal);
                P.Specular=Rp9UserGraphics("room_specular_strength",P.Specular);
                P.Map = Map; E->RoomProfiles[LowerString(Key)] = P;
            }
            fclose(File);
        }
        GRoomByTexture.clear();
        for (auto& Item : E->RoomProfiles)
        {
            size_t Bar = Item.first.rfind('|');
            if (Bar != std::string::npos)
            {
                GRoomByTexture[Item.first.substr(0, Bar)] = &Item.second;
                GRoomByTexture[Item.first.substr(Bar + 1)] = &Item.second;
            }
        }
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "room materials: %u profiles, %s; authored room lights and UVs retained",
            (unsigned)E->RoomProfiles.size(), E->bRoomEnabled ? "enabled" : "disabled");
        RoomFinishLoad();
        E->bRoomFinishLog = ReadShadowSetting("room_finish_log", 0, 0, 1) > .5f;
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "room finishes: %u rules",
            (unsigned)GRoomFinishRules.size());
    }
    if (Enabled)
    {
        E->bRoomPaletteUnsupported = false;
        ++E->RoomFrame;
        if ((E->RoomFrame % 120) == 0)
            for (auto& Item : E->RoomProfiles)
                if (Item.second.Texture && E->RoomFrame - Item.second.LastFrame > 120)
                { Item.second.Texture->Release(); Item.second.Texture = nullptr; Item.second.Tried = false; }
    }
    return GR_OK;
}

static float RoomDetailKind(std::string const& Detail)
{
    if (Detail.find("wood") != std::string::npos) return 4;
    if (Detail.find("marble") != std::string::npos || Detail.find("granite") != std::string::npos ||
        Detail.find("stone") != std::string::npos) return 1;
    if (Detail.find("metal") != std::string::npos) return 3;
    if (Detail.find("glass") != std::string::npos) return 2;
    return 0;
}

GENRESULT DACOM_API FDirectX9::SetRoomDetail(const char* Detail)
{
    auto* E = Ex_; if (!E) return GR_GENERIC;
    E->RoomDetail = Detail ? LowerString(Detail) : std::string();
    float Kind = RoomDetailKind(E->RoomDetail);
    if (Kind != 0)
    {
        E->RoomFinish = Kind;
        if (!E->RoomCurrent && E->bRoomFrame && E->bRoomEnabled)
        {
            E->PropFallback.Normal = 0;
            E->PropFallback.Roughness = 0.16f;
            E->PropFallback.Specular = 1.6f;
            E->PropFallback.Skin = 0;
            E->PropFallback.Tried = true;
            E->RoomCurrent = &E->PropFallback;
        }
    }
    return GR_OK;
}

// Authored Bretonian bar atlases, inspected in the CMP texture libraries.
// 0 = native/general room finish, 1 = restrained relief, 2 = masonry relief.
// Exact atlas stems retain exporter suffixes; unrelated rooms with generic names
// are not selected. Barbican is deliberately excluded.
static int BretonBarRelief(const char* Texture)
{
    if (!Texture) return 0;
    const std::string T=LowerString(Texture);
    auto Match=[&](const char* Stem,const char* Stamp) {
        return T.find(std::string(Stem)+".tga"+Stamp)==0;
    };
    for (const char* S : {"main_floor-1","main_floor-2","main_floor-3","main_floor-4",
                         "floor_rest","wall-1","wall-2","wall-3","wall-4","arcs+ccol"})
        if(Match(S,"021211150031")) return 2;
    for (const char* S : {"bar_stojka-1","barrels","chairs-1","column_mask","column_mask-1",
                         "quad-table-1","f_place-1","f_place-2","f_place-3","br_bar_equip"})
        if(Match(S,"021211150031")) return 1;
    for (const char* S : {"03","04","05","06","10","11","12","13","14"})
        if(Match((std::string("bret_bar#2_")+S).c_str(),"030103145139")) return 2;
    for (const char* S : {"01","02","08","09","15","16","18","19","20","21","22","24"})
        if(Match((std::string("bret_bar#2_")+S).c_str(),"030103145139")) return 1;
    for (const char* S : {"02","10","19","20","21","22","23","28","29","30"})
        if(Match((std::string("bret_bar#3-")+S).c_str(),"021124165307")) return 2;
    for (const char* S : {"03","04","05","06","08","11","12","13","14","15","16","24","25","26","27"})
        if(Match((std::string("bret_bar#3-")+S).c_str(),"021124165307")) return 1;
    for (const char* S : {"1","2","3","4","5","6","7","10","11"})
        if(Match((std::string("bsbar-")+S).c_str(),"021219125156")) return 2;
    for (const char* S : {"8","9","12","14","15","16","17","18","19","20"})
        if(Match((std::string("bsbar-")+S).c_str(),"021219125156")) return 1;
    return 0;
}

GENRESULT DACOM_API FDirectX9::SetRoomMaterial(const char* Name, const char* Texture)
{
    auto* E = Ex_; if (!E) return GR_GENERIC;
    E->RoomCurrent = nullptr;
    E->ShipNormalCurrent = nullptr;
    E->RoomDetail.clear();
    E->bRoomBrickDraw = false;
    E->bRoomMasonry = false;
    E->bRoomBretonRelief = false;
    if (E->bShipNormalScope && !E->bRoomFrame && Name)
    {
        auto& Profiles=E->bSolarNormalScope ? E->SolarNormalProfiles : E->ShipNormalProfiles;
        auto Found=Profiles.find(LowerString(std::string(Name)+"|"+(Texture?Texture:"")));
        if(Found!=Profiles.end()) E->ShipNormalCurrent=Found->second;
    }
    if (!E->bRoomFrame || !E->bRoomEnabled || !Name) return GR_OK;
    // Exact authored hair-only groups; never activate on a shared face atlas.
    if (Texture && (_strnicmp(Name,"short_hair_",11)==0 ||
                    _strnicmp(Name,"hero_hair_",10)==0 ||
                    _stricmp(Name,"hatcher_hair_v1")==0 ||
                    _stricmp(Name,"hatcher_hat_hair")==0))
    for (auto const& Entry : kFullHairMaterials)
    {
        if (_stricmp(Name,Entry.Name)!=0 || _stricmp(Texture,Entry.Texture)!=0) continue;
        const float Quality=Rp9UserGraphics("character_hair",3);
        if(Quality<.5f)return GR_OK;
        auto& Hair=E->RoomProfiles[LowerString(std::string(Name)+"|"+Texture)];
        if (Hair.Map.empty()) { Hair.Map=Entry.Map; Hair.Tried=false; }
        Hair.Normal=(.36f+.14f*Quality)*1.08f;
        Hair.Roughness=.50f;
        Hair.Specular=.28f+.07f*Quality;
        Hair.Skin=.25f;
        E->RoomCurrent=&Hair; E->RoomFinish=5.4f;
        return GR_OK;
    }
    auto FacePart = [](const char* S) {
        if (!S || !S[0]) return false;
        std::string L = LowerString(S);
        return L.find("_head") != std::string::npos || L.find("head0") != std::string::npos ||
               L.find("eyelid") != std::string::npos || L.find("eye") != std::string::npos ||
               L.find("beard") != std::string::npos || L.find("teeth") != std::string::npos ||
               L.find("hair") != std::string::npos || L.find("moust") != std::string::npos;
    };
    if (FacePart(Name) || FacePart(Texture))
        return GR_OK;
    std::string Key = LowerString(std::string(Name) + "|" + (Texture ? Texture : ""));
    E->RoomFinish = RoomFinishMatch(E->RoomBase, Key);
    if (E->bRoomFinishLog && E->RoomFinishLogged.insert(Key).second)
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "room finish: %s base %s -> %.0f",
            Key.c_str(), E->RoomBase.c_str(), E->RoomFinish);
    auto Found = E->RoomProfiles.find(Key);
    if (Found != E->RoomProfiles.end())
        E->RoomCurrent = &Found->second;
    auto BrickText = [](const char* S) {
        if (!S || !S[0]) return false;
        std::string L = LowerString(S);
        return L.find("hispahic") != std::string::npos || L.find("ispahic") != std::string::npos;
    };
    const int BretonRelief=BretonBarRelief(Texture);
    E->bRoomBretonRelief=BretonRelief!=0;
    const bool BrickNamed = BrickText(Name) || BrickText(Texture) || BretonRelief!=0;
    if (BrickNamed)
        E->bRoomBrick = true;
    if (!E->RoomCurrent && (E->bRoomBrick || BrickNamed))
    {
        for (const char* S : {Texture, Name})
        {
            if (!S || !S[0]) continue;
            std::string Tex = LowerString(S);
            auto Tga = Tex.find(".tga");
            if (Tga != std::string::npos)
                Tex.resize(Tga + 4);
            auto ByTex = GRoomByTexture.find(Tex);
            if (ByTex != GRoomByTexture.end() && ByTex->second->Skin < -.5f)
            {
                E->RoomCurrent = ByTex->second;
                break;
            }
        }
    }
    if (!E->RoomCurrent && E->RoomFinish != 0 && !BrickNamed)
    {
        E->PropFallback.Normal = 0;
        E->PropFallback.Roughness = 0.16f;
        E->PropFallback.Specular = 1.6f;
        E->PropFallback.Skin = 0;
        E->PropFallback.Tried = true;
        E->RoomCurrent = &E->PropFallback;
    }
    if (BrickNamed && !E->bRoomProp && (!E->RoomCurrent || E->RoomCurrent->Skin >= -.5f))
    {
        E->PropFallback.Normal = 1.f;
        E->PropFallback.Roughness = 0.45f;
        E->PropFallback.Specular = 0.35f;
        E->PropFallback.Skin = -1.f;
        E->PropFallback.Map.clear();
        E->PropFallback.Tried = true;
        E->PropFallback.Texture = nullptr;
        E->RoomCurrent = &E->PropFallback;
    }
    // Select per material, not per base: Havana/Cadiz rooms share these authored
    // wall and wood textures. Actors and unrelated props must retain their route.
    E->bRoomBrickDraw = BrickNamed && !E->bRoomProp && E->RoomCurrent &&
                        E->RoomCurrent->Skin < -.5f;
    // Full relief across the Havana family, including mixed masonry atlases.
    // Only predominantly wooden panels/furniture retain the quarter treatment.
    if (E->bRoomBrickDraw && Texture) {
        E->bRoomMasonry=true;
        const std::string Tex=LowerString(Texture);
        for (const char* S : {"08","15","16","17","22","24","26"})
            if (Tex==std::string("hispahic_m_")+S+".tga" || Tex==std::string("ispahic_m_")+S+".tga")
                E->bRoomMasonry=false;
        if(BretonRelief) E->bRoomMasonry=BretonRelief==2;
    }
    if (E->bRoomBrick) {
        static std::set<std::string> Seen;
        if (Seen.size()<128 && Seen.insert(Key).second)
            ExLogf(kExFdumpNotice,"NOTICE",__LINE__,
                "room relief selection: %s prop=%d selected=%d profile=%s",
                Key.c_str(),(int)E->bRoomProp,(int)E->bRoomBrickDraw,
                E->RoomCurrent ? E->RoomCurrent->Map.c_str() : "NONE");
    }
    return GR_OK;
}

void FDirectX9::ExRoomMaterialRelease()
{
    auto* E = Ex_; if (!E) return;
    for (auto& Item : E->RoomProfiles)
    {
        if (Item.second.Texture) Item.second.Texture->Release();
        Item.second.Texture = nullptr; Item.second.Tried = false;
    }
    if (E->RoomVs) E->RoomVs->Release(); E->RoomVs = nullptr;
    if (E->RoomSkinVs) E->RoomSkinVs->Release(); E->RoomSkinVs = nullptr;
    if (E->RoomPs) E->RoomPs->Release(); E->RoomPs = nullptr;
    if (E->RoomAoPs) E->RoomAoPs->Release(); E->RoomAoPs = nullptr;
    E->bRoomAoFailed = false;
    E->RoomCurrent = nullptr; E->bRoomFrame = E->bRoomFailed = false;
}

bool FDirectX9::ExRoomMaterialBegin()
{
    auto* E = Ex_;
    // Bounded diagnostics for the actual authored draw states, not just shader compilation.
    if (E && E->bRoomFrame && E->bRoomEnabled && E->bRoomFinishLog && E->bRoomBrick && Device_) {
        auto State=[&](unsigned S,unsigned T) {auto& V=DeviceStates_.TextureStates[S][T];return V.bValid?V.Value:~0u;};
        char Line[1024];
        sprintf_s(Line,"room relief draw: selected=%d prop=%d profile=%s enabled=%d failed=%d pass=%d shadow=%d active=%d material=%d fvf=%lx blend=%lu stages=%lu/%lu/%lu uv=%lu/%lu transform=%lu/%lu detail=%s",
            (int)E->bRoomBrickDraw,(int)E->bRoomProp,E->RoomCurrent?E->RoomCurrent->Map.c_str():"NONE",
            (int)E->bRoomEnabled,(int)E->bRoomFailed,(int)E->bInPass,(int)E->bShadowDrawing,(int)E->bSurfaceActive,(int)E->bSurfaceMaterialValid,
            (unsigned long)(StreamCache_.Fvf?StreamCache_.Fvf:StreamCache_.VertexBuffer?StreamCache_.VertexBuffer->Fvf:0),
            (unsigned long)RenderStates_.GetPending(D3DRS_ALPHABLENDENABLE),
            (unsigned long)State(0,D3DTSS_COLOROP),(unsigned long)State(1,D3DTSS_COLOROP),(unsigned long)State(2,D3DTSS_COLOROP),
            (unsigned long)State(0,D3DTSS_TEXCOORDINDEX),(unsigned long)State(1,D3DTSS_TEXCOORDINDEX),
            (unsigned long)State(0,D3DTSS_TEXTURETRANSFORMFLAGS),(unsigned long)State(1,D3DTSS_TEXTURETRANSFORMFLAGS),E->RoomDetail.c_str());
        static std::set<std::string> Seen;
        if(Seen.size()<128 && Seen.insert(Line).second) ExLog(kExFdumpNotice,"NOTICE",__LINE__,Line);
    }
    if (!E || !Device_ || !E->bRoomFrame || !E->bRoomEnabled || E->bRoomFailed ||
        E->bInPass || E->bShadowDrawing || E->bSurfaceActive) return false;
    if (!E->RoomCurrent || !E->bSurfaceMaterialValid) return false;
    // Restore native face shading, including its per-vertex lighting. Merely
    // zeroing the generated normal would retain the new per-pixel facial shading.
    if (E->RoomCurrent->Skin > .5f) return false;
    const bool Hair=E->RoomFinish>=5.f && E->RoomFinish<5.5f && E->RoomCurrent->Skin==.25f;
    if (!Hair && E->bRoomBrick && E->RoomCurrent->Skin >= -.5f) return false;
    const unsigned Fvf = StreamCache_.Fvf ? StreamCache_.Fvf : StreamCache_.VertexBuffer ? StreamCache_.VertexBuffer->Fvf : 0;
    const unsigned Uvs = (Fvf & D3DFVF_TEXCOUNT_MASK) >> D3DFVF_TEXCOUNT_SHIFT;
    const bool Skin = (Fvf & D3DFVF_POSITION_MASK) == D3DFVF_XYZB4 && (Fvf & D3DFVF_LASTBETA_UBYTE4) &&
                     RenderStates_.GetPending(D3DRS_INDEXEDVERTEXBLENDENABLE) && RenderStates_.GetPending(D3DRS_VERTEXBLEND) == D3DVBF_3WEIGHTS;
    if (Skin && !Hair && (E->bRoomBrick || E->bRoomBrickDraw || E->RoomCurrent->Skin < -.5f)) return false;
    const unsigned FvfBody = Fvf;
    if ((!Skin && (FvfBody & D3DFVF_POSITION_MASK) != D3DFVF_XYZ) || !(FvfBody & D3DFVF_NORMAL) ||
        !Uvs || Uvs > 3 || (Fvf & 0xffff0000u) ||
        (RenderStates_.GetPending(D3DRS_ALPHABLENDENABLE) &&
        !(Hair || (E->RoomFinish > 1.5f && E->RoomFinish < 2.5f)))) return false;
    if (Skin && E->bRoomPaletteUnsupported) return false;
    // Never reinterpret authored reflection vectors or unusual multipass blends.
    auto Tss = [&](unsigned S, unsigned T, unsigned Default) {
        auto& V = DeviceStates_.TextureStates[S][T]; return V.bValid ? V.Value : Default;
    };
    unsigned Stages = 0;
    for (unsigned S = 0; S < 3; ++S)
    {
        unsigned Op = Tss(S, D3DTSS_COLOROP, S ? D3DTOP_DISABLE : D3DTOP_MODULATE);
        if (Op == D3DTOP_DISABLE) break;
        if (S == 2 || Op < 2 || Op > 16 || Tss(S,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1) > 16 ||
            Tss(S,D3DTSS_TEXCOORDINDEX,S) >= Uvs ||
            (Tss(S,D3DTSS_TEXTURETRANSFORMFLAGS,0) != 0 && Tss(S,D3DTSS_TEXTURETRANSFORMFLAGS,0) != D3DTTFF_COUNT2) ||
            Tss(S,D3DTSS_RESULTARG,D3DTA_CURRENT) != D3DTA_CURRENT) return false;
        for (unsigned A : {D3DTSS_COLORARG1, D3DTSS_COLORARG2, D3DTSS_ALPHAARG1, D3DTSS_ALPHAARG2})
            if ((Tss(S,A,A == D3DTSS_COLORARG1 || A == D3DTSS_ALPHAARG1 ? D3DTA_TEXTURE : D3DTA_CURRENT) & 15) > 3) return false;
        if (!DeviceStates_.TextureBindings[S].bValid) return false;
        auto* Tex = PipelineTextureFromHandle(DeviceStates_.TextureBindings[S].Handle);
        if (!Tex || Tex->GetType() != D3DRTYPE_TEXTURE) return false;
        ++Stages;
    }
    if (!Stages) return false;
    if (!E->RoomVs || !E->RoomPs)
        if (!ExCompileShaderPair("room_material.hlsl", &E->RoomVs, &E->RoomPs, "VSMain", "PSMain"))
        { E->bRoomFailed = true; return false; }
    if (Skin && !E->RoomSkinVs)
    {
        // Compile the same PS too through the shared helper, release the temporary reference.
        IDirect3DPixelShader9* Ps = nullptr;
        bool Ok = ExCompileShaderPair("room_material.hlsl", &E->RoomSkinVs, &Ps, "VSSkin", "PSMain");
        if (Ps) Ps->Release(); if (!Ok) return false;
    }
    auto& P = *E->RoomCurrent;
    P.LastFrame = E->RoomFrame;
    if (!P.Tried)
    {
        RuntimeHitchScope Hitch("room_texture", P.Map.c_str());
        P.Tried = true;
        D3DXCreateTextureFromFileExA(Device_, RoomDataPath(P.Map.c_str()).c_str(), D3DX_DEFAULT, D3DX_DEFAULT,
            D3DX_DEFAULT, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, D3DX_FILTER_NONE, D3DX_FILTER_NONE, 0, nullptr, nullptr, &P.Texture);
        if (!P.Texture) ExLogf(kExFdumpWarning,"WARNING",__LINE__,"room map unavailable: %s; native material retained",P.Map.c_str());
    }
    if (!P.Texture && !P.Map.empty() && !E->bRoomBrickDraw) return false;
    float Vs[22*4] = {};
    MulMatrix4(Transforms_.World.Values, Transforms_.View.Values, Vs);
    memcpy(Vs+16,Transforms_.Projection.Values,64);
    D3DXMATRIX M,Inv,N; memcpy(&M,Vs,64);
    if (!D3DXMatrixInverse(&Inv,nullptr,&M)) return false; D3DXMatrixTranspose(&N,&Inv); memcpy(Vs+32,&N,64);
    memcpy(Vs+48,DeviceStates_.TextureTransforms[0].Values,64);memcpy(Vs+64,DeviceStates_.TextureTransforms[1].Values,64);
    Vs[80]=(float)Tss(0,D3DTSS_TEXCOORDINDEX,0);Vs[81]=Stages>1 ? (float)Tss(1,D3DTSS_TEXCOORDINDEX,1) : 0;
    Vs[82]=(float)Tss(0,D3DTSS_TEXTURETRANSFORMFLAGS,0);Vs[83]=(float)Tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,0);
    Vs[84]=(Fvf&D3DFVF_DIFFUSE) ? 1.f : 0.f;Vs[85]=(Fvf&D3DFVF_SPECULAR) ? 1.f : 0.f;
    float Ps[55*4] = {};
    auto Set = [&](unsigned R,float X,float Y,float Z,float W){float* V=Ps+R*4;V[0]=X;V[1]=Y;V[2]=Z;V[3]=W;};
    auto Colour = [&](unsigned R,unsigned C){Set(R,((C>>16)&255)/255.f,((C>>8)&255)/255.f,(C&255)/255.f,((C>>24)&255)/255.f);};
    const auto& Mat=E->SurfaceMaterial;
    memcpy(Ps,&Mat.Diffuse,16);memcpy(Ps+4,&Mat.Ambient,16);memcpy(Ps+8,&Mat.Emissive,16);memcpy(Ps+12,&Mat.Specular,16);
    static const unsigned MaxLights=(unsigned)ReadShadowSetting("room_light_count",8,1,8);
    D3DLIGHT9 Lights[8];unsigned Count=ExCollectSurfaceLights(Lights,MaxLights);
    Set(4,(float)Count,RenderStates_.GetPending(D3DRS_LIGHTING) ? 1.f : 0.f,P.Texture ? 1.f : 0.f,(float)Stages);
    unsigned FogMode=RenderStates_.GetPending(D3DRS_FOGTABLEMODE);
    if (!FogMode) FogMode=RenderStates_.GetPending(D3DRS_FOGVERTEXMODE);
    if (!RenderStates_.GetPending(D3DRS_FOGENABLE)) FogMode=0;
    Set(5,FloatBits(RenderStates_.GetPending(D3DRS_FOGSTART)),FloatBits(RenderStates_.GetPending(D3DRS_FOGEND)),
        FloatBits(RenderStates_.GetPending(D3DRS_FOGDENSITY)),(float)FogMode);
    Colour(6,RenderStates_.GetPending(D3DRS_FOGCOLOR));Ps[27]=RenderStates_.GetPending(D3DRS_RANGEFOGENABLE) ? 1.f : 0.f;
    for (unsigned S=0;S<Stages;++S)
    {
        Set(7+S,(float)Tss(S,D3DTSS_COLOROP,D3DTOP_MODULATE),(float)Tss(S,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1),
            (float)Tss(S,D3DTSS_COLORARG1,D3DTA_TEXTURE),(float)Tss(S,D3DTSS_COLORARG2,D3DTA_CURRENT));
        Ps[36+S*2]=(float)Tss(S,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);Ps[37+S*2]=(float)Tss(S,D3DTSS_ALPHAARG2,D3DTA_CURRENT);
    }
    Colour(10,RenderStates_.GetPending(D3DRS_TEXTUREFACTOR));
    Set(11,Rp9UserGraphics("room_normal_strength",P.Normal),P.Roughness,
        Rp9UserGraphics("room_specular_strength",P.Specular),P.Skin);
    Colour(53,RenderStates_.GetPending(D3DRS_AMBIENT));
    memcpy(&M,Transforms_.View.Values,64);
    for (unsigned I=0;I<Count;++I)
    {
        auto& L=Lights[I];D3DXVECTOR3 Pos,Dir;
        D3DXVec3TransformCoord(&Pos,reinterpret_cast<const D3DXVECTOR3*>(&L.Position),&M);
        D3DXVec3TransformNormal(&Dir,reinterpret_cast<const D3DXVECTOR3*>(&L.Direction),&M);
        unsigned R=12+I*5;Set(R,Pos.x,Pos.y,Pos.z,(float)L.Type);Set(R+1,Dir.x,Dir.y,Dir.z,L.Range);
        Set(R+2,L.Diffuse.r,L.Diffuse.g,L.Diffuse.b,L.Falloff);
        bool S=L.Specular.r>0 || L.Specular.g>0 || L.Specular.b>0;
        Set(R+3,S?L.Specular.r:L.Diffuse.r,S?L.Specular.g:L.Diffuse.g,S?L.Specular.b:L.Diffuse.b,std::cos(L.Phi*.5f));
        Set(R+4,L.Attenuation0,L.Attenuation1,L.Attenuation2,std::cos(L.Theta*.5f));
        Ps[212]+=L.Ambient.r;Ps[213]+=L.Ambient.g;Ps[214]+=L.Ambient.b;
    }
    const bool ColourVertex=RenderStates_.GetPending(D3DRS_COLORVERTEX)!=0;
    auto Source=[&](unsigned State){unsigned S=RenderStates_.GetPending(State);return ColourVertex &&
        ((S==D3DMCS_COLOR1 && (Fvf&D3DFVF_DIFFUSE)) || (S==D3DMCS_COLOR2 && (Fvf&D3DFVF_SPECULAR))) ? (float)S : 0.f;};
    Set(52,Source(D3DRS_DIFFUSEMATERIALSOURCE),Source(D3DRS_AMBIENTMATERIALSOURCE),Source(D3DRS_EMISSIVEMATERIALSOURCE),E->bRoomBrickDraw ? (E->bRoomMasonry ? 4.f : 2.f)+(E->bRoomBretonRelief ? 4.f : 0.f) : 0.f);
    Set(54,E->RoomFinish,Skin?1.f:0.f,E->bRoomPolish?(E->bRoomProp?.5f:1.f):0.f,E->bRoomBar?1.f:0.f);
    static const bool Relief=ReadShadowSetting("room_procedural_relief",1,0,1)>.5f;
    static const bool Finish=ReadShadowSetting("room_finish",1,0,1)>.5f;
    if (!Relief) Ps[52*4+3]=0;
    if (!Finish) { Ps[54*4]=0; Ps[54*4+2]=0; }
    HRESULT Hr=Rp9SetVertexShader(Device_,Skin ? E->RoomSkinVs : E->RoomVs);
    if(SUCCEEDED(Hr))Hr=Rp9SetPixelShader(Device_,E->RoomPs);
    if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,0,Vs,22);
    if(Skin && SUCCEEDED(Hr))
    {
        float Rows[192*4];
        for(unsigned I=0;I<64;++I)for(unsigned R=0;R<3;++R)for(unsigned C=0;C<4;++C)
            Rows[I*12+R*4+C]=(I ? E->RoomBones[I] : Transforms_.World.Values)[C*4+R];
        Hr=Rp9SetVertexConstants(Device_,24,Rows,192);
        if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,216,Transforms_.View.Values,4);
    }
    if(SUCCEEDED(Hr))Hr=Rp9SetPixelConstants(Device_,0,Ps,55);
    if(SUCCEEDED(Hr) && P.Texture)Hr=Rp9SetTexture(Device_,14,P.Texture);
    // Match the diffuse address mode for the existing (possibly mirrored) UVs.
    for(unsigned S : {D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV})
    {
        auto& A=Rp9DeviceCalls();
        unsigned V=A.SamplerValid[0][S] ? A.Samplers[0][S] : D3DTADDRESS_WRAP;
        Rp9SetSamplerState(Device_,14,(D3DSAMPLERSTATETYPE)S,V);
    }
    Rp9SetSamplerState(Device_,14,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);Rp9SetSamplerState(Device_,14,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
    Rp9SetSamplerState(Device_,14,D3DSAMP_MIPFILTER,D3DTEXF_LINEAR);Rp9SetSamplerState(Device_,14,D3DSAMP_SRGBTEXTURE,FALSE);
    if(FAILED(Hr)){ExSurfaceRelease();return false;}
    E->bSurfaceActive=true;
    if(E->RoomLoggedMaps.size()<16 && E->RoomLoggedMaps.insert(P.Map).second)
        ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"room material active: map %s, FVF 0x%x, lights %u, normal %.2f, roughness %.2f, skin %.1f",
            P.Map.c_str(),Fvf,Count,P.Normal,P.Roughness,P.Skin);
    return true;
}

GENRESULT DACOM_API FDirectX9::ApplyRoomContactShadows()
{
    auto* E=Ex_;
    if(!Device_ || !E || !E->bRoomFrame || !E->bRoomEnabled || E->bRoomAoFailed ||
       E->bInPass || E->bShadowDrawing || !E->SceneDepth.Texture || !E->SceneDepth.Surface) return GR_OK;
    static const float Strength=ReadShadowSetting("room_contact_shadows",.32f,0,.6f);
    if(Strength<=0) return GR_OK;
    IDirect3DSurface9* Depth=nullptr;
    if(FAILED(Device_->GetDepthStencilSurface(&Depth)))return GR_OK;
    if(Depth!=E->SceneDepth.Surface){if(Depth)Depth->Release();return GR_OK;}
    D3DVIEWPORT9 V={};Device_->GetViewport(&V);
    D3DXMATRIX Proj,Inv;memcpy(&Proj,Transforms_.Projection.Values,64);
    if(!D3DXMatrixInverse(&Inv,nullptr,&Proj)){Depth->Release();return GR_OK;}
    if(!E->RoomAoPs)
    {
        std::string Path=RoomDataPath("../SHADERS/room_contact.hlsl"),Source;
        FILE* File=fopen(Path.c_str(),"rb");
        if(File){char Bytes[4096];size_t N;while((N=fread(Bytes,1,sizeof(Bytes),File)))Source.append(Bytes,N);fclose(File);}
        std::vector<unsigned char> Code;
        if(Source.empty() || !CompileStage(Source,Path,nullptr,"PSMain","ps_3_0",&Code) ||
           FAILED(Device_->CreatePixelShader((DWORD*)Code.data(),&E->RoomAoPs)))
        {E->bRoomAoFailed=true;Depth->Release();return GR_GENERIC;}
    }
    ExSurfaceEnd();ExSurfaceRelease();FlushDrawState(Device_);
    HRESULT Hr=E->RoomAoState ? E->RoomAoState->Capture() : Device_->CreateStateBlock(D3DSBT_ALL,&E->RoomAoState);
    if(FAILED(Hr)){Depth->Release();return (GENRESULT)Hr;}
    D3DSURFACE_DESC Desc={};Depth->GetDesc(&Desc);
    float Params[32]={};memcpy(Params,&Inv,64);
    Params[16]=1.f/Desc.Width;Params[17]=1.f/Desc.Height;Params[18]=(float)Desc.Width;Params[19]=(float)Desc.Height;
    Params[20]=(float)V.X;Params[21]=(float)V.Y;Params[22]=(float)V.Width;Params[23]=(float)V.Height;
    Params[24]=V.MinZ;Params[25]=V.MaxZ;Params[26]=.4f;Params[27]=Strength;Params[28]=Proj._22;
    struct Vertex{float X,Y,Z,W,U,V;};
    float X=(float)V.X,Y=(float)V.Y,W=(float)V.Width,H=(float)V.Height,Iw=Params[16],Ih=Params[17];
    Vertex Q[]={{X-.5f,Y-.5f,0,1,X*Iw,Y*Ih},{X+W-.5f,Y-.5f,0,1,(X+W)*Iw,Y*Ih},
                {X-.5f,Y+H-.5f,0,1,X*Iw,(Y+H)*Ih},{X+W-.5f,Y+H-.5f,0,1,(X+W)*Iw,(Y+H)*Ih}};
    Hr=Device_->SetDepthStencilSurface(nullptr);
    if(SUCCEEDED(Hr))Hr=Rp9SetTexture(Device_,14,E->SceneDepth.Texture);
    Rp9SetVertexShader(Device_,nullptr);Rp9SetFvf(Device_,D3DFVF_XYZRHW|D3DFVF_TEX1);
    Rp9SetPixelShader(Device_,E->RoomAoPs);Rp9SetPixelConstants(Device_,0,Params,8);
    Device_->SetTextureStageState(0,D3DTSS_TEXCOORDINDEX,0);Device_->SetTextureStageState(0,D3DTSS_TEXTURETRANSFORMFLAGS,0);
    Rp9SetRenderState(Device_,D3DRS_ZENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_ZWRITEENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_ALPHATESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_FOGENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_ALPHABLENDENABLE,TRUE);Rp9SetRenderState(Device_,D3DRS_SRCBLEND,D3DBLEND_ZERO);
    Rp9SetRenderState(Device_,D3DRS_DESTBLEND,D3DBLEND_SRCCOLOR);Rp9SetRenderState(Device_,D3DRS_BLENDOP,D3DBLENDOP_ADD);
    Rp9SetRenderState(Device_,D3DRS_COLORWRITEENABLE,7);Rp9SetRenderState(Device_,D3DRS_CULLMODE,D3DCULL_NONE);
    Rp9SetRenderState(Device_,D3DRS_SCISSORTESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_STENCILENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_CLIPPLANEENABLE,0);Rp9SetRenderState(Device_,D3DRS_SRGBWRITEENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_FILLMODE,D3DFILL_SOLID);
    Rp9SetSamplerState(Device_,14,D3DSAMP_MINFILTER,D3DTEXF_POINT);Rp9SetSamplerState(Device_,14,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
    Rp9SetSamplerState(Device_,14,D3DSAMP_MIPFILTER,D3DTEXF_NONE);Rp9SetSamplerState(Device_,14,D3DSAMP_SRGBTEXTURE,FALSE);
    Rp9SetSamplerState(Device_,14,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Rp9SetSamplerState(Device_,14,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    if(SUCCEEDED(Hr))Hr=Device_->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Q,sizeof(Vertex));
    Rp9SetTexture(Device_,14,nullptr);HRESULT Restore=Device_->SetDepthStencilSurface(Depth);
    if(SUCCEEDED(Restore))Restore=E->RoomAoState->Apply();
    Depth->Release();Rp9DeviceCalls().Invalidate();
    if(SUCCEEDED(Hr) && !E->bRoomAoLogged)
    {E->bRoomAoLogged=true;ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"room contact shading active: strength %.2f, radius 0.4, opaque depth before translucency",Strength);}
    return (GENRESULT)(FAILED(Hr) ? Hr : Restore);
}
