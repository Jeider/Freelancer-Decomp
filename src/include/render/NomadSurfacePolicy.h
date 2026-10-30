#pragma once
#include <cstring>

// Bump rendering for the authored Dyson family, including aliases whose
// material names do not mention Dyson and transparent/fading variants.
inline bool IsDysonSurfaceMaterial(const char* name,const char* texture)
{
    // BEAST has its own explicitly authored material and a bounded bump profile.
    if(name && !_stricmp(name,"beast_dyson_recess")) return false;
    if(texture) {
        const char* base=texture;
        for(const char* p=texture;*p;++p) if(*p=='/' || *p=='\\') base=p+1;
        if(!_strnicmp(base,"dyson_",6)) return true;
        // ANM's virtual Dyson rings use these authored aliases in virt_dyson.mat.
        if(!_stricmp(base,"vdyson1") || !_stricmp(base,"vdyson2") || !_stricmp(base,"vdyson3")) return true;
    }
    return name && (!_strnicmp(name,"dyson_",6) ||
        !_strnicmp(name,"detailmap_dyson_",16) ||
        !_strnicmp(name,"asteroid_dyson",14));
}

// Explicit authored identities, not colour/name substring heuristics. No retail ABI changes.
inline unsigned NomadSurfaceProfile(const char* name)
{
    if (!name) return 0;
    if (!_stricmp(name,"beast_dyson_recess")) return 17;
    if (IsDysonSurfaceMaterial(name,nullptr)) return 6;
    static const char* const lair[] = {
        "detailmap_lair_rock01", "detailmap_lair_rock02", "detailmap_lair_rock03",
        "detailmap_lair_rockdtl01", "detailmap_lair_rockdtl02",
        "detailmap_lair_rockdtl03", "detailmap_lair_rockdtl04"};
    for (const char* candidate : lair) if (!_stricmp(name,candidate)) return 5;
    static const char* const inside[]={"detailmap_lair_skin01","detailmap_lair_skin02",
        "detailmap_lair_skin03","detailmap_lair_rckint02","lair_int_door","lair_int_doorR"};
    for (const char* candidate : inside) if (!_stricmp(name,candidate)) return 7;
    return 0;
}
