#pragma once
#include <cmath>

// Shared by the game and standalone renderer; no D3DX or game-clock dependency.
namespace JumpCloud {
// Visual playback only; the game's jump duration and ship simulation are unchanged.
constexpr float MaterialSpeed=16.f;
constexpr float TravelSpeed=11.2f;
constexpr float PathSegment=32.f;
constexpr float PathWidth=12.f;
constexpr float PathHeight=8.f;
struct Point { float x,y,z; };
inline Point Sub(Point a,Point b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline Point Cross(Point a,Point b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline Point Unit(Point p){float r=1/std::sqrt(p.x*p.x+p.y*p.y+p.z*p.z);return {p.x*r,p.y*r,p.z*r};}
inline Point Centre(float z){
    float s=z/PathSegment,n=std::floor(s),u=s-n;
    float x[4],y[4];
    for(int i=0;i<4;++i){float k=n+i-1;x[i]=PathWidth*std::sin(k*1.1f);y[i]=PathHeight*std::sin(k*.83f+.5f);}
    auto cubic=[u](float const* p){return .5f*(2*p[1]+(-p[0]+p[2])*u+(2*p[0]-5*p[1]+4*p[2]-p[3])*u*u+(-p[0]+3*p[1]-3*p[2]+p[3])*u*u*u);};
    return {cubic(x),cubic(y),z};
}
inline void Camera(float z,float* out){
    // Gently anticipate the next bend; no roll or high-frequency camera wobble.
    Point eye=Centre(z),forward=Unit(Sub(Centre(z+20),Centre(z-12)));
    Point right=Unit(Cross({0,1,0},forward)),up=Cross(forward,right);
    Point p[4]={eye,forward,right,up};
    for(int i=0;i<4;++i){out[i*4]=p[i].x;out[i*4+1]=p[i].y;out[i*4+2]=p[i].z;out[i*4+3]=0;}
}
inline void Destination(float z,float const* frame,float* out){
    Point toward=Sub(Centre(z+40),Centre(z));
    auto dot=[&](int i){return toward.x*frame[i]+toward.y*frame[i+1]+toward.z*frame[i+2];};
    float depth=dot(4);
    out[0]=dot(8)/depth;out[1]=dot(12)/depth;out[2]=out[3]=0;
}
}
