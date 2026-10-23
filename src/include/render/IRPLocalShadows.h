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
    // Bit 2 enables a bounded opaque-instance batching scope for attached solars.
    // Bit 3 selects diffuse/env-only static surfaces; bit 4 uses native materials.
    // Bits 5..6 (value 0..2) lower a ship receiver's shadow quality: 0 the full filter,
    // 1 a moderate fixed filter, 2 a simple single bilinear comparison.
    // Existing callers passing 0/1 retain their meaning and vtable layout.
    virtual GENRESULT DACOM_API SetLocalShadowReceiver(unsigned long Enabled) = 0;
    virtual GENRESULT DACOM_API AddLocalShadowPlanet(const float* Center3, float Radius) = 0;
    // Far-cascade static cache: 0 opens a rebuild pass (caller must End),
    // 1 reuses it (no pass opened), negative requests the ordinary full pass.
    // The following BeginLocalShadowMap composites this depth before live casters.
    virtual GENRESULT DACOM_API BeginStaticShadowCache(unsigned long KeyLow, unsigned long KeyHigh) = 0;
    // Inside a shadow map: bit 0 marks the following casters short-reach (NPC ships, [Render]
    // shadow_npc_ship_length metres behind the caster); 0 restores the full shadow length.
    virtual GENRESULT DACOM_API SetLocalShadowCaster(unsigned long Flags) = 0;
    // A planet eclipse (port.ini planet_eclipses) on ships: like AddLocalShadowPlanet, but the
    // shadow reaches Range metres behind the planet with a penumbra from the sun's angular radius.
    virtual GENRESULT DACOM_API AddLocalShadowEclipse(const float* Center3, float Radius, float Range,
                                                     float SunAngle) = 0;
};
