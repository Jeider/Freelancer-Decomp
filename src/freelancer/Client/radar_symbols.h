#pragma once
#include "radar_contacts.h"
#include "radar_symbol_geometry.h"

namespace RadarSymbols
{
    constexpr unsigned ShipMask=0x7f0000u, LootMask=0x10000000u, MissileMask=0x1000000u;
    constexpr unsigned SolarMask=0x3u|0x10u|0x20u|0x40u|0x80u|0x100u|0x400u|0x800u|0x1000u|0x2000u|0x8000u;
    enum class Kind {Triangle,Diamond,Planet,Capital,Transport,Dockable,Platform,TradeLane,Missile};
    inline unsigned ContactColor(Kind kind,int attitude)
    {
        return attitude<0 ? 0xff4438u : attitude>0 && kind!=Kind::Planet ? 0x55f293u : 0xc1d8deu;
    }
    inline Kind Classify(unsigned type)
    {
        if(type&MissileMask) return Kind::Missile;
        if(type&0x3u) return Kind::Planet; // PLANET and MOON.
        if(type&0x80u) return Kind::TradeLane;
        if(type&0x1000u) return Kind::Platform;
        if(type&(0x40000u|0x80000u|0x200000u)) return Kind::Capital;
        if(type&(0x100000u|0x400000u)) return Kind::Transport;
        if(type&(0x10000u|0x20000u|LootMask)) return Kind::Triangle;
        if(type&SolarMask) return Kind::Dockable;
        return Kind::Diamond;
    }
    // Two red/yellow cycles per second, independent of the decorative sweep.
    inline unsigned MissileColor(int attitude,bool incoming,float phase)
    {
        return incoming ? (phase<.25f ? 0xff4438u : 0xffe35bu) : ContactColor(Kind::Missile,attitude);
    }
    inline RadarSymbolsData::Mesh const* Mesh(Kind kind)
    {
        using namespace RadarSymbolsData;
        switch(kind) {
        case Kind::Planet:return &Planet;
        case Kind::Capital:return &Capital;
        case Kind::Transport:return &Transport;
        case Kind::Dockable:return &Dockable;
        case Kind::Platform:return &Platform;
        case Kind::TradeLane:return &TradeLane;
        default:return nullptr;
        }
    }
    // Clip large symbols to the radar contact area instead of shrinking planets
    // or spilling their wireframes across the adjacent Targeting/Health panels.
    inline bool Clip(RadarProjection::Layout const& l,float& ax,float& ay,float& bx,float& by)
    {
        if(!std::isfinite(ax)||!std::isfinite(ay)||!std::isfinite(bx)||!std::isfinite(by)) return false;
        double lo=0,hi=1,dx=double(bx)-ax,dy=double(by)-ay;
        auto bound=[&](double p,double q) {
            if(p==0) return q>=0;
            double const t=q/p;
            if(p<0) {if(t>hi)return false;lo=(std::max)(lo,t);}
            else {if(t<lo)return false;hi=(std::min)(hi,t);}
            return true;
        };
        float const top=(std::max)(l.contactTop,l.y-l.radius*(l.ellipse+l.elevation));
        if(!bound(-dx,double(ax)-(l.x-l.radius))||!bound(dx,double(l.x+l.radius)-ax)||
           !bound(-dy,double(ay)-top)||!bound(dy,double(l.contactBottom)-ay)) return false;
        bx=float(ax+dx*hi);by=float(ay+dy*hi);
        ax=float(ax+dx*lo);ay=float(ay+dy*lo);
        return true;
    }
    template<class DrawLine>
    void Emit(RadarProjection::Contact const& p,Kind kind,float physicalRadius,float range,
              RadarProjection::Layout const& layout,unsigned rgb,bool selected,float alpha,float size,DrawLine draw)
    {
        if(kind==Kind::Missile)
        {
            if(!std::isfinite(size)||size<=0) return;
            auto clipped=[&](float ax,float ay,float bx,float by,unsigned color,float width) {
                if(Clip(layout,ax,ay,bx,by)) draw(ax,ay,bx,by,color,width);
            };
            float const radius=size*1.25f;
            auto stem=p;
            stem.tipY=p.tipY+(p.baseY>p.tipY ? radius : -radius);
            if(std::fabs(p.baseY-p.tipY)>radius) RadarContacts::Stem(stem,rgb,alpha,clipped);
            for(int i=0;i<16;++i)
            {
                float const a=i*(6.28318530718f/16),b=(i+1)*(6.28318530718f/16);
                clipped(p.x+std::cos(a)*radius,p.tipY+std::sin(a)*radius,
                        p.x+std::cos(b)*radius,p.tipY+std::sin(b)*radius,RadarFrame::Color(rgb,alpha),1.2f);
            }
            if(selected) RadarContacts::Selection(p,alpha,radius,clipped);
            return;
        }
        auto const* mesh=Mesh(kind);
        if(!mesh) {RadarContacts::Emit(p,rgb,selected,kind==Kind::Triangle,alpha,size,draw);return;}
        if(!std::isfinite(range)||range<=0) return;
        float const radius=kind==Kind::Planet ? physicalRadius/range*layout.radius : size*1.8f;
        if(!std::isfinite(radius)||radius<=0) return;
        auto clipped=[&](float ax,float ay,float bx,float by,unsigned color,float width) {
            if(Clip(layout,ax,ay,bx,by)) draw(ax,ay,bx,by,color,width);
        };
        if(kind==Kind::Planet)
        {
            auto const& outline=RadarSymbolsData::PlanetOutline;
            constexpr unsigned count=sizeof(outline)/sizeof(outline[0]);
            float const top=(std::max)(layout.contactTop,layout.y-layout.radius*(layout.ellipse+layout.elevation));
            float const start=std::ceil((std::max)(top,p.tipY-radius));
            float const end=(std::min)(layout.contactBottom,p.tipY+radius);
            // One screen-bounded scanline per row: no giant offscreen mesh work.
            for(float y=start;y<=end;y+=1.f)
            {
                float lo=1e30f,hi=-1e30f;
                for(unsigned i=0;i<count;++i)
                {
                    auto const& a=outline[i];auto const& b=outline[(i+1)%count];
                    float const ay=p.tipY-a.y*radius,by=p.tipY-b.y*radius;
                    if((ay<=y && by>y)||(by<=y && ay>y))
                    {
                        float const x=p.x+(a.x+(b.x-a.x)*(y-ay)/(by-ay))*radius;
                        lo=(std::min)(lo,x);hi=(std::max)(hi,x);
                    }
                }
                if(lo<=hi)clipped(lo,y,hi,y,RadarFrame::Color(rgb,alpha*.32f),1.f);
            }
            // Only the spherical silhouette: no internal latitude/longitude mesh.
            for(unsigned i=0;i<count;++i)
            {
                auto const& a=outline[i];auto const& b=outline[(i+1)%count];
                clipped(p.x+a.x*radius,p.tipY-a.y*radius,p.x+b.x*radius,p.tipY-b.y*radius,
                        RadarFrame::Color(rgb,alpha*.38f),1.f);
            }
        }
        if(kind!=Kind::Planet) RadarContacts::Stem(p,rgb,alpha,clipped);
        else if(p.baseY<p.tipY-radius || p.baseY>p.tipY+radius)
        {
            auto stem=p;
            stem.tipY=p.tipY+(p.baseY>p.tipY ? radius : -radius);
            RadarContacts::Stem(stem,rgb,alpha,clipped); // Stop at the sphere's surface.
        }
        unsigned const color=RadarFrame::Color(rgb,alpha);
        if(kind!=Kind::Planet)
        for(unsigned i=0;i<mesh->edgeCount;++i)
        {
            auto const& a=mesh->vertices[mesh->edges[i][0]];
            auto const& b=mesh->vertices[mesh->edges[i][1]];
            // Native glyphs face the player; retain TLR's shallow depth relief.
            clipped(p.x+(a.x+a.z*.35f)*radius,p.tipY-(a.y+a.z*.25f)*radius,
                    p.x+(b.x+b.z*.35f)*radius,p.tipY-(b.y+b.z*.25f)*radius,color,1.f);
        }
        if(selected) RadarContacts::Selection(p,alpha,radius,clipped);
    }
}
