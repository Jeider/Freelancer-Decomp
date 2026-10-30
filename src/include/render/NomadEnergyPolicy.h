#pragma once
#include "IRPSurfaceShader.h"
#include <cstring>

// Match both material and texture: several unrelated solar libraries reuse names.
inline unsigned NomadEnergyProfile(const char* Material, const char* Texture)
{
    if (!Material || !Texture) return RPSurfaceAuto;
    auto eq = [](const char* a, const char* b) { return !_stricmp(a,b); };
    if ((eq(Material,"lair_rock_mbrn_2side") && eq(Texture,"lair_rock_membrane.tga")) ||
        (eq(Material,"lair_rckint_mem_2side") && eq(Texture,"lair_rckint_membrane.tgalair_op.tga")))
        return RPSurfaceLairMembrane;
    if ((eq(Material,"lair_energy") || eq(Material,"lair_energyglow_ni") ||
         eq(Material,"lair_energy_ni") || eq(Material,"detailmap_lair_rckint_128")) &&
        (eq(Texture,"lair_energy2.tga") || eq(Texture,"lair_energy.tga")))
        return RPSurfaceLairEnergy;
    return RPSurfaceAuto;
}
