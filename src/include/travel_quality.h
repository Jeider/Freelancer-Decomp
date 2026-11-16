#pragma once

// Independent travel profiles. Zero retains a cheap visible travel effect.
namespace TravelQuality
{
    inline char const* TradeLaneEntry(int level)
    {
        static char const* const entries[]={"PSStandard","PSLow","PSMedium","PSMain"};
        return entries[level>=0&&level<=3?level:3];
    }
    inline float HyperspaceScale(int level)
    {
        return level<=0?0.f:level==1?.25f:level==2?1.f/3.f:.5f;
    }
}
