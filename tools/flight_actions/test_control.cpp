#include "../../src/freelancer/Client/flight_action_math.h"
#include "../../src/freelancer/Client/flight_action_camera.h"
#include <cassert>
#include <cstdio>
#include <limits>
using namespace FlightActionMath;
static void testGotoWeave() {
    namespace FC=FlightActionCamera;
    // A destination above/below the ship must still have a valid yaw axis
    // and an orthonormal camera frame, even parallel to initial up.
    for(V forward:{V{0,1,0},V{0,-1,0},unit(V{0.001f,1,0}),unit(V{1,2,3})}) {
        auto course=FC::levelCourse(forward,{0,1,0});
        V right=FC::transform(course,{1,0,0}),up=FC::transform(course,{0,1,0});
        assert(length(FC::transform(course,{0,0,-1})-forward)<1e-5f);
        assert(std::abs(dot(right,forward))<1e-5f && std::abs(dot(up,forward))<1e-5f);
        assert(std::abs(length(right)-1)<1e-5f && std::abs(length(up)-1)<1e-5f);
    }
    for(float dt:{1.f/30,1.f/60,1.f/144})
    for(float inertia:{1000.f,2800.f,6000.f})
    for(float speed:{80.f,300.f}) {
        ReverseStrafeCycle wave;
        wave.reset(2);
        float yaw=0,omega=0,elapsed=0,previous=0,minYaw=0,maxYaw=0;
        V position{},velocity{0,0,-speed};
        float minPosition=0,maxPosition=0;
        int reversals=0;
        FC::Q course=FC::levelCourse({0,0,-1},{0,1,0});
        V cameraLocal{0,5,50};
        for(int frame=0;frame<int(40/dt);++frame) {
            elapsed=std::min(elapsed+dt,1.f);
            float entry=elapsed*elapsed*(3-2*elapsed);
            float angle=-wave.sine()*(25*Pi/180)*entry;
            assert(std::abs(angle)<=25*Pi/180);
            float bearing=std::atan2(position.x,20000+position.z);
            float desired=angle+bearing;
            float error=std::sin(desired-yaw);
            float command=torque(error,omega,inertia,15000,18000);
            assert(std::isfinite(command) && std::abs(command)<=1);
            // Integrate the physical steering torque, then only FORWARD thrust.
            // No lateral engine force: visible yaw must itself create the path.
            for(int step=0;step<8;++step) {
                omega+=(18000*command-15000*omega)/inertia*(dt/8);
                yaw+=omega*(dt/8);
                V forward=rotate(V{0,0,-1},V{0,1,0},yaw);
                velocity=velocity+(forward*speed-velocity)*(2*dt/8);
                position=position+velocity*(dt/8);
            }
            if(frame*dt<2) assert(yaw>-0.01f); // Nose turns LEFT first.
            if(frame*dt>8) {
                minPosition=std::min(minPosition,position.x); maxPosition=std::max(maxPosition,position.x);
                minYaw=std::min(minYaw,yaw); maxYaw=std::max(maxYaw,yaw);
                if(yaw*previous<0) ++reversals;
            }
            assert(std::abs(position.x)<500);
            assert(std::abs(yaw-previous)<2*dt);
            previous=yaw;
            // The camera must remain level/forward while the physical ship yaws.
            FC::Q nativeRotation=FC::axisAngle({0,1,0},yaw);
            FC::Pose normal{FC::transform(nativeRotation,cameraLocal),nativeRotation};
            auto stable=FC::blendCourse(normal,course,cameraLocal,1);
            assert(length(stable.offset-cameraLocal)<1e-4f);
            assert(length(FC::transform(stable.rotation,{0,1,0})-V{0,1,0})<1e-5f);
            assert(length(FC::transform(stable.rotation,{0,0,-1})-V{0,0,-1})<1e-5f);
            auto released=FC::blendCourse(normal,course,cameraLocal,0);
            assert(length(released.offset-normal.offset)<1e-4f);
            wave.advance(dt);
        }
        assert(minYaw<-20*Pi/180 && maxYaw>20*Pi/180);
        assert(minYaw>-30*Pi/180 && maxYaw<30*Pi/180);
        assert(reversals>=15);
        assert(maxPosition-minPosition>10 && position.z<-speed*35);
    }
    for(float interval:{0.5f,2.f,3.5f}) {
        ReverseStrafeCycle wave; wave.reset(interval);
        assert(std::abs(wave.sine())<1e-6f);
        wave.advance(interval/2); assert(wave.sine()<-0.999f);
        wave.advance(interval); assert(wave.sine()>0.999f);
    }
    std::puts("PASS: Go To physical yaw left/right, forward-thrust wave, 80/300 m/s, three inertias, configurable period and fixed camera at 30/60/144 Hz.");
}
static void testTurnCamera() {
    namespace FC=FlightActionCamera;
    V up{0,1,0},forward{0,0,1};
    FC::Pose initial{{0,5,50},{}};
    for(V axis:{V{1,0,0},up,V{0,0,1},unit(V{1,2,3})})
    for(float angle:{0.f,Pi/2,Pi,Pi+0.01f}) {
        FC::Q q=FC::axisAngle(axis,angle);
        float m[9]; FC::toMatrix(q,m);
        assert(std::abs(FC::dot(q,FC::fromMatrix(m)))>0.99999f);
    }
    for(float dt:{1.f/30,1.f/60,1.f/144}) {
        FC::ReverseTurnCamera camera;
        camera.begin(initial,up);
        FC::Pose normal;
        // Rotate the ship/native camera through 180 while it travels in the old
        // direction. The actual displayed camera must not follow that rotation.
        for(float time=0;time<2.f;time+=dt) {
            FC::Q q=FC::axisAngle(up,Pi*std::min(time/2,1.f));
            normal={FC::transform(q,initial.offset),q};
            auto shown=camera.update(normal,{0,0,-100},forward,dt);
            assert(length(shown.offset-initial.offset)<1e-5f);
            assert(std::abs(FC::dot(shown.rotation,initial.rotation))>0.99999f);
        }
        camera.complete();
        FC::Q reversed=FC::axisAngle(up,Pi);
        normal={FC::transform(reversed,initial.offset),reversed};
        // Finishing the figure / restoring the engine must not release the view
        // while still moving backwards, stationary or mostly sideways.
        for(V velocity:{V{0,0,-80},V{},V{0,0,2},V{100,0,4}})
        for(int frame=0;frame<300;++frame) {
            auto shown=camera.update(normal,velocity,forward,dt);
            assert(camera.stage==FC::ReverseTurnCamera::Waiting);
            assert(length(shown.offset-initial.offset)<1e-5f);
        }
        // Isolated forward samples do not trip the 0.2-second stability gate.
        for(int i=0;i<10;++i) {
            camera.update(normal,{0,0,20},forward,dt);
            camera.update(normal,{0,0,-1},forward,dt);
            assert(camera.stage==FC::ReverseTurnCamera::Waiting);
        }
        float wait=0;
        while(camera.stage==FC::ReverseTurnCamera::Waiting) {
            camera.update(normal,{0,0,20},forward,dt);
            wait+=dt;
            assert(wait<0.3f);
        }
        assert(wait>=0.19f);
        int frames=0;
        while(camera.running()) {
            // Jitter either side of 180 must not reverse the orbit halfway through.
            FC::Q q=FC::axisAngle(up,Pi+(frames%2 ? 0.001f:-0.001f));
            normal={FC::transform(q,initial.offset),q};
            camera.cancel(); // Held manual input must not restart the return timer.
            auto shown=camera.update(normal,{0,0,20},forward,dt);
            assert(std::isfinite(length(shown.offset)));
            assert(std::abs(length(shown.offset-up*dot(shown.offset,up))-50)<1e-3f);
            assert(std::abs(shown.offset.y-5)<1e-3f);
            assert(shown.offset.x>=-0.06f);
            V back=FC::transform(shown.rotation,{0,0,1});
            assert(dot(back,unit(shown.offset-up*5))>0.999f);
            if(!camera.running()) {
                assert(length(shown.offset-normal.offset)<1e-5f);
                assert(std::abs(FC::dot(shown.rotation,normal.rotation))>0.99999f);
            }
            assert(++frames*dt<3.1f);
        }
    }
    // Manual abort before the ship finishes, pause, then a tilted moving target.
    FC::ReverseTurnCamera camera;
    camera.begin(initial,up);
    camera.cancel();
    FC::Q tilted=FC::axisAngle(up,Pi/3)*FC::axisAngle({1,0,0},0.3f);
    FC::Pose normal{FC::transform(tilted,initial.offset),tilted};
    for(float dt:{0.f,-1.f,std::numeric_limits<float>::quiet_NaN()}) {
        auto shown=camera.update(normal,{},forward,dt);
        assert(camera.returnSeconds==0 && length(shown.offset-initial.offset)<1e-5f);
    }
    for(int frame=0;frame<241;++frame) {
        auto shown=camera.update(normal,{},forward,1.f/60);
        assert(length(shown.offset)>40); // The camera never cuts through the ship.
        float m[9]; FC::toMatrix(shown.rotation,m);
        V a{m[0],m[3],m[6]},b{m[1],m[4],m[7]},c{m[2],m[5],m[8]};
        assert(std::abs(dot(a,b))<1e-5f && std::abs(dot(b,c))<1e-5f);
        assert(length(cross(a,b)-c)<1e-5f);
    }
    assert(!camera.running());

    // Feed a physical, torque-limited half-turn into the early camera trigger.
    // It must start near the end of the actual figure, while still drifting,
    // and spread the orbit across three seconds at every supported frame rate.
    for(float dt:{1.f/30,1.f/60,1.f/144}) {
        camera.begin(initial,up);
        float angle=0,omega=0,time=0,start=-1,finish=-1,turnFinish=-1;
        FC::Pose previous=initial;
        for(;time<12;time+=dt) {
            float error=std::sin(goal(angle,Pi)-angle);
            float u=torque(error,omega,2800,15000,18000);
            for(int step=0;step<8;++step) {
                omega+=(18000*u-15000*omega)/2800*(dt/8);
                angle+=omega*(dt/8);
            }
            FC::Q q=FC::axisAngle(up,angle);
            normal={FC::transform(q,initial.offset),q};
            auto shown=camera.update(normal,{0,0,-100},forward,dt,
                FC::remainingTurnTime(angle,omega,true,1));
            float frameAngle=std::acos(std::clamp(dot(unit(previous.offset-up*5),
                unit(shown.offset-up*5)),-1.f,1.f));
            assert(frameAngle<2.f*dt); // No fast one-second whip around the hull.
            previous=shown;
            if(start<0 && camera.stage==FC::ReverseTurnCamera::Returning) {
                start=time;
                assert(angle>=Pi/2 && angle<Pi-0.1f);
            }
            if(turnFinish<0 && settled(angle,Pi,std::abs(error),std::abs(omega))) {
                turnFinish=time;
                camera.complete();
            }
            if(!camera.running()) { finish=time; break; }
        }
        assert(start>=0 && turnFinish>start);
        assert(turnFinish-start>1 && turnFinish-start<3);
        assert(finish-start>2.9f && finish-start<3.1f);
        assert(FC::remainingTurnTime(Pi*0.8f,1,false,1)<0);
        assert(FC::remainingTurnTime(Pi*0.8f,1,true,0)<0);
    }
    camera.begin(initial,up);
    camera.reset(); // Death/system/camera switch discards the held frame.
    assert(!camera.running());
    std::puts("PASS: turn camera early start, three-second orbit, forward-speed fallback, pause/abort and native handoff at 30/60/144 Hz.");
}
int main() {
    testGotoWeave();
    testTurnCamera();
    // Exercise a torque-limited physical body, not just the controller's formulas.
    // Both axes/signs and different frame rates must reach the full requested angle.
    for(float dt:{1.f/30,1.f/60,1.f/144})
    for(float sign:{-1.f,1.f})
    for(float total:{Pi,2*Pi})
    for(float inertia:{1000.f,2800.f,6000.f}) {
        float angle=0,omega=0,time=0;
        for(;time<12;time+=dt) {
            float error=std::sin(sign*goal(sign*angle,total)-angle);
            float u=torque(error,omega,inertia,15000,18000);
            assert(std::isfinite(u) && std::abs(u)<=1);
            // Smaller physical substeps expose overshoot and braking behavior.
            for(int step=0;step<8;++step) {
                omega+=(18000*u-15000*omega)/inertia*(dt/8);
                angle+=omega*(dt/8);
            }
            if(settled(sign*angle,total,std::abs(error),std::abs(omega))) break;
        }
        assert(time<12);
        assert(std::abs(sign*angle-total)<0.06f);
        assert(std::abs(omega)<0.1f);
    }
    V x{1,0,0},up{0,1,0};
    V reversed=rotate(x,up,Pi);
    assert(length(reversed-V{-1,0,0})<1e-5f);
    assert(torque(1,0,1,1,0)==0);
    assert(torque(std::numeric_limits<float>::quiet_NaN(),0,1,1,1)==0);
    assert(!settled(0,2*Pi,0,0)); // Identity orientation alone is not a full roll.
    assert(length(rotate(x,V{0,0,-1},Pi/2)-V{0,-1,0})<1e-5f); // Clockwise as seen from aft.

    ReverseStrafeCycle cycle;
    for(float bad:{0.f,-1.f,std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}) {
        cycle.reset(bad);
        assert(cycle.interval==2 && cycle.left());
    }
    for(float interval:{2.f,0.75f}) {
        cycle.reset(interval);
        assert(cycle.left());
        cycle.advance(interval);
        assert(!cycle.left());
        cycle.advance(interval);
        assert(cycle.left());
        cycle.advance(0);
        cycle.advance(-1);
        cycle.advance(std::numeric_limits<float>::quiet_NaN());
        assert(cycle.phase==0);
    }
    for(float dt:{1.f/30,1.f/60,1.f/144}) {
        cycle.reset(2);
        double time=0;
        for(int frame=0;frame<100000;++frame) {
            double phase=std::fmod(time,4.0);
            if(std::abs(phase-2)>1e-6 && phase>1e-6 && phase<4-1e-6)
                assert(cycle.left()==(phase<2));
            cycle.advance(dt);
            time+=dt;
        }
    }
    cycle.reset(2);
    cycle.advance(24*60*60.f+2); // Many skipped periods: no expiry or overflow.
    assert(!cycle.left());
    cycle.advance(2);
    assert(cycle.left());
    std::puts("PASS: physical turn/roll convergence, 30/60/144 Hz, both directions, three inertias, limits and full-roll completion.");
    std::puts("PASS: clockwise roll, repeating reverse/strafe timing, configurable intervals, pause and long-running cycle.");
}
