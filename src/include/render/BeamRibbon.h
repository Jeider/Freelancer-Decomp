#pragma once
#include <cmath>
#include <string>

// Local-space ribbon frame. Shared by the batched ALE renderer and its fixture.
namespace BeamRibbon
{
    inline bool NameMatches(std::string const& list, const char* name)
    {
        if (!name) return false;
        std::string lower(name);
        for (char& c : lower) if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
        size_t pos = 0;
        while (pos < list.size())
        {
            size_t end = list.find(',', pos);
            if (end == std::string::npos) end = list.size();
            std::string token = list.substr(pos, end - pos);
            size_t a = token.find_first_not_of(" \t"), b = token.find_last_not_of(" \t");
            if (a != std::string::npos)
            {
                token = token.substr(a, b - a + 1);
                if (token == "*" || lower.find(token) != std::string::npos) return true;
            }
            pos = end + 1;
        }
        return false;
    }
    inline unsigned long FadeColour(unsigned long colour, float depth, float nearPlane,
                                    float distance, bool sourceAlpha)
    {
        if (!(distance > 0) || !std::isfinite(distance)) return colour;
        float t = std::fmax(0.f, std::fmin(1.f, (depth - nearPlane) / distance));
        float fade = t*t*(3.f-2.f*t);
        if (sourceAlpha)
            return (colour & 0xfffffful) | (static_cast<unsigned long>((colour >> 24)*fade+.5f) << 24);
        unsigned long result = colour & 0xff000000ul;
        for(unsigned shift=0;shift<24;shift+=8)
            result |= static_cast<unsigned long>(((colour >> shift) & 255)*fade+.5f) << shift;
        return result;
    }
    struct Vec { float x, y, z; };
    inline Vec Sub(Vec a, Vec b) { return {a.x-b.x,a.y-b.y,a.z-b.z}; }
    inline Vec Mul(Vec a, float s) { return {a.x*s,a.y*s,a.z*s}; }
    inline float Dot(Vec a, Vec b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
    inline Vec Cross(Vec a, Vec b)
    { return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
    inline Vec Unit(Vec a, Vec fallback)
    {
        float n=Dot(a,a);
        return n>1e-12f && std::isfinite(n) ? Mul(a,1.f/std::sqrt(n)) : fallback;
    }
    inline Vec Side(Vec before, Vec position, Vec after, Vec camera,
                    Vec cameraRight, Vec cameraUp, Vec previous)
    {
        Vec incoming=Unit(Sub(position,before),{0,0,0});
        Vec outgoing=Unit(Sub(after,position),incoming);
        Vec axis=Unit({incoming.x+outgoing.x,incoming.y+outgoing.y,incoming.z+outgoing.z},outgoing);
        axis=Unit(axis,{0,0,1});
        Vec sight=Unit(Sub(camera,position),{0,0,1});
        Vec side=Cross(axis,sight);
        // At an end-on view the cross product has no reliable direction.
        if(Dot(side,side)<1e-6f)
        {
            side=Sub(cameraRight,Mul(axis,Dot(cameraRight,axis)));
            if(Dot(side,side)<1e-6f) side=Sub(cameraUp,Mul(axis,Dot(cameraUp,axis)));
        }
        side=Unit(side,{1,0,0});
        // Keep the two UV edges continuous around bends in a particle trail.
        if(Dot(side,previous)<0) side=Mul(side,-1);
        return side;
    }
}
