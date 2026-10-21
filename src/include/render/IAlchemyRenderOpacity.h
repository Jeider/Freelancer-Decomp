#pragma once
#include "dacom.h"

// Optional geometry-build scope. Does not alter ALE outer time, emission or simulation.
struct IAlchemyRenderOpacity : IDAComponent
{
    virtual GENRESULT DACOM_API SetRenderOpacity(float Opacity) = 0;
};
