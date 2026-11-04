#pragma once
#include <algorithm>
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

struct Rock { Vec position, velocity; double radius; unsigned id=0; };
struct Result { Vec direction; double speedScale; };
// The production wrapper owns one of these per PathfindManager. Keeping the
// lateral side, rather than the old absolute heading, lets the detour tighten
// and relax as the destination direction changes without left/right flicker.
struct Memory {
    unsigned rockId=0, rockIndex=0;
    bool engaged=false;
    Vec side{0,0,0};
};

inline bool Choose(Vec position, Vec velocity, Vec goal, Vec right,
                   double shipRadius, Rock const* rocks, unsigned count, Result& out,
                   Memory* memory=nullptr) {
    if (!Finite(position)||!Finite(velocity)||!Finite(goal)||!std::isfinite(shipRadius)||
        (count && !rocks)) return false;
    auto reset=[&]() { if (memory) *memory=Memory{}; };
    double goalDistance=std::sqrt(Dot(Sub(goal,position),Sub(goal,position)));
    if (goalDistance<1) { reset(); return false; }
    Vec desired=Unit(Sub(goal,position),Unit(velocity,{0,0,-1}));
    double speed=std::sqrt(Dot(velocity,velocity));
    if (speed<20) speed=20;
    double clearance=0.0;
    double expandedRadius=shipRadius+clearance;
    if (expandedRadius<0) expandedRadius=0;

    unsigned locked=count;
    if (memory && memory->engaged) {
        for (unsigned i=0;i<count;++i) {
            if ((memory->rockId && rocks[i].id==memory->rockId) ||
                (!memory->rockId && i==memory->rockIndex)) { locked=i; break; }
        }
    }
    double horizon=0.35;
    if (goalDistance/speed<horizon) horizon=goalDistance/speed;
    if (locked<count) {
        // Release the bypass as soon as the intended heading is clear again.
        // Distant rocks must not hold the ship in a long detour or cruise lock.
        Rock const& rock=rocks[locked];
        double intendedContact=Contact(Sub(rock.position,position),
            Sub(rock.velocity,Mul(desired,speed)),expandedRadius+rock.radius,horizon);
        if (!std::isfinite(intendedContact)) { reset(); locked=count; }
    }

    auto firstContact=[&](Vec v,unsigned* index=nullptr) {
        double earliest=INFINITY;
        for (unsigned i=0;i<count;++i) {
            Rock const& rock=rocks[i];
            if (!Finite(rock.position)||!Finite(rock.velocity)||!std::isfinite(rock.radius)||rock.radius<=0) continue;
            double t=Contact(Sub(rock.position,position),Sub(rock.velocity,v),
                             expandedRadius+rock.radius,horizon);
            if (t<earliest) { earliest=t; if (index) *index=i; }
        }
        return earliest;
    };

    unsigned critical=locked;
    if (critical==count) {
        unsigned intendedIndex=count;
        double intended=firstContact(Mul(desired,speed),&intendedIndex);
        // A rock near the current velocity is irrelevant when the autopilot's
        // actual destination heading already goes past it safely.
        if (!std::isfinite(intended)) { reset(); return false; }
        critical=intendedIndex;
    }
    if (critical>=count) { reset(); return false; }

    right=Unit(Sub(right,Mul(desired,Dot(right,desired))),
               Unit(Cross(desired,{0,1,0}),{1,0,0}));
    Vec up=Unit(Cross(right,desired),{0,1,0});
    Vec preferred{0,0,0};
    if (memory && memory->engaged)
        preferred=Unit(Sub(memory->side,Mul(desired,Dot(memory->side,desired))),{0,0,0});

    // Only a real physical overlap justifies a direct radial escape. Otherwise
    // use the smallest full-speed heading change that clears every nearby rock.
    Vec offset=Sub(position,rocks[critical].position);
    Vec escape=Unit(offset,right);
    double physicalRadius=(std::max)(0.0,shipRadius)+rocks[critical].radius;
    bool escaping=Dot(offset,offset)<physicalRadius*physicalRadius;

    double best=-1e30;
    bool found=false;
    if (escaping) {
        out={escape,1.0};
        found=true;
    } else {
        for (double angle : {0.0,0.15,0.35,0.7}) {
            for (unsigned side=0;side<8;++side) {
                double phi=side*0.7853981633974483;
                Vec lateral=Add(Mul(right,std::cos(phi)),Mul(up,std::sin(phi)));
                Vec direction=Add(Mul(desired,std::cos(angle)),Mul(lateral,std::sin(angle)));
                double contact=firstContact(Mul(direction,speed));
                if (std::isfinite(contact)) continue;
                double score=Dot(direction,desired);
                score+=Dot(lateral,preferred)*std::sin(angle)*.35;
                if (score>best) { best=score;out={direction,1.0};found=true; }
                if (angle==0) break;
            }
        }
    }
    // A dense field with no gentle full-speed opening is not a reason to brake
    // or reverse. Hand control back to the ordinary route and native avoidance.
    if (!found) { reset(); return false; }
    if (memory) {
        memory->engaged=true;
        memory->rockId=rocks[critical].id;
        memory->rockIndex=critical;
        Vec lateral=Sub(out.direction,Mul(desired,Dot(out.direction,desired)));
        memory->side=Unit(lateral,preferred);
    }
    // The flight controller still performs the physical turn. This extension
    // never asks for braking: speed remains under the normal autopilot's control.
    return Finite(out.direction);
}
}
