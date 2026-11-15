#include "cursor_vector_art.h"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
using namespace CursorVectorArt;
static void Require(bool ok,char const* message) {if(!ok){std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}}
static void Write(std::string path,std::vector<uint32_t> const& pixels) {
    std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<char const*>(pixels.data()),pixels.size()*4);
    Require(bool(f),"preview output");
}
int main(int argc,char** argv) {
    Require(argc==2,"output directory argument");std::string dir=argv[1];
    Require(Icons().size()==16,"sixteen distinct mouse.ini shapes");
    // Compare actual evaluated surfaces, including ship shading and container
    // occlusion, against the authoritative BASESIDE shapes at matching coordinates.
    for(char const* name:{"talk_equip_dealer","talk_commodity_dealer","talk_ship_dealer","talk_story"}) {
        auto cursor=Icons()[Find(name)];cursor.strength=0;
        int index=std::strcmp(name,"talk_equip_dealer")==0?1:
            std::strcmp(name,"talk_commodity_dealer")==0?2:5;
        auto base=std::strcmp(name,"talk_story")==0 ? NnIconArt::Shapes()[2] : BaseIconArt::Shapes()[index];base.strength=0;
        for(int y=8;y<248;y+=7)for(int x=8;x<248;x+=7) {
            Point p{float(x),float(y)};
            auto a=Evaluate(cursor,p,1);
            auto b=Evaluate(base,p*cursor.sampleScale+cursor.sampleOffset,cursor.sampleScale);
            Require(std::fabs(a.alpha-b.alpha)<.00001f,"shared BASESIDE/cursor silhouette and detail alignment");
            if(a.alpha>.1f)Require(std::fabs(a.color.r-b.color.r*Blue.r/255)<.001f &&
                std::fabs(a.color.g-b.color.g*Blue.g/255)<.001f &&
                std::fabs(a.color.b-b.color.b*Blue.b/255)<.001f,"shared surface shading with cursor blue tint");
        }
    }
    auto const& arrow=Icons()[Find("arrow")];
    Point axis{.64f,.7683749f},normal{-axis.y,axis.x},tip{80,72};
    for(int t=0;t<=135;t+=3)for(int n=0;n<=30;++n) {
        auto a=Evaluate(arrow,tip+axis*float(t)+normal*float(n),1);
        auto b=Evaluate(arrow,tip+axis*float(t)-normal*float(n),1);
        Require(std::fabs(a.alpha-b.alpha)<.0001f,"front and rear triangles share exact reflection symmetry");
    }
    Require(Evaluate(arrow,{80,72},1).alpha>.95f,"arrow tip coincides with unchanged mouse.ini hotspot");
    Require(Evaluate(arrow,tip+axis*68.f,1).alpha>.08f,"visible internal arrow halo");
    Require(Evaluate(arrow,{80,72},1).color.r<200,"arrow core is blue, not white");
    auto const& circle=Icons()[Find("cross")];
    for(int k=0;k<90;++k) {
        Point d{std::cos(k*.07f),std::sin(k*.07f)};
        float a=Evaluate(circle,Point{128,128}+d*99.5f,1).alpha;
        float b=Evaluate(circle,{227.5f,128},1).alpha;
        Require(std::fabs(a-b)<.0001f,"ring antialiasing is concentric at equal radius");
    }
    float outer=Evaluate(circle,{238,128},1).alpha;
    float inner=Evaluate(circle,{205,128},1).alpha;
    Require(outer==0 && inner==0,"targeting rings have NO inner or outer glow");
    for(char const* name:{"neutral","hostile_fire","friendly","cross","no_fire"})
        Require(Icons()[Find(name)].strength==0,"all flight cursor halos disabled");
    float last=1;
    for(int i=0;i<25;++i) {float a=Halo(circle,float(i));Require(a<=last,"monotonic smooth glow falloff");last=a;}
    Require(TextureSize(24)==64 && TextureSize(85)==256 && TextureSize(300)==512,"bounded size-adaptive cache");
    auto const& dollar=Icons()[Find("talk_bribe")];
    Require(Evaluate(dollar,{112,113},1).alpha>.9f && Evaluate(dollar,{145,113},1).alpha<.3f,
        "dollar S descends left to right, never mirrored");
    Require(Evaluate(dollar,{128,42},1).alpha>.95f && Evaluate(dollar,{116,42},1).alpha<.3f &&
        Evaluate(dollar,{140,42},1).alpha<.3f,"dollar has one centred vertical bar");
    auto const& info=Icons()[Find("talk_info")];
    Require(Evaluate(info,{128,81},1).alpha>.95f && Evaluate(info,{128,99},1).alpha<.5f &&
        Evaluate(info,{128,160},1).alpha>.95f,"information icon is lowercase i with a separate upper dot");
    auto start=std::chrono::steady_clock::now();
    for(size_t i=0;i<Icons().size();++i) {
        auto const& icon=Icons()[i];
        for(int size:{64,128,256}) {
            auto pixels=Rasterize(icon,size);
            size_t visible=0;
            for(auto p:pixels)visible+=(p>>24)>16;
            Require(visible>5 && visible<pixels.size()*3/4,"nonempty icon with transparent background");
            for(int j=0;j<size;++j)
                Require((pixels[j]>>24)<3 && (pixels[(size-1)*size+j]>>24)<3 &&
                    (pixels[j*size]>>24)<3 && (pixels[j*size+size-1]>>24)<3,"halo does not clip tile boundaries");
            Write(dir+"/"+icon.name+"_"+std::to_string(size)+".bgra",pixels);
        }
    }
    // A second pass matches the expected cache warm-up sizes at 1080p.
    auto warm=std::chrono::steady_clock::now();size_t bytes=0;
    for(auto const& icon:Icons()) {
        float scale=std::strcmp(icon.name,"arrow")==0?.25f:
            std::strncmp(icon.name,"talk_",5)==0?.175f:.1125f;
        int size=TextureSize(256*scale*1.8f);bytes+=Rasterize(icon,size).size()*4;
    }
    auto end=std::chrono::steady_clock::now();
    std::printf("PASS: geometry, alpha, symmetric arrow/hotspot, concentric AA and no reticle halos, 16 shapes at 3 sizes\n");
    std::printf("CPU export %.1f ms; 1080p warm %.1f ms; cache %.2f MiB; draw 2 triangles\n",
        std::chrono::duration<double,std::milli>(warm-start).count(),
        std::chrono::duration<double,std::milli>(end-warm).count(),bytes/1048576.0);
}
