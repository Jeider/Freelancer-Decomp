#pragma once
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <vector>

// Connected view-space tube: adjacent spans share the exact same ring positions,
// normals and colours. No per-particle caps, clipping planes or additive joins.
namespace Rp9BeamMesh
{
    constexpr int Sides = 24;
    constexpr float Pi = 3.14159265359f;
    struct Point { D3DXVECTOR3 position; float radius; D3DXVECTOR4 colour; };
    struct Vertex { D3DXVECTOR3 position, normal; D3DXVECTOR4 colour; float u, v; D3DXVECTOR4 axis; D3DXVECTOR2 radial; };
    inline float Dot(D3DXVECTOR3 a, D3DXVECTOR3 b) { return D3DXVec3Dot(&a, &b); }
    inline D3DXVECTOR3 Unit(D3DXVECTOR3 a, D3DXVECTOR3 fallback = D3DXVECTOR3(0,0,1))
    {
        float n = D3DXVec3Length(&a);
        return n > 1e-7f ? a / n : fallback;
    }
    inline D3DXVECTOR3 Cross(D3DXVECTOR3 a, D3DXVECTOR3 b)
    { D3DXVECTOR3 c; D3DXVec3Cross(&c, &a, &b); return c; }

    inline std::vector<Vertex> Build(std::vector<Point> const& input, float u, float v, bool& inside)
    {
        inside = false;
        std::vector<Point> points;
        for (auto p : input)
        {
            if (!std::isfinite(p.position.x+p.position.y+p.position.z+p.radius)) return {};
            p.radius = (std::max)(0.f, p.radius);
            auto separation=points.empty() ? D3DXVECTOR3(0,0,0) : p.position-points.back().position;
            if (!points.empty() && Dot(separation,separation) < 1e-12f)
            { points.back() = p; continue; }
            points.push_back(p);
        }
        if (points.empty() || points.size() > 4096) return {};
        std::vector<Point> samples;
        std::vector<D3DXVECTOR3> tangents;
        for (size_t i=0; i<points.size(); ++i)
        {
            auto before = points[i].position-points[i ? i-1 : i].position;
            auto after = points[i+1<points.size() ? i+1 : i].position-points[i].position;
            tangents.push_back(Unit(Unit(before,Unit(after))+Unit(after,Unit(before))));
        }
        samples.push_back(points.front());
        for (size_t i=1; i<points.size(); ++i)
        {
            auto const& a=points[i-1]; auto const& b=points[i];
            auto delta=b.position-a.position;
            float length=D3DXVec3Length(&delta);
            auto axis=Unit(delta);
            // Hermite tangents use chord length: no long-neighbour overshoot.
            int steps=(Dot(tangents[i-1],axis)<.9999f || Dot(tangents[i],axis)<.9999f) ? 8 : 1;
            for(int j=1;j<=steps;++j)
            {
                float t=float(j)/steps,t2=t*t,t3=t2*t;
                Point p;
                p.position=a.position*(2*t3-3*t2+1)+b.position*(-2*t3+3*t2)+
                    tangents[i-1]*(length*(t3-2*t2+t))+tangents[i]*(length*(t3-t2));
                p.radius=a.radius+(b.radius-a.radius)*t;
                p.colour=a.colour+(b.colour-a.colour)*t;
                samples.push_back(p);
            }
        }
        std::vector<Vertex> vertices;
        vertices.reserve((samples.size()+1)*Sides*6);
        std::vector<Vertex> previous;
        auto ring=[&](D3DXVECTOR3 centre,D3DXVECTOR3 axis,D3DXVECTOR3 side,float radius,
                      float radialNormal,float axialNormal,D3DXVECTOR4 colour)
        {
            auto up=Unit(Cross(axis,side));
            std::vector<Vertex> current;
            for(int k=0;k<Sides;++k)
            {
                float angle=2*Pi*k/Sides;
                auto radial=side*std::cos(angle)+up*std::sin(angle);
                current.push_back({centre+radial*radius,Unit(radial*radialNormal+axis*axialNormal),colour,u,v,
                    D3DXVECTOR4(axis.x,axis.y,axis.z,0),D3DXVECTOR2(0,0)});
            }
            if(!previous.empty()) for(int k=0;k<Sides;++k)
            {
                int next=(k+1)%Sides;
                for(auto const* q : {&previous[k],&previous[next],&current[next],
                                     &previous[k],&current[next],&current[k]}) vertices.push_back(*q);
            }
            previous=std::move(current);
        };
        // Close the existing cross-section, without extending the beam or
        // adding a spherical bulb. Cap UVs carry the same soft radial profile
        // as the body; surface normals alone would make a solid bright disc.
        auto cap=[&](Point const& p,D3DXVECTOR3 axis,D3DXVECTOR3 side,float sign)
        {
            auto up=Unit(Cross(axis,side));
            Vertex centre={p.position,axis*sign,p.colour,u,v,
                           D3DXVECTOR4(axis.x,axis.y,axis.z,1),D3DXVECTOR2(0,0)};
            for(int k=0;k<Sides;++k)
            {
                vertices.push_back(centre);
                for(int j : {k,(k+1)%Sides})
                {
                    float angle=2*Pi*j/Sides;
                    float x=std::cos(angle),y=std::sin(angle);
                    Vertex rim=centre;rim.position+=(side*x+up*y)*p.radius;
                    rim.radial=D3DXVECTOR2(x,y);vertices.push_back(rim);
                }
            }
        };
        auto firstAxis=tangents.front();
        auto side=Unit(Cross(firstAxis, std::fabs(firstAxis.y)<.9f ? D3DXVECTOR3(0,1,0) : D3DXVECTOR3(1,0,0)));
        cap(samples.front(),firstAxis,side,-1);
        D3DXVECTOR3 lastAxis=firstAxis;
        for(size_t i=0;i<samples.size();++i)
        {
            auto const& p=samples[i];
            auto axis=i==0 ? firstAxis : i+1==samples.size() ? tangents.back() :
                Unit(samples[i+1].position-samples[i-1].position,lastAxis);
            // Parallel transport avoids twisted rings along a curved trail.
            side=Unit(side-axis*Dot(side,axis),Unit(Cross(axis,D3DXVECTOR3(0,1,0))));
            ring(p.position,axis,side,p.radius,1,0,p.colour);
            if(i)
            {
                auto d=p.position-samples[i-1].position;
                float t=(std::max)(0.f,(std::min)(1.f,-Dot(samples[i-1].position,d)/(std::max)(1e-12f,Dot(d,d))));
                auto c=samples[i-1].position+d*t;
                float r=samples[i-1].radius+(p.radius-samples[i-1].radius)*t;
                inside=inside || Dot(c,c)<r*r;
            }
            else inside=Dot(p.position,p.position)<p.radius*p.radius;
            lastAxis=axis;
        }
        cap(samples.back(),lastAxis,side,1);
        return vertices;
    }
}
