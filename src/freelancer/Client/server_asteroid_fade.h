#pragma once
#include <cmath>
#include <unordered_map>

// Client lifetime, independent of camera, network motion and gameplay cloak.
// A reused address starts a new fade only after the old object was forgotten.
namespace ServerAsteroidFade {
inline std::unordered_map<void const*, float>& Ages() {
    static std::unordered_map<void const*, float> ages;
    return ages;
}
constexpr float Duration = 0.75f;
inline void Begin(void const* object) { Ages().emplace(object, 0.0f); }
inline void Forget(void const* object) { Ages().erase(object); }
inline void Tick(void const* object, float dt) {
    auto it = Ages().find(object);
    if (it == Ages().end() || !(dt > 0.0f) || !std::isfinite(dt)) return;
    it->second = (dt >= Duration-it->second) ? Duration : it->second+dt;
}
inline float Opacity(void const* object) {
    auto it = Ages().find(object);
    if (it == Ages().end()) return 1.0f;
    float t = it->second / Duration;
    return t*t*(3.0f-2.0f*t);
}
}
