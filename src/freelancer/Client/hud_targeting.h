// Port-only [Targeting] panel: the native target details beside the contact list.
#pragma once
#include "hud_target.h"
#include "nn_montage_draw.h"
#include "targeting_window_state.h"

class NnTextControl;
bool TargetingOwnsContent(HudTarget const* source);
bool TargetingHostProperty(HudTarget const* source, int msg, uintptr_t a, uintptr_t b);
void TargetingUpdateHostButtons(HudTarget const* source);

class HUD_Targeting final : public HUDItem, public WinControl, public ButtonMover, public ButtonScaler
{
public:
    explicit HUD_Targeting(INI_Reader& reader);
    ~HUD_Targeting() override;
    void Destroy() override;
    bool Init() override;
    void Update() override;
    void Draw() override;
    bool HitTest(float const* ray) override;
    bool MouseEvent(FWin3DMouseEvent const* event) override;
    intptr_t SetProperty(int msg, uintptr_t a, uintptr_t b) override;
    bool OwnsContent(HudTarget const* source) const;
    void OnMoveFinished() override;
    void OnScaleFinished() override;
    bool HostProperty(int msg, uintptr_t a, uintptr_t b);
    void UpdateHostButtons();

private:
    static constexpr int ProjectionCount = 4;
    bool BindContent();
    bool CanShow() const;
    HudTarget* Source() const;
    void UpdateButtons();
    void ReleaseContent();
    void TogglePanel();
    void ReconcileVisibility();
    FVector IconHome() const;
    bool IsAnimating() const { return motion != Motion::None; }
    void NormalizeIcon(WinControl* control, int index);
    enum class Motion { None, ClosingScale, ClosingSlide, OpeningSlide, OpeningScale };
    Motion motion = Motion::None;
    struct IconSize
    {
        WinControl* control = nullptr;
        FButtonMontageTile* originalTile = nullptr;
        FButtonMontageTile tile = {};
        float orientation[9], half[3];
    } iconSizes[ProjectionCount + 3];
    struct LabelPlacement
    {
        NnTextControl* label = nullptr;
        float offset[3], home[3], attach[3], width;
        int alignment = 0;
        bool pickable = false;
    } labels[3];
    struct ButtonPlacement
    {
        WinControl* button = nullptr;
        float offset[3], attach[3];
    } subtargetButtons[2];
    WinControl* projections[ProjectionCount] = {};
    WinControl* autoselectButton = nullptr;
    WinControl* closeButton = nullptr;
    WinControl* openButton = nullptr;
    WinControl* windowButton = nullptr;
    WinControl* lockButton = nullptr;
    TargetingWindowState windowState;
    unsigned savedStateRevision = ~0u;
    TargetingProjection projection = TargetingProjection::Vanilla;
    HudTarget* owner = nullptr;
    WinControl* background = nullptr;
    FVector center = {-0.152f, -0.300f, -1.0f};
    FVector viewCenter = {};
    bool enabled = true;
    bool collapsed = true;
};
