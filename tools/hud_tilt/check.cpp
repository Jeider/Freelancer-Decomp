#include "../../src/freelancer/Client/hud_tilt_math.h"
#include <cstdio>
#include <cstdlib>
#include <initializer_list>

static void Require(bool ok, const char* what)
{
    if (!ok) { std::fprintf(stderr,"FAIL: %s\n",what); std::exit(1); }
}
int main()
{
    unsigned points = 0;
    float maxError = 0;
    for (float width : {800.f,1920.f,3440.f,5120.f})
    for (float height : {600.f,1080.f,1440.f})
    for (int side : {-1,1})
    for (float angle : {0.f,1.f,10.f,20.f,30.f,45.f,50.f})
    {
        auto t = HudTiltTransform::Make(width,height,side,angle);
        float px=t.PivotX, py=t.PivotY;
        t.Project(px,py);
        Require(px==t.PivotX && py==t.PivotY,"outer hinge remains fixed");
        for (int ix=0;ix<=40;++ix)
        for (int iy=-5;iy<=25;++iy)
        {
            const float sx=width*ix/40, sy=height*iy/20;
            float x=sx,y=sy;
            // Only the corresponding half-screen belongs to this panel; drag/capture
            // deliberately includes points above/below the viewport.
            if ((side<0 && sx>width*.5f) || (side>0 && sx<width*.5f)) continue;
            t.Project(x,y);
            Require(std::isfinite(x) && std::isfinite(y),"finite projected panel");
            if (angle==0) Require(std::fabs(x-sx)<.001f && std::fabs(y-sy)<.001f,"zero angle identity");
            Require(t.Unproject(x,y),"inverse exists throughout panel and drag bounds");
            maxError=std::fmax(maxError,std::fmax(std::fabs(x-sx),std::fabs(y-sy)));
            // Float cancellation grows at large angles on 5120x600. Still require
            // less than 1/100 pixel error throughout panel and capture bounds.
            Require(std::fabs(x-sx)<.01f && std::fabs(y-sy)<.01f,"click matches displayed geometry");
            ++points;
        }
        auto other=HudTiltTransform::Make(width,height,-side,angle);
        float x=width*.1f,y=height*.6f,mx=width-x,my=y;
        if(side>0) { x=width-x; mx=width-mx; }
        t.Project(x,y); other.Project(mx,my);
        Require(std::fabs(x+mx-width)<.002f && std::fabs(y-my)<.002f,"left/right symmetry");
    }
    std::printf("PASS: %u panel points, inverse picking, zero angle, hinge, symmetry and capture bounds\n",points);
    std::printf("Maximum roundtrip error: %g pixels\n",maxError);
}
