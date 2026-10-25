// Port-only radar geometry. Independent of the renderer and object lifetimes.
#pragma once
#include <algorithm>
#include <cmath>

namespace RadarProjection
{
    struct Vec3 { float x, y, z; };
    struct Viewport { int left, top, right, bottom; }; // inclusive, like ICamera
    struct Layout { float x, y, radius, ellipse, elevation; };
    struct Contact { float x, baseY, tipY, distanceSquared; bool below; };
    struct BatchSpace { float left, top, scaleX, scaleY; };

    inline bool MakeBatchSpace(Viewport const& active, Viewport const& ortho, BatchSpace& out)
    {
        double const w = double(active.right)-active.left+1;
        double const h = double(active.bottom)-active.top+1;
        double const ow = double(ortho.right)-ortho.left+1;
        double const oh = double(ortho.bottom)-ortho.top+1;
        if(w<=0 || h<=0 || ow<=0 || oh<=0 || w>32768 || h>32768 || ow>32768 || oh>32768)
            return false;
        out = {float(active.left),float(active.top),float(ow/w),float(oh/h)};
        return true;
    }

    inline void ToBatch(BatchSpace const& space, float x, float y, float (&out)[3])
    {
        out[0]=(x-space.left)*space.scaleX;
        out[1]=(y-space.top)*space.scaleY;
        out[2]=0;
    }

    inline float Bounded(float value, float lo, float hi, float fallback)
    {
        return std::isfinite(value) ? (std::max)(lo, (std::min)(hi, value)) : fallback;
    }

    inline bool MakeLayout(Viewport const& viewport, float centerX, float centerY,
                           float heightRadius, float ellipse, float elevation, Layout& out)
    {
        double const width = double(viewport.right) - viewport.left + 1.0;
        double const height = double(viewport.bottom) - viewport.top + 1.0;
        if (width < 64 || height < 64 || width > 32768 || height > 32768)
            return false;
        out.ellipse = Bounded(ellipse, 0.15f, 0.9f, 0.42f);
        out.elevation = Bounded(elevation, 0.1f, 1.0f, 0.65f);
        float const verticalExtent = out.ellipse + out.elevation;
        // Reserve space for selected brackets as well as the point itself.
        float const maxRadius = (std::min)(float(width - 24) * 0.5f / 1.04f,
                                            float(height - 24) * 0.5f / (verticalExtent + 0.04f));
        out.radius = (std::min)(float(height) * Bounded(heightRadius, 0.025f, 0.3f, 0.095f), maxRadius);
        float const blipMargin = (std::max)(10.0f, out.radius * 0.026f + 6.0f);
        float const marginX = out.radius + blipMargin;
        float const marginY = out.radius * verticalExtent + blipMargin;
        out.x = Bounded(float(viewport.left) + Bounded(centerX, 0, 1, 0.84f) * float(width - 1),
                        viewport.left + marginX, viewport.right - marginX, float(viewport.left) + float(width) * 0.5f);
        out.y = Bounded(float(viewport.top) + Bounded(centerY, 0, 1, 0.72f) * float(height - 1),
                        viewport.top + marginY, viewport.bottom - marginY, float(viewport.top) + float(height) * 0.5f);
        return out.radius > 0;
    }

    inline float EffectiveRange(float scannerRange, float factor)
    {
        if (!std::isfinite(scannerRange) || scannerRange <= 0)
            return 0;
        return scannerRange * Bounded(factor, 0.01f, 1.0f, 1.0f);
    }

    inline bool Accept(unsigned id, unsigned playerId, unsigned type, unsigned mask,
                       bool targetable, bool dying)
    {
        return id != 0 && id != playerId && (type & mask) != 0 && targetable && !dying;
    }

    // FL orientation is local-to-world. Its transpose converts the relative
    // position back into ship axes; forward is -Z. Camera movement is irrelevant.
    inline bool Project(Vec3 world, Vec3 player, float const rotation[3][3],
                        float range, Layout const& layout, Contact& out)
    {
        if (!std::isfinite(range) || range <= 0)
            return false;
        double const delta[3] = {double(world.x) - player.x, double(world.y) - player.y, double(world.z) - player.z};
        double const distanceSquared = delta[0]*delta[0] + delta[1]*delta[1] + delta[2]*delta[2];
        if (!std::isfinite(distanceSquared) || distanceSquared > double(range)*range)
            return false;
        double local[3] = {};
        for (int axis = 0; axis != 3; ++axis)
            for (int row = 0; row != 3; ++row)
                local[axis] += delta[row] * rotation[row][axis];
        if (!std::isfinite(local[0]) || !std::isfinite(local[1]) || !std::isfinite(local[2]))
            return false;
        double const scale = double(layout.radius) / range;
        out.x = float(layout.x + local[0] * scale);
        out.baseY = float(layout.y + local[2] * scale * layout.ellipse);
        out.tipY = float(out.baseY - local[1] * scale * layout.elevation);
        out.distanceSquared = float(distanceSquared);
        out.below = local[1] < 0;
        return true;
    }
}
