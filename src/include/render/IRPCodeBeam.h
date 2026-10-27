#pragma once
#include "dacom.h"

// Optional, scoped to the client's code_beam indexed batch. Does not affect ALE particles.
// RP8 / older RP9 do not expose the IID and keep the native draw.
// v2: XYZ|DIFFUSE|TEX2, TEXCOORD1 = local transverse XY, axial fraction, stable phase.
const unsigned RPCodeBeamFvf = 0x80242u;
struct IRPCodeBeam : IDAComponent
{
    virtual GENRESULT DACOM_API SetCodeBeamEnabled(unsigned long Enabled) = 0;
};
