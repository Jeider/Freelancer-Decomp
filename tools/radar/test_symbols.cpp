#include "../../src/freelancer/Client/radar_symbols.h"
#include <cassert>
#include <cstdio>
#include <limits>

int main()
{
    using namespace RadarSymbols;
    using namespace RadarProjection;
    assert(Classify(MissileMask)==Kind::Missile);
    for(int attitude:{-1,0,1}) {
        assert(MissileColor(attitude,true,0)==0xff4438u);
        assert(MissileColor(attitude,true,.249f)==0xff4438u);
        assert(MissileColor(attitude,true,.25f)==0xffe35bu);
        assert(MissileColor(attitude,true,.499f)==0xffe35bu);
        assert(MissileColor(attitude,false,.3f)==ContactColor(Kind::Missile,attitude));
    }
    assert(Classify(2)==Kind::Planet && Classify(1)==Kind::Planet);
    assert(Classify(0x10000)==Kind::Triangle && Classify(0x20000)==Kind::Triangle && Classify(LootMask)==Kind::Triangle);
    assert(Classify(0x200000)==Kind::Capital && Classify(0x80000)==Kind::Capital);
    assert(Classify(0x100000)==Kind::Transport && Classify(0x400000)==Kind::Transport);
    assert(Classify(0x100)==Kind::Dockable && Classify(0x1000)==Kind::Platform && Classify(0x80)==Kind::TradeLane);
    assert((SolarMask&0x83)==0x83 && !(SolarMask&0x20004004)); // No stars, debris or non-targetables.
    assert(ContactColor(Kind::Planet,1)==ContactColor(Kind::Planet,0));
    assert(ContactColor(Kind::Triangle,1)==0x55f293u && ContactColor(Kind::Planet,-1)==0xff4438u);
    Layout l;assert(MakeLayout({0,0,1023,767},.5f,.845f,.3f,.32f,.94f,l));
    // No internal wire edges: nonhorizontal sphere lines must join silhouette vertices.
    Contact const sphere={l.x,l.y,l.y,0,false};
    unsigned circleEdges=0;
    Emit(sphere,Kind::Missile,0,1000,l,0xff4438u,false,.8f,4,
        [&](float x,float y,float bx,float by,unsigned rgb,float) {
            assert((rgb&0xffffffu)==0xff4438u);
            assert(std::fabs(std::hypot(x-l.x,y-l.y)-5.f)<.001f);
            assert(std::fabs(std::hypot(bx-l.x,by-l.y)-5.f)<.001f);
            ++circleEdges;
        });
    assert(circleEdges==16); // Hollow circle, no diamond or interior fill.
    float const sphereRadius=80.f/1000.f*l.radius;
    unsigned outlines=0,fills=0;
    Emit(sphere,Kind::Planet,80,1000,l,ContactColor(Kind::Planet,1),false,.8f,5,
        [&](float x,float y,float bx,float by,unsigned rgb,float) {
            assert((rgb&0xffffffu)==0xc1d8deu);
            if(std::fabs(y-by)<.00001f) ++fills;
            else {
                assert(std::fabs(std::hypot(x-l.x,y-l.y)-sphereRadius)<.001f);
                assert(std::fabs(std::hypot(bx-l.x,by-l.y)-sphereRadius)<.001f);
                ++outlines;
            }
        });
    assert(outlines==16 && fills>0);
    float const rotation[3][3]={{1,0,0},{0,1,0},{0,0,1}};
    Contact p;
    assert(!Project({1200,0,0},{0,0,0},rotation,1000,l,p));
    assert(Project({1200,0,0},{0,0,0},rotation,1000,l,p,300)); // Planet surface within range.
    assert(p.x>l.x+l.radius); // Keep the true centre instead of sticking it to the rim.
    assert(!Project({1400,0,0},{0,0,0},rotation,1000,l,p,300));
    assert(!Project({0,0,0},{0,0,0},rotation,1000,l,p,std::numeric_limits<float>::quiet_NaN()));
    FILE* preview=nullptr;fopen_s(&preview,"radar_symbols.csv","w");assert(preview);
    unsigned emitted=0;
    auto draw=[&](float x,float y,float bx,float by,unsigned color,float width) {
        assert(std::isfinite(x)&&std::isfinite(y)&&std::isfinite(bx)&&std::isfinite(by));
        assert(x>=l.x-l.radius-.001f&&x<=l.x+l.radius+.001f&&bx>=l.x-l.radius-.001f&&bx<=l.x+l.radius+.001f);
        assert(y>=l.contactTop-.001f&&by>=l.contactTop-.001f&&y<=l.contactBottom+.001f&&by<=l.contactBottom+.001f);
        ++emitted;
        std::fprintf(preview,"%f,%f,%f,%f,%u,%f\n",x,y,bx,by,color,width);
    };
    for(auto kind:{Kind::Planet,Kind::Capital,Kind::Transport,Kind::Dockable,Kind::Platform,Kind::TradeLane}) {
        assert(Mesh(kind) && Mesh(kind)->edgeCount>0);
        p={l.x,l.y,l.y-40,0,false};
        auto const before=emitted;Emit(p,kind,80,1000,l,0xc1d8de,true,.8f,5,draw);
        assert(emitted>before);
    }
    // Real planetary radius doubles on zoom-in, without a marker-size clamp.
    for(auto const& marker:{Contact{l.x,l.y,l.y-40,0,false},
                           Contact{l.x+l.radius,l.y,l.y,0,false},
                           Contact{l.x,l.y,l.contactBottom,0,true}})
        Emit(marker,Kind::Missile,0,1000,l,0xffe35bu,true,.8f,5,draw);
    float extents[2]={};
    p={l.x,l.y,l.y-70,0,false};
    for(int mode=0;mode<2;++mode)
        Emit(p,Kind::Planet,80,mode==0?1000.f:500.f,l,0xc1d8de,false,.8f,5,
            [&](float x,float,float bx,float,unsigned,float) {extents[mode]=(std::max)(extents[mode],(std::max)(std::fabs(x-p.x),std::fabs(bx-p.x)));});
    assert(std::fabs(extents[1]-2*extents[0])<.001f);
    // Giant planet clipped in bounded work even when its centre is offscreen.
    assert(Project({1200,0,0},{0,0,0},rotation,1000,l,p,1000));
    unsigned const before=emitted;Emit(p,Kind::Planet,1000,1000,l,0xc1d8de,true,.8f,5,draw);
    assert(emitted>before && emitted-before<1000);
    std::fclose(preview);
    FILE* catalog=nullptr;fopen_s(&catalog,"radar_symbol_catalog.csv","w");assert(catalog);
    Layout const catalogLayout={400,100,400,.32f,.94f,0,180};
    int column=0;
    for(auto kind:{Kind::Planet,Kind::Capital,Kind::Transport,Kind::Dockable,Kind::Platform,Kind::TradeLane}) {
        Contact const sample={65.f+column++*130.f,70,70,0,false};
        Emit(sample,kind,70,1000,catalogLayout,0xc1d8de,false,.9f,16,
            [&](float x,float y,float bx,float by,unsigned color,float width) {
                std::fprintf(catalog,"%f,%f,%f,%f,%u,%f\n",x,y,bx,by,color,width);
            });
    }
    std::fclose(catalog);
    puts("PASS: Beta symbols, triangles, hollow missile circles, threat colors, planetary size, zoom and clipped drawing");
}
