#pragma once

#include <algorithm>
#include <cmath>

// Port-only cockpit look-ahead. Angles follow the ship's local torque axes:
// positive pitch looks up, positive yaw looks left (the camera looks along -Z).
namespace CockpitHeadMotion
{
    constexpr float DegreesToRadians = 0.01745329252f;
    constexpr float TurnResponse = .64f;
    constexpr float ReturnResponse = .96f;
    constexpr float MaxTurnRate = 45.f * DegreesToRadians;
    constexpr float MaxReturnRate = 30.f * DegreesToRadians;

    struct ManualControl
    {
        float pitch;
        float yaw;
    };

    inline ManualControl FromManualInput(float horizontal, float vertical)
    {
        // Screen-normalized player intent, without the ship's steering sensitivity
        // gain. Otherwise a small mouse deflection can demand the full head angle.
        // Input is right/down; torque axes are pitch-up/yaw-left. Roll is ignored.
        const auto axis = [](float value) {
            if (!std::isfinite(value)) return 0.f;
            return (std::max)(-1.f, (std::min)(1.f, -value));
        };
        return {axis(vertical), axis(horizontal)};
    }

    inline float LimitDegrees(double value)
    {
        if (!std::isfinite(value)) return 0.f;
        return static_cast<float>((std::max)(0.0, (std::min)(90.0, value)));
    }

    inline float SteeringAxis(float value)
    {
        if (!std::isfinite(value)) return 0.f;
        const float magnitude = (std::min)(1.f, std::fabs(value));
        constexpr float deadZone = .025f;
        if (magnitude <= deadZone) return 0.f;
        return std::copysign((magnitude - deadZone) / (1.f - deadZone), value);
    }

    struct State
    {
        float pitch = 0.f;
        float yaw = 0.f;

        void Reset() { pitch = yaw = 0.f; }

        void Step(float pitchControl, float yawControl, float horizontalDegrees,
                  float verticalDegrees, float dt)
        {
            const float pitchLimit = LimitDegrees(verticalDegrees) * DegreesToRadians;
            const float yawLimit = LimitDegrees(horizontalDegrees) * DegreesToRadians;
            // A disabled axis takes effect immediately, including while paused.
            pitch = (std::max)(-pitchLimit, (std::min)(pitchLimit, pitch));
            yaw = (std::max)(-yawLimit, (std::min)(yawLimit, yaw));
            if (!std::isfinite(dt) || dt <= 0.f) return;
            dt = (std::min)(dt, .25f);
            const float targetPitch = SteeringAxis(pitchControl) * pitchLimit;
            const float targetYaw = SteeringAxis(yawControl) * yawLimit;
            // Exponential response has the same time constant at different FPS.
            Follow(pitch, targetPitch, dt);
            Follow(yaw, targetYaw, dt);
        }

        void WriteOrientation(float* out) const
        {
            // R_yaw * R_pitch: rotate about the eye, with no added translation/roll.
            const float cp = std::cos(pitch), sp = std::sin(pitch);
            const float cy = std::cos(yaw), sy = std::sin(yaw);
            out[0] = cy;  out[1] = sy * sp; out[2] = sy * cp;
            out[3] = 0;   out[4] = cp;      out[5] = -sp;
            out[6] = -sy; out[7] = cy * sp; out[8] = cy * cp;
        }

    private:
        static void Follow(float& angle, float target, float dt)
        {
            const double response = target == 0.f ? ReturnResponse : TurnResponse;
            const double maxRate = target == 0.f ? MaxReturnRate : MaxTurnRate;
            const double error = static_cast<double>(target) - angle;
            const double distance = std::fabs(error);
            // Exact integration of a rate-limited exponential, including a switch
            // from constant speed to exponential settling within one frame.
            // Merely clamping an exponential step makes that switch FPS-dependent.
            const double exponentialDistance = maxRate * response;
            const double linearTime = (std::max)(0.0, (distance - exponentialDistance) / maxRate);
            const double usedTime = (std::min)(static_cast<double>(dt), linearTime);
            double movement = maxRate * usedTime;
            movement += (distance - movement) * (1.0 - std::exp(-(dt - usedTime) / response));
            angle = static_cast<float>(angle + std::copysign(movement, error));
            if (target == 0.f && std::fabs(angle) < .00001f) angle = 0.f;
        }
    };
}
