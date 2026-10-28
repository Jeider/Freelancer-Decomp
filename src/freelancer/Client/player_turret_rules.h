#pragma once
#include <cmath>

namespace PlayerTurretRules
{
    // Per-controller values, deliberately independent of shared gun archetypes.
    struct Behavior
    {
        float aimSeconds = 0.35f;
        float burstSeconds = 1.5f;
        float restSeconds = 0.75f;
        float accuracyPercent = 80.f;
        float spreadDegrees = 2.f;
        float searchSeconds = 0.2f;
        float targetHoldSeconds = 0.75f;
        unsigned reservePercent = 35;
    };

    struct BurstCycle
    {
        enum class Phase { Aim, Burst, Rest };
        Phase phase = Phase::Aim;
        float remaining = 0;
        void Reset(Behavior const& b) { phase = Phase::Aim; remaining = b.aimSeconds; }
        // Returns true when a new aiming period begins. A hitch never emits catch-up shots.
        bool Advance(float dt, Behavior const& b)
        {
            if (!std::isfinite(dt) || dt <= 0) return false;
            remaining = remaining > dt ? remaining - dt : 0;
            if (phase == Phase::Burst && remaining == 0)
            { phase = Phase::Rest; remaining = b.restSeconds; }
            if (phase == Phase::Rest && remaining == 0)
            { Reset(b); return true; }
            return false;
        }
        bool Ready() const { return phase == Phase::Burst || (phase == Phase::Aim && remaining == 0); }
        void Fired(Behavior const& b)
        {
            if (phase == Phase::Aim) { phase = Phase::Burst; remaining = b.burstSeconds; }
        }
    };

    // Accuracy is aim quality, not a promised hit rate: 100% removes controller error.
    inline float SpreadRadians(Behavior const& b)
    {
        return b.spreadDegrees * (1.f - b.accuracyPercent / 100.f) * 0.01745329252f;
    }

    // Reserve is a hard floor for the complete volley, including every barrel.
    inline bool CanSpend(float power, float capacity, double cost, unsigned reserve)
    {
        return std::isfinite(power) && std::isfinite(capacity) && std::isfinite(cost) &&
            capacity > 0 && cost >= 0 && reserve <= 100 &&
            double(power) - cost >= double(capacity) * reserve / 100.0;
    }

    inline bool Resume(float power, float capacity, unsigned reserve)
    {
        return CanSpend(power, capacity, 0, (reserve > 90 ? 100 : reserve + 10));
    }
}
