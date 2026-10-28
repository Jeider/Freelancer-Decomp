#include "cockpit_free_look.h"
#include "cockpit_free_look_state.h"
#include "cargo_bar_control.h" // ToolTipHoverInit / ToolTipHoverSetCaption
#include "DALib.h"
#include "client_environment.h"
#include "common_iface.h"
#include "engine/engbase.h"
#include "game_options.h"
#include "globals.h"
#include "hud_command_dispatch.h"
#include "hud_maneuvers.h"
#include "input_manager.h"
#include "menu_universe_base.h"
#include "nn_button_control.h"
#include "nn_modal.h"
#include "nn_montage_draw.h"
#include "player_behavior.h"
#include "port_config.h"
#include "space_camera.h"
#include "space_camera_first.h"
#include "space_letterbox.h"
#include "space_state.h"
#include "tooltip_hover.h"
#include "win3d_engine_submit.h"
#include <cstring>

namespace CockpitFreeLook
{
namespace
{
    State Look;
    bool Captured = false;
    bool LockedCapture = false;
    bool OwnLeftButton = false;
    bool EatReleaseFrame = false;
    bool EatMoveFrame = false;
    bool SavedFlightLock = false;
    int SavedX = 0, SavedY = 0;
    HUD_Maneuvers* Owner = nullptr;

    bool CameraAvailable()
    {
        return g_client.current_state == GetSpaceState() && !IsSpaceInitInProgress() &&
            IsFirstPersonCameraCurrent() && GetPlayerObjRW() != nullptr;
    }

    bool InputAvailable()
    {
        // Hide only the cursor drawing, not the game's control-availability
        // flag: that flag also gates keyboard steering and throttle commands.
        return CameraAvailable() && ClientInputIsActive() && GetForegroundWindow() == g_client.window &&
            !G_bNnScreenUp && G_ModalCaptureCount == 0 && HudGetInputFocus() == nullptr &&
            !Win3DAnyCaptured() && !IsClientServerTickPaused() && !IsClientLocationInTransition() &&
            !IsLetterboxVisible() && GetClientMouseCursorDrawFlag() != 0;
    }

    void ReleaseCursor()
    {
        if (!Captured) return;
        SetClientSoftwareCursor(SavedX, SavedY);
        Captured = false;
    }

    void EndDrag()
    {
        LockedCapture = false;
        Look.Release();
        ReleaseCursor();
    }

    bool CanBeginAtCursor()
    {
        if (!Look.enabled || Look.waitingForRelease || !InputAvailable()) return false;
        int x = 0, y = 0, z = 0;
        GetClientSoftwareCursor(&x, &y, &z);
        float ray[3];
        Win3DUnprojectScreenRayDir(Win3DGetCamera(), float(x), float(y), ray);
        // Fresh pick: a cached hover can still refer to the toggle we just left.
        return Win3DPick(ray) == nullptr;
    }

    void BeginDrag(bool locked = false)
    {
        if (!Look.Begin()) return;
        int z = 0;
        GetClientSoftwareCursor(&SavedX, &SavedY, &z);
        Captured = true;
        LockedCapture = locked;
        if (!locked) OwnLeftButton = true;
    }

    class LookButton;
    LookButton* Button = nullptr;

    class LookButton final : public NnButtonControl
    {
    public:
        FButtonMontageTile Tile = {};
        FButtonMontageTile* OriginalTile = nullptr;

        ~LookButton() override
        {
            MontageTile = OriginalTile;
            // WinControl::Destroy can delete children before HUD_Maneuvers's
            // destructor runs. Do not leave an external dangling button pointer.
            if (Button == this)
            {
                Button = nullptr;
                Owner = nullptr;
                Reset();
            }
        }

        void Activate() override
        {
            if ((Flags & kWin3DVisible) && InputAvailable()) Toggle();
        }
        void ShowToolTip() override
        {
            FToolTipHoverInfo info;
            ToolTipHoverInit(&info);
            info.Ids = Look.enabled ? -100012 : -100011;
            bool const ru = _stricmp(PortLanguage(), "ru") == 0;
            ToolTipHoverSetCaption(&info, ru ?
                (Look.enabled ? L"\u041e\u0441\u043c\u043e\u0442\u0440 \u043a\u0430\u0431\u0438\u043d\u044b: \u0432\u043a\u043b. \u041b\u041a\u041c \u2014 \u043e\u0441\u043c\u043e\u0442\u0440, \u043f\u0440\u043e\u0431\u0435\u043b \u2014 \u0431\u0435\u0437 \u0443\u0434\u0435\u0440\u0436\u0430\u043d\u0438\u044f" :
                                L"\u041e\u0441\u043c\u043e\u0442\u0440 \u043a\u0430\u0431\u0438\u043d\u044b: \u0432\u044b\u043a\u043b.") :
                (Look.enabled ? L"Cockpit look: ON (hold LMB, Space toggles hands-free look)" : L"Cockpit look: OFF"));
            for (int i = 0; i < 3; ++i)
            {
                info.WorldPos[i] = Position[i] + Offset[i];
                info.HalfExtents[i] = HalfExtents[i];
            }
            info.bLive = 1;
            NnToolTipFeedHover(&info);
        }
    };

    bool BindHud(HUD_Maneuvers* host)
    {
        if (Owner) return Owner == host;
        Owner = host;
        Button = new LookButton;
        if (!Button->Create(host, nullptr)) { ReleaseHud(host); return false; }
        float const zero[3] = {}, half[3] = {.017f, .017f, 0};
        Button->SetName("CockpitFreeLookToggle");
        Button->Init("Interface\\NeuroNet\\Icons\\nn_playerstatus.3db", nullptr,
            "ui_item_select", nullptr, zero, nullptr, half, 0, 1, 0, 0, -100011, 0, 0);
        Button->OriginalTile = Button->MontageTile;
        if (Button->MontageTile)
        {
            Button->Tile = *Button->MontageTile;
            Button->Tile.Scale = .017f;
            Button->MontageTile = &Button->Tile;
        }
        else if (ClientMeshHolderHasInstance(&Button->MeshHolder))
        {
            float radius = 0, unused[3] = {};
            DALib::Engine->GetInstanceExtent(Button->MeshHolder.EngineInstance, 1, &radius, unused);
            if (std::isfinite(radius) && radius > 0)
            {
                float orientation[9];
                for (int i = 0; i < 9; ++i) orientation[i] = Button->Orientation[i] * .017f / radius;
                Button->SetOrientation(orientation);
            }
        }
        return true;
    }
}

bool Enabled() { return Look.enabled; }
bool BlocksMouseFlight() { return Look.enabled; }
bool HidesCursor() { return Captured; }

void Toggle()
{
    if (!CameraAvailable()) return;
    // Clear only mouse steering, once at the handoff. Never send throttle,
    // engine, cruise or autopilot commands and never zero keyboard input per frame.
    ClearMouseFlightSteering();
    bool const enable = !Look.enabled;
    if (enable) SavedFlightLock = IsMouseFlightLockRequested();
    EndDrag();
    Look.Enable(enable);
    if (!enable) SetMouseFlightLockRequested(SavedFlightLock);
    if (!enable && IsMouseFlightLocked())
        SetClientSoftwareCursor(int(G_RenderSurfaceWidth / 2), int(G_RenderSurfaceHeight / 2));
}

void Reset()
{
    bool const wasEnabled = Look.enabled;
    ReleaseCursor();
    LockedCapture = false;
    Look = State{};
    if (wasEnabled)
    {
        ClearMouseFlightSteering();
        SetMouseFlightLockRequested(SavedFlightLock);
        if (IsMouseFlightLocked())
            SetClientSoftwareCursor(int(G_RenderSurfaceWidth / 2), int(G_RenderSurfaceHeight / 2));
    }
    // Keep ownership of a swallowed press until its release can be consumed.
    // This also prevents an orphan button-up from reaching a HUD widget.
}

void Suspend()
{
    if (!Look.enabled && !Captured) return;
    EndDrag();
    Look.waitingForRelease = true;
}

bool MouseFrame(bool read, int dx, int dy)
{
    EatMoveFrame = Captured;
    EatReleaseFrame = false;
    if (!CameraAvailable())
    {
        Reset();
    }
    else if (!read || !InputAvailable())
    {
        Suspend();
    }
    bool const left = read && (GetClientMouseButtons() & 1u) != 0;
    bool const locked = IsMouseFlightLockRequested();
    if (Look.dragging && locked) LockedCapture = true;
    if (read && !left)
    {
        EatReleaseFrame = OwnLeftButton;
        OwnLeftButton = false;
        Look.waitingForRelease = false;
        if (Look.dragging && !LockedCapture) EndDrag();
    }
    if (LockedCapture && !locked)
    {
        EndDrag();
        Look.waitingForRelease = left;
    }
    // Space uses the same preference as mouse flight. Wait until the activating
    // HUD click has ended and the cursor has left UI before taking it over.
    if (read && locked && !left && !Look.dragging && CanBeginAtCursor())
        BeginDrag(true);
    if (Look.dragging && read)
    {
        Look.Move(float(dx), float(dy), float(G_RenderSurfaceWidth),
            GetGameOption(kGameOptInverseMouse) != 0, G_CockpitHeadTurnX, G_CockpitHeadTurnY);
        // Restore the software position before clamp/release, so the cursor's
        // original screen edge cannot limit how far the player turns their head.
        SetClientSoftwareCursor(SavedX, SavedY);
    }
    return EatMoveFrame || Captured;
}

bool ConsumeMouseEvent(FMouseEvent const& event)
{
    if (event.bMove) return Captured || EatMoveFrame;
    if (event.ButtonIndex != 0) return false;
    if (event.Record.Byte18 == 0 && (OwnLeftButton || EatReleaseFrame))
    {
        if (Look.dragging && !LockedCapture) EndDrag();
        OwnLeftButton = false;
        return true;
    }
    if (event.Record.Byte18 != 0 && LockedCapture)
    {
        OwnLeftButton = true;
        return true;
    }
    if (event.Record.Byte18 != 0 && CanBeginAtCursor())
    {
        BeginDrag();
        return true;
    }
    return OwnLeftButton;
}

bool UpdateHead(CockpitHeadMotion::State& head, float dt)
{
    if (Look.enabled)
    {
        if (!CameraAvailable()) Reset();
        else
        {
            bool lane = false;
            static_cast<IObjRW*>(GetPlayerObjRW())->is_using_tradelane(&lane);
            if (lane || IsLetterboxVisible() || IsClientLocationInTransition()) Reset();
            else if (!InputAvailable()) Suspend();
        }
    }
    return Look.Step(head, G_CockpitHeadTurnX, G_CockpitHeadTurnY, dt);
}

void UpdateHud(HUD_Maneuvers* host)
{
    if (!host->Frame || !host->Buttons[0] || !BindHud(host)) return;
    bool const visible = CameraAvailable() && GetGameOption(kGameOptInterfaceGroup) && GetGameOption(kGameOptHud) &&
        !G_bNnScreenUp && !IsLetterboxVisible() && !IsClientLocationInTransition() &&
        (Captured || GetClientMouseCursorDrawFlag() != 0);
    Button->SetProperty(1, !visible, 0);
    Button->SetProperty(0xc, Look.enabled, 0);
    std::memcpy(Button->AttachPosition, host->Frame->AttachPosition, sizeof(Button->AttachPosition));
    // Follow the actual bar frame, including its width and screen attachment.
    float const halfWidth = (std::max)(host->FrameHalfExtents[0], host->FrameButtonCount * .02f);
    Button->SetOffset(host->Frame->Offset[0] - halfWidth - .023f,
        host->Buttons[0]->Offset[1], host->Buttons[0]->Offset[2]);
}

bool HitTestHud(HUD_Maneuvers const* host, float const* ray)
{
    return Owner == host && Button && (Button->Flags & kWin3DVisible) && Button->HitTest(ray);
}

void ReleaseHud(HUD_Maneuvers const* host)
{
    if (Owner != host) return;
    Reset();
    if (Button)
    {
        Button->MontageTile = Button->OriginalTile;
        Button->Destroy();
        delete Button;
        Button = nullptr;
    }
    Owner = nullptr;
}
}
