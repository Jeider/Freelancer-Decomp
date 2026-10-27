#pragma once
#include <algorithm>
#include <cmath>

namespace RadarMotion
{
    constexpr float MaxRate = 8.f * .01745329252f;
    // The Beta rim has four identical forward arrows; its grid shares that symmetry.
    constexpr float ArrowSpacing = 1.57079632679f;
    inline float Axis(float speed, float maximum)
    {
        if (!std::isfinite(speed) || !std::isfinite(maximum) || maximum <= .00001f) return 0;
        return (std::max)(-1.f, (std::min)(1.f, speed / maximum));
    }
    inline float TurnRate(float pitch, float yaw, float maxPitch, float maxYaw)
    {
        float const x=Axis(pitch,maxPitch),y=Axis(yaw,maxYaw);
        float const amount=(std::min)(1.f,std::sqrt(x*x+y*y));
        if (amount<=.01f) return 0; // Suppress physics jitter at rest.
        // Yaw follows left/right on screen; mostly vertical turns use pitch sign.
        float const direction=std::fabs(y)>=std::fabs(x) ? -y : x;
        return (direction<0 ? -1.f : 1.f)*MaxRate*(amount-.01f)/.99f;
    }
    struct State
    {
        unsigned ship=0;
        float angle=0,rate=0;
        bool aligning=false;
        bool returning=false;
        void Reset() {ship=0;angle=rate=0;aligning=returning=false;}
        void FaceForward() { aligning=true; rate=0; }
        void Step(unsigned id,float pitch,float yaw,float maxPitch,float maxYaw,float dt,bool steeringActive=true)
        {
            if (!id) {Reset();return;}
            if (ship!=id) {Reset();ship=id;}
            if (!std::isfinite(dt) || dt<=0) return;
            dt=(std::min)(dt,.25f);
            // Use the nearest arrow, at most 45 degrees away, regardless of the
            // previous turn direction. Equivalent quarter turns render identically.
            angle=std::remainder(angle,ArrowSpacing);
            if (aligning)
            {
                float const step=MaxRate*dt;
                if (std::fabs(angle)<=step) {angle=0;aligning=false;}
                else angle += angle>0 ? -step : step;
                rate=0;
                return;
            }
            float const x=Axis(pitch,maxPitch),y=Axis(yaw,maxYaw);
            float const turnStrength=std::sqrt(x*x+y*y);
            // Hysteresis keeps small corrections from continually switching modes.
            // Mouse release also returns the rim while residual ship rotation decays.
            returning=!steeringActive || turnStrength<(returning ? .14f : .08f);
            float const forwardAngle=angle;
            float const homeRate=(std::max)(-MaxRate,(std::min)(MaxRate,-forwardAngle*2.5f));
            float const target=returning ? homeRate : TurnRate(pitch,yaw,maxPitch,maxYaw);
            // Exact integral of exponential response: equal motion at different FPS.
            constexpr float response=.16f;
            float const blend=1.f-std::exp(-dt/response);
            float const movement=target*dt+(rate-target)*response*blend;
            angle+=movement;
            angle=std::remainder(angle,ArrowSpacing);
            rate += (target-rate)*blend;
            if (returning && ((forwardAngle!=0 && forwardAngle*(forwardAngle+movement)<=0) ||
                (std::fabs(forwardAngle)<.0001f && std::fabs(rate)<.0001f)))
                {angle=rate=0;}
            if (target==0 && std::fabs(rate)<.00001f) rate=0;
        }
    };
}
