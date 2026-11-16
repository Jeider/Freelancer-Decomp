#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

// Prototype geometry for the original two texture layers. Camera-relative metre
// coordinates; deterministic travel through one smooth path, no frame history.
namespace ClassicTravel {
struct Point {double x,y,z;};
inline Point Add(Point a,Point b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline Point Sub(Point a,Point b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline Point Scale(Point a,double b){return {a.x*b,a.y*b,a.z*b};}
inline double Dot(Point a,Point b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline Point Cross(Point a,Point b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline Point Unit(Point p){return Scale(p,1/std::sqrt(Dot(p,p)));}
inline Point Path(double s){return {200*std::sin(s/1050)+55*std::sin(s/410),120*std::sin(s/1330+.7),-s};}
inline Point Tangent(double s){return Unit({200/1050.*std::cos(s/1050)+55/410.*std::cos(s/410),120/1330.*std::cos(s/1330+.7),-1});}
inline float Smooth(float a,float b,float x){x=std::max(0.f,std::min(1.f,(x-a)/(b-a)));return x*x*(3-2*x);}
template<class Vertex>void Build(std::vector<Vertex>& out,int layer,double time) {
    constexpr int rings=96,sectors=32;
    constexpr double pi=3.14159265358979323846;
    double travel=time*165;
    Point eye=Path(travel),forward=Tangent(travel),right=Unit(Cross(forward,{0,1,0})),up=Cross(right,forward);
    auto local=[&](Point p){p=Sub(p,eye);return Point{Dot(p,right),Dot(p,up),-Dot(p,forward)};};
    std::vector<Vertex> grid((rings+1)*(sectors+1));
    for(int j=0;j<=rings;++j){
        // Concentrate subdivisions around the camera and retain distant detail.
        double q=double(j)/rings,z=-160+4560*q*q,s=travel+z;
        Point centre=Path(s),axis=Tangent(s),side=Unit(Cross(axis,{0,1,0})),vertical=Cross(side,axis);
        double radius=(86+10*std::sin(s/480)+7*std::sin(s/217))*(layer?1:1.62);
        float fade=1-Smooth(3100,4400,float(z));
        float alpha=(layer?.86f:.72f)*fade;
        // Original palette and sharp texture contrast remain intact.
        // Layer 1 uses ONE/INVSRCALPHA: its RGB must fade too, otherwise
        // transparent distant rings still add light and reveal the mesh end.
        unsigned rgb=layer?((unsigned(150*fade)<<8)|unsigned(191*fade)):0x000096u;
        for(int a=0;a<=sectors;++a){
            double angle=2*pi*(a%sectors)/sectors;
            double flute=1+.055*std::sin(angle*3+s/390)+.025*std::sin(angle*5-s/510);
            Point p=local(Add(centre,Add(Scale(side,radius*flute*std::cos(angle)),Scale(vertical,radius*flute*std::sin(angle)))));
            // Same angular and longitudinal scroll rates as the game.
            // Geometry supplies parallax independently of texture scrolling.
            float u=float(a)/sectors+float(layer?.5-time*.2:time*.1);
            float v=float((.5+z/20000)*(layer?15:10)+(layer?.33+time*.1:time*.07));
            grid[j*(sectors+1)+a]={float(p.x),float(p.y),float(p.z),(std::uint32_t(alpha*255)<<24)|rgb,u,v};
        }
    }
    out.clear();out.reserve(rings*sectors*6);
    for(int j=rings-1;j>=0;--j)for(int a=0;a<sectors;++a){
        auto p=grid[j*(sectors+1)+a],q=grid[(j+1)*(sectors+1)+a];
        auto r=grid[j*(sectors+1)+a+1],s=grid[(j+1)*(sectors+1)+a+1];
        out.insert(out.end(),{p,q,r,r,q,s});
    }
}
}
