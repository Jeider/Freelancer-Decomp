// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: the beta's ChaseCamera and hardpoint display. See dbg_chase_camera.h.

#include "dbg_chase_camera.h"

#ifdef FREELANCER_DBG_OPTIONS

#include "dbg_options.h"         // DbgDrawWorldLines
#include "font_atlas.h"
#include "font_imp.h"
#include "font_string.h"
#include "globals.h"
#include "player_spawn.h"        // GetPlayerShipObject
#include "space_camera.h"        // SwitchSpaceCameraMode, GetActiveSpaceCamera
#include "space_camera_game.h"
#include "win3d_immediate.h"
#include "win3d_renderables.h"   // UiOverlayPrepPipeline

#include "DALib.h"
#include "common_cobject.h"
#include "common_iface.h"     // IObjRW (the player's target)
#include "engine/engbase.h"

#include <cmath>
#include <cstdio>
#include <string>
#include <vector>
#include <windows.h>

namespace
{
    // Beta .data 0x0060935c..0x00609368, never written.
    float const kRotAccel = 200.0f;
    float const kRotMax = 100.0f;
    float const kZoomAccel = 1000.0f;
    float const kZoomMax = 550.0f;

    struct FChaseCamera : FGameCamera
    {
        bool Activate(int const* ViewRect4) override;
        void Deactivate() override;
        void Update(float DeltaSeconds) override;
        void DrawScene(unsigned LayerFlags, unsigned Param2) override;
        char const* GetName() override { return "ChaseCamera"; }
    };

    FChaseCamera G_Camera;
    bool G_bConstructed = false;
    bool G_bActive = false;

    // The beta's fields (+0x110..+0x15c).
    unsigned G_TargetId = 0;
    CObject::Class G_TargetClass = CObject::ClassShip;
    float G_MinDistance = 10.0f;
    float G_Distance = 12.5f;
    float G_Yaw = 0.0f;
    float G_Pitch = 0.0f;
    float G_YawRate = 0.0f;
    float G_PitchRate = 0.0f;
    float G_ZoomSpeed = 0.0f;
    float G_YawAccel = 0.0f;
    float G_PitchAccel = 0.0f;
    float G_ZoomAccelNow = 0.0f;
    int G_Mode = 0;              // 0 orbit, 1 ahead, 2 behind, 3 facing
    int G_HardpointMode = 0;     // 0 off, 1 on top, 2 depth-tested
    int G_HardpointIndex = -1;   // -1 = all
    int G_HardpointCount = 0;
    std::string G_HardpointName;
    bool G_bInfo = true;

    // ---- target ----------------------------------------------------------------------------

    CObject* Target()
    {
        if (G_TargetId == 0)
            return nullptr;
        return CObject::Find(G_TargetId, G_TargetClass);
    }

    unsigned IdOf(CObject const* Object)
    {
        return (static_cast<unsigned>(Object->ObjectClass) & 3u) == 3u ? static_cast<CSimple const*>(Object)->Id : 0;
    }

    void Attach(CObject* Object)
    {
        // Beta 0x004f18a0: minimum distance = (|sphere centre| + radius) * 0.8 (* 1.5 for a
        // solar), distance 1.25 times that, rates zero.
        G_TargetId = Object != nullptr ? IdOf(Object) : 0;
        if (Object == nullptr)
            return;
        G_TargetClass = (static_cast<unsigned>(Object->ObjectClass) & CObject::ClassShip) == CObject::ClassShip
                            ? CObject::ClassShip
                            : CObject::ClassSolar;
        Vector Centre;
        float const Radius = Object->get_physical_radius_r(Centre);
        Vector const& Pos = Object->get_position();
        float const Dx = Centre.x - Pos.x, Dy = Centre.y - Pos.y, Dz = Centre.z - Pos.z;
        G_MinDistance = (std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz) + Radius) * 0.8f;
        if (G_TargetClass == CObject::ClassSolar)
            G_MinDistance *= 1.5f;
        if (G_MinDistance < 1.0f)
            G_MinDistance = 1.0f;
        G_Distance = G_MinDistance * 1.25f;
        G_YawRate = G_PitchRate = G_ZoomSpeed = 0.0f;
        G_HardpointIndex = -1;
    }

    void Cycle(bool bNext, bool bSolar)
    {
        // Beta 0x004f2ac0: the next / previous object of the wanted type, wrapping.
        CObject::Class const Class = bSolar ? CObject::ClassSolar : CObject::ClassShip;
        std::vector<CObject*> Objects;
        for (CObject* Object = CObject::FindFirst(Class); Object != nullptr; Object = CObject::FindNext())
            if (IdOf(Object) != 0)
                Objects.push_back(Object);
        if (Objects.empty())
            return;
        int Current = -1;
        for (size_t Index = 0; Index < Objects.size(); ++Index)
            if (IdOf(Objects[Index]) == G_TargetId)
                Current = static_cast<int>(Index);
        int const Count = static_cast<int>(Objects.size());
        int const Next = Current < 0 ? 0 : (Current + (bNext ? 1 : Count - 1)) % Count;
        Attach(Objects[static_cast<size_t>(Next)]);
    }

    // ---- maths ---------------------------------------------------------------------------

    struct FV
    {
        float X, Y, Z;
    };

    FV Column(Matrix const& M, int Col)
    {
        return {M.E[0][Col], M.E[1][Col], M.E[2][Col]};
    }

    FV Normalise(FV V)
    {
        float const Length = std::sqrt(V.X * V.X + V.Y * V.Y + V.Z * V.Z);
        if (Length < 1e-6f)
            return {0.0f, 0.0f, 1.0f};
        return {V.X / Length, V.Y / Length, V.Z / Length};
    }

    FV Cross(FV A, FV B)
    {
        return {A.Y * B.Z - A.Z * B.Y, A.Z * B.X - A.X * B.Z, A.X * B.Y - A.Y * B.X};
    }

    // Camera orientation looking along Look with Up roughly up: the camera's -Z is the view axis,
    // as the ships' (the engines push along -Z).
    void SetLook(FV Pos, FV Look, FV Up)
    {
        FV const Z = Normalise({-Look.X, -Look.Y, -Look.Z});
        FV X = Cross(Up, Z);
        if (X.X * X.X + X.Y * X.Y + X.Z * X.Z < 1e-8f)
            X = Cross({1.0f, 0.0f, 0.0f}, Z);
        X = Normalise(X);
        FV const Y = Cross(Z, X);
        float* const W = G_Camera.World;
        W[0] = X.X; W[1] = Y.X; W[2] = Z.X;
        W[3] = X.Y; W[4] = Y.Y; W[5] = Z.Y;
        W[6] = X.Z; W[7] = Y.Z; W[8] = Z.Z;
        G_Camera.WorldPos[0] = Pos.X;
        G_Camera.WorldPos[1] = Pos.Y;
        G_Camera.WorldPos[2] = Pos.Z;
        G_Camera.bViewDirty = 1;
    }

    float Approach(float Rate, float Accel, float Dt)
    {
        // Beta 0x004f1dd0: accelerate while held, otherwise decay to 0 at 1.5 times the
        // acceleration; clamp to the maximum.
        if (Accel != 0.0f)
            Rate += Accel * Dt;
        else if (Rate > 0.0f)
            Rate = (Rate - kRotAccel * 1.5f * Dt) < 0.0f ? 0.0f : Rate - kRotAccel * 1.5f * Dt;
        else if (Rate < 0.0f)
            Rate = (Rate + kRotAccel * 1.5f * Dt) > 0.0f ? 0.0f : Rate + kRotAccel * 1.5f * Dt;
        return Rate > kRotMax ? kRotMax : Rate < -kRotMax ? -kRotMax : Rate;
    }

    // ---- hardpoints ------------------------------------------------------------------------

    struct FHardpointWalk
    {
        long Instance;
        std::vector<std::string>* Names;
    };

    void __cdecl CollectHardpoint(char const* Name, void* Context)
    {
        static_cast<std::vector<std::string>*>(Context)->push_back(Name);
    }

    struct FInstanceHardpoints
    {
        long Instance;
        std::vector<std::string> Names;
    };

    std::vector<FInstanceHardpoints> CollectHardpoints(long Root)
    {
        // Beta 0x0040c040: the root and every child instance (IEngine slot 0xd8), each
        // archetype's hardpoints (IHardpoint slot 5).
        std::vector<FInstanceHardpoints> Out;
        auto Add = [&Out](long Instance) {
            FInstanceHardpoints Entry;
            Entry.Instance = Instance;
            void* const Arch = DALib::Engine->GetInstanceArchetype(reinterpret_cast<void*>(Instance));
            DALib::Engine->ReleaseHandle(Arch);
            DALib::Hardpoint->EnumerateHardpoints(&CollectHardpoint, Arch, &Entry.Names);
            Out.push_back(Entry);
        };
        Add(Root);
        for (long Child = reinterpret_cast<long>(DALib::Engine->GetRelatedInstance(reinterpret_cast<void*>(Root), 0,
                                                                                  G_InvalidEngineHandle));
             Child != -1;
             Child = reinterpret_cast<long>(DALib::Engine->GetRelatedInstance(reinterpret_cast<void*>(Root), 0,
                                                                             reinterpret_cast<void*>(Child))))
            Add(Child);
        return Out;
    }

    void DrawHardpoints(CObject* Object)
    {
        // Beta 0x0040c160: red, green and blue unit axes at each hardpoint (the wanted index, or
        // all), its name remembered for the label.
        std::vector<FInstanceHardpoints> const Instances = CollectHardpoints(Object->get_index());
        std::vector<float> Points;
        std::vector<unsigned> Colors;
        int Counter = 0;
        G_HardpointName.clear();
        float const Scale = G_MinDistance * 0.05f > 1.0f ? G_MinDistance * 0.05f : 1.0f;
        for (FInstanceHardpoints const& Instance : Instances)
        {
            for (std::string const& Name : Instance.Names)
            {
                bool const bWanted = G_HardpointIndex < 0 || G_HardpointIndex == Counter;
                ++Counter;
                if (!bWanted)
                    continue;
                Vector Pos;
                Matrix Orient;
                if (!HardpointPosition(Instance.Instance, Name.c_str(), &Pos, &Orient))
                    continue;
                if (G_HardpointIndex >= 0)
                    G_HardpointName = Name;
                unsigned const Axis[3] = {0xffff0000u, 0xff00ff00u, 0xff0000ffu};
                for (int Col = 0; Col < 3; ++Col)
                {
                    Points.push_back(Pos.x);
                    Points.push_back(Pos.y);
                    Points.push_back(Pos.z);
                    Points.push_back(Pos.x + Orient.E[0][Col] * Scale);
                    Points.push_back(Pos.y + Orient.E[1][Col] * Scale);
                    Points.push_back(Pos.z + Orient.E[2][Col] * Scale);
                    Colors.push_back(Axis[Col]);
                    Colors.push_back(Axis[Col]);
                }
            }
        }
        G_HardpointCount = Counter;
        if (!Colors.empty())
            DbgDrawWorldLines(Points.data(), Colors.data(), static_cast<unsigned>(Colors.size()), &G_Camera,
                              G_HardpointMode == 1);
    }

    // ---- camera slots ---------------------------------------------------------------------

    bool FChaseCamera::Activate(int const* ViewRect4)
    {
        // Beta 0x004f15b0.
        G_YawRate = G_PitchRate = G_ZoomSpeed = 0.0f;
        G_YawAccel = G_PitchAccel = G_ZoomAccelNow = 0.0f;
        G_Yaw = G_Pitch = 0.0f;
        G_Mode = 0;
        return GameCameraActivate(this, ViewRect4);
    }

    void FChaseCamera::Deactivate()
    {
        G_bActive = false;
        G_YawAccel = G_PitchAccel = G_ZoomAccelNow = 0.0f;
    }

    void FChaseCamera::Update(float Dt)
    {
        GameCameraUpdate(this, Dt);
        CObject* const Object = Target();
        if (Object == nullptr)
            return;
        G_YawRate = Approach(G_YawRate, G_YawAccel, Dt);
        G_PitchRate = Approach(G_PitchRate, G_PitchAccel, Dt);
        G_Yaw += G_YawRate * Dt;
        G_Pitch += G_PitchRate * Dt;
        if (G_Yaw > 360.0f)
            G_Yaw -= 360.0f;
        else if (G_Yaw < -360.0f)
            G_Yaw += 360.0f;
        if (G_ZoomAccelNow != 0.0f)
            G_ZoomSpeed += G_ZoomAccelNow * Dt;
        else
            G_ZoomSpeed = 0.0f;
        G_ZoomSpeed = G_ZoomSpeed > kZoomMax ? kZoomMax : G_ZoomSpeed < -kZoomMax ? -kZoomMax : G_ZoomSpeed;
        G_Distance += G_ZoomSpeed * Dt;
        if (G_Distance < G_MinDistance)
        {
            G_Distance = G_MinDistance;
            G_ZoomSpeed = 0.0f;
        }

        Vector const& P = Object->get_position();
        Matrix const& M = Object->get_orientation();
        FV const Pos = {P.x, P.y, P.z};
        FV const Forward = Normalise({-M.E[0][2], -M.E[1][2], -M.E[2][2]});
        FV const Up = Column(M, 1);
        switch (G_Mode)
        {
        case 1:
        {
            // Ahead of the object, looking where it goes.
            FV const At = {Pos.X + Forward.X * G_MinDistance, Pos.Y + Forward.Y * G_MinDistance,
                           Pos.Z + Forward.Z * G_MinDistance};
            SetLook(At, Forward, Up);
            break;
        }
        case 2:
        {
            // Behind and above, looking where it goes.
            FV const At = {Pos.X - Forward.X * G_Distance + Up.X * G_Distance * 0.4f,
                           Pos.Y - Forward.Y * G_Distance + Up.Y * G_Distance * 0.4f,
                           Pos.Z - Forward.Z * G_Distance + Up.Z * G_Distance * 0.4f};
            SetLook(At, Forward, Up);
            break;
        }
        case 3:
        {
            // In front, facing the object.
            FV const At = {Pos.X + Forward.X * G_Distance, Pos.Y + Forward.Y * G_Distance,
                           Pos.Z + Forward.Z * G_Distance};
            SetLook(At, {-Forward.X, -Forward.Y, -Forward.Z}, Up);
            break;
        }
        default:
        {
            // Orbit about the object, yaw about its up axis and pitch about its right axis,
            // starting behind it.
            double const Yaw = G_Yaw * 3.14159265358979 / 180.0;
            double const Pitch = G_Pitch * 3.14159265358979 / 180.0;
            FV const Right = Column(M, 0);
            FV const Back = {-Forward.X, -Forward.Y, -Forward.Z};
            float const Cy = static_cast<float>(std::cos(Yaw)), Sy = static_cast<float>(std::sin(Yaw));
            float const Cp = static_cast<float>(std::cos(Pitch)), Sp = static_cast<float>(std::sin(Pitch));
            FV const Flat = {Back.X * Cy + Right.X * Sy, Back.Y * Cy + Right.Y * Sy, Back.Z * Cy + Right.Z * Sy};
            FV const Dir = {Flat.X * Cp + Up.X * Sp, Flat.Y * Cp + Up.Y * Sp, Flat.Z * Cp + Up.Z * Sp};
            FV const At = {Pos.X + Dir.X * G_Distance, Pos.Y + Dir.Y * G_Distance, Pos.Z + Dir.Z * G_Distance};
            SetLook(At, {-Dir.X, -Dir.Y, -Dir.Z}, Up);
            break;
        }
        }
    }

    void FChaseCamera::DrawScene(unsigned LayerFlags, unsigned Param2)
    {
        FGameCamera::DrawScene(LayerFlags, Param2);
        CObject* const Object = Target();
        if (Object != nullptr && G_HardpointMode != 0)
            DrawHardpoints(Object);
    }

    // ---- overlay text -------------------------------------------------------------------

    struct FOverlayText
    {
        FFontString Rows[3];
        std::wstring Shown[3];
        int RowHeight = 0;
    };
    FOverlayText* G_Text = nullptr;

    void SetRow(int Row, wchar_t const* Text)
    {
        if (G_Text->Shown[Row] != Text)
        {
            FontStringSetText(&G_Text->Rows[Row], Text[0] != 0 ? Text : L" ");
            G_Text->Shown[Row] = Text;
        }
    }

    void Leave()
    {
        G_bActive = false;
        SwitchSpaceCameraMode("player", nullptr);
    }

    void Enter()
    {
        if (!G_bConstructed)
        {
            GameCameraConstruct(&G_Camera);
            G_bConstructed = true;
        }
        CObject* Start = nullptr;
        if (CObject* const Player = static_cast<CObject*>(GetPlayerShipObject()))
        {
            Start = Player;
            if ((static_cast<unsigned>(Player->ObjectClass) & 0x503u) == 0x503u)
                if (IObjRW* const Targeted = static_cast<CShip*>(Player)->get_target())
                    if (CObject const* const TargetObject = Targeted->cobject())
                        Start = const_cast<CObject*>(TargetObject);
        }
        if (Start == nullptr)
            return;
        Attach(Start);
        if (SwitchSpaceCameraMode("chase", nullptr) != nullptr)
            G_bActive = true;
    }
}

FSpaceCamera* DbgChaseCamera()
{
    return G_bConstructed ? &G_Camera : nullptr;
}

bool DbgChaseHandleKey(unsigned Message, unsigned Key)
{
    bool const bDown = Message == WM_KEYDOWN || Message == WM_SYSKEYDOWN;
    bool const bUp = Message == WM_KEYUP || Message == WM_SYSKEYUP;
    if (!bDown && !bUp)
        return false;
    bool const bCtrl = (GetKeyState(VK_CONTROL) & 0x8000) != 0;
    bool const bShift = (GetKeyState(VK_SHIFT) & 0x8000) != 0;
    if (bDown && Key == 'C' && bCtrl && bShift)
    {
        if (G_bActive)
            Leave();
        else if (GetActiveSpaceCamera() != nullptr)
            Enter();
        return true;
    }
    if (!G_bActive)
        return false;
    if (GetActiveSpaceCamera() != DbgChaseCamera())
    {
        // Something else (a cutscene, death) took the view.
        G_bActive = false;
        return false;
    }

    switch (Key)
    {
    case VK_ESCAPE:
        if (bDown)
            Leave();
        return true;
    case VK_NEXT:
    case VK_PRIOR:
        if (bDown)
        {
            bool const bNext = Key == VK_NEXT;
            if (G_HardpointMode != 0 && !bCtrl)
            {
                if (G_HardpointCount > 0)
                {
                    G_HardpointIndex += bNext ? 1 : -1;
                    if (G_HardpointIndex >= G_HardpointCount)
                        G_HardpointIndex = -1;
                    else if (G_HardpointIndex < -1)
                        G_HardpointIndex = G_HardpointCount - 1;
                }
            }
            else
                Cycle(bNext, bCtrl);
        }
        return true;
    case VK_UP:
        G_PitchAccel = bDown ? kRotAccel : 0.0f;
        return true;
    case VK_DOWN:
        G_PitchAccel = bDown ? -kRotAccel : 0.0f;
        return true;
    case VK_LEFT:
        G_YawAccel = bDown ? -kRotAccel : 0.0f;
        return true;
    case VK_RIGHT:
        G_YawAccel = bDown ? kRotAccel : 0.0f;
        return true;
    case VK_ADD:
        G_ZoomAccelNow = bDown ? kZoomAccel : 0.0f;
        return true;
    case VK_SUBTRACT:
        G_ZoomAccelNow = bDown ? -kZoomAccel : 0.0f;
        return true;
    case VK_HOME:
        if (bDown)
        {
            G_Distance = G_MinDistance * 2.0f;
            G_Yaw = G_Pitch = G_YawRate = G_PitchRate = 0.0f;
        }
        return true;
    case VK_BACK:
        if (bDown)
            G_MinDistance = 1.0f;
        return true;
    case 'V':
        if (bDown)
            G_Mode = (G_Mode + 1) % 4;
        return true;
    case VK_MULTIPLY:
        if (bDown)
        {
            G_HardpointMode = (G_HardpointMode + 1) % 3;
            G_HardpointIndex = -1;
        }
        return true;
    case 'I':
        if (bDown)
            G_bInfo = !G_bInfo;
        return true;
    default:
        return false;
    }
}

void DbgChaseDrawOverlay()
{
    if (!G_bActive || GetActiveSpaceCamera() != DbgChaseCamera())
        return;
    IFont* Font = FindMenuFontImp("DebugText");
    if (Font == nullptr)
        Font = FindMenuFontImp("ListText");
    if (Font == nullptr)
        return;
    if (G_Text == nullptr)
    {
        G_Text = new FOverlayText;
        for (FFontString& Row : G_Text->Rows)
            FontStringSetFont(&Row, Font);
    }

    wchar_t Text[256];
    // Beta resource 0x577: "EXTERNAL VIEW - PRESS %s TO RETURN TO NORMAL VIEW".
    SetRow(0, L"EXTERNAL VIEW - PRESS ESC TO RETURN TO NORMAL VIEW");
    CObject* const Object = Target();
    if (Object != nullptr && G_bInfo)
    {
        Vector const& P = Object->get_position();
        float const* const C = G_Camera.WorldPos;
        float const Range = std::sqrt((P.x - C[0]) * (P.x - C[0]) + (P.y - C[1]) * (P.y - C[1]) +
                                      (P.z - C[2]) * (P.z - C[2]));
        _snwprintf(Text, 255, L"%s ID = %X  pos = %.0f, %.0f, %.0f  range = %.0f  mode = %d",
                   G_TargetClass == CObject::ClassShip ? L"SHIP" : L"SOLAR", G_TargetId,
                   static_cast<double>(P.x), static_cast<double>(P.y), static_cast<double>(P.z),
                   static_cast<double>(Range), G_Mode);
        Text[255] = 0;
        SetRow(1, Text);
    }
    else
        SetRow(1, L"");
    if (G_HardpointMode != 0)
    {
        // Beta 0x004f3670: "HARDPOINT [ALL]" / "HARDPOINT [%d] = %S", "(DRAW ON TOP)".
        if (G_HardpointIndex < 0)
            _snwprintf(Text, 255, L"HARDPOINT [ALL] (%d)%s", G_HardpointCount,
                       G_HardpointMode == 1 ? L"  (DRAW ON TOP)" : L"");
        else
            _snwprintf(Text, 255, L"HARDPOINT [%d] = %S%s", G_HardpointIndex, G_HardpointName.c_str(),
                       G_HardpointMode == 1 ? L"  (DRAW ON TOP)" : L"");
        Text[255] = 0;
        SetRow(2, Text);
    }
    else
        SetRow(2, L"");
    if (G_Text->RowHeight == 0)
    {
        int Size[2] = {};
        FontStringGetExtent(&G_Text->Rows[0], Size);
        G_Text->RowHeight = Size[1] > 0 ? Size[1] : 16;
    }

    UiOverlayPrepPipeline();
    int SavedViewport[4] = {};
    Win3DGetViewport(0xba2, SavedViewport);
    Win3DSetViewportRect(0, 0, static_cast<int>(G_RenderSurfaceWidth),
                        static_cast<int>(G_RenderSurfaceHeight), __FILE__, __LINE__);
    unsigned const SavedColor = FontAtlasDrawColor();
    FFontStringDrawOrigin Origin = {};
    Origin.Scale = static_cast<float>(G_RenderSurfaceWidth) - 16.0f;
    Origin.Height = static_cast<float>(G_RenderSurfaceHeight) - 8.0f;
    float const Heights[3] = {8.0f, static_cast<float>(G_RenderSurfaceHeight) - 2.0f * (G_Text->RowHeight + 4),
                              static_cast<float>(G_RenderSurfaceHeight) - (G_Text->RowHeight + 4)};
    unsigned const Colours[3] = {0xffffffffu, 0xffe0e0e0u, 0xffff4040u};
    for (int Row = 0; Row < 3; ++Row)
    {
        FontAtlasSetDrawColor(Colours[Row]);
        Origin.X = 16.0f;
        Origin.Y = Heights[Row];
        FontStringDrawChildren(&Origin, &G_Text->Rows[Row], nullptr, nullptr);
    }
    UiOverlayPrepPipeline();
    FontAtlasSetDrawColor(SavedColor);
    Win3DSetViewportRect(SavedViewport[0], SavedViewport[1], SavedViewport[2],
                        SavedViewport[3], __FILE__, __LINE__);
}

void DbgChaseShutdown()
{
    delete G_Text;
    G_Text = nullptr;
}

#endif
