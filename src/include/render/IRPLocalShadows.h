#pragma once
#include "dacom.h"

// Port-only, independent of the retail render interfaces. Coordinates passed here
// are game world coordinates; the pipeline keeps shadow calculations camera-relative.
struct IRPLocalShadows : IDAComponent
{
    virtual GENRESULT DACOM_API BeginLocalShadowFrame(const float* CameraView12,
        const float* CameraPosition3, const float* SunRayDirection3) = 0;
    virtual GENRESULT DACOM_API BeginLocalShadowMap(unsigned long Cascade) = 0;
    virtual GENRESULT DACOM_API EndLocalShadowMap() = 0;
    // 0 = off, 1 = static hull receiver, 3 = ship receiver (shorter quality radius).
    // Existing callers passing 0/1 retain their meaning and vtable layout.
    virtual GENRESULT DACOM_API SetLocalShadowReceiver(unsigned long Enabled) = 0;
    virtual GENRESULT DACOM_API AddLocalShadowPlanet(const float* Center3, float Radius) = 0;
};
