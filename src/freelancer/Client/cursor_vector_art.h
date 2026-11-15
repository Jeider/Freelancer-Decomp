#pragma once
#include "icon_vector_raster.h"
#include "base_icon_art.h"
#include "nn_icon_art.h"
namespace CursorVectorArt {
inline void Reticle(Layer& l,float thickness,bool arrowHeads) {
    float radius=arrowHeads?83.f:97.5f;
    l.parts.push_back(Ring({128,128},radius,thickness));l.parts.push_back(Disk({128,128},4.2f));
    // Reconstructed from the upright newcursors alpha silhouette, not a generic
    // arrow/bar. The shoulders bend into a rounded tapered inner end.
    Path master({51,44});
    master.Curve({55,43},{59,44},{62,48}).To({69,57})
        .Curve({72,60},{76,61},{78,65}).Curve({80,68},{79,72},{82,76})
        .To({88,83}).Curve({91,88},{85,92},{81,88}).To({70,81})
        .Curve({66,80},{63,82},{60,78}).To({55,71}).To({43,62})
        .Curve({39,59},{40,55},{43,52});
    for(int i=0;i<4;++i) {
        auto p=master.p;
        for(auto& v:p) v=Point{128,128}+Rotate((v-Point{128,128})*(arrowHeads?1.f:1.23f),i*Pi*.5f);
        auto mark=Poly(p);mark.dilation=arrowHeads?1.f:2.f;
        l.parts.push_back(mark);
    }
}
inline std::vector<Point> BubbleOutline() {
    std::vector<Point> p{{182,126}};
    auto curve=[&](Point a,Point b,Point c,Point d) {
        for(int i=1;i<=12;++i) {float t=i/12.f,u=1-t;p.push_back(a*(u*u*u)+b*(3*u*u*t)+c*(3*u*t*t)+d*(t*t*t));}
    };
    curve({182,126},{182,141},{174,149},{165,153});
    curve({165,153},{162,169},{168,187},{176,194});
    curve({176,194},{153,191},{138,174},{136,153});
    p.push_back({72,153});curve({72,153},{56,153},{48,143},{48,129});
    p.push_back({48,75});curve({48,75},{48,59},{58,50},{74,50});
    p.push_back({156,50});curve({156,50},{173,50},{182,58},{182,75});
    return p;
}
inline std::vector<Icon> Build() {
    std::vector<Icon> v;
    auto add=[&](char const* name,Color color)->Icon& {v.push_back({name,color,5,.38f,{}});return v.back();};
    auto& neutral=add("neutral",White);neutral.strength=0;Reticle(neutral.Add(White),5.5f,true);
    auto& fire=add("hostile_fire",White);fire.strength=0;Reticle(fire.Add(White),13,false);
    for(int text=0;text<2;++text) {
        auto& l=add(text?"talk_rumor":"talk_empty",Blue).Add(Blue);
        Outline(l,BubbleOutline(),7);
        if(text) {
            for(int row=0;row<4;++row) {
                float y=74+row*18.f;
                if(row==0 || row==3) {
                    l.parts.push_back(Box({89,y},{20,4}));l.parts.push_back(Box({144,y},{24,4}));
                } else {
                    l.parts.push_back(Box({79,y},{10,4}));l.parts.push_back(Box({117,y},{17,4}));l.parts.push_back(Box({157,y},{11,4}));
                }
            }
        }
    }
    {
        auto& icon=add("arrow",Blue);icon.sigma=7;icon.strength=.48f;
        auto& l=icon.Add(Blue);
        // The actual click point stays exactly (80,72). Both triangles share an
        // analytic axis; the tail base is centred, with equal shoulders.
        Point tip{80,72},axis{.64f,.7683749f},normal{-axis.y,axis.x};
        Point base=tip+axis*91.f;
        Outline(l,{tip,base+normal*17.f,base-normal*17.f},3.4f);
        Outline(l,{base+normal*7.f,base+axis*40.f,base-normal*7.f},3.4f);
    }
    {
        Color red{240,37,26};auto& icon=add("no_fire",red);icon.strength=0;auto& l=icon.Add(red);
        l.parts.push_back(Ring({128,128},88,12));l.parts.push_back(Line({66,66},{190,190},12));
    }
    Color green{95,235,35};auto& friendly=add("friendly",green);friendly.strength=0;Reticle(friendly.Add(green),5.5f,true);
    {auto& icon=add("cross",White);icon.strength=0;auto& l=icon.Add(White);l.parts={Ring({128,128},94,11),Disk({128,128},19)};}
    {
        add("talk_equip_dealer",Blue);
    }
    {
        auto& l=add("talk_mission",Blue).Add(Blue);
        Hollow(l,Poly(Rounded({{91,80},{105,38},{154,38},{170,80}},3)),
            Poly({{104,80},{113,50},{146,50},{157,80}}));
        l.parts.push_back(Box({130,142},{90,65},18));
    }
    // This is the original information 'i', not the '!' invented by the PNG.
    {auto& l=add("talk_info",Blue).Add(Blue);l.parts={Ring({128,128},89,10),Disk({128,81},11),Line({128,111},{128,176},22)};}
    {
        auto& l=add("talk_bribe",Blue).Add(Blue);
        // One upright stem and the original S, with rounded bends. The old
        // hand-written substitute added a second stem and mirrored the slash.
        l.parts={Line({128,41},{128,213},11)};
        Path dollar({151,89});
        dollar.To({151,65}).Curve({151,59},{148,56},{142,56})
            .To({112,56}).Curve({104,56},{103,59},{103,67}).To({103,94})
            .Curve({103,104},{109,109},{116,117}).To({140,145})
            .Curve({148,153},{151,158},{151,167}).To({151,188})
            .Curve({151,195},{148,197},{141,197}).To({112,197})
            .Curve({105,197},{103,194},{103,187}).To({103,164});
        Stroke(l,dollar.p,12);
    }
    {
        add("talk_commodity_dealer",Blue);
    }
    {
        add("talk_ship_dealer",Blue);
    }
    {
        auto& icon=add("talk_story",Blue);
        icon=NnIconArt::Shapes()[2];icon.name="talk_story";
        // Identical raised facets, at the cursor's original 88-unit radius.
        icon.sampleScale=111.f/88.f;
        icon.sampleOffset={128-128*icon.sampleScale,128-128*icon.sampleScale};
        icon.tint=Blue;icon.sigma=5*icon.sampleScale;
    }
    {
        auto& l=add("stretch",Blue).Add(Blue);
        l.parts={Box({109,128},{6,101},1),Box({149,128},{6,101},1),
            Poly({{105,121},{82,121},{82,107},{30,128},{82,149},{82,135},{105,135}}),
            Poly({{153,121},{175,121},{175,107},{226,128},{175,149},{175,135},{153,135}})};
    }
    // One approved artwork source for room buttons and matching mouse cursors.
    struct Shared {char const* cursor;int base;float scale;Point offset;};
    for(auto const& item:std::vector<Shared>{
        {"talk_equip_dealer",1,1/.62f,{128-128/.62f,128-128/.62f}},
        {"talk_commodity_dealer",2,1.38f,{128-112*1.38f,152-153*1.38f}},
        {"talk_ship_dealer",5,1.52f,{128-128*1.52f,128-128*1.52f}}}) {
        for(auto& icon:v)if(std::strcmp(icon.name,item.cursor)==0) {
            icon=BaseIconArt::Shapes()[item.base];icon.name=item.cursor;
            icon.sampleScale=item.scale;icon.sampleOffset=item.offset;icon.tint=Blue;
            icon.sigma=5*item.scale;icon.strength=item.base==2?.28f:.38f;
        }
    }
    return v;
}
inline std::vector<Icon> const& Icons() {static auto const icons=Build();return icons;}
inline int Find(char const* name) {
    for(size_t i=0;i<Icons().size();++i) if(std::strcmp(name,Icons()[i].name)==0)return static_cast<int>(i);
    return -1;
}
}
