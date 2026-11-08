#include "common_interior_profiles.h"
#ifdef FREELANCER_BASE_INTERIORS
#include "common_archetype.h"
#include "common_goods.h"
#include "common_id.h"
#include "common_ini.h"
#include "common_misc.h"
#include "DALib.h"
#include <map>
#include <set>
#include <string>
#include <vector>

namespace BaseInteriors
{
    namespace
    {
        struct Selector
        {
            unsigned Types = 0;
            std::set<unsigned> Ships;
            bool Valid = true;
            bool Empty() const { return Types == 0 && Ships.empty(); }
            bool Matches(unsigned ShipId) const
            {
                if (!Valid || !ShipId) return false;
                if (Empty() || Ships.count(ShipId)) return true;
                auto* Ship = Archetype::GetShip(ShipId);
                return Ship && (Ship->ObjectType & Types) != 0;
            }
            bool Read(INI_Reader& Reader)
            {
                if (Reader.is_value("ship_type"))
                {
                    for (unsigned i = 0; i < Reader.get_num_parameters(); ++i)
                    {
                        unsigned Type = DecodeType(Reader.get_value_string(i));
                        if ((Type & 0x7f0000u) == 0)
                        {
                            FDUMP(0x100002, "Interior: invalid ship_type in %s\n", Reader.get_file_name());
                            Valid = false;
                        }
                        Types |= Type;
                    }
                    return true;
                }
                if (Reader.is_value("ship"))
                {
                    for (unsigned i = 0; i < Reader.get_num_parameters(); ++i)
                        Ships.insert(CreateID(Reader.get_value_string(i)));
                    return true;
                }
                return false;
            }
        };
        struct Profile
        {
            unsigned Id = 0;
            unsigned Start = 0;
            Selector Ships;
            std::map<unsigned, std::string> Rooms;
            std::set<unsigned> DisabledServices;
            bool Valid = true;
        };
        struct Placement
        {
            Selector Ships;
            bool Shadow = true;
        };
        struct Registry
        {
            std::map<unsigned, std::vector<Profile>> Bases;
            std::set<RoomData const*> NoCharacters;
            std::map<ShipPlaceInfo const*, Placement> Placements;
        };
        Registry& Data()
        {
            // The registry must remain available to RoomData/BaseData destructors
            // in other translation units during DLL shutdown. Entries are erased
            // by their owning objects; the small registry shell is process-lived.
            static Registry* Store = new Registry();
            return *Store;
        }
        Profile const* Select(unsigned Base, unsigned Ship)
        {
            auto It = Data().Bases.find(Base);
            if (It != Data().Bases.end())
                for (auto const& Profile : It->second)
                    if (Profile.Valid && Profile.Ships.Matches(Ship)) return &Profile;
            return nullptr;
        }
    }

    void ResetBase(unsigned Base) { Data().Bases.erase(Base); }

    void ReadProfile(unsigned Base, INI_Reader& Reader)
    {
        Profile Profile;
        while (Reader.read_value())
        {
            if (Profile.Ships.Read(Reader)) continue;
            if (Reader.is_value("nickname"))
                Profile.Id = CreateID(Reader.get_value_string());
            else if (Reader.is_value("start_room"))
                Profile.Start = MakeLocationID(Base, Reader.get_value_string());
            else if (Reader.is_value("room"))
            {
                unsigned Room = MakeLocationID(Base, Reader.get_value_string(0));
                std::string File;
                if (Reader.get_num_parameters() >= 2) File = Reader.get_value_string(1);
                if (!Profile.Rooms.emplace(Room, File).second) Profile.Valid = false;
            }
            else if (Reader.is_value("disable_service"))
                for (unsigned i = 0; i < Reader.get_num_parameters(); ++i)
                    Profile.DisabledServices.insert(CreateID(Reader.get_value_string(i)));
            else
            {
                FDUMP(0x100002, "Interior: unknown profile key in %s\n", Reader.get_file_name());
                Profile.Valid = false;
            }
        }
        if (!Profile.Id || Profile.Ships.Empty() || !Profile.Ships.Valid || Profile.Rooms.empty())
            Profile.Valid = false;
        Data().Bases[Base].push_back(Profile);
    }

    void ValidateProfiles(BaseData const& Base)
    {
        auto It = Data().Bases.find(Base.BaseId);
        if (It == Data().Bases.end()) return;
        std::set<unsigned> Names;
        for (auto& Profile : It->second)
        {
            if (!Names.insert(Profile.Id).second) Profile.Valid = false;
            if (!Profile.Start) Profile.Start = Base.StartRoomId;
            if (!Profile.Rooms.count(Profile.Start)) Profile.Valid = false;
            for (auto const& Entry : Profile.Rooms)
            {
                bool Known = false;
                for (auto* Room : Base.Rooms) Known |= Room && Room->RoomId == Entry.first;
                if (!Known) Profile.Valid = false;
                if (!Entry.second.empty())
                {
                    char Path[1024];
                    GetFileSysPath(Path, Entry.second.c_str(), DALib::Data);
                    INI_Reader Check;
                    if (!Check.open(Path, false)) Profile.Valid = false;
                    else Check.close();
                }
            }
            if (!Profile.Valid)
                FDUMP(0x100002, "Interior: ignoring invalid profile %08X on base %08X\n", Profile.Id, Base.BaseId);
        }
    }

    unsigned ProfileId(unsigned Base, unsigned Ship)
    {
        auto* Profile = Select(Base, Ship);
        return Profile ? Profile->Id : 0;
    }
    char const* RoomFile(unsigned Base, unsigned Room, unsigned Ship)
    {
        auto* Profile = Select(Base, Ship);
        if (!Profile) return nullptr;
        auto It = Profile->Rooms.find(Room);
        return It == Profile->Rooms.end() || It->second.empty() ? nullptr : It->second.c_str();
    }
    bool RoomAllowed(unsigned Base, unsigned Room, unsigned Ship)
    {
        auto* Profile = Select(Base, Ship);
        return !Profile || Profile->Rooms.count(Room) != 0;
    }
    unsigned ResolveRoom(unsigned Base, unsigned Room, unsigned Ship)
    {
        auto* Profile = Select(Base, Ship);
        return Profile && (!Room || !Profile->Rooms.count(Room)) ? Profile->Start : Room;
    }
    bool ServiceAllowed(unsigned Base, unsigned Ship, char const* Service)
    {
        auto* Profile = Select(Base, Ship);
        return !Profile || !Profile->DisabledServices.count(CreateID(Service));
    }

    bool HasCharacters(RoomData const* Room) { return !Data().NoCharacters.count(Room); }
    void SetCharacters(RoomData const* Room, bool Enabled)
    {
        if (Enabled) Data().NoCharacters.erase(Room);
        else Data().NoCharacters.insert(Room);
    }
    void ForgetRoom(RoomData const* Room) { Data().NoCharacters.erase(Room); }
    bool ReadPlacementValue(ShipPlaceInfo const* Place, INI_Reader& Reader)
    {
        if (Reader.is_value("shadow"))
        {
            Data().Placements[Place].Shadow = Reader.get_value_bool(0);
            return true;
        }
        if (Reader.is_value("ship_type") || Reader.is_value("ship"))
            return Data().Placements[Place].Ships.Read(Reader);
        return false;
    }
    void ForgetPlacement(ShipPlaceInfo const* Place) { Data().Placements.erase(Place); }
    bool PlacementMatches(ShipPlaceInfo const* Place, unsigned Ship)
    {
        auto It = Data().Placements.find(Place);
        return It == Data().Placements.end() || It->second.Ships.Matches(Ship);
    }
    bool PlacementShadow(ShipPlaceInfo const* Place)
    {
        auto It = Data().Placements.find(Place);
        return It == Data().Placements.end() || It->second.Shadow;
    }
}
#endif // FREELANCER_BASE_INTERIORS: shelved experiment, disabled by default.
