#pragma once
#include <cmath>

// Uniform per planet draw: fades reach exact zero before their shader branches skip work.
// Pixel diameter respects resolution/FOV; unknown bounds retain full quality.
inline void Rp9PlanetQuality(float Radius, float ViewZ, float ProjectionY,
                             unsigned ViewportHeight, float PixelScale, float* Out)
{
    for (int I = 0; I < 4; ++I) Out[I] = 1.0f;
    if (!(Radius > 0.0f) || !std::isfinite(Radius) || !std::isfinite(ViewZ) ||
        !std::isfinite(ProjectionY) || !(PixelScale > 0.0f) || !std::isfinite(PixelScale) ||
        !ViewportHeight || std::fabs(ViewZ) <= Radius || ProjectionY == 0.0f)
        return;
    double const Z = std::fabs(static_cast<double>(ViewZ));
    // Conservative estimate off-axis, so edge-of-screen planets are not under-detailed.
    double const Pixels = ViewportHeight * std::fabs(static_cast<double>(ProjectionY)) * Radius /
        std::sqrt(Z * Z - static_cast<double>(Radius) * Radius) * PixelScale;
    float const Low[4] = {60.0f, 250.0f, 180.0f, 350.0f};
    float const High[4] = {180.0f, 700.0f, 800.0f, 900.0f};
    for (int I = 0; I < 4; ++I)
    {
        double T = (Pixels - Low[I]) / (High[I] - Low[I]);
        T = T < 0.0 ? 0.0 : (T > 1.0 ? 1.0 : T);
        Out[I] = static_cast<float>(T * T * (3.0 - 2.0 * T));
    }
}
