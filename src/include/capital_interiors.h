#pragma once

// Archived first prototype; not used by production source. See
// tools/capital_interiors/README.txt before reusing this implementation.

// Optional base interiors for ships that use external moorings. Shared by the
// client and server; keep the retail BaseData/RoomData/Ship layouts unchanged.
#include "common_archetype.h"
#include "common_id.h"
#include "common_ini.h"
#include "common_misc.h"
#include "DALib.h"
#include <map>
#include <string>

namespace CapitalInteriors
{
    struct BaseProfile
    {
        std::map<unsigned, std::string> Rooms;
    };

    inline std::map<unsigned, BaseProfile> const& Profiles()
    {
        static std::map<unsigned, BaseProfile> Profiles;
        static bool Loaded = false;
        if (!Loaded)
        {
            Loaded = true;
            char Path[1024];
            GetFileSysPath(Path, "INTERFACE\\capital_interiors.ini", DALib::Data);
            INI_Reader Reader;
            if (Reader.open(Path, false))
            {
                while (Reader.read_header())
                {
                    if (!Reader.is_header("Base"))
                        continue;
                    unsigned Base = 0;
                    std::map<std::string, std::string> Rooms;
                    while (Reader.read_value())
                    {
                        if (Reader.is_value("nickname"))
                            Base = CreateID(Reader.get_value_string(0));
                        else if (Reader.is_value("room") && Reader.get_num_parameters() >= 2)
                        {
                            // INI_Reader returns a shared scratch buffer.
                            std::string Name = Reader.get_value_string(0);
                            Rooms[Name] = Reader.get_value_string(1);
                        }
                    }
                    if (Base != 0)
                        for (auto const& Room : Rooms)
                        {
                            char RoomPath[1024];
                            GetFileSysPath(RoomPath, Room.second.c_str(), DALib::Data);
                            INI_Reader Check;
                            if (Check.open(RoomPath, false))
                            {
                                Profiles[Base].Rooms[MakeLocationID(Base, Room.first.c_str())] = Room.second;
                                Check.close();
                            }
                            else
                                FDUMP(0x100002, "Capital interior not found: %s\n", RoomPath);
                        }
                }
                Reader.close();
            }
        }
        return Profiles;
    }

    inline bool IsLargeShip(unsigned ShipId)
    {
        Archetype::Ship const* Ship = ShipId ? Archetype::GetShip(ShipId) : nullptr;
        // type = CRUISER / TRANSPORT / CAPITAL. ship_class is only a UI label:
        // the player train has ship_class = 2, just like ordinary freighters.
        return Ship && (Ship->ObjectType & (0x80000u | 0x100000u | 0x200000u)) != 0;
    }

    inline bool Active(unsigned Base, unsigned Ship)
    {
        return IsLargeShip(Ship) && Profiles().find(Base) != Profiles().end();
    }

    inline char const* RoomFile(unsigned Base, unsigned Room, unsigned Ship)
    {
        if (!IsLargeShip(Ship))
            return nullptr;
        auto const& All = Profiles();
        auto Profile = All.find(Base);
        if (Profile == All.end())
            return nullptr;
        auto File = Profile->second.Rooms.find(Room);
        return File == Profile->second.Rooms.end() ? nullptr : File->second.c_str();
    }
}
