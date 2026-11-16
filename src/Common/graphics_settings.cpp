#include "graphics_policy.h"
#include "graphics_adapter.h"
#include "common_misc.h"
#include <windows.h>
#include <cstdlib>
#include <cstdio>
#include <mutex>

namespace
{
    thread_local unsigned CharacterPortraitDepth=0;
    struct Preferences
    {
        int Active[GraphicsSettings::Count];
        int Configured[GraphicsSettings::Count];
        char AutoAdapter[96]={};
        int AutoVersion=0;
        Preferences()
        {
            char folder[MAX_PATH]={}, path[MAX_PATH]={};
            if (GetUserDataPath(folder))
                _snprintf_s(path,sizeof(path),_TRUNCATE,"%s\\PerfOptions.ini",folder);
            char port[MAX_PATH]={};
            GetModuleFileNameA(nullptr,port,MAX_PATH);
            char const* executable=std::strrchr(port,'\\');
            bool const client=executable && _strnicmp(executable+1,"freelancer",10)==0;
            if (char* slash=std::strrchr(port,'\\')) strcpy_s(slash+1,sizeof(port)-size_t(slash+1-port),"port.ini");
            if (path[0]) {
                AutoVersion=GetPrivateProfileIntA("Graphics","auto_profile_version",0,path);
                GetPrivateProfileStringA("Graphics","auto_adapter","",AutoAdapter,sizeof(AutoAdapter),path);
            }
            auto const gpu=client ? GraphicsAdapter::Detect() : GraphicsAdapter::Info{};
            bool const apply=gpu.Type!=GraphicsAdapter::Unknown &&
                (AutoVersion!=1 || std::strcmp(AutoAdapter,gpu.Key)!=0);
            for (int i=0;i<GraphicsSettings::Count;++i)
            {
                int value=GraphicsSettings::Default(i);
                // New setting on an already-profiled integrated adapter: do not
                // reset other manual choices just to initialize this addition.
                if ((i==GraphicsSettings::Interiors || i==GraphicsSettings::Hair || i==GraphicsSettings::TradeLane || i==GraphicsSettings::Hyperspace) && gpu.Type==GraphicsAdapter::Integrated) value=0;
                // Migrate existing synchronization/filtering preferences on first run.
                if (i==GraphicsSettings::VSync) value=GetPrivateProfileIntA("Render","vsync",1,port)!=0;
                if (i==GraphicsSettings::WeaponLights) value=GetPrivateProfileIntA("Render","weapon_lights",1,port)!=0;
                if (i==GraphicsSettings::Anisotropy) {
                    int af=int(GetPrivateProfileIntA("Render","anisotropy",16,port));
                    value=0;while (value<4 && (1<<(value+1))<=af) ++value;
                }
                if (i==GraphicsSettings::FpsLimit) {
                    int fps=int(GetPrivateProfileIntA("Render","fps_limit",144,port));
                    if (fps==0 || fps>180) value=GraphicsSettings::Maximum(i);
                    for(int index=1;index<=GraphicsSettings::Maximum(i);++index)
                        if (GraphicsSettings::Fps(index)==fps) value=index;
                }
                char text[64]={};
                if (path[0]) GetPrivateProfileStringA("Graphics",GraphicsSettings::Key(i),"",text,sizeof(text),path);
                if (!text[0] && path[0] && (i==GraphicsSettings::Relief || i==GraphicsSettings::Highlights)) {
                    char legacy[32]={};
                    GetPrivateProfileStringA("Graphics",i==GraphicsSettings::Relief?"relief":"highlights","",legacy,sizeof(legacy),path);
                    if (!std::strcmp(legacy,"0")) strcpy_s(text,"0");
                    else if (!std::strcmp(legacy,"1")) strcpy_s(text,"3");
                }
                char* end=nullptr;
                long const parsed=std::strtol(text,&end,10);
                while (end && (*end==' ' || *end=='\t')) ++end;
                if (end!=text && (*end==0 || *end==';') && parsed>=0 && parsed<=GraphicsSettings::Maximum(i)) value=int(parsed);
                // Keep old choice indices stable; unlimited/240/360 migrate to 180.
                if (i==GraphicsSettings::FpsLimit && end!=text && (*end==0 || *end==';') &&
                    (parsed==0 || parsed==9 || parsed==10)) value=GraphicsSettings::Maximum(GraphicsSettings::FpsLimit);
                if (value<GraphicsSettings::Minimum(i)) value=GraphicsSettings::Minimum(i);
                Active[i]=Configured[i]=value;
            }
            if (apply)
            {
                // Snapshot the previous user preferences before migrating this adapter.
                char backup[MAX_PATH]={};
                _snprintf_s(backup,sizeof(backup),_TRUNCATE,"%s.before_gpu_profile.bak",path);
                bool const exists=path[0] && GetFileAttributesA(path)!=INVALID_FILE_ATTRIBUTES;
                bool const canSave=path[0] && (!exists || CopyFileA(path,backup,FALSE));
                bool saved=canSave;
                for (int i=0;i<GraphicsSettings::Count;++i)
                {
                    // Keep frame pacing independent of the effect-quality profile.
                    if (i==GraphicsSettings::VSync || i==GraphicsSettings::FpsLimit) continue;
                    Active[i]=Configured[i]=gpu.Type==GraphicsAdapter::Integrated ? GraphicsSettings::Minimum(i) : GraphicsSettings::Default(i);
                    char value[16];sprintf_s(value,"%d",Active[i]);
                    if (canSave && !WritePrivateProfileStringA("Graphics",GraphicsSettings::Key(i),value,path)) saved=false;
                }
                if (saved && WritePrivateProfileStringA("Graphics","auto_adapter",gpu.Key,path) &&
                    WritePrivateProfileStringA("Graphics","auto_profile_version","1",path))
                {
                    strcpy_s(AutoAdapter,gpu.Key);
                    AutoVersion=1;
                }
            }
            if (path[0]) {
                char logPath[MAX_PATH]={};
                _snprintf_s(logPath,sizeof(logPath),_TRUNCATE,"%s.graphics_adapter.txt",path);
                if (FILE* log=std::fopen(logPath,"w")) {
                    std::fprintf(log,"GPU: %s\nAdapter: %s\nType: %s\nProfile: %s\nSaved marker: %d\n",
                        gpu.Name,gpu.Key,gpu.Type==GraphicsAdapter::Integrated?"integrated":gpu.Type==GraphicsAdapter::Discrete?"discrete":"unknown",
                        apply?"applied startup defaults":"preserved preferences",AutoVersion);
                    std::fclose(log);
                }
            }
        }
    };
    Preferences& State() { static Preferences state; return state; }
    std::mutex ConfiguredMutex;
}

int __cdecl GraphicsSettings::Get(int setting, bool configured)
{
    if (setting<0 || setting>=Count) return 0;
    auto& state=State();
    if (!configured) return state.Active[setting];
    std::lock_guard<std::mutex> lock(ConfiguredMutex);
    return state.Configured[setting];
}
void __cdecl GraphicsSettings::Set(int setting, int value)
{
    if (setting==FpsLimit && (value==0 || value==9 || value==10)) value=Maximum(FpsLimit);
    if (setting<0 || setting>=Count || value<0 || value>Maximum(setting)) return;
    auto& state=State();
    std::lock_guard<std::mutex> lock(ConfiguredMutex);
    state.Configured[setting]=value;
}
bool __cdecl GraphicsSettings::RestartRequired()
{
    auto& state=State();
    std::lock_guard<std::mutex> lock(ConfiguredMutex);
    for (int i=0;i<Count;++i) if (state.Active[i]!=state.Configured[i]) return true;
    return false;
}
void __cdecl GraphicsSettings::WriteAutoProfile(FILE* file)
{
    auto& state=State();
    std::fprintf(file,"auto_profile_version = %d\nauto_adapter = %s\n",state.AutoVersion,state.AutoAdapter);
}
float __cdecl PortGraphicsRenderValue(char const* key, float authored)
{
    if (CharacterPortraitDepth && key && std::strncmp(key,"character_hair",14)==0) return 0;
    return key ? GraphicsSettings::RenderValue(State().Active,key,authored) : authored;
}

void __cdecl PortCharacterPortraitScope(int enter)
{
    if(enter)++CharacterPortraitDepth;
    else if(CharacterPortraitDepth)--CharacterPortraitDepth;
}

#include "common_reputation.h"
#include "player_customization.h"
#include <string>

namespace {

char const* BodyNick(char const* key)
{
    if (!key || !key[0] || strcmp(key, "default") == 0) return "pl_male2_journeyman_body";
    if (strcmp(key, "li_elite") == 0) return "li_male_elite_body";
    if (strcmp(key, "li_guard") == 0) return "li_male_guard_body";
    if (strcmp(key, "br_elite") == 0) return "br_male_elite_body";
    if (strcmp(key, "br_guard") == 0) return "br_male_guard_body";
    if (strcmp(key, "rh_elite") == 0) return "rh_male_elite_body";
    if (strcmp(key, "rh_guard") == 0) return "rh_male_guard_body";
    if (strcmp(key, "ku_elite") == 0) return "ku_male_elite_body";
    if (strcmp(key, "ku_guard") == 0) return "ku_male_guard_body";
    if (strcmp(key, "order") == 0) return "pi_orillion_body";
    if (strcmp(key, "classic") == 0) return "pl_trent_body";
    return nullptr;
}

char const* GloveKind(char const* key)
{
    if (!key) return nullptr;
    if (strcmp(key, "li_guard") == 0) return "yel";
    if (strcmp(key, "li_elite") == 0) return "li";
    if (strcmp(key, "br_elite") == 0 || strcmp(key, "br_guard") == 0) return "br";
    if (strcmp(key, "rh_elite") == 0) return "rh";
    return nullptr;
}

void HandNicks(char const* kind, char const*& right, char const*& left)
{
    right = "benchmark_male_hand_right";
    left = "benchmark_male_hand_left";
    if (!kind) return;
    if (strcmp(kind, "rh") == 0) { right = "rh_male_glove_right"; left = "rh_male_glove_left"; }
    else if (strcmp(kind, "li") == 0) { right = "li_male_glove_right"; left = "li_male_glove_left"; }
    else if (strcmp(kind, "yel") == 0) { right = "yel_male_glove_right"; left = "yel_male_glove_left"; }
    else if (strcmp(kind, "br") == 0) { right = "br_male_glove_right"; left = "br_male_glove_left"; }
}

char const* HatNick(char const* key)
{
    if (!key || !key[0] || strcmp(key, "default") == 0) return nullptr;
    if (strcmp(key, "rh_elite") == 0) return "prop_hat_male_rh_elite";
    if (strcmp(key, "li_elite") == 0) return "prop_hat_male_li_elite";
    if (strcmp(key, "br_elite") == 0) return "prop_hat_male_br_elite";
    if (strcmp(key, "ku_elite") == 0) return "prop_hat_male_ku_elite";
    return nullptr;
}

char const* HelmNick(char const* key)
{
    if (!key || !key[0] || strcmp(key, "default") == 0) return "comm_ge_generic2";
    if (strcmp(key, "ge_generic1") == 0) return "comm_ge_generic1";
    if (strcmp(key, "pl_player") == 0) return "comm_pl_player";
    if (strcmp(key, "br_brighton") == 0) return "comm_br_brighton";
    if (strcmp(key, "br_darcy") == 0) return "comm_br_darcy";
    if (strcmp(key, "br_kaitlyn") == 0) return "comm_br_kaitlyn";
    if (strcmp(key, "ku_kym") == 0) return "comm_ku_kym";
    if (strcmp(key, "li_hatcher") == 0) return "comm_li_hatcher";
    if (strcmp(key, "pi_pirate") == 0) return "comm_pi_pirate";
    if (strcmp(key, "rh_alaric") == 0) return "comm_rh_alaric";
    if (strcmp(key, "rh_reichman") == 0) return "comm_rh_reichman";
    if (strcmp(key, "rh_wilham") == 0) return "comm_rh_wilham";
    if (strcmp(key, "br_elite") == 0) return "comm_br_elite";
    if (strcmp(key, "rh_elite") == 0) return "comm_rh_elite";
    if (strcmp(key, "li_elite") == 0) return "comm_li_elite";
    if (strcmp(key, "ku_elite") == 0) return "comm_ku_elite";
    return nullptr;
}

unsigned PartId(int typeId, char const* name)
{
    CostumeDescriptions const* descriptions = GetCostumeDescriptions();
    if (!descriptions || !name || !name[0]) return 0;
    bodypart const* part = descriptions->find_bodypart(typeId, name);
    return part ? part->Id : 0;
}

unsigned AccessoryId(char const* name)
{
    CostumeDescriptions const* descriptions = GetCostumeDescriptions();
    if (!descriptions || !name || !name[0]) return 0;
    accessory const* item = descriptions->find_accessory(name);
    return item ? item->Id : 0;
}

void AddAccessory(Costume& costume, unsigned id)
{
    if (!id) return;
    for (unsigned i = 0; i < costume.AccessoryCount && i < 8; ++i)
        if (costume.AccessoryIds[i] == id) return;
    if (costume.AccessoryCount >= 8) return;
    costume.AccessoryIds[costume.AccessoryCount++] = id;
}

bool PerfPath(char* path, size_t size)
{
    char folder[MAX_PATH] = {};
    if (!GetUserDataPath(folder)) return false;
    _snprintf_s(path, size, _TRUNCATE, "%s\\PerfOptions.ini", folder);
    return true;
}

}  // namespace

namespace {
template<size_t N> int ChoiceIndex(PlayerCustomization::Choice const (&choices)[N], char const* key)
{
    for (size_t i = 0; i < N; ++i) if (strcmp(choices[i].Key, key) == 0) return static_cast<int>(i);
    return -1;
}
void RemoveAccessory(Costume& cost, unsigned id)
{
    unsigned count = 0;
    for (unsigned i = 0; i < cost.AccessoryCount && i < 8; ++i)
        if (cost.AccessoryIds[i] != id) cost.AccessoryIds[count++] = cost.AccessoryIds[i];
    cost.AccessoryCount = count;
}
void RemoveEmptyAccessories(Costume& cost)
{
    unsigned count = 0;
    for (unsigned i = 0; i < cost.AccessoryCount && i < 8; ++i) {
        accessory const* desc = GetCostumeDescriptions()->find_accessory(cost.AccessoryIds[i]);
        if (desc && _stricmp(desc->Mesh.c_str(), "null.3db") != 0)
            cost.AccessoryIds[count++] = cost.AccessoryIds[i];
    }
    cost.AccessoryCount = count;
}
void ApplyKeys(Costume& Base, Costume& Comm, char const* body, char const* hat, char const* helm)
{
    using namespace PlayerCustomization;
    if (!GetCostumeDescriptions()) return;
    if (ChoiceIndex(Bodies, body) >= 0) {
        if (unsigned id = PartId(0, BodyNick(body)))
            Base.PartIds[1] = id;
        char const* right = nullptr;
        char const* left = nullptr;
        HandNicks(GloveKind(body), right, left);
        if (unsigned id = PartId(3, right))
            Base.PartIds[3] = id;
        if (unsigned id = PartId(2, left))
            Base.PartIds[2] = id;
        for (int i = 1; i < 4; ++i) Comm.PartIds[i] = Base.PartIds[i];
    }
    if (ChoiceIndex(Hats, hat) >= 0) {
        for (auto const& choice : Hats) RemoveAccessory(Base, AccessoryId(HatNick(choice.Key)));
        RemoveAccessory(Base, AccessoryId("player_prop_hat"));
        RemoveEmptyAccessories(Base);
        AddAccessory(Base, AccessoryId(HatNick(hat)));
    }
    if (ChoiceIndex(Helmets, helm) >= 0) {
        for (auto const& choice : Hats) RemoveAccessory(Comm, AccessoryId(HatNick(choice.Key)));
        RemoveAccessory(Comm, AccessoryId("player_prop_hat"));
        for (auto const& choice : Helmets) RemoveAccessory(Comm, AccessoryId(HelmNick(choice.Key)));
        RemoveAccessory(Comm, AccessoryId("player_commhelmet"));
        RemoveEmptyAccessories(Comm);
        AddAccessory(Comm, AccessoryId(HelmNick(helm)));
    }
}
}

PlayerCustomization::Selection __cdecl PlayerCustomization::Load()
{
    Selection result;
    char path[MAX_PATH] = {}, value[64] = {};
    if (!PerfPath(path, sizeof(path))) return result;
    GetPrivateProfileStringA("Costume", "player_body", "default", value, sizeof(value), path);
    result.Body = ChoiceIndex(Bodies, value); if (result.Body < 0) result.Body = 0;
    GetPrivateProfileStringA("Costume", "player_hat", "default", value, sizeof(value), path);
    result.Hat = ChoiceIndex(Hats, value); if (result.Hat < 0) result.Hat = 0;
    GetPrivateProfileStringA("Costume", "player_commhelmet", "default", value, sizeof(value), path);
    result.Helmet = ChoiceIndex(Helmets, value); if (result.Helmet < 0) result.Helmet = 0;
    return result;
}

bool __cdecl PlayerCustomization::Save(Selection const& value)
{
    if (value.Body < 0 || value.Body >= _countof(Bodies) || value.Hat < 0 ||
        value.Hat >= _countof(Hats) || value.Helmet < 0 || value.Helmet >= _countof(Helmets)) return false;
    char path[MAX_PATH] = {}, old[32768] = {};
    if (!PerfPath(path, sizeof(path))) return false;
    if (GetPrivateProfileSectionA("Costume", old, sizeof(old), path) >= sizeof(old)-2) return false;
    std::string section;
    for (char const* p = old; *p; p += strlen(p)+1) {
        if (_strnicmp(p,"player_body=",12) && _strnicmp(p,"player_hat=",11) &&
            _strnicmp(p,"player_commhelmet=",18)) section.append(p,strlen(p)+1);
    }
    section += std::string("player_body=")+Bodies[value.Body].Key; section += '\0';
    section += std::string("player_hat=")+Hats[value.Hat].Key; section += '\0';
    section += std::string("player_commhelmet=")+Helmets[value.Helmet].Key; section += '\0';
    section += '\0';
    return WritePrivateProfileSectionA("Costume", section.data(), path) != FALSE;
}

void __cdecl PlayerCustomization::Apply(Costume& base, Costume& comm, Selection const& value)
{
    if (value.Body < 0 || value.Body >= _countof(Bodies) || value.Hat < 0 ||
        value.Hat >= _countof(Hats) || value.Helmet < 0 || value.Helmet >= _countof(Helmets)) return;
    ApplyKeys(base, comm, Bodies[value.Body].Key, Hats[value.Hat].Key, Helmets[value.Helmet].Key);
}

void __cdecl PlayerCostume_ApplyOverride(Costume& Base, Costume& Comm)
{
    if (!SinglePlayer()) return;
    char path[MAX_PATH] = {}, body[64] = {}, hat[64] = {}, helm[64] = {};
    if (!PerfPath(path, sizeof(path))) return;
    GetPrivateProfileStringA("Costume", "player_body", "", body, sizeof(body), path);
    GetPrivateProfileStringA("Costume", "player_hat", "", hat, sizeof(hat), path);
    GetPrivateProfileStringA("Costume", "player_commhelmet", "", helm, sizeof(helm), path);
    ApplyKeys(Base, Comm, body, hat, helm);
}
