// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only, adoxa's engclass.dll v2.02 (docs/adoxa.md): the hp types of classed engines and
// powerplants, shared by Ship::read, Power::read and Engine::read. Retail had none of it: the
// plugin patched those readers (062f2598, 062f4878, 062f51b8).

#ifdef FREELANCER_ADOXA

#include <stdlib.h>
#include <string.h>

// engclass.c HP_TYPE / CLASSES: hp_<fighter|elite|freighter>_<power|engine>_special_<1..10>
// take the hp types 0x43..0x7e, ten per family in the order of the name table.
enum
{
    ADOXA_ENGCLASS_HP_TYPE = 0x43,
    ADOXA_ENGCLASS_CLASSES = 10,
    ADOXA_ENGCLASS_HP_TYPE_END = ADOXA_ENGCLASS_HP_TYPE + 6 * ADOXA_ENGCLASS_CLASSES // 0x7f
};

// engclass.c HP_Search: the hp type of one of the new names, 0 when it is none of them (a
// class outside 1..10, or anything after the number, is no match).
inline unsigned AdoxaEngclassHpSearch(char const* Type)
{
    static char const* const kNames[] = {
        "hp_fighter_power_special_", "hp_elite_power_special_",  "hp_freighter_power_special_",
        "hp_fighter_engine_special_", "hp_elite_engine_special_", "hp_freighter_engine_special_",
    };
    if (Type == nullptr)
        return 0;
    for (unsigned Index = 0; Index < sizeof(kNames) / sizeof(kNames[0]); ++Index)
    {
        size_t const Length = strlen(kNames[Index]);
        if (_strnicmp(Type, kNames[Index], Length) == 0)
        {
            char* End = nullptr;
            long const Class = strtol(Type + Length, &End, 10);
            if (Class < 1 || Class > ADOXA_ENGCLASS_CLASSES || *End != '\0')
                return 0;
            return ADOXA_ENGCLASS_HP_TYPE + Index * ADOXA_ENGCLASS_CLASSES + (unsigned)Class - 1;
        }
    }
    return 0;
}

#endif
