#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

// World-fixed cells for a local decorative mesh layer. Camera movement only
// changes which cells are resident, never their positions, size or orientation.
namespace NebulaAsteroidMesh
{
    constexpr double CellSize=1000.0;
    constexpr float Near=900.0f, NearFade=800.0f, Far=4200.0f, FarFade=900.0f;
    constexpr int PerCell=6;
    inline uint64_t Hash(uint64_t x) {
        x+=0x9e3779b97f4a7c15ull;x=(x^(x>>30))*0xbf58476d1ce4e5b9ull;
        x=(x^(x>>27))*0x94d049bb133111ebull;return x^(x>>31);
    }
    inline double Unit(uint64_t& h) {h=Hash(h);return double(h>>40)/16777216.0;}
    inline int Cell(double x) {return int(std::floor(x/CellSize));}
    struct Rock {float position[3],scale,rotation[4];int model;unsigned colour;};
    template<class Emit> void Generate(int const* cell,int models,Emit emit) {
        if(models<=0)return;
        const double centre[3]={(cell[0]+.5)*CellSize,(cell[1]+.5)*CellSize,(cell[2]+.5)*CellSize};
        // A complete visible sphere for every camera position in this cell.
        const double radius=Far+CellSize*.866025404+128.0;
        const int span=int(std::ceil(radius/CellSize))+1;
        for(int z=cell[2]-span;z<=cell[2]+span;++z)
        for(int y=cell[1]-span;y<=cell[1]+span;++y)
        for(int x=cell[0]-span;x<=cell[0]+span;++x) {
            uint64_t h=Hash(Hash(Hash(uint32_t(x))^uint32_t(y))^uint32_t(z)^0x0f150a57ull);
            for(int n=0;n<PerCell;++n) {
                Rock r={};r.position[0]=float((x+Unit(h))*CellSize);
                r.position[1]=float((y+Unit(h))*CellSize);r.position[2]=float((z+Unit(h))*CellSize);
                r.model=(std::min)(models-1,int(Unit(h)*models));r.scale=float(.85+.55*Unit(h));
                const double u=Unit(h),a=6.283185307179586*Unit(h),b=6.283185307179586*Unit(h);
                r.rotation[0]=float(std::sqrt(1-u)*std::sin(a));r.rotation[1]=float(std::sqrt(1-u)*std::cos(a));
                r.rotation[2]=float(std::sqrt(u)*std::sin(b));r.rotation[3]=float(std::sqrt(u)*std::cos(b));
                r.colour=0xff000000u|(unsigned(100+155*Unit(h))<<16);
                double d2=0;for(int k=0;k<3;++k){double d=r.position[k]-centre[k];d2+=d*d;}
                if(d2<=radius*radius)emit(r);
            }
        }
    }
}
