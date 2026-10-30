#pragma once

struct ICamera;

namespace CockpitEffectBrightness
{
    enum class Kind { None, Weapon, Shield };

    // Classify new visual effects and their lights without changing retail layouts.
    // Classification survives camera changes and detaching an effect into world space.
    class CreationScope
    {
    public:
        explicit CreationScope(Kind kind);
        ~CreationScope();
        CreationScope(CreationScope const&) = delete;
        CreationScope& operator=(CreationScope const&) = delete;
    private:
        Kind previous;
    };

    void Register(void const* object);
    void Forget(void const* object);
    Kind KindOf(void const* object);
    float Scale(Kind kind, ICamera const* camera);
    float Scale(void const* object, ICamera const* camera);
}
