#pragma once
#include "train_joint_math.h"
#include <vector>

namespace TrainJoint {
struct Capsule {V a,b;double radius;};
inline V worldPoint(const Body& b,V p) {return b.position+b.originOffset+b.rotation.mul(p);}
inline void nearestSegments(V a,V b,V c,V d,V& pa,V& pb) {
    const V u=b-a,v=d-c,w=a-c;
    const double uu=u.dot(u),vv=v.dot(v),uv=u.dot(v),uw=u.dot(w),vw=v.dot(w);
    double s=0,t=0;
    if(uu<1e-10) t=vv>1e-10?clamp(vw/vv,0,1):0;
    else if(vv<1e-10) s=clamp(-uw/uu,0,1);
    else {
        const double den=uu*vv-uv*uv;
        s=den>1e-10?clamp((uv*vw-vv*uw)/den,0,1):0;
        t=(uv*s+vw)/vv;
        if(t<0){t=0;s=clamp(-uw/uu,0,1);}
        else if(t>1){t=1;s=clamp((uv-uw)/uu,0,1);}
    }
    pa=a+u*s;pb=c+v*t;
}
inline void addContact(Body* bodies,int i,int j,Capsule ca,Capsule cb,double dt,std::vector<Contact>& out) {
    Body& a=bodies[i];Body& b=bodies[j];V pa,pb;
    nearestSegments(worldPoint(a,ca.a),worldPoint(a,ca.b),worldPoint(b,cb.a),worldPoint(b,cb.b),pa,pb);
    V n=pb-pa;const double distance=n.length();
    const double gap=distance-ca.radius-cb.radius;
    if(gap>2+(b.velocity-a.velocity).length()*dt)return;
    if(distance>1e-6)n=n*(1/distance);
    else {
        // Crossing centrelines need a deterministic lateral escape, not a
        // divide by zero or an arbitrary vertical launch.
        n=a.rotation.axes[0];
        if((b.position-a.position).dot(n)<0)n=-n;
    }
    const V point=(pa+n*ca.radius+pb-n*cb.radius)*.5;
    Contact c;c.a=i;c.b=j;c.normal=n;c.ra=point-a.position;c.rb=point-b.position;
    const double inv=a.inverseMass+b.inverseMass+
        c.ra.cross(n).dot(a.invI(c.ra.cross(n)))+c.rb.cross(n).dot(b.invI(c.rb.cross(n)));
    if(inv<1e-12)return;
    c.inverseEffectiveMass=1/inv;
    const double closing=(b.pointVelocity(c.rb)-a.pointVelocity(c.ra)).dot(n);
    // Speculative contact brakes before overlap. Existing intersections separate
    // gently, with bounded bias/impulse and no restitution or pose teleport.
    c.target=gap>0 ? -gap/dt : (std::min)(2.0,-gap*.8);
    if(closing>=c.target)return;
    c.maxImpulse=((std::max)(0.0,-closing)+(std::min)(2.0,12*dt))/inv;
    out.push_back(c);
}
inline void trainContacts(Body* bodies,int count,double dt,bool locomotive,std::vector<Contact>& out) {
    out.clear();
    if(!(dt>0 && dt<=.2) || count<1 || count>20)return;
    // Model-local envelopes, leaving the coupling pins outside the rounded ends.
    const Capsule wagon={{-.1,3,9},{-.1,3,34},8};
    const int first=locomotive?1:0;
    for(int i=first;i<=count;++i)for(int j=i+2;j<=count;++j)
        addContact(bodies,i,j,wagon,wagon,dt,out); // neighbouring wagons must articulate
    if(locomotive)for(int j=1;j<=count;++j) {
        addContact(bodies,0,j,{{-.1,0,-33},{-.1,0,4},10},wagon,dt,out);
        // Two engine nacelles, measured from the locomotive CMP child transforms.
        addContact(bodies,0,j,{{16.69,-14.05,-21},{16.69,-14.05,-16},8.5},wagon,dt,out);
        addContact(bodies,0,j,{{-16.90,-14.05,-21},{-16.90,-14.05,-16},8.5},wagon,dt,out);
    }
}
}
