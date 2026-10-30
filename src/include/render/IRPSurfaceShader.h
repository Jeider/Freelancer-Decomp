#pragma once

#include "dacom.h"

// Independent, optional RP9 interface: no changes to the retail or RP9Ex vtables.
// Auto selects the reflective shader only for a supported material with an envmap.
// Future ice/other profiles use this same entry; unsupported IDs fail without changing state.
enum ERPSurfaceShader : unsigned long
{
    RPSurfaceAuto = 0,
    RPSurfaceLegacy = 1,
    RPSurfaceReflective = 2,
    RPSurfaceIce = 3, // opaque crystal ice; no alpha/refraction scene pass
    RPSurfaceGreenhouse = 4, // alpha-masked greenhouse glazing and its painted frame
    RPSurfaceNomadLair = 5, // stone/bone exterior: normal/height relief, mineral finish
    RPSurfaceDyson = 6, // cheaper relief for dense opaque cube walls; no shadow sampling
    RPSurfaceNomadInterior = 7, // wet organic folds; preserve authored illumination layer
    RPSurfaceRock = 8, // asteroid rock texture: relief normals (any object that uses it, stations too)
    RPSurfaceRockDebris = 9, // the same for scrap and debris textures
    // Same lair shader, different authored bone masks (not separate finish styles).
    RPSurfaceLairBone1 = 10,
    RPSurfaceLairBone2 = 11,
    RPSurfaceLairBone3 = 12,
    RPSurfaceLairBone4 = 13,
    RPSurfaceLairSkinBone = 14,
    RPSurfaceLairEnergy = 15, // native material plus an additive glow pass
    RPSurfaceLairMembrane = 16, // native alpha/UVs plus animated surface sheen
    RPSurfaceBeast = 17, // single-layer static bump on BEAST's Dyson atlas; no parallax
};

inline bool IsNomadEnergy(unsigned long Profile)
{
    return Profile == RPSurfaceLairEnergy || Profile == RPSurfaceLairMembrane;
}

inline bool IsNomadSurface(unsigned long Profile)
{
    return Profile == RPSurfaceBeast || (Profile >= RPSurfaceNomadLair && Profile <= RPSurfaceNomadInterior) ||
           (Profile >= RPSurfaceLairBone1 && Profile <= RPSurfaceLairSkinBone);
}

struct IRPSurfaceShader : IDAComponent
{
    // Material-scoped state. Reset to Auto after an explicit override. Roughness <= 0 uses
    // the authored specular power; EnvironmentStrength < 0 uses the configured default.
    virtual GENRESULT DACOM_API SetSurfaceShader(unsigned long Shader, float Roughness,
                                                  float EnvironmentStrength) = 0;
};
