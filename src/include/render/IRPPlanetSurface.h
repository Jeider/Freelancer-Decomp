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

struct IRPPlanetSurface : IDAComponent
{
    virtual GENRESULT DACOM_API SetPlanetSurface(const FRPPlanetSurface* Desc) = 0;
};
