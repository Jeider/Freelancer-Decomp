#pragma once
#include "dacom.h"

// Optional port-only RP9 interface: the next draws are a planet surface (DetailMapMaterial,
// DetailMap2Dm1Msk2PassMaterial, Masked2DetailMapMaterial or IllumDetailMapMaterial), drawn in one pass with planet_surface.hlsl.
// Shading binds the base map to stage 0 and the detail maps to stages 1 and 2. A failed Set means
// RP9 will not draw it: the caller keeps the retail passes. nullptr ends the scope.
struct FRPPlanetSurface
{
    const char* Name;      // material instance name (port.ini planet_surface_exclude substrings skip it)
    unsigned long Mode;    // 0 DetailMap2Dm1Msk2PassMaterial, 1 Masked2DetailMapMaterial,
                           // 2 IllumDetailMapMaterial, 3 DetailMapMaterial
    const char* Detail0;   // texture name on stage 1
    const char* Detail1;   // texture name on stage 2 ("" for mode 0)
    float TileRate0;       // stage 1 uv scale
    float TileRate1;       // stage 2 uv scale
};

// A planet that eclipses the next planet draws (surface and atmosphere): the caster sphere and
// the sun sphere in world space; the shadow reaches Range metres from the caster. nullptr ends it.
struct FRPPlanetEclipse
{
    float Caster[4]; // world centre, radius
    float Sun[4];    // world centre, radius
    float Range;     // how far behind the caster the shadow reaches
    float Strength;  // 1 = full shadow in the umbra
    // The camera (planets draw through a modelview, so RP9's own view transform is identity):
    // the game camera's view transform (as BeginLocalShadowFrame takes it) and its position.
    float View12[12];
    float Eye[3];
};

struct IRPPlanetSurface : IDAComponent
{
    virtual GENRESULT DACOM_API SetPlanetSurface(const FRPPlanetSurface* Desc) = 0;
    virtual GENRESULT DACOM_API SetPlanetEclipse(const FRPPlanetEclipse* Desc) = 0;
};
