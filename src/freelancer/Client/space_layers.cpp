// Port-only (RP9) space layers: world-anchored layers of camera-facing sprites that give open
// space depth. See space_layers.h and docs/re/space_layers.md.

#include "space_layers.h"

#ifdef FREELANCER_RP9

#include "DALib.h"
#include "common_ini.h"
#include "common_misc.h"
#include "dacom_iids.h"
#include "game_options.h"
#include "globals.h" // GetClientElapsedTime
#include "port_config.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/RenderPipeline.h"
#include "solar_spheres.h"
#include "star_sphere.h" // Win3DBindModelview / Win3DIdentityRotation3x3
#include "texture_panels.h"
#include "texture_shapes.h"
#include "part_cache.h" // FvfTexcoordBlockBytes

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

namespace
{
    int const kMaxLayers = 8;
    int const kMaxShapes = 8;
    // The most cells visited per axis: bigger shells enlarge the cell instead.
    int const kMaxCellsPerAxis = 24;
    double const kPi = 3.14159265358979323846;

    // One sprite found by the (cached) cell walk. Rel is relative to the layer's cache origin.
    struct FCand
    {
        uint64_t Seed; // the hash state after the placement draws: size, shape, colour... follow
        float Rel[3];
        float Size;
    };

    struct FSpaceLayer
    {
        std::unique_ptr<FShapeDB> Shapes;
        std::vector<std::string> ShapeNames;
        std::vector<FTexShape*> ShapePtrs;
        float ColorA[3] = {1.0f, 1.0f, 1.0f};
        float ColorB[3] = {1.0f, 1.0f, 1.0f};
        float Alpha = 0.06f;
        float SizeMin = 800.0f;
        float SizeMax = 2500.0f;
        double Near = 3000.0;
        double Far = 30000.0;
        double NearFade = 0.3;
        double FarFade = 0.3;
        double Cell = 0.0; // 0 = the default
        double Density = 1.5;
        double ClumpSize = 0.0; // 0 = the default
        double Coverage = 0.45;
        double Softness = 0.1;
        int Count = 300;
        bool Additive = false;
        bool Lit = true;
        double Ambient = 0.35;
        double Forward = 1.5;
        double Spin = 2.0;
        double RotationStep = 0.0;
        double Wind[3] = {0.0, 0.0, 0.0};

        // The candidate cache: the cell walk is the expensive part, so it is redone only when the
        // grid origin Q has moved CacheMargin from where it was built (the walk covers the shell
        // widened by that margin, the per-frame pass filters exactly).
        bool CacheValid = false;
        double CacheQ[3] = {0.0, 0.0, 0.0};
        double CacheMargin = 0.0;
        std::vector<FCand> Cands;
    };

    std::vector<std::unique_ptr<FSpaceLayer>> G_Layers;

    // splitmix64: deterministic (the same as the nebula puff layer's).
    uint64_t Hash(uint64_t X)
    {
        X += 0x9e3779b97f4a7c15ull;
        X = (X ^ (X >> 30)) * 0xbf58476d1ce4e5b9ull;
        X = (X ^ (X >> 27)) * 0x94d049bb133111ebull;
        return X ^ (X >> 31);
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

    // -- The clump field: the nebula puff layer's (cli_nebula.cpp NebulaLayerFbm / Clump), copied
    // because that file's helpers are file-local.
    double Lattice(int Ix, int Iy, int Iz, int Octave)
    {
        uint64_t H = Hash((static_cast<uint64_t>(static_cast<uint32_t>(Ix)) << 32) |
                          static_cast<uint64_t>(static_cast<uint32_t>(Iy)));
        H = Hash(H ^ (static_cast<uint64_t>(static_cast<uint32_t>(Iz)) << 8) ^ static_cast<uint64_t>(Octave));
        return Unit(H);
    }

    // 3D value noise, trilinear with a smoothstep fade, 0..1.
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

    // Three octaves (scale x2.03, weights 0.5 / 0.3 / 0.2), 0..1.
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

    // The masses (1) and the gaps between them (0): the noise through a smoothstep around the
    // coverage threshold.
    double Clump(double const* Pos, double ClumpSize, double Coverage, double Softness)
    {
        double const Noise = Fbm(Pos[0] / ClumpSize, Pos[1] / ClumpSize, Pos[2] / ClumpSize);
        double const Low = Coverage - Softness;
        double const High = Coverage + Softness;
        return Smooth(Clamp01((Noise - Low) / (High - Low)));
    }

    // FVF layout helpers (texture_panels.cpp keeps its own file-local; it exports these).
    struct FVertexLayout
    {
        int PosBytes;
        int DiffBytes;
        int Stride;
    };

    FVertexLayout LayoutOf(unsigned Fvf)
    {
        int const NormalBytes = (Fvf & 0x10) != 0 ? 0xc : 0;
        FVertexLayout L;
        L.DiffBytes = TexturePanelsFvfDiffuseNormalBytes(static_cast<unsigned char>(Fvf));
        L.PosBytes = TexturePanelsFvfPositionBytes(static_cast<unsigned char>(Fvf)) + NormalBytes;
        L.Stride = FvfTexcoordBlockBytes(Fvf) + L.PosBytes + L.DiffBytes;
        return L;
    }

    IRenderPipelineEx* PipelineEx()
    {
        static bool S_bAsked = false;
        static IRenderPipelineEx* S_Ex = nullptr;
        if (!S_bAsked && DALib::Pipeline != nullptr)
        {
            S_bAsked = true;
            if (DALib::Pipeline->QueryInterface(Iids::RenderPipelineEx, reinterpret_cast<void**>(&S_Ex)) >= 0 &&
                S_Ex != nullptr)
                S_Ex->Release(); // the pipeline outlives the layers
            else
                S_Ex = nullptr;
        }
        return S_Ex;
    }

    void ReadColor(INI_Reader& Reader, float* Out)
    {
        for (unsigned I = 0; I < 3; ++I)
            Out[I] = static_cast<float>(Clamp01(Reader.get_value_float(I) / 255.0));
    }

    // Fills the layer's cache: every sprite of the cells that reach the shell [Near - M, Far + M]
    // about Qc. Deterministic: a sprite depends only on its cell, its index and the layer.
    void BuildCache(FSpaceLayer& L, size_t LayerIndex, double const* Qc)
    {
        L.Cands.clear();
        L.CacheValid = true;
        L.CacheQ[0] = Qc[0];
        L.CacheQ[1] = Qc[1];
        L.CacheQ[2] = Qc[2];

        double const Margin = L.CacheMargin;
        double const NearR = (std::max)(0.0, L.Near - Margin);
        double const FarR = L.Far + Margin;
        double Cell = L.Cell;
        // Bounds the visited cells to kMaxCellsPerAxis^3.
        if (2.0 * FarR / Cell + 1.0 > kMaxCellsPerAxis)
            Cell = 2.0 * FarR / (kMaxCellsPerAxis - 1);

        int Lo[3];
        int Hi[3];
        for (int Axis = 0; Axis < 3; ++Axis)
        {
            Lo[Axis] = static_cast<int>(std::floor((Qc[Axis] - FarR) / Cell));
            Hi[Axis] = static_cast<int>(std::floor((Qc[Axis] + FarR) / Cell));
        }
        double const SizeSpan = static_cast<double>(L.SizeMax) - L.SizeMin;
        for (int Iz = Lo[2]; Iz <= Hi[2]; ++Iz)
        {
            for (int Iy = Lo[1]; Iy <= Hi[1]; ++Iy)
            {
                for (int Ix = Lo[0]; Ix <= Hi[0]; ++Ix)
                {
                    double const Origin[3] = {Ix * Cell, Iy * Cell, Iz * Cell};
                    // Nearest and farthest point of the cell's box from Qc.
                    double NearSq = 0.0;
                    double FarSq = 0.0;
                    for (int Axis = 0; Axis < 3; ++Axis)
                    {
                        double const Min = Origin[Axis];
                        double const Max = Origin[Axis] + Cell;
                        double const Delta = Qc[Axis] < Min ? Min - Qc[Axis] : (Qc[Axis] > Max ? Qc[Axis] - Max : 0.0);
                        double const Reach = (std::max)(std::fabs(Qc[Axis] - Min), std::fabs(Qc[Axis] - Max));
                        NearSq += Delta * Delta;
                        FarSq += Reach * Reach;
                    }
                    // Skip cells entirely outside the far sphere or entirely inside the near one.
                    if (!(NearSq < FarR * FarR))
                        continue;
                    if (FarSq < NearR * NearR)
                        continue;
                    double const Centre[3] = {Origin[0] + 0.5 * Cell, Origin[1] + 0.5 * Cell,
                                              Origin[2] + 0.5 * Cell};
                    double const CellClump = Clump(Centre, L.ClumpSize, L.Coverage, L.Softness);
                    int const PerCell = (std::min)(4, static_cast<int>(std::ceil(CellClump * L.Density * 2.0 - 0.25)));
                    if (PerCell <= 0)
                        continue;
                    for (int N = 0; N < PerCell; ++N)
                    {
                        uint64_t H = Hash((static_cast<uint64_t>(static_cast<uint32_t>(Ix)) << 32) |
                                          static_cast<uint64_t>(static_cast<uint32_t>(Iy)));
                        H = Hash(H ^ (static_cast<uint64_t>(static_cast<uint32_t>(Iz)) << 8) ^
                                 (static_cast<uint64_t>(N) << 4) ^ (static_cast<uint64_t>(LayerIndex) << 1));
                        H = Hash(H);
                        double const Ux = Unit(H);
                        H = Hash(H);
                        double const Uy = Unit(H);
                        H = Hash(H);
                        double const Uz = Unit(H);
                        H = Hash(H);
                        double const Uthin = Unit(H);
                        H = Hash(H);
                        double const Usize = Unit(H);
                        double const X[3] = {Origin[0] + Ux * Cell, Origin[1] + Uy * Cell, Origin[2] + Uz * Cell};
                        double const Dx = X[0] - Qc[0], Dy = X[1] - Qc[1], Dz = X[2] - Qc[2];
                        double const Dist = std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
                        if (Dist < NearR || Dist > FarR)
                            continue;
                        // Gaps inside a cell stay empty: thin by the clump at the sprite's own
                        // place relative to the cell's (whose level already set the count).
                        double const Ratio = Clump(X, L.ClumpSize, L.Coverage, L.Softness) / (std::max)(CellClump, 1.0e-3);
                        if (Uthin > Ratio)
                            continue;
                        FCand C;
                        C.Seed = H;
                        C.Rel[0] = static_cast<float>(Dx);
                        C.Rel[1] = static_cast<float>(Dy);
                        C.Rel[2] = static_cast<float>(Dz);
                        C.Size = static_cast<float>(L.SizeMin + SizeSpan * Usize);
                        L.Cands.push_back(C);
                    }
                }
            }
        }
    }

    struct FVisible
    {
        size_t Index; // into Cands
        float Rel[3]; // from the camera
        float Dist;
        float Depth; // along the view direction
    };

    struct FQuad
    {
        float Pos[4][3];
        float U[2], V[2]; // U0/U1, V0/V1 of the shape
        unsigned Diffuse;
        void* Texture;
        float Depth;
    };

    void DrawLayer(FSpaceLayer& L, size_t LayerIndex, ICamera* Cam, double const* P, double T, float const* SunDir,
                   bool bHasSun, std::vector<FVisible>& Visible, std::vector<FQuad>& Quads)
    {
        // The grid is evaluated at Q = P - wind * T and the sprites sit at their grid place + wind * T.
        double const Q[3] = {P[0] - L.Wind[0] * T, P[1] - L.Wind[1] * T, P[2] - L.Wind[2] * T};
        double const Moved = std::sqrt((Q[0] - L.CacheQ[0]) * (Q[0] - L.CacheQ[0]) +
                                       (Q[1] - L.CacheQ[1]) * (Q[1] - L.CacheQ[1]) +
                                       (Q[2] - L.CacheQ[2]) * (Q[2] - L.CacheQ[2]));
        if (!L.CacheValid || Moved > L.CacheMargin)
            BuildCache(L, LayerIndex, Q);
        double const Shift[3] = {Q[0] - L.CacheQ[0], Q[1] - L.CacheQ[1], Q[2] - L.CacheQ[2]};

        // Camera axes: columns of the 3x3 orientation; the view looks down -column 2.
        float const* const O = Cam->GetOrientation();
        float const Right[3] = {O[0], O[3], O[6]};
        float const Up[3] = {O[1], O[4], O[7]};
        float const Back[3] = {O[2], O[5], O[8]};

        Visible.clear();
        for (size_t I = 0; I < L.Cands.size(); ++I)
        {
            FCand const& C = L.Cands[I];
            float const Rx = static_cast<float>(C.Rel[0] - Shift[0]);
            float const Ry = static_cast<float>(C.Rel[1] - Shift[1]);
            float const Rz = static_cast<float>(C.Rel[2] - Shift[2]);
            float const Dist = std::sqrt(Rx * Rx + Ry * Ry + Rz * Rz);
            if (Dist < L.Near || Dist > L.Far)
                continue;
            float const Depth = -(Rx * Back[0] + Ry * Back[1] + Rz * Back[2]);
            // Wholly behind the camera.
            if (Depth + C.Size < 0.0f)
                continue;
            FVisible V;
            V.Index = I;
            V.Rel[0] = Rx;
            V.Rel[1] = Ry;
            V.Rel[2] = Rz;
            V.Dist = Dist;
            V.Depth = Depth;
            Visible.push_back(V);
        }
        // More than `count`: the nearest win.
        if (static_cast<int>(Visible.size()) > L.Count)
        {
            std::nth_element(Visible.begin(), Visible.begin() + L.Count, Visible.end(),
                             [](FVisible const& A, FVisible const& B) { return A.Dist < B.Dist; });
            Visible.resize(static_cast<size_t>(L.Count));
        }

        Quads.clear();
        double const SpinRad = L.Spin * (kPi / 180.0);
        double const Span = L.Far - L.Near;
        float const* const CamPos = Cam->GetPosition();
        for (FVisible const& V : Visible)
        {
            FCand const& C = L.Cands[V.Index];
            uint64_t H = Hash(C.Seed);
            size_t const ShapeIndex = static_cast<size_t>(Unit(H) * L.ShapePtrs.size()) % L.ShapePtrs.size();
            H = Hash(H);
            double const Mix = Unit(H);
            H = Hash(H);
            double const Urot = Unit(H);
            H = Hash(H);
            double const Jitter = 0.7 + 0.3 * Unit(H);
            H = Hash(H);
            double const Uspin = Unit(H) * 2.0 - 1.0;

            FTexShape const* const Shape = L.ShapePtrs[ShapeIndex];
            void* const Texture = TexShapeGetGpuHandle(Shape, 0);
            if (Texture == nullptr)
                continue;

            // Alpha ramps in from the near edge and out to the far one.
            double const S = (V.Dist - L.Near) / Span;
            double Fade = 1.0;
            if (L.NearFade > 0.0)
                Fade = (std::min)(Fade, Smooth(Clamp01(S / L.NearFade)));
            if (L.FarFade > 0.0)
                Fade = (std::min)(Fade, Smooth(Clamp01((1.0 - S) / L.FarFade)));
            double const Alpha = Clamp01(static_cast<double>(L.Alpha) * Fade * Jitter);
            if (Alpha < 0.004)
                continue;

            double Col[3];
            for (int K = 0; K < 3; ++K)
                Col[K] = L.ColorA[K] + (L.ColorB[K] - L.ColorA[K]) * Mix;
            if (L.Lit)
            {
                // Shadow of the planets, then the glow of looking through the sprite towards the sun.
                float const World[3] = {CamPos[0] + V.Rel[0], CamPos[1] + V.Rel[1], CamPos[2] + V.Rel[2]};
                double const Lit = L.Ambient + (1.0 - L.Ambient) * SolarSunlitAt(World);
                double Gain = Lit;
                if (bHasSun && V.Dist > 1.0e-3f)
                {
                    double const Dot = (V.Rel[0] * SunDir[0] + V.Rel[1] * SunDir[1] + V.Rel[2] * SunDir[2]) / V.Dist;
                    Gain *= 1.0 + L.Forward * std::pow((std::max)(0.0, Dot), 8.0);
                }
                for (int K = 0; K < 3; ++K)
                    Col[K] = Clamp01(Col[K] * Gain);
            }

            // The sprite's own turn: a fixed angle (or a multiple of rotation_step) plus its spin.
            double Angle = Urot * 2.0 * kPi;
            if (L.RotationStep > 0.0)
                Angle = std::floor(Urot * 360.0 / L.RotationStep) * L.RotationStep * (kPi / 180.0);
            Angle = std::fmod(Angle + SpinRad * Uspin * T, 2.0 * kPi);
            float const Cs = static_cast<float>(std::cos(Angle)) * C.Size;
            float const Sn = static_cast<float>(std::sin(Angle)) * C.Size;

            // View space (identity modelview): x right, y up, z back.
            float const Vx = V.Rel[0] * Right[0] + V.Rel[1] * Right[1] + V.Rel[2] * Right[2];
            float const Vy = V.Rel[0] * Up[0] + V.Rel[1] * Up[1] + V.Rel[2] * Up[2];
            float const Vz = -V.Depth;
            // Quad axes in the view plane: right (Cs, Sn), up (-Sn, Cs). Corners as the cloud
            // puffs have them: (-,-) U0 V0, (+,-) U1 V0, (+,+) U1 V1, (-,+) U0 V1.
            float const Ex[2] = {Cs, Sn};
            float const Ey[2] = {-Sn, Cs};
            float const Signs[4][2] = {{-1.0f, -1.0f}, {1.0f, -1.0f}, {1.0f, 1.0f}, {-1.0f, 1.0f}};
            FQuad Quad;
            for (int K = 0; K < 4; ++K)
            {
                Quad.Pos[K][0] = Vx + Signs[K][0] * Ex[0] + Signs[K][1] * Ey[0];
                Quad.Pos[K][1] = Vy + Signs[K][0] * Ex[1] + Signs[K][1] * Ey[1];
                Quad.Pos[K][2] = Vz;
            }
            Quad.U[0] = Shape->U0;
            Quad.U[1] = Shape->U1;
            Quad.V[0] = Shape->V0;
            Quad.V[1] = Shape->V1;
            unsigned const A = static_cast<unsigned>(Alpha * 255.0 + 0.5);
            unsigned const R = static_cast<unsigned>(Col[0] * 255.0 + 0.5);
            unsigned const G = static_cast<unsigned>(Col[1] * 255.0 + 0.5);
            unsigned const B = static_cast<unsigned>(Col[2] * 255.0 + 0.5);
            Quad.Diffuse = (A << 24) | (R << 16) | (G << 8) | B;
            Quad.Texture = Texture;
            Quad.Depth = V.Depth;
            Quads.push_back(Quad);
        }
        if (Quads.empty())
            return;

        // Alpha blending needs far to near; an additive sum does not care, so only group by texture.
        if (!L.Additive)
            std::sort(Quads.begin(), Quads.end(), [](FQuad const& A, FQuad const& B) { return A.Depth > B.Depth; });
        else
            std::stable_sort(Quads.begin(), Quads.end(),
                             [](FQuad const& A, FQuad const& B) { return A.Texture < B.Texture; });

        IRenderPipeline* const Pipe = DALib::Pipeline;
        FVertexMemoryLock Desc = {};
        if (DALib::VertexBuffer->LockVertexMemory(0x142, static_cast<unsigned>(Quads.size() * 6), &Desc) != GR_OK)
            return;
        FVertexLayout const Layout = LayoutOf(static_cast<unsigned>(Desc.Listing.Fvf));
        unsigned char* Out = static_cast<unsigned char*>(Desc.Vertices);
        static int const Corner[6] = {0, 1, 2, 2, 3, 0};
        for (FQuad const& Quad : Quads)
        {
            for (int Vert = 0; Vert < 6; ++Vert)
            {
                int const K = Corner[Vert];
                memcpy(Out, Quad.Pos[K], sizeof(Quad.Pos[K]));
                *reinterpret_cast<unsigned*>(Out + Layout.PosBytes) = Quad.Diffuse;
                float* const Uv = reinterpret_cast<float*>(Out + Layout.PosBytes + Layout.DiffBytes);
                Uv[0] = Quad.U[(K == 1 || K == 2) ? 1 : 0];
                Uv[1] = Quad.V[(K == 2 || K == 3) ? 1 : 0];
                Out += Layout.Stride;
            }
        }
        DALib::VertexBuffer->UnlockVertexMemory(&Desc);

        IRenderPipelineEx* const SoftEx = PipelineEx();
        if (SoftEx != nullptr)
        {
            SoftEx->SetSoftParticles(RPExSoftClouds);
            // A sprite fades out where it nears the scene over about a quarter of its width.
            SoftEx->SetSoftParticleFade((std::max)(1.0f, (L.SizeMin + L.SizeMax) * 0.25f));
        }
        // One draw per run of quads sharing a texture.
        size_t Run = 0;
        while (Run < Quads.size())
        {
            size_t End = Run + 1;
            while (End < Quads.size() && Quads[End].Texture == Quads[Run].Texture)
                ++End;
            Pipe->SetTextureStageTexture(0, Quads[Run].Texture);
            Pipe->DrawPrimitiveVb(4, Desc.Listing.VertexBuffer, static_cast<unsigned>(Desc.Listing.BaseVertex + Run * 6),
                                  static_cast<unsigned>((End - Run) * 6), nullptr);
            Run = End;
        }
        if (SoftEx != nullptr)
            SoftEx->SetSoftParticles(RPExSoftOff);
    }
}

void SpaceLayersParseSection(INI_Reader& Reader)
{
    std::unique_ptr<FSpaceLayer> Layer(new FSpaceLayer());
    FSpaceLayer& L = *Layer;
    bool bColorB = false;
    bool bDrop = static_cast<int>(G_Layers.size()) >= kMaxLayers;
    Layer->Shapes.reset(new FShapeDB());
    while (Reader.read_value())
    {
        if (Reader.is_value("shapes"))
        {
            if (!bDrop)
                L.Shapes->Load(GetFullFilename(Reader.get_value_string()), nullptr);
        }
        else if (Reader.is_value("shape"))
        {
            if (static_cast<int>(L.ShapeNames.size()) < kMaxShapes)
                L.ShapeNames.push_back(Reader.get_value_string());
        }
        else if (Reader.is_value("color"))
            ReadColor(Reader, L.ColorA);
        else if (Reader.is_value("color_b"))
        {
            ReadColor(Reader, L.ColorB);
            bColorB = true;
        }
        else if (Reader.is_value("alpha"))
            L.Alpha = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("size"))
        {
            L.SizeMin = static_cast<float>(Reader.get_value_float(0));
            L.SizeMax = Reader.get_num_parameters() > 1 ? static_cast<float>(Reader.get_value_float(1)) : L.SizeMin;
        }
        else if (Reader.is_value("near_distance"))
            L.Near = Reader.get_value_float(0);
        else if (Reader.is_value("far_distance"))
            L.Far = Reader.get_value_float(0);
        else if (Reader.is_value("near_fade"))
            L.NearFade = Reader.get_value_float(0);
        else if (Reader.is_value("far_fade"))
            L.FarFade = Reader.get_value_float(0);
        else if (Reader.is_value("cell"))
            L.Cell = Reader.get_value_float(0);
        else if (Reader.is_value("density"))
            L.Density = Reader.get_value_float(0);
        else if (Reader.is_value("clump_size"))
            L.ClumpSize = Reader.get_value_float(0);
        else if (Reader.is_value("clump_coverage"))
            L.Coverage = Reader.get_value_float(0);
        else if (Reader.is_value("clump_softness"))
            L.Softness = Reader.get_value_float(0);
        else if (Reader.is_value("count"))
            L.Count = Reader.get_value_int(0);
        else if (Reader.is_value("blend"))
            L.Additive = _stricmp(Reader.get_value_string(), "additive") == 0;
        else if (Reader.is_value("lit"))
            L.Lit = Reader.get_value_int(0) != 0;
        else if (Reader.is_value("ambient_floor"))
            L.Ambient = Clamp01(Reader.get_value_float(0));
        else if (Reader.is_value("forward"))
            L.Forward = Reader.get_value_float(0);
        else if (Reader.is_value("spin"))
            L.Spin = Reader.get_value_float(0);
        else if (Reader.is_value("rotation_step"))
            L.RotationStep = Reader.get_value_float(0);
        else if (Reader.is_value("wind"))
        {
            for (unsigned I = 0; I < 3; ++I)
                L.Wind[I] = Reader.get_value_float(I);
        }
    }
    if (bDrop)
        return;

    for (std::string const& Name : L.ShapeNames)
    {
        FTexShape* const Shape = L.Shapes->Find(Name.c_str());
        if (Shape != nullptr)
            L.ShapePtrs.push_back(Shape);
    }
    // Nothing to draw without a shape.
    if (L.ShapePtrs.empty())
        return;

    if (!bColorB)
        memcpy(L.ColorB, L.ColorA, sizeof(L.ColorB));
    if (L.SizeMin < 1.0f)
        L.SizeMin = 1.0f;
    L.SizeMax = (std::max)(L.SizeMax, L.SizeMin);
    L.Near = (std::max)(0.0, L.Near);
    L.Far = (std::max)(L.Far, L.Near + 1.0);
    L.Density = (std::max)(0.0, (std::min)(4.0, L.Density));
    L.Count = (std::max)(1, L.Count);
    L.Softness = (std::max)(0.001, L.Softness);
    // A cell holds sprites that can be as large as itself: never smaller than the biggest.
    if (!(L.Cell > 0.0))
        L.Cell = (std::max)(L.Far / 12.0, static_cast<double>(L.SizeMax));
    L.Cell = (std::max)(L.Cell, 1.0);
    if (!(L.ClumpSize > 0.0))
        L.ClumpSize = L.Far * 0.4;
    // The cache is redone when the grid origin has moved half a cell.
    L.CacheMargin = 0.5 * L.Cell;
    G_Layers.push_back(std::move(Layer));
}

void SpaceLayersClear()
{
    G_Layers.clear();
}

void SpaceLayersDraw(ICamera* Cam)
{
    static int const S_Enabled = PortConfigInt("Render", "space_layers", 1);
    if (S_Enabled == 0 || G_Layers.empty() || Cam == nullptr || DALib::Pipeline == nullptr)
        return;
    if (GetGameOption(kGameOptEffectsGroup) == 0)
        return;

    IRenderPipeline* const Pipe = DALib::Pipeline;
    float const* const CamPos = Cam->GetPosition();
    double const P[3] = {CamPos[0], CamPos[1], CamPos[2]};
    double const T = GetClientElapsedTime();

    // The sun's direction from the camera, for the forward-scatter glow.
    float SunDir[3] = {0.0f, 0.0f, 0.0f};
    bool bHasSun = false;
    float Sun[4];
    if (FindSystemSunSphere(Sun))
    {
        double const Dx = Sun[0] - P[0], Dy = Sun[1] - P[1], Dz = Sun[2] - P[2];
        double const Len = std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
        if (Len > 1.0)
        {
            SunDir[0] = static_cast<float>(Dx / Len);
            SunDir[1] = static_cast<float>(Dy / Len);
            SunDir[2] = static_cast<float>(Dz / Len);
            bHasSun = true;
        }
    }

    // Render states: the cloud puffs' (texture_panels.cpp) -- depth test on, depth write off,
    // no cull, no lighting; modulate stage 0, stage 1 off.
    int Saved89 = 0;
    Pipe->GetRenderState(D3DRS_LIGHTING, &Saved89);
    int Saved16 = 0;
    Pipe->GetRenderState(D3DRS_CULLMODE, &Saved16);
    int Saved18 = 0;
    Pipe->GetRenderState(D3DRS_ALPHAREF, &Saved18);
    Pipe->SetRenderState((D3DRENDERSTATETYPE)0x8d, 1);
    Pipe->SetRenderState((D3DRENDERSTATETYPE)0x91, 1);
    Pipe->SetRenderState(D3DRS_LIGHTING, 0);
    Pipe->SetRenderState(D3DRS_CULLMODE, 1);
    Pipe->SetRenderState(D3DRS_ZENABLE, 1);
    Pipe->SetRenderState(D3DRS_ZWRITEENABLE, 0);
    Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 1);
    Pipe->SetRenderState(D3DRS_ALPHAREF, 5);
    {
        // Vertices are in view space.
        float Ident12[12];
        Win3DIdentityRotation3x3(Ident12);
        Ident12[9] = 0.0f;
        Ident12[10] = 0.0f;
        Ident12[11] = 0.0f;
        Win3DBindModelview(nullptr, Ident12);
    }
    static unsigned long const kTss0[] = {1, 4, 2, 2, 3, 0, 4, 4, 5, 2, 6, 0, 0};
    static unsigned long const kTss1[] = {1, 1, 2, 2, 3, 1, 4, 1, 5, 2, 6, 1, 0};
    for (unsigned long const* Pair = kTss0; Pair[0] != 0; Pair += 2)
        Pipe->SetTextureStageState(0, static_cast<int>(Pair[0]), static_cast<int>(Pair[1]));
    for (unsigned long const* Pair = kTss1; Pair[0] != 0; Pair += 2)
        Pipe->SetTextureStageState(1, static_cast<int>(Pair[0]), static_cast<int>(Pair[1]));

    static std::vector<FVisible> S_Visible;
    static std::vector<FQuad> S_Quads;
    for (size_t I = 0; I < G_Layers.size(); ++I)
    {
        FSpaceLayer& L = *G_Layers[I];
        Pipe->SetRenderState(D3DRS_SRCBLEND, 5);                     // SRCALPHA
        Pipe->SetRenderState(D3DRS_DESTBLEND, L.Additive ? 2 : 6);   // ONE : INVSRCALPHA
        DrawLayer(L, I, Cam, P, T, SunDir, bHasSun, S_Visible, S_Quads);
    }

    Pipe->SetRenderState(D3DRS_DESTBLEND, 6);
    Pipe->SetRenderState(D3DRS_ALPHAFUNC, 5);
    Pipe->SetRenderState(D3DRS_ALPHAREF, Saved18);
    Pipe->SetRenderState(D3DRS_LIGHTING, Saved89);
    Pipe->SetRenderState(D3DRS_CULLMODE, Saved16);
    Pipe->SetRenderState((D3DRENDERSTATETYPE)0x8d, 0);
    Pipe->SetRenderState(D3DRS_ZWRITEENABLE, 1);
    Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 0);
}

#else

void SpaceLayersParseSection(INI_Reader&) {}
void SpaceLayersClear() {}
void SpaceLayersDraw(ICamera*) {}

#endif
