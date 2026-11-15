// Top-right NeuroNet panel. Geometry follows the original individual textures.
#pragma once
#include "base_icon_art.h"
namespace NnIconArt {
using namespace CursorVectorArt;
inline Color Sphere(Point p,Layer const& layer) {
    auto const& disk=layer.parts.front();
    float x=(p.x-disk.center.x)/disk.radius,y=(p.y-disk.center.y)/disk.radius;
    float z=std::sqrt((std::max)(0.f,1-x*x-y*y));
    return BaseIconArt::Gray(140+115*Clamp(-.36f*x-.48f*y+.8f*z,0,1));
}
inline std::vector<Icon> Build() {
    std::vector<Icon> v;
    auto add=[&](char const* name)->Icon& {v.push_back({name,White,2,.12f,{}});return v.back();};
    {
        auto& icon=add("nn_map");auto& grid=icon.Add({150,150,150});
        for(float n:{49.f,124.f,204.f}) {
            grid.parts.push_back(Line({n,0},{n,256},4));
            grid.parts.push_back(Line({0,n},{256,n},4));
        }
        auto& routes=icon.Add(White);
        Stroke(routes,{{72,49},{151,87}},6);
        Stroke(routes,{{175,130},{104,174}},6);
        for(auto q:std::vector<std::vector<float>>{{65,42,24},{195,103,31},{77,185,59}}) {
            auto& planet=icon.Add(White);planet.parts.push_back(Disk({q[0],q[1]},q[2]));planet.paint=Sphere;
        }
    }
    {
        auto& icon=add("nn_inventory");
        // Wider clean cases: only outer silhouettes and shared face boundaries.
        // Preserve the broad right end face and the original upward-right projection.
        for(int i=0;i<3;++i) {
            Point a{6+i*58.f,126-i*6.f},across{58,-6},depth{55,-24},down{8,84};
            auto face=[&](std::vector<Point> p,float gray) {
                icon.Add(BaseIconArt::Gray(gray)).parts.push_back(Poly(p));
                Outline(icon.Add({119,119,119}),p,2);
            };
            face({a,a+across,a+across+down,a+down},188);
            face({a+across,a+across+depth,a+across+depth+down,a+across+down},221);
            face({a,a+depth,a+across+depth,a+across},245);
        }
    }
    {
        auto& icon=add("nn_storystar");std::vector<Point> p;
        icon.strength=.24f;
        for(int i=0;i<16;++i) {
            float a=-Pi/2+i*Pi/8,r=i%2?29.f:(i%4?83.f:111.f);
            p.push_back({128+std::cos(a)*r,128+std::sin(a)*r});
        }
        // Each ray is a raised ridge with two differently lit planar faces.
        for(int i=0;i<16;i+=2) {
            Point tip=p[i],a=p[(i+15)%16],b=p[(i+1)%16];
            Point axis=tip-Point{128,128};axis=axis*(1/Length(axis));
            float lighting=-axis.y*.8f+axis.x*.6f;
            icon.Add(BaseIconArt::Gray(239+16*lighting)).parts.push_back(Poly({{128,128},a,tip}));
            icon.Add(BaseIconArt::Gray(231-25*lighting)).parts.push_back(Poly({{128,128},tip,b}));
        }
    }
    {
        auto& l=add("nn_playerstatus").Add(White);
        // Clean reconstruction of the original broad shoulders, narrow waist,
        // relaxed arms and slightly spread legs. One continuous symmetric contour.
        Path half({130,13});
        half.Curve({137,13},{141,16},{141,23}).To({140,36})
            .Curve({140,43},{136,45},{136,48})
            .Curve({145,49},{153,53},{160,60})
            .Curve({167,63},{170,69},{171,78})
            .Curve({172,95},{174,108},{174,122})
            .To({176,139}).Curve({177,146},{173,150},{170,149})
            .To({166,144}).To({167,129})
            .Curve({165,117},{164,104},{163,94}).To({160,81})
            .Curve({157,78},{155,83},{153,89})
            .Curve({149,97},{146,103},{148,112})
            .Curve({152,124},{152,139},{153,151})
            .Curve({158,165},{160,179},{161,192}).To({167,225})
            .Curve({168,232},{173,238},{175,241})
            .Curve({177,245},{168,247},{163,243})
            .To({157,229}).Curve({151,213},{150,198},{147,184})
            .Curve({143,170},{140,157},{139,147})
            .Curve({137,138},{134,134},{130,134});
        auto outline=half.p;
        for(auto it=half.p.rbegin()+1;it!=half.p.rend();++it)
            outline.push_back({260-it->x,it->y});
        l.parts.push_back(Poly(outline));
    }
    {
        auto& l=add("nn_info").Add(White);
        l.parts.push_back(Ring({128,128},105,12));
        l.parts.push_back(Disk({128,76},18));
        l.parts.push_back(Box({128,160},{16.5f,42},4.5f));
    }
    {
        auto& icon=add("nn_chat");auto& l=icon.Add(White);
        Path head({49,232});head.Curve({54,211},{64,189},{57,169})
            .Curve({31,149},{19,119},{23,88}).Curve({27,47},{59,22},{102,22})
            .Curve({147,20},{174,42},{177,75}).To({181,95})
            .Curve({169,94},{159,99},{160,107}).Curve({160,113},{169,115},{175,113})
            .To({195,138}).Curve({197,143},{188,147},{179,146})
            .To({179,153}).To({187,158}).To({163,166}).To({163,177})
            .To({183,185}).Curve({185,195},{171,198},{157,194})
            .To({156,211}).To({174,232});
        l.parts.push_back(Poly(head.p));
        auto& ear=icon.Add({188,188,188});
        Path fold({116,115});fold.Curve({100,102},{85,113},{89,131})
            .Curve({91,143},{106,148},{111,138});Stroke(ear,fold.p,6);
        // Eye socket opens into the silhouette like the original speaking profile.
        auto socket=Poly({{160,98},{175,96},{175,113},{160,113},{155,106}});
        socket.subtract=true;icon.layers[0].parts.push_back(socket);
        auto& speech=icon.Add(White);
        for(auto ends:std::vector<std::vector<Point>>{
                {{209,151},{225,143}},{{212,171},{232,172}},{{207,191},{223,203}}})Stroke(speech,ends,5);
    }
    {
        auto& l=add("nn_request").Add(White);
        l.parts.push_back(Disk({106,108},25));
        Path body({50,245});body.To({54,186}).Curve({54,170},{69,164},{89,163})
            .Curve({118,158},{144,148},{158,127}).Curve({171,107},{168,80},{170,53})
            .To({170,24}).Curve({177,20},{183,26},{182,36}).To({191,43})
            .To({184,60}).To({184,110}).Curve({181,143},{158,165},{149,183})
            .To({148,245}).To({79,245}).To({79,192}).To({70,199}).To({68,245});
        l.parts.push_back(Poly(body.p));
    }
    {
        auto& icon=add("nn_grouprequest");
        for(Point center:std::vector<Point>{{128,74},{66,192},{190,192}}) {
            auto const& ship=BaseIconArt::Shapes()[5];
            for(auto const& layer:ship.layers) {
                auto& copy=icon.Add(layer.color);
                for(auto shape:layer.parts) {
                    for(auto& p:shape.points)p=center+(p-Point{128,128})*.47f;
                    copy.parts.push_back(shape);
                }
            }
        }
    }
    return v;
}
inline std::vector<Icon> const& Shapes(){static auto const shapes=Build();return shapes;}
}

