#pragma once
#include <cmath>

inline float JumpHoleExteriorVisibility(bool HasIdle,float Opening)
{
    if(HasIdle) return 1;
    if(!std::isfinite(Opening) || Opening<=0) return 0;
    if(Opening>=1) return 1;
    return Opening*Opening*(3-2*Opening);
}

// Smooth only the last tenth of an authored limit; never extend it.
inline float JumpHoleRangeVisibility(float Distance, float Limit)
{
    if (!std::isfinite(Distance) || !std::isfinite(Limit) || Limit<=0) return 0;
    float T=(Limit-Distance)/(Limit*.10f);
    if(T<=0) return 0;
    if(T>=1) return 1;
    return T*T*(3-2*T);
}

inline float JumpHolePbubbleLimit(float Near,float Far,float Perf)
{
    if(!std::isfinite(Near)||!std::isfinite(Far)||!std::isfinite(Perf)) return 0;
    Perf=Perf<0 ? 0 : Perf>1 ? 1 : Perf;
    return Near+(Far-Near)*(1-Perf);
}

// Retain the luminosity gradient of the blue source volume while matching its
// bright wall to the authored tunnel/nebula hue. The floor keeps smoky shadows.
inline bool JumpHolePaletteMultiplier(float const* Hue,float* Out)
{
    float Peak=0;
    for(int I=0;I<3;++I) {
        if(!std::isfinite(Hue[I]) || Hue[I]<0) return false;
        if(Hue[I]>Peak) Peak=Hue[I];
    }
    if(Peak<.001f) return false;
    float const Source[3]={.60f,.82f,1};
    for(int I=0;I<3;++I) Out[I]=(.18f+.82f*Hue[I]/Peak)/Source[I];
    Out[3]=0;
    return true;
}
