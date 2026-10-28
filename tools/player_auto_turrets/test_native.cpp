// Exercise native Common interception and the controller's full-volley budget.
#include "../../src/freelancer/Client/player_turret_rules.h"
#include "common_cequip.h"
#include <cassert>
#include <cstdio>
#include <limits>

int main()
{
    using namespace PlayerTurretRules;
    assert(CanSpend(100, 100, 65, 35));
    assert(!CanSpend(100, 100, 65.0001, 35));
    assert(!CanSpend(35, 100, 1, 35));
    assert(CanSpend(35, 100, 0, 35));
    assert(!Resume(44.99f, 100, 35));
    assert(Resume(45, 100, 35));
    assert(CanSpend(10, 100, 10, 0));
    assert(!CanSpend(100, 0, 0, 0));
    assert(!CanSpend(100, 100, -1, 35));
    assert(!CanSpend(100, 100, 0, 101));
    float const nan = std::numeric_limits<float>::quiet_NaN();
    float const inf = std::numeric_limits<float>::infinity();
    // Aiming never consumes a burst; only an actual successful shot starts it.
    Behavior behavior;
    behavior.aimSeconds = 0.5f; behavior.burstSeconds = 1; behavior.restSeconds = 0.5f;
    BurstCycle cycle;
    cycle.Reset(behavior);
    assert(!cycle.Ready());
    cycle.Advance(0.25f, behavior); assert(!cycle.Ready());
    cycle.Advance(0.25f, behavior); assert(cycle.Ready());
    cycle.Advance(10, behavior); assert(cycle.Ready() && cycle.phase == BurstCycle::Phase::Aim);
    cycle.Fired(behavior);
    cycle.Advance(0.75f, behavior); assert(cycle.Ready());
    cycle.Fired(behavior); // Further shots must not restart the burst timer.
    cycle.Advance(0.25f, behavior); assert(!cycle.Ready());
    assert(cycle.phase == BurstCycle::Phase::Rest);
    cycle.Advance(0, behavior); cycle.Advance(nan, behavior);
    assert(cycle.remaining == 0.5f);
    assert(cycle.Advance(0.5f, behavior));
    assert(cycle.phase == BurstCycle::Phase::Aim && !cycle.Ready());
    cycle.Advance(0.5f, behavior); cycle.Fired(behavior);
    cycle.Advance(100, behavior); // A hitch cannot skip the required rest.
    assert(cycle.phase == BurstCycle::Phase::Rest && !cycle.Ready());
    behavior.accuracyPercent = 100;
    assert(SpreadRadians(behavior) == 0);
    behavior.accuracyPercent = 0;
    assert(std::fabs(SpreadRadians(behavior) - behavior.spreadDegrees * 0.01745329252f) < 1e-6f);
    behavior.accuracyPercent = 50;
    assert(std::fabs(SpreadRadians(behavior) - behavior.spreadDegrees * 0.00872664626f) < 1e-6f);
    assert(!CanSpend(nan, 100, 0, 35));
    assert(!CanSpend(100, inf, 0, 35));
    assert(!CanSpend(100, 100, nan, 35));
    // A manual volley spends first. Two-barrel automatic volleys cannot cross the floor.
    float energy = 100 - 17;
    unsigned volleys = 0;
    while (CanSpend(energy, 100, 2 * 8, 35)) { energy -= 16; ++volleys; }
    assert(volleys == 3 && energy == 35);
    for (unsigned reserve = 0; reserve <= 90; ++reserve)
        for (int power = 0; power <= 1000; ++power)
            if (CanSpend(float(power), 1000, 19.5, reserve))
                assert(double(power) - 19.5 >= 10.0 * reserve);

    Vector pos = {0, 0, 600}, velocity = {0, 0, 0};
    float time = 0;
    assert(CEGun::ComputeTimeToTgt(pos, velocity, 600, time));
    assert(std::fabs(time - 1) < 0.00001f);
    velocity.z = 100;
    assert(CEGun::ComputeTimeToTgt(pos, velocity, 600, time));
    assert(std::fabs(time - 1.2f) < 0.00001f);
    velocity.z = 1000;
    assert(!CEGun::ComputeTimeToTgt(pos, velocity, 600, time));
    velocity.z = -100;
    assert(CEGun::ComputeTimeToTgt(pos, velocity, 600, time));
    assert(std::fabs(time - 600.f / 700.f) < 0.00001f);
    velocity = {300, 0, 0};
    assert(CEGun::ComputeTimeToTgt(pos, velocity, 600, time));
    double const path2 = 600.0*600.0 + 300.0*300.0*time*time;
    assert(std::fabs(path2 - 600.0*600.0*time*time) < 0.1);
    puts("PASS: aim/burst/rest, blocked fire, pause/hitch timing, spread, native interception and energy budget");
}
