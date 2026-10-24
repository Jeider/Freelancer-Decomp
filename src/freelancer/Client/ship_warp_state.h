#pragma once
#include <cmath>
#include <cstring>
#include <cctype>
#include "ship_warp_mesh.h"

inline bool ShipWarpTrailName(char const* Name)
{
    if(!Name) return false;
    char const* Prefixes[]={"hpcontrail","hpcontail"};
    for(char const* Prefix:Prefixes)
    {
        unsigned I=0;
        while(Prefix[I] && Name[I] && std::tolower(static_cast<unsigned char>(Name[I]))==Prefix[I]) ++I;
        if(Prefix[I] || !Name[I]) continue;
        for(;Name[I];++I) if(Name[I]<'0' || Name[I]>'9') return false;
        return true;
    }
    return false;
}
inline float ShipWarpSmooth(float T)
{
    T=T<0?0:T>1?1:T;
    return T*T*(3-2*T);
}
struct FShipWarpClock
{
    float Time=0,Age=0,ExitAge=0,Intensity=0,ExitIntensity=0,StartIntensity=0;
    bool Stopping=false;
    void Stop() {if(!Stopping) {Stopping=true;ExitAge=0;ExitIntensity=Intensity;}}
    void Resume() {if(Stopping) {Stopping=false;Age=0;StartIntensity=Intensity;}}
    void Tick(float Dt)
    {
        if(!std::isfinite(Dt)||Dt<=0) return;
        Time=std::fmod(Time+Dt,96.0f);
        if(Stopping) {ExitAge+=Dt;Intensity=ExitIntensity*(1-ShipWarpSmooth(ExitAge/.45f));}
        else {Age=Age+Dt<1?Age+Dt:1;Intensity=StartIntensity+(1-StartIntensity)*ShipWarpSmooth(Age/.25f);}
    }
};

// Fixed storage and simulation time only: drawing/extra cameras never advance a trail.
struct FShipWarpHistory
{
    struct FSample {FShipWarpPoint Pos;float Age;};
    FSample Samples[64]={};
    unsigned Count=0;
    float SinceSample=0;
    void Clear() {Count=0;SinceSample=0;}
    void Tick(FShipWarpPoint Pos,float Dt)
    {
        if(!ShipWarpMesh::Finite(Pos)||!std::isfinite(Dt)||Dt<=0) return;
        for(unsigned I=0;I<Count;++I) Samples[I].Age+=Dt;
        while(Count && Samples[Count-1].Age>.8f) --Count;
        SinceSample+=Dt;
        if(Count && SinceSample<1.f/90) return;
        SinceSample=std::fmod(SinceSample,1.f/90);
        Count=(std::min)(Count+1,64u);
        for(unsigned I=Count-1;I>0;--I) Samples[I]=Samples[I-1];
        Samples[0]={Pos,0};
    }
    unsigned Path(FShipWarpPoint Head,FShipWarpPoint Back,float Wind,float MaxLength,FShipWarpPoint* Out) const
    {
        using namespace ShipWarpMesh;
        if(!Out||!Finite(Head)||!Finite(Back)||!std::isfinite(Wind)||!std::isfinite(MaxLength)||MaxLength<=0) return 0;
        Out[0]=Head; unsigned N=1;float Length=0;
        for(unsigned I=0;I<Count && N<33;++I)
        {
            auto P=Add(Samples[I].Pos,Mul(Back,Samples[I].Age*Wind));
            auto Delta=Sub(P,Out[N-1]);float D=std::sqrt(Dot(Delta,Delta));
            if(D<.001f) continue;
            if(Length+D>=MaxLength) {Out[N]=Add(Out[N-1],Mul(Delta,(MaxLength-Length)/D));++N;break;}
            Out[N++]=P;Length+=D;
        }
        return N;
    }
};
