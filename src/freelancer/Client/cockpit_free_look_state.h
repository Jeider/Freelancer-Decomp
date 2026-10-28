#pragma once
#include "cockpit_head_motion.h"

// No engine dependencies: the camera owns the actual angles; mouse input owns
// only these targets. All motion uses the existing per-cockpit head_turn limits.
namespace CockpitFreeLook
{
    struct State
    {
        bool enabled = false;
        bool dragging = false;
        bool waitingForRelease = false;
        bool returning = false;
        float targetPitch = 0.f;
        float targetYaw = 0.f;
        float currentPitch = 0.f;
        float currentYaw = 0.f;

        void Enable(bool value)
        {
            enabled = value;
            waitingForRelease = true; // The activating click never starts a drag.
            Release();
            // Ordinary look-ahead already smooths from the current angles.
            // Do not suppress it for the entire exponential return (~10 s).
            if (!enabled) returning = false;
        }
        void Release()
        {
            dragging = false;
            returning = true;
            targetPitch = targetYaw = 0.f;
        }
        bool Begin()
        {
            if (!enabled || waitingForRelease) return false;
            dragging = true;
            returning = false;
            targetPitch = currentPitch;
            targetYaw = currentYaw;
            return true;
        }
        void Move(float dx, float dy, float width, bool inverse,
                  float horizontalDegrees, float verticalDegrees)
        {
            if (!dragging || !std::isfinite(width) || width <= 0.f ||
                !std::isfinite(dx) || !std::isfinite(dy)) return;
            // Input deltas already contain the user's mouse-speed gain and the
            // surface-width scale. Do not multiply displacement by frame time.
            const float sensitivity = 120.f * CockpitHeadMotion::DegreesToRadians / width;
            const float yawLimit = CockpitHeadMotion::LimitDegrees(horizontalDegrees) * CockpitHeadMotion::DegreesToRadians;
            const float pitchLimit = CockpitHeadMotion::LimitDegrees(verticalDegrees) * CockpitHeadMotion::DegreesToRadians;
            targetYaw = (std::max)(-yawLimit, (std::min)(yawLimit, targetYaw - dx * sensitivity));
            targetPitch = (std::max)(-pitchLimit, (std::min)(pitchLimit,
                targetPitch + (inverse ? dy : -dy) * sensitivity));
        }
        bool Step(CockpitHeadMotion::State& head, float horizontalDegrees, float verticalDegrees, float dt)
        {
            currentPitch = head.pitch;
            currentYaw = head.yaw;
            if (!enabled && !returning) return false;
            head.StepAngles(dragging ? targetPitch : 0.f, dragging ? targetYaw : 0.f,
                            horizontalDegrees, verticalDegrees, dt);
            currentPitch = head.pitch;
            currentYaw = head.yaw;
            if (!dragging && head.pitch == 0.f && head.yaw == 0.f) returning = false;
            return true;
        }
    };
}
