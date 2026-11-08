#pragma once

#include "base_interior_profiles.h"
class BaseData;
class INI_Reader;

namespace BaseInteriors
{
#ifdef FREELANCER_BASE_INTERIORS
    void ResetBase(unsigned Base);
    void ReadProfile(unsigned Base, INI_Reader& Reader);
    void ValidateProfiles(BaseData const& Base);
    void SetCharacters(RoomData const* Room, bool Enabled);
    void ForgetRoom(RoomData const* Room);
    bool ReadPlacementValue(ShipPlaceInfo const* Place, INI_Reader& Reader);
    void ForgetPlacement(ShipPlaceInfo const* Place);
#else
    inline void ResetBase(unsigned) {}
    inline void ReadProfile(unsigned, INI_Reader&) {}
    inline void ValidateProfiles(BaseData const&) {}
    inline void SetCharacters(RoomData const*, bool) {}
    inline void ForgetRoom(RoomData const*) {}
    inline bool ReadPlacementValue(ShipPlaceInfo const*, INI_Reader&) { return false; }
    inline void ForgetPlacement(ShipPlaceInfo const*) {}
#endif
}
