#include "hud_interface_ids.h"
#include "hud_targeting.h"

#include "common_ini.h"
#include "common_misc.h"
#include "game_options.h"
#include "hud_status_core.h"
#include "hud_vulnerable.h"
#include "input_manager.h"
#include "nn_modal.h"
#include "nn_button_control.h"
#include "nn_tooltip.h"
#include "nn_text_control.h"
#include "player_behavior.h"
#include "space_letterbox.h"
#include "win3d_immediate.h"
#include "dacom.h"
#include "DALib.h"
#include "engine/engbase.h"

#include <algorithm>
#include <cmath>
#include <cstring>

namespace
{
    HUDFACTORY<HUD_Targeting> TargetingFactory("Targeting");
    HUD_Targeting* ActivePanel = nullptr;
    constexpr float PanelHalfWidth = 0.0923861f;
    constexpr float ViewHalfWidth = PanelHalfWidth - 0.008f;
    constexpr float ButtonStep = 0.026f;
    constexpr float ButtonLeft = -2.0f * ButtonStep;
    constexpr float ButtonY = -0.070f;
    constexpr float IconRadius = 0.016f;
    constexpr float ViewTop = 0.073f;
    constexpr float ViewBottom = ButtonY + IconRadius + 0.004f;
    constexpr float ViewHalfHeight = (ViewTop - ViewBottom) * 0.5f;
    constexpr float AnimSeconds = 0.3f; // HUD_Target: scale, then slide (reverse when opening).

    float PositionValue(float value, float limit, float fallback)
    {
        return std::isfinite(value) ? (std::max)(-limit, (std::min)(limit, value)) : fallback;
    }
}

bool TargetingOwnsContent(HudTarget const* source)
{
    return ActivePanel && ActivePanel->OwnsContent(source);
}

bool TargetingHostProperty(HudTarget const* source, int msg, uintptr_t a, uintptr_t b)
{
    return TargetingOwnsContent(source) && ActivePanel->HostProperty(msg, a, b);
}

void TargetingUpdateHostButtons(HudTarget const* source)
{
    if (TargetingOwnsContent(source)) ActivePanel->UpdateHostButtons();
}

HUD_Targeting::HUD_Targeting(INI_Reader& reader)
{
    HUDItem::Name = "Targeting";
    Win3D::SetName("HUD_Targeting");
    ClassName = "HUD_Targeting";
    while (reader.read_value())
    {
        if (reader.is_value("enabled")) enabled = reader.get_value_bool(0);
        else if (reader.is_value("position"))
        {
            center.X = PositionValue(static_cast<float>(reader.get_value_float(0)), 0.39f, -0.152f);
            center.Y = PositionValue(static_cast<float>(reader.get_value_float(1)), 0.30f, -0.300f);
        }
    }
    viewCenter = {center.X, center.Y + (ViewTop + ViewBottom) * 0.5f, -1.0f};
}

HUD_Targeting::~HUD_Targeting()
{
    ReleaseContent();
}

void HUD_Targeting::Destroy()
{
    // Win3D can destroy children before invoking our destructor.
    ReleaseContent();
    WinControl::Destroy();
}

void HUD_Targeting::ReleaseContent()
{
    ButtonMover::bActive = ButtonScaler::bActive = false;
    ButtonMover::Entries.clear();
    ButtonScaler::Entries.clear();
    for (auto& saved : iconSizes)
    {
        if (!saved.control) continue;
        static_cast<NnButtonControl*>(saved.control)->MontageTile = saved.originalTile;
        saved.control->SetOrientation(saved.orientation);
        std::memcpy(saved.control->HalfExtents, saved.half, sizeof(saved.half));
        saved.control = nullptr;
    }
    if (ActivePanel == this)
    {
        ActivePanel = nullptr;
        VulnerableTargetingReset();
    }
    // Either HUD can be destroyed first. Return the labels only while their
    // controller is alive; otherwise WinControl owns and destroys them here.
    if (HudTarget* source = Source())
    {
        if (windowButton) { windowButton->Destroy(); delete windowButton; }
        if (lockButton) { lockButton->Destroy(); delete lockButton; }
        for (auto& saved : labels)
        {
            Win3DReparent(saved.label, source);
            std::memcpy(saved.label->Offset, saved.offset, sizeof(saved.offset));
            std::memcpy(saved.label->HomeOffset, saved.home, sizeof(saved.home));
            std::memcpy(saved.label->AttachPosition, saved.attach, sizeof(saved.attach));
            saved.label->SetWidth(saved.width);
            saved.label->Dword358 = saved.alignment;
            saved.label->SetPosition(source->Position);
            saved.label->SetCachedDraw(0, 1);
            if (saved.pickable) saved.label->Flags |= kWin3DPickable;
        }
        for (auto& saved : subtargetButtons)
        {
            Win3DReparent(saved.button, source);
            std::memcpy(saved.button->Offset, saved.offset, sizeof(saved.offset));
            std::memcpy(saved.button->AttachPosition, saved.attach, sizeof(saved.attach));
            saved.button->SetPosition(source->Position);
        }
    }
    windowButton = lockButton = nullptr;
    owner = nullptr;
}

HudTarget* HUD_Targeting::Source() const
{
    return owner && G_HudTargetPanel == owner ? owner : nullptr;
}

bool HUD_Targeting::OwnsContent(HudTarget const* source) const
{
    return source && Source() == source;
}

void HUD_Targeting::NormalizeIcon(WinControl* control, int index)
{
    auto* button = static_cast<NnButtonControl*>(control);
    auto& saved = iconSizes[index];
    saved.control = control;
    saved.originalTile = button->MontageTile;
    std::memcpy(saved.orientation, control->Orientation, sizeof(saved.orientation));
    std::memcpy(saved.half, control->HalfExtents, sizeof(saved.half));
    float const targetRadius = index == ProjectionCount + 2 ? 0.014f : IconRadius;
    control->HalfExtents[0] = control->HalfExtents[1] = targetRadius;
    // Keep adjacent toolbar hit boxes separate without shrinking the artwork.
    if (index < ProjectionCount + 2) control->HalfExtents[0] = ButtonStep * 0.5f;
    control->HalfExtents[2] = 0.0f;
    // A private tile copy keeps the size of other HUD buttons unchanged.
    if (button->MontageTile)
    {
        saved.tile = *button->MontageTile;
        saved.tile.Scale = targetRadius;
        button->MontageTile = &saved.tile;
    }
    // Custom 3DBs need the same normalization when no montage tile is present.
    if (ClientMeshHolderHasInstance(&control->MeshHolder))
    {
        float radius = 0.0f, unusedCenter[3] = {};
        DALib::Engine->GetInstanceExtent(control->MeshHolder.EngineInstance, 1, &radius, unusedCenter);
        if (std::isfinite(radius) && radius > 0.0f)
        {
            float rotation[9];
            for (int i = 0; i < 9; ++i) rotation[i] = saved.orientation[i] * targetRadius / radius;
            control->SetOrientation(rotation);
        }
    }
}

FVector HUD_Targeting::IconHome() const
{
    return windowButton && Source() ? FVector{windowButton->Offset[0], windowButton->Offset[1], 0}
                                   : FVector{center.X, center.Y, 0};
}

void HUD_Targeting::ReconcileVisibility()
{
    HudTarget* source = Source();
    // Restore once per loaded player, even if the HUD itself survives loading.
    unsigned const revision = GetGameSessionLoadRevision();
    if (savedStateRevision != revision)
    {
        savedStateRevision = revision;
        windowState.Restore(GetSavedTargetingWindowOpen(), GetSavedTargetingWindowLocked());
    }
    windowState.SetLocked(GetSavedTargetingWindowLocked());
    windowState.Observe(source ? source->TargetingObjectId() : 0,
                        source && source->TargetingIsHostileShip());
    // Losing the target hides the panel temporarily; keep its saved preference.
    if (windowState.targetId && !windowState.restorePending && !IsSpaceInitInProgress())
        SetSavedTargetingWindowOpen(windowState.open);
    if (CanShow() && !IsAnimating() && collapsed == windowState.open) TogglePanel();
}

void HUD_Targeting::TogglePanel()
{
    if (IsAnimating()) return;
    if (HudTarget* source = Source()) source->SubTargetId = SUBOBJ_ID_NONE;
    NnToolTipHideGlobal();
    if (collapsed)
    {
        motion = Motion::OpeningSlide;
        FVector const home = IconHome();
        float const middle[] = {center.X, center.Y, 0.0f};
        ButtonMover::Start(AnimSeconds);
        ButtonMover::AddButton(openButton, &home.X, middle);
    }
    else
    {
        motion = Motion::ClosingScale;
        ButtonScaler::Start(AnimSeconds);
        ButtonScaler::AddButton(background, 1.0f, 0.1f);
    }
    UpdateButtons();
}

void HUD_Targeting::OnScaleFinished()
{
    if (motion == Motion::ClosingScale)
    {
        motion = Motion::ClosingSlide;
        float const middle[] = {center.X, center.Y, 0.0f};
        FVector const home = IconHome();
        openButton->SetOffset(middle[0], middle[1], middle[2]);
        ButtonMover::Start(AnimSeconds);
        ButtonMover::AddButton(openButton, middle, &home.X);
    }
    else if (motion == Motion::OpeningScale)
    {
        collapsed = false;
        motion = Motion::None;
    }
}

void HUD_Targeting::OnMoveFinished()
{
    if (motion == Motion::OpeningSlide)
    {
        motion = Motion::OpeningScale;
        ButtonScaler::Start(AnimSeconds);
        ButtonScaler::AddButton(background, 0.1f, 1.0f);
    }
    else if (motion == Motion::ClosingSlide)
    {
        collapsed = true;
        motion = Motion::None;
    }
}

bool HUD_Targeting::Init()
{
    if (!enabled || ActivePanel) return false;
    float const zero[3] = {};
    background = CreateStaticControl("TargetingBackground", "Interface\\hud\\hud_target2.cmp",
                                      &center.X, nullptr, zero, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, zero);
    if (!background || !ClientMeshHolderHasInstance(&background->MeshHolder))
    {
        FDUMP(0x100002, "HUD_TARGETING: cannot load Interface\\hud\\hud_target2.cmp\n");
        return false;
    }
    float const half[] = {IconRadius, IconRadius, 0.0f};
    float const autoPos[] = {center.X + ButtonLeft, center.Y + ButtonY, 0.0f};
    autoselectButton = CreateButtonControl("TargetingAutoselect", "interface\\hud\\HUD_nextsub.3db",
        nullptr, "ui_item_select", nullptr, autoPos, nullptr, half, 0, 1, 0, 0, HudIds::AutoselectEnable, 0, 0);
    if (!autoselectButton) return false;
    NormalizeIcon(autoselectButton, 0);
    char const* const names[] = {"TargetingVanilla", "TargetingFit", "TargetingTop", "TargetingSide"};
    char const* const meshes[] = {"interface\\hud\\HUD_target_view1.3db",
        "interface\\hud\\HUD_target_view2.3db", "interface\\hud\\HUD_target_view3.3db",
        "interface\\hud\\HUD_target_view4.3db"};
    char const* const fallbackMeshes[] = {"interface\\hud\\hud_shiptarget.3db",
        "interface\\hud\\hud_targetedobject.3db", "interface\\hud\\hud_playershipinfo.3db",
        "interface\\hud\\hud_formation.3db"};
    for (int i = 0; i < ProjectionCount; ++i)
    {
        float const pos[] = {center.X + ButtonLeft + (i + 1) * ButtonStep, center.Y + ButtonY, 0.0f};
        projections[i] = CreateButtonControl(names[i], meshes[i], nullptr, "ui_item_select",
            nullptr, pos, nullptr, half, 0, 1, 0, 0, HudIds::TargetVanilla + i, 0, 0);
        if (!projections[i]) return false;
        auto* button = static_cast<NnButtonControl*>(projections[i]);
        if (!ClientMeshHolderHasInstance(&button->MeshHolder) &&
            (!button->MontageTile || !button->MontageTile->Shape))
        {
            button->SetMesh(fallbackMeshes[i], 0);
            button->MontageTile = FindButtonMontageTile(fallbackMeshes[i]);
        }
        NormalizeIcon(button, i + 2);
    }
    float const openPos[] = {center.X, center.Y - 0.067f, 0.0f};
    float const slideHalf[] = {0.014f, 0.014f, 0.0f};
    openButton = CreateButtonControl("TargetingOpen", "interface\\hud\\hud_targetedobject.3db",
        nullptr, "ui_window_open", nullptr, openPos, nullptr, slideHalf, 0, 1, 0, 0, HudIds::TargetWindow, 0, 0);
    if (!openButton) return false;
    NormalizeIcon(openButton, ProjectionCount + 2);
    SetOffset(0.0f, 0.0f, -1.0f);
    SetPosition(Position);
    background->Flags &= ~kWin3DPickable;
    if (!Win3D::Create(nullptr, nullptr)) return false;
    ActivePanel = this;
    BindContent();
    UpdateButtons();
    FDUMP(0x100002, "HUD_TARGETING Init position=%.3f,%.3f hud='%s'\n",
          center.X, center.Y, GetHudIniPath());
    return true;
}

bool HUD_Targeting::BindContent()
{
    if (Source()) return true;
    if (owner || !G_HudTargetPanel) return false;
    HudTarget* source = static_cast<HudTarget*>(G_HudTargetPanel);
    WinControl* controls[] = {source->ShipName, source->SubtargetName, source->RankText};
    for (auto* control : controls) if (!control) return false;
    if (!source->PreviousButton || !source->NextButton) return false;
    float const rows[] = {center.Y + 0.079f, center.Y + 0.061f, center.Y + 0.079f};
    for (int i = 0; i < 3; ++i)
    {
        auto& saved = labels[i];
        saved.label = static_cast<NnTextControl*>(controls[i]);
        std::memcpy(saved.offset, saved.label->Offset, sizeof(saved.offset));
        std::memcpy(saved.home, saved.label->HomeOffset, sizeof(saved.home));
        std::memcpy(saved.attach, saved.label->AttachPosition, sizeof(saved.attach));
        saved.width = saved.label->Width;
        saved.alignment = saved.label->Dword358;
        saved.pickable = (saved.label->Flags & kWin3DPickable) != 0;
        saved.label->Flags &= ~kWin3DPickable;
        Win3DReparent(saved.label, this);
        float const offset[] = {center.X - PanelHalfWidth + 0.010f, rows[i], 0.0f};
        float const attach[] = {0.0f, 0.0f, -1.0f};
        std::memcpy(saved.label->Offset, offset, sizeof(offset));
        std::memcpy(saved.label->HomeOffset, offset, sizeof(offset));
        std::memcpy(saved.label->AttachPosition, attach, sizeof(attach));
        // Centre each line within a symmetric box across the panel.
        saved.label->SetWidth(2.0f * (PanelHalfWidth - 0.010f));
        saved.label->Dword358 = 1;
        saved.label->SetPosition(Position);
        saved.label->SetCachedDraw(0, 1);
    }
    WinControl* const arrows[] = {source->PreviousButton, source->NextButton};
    for (int i = 0; i < 2; ++i)
    {
        auto& saved = subtargetButtons[i];
        saved.button = arrows[i];
        std::memcpy(saved.offset, saved.button->Offset, sizeof(saved.offset));
        std::memcpy(saved.attach, saved.button->AttachPosition, sizeof(saved.attach));
        Win3DReparent(saved.button, this);
        saved.button->AttachPosition[0] = saved.button->AttachPosition[1] = 0.0f;
        saved.button->AttachPosition[2] = -1.0f;
        saved.button->SetProperty(1, 1, 0);
    }
    owner = source;
    float const zero[] = {0, 0, 0};
    float const half[] = {0.014f, 0.014f, 0};
    windowButton = source->CreateButtonControl("TargetingWindow", "interface\\hud\\HUD_targetedobject.3db",
        nullptr, "ui_item_select", nullptr, zero, nullptr, half, 0, 1, 0, 0, HudIds::TargetWindow, 0, 0);
    lockButton = source->CreateButtonControl("TargetingWindowLock", "interface\\hud\\HUD_target_window_lock.3db",
        nullptr, "ui_item_select", nullptr, zero, nullptr, half, 0, 1, 0, 0, HudIds::TargetLock, 0, 0);
    if (!windowButton || !lockButton) { ReleaseContent(); return false; }
    // Match the rendered ship icon, not the 0.014 input hit box. Montage scale
    // is the quad's circumscribed radius (draw width = scale * sqrt(2)).
    auto const* windowTile = static_cast<NnButtonControl*>(windowButton)->MontageTile;
    float iconRadius = windowTile ? windowTile->Scale : 0.022f;
    if (!std::isfinite(iconRadius) || iconRadius <= 0) iconRadius = 0.022f;
    if (ClientMeshHolderHasInstance(&lockButton->MeshHolder))
    {
        float radius = 0, unused[3] = {};
        DALib::Engine->GetInstanceExtent(lockButton->MeshHolder.EngineInstance, 1, &radius, unused);
        if (std::isfinite(radius) && radius > 0)
        {
            float rotation[9];
            for (int i = 0; i < 9; ++i) rotation[i] = lockButton->Orientation[i] * iconRadius / radius;
            lockButton->SetOrientation(rotation);
        }
    }
    UpdateHostButtons();
    source->LabelRefreshTimer = 1.0f;
    source->Slot15();
    FDUMP(0x100002, "HUD_TARGETING: native target labels and view attached\n");
    return true;
}

bool HUD_Targeting::CanShow() const
{
    return enabled && !AreAuxiliaryHudWindowsMinimized() && GetGameOption(kGameOptInterfaceGroup) && GetGameOption(kGameOptHud) &&
        !IsSpaceInitInProgress() && !G_bNnScreenUp && !IsLetterboxVisible() &&
        GetPlayerObjRW() && GetClientMouseCursorDrawFlag();
}

void HUD_Targeting::UpdateHostButtons()
{
    HudTarget* source = Source();
    if (!source || !windowButton || !lockButton) return;
    WinControl* anchor = source->ContactListButton;
    bool const moving = source->ButtonMover::IsActive() || source->ButtonScaler::IsActive();
    bool const visible = CanShow() && !moving;
    WinControl* buttons[] = {windowButton, lockButton};
    for (int i = 0; i < 2; ++i)
    {
        std::memcpy(buttons[i]->AttachPosition, anchor->AttachPosition, sizeof(anchor->AttachPosition));
        // SetOffset repositions from Parent->Position. NnButtonControl adds its
        // attach transform there; anchor->Position already includes that shift.
        buttons[i]->SetOffset(anchor->Offset[0] - i * 0.034f, anchor->Offset[1], anchor->Offset[2]);
        buttons[i]->SetProperty(1, visible ? 0 : 1, 0);
    }
    source->ContactListButton->SetProperty(1, 1, 0);
    source->TargetButton->SetProperty(1, 1, 0);
    if (source->bExpanded && !moving)
    {
        auto* scan = source->ScanButton;
        source->FormationButton->SetOffset(scan->Offset[0] + 0.029f, scan->Offset[1], scan->Offset[2]);
    }
    windowButton->SetProperty(0xc, windowState.open ? 1 : 0, 0);
    lockButton->SetProperty(3, windowState.locked ? HudIds::TargetUnlock : HudIds::TargetLock, 0);
    lockButton->SetProperty(0xc, windowState.locked ? 1 : 0, 0);
}

bool HUD_Targeting::HostProperty(int msg, uintptr_t a, uintptr_t /*b*/)
{
    WinControl* button = reinterpret_cast<WinControl*>(a);
    if (!button || (button != windowButton && button != lockButton) || !Source()) return false;
    if (msg == 0x26 && CanShow())
    {
        ReconcileVisibility();
        if (button == windowButton) windowState.ToggleOpen();
        else
        {
            windowState.ToggleLock();
            SetSavedTargetingWindowLocked(windowState.locked);
        }
        SetSavedTargetingWindowOpen(windowState.open);
        ReconcileVisibility();
        UpdateHostButtons();
        return true;
    }
    return false;
}

void HUD_Targeting::Update()
{
    BindContent();
    ReconcileVisibility();
    if (ButtonScaler::IsActive()) ButtonScaler::Update();
    else if (ButtonMover::IsActive()) ButtonMover::Update();
    ReconcileVisibility();
    UpdateButtons();
    if (HudTarget* source = Source())
    {
        if (CanShow() && windowState.targetId && !collapsed && !IsAnimating()) source->UpdateTargetingHover(viewCenter, ViewHalfWidth, ViewHalfHeight);
        else source->SubTargetId = SUBOBJ_ID_NONE;
    }
    Win3D::Update();
}

void HUD_Targeting::Draw()
{
    if (!CanShow()) return;
    if (ButtonScaler::IsActive())
    {
        background->Draw();
        return;
    }
    if (ButtonMover::IsActive())
    {
        openButton->Draw();
        return;
    }
    if (collapsed)
    {
        return;
    }
    background->Draw();
    if (HudTarget* source = Source())
    {
        source->DrawTargetingView(viewCenter, ViewHalfWidth, ViewHalfHeight, projection);
        // Keep the native labels attached for later placement, but devote the
        // panel to the wireframe even when the pointer is over a subsystem.
    }
    if (autoselectButton->Flags & kWin3DVisible) autoselectButton->Draw();
    for (auto* button : projections)
        if (button->Flags & kWin3DVisible) button->Draw();
}

bool HUD_Targeting::HitTest(float const* ray)
{
    if (collapsed || IsAnimating() || !windowState.targetId || !CanShow() || !Source() || !ray || !std::isfinite(ray[2]) || ray[2] >= 0.0f)
        return false;
    float const x = -ray[0] / ray[2], y = -ray[1] / ray[2];
    return std::fabs(x - viewCenter.X) <= ViewHalfWidth &&
           std::fabs(y - viewCenter.Y) <= ViewHalfHeight;
}

bool HUD_Targeting::MouseEvent(FWin3DMouseEvent const* event)
{
    HudTarget* source = Source();
    return !collapsed && !IsAnimating() && windowState.targetId && CanShow() && source && source->MouseEvent(event);
}

void HUD_Targeting::UpdateButtons()
{
    // Read session state even if the HUD already exists when another save loads.
    projection = static_cast<TargetingProjection>(GetSavedTargetingProjection());
    bool const visible = CanShow();
    bool const expanded = visible && windowState.targetId && !collapsed && !IsAnimating();
    HudTarget* const source = Source();
    bool const hasTarget = source && source->ViewObject.target();
    for (auto const& saved : subtargetButtons)
        if (saved.button) saved.button->SetProperty(1, 1, 0);
    autoselectButton->SetProperty(1, expanded && source && source->TargetingIsCruiser() ? 0 : 1, 0);
    autoselectButton->SetProperty(3, VulnerableAutoselectEnabled() ? HudIds::AutoselectDisable : HudIds::AutoselectEnable, 0);
    autoselectButton->SetProperty(0xc, VulnerableAutoselectEnabled() ? 1 : 0, 0);
    for (int i = 0; i < ProjectionCount; ++i)
    {
        projections[i]->SetProperty(1, expanded && hasTarget ? 0 : 1, 0);
        projections[i]->SetProperty(0xc, static_cast<int>(projection) == i ? 1 : 0, 0);
    }
    openButton->SetProperty(1, visible && ButtonMover::IsActive() ? 0 : 1, 0);
    openButton->Flags &= ~(kWin3DActive | kWin3DPickable);
    UpdateHostButtons();
}

intptr_t HUD_Targeting::SetProperty(int msg, uintptr_t a, uintptr_t b)
{
    if (msg == 0x26 && CanShow() && !IsAnimating())
    {
        if (!collapsed)
        {
            if (a == reinterpret_cast<uintptr_t>(autoselectButton) &&
                Source() && Source()->TargetingIsCruiser())
            {
                SetVulnerableAutoselect(!VulnerableAutoselectEnabled());
                UpdateButtons();
                return 1;
            }
            for (int i = 0; i < ProjectionCount; ++i)
                if (a == reinterpret_cast<uintptr_t>(projections[i]))
                {
                    SetSavedTargetingProjection(static_cast<unsigned>(i));
                    UpdateButtons();
                    return 1;
                }
        }
    }
    return WinControl::SetProperty(msg, a, b);
}
