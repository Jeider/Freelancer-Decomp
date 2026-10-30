#pragma once
#include "flight_action_math.h"

// Ship-relative camera poses: no world position is frozen while the ship drifts.
// Independent of game interfaces so the hold/return trajectory can be simulated.
namespace FlightActionCamera {
using namespace FlightActionMath;
struct Q { V xyz; float w=1; };
inline float dot(Q a,Q b) { return dot(a.xyz,b.xyz)+a.w*b.w; }
inline Q normalized(Q q) {
    float n=std::sqrt(dot(q,q));
    return n>1e-6f ? Q{q.xyz*(1/n),q.w/n} : Q{};
}
inline Q conjugate(Q q) { return {q.xyz*-1.f,q.w}; }
inline Q operator*(Q a,Q b) {
    return {b.xyz*a.w+a.xyz*b.w+cross(a.xyz,b.xyz),a.w*b.w-dot(a.xyz,b.xyz)};
}
inline Q axisAngle(V axis,float angle) { return {axis*std::sin(angle/2),std::cos(angle/2)}; }
inline V transform(Q q,V v) {
    V twice=cross(q.xyz,v)*2.f;
    return v+twice*q.w+cross(q.xyz,twice);
}
inline Q slerp(Q a,Q b,float t) {
    float cosine=dot(a,b);
    if(cosine<0) { b={b.xyz*-1.f,-b.w}; cosine=-cosine; }
    float wa=1-t,wb=t;
    if(cosine<0.9995f) {
        float angle=std::acos(std::clamp(cosine,0.f,1.f));
        float sine=std::sin(angle);
        wa=std::sin((1-t)*angle)/sine; wb=std::sin(t*angle)/sine;
    }
    return normalized({a.xyz*wa+b.xyz*wb,a.w*wa+b.w*wb});
}
inline Q fromMatrix(float const* m) {
    Q q;
    float trace=m[0]+m[4]+m[8];
    if(trace>0) {
        float s=std::sqrt(trace+1.f)*2.f;
        q={{(m[7]-m[5])/s,(m[2]-m[6])/s,(m[3]-m[1])/s},s/4};
    } else if(m[0]>m[4] && m[0]>m[8]) {
        float s=std::sqrt(1+m[0]-m[4]-m[8])*2.f;
        q={{s/4,(m[1]+m[3])/s,(m[2]+m[6])/s},(m[7]-m[5])/s};
    } else if(m[4]>m[8]) {
        float s=std::sqrt(1+m[4]-m[0]-m[8])*2.f;
        q={{(m[1]+m[3])/s,s/4,(m[5]+m[7])/s},(m[2]-m[6])/s};
    } else {
        float s=std::sqrt(1+m[8]-m[0]-m[4])*2.f;
        q={{(m[2]+m[6])/s,(m[5]+m[7])/s,s/4},(m[3]-m[1])/s};
    }
    return normalized(q);
}
inline void toMatrix(Q q,float* m) {
    V axes[]={transform(q,{1,0,0}),transform(q,{0,1,0}),transform(q,{0,0,1})};
    for(int i=0;i<3;++i) { m[i]=axes[i].x; m[i+3]=axes[i].y; m[i+6]=axes[i].z; }
}
struct Pose { V offset; Q rotation; };
inline Q levelCourse(V forward,V up) {
    V back=unit(forward)*-1.f;
    V right=unit(cross(up,back));
    if(length(right)<0.5f)
        right=unit(cross(std::abs(back.y)<0.9f ? V{0,1,0}:V{1,0,0},back));
    V levelUp=cross(back,right);
    float m[]={right.x,levelUp.x,back.x,right.y,levelUp.y,back.y,right.z,levelUp.z,back.z};
    return fromMatrix(m);
}
inline Pose blendCourse(Pose normal,Q course,V localOffset,float blend) {
    Q rotation=slerp(normal.rotation,course,blend);
    V nativeLocal=transform(conjugate(normal.rotation),normal.offset);
    return {transform(rotation,nativeLocal*(1-blend)+localOffset*blend),rotation};
}

inline float remainingTurnTime(float progress,float angularSpeed,bool resumeEngine,float throttle) {
    // Anticipate only the last half of a powered reversal. Coasting / zero
    // throttle keeps the existing wait for actual forward travel or manual input.
    if(!resumeEngine || !(throttle>0) || !(progress>=Pi/2) || !(angularSpeed>0.05f) ||
        !std::isfinite(progress) || !std::isfinite(angularSpeed)) return -1;
    return std::max(0.f,Pi-progress)/angularSpeed;
}

struct ReverseTurnCamera {
    static constexpr float LeadSeconds=2.f;
    static constexpr float ReturnSeconds=3.f;
    enum Stage { Off,Holding,Waiting,Returning } stage=Off;
    Pose held;
    V up{0,1,0};
    float forwardSeconds=0,returnSeconds=0,yaw=0;
    bool haveYaw=false;
    bool running() const { return stage!=Off; }
    bool holding() const { return stage==Holding || stage==Waiting; }
    void reset() { *this=ReverseTurnCamera{}; }
    void begin(Pose pose,V shipUp) {
        reset(); held=pose; up=unit(shipUp); stage=Holding;
    }
    void complete() { if(stage==Holding) stage=Waiting; }
    void cancel() {
        if(!holding()) return;
        stage=Returning; returnSeconds=0; haveYaw=false;
    }
    Pose update(Pose normal,V velocity,V forward,float dt,float turnSecondsRemaining=-1.f) {
        float step=std::isfinite(dt) ? std::clamp(dt,0.f,0.1f) : 0.f;
        if(stage==Holding && step>0 && std::isfinite(turnSecondsRemaining) &&
            turnSecondsRemaining>=0 && turnSecondsRemaining<=LeadSeconds)
            cancel();
        if(stage==Waiting) {
            float speed=length(velocity),ahead=dot(velocity,forward);
            // Actual forward travel, stable for 0.2 s, rather than engine activation
            // or the near-zero velocity flicker as reverse drift is braked away.
            bool moving=std::isfinite(speed) && ahead>3.f && ahead>speed*0.5f;
            forwardSeconds=moving ? forwardSeconds+step : 0;
            if(forwardSeconds>=0.2f) cancel();
        }
        if(holding()) return held;
        if(stage==Off) return normal;
        returnSeconds+=step;
        if(returnSeconds>=ReturnSeconds) { reset(); return normal; }
        float fraction=returnSeconds/ReturnSeconds;
        float t=fraction*fraction*(3-2*fraction);
        float h0=dot(held.offset,up),h1=dot(normal.offset,up);
        V radial0=held.offset-up*h0,radial1=normal.offset-up*h1;
        float r0=length(radial0),r1=length(radial1);
        if(r0<1e-3f || r1<1e-3f) { reset(); return normal; }
        V a=radial0*(1/r0),b=radial1*(1/r1);
        float raw=std::atan2(dot(up,cross(a,b)),dot(a,b));
        // Pick the ship turn's side near 180 degrees, then unwrap so camera
        // shake or a moving destination cannot flip the orbit halfway through.
        if(!haveYaw) { yaw=raw < -Pi+0.1f ? raw+2*Pi : raw; haveYaw=true; }
        else yaw+=std::remainder(raw-yaw,2*Pi);
        Q sweep=axisAngle(up,yaw*t);
        Q residual=conjugate(axisAngle(up,yaw))*normal.rotation;
        Pose result;
        result.offset=transform(sweep,a)*(r0+(r1-r0)*t)+up*(h0+(h1-h0)*t);
        result.rotation=normalized(sweep*slerp(held.rotation,residual,t));
        return result;
    }
};
}
