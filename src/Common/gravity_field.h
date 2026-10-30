#pragma once
#include <algorithm>
#include <cmath>

namespace GravityField
{
struct Vector { double x=0, y=0, z=0; };
enum class Mode { Attract, Repel, Suppress };
struct Settings
{
    Mode mode=Mode::Attract;
    double suppression=1;
    double radius=20000;
    double referenceRadius=5000;
    double acceleration=60;
    double softening=650;
    double maxAcceleration=300;
    double edgeFraction=.2;
};

inline bool Finite(Vector v)
{
    return std::isfinite(v.x) && std::isfinite(v.y) && std::isfinite(v.z);
}

inline double Length(Vector v) { return std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z); }

inline double EdgeWeight(Settings const& s, double r)
{
    if (!(r>=0 && r<s.radius)) return 0;
    double start=s.radius*(1-s.edgeFraction);
    if (r<=start) return 1;
    double t=(s.radius-r)/(s.radius-start);
    return t*t*(3-2*t);
}

inline double Suppression(Settings const& s, Vector source, Vector position)
{
    if (s.mode!=Mode::Suppress || !Finite(source) || !Finite(position)) return 0;
    return s.suppression*EdgeWeight(s,Length({source.x-position.x,source.y-position.y,source.z-position.z}));
}

// Softened inverse-square field. The acceleration setting is the magnitude at
// referenceRadius before the outer fade/cap. Inside the soft core it tends to
// zero continuously, so crossing the centre cannot divide by zero or flip an
// infinite impulse. This is tunable game physics, independent of lensing units.
inline Vector Sample(Settings const& s, Vector source, Vector position)
{
    if (s.mode==Mode::Suppress || !Finite(source) || !Finite(position)) return {};
    Vector d{source.x-position.x,source.y-position.y,source.z-position.z};
    double r=Length(d);
    if (!(r>0 && r<s.radius) || s.acceleration<=0) return {};
    double core2=s.softening*s.softening;
    double reference2=s.referenceRadius*s.referenceRadius+core2;
    double mu=s.acceleration*reference2*std::sqrt(reference2)/s.referenceRadius;
    double distance2=r*r+core2;
    double magnitude=mu*r/(distance2*std::sqrt(distance2));
    magnitude=(std::min)(magnitude,s.maxAcceleration);
    magnitude*=EdgeWeight(s,r);
    double scale=(s.mode==Mode::Repel ? -magnitude : magnitude)/r;
    return {d.x*scale,d.y*scale,d.z*scale};
}
}
