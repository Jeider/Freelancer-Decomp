#pragma once
#include <array>
#include <cmath>
#include <vector>

// A periodic, piecewise-linear approximation of the existing nebula noise. Baked once,
// shared by every faceted volume; the original noise/white/walker styles are untouched.
namespace NebulaFacetedNoise
{
    const int Size = 128;
    inline void Generate(std::vector<unsigned long> const& Source, std::vector<unsigned long>* Out)
    {
        const int Grid = 12, SourceSize = 64;
        using Texel = std::array<float, 4>;
        std::vector<Texel> Lattice(Grid * Grid * Grid);
        auto Index = [=](int x, int y, int z) { return ((z % Grid) * Grid + y % Grid) * Grid + x % Grid; };
        for (int z=0; z<Grid; ++z) for (int y=0; y<Grid; ++y) for (int x=0; x<Grid; ++x)
        {
            const float q[3] = {float(x)*SourceSize/Grid-.5f, float(y)*SourceSize/Grid-.5f,
                                float(z)*SourceSize/Grid-.5f};
            const int b[3] = {int(std::floor(q[0])),int(std::floor(q[1])),int(std::floor(q[2]))};
            const float f[3] = {q[0]-b[0],q[1]-b[1],q[2]-b[2]};
            Texel& v = Lattice[Index(x,y,z)];
            for (int dz=0; dz<2; ++dz) for (int dy=0; dy<2; ++dy) for (int dx=0; dx<2; ++dx)
            {
                const float w=(dx?f[0]:1-f[0])*(dy?f[1]:1-f[1])*(dz?f[2]:1-f[2]);
                const unsigned long p=Source[(((b[2]+dz+SourceSize)%SourceSize)*SourceSize+
                    (b[1]+dy+SourceSize)%SourceSize)*SourceSize+(b[0]+dx+SourceSize)%SourceSize];
                for(int c=0;c<4;++c) v[c] += float((p>>(c*8))&255)*w;
            }
        }
        Out->resize(Size*Size*Size);
        unsigned long Min[4]={255,255,255,255}, Max[4]={0,0,0,0};
        for(int z=0;z<Size;++z) for(int y=0;y<Size;++y) for(int x=0;x<Size;++x)
        {
            const float q[3]={(x+.5f)*Grid/Size,(y+.5f)*Grid/Size,(z+.5f)*Grid/Size};
            const int b[3]={int(q[0]),int(q[1]),int(q[2])};
            const float f[3]={q[0]-b[0],q[1]-b[1],q[2]-b[2]};
            int axes[3]={0,1,2};
            auto Swap=[&](int a,int c){if(f[axes[a]]<f[axes[c]]){int t=axes[a];axes[a]=axes[c];axes[c]=t;}};
            Swap(0,1);Swap(1,2);Swap(0,1);
            int a[3]={b[0],b[1],b[2]}, mid[3]={b[0],b[1],b[2]};
            ++a[axes[0]]; ++mid[axes[0]]; ++mid[axes[1]];
            const Texel &v0=Lattice[Index(b[0],b[1],b[2])], &v1=Lattice[Index(a[0],a[1],a[2])],
                &v2=Lattice[Index(mid[0],mid[1],mid[2])], &v3=Lattice[Index(b[0]+1,b[1]+1,b[2]+1)];
            const float weights[4]={1-f[axes[0]],f[axes[0]]-f[axes[1]],f[axes[1]]-f[axes[2]],f[axes[2]]};
            unsigned long packed=0;
            for(int c=0;c<4;++c)
            {
                const unsigned long value=static_cast<unsigned long>(v0[c]*weights[0]+v1[c]*weights[1]+
                    v2[c]*weights[2]+v3[c]*weights[3]+.5f);
                if(value<Min[c])Min[c]=value;
                if(value>Max[c])Max[c]=value;
                packed|=value<<(c*8);
            }
            (*Out)[(z*Size+y)*Size+x]=packed;
        }
        // Restore the same full channel range as GenerateNoise; interpolation otherwise
        // narrows the field so much that the authored coverage turns into almost pure haze.
        for(auto& packed:*Out)
        {
            unsigned long result=0;
            for(int c=0;c<4;++c)
            {
                const unsigned long range=Max[c]-Min[c];
                const unsigned long value=range?((((packed>>(c*8))&255)-Min[c])*255+range/2)/range:128;
                result|=value<<(c*8);
            }
            packed=result;
        }
    }
}
