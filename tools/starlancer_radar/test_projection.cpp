#include "../../src/freelancer/Client/radar_projection.h"
#include <cassert>
#include <cstdio>
#include <limits>

using namespace RadarProjection;
static bool near(float a,float b) {return std::fabs(a-b)<0.002f;}
int main()
{
    float const identity[3][3]={{1,0,0},{0,1,0},{0,0,1}};
    Layout l;
    assert(MakeLayout({0,0,1919,1079},.5f,.5f,.1f,.42f,.65f,l));
    assert(near(l.radius,108));
    Contact p;
    assert(Project({0,0,-500},{0,0,0},identity,1000,l,p));
    assert(near(p.x,l.x) && p.baseY<l.y && near(p.baseY,p.tipY));
    assert(Project({500,0,0},{0,0,0},identity,1000,l,p) && p.x>l.x);
    assert(Project({0,500,0},{0,0,0},identity,1000,l,p) && !p.below && p.tipY<p.baseY);
    assert(Project({0,-500,0},{0,0,0},identity,1000,l,p) && p.below && p.tipY>p.baseY);
    float const yaw90[3][3]={{0,0,1},{0,1,0},{-1,0,0}};
    assert(Project({-500,0,0},{0,0,0},yaw90,1000,l,p));
    assert(near(p.x,l.x) && p.baseY<l.y); // ship now faces world -X
    Contact moved;
    assert(Project({99500,30000,-70000},{100000,30000,-70000},yaw90,1000,l,moved));
    assert(near(p.x,moved.x) && near(p.tipY,moved.tipY));
    assert(!Project({1001,0,0},{0,0,0},identity,1000,l,p));
    assert(!Project({800,800,0},{0,0,0},identity,1000,l,p)); // spherical, not rectangular range
    assert(Project({1000,0,0},{0,0,0},identity,1000,l,p));
    float const nan=std::numeric_limits<float>::quiet_NaN();
    assert(!Project({nan,0,0},{0,0,0},identity,1000,l,p));
    assert(!Project({0,0,0},{0,0,0},identity,0,l,p));
    assert(EffectiveRange(2500,.25f)==625 && EffectiveRange(2500,5)==2500);
    assert(EffectiveRange(nan,1)==0 && EffectiveRange(-1,1)==0);
    assert(Accept(2,1,0x10000,0x7f0000,true,false));
    assert(!Accept(1,1,0x10000,0x7f0000,true,false));
    assert(!Accept(2,1,0x10000,0x7f0000,false,false));
    assert(!Accept(2,1,0x10000,0x7f0000,true,true));
    assert(!Accept(2,1,0x20000000,0x7f0000,true,false));
    Viewport const views[]={{0,0,639,479},{0,0,1919,1079},{0,0,3439,1439},{100,60,1099,859}};
    for(auto const& v:views)
    {
        assert(MakeLayout(v,1,1,.3f,.9f,1,l));
        assert(l.x-l.radius>=v.left && l.x+l.radius<=v.right);
        for(int angle=0;angle<360;angle+=5)
        {
            float const a=float(angle)*0.01745329252f;
            assert(Project({0,std::sin(a)*999,std::cos(a)*999},{0,0,0},identity,1000,l,p));
            assert(p.tipY>=v.top && p.tipY<=v.bottom && p.x>=v.left && p.x<=v.right);
        }
    }
    assert(!MakeLayout({10,10,9,9},.5f,.5f,.1f,.4f,.6f,l));
    assert(MakeLayout({0,0,1919,1079},nan,nan,nan,nan,nan,l));
    assert(std::isfinite(l.x) && std::isfinite(l.y));
    BatchSpace batch;
    assert(MakeBatchSpace({100,60,1099,859},{0,0,1919,1079},batch));
    float vertex[3];ToBatch(batch,600,460,vertex);
    assert(near(vertex[0],960) && near(vertex[1],540));
    // Actual viewport maps that ortho position back to the exact desired pixel.
    assert(near(vertex[0]/1920*1000+100,600));
    assert(near(vertex[1]/1080*800+60,460));
    assert(!MakeBatchSpace({0,0,-1,1},{0,0,639,479},batch));
    puts("PASS: forward/right/height, rotated and translated ship axes, spherical scanner clipping, interference-range scaling, contact filtering, finite input, 4:3/wide/ultrawide/offset viewport bounds.");
}
