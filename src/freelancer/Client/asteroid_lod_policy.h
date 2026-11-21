#pragma once

namespace AsteroidLod
{
// Apparent radius in pixels. Hysteresis is per instance, not per frame;
// teleporting can cross both thresholds in one update.
inline unsigned Select(double projectedRadiusSquared, double distanceSquared, unsigned previous)
{
    double nearThreshold = previous == 0 ? 28.0 : previous < 3 ? 36.0 : 32.0;
    double farThreshold = previous == 2 ? 14.0 : previous < 3 ? 10.0 : 12.0;
    if (projectedRadiusSquared >= distanceSquared * nearThreshold * nearThreshold) return 0;
    if (projectedRadiusSquared >= distanceSquared * farThreshold * farThreshold) return 1;
    return 2;
}
}
