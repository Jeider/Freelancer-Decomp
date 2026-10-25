// Port-only opt-in radar, registered as [StarlancerRadar] in the active hud.ini.
#pragma once
#include "hud_element_list.h"
#include "wincontrol_base.h"

class HUD_StarlancerRadar final : public HUDItem, public WinControl
{
public:
    explicit HUD_StarlancerRadar(INI_Reader& reader);
    bool Init() override;
    void Draw() override;

private:
    bool enabled = false;
    bool showSolars = true;
    float centerX = 0.84f;
    float centerY = 0.72f;
    float radius = 0.095f;
    float ellipse = 0.42f;
    float elevation = 0.65f;
    float opacity = 0.8f;
    float ranges[3] = {0.25f, 0.5f, 1.0f};
    int rangeIndex = 2;
    int maxContacts = 96;
    unsigned reportedReasons = 0;
    bool reportedDraw = false;
    void ReportOnce(unsigned bit, char const* reason);
};
