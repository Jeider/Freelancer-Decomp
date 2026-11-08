#pragma once

#include "common_exports.h"

class RoomData;
struct ShipPlaceInfo;

// Optional [InteriorProfile] sections belong to the base INI. The Common
// registry owns them; client/server use the same selection and access rules.
// No retail object layout or saved/network location ID changes are required.
namespace BaseInteriors
{
#ifdef FREELANCER_BASE_INTERIORS
    COMMON_API unsigned ProfileId(unsigned Base, unsigned Ship);
    COMMON_API char const* RoomFile(unsigned Base, unsigned Room, unsigned Ship);
    COMMON_API bool RoomAllowed(unsigned Base, unsigned Room, unsigned Ship);
    COMMON_API unsigned ResolveRoom(unsigned Base, unsigned Room, unsigned Ship);
    COMMON_API bool ServiceAllowed(unsigned Base, unsigned Ship, char const* Service);

    // Room/placement options are explicit INI properties, independent of any
    // profile name or ship class. Missing options retain the retail defaults.
    COMMON_API bool HasCharacters(RoomData const* Room);
    COMMON_API bool PlacementMatches(ShipPlaceInfo const* Place, unsigned Ship);
    COMMON_API bool PlacementShadow(ShipPlaceInfo const* Place);
#else
    // Shelved at the user's request, 2026-11-06. Keep normal base behavior
    // and avoid new Common.dll imports in default builds. The unfinished
    // experiment is documented in tools/capital_interiors/README.txt.
    inline unsigned ProfileId(unsigned, unsigned) { return 0; }
    inline char const* RoomFile(unsigned, unsigned, unsigned) { return nullptr; }
    inline bool RoomAllowed(unsigned, unsigned, unsigned) { return true; }
    inline unsigned ResolveRoom(unsigned, unsigned Room, unsigned) { return Room; }
    inline bool ServiceAllowed(unsigned, unsigned, char const*) { return true; }
    inline bool HasCharacters(RoomData const*) { return true; }
    inline bool PlacementMatches(ShipPlaceInfo const*, unsigned) { return true; }
    inline bool PlacementShadow(ShipPlaceInfo const*) { return true; }
#endif
}
