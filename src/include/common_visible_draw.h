#pragma once
#include "common_exports.h"

namespace VisibleDraw {
COMMON_API void Reset();
COMMON_API void AddOccluder(float x, float y, float z, float radius);
COMMON_API bool FullyHidden(float camX, float camY, float camZ,
                            float x, float y, float z, float radius);
}
