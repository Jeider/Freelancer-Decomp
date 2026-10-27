#include "../../src/freelancer/Client/cockpit_head_motion.h"
#include <cstdio>
#include <cstdlib>
#include <limits>

using CockpitHeadMotion::State;

static void Require(bool condition, const char* message)
{
    if (!condition) { std::fprintf(stderr, "FAIL: %s\n", message); std::exit(1); }
}

static void Near(float actual, float expected, const char* message)
{
    Require(std::isfinite(actual) && std::fabs(actual - expected) < .00002f, message);
}

static void Run(State& state, int fps, float pitch, float yaw, float seconds)
{
    for (int i = 0; i < static_cast<int>(fps * seconds); ++i)
        state.Step(pitch, yaw, 40.f, 25.f, 1.f / fps);
}

int main()
{
    const auto right = CockpitHeadMotion::FromManualInput(1.f, 0.f);
    const auto up = CockpitHeadMotion::FromManualInput(0.f, -1.f);
    Near(right.pitch, 0.f, "horizontal input affects pitch");
    Near(right.yaw, -1.f, "right input must look right");
    Near(up.pitch, 1.f, "up input must look up");
    Near(up.yaw, 0.f, "vertical input affects yaw");
    const auto partial = CockpitHeadMotion::FromManualInput(.25f, -.25f);
    Near(partial.pitch, .25f, "mouse pitch must not be amplified");
    Near(partial.yaw, -.25f, "mouse yaw must not be amplified");
    const auto invalid = CockpitHeadMotion::FromManualInput(
        std::numeric_limits<float>::infinity(), std::numeric_limits<float>::quiet_NaN());
    Near(invalid.pitch, 0.f, "invalid manual pitch");
    Near(invalid.yaw, 0.f, "invalid manual yaw");

    // Small angles stay below the rate cap: response is twice as slow as the
    // last installed .32/.48 version, without changing the input during the test.
    State small;
    for (int i = 0; i < 64; ++i) small.Step(0.f, -1.f, 10.f, 10.f, .01f);
    Near(small.yaw, -10.f * CockpitHeadMotion::DegreesToRadians * (1.f - std::exp(-1.f)),
         "turn response should take .64 seconds");
    const float smallReturn = small.yaw;
    for (int i = 0; i < 96; ++i) small.Step(0.f, 0.f, 10.f, 10.f, .01f);
    Near(small.yaw, smallReturn * std::exp(-1.f), "return response should take .96 seconds");

    // A held edge must not pull back, exceed the physical speed cap or overshoot.
    const float yawLimit = 40.f * CockpitHeadMotion::DegreesToRadians;
    State slower;
    for (int i = 0; i < 1200; ++i)
    {
        const float previous = slower.yaw;
        slower.Step(right.pitch, right.yaw, 40.f, 25.f, 1.f / 60.f);
        Require(slower.yaw <= previous && slower.yaw >= -yawLimit, "held edge pulls back or overshoots");
        Require(previous - slower.yaw <= CockpitHeadMotion::MaxTurnRate / 60.f + .000001f,
                "turn exceeds angular speed cap");
    }
    const float beforeReturn = slower.yaw;
    for (int i = 0; i < 1500; ++i)
    {
        const float previous = slower.yaw;
        slower.Step(0.f, 0.f, 40.f, 25.f, .01f);
        Require(slower.yaw >= previous && slower.yaw <= 0.f, "return reverses or crosses center");
        Require(slower.yaw - previous <= CockpitHeadMotion::MaxReturnRate * .01f + .00001f,
                "return exceeds angular speed cap");
    }
    Require(beforeReturn < 0.f && slower.yaw == 0.f, "slow return must settle at center");

    // End-to-end regression: same mouse input as the last installed build,
    // including its sensitivity gain, rather than only testing the filter.
    for (float sensitivity : {.1f, .25f, .75f, 1.f})
        for (float mouseX : {.1f, .25f, .5f, 1.f})
        {
            const float oldControl = -(std::min)(1.f, mouseX / sensitivity);
            const float oldTarget = CockpitHeadMotion::SteeringAxis(oldControl) * yawLimit;
            float oldYaw = 0.f;
            State current;
            const auto control = CockpitHeadMotion::FromManualInput(mouseX, 0.f);
            for (int frame = 0; frame < 60; ++frame)
            {
                oldYaw += (oldTarget - oldYaw) * (1.f - std::exp(-1.f / (60.f * .32f)));
                current.Step(control.pitch, control.yaw, 40.f, 25.f, 1.f / 60.f);
                Require(std::fabs(current.yaw) < std::fabs(oldYaw), "same mouse input moves head faster than previous build");
            }
        }

    // The same elapsed time must produce the same look, including a reversal
    // and release. Four FPS also exercises the maximum accepted time step.
    State reference;
    Run(reference, 60, 1.f, -1.f, .5f);
    const State first = reference;
    Run(reference, 60, -.5f, .75f, .5f);
    const State reversed = reference;
    Run(reference, 60, 0.f, 0.f, .5f);
    for (int fps : {4, 30, 60, 144, 240})
    {
        State state;
        Run(state, fps, 1.f, -1.f, .5f);
        Near(state.pitch, first.pitch, "pitch response depends on FPS");
        Near(state.yaw, first.yaw, "yaw response depends on FPS");
        Run(state, fps, -.5f, .75f, .5f);
        Near(state.pitch, reversed.pitch, "pitch reversal depends on FPS");
        Near(state.yaw, reversed.yaw, "yaw reversal depends on FPS");
        Run(state, fps, 0.f, 0.f, .5f);
        Near(state.pitch, reference.pitch, "pitch return depends on FPS");
        Near(state.yaw, reference.yaw, "yaw return depends on FPS");
        Run(state, fps, 0.f, 0.f, 15.f);
        Require(state.pitch == 0 && state.yaw == 0, "return never settles");
    }

    State state;
    Run(state, 60, 1.f, -1.f, 12.f);
    Near(state.pitch, 25.f * CockpitHeadMotion::DegreesToRadians, "vertical limit");
    Near(state.yaw, -40.f * CockpitHeadMotion::DegreesToRadians, "horizontal limit");
    float matrix[9];
    state.WriteOrientation(matrix);
    // Eye forward is -column 2. Positive pitch / negative yaw must look up/right.
    Require(-matrix[2] > 0 && -matrix[5] > 0 && -matrix[8] < 0, "look direction signs");
    for (int a = 0; a < 3; ++a)
        for (int b = 0; b < 3; ++b)
        {
            float dot = 0;
            for (int row = 0; row < 3; ++row) dot += matrix[row * 3 + a] * matrix[row * 3 + b];
            Near(dot, a == b ? 1.f : 0.f, "orientation is not orthonormal");
        }
    const float determinant = matrix[0] * (matrix[4] * matrix[8] - matrix[5] * matrix[7])
                            - matrix[1] * (matrix[3] * matrix[8] - matrix[5] * matrix[6])
                            + matrix[2] * (matrix[3] * matrix[7] - matrix[4] * matrix[6]);
    Near(determinant, 1.f, "orientation reflects the scene");

    // Freeze on pause / bad time; cap a hitch instead of snapping to the limit.
    const State saved = state;
    const float nan = std::numeric_limits<float>::quiet_NaN();
    const float inf = std::numeric_limits<float>::infinity();
    for (float dt : {0.f, -1.f, nan, inf})
    {
        state.Step(-1.f, 1.f, 40.f, 25.f, dt);
        Near(state.pitch, saved.pitch, "invalid dt changed pitch");
        Near(state.yaw, saved.yaw, "invalid dt changed yaw");
    }
    State hitch, quarter;
    hitch.Step(1.f, -1.f, 40.f, 25.f, 10.f);
    quarter.Step(1.f, -1.f, 40.f, 25.f, .25f);
    Near(hitch.pitch, quarter.pitch, "hitch cap pitch");
    Near(hitch.yaw, quarter.yaw, "hitch cap yaw");

    state.Step(1.f, 1.f, 0.f, 0.f, 0.f);
    Require(state.pitch == 0 && state.yaw == 0, "zero limits do not disable motion");
    state.Step(inf, nan, 40.f, 25.f, .1f);
    Require(state.pitch == 0 && state.yaw == 0, "invalid control propagates");
    state.Step(.02f, -.02f, 40.f, 25.f, .1f);
    Require(state.pitch == 0 && state.yaw == 0, "jitter inside dead zone");
    state.Step(100.f, -100.f, 1000.f, 1000.f, .25f);
    Require(state.pitch <= 1.570797f && state.yaw >= -1.570797f, "extreme values exceed limits");
    state.Step(1.f, 1.f, nan, -5.f, .1f);
    Require(state.pitch == 0 && state.yaw == 0, "invalid configuration propagates");
    state = first;
    state.Reset();
    state.WriteOrientation(matrix);
    for (int i = 0; i < 9; ++i)
        Near(matrix[i], i % 4 == 0 ? 1.f : 0.f, "reset does not restore forward view");

    std::puts("Cockpit head motion: FPS, reversal, return, limits, axes, rotation and reset checks passed.");
}
