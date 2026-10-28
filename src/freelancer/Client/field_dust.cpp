// Port-only (RP9) field dust: a faint lit dust volume filling an asteroid field's zone ellipsoid.
// See field_dust.h and docs/re/asteroid_far_look.md ("Field dust").

#include "field_dust.h"
#include "field_dust_batch.h"

#ifdef FREELANCER_RP9

#include "cli_asteroid.h"
#include "DALib.h"
#include "common_ini.h"
#include "common_misc.h" // ICamera
#include "common_universe.h"
#include "game_options.h"
#include "port_config.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render_ex.h"
#include "solar_spheres.h"
#include "space_haze.h" // SpaceHazeEnsureNoise
#include "star_sys.h"   // StarSysFindNebula

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <map>
#include <memory>
#include <vector>

namespace
{
    char const kShader[] = "SHADERS\\field_dust.hlsl";
    int const kMaxFields = FieldDustBatch::MaxFields;
    int const kMaxExclusions = 4;
    int const kFieldRegisters = 12 + kMaxExclusions * 4;
    int const kFirstFieldRegister = 8;
    static_assert(kFieldRegisters == FieldDustBatch::FieldRegisters, "dust batch constant layout");
    double const kPi = 3.14159265358979323846;

    // [FieldDust] as parsed; a negative value means "derive it from the field's other sections".
    struct FDustParams
    {
        float Opacity = 0.22f;
        float MaxOpacity = 0.35f;
        bool bColor = false;
        float Color[3] = {0.0f, 0.0f, 0.0f};
        float Ambient = 0.12f;
        float Brightness = 0.8f;
        float Forward = 0.55f;
        float ForwardWeight = 0.5f;
        float Back = 0.25f;
        float NoiseScale = 4000.0f;
        float Coverage = 0.45f;
        float Softness = 0.25f;
        float Clump = 0.7f;
        float EdgeSoftness = 1.5f;
        float Thickness = -1.0f;
        float ClearRadius = -1.0f;
        int Steps = 6;
        float LodDistance = 25000.0f;
        float FarDist = -1.0f;
        float FarFade = -1.0f;
        bool bExcludeZones = false;
    };

    struct FDustField
    {
        FDustParams P;
        bool bBuilt = false;
        bool bBlocked = false; // a nebula is the medium here, or the zone is unusable
        Universe::IZone const* Zone = nullptr;
        double Anchor[3] = {0.0, 0.0, 0.0};
        float Radii[3] = {1.0f, 1.0f, 1.0f};
        float MaxRadius = 1.0f;
        float Rows[3][3] = {};
        float Sigma = 0.0f;
        float Colour[3] = {0.6f, 0.55f, 0.5f};
        float SunColour[3] = {1.0f, 1.0f, 1.0f};
        float ThicknessUnit = 0.0f;
        float ClearRadius = 2000.0f;
        float FarDist = 70000.0f;
        float FarFade = 10000.0f;
        double NoiseOffset[3] = {0.0, 0.0, 0.0};
        int ExclusionCount = 0;
        Universe::IZone const* Exclusions[kMaxExclusions] = {};
        // A planetary ring's dust (FieldDustRingUpdate): a slab round the ring plane with a hole.
        bool bRing = false;
        bool bSeen = false;       // registered since the last draw
        float InnerRatio = 0.0f;  // the hole's radius over the outer one
    };

    std::map<FCliAsteroid const*, std::unique_ptr<FDustField>> G_Fields;
    std::map<Universe::IZone const*, std::unique_ptr<FDustField>> G_Rings;
    FRPExProgram* G_MarchProgram = nullptr;
    FRPExProgram* G_CompositeProgram = nullptr;
    bool G_bProgramsTried = false;
    FRPExTexture* G_Target = nullptr;
    bool G_bTargetTried = false;
    float G_TargetScale = 0.0f;

    double Clamp01(double T)
    {
        return T < 0.0 ? 0.0 : (T > 1.0 ? 1.0 : T);
    }

    // splitmix64: deterministic.
    uint64_t Hash(uint64_t X)
    {
        X += 0x9e3779b97f4a7c15ull;
        X = (X ^ (X >> 30)) * 0xbf58476d1ce4e5b9ull;
        X = (X ^ (X >> 27)) * 0x94d049bb133111ebull;
        return X ^ (X >> 31);
    }

    void Set4(float* Out, float A, float B, float C, float D)
    {
        Out[0] = A;
        Out[1] = B;
        Out[2] = C;
        Out[3] = D;
    }

    // The zone's radii along its local axes (box, cylinder and ring: the inscribed ellipsoid) --
    // nebula_volume.cpp's ZoneRadii (that file's helpers are file-local).
    void ZoneRadii(Universe::IZone const* Zone, float* Radius)
    {
        const Vector Size = Zone->GetSize();
        switch (Zone->GetShape())
        {
        case Universe::ZoneShapeSphere:
            Radius[0] = Size.x;
            Radius[1] = Size.x;
            Radius[2] = Size.x;
            break;
        case Universe::ZoneShapeEllipsoid:
            Radius[0] = Size.x;
            Radius[1] = Size.y;
            Radius[2] = Size.z;
            break;
        case Universe::ZoneShapeBox:
            Radius[0] = Size.x * 0.5f;
            Radius[1] = Size.y * 0.5f;
            Radius[2] = Size.z * 0.5f;
            break;
        case Universe::ZoneShapeCylinder:
            Radius[0] = Size.x;
            Radius[1] = Size.y * 0.5f;
            Radius[2] = Size.x;
            break;
        case Universe::ZoneShapeRing:
            Radius[0] = Size.x;
            Radius[1] = Size.z * 0.5f;
            Radius[2] = Size.x;
            break;
        default:
        {
            const float R = Zone->GetRadius();
            Radius[0] = R;
            Radius[1] = R;
            Radius[2] = R;
            break;
        }
        }
    }

    // Rows that take a camera-relative point into the zone's unit space (|local| = 1 on the
    // surface): row j = the zone's local axis j (column j of its orientation) / radius j.
    void ZoneLocalRows(Universe::IZone const* Zone, float Rows[3][3])
    {
        const Matrix& Orientation = Zone->GetOrientation();
        float Radius[3];
        ZoneRadii(Zone, Radius);
        for (int Axis = 0; Axis < 3; ++Axis)
        {
            const float Inv = Radius[Axis] > 1.0e-3f ? 1.0f / Radius[Axis] : 0.0f;
            Rows[Axis][0] = Orientation.E[0][Axis] * Inv;
            Rows[Axis][1] = Orientation.E[1][Axis] * Inv;
            Rows[Axis][2] = Orientation.E[2][Axis] * Inv;
        }
    }

    // Derives everything the dust needs from the zone and the field's other sections. Run once.
    void BuildField(FCliAsteroid const* Field, FDustField& D)
    {
        D.bBuilt = true;
        FCliAsteroidFarInfo Info;
        if (!CliAsteroidGetFarInfo(Field, &Info) || Info.Zone == nullptr)
        {
            D.bBlocked = true;
            return;
        }
        FDustParams const& P = D.P;
        Universe::IZone const* const Zone = Info.Zone;
        D.Zone = Zone;
        Vector const& ZonePos = Zone->GetPos();
        D.Anchor[0] = ZonePos.x;
        D.Anchor[1] = ZonePos.y;
        D.Anchor[2] = ZonePos.z;

        // Inside a nebula the nebula is the medium (li_cal's fields are like that).
        if (Info.bFogZone || StarSysFindNebula(&ZonePos, nullptr, nullptr) != nullptr)
        {
            D.bBlocked = true;
            return;
        }

        ZoneRadii(Zone, D.Radii);
        for (int I = 0; I < 3; ++I)
            D.Radii[I] = (std::max)(1.0f, D.Radii[I]);
        D.MaxRadius = (std::max)(D.Radii[0], (std::max)(D.Radii[1], D.Radii[2]));
        float const MinRadius = (std::min)(D.Radii[0], (std::min)(D.Radii[1], D.Radii[2]));
        ZoneLocalRows(Zone, D.Rows);
        if (P.bExcludeZones)
        {
            for (int I = 0; I < Info.ExclusionCount && D.ExclusionCount < kMaxExclusions; ++I)
            {
                Universe::IZone const* Hole = Info.Exclusion[I];
                if (Hole->GetShape() == Universe::ZoneShapeSphere || Hole->GetShape() == Universe::ZoneShapeEllipsoid)
                    D.Exclusions[D.ExclusionCount++] = Hole;
            }
        }

        // sigma from the opacity straight through the centre along the shortest axis: the chord
        // integral of 1 - r^2 there is 4/3 R.
        float const Opacity = (std::max)(0.001f, (std::min)(0.95f, P.Opacity));
        D.Sigma = -std::log(1.0f - Opacity) / ((4.0f / 3.0f) * MinRadius);

        float const Thickness = P.Thickness >= 0.0f ? P.Thickness : Info.MaxBandThickness;
        D.ThicknessUnit = Thickness > 0.0f ? Thickness / D.Radii[1] : 0.0f;

        D.ClearRadius = P.ClearRadius > 0.0f
                            ? P.ClearRadius
                            : ((Info.bHasBillboards && Info.BillboardCentre > 0.0f) ? Info.BillboardCentre : 2000.0f);
        bool const bBandFade = Info.bHasBand && Info.BandFade[3] > Info.BandFade[2];
        D.FarDist = P.FarDist > 0.0f ? P.FarDist : (bBandFade ? Info.BandFade[3] : 70000.0f);
        float const FarFade = P.FarFade > 0.0f ? P.FarFade
                                               : (bBandFade ? Info.BandFade[3] - Info.BandFade[2] : 10000.0f);
        D.FarFade = (std::max)(1.0f, (std::min)(FarFade, D.FarDist));

        // The colour: the band's (else the billboards') color_shift times the field's diffuse tint.
        float Diffuse[3] = {Info.Diffuse[0], Info.Diffuse[1], Info.Diffuse[2]};
        if (Diffuse[0] + Diffuse[1] + Diffuse[2] < 0.01f)
            Diffuse[0] = Diffuse[1] = Diffuse[2] = 1.0f;
        float Shift[3] = {0.6f, 0.55f, 0.5f};
        if (Info.bHasBand)
            memcpy(Shift, Info.BandColor, sizeof(Shift));
        else if (Info.bHasBillboards)
            memcpy(Shift, Info.BillboardColor, sizeof(Shift));
        for (int I = 0; I < 3; ++I)
            D.Colour[I] = P.bColor ? P.Color[I] : static_cast<float>(Clamp01(Shift[I] * Diffuse[I]));

        // The sun's light at the zone's centre.
        float Sun[4];
        float const Centre[3] = {ZonePos.x, ZonePos.y, ZonePos.z};
        float Rgb[3];
        if (FindSystemSunSphere(Sun) && FindSunLightColour(Sun, Centre, Rgb))
        {
            for (int I = 0; I < 3; ++I)
                D.SunColour[I] = (std::max)(0.0f, Rgb[I]);
        }

        // Where in the shared noise this field samples: the zone's position decides, so it is the
        // same every run and differs per field.
        uint32_t PosBits[3];
        memcpy(PosBits, Centre, sizeof(PosBits));
        uint64_t Seed = 0x5d0c7fe1d5ull;
        for (int I = 0; I < 3; ++I)
            Seed = Hash(Seed ^ PosBits[I]);
        for (int I = 0; I < 3; ++I)
        {
            Seed = Hash(Seed);
            D.NoiseOffset[I] = static_cast<double>(Seed >> 11) * (32.0 / 9007199254740992.0);
        }
    }

    float ReadColor255(INI_Reader& Reader, int I)
    {
        return static_cast<float>(Clamp01(Reader.get_value_float(I) / 255.0));
    }

    bool GatesPass(int Enclosure)
    {
        static int const S_Enabled = PortConfigInt("Render", "field_dust", 1);
        if (S_Enabled == 0 || Enclosure == 2 || !RenderEx::IsAvailable())
            return false;
        if (GetGameOption(kGameOptEffectsGroup) == 0 || GetGameOption(kGameOptAsteroids) == 0)
            return false;
        FRPExCaps Caps;
        return RenderEx::GetCaps(&Caps) && Caps.bSceneDepth;
    }

    // A ring's dust needs the extension and a depth buffer, not the asteroid options.
    bool RingGatesPass()
    {
        static int const S_Enabled = PortConfigInt("Render", "ring_dust", 0);
        if (S_Enabled == 0 || !RenderEx::IsAvailable() || GetGameOption(kGameOptEffectsGroup) == 0)
            return false;
        FRPExCaps Caps;
        return RenderEx::GetCaps(&Caps) && Caps.bSceneDepth;
    }

    // Everything a ring's dust takes from its zone (size: x outer, y inner, z thickness) and ring layer.
    void BuildRing(Universe::IZone const* Zone, float LayerThickness, float Density, float const* Tint,
                   FDustField& D)
    {
        D.bBuilt = true;
        D.bRing = true;
        D.Zone = Zone;
        Vector const& ZonePos = Zone->GetPos();
        D.Anchor[0] = ZonePos.x;
        D.Anchor[1] = ZonePos.y;
        D.Anchor[2] = ZonePos.z;
        Vector const Size = Zone->GetSize();
        float const Outer = (std::max)(10.0f, Size.x);
        float const Inner = (std::max)(0.0f, (std::min)(Size.y, Outer * 0.98f));
        float const Thickness = LayerThickness > 0.0f ? LayerThickness : (std::max)(10.0f, Size.z * 0.5f);
        D.InnerRatio = Inner / Outer;
        // A flat ellipsoid would pinch the slab towards the rim: this one is three layers thick and the
        // slab is cut inside it (ThicknessUnit); its axes are the zone's (local y = the ring's normal).
        float const Bound = 3.0f * Thickness;
        D.Radii[0] = Outer;
        D.Radii[1] = Bound;
        D.Radii[2] = Outer;
        D.MaxRadius = Outer;
        Matrix const& Orientation = Zone->GetOrientation();
        for (int Axis = 0; Axis < 3; ++Axis)
        {
            float const Inv = 1.0f / D.Radii[Axis];
            D.Rows[Axis][0] = Orientation.E[0][Axis] * Inv;
            D.Rows[Axis][1] = Orientation.E[1][Axis] * Inv;
            D.Rows[Axis][2] = Orientation.E[2][Axis] * Inv;
        }
        D.ThicknessUnit = Thickness / Bound;

        // The extinction per metre at full density: about the opacity through the slab (ring_dust_opacity)
        // scaled by the layer's density.
        static float const S_Opacity = (std::max)(0.0f, PortConfigFloat("Render", "ring_dust_opacity", 1.0f));
        D.Sigma = S_Opacity * (std::max)(0.05f, Density) * 0.9f / Thickness;

        FDustParams& P = D.P;
        P.MaxOpacity = 0.6f;
        P.Ambient = 0.10f;
        P.Brightness = (std::max)(0.0f, PortConfigFloat("Render", "ring_dust_brightness", 1.1f));
        P.Forward = 0.65f;       // ice: the glow against the sun
        P.ForwardWeight = 0.6f;
        P.Back = 0.25f;
        P.NoiseScale = (std::max)(100.0f, PortConfigFloat("Render", "ring_dust_noise_scale", 700.0f));
        P.Coverage = 0.45f;
        P.Softness = 0.25f;
        P.Clump = (std::max)(0.0f, (std::min)(1.0f, PortConfigFloat("Render", "ring_dust_clump", 0.85f)));
        P.Steps = 8;
        P.LodDistance = 1.0e9f;  // always sampled: the closed form has no hole
        D.ClearRadius = (std::max)(1.0f, PortConfigFloat("Render", "ring_dust_clear", 25.0f));
        D.FarDist = Outer * 8.0f;
        D.FarFade = Outer * 4.0f;

        // The colour: the ring's own, a little cooler like ice. The sun's light at the ring's centre.
        float const IceTint[3] = {0.90f, 0.93f, 1.0f};
        for (int I = 0; I < 3; ++I)
            D.Colour[I] = static_cast<float>(Clamp01((Tint != nullptr ? Tint[I] : 1.0f) * IceTint[I]));
        float Sun[4];
        float const Centre[3] = {ZonePos.x, ZonePos.y, ZonePos.z};
        float Rgb[3];
        if (FindSystemSunSphere(Sun) && FindSunLightColour(Sun, Centre, Rgb))
            for (int I = 0; I < 3; ++I)
                D.SunColour[I] = (std::max)(0.0f, Rgb[I]);

        // Where in the shared noise this ring samples: its position decides.
        uint32_t PosBits[3];
        memcpy(PosBits, Centre, sizeof(PosBits));
        uint64_t Seed = 0x7a1b9c0de5ull;
        for (int I = 0; I < 3; ++I)
            Seed = Hash(Seed ^ PosBits[I]);
        for (int I = 0; I < 3; ++I)
        {
            Seed = Hash(Seed);
            D.NoiseOffset[I] = static_cast<double>(Seed >> 11) * (32.0 / 9007199254740992.0);
        }
    }

    FDustField* EntryFor(FCliAsteroid const* Field)
    {
        auto const Found = G_Fields.find(Field);
        if (Found != G_Fields.end())
            return Found->second.get();
        static int const S_Auto = PortConfigInt("Render", "field_dust_auto", 0);
        if (S_Auto == 0 || Field->FlagF8 == 0)
            return nullptr;
        std::unique_ptr<FDustField>& Slot = G_Fields[Field];
        Slot.reset(new FDustField());
        return Slot.get();
    }

    // One field found by the visit, with its camera-relative centre and distance.
    struct FCandidate
    {
        FDustField* Dust;
        double Rel[3];
        double Distance;
        double Strength;
    };

    struct FVisit
    {
        double Cam[3];
        std::vector<FCandidate>* Out;
    };

    void Collect(FCliAsteroid* Field, void* Ctx)
    {
        FVisit* const Visit = static_cast<FVisit*>(Ctx);
        if (Field == nullptr || Field->Zone == nullptr)
            return;
        FDustField* const Dust = EntryFor(Field);
        if (Dust == nullptr)
            return;
        if (!Dust->bBuilt)
            BuildField(Field, *Dust);
        if (Dust->bBlocked)
            return;
        FCandidate Candidate;
        Candidate.Dust = Dust;
        for (int I = 0; I < 3; ++I)
            Candidate.Rel[I] = Dust->Anchor[I] - Visit->Cam[I];
        Candidate.Distance = std::sqrt(Candidate.Rel[0] * Candidate.Rel[0] + Candidate.Rel[1] * Candidate.Rel[1] +
                                       Candidate.Rel[2] * Candidate.Rel[2]);
        Candidate.Strength = Clamp01((Dust->FarDist - Candidate.Distance) / Dust->FarFade);
        if (Candidate.Strength <= 0.0)
            return;
        Visit->Out->push_back(Candidate);
    }

    // A world sphere's exact perspective rectangle in target UV (U0, V0, U1, V1), clipped to the
    // viewport -- nebula_volume.cpp's VolumeScreenRect from this file's own constants. V = the
    // sphere's centre in view space; the camera inside the sphere or level with it gives the whole
    // viewport. Returns false when nothing of it is on screen.
    bool SphereScreenRect(double const V[3], double Radius, float const* ViewRect, float const* ProjInv,
                          float* Rect)
    {
        Rect[0] = ViewRect[0];
        Rect[1] = ViewRect[1];
        Rect[2] = ViewRect[0] + ViewRect[2];
        Rect[3] = ViewRect[1] + ViewRect[3];
        const double Z = -V[2]; // the game's view looks down -z
        if (Z < -Radius)
            return false; // wholly behind the camera
        if (!(Z > Radius * 1.001) || !(ProjInv[0] > 0.0f) || !(ProjInv[1] > 0.0f))
            return true;
        const double Denom = Z * Z - Radius * Radius;
        double Ndc[2][2];
        for (int Axis = 0; Axis < 2; ++Axis)
        {
            // Tangent slopes s = a / z of the sphere: (a - s z)^2 = R^2 (1 + s^2).
            const double A = V[Axis];
            const double Root = Radius * std::sqrt((std::max)(0.0, A * A + Z * Z - Radius * Radius));
            Ndc[Axis][0] = (A * Z - Root) / Denom / ProjInv[Axis];
            Ndc[Axis][1] = (A * Z + Root) / Denom / ProjInv[Axis];
        }
        // ViewUv.x = (ndc + 1) / 2, ViewUv.y = (1 - ndc) / 2.
        const double U0 = (std::max)(0.0, (Ndc[0][0] + 1.0) * 0.5);
        const double U1 = (std::min)(1.0, (Ndc[0][1] + 1.0) * 0.5);
        const double V0 = (std::max)(0.0, (1.0 - Ndc[1][1]) * 0.5);
        const double V1 = (std::min)(1.0, (1.0 - Ndc[1][0]) * 0.5);
        if (!(U1 > U0) || !(V1 > V0))
            return false;
        Rect[0] = static_cast<float>(ViewRect[0] + U0 * ViewRect[2]);
        Rect[1] = static_cast<float>(ViewRect[1] + V0 * ViewRect[3]);
        Rect[2] = static_cast<float>(ViewRect[0] + U1 * ViewRect[2]);
        Rect[3] = static_cast<float>(ViewRect[1] + V1 * ViewRect[3]);
        return true;
    }

    // DrawFullscreenQuad over Rect only (target UV), widened to whole pixels plus Pad of them;
    // the same half-pixel placement, so every covered pixel samples exactly as before
    // (nebula_volume.cpp's DrawVolumeRect).
    bool DrawVolumeRect(IRPDrawEx* DrawEx, float const Rect[4], unsigned long Width, unsigned long Height,
                        int Pad)
    {
        if (Rect[0] <= 0.0f && Rect[1] <= 0.0f && Rect[2] >= 1.0f && Rect[3] >= 1.0f)
            return DrawEx->DrawFullscreenQuad() == GR_OK;
        const float W = static_cast<float>(Width), H = static_cast<float>(Height);
        const float X0 = static_cast<float>((std::max)(0, static_cast<int>(std::floor(Rect[0] * W)) - Pad)) / W;
        const float Y0 = static_cast<float>((std::max)(0, static_cast<int>(std::floor(Rect[1] * H)) - Pad)) / H;
        const float X1 =
            static_cast<float>((std::min)(static_cast<int>(Width), static_cast<int>(std::ceil(Rect[2] * W)) + Pad)) / W;
        const float Y1 =
            static_cast<float>((std::min)(static_cast<int>(Height), static_cast<int>(std::ceil(Rect[3] * H)) + Pad)) / H;
        if (!(X1 > X0) || !(Y1 > Y0))
            return true;
        const float HalfX = 1.0f / W, HalfY = 1.0f / H;
        const float Quad[4][5] = {
            {X0 * 2.0f - 1.0f - HalfX, 1.0f - Y0 * 2.0f + HalfY, 0.0f, X0, Y0},
            {X1 * 2.0f - 1.0f - HalfX, 1.0f - Y0 * 2.0f + HalfY, 0.0f, X1, Y0},
            {X0 * 2.0f - 1.0f - HalfX, 1.0f - Y1 * 2.0f + HalfY, 0.0f, X0, Y1},
            {X1 * 2.0f - 1.0f - HalfX, 1.0f - Y1 * 2.0f + HalfY, 0.0f, X1, Y1},
        };
        return DrawEx->DrawExPrimitiveUp(D3DPT_TRIANGLESTRIP, D3DFVF_XYZ | D3DFVF_TEX1, Quad, 4) == GR_OK;
    }

    // The march target: FP16 when the card has it, else 8-bit (the values are premultiplied
    // 0..1 light and a coverage, which fit). Made once; the pipeline keeps its size with the
    // back buffer.
    bool EnsureTarget(IRenderPipelineEx* Ex, float Scale)
    {
        if (G_Target != nullptr && G_TargetScale == Scale)
            return true;
        if (G_bTargetTried && G_Target == nullptr && G_TargetScale == Scale)
            return false;
        if (G_Target != nullptr)
        {
            Ex->DestroyExTexture(G_Target);
            G_Target = nullptr;
        }
        G_bTargetTried = true;
        G_TargetScale = Scale;
        FRPExCaps Caps;
        bool const bFloat16 = RenderEx::GetCaps(&Caps) && Caps.bFloat16Target != 0;
        FRPExRenderTargetDesc Desc;
        Desc.Width = 0;
        Desc.Height = 0;
        Desc.BackBufferScale = Scale;
        Desc.Format = bFloat16 ? RPExFormatA16B16G16R16F : RPExFormatA8R8G8B8;
        if (Ex->CreateExRenderTarget(&Desc, &G_Target) != GR_OK && bFloat16)
        {
            // FP16 refused: 8-bit RGBA.
            Desc.Format = RPExFormatA8R8G8B8;
            Ex->CreateExRenderTarget(&Desc, &G_Target);
        }
        return G_Target != nullptr;
    }
}

void FieldDustParseSection(FCliAsteroid* Field, INI_Reader& Reader)
{
    std::unique_ptr<FDustField>& Slot = G_Fields[Field];
    Slot.reset(new FDustField());
    FDustParams& P = Slot->P;
    while (Reader.read_value())
    {
        if (Reader.is_value("opacity"))
            P.Opacity = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("max_opacity"))
            P.MaxOpacity = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("color"))
        {
            P.bColor = true;
            for (int I = 0; I < 3; ++I)
                P.Color[I] = ReadColor255(Reader, I);
        }
        else if (Reader.is_value("ambient"))
            P.Ambient = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("brightness"))
            P.Brightness = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("forward"))
            P.Forward = (std::max)(0.0f, (std::min)(0.95f, static_cast<float>(Reader.get_value_float(0))));
        else if (Reader.is_value("forward_weight"))
            P.ForwardWeight = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("back"))
            P.Back = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("noise_scale"))
            P.NoiseScale = (std::max)(100.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("coverage"))
            P.Coverage = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("softness"))
            P.Softness = (std::max)(0.001f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("clump"))
            P.Clump = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("edge_softness"))
            P.EdgeSoftness = (std::max)(0.05f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("thickness"))
            P.Thickness = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("clear_radius"))
            P.ClearRadius = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("steps"))
            P.Steps = (std::max)(0, (std::min)(8, static_cast<int>(Reader.get_value_float(0))));
        else if (Reader.is_value("lod_distance"))
            P.LodDistance = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("far_dist"))
            P.FarDist = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("far_fade"))
            P.FarFade = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("exclude_zones"))
            P.bExcludeZones = Reader.get_value_float(0) != 0.0f;
    }
}

void FieldDustForget(FCliAsteroid const* Field)
{
    G_Fields.erase(Field);
}

bool FieldDustRingUpdate(Universe::IZone const* Zone, float Thickness, float Density, float const* Tint)
{
    if (Zone == nullptr || !RingGatesPass())
        return false;
    std::unique_ptr<FDustField>& Slot = G_Rings[Zone];
    if (!Slot)
        Slot.reset(new FDustField());
    FDustField& D = *Slot;
    if (!D.bBuilt)
        BuildRing(Zone, Thickness, Density, Tint, D);
    D.bSeen = true;
    return !D.bBlocked;
}

void FieldDustShutdown()
{
    IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
    if (Ex != nullptr)
    {
        if (G_MarchProgram != nullptr)
            Ex->DestroyExProgram(G_MarchProgram);
        if (G_CompositeProgram != nullptr)
            Ex->DestroyExProgram(G_CompositeProgram);
        if (G_Target != nullptr)
            Ex->DestroyExTexture(G_Target);
    }
    G_MarchProgram = nullptr;
    G_CompositeProgram = nullptr;
    G_bProgramsTried = false;
    G_Target = nullptr;
    G_bTargetTried = false;
    G_TargetScale = 0.0f;
    G_Fields.clear();
    G_Rings.clear();
}

void FieldDustDraw(ICamera* Cam, float Near, float Far, int Enclosure)
{
    if (Cam == nullptr || DALib::Pipeline == nullptr)
        return;
    // Asteroid fields and planetary rings have their own gates: a ring's dust does not depend on the
    // asteroid options, nor on the camera being outside a field's enclosure.
    bool const bFields = GatesPass(Enclosure);
    bool const bRings = !G_Rings.empty() && RingGatesPass();
    if (!bFields && !bRings)
        return;
    // Fields only take part when one has [FieldDust] or the auto switch can give one the defaults.
    static int const S_Auto = PortConfigInt("Render", "field_dust_auto", 0);
    if ((!bFields || (G_Fields.empty() && S_Auto == 0)) && !bRings)
        return;
    static float const S_Resolution =
        (std::max)(0.25f, (std::min)(1.0f, PortConfigFloat("Render", "field_dust_resolution", 0.5f)));

    IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
    IRPDrawEx* const DrawEx = RenderEx::GetDrawEx();
    FRPExTexture* SceneDepth = nullptr;
    if (Ex == nullptr || DrawEx == nullptr || Ex->GetSceneDepth(&SceneDepth) != GR_OK || SceneDepth == nullptr)
        return;

    // The fields in reach, nearest first.
    float const* const CamPosF = Cam->GetPosition();
    double const CamPos[3] = {CamPosF[0], CamPosF[1], CamPosF[2]};
    static std::vector<FCandidate> S_Fields;
    S_Fields.clear();
    FVisit Visit = {{CamPos[0], CamPos[1], CamPos[2]}, &S_Fields};
    if (bFields)
        CliAsteroidForEach(&Collect, &Visit);
    if (bRings)
    {
        // The rings drawn since the last frame (FieldDustRingUpdate); each is registered again the
        // next time it is drawn.
        for (auto& Item : G_Rings)
        {
            FDustField* const D = Item.second.get();
            if (!D->bSeen)
                continue;
            D->bSeen = false;
            if (D->bBlocked || !D->bBuilt)
                continue;
            FCandidate Candidate;
            Candidate.Dust = D;
            for (int I = 0; I < 3; ++I)
                Candidate.Rel[I] = D->Anchor[I] - CamPos[I];
            Candidate.Distance = std::sqrt(Candidate.Rel[0] * Candidate.Rel[0] + Candidate.Rel[1] * Candidate.Rel[1] +
                                           Candidate.Rel[2] * Candidate.Rel[2]);
            Candidate.Strength = Clamp01((D->FarDist - Candidate.Distance) / D->FarFade);
            if (Candidate.Strength > 0.0)
                S_Fields.push_back(Candidate);
        }
    }
    if (S_Fields.empty())
        return;
    std::sort(S_Fields.begin(), S_Fields.end(),
              [](FCandidate const& A, FCandidate const& B) { return A.Distance < B.Distance; });

    unsigned long FullWidth = 0;
    unsigned long FullHeight = 0;
    if (Ex->GetExTextureSize(SceneDepth, &FullWidth, &FullHeight) != GR_OK || FullWidth == 0 || FullHeight == 0)
        return;

    // Camera: projection and view rotation as space_haze.cpp / nebula_volume.cpp build them.
    float const* const View = Cam->GetViewTransform();
    double const Cot = 1.0 / std::tan(kPi / 180.0 * static_cast<double>(Cam->GetFovYDeg()));
    double const ScaleX = Cot / static_cast<double>(Cam->GetAspect());
    double const ScaleY = Cot;
    double const InvDepth = 1.0 / (static_cast<double>(Far) - static_cast<double>(Near));
    if (!(ScaleX != 0.0) || !(ScaleY != 0.0) || !std::isfinite(InvDepth) || !std::isfinite(ScaleX))
        return;

    float C[(kFirstFieldRegister + kMaxFields * kFieldRegisters) * 4];
    memset(C, 0, sizeof(C));
    Set4(&C[0], static_cast<float>(Far * InvDepth), static_cast<float>(-static_cast<double>(Far) * Near * InvDepth),
         1.0f, 0.0f);
    int const* const Vp = Cam->GetViewport();
    float const VpW = static_cast<float>(Vp[2] - Vp[0]);
    float const VpH = static_cast<float>(Vp[3] - Vp[1]);
    if (VpW > 0.0f && VpH > 0.0f)
        Set4(&C[4], static_cast<float>(Vp[0]) / FullWidth, static_cast<float>(Vp[1]) / FullHeight,
             VpW / FullWidth, VpH / FullHeight);
    else
        Set4(&C[4], 0.0f, 0.0f, 1.0f, 1.0f);
    // c2: 1/ScaleX, 1/ScaleY and half a full-res texel (the depth the march reads).
    Set4(&C[8], static_cast<float>(1.0 / ScaleX), static_cast<float>(1.0 / ScaleY), 0.5f / FullWidth,
         0.5f / FullHeight);
    for (int Row = 0; Row < 3; ++Row)
        Set4(&C[12 + Row * 4], View[Row * 3 + 0], View[Row * 3 + 1], View[Row * 3 + 2], 0.0f);

    // The sun's disc, camera-relative.
    float Sun[4];
    bool const bSun = FindSystemSunSphere(Sun);
    if (bSun)
        Set4(&C[28], static_cast<float>(Sun[0] - CamPos[0]), static_cast<float>(Sun[1] - CamPos[1]),
             static_cast<float>(Sun[2] - CamPos[2]), Sun[3]);
    else
        Set4(&C[28], 0.0f, 0.0f, 1.0f, 0.0f);

    // Four is a shader batch size, not a visibility cap. Dropping further fields here
    // made neighbouring clouds blink whenever camera rotation changed the first four.
    std::vector<FieldDustBatch::Batch> Batches;
    for (FCandidate const& Candidate : S_Fields)
    {
        FDustField const& D = *Candidate.Dust;
        FDustParams const& P = D.P;
        double V[3];
        for (int Row = 0; Row < 3; ++Row)
            V[Row] = Candidate.Rel[0] * View[Row * 3 + 0] + Candidate.Rel[1] * View[Row * 3 + 1] +
                     Candidate.Rel[2] * View[Row * 3 + 2];
        float FieldRect[4];
        if (!SphereScreenRect(V, static_cast<double>(D.MaxRadius) * 1.02, &C[4], &C[8], FieldRect))
            continue;
        float* const R = FieldDustBatch::Append(Batches, C, FieldRect);
        // The caster list and the reaches of the planets that can shade this zone (Decision 5).
        float CasterSphere[8] = {};
        float CasterReach[2] = {};
        float const ZoneCentre[3] = {static_cast<float>(D.Anchor[0]), static_cast<float>(D.Anchor[1]),
                                     static_cast<float>(D.Anchor[2])};
        int const Casters = bSun ? SolarShadowCasters(ZoneCentre, 3.0f * D.MaxRadius + 50000.0f, CasterSphere,
                                                      CasterReach, 2)
                                 : 0;

        Set4(&R[0], static_cast<float>(Candidate.Rel[0]), static_cast<float>(Candidate.Rel[1]),
             static_cast<float>(Candidate.Rel[2]), static_cast<float>(Candidate.Strength));
        for (int Row = 0; Row < 3; ++Row)
            Set4(&R[4 + Row * 4], D.Rows[Row][0], D.Rows[Row][1], D.Rows[Row][2], 0.0f);
        R[4 + 3] = Casters > 0 ? CasterReach[0] : 0.0f;
        R[8 + 3] = Casters > 1 ? CasterReach[1] : 0.0f;
        R[12 + 3] = D.ThicknessUnit;
        // The camera is farther than lod_distance from the zone surface: only the closed form.
        // The analytic distant LOD has no exclusion mask. Keep samples for fields with holes.
        int const Steps = D.bRing ? P.Steps : (D.ExclusionCount > 0 ? (std::max)(P.Steps, 6)
            : (Candidate.Distance - D.MaxRadius > P.LodDistance ? 0 : P.Steps));
        Set4(&R[16], D.Sigma, P.EdgeSoftness, P.Clump, static_cast<float>(Steps));
        // The noise origin: the camera in the zone's noise tiles plus the field's offset, wrapped in
        // double (the texture repeats, so only the fraction matters) to keep the floats small.
        float NoiseOrigin[3];
        for (int I = 0; I < 3; ++I)
        {
            double const Tile = (CamPos[I] - D.Anchor[I]) / P.NoiseScale + D.NoiseOffset[I];
            NoiseOrigin[I] = static_cast<float>(Tile - std::floor(Tile));
        }
        Set4(&R[20], NoiseOrigin[0], NoiseOrigin[1], NoiseOrigin[2], 1.0f / P.NoiseScale);
        Set4(&R[24], P.Coverage, P.Softness, D.ClearRadius, P.MaxOpacity);
        Set4(&R[28], D.Colour[0], D.Colour[1], D.Colour[2], P.Brightness);
        Set4(&R[32], D.SunColour[0], D.SunColour[1], D.SunColour[2], P.Ambient);
        Set4(&R[36], P.Forward, P.ForwardWeight, P.Back, bSun ? 1.0f : 0.0f);
        for (int Caster = 0; Caster < 2; ++Caster)
        {
            float* const Out = &R[40 + Caster * 4];
            if (Caster < Casters)
                Set4(Out, static_cast<float>(CasterSphere[Caster * 4 + 0] - CamPos[0]),
                     static_cast<float>(CasterSphere[Caster * 4 + 1] - CamPos[1]),
                     static_cast<float>(CasterSphere[Caster * 4 + 2] - CamPos[2]), CasterSphere[Caster * 4 + 3]);
            else
                Set4(Out, 0.0f, 0.0f, 0.0f, 0.0f);
        }
        // A ring: the last exclusion slot carries its profile (w = 2 marks it): the hole's radius over
        // the outer one, the softness of the hole's and of the outer edge.
        if (D.bRing)
            Set4(&R[(12 + 3 * 4) * 4], D.InnerRatio, 0.05f, 0.12f, 2.0f);
        for (int E = 0; E < D.ExclusionCount; ++E)
        {
            Universe::IZone const* Hole = D.Exclusions[E];
            Vector const& Pos = Hole->GetPos();
            float Rows[3][3];
            ZoneLocalRows(Hole, Rows);
            float* H = &R[(12 + E * 4) * 4];
            Set4(H, static_cast<float>(Pos.x - CamPos[0]), static_cast<float>(Pos.y - CamPos[1]),
                 static_cast<float>(Pos.z - CamPos[2]), 1.0f);
            for (int Axis = 0; Axis < 3; ++Axis)
                Set4(H + 4 + Axis * 4, Rows[Axis][0], Rows[Axis][1], Rows[Axis][2], 0.0f);
        }
    }
    // Nothing on screen: no pass.
    if (Batches.empty())
        return;

    if (!G_bProgramsTried)
    {
        G_bProgramsTried = true;
        Ex->CreateExProgram(RenderEx::GetExtraData(), kShader, "VSMain", "PSMarch", &G_MarchProgram);
        Ex->CreateExProgram(RenderEx::GetExtraData(), kShader, "VSMain", "PSComposite", &G_CompositeProgram);
    }
    FRPExTexture* const Noise = SpaceHazeEnsureNoise();
    if (G_MarchProgram == nullptr || G_CompositeProgram == nullptr || Noise == nullptr ||
        !EnsureTarget(Ex, S_Resolution))
        return;
    unsigned long LowWidth = 0;
    unsigned long LowHeight = 0;
    if (Ex->GetExTextureSize(G_Target, &LowWidth, &LowHeight) != GR_OK || LowWidth == 0 || LowHeight == 0)
        return;

    // Composite constants: c0 ProjZ, c1 the march target's size, c2 half a full-res texel and the
    // relative depth threshold of the depth-aware upsample.
    float Composite[3 * 4];
    memcpy(&Composite[0], &C[0], sizeof(float) * 4);
    Set4(&Composite[4], static_cast<float>(LowWidth), static_cast<float>(LowHeight), 1.0f / LowWidth,
         1.0f / LowHeight);
    Set4(&Composite[8], 0.5f / FullWidth, 0.5f / FullHeight, 0.1f, 0.0f);

    IRenderPipeline* const Pipe = DALib::Pipeline;
    int SavedEnable = 0, SavedSrc = 0, SavedDest = 0, SavedOp = 0;
    Pipe->GetRenderState(D3DRS_ALPHABLENDENABLE, &SavedEnable);
    Pipe->GetRenderState(D3DRS_SRCBLEND, &SavedSrc);
    Pipe->GetRenderState(D3DRS_DESTBLEND, &SavedDest);
    Pipe->GetRenderState(D3DRS_BLENDOP, &SavedOp);

    FRPExSamplerState Point = {RPExFilterPoint, RPExMipNone, RPExAddressClamp, RPExAddressClamp, RPExAddressClamp};
    FRPExSamplerState LinearWrap = {RPExFilterLinear, RPExMipNone, RPExAddressWrap, RPExAddressWrap,
                                    RPExAddressWrap};
    FRPExSamplerState LinearClamp = {RPExFilterLinear, RPExMipNone, RPExAddressClamp, RPExAddressClamp,
                                     RPExAddressClamp};

    // Pass 1: the march into the low-resolution target over the fields' screen rectangle; no clear
    // needed, the composite reads only inside it. Two texels of margin: its depth-aware taps.
    FRPExPassDesc Pass = {G_Target, 0, 0};
    if (Ex->BeginExPass(&Pass) != GR_OK)
        return;
    for (auto It = Batches.rbegin(); It != Batches.rend(); ++It)
    {
        FieldDustBatch::Batch const& B = *It;
        // A target must not remain sampled when the next batch writes into it.
        Ex->BindExTexture(2, nullptr, &LinearClamp);
        bool bOk = Ex->SetExRenderTarget(G_Target, 0) == GR_OK &&
                   Ex->BindExProgram(G_MarchProgram) == GR_OK && Ex->BindExTexture(0, SceneDepth, &Point) == GR_OK &&
                   Ex->BindExTexture(1, Noise, &LinearWrap) == GR_OK;
        if (!bOk) break;
        Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 0);
        Ex->SetExPixelConstants(0, B.Constants, kFirstFieldRegister + B.Count * kFieldRegisters);
        if (!DrawVolumeRect(DrawEx, B.Rect, LowWidth, LowHeight, 2)) break;

        // Composite farther batches first, premultiplied (ONE, INVSRCALPHA).
        bOk = Ex->SetExRenderTarget(nullptr, 0) == GR_OK && Ex->BindExProgram(G_CompositeProgram) == GR_OK &&
              Ex->BindExTexture(0, SceneDepth, &Point) == GR_OK && Ex->BindExTexture(2, G_Target, &LinearClamp) == GR_OK;
        if (!bOk) break;
        Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 1);
        Pipe->SetRenderState(D3DRS_SRCBLEND, D3DBLEND_ONE);
        Pipe->SetRenderState(D3DRS_DESTBLEND, D3DBLEND_INVSRCALPHA);
        Pipe->SetRenderState(D3DRS_BLENDOP, D3DBLENDOP_ADD);
        Ex->SetExPixelConstants(0, Composite, 3);
        if (!DrawVolumeRect(DrawEx, B.Rect, FullWidth, FullHeight, 1)) break;
    }
    Ex->EndExPass();
    Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, SavedEnable);
    Pipe->SetRenderState(D3DRS_SRCBLEND, SavedSrc);
    Pipe->SetRenderState(D3DRS_DESTBLEND, SavedDest);
    Pipe->SetRenderState(D3DRS_BLENDOP, SavedOp);
}

#else

void FieldDustParseSection(FCliAsteroid*, INI_Reader&) {}
void FieldDustForget(FCliAsteroid const*) {}
void FieldDustDraw(ICamera*, float, float, int) {}
void FieldDustShutdown() {}
bool FieldDustRingUpdate(Universe::IZone const*, float, float, float const*) { return false; }

#endif
