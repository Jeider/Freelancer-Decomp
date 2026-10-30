#pragma once

#include "common_exports.h"

// User preferences are separate from authored port.ini values. Active values are
// frozen before the first frame; editing Configured never partly updates caches.
namespace GraphicsSettings
{
    enum Setting { Shadows, Relief, Highlights, Reflections, Anisotropy, Antialiasing,
                   Nebulae, VSync, FpsLimit, Count };
    inline char const* Key(int setting)
    {
        static char const* const keys[] = {"shadows", "relief", "highlights", "reflections",
            "anisotropy", "antialiasing", "nebulae", "vsync", "fps_limit"};
        return setting >= 0 && setting < Count ? keys[setting] : "";
    }
    inline int Maximum(int setting)
    {
        static int const maxima[] = {3,1,1,1,4,2,3,1,8};
        return setting >= 0 && setting < Count ? maxima[setting] : 0;
    }
    inline int Default(int setting)
    {
        static int const defaults[] = {3,1,1,1,4,2,3,1,6};
        return setting >= 0 && setting < Count ? defaults[setting] : 0;
    }
    inline bool Toggle(int setting)
    { return setting==Relief || setting==Highlights || setting==Reflections || setting==VSync; }
    inline int Fps(int index)
    {
        // Indices 1..8 remain compatible with existing saves; old 0 was unlimited.
        static int const values[] = {180,30,60,75,90,120,144,165,180};
        return index >= 0 && index <= Maximum(FpsLimit) ? values[index] : 180;
    }
    COMMON_API int __cdecl Get(int setting, bool configured = false);
    COMMON_API void __cdecl Set(int setting, int value);
    COMMON_API bool __cdecl RestartRequired();
}

// C linkage lets the standalone RP9 renderer use this policy without linking
// the game's Common import library (RP9 can also be used by other applications).
extern "C" COMMON_API float __cdecl PortGraphicsRenderValue(char const* key, float authored);
