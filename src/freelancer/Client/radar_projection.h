// Port-only radar geometry. Independent of the renderer and object lifetimes.
#pragma once
#include <algorithm>
#include <cmath>
#include "../../include/common_server_asteroid.h"

namespace RadarProjection
{
    struct Vec3 { float x, y, z; };
    struct Viewport { int left, top, right, bottom; }; // inclusive, like ICamera
    struct Layout { float x, y, radius, ellipse, elevation, contactTop, contactBottom; bool topDown = false; };
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
                           float heightRadius, float ellipse, float elevation, Layout& out, bool topDown = false)
    {
        double const width = double(viewport.right) - viewport.left + 1.0;
        double const height = double(viewport.bottom) - viewport.top + 1.0;
        if (width < 64 || height < 64 || width > 32768 || height > 32768)
            return false;
        out.topDown = topDown;
        out.ellipse = topDown ? 1.f : Bounded(ellipse, 0.15f, 0.9f, 0.32f);
        out.elevation = topDown ? 0.f : Bounded(elevation, 0.1f, 1.0f, 0.94f);
        float const verticalExtent = out.ellipse + out.elevation;
        // Reserve space for selected brackets as well as the point itself.
        float const maxRadius = (std::min)(float(width - 24) * 0.5f / 1.04f,
                                            float(height - 24) * 0.5f / (verticalExtent + 0.04f));
        out.radius = (std::min)(float(height) * Bounded(heightRadius, 0.025f, 0.3f, 0.30f), maxRadius);
        // Compact top view retains the bottom-centre anchor; its smaller margin
        // lets it sit lower without changing the ordinary oblique projection.
        if (topDown) out.radius *= 0.5f;
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
                       bool targetable, bool dying, bool valuable = false)
    {
        // Server physics represents moving asteroids as solars; they are scenery,
        // not radar contacts (including the mining scan and auto-open policy).
        return id != 0 && id != playerId && (!IsServerAsteroidType(type) || valuable) &&
               (type & mask) != 0 && targetable && !dying;
    }

    inline void LevelRotation(float const source[3][3], float (&out)[3][3])
    {
        // Heading in the ecliptic plane only. Near vertical flight use the right
        // axis, so the top view remains finite without introducing pitch or roll.
        double x = source[0][2], z = source[2][2];
        double length = std::hypot(x,z);
        if (length < 0.0001) { x = -source[2][0]; z = source[0][0]; length = std::hypot(x,z); }
        if (!std::isfinite(length) || length < 0.0001) { x = 0; z = 1; length = 1; }
        float const sx = float(x/length), sz = float(z/length);
        out[0][0]=sz;out[0][1]=0;out[0][2]=sx;
        out[1][0]=0;out[1][1]=1;out[1][2]=0;
        out[2][0]=-sx;out[2][1]=0;out[2][2]=sz;
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
        float level[3][3];
        if (layout.topDown) { LevelRotation(rotation,level); rotation=level; }
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
