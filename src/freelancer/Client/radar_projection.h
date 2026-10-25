// Port-only radar geometry. Independent of the renderer and object lifetimes.
#pragma once
#include <algorithm>
#include <cmath>

namespace RadarProjection
{
    struct Vec3 { float x, y, z; };
    struct Viewport { int left, top, right, bottom; }; // inclusive, like ICamera
    struct Layout { float x, y, radius, ellipse, elevation, contactTop, contactBottom; };
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
        out.ellipse = Bounded(ellipse, 0.15f, 0.9f, 0.32f);
        out.elevation = Bounded(elevation, 0.1f, 1.0f, 0.94f);
        float const verticalExtent = out.ellipse + out.elevation;
        // Reserve space for selected brackets as well as the point itself.
        float const maxRadius = (std::min)(float(width - 24) * 0.5f / 1.04f,
                                            float(height - 24) * 0.5f / (verticalExtent + 0.04f));
        out.radius = (std::min)(float(height) * Bounded(heightRadius, 0.025f, 0.3f, 0.30f), maxRadius);
        float const blipMargin = (std::max)(10.0f, out.radius * 0.026f + 6.0f);
        float const marginX = out.radius + blipMargin;
        // Keep the plane low; tall stems stop at the viewport's safe edge.
        float const marginY = out.radius * (out.ellipse + 0.025f) + blipMargin;
        out.contactTop = viewport.top + blipMargin;
        out.contactBottom = viewport.bottom - blipMargin;
        out.x = Bounded(float(viewport.left) + Bounded(centerX, 0, 1, 0.50f) * float(width - 1),
                        viewport.left + marginX, viewport.right - marginX, float(viewport.left) + float(width) * 0.5f);
        out.y = Bounded(float(viewport.top) + Bounded(centerY, 0, 1, 0.845f) * float(height - 1),
                        viewport.top + marginY, viewport.bottom - marginY, float(viewport.top) + float(height) * 0.5f);
        return out.radius > 0;
    }

    inline float EffectiveRange(float scannerRange, float factor)
    {
        if (!std::isfinite(scannerRange) || scannerRange <= 0)
            return 0;
        return scannerRange * Bounded(factor, 0.01f, 1.0f, 1.0f);
    }

    // Zoom-in lowers displayed range; never extends scanner detection distance.
    inline int ZoomIndex(int current, bool zoomIn)
    { return (std::max)(0, (std::min)(2, current + (zoomIn ? -1 : 1))); }

    inline bool Accept(unsigned id, unsigned playerId, unsigned type, unsigned mask,
                       bool targetable, bool dying)
    {
        return id != 0 && id != playerId && (type & mask) != 0 && targetable && !dying;
    }

    // FL orientation is local-to-world. Its transpose converts the relative
    // position back into ship axes; forward is -Z. Camera movement is irrelevant.
    inline bool Project(Vec3 world, Vec3 player, float const rotation[3][3],
                        float range, Layout const& layout, Contact& out, float objectRadius=0)
    {
        if (!std::isfinite(range) || range <= 0)
            return false;
        double const delta[3] = {double(world.x) - player.x, double(world.y) - player.y, double(world.z) - player.z};
        double const distanceSquared = delta[0]*delta[0] + delta[1]*delta[1] + delta[2]*delta[2];
        if (!std::isfinite(objectRadius) || objectRadius<0) return false;
        double const reach=double(range)+objectRadius;
        if (!std::isfinite(distanceSquared) || distanceSquared > reach*reach)
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
        float const tip=float(out.baseY - local[1] * scale * layout.elevation);
        // Extended objects retain their true centres; the renderer clips their edges.
        out.tipY = objectRadius>0 ? tip : Bounded(tip,layout.contactTop,layout.contactBottom,out.baseY);
        out.distanceSquared = float(distanceSquared);
        out.below = local[1] < 0;
        return true;
    }
}
