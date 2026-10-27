#pragma once
#include <cmath>

namespace PlayerTurretRules
{
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
