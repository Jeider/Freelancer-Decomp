#pragma once
#include "dacom.h"

// Optional RP9 surface-only weapon glow; no native light or shadow-map resources.
struct IRPWeaponGlints : IDAComponent
{
    // Clears last frame. Null camera arguments clear/disable without retaining pointers.
    virtual GENRESULT DACOM_API BeginWeaponGlints(const float* View12, const float* Eye3) = 0;
    // Submit one tracked representative and an averaged colour per shooter.
    // Repeated submissions for that owner merge colours without splitting directions. Returns group index + 1 when admitted,
    // 0 when skipped, negative on invalid input.
    // Position is world-space, colour is linear RGB in [0,1]. Direction is
    // ignored by the lightweight profile and retained for call compatibility.
    virtual GENRESULT DACOM_API AddWeaponGlint(const float* Position3, const float* Direction3,
        const float* Colour3, unsigned long Owner) = 0;
    virtual GENRESULT DACOM_API SetWeaponGlintReceiver(unsigned long Enabled) = 0;
    // Object-level broad phase: only nearby groups reach this object's pixel shader.
    virtual GENRESULT DACOM_API SetWeaponGlintReceiverBounds(const float* Center3,float Radius) = 0;
};
