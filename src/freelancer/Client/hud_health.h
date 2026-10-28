#pragma once
#include "hud_target.h"
#include "nn_montage_draw.h"
#include "health_window_state.h"

class HUD_Status;
bool HealthOwnsShipView(HUD_Status const* source);
bool HealthHostProperty(HUD_Status const* source, int msg, uintptr_t a, uintptr_t b);
void HealthUpdateHostButtons(HUD_Status const* source);
void HealthNotifyDamageMessage(unsigned messageId);

// Independent player damage view; HUD_Status retains the weapons and consumables.
class HUD_Health final : public HudTargetBase, public ButtonScaler
{
public:
    explicit HUD_Health(INI_Reader& reader);
    ~HUD_Health() override;
    bool Init() override;
    void Destroy() override;
    void SetTarget(IObjRW* target) override;
    void Update() override;
    void Draw() override;
    bool HitTest(float const* ray) override;
    bool MouseEvent(FWin3DMouseEvent const* event) override;
    intptr_t SetProperty(int msg, uintptr_t a, uintptr_t b) override;
    void OnMoveFinished() override;
    void OnScaleFinished() override;
    bool OnEvent(unsigned) override { return false; }
    bool Owns(HUD_Status const* source) const;
    bool HostProperty(int msg, uintptr_t a, uintptr_t b);
    void UpdateHostButtons();
    void NotifyDamage();
private:
    HUD_Status* Source() const;
    bool BindHost();
    bool CanShow(bool hostControls = false) const;
    void ReleaseHost();
    void TogglePanel();
    void SyncPanel();
    void ObserveDamage();
    void RestoreSavedState();
    void DrawShip();
    void UpdateVisibility();
    FVector IconHome() const;
    void NormalizeIcon(WinControl* control, int index, float radius);
    enum class Motion { None, OpeningSlide, OpeningScale, ClosingScale, ClosingSlide };
    Motion motion = Motion::None;
    bool IsAnimating() const { return motion != Motion::None; }
    HUD_Status* owner = nullptr;
    WinControl* hostButton = nullptr;
    WinControl* lockButton = nullptr;
    WinControl* slideIcon = nullptr;
    WinControl* toolbar[5] = {};
    bool viewLeft = false;
    FButtonMontageTile tiles[11] = {};
    FButtonMontageTile* originalTiles[11] = {};
    WinControl* normalized[11] = {};
    HealthWindowState windowState;
    HealthDamageState damageState;
    unsigned savedStateRevision = ~0u;
    float savedConsumableOffsets[4][3] = {};
    FVector center = {0.152f, -0.300f, -1.0f};
    bool enabled = true;
    bool open = false;
};
