#pragma once
#include "dacom.h"

// Optional geometry-build scope. Does not alter ALE outer time, emission or simulation.
struct IAlchemyRenderOpacity : IDAComponent
{
    virtual GENRESULT DACOM_API SetRenderOpacity(float Opacity) = 0;
    // 0 draws the following appearances without soft particles (effects attached to a hull:
    // engines, thrusters, lights sit on the surface and would fade into it); 1 restores.
    virtual GENRESULT DACOM_API SetRenderSoftParticles(unsigned long Enabled) = 0;
};
