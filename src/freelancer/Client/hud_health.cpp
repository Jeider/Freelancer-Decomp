#include "hud_interface_ids.h"
#include "hud_health.h"
#include "player_turret_hud.h"
#include "hud_status_core.h"
#include "hud_weapon_groups.h"
#include "wing_anim.h"
#include "common_ini.h"
#include "common_cobject.h"
#include "common_cequip.h"
#include "common_archetype.h"
#include "common_id.h"
#include "common_csys.h"
#include "common_iface.h"
#include "common_misc.h"
#include "game_options.h"
#include "input_manager.h"
#include "nn_button_control.h"
#include "nn_modal.h"
#include "nn_tooltip.h"
#include "player_behavior.h"
#include "space_letterbox.h"
#include "win3d_immediate.h"
#include "win3d_render.h"
#include "DALib.h"
#include "engine/engbase.h"
#include <algorithm>
#include <cmath>
#include <cstring>

namespace
{
    HUDFACTORY<HUD_Health> HealthFactory("Health");
    HUD_Health* ActiveHealth = nullptr;
    constexpr float PanelHalfWidth = 0.0923861f;
    constexpr float AnimSeconds = 0.3f;
    constexpr char HealthMesh[] = "interface\\hud\\HUD_targetedobject.3db";


}

bool HealthIsDamageMessage(unsigned messageId)
{
    static unsigned const messages[] = {
        CreateID("hull_breach_imminent"), CreateID("engine_critical"),
        CreateID("weapon_expired"), CreateID("cargo_expired"),
        CreateID("thruster_destroyed"), CreateID("engine_destroyed"),
        CreateID("mine_dropper_destroyed"), CreateID("countermeasure_dropper_destroyed"),
        CreateID("gun_destroyed"), CreateID("launcher_destroyed"), CreateID("turret_destroyed"),
        CreateID("radiation_damage_detected")
    };
    for (unsigned id : messages) if (messageId == id) return true;
    return false;
}

bool HealthTracksEquipment(unsigned type)
{
    // Shield charge, failure and loss must never request the damage window.
    return (type & (EquipTypeShield | EquipTypeShieldGen)) == 0;
}

void HealthNotifyDamageMessage(unsigned messageId)
{
    if (ActiveHealth && GetPlayerObjRW() && HealthIsDamageMessage(messageId))
        ActiveHealth->NotifyDamage();
}

bool HealthOwnsShipView(HUD_Status const* source)
{
    return ActiveHealth && ActiveHealth->Owns(source);
}

bool HealthHostProperty(HUD_Status const* source, int msg, uintptr_t a, uintptr_t b)
{
    return HealthOwnsShipView(source) && ActiveHealth->HostProperty(msg, a, b);
}

void HealthUpdateHostButtons(HUD_Status const* source)
{
    if (HealthOwnsShipView(source)) ActiveHealth->UpdateHostButtons();
}

HUD_Health::HUD_Health(INI_Reader& reader)
{
    HUDItem::Name = "Health";
    Win3D::SetName("HUD_Health");
    ClassName = "HUD_Health";
    while (reader.read_value())
    {
        if (reader.is_value("enabled")) enabled = reader.get_value_bool(0);
        else if (reader.is_value("position"))
        {
            float const x = static_cast<float>(reader.get_value_float(0));
            float const y = static_cast<float>(reader.get_value_float(1));
            if (std::isfinite(x)) center.X = (std::max)(-0.39f, (std::min)(0.39f, x));
            if (std::isfinite(y)) center.Y = (std::max)(-0.30f, (std::min)(0.30f, y));
        }
    }
    // Fill the former gauge strip; reserve only the bottom for the next toolbar.
    HitCenter = center;
    HitCenter.Y += 0.0115f;
    HitHalfWidth = PanelHalfWidth - 0.008f;
    HitHalfHeight = 0.0615f;
    bExpanded = 0;
}

HUD_Health::~HUD_Health() { ReleaseHost(); }
void HUD_Health::Destroy() { ReleaseHost(); WinControl::Destroy(); }

HUD_Status* HUD_Health::Source() const { return owner && owner == GetHudStatus() ? owner : nullptr; }
bool HUD_Health::Owns(HUD_Status const* source) const { return source && Source() == source; }

void HUD_Health::ReleaseHost()
{
    PlayerTurretHud::Release(owner);
    ButtonMover::bActive = ButtonScaler::bActive = false;
    ButtonMover::Entries.clear();
    ButtonScaler::Entries.clear();
    if (ActiveHealth == this) ActiveHealth = nullptr;
    // The host may have been destroyed first; never dereference its old children.
    if (Source())
    {
        WinControl* consumables[] = {owner->RepairButton, owner->RepairCountText,
                                    owner->UseBatteryButton, owner->BatteryCountText};
        for (int i = 0; i < 4; ++i)
            consumables[i]->SetOffset(savedConsumableOffsets[i][0], savedConsumableOffsets[i][1], savedConsumableOffsets[i][2]);
        for (int i = 0; i < 11; ++i)
        {
            if (i >= 4 && i < 10) continue;
            if (!normalized[i]) continue;
            static_cast<NnButtonControl*>(normalized[i])->MontageTile = originalTiles[i];
            normalized[i]->Destroy();
            delete normalized[i];
        }
    }
    for (int i = 4; i < 10; ++i)
        if (normalized[i]) static_cast<NnButtonControl*>(normalized[i])->MontageTile = originalTiles[i];
    for (auto& control : normalized) control = nullptr;
    owner = nullptr;
    hostButton = nullptr;
    lockButton = nullptr;
    for (auto& group : groups) group = nullptr;
}

void HUD_Health::NormalizeIcon(WinControl* control, int index, float radius)
{
    auto* button = static_cast<NnButtonControl*>(control);
    normalized[index] = control;
    originalTiles[index] = button->MontageTile;
    if (button->MontageTile)
    {
        tiles[index] = *button->MontageTile;
        tiles[index].Scale = radius;
        button->MontageTile = &tiles[index];
    }
    if (ClientMeshHolderHasInstance(&control->MeshHolder))
    {
        float extent = 0, unused[3] = {};
        DALib::Engine->GetInstanceExtent(control->MeshHolder.EngineInstance, 1, &extent, unused);
        if (std::isfinite(extent) && extent > 0)
        {
            float orientation[9];
            for (int i = 0; i < 9; ++i) orientation[i] = control->Orientation[i] * radius / extent;
            control->SetOrientation(orientation);
        }
    }
}

bool HUD_Health::Init()
{
    if (!enabled || ActiveHealth) return false;
    float const zero[3] = {}, half[3] = {0.014f, 0.014f, 0};
    ViewPanel = CreateStaticControl("HealthBackground", "Interface\\hud\\hud_target2.cmp",
        &center.X, nullptr, zero, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, zero);
    if (!ViewPanel || !ClientMeshHolderHasInstance(&ViewPanel->MeshHolder)) return false;
    slideIcon = CreateButtonControl("HealthSlide", HealthMesh, nullptr, nullptr, nullptr,
        zero, nullptr, half, 0, 1, 0, 0, 0, 0, 0);
    if (!slideIcon) return false;
    NormalizeIcon(slideIcon, 4, 0.022f);
    char const* const names[] = {"HealthWingPlay", "HealthWingPause", "HealthWingLock", "HealthTop", "HealthLeft"};
    char const* const meshes[] = {"interface\\hud\\HUD_health_wing.3db",
        "interface\\hud\\HUD_health_pause.3db", "interface\\hud\\HUD_health_wing_lock.3db",
        "interface\\hud\\HUD_target_view1.3db", "interface\\hud\\HUD_target_view2.3db"};
    int const tips[] = {HudIds::WingPlay, HudIds::WingPause, HudIds::WingLock, HudIds::HealthTop, HudIds::HealthLeft};
    float const toolbarHalf[] = {0.013f, 0.016f, 0};
    for (int i = 0; i < 5; ++i)
    {
        float const pos[] = {center.X + (i - 2) * 0.026f, center.Y - 0.070f, 0};
        toolbar[i] = CreateButtonControl(names[i], meshes[i], nullptr, "ui_item_select", nullptr,
            pos, nullptr, toolbarHalf, 0, 1, 0, 0, tips[i], 0, 0);
        if (!toolbar[i]) return false;
        NormalizeIcon(toolbar[i], i + 5, i < 3 ? 0.008f : 0.016f);
    }
    ViewPanel->Flags &= ~kWin3DPickable;
    slideIcon->Flags &= ~(kWin3DPickable | kWin3DActive);
    SetOffset(0, 0, -1);
    SetPosition(Position);
    if (!Win3D::Create(nullptr, nullptr)) return false;
    RestoreSavedState();
    open = windowState.open;
    ActiveHealth = this;
    BindHost();
    UpdateVisibility();
    FDUMP(0x100002, "HUD_HEALTH Init position=%.3f,%.3f\n", center.X, center.Y);
    return true;
}

bool HUD_Health::BindHost()
{
    if (Source()) return true;
    if (owner || !GetHudStatus()) return false;
    owner = GetHudStatus();
    WinControl* consumables[] = {owner->RepairButton, owner->RepairCountText,
                                owner->UseBatteryButton, owner->BatteryCountText};
    for (int i = 0; i < 4; ++i)
        std::memcpy(savedConsumableOffsets[i], consumables[i]->Offset, sizeof(savedConsumableOffsets[i]));
    float const zero[3] = {}, half[3] = {0.012f, 0.014f, 0};
    hostButton = owner->CreateButtonControl("HealthWindow", HealthMesh, nullptr, "ui_item_select",
        nullptr, zero, nullptr, half, 0, 1, 0, 0, HudIds::HealthWindow, 0, 0);
    if (!hostButton) { ReleaseHost(); return false; }
    NormalizeIcon(hostButton, 0, 0.022f);
    lockButton = owner->CreateButtonControl("HealthWindowLock", "interface\\hud\\HUD_target_window_lock.3db",
        nullptr, "ui_item_select", nullptr, zero, nullptr, half, 0, 1, 0, 0, HudIds::HealthLock, 0, 0);
    if (!lockButton) { ReleaseHost(); return false; }
    NormalizeIcon(lockButton, 10, 0.022f);
    char const* meshes[] = {"interface\\hud\\HUD_weaponsgroup1.3db",
        "interface\\hud\\HUD_weaponsgroup2.3db", "interface\\hud\\HUD_weaponsgroup3.3db"};
    char const* names[] = {"HealthWeaponGroup1", "HealthWeaponGroup2", "HealthWeaponGroup3"};
    float const groupHalf[] = {0.012f, 0.012f, 0};
    for (int i = 0; i < 3; ++i)
    {
        // HudWeaponGroups.dll 0041A18C: native select commands 0x91, 0x92, 0x93.
        groups[i] = owner->CreateButtonControl(names[i], meshes[i], nullptr, "ui_item_select",
            nullptr, zero, nullptr, groupHalf, 0, 1, 0, 0, HudIds::WeaponGroup1 + i, 0, 0x91 + i);
        if (!groups[i]) { ReleaseHost(); return false; }
        NormalizeIcon(groups[i], i + 1, 0.017f);
    }
    UpdateHostButtons();
    return true;
}

bool HUD_Health::CanShow() const
{
    return enabled && !AreAuxiliaryHudWindowsMinimized() && GetGameOption(kGameOptInterfaceGroup) && GetGameOption(kGameOptHud) &&
        !IsSpaceInitInProgress() && !G_bNnScreenUp && !IsLetterboxVisible() &&
        GetPlayerObjRW() && GetClientMouseCursorDrawFlag();
}

void HUD_Health::UpdateHostButtons()
{
    auto* source = Source();
    if (!source || !hostButton || !lockButton) return;
    bool const moving = source->ButtonMover::IsActive() || source->ButtonScaler::IsActive();
    bool const visible = CanShow() && !moving;
    bool const expanded = source->bExpanded != 0;
    PlayerTurretHud::Update(source, source->RepairButton->AttachPosition, visible && expanded);
    hostButton->SetProperty(1, visible ? 0 : 1, 0);
    hostButton->SetProperty(0xc, windowState.open ? 1 : 0, 0);
    lockButton->SetProperty(1, visible ? 0 : 1, 0);
    lockButton->SetProperty(3, GetSavedHealthWindowLocked() ? HudIds::HealthUnlock : HudIds::HealthLock, 0);
    lockButton->SetProperty(0xc, GetSavedHealthWindowLocked() ? 1 : 0, 0);
    for (int i = 0; i < 3; ++i)
        if (groups[i])
        {
            groups[i]->SetProperty(1, visible && expanded ? 0 : 1, 0);
            groups[i]->SetProperty(0xc, G_WeaponGroups.GetCurrent() == i ? 1 : 0, 0);
        }
    if (moving) return;
    float const y = expanded ? -0.171f : -0.371f;
    float const healthX = expanded ? 0.292f : 0.338f;
    float const repairX = expanded ? 0.358f : 0.405f;
    float const batteryX = expanded ? 0.411f : 0.462f;
    // Copy attachment, then SetOffset once: Position already includes attachment.
    std::memcpy(hostButton->AttachPosition, source->RepairButton->AttachPosition, sizeof(hostButton->AttachPosition));
    hostButton->SetOffset(healthX, y, 0);
    std::memcpy(lockButton->AttachPosition, hostButton->AttachPosition, sizeof(hostButton->AttachPosition));
    lockButton->SetOffset(healthX + 0.034f, y, 0);
    source->RepairButton->SetOffset(repairX, y, 0);
    source->RepairCountText->SetOffset(repairX + 0.010f, y + 0.011f, 0);
    source->UseBatteryButton->SetOffset(batteryX, y, 0);
    source->BatteryCountText->SetOffset(batteryX + 0.010f, y + 0.011f, 0);
    for (int i = 0; i < 3; ++i)
        if (groups[i])
        {
            std::memcpy(groups[i]->AttachPosition, hostButton->AttachPosition, sizeof(hostButton->AttachPosition));
            // Beneath the close cross, just left of the native weapon numbers.
            groups[i]->SetOffset(0.255f, -0.247f - i * 0.024f, 0);
        }
}

bool HUD_Health::HostProperty(int msg, uintptr_t a, uintptr_t)
{
    auto* button = reinterpret_cast<WinControl*>(a);
    if (!Source() || !button || (button != hostButton && button != lockButton)) return false;
    if (msg == 0x26 && CanShow())
    {
        RestoreSavedState();
        if (button == hostButton) TogglePanel();
        else
        {
            windowState.SetLocked(!GetSavedHealthWindowLocked());
            SetSavedHealthWindowLocked(windowState.locked);
            SetSavedHealthWindowOpen(windowState.open);
            UpdateHostButtons();
        }
        return true;
    }
    return false;
}

void HUD_Health::SetTarget(IObjRW* target)
{
    auto const* previous = ViewObject.target();
    HUDItem::SetTarget(target);
    SetViewObject(target);
    if (previous != ViewObject.target()) damageState.Reset();
}

void HUD_Health::RestoreSavedState()
{
    unsigned const revision = GetGameSessionLoadRevision();
    if (savedStateRevision == revision) return;
    savedStateRevision = revision;
    windowState = {};
    windowState.SetLocked(GetSavedHealthWindowLocked());
    windowState.open = GetSavedHealthWindowOpen();
    viewLeft = GetSavedHealthViewLeft();
    damageState.Reset();
}

void HUD_Health::NotifyDamage()
{
    RestoreSavedState();
    windowState.SetLocked(GetSavedHealthWindowLocked());
    windowState.Damage();
    SetSavedHealthWindowOpen(windowState.open);
}

void HUD_Health::ObserveDamage()
{
    CObject* object = GetViewCObject();
    if (!object || (static_cast<unsigned>(object->ObjectClass) & 0x503u) != 0x503u)
    {
        damageState.Reset();
        return;
    }
    auto* ship = static_cast<CEqObj*>(object);
    damageState.Begin();
    damageState.Sample(0, ship->get_relative_health());
    CArchGrpTraverser groupsWalk;
    for (CArchGroup* group = ship->ArchGroups.Traverse(groupsWalk); group;
         group = ship->ArchGroups.Traverse(groupsWalk))
        damageState.Sample(0x10000u | group->GetID(), group->GetRelativeHealth(),
                           group->Arch && group->Arch->bVulnerable, group->State != 1);
    CEquipTraverser equipWalk(0x1fe0);
    for (CEquip* equip = ship->EquipManager.Traverse(equipWalk); equip;
         equip = ship->EquipManager.Traverse(equipWalk))
        if (HealthTracksEquipment(equip->GetType()))
            damageState.Sample(0x20000u | equip->GetID(), equip->GetRelativeHealth(), false, equip->IsDestroyed());
    if (damageState.Finish()) NotifyDamage();
}

FVector HUD_Health::IconHome() const
{
    return hostButton && Source() ? FVector{hostButton->Offset[0], hostButton->Offset[1], 0}
                                 : FVector{center.X, center.Y, 0};
}

void HUD_Health::TogglePanel()
{
    RestoreSavedState();
    windowState.ToggleOpen();
    SetSavedHealthWindowOpen(windowState.open);
    SyncPanel();
}

void HUD_Health::SyncPanel()
{
    if (IsAnimating() || windowState.open == open || !CanShow()) return;
    SubTargetId = SUBOBJ_ID_NONE;
    NnToolTipHideGlobal();
    if (!open)
    {
        motion = Motion::OpeningSlide;
        FVector const home = IconHome();
        float const middle[] = {center.X, center.Y, 0};
        slideIcon->SetOffset(home.X, home.Y, 0);
        ButtonMover::Start(AnimSeconds);
        ButtonMover::AddButton(slideIcon, &home.X, middle);
    }
    else
    {
        motion = Motion::ClosingScale;
        ButtonScaler::Start(AnimSeconds);
        ButtonScaler::AddButton(ViewPanel, 1, 0.1f);
    }
    UpdateVisibility();
}

void HUD_Health::OnScaleFinished()
{
    if (motion == Motion::ClosingScale)
    {
        motion = Motion::ClosingSlide;
        float const middle[] = {center.X, center.Y, 0};
        FVector const home = IconHome();
        slideIcon->SetOffset(middle[0], middle[1], 0);
        ButtonMover::Start(AnimSeconds);
        ButtonMover::AddButton(slideIcon, middle, &home.X);
    }
    else if (motion == Motion::OpeningScale)
    {
        open = true;
        windowState.Opened();
        motion = Motion::None;
    }
}

void HUD_Health::OnMoveFinished()
{
    if (motion == Motion::OpeningSlide)
    {
        motion = Motion::OpeningScale;
        ButtonScaler::Start(AnimSeconds);
        ButtonScaler::AddButton(ViewPanel, 0.1f, 1);
    }
    else if (motion == Motion::ClosingSlide) { open = false; motion = Motion::None; }
}

void HUD_Health::UpdateVisibility()
{
    bExpanded = CanShow() && open && !IsAnimating();
    slideIcon->SetProperty(1, CanShow() && ButtonMover::IsActive() ? 0 : 1, 0);
    slideIcon->Flags &= ~(kWin3DPickable | kWin3DActive);
    bool const wing = WingAnimAvailable();
    bool const paused = WingAnimPaused();
    toolbar[0]->SetProperty(3, paused ? HudIds::WingResume : HudIds::WingPlay, 0);
    toolbar[1]->SetProperty(3, paused ? HudIds::WingResume : HudIds::WingPause, 0);
    toolbar[2]->SetProperty(3, WingAnimCruiseLocked() ? HudIds::WingUnlock : HudIds::WingLock, 0);
    bool const selected[] = {wing && WingAnimDisplayState() == 2 && !paused, paused,
                             WingAnimCruiseLocked(), !viewLeft, viewLeft};
    for (int i = 0; i < 5; ++i)
    {
        toolbar[i]->SetProperty(1, bExpanded && ViewObject.target() ? 0 : 1, 0);
        toolbar[i]->SetProperty(0xc, selected[i] ? 1 : 0, 0);
        auto* button = static_cast<NnButtonControl*>(toolbar[i]);
        bool const usable = i >= 3 || (wing && (i != 1 || WingAnimCanPause()));
        button->SetFlags331(static_cast<unsigned char>((button->GetFlags331() & ~2u) | (usable ? 2u : 0u)));
    }
    UpdateHostButtons();
}

void HUD_Health::Update()
{
    BindHost();
    RestoreSavedState();
    SetTarget(static_cast<IObjRW*>(GetPlayerObjRW()));
    windowState.SetLocked(GetSavedHealthWindowLocked());
    ObserveDamage();
    if (ButtonScaler::IsActive()) ButtonScaler::Update();
    else if (ButtonMover::IsActive()) ButtonMover::Update();
    SyncPanel();
    UpdateVisibility();
    Win3D::Update();
    if (bExpanded) UpdateSubTargetToolTip();
    else SubTargetId = SUBOBJ_ID_NONE;
}

void HUD_Health::DrawShip()
{
    IObjRW* const view = ObjRwFromWatchable(const_cast<Watchable*>(ViewObject.target()));
    if (!view) return;
    int viewport[4];
    Win3DGetViewport(0xba2, viewport);
    SetupViewCamera(true, 0);
    if (viewLeft)
    {
        // Port side: the opposite camera to Targeting's starboard view.
        auto const& object = *reinterpret_cast<FTransform const*>(&view->get_transform());
        for (int row = 0; row < 3; ++row)
        {
            ViewCamera.World[row * 3] = object.Rotation.D[row][2];
            ViewCamera.World[row * 3 + 1] = object.Rotation.D[row][1];
            ViewCamera.World[row * 3 + 2] = -object.Rotation.D[row][0];
        }
        ViewCamera.bViewDirty = 1;
    }
    ColourViewParts();
    FitDetachedView(true);
    PartCacheDraw(&PartCache, AsCamera(&ViewCamera), reinterpret_cast<FTransform const*>(&view->get_transform()));
    Win3DApplyCamera(AsCamera(Win3DGetCamera()));
    Win3DSetViewportRect(viewport[0], viewport[1], viewport[2], viewport[3], __FILE__, __LINE__);
}

void HUD_Health::Draw()
{
    if (!CanShow()) return;
    if (ButtonScaler::IsActive()) { ViewPanel->Draw(); return; }
    if (ButtonMover::IsActive()) { slideIcon->Draw(); return; }
    if (!open) return;
    ViewPanel->Draw();
    DrawShip();
    for (auto* button : toolbar)
        if (button->Flags & kWin3DVisible) button->Draw();
}

bool HUD_Health::HitTest(float const* ray)
{
    if (!CanShow() || !open || IsAnimating() || !ViewObject.target() || !ray ||
        !std::isfinite(ray[2]) || ray[2] >= 0) return false;
    return std::fabs(-ray[0] / ray[2] - HitCenter.X) <= HitHalfWidth &&
           std::fabs(-ray[1] / ray[2] - HitCenter.Y) <= HitHalfHeight;
}

bool HUD_Health::MouseEvent(FWin3DMouseEvent const* event)
{
    if (!CanShow() || !open || IsAnimating() || !event) return false;
    if (event->Field0 == -1 && event->Field1 == 2 && SubTargetId != SUBOBJ_ID_NONE && Source())
    {
        NnToolTipHideGlobal();
        Source()->ToggleLauncher(SubTargetId);
    }
    return true;
}

intptr_t HUD_Health::SetProperty(int msg, uintptr_t a, uintptr_t b)
{
    if (msg == 0x26 && CanShow() && open && !IsAnimating())
    {
        for (int i = 0; i < 5; ++i)
            if (a == reinterpret_cast<uintptr_t>(toolbar[i]))
            {
                if (i == 0) WingAnimRequestToggle();
                else if (i == 1) WingAnimTogglePause();
                else if (i == 2) WingAnimSetCruiseLocked(!WingAnimCruiseLocked());
                else
                {
                    viewLeft = i == 4;
                    SetSavedHealthViewLeft(viewLeft);
                    SubTargetId = SUBOBJ_ID_NONE;
                }
                UpdateVisibility();
                return 1;
            }
    }
    return WinControl::SetProperty(msg, a, b);
}
