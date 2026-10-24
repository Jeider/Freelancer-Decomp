// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Retail TexturePanels / planet-ring — freelancer.exe PTR_LAB_005db1b4 (14 slots).
// Epic: texture-panels. NOT StarGlow (that is StarSphere PTR_FUN_005db658).
//
// Layout recovered from FUN_0050a040 ctor + LAB_0050a240 Exterior stores + Clear/GetPiece.
// Load creates FNebulaClouds (0x12c) via FUN_00550180/00550240 and links them at +0x68.
// DrawPanels / Nebula slot 005091a0 both call FUN_00551500 on those clouds objects.

#include "cli_nebula.h"
#include "common_universe.h"
#include "texture_shapes.h"

#include <cstddef>

// Piece record, stride 0x18, eight per ring, built by Load (LAB_0050a240, 0050aa4f..0050ac5d):
// a run of ring segments plus the bounding sphere of their vertices.
struct FTexturePanelPiece
{
    int FirstSegment; // +0x00  the previous piece's LastSegment (0 for piece 0)
    int LastSegment;  // +0x04  ftol(1e-4f + (P + 1) * NumSegments / PieceCount)
    float Center[3];  // +0x08  (bbox max + bbox min) * 0.5 -- slot 7 GetPiece
    float Radius;     // +0x14  |bbox max - Center| -- slot 8 GetPieceFloat
};
static_assert(sizeof(FTexturePanelPiece) == 0x18, "planet ring piece record 0x18");

struct FTexturePanelsListNode
{
    FTexturePanelsListNode* Next; // +0x00
    FTexturePanelsListNode* Prev; // +0x04
    FNebulaClouds* Clouds;        // +0x08
};

// Retail IPlanetRing : Universe::IZoneImmersion (single primary base).
class IPlanetRing : public Universe::IZoneImmersion
{
public:
    virtual void Load(char const* IniPath, char const* Nickname) = 0; // +0x04
    virtual void Clear() = 0;                                      // +0x08
    virtual void Update(void* Camera, float Dt) = 0;                // +0x0c
    virtual void DrawPiece(void* Camera, int PieceIndex) = 0;       // +0x10
    virtual void DrawPanels(void* Camera) = 0;                      // +0x14
    virtual int GetPieceCount() = 0;                               // +0x18
    virtual float const* GetPiece(int Index) = 0;                   // +0x1c
    virtual float GetPieceFloat(int Index) = 0;                     // +0x20
    virtual float GetVisibility() = 0;                             // +0x24
    virtual Universe::IZone const* GetZone() = 0;                   // +0x28
    virtual double GetZonePos(float* Out3) = 0;                     // +0x2c
    virtual void ApplyDetail(float Detail) = 0;                    // +0x30
    virtual ~IPlanetRing();                                       // +0x34
};

// PlanetaryRings::PlanetRing; retail sizeof 0x78.
struct FTexturePanels : IPlanetRing
{
    FTexturePanels();
    double GetImmersion(Vector const& Point) const override;       // formerly ComputeFactor
    void Load(char const* IniPath, char const* Nickname) override;
    void Clear() override;
    void Update(void* Camera, float Dt) override;
    void DrawPiece(void* Camera, int PieceIndex) override;
    void DrawPanels(void* Camera) override;
    int GetPieceCount() override;
    float const* GetPiece(int Index) override;
    float GetPieceFloat(int Index) override;
    float GetVisibility() override;
    Universe::IZone const* GetZone() override;
    double GetZonePos(float* Out3) override;
    void ApplyDetail(float Detail) override;
    ~FTexturePanels() override;

    FShapeDB Shapes;                     // +0x04, destroyed automatically on constructor failure
    unsigned char ShapePadding[0x18 - sizeof(FShapeDB)];
    // Retail Load: Universe::get_zone(sysId, nickname) — IZone*, not ISystem.
    // Universe::IZone (common_universe.h); retail calls its vt +0xc/+0x28/+0x34/+0x44.
    Universe::IZone const* Zone;          // +0x1c
    int NumSegments;                      // +0x20  default 0x20
    float ThicknessEdge;                  // +0x24  Exterior thickness_edge= (ctor 0.1)
    float InnerEdge;                      // +0x28
    float OuterEdge;                      // +0x2c
    float TransitionDist;                 // +0x30  150.0
    int Field34;                          // +0x34  ring mesh vertex count, 2 * NumSegments (Load)
    void* MeshBuffer;                     // +0x38  ring mesh, Field34 world-space XYZ; freed on Clear
    int PieceCount;                       // +0x3c  Load sets 8; GetPiece bounds
    FTexturePanelPiece* Pieces;           // +0x40  stride 0x18
    float ColorR;                         // +0x44
    float ColorG;                         // +0x48
    float ColorB;                         // +0x4c
    float Opacity;                        // +0x50  1.0
    FTexShape const* Shape;               // +0x54  Exterior shape=
    FTexShape const* DetailShape;         // +0x58  detail_shape=
    float DetailTileU;                    // +0x5c  detail_tile[0] (ctor default 10.0)
    int DetailTileV;                      // +0x60  ftol(detail_tile[1]) (ctor default 2)
    unsigned char TreeFlag;               // +0x64  allocator byte of the +0x68 list (50a093)
    unsigned char Pad65[3];
    FTexturePanelsListNode* ListSentinel; // +0x68
    int ListCount;                        // +0x6c
    float Visibility;                     // +0x70  written by Update via slot0
    unsigned char bLoaded;                // +0x74
    unsigned char Pad75[3];
#ifdef FREELANCER_RP9
    // Port-only (2002 beta [Exterior] fade_range): the planet ring band fades out between these
    // distances as the camera closes in (drawn by RP9's planet_ring.hlsl).
    float FadeFar;                        // +0x78  3400.0
    float FadeNear;                       // +0x7c  500.0
    // Port-only ring puff layer (port.ini [Render] ring_puff_layer; ring ini [RingLayer]): the
    // puffs sit in the ring plane instead of following the camera. 0 = use the default.
    float RingLayerThickness;             // half-thickness in metres (default zone height / 2, min 10)
    float RingLayerCell;                  // cell size in metres (default max_distance * 0.35, min 20)
    float RingLayerDensity;               // multiplier on the puffs per cell (1)
    float RingLayerBodyClear;             // [RingLayer] body_clear: no puff within this many radii (plus a puff)
                                          // of the sun or another planet/moon (0 = off; light clouds round a sun)
    float RingLayerOrbit;                 // degrees per second at the inner edge, Keplerian outwards (0)
    // The band's opacity across it (inner edge .. outer, before Opacity), read back from RP9 at
    // the first draw: the sun behind the ring is dimmed by it (TexturePanelsRayTransmittance).
    float SunProfile[128];
    unsigned char bSunProfile;
#endif
};

static_assert(sizeof(FShapeDB) < 0x18, "ShapeDB leaves room for reserved owner bytes");
#ifndef FREELANCER_RP9
static_assert(sizeof(FTexturePanels) == 0x78, "TexturePanels 0x78");
#endif
static_assert(offsetof(FTexturePanels, Shapes) == 0x04, "ShapeDB +0x04");
static_assert(offsetof(FTexturePanels, Zone) == 0x1c, "Zone +0x1c");
static_assert(offsetof(FTexturePanels, Shape) == 0x54, "Shape +0x54");
static_assert(offsetof(FTexturePanels, ListSentinel) == 0x68, "list +0x68");
static_assert(offsetof(FTexturePanels, bLoaded) == 0x74, "bLoaded +0x74");

FTexturePanels* TexturePanelsCreate(); // FUN_0050bfa0

// FUN_00551500 — shared Clouds panel draw (this = FNebulaClouds).
void TexturePanelDrawClouds(FNebulaClouds* Clouds, void* Camera, void* ExclusionCtx);

// FUN_0050c040 — destroy all TexturePanels in the global Create list.
void TexturePanelsDestroyAll();

// Node of the global TexturePanels instance list DAT_0067505c (FUN_0050bfa0 links every new
// instance at the tail).
struct FTexturePanelsGlobalNode
{
    FTexturePanelsGlobalNode* Next;
    FTexturePanelsGlobalNode* Prev;
    FTexturePanels* Panels;
};

// FUN_00509f20 hands out &DAT_0067505c; its callers read the root's +4, the sentinel node.
// This returns that sentinel.
FTexturePanelsGlobalNode* TexturePanelsListSentinel();

#ifdef FREELANCER_RP9
// Port-only: the fraction of light that gets through every planet ring band (TexturePanels) on
// the straight path From -> To, world space (1 = none in the way). The sun is dimmed by it.
// SunRadius (> 0) spreads the test over the sun's disc where the ray meets a band.
float TexturePanelsRayTransmittance(float const* From, float const* To, float SunRadius);
#endif

// The StarSys tick's walk (FUN_00554eb0 via FUN_00509f20 = &DAT_0067505c): slot 3 update
// (camera, dt) on every live TexturePanels.
void TexturePanelsUpdateAll(void* Camera, float Dt);

// FUN_00509f60 — DAT_00613324 = Detail, then slot 12 ApplyDetail on every live TexturePanels.
void TexturePanelsApplyDetailAll(float Detail);

// FUN_00509f30 — slot 5 DrawPanels(camera) on every live TexturePanels (space draw pass).
void TexturePanelsDrawAll(void* Camera);

// FUN_00552420 / 00552440 / 00552480 — FVF / texture-format helpers used by DrawClouds.
unsigned char TexturePanelsFormatHasAlpha(int FormatId);
int TexturePanelsFvfPositionBytes(unsigned char FvfLow);
int TexturePanelsFvfDiffuseNormalBytes(unsigned char FvfLow);

// Nebula vtable slot 7 LAB_005091a0.
void NebulaDrawCloudsPanels(FNebulaEffect* Nebula, void* Camera);
