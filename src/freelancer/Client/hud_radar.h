// Port-only opt-in radar, registered as [Radar] in the active hud.ini.
#pragma once
#include "hud_element_list.h"
#include "wincontrol_base.h"
#include "radar_motion.h"

class HUD_Radar final : public HUDItem, public WinControl
{
public:
    explicit HUD_Radar(INI_Reader& reader);
    ~HUD_Radar() override;
    bool MessageAnchor(float& x, float& y) const;
    bool Init() override;
    void Update() override;
    void Draw() override;
    intptr_t SetProperty(int msg, uintptr_t a, uintptr_t b) override;

private:
    bool enabled = false;
    bool showSolars = true;
    float centerX = 0.50f;
    float centerY = 0.845f;
    float radius = 0.30f;
    float ellipse = 0.32f;
    float elevation = 0.94f;
    float sweepSpeed = 45.0f; // Scanner light, independent of ship-driven rim.
    float sweepAngle = 0.0f;
    RadarMotion::State ringMotion;
    WinControl* zoomButtons[2] = {};
    WinControl* toggleButton = nullptr;
    WinControl* background = nullptr;
    unsigned lastSystem = 0;
    bool wasInLane = false;
    bool CanShow() const;
    void UpdateButtons();
    float opacity = 0.8f;
    float ranges[3] = {0.25f, 0.5f, 1.0f};
    int rangeIndex = 2;
    unsigned defaultRangeIndex = 2;
    int maxContacts = 96;
    unsigned reportedReasons = 0;
    bool reportedDraw = false;
    void ReportOnce(unsigned bit, char const* reason);
};

// Centre above the disk, in native HUD coordinates; false without a Radar item.
bool RadarMessageAnchor(float& x, float& y);
