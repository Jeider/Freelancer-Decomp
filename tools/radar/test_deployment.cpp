#include "../../src/freelancer/Client/radar_deployment.h"
#include "../../src/freelancer/Client/radar_frame.h"
#include <cassert>
#include <cstdio>
#include <limits>

int main()
{
    using RadarDeployment::State;
    RadarDeployment::AutoState automatic;
    automatic.Step(.1f);assert(!automatic.Open());
    automatic.match=true;automatic.Step(.1f);assert(automatic.Open());
    automatic.match=false;automatic.Step(1.f);assert(automatic.Open());
    automatic.Step(.6f);assert(!automatic.Open());
    automatic.match=true;automatic.Step(.1f);automatic.Close();
    automatic.Step(.1f);assert(!automatic.Open()); // Manual close wins until this contact group leaves.
    automatic.match=false;automatic.Step(.1f);
    automatic.match=true;automatic.Step(.1f);assert(automatic.Open());
    State s;
    assert(!s.Visible() && !s.Running(false));
    s.Step(true, .175f);
    assert(std::fabs(s.Scale() - .59f) < .00001f && !s.Running(true));
    float const before = s.Scale();
    s.Step(false, .01f);
    assert(s.Scale() < before && s.Scale() > .18f);
    s.Step(true, .35f);
    assert(s.Scale() == 1 && s.Running(true));
    assert(!s.Running(false)); // Contacts stop immediately, before the first closing frame.
    s.Step(false, .35f);
    assert(s.position == 0 && !s.Visible());
    s.Step(true, std::numeric_limits<float>::quiet_NaN());
    s.Step(true, -1);
    assert(s.position == 0);
    for (int fps : {30, 60, 144, 240})
    {
        State timed;
        for (int i = 0; i < fps; ++i) timed.Step(true, 1.f / fps);
        assert(timed.Running(true) && timed.Scale() == 1);
        for (int i = 0; i < fps; ++i) timed.Step(false, 1.f / fps);
        assert(timed.position == 0);
    }
    RadarProjection::Layout l = {500, 500, 100, .32f, .94f, 0, 1000};
    int idleLines = 0, liveLines = 0;
    auto idle = [&](float, float, float, float, unsigned, float) { ++idleLines; };
    auto live = [&](float, float, float, float, unsigned, float) { ++liveLines; };
    RadarFrame::Emit(l, 2, .8f, idle, 0, 0, false);
    RadarFrame::Emit(l, 2, .8f, live, 0, 0, true);
    assert(idleLines > 0 && liveLines == idleLines + 2 * 64 * 4 + 3);
    // Exercise the real rim emitter across resolutions and viewport offsets.
    for (int width : {1024, 1920, 3440})
    {
        RadarProjection::Layout base;
        int const bottom = 1109;
        assert(RadarProjection::MakeLayout({50,30,width+49,bottom},.5f,.845f,.3f,.32f,.94f,base));
        float previousY = base.y;
        for (int frame=0; frame<=100; ++frame)
        {
            State slide;slide.position=1.f-float(frame)/100.f;
            auto animated=base;slide.Apply(animated,bottom);
            assert(animated.y>=previousY-.001f);
            assert(animated.x==base.x);
            previousY=animated.y;
            if (frame==0) assert(animated.y==base.y&&animated.radius==base.radius);
            if (frame==100)
            {
                assert(!slide.Visible());
                auto below=[&](float, float ay, float, float by, unsigned, float) {
                    assert(ay>bottom+1&&by>bottom+1);
                };
                for (float angle : {0.f, .4f, .8f, 1.2f})
                    RadarFrame::Emit(animated,2,.8f,below,0,angle,false);
                assert(animated.y-animated.radius*.93f*animated.ellipse>bottom+1);
            }
        }
    }
    puts("PASS: reversible deployment, FPS independence, contacts stop, rim/background exit below viewport");
}
