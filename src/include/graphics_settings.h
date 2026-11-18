#pragma once

#include "common_exports.h"
#include <cstdio>

// User preferences are separate from authored port.ini values. Active values are
// frozen before the first frame; editing Configured never partly updates caches.
namespace GraphicsSettings
{
    enum Setting { Shadows, Relief, Highlights, Reflections, Anisotropy, Antialiasing,
                   Nebulae, VSync, FpsLimit, WeaponLights, Anomalies, Interiors, Hair, TradeLane, Hyperspace, CharacterGeometry, Count };
    inline char const* Key(int setting)
    {
        static char const* const keys[] = {"shadows", "relief_quality", "highlight_quality", "reflections",
            "anisotropy", "antialiasing", "nebulae", "vsync", "fps_limit", "weapon_lights", "anomalies", "interiors", "character_hair", "tradelane_quality", "hyperspace_quality", "character_detail_quality"};
        return setting >= 0 && setting < Count ? keys[setting] : "";
    }
    inline int Maximum(int setting)
    {
        static int const maxima[] = {3,3,3,1,4,2,3,1,8,1,3,3,3,3,3,3};
        return setting >= 0 && setting < Count ? maxima[setting] : 0;
    }
    inline int Minimum(int setting) { return setting==FpsLimit ? 1 : 0; }
    inline int Default(int setting)
    {
        static int const defaults[] = {3,3,3,1,4,2,3,1,6,1,3,3,3,3,3,3};
        return setting >= 0 && setting < Count ? defaults[setting] : 0;
    }
    inline bool Toggle(int setting)
    { return setting==Reflections || setting==VSync || setting==WeaponLights; }
    inline int PresetValue(int setting, int quality)
    {
        // Frame pacing is intentionally outside the visual presets.
        if (quality<0 || quality>3 || setting==VSync || setting==FpsLimit) return -1;
        static int const presets[4][Count]={
            {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0},
            {1,1,1,0,1,1,1,0,0,0,1,1,1,1,1,1},
            {2,2,2,1,3,2,2,0,0,1,2,2,2,2,2,2},
            {3,3,3,1,4,2,3,0,0,1,3,3,3,3,3,3}};
        return setting>=0 && setting<Count ? presets[quality][setting] : -1;
    }
    inline int Fps(int index)
    {
        // Indices 1..8 remain compatible with existing saves; old 0 was unlimited.
        static int const values[] = {180,30,60,75,90,120,144,165,180};
        return index >= 0 && index <= Maximum(FpsLimit) ? values[index] : 180;
    }
    COMMON_API int __cdecl Get(int setting, bool configured = false);
    COMMON_API void __cdecl Set(int setting, int value);
    COMMON_API bool __cdecl RestartRequired();
    COMMON_API void __cdecl WriteAutoProfile(FILE* file);
}

// C linkage lets the standalone RP9 renderer use this policy without linking
// the game's Common import library (RP9 can also be used by other applications).
extern "C" COMMON_API float __cdecl PortGraphicsRenderValue(char const* key, float authored);
extern "C" COMMON_API void __cdecl PortCharacterPortraitScope(int enter);

struct Costume;
COMMON_API void __cdecl PlayerCostume_ApplyOverride(Costume& Base, Costume& Comm);
