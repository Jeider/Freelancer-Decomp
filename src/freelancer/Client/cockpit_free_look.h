#pragma once

class HUD_Maneuvers;
struct FMouseEvent;
namespace CockpitHeadMotion { struct State; }

namespace CockpitFreeLook
{
    bool Enabled();
    bool BlocksMouseFlight();
    bool HidesCursor();
    void Toggle();
    void Reset();
    void Suspend();
    bool MouseFrame(bool read, int dx, int dy);
    bool ConsumeMouseEvent(FMouseEvent const& event);
    bool UpdateHead(CockpitHeadMotion::State& head, float dt);
    void UpdateHud(HUD_Maneuvers* host);
    bool HitTestHud(HUD_Maneuvers const* host, float const* ray);
    void ReleaseHud(HUD_Maneuvers const* host);
}
