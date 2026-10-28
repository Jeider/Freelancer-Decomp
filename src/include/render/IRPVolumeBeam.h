#pragma once
#include "dacom.h"

struct FRPVolumeBeamPoint
{
    float Position[3];
    float Radius;
    unsigned long Colour;
    float V;
};

// Optional RP9 path. Coordinates use the current modelview, matching ALE vertices.
// Probe before collecting points; unsupported devices retain the retail ribbon.
// The name probe also classifies the immediately following synchronous draw
// for trail-only camera fading; every new probe replaces that classification.
struct IRPVolumeBeam : IDAComponent
{
    virtual GENRESULT DACOM_API VolumeBeamAvailable(const char* NodeName,
        unsigned long SrcBlend, unsigned long DstBlend) = 0;
    virtual GENRESULT DACOM_API DrawVolumeBeam(const FRPVolumeBeamPoint* Points,
        unsigned long Count, float TextureU, unsigned long SrcBlend) = 0;
};
