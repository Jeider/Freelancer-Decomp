#pragma once
#include "graphics_settings.h"
#include <cstring>
#include <cmath>

namespace GraphicsSettings
{
    inline bool OneOf(char const* key, char const* const* keys, unsigned count)
    {
        for (unsigned i=0;i<count;++i) if (std::strcmp(key,keys[i])==0) return true;
        return false;
    }
    template<unsigned N> inline bool OneOf(char const* key, char const* const (&keys)[N])
    { return OneOf(key,keys,N); }

    inline float RenderValue(int const* values, char const* key, float authored)
    {
        static char const* const shadowKeys[]={"local_shadows","rock_shadows","room_object_shadows",
            "room_contact_shadows","planet_terrain_shadows"};
        static char const* const reliefKeys[]={"ship_normals","ship_normal_strength","rock_relief",
            "rock_macro_relief","rock_parallax","rock_debris_relief","rock_debris_macro",
            "cockpit_relief","planet_relief","planet_detail_relief","nomad_relief","beast_relief",
            "dyson_relief","far_rocks_relief","room_normal_strength","ice_depth","surface_relief"};
        static char const* const highlightKeys[]={"surface_highlights","surface_clearcoat","surface_brushed",
            "cockpit_finish","planet_glint","planet_ice_sheen","rock_asteroid_gloss","rock_debris_gloss",
            "weapon_glints","weapon_glint_strength","room_specular_strength"};
        if (!values[Shadows] && OneOf(key,shadowKeys)) return 0;
        if (!values[Relief] && OneOf(key,reliefKeys)) return 0;
        if (!values[Highlights] && OneOf(key,highlightKeys)) return 0;
        if (!values[Reflections] && !std::strcmp(key,"environment_maps")) return 0;
        if (!std::strcmp(key,"anisotropy")) return float(1 << values[Anisotropy]);
        if (!std::strcmp(key,"fxaa")) return values[Antialiasing]==1 ? 1.f : 0.f;
        if (!std::strcmp(key,"smaa")) return values[Antialiasing]==2 ? 1.f : 0.f;
        if (!std::strcmp(key,"vsync")) return float(values[VSync]);
        if (!std::strcmp(key,"fps_limit")) return float(Fps(values[FpsLimit]));
        // High retains the mod's authored quality. Lower tiers cap cost without
        // changing shadow reach/strength or nebula density/visibility.
        int const shadows=values[Shadows];
        if (shadows==1 || shadows==2)
        {
            if (!std::strcmp(key,"shadow_resolution") || !std::strcmp(key,"shadow_near_resolution") ||
                !std::strcmp(key,"shadow_far_resolution")) return std::fmin(authored,shadows==1?1024.f:2048.f);
            if (std::strstr(key,"shadow_")==key && std::strstr(key,"samples"))
                return std::fmin(authored,shadows==1?8.f:16.f);
        }
        if (!std::strcmp(key,"nebula_enabled")) return values[Nebulae] ? authored : 0.f;
        if (values[Nebulae]==1 || values[Nebulae]==2)
        {
            bool const low=values[Nebulae]==1;
            if (!std::strcmp(key,"nebula_resolution_scale")) return std::fmin(authored,low?.25f:.5f);
            if (!std::strcmp(key,"nebula_steps")) return std::fmin(authored,low?32.f:64.f);
            if (!std::strcmp(key,"nebula_shadow_steps")) return std::fmin(authored,low?2.f:4.f);
        }
        return authored;
    }
}
