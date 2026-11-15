// BASESIDE artwork. White geometry is tinted by the original button material.
// Coordinates match upright original textures, not cursor atlas orientation.
#pragma once
#include "icon_vector_raster.h"
namespace BaseIconArt {
using namespace CursorVectorArt;
inline Color Gray(float v){v=Clamp(v,0,255);return {v,v,v};}
inline Color MugSurface(Point p,Layer const&) {
    // Original smooth cylinder: dark left edge, wide bright face, narrow right shade.
    float x=Clamp((p.x-88)/108,0,1);
    float v=158+91*std::sin(x*Pi*.83f);
    v-=18*std::exp(-std::pow((p.y-221)/4,2));
    return Gray(v);
}
inline Color ShipLeft(Point p,Layer const&) {
    float t=Clamp((p.x-67)/48,0,1);
    return Gray(248-139*t*t);
}
inline Color ShipRight(Point p,Layer const&) {
    return Gray(226+24*Clamp((p.x-137)/40,0,1));
}
inline Color ShipSpine(Point p,Layer const& layer) {
    // Shade a convex cross-section, following the changing width of the hull.
    // Both edges recede into shadow; the broad axial highlight sits on the crown.
    auto const& points=layer.parts.front().points;
    float left=1e9f,right=-1e9f;
    for(size_t i=0,j=points.size()-1;i<points.size();j=i++) {
        Point a=points[j],b=points[i];
        if((a.y>p.y)!=(b.y>p.y)) {
            float x=a.x+(b.x-a.x)*(p.y-a.y)/(b.y-a.y);
            left=(std::min)(left,x);right=(std::max)(right,x);
        }
    }
    if(right-left<.01f)return White;
    float u=Clamp((p.x-(left+right)*.5f)/((right-left)*.5f),-1,1);
    return Gray(146+109*std::sqrt((std::max)(0.f,1-u*u)));
}
inline std::vector<Icon> Build() {
    std::vector<Icon> icons;
    auto add=[&](char const* name)->Layer& {
        icons.push_back({name,White,3,.16f,{}});return icons.back().Add(White);
    };
    {
        add("cityscape");auto& icon=icons.back();
        // Original skyline is overlapping broad buildings, not isolated bars.
        // Paint rear towers first; foreground blocks hide their lower floors.
        auto building=[&](float left,float top,float right,float value) {
            auto shape=Box({(left+right)*.5f,(top+240)*.5f},
                          {(right-left)*.5f,(240-top)*.5f},1.5f);
            icon.Add(Gray(72)).parts.push_back(shape);
            icon.Add(Gray(value)).parts.push_back(Box(
                {(left+right)*.5f,(top+240)*.5f},
                {(right-left)*.5f-4,(240-top)*.5f-4},.5f));
            icon.Add(Gray(value-35)).parts.push_back(Line({right-6,top+6},{right-6,234},2));
        };
        building(136,48,180,238);
        building(48,80,94,230);
        building(190,98,230,244);
        building(153,211,197,225);
        building(88,169,157,250);
        building(25,122,62,248);
        icon.Add(White).parts.push_back(Box({128,240},{115,2},.5f));
    }
    {
        add("equipment_dealer");std::vector<Point> p;
        // Original texture has NINE narrow teeth, confirmed by radial contour peaks.
        // Circular root arcs between small teeth avoid the earlier chunky cog shape.
        for(int i=0;i<9;++i)for(auto q:std::vector<Point>{{-.34906585f,84},{-.28f,84},
                {-.22f,84},{-.15f,89},{-.09f,100},{.09f,100},{.15f,89},
                {.22f,84},{.28f,84}}) {
            float a=i*2*Pi/9-Pi/2+q.x;p.push_back({std::cos(a)*q.y,std::sin(a)*q.y});
        }
        p=Rounded(p,3);
        // Face-on, circular bore and uniform colour: no perspective or surface gradient.
        for(auto& q:p)q=Point{128,128}+q;
        auto& face=icons.back().layers.front();
        face.parts.push_back(Poly(p));
        auto hole=Disk({128,128},35);hole.subtract=true;face.parts.push_back(hole);
    }
    {
        // Same six-container projection and back-to-front order as the cursor.
        // Corrugation belongs to each individual box, so nearer boxes occlude it.
        add("commod_trader");auto& icon=icons.back();
        auto project=[](Point p){return Point{128,152}+(p-Point{112,153})*1.38f;};
        auto line=[&](Point a,Point b,float value,float width) {
            icon.Add(Gray(value)).parts.push_back(Line(project(a),project(b),width*1.38f));
        };
        auto face=[&](std::vector<Point> p,float value) {
            for(auto& q:p)q=project(q);
            icon.Add(Gray(value)).parts.push_back(Poly(p));
            Outline(icon.Add(Gray(110)),p,1.4f*1.38f);
        };
        auto box=[&](float x,float y) {
            Point a{x,y},b{x+28,y-7},c{x+28,y+25},d{x,y+32},depth{-57,-24};
            face({a+depth,b+depth,b,a},245);
            // Shallow roof ribs run across the width in the same projected basis.
            for(int i=1;i<=5;++i) {
                Point q=a+depth*(i/6.f);
                line(q+Point{3,-.75f},q+Point{25,-6.25f},211,1);
            }
            face({a+depth,a,d,d+depth},188);
            // Paired shade/highlight strokes give the metal ribs a raised profile.
            for(int i=1;i<=5;++i) {
                Point q=a+depth*(i/6.f);
                line(q+Point{0,4},q+Point{0,28},128,1.7f);
                line(q+Point{1.5f,4.6f},q+Point{1.5f,28.6f},229,1.1f);
            }
            line(a+depth+Point{2,4},a+Point{-2,2.3f},218,1.6f);
            line(d+depth+Point{2,-3},d+Point{-2,-4.7f},133,1.6f);
            face({a,b,c,d},221);
            // Right-facing double doors, with two locking bars inside the frame.
            line(a+Point{14,-1},d+Point{14,-6},125,1.1f);
            for(float u:{7.f,21.f}) {
                Point q=a+Point{u,-u*.25f};
                line(q+Point{0,4},q+Point{0,28},159,1.2f);
                line(q+Point{1,4},q+Point{1,28},249,.8f);
            }
        };
        for(int tier=0;tier<3;++tier)for(int col=2-tier;col>=0;--col)
            box(92+col*31.f+tier*15.5f,176-col*7.f-tier*38.f);
    }
    {
        auto& l=add("bar");
        Path handle({91,96});handle.Curve({58,96},{51,113},{51,140}).To({51,169})
            .Curve({51,190},{65,201},{91,201});
        Stroke(l,handle.p,13);
        auto& body=icons.back().Add(White);
        Path vessel({88,72});vessel.Curve({105,69},{176,69},{194,73}).To({191,229})
            .Curve({166,233},{111,233},{89,229}).To({88,72});
        body.parts.push_back(Poly(vessel.p));
        body.paint=MugSurface;
        auto& rim=icons.back().Add(White);
        Path base({94,226});base.Curve({116,229},{167,229},{186,226});Stroke(rim,base.p,4);
        Path lip({92,74});lip.Curve({116,79},{174,79},{189,74});Stroke(rim,lip.p,4);
        // A single connected cap spans the lip; the spill hangs ON the front wall.
        Path foam({88,72});foam.Curve({84,62},{91,54},{102,55})
            .Curve({107,44},{119,44},{128,49}).Curve({137,39},{150,42},{157,49})
            .Curve({171,43},{180,49},{181,55}).Curve({195,53},{200,63},{194,74})
            .Curve({188,77},{189,88},{188,99}).Curve({188,116},{175,116},{174,101})
            .To({174,85}).Curve({173,78},{164,77},{158,79})
            .Curve({142,82},{119,77},{108,78}).Curve({97,80},{90,78},{88,72});
        rim.parts.push_back(Poly(foam.p));
        auto& foamShade=icons.back().Add({218,218,218});
        Path fold({102,66});fold.Curve({118,69},{143,69},{156,66});Stroke(foamShade,fold.p,2.5f);
    }
    {
        auto& l=add("deck");
        std::vector<Point> pent{{128,25},{239,105},{197,235},{59,235},{17,105}};
        Outline(l,pent,6);l.parts.push_back(Ring({128,146},49,5));
        for(auto p:pent) {
            Point axis=Point{128,146}-p;axis=axis*(1/Length(axis));Point n{-axis.y,axis.x};
            l.parts.push_back(Poly({p+axis*2+n*10,p+axis*31,p+axis*2-n*10}));
        }
        l.parts.push_back(Ring({128,146},15,4));
    }
    {
        Icon icon{"ship_dealer",White,3,.16f,{}};
        icon.Add({139,210,233});icon.Add({119,197,224});
        Path panel({128,62});
        panel.Curve({132,62},{132,83},{134,108}).To({138,185})
            .Curve({138,191},{132,195},{128,194})
            .Curve({124,193},{119,190},{119,185}).To({122,108})
            .Curve({124,82},{123,62},{128,62});
        icon.Add({171,230,245}).parts.push_back(Poly(panel.p));

        // BASESIDE reference: wings join below the bare nose and stop short of
        // the rounded tail. Do not carry their shading along the entire spine.
        Path wing({120,116});
        wing.Curve({116,130},{107,145},{101,153}).To({85,184})
            .To({106,184}).To({120,190}).To({120,116});
        icon.layers[0].parts={Poly(wing.p)};
        auto right=wing.p;for(auto& p:right)p.x=256-p.x;
        icon.layers[1].parts={Poly(right)};
        for(auto& l:icon.layers) {
            float value=Clamp(l.color.b/245.f*255.f,0,255);l.color={value,value,value};
            for(auto& s:l.parts)for(auto& p:s.points)
                p=Point{128,128}+(p-Point{128,128})*1.52f;
        }
        // Original: a dark recess LEFT of the bright spine, a bright right wing.
        icon.layers[0].paint=ShipLeft;
        icon.layers[1].paint=ShipRight;
        icon.layers[2].paint=ShipSpine;
        icon.glow=White;icon.sigma=3;icon.strength=.16f;icons.push_back(icon);
    }
    {
        auto& l=add("planetscape");
        l.parts.push_back(Disk({77,78},24));
        for(int i=0;i<8;++i) {
            Point a{std::cos(i*Pi/4),std::sin(i*Pi/4)};
            Point n{-a.y,a.x};
            l.parts.push_back(Poly({Point{77,78}+a*22+n*6,
                Point{77,78}+a*(i%2?38.f:55.f),Point{77,78}+a*22-n*6}));
        }
        Path hills({4,180});hills.Curve({31,180},{40,210},{59,222})
            .Curve({87,227},{97,209},{120,205}).Curve({162,188},{202,185},{252,192});
        Stroke(l,hills.p,6);
        Stroke(l,{{3,214},{19,207},{43,221}},4);
    }
    return icons;
}
inline std::vector<Icon> const& Shapes(){static auto const value=Build();return value;}
}



