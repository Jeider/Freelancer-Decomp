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
        // Room-only controls. Never change global surface settings here: ships
        // use those same shaders in space. The renderer gates them by room scope.
        int const room=values[Interiors];
        if (!std::strcmp(key,"character_hair")) return float(values[Hair]);
        if (!std::strcmp(key,"character_hair_motion")) return values[Hair]<2 ? 0.f : values[Hair]==2 ? .55f : 1.f;
        if (!std::strcmp(key,"room_quality")) return float(room);
        if (!room && (!std::strcmp(key,"room_materials") ||
            !std::strcmp(key,"room_object_shadows") || !std::strcmp(key,"room_contact_shadows"))) return 0;
        if (room<3 && !std::strcmp(key,"room_contact_shadows")) return 0;
        if (room<2 && !std::strcmp(key,"room_object_shadows")) return 0;
        if (!std::strcmp(key,"room_light_count")) return std::fmin(authored,room<=1?2.f:room==2?4.f:8.f);
        if (!std::strcmp(key,"room_shadow_resolution")) return std::fmin(authored,room<3?512.f:1024.f);
        if (!std::strcmp(key,"room_procedural_relief") || !std::strcmp(key,"room_finish") ||
            !std::strcmp(key,"room_normal_strength")) return room<2 ? 0 : authored;
        if (!std::strcmp(key,"room_specular_strength")) return room ? authored : 0;
        if (!std::strcmp(key,"space_relief_quality")) return float(values[Relief]);
        if (!std::strcmp(key,"space_highlight_quality")) return float(values[Highlights]);
        if (values[Relief]<3 && !std::strcmp(key,"rock_parallax")) return 0;
        if (values[Relief]<2 && (!std::strcmp(key,"planet_detail_relief") ||
            !std::strcmp(key,"rock_macro_relief") || !std::strcmp(key,"rock_debris_macro"))) return 0;
        if (values[Relief]<2 && !std::strcmp(key,"cockpit_relief")) return 0;
        if (values[Relief]<3 && std::strncmp(key,"rock_lod_",9)==0)
            return authored*(values[Relief]<2?.35f:.65f);
        static char const* const shadowKeys[]={"local_shadows","rock_shadows","planet_terrain_shadows"};
        static char const* const reliefKeys[]={"ship_normals","ship_normal_strength","rock_relief",
            "rock_macro_relief","rock_parallax","rock_debris_relief","rock_debris_macro",
            "cockpit_relief","planet_relief","planet_detail_relief","nomad_relief","beast_relief",
            "dyson_relief","far_rocks_relief","ice_depth","surface_relief"};
        static char const* const highlightKeys[]={"surface_highlights","surface_clearcoat","surface_brushed",
            "cockpit_finish","planet_glint","planet_ice_sheen","rock_asteroid_gloss","rock_debris_gloss",
            "weapon_glints","weapon_glint_strength"};
        if (!values[Shadows] && OneOf(key,shadowKeys)) return 0;
        if (!values[Relief] && OneOf(key,reliefKeys)) return 0;
        if (!values[Highlights] && OneOf(key,highlightKeys)) return 0;
        if (!values[WeaponLights] && !std::strcmp(key,"weapon_lights")) return 0;
        // Zero is an explicit emergency opt-out of the enhanced anomaly renderer.
        if (!std::strcmp(key,"black_hole_visual") || !std::strcmp(key,"jumphole_visual")) return values[Anomalies]>0 ? 1.f : 0.f;
        if (values[Anomalies]<=2)
        {
            bool const low=values[Anomalies]<=1;
            if (!std::strcmp(key,"black_hole_resolution")) return std::fmin(authored,low?.25f:.5f);
            if (!std::strcmp(key,"black_hole_steps")) return std::fmin(authored,low?64.f:112.f);
            if (!std::strcmp(key,"jumphole_steps")) return std::fmin(authored,low?24.f:40.f);
        }
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
