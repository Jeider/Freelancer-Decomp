#pragma once
#include <cstdint>

constexpr unsigned TradeLaneNoiseSize = 64;

namespace TradeLaneNoiseDetail
{
    inline float Hash(unsigned X, unsigned Y, unsigned Z, std::uint32_t Seed)
    {
        std::uint32_t H = Seed ^ (X * 0x9e3779b9u) ^ (Y * 0x85ebca6bu) ^ (Z * 0xc2b2ae35u);
        H ^= H >> 16; H *= 0x7feb352du;
        H ^= H >> 15; H *= 0x846ca68bu; H ^= H >> 16;
        return float(H >> 8) / 16777215.0f;
    }

    inline float Fade(float T) { return T * T * T * (T * (T * 6 - 15) + 10); }
    inline float Mix(float A, float B, float T) { return A + (B - A) * T; }

    inline float Value(unsigned X, unsigned Y, unsigned Z, unsigned Grid, std::uint32_t Seed)
    {
        unsigned const Step = TradeLaneNoiseSize / Grid;
        unsigned const Ix = X / Step, Iy = Y / Step, Iz = Z / Step;
        float const Fx = Fade(float(X % Step) / Step);
        float const Fy = Fade(float(Y % Step) / Step);
        float const Fz = Fade(float(Z % Step) / Step);
        float Planes[2];
        for (unsigned K = 0; K < 2; ++K)
        {
            float Rows[2];
            for (unsigned J = 0; J < 2; ++J)
                Rows[J] = Mix(Hash(Ix % Grid, (Iy + J) % Grid, (Iz + K) % Grid, Seed),
                              Hash((Ix + 1) % Grid, (Iy + J) % Grid, (Iz + K) % Grid, Seed), Fx);
            Planes[K] = Mix(Rows[0], Rows[1], Fy);
        }
        return Mix(Planes[0], Planes[1], Fz);
    }

    inline std::uint32_t Byte(float V)
    {
        V = V < 0 ? 0 : V > 1 ? 1 : V;
        return static_cast<std::uint32_t>(V * 255.0f + 0.5f);
    }
}

// Deterministic periodic value noise, independent of gameplay RNG. X is the fastest axis.
// Packed AARRGGBB matches RPExFormatA8R8G8B8 (BGRA byte order on the client).
// R: broad density fBm; G/B: independent smooth displacement; A: fine density detail.
inline void BuildTradeLaneNoise(std::uint32_t* Texels)
{
    using namespace TradeLaneNoiseDetail;
    for (unsigned Z = 0; Z < TradeLaneNoiseSize; ++Z)
        for (unsigned Y = 0; Y < TradeLaneNoiseSize; ++Y)
            for (unsigned X = 0; X < TradeLaneNoiseSize; ++X)
            {
                float const R = 0.50f * Value(X,Y,Z,4,0x711e53a1u) +
                                0.28f * Value(X,Y,Z,8,0x827f64b2u) +
                                0.15f * Value(X,Y,Z,16,0x938075c3u) +
                                0.07f * Value(X,Y,Z,32,0xa49186d4u);
                float const G = 0.65f * Value(X,Y,Z,4,0x1237abcd) +
                                0.35f * Value(X,Y,Z,8,0x2348bcde);
                float const B = 0.65f * Value(X,Y,Z,4,0xace13579) +
                                0.35f * Value(X,Y,Z,8,0xbdf24680);
                float const A = 0.60f * Value(X,Y,Z,16,0x376aac12) +
                                0.40f * Value(X,Y,Z,32,0x487bbd23);
                Texels[(Z * TradeLaneNoiseSize + Y) * TradeLaneNoiseSize + X] =
                    (Byte(A) << 24) | (Byte(R) << 16) | (Byte(G) << 8) | Byte(B);
            }
}
