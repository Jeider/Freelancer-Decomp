#pragma once
#include <cmath>

// Port-only visual clocks. They never alter docking or jump-state durations.
inline float JumpHoleSaturate(float T) { return T < 0 ? 0 : T > 1 ? 1 : T; }
inline float JumpHoleSmooth(float T)
{
    T = JumpHoleSaturate(T);
    return T*T*(3.0f-2.0f*T);
}
constexpr float JumpHoleActivationDuration = 2.4f;
constexpr float JumpHoleIngressDuration = 1.35f;
inline float JumpHoleApproachStrength(bool DockingSelectedHole, float X, float Y, float Z)
{
    if (!DockingSelectedHole || !std::isfinite(X) || !std::isfinite(Y) || !std::isfinite(Z)) return 0;
    // The authored docking path approaches from local -Z, ending near Z=-28.
    float const Radial=std::sqrt(X*X+Y*Y);
    return JumpHoleSmooth((650+Z)/600)*(1-JumpHoleSmooth((Radial-110)/240))*
           (1-JumpHoleSmooth((Z-30)/100));
}
inline float JumpHoleIngressEnvelope(float Seconds)
{
    if (!std::isfinite(Seconds) || Seconds < 0 || Seconds >= JumpHoleIngressDuration) return 0;
    // Already bright on the first tunnel frame; then breathe out into the travel effect.
    return (0.85f+0.15f*JumpHoleSmooth(Seconds/.08f))*
           (1-JumpHoleSmooth((Seconds-.22f)/(JumpHoleIngressDuration-.22f)));
}
struct FJumpHoleVisualPhase
{
    float Time = 0, Opening = 0, Target = 0, Ripple = 0;
    float ActivationAge = JumpHoleActivationDuration;

    void Open()
    {
        if (Target <= 0) ActivationAge = 0;
        Target = 1;
    }
    void Close()
    {
        Target = 0;
        ActivationAge = JumpHoleActivationDuration;
        Ripple = 1;
    }
    void Tick(float Dt)
    {
        if (!std::isfinite(Dt) || Dt <= 0) return;
        Time = std::fmod(Time+Dt,96.0f);
        ActivationAge = (std::fmin)(JumpHoleActivationDuration,ActivationAge+Dt);
        float const Step = Dt/(Target > Opening ? 1.15f : 1.40f);
        if (Opening < Target) Opening = (std::fmin)(Target,Opening+Step);
        else Opening = (std::fmax)(Target,Opening-Step);
        Ripple = (std::fmax)(0.0f,Ripple-Dt/.85f);
    }
    float ActivationEnvelope() const
    {
        return JumpHoleSmooth(ActivationAge/.20f)*
               (1-JumpHoleSmooth((ActivationAge-.55f)/(JumpHoleActivationDuration-.55f)));
    }
};
