#pragma once
#include <cmath>
#include <initializer_list>

namespace AsteroidAvoidance {
struct Vec { double x, y, z; };
inline Vec Add(Vec a, Vec b) { return {a.x+b.x, a.y+b.y, a.z+b.z}; }
inline Vec Sub(Vec a, Vec b) { return {a.x-b.x, a.y-b.y, a.z-b.z}; }
inline Vec Mul(Vec a, double n) { return {a.x*n, a.y*n, a.z*n}; }
inline double Dot(Vec a, Vec b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
inline Vec Cross(Vec a, Vec b) { return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline Vec Unit(Vec a, Vec fallback) { double d=Dot(a,a); return d>1e-12 ? Mul(a,1/std::sqrt(d)) : fallback; }
inline bool Finite(Vec a) { return std::isfinite(a.x)&&std::isfinite(a.y)&&std::isfinite(a.z); }

// Time to first contact of two moving spheres; infinity means no contact in
// the horizon. Receding overlaps do not trap the ship in an avoidance loop.
inline double Contact(Vec offset, Vec relativeVelocity, double radius, double horizon) {
    double a=Dot(relativeVelocity,relativeVelocity), b=Dot(offset,relativeVelocity);
    double c=Dot(offset,offset)-radius*radius;
    if (c<=0) return b<=0 ? 0.0 : INFINITY;
    if (a<1e-12 || b>=0) return INFINITY;
    double discriminant=b*b-a*c;
    if (discriminant<0) return INFINITY;
    double t=(-b-std::sqrt(discriminant))/a;
    return t<=horizon ? t : INFINITY;
}

struct Rock { Vec position, velocity; double radius; };
struct Result { Vec direction; double speedScale; };
inline bool Choose(Vec position, Vec velocity, Vec goal, Vec right,
                   double shipRadius, Rock const* rocks, unsigned count, Result& out) {
    if (!Finite(position)||!Finite(velocity)||!Finite(goal)||!std::isfinite(shipRadius)) return false;
    Vec desired=Unit(Sub(goal,position),Unit(velocity,{0,0,-1}));
    double speed=std::sqrt(Dot(velocity,velocity));
    if (speed<20) speed=20;
    double goalDistance=std::sqrt(Dot(Sub(goal,position),Sub(goal,position)));
    double horizon=3.0;
    if (goalDistance>1 && goalDistance/speed<horizon) horizon=goalDistance/speed;
    auto firstContact=[&](Vec v) {
        double earliest=INFINITY;
        for (unsigned i=0;i<count;++i) {
            Rock const& rock=rocks[i];
            if (!Finite(rock.position)||!Finite(rock.velocity)||!std::isfinite(rock.radius)||rock.radius<=0) continue;
            double t=Contact(Sub(rock.position,position),Sub(rock.velocity,v),
                             shipRadius+rock.radius+10.0,horizon);
            if (t<earliest) earliest=t;
        }
        return earliest;
    };
    double current=firstContact(velocity), intended=firstContact(Mul(desired,speed));
    if (!std::isfinite(current)&&!std::isfinite(intended)) return false;
    right=Unit(Sub(right,Mul(desired,Dot(right,desired))),
               Unit(Cross(desired,{0,1,0}),{1,0,0}));
    Vec up=Unit(Cross(right,desired),{0,1,0});
    // Evaluate a small deterministic fan, including braking, against every
    // nearby asteroid. Deterministic tie-breaking avoids random left/right flips.
    double best=-1e30;
    for (double scale : {0.7,0.4,0.15}) {
        for (double angle : {0.0,0.35,0.7,1.15}) {
            for (unsigned side=0;side<8;++side) {
                double phi=side*0.7853981633974483;
                Vec lateral=Add(Mul(right,std::cos(phi)),Mul(up,std::sin(phi)));
                Vec direction=Add(Mul(desired,std::cos(angle)),Mul(lateral,std::sin(angle)));
                double contact=firstContact(Mul(direction,speed*scale));
                double score=std::isfinite(contact) ? -100.0+contact : 0.0;
                score+=Dot(direction,desired)+scale*3.0;
                if (score>best) { best=score;out={direction,scale}; }
                if (angle==0) break;
            }
        }
    }
    // Give the existing flight controller room to turn; it applies this as a
    // throttle/approach scale, never as a teleport or direct velocity change.
    return true;
}
}
