#pragma once
#include "dacom.h"
struct IFxEffectArchetype;
// Optional read-only metadata service. Samples authored ALE appearance colour keys,
// without creating effects, mutating particle nodes or adding native lights.
struct IAlchemyEffectColour : IDAComponent
{
    virtual GENRESULT DACOM_API SampleEffectColour(IFxEffectArchetype* Effect,float* Rgb3) = 0;
};
