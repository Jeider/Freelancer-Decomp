#pragma once
#include <string>

// Opaque asteroids and solar hulls share one coverage mask for fog extinction.
// Surviving samples keep their material; colour and depth share the same holes.
namespace Rp9SurfaceFade {
inline std::string Wrap(std::string const& source) {
    return std::string("#define PSMain Rp9UnfadedMain\n#define SURFACE_PIXEL_COVERAGE 1\n"
        "float4 ObjectCoverage : register(c109);\n")+source+R"(
#undef PSMain
float4 PSMain(SurfacePixel In, float2 Pixel : VPOS) : COLOR0
{
    float Coverage=ObjectCoverage.x;
    if(ObjectCoverage.y>0 && Fog.w>.5) {
        float Transmission=SurfaceFogPathTransmission(In.ViewPosition);
        Coverage*=Transmission/max(Transmission,ObjectCoverage.y);
    }
    float2 P=floor(Pixel);
    float2 B0=fmod(P,2), B1=fmod(floor(P*.5),2), B2=fmod(floor(P*.25),2);
    float A=2*abs(B0.x-B0.y)+B0.y;
    float B=2*abs(B1.x-B1.y)+B1.y;
    float C=2*abs(B2.x-B2.y)+B2.y;
    clip(Coverage-(16*A+4*B+C+.5)/64);
    return Rp9UnfadedMain(In);
}
)";
}
inline bool Variant(std::string prefix) {
    const std::string cube="#define SURFACE_ENV_CUBE 1\n";
    if(prefix.size()>=cube.size() && prefix.compare(prefix.size()-cube.size(),cube.size(),cube)==0)
        prefix.resize(prefix.size()-cube.size());
    return prefix.empty() || prefix=="#define SURFACE_LOW_DETAIL 1\n" || prefix=="#define SURFACE_NO_SHADOW 1\n" ||
        prefix=="#define SURFACE_SHIP_NORMALS 1\n" || prefix=="#define SURFACE_SHIP_NORMALS 1\n#define SURFACE_NO_SHADOW 1\n" ||
        prefix=="#define SURFACE_ROCK 1\n#define SURFACE_NO_SHADOW 1\n" ||
        prefix=="#define SURFACE_ROCK 1\n";
}
}
