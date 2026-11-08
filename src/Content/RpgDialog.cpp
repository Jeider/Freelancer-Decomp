#include "RpgDialog.h"
#include "TrainCourier.h"

#ifdef FREELANCER_RPG_WORLD
#include "ContentInternal.h"
#include "ContentPlayerState.h"
#include "BaseDB.h"
#include "common_id.h"
#include "common_ini.h"
#include "common_server.h"
#include "common_server_controller.h"
#include "common_tstring.h"
#include "content.h"
#include "port_config.h"
#include "ship_parking.h"
#include "rpg_fragment_rotation.h"

#include <cstring>
#include <string>
#include <unordered_map>
#include <vector>
#include <windows.h>

namespace
{
struct Choice
{
    unsigned TextIds = 0;
    unsigned FirstWagons = 0;
    unsigned Goto = 0;
    int Action = 0;
    std::string Script;
    std::wstring Ru;
    std::wstring En;
    std::vector<std::string> Fragments;
    unsigned BadReputation = 0, Busy = 0, Failed = 0;
};

struct Node
{
    unsigned Id = 0;
    unsigned TextIds = 0;
    std::wstring Ru;
    std::wstring En;
    std::vector<Choice> Choices;
    std::vector<std::string> Fragments;
    unsigned Escape = 0;
};

struct Dialog
{
    unsigned Id = 0;
    unsigned Start = 0;
    unsigned ParkingBase = 0;
    unsigned ParkingSeller = 0;
    unsigned CourierBase = 0;
    std::unordered_map<unsigned, Node> Nodes;
    std::string SceneGroup;
    std::string SessionScript;
    std::string GestureGroup;
    unsigned ReputationFaction = 0;
    float MinimumReputation = -1;
    bool StrictReputation = false;
};

std::unordered_map<unsigned, Dialog> G_Dialogs;
struct SpokenConversation { unsigned DialogId = 0, NodeId = 0; };
std::unordered_map<unsigned, SpokenConversation> G_Spoken;
std::unordered_map<std::string, RpgFragmentRotation> G_Rotation;

bool ValidGroup(char const* Value) {
    if (!Value || strlen(Value) != 6 || strncmp(Value, "rm", 2)) return false;
    for (int I = 2; I < 6; ++I) if (Value[I] < '0' || Value[I] > '9') return false;
    return true;
}
bool ValidFragment(char const* Value) {
    if (!Value || strlen(Value) != 15 || strncmp(Value, "rm", 2) || strncmp(Value + 6, "_frag", 5)) return false;
    for (int I : {2,3,4,5,11,12,13,14}) if (Value[I] < '0' || Value[I] > '9') return false;
    return true;
}
struct ParkingConversation {
    unsigned DialogId = 0, NodeId = 0;
    ShipParkingStatus Quote;
    bool Confirming = false;
};
std::unordered_map<unsigned, ParkingConversation> G_ParkingConversations;

int ParkingStatus(unsigned Session, Dialog const& Tree, ShipParkingStatus& Status) {
    auto Fn = reinterpret_cast<ShipParkingStatusFn>(GetProcAddress(GetModuleHandleA("Server.dll"), "PlayerShipParking_Status"));
    int const Result = Fn ? Fn(Session, &Status) : ParkingInvalid;
    if (Result) return Result;
    if (Status.BaseId != Tree.ParkingBase) return ParkingWrongBase;
    if (!Tree.ParkingSeller || Status.SellerId != Tree.ParkingSeller) return ParkingNoSeller;
    return ParkingOk;
}

unsigned ParkingResultNode(int Result) {
    return CreateID(Result == ParkingOk ? "parking_success" :
        Result == ParkingBadReputation ? "parking_bad_reputation" :
        Result == ParkingNoMoney ? "parking_no_money" :
        Result == ParkingMaxOwned ? "parking_maximum" : "parking_error");
}

void Replace(std::wstring& Text, wchar_t const* Key, unsigned Value) {
    std::wstring const Replacement = std::to_wstring(Value);
    size_t Pos = 0;
    while ((Pos = Text.find(Key, Pos)) != std::wstring::npos) {
        Text.replace(Pos, wcslen(Key), Replacement);
        Pos += Replacement.size();
    }
}
char G_PendingScript[260] = {};
unsigned G_PendingCourierWagons = 0;
wchar_t G_Text[512] = {};
wchar_t G_ChoiceText[4][192] = {};

std::wstring Widen(char const* Text)
{
    if (Text == nullptr || Text[0] == '\0')
        return {};
    int Count = MultiByteToWideChar(CP_UTF8, 0, Text, -1, nullptr, 0);
    if (Count <= 1)
        Count = MultiByteToWideChar(CP_ACP, 0, Text, -1, nullptr, 0);
    if (Count <= 1)
        return {};
    std::wstring Out(static_cast<size_t>(Count), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, Text, -1, &Out[0], Count);
    if (Out.find(L'\uFFFD') != std::wstring::npos)
        MultiByteToWideChar(CP_ACP, 0, Text, -1, &Out[0], Count);
    Out.resize(wcslen(Out.c_str()));
    return Out;
}

std::wstring const& Localized(std::wstring const& Ru, std::wstring const& En)
{
    bool English = _stricmp(PortLanguage(), "en") == 0;
    return English ? (!En.empty() ? En : Ru) : (!Ru.empty() ? Ru : En);
}

wchar_t const* Show(std::wstring const& Ru, std::wstring const& En)
{
    std::wstring const& Src = Localized(Ru, En);
    if (Src.empty())
        return L"";
    wcsncpy(G_Text, Src.c_str(), 511);
    G_Text[511] = 0;
    return G_Text;
}

Dialog* FindDialog(unsigned Id)
{
    auto It = G_Dialogs.find(Id);
    return It == G_Dialogs.end() ? nullptr : &It->second;
}

Node* FindNode(Dialog& Tree, unsigned Id)
{
    auto It = Tree.Nodes.find(Id);
    return It == Tree.Nodes.end() ? nullptr : &It->second;
}

void ReadNode(INI_Reader& Reader, Dialog& Tree)
{
    Node Item;
    while (Reader.read_value())
    {
        if (Reader.is_value("nickname"))
            Item.Id = CreateID(Reader.get_value_string());
        else if (Reader.is_value("text_ids"))
            Item.TextIds = Reader.get_value_int(0);
        else if (Reader.is_value("text_ru"))
            Item.Ru = Widen(Reader.get_value_string());
        else if (Reader.is_value("text_en"))
            Item.En = Widen(Reader.get_value_string());
        else if (Reader.is_value("fragment") && ValidFragment(Reader.get_value_string()))
            Item.Fragments.push_back(Reader.get_value_string());
        else if (Reader.is_value("escape"))
            Item.Escape = CreateID(Reader.get_value_string());
    }
    if (Item.Id == 0)
        return;
    Node& Slot = Tree.Nodes[Item.Id];
    std::vector<Choice> Kept = Slot.Choices;
    Slot = Item;
    Slot.Choices = Kept;
}

void ReadChoice(INI_Reader& Reader, Dialog& Tree)
{
    unsigned NodeId = 0;
    Choice Item;
    while (Reader.read_value())
    {
        if (Reader.is_value("node"))
            NodeId = CreateID(Reader.get_value_string());
        else if (Reader.is_value("text_ids"))
            Item.TextIds = Reader.get_value_int(0);
        else if (Reader.is_value("first_wagons"))
            Item.FirstWagons = Reader.get_value_int(0);
        else if (Reader.is_value("text_ru"))
            Item.Ru = Widen(Reader.get_value_string());
        else if (Reader.is_value("text_en"))
            Item.En = Widen(Reader.get_value_string());
        else if (Reader.is_value("fragment") && ValidFragment(Reader.get_value_string()))
            Item.Fragments.push_back(Reader.get_value_string());
        else if (Reader.is_value("bad_reputation")) Item.BadReputation = CreateID(Reader.get_value_string());
        else if (Reader.is_value("busy")) Item.Busy = CreateID(Reader.get_value_string());
        else if (Reader.is_value("failed")) Item.Failed = CreateID(Reader.get_value_string());
        else if (Reader.is_value("goto") && !Reader.is_value_empty(0))
            Item.Goto = CreateID(Reader.get_value_string());
        else if (Reader.is_value("action"))
        {
            char const* Action = Reader.get_value_string();
            if (_stricmp(Action, "close") == 0)
                Item.Action = 1;
            else if (_stricmp(Action, "start_script") == 0)
                Item.Action = 2;
            else if (_stricmp(Action, "start_train_courier") == 0)
                Item.Action = 3;
            else if (_stricmp(Action, "quote_parking") == 0)
                Item.Action = 4;
            else if (_stricmp(Action, "buy_parking") == 0)
                Item.Action = 5;
            else if (_stricmp(Action, "check_courier_eligibility") == 0)
                Item.Action = 6;
        }
        else if (Reader.is_value("script"))
            Item.Script = Reader.get_value_string();
    }
    if (NodeId == 0)
        return;
    Node& Owner = Tree.Nodes[NodeId];
    if (Owner.Id == 0)
        Owner.Id = NodeId;
    if (Owner.Choices.size() < 4)
        Owner.Choices.push_back(Item);
}

void ReadDialogHeader(INI_Reader& Reader, Dialog& Tree)
{
    // Inline contact definitions are read on every visit. Do not accumulate choices.
    Tree.Nodes.clear();
    Tree.Start = Tree.ParkingBase = Tree.ParkingSeller = 0;
    Tree.CourierBase = 0;
    Tree.SceneGroup.clear(); Tree.ReputationFaction = 0; Tree.MinimumReputation = -1;
    Tree.StrictReputation = false;
    Tree.SessionScript.clear();
    Tree.GestureGroup.clear();
    bool LocalScene = false;
    while (Reader.read_value())
    {
        if (Reader.is_value("nickname") && Tree.Id == 0)
            Tree.Id = CreateID(Reader.get_value_string());
        else if (Reader.is_value("start"))
            Tree.Start = CreateID(Reader.get_value_string());
        else if (Reader.is_value("parking_base"))
            Tree.ParkingBase = CreateID(Reader.get_value_string());
        else if (Reader.is_value("parking_seller"))
            Tree.ParkingSeller = CreateID(Reader.get_value_string());
        else if (Reader.is_value("courier_base"))
            Tree.CourierBase = CreateID(Reader.get_value_string());
        else if (Reader.is_value("session_group") && ValidGroup(Reader.get_value_string()))
            Tree.GestureGroup = Reader.get_value_string();
        else if (Reader.is_value("scene_group") && ValidGroup(Reader.get_value_string()))
            Tree.SceneGroup = Reader.get_value_string();
        else if (Reader.is_value("local_scene"))
            LocalScene = Reader.get_value_int(0) != 0;
        else if (Reader.is_value("reputation_faction"))
            pub::Reputation::GetReputationGroup(Tree.ReputationFaction, Reader.get_value_string());
        else if (Reader.is_value("minimum_reputation"))
            Tree.MinimumReputation = Reader.get_value_float(0);
        else if (Reader.is_value("reputation_strict"))
            Tree.StrictReputation = Reader.get_value_int(0) != 0;
    }
    if (!Tree.GestureGroup.empty())
        Tree.SessionScript = "SCRIPTS\\RPG\\" + Tree.GestureGroup + "\\conversation.thn";
    else if (LocalScene && !Tree.SceneGroup.empty())
        Tree.SessionScript = "SCRIPTS\\RPG\\" + Tree.SceneGroup + "\\conversation.thn";
}

bool StartScript(char const* Path, unsigned SessionId, bool Courier=false, unsigned FirstWagons=0)
{
    if (Path == nullptr || Path[0] == '\0')
        return false;
    FContentPlayerState* State = FindContentPlayerState(SessionId);
    if (State == nullptr || State->GetGroupLiveMission() != 0)
        return false;
    if (Courier && (!State->GetBaseRecord() ||
        !TrainCourierCanStart(State->GetBaseRecord()->BaseId))) return false;
    strncpy(G_PendingScript, Path, 259);
    G_PendingScript[259] = 0;
    FStoryMissionCreateParms Parms;
    Parms.PlayerId = State->PlayerId;
    Parms.StoryEvents = nullptr;
    G_PendingCourierWagons = Courier ? FirstWagons : 0;
    unsigned int const Controller = pub::Controller::Create(
        "content.dll", Courier ? "TrainCourier" : "ScriptMission", &Parms, pub::Controller::ABOVE_NORMAL);
    G_PendingCourierWagons = 0;
    if (Controller == 0)
        return false;
    ID_String NoVnpc;
    NoVnpc.clear();
    unsigned int const BaseId = State->GetBaseRecord() != nullptr ? State->GetBaseRecord()->BaseId : 0;
    State->JoinMissionAsGroup(Controller, BaseId, &NoVnpc, false, 0);
    pub::Controller::_SendMessage(Controller, pub::Controller::EMessage::MissionStart, nullptr);
    return State->GetGroupLiveMission() == Controller;
}
}

unsigned RpgDialogLoadFile(char const* Path)
{
    INI_Reader Reader;
    if (Path == nullptr || !OpenContentDataIni(Path, &Reader))
        return 0;
    Dialog Tree;
    while (Reader.read_header())
    {
        if (Reader.is_header("Dialog"))
            ReadDialogHeader(Reader, Tree);
        else if (Reader.is_header("DialogNode"))
            ReadNode(Reader, Tree);
        else if (Reader.is_header("DialogChoice"))
            ReadChoice(Reader, Tree);
    }
    if (Tree.Id == 0 || Tree.Nodes.empty())
        return 0;
    if (Tree.Start == 0)
        Tree.Start = Tree.Nodes.begin()->second.Id;
    G_Dialogs[Tree.Id] = Tree;
    return Tree.Id;
}

bool RpgDialogConsumeHeader(INI_Reader& Reader, unsigned DialogId)
{
    if (DialogId == 0)
        return false;
    Dialog& Tree = G_Dialogs[DialogId];
    Tree.Id = DialogId;
    if (Reader.is_header("Dialog"))
    {
        ReadDialogHeader(Reader, Tree);
        Tree.Id = DialogId;
        return true;
    }
    if (Reader.is_header("DialogNode"))
    {
        ReadNode(Reader, Tree);
        return true;
    }
    if (Reader.is_header("DialogChoice"))
    {
        ReadChoice(Reader, Tree);
        return true;
    }
    return false;
}

extern "C" unsigned __cdecl RpgDialogStart(unsigned DialogId)
{
    Dialog* Tree = FindDialog(DialogId);
    if (Tree == nullptr)
        return 0;
    if (Tree->Start == 0 && !Tree->Nodes.empty())
        Tree->Start = Tree->Nodes.begin()->second.Id;
    return Tree->Start;
}

extern "C" unsigned __cdecl RpgDialogBeginSession(unsigned DialogId, unsigned SessionId)
{
    G_ParkingConversations.erase(SessionId);
    G_Spoken.erase(SessionId);
    Dialog* Tree = FindDialog(DialogId);
    if (!Tree) return 0;
    unsigned const Start = RpgDialogStart(DialogId);
    if (!Tree->SceneGroup.empty()) G_Spoken[SessionId] = {DialogId, Start};
    if (Tree->ParkingBase || Tree->ParkingSeller) {
        ShipParkingStatus Status;
        if (ParkingStatus(SessionId, *Tree, Status) != ParkingOk) {
            G_Spoken.erase(SessionId);
            return 0;
        }
        ParkingConversation Conversation;
        Conversation.DialogId = DialogId;
        Conversation.NodeId = Start;
        G_ParkingConversations[SessionId] = Conversation;
    }
    return Start;
}

extern "C" void __cdecl RpgDialogEndSession(unsigned SessionId)
{
    G_ParkingConversations.erase(SessionId);
    G_Spoken.erase(SessionId);
}

extern "C" char const* __cdecl RpgDialogSceneGroup(unsigned DialogId) {
    Dialog* Tree = FindDialog(DialogId);
    return Tree ? Tree->SceneGroup.c_str() : "";
}
char const* RpgDialogSessionScript(unsigned DialogId) {
    Dialog* Tree = FindDialog(DialogId);
    return Tree && !Tree->SessionScript.empty() ? Tree->SessionScript.c_str() : "SCRIPTS\\RPG\\conversation.thn";
}
extern "C" char const* __cdecl RpgDialogFragment(unsigned DialogId, unsigned NodeId, int Index, unsigned SessionId) {
    static std::string Result;
    Result.clear();
    Dialog* Tree = FindDialog(DialogId);
    Node* Item = Tree ? FindNode(*Tree, NodeId) : nullptr;
    auto It = G_Spoken.find(SessionId);
    if (!Item || Tree->SceneGroup.empty() || It == G_Spoken.end() ||
        It->second.DialogId != DialogId || It->second.NodeId != NodeId || Index < -1 ||
        Index >= static_cast<int>(Item->Choices.size())) return "";
    auto const& Pool = Index < 0 ? Item->Fragments : Item->Choices[Index].Fragments;
    if (Pool.empty()) return "";
    for (auto const& Id : Pool) if (Id.compare(0, 6, Tree->SceneGroup)) return "";
    std::string const Key = std::to_string(SessionId) + ":" + std::to_string(DialogId) + ":" + Pool.front();
    Result = G_Rotation[Key].Next(Pool);
    return Result.c_str();
}
extern "C" unsigned __cdecl RpgDialogEscape(unsigned DialogId, unsigned NodeId, unsigned SessionId) {
    Dialog* Tree = FindDialog(DialogId);
    Node* Item = Tree ? FindNode(*Tree, NodeId) : nullptr;
    auto It = G_Spoken.find(SessionId);
    if (!Item || It == G_Spoken.end() || It->second.DialogId != DialogId || It->second.NodeId != NodeId) return 0;
    It->second.NodeId = Item->Escape;
    return Item->Escape;
}

extern "C" wchar_t const* __cdecl RpgDialogRenderText(unsigned DialogId, unsigned NodeId, int ChoiceIndex, unsigned SessionId)
{
    Dialog* Tree = FindDialog(DialogId);
    Node* Item = Tree ? FindNode(*Tree, NodeId) : nullptr;
    if (!Item || ChoiceIndex < -1 || ChoiceIndex >= static_cast<int>(Item->Choices.size())) return L"";
    std::wstring Text = ChoiceIndex < 0 ? Localized(Item->Ru, Item->En) :
        Localized(Item->Choices[ChoiceIndex].Ru, Item->Choices[ChoiceIndex].En);
    if (Tree->ParkingBase) {
        ShipParkingStatus Status;
        if (ParkingStatus(SessionId, *Tree, Status) != ParkingOk) return L"";
        auto const It = G_ParkingConversations.find(SessionId);
        if (It != G_ParkingConversations.end() && It->second.DialogId == DialogId && It->second.Confirming)
            Status = It->second.Quote;
        Replace(Text, L"{owned}", Status.Owned);
        Replace(Text, L"{used}", Status.Used);
        Replace(Text, L"{maximum}", Status.Maximum);
        Replace(Text, L"{price}", static_cast<unsigned>(Status.Price));
    }
    wcsncpy(G_Text, Text.c_str(), 511);
    G_Text[511] = 0;
    return G_Text;
}

extern "C" int __cdecl RpgDialogChoiceCount(unsigned DialogId, unsigned NodeId)
{
    Dialog* Tree = FindDialog(DialogId);
    if (Tree == nullptr)
        return 0;
    Node* Item = FindNode(*Tree, NodeId);
    if (Item == nullptr)
        return 0;
    int Count = static_cast<int>(Item->Choices.size());
    return Count > 4 ? 4 : Count;
}

extern "C" wchar_t const* __cdecl RpgDialogNodeText(unsigned DialogId, unsigned NodeId)
{
    Dialog* Tree = FindDialog(DialogId);
    if (Tree == nullptr)
        return L"";
    Node* Item = FindNode(*Tree, NodeId);
    return Item == nullptr ? L"" : Show(Item->Ru, Item->En);
}

extern "C" unsigned __cdecl RpgDialogNodeTextIds(unsigned DialogId, unsigned NodeId)
{
    Dialog* Tree = FindDialog(DialogId);
    Node* Item = Tree == nullptr ? nullptr : FindNode(*Tree, NodeId);
    return Item == nullptr ? 0 : Item->TextIds;
}

extern "C" unsigned __cdecl RpgDialogChoiceTextIds(unsigned DialogId, unsigned NodeId, int Index)
{
    Dialog* Tree = FindDialog(DialogId);
    Node* Item = Tree == nullptr ? nullptr : FindNode(*Tree, NodeId);
    return Item == nullptr || Index < 0 || Index >= static_cast<int>(Item->Choices.size())
        ? 0 : Item->Choices[Index].TextIds;
}

extern "C" wchar_t const* __cdecl RpgDialogChoiceText(unsigned DialogId, unsigned NodeId, int Index)
{
    if (Index < 0 || Index > 3)
        return L"";
    Dialog* Tree = FindDialog(DialogId);
    Node* Item = Tree == nullptr ? nullptr : FindNode(*Tree, NodeId);
    if (Item == nullptr || Index >= static_cast<int>(Item->Choices.size()))
        return L"";
    std::wstring const& Src = Localized(Item->Choices[Index].Ru, Item->Choices[Index].En);
    wcsncpy(G_ChoiceText[Index], Src.c_str(), 191);
    G_ChoiceText[Index][191] = 0;
    return G_ChoiceText[Index];
}

extern "C" unsigned __cdecl RpgDialogChoose(unsigned DialogId, unsigned NodeId, int Index,
                                        unsigned SessionId)
{
    Dialog* Tree = FindDialog(DialogId);
    if (Tree == nullptr)
        return 0;
    Node* Item = FindNode(*Tree, NodeId);
    if (Item == nullptr || Index < 0 || Index >= static_cast<int>(Item->Choices.size()))
        return 0;
    Choice const& Pick = Item->Choices[Index];
    if (!Tree->SceneGroup.empty() && !Tree->ParkingBase && !Tree->ParkingSeller) {
        auto It = G_Spoken.find(SessionId);
        if (It == G_Spoken.end() || It->second.DialogId != DialogId || It->second.NodeId != NodeId) return 0;
        It->second.NodeId = 0; // consume before a mission action; repeated UI events cannot issue twice
        unsigned Next = Pick.Goto;
        if (Pick.Action == 3 || Pick.Action == 6) {
            auto* State = FindContentPlayerState(SessionId);
            if (!State || !State->GetBaseRecord() ||
                (Tree->CourierBase && Tree->CourierBase != State->GetBaseRecord()->BaseId)) Next = Pick.Failed;
            else if (State->GetGroupLiveMission()) Next = Pick.Busy;
            else {
                int Rep = -1; float Attitude = 0;
                bool const Check = Tree->ReputationFaction != 0;
                if (Check && (pub::Player::GetRep(SessionId, Rep) ||
                    pub::Reputation::GetReputation(Rep, Tree->ReputationFaction, Attitude))) Next = Pick.Failed;
                else if (Check && (Tree->StrictReputation ? !(Attitude > Tree->MinimumReputation) :
                                   !(Attitude >= Tree->MinimumReputation))) Next = Pick.BadReputation;
                else if (Pick.Action == 3 && !StartScript("Missions\\TrainCourier\\courier.ini", SessionId, true, Pick.FirstWagons)) Next = Pick.Failed;
            }
        }
        // Controller callbacks may end a session; do not retain an iterator across them.
        auto Current = G_Spoken.find(SessionId);
        if (Current == G_Spoken.end() || Current->second.DialogId != DialogId) return 0;
        Current->second.NodeId = Next;
        return Next;
    }
    if (Tree->ParkingBase || Tree->ParkingSeller || Pick.Action == 4 || Pick.Action == 5) {
        auto It = G_ParkingConversations.find(SessionId);
        if (It == G_ParkingConversations.end() || It->second.DialogId != DialogId || It->second.NodeId != NodeId)
            return 0;
        ParkingConversation& Conversation = It->second;
        ShipParkingStatus Status;
        int Result = ParkingStatus(SessionId, *Tree, Status);
        unsigned Next = Pick.Goto;
        if (Result) { RpgDialogEndSession(SessionId); return 0; }
        if (Pick.Action == 4) {
            Conversation.Confirming = false;
            auto CanBuy = reinterpret_cast<ShipParkingCanBuyFn>(GetProcAddress(GetModuleHandleA("Server.dll"), "PlayerShipParking_CanBuy"));
            Result = CanBuy ? CanBuy(SessionId) : ParkingInvalid;
            if (Result) Next = ParkingResultNode(Result);
            else if (Status.Owned >= Status.Maximum) Next = ParkingResultNode(ParkingMaxOwned);
            else { Conversation.Quote = Status; Conversation.Confirming = true; }
        } else if (Pick.Action == 5) {
            if (!Conversation.Confirming) return 0;
            Conversation.Confirming = false; // consume before calling the cash mutation
            auto Buy = reinterpret_cast<ShipParkingBuyFn>(GetProcAddress(GetModuleHandleA("Server.dll"), "PlayerShipParking_Buy"));
            ShipParkingStatus const& Quote = Conversation.Quote;
            Result = Buy ? Buy(SessionId, Quote.BaseId, Quote.SellerId, Quote.Owned, Quote.Price) : ParkingInvalid;
            Next = ParkingResultNode(Result);
        } else Conversation.Confirming = false;
        if (Pick.Action == 1 || !Next) { RpgDialogEndSession(SessionId); return 0; }
        Conversation.NodeId = Next;
        // Voiced parking uses the same authoritative quote/buy transaction as text
        // parking. Keep its speech cursor in step with the transaction result.
        auto Spoken = G_Spoken.find(SessionId);
        if (Spoken != G_Spoken.end() && Spoken->second.DialogId == DialogId)
            Spoken->second.NodeId = Next;
        return Next;
    }
    if (Pick.Action == 2)
        StartScript(Pick.Script.c_str(), SessionId);
    else if (Pick.Action == 3)
        StartScript("Missions\\TrainCourier\\courier.ini", SessionId, true, Pick.FirstWagons);
    if (Pick.Action == 1 || Pick.Goto == 0)
        return 0;
    return Pick.Goto;
}

char const* RpgPendingScript()
{
    return G_PendingScript;
}
unsigned RpgPendingCourierWagons() { return G_PendingCourierWagons; }
extern "C" char const* __cdecl RpgDialogGestureGroup(unsigned DialogId) {
    auto* Tree = FindDialog(DialogId);
    return Tree ? (Tree->GestureGroup.empty() ? Tree->SceneGroup.c_str() : Tree->GestureGroup.c_str()) : "";
}
#else
extern "C" char const* __cdecl RpgDialogGestureGroup(unsigned) { return ""; }
char const* RpgDialogSessionScript(unsigned) { return ""; }
char const* RpgDialogSceneGroup(unsigned) { return ""; }
char const* RpgDialogFragment(unsigned, unsigned, int, unsigned) { return ""; }
unsigned RpgDialogEscape(unsigned, unsigned, unsigned) { return 0; }
unsigned RpgDialogBeginSession(unsigned, unsigned) { return 0; }
void RpgDialogEndSession(unsigned) {}
wchar_t const* RpgDialogRenderText(unsigned, unsigned, int, unsigned) { return L""; }
unsigned RpgPendingCourierWagons() { return 0; }
unsigned RpgDialogNodeTextIds(unsigned, unsigned) { return 0; }
unsigned RpgDialogChoiceTextIds(unsigned, unsigned, int) { return 0; }
unsigned RpgDialogLoadFile(char const*) { return 0; }
bool RpgDialogConsumeHeader(INI_Reader&, unsigned) { return false; }
unsigned RpgDialogStart(unsigned) { return 0; }
int RpgDialogChoiceCount(unsigned, unsigned) { return 0; }
wchar_t const* RpgDialogNodeText(unsigned, unsigned) { return L""; }
wchar_t const* RpgDialogChoiceText(unsigned, unsigned, int) { return L""; }
unsigned RpgDialogChoose(unsigned, unsigned, int, unsigned) { return 0; }
char const* RpgPendingScript() { return ""; }
#endif
