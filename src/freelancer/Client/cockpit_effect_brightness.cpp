#include "cockpit_effect_brightness.h"
#include "space_camera.h"

#include <unordered_map>

namespace CockpitEffectBrightness
{
    namespace
    {
        Kind creationKind = Kind::None;
        std::unordered_map<void const*, Kind>& Objects()
        {
            // ClientAtExitTeardown is registered before the first light. It can
            // delete room/HUD lights after function-static destructors ran.
            // Keep the registry alive through that final engine teardown.
            static auto* objects = new std::unordered_map<void const*, Kind>;
            return *objects;
        }
    }

    CreationScope::CreationScope(Kind kind) : previous(creationKind)
    {
        // A projectile splash spawned by a shield hit belongs to that shield hit.
        if (creationKind != Kind::Shield) creationKind = kind;
    }

    CreationScope::~CreationScope() { creationKind = previous; }

    void Register(void const* object)
    {
        if (!object) return;
        if (creationKind == Kind::None) Objects().erase(object);
        else Objects()[object] = creationKind;
    }

    void Forget(void const* object) { Objects().erase(object); }

    Kind KindOf(void const* object)
    {
        auto const found = Objects().find(object);
        return found == Objects().end() ? Kind::None : found->second;
    }

    float Scale(Kind kind, ICamera const* camera)
    {
        if (!camera || camera != AsCamera(GetFirstPersonSpaceCamera())) return 1.0f;
        if (kind == Kind::Shield) return 0.20f;
        if (kind == Kind::Weapon) return 0.33f;
        return 1.0f;
    }

    float Scale(void const* object, ICamera const* camera) { return Scale(KindOf(object), camera); }
}
