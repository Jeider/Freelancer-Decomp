#pragma once
#include <cmath>
#include <cstdint>

// Shared by the runtime and the standalone D3D9 render check.
struct FTradeLaneVertex
{
    float Position[3];
    std::uint32_t Color;
    float UV[2];
};
static_assert(sizeof(FTradeLaneVertex) == 24, "corridor XYZ/DIFFUSE/TEX1 layout");
constexpr unsigned TradeLaneCorridorVertexCount = 48 * 5 * 6 + 48 * 2 * 3;
constexpr unsigned TradeLaneStreakCount = 384;
constexpr unsigned TradeLaneVertexCount = TradeLaneCorridorVertexCount + TradeLaneStreakCount * 6;

inline void BuildTradeLaneVisualMesh(FTradeLaneVertex* Vertices)
{
    // Long triangles crossing the eye plane can leave a one-pixel crack during D3D9
    // clipping. Five axial bands keep near-camera triangles short. Still one draw,
    // 480 wall triangles, and no dynamic geometry generation during travel.
    float const Distances[] = {-3500, -400, -40, 40, 400, 9500};
    for (int Band = 0; Band < 5; ++Band)
        for (int Sector = 0; Sector < 48; ++Sector)
        {
            FTradeLaneVertex Corners[4];
            for (int I = 0; I < 4; ++I)
            {
                int const Angular = Sector + (I & 1);
                float const U = (Angular + 0.5f) / 48.0f;
                // Identical positions at the seam, with unwrapped U for interpolation.
                float const Angle = ((Angular % 48) + 0.5f) * (6.283185307f / 48.0f);
                float const Forward = Distances[Band + (I / 2)];
                Corners[I] = {{165.0f * std::cos(Angle), 165.0f * std::sin(Angle), -Forward},
                               0xffffffffu, {U, Forward / 1600.0f}};
            }
            int const Order[] = {0, 1, 2, 2, 1, 3};
            for (int I = 0; I < 6; ++I)
                Vertices[(Band * 48 + Sector) * 6 + I] = Corners[Order[I]];
        }
    // End caps also shade the distant focus and the rear end of the volume.
    for (unsigned Cap = 0; Cap < 2; ++Cap)
    {
        float const Forward = Cap ? -3500.0f : 9500.0f;
        for (unsigned Sector = 0; Sector < 48; ++Sector)
        {
            unsigned const First = 48 * 5 * 6 + (Cap * 48 + Sector) * 3;
            Vertices[First] = {{0, 0, -Forward}, 0xffffffffu, {0.5f, Forward / 1600.0f}};
            for (unsigned Corner = 0; Corner < 2; ++Corner)
            {
                unsigned const Angular = Sector + Corner;
                float const U = (Angular + 0.5f) / 48.0f;
                float const Angle = ((Angular % 48) + 0.5f) * (6.283185307f / 48.0f);
                Vertices[First + Corner + 1] = {
                    {165.0f * std::cos(Angle), 165.0f * std::sin(Angle), -Forward},
                    0xffffffffu, {U, Forward / 1600.0f}};
            }
        }
    }
    // Stable seeds only; the vertex shader expands and animates these quads.
    std::uint32_t Seed = 0x7ac49e13u;
    auto Random = [&Seed]() {
        Seed ^= Seed << 13; Seed ^= Seed >> 17; Seed ^= Seed << 5;
        return float(Seed >> 8) / 16777216.0f;
    };
    int const Order[] = {0, 1, 2, 2, 1, 3};
    for (unsigned Streak = 0; Streak < TradeLaneStreakCount; ++Streak)
    {
        float const Angle = Random() * 6.283185307f;
        float const Radius = 65.0f + std::sqrt(Random()) * 90.0f;
        float const Phase = Random();
        FTradeLaneVertex Corners[4];
        for (unsigned Corner = 0; Corner < 4; ++Corner)
            Corners[Corner] = {{std::cos(Angle) * Radius, std::sin(Angle) * Radius, Phase},
                              0x00ffffffu, {(Corner & 1) ? 1.0f : -1.0f, (Corner & 2) ? 1.0f : -1.0f}};
        for (unsigned Corner = 0; Corner < 6; ++Corner)
            Vertices[TradeLaneCorridorVertexCount + Streak * 6 + Corner] = Corners[Order[Corner]];
    }
}
