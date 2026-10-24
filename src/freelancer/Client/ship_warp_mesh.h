#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

struct FShipWarpPoint { float X,Y,Z; };
struct FShipWarpVertex { float Position[3]; std::uint32_t Color; float UV[2]; };
static_assert(sizeof(FShipWarpVertex)==24,"XYZ DIFFUSE TEX1 layout");
namespace ShipWarpMesh
{
inline FShipWarpPoint Add(FShipWarpPoint A,FShipWarpPoint B){return {A.X+B.X,A.Y+B.Y,A.Z+B.Z};}
inline FShipWarpPoint Mul(FShipWarpPoint A,float S){return {A.X*S,A.Y*S,A.Z*S};}
inline FShipWarpPoint Sub(FShipWarpPoint A,FShipWarpPoint B){return Add(A,Mul(B,-1));}
inline float Dot(FShipWarpPoint A,FShipWarpPoint B){return A.X*B.X+A.Y*B.Y+A.Z*B.Z;}
inline FShipWarpPoint Cross(FShipWarpPoint A,FShipWarpPoint B){return {A.Y*B.Z-A.Z*B.Y,A.Z*B.X-A.X*B.Z,A.X*B.Y-A.Y*B.X};}
inline FShipWarpPoint Unit(FShipWarpPoint A,FShipWarpPoint F={1,0,0}){float L=Dot(A,A);return L>1e-10f ? Mul(A,1/std::sqrt(L)):F;}
inline float Clock(float T){return std::isfinite(T)?std::fmod(T,96.f):0;}
inline bool Finite(FShipWarpPoint A){return std::isfinite(A.X)&&std::isfinite(A.Y)&&std::isfinite(A.Z);}
inline FShipWarpVertex Vertex(FShipWarpPoint P,float U,float V,unsigned Kind,float Gain,float Seed=0)
{
    unsigned R=unsigned(std::max(0.f,std::min(1.f,Gain))*255);
    unsigned B=unsigned((Seed-std::floor(Seed))*255);
    return {{P.X,P.Y,P.Z},0xff000000u|(R<<16)|(Kind?0xff00u:0)|B,{U,V}};
}
inline void Quad(std::vector<FShipWarpVertex>& O,FShipWarpVertex A,FShipWarpVertex B,FShipWarpVertex C,FShipWarpVertex D)
{O.push_back(A);O.push_back(B);O.push_back(C);O.push_back(C);O.push_back(B);O.push_back(D);}
}

// Append triangle-list vertices; callers retain vector capacity. Centre is already
// ahead of the hardpoint. The fixed ship basis makes the curved bow world oriented.
inline void BuildShipWarpNose(std::vector<FShipWarpVertex>& Out,FShipWarpPoint Centre,
    FShipWarpPoint Right,FShipWarpPoint Up,FShipWarpPoint Back,float Size,float Time,float WidthScale=1)
{
    using namespace ShipWarpMesh;
    if(!Finite(Centre)||!Finite(Right)||!Finite(Up)||!Finite(Back)||!std::isfinite(Size)||Size<=0||!std::isfinite(WidthScale)||WidthScale<=0)return;
    Right=Unit(Right);Up=Unit(Up,{0,1,0});Back=Unit(Back,{0,0,1});
    constexpr unsigned Sectors=32,Rings=6;
    float T=Clock(Time)*6.283185307f/96;
    auto V=[&](unsigned Ring,unsigned Sector){float R=float(Ring)/Rings,A=float(Sector%Sectors)*6.283185307f/Sectors;
        float X=R*std::cos(A),Y=R*std::sin(A);
        float Bend=R*R*(.62f+.035f*std::sin(A*3+T*48));
        auto P=Add(Centre,Mul(Add(Add(Mul(Right,X*WidthScale),Mul(Up,Y*WidthScale)),Mul(Back,Bend)),Size));
        return Vertex(P,X,Y,0,1);};
    for(unsigned R=0;R<Rings;++R)for(unsigned S=0;S<Sectors;++S)
        Quad(Out,V(R,S),V(R,S+1),V(R+1,S),V(R+1,S+1));
    // A minute solid compression node keeps the apex luminous even when the bow
    // surface is viewed edge-on. Its entire depth remains behind Centre.
    auto CoreCentre=Add(Centre,Mul(Back,Size*.10f));
    FShipWarpPoint Axis[]={Right,Up,Mul(Right,-1),Mul(Up,-1)};
    for(unsigned I=0;I<4;++I)for(int End=-1;End<=1;End+=2)
    {
        Out.push_back(Vertex(Add(CoreCentre,Mul(Back,End*Size*.10f)),0,0,0,1));
        Out.push_back(Vertex(Add(CoreCentre,Mul(Axis[I],Size*.10f*WidthScale)),.035f,0,0,1));
        Out.push_back(Vertex(Add(CoreCentre,Mul(Axis[(I+1)%4],Size*.10f*WidthScale)),0,.035f,0,1));
    }
}

// Points run from the attached emitter to the oldest tail sample (at most33).
// Three ribbon layers follow the real path; their helical offsets have world depth.
inline void BuildShipWarpTrail(std::vector<FShipWarpVertex>& Out,FShipWarpPoint const* Points,
    unsigned Count,FShipWarpPoint Eye,float Width,float Time,float Seed)
{
    using namespace ShipWarpMesh;
    Count=std::min(Count,33u);
    if(!Points||Count<2||!Finite(Eye)||!std::isfinite(Width)||Width<=0||!std::isfinite(Seed))return;
    for(unsigned I=0;I<Count;++I)if(!Finite(Points[I]))return;
    float Length[33]={};for(unsigned I=1;I<Count;++I)Length[I]=Length[I-1]+std::sqrt(Dot(Sub(Points[I],Points[I-1]),Sub(Points[I],Points[I-1])));
    if(Length[Count-1]<.001f)return;
    float T=Clock(Time)*6.283185307f/96;
    for(unsigned Layer=0;Layer<3;++Layer)
    {
        FShipWarpVertex Prev[2];
        for(unsigned I=0;I<Count;++I)
        {
            float U=Length[I]/Length[Count-1];
            auto Tangent=Unit(Sub(Points[std::min(I+1,Count-1)],Points[I?I-1:0]),{0,0,1});
            auto Side=Unit(Cross(Tangent,Sub(Eye,Points[I])),Unit(Cross(Tangent,{0,1,0}),{1,0,0}));
            auto Other=Unit(Cross(Tangent,Side),{0,1,0});
            float Phase=U*19+T*192+Seed*6.283185307f+Layer*2.0943951f;
            float Radius=Layer?Width*(.30f+.35f*U):0;
            auto P=Add(Points[I],Add(Mul(Side,std::cos(Phase)*Radius),Mul(Other,std::sin(Phase)*Radius)));
            float Half=Width*(Layer?.22f:1.15f)*(1-.65f*U);
            float Gain=(Layer?.55f:1.f)*(1-U)*(1-U);
            FShipWarpVertex Pair[]={Vertex(Add(P,Mul(Side,-Half)),U,-1,1,Gain,Seed+Layer*.17f),Vertex(Add(P,Mul(Side,Half)),U,1,1,Gain,Seed+Layer*.17f)};
            if(I)Quad(Out,Prev[0],Prev[1],Pair[0],Pair[1]);
            Prev[0]=Pair[0];Prev[1]=Pair[1];
        }
    }
}
