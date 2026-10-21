#pragma once
#include "dacom.h"
// Scoped draw context, independent of retail material/pipeline vtables.
struct IRPSurfaceContext : IDAComponent
{
    virtual GENRESULT DACOM_API SetCockpitSurface(unsigned long Enabled) = 0;
    virtual GENRESULT DACOM_API SetGlassSurface(unsigned long Enabled) = 0;
};
