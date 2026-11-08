#include <windows.h>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <list>
#include <map>
#include <deque>
#include <algorithm>
#include <limits>
#include "ship_parking.h"
#include "RpgDialog.h"
#include "rpg_fragment_rotation.h"
#define SERVER_API
#define FREELANCER_RPG_WORLD
#define FDUMP(...) ((void)0)

struct INI_Reader {
    struct Section {std::string name; std::vector<std::pair<std::string,std::vector<std::string>>> rows;};
    std::vector<Section> sections;
    int section=-1, row=-1;
    static std::string trim(std::string s) {
        auto a=s.find_first_not_of(" \t\r\n");
        return a==s.npos ? "" : s.substr(a,s.find_last_not_of(" \t\r\n")-a+1);
    }
    bool open(char const* path,bool) {
        std::ifstream in(path); if(!in)return false;
        sections.clear();std::string line;
        while(std::getline(in,line)) {
            line=trim(line.substr(0,line.find(';')));
            if(line.empty())continue;
            if(line[0]=='['){sections.push_back({line.substr(1,line.size()-2),{}});continue;}
            auto eq=line.find('=');if(eq==line.npos || sections.empty())continue;
            std::vector<std::string> values;std::istringstream split(line.substr(eq+1));std::string v;
            while(std::getline(split,v,','))values.push_back(trim(v));
            // Dialogue text is an unquoted whole value in real INI_Reader::get_value_string().
            sections.back().rows.push_back({trim(line.substr(0,eq)),values});
        }
        reset();return true;
    }
    void reset(){section=-1;row=-1;}
    bool read_header(){row=-1;return ++section<static_cast<int>(sections.size());}
    bool read_value(){return ++row<static_cast<int>(sections[section].rows.size());}
    bool is_header(char const* s){return !_stricmp(sections[section].name.c_str(),s);}
    bool is_value(char const* s){return !_stricmp(sections[section].rows[row].first.c_str(),s);}
    char const* get_value_string(unsigned i){static std::string scratch;auto const& v=sections[section].rows[row].second;scratch=i<v.size()?v[i]:"";return scratch.c_str();}
    char const* get_value_string(){static std::string raw;raw.clear();for(auto const& v:sections[section].rows[row].second){if(!raw.empty())raw+=", ";raw+=v;}return raw.c_str();}
    int get_value_int(unsigned i){return static_cast<int>(strtoul(get_value_string(i),nullptr,10));}
    double get_value_float(unsigned i){return atof(get_value_string(i));}
    unsigned get_num_parameters(){return static_cast<unsigned>(sections[section].rows[row].second.size());}
    bool is_value_empty(unsigned i){return !*get_value_string(i);}
};

unsigned CreateID(char const* s){unsigned h=2166136261u;while(*s)h=(h^static_cast<unsigned char>(tolower(*s++)))*16777619u;return h;}
struct CacheString {char const* Value=nullptr;};
struct EquipDesc {
    unsigned ArchId=0;char const* Hardpoint=nullptr;float Health=1;int Count=1;
    unsigned char bEquipped=0;bool bMission=false;int Owner=0;
    void set_arch_id(unsigned v){ArchId=v;} void set_hardpoint(CacheString v){Hardpoint=v.Value;}
    void set_status(float v){Health=v;} void set_count(int v){Count=v;}
    void set_equipped(unsigned char v){bEquipped=v;}void set_owner(int v){Owner=v;}void set_id(int){}
};
struct EquipDescList {std::list<EquipDesc> Items;};
struct CollisionGroupDesc {unsigned short Id=0;float Health=1;};
using EquipDescVector=std::vector<EquipDesc>;
constexpr int SUBOBJ_ID_NONE=0;
std::deque<std::string> Strings;
char const* StringAlloc(char const* s,bool){Strings.emplace_back(s);return Strings.back().c_str();}
namespace Archetype {struct Ship{};Ship* GetShip(unsigned id){static Ship s;return id && id!=999 ? &s:nullptr;}}
#include "cache_types.inc"
struct PlayerSlot {
    unsigned client_id=1,ship_archetype=11,current_base=0,ship_object_id=0;
    float relative_health=.75f;int cash=200000;
    std::string weapon_group_name="guns";
    EquipDescList equipment;std::list<CollisionGroupDesc> collision_groups;
};
PlayerSlot Players[2];bool Multiplayer=false,FailCash=false;
bool IsMPServer(){return Multiplayer;}
unsigned PlayerDB_GetMaxPlayers(){return 2;}
PlayerSlot* PlayerDB_GetPlayer(unsigned id){return &Players[id-1];}
void PlayerData_SetShipArch(PlayerSlot& s,unsigned a){s.ship_archetype=a;}
void PlayerData_LoadEquipment(PlayerSlot& s,EquipDescList const& e){s.equipment=e;}
void PlayerData_SetRelativeHealth(PlayerSlot& s,float h,bool){s.relative_health=h;}
void PlayerData_SetCollisionGroups(PlayerSlot& s,std::list<CollisionGroupDesc> const& g){s.collision_groups=g;}
struct IClient {void SendCommonSetWeaponGroup(unsigned,unsigned char const*,unsigned){}};
IClient* g_pClientInterface=nullptr;
struct IFileSystem {void GetFileSysPath(char* p,size_t){strcpy(p,".");}};
namespace pub {
IFileSystem* GetDataPath(){static IFileSystem f;return &f;}
namespace Reputation {int GetReputationGroup(unsigned&,char const*);int GetReputation(int,unsigned,float&);}
namespace Player {
int GetRep(unsigned,int&);
int AdjustCash(unsigned id,int amount){if(FailCash)return -1;Players[id-1].cash+=amount;return 0;}
int SetShipAndLoadout(unsigned id,unsigned arch,EquipDescVector const&){Players[id-1].ship_archetype=arch;return 0;}
}}
#include "cache.inc"

// Dialogue host adapters; server exports above remain the actual production implementation.
char const* PortLanguage(){return "ru";}
bool CourierAvailable=true;
bool TrainCourierCanStart(unsigned base){return CourierAvailable && base!=0;}
bool OpenContentDataIni(char const* path,INI_Reader* r){return r->open(path,false);}
struct FContentBase {unsigned BaseId=0;};
struct ID_String {void clear(){}};
struct FStoryMissionCreateParms {unsigned PlayerId=0;void* StoryEvents=nullptr;};
struct FContentPlayerState {
    unsigned PlayerId=1, Mission=0; FContentBase Base{123};
    unsigned GetGroupLiveMission(){return Mission;}
    FContentBase* GetBaseRecord(){return &Base;}
    void JoinMissionAsGroup(unsigned m,unsigned,ID_String*,bool,unsigned){Mission=m;}
};
FContentPlayerState* FindContentPlayerState(unsigned){static FContentPlayerState s;return &s;}
namespace pub {namespace Controller {
constexpr unsigned ABOVE_NORMAL=1;
enum class EMessage {MissionStart};
unsigned Create(char const*,char const*,FStoryMissionCreateParms*,unsigned){return 1;}
void _SendMessage(unsigned,EMessage,void*){}
}}
float TestAttitude = 1;
bool RepFailure=false;
unsigned LastFaction=0;
namespace pub {
namespace Player { int GetRep(unsigned, int& rep) { rep=1; return RepFailure?-1:0; } }
namespace Reputation {
int GetReputationGroup(unsigned& group, char const* name) { group=CreateID(name); return 0; }
int GetReputation(int, unsigned group, float& attitude) { LastFaction=group;attitude=TestAttitude; return RepFailure?-1:0; }
}}
FARPROC FakeGetProcAddress(HMODULE,char const* name) {
    if(!strcmp(name,"PlayerShipParking_Status"))return reinterpret_cast<FARPROC>(&PlayerShipParking_Status);
    if(!strcmp(name,"PlayerShipParking_Buy"))return reinterpret_cast<FARPROC>(&PlayerShipParking_Buy);
    if(!strcmp(name,"PlayerShipParking_CanBuy"))return reinterpret_cast<FARPROC>(&PlayerShipParking_CanBuy);
    return nullptr;
}
#define GetProcAddress FakeGetProcAddress
#include "dialog.inc"

static ShipParkingStatus status() {ShipParkingStatus s;assert(PlayerShipParking_Status(1,&s)==0);return s;}
static int buy() {auto s=status();return PlayerShipParking_Buy(1,s.BaseId,s.SellerId,s.Owned,s.Price);}
static void roundtrip() {
    FILE* f=fopen("save.ini","w");assert(f);fputs("[Player]\n",f);ShipCache_Write(f,1);fclose(f);
    INI_Reader r;assert(r.open("save.ini",false));std::vector<ShipCacheRecord> ships;ShipParkingSave rights;
    while(r.read_header())while(r.read_value())assert(ShipCache_TryRead(ships,rights,r));
    ShipCache_Clear(1);ShipCache_Install(1,ships,rights);
}

int main() {
    unsigned a=CreateID("base_a"),b=CreateID("base_b");auto& p=Players[0];p.current_base=a;
    EquipDesc gun;gun.ArchId=51;gun.Hardpoint="HpGun01";gun.Health=.6f;gun.bEquipped=1;
    p.equipment.Items.push_back(gun);p.collision_groups.push_back({7,.4f});
    ShipCache_Install(1,{},{});
    assert(status().Owned==0 && status().Price==20000 && status().Maximum==3);
    assert(PlayerShipCache_Park(1)==ParkingFull && p.ship_archetype==11);
    p.cash=19999;assert(buy()==ParkingNoMoney && p.cash==19999 && status().Owned==0);
    p.cash=200000;FailCash=true;assert(buy()==ParkingInvalid && status().Owned==0);FailCash=false;
    auto quote=status();assert(buy()==0 && p.cash==180000);
    assert(PlayerShipParking_Buy(1,a,quote.SellerId,quote.Owned,quote.Price)==ParkingStale && p.cash==180000);
    assert(PlayerShipCache_Park(1)==0 && !p.ship_archetype && status().Used==1);
    roundtrip();assert(status().Owned==1 && status().Used==1);
    p.current_base=b;assert(status().Owned==0 && status().Used==0 && status().Price==12000);
    assert(PlayerShipCache_Take(1,0)==ParkingWrongBase && !p.ship_archetype);
    assert(PlayerShipParking_Buy(1,a,quote.SellerId,0,20000)==ParkingWrongBase);
    assert(buy()==0 && p.cash==168000);
    p.current_base=a;assert(PlayerShipCache_Take(1,0)==0);
    assert(p.ship_archetype==11 && p.relative_health==.75f && p.weapon_group_name=="guns");
    assert(p.equipment.Items.front().Health==.6f && p.collision_groups.front().Id==7);
    roundtrip();assert(status().Used==0 && status().Owned==1); // empty rights survive
    assert(PlayerShipCache_Park(1)==0);p.ship_archetype=22;p.weapon_group_name="newguns";
    assert(PlayerShipCache_Park(1)==ParkingFull);
    assert(PlayerShipCache_Take(1,0)==0 && p.ship_archetype==11 && status().Used==1);
    PlayerShipCacheView v;assert(PlayerShipCache_Get(1,0,&v)==0 && v.ShipArchetype==22);
    assert(buy()==0 && buy()==0 && buy()==ParkingMaxOwned && status().Owned==3);
    p.current_base=b;assert(status().Owned==1);p.current_base=a;
    assert(pub::Player::CacheShipAndSetLoadout(1,"train_courier_ship",33,{})==0);
    assert(PlayerShipCache_Count(1)==1 && status().Used==1);
    assert(PlayerShipCache_Park(1)==ParkingMissionShip && PlayerShipCache_Take(1,0)==ParkingMissionShip);
    roundtrip();assert(pub::Player::RestoreCachedShip(1,"train_courier_ship")==0 && p.ship_archetype==11);
    assert(status().Owned==3 && PlayerShipCache_Count(1)==1);
    assert(pub::Player::RestoreCachedShip(1,"park_1")==ParkingInvalid);
    // Migration keeps over-cap ships and excludes named mission storage.
    std::vector<ShipCacheRecord> old;
    for(int i=0;i<5;++i){ShipCacheRecord s;s.Parking=true;s.BaseId=a;s.ShipArchetype=11;strcpy(s.Name,("park_"+std::to_string(i+1)).c_str());s.Id=CreateID(s.Name);old.push_back(s);}
    ShipCache_Install(1,old,{});assert(status().Owned==3 && status().Used==5);
    assert(PlayerShipCache_Park(1)==ParkingFull);assert(PlayerShipCache_Take(1,0)==0 && status().Used==5);
    p.ship_archetype=0;assert(PlayerShipCache_Take(1,0)==0 && status().Used==4);
    roundtrip();assert(status().Used==4 && status().Owned==3);
    // Explicit marker prevents a second migration after ownership is deliberately zero.
    ShipParkingSave explicitZero;explicitZero.Initialized=true;
    ShipCache_Install(1,old,explicitZero);assert(status().Owned==0 && status().Used==5);
    // Parse both legacy record kinds and preserve an explicit mission kind named park_N.
    {FILE* f=fopen("legacy.ini","w");fputs("[Player]\nship_cache = 1, park_1, 11, 1, 123\nship_cache = 2, train_courier_ship, 22, 1, 123\nship_cache = 3, park_9, 33, 1, 123, 0\n",f);fclose(f);
     INI_Reader r;assert(r.open("legacy.ini",false));old.clear();ShipParkingSave rights;
     while(r.read_header())while(r.read_value())assert(ShipCache_TryRead(old,rights,r));
     assert(old.size()==3 && old[0].Parking && !old[1].Parking && !old[2].Parking);}
    ShipCache_Install(1,{},{});p.current_base=CreateID("invalid_price");assert(!status().SellerId);
    assert(PlayerShipParking_Buy(1,p.current_base,CreateID("seller_c"),0,20000)==ParkingNoSeller);
    Multiplayer=true;assert(PlayerShipCache_Park(1)==ParkingMultiplayer);Multiplayer=false;
    p.current_base=a;p.ship_object_id=1;ShipParkingStatus unavailable;
    assert(PlayerShipParking_Status(1,&unavailable)==ParkingWrongBase);p.ship_object_id=0;
    // Real dialogue parsing, localization, quote/confirm, cancellation, replay and base changes.
    unsigned dialog=RpgDialogLoadFile("dialog.ini");assert(dialog);
    unsigned start=RpgDialogBeginSession(dialog,1);assert(start==CreateID("parking_start"));
    assert(wcsstr(RpgDialogRenderText(dialog,start,-1,1),L"20000"));
    unsigned confirm=RpgDialogChoose(dialog,start,0,1);assert(confirm==CreateID("parking_confirm"));
    unsigned back=RpgDialogChoose(dialog,confirm,1,1);assert(back==start && status().Owned==0);
    confirm=RpgDialogChoose(dialog,start,0,1);int cash=p.cash;
    unsigned success=RpgDialogChoose(dialog,confirm,0,1);assert(success==CreateID("parking_success") && p.cash==cash-20000);
    assert(RpgDialogChoose(dialog,confirm,0,1)==0 && status().Owned==1 && p.cash==cash-20000);
    RpgDialogEndSession(1);assert(RpgDialogChoose(dialog,start,0,1)==0);
    start=RpgDialogBeginSession(dialog,1);confirm=RpgDialogChoose(dialog,start,0,1);p.current_base=b;cash=p.cash;
    assert(RpgDialogChoose(dialog,confirm,0,1)==0 && p.cash==cash);
    assert(RpgDialogBeginSession(dialog,1)==0);
    p.current_base=a;start=RpgDialogBeginSession(dialog,1);confirm=RpgDialogChoose(dialog,start,0,1);p.cash=0;
    assert(RpgDialogChoose(dialog,confirm,0,1)==CreateID("parking_no_money") && status().Owned==1);
    // Re-reading an inline definition must not multiply its choices.
    for(int visit=0;visit<5;++visit){INI_Reader r;assert(r.open("dialog.ini",false));while(r.read_header())assert(RpgDialogConsumeHeader(r,dialog));assert(RpgDialogChoiceCount(dialog,start)==3);}
    puts("PASS: production parking/save/dialogue: local rights, prices, full exchange, migration, mission cache, cash failures, replay/cancel, repeat visits, SP-only");
    {
        // Voiced parking must execute purchases, rather than only advance speech.
        ShipCache_Install(1,{},{}); p.current_base=a; p.cash=100000;
        unsigned voiced=RpgDialogLoadFile("rm0002.ini"); assert(voiced);
        assert(!strcmp(RpgDialogSessionScript(voiced),"SCRIPTS\\RPG\\rm0002\\conversation.thn"));
        unsigned start=RpgDialogBeginSession(voiced,1);
        assert(!strcmp(RpgDialogFragment(voiced,start,-1,1),"rm0002_frag0001"));
        unsigned confirm=RpgDialogChoose(voiced,start,0,1);
        assert(confirm==CreateID("parking_confirm"));
        assert(!strcmp(RpgDialogFragment(voiced,confirm,-1,1),"rm0002_frag0003"));
        assert(wcsstr(RpgDialogRenderText(voiced,confirm,0,1),L"20000"));
        unsigned resume=RpgDialogChoose(voiced,confirm,1,1);
        assert(resume==CreateID("parking_resume") && status().Owned==0);
        assert(RpgDialogChoose(voiced,confirm,0,1)==0 && p.cash==100000);
        confirm=RpgDialogChoose(voiced,resume,0,1);
        unsigned success=RpgDialogChoose(voiced,confirm,0,1);
        assert(success==CreateID("parking_success") && status().Owned==1 && p.cash==80000);
        assert(strlen(RpgDialogFragment(voiced,success,-1,1))>0);
        assert(RpgDialogFragment(voiced,confirm,-1,1)[0]==0);
        assert(RpgDialogChoose(voiced,confirm,0,1)==0 && p.cash==80000);
        start=RpgDialogChoose(voiced,success,0,1);
        confirm=RpgDialogChoose(voiced,start,0,1); p.cash=0;
        unsigned failure=RpgDialogChoose(voiced,confirm,0,1);
        assert(failure==CreateID("parking_no_money") && status().Owned==1 && p.cash==0);
        assert(!strcmp(RpgDialogFragment(voiced,failure,-1,1),"rm0002_frag0014"));
        p.cash=100000;
        for(int i=0;i<2;++i){start=RpgDialogBeginSession(voiced,1);confirm=RpgDialogChoose(voiced,start,0,1);assert(RpgDialogChoose(voiced,confirm,0,1)==CreateID("parking_success"));}
        start=RpgDialogBeginSession(voiced,1);
        assert(RpgDialogChoose(voiced,start,0,1)==CreateID("parking_maximum") && status().Owned==3 && p.cash==60000);
        ShipCache_Install(1,{},{});start=RpgDialogBeginSession(voiced,1);confirm=RpgDialogChoose(voiced,start,0,1);
        assert(PlayerShipParking_Buy(1,a,CreateID("seller_a"),0,20000)==ParkingOk);
        assert(RpgDialogChoose(voiced,confirm,0,1)==CreateID("parking_error") && p.cash==40000);
        start=RpgDialogBeginSession(voiced,1);confirm=RpgDialogChoose(voiced,start,0,1);p.current_base=b;
        assert(RpgDialogChoose(voiced,confirm,0,1)==0 && p.cash==40000);
        assert(RpgDialogBeginSession(voiced,1)==0 && RpgDialogFragment(voiced,start,-1,1)[0]==0);
        p.current_base=a;start=RpgDialogBeginSession(voiced,1);
        assert(RpgDialogChoose(voiced,start,2,1)==CreateID("parking_farewell"));
        assert(!strcmp(RpgDialogFragment(voiced,CreateID("parking_farewell"),-1,1),"rm0002_frag0019"));
        RpgDialogEndSession(1);
        puts("PASS: voiced parking purchase, cancel, no money, maximum, stale quote, repeat click, base change and speech cursor");
    }
    if (std::ifstream("rm0001.ini")) {
        unsigned const voiced = RpgDialogLoadFile("rm0001.ini"); assert(voiced);
        assert(!strcmp(RpgDialogSessionScript(voiced),"SCRIPTS\\RPG\\conversation.thn"));
        unsigned const greeting = RpgDialogBeginSession(voiced,1);
        assert(!strcmp(RpgDialogSceneGroup(voiced), "rm0001"));
        assert(!strcmp(RpgDialogFragment(voiced,greeting,-1,1), "rm0001_frag0001"));
        unsigned offer = RpgDialogChoose(voiced,greeting,0,1); assert(offer==CreateID("offer"));
        assert(RpgDialogChoiceCount(voiced,offer)==4);
        assert(!strcmp(RpgDialogFragment(voiced,offer,1,1), "rm0001_frag0005"));
        unsigned resume = RpgDialogEscape(voiced,offer,1); assert(resume==CreateID("resume"));
        assert(RpgDialogChoose(voiced,offer,1,1)==0);
        offer=RpgDialogChoose(voiced,resume,0,1);
        assert(RpgDialogChoose(voiced,offer,1,1)==CreateID("issued"));
        assert(FindContentPlayerState(1)->Mission==1);
        assert(RpgDialogChoose(voiced,offer,1,1)==0);
        RpgDialogEndSession(1);
        RpgDialogBeginSession(voiced,1);
        assert(RpgDialogChoose(voiced,greeting,0,1)==CreateID("busy"));
        FindContentPlayerState(1)->Mission=0;
        RpgDialogBeginSession(voiced,1);
        auto* tree=FindDialog(voiced); tree->ReputationFaction=1; tree->MinimumReputation=0;
        TestAttitude=-.5f;
        assert(RpgDialogChoose(voiced,greeting,0,1)==CreateID("bad_reputation"));
        TestAttitude=1; RpgDialogBeginSession(voiced,1);
        offer=RpgDialogChoose(voiced,greeting,0,1); TestAttitude=-.5f;
        assert(RpgDialogChoose(voiced,offer,0,1)==CreateID("bad_reputation"));
        assert(!FindContentPlayerState(1)->Mission);
        RpgFragmentRotation rotation;
        std::vector<std::string> pool{"a","b","c"}; std::string last;
        for(int cycle=0;cycle<20;++cycle) {
            std::vector<std::string> seen;
            for(int i=0;i<3;++i) {auto next=rotation.Next(pool);assert(next!=last);seen.push_back(next);last=next;}
            std::sort(seen.begin(),seen.end());assert(seen==pool);
        }
        puts("PASS: voiced graph, four wagon choices, escape back, exactly-once issue, busy/reputation and repeat check, shuffle bags");
    }
    {
        unsigned owner=RpgDialogLoadFile("owner.ini");assert(owner);
        assert(!strcmp(RpgDialogSceneGroup(owner),"rm0001"));
        assert(!strcmp(RpgDialogGestureGroup(owner),"rm0201"));
        assert(!strcmp(RpgDialogSessionScript(owner),"SCRIPTS\\RPG\\rm0201\\conversation.thn"));
        TestAttitude=1;auto* player=FindContentPlayerState(1);player->Mission=0;
        player->Base.BaseId=a;
        unsigned start=RpgDialogBeginSession(owner,1);
        assert(RpgDialogChoose(owner,start,0,1)==CreateID("failed"));
        player->Base.BaseId=b;start=RpgDialogBeginSession(owner,1);
        unsigned offer=RpgDialogChoose(owner,start,0,1);
        assert(offer==CreateID("offer"));
        player->Base.BaseId=a;
        assert(RpgDialogChoose(owner,offer,0,1)==CreateID("failed") && !player->Mission);
        player->Base.BaseId=b;start=RpgDialogBeginSession(owner,1);offer=RpgDialogChoose(owner,start,0,1);
        CourierAvailable=false;
        assert(RpgDialogChoose(owner,offer,0,1)==CreateID("failed") && !player->Mission);
        CourierAvailable=true;start=RpgDialogBeginSession(owner,1);offer=RpgDialogChoose(owner,start,0,1);
        assert(RpgDialogChoose(owner,offer,0,1)==CreateID("issued") && player->Mission);
        assert(!RpgDialogChoose(owner,offer,0,1));
        puts("PASS: shared voice / separate session and gestures; wrong base, moved player, missing berth, exactly-once local issue");
    }
    {
        auto* player=FindContentPlayerState(1);player->Mission=0;player->Base.BaseId=b;
        unsigned owner=RpgDialogLoadFile("owner.ini");auto* tree=FindDialog(owner);
        tree->ReputationFaction=CreateID("faction_b");tree->MinimumReputation=0;tree->StrictReputation=true;
        for(float attitude:{-1.f,0.f,-0.f,std::numeric_limits<float>::quiet_NaN()}) {
            TestAttitude=attitude;unsigned start=RpgDialogBeginSession(owner,1);
            assert(RpgDialogChoose(owner,start,0,1)==CreateID("bad_reputation") && !player->Mission);
        }
        TestAttitude=.00001f;unsigned start=RpgDialogBeginSession(owner,1);
        unsigned offer=RpgDialogChoose(owner,start,0,1);assert(offer==CreateID("offer"));
        TestAttitude=0;
        assert(RpgDialogChoose(owner,offer,0,1)==CreateID("bad_reputation") && !player->Mission);
        TestAttitude=.00001f;start=RpgDialogBeginSession(owner,1);offer=RpgDialogChoose(owner,start,0,1);
        assert(RpgDialogChoose(owner,offer,0,1)==CreateID("issued") && player->Mission);
        player->Mission=0;
        ShipCache_Install(1,{},{});p.current_base=a;p.cash=200000;
        unsigned parking=RpgDialogLoadFile("rm0002.ini");assert(parking);
        for(float attitude:{-.5f,0.f,std::numeric_limits<float>::quiet_NaN()}) {
            TestAttitude=attitude;auto before=status();int cash=p.cash;
            assert(PlayerShipParking_CanBuy(1)==ParkingBadReputation && LastFaction==CreateID("faction_a"));
            assert(buy()==ParkingBadReputation && p.cash==cash && status().Owned==before.Owned);
            start=RpgDialogBeginSession(parking,1);
            assert(RpgDialogChoose(parking,start,0,1)==CreateID("parking_bad_reputation"));
            assert(!strcmp(RpgDialogFragment(parking,CreateID("parking_bad_reputation"),-1,1),"rm0002_frag0023"));
        }
        TestAttitude=.00001f;start=RpgDialogBeginSession(parking,1);
        unsigned confirm=RpgDialogChoose(parking,start,0,1);assert(confirm==CreateID("parking_confirm"));
        TestAttitude=0;int cash=p.cash;
        assert(RpgDialogChoose(parking,confirm,0,1)==CreateID("parking_bad_reputation") && p.cash==cash && !status().Owned);
        assert(!RpgDialogChoose(parking,confirm,0,1));
        TestAttitude=.00001f;assert(buy()==ParkingOk && status().Owned==1);
        TestAttitude=-1;
        assert(status().CanPark==ParkingOk && PlayerShipCache_Park(1)==ParkingOk);
        assert(status().Used==1); // reputation does not confiscate existing property
        RepFailure=true;assert(PlayerShipParking_CanBuy(1)==ParkingInvalid && buy()==ParkingInvalid);RepFailure=false;
        p.current_base=b;TestAttitude=1;assert(PlayerShipParking_CanBuy(1)==ParkingOk && LastFaction==CreateID("faction_b"));
        puts("PASS: strict positive reputation: negative/zero/NaN refused, tiny positive accepted, seller faction, quote-to-buy recheck, direct API, lookup errors, no lost money or existing berths");
    }
}
