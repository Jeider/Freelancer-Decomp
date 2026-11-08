#include "RpgContacts.h"

#ifdef FREELANCER_RPG_WORLD
#include "BaseDB.h"
#include "ContentInternal.h"
#include "common_server.h"
#include "common_iface.h"
#include "rpg_dialog_protocol.h"
#include "RpgDialog.h"

#include <algorithm>
#include <cstring>
#include <set>
#include <string>
#include <utility>

namespace
{
    // Only owned characters/locks live here. A visit never owns another controller's NPC.
    typedef std::pair<FContentBase*, unsigned int> VisitKey;
    std::map<VisitKey, std::vector<FBarScene>> Visits;

    struct Actor
    {
        std::string Npc, Role, Spot, Fidget;
    };

    void Report(char const* Path, char const* Reason)
    {
        FDUMP(0x100001, "RPG contact %s: %s\n", Path, Reason);
    }

    bool DataPath(std::string const& Path)
    {
        return !Path.empty() && Path.size() < 240 && Path[0] != '/' && Path[0] != '\\' &&
            Path.find(':') == std::string::npos && Path.find("..") == std::string::npos;
    }

    // Presence-only subset of RTC, with local [NPC] descriptions. Deliberately does not
    // insert into GSpecificNpcs: StoryLauncher owns and clears that global table.
    bool LoadPresence(FContentBase& Base, unsigned int PlayerId, char const* Path,
                      FBarScene& Scene)
    {
        INI_Reader Reader;
        if (!OpenContentDataIni(Path, &Reader))
            return false;
        FNpcCharacterDescMap Npcs;
        std::vector<Actor> Actors;
        std::vector<std::string> Reserves;
        std::string BaseName, RoomName, ClickScript;
        bool Choices = false;
        bool ScriptOffer = false;
        unsigned ContactIcon = RpgContactIconRumor;
        std::string DialogFile;
        unsigned DialogId = CreateID(Path);
        bool Valid = true;
        while (Reader.read_header())
        {
            if (Reader.is_header("NPC"))
            {
                FNpcCharacterDesc Npc;
                ID_String Name;
                Name.clear();
                if (!LoadNpcCharacterDesc(&Name, &Npc, &Reader) ||
                    !Npcs.insert(std::make_pair(Name.Id, Npc)).second)
                    Valid = false;
            }
            else if (Reader.is_header("CharacterEncounter"))
            {
                while (Reader.read_value())
                {
                    if (Reader.is_value("Location") && BaseName.empty())
                    {
                        BaseName = Reader.get_value_string(0);
                        RoomName = Reader.get_value_string(1);
                    }
                    else if (Reader.is_value("click_script") && ClickScript.empty())
                    {
                        ClickScript = Reader.get_value_string();
                        if (!DataPath(ClickScript)) Valid = false;
                    }
                    else if (Reader.is_value("choices")) Choices = Reader.get_value_bool(0);
                    else if (Reader.is_value("script_offer")) ScriptOffer = Reader.get_value_bool(0);
                    else if (Reader.is_value("icon"))
                    {
                        char const* Icon = Reader.get_value_string();
                        if (_stricmp(Icon, "mission") == 0) ContactIcon = RpgContactIconMission;
                        else if (_stricmp(Icon, "rumor") == 0) ContactIcon = RpgContactIconRumor;
                        else Valid = false;
                    }
                    else if (Reader.is_value("dialog")) DialogFile = Reader.get_value_string();
                    else
                        Valid = false; // Dialog actions/autoplay need a future conversation owner.
                }
            }
            else if (Reader.is_header("Reserve"))
            {
                while (Reader.read_value())
                {
                    if (Reader.is_value("spot"))
                        Reserves.push_back(Reader.get_value_string());
                    else
                        Valid = false;
                }
            }
            else if (Reader.is_header("Char"))
            {
                Actor Item;
                while (Reader.read_value())
                {
                    if (Reader.is_value("npc")) Item.Npc = Reader.get_value_string();
                    else if (Reader.is_value("actor")) Item.Role = Reader.get_value_string();
                    else if (Reader.is_value("spot")) Item.Spot = Reader.get_value_string();
                    else if (Reader.is_value("fidget")) Item.Fidget = Reader.get_value_string();
                    else Valid = false;
                }
                Actors.push_back(Item);
            }
            else if (!RpgDialogConsumeHeader(Reader, DialogId))
                Valid = false;
        }
        if (!DialogFile.empty())
            DialogId = RpgDialogLoadFile(DialogFile.c_str());
        unsigned int BaseId = 0;
        pub::GetBaseID(BaseId, BaseName.c_str());
        unsigned int const RoomId = pub::GF::FindLocation(BaseId, RoomName.c_str());
        if (!Valid || (Choices && ClickScript.empty() && !RpgDialogStart(DialogId)) || BaseId != Base.BaseId || RoomId == 0 || Actors.empty())
            return false;

        // Resolve and validate everything before changing the room.
        std::set<int> Spots;
        for (std::string const& Name : Reserves)
        {
            int Spot = -1;
            if (pub::GF::GetCharacterPlacementByName(RoomId, Name.c_str(), Spot) != 0 ||
                Spot < 0 || !Spots.insert(Spot).second)
                return false;
        }
        std::set<int> ActorSpots;
        std::set<unsigned int> Roles;
        std::vector<FBarCharacterDesc> Descriptions;
        FBaseRoomState* State = Base.FindRoomState(&RoomId);
        for (Actor const& Item : Actors)
        {
            auto const Npc = Npcs.find(CreateID(Item.Npc.c_str()));
            int Spot = -1;
            if (Npc == Npcs.end() || Item.Role.empty() || Item.Role.size() >= 32 ||
                Item.Fidget.size() >= 64 || !DataPath(Item.Fidget) ||
                !Roles.insert(CreateID(Item.Role.c_str())).second ||
                pub::GF::GetCharacterPlacementByName(RoomId, Item.Spot.c_str(), Spot) != 0 ||
                Spot < 0 || Spots.count(Spot) == 0 || !ActorSpots.insert(Spot).second)
                return false;
            FBarCharacterDesc Desc;
            Desc.PlayerId = PlayerId;
            Desc.RoomId = RoomId;
            Desc.Placement = Spot;
            Desc.Role = Item.Role.c_str();
            Desc.Fidget = Item.Fidget.c_str();
            Desc.Appearance = Npc->second.Appearance;
            Desc.Affiliation = Npc->second.Affiliation;
            Desc.IndividualName = Npc->second.IndividualName;
            Desc.Voice = Npc->second.Voice;
            Desc.Nickname = Npc->second.Nickname;
            FBarCharacterList::iterator Existing;
            if (State && State->FindCharacter(&Desc.Role, PlayerId, &Existing))
                return false;
            // Never suppress an authored fixture or borrow its role.
            for (FBaseRoom const& Room : Base.Rooms)
                if (Room.RoomId == RoomId)
                    for (FBaseFixture const* Fixture : Room.Fixtures.Fixtures)
                        if (Spots.count(Fixture->Placement) ||
                            _stricmp(Fixture->Role.Data, Item.Role.c_str()) == 0)
                            return false;
            Descriptions.push_back(Desc);
        }
        for (int Spot : Spots)
            if (State && (State->HasLock(PlayerId, Spot) || State->HasCharacter(PlayerId, Spot)))
                return false;

        Scene.Base = &Base;
        Scene.PlayerId = PlayerId;
        Scene.RoomId = RoomId;
        Scene.SceneId = -1;
        Scene.Placements.assign(Spots.begin(), Spots.end());
        FBaseRoomState& RoomState = Base.RoomStates[RoomId];
        for (int Spot : Scene.Placements)
            RoomState.AddLock(PlayerId, Spot);
        for (FBarCharacterDesc const& Desc : Descriptions)
        {
            auto Character = Base.AddBarCharacter(&Desc);
            Scene.Characters.push_back(Character);
            if (Character->CharacterId == 0)
            {
                Scene.Release(nullptr);
                return false;
            }
        }
        if (!ClickScript.empty() || Choices)
        {
            // A self-contained THN at its authored origin, without generic bar scripts,
            // room actor bindings, mission decisions or a Story RTCDone sequence id.
            CharacterBehaviorDescription Behavior;
            Behavior.Field00 = static_cast<int>(RoomId);
            Behavior.Field04 = 0;
            Behavior.Field05 = 0;
            Behavior.Field06 = 1;
            Behavior.Field10 = 0;
            Behavior.Filter = PlayerId;
            Behavior.StringArray2Count = 0;
            if (!ClickScript.empty()) {
                Behavior.StringArray2[0] = ClickScript.c_str();
                Behavior.StringArray2Dword[0] = 0;
                Behavior.StringArray2Count = 1;
            }
            if (Choices)
            {
                Behavior.Field21c = RpgDialogOfferType;
                if (RpgDialogStart(DialogId) == 0)
                    DialogId = 0;
                Behavior.Field220 = DialogId;
                Behavior.Field224 = ContactIcon;
                unsigned const Entry = Behavior.StringArray2Count;
                char const* Group = RpgDialogSceneGroup(DialogId);
                if (Group && *Group) Behavior.Field10 = 1; // Bind the clicked NPC as Mirror.First().
                Behavior.StringArray2[Entry] = Group && *Group
                    ? RpgDialogSessionScript(DialogId) : "RPG\\dialogue_choice.thn";
                Behavior.StringArray2Dword[Entry] =
                    ScriptOffer ? RpgScriptOfferEntryKind : RpgDialogEntryKind;
                ++Behavior.StringArray2Count;
            }
            unsigned long const Handle = pub::GF::CharacterBehaviorCreate(Behavior);
            if (Handle == 0xffffffffu)
            {
                Scene.Release(nullptr);
                return false;
            }
            Scene.Characters.front()->SetBehavior(Handle);
        }
        return true;
    }

    void Release(std::vector<FBarScene>& Scenes)
    {
        for (FBarScene& Scene : Scenes)
            Scene.Release(nullptr);
    }
}

bool RpgContactsOwns(FBarCharacter const* Character)
{
    for (auto const& Visit : Visits)
        for (auto const& Scene : Visit.second)
            for (auto const& Owned : Scene.Characters)
                if (&*Owned == Character) return true;
    return false;
}

void RpgContactsEnter(FContentBase& Base, unsigned int PlayerId)
{
    VisitKey const Key(&Base, PlayerId);
    if (Visits.find(Key) != Visits.end())
        return;
    auto& Scenes = Visits[Key];
    std::set<unsigned int> Seen;
    // Parking has its own generated catalog; preserve authored mission contacts.
    for (char const* Catalog : {"RPG\\contacts.ini", "RPG\\parking_contacts.ini", "RPG\\courier_contacts.ini"}) {
    INI_Reader Reader;
    if (!OpenContentDataIni(Catalog, &Reader)) continue;
    while (Reader.read_header())
    {
        if (!Reader.is_header("RpgContact"))
            continue;
        std::string Name, BaseName, Rtc;
        bool Enabled = false;
        while (Reader.read_value())
        {
            if (Reader.is_value("nickname")) Name = Reader.get_value_string();
            else if (Reader.is_value("base")) BaseName = Reader.get_value_string();
            else if (Reader.is_value("rtc")) Rtc = Reader.get_value_string();
            else if (Reader.is_value("enabled")) Enabled = Reader.get_value_bool(0);
        }
        if (!Enabled || BaseName.empty() || CreateID(BaseName.c_str()) != Base.BaseId)
            continue;
        if (Name.empty() || !DataPath(Rtc) || !Seen.insert(CreateID(Name.c_str())).second)
        {
            Report(Name.c_str(), "invalid/duplicate catalog entry");
            continue;
        }
        FBarScene Scene = {};
        if (LoadPresence(Base, PlayerId, Rtc.c_str(), Scene))
            Scenes.push_back(Scene);
        else
            Report(Rtc.c_str(), "invalid presence RTC or occupied placement; skipped");
    }
    }
}

void RpgContactsLeave(FContentBase& Base, unsigned int PlayerId)
{
    auto It = Visits.find(VisitKey(&Base, PlayerId));
    if (It == Visits.end()) return;
    Release(It->second);
    Visits.erase(It);
}

void RpgContactsLogout(unsigned int PlayerId)
{
    for (auto It = Visits.begin(); It != Visits.end();)
        if (It->first.second == PlayerId)
        {
            Release(It->second);
            It = Visits.erase(It);
        }
        else ++It;
}

void RpgContactsUnload(FContentBase& Base)
{
    for (auto It = Visits.begin(); It != Visits.end();)
        if (It->first.first == &Base)
        {
            Release(It->second);
            It = Visits.erase(It);
        }
        else ++It;
}

void RpgContactsClear()
{
    for (auto& Visit : Visits) Release(Visit.second);
    Visits.clear();
}
#endif
