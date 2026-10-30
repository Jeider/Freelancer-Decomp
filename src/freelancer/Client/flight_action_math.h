#pragma once
#include <algorithm>
#include <cmath>

// Port-only flight control math, independent of engine interfaces for simulation tests.
namespace FlightActionMath {
constexpr float Pi = 3.14159265358979323846f;
struct ReverseStrafeCycle {
    double phase=0, interval=2;
    void reset(float seconds) {
        phase=0;
        interval=std::isfinite(seconds) && seconds>0 ? seconds : 2.0;
    }
    bool left() const { return phase<interval; }
    float sine() const { return -static_cast<float>(std::sin(double(Pi)*phase/interval)); }
    void advance(float dt) {
        // Keep a bounded double-precision phase even after hours of flight.
        if(std::isfinite(dt) && dt>0) phase=std::fmod(phase+dt,2*interval);
    }
};
struct V { float x=0, y=0, z=0; };
inline V operator+(V a,V b) { return {a.x+b.x,a.y+b.y,a.z+b.z}; }
inline V operator-(V a,V b) { return {a.x-b.x,a.y-b.y,a.z-b.z}; }
inline V operator*(V a,float b) { return {a.x*b,a.y*b,a.z*b}; }
inline float dot(V a,V b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
inline V cross(V a,V b) { return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline float length(V a) { return std::sqrt(dot(a,a)); }
inline V unit(V a) { float n=length(a); return n>1e-6f ? a*(1/n) : V{}; }
inline V rotate(V v,V axis,float angle) {
    float c=std::cos(angle),s=std::sin(angle);
    return v*c+cross(axis,v)*s+axis*(dot(axis,v)*(1-c));
}
inline float torque(float error,float omega,float inertia,float drag,float limit) {
    if (!(limit>0) || !std::isfinite(error) || !std::isfinite(omega)) return 0;
    // Critically damped orientation servo with physical drag compensation.
    float t=std::max(inertia,0.01f)*(36*error-12*omega)+std::max(drag,0.0f)*omega;
    return std::clamp(t/limit,-1.0f,1.0f);
}
inline float goal(float progress,float total) {
    // Keep the target close enough that the orientation error never reaches the
    // 180-degree singularity. Progress is unwrapped, including for a full roll.
    return std::min(total,std::max(0.0f,progress)+0.65f);
}
inline bool settled(float progress,float total,float error,float speed) {
    return std::abs(total-progress)<0.06f && error<0.04f && speed<0.10f;
}
}
