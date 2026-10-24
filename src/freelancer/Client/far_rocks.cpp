// Port-only (RP9) far rocks: the distant look of an asteroid field as thousands of lit rock
// impostors, coloured with the diffuse texture of the field's dynamic asteroids. See far_rocks.h
// and docs/re/asteroid_far_look.md.

#include "far_rocks.h"

#ifdef FREELANCER_RP9

#include "cli_asteroid.h"
#include "DALib.h"
#include "common_ini.h"
#include "common_misc.h" // ICamera
#include "common_universe.h"
#include "dacom.h"       // FDUMP
#include "engine_light.h" // EngineLightGetAmbientRgbBytes
#include "game_options.h"
#include "globals.h"     // GetClientElapsedTime
#include "nebula_volume.h"
#include "port_config.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/shading.h"       // ITextureLibrary2
#include "render_ex.h"
#include "solar_spheres.h"
#include "space_scene_obj_draw.h" // GetSpaceFieldEnclosure
#include "texture_shapes.h"       // FTexShape, TexShapeGetGpuHandle

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <windows.h> // GetTickCount

namespace
{
    char const kSource[] = "far_rocks.cpp";
    char const kShader[] = "SHADERS\\far_rocks.hlsl";
    // One DrawExPrimitiveUp call carries at most this many rocks (6 vertices each).
    int const kBatchRocks = 8192;
    int const kVolumeGrid = 24;
    int const kMaxClasses = 6;
    // Cells per axis of the build's walk, rocks per cell.
    int const kMaxCellsPerAxis = 96;
    int const kMaxRocksPerCell = 12;
    int const kMaxFarRocks = 20000;
    double const kPi = 3.14159265358979323846;

    // [FarRocks] as parsed; a negative value means "derive it at build time".
    struct FFarParams
    {
        int Count = 8000;
        float SizeMin = 15.0f;
        float SizeMax = 250.0f;
        float SizePower = 2.6f;
        float EdgeSoftness = 1.5f;
        float Thickness = -1.0f;
        float ClumpSize = -1.0f;
        float ClumpCoverage = 0.45f;
        float ClumpSoftness = 0.15f;
        float ClumpAmount = 0.7f;
        float StartDist = -1.0f;
        float StartFade = -1.0f;
        float FarDist = -1.0f;
        float FarFade = -1.0f;
        bool bColor = false;
        float ColorA[3] = {0.0f, 0.0f, 0.0f};
        float Brightness = 1.0f;
        float Ambient = 1.0f; // scale of the system ambient at the field
        float MinPixels = 1.5f;
        // solid_pixels: a rock at least this many pixels across in radius is drawn solid (depth
        // written, its rim cut at half cover); smaller ones are soft dots without depth -- a cut
        // rim on a rock of a few pixels sparkles as it moves, and a written dot would punch holes.
        float SolidPixels = 4.0f;
        float Lump = 0.25f;   // how far the outline departs from a circle
        float Bump = 0.5f;    // surface normal bumpiness
        float TextureScale = 1.0f; // the texture's repeats over a rock's face
        bool bDynTexture = true;   // wear the field's dynamic asteroids' diffuse texture
        bool bReplaceBand = true;
    };

    // One rock as the build finds it.
    struct FRock
    {
        float Off[3]; // relative to the zone's centre, world axes
        float Radius;
        float Seed;   // 0..1
        uint8_t TexIndex; // which of the field's dynamic textures the rock wears
        uint8_t Jitter;
        uint8_t Class;
    };

    // A rock corner as drawn: FVF XYZ | DIFFUSE | TEX1. Diffuse: A texture index times 85, R
    // brightness jitter, G / B the corner (0 / 255). Tex: radius, seed.
    struct FRockVertex
    {
        float X, Y, Z;
        uint32_t Diffuse;
        float Radius;
        float Seed;
    };
    static_assert(sizeof(FRockVertex) == 24, "rock vertex is 24 bytes");

    struct FClassRange
    {
        int End;       // rocks [previous End, End) belong to the class
        float RadiusHi;
    };

    struct FFarField
    {
        FFarParams P;
        bool bBuilt = false;
        bool bFailed = false;
        // Resolved at build.
        double Anchor[3] = {0.0, 0.0, 0.0};
        float MaxRadius = 0.0f;
        float StartDist = 0.0f;
        float StartFade = 0.0f;
        float FarDist = 0.0f;
        float FarFade = 0.0f;
        float Tint[3] = {0.5f, 0.5f, 0.5f}; // the albedo of a rock without a texture
        // The diffuse textures of the field's dynamic asteroids (library records this field holds a
        // reference to) and the tint each is multiplied by.
        int TexCount = 0;
        FTextureRef Tex[4];
        float TexTint[4][3] = {};
        // The field's light, made on the CPU (UpdateLighting): the sun, its colour at the field, the
        // planets' shadow at the field's centre, the system ambient.
        bool bHasSun = false;
        float SunPos[3] = {0.0f, 0.0f, 0.0f};
        float SunDir[3] = {0.0f, 1.0f, 0.0f}; // unit, field to sun
        float SunColour[3] = {1.0f, 1.0f, 1.0f};
        float Sunlit = 1.0f;
        float AmbientTint[3] = {1.0f, 1.0f, 1.0f}; // the field's ambient tint times ambient_intensity
        float AmbientRgb[3] = {0.0f, 0.0f, 0.0f};
        unsigned SunFrame = 0;                     // the frame the sun terms were made
        int RockCount = 0;
        std::vector<FRockVertex> Verts; // 6 per rock, the biggest class first
        // The same vertices in a static GPU buffer (far_rocks_static_vb), uploaded once.
        FRPExBuffer* Vb = nullptr;
        bool bVbBad = false; // a draw from it failed: the upload path from here on
        std::vector<FClassRange> Classes;
    };

    std::map<FCliAsteroid const*, std::unique_ptr<FFarField>> G_Fields;

    FRPExProgram* G_Program = nullptr;
    bool G_bProgramTried = false;

    // The vertex format of a rock corner (see FRockVertex).
    unsigned long const kRockFvf = D3DFVF_XYZ | D3DFVF_DIFFUSE | D3DFVF_TEX1;

    void ReleaseVb(FFarField& F)
    {
        if (F.Vb == nullptr)
            return;
        IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
        if (Ex != nullptr)
            Ex->DestroyExVertexBuffer(F.Vb);
        F.Vb = nullptr;
    }

    // Gives the texture records back. The library may be gone already at shutdown: then the
    // pointers are only dropped.
    void ReleaseTextures(FFarField& F)
    {
        for (FTextureRef& Ref : F.Tex)
        {
            if (Ref.Texture != nullptr && DALib::TextureLib != nullptr)
                DALib::TextureLib->ReleaseTextureRecord(Ref.Texture);
            Ref.Texture = nullptr;
        }
        F.TexCount = 0;
    }

    // Uploads a built field's vertices once (port.ini [Render] far_rocks_static_vb, default 1); the
    // upload path stays as the fallback when the pipeline refuses.
    void UploadVb(FFarField& F)
    {
        static int const S_StaticVb = PortConfigInt("Render", "far_rocks_static_vb", 1);
        IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
        if (S_StaticVb == 0 || Ex == nullptr || F.Verts.empty() || F.Vb != nullptr)
            return;
        if (Ex->CreateExVertexBuffer(static_cast<unsigned long>(F.Verts.size() * sizeof(FRockVertex)),
                                     &F.Verts[0], &F.Vb) != GR_OK)
            F.Vb = nullptr;
    }

    // -- the hash and the clump field: space_layers.cpp's (that file's helpers are file-local)
    uint64_t Hash(uint64_t X)
    {
        X += 0x9e3779b97f4a7c15ull;
        X = (X ^ (X >> 30)) * 0xbf58476d1ce4e5b9ull;
        X = (X ^ (X >> 27)) * 0x94d049bb133111ebull;
        return X ^ (X >> 31);
    }

    uint64_t Mix(uint64_t State, uint64_t Value)
    {
        return Hash(State ^ Hash(Value));
    }

    // [0, 1) from the top 24 bits.
    double Unit(uint64_t H)
    {
        return static_cast<double>(H >> 40) * (1.0 / 16777216.0);
    }

    double Smooth(double T)
    {
        return T * T * (3.0 - 2.0 * T);
    }

    double Clamp01(double T)
    {
        return T < 0.0 ? 0.0 : (T > 1.0 ? 1.0 : T);
    }

    double Lattice(int Ix, int Iy, int Iz, int Octave)
    {
        uint64_t H = Hash((static_cast<uint64_t>(static_cast<uint32_t>(Ix)) << 32) |
                          static_cast<uint64_t>(static_cast<uint32_t>(Iy)));
        H = Hash(H ^ (static_cast<uint64_t>(static_cast<uint32_t>(Iz)) << 8) ^ static_cast<uint64_t>(Octave));
        return Unit(H);
    }

    double ValueNoise(double X, double Y, double Z, int Octave)
    {
        double const Fx = std::floor(X);
        double const Fy = std::floor(Y);
        double const Fz = std::floor(Z);
        int const Ix = static_cast<int>(Fx);
        int const Iy = static_cast<int>(Fy);
        int const Iz = static_cast<int>(Fz);
        double const Tx = Smooth(X - Fx);
        double const Ty = Smooth(Y - Fy);
        double const Tz = Smooth(Z - Fz);
        double Plane[2];
        for (int Dz = 0; Dz < 2; ++Dz)
        {
            double const A = Lattice(Ix, Iy, Iz + Dz, Octave);
            double const B = Lattice(Ix + 1, Iy, Iz + Dz, Octave);
            double const C = Lattice(Ix, Iy + 1, Iz + Dz, Octave);
            double const D = Lattice(Ix + 1, Iy + 1, Iz + Dz, Octave);
            double const Low = A + (B - A) * Tx;
            double const High = C + (D - C) * Tx;
            Plane[Dz] = Low + (High - Low) * Ty;
        }
        return Plane[0] + (Plane[1] - Plane[0]) * Tz;
    }

    double Fbm(double X, double Y, double Z)
    {
        double const Weights[3] = {0.5, 0.3, 0.2};
        double Scale = 1.0;
        double Sum = 0.0;
        for (int Octave = 0; Octave < 3; ++Octave)
        {
            Sum += Weights[Octave] * ValueNoise(X * Scale, Y * Scale, Z * Scale, Octave);
            Scale *= 2.03;
        }
        return Sum;
    }

    double Clump(double const* Pos, double ClumpSize, double Coverage, double Softness)
    {
        double const Noise = Fbm(Pos[0] / ClumpSize, Pos[1] / ClumpSize, Pos[2] / ClumpSize);
        double const Low = Coverage - Softness;
        double const High = Coverage + Softness;
        return Smooth(Clamp01((Noise - Low) / (High - Low)));
    }

    // -- the zone's frame: nebula_volume.cpp's ZoneRadii (that file's helpers are file-local)
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

    // The zone's local axis k in world axes (column k of its orientation).
    void ZoneAxis(Universe::IZone const* Zone, int Axis, double* Out)
    {
        const Matrix& Orientation = Zone->GetOrientation();
        Out[0] = Orientation.E[0][Axis];
        Out[1] = Orientation.E[1][Axis];
        Out[2] = Orientation.E[2][Axis];
    }

    // The relative weight of the rock density at a zone-local position: the ellipsoid profile
    // (1 - |q|^2)^e, a slab about the local XZ plane, and the clump field.
    struct FDensity
    {
        double Radii[3] = {1.0, 1.0, 1.0};
        double Edge = 1.5;
        double Thickness = 0.0;
        double ClumpSize = 1.0;
        double Coverage = 0.45;
        double Softness = 0.15;
        double Amount = 0.7;
        double ClumpOffset[3] = {0.0, 0.0, 0.0};

        double Profile(double const* P) const
        {
            double const Qx = P[0] / Radii[0], Qy = P[1] / Radii[1], Qz = P[2] / Radii[2];
            double const Q2 = Qx * Qx + Qy * Qy + Qz * Qz;
            if (!(Q2 < 1.0))
                return 0.0;
            double W = std::pow(1.0 - Q2, Edge);
            if (Thickness > 0.0)
            {
                double const T = P[1] / Thickness;
                W *= Clamp01(1.0 - T * T);
            }
            return W;
        }

        // The largest the profile gets in the cube [Lo, Lo + Size]^3: at its point nearest the
        // centre of the zone.
        double ProfileBound(double const* Lo, double Size) const
        {
            double Q2 = 0.0;
            double NearestY = 0.0;
            for (int A = 0; A < 3; ++A)
            {
                double const Low = Lo[A], High = Lo[A] + Size;
                double const Nearest = (Low <= 0.0 && High >= 0.0) ? 0.0 : (std::min)(std::fabs(Low), std::fabs(High));
                if (A == 1)
                    NearestY = Nearest;
                Q2 += (Nearest / Radii[A]) * (Nearest / Radii[A]);
            }
            if (!(Q2 < 1.0))
                return 0.0;
            double W = std::pow(1.0 - Q2, Edge);
            if (Thickness > 0.0)
            {
                double const T = NearestY / Thickness;
                W *= Clamp01(1.0 - T * T);
            }
            return W;
        }

        double ClumpFactor(double const* P) const
        {
            if (Amount <= 0.0)
                return 1.0;
            double const Shifted[3] = {P[0] + ClumpOffset[0], P[1] + ClumpOffset[1], P[2] + ClumpOffset[2]};
            return (1.0 - Amount) + Amount * Clump(Shifted, ClumpSize, Coverage, Softness);
        }

        double Weight(double const* P) const
        {
            double const W = Profile(P);
            return W > 0.0 ? W * ClumpFactor(P) : 0.0;
        }
    };

    bool GatesPass()
    {
        static int const S_Enabled = PortConfigInt("Render", "far_rocks", 1);
        if (S_Enabled == 0 || !RenderEx::IsAvailable())
            return false;
        // The band's own gates.
        if (GetGameOption(kGameOptEffectsGroup) == 0 || GetGameOption(kGameOptAsteroids) == 0)
            return false;
        int const Ext = GetGameOption(kGameOptAsteroidExt);
        if (Ext < 1 || Ext > 2)
            return false;
        FRPExCaps Caps;
        if (!RenderEx::GetCaps(&Caps) || !Caps.bSceneDepth)
            return false;
        return true;
    }

    FFarField* EntryFor(FCliAsteroid const* Field, bool bCreateAuto)
    {
        auto const Found = G_Fields.find(Field);
        if (Found != G_Fields.end())
            return Found->second.get();
        static int const S_Auto = PortConfigInt("Render", "far_rocks_auto", 0);
        if (!bCreateAuto || S_Auto == 0 || Field->FlagF8 == 0)
            return nullptr;
        std::unique_ptr<FFarField>& Slot = G_Fields[Field];
        Slot.reset(new FFarField());
        return Slot.get();
    }

    // The fog of a nebula over the field lays over the rocks: they draw only while the volume does
    // the fogging, else the field keeps the retail band. Inside a field enclosure they draw only
    // under the volume as well.
    bool BlockedByFog(FCliAsteroid const* Field, int Enclosure)
    {
        if (Enclosure != 0 && !NebulaVolume::IsActive())
            return true;
        // Retail's nebula lookup at the zone's centre (CliAsteroidUpdate, once).
        FNebulaEffect const* const Nebula =
            reinterpret_cast<FNebulaEffect const*>(static_cast<uintptr_t>(Field->ZeroD4));
        if (Field->FlagD3 != 0 || Nebula != nullptr)
            return Nebula == nullptr || !NebulaVolume::IsActiveFor(Nebula);
        return false;
    }

    // Frames between two makings of a field's sun terms (the sun does not move and the planets
    // barely do; the ambient is read every frame).
    unsigned const kSunRefreshFrames = 16;

    // The whole field's light, once per field instead of per rock or per pixel: the sun's direction
    // from the zone's centre, its colour there, the planets' shadow at the centre, and the system
    // ambient (the value the field's own asteroids and billboards are lit with).
    void UpdateLighting(FFarField& F, unsigned Frame, bool bForce)
    {
        unsigned char Ambient[3];
        EngineLightGetAmbientRgbBytes(Ambient);
        for (int I = 0; I < 3; ++I)
            F.AmbientRgb[I] = (static_cast<float>(Ambient[I]) / 255.0f) * F.AmbientTint[I] * F.P.Ambient;
        if (!bForce && Frame - F.SunFrame < kSunRefreshFrames)
            return;
        F.SunFrame = Frame;
        float Sun[4];
        F.bHasSun = FindSystemSunSphere(Sun);
        if (!F.bHasSun)
            return;
        float const Centre[3] = {static_cast<float>(F.Anchor[0]), static_cast<float>(F.Anchor[1]),
                                 static_cast<float>(F.Anchor[2])};
        F.SunPos[0] = Sun[0];
        F.SunPos[1] = Sun[1];
        F.SunPos[2] = Sun[2];
        double Dir[3] = {Sun[0] - F.Anchor[0], Sun[1] - F.Anchor[1], Sun[2] - F.Anchor[2]};
        double const Length = std::sqrt(Dir[0] * Dir[0] + Dir[1] * Dir[1] + Dir[2] * Dir[2]);
        if (Length > 1.0)
        {
            for (int I = 0; I < 3; ++I)
                F.SunDir[I] = static_cast<float>(Dir[I] / Length);
        }
        float Rgb[3];
        if (FindSunLightColour(Sun, Centre, Rgb))
        {
            for (int I = 0; I < 3; ++I)
                F.SunColour[I] = (std::max)(0.0f, Rgb[I]);
        }
        F.Sunlit = static_cast<float>(Clamp01(SolarSunlitAt(Centre)));
    }

    // Generates the rocks of one field. Returns false when the field cannot have any.
    bool BuildField(FCliAsteroid const* Field, FFarField& F)
    {
        DWORD const StartTick = GetTickCount();
        FCliAsteroidFarInfo Info;
        if (!CliAsteroidGetFarInfo(Field, &Info))
            return false;
        Universe::IZone const* const Zone = Info.Zone;
        FFarParams const& P = F.P;

        // The zone's frame.
        float Radii[3];
        ZoneRadii(Zone, Radii);
        for (int I = 0; I < 3; ++I)
            Radii[I] = (std::max)(1.0f, Radii[I]);
        double Axis[3][3];
        for (int K = 0; K < 3; ++K)
            ZoneAxis(Zone, K, Axis[K]);
        Vector const& ZonePos = Zone->GetPos();
        F.Anchor[0] = ZonePos.x;
        F.Anchor[1] = ZonePos.y;
        F.Anchor[2] = ZonePos.z;
        F.MaxRadius = (std::max)(Radii[0], (std::max)(Radii[1], Radii[2]));

        // The defaults from the field's other sections.
        int const Count = (std::max)(500, (std::min)(kMaxFarRocks, P.Count));
        double const SizeMin = (std::max)(1.0, static_cast<double>(P.SizeMin));
        double const SizeMax = (std::max)(SizeMin, static_cast<double>(P.SizeMax));
        double SizePower = P.SizePower;
        if (SizePower < 1.001)
            SizePower = 1.001;
        double const Thickness = P.Thickness >= 0.0f ? P.Thickness : Info.MaxBandThickness;

        FDensity D;
        for (int I = 0; I < 3; ++I)
            D.Radii[I] = Radii[I];
        D.Edge = (std::max)(0.05f, P.EdgeSoftness);
        D.Thickness = Thickness;
        D.ClumpSize = P.ClumpSize > 1.0f ? P.ClumpSize : 0.35 * F.MaxRadius;
        D.Coverage = P.ClumpCoverage;
        D.Softness = (std::max)(0.001f, P.ClumpSoftness);
        D.Amount = Clamp01(P.ClumpAmount);

        // The field's seed: the zone's position, so it is the same every run and differs per field.
        uint32_t PosBits[3];
        float const PosF[3] = {ZonePos.x, ZonePos.y, ZonePos.z};
        memcpy(PosBits, PosF, sizeof(PosBits));
        uint64_t const FieldSeed = Mix(Mix(Mix(0x4fa2c0de5eedull, PosBits[0]), PosBits[1]), PosBits[2]);
        for (int I = 0; I < 3; ++I)
            D.ClumpOffset[I] = Unit(Mix(FieldSeed, 50 + I)) * 64.0 * D.ClumpSize;

        // Distances. With billboards the rocks take over where they end: asteroid_billboard.cpp
        // BillboardDraw keeps every rock within Float04 + Float00 of the camera (the sphere's centre
        // ahead plus its radius; the band mode's BandFar is the same sum) and fades its alpha out
        // over the last Float2C of it, so the rocks start at that sum minus the fade, and come in over
        // start_fade (20% of it) beyond: the two cross-fade, no gap.
        float Start = P.StartDist;
        if (!(Start > 0.0f))
        {
            if (Info.bHasBillboards && Info.BillboardCentre > 0.0f && Info.BillboardRadius > 0.0f)
                Start = (std::max)(Info.BillboardCentre,
                                   Info.BillboardCentre + Info.BillboardRadius - Info.BillboardFade);
            else
            {
                float const Cube = Info.bHasCubes ? Info.FillDist + 1.25f * Info.CubeSize : 0.0f;
                Start = (std::max)(1500.0f, (std::max)(1.1f * Info.MaxPlacementRadius, Cube));
            }
        }
        F.StartDist = Start;
        // A long fade-in (half the start distance) so the rocks come out of the distance softly.
        F.StartFade = P.StartFade > 0.0f ? P.StartFade : 0.5f * Start;
        float FarDist = P.FarDist;
        float FarFade = P.FarFade;
        if (!(FarDist > 0.0f))
            FarDist = (Info.bHasBand && Info.BandFade[3] > Info.BandFade[2]) ? Info.BandFade[3] : 70000.0f;
        if (!(FarFade > 0.0f))
            FarFade = (Info.bHasBand && Info.BandFade[3] > Info.BandFade[2]) ? Info.BandFade[3] - Info.BandFade[2]
                                                                            : 10000.0f;
        F.FarDist = FarDist;
        // Fade out over at least the last third of the reach: a short fade made the far rim pop.
        if (!(P.FarFade > 0.0f))
            FarFade = (std::max)(FarFade, FarDist / 3.0f);
        F.FarFade = (std::max)(1.0f, (std::min)(FarFade, FarDist));

        // Colours: the band's (else the billboards') color_shift times the field's diffuse tint.
        float Diffuse[3] = {Info.Diffuse[0], Info.Diffuse[1], Info.Diffuse[2]};
        if (Diffuse[0] + Diffuse[1] + Diffuse[2] < 0.01f)
            Diffuse[0] = Diffuse[1] = Diffuse[2] = 1.0f;
        float Shift[3] = {0.55f, 0.5f, 0.45f};
        if (Info.bHasBand)
            memcpy(Shift, Info.BandColor, sizeof(Shift));
        else if (Info.bHasBillboards)
            memcpy(Shift, Info.BillboardColor, sizeof(Shift));
        for (int I = 0; I < 3; ++I)
            F.Tint[I] = P.bColor ? P.ColorA[I] : static_cast<float>(Clamp01(Shift[I] * Diffuse[I]));

        // The textures: the diffuse texture of each dynamic asteroid of the field (the material of
        // its archetype's mesh, see CliAsteroidGetFarInfo), tinted as that manager tints its
        // rocks; [FarRocks] color replaces the tints. No dynamic asteroid, no texture: the tint
        // colour alone, as before.
        ReleaseTextures(F);
        std::string TextureNames;
        if (P.bDynTexture)
        {
            for (int I = 0; I < Info.DynTextureCount && F.TexCount < 4; ++I)
            {
                FTextureRef& Ref = F.Tex[F.TexCount];
                if (!TextureRefLoad(&Ref, Info.DynTexture[I]))
                    continue;
                float const* const Source = Info.DynTint[I];
                bool const bUnset = Source[0] + Source[1] + Source[2] < 0.01f;
                for (int C = 0; C < 3; ++C)
                    F.TexTint[F.TexCount][C] = P.bColor ? P.ColorA[C]
                                                        : static_cast<float>(Clamp01(bUnset ? 1.0f : Source[C]));
                if (!TextureNames.empty())
                    TextureNames += ", ";
                TextureNames += Info.DynTexture[I];
                ++F.TexCount;
            }
        }
        if (TextureNames.empty())
            TextureNames = "none (tint colour)";

        // The system ambient scale as the field's billboards take it (ambient_intensity times the
        // field's ambient tint); a field with only a band takes the band's.
        float const Intensity = Info.bHasBillboards ? Info.BillboardAmbient : (Info.bHasBand ? Info.BandAmbient : 1.0f);
        for (int I = 0; I < 3; ++I)
            F.AmbientTint[I] = (std::max)(0.0f, Intensity * Info.Ambient[I]);
        if (F.AmbientTint[0] + F.AmbientTint[1] + F.AmbientTint[2] < 0.001f)
            F.AmbientTint[0] = F.AmbientTint[1] = F.AmbientTint[2] = (std::max)(0.0f, Intensity);
        UpdateLighting(F, 0, true);

        // The box of the walk, and the effective volume: the weight summed over a coarse grid.
        double Box[3] = {Radii[0], Radii[1], Radii[2]};
        if (Thickness > 0.0)
            Box[1] = (std::min)(Box[1], Thickness);
        double Veff = 0.0;
        {
            double const Voxel = (2.0 * Box[0] / kVolumeGrid) * (2.0 * Box[1] / kVolumeGrid) *
                                 (2.0 * Box[2] / kVolumeGrid);
            for (int Iz = 0; Iz < kVolumeGrid; ++Iz)
                for (int Iy = 0; Iy < kVolumeGrid; ++Iy)
                    for (int Ix = 0; Ix < kVolumeGrid; ++Ix)
                    {
                        double const Pt[3] = {(-1.0 + (Ix + 0.5) * 2.0 / kVolumeGrid) * Box[0],
                                              (-1.0 + (Iy + 0.5) * 2.0 / kVolumeGrid) * Box[1],
                                              (-1.0 + (Iz + 0.5) * 2.0 / kVolumeGrid) * Box[2]};
                        Veff += D.Weight(Pt) * Voxel;
                    }
        }
        if (!(Veff > 0.0))
            return false;

        // Size classes: edges geometric, the share of each from the power law r^-q.
        int Classes = static_cast<int>(std::ceil(std::log(SizeMax / SizeMin) / std::log(2.0)));
        Classes = (std::max)(1, (std::min)(kMaxClasses, Classes));
        double Edges[kMaxClasses + 1];
        for (int J = 0; J <= Classes; ++J)
            Edges[J] = SizeMin * std::pow(SizeMax / SizeMin, static_cast<double>(J) / Classes);
        double const Expo = 1.0 - SizePower;
        double Share[kMaxClasses];
        double ShareSum = 0.0;
        for (int J = 0; J < Classes; ++J)
        {
            Share[J] = (std::pow(Edges[J], Expo) - std::pow(Edges[J + 1], Expo)) / (SizePower - 1.0);
            ShareSum += Share[J];
        }
        if (!(ShareSum > 0.0))
            return false;

        // The cell walk, one pass per class: cells of c (zone-local integer grid), K rocks each
        // from the expected number, thinned to the weight at the rock.
        std::vector<FRock> Rocks;
        Rocks.reserve(static_cast<size_t>(Count) * 12 / 10 + 64);
        size_t CellsTotal = 0;
        double const MaxHalf = (std::max)(Box[0], (std::max)(Box[1], Box[2]));
        for (int J = 0; J < Classes; ++J)
        {
            double const Density = Count * (Share[J] / ShareSum) / Veff; // rocks per m^3 at weight 1
            if (!(Density > 0.0))
                continue;
            double Cell = std::cbrt(1.5 / Density);
            Cell = (std::max)(Cell, 2.0 * Edges[J + 1]);
            Cell = (std::max)(Cell, 2.0 * MaxHalf / kMaxCellsPerAxis);
            int Lo[3], Hi[3];
            for (int A = 0; A < 3; ++A)
            {
                Lo[A] = static_cast<int>(std::floor(-Box[A] / Cell));
                Hi[A] = static_cast<int>(std::ceil(Box[A] / Cell));
            }
            double const CellVolume = Cell * Cell * Cell;
            double const InvA = std::pow(Edges[J], Expo);
            double const InvB = std::pow(Edges[J + 1], Expo);
            for (int Iz = Lo[2]; Iz < Hi[2]; ++Iz)
                for (int Iy = Lo[1]; Iy < Hi[1]; ++Iy)
                    for (int Ix = Lo[0]; Ix < Hi[0]; ++Ix)
                    {
                        ++CellsTotal;
                        // The profile at the cell's point nearest the centre bounds the weight in it;
                        // the clump is taken at the cell's centre.
                        double const CellLo[3] = {Ix * Cell, Iy * Cell, Iz * Cell};
                        double const ProfileMax = D.ProfileBound(CellLo, Cell);
                        if (!(ProfileMax > 1.0e-4))
                            continue;
                        double const Centre[3] = {(Ix + 0.5) * Cell, (Iy + 0.5) * Cell, (Iz + 0.5) * Cell};
                        double const Wc = (std::max)(1.0e-3, ProfileMax * D.ClumpFactor(Centre));
                        uint64_t const CellHash =
                            Mix(Mix(Mix(Mix(FieldSeed, static_cast<uint64_t>(J)), static_cast<uint32_t>(Ix)),
                                    static_cast<uint32_t>(Iy)),
                                static_cast<uint32_t>(Iz));
                        double const Expected = Density * CellVolume * Wc;
                        int const Take = (std::min)(kMaxRocksPerCell,
                                                    static_cast<int>(std::floor(Expected + Unit(Hash(CellHash)))));
                        for (int K = 0; K < Take; ++K)
                        {
                            uint64_t R = Mix(CellHash, 100 + K);
                            double const Pos[3] = {(Ix + Unit(R = Hash(R))) * Cell,
                                                   (Iy + Unit(R = Hash(R))) * Cell,
                                                   (Iz + Unit(R = Hash(R))) * Cell};
                            double const Thin = Unit(R = Hash(R));
                            double const Weight = D.Weight(Pos);
                            if (!(Thin * Wc < Weight))
                                continue;
                            double const Radius =
                                std::pow(InvA - Unit(R = Hash(R)) * (InvA - InvB), 1.0 / Expo);
                            double Off[3];
                            for (int I = 0; I < 3; ++I)
                                Off[I] = Pos[0] * Axis[0][I] + Pos[1] * Axis[1][I] + Pos[2] * Axis[2][I];
                            Vector World;
                            World.x = static_cast<float>(F.Anchor[0] + Off[0]);
                            World.y = static_cast<float>(F.Anchor[1] + Off[1]);
                            World.z = static_cast<float>(F.Anchor[2] + Off[2]);
                            // The exclusion zones are holes in the field.
                            bool bExcluded = false;
                            for (int E = 0; E < Info.ExclusionCount && !bExcluded; ++E)
                                bExcluded = Info.Exclusion[E]->InZone(World, static_cast<float>(Radius));
                            if (bExcluded)
                                continue;
                            FRock Rock;
                            Rock.Off[0] = static_cast<float>(Off[0]);
                            Rock.Off[1] = static_cast<float>(Off[1]);
                            Rock.Off[2] = static_cast<float>(Off[2]);
                            Rock.Radius = static_cast<float>(Radius);
                            Rock.Seed = static_cast<float>(Unit(R = Hash(R)));
                            // Which dynamic texture the rock wears, and a small brightness jitter
                            // (the shader maps 0..255 to 0.85..1.1); the shader turns the lumps and
                            // the texture by the seed.
                            int const Pick = static_cast<int>(Unit(R = Hash(R)) * (std::max)(1, F.TexCount));
                            Rock.TexIndex = static_cast<uint8_t>((std::max)(0, (std::min)(F.TexCount - 1, Pick)));
                            Rock.Jitter = static_cast<uint8_t>(Unit(R = Hash(R)) * 255.0 + 0.5);
                            Rock.Class = static_cast<uint8_t>(J);
                            Rocks.push_back(Rock);
                        }
                    }
        }

        // Biggest class first, a class in seed order, so a prefix is a fair sample of it.
        std::sort(Rocks.begin(), Rocks.end(), [](FRock const& A, FRock const& B) {
            return A.Class != B.Class ? A.Class > B.Class : A.Seed < B.Seed;
        });
        size_t const Keep = static_cast<size_t>(Count) * 11 / 10;
        if (Rocks.size() > Keep)
            Rocks.resize(Keep);
        if (Rocks.empty())
            return false;

        F.RockCount = static_cast<int>(Rocks.size());
        F.Classes.clear();
        for (int J = Classes - 1; J >= 0; --J)
        {
            FClassRange Range;
            Range.RadiusHi = static_cast<float>(Edges[J + 1]);
            int End = F.Classes.empty() ? 0 : F.Classes.back().End;
            while (End < F.RockCount && Rocks[End].Class == J)
                ++End;
            Range.End = End;
            F.Classes.push_back(Range);
        }

        // Six vertices a rock: (-,-) (+,-) (+,+), (+,+) (-,+) (-,-).
        int const CornerX[6] = {0, 1, 1, 1, 0, 0};
        int const CornerY[6] = {0, 0, 1, 1, 1, 0};
        F.Verts.resize(static_cast<size_t>(F.RockCount) * 6);
        for (int I = 0; I < F.RockCount; ++I)
        {
            FRock const& Rock = Rocks[I];
            for (int V = 0; V < 6; ++V)
            {
                FRockVertex& Out = F.Verts[static_cast<size_t>(I) * 6 + V];
                Out.X = Rock.Off[0];
                Out.Y = Rock.Off[1];
                Out.Z = Rock.Off[2];
                Out.Diffuse = (static_cast<uint32_t>(Rock.TexIndex) * 85u << 24) | (static_cast<uint32_t>(Rock.Jitter) << 16) |
                              (static_cast<uint32_t>(CornerX[V] != 0 ? 255 : 0) << 8) |
                              static_cast<uint32_t>(CornerY[V] != 0 ? 255 : 0);
                Out.Radius = Rock.Radius;
                Out.Seed = Rock.Seed;
            }
        }
        FDUMP(0x100003, "%s(%d) : NOTICE:General:far rocks built: %d rocks, %d size classes, %lu cells, "
              "%lu ms (zone radii %.0f x %.0f x %.0f, slab %.0f, start %.0f + %.0f, texture %s)", kSource,
              __LINE__, F.RockCount, Classes, static_cast<unsigned long>(CellsTotal),
              static_cast<unsigned long>(GetTickCount() - StartTick), Radii[0], Radii[1], Radii[2],
              Thickness, F.StartDist, F.StartFade,
              TextureNames.c_str());
        return true;
    }

    // One field found by the visit, with its distance.
    struct FCandidate
    {
        FCliAsteroid* Field;
        FFarField* Far;
        double Distance;
    };

    struct FVisit
    {
        double Cam[3];
        int Enclosure;
        std::vector<FCandidate>* Out;
    };

    void Collect(FCliAsteroid* Field, void* Ctx)
    {
        FVisit* const Visit = static_cast<FVisit*>(Ctx);
        if (Field == nullptr || Field->Zone == nullptr)
            return;
        FFarField* const Far = EntryFor(Field, true);
        if (Far == nullptr || Far->bFailed || BlockedByFog(Field, Visit->Enclosure))
            return;
        Vector const& Pos = Field->Zone->GetPos();
        double const Dx = Visit->Cam[0] - Pos.x, Dy = Visit->Cam[1] - Pos.y, Dz = Visit->Cam[2] - Pos.z;
        double const Distance = std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
        float Radii[3];
        ZoneRadii(Field->Zone, Radii);
        double const Reach = Far->bBuilt ? Far->FarDist : 100000.0;
        if (Distance - (std::max)(Radii[0], (std::max)(Radii[1], Radii[2])) > Reach)
            return;
        FCandidate Candidate = {Field, Far, Distance};
        Visit->Out->push_back(Candidate);
    }

    void Set4(float* Out, float A, float B, float C, float D)
    {
        Out[0] = A;
        Out[1] = B;
        Out[2] = C;
        Out[3] = D;
    }

    float ReadColor255(INI_Reader& Reader, int I)
    {
        return static_cast<float>(Clamp01(Reader.get_value_float(I) / 255.0));
    }

    // The program, compiled on first use (the band skip asks before the first draw). False when the
    // pipeline has no Ex or the shader did not compile.
    bool EnsureProgram()
    {
        if (G_Program != nullptr)
            return true;
        if (G_bProgramTried)
            return false;
        IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
        if (Ex == nullptr)
            return false;
        G_bProgramTried = true;
        Ex->CreateExProgram(RenderEx::GetExtraData(), kShader, "VSMain", "PSMain", &G_Program);
        return G_Program != nullptr;
    }

    // The fields not built yet, built until the frame's budget is spent (the rest next frame; the
    // band is already hidden, FarRocksReplacesBand does not wait for the build).
    struct FBuildVisit
    {
        double ElapsedMs;
        int Built;
        int Pending;
    };

    double const kBuildBudgetMs = 100.0;

    void BuildPending(FCliAsteroid* Field, void* Ctx)
    {
        FBuildVisit* const Visit = static_cast<FBuildVisit*>(Ctx);
        if (Field == nullptr || Field->Zone == nullptr)
            return;
        FFarField* const Far = EntryFor(Field, true);
        if (Far == nullptr || Far->bBuilt || Far->bFailed)
            return;
        if (Visit->ElapsedMs >= kBuildBudgetMs)
        {
            ++Visit->Pending;
            return;
        }
        auto const Begin = std::chrono::steady_clock::now();
        Far->bBuilt = BuildField(Field, *Far);
        Far->bFailed = !Far->bBuilt;
        if (Far->bBuilt)
            UploadVb(*Far);
        Visit->ElapsedMs += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - Begin).count();
        ++Visit->Built;
    }
}

void FarRocksParseSection(FCliAsteroid* Field, INI_Reader& Reader)
{
    std::unique_ptr<FFarField>& Slot = G_Fields[Field];
    Slot.reset(new FFarField());
    FFarParams& P = Slot->P;
    while (Reader.read_value())
    {
        if (Reader.is_value("count"))
            P.Count = (std::max)(500, (std::min)(kMaxFarRocks, static_cast<int>(Reader.get_value_float(0))));
        else if (Reader.is_value("size"))
        {
            P.SizeMin = (std::max)(1.0f, static_cast<float>(Reader.get_value_float(0)));
            P.SizeMax = (std::max)(P.SizeMin, static_cast<float>(Reader.get_value_float(1)));
        }
        else if (Reader.is_value("size_power"))
            P.SizePower = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("edge_softness"))
            P.EdgeSoftness = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("thickness"))
            P.Thickness = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("clump_size"))
            P.ClumpSize = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("clump_coverage"))
            P.ClumpCoverage = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("clump_softness"))
            P.ClumpSoftness = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("clump_amount"))
            P.ClumpAmount = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("start_dist"))
            P.StartDist = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("start_fade"))
            P.StartFade = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("far_dist"))
            P.FarDist = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("far_fade"))
            P.FarFade = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("color"))
        {
            P.bColor = true;
            for (int I = 0; I < 3; ++I)
                P.ColorA[I] = ReadColor255(Reader, I);
        }
        else if (Reader.is_value("lump"))
            P.Lump = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("bump"))
            P.Bump = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("texture_scale"))
            P.TextureScale = (std::max)(0.05f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("dynamic_texture"))
            P.bDynTexture = Reader.get_value_float(0) != 0.0f;
        else if (Reader.is_value("brightness"))
            P.Brightness = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("ambient"))
            P.Ambient = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("min_pixels"))
            P.MinPixels = (std::max)(0.25f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("solid_pixels"))
            P.SolidPixels = (std::max)(0.5f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("replace_band"))
            P.bReplaceBand = Reader.get_value_float(0) != 0.0f;
    }
}

void FarRocksForget(FCliAsteroid const* Field)
{
    auto const Found = G_Fields.find(Field);
    if (Found == G_Fields.end())
        return;
    ReleaseVb(*Found->second);
    ReleaseTextures(*Found->second);
    G_Fields.erase(Found);
}

bool FarRocksReplacesBand(FCliAsteroid const* Field)
{
    // Whether the rocks are built yet does not matter: they are built before the first frame they
    // would draw in (FarRocksDrawAll builds every field at once), and the band must not come and
    // go with the camera. Only a program that did not compile, or a field that cannot have rocks,
    // keeps the band.
    if (!GatesPass() || !EnsureProgram())
        return false;
    FFarField const* const Far = EntryFor(Field, true);
    if (Far == nullptr || Far->bFailed || !Far->P.bReplaceBand)
        return false;
    return !BlockedByFog(Field, GetSpaceFieldEnclosure());
}

void FarRocksShutdown()
{
    IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
    if (Ex != nullptr && G_Program != nullptr)
        Ex->DestroyExProgram(G_Program);
    G_Program = nullptr;
    G_bProgramTried = false;
    for (auto& Entry : G_Fields)
    {
        ReleaseVb(*Entry.second);
        ReleaseTextures(*Entry.second);
    }
    G_Fields.clear();
}

void FarRocksDrawAll(ICamera* Cam, float Far, int Enclosure)
{
    if (Cam == nullptr || DALib::Pipeline == nullptr || !GatesPass())
        return;
    // Fields only take part when one has [FarRocks] or the auto switch can give one a default.
    static int const S_Auto = PortConfigInt("Render", "far_rocks_auto", 0);
    if (G_Fields.empty() && S_Auto == 0)
        return;
    static int const S_MaxTotal = PortConfigInt("Render", "far_rocks_max_total", 24000);
    static unsigned S_Frame = 0;
    ++S_Frame;

    // Every field is built as soon as it is known (its band is hidden from the start, see
    // FarRocksReplacesBand), within a time budget a frame.
    {
        static double S_BuildTotalMs = 0.0;
        static int S_BuiltTotal = 0;
        FBuildVisit Build = {0.0, 0, 0};
        CliAsteroidForEach(&BuildPending, &Build);
        if (Build.Built > 0)
        {
            S_BuildTotalMs += Build.ElapsedMs;
            S_BuiltTotal += Build.Built;
            FDUMP(0x100003, "%s(%d) : NOTICE:General:far rocks: built %d field(s) in %.1f ms this frame, %d in %.1f ms "
                  "in all, %d pending", kSource, __LINE__, Build.Built, Build.ElapsedMs, S_BuiltTotal,
                  S_BuildTotalMs, Build.Pending);
        }
    }

    IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
    IRPDrawEx* const DrawEx = RenderEx::GetDrawEx();
    FRPExTexture* SceneDepth = nullptr;
    if (Ex->GetSceneDepth(&SceneDepth) != GR_OK || SceneDepth == nullptr)
        return;
    if (!EnsureProgram())
        return;
    unsigned long FullWidth = 0;
    unsigned long FullHeight = 0;
    if (Ex->GetExTextureSize(SceneDepth, &FullWidth, &FullHeight) != GR_OK || FullWidth == 0 ||
        FullHeight == 0)
        return;

    // Camera: projection and view rotation as space_haze.cpp / nebula_volume.cpp build them.
    float const Near = Cam->GetZNear();
    float const* const CamPosF = Cam->GetPosition();
    double const CamPos[3] = {CamPosF[0], CamPosF[1], CamPosF[2]};
    float const* const View = Cam->GetViewTransform();
    double const Cot = 1.0 / std::tan(kPi / 180.0 * static_cast<double>(Cam->GetFovYDeg()));
    double const ScaleX = Cot / static_cast<double>(Cam->GetAspect());
    double const ScaleY = Cot;
    double const InvDepth = 1.0 / (static_cast<double>(Far) - static_cast<double>(Near));
    if (!(ScaleX != 0.0) || !(ScaleY != 0.0) || !std::isfinite(InvDepth) || !std::isfinite(ScaleX))
        return;
    int const* const Vp = Cam->GetViewport();
    float const VpW = static_cast<float>(Vp[2] - Vp[0]);
    float const VpH = static_cast<float>(Vp[3] - Vp[1]);
    double const PxPerUnit = ScaleY * (VpH > 0.0f ? VpH : static_cast<float>(FullHeight)) * 0.5;

    // The fields in reach, the nearest first.
    static std::vector<FCandidate> S_Fields;
    S_Fields.clear();
    FVisit Visit = {{CamPos[0], CamPos[1], CamPos[2]}, Enclosure, &S_Fields};
    CliAsteroidForEach(&Collect, &Visit);
    if (S_Fields.empty())
        return;
    std::sort(S_Fields.begin(), S_Fields.end(),
              [](FCandidate const& A, FCandidate const& B) { return A.Distance < B.Distance; });

    struct FDraw
    {
        FFarField* Far;
        int Rocks;
    };
    std::vector<FDraw> Draws;
    int Remaining = (std::max)(0, S_MaxTotal);
    for (FCandidate const& Candidate : S_Fields)
    {
        FFarField& F = *Candidate.Far;
        if (!F.bBuilt)
            continue;
        if (Remaining <= 0)
            break;
        double const ToRim = Candidate.Distance - F.MaxRadius;
        if (ToRim > F.FarDist)
            continue;
        // The size classes that can be seen from this near: a rock under a quarter of min_pixels
        // across is not worth its vertices.
        double const DNear = (std::max)(1.0, ToRim);
        int Include = 0;
        for (FClassRange const& Class : F.Classes)
        {
            if (Class.RadiusHi * PxPerUnit / DNear < 0.25 * F.P.MinPixels)
                break;
            Include = Class.End;
        }
        int const Rocks = (std::min)(Include, Remaining);
        if (Rocks <= 0)
            continue;
        FDraw Item = {&F, Rocks};
        Draws.push_back(Item);
        Remaining -= Rocks;
    }
    if (Draws.empty())
        return;

    // Camera-independent vertex constants.
    float V[9 * 4];
    memset(V, 0, sizeof(V));
    for (int Row = 0; Row < 3; ++Row)
        Set4(&V[4 + Row * 4], View[Row * 3 + 0], View[Row * 3 + 1], View[Row * 3 + 2], 0.0f);
    Set4(&V[16], static_cast<float>(ScaleX), static_cast<float>(ScaleY),
         static_cast<float>(static_cast<double>(Far) * InvDepth),
         static_cast<float>(-static_cast<double>(Far) * Near * InvDepth));
    if (VpW > 0.0f && VpH > 0.0f)
    {
        float const Sx = VpW / FullWidth;
        float const Sy = VpH / FullHeight;
        Set4(&V[20], Sx, Sy, 2.0f * Vp[0] / FullWidth + Sx - 1.0f, 1.0f - 2.0f * Vp[1] / FullHeight - Sy);
    }
    else
        Set4(&V[20], 1.0f, 1.0f, 0.0f, 0.0f);

    IRenderPipeline* const Pipe = DALib::Pipeline;
    int SavedEnable = 0, SavedSrc = 0, SavedDest = 0, SavedOp = 0;
    int SavedZWrite = 1;
    Pipe->GetRenderState(D3DRS_ZWRITEENABLE, &SavedZWrite);
    Pipe->GetRenderState(D3DRS_ALPHABLENDENABLE, &SavedEnable);
    Pipe->GetRenderState(D3DRS_SRCBLEND, &SavedSrc);
    Pipe->GetRenderState(D3DRS_DESTBLEND, &SavedDest);
    Pipe->GetRenderState(D3DRS_BLENDOP, &SavedOp);
    // The rocks are alpha blended and depth tested but write no depth: a rock fades smoothly, with
    // no screen door, and they need no sorting (small, alike in colour).
    FRPExPassDesc Pass = {nullptr, RPExPassKeepDepth, 0};
    if (Ex->BeginExPass(&Pass) != GR_OK)
        return;
    if (Ex->BindExProgram(G_Program) == GR_OK)
    {
        Pipe->SetRenderState(D3DRS_ZENABLE, 1);
        // Depth written: a nearer rock hides a farther one (blended without it they showed
        // through each other); the shader keeps every written pixel at least half covered.
        Pipe->SetRenderState(D3DRS_ZWRITEENABLE, 1);
        Pipe->SetRenderState(D3DRS_ZFUNC, 4); // LESSEQUAL
        Pipe->SetRenderState(D3DRS_CULLMODE, D3DCULL_NONE);
        Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 1);
        Pipe->SetRenderState(D3DRS_SRCBLEND, D3DBLEND_SRCALPHA);
        Pipe->SetRenderState(D3DRS_DESTBLEND, D3DBLEND_INVSRCALPHA);
        Pipe->SetRenderState(D3DRS_BLENDOP, D3DBLENDOP_ADD);
        // The rock textures wrap: each rock samples at a random offset.
        FRPExSamplerState const Sampler = {RPExFilterLinear, RPExMipLinear, RPExAddressWrap, RPExAddressWrap,
                                           RPExAddressWrap};
        for (FDraw const& Item : Draws)
        {
            FFarField& F = *Item.Far;
            FFarParams const& P = F.P;
            UpdateLighting(F, S_Frame, false);
            // The camera relative to the anchor in double, so the floats stay small.
            Set4(&V[0], static_cast<float>(CamPos[0] - F.Anchor[0]), static_cast<float>(CamPos[1] - F.Anchor[1]),
                 static_cast<float>(CamPos[2] - F.Anchor[2]), 0.0f);
            Set4(&V[24], static_cast<float>(Far), static_cast<float>(PxPerUnit), P.MinPixels,
                 1.0f - 1.0f / 4194304.0f);
            Set4(&V[28], F.StartDist, 1.0f / (std::max)(1.0f, F.StartFade), F.FarDist - F.FarFade,
                 1.0f / F.FarFade);
            // The pixel constants: the field's light (the sun's direction in view space, made here
            // once per field, not per rock) and the rocks' textures with their tints.
            float const Sun = F.bHasSun ? 1.0f : 0.0f;
            float const ViewSun[3] = {
                F.SunDir[0] * View[0] + F.SunDir[1] * View[1] + F.SunDir[2] * View[2],
                F.SunDir[0] * View[3] + F.SunDir[1] * View[4] + F.SunDir[2] * View[5],
                F.SunDir[0] * View[6] + F.SunDir[1] * View[7] + F.SunDir[2] * View[8]};
            // Without a sun the rocks are flat lit: the fill alone, as bright as a lit rock.
            float const Fill = F.bHasSun ? 0.0f : 0.6f;
            float const SunGain = Sun * F.Sunlit * P.Brightness;
            float Ps[8 * 4];
            memset(Ps, 0, sizeof(Ps));
            for (int I = 0; I < F.TexCount; ++I)
            {
                void* const Handle = TexShapeGetGpuHandle(&F.Tex[I], 0);
                bool const bBound = Handle != nullptr &&
                                    Ex->BindExPipelineTexture(static_cast<unsigned long>(I), Handle, &Sampler) == GR_OK;
                // A texture that cannot be bound leaves that rock kind on the tint colour.
                if (!bBound)
                    Ex->BindExPipelineTexture(static_cast<unsigned long>(I), nullptr, &Sampler);
                Set4(&Ps[I * 4], F.TexTint[I][0], F.TexTint[I][1], F.TexTint[I][2], bBound ? 1.0f : 0.0f);
            }
            Set4(&Ps[16], F.Tint[0], F.Tint[1], F.Tint[2], static_cast<float>(F.TexCount));
            Set4(&Ps[20], F.AmbientRgb[0] + Fill, F.AmbientRgb[1] + Fill, F.AmbientRgb[2] + Fill, P.Lump);
            Set4(&Ps[24], F.SunColour[0] * SunGain, F.SunColour[1] * SunGain, F.SunColour[2] * SunGain, P.Bump);
            Set4(&Ps[28], Sun > 0.5f ? ViewSun[0] : 0.0f, Sun > 0.5f ? ViewSun[1] : 0.0f,
                 Sun > 0.5f ? ViewSun[2] : 1.0f, P.TextureScale);
            Ex->SetExPixelConstants(0, Ps, 8);
            // Two passes over the same rocks (the vertex shader keeps one kind per pass): the solid
            // ones with depth written, then the soft dots without it.
            for (int Kind = 0; Kind < 2; ++Kind)
            {
                Pipe->SetRenderState(D3DRS_ZWRITEENABLE, Kind == 0 ? 1 : 0);
                Set4(&V[32], static_cast<float>(Kind), P.SolidPixels, 0.0f, 0.0f);
                Ex->SetExVertexConstants(0, V, 9);
                // One call from the static buffer (the contiguous prefix is the visible size
                // classes), else the rocks go up in batches.
                if (F.Vb != nullptr && !F.bVbBad)
                {
                    if (DrawEx->DrawExVertexBuffer(F.Vb, D3DPT_TRIANGLELIST, kRockFvf,
                                                   static_cast<unsigned long>(sizeof(FRockVertex)), 0,
                                                   static_cast<unsigned long>(Item.Rocks) * 2) == GR_OK)
                        continue;
                    F.bVbBad = true;
                }
                for (int First = 0; First < Item.Rocks; First += kBatchRocks)
                {
                    int const N = (std::min)(kBatchRocks, Item.Rocks - First);
                    DrawEx->DrawExPrimitiveUp(D3DPT_TRIANGLELIST, kRockFvf,
                                              &F.Verts[static_cast<size_t>(First) * 6],
                                              static_cast<unsigned long>(N) * 6);
                }
            }
        }
    }
    Ex->EndExPass();
    Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, SavedEnable);
    Pipe->SetRenderState(D3DRS_SRCBLEND, SavedSrc);
    Pipe->SetRenderState(D3DRS_DESTBLEND, SavedDest);
    Pipe->SetRenderState(D3DRS_BLENDOP, SavedOp);
    Pipe->SetRenderState(D3DRS_ZWRITEENABLE, SavedZWrite);
}

#else

void FarRocksParseSection(FCliAsteroid*, INI_Reader&) {}
void FarRocksForget(FCliAsteroid const*) {}
bool FarRocksReplacesBand(FCliAsteroid const*) { return false; }
void FarRocksDrawAll(ICamera*, float, int) {}
void FarRocksShutdown() {}

#endif
