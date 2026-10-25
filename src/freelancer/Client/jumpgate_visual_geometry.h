#pragma once
#include <cmath>
#include <algorithm>
#include <vector>
#include "jumphole_visual_geometry.h"

// gf_tradelaneinship01.ale: shooter -40.7961426 Z, child donut -550 Z,
// 2 emissions/s, +Z speed 600 m/s, 1.5455 s life, child mean radius 100.8908.
constexpr float JumpGateDonutEmitterOffsetZ=-590.7961426f-100.f; // 100 m toward approach
constexpr int JumpGateDonutPulseCount=5;
constexpr float JumpGateDonutSpeed=425.f;
constexpr float JumpGateDonutFrequency=2.25f;
constexpr float JumpGateDonutInterval=1.f/JumpGateDonutFrequency;
constexpr float JumpGateDonutLifetime=1.5455f*600.f/JumpGateDonutSpeed;
inline void BuildJumpGateDonutPulses(float Time,float ActivationAge,float OriginZ,float* Out)
{
    float Emission=std::floor(Time*JumpGateDonutFrequency);
    float Fraction=Time-Emission*JumpGateDonutInterval;
    for(int I=0;I<JumpGateDonutPulseCount;++I) {
        float Age=Fraction+I*JumpGateDonutInterval;
        float Birth=Emission-I;
        float Seed=Birth-std::floor(Birth/16)*16;
        float FadeIn=(std::max)(0.f,(std::min)(1.f,Age/.30f));
        FadeIn=FadeIn*FadeIn*(3-2*FadeIn);
        float Gain=FadeIn*(std::max)(0.f,(std::min)(1.f,(JumpGateDonutLifetime-Age)/(210.f/JumpGateDonutSpeed)));
        if(Age>ActivationAge)Gain=0;
        Out[I*4]=OriginZ+JumpGateDonutSpeed*Age;
        Out[I*4+1]=Age; Out[I*4+2]=Seed; Out[I*4+3]=Gain;
    }
}

// GetProjection's transposed device matrix maps +Z-forward view coordinates to clip.
// The nominal camera horizontal FOV is still a 4:3 value in Hor+ mode. Never use it
// to reconstruct world-space rays: it stretches and displaces off-centre objects.
inline bool JumpGateProjectionRayParams(float const* Projection,float* Out)
{
    if (!std::isfinite(Projection[0]) || !std::isfinite(Projection[5]) ||
        !std::isfinite(Projection[2]) || !std::isfinite(Projection[6]) ||
        Projection[0]<=0 || Projection[5]<=0 ||
        std::fabs(Projection[14]-1)>1e-5f || std::fabs(Projection[15])>1e-5f) return false;
    Out[0]=1/Projection[0]; Out[1]=1/Projection[5];
    Out[2]=Projection[2]; Out[3]=Projection[6];
    return true;
}

inline float JumpGateInflowHash(unsigned Seed)
{
    Seed=(Seed^61u)^(Seed>>16); Seed*=9; Seed^=Seed>>4;
    Seed*=0x27d4eb2du; Seed^=Seed>>15;
    return float(Seed&0xffffu)/65536.f;
}
inline void JumpGateInflowPoint(unsigned Seed,float Age,float const* Source,
    float const* Portal,float const* PortalRows,float* Out,float Time=0)
{
    float Progress=Age*Age;
    // Five coherent spiral arms. Both the long wisps and small streaks travel on
    // this same field, with increasing axial and angular speed toward the throat.
    float Angle=6.2831853f*(float(Seed%5)/5+.10f*(JumpGateInflowHash(Seed)-.5f)+
        .55f*Age+.85f*Progress+Time/12);
    float C=std::cos(Angle),S=std::sin(Angle);
    float StartRadius=125+65*JumpGateInflowHash(Seed+301);
    float EndRadius=15+33*JumpGateInflowHash(Seed+701);
    float Radius=EndRadius+(StartRadius-EndRadius)*(1-Progress)*(1-.2f*Progress);
    // Pick a continuous radial frame facing solar +Z. The actual exit HP faces
    // -Z: interpolating its raw X row would pinch and reverse the vortex midway.
    float N[3]={PortalRows[8],PortalRows[9],PortalRows[10]},X[3],Y[3];
    if(N[2]<0)for(float& V:N)V=-V;
    int Axis=std::fabs(N[0])<.9f?0:1;
    float Length=0;
    for(int K=0;K<3;++K){X[K]=(K==Axis?1.f:0.f)-N[K]*N[Axis];Length+=X[K]*X[K];}
    Length=std::sqrt(Length);
    for(float& V:X)V/=Length;
    for(int K=0;K<3;++K)Y[K]=N[(K+1)%3]*X[(K+2)%3]-N[(K+2)%3]*X[(K+1)%3];
    for(int K=0;K<3;++K) {
        float Start=K==0?C:K==1?S:0;
        float End=C*X[K]+S*Y[K];
        Out[K]=Source[K]+(Portal[K]-Source[K])*Progress+Radius*(Start+(End-Start)*Progress);
    }
}
constexpr int JumpGateInflowCount=448,JumpGateInflowSegments=24;
constexpr int JumpGateInflowVertices=JumpGateInflowCount*JumpGateInflowSegments*6;
inline void BuildJumpGateInflow(float Time,float const* Source,float const* Portal,
    float const* PortalRows,float const* Eye,std::vector<FJumpHoleVertex>& Out)
{
    Out.clear(); if(Source[3]<=0)return;
    constexpr int Count=JumpGateInflowCount,Segments=JumpGateInflowSegments;
    Out.reserve(JumpGateInflowVertices);
    for(unsigned I=0;I<Count;++I) {
        float Lifetime=I%2?3.f:4.f; // both repeat exactly with the 192-second clock
        float Head=Time/Lifetime+JumpGateInflowHash(I+1103);
        Head-=std::floor(Head);
        bool Wisp=I%7==0;
        float Tail=(std::max)(0.f,Head-(Wisp?1.25f:.22f)/Lifetime);
        float Fade=(std::min)(1.f,Head*12)*(std::min)(1.f,(1-Head)*15);
        FJumpHoleVertex Strip[(Segments+1)*2];
        for(int J=0;J<=Segments;++J) {
            float U=float(J)/Segments,Age=Tail+(Head-Tail)*U;
            float P[3],Next[3],T[3],V[3],Side[3];
            JumpGateInflowPoint(I,Age,Source,Portal,PortalRows,P,Time);
            JumpGateInflowPoint(I,Age+.001f,Source,Portal,PortalRows,Next,Time);
            for(int K=0;K<3;++K){T[K]=Next[K]-P[K];V[K]=Eye[K]-P[K];}
            for(int K=0;K<3;++K)Side[K]=T[(K+1)%3]*V[(K+2)%3]-T[(K+2)%3]*V[(K+1)%3];
            float Len=std::sqrt(Side[0]*Side[0]+Side[1]*Side[1]+Side[2]*Side[2]);
            if(Len<1e-6f){Side[0]=1;Side[1]=Side[2]=0;Len=1;}
            float Width=(Wisp?9.f+5*JumpGateInflowHash(I+503):.85f+.65f*JumpGateInflowHash(I+503))*(.2f+.8f*std::sin(U*3.14159265f));
            for(int S=0;S<2;++S) {
                auto& Vertex=Strip[J*2+S];
                for(int K=0;K<3;++K)Vertex.Position[K]=P[K]+Side[K]/Len*Width*(S?1:-1);
                // R selects fine streak versus misty wisp, G supplies material variation.
                Vertex.Color=(unsigned(Fade*(Wisp?90:180))<<24)|(Wisp?0:0xff0000u)|
                    (unsigned(JumpGateInflowHash(I+907)*255)<<8)|0xffu;
                Vertex.UV[0]=S?1.f:-1.f;Vertex.UV[1]=U;
            }
        }
        for(int J=0;J<Segments;++J)for(int K:{0,1,2,2,1,3})Out.push_back(Strip[J*2+K]);
    }
}
