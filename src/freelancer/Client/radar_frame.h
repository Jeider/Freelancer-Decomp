// Vector radar: original Beta ring edges plus a procedural clipped plane grid.
#pragma once
#include "radar_projection.h"
#include "radar_ring_geometry.h"
namespace RadarFrame
{
    inline unsigned Color(unsigned rgb,float alpha)
    { return (unsigned(RadarProjection::Bounded(alpha,0,1,0.8f)*255)<<24)|(rgb&0xffffffu); }
    template<class DrawLine>
    void Emit(RadarProjection::Layout const& l,int rangeIndex,float opacity,DrawLine draw,float sweepAngle=0,float ringAngle=0)
    {
        // Ship-driven rim and scanner light have independent angles.
        float const cs=std::cos(ringAngle),sn=std::sin(ringAngle);
        auto point=[&](RadarRing::Vertex const& p,float& x,float& y) {
            x=l.x+(p.x*cs-p.z*sn)*l.radius;
            y=l.y+(p.x*sn+p.z*cs)*l.radius*l.ellipse-p.y*l.radius*l.elevation;
        };
        for(auto const& edge:RadarRing::Edges)
        {
            float ax,ay,bx,by;
            point(RadarRing::Vertices[edge[0]],ax,ay);
            point(RadarRing::Vertices[edge[1]],bx,by);
            float const front=(ay+by)*.5f>=l.y ? 1.0f : .65f;
            draw(ax,ay,bx,by,Color(0x86d6e8,opacity*front),1.0f);
        }
        // Square lattice in an oblique projection, clipped to the inner circle.
        constexpr float inner=.855f,diagonal=.70710678118f;
        float const gridCos=diagonal*(cs-sn),gridSin=diagonal*(sn+cs);
        // The disk stays fixed; zooming in shows fewer, larger grid squares.
        int const mode=(std::max)(0,(std::min)(2,rangeIndex));
        float const spacing=.125f*float(1<<(2-mode));
        int const steps=static_cast<int>(inner/spacing);
        for(int i=-steps;i<=steps;++i)
        {
            float const u=float(i)*spacing;
            float const v=std::sqrt(inner*inner-u*u);
            for(int axis=0;axis<2;++axis)
            {
                float const ax=axis? -v:u,az=axis?u:-v;
                float const bx=axis? v:u,bz=axis?u:v;
                draw(l.x+(ax*gridCos-az*gridSin)*l.radius,l.y+(ax*gridSin+az*gridCos)*l.radius*l.ellipse,
                     l.x+(bx*gridCos-bz*gridSin)*l.radius,l.y+(bx*gridSin+bz*gridCos)*l.radius*l.ellipse,
                     Color(0x5595a8,opacity*(i==0?.34f:.20f)),.65f);
            }
        }
        // Two opposing sweep fans, as in the reference HUD. Angular afterglow
        // fades behind the leading ray; radial fade softens center and outer edge.
        constexpr int rays=64,segments=4;
        constexpr float tail=.62f;
        for(int side=0;side<2;++side) for(int ray=0;ray<rays;++ray)
        {
            float const age=float(ray)/float(rays-1);
            float const a=sweepAngle+float(side)*3.14159265359f-age*tail;
            float const dx=std::cos(a)*l.radius*inner;
            float const dy=std::sin(a)*l.radius*inner*l.ellipse;
            float const fade=(1-age)*(1-age);
            for(int segment=0;segment<segments;++segment)
            {
                float const begin=float(segment)/segments,end=float(segment+1)/segments;
                float const radial=segment==0?.45f:segment==segments-1?.55f:1.f;
                draw(l.x+dx*begin,l.y+dy*begin,l.x+dx*end,l.y+dy*end,
                     Color(0x9dd8e6,opacity*.26f*fade*radial),
                     (std::max)(.65f,l.radius*inner*tail/rays*.6f));
            }
        }
        float const s=(std::max)(3.f,l.radius*.022f);
        draw(l.x-s,l.y+s,l.x,l.y-s,Color(0x70ffb0,opacity),1.2f);
        draw(l.x,l.y-s,l.x+s,l.y+s,Color(0x70ffb0,opacity),1.2f);
        draw(l.x-s,l.y+s,l.x+s,l.y+s,Color(0x70ffb0,opacity*.6f),.8f);
    }
}
