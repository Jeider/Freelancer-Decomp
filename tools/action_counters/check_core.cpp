#include "player_action_stats.h"
#include <cassert>
#include <limits>
#include <set>
#include <string>
#include <cstdio>
using namespace PlayerActionStats;
int main() {
    State state; Tracker tracker;Flight f;
    f.valid=f.manual=true;f.engine=false;f.dt=.25;f.velocity={0,0,-80};f.forward={0,0,-1};
    state.Set(Counter::InertiaSeconds,999.5);
    tracker.Step(state,f);assert(state.Get(Counter::InertiaSeconds)==999.75);
    f.boost=true;tracker.Step(state,f);
    assert(state.Get(Counter::InertiaSeconds)==1000 && state.Get(Counter::InertiaBoostSeconds)==.25);
    assert(state.Get(Counter::BoostActivations)==1);
    f.valid=false;for(int i=0;i<100;++i)tracker.Step(state,f);
    assert(state.Get(Counter::InertiaSeconds)==1000);
    f.valid=true;f.manual=false;tracker.Step(state,f);
    assert(state.Get(Counter::InertiaSeconds)==1000 && state.Get(Counter::AutopilotSeconds)==.25);
    f.manual=true;f.velocity={};tracker.Step(state,f);
    assert(state.Get(Counter::InertiaSeconds)==1000);
    f.velocity={0,0,-80};f.lane=true;tracker.Step(state,f);f.lane=false;
    assert(state.Get(Counter::InertiaSeconds)==1000);
    f.dt=2;tracker.Step(state,f);f.dt=std::numeric_limits<double>::quiet_NaN();tracker.Step(state,f);
    assert(state.Get(Counter::InertiaSeconds)==1000);
    f.dt=.25;f.boost=false;tracker.Step(state,f);
    f.forward={0,0,1};tracker.Step(state,f);
    assert(state.Get(Counter::InertiaTurnarounds)==1 && state.Get(Counter::ReverseSeconds)==.25);
    for(int i=0;i<10;++i)tracker.Step(state,f);
    assert(state.Get(Counter::InertiaTurnarounds)==1);
    f.strafe=1;f.target=2;f.subtarget=4;f.targetHostile=true;f.aimDot=1;f.distance=500;f.closing=20;
    tracker.Step(state,f);assert(state.Get(Counter::StrafeChanges)==1 && state.Get(Counter::TargetSwitches)==1);
    assert(state.Get(Counter::SubtargetSelections)==1 && state.Get(Counter::AimedStrafeSeconds)==.25);
    f.thrust=0;tracker.Step(state,f);tracker.Step(state,f);assert(state.Get(Counter::ThrustDepletions)==1);
    tracker.Combat(state);tracker.damaged=tracker.repaired=true;
    f.targetHostile=false;f.dt=1;f.critical=true;
    for(int i=0;i<15;++i)tracker.Step(state,f);
    assert(state.Get(Counter::CombatSurvived)==1 && state.Get(Counter::CriticalSurvivals)==1);
    assert(state.Get(Counter::CombatNoRepair)==0 && state.Get(Counter::CombatNoDamage)==0 && state.Get(Counter::CombatNoThrustEmpty)==0);
    tracker.Combat(state);tracker.Reset(); // Death/load/landing must not award survival.
    tracker.Step(state,f);assert(state.Get(Counter::CombatSurvived)==1);
    assert(!state.Load("unknown_future_counter",4));
    assert(!state.Load("inertia_seconds",-1));
    assert(!state.Set(Counter::InertiaSeconds,std::numeric_limits<double>::infinity()));
    assert(!state.Set(Counter::InertiaSeconds,std::numeric_limits<double>::quiet_NaN()));
    state.Set(Counter::Distance,Limit);state.Add(Counter::Distance,100);assert(state.Get(Counter::Distance)==Limit);
    std::set<std::string> names;
    for(size_t i=0;i<Count;++i)assert(names.insert(Name(static_cast<Counter>(i))).second);
    printf("PASS: %zu unique counters; 1000-second threshold, pause/AI/stop/lane guards, maneuver transitions, combat boundaries and validation\n",Count);
}
