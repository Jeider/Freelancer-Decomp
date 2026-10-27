#pragma once

#include <d3d9.h>
#include <cmath>

// D3D8 -> D3D9 spotlight compatibility, shared by FFP and material shaders.
// d3d8to9 narrows the inner cone by 1.75. Freelancer also uses equal inner/outer
// cones: modern D3D9 FFP can divide by zero there. A zero inner angle and tiny
// positive falloff retain the hard edge without that singularity (or pow(0,0)).
// References: github.com/crosire/d3d8to9 (SetLight),
//             github.com/FLHDE/fl-lighting-bug-fix (SetLight_Hook).
// Always translate a COPY at the rendering boundary; engine lights and the
// direct-light source cache must retain authored values across updates.
inline D3DLIGHT9 Rp9CompatibleLight(const D3DLIGHT9& Source)
{
    D3DLIGHT9 Light = Source;
    if (Light.Type == D3DLIGHT_SPOT && Light.Theta <= Light.Phi)
    {
        const float Inner = static_cast<float>(std::cos(Light.Theta * 0.5f));
        const float Outer = static_cast<float>(std::cos(Light.Phi * 0.5f));
        if (Inner == Outer)
        {
            Light.Theta = 0.0f;
            Light.Falloff = 1.0e-6f;
        }
        else
            Light.Theta /= 1.75f;
    }
    return Light;
}
