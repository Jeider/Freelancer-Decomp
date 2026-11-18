#pragma once

// Optional DFM extension. Unmarked assets retain the retail load policy.
namespace CharacterGeometryLod
{
    constexpr unsigned MarkerVersion = 1;
    constexpr int ExtraLoaded = 1; // FDeformPartDesc::Field08 output, no ABI change
    inline unsigned First(bool enhanced, bool enabled, unsigned flags, bool nativeQuality = false)
    {
        // Off/low retain the complete standard chain on models without an extra LOD.
        if (!enhanced) return (flags & 2) ? 1u : 0u;
        // The old low-character option still removes the original highest LOD.
        return (flags & 2) ? 2u : enabled ? 0u : 1u;
    }
    inline unsigned NativeIndex(bool enhanced, unsigned physical)
    { return enhanced && physical ? physical - 1 : physical; }
    inline float NearDistance(float original) { return original * .5f; }
}
