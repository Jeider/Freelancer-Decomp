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
    bool get_value_bool(int) { return strcmp(get_value_string(), "true") == 0; }
};
bool OpenContentDataIni(char const* Path, INI_Reader* Reader) {
    auto It = Files.find(Path); if (It == Files.end()) return false;
    std::istringstream Stream(It->second); std::string Line;
    while (std::getline(Stream, Line)) if (!Line.empty()) Reader->Lines.push_back(Line);
    return true;
}
// These presence/legacy-choice fixtures have no authored dialogue tree.
// Dialogue loading is a separate service; keep its boundary explicit here.
bool RpgDialogConsumeHeader(INI_Reader&,unsigned) { return false; }
unsigned RpgDialogLoadFile(char const*) { return 0; }
bool HasDialogTree=false;
unsigned RpgDialogStart(unsigned) { return HasDialogTree ? 1 : 0; }
char const* RpgDialogSceneGroup(unsigned) { return ""; }
char const* RpgDialogSessionScript(unsigned) { return "SCRIPTS\\RPG\\conversation.thn"; }
struct FNpcCharacterDesc { int Appearance = 7, IndividualName = 9; unsigned Affiliation = 1, Voice = 2; ID_String Nickname; };
typedef std::map<unsigned, FNpcCharacterDesc> FNpcCharacterDescMap;
bool LoadNpcCharacterDesc(ID_String* Name, FNpcCharacterDesc* Npc, INI_Reader* Reader) {
    while (Reader->read_value()) if (Reader->is_value("nickname")) Name->Id = CreateID(Reader->get_value_string());
    Npc->Nickname = *Name; return Name->Id != 0;
}
struct CharacterBehaviorDescription {
    int Field00=0;unsigned Field04=1,Field05=0,Field06=1,Field10=1,Filter=0,Field21c=0,Field220=0,Field224=0;
    char const* StringArray2[32]={};unsigned StringArray2Dword[32]={};int StringArray2Count=0;
};
std::map<unsigned long,std::string> Behaviors;
unsigned long NextBehavior=1;
bool FailBehavior=false;
unsigned LastContactIcon=0;
namespace pub {
    int GetBaseID(unsigned& Id, char const* Name) { Id = *Name ? CreateID(Name) : 0; return 0; }
    namespace GF {
        unsigned long CharacterBehaviorCreate(CharacterBehaviorDescription const& D) {
            LastContactIcon=D.Field224;
            assert(D.Field04==0 && D.Field05==0 && D.Field10==0);
            assert(D.StringArray2Count==1 || (D.StringArray2Count==2 && D.Field21c==RpgDialogOfferType && D.StringArray2Dword[1]==RpgDialogEntryKind));
            assert(D.Filter!=0 && (D.StringArray2Dword[0]==0 ||
                (D.StringArray2Count==1 && D.Field21c==RpgDialogOfferType && D.Field220 && D.StringArray2Dword[0]==RpgDialogEntryKind)));
            if (FailBehavior) return 0xffffffffu;
            unsigned long Id=NextBehavior++;Behaviors[Id]=D.StringArray2[0];return Id;
        }
        unsigned FindLocation(unsigned Base, char const* Room) { return Base && strcmp(Room,"Bar")==0 ? 10 : 0; }
        int GetCharacterPlacementByName(unsigned, char const* Name, int& Spot) {
            if (strcmp(Name,"spot_a")==0) { Spot=1; return 0; }
            if (strcmp(Name,"spot_b")==0) { Spot=2; return 0; }
            return -1;
        }
    }
}
struct FBarCharacterDesc {
    unsigned PlayerId=0, RoomId=0, Affiliation=0, Voice=0;
    int Placement=-1, Appearance=0, IndividualName=0;
    TString<32> Role; TString<64> Fidget; ID_String Nickname;
};
struct FBarCharacter : FBarCharacterDesc {
    unsigned CharacterId=0; unsigned long Behavior=0xffffffffu;
    void SetBehavior(unsigned long B) { Behaviors.erase(Behavior);Behavior=B; }
};
typedef std::list<FBarCharacter> FBarCharacterList;
struct FBaseFixture { int Placement; TString<32> Role; };
struct FBaseRoom { unsigned RoomId=10; struct { std::list<FBaseFixture*> Fixtures; } Fixtures; };
struct FBaseRoomState {
    FBarCharacterList Characters;
    std::map<std::pair<unsigned,int>, int> Locks;
    bool HasLock(unsigned Player, int Spot) const { return Locks.count({Player,Spot}) != 0; }
    bool HasCharacter(unsigned Player, int Spot) const {
        for (auto& C : Characters) if (C.PlayerId==Player && C.Placement==Spot) return true;
        return false;
    }
    void AddLock(unsigned Player,int Spot) { ++Locks[{Player,Spot}]; }
    bool FindCharacter(TString<32> const* Role,unsigned Player,FBarCharacterList::iterator* Out) {
        for (auto It=Characters.begin();It!=Characters.end();++It)
            if (It->PlayerId==Player && _stricmp(It->Role.Data,Role->Data)==0) { *Out=It;return true; }
        return false;
    }
};
unsigned NextCharacter = 1;
bool FailCreate = false;
struct FContentBase {
    unsigned BaseId=CreateID("test_base");
    std::map<unsigned,FBaseRoomState> RoomStates;
    std::vector<FBaseRoom> Rooms;
    FBaseRoomState* FindRoomState(unsigned const* Id) { auto It=RoomStates.find(*Id);return It==RoomStates.end()?nullptr:&It->second; }
    FBarCharacterList::iterator AddBarCharacter(FBarCharacterDesc const* Desc) {
        FBarCharacter C; static_cast<FBarCharacterDesc&>(C)=*Desc; C.CharacterId=FailCreate?0:NextCharacter++;
        auto& List=RoomStates[Desc->RoomId].Characters;List.push_front(C);return List.begin();
    }
};
struct FBarScene {
    FContentBase* Base=nullptr;unsigned PlayerId=0,RoomId=0;int SceneId=0;
    std::vector<int> Placements;std::vector<FBarCharacterList::iterator> Characters;
    void Release(void*) {
        auto& Room=Base->RoomStates.at(RoomId);
        for (auto C:Characters) { assert(C->PlayerId==PlayerId);Behaviors.erase(C->Behavior);Room.Characters.erase(C); }
        Characters.clear();
        for (int Spot:Placements) { auto It=Room.Locks.find({PlayerId,Spot});assert(It!=Room.Locks.end());if (--It->second==0) Room.Locks.erase(It); }
        Placements.clear();
    }
};
#define FREELANCER_RPG_WORLD
#include "runtime.inc"
int GenericCalls=0;
unsigned long BuildBarBehavior(FBarCharacter const*) { ++GenericCalls;return 0xffffffffu; }
#include "generic_entry.inc"

int main() {
    for(int I=0;I<3;++I) {
        FRpgDialogModel Model;Model.Choose(I);assert(Model.Node==I+1 && !Model.Done);
        Model.Choose(3);assert(!Model.Done);Model.Choose(0);assert(Model.Node==0);
        Model.Choose(I);Model.Choose(1);assert(Model.Done);
    }
    FRpgDialogModel Exit;Exit.Choose(3);assert(Exit.Done);
    Files["RPG\\contacts.ini"]="[RpgContact]\nnickname=contact\nenabled=true\nbase=test_base\nrtc=RPG\\contact.ini\n";
    std::string const Good="[CharacterEncounter]\nLocation=test_base,Bar\n[Reserve]\nspot=spot_a\n[Char]\nnpc=guard\nactor=rpg_guard\nspot=spot_a\nfidget=scripts\\idle.thn\n[NPC]\nnickname=guard\n";
    Files["RPG\\contact.ini"]=Good;
    FContentBase Base;
    RpgContactsEnter(Base,1); RpgContactsEnter(Base,1); RpgContactsEnter(Base,2);
    auto& Room=Base.RoomStates.at(10);
    assert(Room.Characters.size()==2 && Room.Locks.size()==2);
    assert(strcmp(Room.Characters.front().Fidget.Data,"scripts\\idle.thn")==0);
    RpgContactsLogout(1);assert(Room.Characters.size()==1 && Room.HasLock(2,1));
    RpgContactsEnter(Base,1);assert(Room.Characters.size()==2);
    RpgContactsLeave(Base,1);RpgContactsLeave(Base,1);assert(Room.Characters.size()==1);
    RpgContactsUnload(Base);assert(Room.Characters.empty() && Room.Locks.empty());
    // An existing actor and another controller's reservation survive rejection.
    FBarCharacterDesc Other;Other.PlayerId=1;Other.RoomId=10;Other.Placement=1;Other.Role="other";
    Base.AddBarCharacter(&Other);Room.AddLock(1,1);
    RpgContactsEnter(Base,1);RpgContactsLeave(Base,1);
    assert(Room.Characters.size()==1 && Room.HasLock(1,1));
    Room.Characters.clear();Room.Locks.clear();
    FBaseFixture Fixture;Fixture.Placement=1;Fixture.Role="bartender";
    FBaseRoom Fixed;Fixed.Fixtures.Fixtures.push_back(&Fixture);Base.Rooms.push_back(Fixed);
    RpgContactsEnter(Base,1);assert(Room.Characters.empty());RpgContactsClear();Base.Rooms.clear();
    // Missing reserve, missing NPC and unsupported dialogue must fail before mutation.
    for (auto const& Bad:std::vector<std::string>{
        "[CharacterEncounter]\nLocation=test_base,Bar\n[Char]\nnpc=guard\nactor=rpg_guard\nspot=spot_a\nfidget=scripts\\idle.thn\n[NPC]\nnickname=guard\n",
        Good.substr(0,Good.find("[NPC]")),
        Good+"[CharacterEncounter]\nautoplay=false\n"}) {
        Files["RPG\\contact.ini"]=Bad;RpgContactsEnter(Base,1);
        assert(Room.Characters.empty() && Room.Locks.empty());RpgContactsClear();
    }
    Files["RPG\\contact.ini"]=Good;FailCreate=true;RpgContactsEnter(Base,1);
    assert(Room.Characters.empty() && Room.Locks.empty());RpgContactsClear();FailCreate=false;
    RpgContactsEnter(Base,1);RpgContactsClear();assert(Room.Characters.empty() && Room.Locks.empty());
    // Regression: the real generic entry must leave RPG behavior untouched, including
    // presence-only contacts. Ordinary characters must still use the old builder.
    RpgContactsEnter(Base,1);StartBarCharacterScript(Room.Characters.begin());
    assert(GenericCalls==0);RpgContactsClear();
    Files["RPG\\contact.ini"]=Good+"[CharacterEncounter]\nclick_script=scripts\\generated\\test.thn\nchoices=true\n";
    RpgContactsEnter(Base,1);RpgContactsEnter(Base,2);
    assert(Behaviors.size()==2);
    for(auto It=Room.Characters.begin();It!=Room.Characters.end();++It) {
        auto B=It->Behavior;StartBarCharacterScript(It);StartBarCharacterScript(It);
        assert(It->Behavior==B && Behaviors.at(B)=="scripts\\generated\\test.thn");
    }
    assert(GenericCalls==0);RpgContactsLogout(1);assert(Behaviors.size()==1);
    RpgContactsClear();assert(Behaviors.empty());
    FailBehavior=true;RpgContactsEnter(Base,1);
    assert(Room.Characters.empty() && Room.Locks.empty());RpgContactsClear();FailBehavior=false;
    Files["RPG\\contact.ini"]=Good+"[CharacterEncounter]\nclick_script=..\\bad.thn\n";
    RpgContactsEnter(Base,1);assert(Room.Characters.empty());RpgContactsClear();
    auto Normal=Base.AddBarCharacter(&Other);StartBarCharacterScript(Normal);assert(GenericCalls==1);
    Room.Characters.clear();
    // A parking-only catalog can launch its authored dialogue directly, without a movie.
    Files.erase("RPG\\contacts.ini");
    Files["RPG\\parking_contacts.ini"]="[RpgContact]\nnickname=parking\nenabled=true\nbase=test_base\nrtc=RPG\\contact.ini\n";
    Files["RPG\\contact.ini"]=Good+"[CharacterEncounter]\nchoices=true\n";
    HasDialogTree=true;RpgContactsEnter(Base,1);
    assert(Room.Characters.size()==1 && Behaviors.size()==1);
    assert(Behaviors.begin()->second=="RPG\\dialogue_choice.thn");
    assert(LastContactIcon==RpgContactIconRumor);
    assert(strcmp(RpgContactCursor(LastContactIcon),"talk_rumor")==0);
    RpgContactsEnter(Base,1);assert(Room.Characters.size()==1);
    RpgContactsClear();assert(Room.Characters.empty() && Behaviors.empty());
    Files["RPG\\contact.ini"] += "icon=mission\n";
    RpgContactsEnter(Base,1);
    assert(Room.Characters.size()==1 && LastContactIcon==RpgContactIconMission);
    assert(strcmp(RpgContactCursor(LastContactIcon),"talk_mission")==0);
    RpgContactsClear();
    Files["RPG\\contact.ini"] += "icon=invalid\n";
    RpgContactsEnter(Base,1);
    assert(Room.Characters.empty() && Behaviors.empty());
    RpgContactsClear();
    puts("PASS: four dialogue branches, return/exit, invalid choices; owned two-entry behavior survives room refresh; ordinary NPC unchanged; two-player cleanup and failed behavior rollback");
    puts("PASS: two players, duplicate enter, logout/re-entry, leave/unload/reset, conflicts, invalid RTC and creation rollback");
}
