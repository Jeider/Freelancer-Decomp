#pragma once
#include <algorithm>
#include <cmath>

// Screen size is normalized to a 1080-high viewport, independent of resolution.
namespace CharacterQuality
{
    inline float ScreenSize(float radius, float depth, float nearPlane, float yScale, float height)
    {
        if (!std::isfinite(radius+depth+nearPlane+yScale+height) || radius<=0 ||
            height<=0 || depth-radius<=nearPlane || nearPlane<=0 || yScale==0) return -1;
        return 2160.f*radius*std::abs(yScale)/(height*std::sqrt(depth*depth-radius*radius));
    }
    inline float Threshold(int level, int boundary)
    {
        static const float normal[]={240,60,30}, high[]={120,40,20};
        return level>=3 ? high[boundary] : normal[boundary];
    }
    inline int Tier(float pixels, int level)
    {
        if (!(pixels>=0) || !std::isfinite(pixels)) return 0;
        int tier=0;while(tier<3 && pixels<Threshold(level,tier))++tier;return tier;
    }
    struct State { int Tier=0; bool Valid=false; };
    inline int Update(State& state,float pixels,int level,bool reset)
    {
        if (!(pixels>=0) || !std::isfinite(pixels)) {state=State{};return 0;}
        if(reset || !state.Valid) state.Tier=Tier(pixels,level);
        else {
            while(state.Tier<3 && pixels<Threshold(level,state.Tier)*.85f)++state.Tier;
            while(state.Tier>0 && pixels>Threshold(level,state.Tier-1)*1.15f)--state.Tier;
        }
        state.Valid=true;return state.Tier;
    }
    inline float Strength(float pixels,int level)
    {
        if(level<=0)return 0;
        if(!(pixels>=0) || !std::isfinite(pixels))return 1;
        float lo=level>=3?45.f:120.f,hi=level>=3?75.f:180.f;
        float t=(std::max)(0.f,(std::min)(1.f,(pixels-lo)/(hi-lo)));
        return t*t*(3-2*t); // Full normal-map quality; fade the final added response.
    }
    // Native level -1 is the added super LOD. Mapping is recorded while loading,
    // so skipped/failed meshes and legacy low_character_lod are handled exactly.
    inline int Pick(int requested,int count,int const* nativeLevels,int tier)
    {
        if(requested<0 || requested>=count || tier<=0)return requested;
        int minimum=tier-1,index=0;
        while(index+1<count && nativeLevels[index]<minimum)++index;
        return (std::max)(requested,index);
    }
}
