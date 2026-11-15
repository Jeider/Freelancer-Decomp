#include "common_visible_draw.h"
#include <cmath>

namespace {
struct Sphere { float X, Y, Z, R; };
Sphere Occluders[48];
unsigned OccluderCount = 0;
}

namespace VisibleDraw {
void Reset() { OccluderCount = 0; }

void AddOccluder(float x, float y, float z, float radius) {
    if (!(radius >= 200.f) || !std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z) || !std::isfinite(radius))
        return;
    if (OccluderCount >= 48) return;
    Occluders[OccluderCount++] = {x, y, z, radius};
}

bool FullyHidden(float camX, float camY, float camZ, float x, float y, float z, float radius) {
    if (!(radius > 0.f) || !std::isfinite(radius) || OccluderCount == 0) return false;
    const float tx = x - camX, ty = y - camY, tz = z - camZ;
    const float td2 = tx * tx + ty * ty + tz * tz;
    if (!(td2 > 0.f)) return false;
    const float td = std::sqrt(td2);
    if (td <= radius) return false;
    for (unsigned i = 0; i < OccluderCount; ++i) {
        const Sphere& O = Occluders[i];
        if (O.R <= radius) continue;
        const float dx = O.X - camX, dy = O.Y - camY, dz = O.Z - camZ;
        const float od2 = dx * dx + dy * dy + dz * dz;
        if (!(od2 > O.R * O.R)) continue;
        const float od = std::sqrt(od2);
        const float along = (tx * dx + ty * dy + tz * dz) / od;
        const float sx = x - O.X, sy = y - O.Y, sz = z - O.Z;
        const float sep2 = sx * sx + sy * sy + sz * sz;
        const float sumR = O.R + radius;
        if (sep2 <= sumR * sumR) continue;
        if (along - radius <= od) continue;
        const float perp2 = td2 - along * along;
        if (perp2 < 0.f) continue;
        const float sinA = O.R / od;
        if (!(sinA < 1.f)) continue;
        const float coneR = along * sinA / std::sqrt(1.f - sinA * sinA);
        if (std::sqrt(perp2) + radius <= coneR) return true;
    }
    return false;
}
}
