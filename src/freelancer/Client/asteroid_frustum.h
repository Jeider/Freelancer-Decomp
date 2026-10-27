#pragma once
#include <cmath>

// Camera-space bounding sphere, forward positive. Tangents describe half-FOV.
// Testing the mesh centre alone is not conservative for large edge-straddling rocks.
inline bool AsteroidBoundsInFrustum(double x,double y,double z,double radius,
                                    double tanX,double tanY,double farDistance)
{
    const double rx=radius*std::sqrt(1+tanX*tanX);
    const double ry=radius*std::sqrt(1+tanY*tanY);
    return z>=-radius && z<=farDistance+radius &&
        x+z*tanX>=-rx && -x+z*tanX>=-rx &&
        y+z*tanY>=-ry && -y+z*tanY>=-ry;
}
