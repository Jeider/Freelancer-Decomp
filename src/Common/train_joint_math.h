#pragma once
// Small velocity-level sequential impulse solver shared by runtime and CPU tests.
// Coordinates/inertia are world-space, independent of the render frame rate.
#include <cmath>
#include <algorithm>

namespace TrainJoint {
struct V {
    double x=0,y=0,z=0;
    V operator+(V b) const {return {x+b.x,y+b.y,z+b.z};}
    V operator-(V b) const {return {x-b.x,y-b.y,z-b.z};}
    V operator*(double s) const {return {x*s,y*s,z*s};}
    V operator-() const {return *this*-1;}
    double dot(V b) const {return x*b.x+y*b.y+z*b.z;}
    V cross(V b) const {return {y*b.z-z*b.y,z*b.x-x*b.z,x*b.y-y*b.x};}
    double length() const {return std::sqrt(dot(*this));}
};
struct M {
    V axes[3]={{1,0,0},{0,1,0},{0,0,1}};
    V mul(V v) const {return axes[0]*v.x+axes[1]*v.y+axes[2]*v.z;}
    V inv(V v) const {return {axes[0].dot(v),axes[1].dot(v),axes[2].dot(v)};}
};
struct Body {
    V position,velocity,omega,originOffset;
    M rotation, inertiaAxes;
    V inverseInertia;
    double inverseMass=0;
    bool endPose=false; // Kinematic head has already been beamed to this PSI's end.
    bool braking=false; // Stop yaw motion without unfolding a stopped train.
    double cruiseStability=0; // Fade in yaw stabilization along the whole train.
    V invI(V v) const {
        V q=inertiaAxes.inv(v);
        return inertiaAxes.mul({q.x*inverseInertia.x,q.y*inverseInertia.y,q.z*inverseInertia.z});
    }
    V pointVelocity(V r) const {return velocity+omega.cross(r);}
    void impulse(V r,V p) {velocity=velocity+p*inverseMass;omega=omega+invI(r.cross(p));}
};
struct Joint {
    int a=0,b=1;
    V anchorA,anchorB;
    double accumulatedAngular[3]={};
};
inline double clamp(double x,double a,double b) {return (std::max)(a,(std::min)(b,x));}
inline V relativeAngle(const M& a,const M& b) {
    // Log of B*A^T, including the pi singularity (limits normally keep it far away).
    V skew;
    double trace=0;
    for(int i=0;i<3;++i) {skew=skew+a.axes[i].cross(b.axes[i]);trace+=a.axes[i].dot(b.axes[i]);}
    double angle=std::acos(clamp((trace-1)*.5,-1,1));
    double s=skew.length();
    if(s>1e-8) return skew*(angle/s);
    if(angle<.01) return skew*.5;
    return a.axes[0]*angle;
}
inline V curvedMotion(V r,V omega,double dt) {
    // Difference between a rotating anchor's arc and its tangent over one PSI.
    // Without this term, long fast-turning chains accumulate O(dt^2) joint gaps.
    const double speed=omega.length(),angle=speed*dt;
    if(angle<1e-5)return omega.cross(omega.cross(r))*(.5*dt*dt);
    V axis=omega*(1/speed);
    return r*(std::cos(angle)-1)+axis.cross(r)*std::sin(angle)+axis*(axis.dot(r)*(1-std::cos(angle)))-omega.cross(r)*dt;
}
inline V upError(const M& reference,const M& wagon) {
    V axis=reference.axes[1].cross(wagon.axes[1]);
    const double sine=axis.length(),cosine=clamp(reference.axes[1].dot(wagon.axes[1]),-1,1);
    if(sine>1e-8)return axis*(std::atan2(sine,cosine)/sine);
    return cosine<0?reference.axes[0]*3.141592653589793:V{};
}
inline double tailWeight(int wagon,int count) {
    const double x=clamp(2.0*wagon/count-1,0,1);
    return x*x*(3-2*x); // Smoothly stiffen only the rear half of the consist.
}
inline void dampWagon(Body& body,double dt,double lateralRate,double brakeRate,double targetSpeed,double angularRate=1.5) {
    // These are brakes, never a motor: every component can only lose kinetic
    // energy. A shared throttle target is independent of the head's disturbed
    // velocity, so a tail impulse cannot become a new acceleration command.
    const V forward=-body.rotation.axes[2];
    const double along=body.velocity.dot(forward);
    const double allowed=along*targetSpeed>0?std::copysign((std::min)(std::abs(along),std::abs(targetSpeed)),along):0;
    const double slowed=allowed+(along-allowed)*std::exp(-brakeRate*dt);
    body.velocity=(body.velocity-forward*along)*std::exp(-lateralRate*dt)+forward*slowed;
    body.omega=body.omega*std::exp(-angularRate*dt);
}
inline void solve(Body* bodies, Joint* joints,int count,double dt,bool powered=true) {
    if(!(dt>0 && dt<=.2) || count<1 || count>20)return;
    for(int j=0;j<count;++j)for(double& v:joints[j].accumulatedAngular)v=0;
    // Long chains need impulses to converge across their full length. Cache all
    // pose/inertia terms once per PSI; only velocities vary in the iterations.
    const int iterations=(std::max)(20,2*count*count);
    const V guideOmega=bodies[0].omega;
    // Locomotive stabilization cancels coupling reaction torque, preserving
    // the turning rate already produced by steering, damping and head contacts.
    // Linear mass and reaction remain physical. This is an active attitude
    // assist, not conservation of angular momentum for an unpowered chain.
    const V axes[3]={{1,0,0},{0,1,0},{0,0,1}};
    struct Row {V angularA,angularB,n;double inv,bias,gamma;};
    struct Prepared {V ra,rb,error;Row linear[3],angular[3],upright[2],follow;double uprightImpulse[2]={};double followImpulse=0;};
    Prepared prepared[20];
    for(int j=0;j<count;++j) {
        Joint& joint=joints[j];Body& a=bodies[joint.a];Body& b=bodies[joint.b];
        auto& p=prepared[j];
        p.ra=a.rotation.mul(joint.anchorA)+a.originOffset;p.rb=b.rotation.mul(joint.anchorB)+b.originOffset;
        p.error=(b.position+p.rb)-(a.position+p.ra);
        V angle=relativeAngle(a.rotation,b.rotation);
        for(int axis=0;axis<3;++axis) {
            auto& l=p.linear[axis];l.n=axes[axis];
            V ca=p.ra.cross(l.n),cb=p.rb.cross(l.n);
            l.angularA=a.invI(ca);l.angularB=b.invI(cb);
            l.inv=a.inverseMass+b.inverseMass+ca.dot(l.angularA)+cb.dot(l.angularB);
            auto& r=p.angular[axis];r.n=a.rotation.axes[axis];
            r.angularA=a.invI(r.n);r.angularB=b.invI(r.n);
            r.inv=r.n.dot(r.angularA+r.angularB);
            // The modeled vertical pin bends freely in yaw. Pitch and roll are
            // restrained, rather than giving every link another 25 degrees to sag.
            const double tail=tailWeight(joint.b,count);
            const double value=angle.dot(r.n),limit=(axis==1?25-19*tail:(axis==0?3:2))*3.141592653589793/180;
            const double excess=value-clamp(value,-limit,limit);
            const double center=2*3.141592653589793*(axis==1?.35+2.15*tail:2.0);
            const double stop=excess!=0?2*3.141592653589793*5.0:0;
            const double stiffness=center*center+stop*stop;
            const double damping=axis==1?.95+.55*tail:.95;
            const double denom=2*damping*std::sqrt(stiffness)+dt*stiffness;
            r.gamma=r.inv/(dt*denom);
            // Keep the centering spring active past the limit. Replacing it by
            // only 'excess' used to drop the restoring torque at the boundary.
            r.bias=clamp((value*center*center+excess*stop*stop)/denom,-2,2);
            if(axis==1 && bodies[0].braking)r.bias=0;
        }
        // Active wagon gyros follow the locomotive's up, not a fixed world axis.
        // Referencing the head prevents small per-link errors accumulating down
        // the entire train. Two axes only: yaw articulation remains free.
        V tilt=upError(bodies[0].rotation,b.rotation);
        for(int axis=0;axis<2;++axis) {
            auto& r=p.upright[axis];r.n=bodies[0].rotation.axes[axis==0?0:2];
            r.angularB=b.invI(r.n);r.inv=r.n.dot(r.angularB);
            if(!powered)r.inv=0;
            const double omega=2*3.141592653589793*40.0;
            const double denom=2*1.1*omega+dt*omega*omega;
            r.gamma=r.inv/(dt*denom);
            r.bias=clamp(tilt.dot(r.n)*omega*omega/denom,-1.5,1.5);
        }
        auto& follow=p.follow;
        const double tail=(std::max)(tailWeight(joint.b,count),bodies[0].cruiseStability);
        follow.inv=0;
        if(powered && tail>0) {
            // Rear yaw gyros track the preceding wagon. Like the up stabilizer,
            // they act on this wagon only, without driving an upstream yaw motor.
            follow.n=bodies[0].rotation.axes[1];
            follow.angularB=b.invI(follow.n);follow.inv=follow.n.dot(follow.angularB);
            const double omega=2*3.141592653589793*80*tail;
            const double denom=2*1.2*omega+dt*omega*omega;
            follow.gamma=follow.inv/(dt*denom);
            follow.bias=clamp(angle.dot(follow.n)*omega*omega/denom,-.05,.05);
            if(bodies[0].braking)follow.bias=0;
        }
    }
    for(int it=0;it<iterations;++it) {
      for(int k=0;k<count;++k) {
        const int index=(it&1)?count-1-k:k;
        Joint& joint=joints[index];auto& p=prepared[index];
        Body& a=bodies[joint.a];Body& b=bodies[joint.b];
        if(it%20==0) {
            // A remote head already occupies its end-of-step target. Match that
            // anchor in this step, without predicting its translation twice or
            // limiting the wagons to the ordinary 12 m/s drift correction.
            V bias=(p.error*(a.endPose?1.0:.35)+curvedMotion(p.rb,b.omega,dt)-curvedMotion(p.ra,a.omega,dt))*(1/dt);
            for(auto& r:p.linear)r.bias=a.endPose?bias.dot(r.n):clamp(bias.dot(r.n),-12,12);
        }
        for(const auto& r:p.linear) {
            if(r.inv<1e-12)continue;
            double lambda=-((b.pointVelocity(p.rb)-a.pointVelocity(p.ra)).dot(r.n)+r.bias)/r.inv;
            a.velocity=a.velocity-r.n*(lambda*a.inverseMass);b.velocity=b.velocity+r.n*(lambda*b.inverseMass);
            a.omega=a.omega-r.angularA*lambda;b.omega=b.omega+r.angularB*lambda;
        }
        for(int axis=0;axis<2;++axis) {
            const auto& r=p.upright[axis];if(r.inv<1e-12)continue;
            const double lambda=-((b.omega-guideOmega).dot(r.n)+r.bias+r.gamma*p.uprightImpulse[axis])/(r.inv+r.gamma);
            p.uprightImpulse[axis]+=lambda;
            b.omega=b.omega+r.angularB*lambda;
        }
        if(p.follow.inv>1e-12) {
            const auto& r=p.follow;
            // Share the head's turning rate so rear yaw velocity errors cannot
            // accumulate down the chain, while the angle follows the preceding
            // wagon with a bounded correction (2.9 degrees per second).
            // Snapshot before the solve: a reaction from this very gyro must
            // not feed back into its own target during the impulse iterations.
            const double lambda=-((b.omega-guideOmega).dot(r.n)+r.bias+r.gamma*p.followImpulse)/(r.inv+r.gamma);
            p.followImpulse+=lambda;
            b.omega=b.omega+r.angularB*lambda;
        }
        double* accumulated=joint.accumulatedAngular;
        for(int axis=0;axis<3;++axis) {
            const auto& r=p.angular[axis];
            if(r.inv<1e-12)continue;
            double lambda=-((b.omega-a.omega).dot(r.n)+r.bias+r.gamma*accumulated[axis])/(r.inv+r.gamma);
            accumulated[axis]+=lambda;
            a.omega=a.omega-r.angularA*lambda;b.omega=b.omega+r.angularB*lambda;
        }
      }
      if(powered)bodies[0].omega=guideOmega;
    }
}
}
