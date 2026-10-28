#pragma once
#include "dacom.h"
#include <cstring>

// Port-only, optional RP9 interface (no change to any retail or RP9Ex vtable).
// Object scope for asteroids and debris: while a scope is open, the lit opaque surfaces drawn by
// the surface shader get strong relief normals made at run time (the authored texture's own
// light/dark structure plus a shared tiling rock detail map) and a dull rock / scrap finish.
// Radius is the object's bounding radius in metres; it sets the height of the relief.
enum ERPRockClass : unsigned long
{
    RPRockOff = 0,
    RPRockAsteroid = 1, // dusty, rough stone and metal-rich rock
    RPRockDebris = 2,   // scrap: harder edges, scratched, a little glossier
};

struct IRPRockNormals : IDAComponent
{
    virtual GENRESULT DACOM_API SetRockNormalScope(unsigned long Class, float Radius) = 0;
};

// Solars that are asteroids in all but their archetype class: the mining asteroids, the large Arch
// chunks and the Arch prison asteroid. They are NON_TARGETABLE solars, found by their model path.
inline bool RockNormalSolarModel(const char* Model)
{
    if (!Model) return false;
    char Path[260];
    unsigned Length = 0;
    for (; Model[Length] && Length + 1 < sizeof(Path); ++Length)
    {
        char C = Model[Length];
        Path[Length] = C == '\\' ? '/' : (C >= 'A' && C <= 'Z' ? char(C - 'A' + 'a') : C);
    }
    Path[Length] = '\0';
    for (const char* Word : {"asteroids/", "asteroids_mod/", "arch_ast", "/ast_", "xast", "space_arch_asteroid", "space_arch_chunk"})
        if (strstr(Path, Word)) return true;
    return false;
}

// Asteroid and debris models that keep their own look: nomad, lair, dyson (their own surface
// profiles) and ice (the ice shader). Lower-cased '/' separated or raw path both work.
inline bool RockNormalExcludedModel(const char* Model)
{
    if (!Model) return false;
    char Path[260];
    unsigned Length = 0;
    for (; Model[Length] && Length + 1 < sizeof(Path); ++Length)
    {
        char C = Model[Length];
        Path[Length] = C == '\\' ? '/' : (C >= 'A' && C <= 'Z' ? char(C - 'A' + 'a') : C);
    }
    Path[Length] = '\0';
    for (const char* Word : {"nmd", "nomad", "lair", "dyson", "icecrystal", "ast_ice", "_ice_", "/ice_", "ice_asteroid"})
        if (strstr(Path, Word)) return true;
    return false;
}
