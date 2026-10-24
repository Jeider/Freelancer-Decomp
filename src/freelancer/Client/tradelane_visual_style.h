#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>

// Copied at lane entry; no pointers into system-owned effect data survive here.
struct FTradeLaneVisualStyle
{
    float Body[3] = {0.10f, 0.38f, 0.65f};
    float Accent[3] = {0.65f, 0.92f, 1.0f};
    float Enabled = 0, Mode = 0;
    float Seed[4] = {};
};

inline bool TradeLaneNormalizePalette(float* Color)
{
    float Peak = 0;
    for (unsigned I = 0; I < 3; ++I)
    {
        if (!std::isfinite(Color[I])) return false;
        Color[I] = Color[I] < 0 ? 0 : Color[I] > 1 ? 1 : Color[I];
        if (Color[I] > Peak) Peak = Color[I];
    }
    if (Peak < 0.001f) return false;
    for (unsigned I = 0; I < 3; ++I) Color[I] /= Peak;
    return true;
}

inline bool TradeLaneBuildPalette(FTradeLaneVisualStyle& Style, float const* Layer0,
                                  float const* Layer1, float const* Minimum,
                                  float const* Maximum, unsigned Mode)
{
    FTradeLaneVisualStyle Result;
    for (unsigned I = 0; I < 3; ++I)
    {
        if (!std::isfinite(Layer0[I]) || !std::isfinite(Layer1[I]) ||
            !std::isfinite(Minimum[I]) || !std::isfinite(Maximum[I])) return false;
        float const Mid = (Minimum[I] + Maximum[I]) * 0.5f;
        Result.Body[I] = Layer0[I] * 0.45f + Layer1[I] * 0.70f + Mid * 0.20f;
        Result.Accent[I] = Layer1[I] + Mid * 0.30f;
    }
    if (!TradeLaneNormalizePalette(Result.Body) || !TradeLaneNormalizePalette(Result.Accent))
        return false;
    Result.Enabled = 1;
    Result.Mode = float(Mode);
    Style = Result;
    return true;
}

struct FTradeLaneStyleCandidate
{
    unsigned TunnelId = 0, GateId = 0;
    double DistanceSq = 0;
    FTradeLaneVisualStyle Style;
};

// Majority by resolved tunnel ID, not jump-effect descriptor or style mode. The nearest
// gate represents each tied group; numeric IDs break exact distance ties independently of order.
// Returns Count when there is no valid candidate.
inline std::size_t TradeLaneSelectStyleCandidate(FTradeLaneStyleCandidate const* Candidates,
                                                std::size_t Count)
{
    std::size_t Best = Count, BestVotes = 0;
    for (std::size_t I = 0; I < Count; ++I)
    {
        auto const& Candidate = Candidates[I];
        if (!Candidate.TunnelId || !Candidate.Style.Enabled ||
            !std::isfinite(Candidate.DistanceSq) || Candidate.DistanceSq < 0) continue;
        std::size_t Votes = 0;
        for (std::size_t J = 0; J < Count; ++J)
            if (Candidates[J].TunnelId == Candidate.TunnelId && Candidates[J].Style.Enabled &&
                std::isfinite(Candidates[J].DistanceSq) && Candidates[J].DistanceSq >= 0) ++Votes;
        if (Best == Count || Votes > BestVotes ||
            (Votes == BestVotes && (Candidate.DistanceSq < Candidates[Best].DistanceSq ||
             (Candidate.DistanceSq == Candidates[Best].DistanceSq &&
              (Candidate.TunnelId < Candidates[Best].TunnelId ||
               (Candidate.TunnelId == Candidates[Best].TunnelId && Candidate.GateId < Candidates[Best].GateId))))))
        {
            Best = I;
            BestVotes = Votes;
        }
    }
    return Best;
}

inline void TradeLaneSeedStyle(FTradeLaneVisualStyle& Style, unsigned SystemId, unsigned RouteId)
{
    auto Hash = [](std::uint32_t H) {
        H ^= H >> 16; H *= 0x7feb352du;
        H ^= H >> 15; H *= 0x846ca68bu; H ^= H >> 16;
        return H;
    };
    std::uint32_t Seed = Hash(SystemId ^ 0x72d4b691u) ^ Hash(RouteId ^ 0xacf38917u);
    for (unsigned I = 0; I < 4; ++I)
    {
        Seed = Hash(Seed + 0x9e3779b9u + I);
        Style.Seed[I] = float(Seed >> 8) / 16777216.0f;
    }
}
