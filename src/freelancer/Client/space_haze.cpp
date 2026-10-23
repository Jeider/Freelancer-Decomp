// Port-only (RP9) space haze: one fullscreen pass of world-anchored gas at a few distances.
// See space_haze.h and docs/re/space_layers.md.

#include "space_haze.h"

#ifdef FREELANCER_RP9

#include "DALib.h"
#include "common_ini.h"
#include "common_misc.h" // ICamera
#include "game_options.h"
#include "globals.h" // GetClientElapsedTime
#include "port_config.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render_ex.h"
#include "solar_spheres.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

namespace
{
    int const kMaxShells = 4;
    int const kNoiseSize = 32;
    // The sampling origin wraps at this many tiles. A multiple of 10 so the detail lookup
    // (frequency 2.7) is continuous across the wrap: 100 * 2.7 is a whole number of tiles.
    double const kWrapTiles = 100.0;
    char const kShader[] = "SHADERS\\space_haze.hlsl";

    struct FShell
    {
        double Distance;
        double Scale;
    };

    struct FSpaceHaze
    {
        bool bValid = false;
        float ColorA[3] = {120.0f / 255.0f, 150.0f / 255.0f, 200.0f / 255.0f};
        float ColorB[3] = {120.0f / 255.0f, 150.0f / 255.0f, 200.0f / 255.0f};
        float Alpha = 0.15f;
        std::vector<FShell> Shells;
        float Coverage = 0.55f;
        float Softness = 0.2f;
        float Detail = 0.35f;
        double Drift[3] = {0.0, 0.0, 0.0};
        float Ambient = 0.45f;
        float Forward = 2.0f;
        float ForwardPower = 6.0f;
        float OcclusionSoftness = 0.1f;
        // sun_clear: how much the gas thins toward the sun (0..1), sun_clear_power: how wide
        // round it (lower = wider) -- the haze reads on the far side, not as a glare round the sun.
        float SunClear = 0.0f;
        float SunClearPower = 4.0f;
        // Flicker as retail's cloud puffs do it ([Clouds] lightning_*): each world-anchored spot
        // waits (0.8 .. 1.5) * flash_gap seconds, then for flash_duration its light jumps every
        // frame to rand * rand (mostly faint, now and then bright), lightning_color * that *
        // flash (the intensity) added to the gas. flash_size = a spot's size as a fraction of the
        // view, flash_density = the share of spots that flicker at all (0..1).
        float Flash = 0.0f;
        float FlashColour[3] = {1.0f, 1.0f, 1.0f};
        float FlashSize = 0.05f;
        float FlashDensity = 0.3f;
        float FlashGap = 3.0f;
        float FlashDuration = 0.5f;
        // The noise's character (no texture): detail_scale = the detail lookup's frequency;
        // grain = a fine third lookup roughening the edges (sandy; 0 = off, saves the lookup),
        // grain_scale its frequency; billow 0..1 = ridged noise (drifts and ridges, not blobs).
        float DetailScale = 2.7f;
        float Grain = 0.0f;
        float GrainScale = 9.0f;
        float Billow = 0.0f;
    };


    FSpaceHaze G_Haze;

    FRPExProgram* G_Program = nullptr;
    bool G_bProgramTried = false;
    FRPExTexture* G_Noise = nullptr;
    bool G_bNoiseTried = false;

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

    // The random value of one wrapped lattice point of an octave.
    float Lattice(int X, int Y, int Z, int Cells, int Octave, uint64_t Seed)
    {
        uint64_t const Ux = static_cast<uint64_t>(((X % Cells) + Cells) % Cells);
        uint64_t const Uy = static_cast<uint64_t>(((Y % Cells) + Cells) % Cells);
        uint64_t const Uz = static_cast<uint64_t>(((Z % Cells) + Cells) % Cells);
        uint64_t H = Hash(Seed ^ (static_cast<uint64_t>(Octave) << 56));
        H = Hash(H ^ (Ux | (Uy << 16) | (Uz << 32)));
        return static_cast<float>(H >> 40) * (1.0f / 16777216.0f);
    }

    float Smooth(float T)
    {
        return T * T * (3.0f - 2.0f * T);
    }

    // Tileable value noise: texel (X, Y, Z) of the 32-texel tile, Cells lattice cells per tile.
    float ValueNoise(int X, int Y, int Z, int Cells, int Octave, uint64_t Seed)
    {
        float const Step = static_cast<float>(Cells) / static_cast<float>(kNoiseSize);
        float const Fx = static_cast<float>(X) * Step;
        float const Fy = static_cast<float>(Y) * Step;
        float const Fz = static_cast<float>(Z) * Step;
        int const Ix = static_cast<int>(std::floor(Fx));
        int const Iy = static_cast<int>(std::floor(Fy));
        int const Iz = static_cast<int>(std::floor(Fz));
        float const Tx = Smooth(Fx - static_cast<float>(Ix));
        float const Ty = Smooth(Fy - static_cast<float>(Iy));
        float const Tz = Smooth(Fz - static_cast<float>(Iz));
        float V[2][2][2];
        for (int Dz = 0; Dz < 2; ++Dz)
            for (int Dy = 0; Dy < 2; ++Dy)
                for (int Dx = 0; Dx < 2; ++Dx)
                    V[Dz][Dy][Dx] = Lattice(Ix + Dx, Iy + Dy, Iz + Dz, Cells, Octave, Seed);
        float Row[2][2];
        for (int Dz = 0; Dz < 2; ++Dz)
            for (int Dy = 0; Dy < 2; ++Dy)
                Row[Dz][Dy] = V[Dz][Dy][0] + (V[Dz][Dy][1] - V[Dz][Dy][0]) * Tx;
        float Plane[2];
        for (int Dz = 0; Dz < 2; ++Dz)
            Plane[Dz] = Row[Dz][0] + (Row[Dz][1] - Row[Dz][0]) * Ty;
        return Plane[0] + (Plane[1] - Plane[0]) * Tz;
    }

    uint32_t ToByte(float V)
    {
        V = V < 0.0f ? 0.0f : (V > 1.0f ? 1.0f : V);
        return static_cast<uint32_t>(V * 255.0f + 0.5f);
    }

    // 32^3 A8R8G8B8: R = 4-octave density fBm (percentile-normalised so coverage behaves the
    // same for any seed), G = an independent 3-octave fBm for the colour mix.
    void GenerateNoise(std::vector<uint32_t>& Texels)
    {
        int const Count = kNoiseSize * kNoiseSize * kNoiseSize;
        std::vector<float> Density(Count);
        std::vector<float> Mix(Count);
        int const DensityCells[4] = {4, 8, 16, 32};
        float const DensityWeights[4] = {0.5f, 0.25f, 0.15f, 0.10f};
        int const MixCells[3] = {4, 8, 16};
        float const MixWeights[3] = {0.5f, 0.3f, 0.2f};
        for (int Z = 0; Z < kNoiseSize; ++Z)
            for (int Y = 0; Y < kNoiseSize; ++Y)
                for (int X = 0; X < kNoiseSize; ++X)
                {
                    int const I = X + kNoiseSize * (Y + kNoiseSize * Z);
                    float D = 0.0f;
                    for (int O = 0; O < 4; ++O)
                        D += DensityWeights[O] * ValueNoise(X, Y, Z, DensityCells[O], O, 0x51ace0001ull);
                    float M = 0.0f;
                    for (int O = 0; O < 3; ++O)
                        M += MixWeights[O] * ValueNoise(X, Y, Z, MixCells[O], O, 0x7a11ed0002ull);
                    Density[I] = D;
                    Mix[I] = M;
                }
        std::vector<float> Sorted(Density);
        std::sort(Sorted.begin(), Sorted.end());
        float const Lo = Sorted[static_cast<size_t>(Count * 0.02)];
        float const Hi = Sorted[static_cast<size_t>(Count * 0.98)];
        float const InvRange = Hi > Lo ? 1.0f / (Hi - Lo) : 1.0f;
        Texels.assign(static_cast<size_t>(Count), 0u);
        for (int I = 0; I < Count; ++I)
            Texels[I] = (ToByte((Density[I] - Lo) * InvRange) << 16) | (ToByte(Mix[I]) << 8);
    }

    void ReadColor(INI_Reader& Reader, float* Out)
    {
        for (unsigned I = 0; I < 3; ++I)
            Out[I] = static_cast<float>(Clamp01(Reader.get_value_float(I) / 255.0));
    }

    void Set4(float* Out, float A, float B, float C, float D)
    {
        Out[0] = A;
        Out[1] = B;
        Out[2] = C;
        Out[3] = D;
    }

    double Wrap(double V)
    {
        V = std::fmod(V, kWrapTiles);
        return V < 0.0 ? V + kWrapTiles : V;
    }
}

void SpaceHazeParseSection(INI_Reader& Reader)
{
    FSpaceHaze H;
    bool bColorB = false;
    while (Reader.read_value())
    {
        if (Reader.is_value("color"))
            ReadColor(Reader, H.ColorA);
        else if (Reader.is_value("color_b"))
        {
            ReadColor(Reader, H.ColorB);
            bColorB = true;
        }
        else if (Reader.is_value("alpha"))
            H.Alpha = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("shell"))
        {
            if (static_cast<int>(H.Shells.size()) < kMaxShells && Reader.get_num_parameters() > 1)
            {
                FShell S;
                S.Distance = (std::max)(1.0, static_cast<double>(Reader.get_value_float(0)));
                S.Scale = (std::max)(1.0, static_cast<double>(Reader.get_value_float(1)));
                H.Shells.push_back(S);
            }
        }
        else if (Reader.is_value("coverage"))
            H.Coverage = static_cast<float>(Reader.get_value_float(0));
        else if (Reader.is_value("softness"))
            H.Softness = (std::max)(0.001f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("detail"))
            H.Detail = (std::max)(0.0f, (std::min)(2.0f, static_cast<float>(Reader.get_value_float(0))));
        else if (Reader.is_value("drift"))
        {
            for (unsigned I = 0; I < 3; ++I)
                H.Drift[I] = Reader.get_value_float(I);
        }
        else if (Reader.is_value("ambient"))
            H.Ambient = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("forward"))
            H.Forward = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("forward_power"))
            H.ForwardPower = (std::max)(1.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("occlusion_softness"))
            H.OcclusionSoftness = (std::max)(0.001f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("flash"))
            H.Flash = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("flash_color"))
        {
            for (int I = 0; I < 3; ++I)
                H.FlashColour[I] = static_cast<float>(Clamp01(Reader.get_value_float(I) / 255.0));
        }
        else if (Reader.is_value("flash_size"))
            H.FlashSize = (std::max)(0.005f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("flash_density"))
            H.FlashDensity = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("detail_scale"))
            H.DetailScale = (std::max)(1.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("grain"))
            H.Grain = (std::max)(0.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("grain_scale"))
            H.GrainScale = (std::max)(1.0f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("billow"))
            H.Billow = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("flash_gap"))
            H.FlashGap = (std::max)(0.05f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("flash_duration"))
            H.FlashDuration = (std::max)(0.02f, static_cast<float>(Reader.get_value_float(0)));
        else if (Reader.is_value("sun_clear"))
            H.SunClear = static_cast<float>(Clamp01(Reader.get_value_float(0)));
        else if (Reader.is_value("sun_clear_power"))
            H.SunClearPower = (std::max)(0.5f, static_cast<float>(Reader.get_value_float(0)));
    }
    if (!bColorB)
        memcpy(H.ColorB, H.ColorA, sizeof(H.ColorB));
    if (H.Shells.empty())
    {
        FShell const Defaults[3] = {{2500.0, 2000.0}, {9000.0, 6000.0}, {30000.0, 18000.0}};
        H.Shells.assign(Defaults, Defaults + 3);
    }
    // Nearest first: the shader composites front to back.
    std::sort(H.Shells.begin(), H.Shells.end(),
              [](FShell const& A, FShell const& B) { return A.Distance < B.Distance; });
    H.bValid = true;
    G_Haze = H;
}

void SpaceHazeClear()
{
    G_Haze = FSpaceHaze();
}

void SpaceHazeShutdown()
{
    IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
    if (Ex != nullptr)
    {
        if (G_Program != nullptr)
            Ex->DestroyExProgram(G_Program);
        if (G_Noise != nullptr)
            Ex->DestroyExTexture(G_Noise);
    }
    G_Program = nullptr;
    G_bProgramTried = false;
    G_Noise = nullptr;
    G_bNoiseTried = false;
}

FRPExTexture* SpaceHazeEnsureNoise()
{
    if (G_Noise == nullptr)
    {
        if (G_bNoiseTried)
            return nullptr;
        G_bNoiseTried = true;
        IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
        if (Ex == nullptr)
            return nullptr;
        std::vector<uint32_t> Texels;
        GenerateNoise(Texels);
        if (Ex->CreateExVolumeTexture(kNoiseSize, kNoiseSize, kNoiseSize, RPExFormatA8R8G8B8,
                                      &Texels[0], &G_Noise) != GR_OK)
            G_Noise = nullptr;
    }
    return G_Noise;
}

void SpaceHazeDraw(ICamera* Cam, float Far)
{
    static int const S_Enabled = PortConfigInt("Render", "space_haze", 1);
    if (S_Enabled == 0 || !G_Haze.bValid || Cam == nullptr || DALib::Pipeline == nullptr)
        return;
    if (GetGameOption(kGameOptEffectsGroup) == 0 || !RenderEx::IsAvailable())
        return;
    IRenderPipelineEx* const Ex = RenderEx::GetPipelineEx();
    IRPDrawEx* const DrawEx = RenderEx::GetDrawEx();
    FRPExTexture* SceneDepth = nullptr;
    if (Ex->GetSceneDepth(&SceneDepth) != GR_OK || SceneDepth == nullptr)
        return;

    if (!G_bProgramTried)
    {
        G_bProgramTried = true;
        Ex->CreateExProgram(RenderEx::GetExtraData(), kShader, "VSMain", "PSMain", &G_Program);
    }
    if (G_Program == nullptr)
        return;
    if (SpaceHazeEnsureNoise() == nullptr)
        return;

    unsigned long FullWidth = 0;
    unsigned long FullHeight = 0;
    if (Ex->GetExTextureSize(SceneDepth, &FullWidth, &FullHeight) != GR_OK || FullWidth == 0 ||
        FullHeight == 0)
        return;

    // Camera: projection and view rotation as nebula_volume.cpp BuildRaymarchConstants builds them.
    double const kPi = 3.14159265358979323846;
    float const Near = Cam->GetZNear();
    float const* const CamPosF = Cam->GetPosition();
    double const CamPos[3] = {CamPosF[0], CamPosF[1], CamPosF[2]};
    float const* const View = Cam->GetViewTransform();
    double const Cot = 1.0 / std::tan(kPi / 180.0 * static_cast<double>(Cam->GetFovYDeg()));
    double const ScaleX = Cot / static_cast<double>(Cam->GetAspect());
    double const ScaleY = Cot;
    double const InvDepth = 1.0 / (static_cast<double>(Far) - static_cast<double>(Near));
    if (!(ScaleX != 0.0) || !(ScaleY != 0.0) || !std::isfinite(InvDepth))
        return;

    float C[21 * 4];
    memset(C, 0, sizeof(C));
    Set4(&C[0], static_cast<float>(Far * InvDepth),
         static_cast<float>(-static_cast<double>(Far) * Near * InvDepth), 1.0f, 0.0f);
    int const* const Vp = Cam->GetViewport();
    float const VpW = static_cast<float>(Vp[2] - Vp[0]);
    float const VpH = static_cast<float>(Vp[3] - Vp[1]);
    if (VpW > 0.0f && VpH > 0.0f)
        Set4(&C[4], static_cast<float>(Vp[0]) / FullWidth, static_cast<float>(Vp[1]) / FullHeight,
             VpW / FullWidth, VpH / FullHeight);
    else
        Set4(&C[4], 0.0f, 0.0f, 1.0f, 1.0f);
    Set4(&C[8], static_cast<float>(1.0 / ScaleX), static_cast<float>(1.0 / ScaleY), 0.0f, 0.0f);
    for (int Row = 0; Row < 3; ++Row)
        Set4(&C[12 + Row * 4], View[Row * 3 + 0], View[Row * 3 + 1], View[Row * 3 + 2], 0.0f);

    // Shells: the origin is the camera plus the field's drift (it moves with +drift, so the point
    // sampled is the camera minus drift * time), in tile units, wrapped in double so the floats
    // stay small however far the ship has flown.
    double const T = GetClientElapsedTime();
    int const Count = static_cast<int>(G_Haze.Shells.size());
    for (int I = 0; I < Count; ++I)
    {
        FShell const& S = G_Haze.Shells[I];
        Set4(&C[24 + I * 4], static_cast<float>(Wrap((CamPos[0] - G_Haze.Drift[0] * T) / S.Scale)),
             static_cast<float>(Wrap((CamPos[1] - G_Haze.Drift[1] * T) / S.Scale)),
             static_cast<float>(Wrap((CamPos[2] - G_Haze.Drift[2] * T) / S.Scale)),
             static_cast<float>(S.Distance / S.Scale));
        C[40 + I] = static_cast<float>(S.Distance);
    }
    Set4(&C[44], G_Haze.ColorA[0], G_Haze.ColorA[1], G_Haze.ColorA[2], G_Haze.Alpha);
    Set4(&C[48], G_Haze.ColorB[0], G_Haze.ColorB[1], G_Haze.ColorB[2], 0.0f);
    Set4(&C[52], G_Haze.Coverage, G_Haze.Softness, G_Haze.Detail, G_Haze.OcclusionSoftness);

    // The sun's direction from the camera for the forward-scatter glow; no sun -> flat light.
    float SunDir[3] = {0.0f, 0.0f, 0.0f};
    float HasSun = 0.0f;
    float Sun[4];
    if (FindSystemSunSphere(Sun))
    {
        double const Dx = Sun[0] - CamPos[0], Dy = Sun[1] - CamPos[1], Dz = Sun[2] - CamPos[2];
        double const Len = std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
        if (Len > 1.0)
        {
            SunDir[0] = static_cast<float>(Dx / Len);
            SunDir[1] = static_cast<float>(Dy / Len);
            SunDir[2] = static_cast<float>(Dz / Len);
            HasSun = 1.0f;
        }
    }
    Set4(&C[56], G_Haze.Ambient, G_Haze.Forward, G_Haze.ForwardPower, HasSun);
    Set4(&C[60], SunDir[0], SunDir[1], SunDir[2], static_cast<float>(Count));
    Set4(&C[64], HasSun > 0.5f ? G_Haze.SunClear : 0.0f, G_Haze.SunClearPower, 0.0f, 0.0f);
    // c17 the flicker colour * strength, w time (wrapped); c18 per shell: spot cells per noise
    // tile, so a spot spans about flash_size of a 70-degree view at the shell's distance; c19
    // density, gap, duration, the flicker frame (retail rolls a new rand per frame; 30 a second
    // here, so the flicker does not depend on the frame rate).
    Set4(&C[68], G_Haze.FlashColour[0] * G_Haze.Flash, G_Haze.FlashColour[1] * G_Haze.Flash,
         G_Haze.FlashColour[2] * G_Haze.Flash, static_cast<float>(std::fmod(GetClientElapsedTime(), 1000.0)));
    for (int I = 0; I < Count && I < 4; ++I)
    {
        FShell const& S = G_Haze.Shells[I];
        const double CellMetres = S.Distance * G_Haze.FlashSize * 1.22;
        C[72 + I] = static_cast<float>(S.Scale / (std::max)(1.0, CellMetres));
    }
    // c20 the noise's character: detail frequency, grain weight, grain frequency, billow.
    Set4(&C[80], G_Haze.DetailScale, G_Haze.Grain, G_Haze.GrainScale, G_Haze.Billow);
    Set4(&C[76], G_Haze.FlashDensity, G_Haze.FlashGap, G_Haze.FlashDuration,
         static_cast<float>(std::fmod(std::floor(GetClientElapsedTime() * 30.0), 8192.0)));

    IRenderPipeline* const Pipe = DALib::Pipeline;
    int SavedEnable = 0, SavedSrc = 0, SavedDest = 0, SavedOp = 0;
    Pipe->GetRenderState(D3DRS_ALPHABLENDENABLE, &SavedEnable);
    Pipe->GetRenderState(D3DRS_SRCBLEND, &SavedSrc);
    Pipe->GetRenderState(D3DRS_DESTBLEND, &SavedDest);
    Pipe->GetRenderState(D3DRS_BLENDOP, &SavedOp);

    FRPExPassDesc Pass = {nullptr, 0, 0};
    if (Ex->BeginExPass(&Pass) != GR_OK)
        return;
    FRPExSamplerState Point = {RPExFilterPoint, RPExMipNone, RPExAddressClamp, RPExAddressClamp,
                               RPExAddressClamp};
    FRPExSamplerState LinearWrap = {RPExFilterLinear, RPExMipNone, RPExAddressWrap,
                                    RPExAddressWrap, RPExAddressWrap};
    if (Ex->BindExProgram(G_Program) == GR_OK && Ex->BindExTexture(0, SceneDepth, &Point) == GR_OK &&
        Ex->BindExTexture(1, G_Noise, &LinearWrap) == GR_OK)
    {
        Ex->SetExPixelConstants(0, C, 21);
        // Premultiplied: the shader outputs (rgb already times alpha, 1 - transmittance).
        Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, 1);
        Pipe->SetRenderState(D3DRS_SRCBLEND, D3DBLEND_ONE);
        Pipe->SetRenderState(D3DRS_DESTBLEND, D3DBLEND_INVSRCALPHA);
        Pipe->SetRenderState(D3DRS_BLENDOP, D3DBLENDOP_ADD);
        DrawEx->DrawFullscreenQuad();
    }
    Ex->EndExPass();
    Pipe->SetRenderState(D3DRS_ALPHABLENDENABLE, SavedEnable);
    Pipe->SetRenderState(D3DRS_SRCBLEND, SavedSrc);
    Pipe->SetRenderState(D3DRS_DESTBLEND, SavedDest);
    Pipe->SetRenderState(D3DRS_BLENDOP, SavedOp);
}

#else

void SpaceHazeParseSection(INI_Reader&) {}
void SpaceHazeClear() {}
void SpaceHazeDraw(ICamera*, float) {}
void SpaceHazeShutdown() {}
FRPExTexture* SpaceHazeEnsureNoise() { return nullptr; }

#endif
