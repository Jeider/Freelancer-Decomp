#pragma once
#include "radar_frame.h"
namespace RadarContacts
{
    template<class DrawLine>
    void Stem(RadarProjection::Contact const& p,unsigned rgb,float alpha,DrawLine draw)
    {
        // Height stems fade into the plane, with the brightest end at the marker.
        for(int segment=0;segment<8;++segment)
        {
            float const a=float(segment)/8,b=float(segment+1)/8;
            draw(p.x,p.baseY+(p.tipY-p.baseY)*a,p.x,p.baseY+(p.tipY-p.baseY)*b,
                 RadarFrame::Color(rgb,alpha*(.04f+.52f*b*b)),.8f);
        }
        draw(p.x-2,p.baseY,p.x+2,p.baseY,RadarFrame::Color(rgb,alpha*.4f),.65f);
    }
    template<class DrawLine>
    void Selection(RadarProjection::Contact const& p,float alpha,float size,DrawLine draw)
    {
        float const s=size+3;
        unsigned const highlight=RadarFrame::Color(0xffe35b,alpha);
        draw(p.x-s,p.tipY-s,p.x-s,p.tipY+s,highlight,1.f);
        draw(p.x+s,p.tipY-s,p.x+s,p.tipY+s,highlight,1.f);
        draw(p.x-s,p.tipY+s,p.x-s+3,p.tipY+s,highlight,1.f);
        draw(p.x+s-3,p.tipY+s,p.x+s,p.tipY+s,highlight,1.f);
    }
    template<class DrawLine>
    void Emit(RadarProjection::Contact const& p,unsigned rgb,bool selected,bool ship,
              float alpha,float size,DrawLine draw)
    {
        unsigned const color=RadarFrame::Color(rgb,alpha);
        Stem(p,rgb,alpha,draw);
        if(ship)
        {
            // Downward contact arrows from the reference HUD, filled with vectors.
            for(float y=-size*.6f;y<size;y+=1.f)
            {
                float const half=size*(size-y)/(size*1.6f);
                draw(p.x-half,p.tipY+y,p.x+half,p.tipY+y,color,.7f);
            }
            draw(p.x-size,p.tipY-size*.6f,p.x,p.tipY+size,color,.8f);
            draw(p.x,p.tipY+size,p.x+size,p.tipY-size*.6f,color,.8f);
        }
        else
        {
            draw(p.x-size,p.tipY,p.x,p.tipY-size,color,1.f);
            draw(p.x,p.tipY-size,p.x+size,p.tipY,color,1.f);
            draw(p.x+size,p.tipY,p.x,p.tipY+size,color,1.f);
            draw(p.x,p.tipY+size,p.x-size,p.tipY,color,1.f);
        }
        if(selected) Selection(p,alpha,size,draw);
    }
}
