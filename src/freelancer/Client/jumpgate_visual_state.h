#pragma once
#include <cmath>
#include <algorithm>

// Visual time only: the authored docking animation and jump durations are unchanged.
struct FJumpGateVisualPhase
{
    float Time = 0, Age = 0, Gain = 0;
    bool Open = false;
    void Activate() { if (!Open) Age = 0; Open = true; }
    void Tick(float Dt)
    {
        if (!std::isfinite(Dt) || Dt <= 0) return;
        Time = std::fmod(Time + Dt, 192.f);
        if (Open) {
            Age = (std::min)(Age + Dt, 12.f);
            Gain = (std::min)(1.f, Gain + Dt / .35f);
        } else Gain = (std::max)(0.f, Gain - Dt / 1.4f);
    }
};
