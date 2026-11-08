// Executes the production presence implementation against an in-memory room/server.
// The build strips only its local includes, leaving all parsing/lifecycle code intact.
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <list>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <utility>
#include "../../src/include/rpg_dialog_protocol.h"
#include "../../src/freelancer/Client/rpg_dialog_model.h"

unsigned CreateID(char const* Text) {
    unsigned Hash = 5381;
    for (; *Text; ++Text) Hash = Hash * 33 + static_cast<unsigned char>(tolower(*Text));
    return Hash;
}
void FDUMP(int, char const*, ...) {}
template<int N> struct TString {
    char Data[N] = {};
    TString& operator=(char const* S) { assert(strlen(S) < N); strcpy_s(Data, S); return *this; }
};
struct ID_String { unsigned Id = 0; void clear() { Id = 0; } };
std::map<std::string, std::string> Files;
struct INI_Reader {
    std::vector<std::string> Lines, Values;
    std::string Header, Key;
    size_t Next = 0;
    bool read_header() {
        while (Next < Lines.size()) {
            std::string Line = Lines[Next++];
            if (Line.size() > 2 && Line[0] == '[') { Header = Line.substr(1, Line.size()-2); return true; }
        }
        return false;
    }
    bool is_header(char const* S) { return _stricmp(Header.c_str(), S) == 0; }
    bool is_value(char const* S) { return _stricmp(Key.c_str(), S) == 0; }
    bool read_value() {
        while (Next < Lines.size()) {
            if (Lines[Next][0] == '[') return false;
            std::string Line = Lines[Next++];
            auto Pos = Line.find('=');
            if (Pos == std::string::npos) continue;
            Key = Line.substr(0, Pos); Values.clear();
            std::istringstream Stream(Line.substr(Pos+1));
            while (std::getline(Stream, Line, ',')) Values.push_back(Line);
            return true;
        }
        return false;
    }
    char const* get_value_string(unsigned Index = 0) { return Index < Values.size() ? Values[Index].c_str() : ""; }
    float get_value_float(unsigned I) { return std::stof(get_value_string(I)); }
    int get_value_int(unsigned I) { return std::stoi(get_value_string(I)); }
    bool get_value_bool(int) { return strcmp(get_value_string(), "true") == 0; }
};
bool OpenContentDataIni(char const* Path, INI_Reader* Reader) {
    auto It = Files.find(Path); if (It == Files.end()) return false;
    std::istringstream Stream(It->second); std::string Line;
    while (std::getline(Stream, Line)) if (!Line.empty()) Reader->Lines.push_back(Line);
    return true;
}
struct Vector {float x=0,y=0,z=0;};
struct Matrix {};
struct FmtStr {void begin_mad_lib(unsigned){} void end_mad_lib(){};};
enum DestroyType {DESTROY_NORMAL};
unsigned NextShip=100, NextRep=1, Creates=0, Destroys=0;
bool HaveLoadout=true, HavePilot=true, FailCreate=false;
std::map<unsigned,unsigned> Players;
unsigned PlayerSystem=0;
std::map<unsigned,int> Objects;
std::set<int> Reps;
namespace pub {
int GetBaseID(unsigned& Id,char const* N){Id=CreateID(N);return 0;}
int GetSystemID(unsigned& Id,char const* N){Id=CreateID(N);return 0;}
int GetShipID(unsigned& Id,char const* N){Id=CreateID(N);return 0;}
int GetLoadoutID(unsigned& Id,char const* N){Id=CreateID(N);return 0;}
namespace Player {
int GetShip(unsigned P,unsigned& S){S=Players[P];return 0;}
int GetRep(unsigned P,int& R){R=1000+P;return 0;}
}
namespace Reputation {
int GetReputationGroup(unsigned& Id,char const* N){Id=CreateID(N);return 0;}
int Alloc(int& R,FmtStr const&,FmtStr const&){R=NextRep++;Reps.insert(R);return 0;}
int Free(int R){assert(Reps.erase(R)==1);return 0;}
void SetAffiliation(int,unsigned){}
void SetAttitude(int,int,float){}
}
namespace SpaceObj {
struct ShipInfo {unsigned ShipArchID=0,LoadoutID=0,ControllerId=0,SystemID=0,ReputationRank=0;
Vector Position;Matrix Orientation;int VibeGroupId=-1,HitPts=0;
unsigned CostumeHead=0,CostumeBody=0,CostumeLeftHand=0,CostumeRightHand=0,CostumeAccessory[8]={};int CostumeAccessoryCount=0;};
int GetSystem(unsigned Object,unsigned& S){S=Object<10 ? PlayerSystem : CreateID("sys");return 0;}
int GetLocation(unsigned,Vector& P,Matrix&){P.x=42000;P.y=0;P.z=-10000;return 0;}
int ExistsAndAlive(unsigned S){return S?0:-2;}
int GetType(unsigned S,unsigned& T){T=1;return Objects.count(S)?0:-2;}
int Create(unsigned& S,ShipInfo const& I){if(FailCreate)return -1;S=NextShip++;Objects[S]=I.VibeGroupId;++Creates;
assert(I.Position.x==41000 && I.Position.y==200 && I.Position.z==-9600);return 0;}
int Destroy(unsigned S,DestroyType){Objects.erase(S);++Destroys;return 0;}
}
namespace AI {
struct Personality {};
struct SetPersonalityParams {Personality Value;int bSetPersonality=0,StateGraphId=0;void* ContentCallbackObject=nullptr;void* DirectiveCallbackObject=nullptr;};
struct DirectiveIdleOp {};
void SubmitState(unsigned,SetPersonalityParams*){}
void SubmitDirective(unsigned,DirectiveIdleOp*){}
}
namespace StateGraph {enum {LEADER};int get_state_graph(char const*,int){return 1;}}
}
namespace Loadout {void const* Get(unsigned){return HaveLoadout?&HaveLoadout:nullptr;}}
bool GetPilotPersonality(unsigned*,pub::AI::Personality*){return HavePilot;}
#define FREELANCER_RPG_WORLD
#include "space_runtime.inc"
int main(){
Files["RPG\\space.ini"]="[RpgShip]\nnickname=test\nenabled=true\nrespawn_seconds=60\nsystem=sys\nanchor=ring\noffset=-1000,200,400\nship_archetype=rh_elite\nloadout=ms3_hassler\npilot=pilot\naffiliation=faction\nindividual_name=33604\n";
PlayerSystem=CreateID("sys");
RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Creates==0);
// Loading in space: no departure event; even delayed readiness is supported.
RpgSpaceTick(1,40);Players[1]=1;RpgSpaceTick(1,1);assert(Creates==1);
Players[2]=2;RpgSpaceTrackPlayer(2);RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Creates==1);
RpgSpaceLogout(1);assert(Objects.size()==1);
Objects.clear();RpgSpaceTick(1,1);assert(Reps.empty() && Creates==1);
RpgSpaceTrackPlayer(2);RpgSpaceTick(1,59);assert(Creates==1);
RpgSpaceTick(1,1);assert(Creates==2); // automatic delayed respawn
RpgSpaceClear();assert(Objects.empty() && Reps.empty());
// Arrival from another system, without docking.
PlayerSystem=CreateID("other");RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Creates==2);
PlayerSystem=CreateID("sys");RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Creates==3);
RpgSpaceClear();
HaveLoadout=false;RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Creates==3 && Reps.empty());
HaveLoadout=true;RpgSpaceTick(1,4);assert(Creates==3);RpgSpaceTick(1,1);assert(Creates==4);RpgSpaceClear();
FailCreate=true;RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Reps.empty());RpgSpaceClear();FailCreate=false;
RpgSpaceTrackPlayer(1);RpgSpaceLogout(1);RpgSpaceTick(1,1);assert(Creates==4);
auto& Config=Files["RPG\\space.ini"];Config.replace(Config.find("respawn_seconds=60"),17,"respawn_seconds=0");
RpgSpaceClear();RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Creates==5);
Objects.clear();RpgSpaceTick(1,1);RpgSpaceTrackPlayer(1);RpgSpaceTick(1,120);assert(Creates==5);
RpgSpaceClear();RpgSpaceTrackPlayer(1);RpgSpaceTick(1,1);assert(Creates==6);RpgSpaceClear();
puts("PASS: space save readiness, system arrival, shared NPC, logout, delayed/disabled respawn, world reset, retry and creation rollback");
}
