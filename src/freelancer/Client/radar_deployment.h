#pragma once
#include <algorithm>
#include <cmath>
#include "radar_projection.h"

// Fold and slide below the viewport; contacts only run after full deployment.
namespace RadarDeployment
{
    struct AutoState
    {
        float hold = 0;
        bool suppressed = false;
        bool match = false;
        void Step(float dt)
        {
            if (!std::isfinite(dt) || dt <= 0) return;
            if (!match) suppressed = false;
            if (match && !suppressed) hold = 1.5f;
            else hold = (std::max)(0.f, hold - dt);
        }
        void Close() { suppressed = true; hold = 0; }
        bool Open() const { return hold > 0; }
    };
    struct State
    {
        float position = 0;
        void Step(bool open, float dt)
        {
            if (!std::isfinite(dt) || dt <= 0) return;
            float const delta = dt / .35f;
            position = open ? (std::min)(1.f, position + delta)
                            : (std::max)(0.f, position - delta);
        }
        float Blend() const { return position * position * position * (position * (position * 6 - 15) + 10); }
        float Scale() const { return .18f + .82f * Blend(); }
        float Opacity() const { return .45f + .55f * Blend(); }
        bool Visible() const { return position > 0; }
        void Apply(RadarProjection::Layout& layout, int viewportBottom) const
        {
            // Use the complete rim height, including raised vertices, so the
            // folded model finishes below the viewport even at another aspect ratio.
            float const hiddenY = float(viewportBottom) + 1.f +
                layout.radius * .18f * (layout.ellipse + layout.elevation) + 16.f;
            layout.y += (hiddenY - layout.y) * (1.f - Blend());
            layout.radius *= Scale();
        }
        bool Running(bool open) const { return open && position >= 1.f; }
    };
}
