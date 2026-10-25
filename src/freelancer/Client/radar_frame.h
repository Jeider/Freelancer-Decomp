// Shared production/test line emission for the scanner-independent radar frame.
#pragma once
#include "radar_projection.h"
namespace RadarFrame
{
    inline unsigned Color(unsigned rgb,float alpha)
    { return (unsigned(RadarProjection::Bounded(alpha,0,1,0.8f)*255)<<24)|(rgb&0xffffffu); }
    template<class DrawLine>
    void Emit(RadarProjection::Layout const& l,int rangeIndex,float opacity,DrawLine draw)
    {
        for(int ring=0;ring<2;++ring)
        {
            float const fraction=ring==0?1.0f:0.5f;
            unsigned const color=Color(ring==0?0x72bad7:0x527d94,opacity*(ring==0?0.8f:0.5f));
            float px=l.x+l.radius*fraction,py=l.y;
            for(int i=1;i<=64;++i)
            {
                float const a=float(i)*6.28318530718f/64;
                float const x=l.x+std::cos(a)*l.radius*fraction;
                float const y=l.y+std::sin(a)*l.radius*fraction*l.ellipse;
                draw(px,py,x,y,color,1.0f);px=x;py=y;
            }
        }
        draw(l.x-l.radius,l.y,l.x+l.radius,l.y,Color(0x527d94,opacity*.45f),1.0f);
        draw(l.x,l.y-l.radius*l.ellipse,l.x,l.y+l.radius*l.ellipse,Color(0x527d94,opacity*.45f),1.0f);
        draw(l.x-4,l.y+3,l.x,l.y-4,Color(0xdaefff,opacity),1.0f);
        draw(l.x,l.y-4,l.x+4,l.y+3,Color(0xdaefff,opacity),1.0f);
        for(int i=0;i<3;++i)
        {
            float const x=l.x-8+float(i)*8,y=l.y+l.radius*(l.ellipse+l.elevation)+5;
            draw(x,y,x+4,y,Color(0xb2dfee,opacity*(i==rangeIndex?1.0f:.3f)),i==rangeIndex?1.5f:.8f);
        }
    }
}
