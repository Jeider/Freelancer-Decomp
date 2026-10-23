// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: the beta's DBG_OPTIONS window and [OUTLINES] drawing. See dbg_options.h.

#include "dbg_options.h"

#ifdef FREELANCER_DBG_OPTIONS

#include "font_atlas.h"
#include "font_imp.h"
#include "font_string.h"
#include "game_options.h"
#include "globals.h"
#include "player_spawn.h"      // GetPlayerShipObject
#include "star_sys.h"          // StarSysGetActiveSystemId
#include "win3d_immediate.h"
#include "win3d_renderables.h" // UiOverlayPrepPipeline

#include "DALib.h"
#include "common_cobject.h"
#include "common_dbg_outlines.h"
#include "common_misc.h"       // ICamera
#include "render/IRenderPipeline.h"

#include <cmath>
#include <cstdio>
#include <vector>
#include <windows.h>

namespace
{
    // ---- The window ----------------------------------------------------------------------

    bool G_bWindowOpen = false;
    int G_Cursor = 0; // row of GGameOptionDescs

    struct FDbgOptionsText
    {
        FFontString Rows[0x50];
        int Shown[0x50];  // the value each row's text was built for (-1: never)
        int Selected = -1;
        int RowHeight = 0;
    };
    FDbgOptionsText* G_Text = nullptr;

    int& OptionValue(int Index)
    {
        return g_display.options[Index];
    }

    void BuildRowText(int Row)
    {
        FGameOptionDesc const& Desc = GGameOptionDescs[Row];
        bool const bHeader = Desc.bSelectable == 0;
        int const Value = OptionValue(Desc.Index);
        wchar_t Text[96];
        // The beta's row: "%c %S = %d" (0x00614bac) with the cursor mark; headers flush left.
        _snwprintf(Text, 95, L"%c %s%S = %d", Row == G_Cursor ? L'>' : L' ', bHeader ? L"" : L"    ",
                   Desc.Name, Value);
        Text[95] = 0;
        FontStringSetText(&G_Text->Rows[Row], Text);
        G_Text->Shown[Row] = Value;
    }

    void Adjust(int Delta)
    {
        FGameOptionDesc const& Desc = GGameOptionDescs[G_Cursor];
        int& Value = OptionValue(Desc.Index);
        if (Delta == 0)
            Value = Value != 0 ? 0 : (Desc.DefaultValue > 1 ? Desc.DefaultValue : 1);
        else
            Value = Value + Delta < 0 ? 0 : Value + Delta;
    }

    // ---- The outlines --------------------------------------------------------------------

    struct FLineVertex
    {
        float X;
        float Y;
        float Z;
        unsigned Color;
    };

    struct FLineBatch
    {
        std::vector<FLineVertex> Vertices;
        unsigned Color = 0xffffffffu;
    };

    void __cdecl AddLine(void* Context, float const* A, float const* B)
    {
        FLineBatch* const Batch = static_cast<FLineBatch*>(Context);
        Batch->Vertices.push_back({A[0], A[1], A[2], Batch->Color});
        Batch->Vertices.push_back({B[0], B[1], B[2], Batch->Color});
    }

    // Three great circles, as the beta's sphere outline (FUN_0040b6d0).
    void __cdecl AddSphere(void* Context, float const* Centre, float Radius)
    {
        int const Segments = 24;
        for (int Axis = 0; Axis < 3; ++Axis)
        {
            float Prev[3] = {};
            for (int Step = 0; Step <= Segments; ++Step)
            {
                double const Angle = 6.283185307179586 * Step / Segments;
                float const U = static_cast<float>(std::cos(Angle) * Radius);
                float const V = static_cast<float>(std::sin(Angle) * Radius);
                float Point[3] = {Centre[0], Centre[1], Centre[2]};
                Point[(Axis + 1) % 3] += U;
                Point[(Axis + 2) % 3] += V;
                if (Step != 0)
                    AddLine(Context, Prev, Point);
                Prev[0] = Point[0];
                Prev[1] = Point[1];
                Prev[2] = Point[2];
            }
        }
    }

    unsigned PackColor(float R, float G, float B)
    {
        return 0xff000000u | (static_cast<unsigned>(R * 255.0f) << 16) |
               (static_cast<unsigned>(G * 255.0f) << 8) | static_cast<unsigned>(B * 255.0f);
    }

    // PartCacheDraw's line pass (FUN_00406510): lighting / specular / blend off, colour from the
    // vertex, stage 0 diffuse only, then a line list through the VB manager.
    unsigned long const kStatesOff[] = {0x89, 0, 0x1d, 0, 0x1b, 0, 0};
    unsigned long const kColourVertexOn[] = {0x8d, 1, 0x91, 1, 0};
    unsigned long const kColourVertexOff[] = {0x8d, 0, 0};
    unsigned long const kStage0[] = {1, 1, 2, 2, 3, 1, 4, 1, 5, 2, 6, 1, 0};

    void ApplyStates(IRenderPipeline* Pipeline, unsigned long const* Table)
    {
        for (; Table[0] != 0; Table += 2)
            Pipeline->SetRenderState((D3DRENDERSTATETYPE)Table[0], static_cast<int>(Table[1]));
    }

    void DrawLines(std::vector<FLineVertex> const& Vertices, ICamera* Camera)
    {
        if (Vertices.empty())
            return;
        IRenderPipeline* const Pipeline = DALib::Pipeline;
        ApplyStates(Pipeline, kStatesOff);
        Pipeline->SetTextureStageTexture(0, nullptr);
        ApplyStates(Pipeline, kColourVertexOn);
        for (unsigned long const* Stage = kStage0; Stage[0] != 0; Stage += 2)
            Pipeline->SetTextureStageState(0, static_cast<int>(Stage[0]), static_cast<int>(Stage[1]));

        float const Identity[12] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
        int bCombined = 1;
        Pipeline->GetPipelineState(7, &bCombined);
        if (bCombined != 0)
            Pipeline->SetModelview(Camera->GetViewTransform());
        else
        {
            Pipeline->SetWorld(Identity);
            Pipeline->SetView(Camera->GetViewTransform());
        }

        unsigned const Chunk = 8192; // even, so no segment is split
        std::vector<unsigned short> Indices(Chunk);
        for (unsigned Index = 0; Index < Chunk; ++Index)
            Indices[Index] = static_cast<unsigned short>(Index);
        for (size_t First = 0; First < Vertices.size(); First += Chunk)
        {
            unsigned const Count = static_cast<unsigned>(
                Vertices.size() - First < Chunk ? Vertices.size() - First : Chunk);
            FRpVertexSrcDesc Source = {};
            Source.Flags = 2;
            Source.Position.ByteSize = 0xc;
            Source.Position.Stride = sizeof(FLineVertex);
            Source.Position.Base = reinterpret_cast<unsigned char const*>(&Vertices[First].X);
            Source.Position.Count = Count;
            Source.Diffuse.ByteSize = 4;
            Source.Diffuse.Stride = sizeof(FLineVertex);
            Source.Diffuse.Base = reinterpret_cast<unsigned char const*>(&Vertices[First].Color);
            Source.Diffuse.Count = Count;
            Source.SrcFvf = 0x42;
            Source.SrcCount = Count;
            FVertexMemoryLock Lock;
            if (DALib::VertexBuffer->LockVertexMemory(0x42, Count, &Lock) < 0)
                break;
            DALib::VertexBuffer->CopyVertexData(Lock.Vertices, Lock.Listing.Fvf, &Source, 0, Count);
            DALib::VertexBuffer->UnlockVertexMemory(&Lock);
            Pipeline->DrawIndexedPrimitiveVb(2, Lock.Listing.VertexBuffer,
                                             static_cast<unsigned>(Lock.Listing.BaseVertex), Count,
                                             Indices.data(), Count, 0);
        }
        ApplyStates(Pipeline, kColourVertexOff);
    }

    bool WithinOutlineRange(CObject const* Object, float const* CameraPos)
    {
        // Beta FUN_00516a10: |camera - object|^2 against 56250000.0f (7500 m, DAT_005c92a0).
        Vector const& Pos = Object->get_position();
        float const Dx = Pos.x - CameraPos[0];
        float const Dy = Pos.y - CameraPos[1];
        float const Dz = Pos.z - CameraPos[2];
        return Dx * Dx + Dy * Dy + Dz * Dz <= 56250000.0f;
    }
}

bool DbgOptionsHandleKey(unsigned Message, unsigned Key)
{
    if (Message != WM_KEYDOWN && Message != WM_SYSKEYDOWN)
        return false;
    if (Key == 'O' && (GetKeyState(VK_CONTROL) & 0x8000) != 0 && (GetKeyState(VK_SHIFT) & 0x8000) != 0)
    {
        G_bWindowOpen = !G_bWindowOpen;
        return true;
    }
    if (!G_bWindowOpen)
        return false;
    switch (Key)
    {
    case VK_UP:
        G_Cursor = G_Cursor > 0 ? G_Cursor - 1 : GGameOptionDescCount - 1;
        return true;
    case VK_DOWN:
        G_Cursor = G_Cursor + 1 < GGameOptionDescCount ? G_Cursor + 1 : 0;
        return true;
    case VK_LEFT:
        Adjust(-1);
        return true;
    case VK_RIGHT:
        Adjust(1);
        return true;
    case VK_RETURN:
    case VK_SPACE:
        Adjust(0);
        return true;
    case VK_ESCAPE:
        G_bWindowOpen = false;
        return true;
    default:
        return false;
    }
}

void DbgOptionsDrawWindow()
{
    if (!G_bWindowOpen)
        return;
    // fonts.ini's DebugText (0.03 of the screen height), else ListText / Normal.
    IFont* Font = FindMenuFontImp("DebugText");
    if (Font == nullptr)
        Font = FindMenuFontImp("ListText");
    if (Font == nullptr)
        Font = FindMenuFontImp("Normal");
    if (Font == nullptr)
        return;
    if (G_Text == nullptr)
    {
        G_Text = new FDbgOptionsText;
        for (int Row = 0; Row < GGameOptionDescCount; ++Row)
        {
            FontStringSetFont(&G_Text->Rows[Row], Font);
            G_Text->Shown[Row] = -1;
        }
    }
    for (int Row = 0; Row < GGameOptionDescCount; ++Row)
    {
        bool const bMarkChanged = (Row == G_Cursor) != (Row == G_Text->Selected);
        if (bMarkChanged || G_Text->Shown[Row] != OptionValue(GGameOptionDescs[Row].Index))
            BuildRowText(Row);
    }
    G_Text->Selected = G_Cursor;
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

    // A page of rows around the cursor.
    int const Top = 40;
    int const Visible = (static_cast<int>(G_RenderSurfaceHeight) - Top - 20) / (G_Text->RowHeight + 1);
    int First = G_Cursor - Visible / 2;
    if (First + Visible > GGameOptionDescCount)
        First = GGameOptionDescCount - Visible;
    if (First < 0)
        First = 0;
    FFontStringDrawOrigin Origin = {};
    Origin.Scale = static_cast<float>(G_RenderSurfaceWidth) - 24.0f;
    Origin.Height = static_cast<float>(G_RenderSurfaceHeight) - 24.0f;
    for (int Row = First; Row < GGameOptionDescCount && Row < First + Visible; ++Row)
    {
        bool const bHeader = GGameOptionDescs[Row].bSelectable == 0;
        // The beta's colours: white for the cursor row, grey otherwise (0x0057004a).
        FontAtlasSetDrawColor(Row == G_Cursor ? 0xffffffffu : bHeader ? 0xffffd27fu : 0xff9f9f9fu);
        Origin.X = 24.0f;
        Origin.Y = static_cast<float>(Top + (Row - First) * (G_Text->RowHeight + 1));
        FontStringDrawChildren(&Origin, &G_Text->Rows[Row], nullptr, nullptr);
    }

    UiOverlayPrepPipeline();
    FontAtlasSetDrawColor(SavedColor);
    Win3DSetViewportRect(SavedViewport[0], SavedViewport[1], SavedViewport[2],
                        SavedViewport[3], __FILE__, __LINE__);
}

void DbgOptionsShutdown()
{
    delete G_Text;
    G_Text = nullptr;
}

void DbgOutlinesDraw(ICamera* Camera)
{
    // Beta FUN_005167a0: nothing unless [OUTLINES] is on, then PHYS SPHERES (2), PHYS WIRES (1),
    // SHIELDS (3) over the object lists, PHANTOMS (4) after.
    if (Camera == nullptr || GetGameOption(kGameOptOutlinesGroup) <= 0)
        return;
    bool const bWires = GetGameOption(kGameOptPhysWires) != 0;
    bool const bSpheres = GetGameOption(kGameOptPhysSpheres) != 0;
    bool const bShields = GetGameOption(kGameOptShields) != 0;
    bool const bPhantoms = GetGameOption(kGameOptPhantoms) != 0;
    if (!bWires && !bSpheres && !bShields && !bPhantoms)
        return;

    float const* const CameraPos = Camera->GetPosition();
    CObject const* const Player = static_cast<CObject const*>(GetPlayerShipObject());
    static std::vector<FLineVertex> S_Vertices;
    FLineBatch Batch;
    Batch.Vertices.swap(S_Vertices);
    Batch.Vertices.clear();

    CObject::Class const Classes[] = {
        CObject::ClassShip, CObject::ClassSolar, CObject::ClassAsteroid, CObject::ClassDynamicAsteroid,
        CObject::ClassLoot, CObject::ClassMine, CObject::ClassGuided, CObject::ClassCounterMeasure,
        CObject::ClassEquipmentObj};
    for (CObject::Class const Class : Classes)
    {
        for (CObject* Object = CObject::FindFirst(Class); Object != nullptr; Object = CObject::FindNext())
        {
            if (!WithinOutlineRange(Object, CameraPos))
                continue;
            // A body made in another system (a solar of the system just left, still referenced)
            // was destroyed with that system's physics: never walk it.
            if (Object->BodyPtr != nullptr && Object->PhysicsSystemId != StarSysGetActiveSystemId())
                continue;
            if (bWires)
            {
                // Beta FUN_00516420: yellow for the player's own, cyan for the rest.
                Batch.Color = Object == Player ? PackColor(1.0f, 1.0f, 0.0f) : PackColor(0.0f, 1.0f, 1.0f);
                DbgOutlineCollisionHull(Object, &AddLine, &AddSphere, &Batch);
            }
            if (bSpheres)
            {
                Batch.Color = PackColor(0.75f, 0.2f, 0.35f);
                DbgOutlinePhysicalSphere(Object, &AddSphere, &Batch);
            }
            if (bShields && Class == CObject::ClassShip)
            {
                // Beta FUN_005162c0: the physical sphere in blue (0, 0, 0.5); brighter here, so
                // it reads against space.
                Batch.Color = PackColor(0.3f, 0.3f, 1.0f);
                DbgOutlinePhysicalSphere(Object, &AddSphere, &Batch);
            }
            if (bPhantoms)
            {
                Batch.Color = PackColor(0.2f, 1.0f, 0.2f);
                DbgOutlinePhantoms(Object, &AddLine, &AddSphere, &Batch);
            }
        }
    }
    DrawLines(Batch.Vertices, Camera);
    Batch.Vertices.swap(S_Vertices);
}

#endif

#ifdef FREELANCER_DBG_OPTIONS
void DbgDrawWorldLines(float const* Points3, unsigned const* Colors, unsigned PointCount, ICamera* Camera,
                       bool bOnTop)
{
    if (Camera == nullptr || PointCount < 2)
        return;
    std::vector<FLineVertex> Vertices;
    Vertices.reserve(PointCount);
    for (unsigned Index = 0; Index < PointCount; ++Index)
        Vertices.push_back({Points3[Index * 3], Points3[Index * 3 + 1], Points3[Index * 3 + 2], Colors[Index]});
    IRenderPipeline* const Pipeline = DALib::Pipeline;
    if (bOnTop)
        Pipeline->SetRenderState(static_cast<D3DRENDERSTATETYPE>(7), 0); // D3DRS_ZENABLE
    DrawLines(Vertices, Camera);
    if (bOnTop)
        Pipeline->SetRenderState(static_cast<D3DRENDERSTATETYPE>(7), 1);
}
#endif
