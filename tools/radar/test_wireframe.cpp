#include "../../src/freelancer/Client/radar_wireframe_geometry.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <string>

using namespace RadarWireframe;
static std::vector<unsigned char> Load(std::string const& path)
{
    std::ifstream file(path, std::ios::binary);
    assert(file);
    return {std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>()};
}

int main()
{
    RadarProjection::Layout layout = {500, 400, 200, .32f, .94f, 100, 700};
    auto inside=[&](float x,float y) {
        double const nx=(double(x)-layout.x)/layout.radius;
        double const ny=(double(y)-layout.y)/(layout.radius*layout.ellipse);
        return nx*nx+ny*ny <= 1.00001;
    };
    {
        float ax=0,ay=400,bx=1000,by=400;
        assert(ClipToDish(layout,ax,ay,bx,by)&&std::fabs(ax-300)<.001&&std::fabs(bx-700)<.001);
        ax=500;ay=0;bx=500;by=1000;
        assert(ClipToDish(layout,ax,ay,bx,by)&&std::fabs(ay-336)<.001&&std::fabs(by-464)<.001);
        ax=300;ay=340;bx=340;by=340;assert(!ClipToDish(layout,ax,ay,bx,by)); // Rectangle corner outside dish.
        ax=400;ay=336;bx=600;by=336;
        assert(ClipToDish(layout,ax,ay,bx,by)&&std::fabs(ax-500)<.001&&std::fabs(bx-500)<.001);
        ax=500;ay=400;bx=500;by=400;assert(ClipToDish(layout,ax,ay,bx,by));
        ax=500;ay=500;bx=500;by=500;assert(!ClipToDish(layout,ax,ay,bx,by));
        ax=500;ay=400;bx=800;by=500;
        assert(ClipToDish(layout,ax,ay,bx,by)&&inside(ax,ay)&&inside(bx,by));
    }
    float const rotation[3][3] = {{1,0,0},{0,1,0},{0,0,1}};
    float model[12] = {1,0,0,0,1,0,0,0,1,0,0,0};
    auto p = Project({100,50,-100}, model, {0,0,0}, rotation, 1000, layout);
    assert(std::fabs(p.x-520) < .001 && std::fabs(p.y-384.2f) < .001);
    model[9] = 100;
    p = Project({100,0,0}, model, {100,0,0}, rotation, 1000, layout);
    assert(std::fabs(p.x-520) < .001);
    float const turned[3][3] = {{0,0,1},{0,1,0},{-1,0,0}};
    p = Project({100,0,0}, model, {100,0,0}, turned, 1000, layout);
    assert(std::fabs(p.x-500) < .001 && std::fabs(p.y-406.4f) < .001);
    model[0]=0;model[2]=1;model[6]=-1;model[8]=0;
    p = Project({100,0,0}, model, {100,0,0}, rotation, 1000, layout);
    assert(std::fabs(p.x-500) < .001 && std::fabs(p.y-393.6f) < .001);
    model[0]=1;model[2]=0;model[6]=0;model[8]=1;model[9]=0;
    {
        auto top=layout;top.topDown=true;top.ellipse=1;top.elevation=0;
        float const pitch[3][3]={{1,0,0},{0,.8660254f,-.5f},{0,.5f,.8660254f}};
        auto a=Project({100,300,-200},model,{0,100,0},rotation,1000,top);
        auto b=Project({100,300,-200},model,{0,100,0},pitch,1000,top);
        assert(std::fabs(a.x-b.x)<.001&&std::fabs(a.y-b.y)<.001);
        auto c=Project({100,300,-200},model,{0,100,0},turned,1000,top);
        assert(std::fabs(a.x-c.x)>1&&std::fabs(a.y-c.y)>1);
    }

    Geometry corridor;
    corridor.vertices = {{-10000,0,0},{10000,0,0}};
    corridor.indices = {0,1};
    std::vector<Point> scratch;
    int lines=0;
    auto line=[&](float ax,float ay,float bx,float by,unsigned,float) {
        assert(std::isfinite(ax)&&std::isfinite(ay)&&std::isfinite(bx)&&std::isfinite(by));
        assert(ax>=300-.01f&&ax<=700+.01f&&bx>=300-.01f&&bx<=700+.01f);
        assert(ay>=148-.01f&&ay<=700+.01f&&by>=148-.01f&&by<=700+.01f);
        assert(inside(ax,ay)&&inside(bx,by));
        ++lines;
    };
    assert(Emit(corridor,model,{0,0,0},rotation,1000,layout,0,scratch,line)==1);
    assert(lines==1); // Both endpoints beyond scanner range; the intersecting segment remains.
    model[10]=100000;
    assert(Emit(corridor,model,{0,0,0},rotation,1000,layout,0,scratch,line)==0);
    model[10]=0;

    std::ifstream fixtures("fixtures.txt");assert(fixtures);
    std::string name;unsigned parts=0,edges=0;
    while(std::getline(fixtures,name))
    {
        if(name.empty())continue;
        auto data=Load(name);
        auto meshBytes=Read<unsigned>(data.data(),0), wireBytes=Read<unsigned>(data.data(),4);
        assert(data.size()==8u+meshBytes+wireBytes);
        auto* mesh=data.data()+8;auto* wire=mesh+meshBytes;
        Geometry geometry;
        assert(Decode(mesh,meshBytes,wire,wireBytes,geometry));
        assert(geometry.indices.size()==Read<unsigned short>(wire,12));
        assert(MeshBytes(mesh)==meshBytes);
        edges+=static_cast<unsigned>(geometry.indices.size()/2);++parts;
        for(float range:{500.f,2000.f,20000.f})
            Emit(geometry,model,{0,0,0},rotation,range,layout,0,scratch,line);
        Geometry bad;
        assert(!Decode(mesh,meshBytes,wire,15,bad));
        assert(!Decode(mesh,meshBytes-1,wire,wireBytes,bad));
        assert(!Decode(mesh,meshBytes,nullptr,0,bad)); // Never synthesize triangle edges.
    }
    assert(parts>0);
    std::cout<<"PASS: "<<parts<<" real Lair wire parts / "<<edges<<" edges; scale, rotation, translation, long-segment clipping, missing-wire rejection\n";
}
