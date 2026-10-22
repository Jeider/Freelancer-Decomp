#pragma once
#include "dacom.h"

// Optional port-only RP9 interface: the next draws are a planet's atmosphere shell, drawn with
// planet_atmosphere.hlsl instead of the fixed-function pipeline. nullptr ends the scope.
struct FRPPlanetAtmosphere
{
    const char* Name;   // material name (port.ini atmosphere_exclude substrings skip it)
    float MeshRadius;   // object-space radius of the shell mesh (length of a vertex position)
    float Scale;        // the material's Scale (the shell transform includes it)
    float Tint[3];      // material diffuse colour (Dc)
    float Alpha;        // material Alpha
};

struct IRPPlanetAtmosphere : IDAComponent
{
    virtual GENRESULT DACOM_API SetPlanetAtmosphere(const FRPPlanetAtmosphere* Desc) = 0;
};
