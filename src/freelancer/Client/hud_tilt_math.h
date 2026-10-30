#pragma once
#include <cmath>

// A panel rotated around its outer vertical edge. Coordinates are physical pixels.
// The same inverse is used by the compositor shader and pointer routing.
struct HudTiltTransform
{
    float PivotX, PivotY, Cos, K;
    static HudTiltTransform Make(float width, float height, int side, float degrees)
    {
        const float angle = degrees * 0.017453292519943295f;
        return { side < 0 ? width * .015f : width * .985f, height * .8f,
            std::cos(angle), -side * std::sin(angle) / (height * .85f) };
    }
    void Project(float& x, float& y) const
    {
        const float dx = x - PivotX;
        const float d = 1.f + K * dx;
        x = PivotX + Cos * dx / d;
        y = PivotY + (y - PivotY) / d;
    }
    bool Unproject(float& x, float& y) const
    {
        const float d = Cos - K * (x - PivotX);
        if (!(d > .01f)) return false;
        const float dx = (x - PivotX) / d;
        y = PivotY + (y - PivotY) * (1.f + K * dx);
        x = PivotX + dx;
        return std::isfinite(x) && std::isfinite(y);
    }
};
