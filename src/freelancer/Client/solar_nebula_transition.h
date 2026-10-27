#pragma once
#include <algorithm>
#include <cmath>

// Visual adaptation only; physical fog/zone tests continue to use raw values.
struct SolarNebulaTransition
{
    double Time = -1.0;
    float Value = 0.0f;

    float Update(float target, double now, float riseSeconds, float fallSeconds)
    {
        target = (std::max)(0.0f, (std::min)(1.0f, target));
        if (Time < 0.0 || now < Time)
            Value = target;
        else
        {
            // A stall/offscreen gap must not snap the visible sun to full size.
            float const dt = static_cast<float>((std::min)(0.1, (std::max)(0.0, now - Time)));
            float const seconds = target > Value ? riseSeconds : fallSeconds;
            float const step = seconds > 0.0f ? dt / seconds : 1.0f;
            Value += target > Value ? (std::min)(target - Value, step)
                                   : (std::max)(target - Value, -step);
        }
        Time = now;
        return Value;
    }
};

inline float SolarNebulaSmoothUnit(float value)
{
    float const t = (std::max)(0.0f, (std::min)(1.0f, value));
    return t * t * (3.0f - 2.0f * t);
}
