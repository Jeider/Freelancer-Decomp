#pragma once
#include <cstring>

// Explicit authored identities, not colour/name substring heuristics. No retail ABI changes.
inline unsigned NomadSurfaceProfile(const char* name)
{
    if (!name) return 0;
    static const char* const lair[] = {
        "detailmap_lair_rock01", "detailmap_lair_rock02", "detailmap_lair_rock03",
        "detailmap_lair_rockdtl01", "detailmap_lair_rockdtl02",
        "detailmap_lair_rockdtl03", "detailmap_lair_rockdtl04"};
    static const char* const dyson[] = {
        "detailmap_dyson_dtl128", "detailmap_dyson_dtl2_128",
        "detailmap_dyson_skin01", "detailmap_dyson_skin02", "detailmap_dyson_skin03",
        "detailmap_dyson_skin04", "detailmap_dyson_skin05",
        "dyson_skin01", "dyson_skin02", "dyson_skin03", "dyson_skin04",
        "dyson_korobox", "dyson_korotun1", "dyson_korotun2"};
    for (const char* candidate : lair) if (!_stricmp(name,candidate)) return 5;
    for (const char* candidate : dyson) if (!_stricmp(name,candidate)) return 6;
    static const char* const inside[]={"detailmap_lair_skin01","detailmap_lair_skin02",
        "detailmap_lair_skin03","detailmap_lair_rckint02","lair_int_door","lair_int_doorR"};
    for (const char* candidate : inside) if (!_stricmp(name,candidate)) return 7;
    return 0;
}
