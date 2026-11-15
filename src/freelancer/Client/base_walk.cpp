// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only feature, compiled only with FREELANCER_WALK_MODE (src/Directory.Build.props).
#ifdef FREELANCER_WALK_MODE

#include "base_walk.h"
#include "base_walk_math.h"
#include "base_presence.h"
#include "base_emotes.h"
#include "login_mgr.h"
#include "player_spawn.h"
#include "graphics_settings.h"
#include "common_server.h"
#include "font_atlas.h"
#include "font_imp.h"
#include "font_string.h"
#include "win3d_immediate.h"
#include "win3d_renderables.h"
#include <map>
#include <memory>
#include <algorithm>

#include "DALib.h"
#include "character_info.h"
#include "cargo_bar_control.h"
#include "client_environment.h"
#include "common_id.h"
#include "common_reputation.h"
#include "fade_to_black.h"
#include "gameflow.h"
#include "gf_character_object.h"
#include "gf_hotspot.h"
#include "globals.h"
#include "hud_command_dispatch.h"
#include "input_manager.h"
#include "menu_universe_base.h"
#include "nav_bar.h"
#include "nn_button_control.h"
#include "nn_montage_draw.h"
#include "nn_modal.h"
#include "room_camera.h"
#include "room_control.h"
#include "space_camera.h"
#include "space_letterbox.h"
#include "tooltip_hover.h"
#include "wincontrol_base.h"
#include "win3d_engine_submit.h"

#include <cstring>
#include <string>
#include <windows.h>

namespace
{
    DWORD GEmoteStart = 0;
    unsigned GEmoteSerial = 0;
    float GEmoteDuration = 0;
    float GEmoteFloorY = 0, GEmoteSavedFloorHeight = 0;
    bool GEmoteRestoreFloorHeight = false;
    int GEmoteHover = -1;
    unsigned GEmoteButtons = 0;
    bool GEmoteClick = false;
    struct FBaseWalkController
    {
        bool bEnabled = false;
        bool bLooking = false;
        bool bMouseSteer = false;
        bool bSpaceDown = false;
        bool bConsumeLookEvents = false;
        bool bWaitingForRelease = false;
        bool bKeys[7] = {};
        bool bSavedNoUpdate = false;
        bool bOwnPlayer = false;
        unsigned char SavedCursorFlag = 1;
        int CursorX = 0;
        int CursorY = 0;
        FRoomRuntime* Room = nullptr;
        FCharacterObject* Player = nullptr;
        void* Deformable = nullptr;
        FBaseWalkPose Pose;
        FBaseWalkMouseLook MouseLook;
        FBaseWalkInterfaceFade InterfaceFade;
        float SavedPosition[3] = {};
        float SavedOrientation[9] = {};
        float SavedCamera[12] = {};
        float SavedHalfFov = 35.0f;
        float SavedNear = 0.25f;
        float SavedHeight = 0.0f;
        std::string SavedScript;
        int MotionHandle = -1;
        unsigned MotionId = 0;
        int MotionKind = -1;
    };

    FBaseWalkController G_BaseWalk;
    float G_BaseWalkInterfaceDrawOpacity = 1.0f;

    bool IsBase()
    {
        return g_client.current_state == GetGameflowState();
    }

    bool RoomAvailable(FRoomRuntime* Room)
    {
        return IsBase() && Room != nullptr && RoomControlGetField1338(Room) == 0 &&
               GetLetterboxTarget() == 0.0f && GetLetterboxAmount() == 0.0f &&
               GetFadeTarget() == 0.0f && GetFadeLevel() == 0.0f;
    }

    bool WorldAvailable(FRoomRuntime* Room, FCharacterObject* Player)
    {
        return RoomAvailable(Room) && Player != nullptr &&
               Player->Lod.Instance != nullptr && Player->ScriptState == 0;
    }

    bool InputAvailable()
    {
        return IsBase() && ClientInputIsActive() && GetForegroundWindow() == g_client.window &&
               G_ModalCaptureCount == 0 && HudGetInputFocus() == nullptr &&
               !Win3DAnyCaptured() && !IsClientServerTickPaused();
    }

    void ReleaseLook()
    {
        if (G_BaseWalk.bLooking)
        {
            SetClientSoftwareCursor(G_BaseWalk.CursorX, G_BaseWalk.CursorY);
            SetClientMouseCursorDrawFlag(G_BaseWalk.SavedCursorFlag);
            G_BaseWalk.bLooking = false;
        }
        G_BaseWalk.bMouseSteer = false;
        G_BaseWalk.bSpaceDown = false;
        G_BaseWalk.bConsumeLookEvents = false;
        G_BaseWalk.InterfaceFade.Tick(0.0f, false);
        std::memset(G_BaseWalk.bKeys, 0, sizeof(G_BaseWalk.bKeys));
    }

    void StopMotion()
    {
        if (G_BaseWalk.MotionKind >= 3)
            G_BaseWalk.Pose.Position[1] = GEmoteFloorY;
        if (G_BaseWalk.Player != nullptr && G_BaseWalk.MotionHandle != -1)
        {
            DALib::Deform->DestroyHandle(G_BaseWalk.Deformable, G_BaseWalk.MotionHandle);
            G_BaseWalk.Player->RemoveMotionHandle(G_BaseWalk.MotionHandle);
        }
        if (GEmoteRestoreFloorHeight && G_BaseWalk.Deformable) {
            DALib::Deform->SetHeight(G_BaseWalk.Deformable, GEmoteSavedFloorHeight);
            GEmoteRestoreFloorHeight = false;
        }
        if (G_BaseWalk.MotionId != 0)
            GetCharacterInfoDb()->ReleaseScript(G_BaseWalk.MotionId);
        G_BaseWalk.MotionHandle = -1;
        G_BaseWalk.MotionId = 0;
        G_BaseWalk.MotionKind = -1;
    }

    void ReleasePlayer(bool bRestore, bool bResumeOwnScript = false)
    {
        ReleaseLook();
        if (G_BaseWalk.Player == nullptr)
            return;
        StopMotion();
        FCharacterObject* const Player = G_BaseWalk.Player;
        if (bRestore && Player->Lod.Instance == G_BaseWalk.Deformable)
        {
            DALib::Deform->SetPosePos(Player->Lod.Instance, G_BaseWalk.SavedPosition);
            DALib::Deform->SetPoseOri(Player->Lod.Instance, G_BaseWalk.SavedOrientation);
            Player->SetFloat1C(G_BaseWalk.SavedHeight);
            // SetPosePos applies animation floor offsets. Restore the exact root as well.
            DALib::Engine->SetInstancePosition(Player->GetEngineInstance(), G_BaseWalk.SavedPosition);
            DALib::Engine->UpdateInstance(Player->GetEngineInstance(), 0, nullptr);
        }
        if (bRestore)
        {
            FRoomCamera* const Camera = GetRoomRuntimeRoomCamera(G_BaseWalk.Room);
            if (Camera != nullptr)
            {
                Camera->SetTransform(G_BaseWalk.SavedCamera);
                RoomCameraSetHalfFovX(Camera, G_BaseWalk.SavedHalfFov);
                RoomCameraSetZNear(Camera, G_BaseWalk.SavedNear);
            }
        }
        if ((bRestore || bResumeOwnScript) && !G_BaseWalk.bOwnPlayer &&
            Player->Lod.Instance == G_BaseWalk.Deformable && Player->ScriptState == 0 &&
            Player->OwnScript == nullptr)
        {
            Player->SetOwnScript(G_BaseWalk.SavedScript.empty() ? nullptr :
                                   G_BaseWalk.SavedScript.c_str(), 0);
            Player->bNoUpdate = G_BaseWalk.bSavedNoUpdate ? 1 : 0;
        }
        bool const bDeletePlayer = G_BaseWalk.bOwnPlayer;
        G_BaseWalk.bOwnPlayer = false;
        G_BaseWalk.Player = nullptr;
        G_BaseWalk.Deformable = nullptr;
        G_BaseWalk.Room = nullptr;
        if (bDeletePlayer)
            delete Player;
    }

    void SuspendPlayer(bool bSameRoom)
    {
        bool const bCameraTaken = RoomControlGetField1338(G_BaseWalk.Room) != 0 ||
            GetLetterboxTarget() != 0.0f || GetLetterboxAmount() != 0.0f ||
            G_BaseWalk.Player->ScriptState != 0;
        // A same-room fade must retain the classic view for the next toggle-off. A script
        // or camera track has already installed its own view, so leave that view alone.
        ReleasePlayer(bSameRoom && !bCameraTaken, true);
    }

    void ApplyPose()
    {
        // Emotes use authored root translation. Sample their resulting position
        // after the room animation tick instead of pinning the root every frame.
        if (G_BaseWalk.MotionKind >= 3) return;
        float Orientation[9];
        G_BaseWalk.Pose.CharacterOrientation(Orientation);
        DALib::Deform->SetPosePos(G_BaseWalk.Deformable, G_BaseWalk.Pose.Position);
        DALib::Deform->SetPoseOri(G_BaseWalk.Deformable, Orientation);
        // Animation clips contain root translation; the controller owns world movement.
        DALib::Engine->SetInstancePosition(G_BaseWalk.Player->GetEngineInstance(),
                                            G_BaseWalk.Pose.Position);
        G_BaseWalk.Player->bPoseDirty = 1;
    }

    void PrepareEmoteHeight(void* script, char const* name)
    {
        // Despite its historical name, this API returns the clip's RootHeight,
        // not its duration. Deformable adds floor_height to it in Play().
        float rootHeight = 0;
        if (DALib::Anim->GetNamedDurationOut(script, name, &rootHeight) && std::isfinite(rootHeight)) {
            DALib::Deform->GetOffset(G_BaseWalk.Deformable, &GEmoteSavedFloorHeight);
            GEmoteRestoreFloorHeight = true;
            DALib::Deform->SetHeight(G_BaseWalk.Deformable, GEmoteFloorY - rootHeight);
        }
    }

    void HoldEmoteLastFrame(unsigned kind, int handle, float elapsed, float duration)
    {
        if (!BaseEmotes::HoldsLastFrame(kind) || handle == -1 || elapsed < duration) return;
        // -1 selects each channel's own final key, including shorter tracks.
        // ApplyChannels retains the pose without advancing/restarting playback.
        DALib::Anim->StopChannels(static_cast<unsigned long>(handle), AsOpaqueDword(-1.f));
        DALib::Anim->ApplyChannels(static_cast<unsigned long>(handle));
    }

    void SetMotion(int Kind)
    {
        if (Kind == G_BaseWalk.MotionKind)
            return;
        StopMotion();
        // These locomotion clips have matching end poses, unlike the stand-to-move
        // transitions. Match their stride cadence to the controller's world speed.
        FCharacterInfoDb* const Db = GetCharacterInfoDb();
        std::map<unsigned, FCharacterScript>::const_iterator const It =
            Db->Scripts.find(CreateID(BaseEmotes::Name(Kind)));
        if (It == Db->Scripts.end())
            return;
        // Animation playback uses the resource's original spelling, unlike CreateID lookup.
        char const* const Name = It->second.Name.c_str();
        void* const Script = GetCharacterInfoDb()->AcquireScriptByName(Name);
        if (Script == reinterpret_cast<void*>(static_cast<intptr_t>(-1)))
        {
            G_BaseWalk.MotionKind = Kind;
            return;
        }
        G_BaseWalk.MotionId = CreateID(Name);
        if (Kind >= 3) {
            GEmoteFloorY = G_BaseWalk.Pose.Position[1];
            PrepareEmoteHeight(Script, Name);
            GEmoteStart = GetTickCount(); ++GEmoteSerial;
            GEmoteDuration = DALib::Anim->GetNamedDuration(Script, Name);
        }
        // IAnimation2 playback flags: 2 loops; no XYZ root loop accumulation.
        DALib::Deform->Play(G_BaseWalk.Deformable, &G_BaseWalk.MotionHandle, Script,
                             const_cast<char*>(Name), AsOpaqueDword(0.0f), AsOpaqueDword(0.15f),
                             AsOpaqueDword(BaseEmotes::Rate(Kind)), AsOpaqueDword(1.0f), AsOpaqueDword(Kind >= 3 ? 0UL : 2UL),
                             AsOpaqueDword(G_BaseWalk.Pose.Yaw + 3.14159265359f), nullptr);
        if (G_BaseWalk.MotionHandle != -1)
            G_BaseWalk.Player->AddMotionHandle(G_BaseWalk.MotionHandle);
        G_BaseWalk.MotionKind = Kind;
    }

    FCharacterObject* CreateWalkPlayer(FRoomRuntime* Room, Costume const* CostumeOverride = nullptr)
    {
        RoomData* const Data = GetRoomRuntimeRoomData(Room);
        CharPlaceInfo* Spawn = nullptr;
        for (unsigned Index = 0; Index < Data->CharacterPlacements.size(); ++Index)
        {
            CharPlaceInfo* const Placement = Data->CharacterPlacements[Index];
            if (Placement->CharType != 1)
                continue;
            if (Spawn == nullptr)
                Spawn = Placement;
            if (Placement->Posture == 0)
            {
                Spawn = Placement;
                break;
            }
        }
        if (Spawn == nullptr)
            return nullptr;
        CharacterProperties Props;
        GetCostumeDescriptions()->get_costume("trent", Props.Cost);
        if (CostumeOverride && CostumeOverride->PartIds[1]) Props.Cost = *CostumeOverride;
        Costume UnusedComm = Props.Cost;
        PlayerCostume_ApplyOverride(Props.Cost, UnusedComm);
        // A private body keeps this optional avatar independent of scripted/shared PCs.
        return CreateCharacterObject(Props, Spawn, -1, Room, 0, Spawn->Frame);
    }

    bool AcquirePlayer(FRoomRuntime* Room, FCharacterObject* Player)
    {
        void* const Instance = Player->GetEngineInstance();
        if (Instance == reinterpret_cast<void*>(static_cast<intptr_t>(-1)))
            return false;
        FRoomCamera* const Camera = GetRoomRuntimeRoomCamera(Room);
        if (Camera == nullptr)
            return false;
        G_BaseWalk.Room = Room;
        G_BaseWalk.Player = Player;
        G_BaseWalk.Deformable = Player->Lod.Instance;
        std::memcpy(G_BaseWalk.SavedPosition, DALib::Engine->GetInstancePosition(Instance),
                    sizeof(G_BaseWalk.SavedPosition));
        std::memcpy(G_BaseWalk.SavedOrientation, DALib::Engine->GetInstanceOrientation(Instance),
                    sizeof(G_BaseWalk.SavedOrientation));
        std::memcpy(G_BaseWalk.SavedCamera, Camera->Orient, sizeof(G_BaseWalk.SavedOrientation));
        std::memcpy(G_BaseWalk.SavedCamera + 9, Camera->Pos, sizeof(G_BaseWalk.SavedPosition));
        G_BaseWalk.SavedHalfFov = Camera->HalfFovXDeg;
        G_BaseWalk.SavedNear = Camera->ZNear;
        G_BaseWalk.SavedHeight = Player->Float1C;
        G_BaseWalk.SavedScript = Player->OwnScriptName != nullptr ? Player->OwnScriptName : "";
        G_BaseWalk.bSavedNoUpdate = Player->bNoUpdate != 0;
        std::memcpy(G_BaseWalk.Pose.Position, G_BaseWalk.SavedPosition, sizeof(G_BaseWalk.SavedPosition));
        G_BaseWalk.Pose.Yaw = std::atan2(-G_BaseWalk.SavedOrientation[2], -G_BaseWalk.SavedOrientation[8]);
        G_BaseWalk.Pose.CameraYaw = G_BaseWalk.Pose.Yaw;
        G_BaseWalk.Pose.Pitch = 0.18f;
        Player->SetOwnScript(nullptr, 0);
        Player->bNoUpdate = 0;
        RoomCameraSetHalfFovX(Camera, 35.0f);
        RoomCameraSetZNear(Camera, 0.05f);
        SetMotion(0);
        return true;
    }

    class FBaseWalkButton : public NnButtonControl
    {
    public:
        FButtonMontageTile IconTile;

        void ShowToolTip() override
        {
            FToolTipHoverInfo Info;
            ToolTipHoverInit(&Info);
            Info.Ids = G_BaseWalk.bEnabled ? -100002 : -100001;
            ToolTipHoverSetCaption(&Info,
                G_BaseWalk.bEnabled ? L"Walk mode: ON (Space toggles mouse)" : L"Walk mode: OFF");
            for (int Index = 0; Index < 3; ++Index)
            {
                Info.WorldPos[Index] = Position[Index] + Offset[Index];
                Info.HalfExtents[Index] = HalfExtents[Index];
            }
            Info.bLive = 1;
            NnToolTipFeedHover(&Info);
        }
    };

    class FBaseWalkPanel : public WinControl
    {
    public:
        FBaseWalkButton* Button = nullptr;

        bool CanShow() const
        {
            auto* found = Win3DFindByName("NavBar");
            auto* bar = found ? static_cast<NavBar*>(found->AsWinControl()) : nullptr;
            if (!bar || !bar->CanDrawToolbar() || G_bNnScreenUp ||
                G_ModalCaptureCount || IsClientServerTickPaused()) return false;
            for (auto const& item : bar->Buttons) if (item.bRoomSwitch && item.Control) {
                for (auto* node = static_cast<Win3D*>(item.Control); node; node = node->GetParent())
                    if (!(node->Flags & 2)) return false;
                return true;
            }
            return false;
        }

        void Draw() override
        {
            // Draw is also called while simulation ticks are paused by F1.
            if (CanShow()) WinControl::Draw();
        }

        bool Create(Win3D* NewParent, void* Data) override
        {
            ClassName = "BaseWalkPanel";
            SetName("BaseWalkPanel");
            DrawLayer = 0x6c;
            DrawSubLayer = 6;
            Win3D::Create(NewParent, Data);
            float const Position[3] = {0.0f, 0.0f, -1.0f};
            float const Extents[3] = {
                FBaseWalkIconLayout::IconHalfExtent, FBaseWalkIconLayout::IconHalfExtent, 0.0f};
            Button = new FBaseWalkButton;
            if (!Button->Create(this, nullptr))
            {
                delete Button;
                Button = nullptr;
                return false;
            }
            Button->SetName("BaseWalkToggle");
            Button->Init("Interface\\HUD\\HUD_contactotherplayers.3db", nullptr,
                "ui_select_item", nullptr, Position, nullptr, Extents, 0, 0, 0, 1, -1, 0, 0);
            if (Button->MontageTile != nullptr)
            {
                Button->IconTile = *Button->MontageTile;
                Button->IconTile.Scale = FBaseWalkIconLayout::IconScale;
                Button->MontageTile = &Button->IconTile;
            }
            RefreshSelection();
            return true;
        }

        bool UpdatePlacement()
        {
            Win3D* const Found = Win3DFindByName("NavBar");
            if (Found == nullptr)
                return false;
            NavBar* const Bar = static_cast<NavBar*>(Found->AsWinControl());
            if (Bar == nullptr || Bar->ManeuverFrame == nullptr)
                return false;
            WinControl* RoomButton = nullptr;
            for (std::list<FNavBarButton>::const_iterator It = Bar->Buttons.begin();
                 It != Bar->Buttons.end(); ++It)
            {
                if (It->bRoomSwitch != 0)
                {
                    RoomButton = It->Control;
                    break;
                }
            }
            if (RoomButton == nullptr)
                return false;
            FSpaceCamera const* const Camera = Win3DGetCamera();
            void* const FrameInstance = Bar->ManeuverFrame->MeshHolder.EngineInstance;
            float FrameRadius;
            float LocalCenter[3];
            DALib::Engine->GetInstanceExtent(FrameInstance, 0, &FrameRadius, LocalCenter);
            if (FrameRadius <= 0.0f)
                return false;
            float const* const Frame = DALib::Engine->GetInstanceTransform(FrameInstance);
            float Center[3];
            for (int Row = 0; Row < 3; ++Row)
                Center[Row] = Frame[9 + Row] + Frame[Row * 3] * LocalCenter[0] +
                    Frame[Row * 3 + 1] * LocalCenter[1] + Frame[Row * 3 + 2] * LocalCenter[2];
            float const* const RoomPosition =
                DALib::Engine->GetInstancePosition(RoomButton->MeshHolder.EngineInstance);
            float const ToolbarLeft = Camera->HalfWidth +
                (Center[0] - FrameRadius) * Camera->XScale / -Center[2];
            float const ToolbarCenterY = Camera->HalfHeight +
                RoomPosition[1] * Camera->YScale / -RoomPosition[2];
            FBaseWalkIconLayout const Layout = FBaseWalkIconLayout::Calculate(
                Camera->HalfWidth, Camera->HalfHeight, Camera->XScale, Camera->YScale,
                ToolbarLeft, ToolbarCenterY);
            std::memcpy(Button->Offset, Layout.ButtonPosition, sizeof(Button->Offset));
            std::memcpy(Button->HalfExtents, Layout.HalfExtents, sizeof(Button->HalfExtents));
            SetPosition(Position);
            return true;
        }

        void RefreshSelection()
        {
            Button->SetProperty(0xc, G_BaseWalk.bEnabled ? 1 : 0, 0);
        }

        intptr_t SetProperty(int Message, uintptr_t A, uintptr_t B) override
        {
            if (Message == 0x26 && A == reinterpret_cast<uintptr_t>(Button))
            {
                if (!CanShow()) return 1;
                ReleasePlayer(true);
                G_BaseWalk.bEnabled = !G_BaseWalk.bEnabled;
                G_BaseWalk.bWaitingForRelease = false;
                RefreshSelection();
                return 1;
            }
            return WinControl::SetProperty(Message, A, B);
        }
    };

    FBaseWalkPanel* G_BaseWalkPanel = nullptr;
}

#include "base_presence_client.inl"

void BaseWalkTick(float DeltaSeconds)
{
    BasePresenceTick(DeltaSeconds);
    if (!IsBase())
        return;
    G_BaseWalk.InterfaceFade.Tick(DeltaSeconds, G_BaseWalk.bLooking);
    if (G_BaseWalkPanel == nullptr)
    {
        G_BaseWalkPanel = new FBaseWalkPanel;
        if (!G_BaseWalkPanel->Create(nullptr, nullptr))
        {
            Win3DDeleteTree(G_BaseWalkPanel);
            G_BaseWalkPanel = nullptr;
        }
    }
    if (G_BaseWalkPanel != nullptr)
    {
        bool const bPlaced = G_BaseWalkPanel->UpdatePlacement();
        G_BaseWalkPanel->SetHiddenWithChildren(!bPlaced || !G_BaseWalkPanel->CanShow() || G_ModalCaptureCount != 0 ||
            GetLetterboxAmount() != 0.0f ||
            (GetClientMouseCursorDrawFlag() == 0 && !BaseWalkShouldDrawInterface()));
    }
    if (!G_BaseWalk.bEnabled)
        return;
    FRoomRuntime* const Room = static_cast<FRoomRuntime*>(GetClientCurrentLocationRuntime());
    FCharacterObject* Player = Room != nullptr ? RoomControlPlayerCharacter(Room) : nullptr;
    if (Player == nullptr && G_BaseWalk.Room == Room && G_BaseWalk.bOwnPlayer)
        Player = G_BaseWalk.Player;
    bool bAvailable = WorldAvailable(Room, Player);
    if (G_BaseWalk.Player != nullptr && (Room != G_BaseWalk.Room || Player != G_BaseWalk.Player ||
        Player->Lod.Instance != G_BaseWalk.Deformable || !bAvailable))
    {
        SuspendPlayer(Room == G_BaseWalk.Room);
        Player = Room != nullptr ? RoomControlPlayerCharacter(Room) : nullptr;
        bAvailable = WorldAvailable(Room, Player);
    }
    if (G_BaseWalk.bWaitingForRelease || !RoomAvailable(Room))
        return;
    if (Player == nullptr)
    {
        Player = CreateWalkPlayer(Room);
        G_BaseWalk.bOwnPlayer = Player != nullptr;
        bAvailable = WorldAvailable(Room, Player);
    }
    if (!bAvailable || (G_BaseWalk.Player == nullptr && !AcquirePlayer(Room, Player)))
    {
        if (G_BaseWalk.bOwnPlayer)
        {
            G_BaseWalk.bOwnPlayer = false;
            delete Player;
        }
        return;
    }
    if (!InputAvailable())
        ReleaseLook();
    float const Forward = static_cast<float>(G_BaseWalk.bKeys[0]) -
                            static_cast<float>(G_BaseWalk.bKeys[1]);
    float const Strafe = static_cast<float>(G_BaseWalk.bKeys[3]) -
                           static_cast<float>(G_BaseWalk.bKeys[2]);
    bool const bMoving = G_BaseWalk.Pose.Step(Forward, Strafe, G_BaseWalk.bKeys[4], DeltaSeconds);
    float const Lift = static_cast<float>(G_BaseWalk.bKeys[5]) - static_cast<float>(G_BaseWalk.bKeys[6]);
    if (G_BaseWalk.MotionKind >= 3 && (bMoving || Lift != 0)) StopMotion();
    if (Lift != 0.0f && DeltaSeconds > 0.0f)
        G_BaseWalk.Pose.Position[1] += Lift * 1.4f * DeltaSeconds;
    if (bMoving || Lift != 0 || G_BaseWalk.MotionKind < 3 ||
        BaseEmotes::Finished(G_BaseWalk.MotionKind, (GetTickCount() - GEmoteStart) * .001f, GEmoteDuration))
        SetMotion(bMoving ? (G_BaseWalk.bKeys[4] ? 2 : 1) : 0);
    HoldEmoteLastFrame(G_BaseWalk.MotionKind, G_BaseWalk.MotionHandle,
                      (GetTickCount() - GEmoteStart) * .001f, GEmoteDuration);
    ApplyPose();
}

void BaseWalkAfterWorldUpdate()
{
    BasePresenceApply();
    if (G_BaseWalk.Player == nullptr)
        return;
    if (!WorldAvailable(G_BaseWalk.Room, G_BaseWalk.Player))
    {
        SuspendPlayer(true);
        return;
    }
    if (G_BaseWalk.MotionKind >= 3) {
        float const* position = DALib::Engine->GetInstancePosition(G_BaseWalk.Player->GetEngineInstance());
        if (position) std::memcpy(G_BaseWalk.Pose.Position, position, sizeof(G_BaseWalk.Pose.Position));
    }
    ApplyPose();
    // Refresh world matrices after overriding the animated root, before drawing/hotspot picks.
    DALib::Engine->UpdateInstance(G_BaseWalk.Player->GetEngineInstance(), 0, nullptr);
    float Transform[12];
    G_BaseWalk.Pose.CameraTransform(Transform);
    GetRoomRuntimeRoomCamera(G_BaseWalk.Room)->SetTransform(Transform);
}

void BaseWalkBeforeInteraction()
{
    if (G_BaseWalk.Player != nullptr)
        ReleasePlayer(true);
    G_BaseWalk.bWaitingForRelease = G_BaseWalk.bEnabled;
}

bool BaseWalkHandleKey(unsigned Message, unsigned Key)
{
    if (!G_BaseWalk.bEnabled || !IsBase())
        return false;
    if (Message == WM_KEYUP || Message == WM_SYSKEYUP)
    {
        char const Keys[4] = {'W', 'S', 'A', 'D'};
        for (int Index = 0; Index < 4; ++Index)
            if (Key == static_cast<unsigned>(Keys[Index]))
                G_BaseWalk.bKeys[Index] = false;
        if (Key == VK_SHIFT)
            G_BaseWalk.bKeys[4] = false;
        if (Key == VK_UP)
            G_BaseWalk.bKeys[5] = false;
        if (Key == VK_DOWN)
            G_BaseWalk.bKeys[6] = false;
    }
    if (G_BaseWalk.Player == nullptr || !InputAvailable())
        return false;
    bool const bDown = Message == WM_KEYDOWN;
    if (!bDown && Message != WM_KEYUP)
        return false;
    char const Keys[4] = {'W', 'S', 'A', 'D'};
    for (int Index = 0; Index < 4; ++Index)
    {
        if (Key != static_cast<unsigned>(Keys[Index]))
            continue;
        G_BaseWalk.bKeys[Index] = bDown;
        return true;
    }
    if (Key == VK_SHIFT)
    {
        G_BaseWalk.bKeys[4] = bDown;
        return true;
    }
    if (Key == VK_UP || Key == VK_DOWN)
    {
        G_BaseWalk.bKeys[Key == VK_UP ? 5 : 6] = bDown;
        return true;
    }
    if (Key == VK_SPACE)
    {
        if (bDown)
        {
            if (!G_BaseWalk.bSpaceDown)
                G_BaseWalk.bMouseSteer = !G_BaseWalk.bMouseSteer;
            G_BaseWalk.bSpaceDown = true;
        }
        else
            G_BaseWalk.bSpaceDown = false;
        if (!G_BaseWalk.bMouseSteer)
            ReleaseLook();
        return true;
    }
    return false;
}

bool BaseWalkConsumeMouseEvent(FMouseEvent const& Event)
{
    if (GEmoteClick && Event.ButtonIndex == 0) return true;
    if (G_BaseWalk.bLooking || G_BaseWalk.bConsumeLookEvents)
        return true;
    if (G_BaseWalk.bEnabled && Event.ButtonIndex == 0 && Event.bMove == 0 &&
        Event.Record.Byte18 != 0 && Win3DGetHover() != nullptr &&
        (G_BaseWalkPanel == nullptr || !Win3DGetHover()->IsDescendantOf(G_BaseWalkPanel)))
    {
        BaseWalkBeforeInteraction();
    }
    return false;
}

bool BaseWalkMouseFrame(bool bRead, int DeltaX, int DeltaY, int CursorX, int CursorY)
{
    bool const bWasLooking = G_BaseWalk.bLooking;
    unsigned const Buttons = bRead ? GetClientMouseButtons() : 0;
    GEmoteHover = -1;
    if (G_BaseWalk.bEnabled && G_BaseWalk.Player && InputAvailable() &&
        RoomAvailable(G_BaseWalk.Room) && !bWasLooking && GetClientMouseCursorDrawFlag() != 0) {
        int top = static_cast<int>(G_RenderSurfaceHeight) - 160;
        if (CursorX >= 16 && CursorX < 246 && CursorY >= top && CursorY < top + 140)
            GEmoteHover = (CursorY - top) / 28;
    }
    bool pressed = (Buttons & 1u) && !(GEmoteButtons & 1u);
    GEmoteButtons = Buttons;
    if (pressed) GEmoteClick = GEmoteHover >= 0;
    if (GEmoteClick) {
        if (pressed) { StopMotion(); SetMotion(GEmoteHover + 3); }
        if (!(Buttons & 1u)) GEmoteClick = false;
        return true;
    }
    if (G_BaseWalk.bWaitingForRelease && (Buttons & 3u) == 0 &&
        InputAvailable())
        G_BaseWalk.bWaitingForRelease = false;
    bool const bAvailable = G_BaseWalk.Player != nullptr && InputAvailable() &&
        RoomAvailable(G_BaseWalk.Room) && (bWasLooking || GetClientMouseCursorDrawFlag() != 0);
    bool bInteractiveTarget = false;
    if (!bWasLooking && bAvailable && (Buttons & 1u) != 0 &&
        (G_BaseWalk.MouseLook.PreviousButtons & 1u) == 0)
    {
        float Ray[3];
        Win3DUnprojectScreenRayDir(Win3DGetCamera(), static_cast<float>(CursorX),
                                 static_cast<float>(CursorY), Ray);
        int const Point[2] = {CursorX, CursorY};
        FHotspot* Hotspot = nullptr;
        bInteractiveTarget = Win3DPick(Ray) != nullptr || FindHotspotAt(Point, &Hotspot);
    }
    EBaseWalkLookMode Mode = G_BaseWalk.MouseLook.Update(Buttons, bAvailable, bInteractiveTarget);
    if (G_BaseWalk.bMouseSteer && bAvailable)
        Mode = EBaseWalkLookMode::Steer;
    G_BaseWalk.bConsumeLookEvents = bWasLooking || Mode != EBaseWalkLookMode::None;
    if (Mode != EBaseWalkLookMode::None)
    {
        if (!G_BaseWalk.bLooking)
        {
            G_BaseWalk.CursorX = CursorX;
            G_BaseWalk.CursorY = CursorY;
            G_BaseWalk.SavedCursorFlag = GetClientMouseCursorDrawFlag();
            ReleaseHoveredHotspot();
            G_BaseWalk.bLooking = true;
        }
        // Start RMB from the current camera direction after a free LMB orbit.
        G_BaseWalk.Pose.Look(bWasLooking ? static_cast<float>(DeltaX) : 0.0f,
                            bWasLooking ? static_cast<float>(DeltaY) : 0.0f,
                            Mode == EBaseWalkLookMode::Steer);
        SetClientSoftwareCursor(G_BaseWalk.CursorX, G_BaseWalk.CursorY);
        SetClientMouseCursorDrawFlag(0);
        return true;
    }
    if (bWasLooking)
    {
        // Releasing either look button keeps movement keys that are still held.
        SetClientSoftwareCursor(G_BaseWalk.CursorX, G_BaseWalk.CursorY);
        SetClientMouseCursorDrawFlag(G_BaseWalk.SavedCursorFlag);
        G_BaseWalk.bLooking = false;
        G_BaseWalk.InterfaceFade.Tick(0.0f, false);
    }
    return bWasLooking;
}

void BaseWalkFocusLost()
{
    ReleaseLook();
}

bool BaseWalkIsLooking()
{
    return G_BaseWalk.bLooking;
}

bool BaseWalkShouldDrawInterface()
{
    return G_BaseWalk.bLooking && G_BaseWalk.SavedCursorFlag != 0 &&
        G_BaseWalk.InterfaceFade.Opacity() > 0.0f && RoomAvailable(G_BaseWalk.Room) &&
        !G_bNnScreenUp && G_ModalCaptureCount == 0 && !IsClientServerTickPaused() &&
        !IsClientLocationInTransition();
}

FBaseWalkInterfaceDraw::FBaseWalkInterfaceDraw() : SavedOpacity(G_BaseWalkInterfaceDrawOpacity)
{
    // Modal UI can draw while the gameflow tick is paused, before ReleaseLook runs.
    G_BaseWalkInterfaceDrawOpacity = G_BaseWalk.bLooking && InputAvailable() &&
        WorldAvailable(G_BaseWalk.Room, G_BaseWalk.Player) ?
        G_BaseWalk.InterfaceFade.Opacity() : 1.0f;
}

FBaseWalkInterfaceDraw::~FBaseWalkInterfaceDraw()
{
    G_BaseWalkInterfaceDrawOpacity = SavedOpacity;
}

float BaseWalkGetInterfaceDrawOpacity()
{
    return G_BaseWalkInterfaceDrawOpacity;
}

unsigned long BaseWalkFadeInterfaceColor(unsigned long Argb, bool bAdditive)
{
    return FBaseWalkInterfaceFade::FadeColor(Argb, G_BaseWalkInterfaceDrawOpacity, bAdditive);
}

void BaseWalkCharacterChanged(FCharacterObject* Character, bool bDestroying)
{
    if (Character != G_BaseWalk.Player)
        return;
    if (G_BaseWalk.bOwnPlayer && !bDestroying)
    {
        // Reload can replace the body. Detach its handles now; recreate after Load returns.
        ReleaseLook();
        StopMotion();
        G_BaseWalk.Deformable = nullptr;
        return;
    }
    if (bDestroying)
        G_BaseWalk.bOwnPlayer = false;
    ReleasePlayer(!bDestroying);
}

void BaseWalkCharacterScriptStarting(FCharacterObject* Character)
{
    // The private avatar is not published to the room's scripted-character slots.
    if (Character == G_BaseWalk.Player && !G_BaseWalk.bOwnPlayer)
        BaseWalkBeforeInteraction();
}

void BaseWalkRoomDestroyed(FRoomRuntime* Room)
{
    BasePresenceRoomDestroyed(Room);
    if (Room == G_BaseWalk.Room)
        ReleasePlayer(false);
}

void BaseWalkLeaveBase()
{
    BasePresenceClear();
    ReleasePlayer(false);
    G_BaseWalk.bEnabled = false;
    G_BaseWalk.bWaitingForRelease = false;
    G_BaseWalk.MouseLook = FBaseWalkMouseLook();
    if (G_BaseWalkPanel != nullptr)
    {
        Win3DDeleteTree(G_BaseWalkPanel);
        G_BaseWalkPanel = nullptr;
    }
}

#endif // FREELANCER_WALK_MODE
