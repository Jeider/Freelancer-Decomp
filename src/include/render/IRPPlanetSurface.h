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
    float MeshRadius;      // v2: object-space sphere radius; 0 = unavailable, retain full detail
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

// A planet ring band (the retail texture panels' [Exterior]) about to be drawn: drawn by RP9 with
// planet_ring.hlsl as a lit particle layer. World space. nullptr ends it.
struct FRPPlanetRing
{
    float Centre[3];        // ring centre
    float Normal[3];        // unit normal of the ring plane
    float InnerRadius;
    float OuterRadius;
    unsigned long Segments; // the band mesh's segments (its outer edge is a polygon of chords)
    float Shape[4];         // the shape's texture rectangle: U0, U1, V0 (outer edge), V1 (inner edge)
    unsigned long bDetail;  // a detail map is bound on stage 1
    float Fade[2];          // far, near: the band fades out between them as the camera closes in
    float Planet[4];        // the ring's planet: centre, radius (radius 0 = none)
    float Sun[4];           // the system's sun: centre, radius
    float Neighbour[4];     // the nearest other planet, which may shadow the ring too (radius 0 = none)
    float SunColour[4];     // rgb the sunlight at the ring centre, w 1 when set (0: RP9 picks a light)
    float Ambient[4];       // rgb the system's ambient light, w 1 when set (0: RP9 reads D3DRS_AMBIENT)
    unsigned long Piece;    // the band piece being drawn (port.ini ring_debug tints each one)
};

struct IRPPlanetSurface : IDAComponent
{
    virtual GENRESULT DACOM_API SetPlanetSurface(const FRPPlanetSurface* Desc) = 0;
    virtual GENRESULT DACOM_API SetPlanetEclipse(const FRPPlanetEclipse* Desc) = 0;
    virtual GENRESULT DACOM_API SetPlanetRing(const FRPPlanetRing* Desc) = 0;
    // The band last drawn through SetPlanetRing: its opacity across the band (Out[0] the inner
    // edge .. Out[Count - 1] the outer), from the shape texture's alpha with the detail map's
    // average and port.ini ring_opacity, before the vertex colour's opacity. GR_GENERIC when the
    // texture could not be read.
    virtual GENRESULT DACOM_API GetPlanetRingProfile(float* Out, unsigned long Count) = 0;
};
