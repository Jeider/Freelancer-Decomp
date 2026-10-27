#include "../../src/freelancer/Client/radar_contacts.h"
#include "../../src/freelancer/Client/radar_motion.h"
#include <cassert>
#include <cstdio>
#include <vector>

struct Line {float x,y,bx,by;unsigned color;float width;};
int main()
{
    using RadarMotion::TurnRate;
    assert(TurnRate(0,0,1,1)==0 && TurnRate(.001f,.001f,1,1)==0);
    assert(TurnRate(0,1,1,1)<0 && TurnRate(0,-1,1,1)>0);
    assert(TurnRate(1,0,1,1)>0 && TurnRate(-1,0,1,1)<0);
    assert(std::fabs(TurnRate(100,100,1,1))<=RadarMotion::MaxRate);
    assert(std::fabs(TurnRate(.5f,0,1,1))<std::fabs(TurnRate(1,0,1,1)));
    assert(TurnRate(.2f,0,.4f,.4f)==TurnRate(1,0,2,2)); // Same fraction on a cruiser/fighter.
    assert(TurnRate(1,1,0,0)==0);
    RadarMotion::State slow,fast;
    for(int i=0;i<30;++i)slow.Step(1,.5f,0,1,1,1.f/30);
    for(int i=0;i<144;++i)fast.Step(1,.5f,0,1,1,1.f/144);
    assert(std::fabs(slow.angle-fast.angle)<.00001f);
    auto const paused=slow.angle;slow.Step(1,1,0,1,1,0);assert(slow.angle==paused);
    for(int i=0;i<180;++i){slow.Step(1,100,100,1,1,1.f/60);assert(std::fabs(slow.rate)<=RadarMotion::MaxRate+.000001f);}
    for(int i=0;i<1200;++i)slow.Step(1,0,0,1,1,1.f/60);
    assert(slow.rate==0 && slow.angle==0);
    slow.Step(2,0,0,1,1,1.f/60);assert(slow.angle==0&&slow.ship==2);
    slow.Step(0,1,1,1,1,1.f/60);assert(slow.angle==0&&slow.ship==0);
    puts("PASS: ship-relative turn strength, directions, 8 deg/s cap, smooth stop, frame-rate independence, pause and ship reset");
    for(float start:{.4f,-.4f,6.1f,-6.1f}) for(bool steering:{true,false})
    {
        RadarMotion::State home;home.ship=1;home.angle=start;
        // Weak steering returns even when held; mouse release ignores full residual yaw.
        float const yaw=steering ? .04f : 1.f;
        for(int i=0;i<3600;++i) {
            home.Step(1,0,yaw,1,1,1.f/60,steering);
            assert(home.returning && std::fabs(home.rate)<=RadarMotion::MaxRate+.000001f);
        }
        assert(home.angle==0 && home.rate==0);
    }
    RadarMotion::State resume;resume.ship=1;resume.angle=.3f;
    resume.Step(1,0,.03f,1,1,.016f);assert(resume.returning);
    resume.Step(1,0,.1f,1,1,.016f);assert(resume.returning); // Inside hysteresis band.
    resume.Step(1,0,.2f,1,1,.016f);assert(!resume.returning); // Maneuver interrupts return.
    resume.Step(1,0,.1f,1,1,.016f);assert(!resume.returning);
    RadarMotion::State home30,home144;
    home30.ship=home144.ship=1;home30.angle=home144.angle=.4f;
    for(int i=0;i<90;++i)home30.Step(1,0,0,1,1,1.f/30);
    for(int i=0;i<432;++i)home144.Step(1,0,0,1,1,1.f/144);
    assert(std::fabs(home30.angle-home144.angle)<.002f);
    puts("PASS: weak steering and mouse release return home, steering resumes, hysteresis, return speed cap and 30/144 FPS");
    // Lane/system alignment always uses the nearest of the four rim arrows.
    for(float start:{.4f,-.4f,6.1f,-6.1f,3.f,-3.f,.78539f,.78541f,1.57079632679f})
    {
        RadarMotion::State home;home.ship=1;home.angle=start;home.FaceForward();
        float previous=std::fabs(std::remainder(start,RadarMotion::ArrowSpacing));
        for(int i=0;i<360 && home.aligning;++i)
        {
            home.Step(1,1,1,1,1,1.f/60); // Homing overrides steering until aligned.
            float const next=std::fabs(home.angle);
            assert(next<=previous+.00001f);
            assert(previous-next<=RadarMotion::MaxRate/60+.00001f);
            previous=next;
        }
        assert(!home.aligning && home.angle==0 && home.rate==0);
    }
    for(float start:{0.f,.00001f,.4f,.78539f,.78541f,1.57079632679f,3.5f,6.1f,12.5f})
        for(float sign:{-1.f,1.f}) for(float initialRate:{-RadarMotion::MaxRate,0.f,RadarMotion::MaxRate})
        for(int fps:{4,30,60,144}) for(bool steering:{false,true})
    {
        RadarMotion::State home;home.ship=1;home.angle=start*sign;home.rate=initialRate;
        float const nearest=std::remainder(home.angle,RadarMotion::ArrowSpacing);
        float previous=home.angle,travel=0;
        for(int i=0;i<12*fps;++i) {
            home.Step(1,0,steering?.04f:1.f,1,1,1.f/fps,steering);
            travel+=std::fabs(std::remainder(home.angle-previous,RadarMotion::ArrowSpacing));
            previous=home.angle;
            assert(home.returning && std::isfinite(home.angle));
            assert(std::fabs(home.rate)<=RadarMotion::MaxRate+.000001f);
            if(i==0 && initialRate==0 && nearest!=0)
                assert(home.rate*nearest<0 || (home.angle==0 && home.rate==0));
        }
        assert(home.angle==0 && home.rate==0);
        // Allow the short exponential braking distance, but never a full turn.
        assert(travel<=RadarMotion::ArrowSpacing*.5f+.1f);
        for(int i=0;i<5*fps;++i) {
            home.Step(1,0,steering?.04f:1.f,1,1,1.f/fps,steering);
            assert(home.angle==0 && home.rate==0); // Stay stopped on later frames.
        }
    }
    puts("PASS: nearest arrow within 45 degrees, forced alignment, wrap boundaries, residual rotation and sustained stop at 4/30/60/144 FPS");
    using namespace RadarProjection;
    float const identity[3][3]={{1,0,0},{0,1,0},{0,0,1}};
    for(int width:{1024,1920,3440})
    {
        int const height=width==1024?768:width==1920?1080:1440;
        Layout l;assert(MakeLayout({0,0,width-1,height-1},.5f,.845f,.30f,.32f,.94f,l));
        assert(std::fabs(l.x-(width-1)*.5f)<.01f&&std::fabs(l.y-(height-1)*.845f)<.01f);
        assert(l.y+l.radius*l.ellipse < height*.95f); // Above central HUD bars.
        for(int mode=0;mode<3;++mode) {
            unsigned count=0;float gridStep=0;
            RadarFrame::Emit(l,mode,.8f,[&](float x,float y,float bx,float by,unsigned,float) {
                // Every emitted line remains on/inside the rim; no range marks above it.
                if(count==306) gridStep=std::hypot(bx-x,by-y);
                ++count;
            });
            unsigned const expected[]={825,833,845};
            assert(count==expected[mode] && gridStep>0);
        }
        std::vector<Line> first;
        for(int phase=0;phase<3;++phase)
        {
            std::vector<Line> lines;
            auto emit=[&](float x,float y,float bx,float by,unsigned color,float lineWidth) {
                assert(std::isfinite(x)&&std::isfinite(y)&&std::isfinite(bx)&&std::isfinite(by));
                assert(x>=0&&bx>=0&&x<width&&bx<width&&y>=0&&by>=0&&y<height&&by<height);
                lines.push_back({x,y,bx,by,color,lineWidth});
            };
            RadarFrame::Emit(l,2,.8f,emit,float(phase)*.4f);
            assert(lines.size()==845);
            assert((lines[330].color>>24)>(lines[330+63*4].color>>24)); // Sweep tail fades out.
            if(phase==0)
            {
                auto baseline=lines;
                lines.clear();
                RadarFrame::Emit(l,2,.8f,emit,0,.6f);
                assert(std::fabs(lines[0].x-baseline[0].x)>.5f); // Ship can turn the rim.
                for(unsigned i=304;i<330;++i) // Grid turns in the disk plane, with the rim.
                {
                    float const x=baseline[i].x-l.x,z=(baseline[i].y-l.y)/l.ellipse;
                    assert(std::fabs(lines[i].x-(l.x+x*std::cos(.6f)-z*std::sin(.6f)))<.001f);
                    assert(std::fabs(lines[i].y-(l.y+(x*std::sin(.6f)+z*std::cos(.6f))*l.ellipse))<.001f);
                }
                for(unsigned i=330;i<lines.size();++i)
                    assert(lines[i].x==baseline[i].x&&lines[i].y==baseline[i].y&&
                           lines[i].bx==baseline[i].bx&&lines[i].by==baseline[i].by);
                lines=baseline; // Sweep and player marker remain independent.
            }
            if(phase==0)first=lines;
            else {
                assert(first[0].x==lines[0].x && first[0].y==lines[0].y); // Fixed ring.
                assert(std::fabs(first[330].bx-lines[330].bx)>.1f); // Sweep rotates.
                assert(first[310].x==lines[310].x&&first[310].y==lines[310].y); // Grid does not spin.
            }
            Vec3 points[]={{-.18f,.48f,-.10f},{.28f,.3f,.3f},{.05f,-.3f,-.22f},
                           {-.45f,.14f,-.3f},{.32f,-.65f,.2f},{.03f,.02f,-.02f}};
            for(int i=0;i<6;++i)
            {
                Contact p;auto const& pos=points[i];
                assert(Project(pos,{0,0,0},identity,1,l,p));
                assert(p.tipY>=l.contactTop&&p.tipY<=l.contactBottom);
                auto const start=lines.size();
                RadarContacts::Emit(p,i%3==0?0xff4438:i%3==1?0xc1d8de:0x55f293,
                    i==0,i!=3,.85f,(std::max)(2.f,l.radius*.022f),emit);
                for(int j=1;j<8;++j) assert((lines[start+j].color>>24)>(lines[start+j-1].color>>24));
            }
            if(width==1024)
            {
                char name[64];std::snprintf(name,sizeof(name),"radar_phase%d.csv",phase);
                FILE* f=nullptr;fopen_s(&f,name,"w");assert(f);
                for(auto const& a:lines)std::fprintf(f,"%f,%f,%f,%f,%u,%f\n",a.x,a.y,a.bx,a.by,a.color,a.width);
                std::fclose(f);
            }
        }
    }
    puts("PASS: original ring edges, ship-driven rim/grid and independent fading sweep, contacts and clipped stems; 4:3/wide/ultrawide placement; three production-geometry previews exported.");
}
