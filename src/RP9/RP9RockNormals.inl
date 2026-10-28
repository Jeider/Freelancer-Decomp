// Included by RP9Ex.cpp. Asteroid / debris relief (IRPRockNormals): one shared, procedural, tiling
// detail map built at device creation. No asset file, no per-material profile; the client opens a
// scope around each asteroid / debris object, so every material they draw is covered.

namespace
{
    float RockHash(int X, int Y, int Seed)
    {
        unsigned H = unsigned(X) * 374761393u + unsigned(Y) * 668265263u + unsigned(Seed) * 2246822519u;
        H = (H ^ (H >> 13)) * 1274126177u;
        H ^= H >> 16;
        return float(H & 0xffffffu) / 16777215.0f;
    }

    // Value noise that repeats every Period cells over [0,1).
    float RockNoise(float U, float V, int Period, int Seed)
    {
        const float Fx = U * Period, Fy = V * Period;
        const int Ix = int(std::floor(Fx)), Iy = int(std::floor(Fy));
        float Tx = Fx - Ix, Ty = Fy - Iy;
        Tx = Tx * Tx * (3.0f - 2.0f * Tx);
        Ty = Ty * Ty * (3.0f - 2.0f * Ty);
        const int X0 = ((Ix % Period) + Period) % Period, X1 = (X0 + 1) % Period;
        const int Y0 = ((Iy % Period) + Period) % Period, Y1 = (Y0 + 1) % Period;
        const float A = RockHash(X0, Y0, Seed), B = RockHash(X1, Y0, Seed);
        const float C = RockHash(X0, Y1, Seed), D = RockHash(X1, Y1, Seed);
        return (A + (B - A) * Tx) + ((C + (D - C) * Tx) - (A + (B - A) * Tx)) * Ty;
    }

    // Rough stone: broad lumps, mid chips and fine grit, plus ridged fractures.
    float RockHeight(float U, float V)
    {
        static const int Periods[6] = {4, 8, 16, 32, 64, 128};
        static const float Weights[6] = {1.0f, 0.62f, 0.38f, 0.24f, 0.15f, 0.10f};
        float Sum = 0, Total = 0;
        for (int I = 0; I < 6; ++I)
        {
            Sum += RockNoise(U, V, Periods[I], 17 + I * 31) * Weights[I];
            Total += Weights[I];
        }
        float Fracture = 0;
        for (int I = 0; I < 2; ++I)
        {
            const float N = RockNoise(U, V, 8 << I, 211 + I * 13);
            Fracture += 1.0f - std::fabs(2.0f * N - 1.0f);
        }
        return (Sum / Total) * 0.78f + Fracture * 0.11f;
    }
}

GENRESULT DACOM_API FDirectX9::SetRockNormalScope(unsigned long Class, float Radius)
{
    auto* E = Ex_;
    if (!E) return GR_GENERIC;
    // Scopes are object boundaries: queued instanced draws must not inherit the next object's.
    ExFlushSurfaceInstances();
    E->RockClass = (E->bRockEnabled && E->RockDetail && Class <= RPRockDebris) ? unsigned(Class) : 0u;
    E->RockRadius = (std::isfinite(Radius) && Radius > 0.5f) ? (std::min)(Radius, 5000.0f) : 0.0f;
    // rock_debug = 1: which classes and sizes the client opens a scope for (see ExSurfaceBegin).
    static const bool Debug = ReadShadowSetting("rock_debug", 0, 0, 1) > 0.5f;
    static std::set<std::string> Seen;
    if (Debug && E->RockClass != 0)
    {
        char Key[96];
        _snprintf(Key, sizeof(Key), "SCOPE class=%u radius~%.0f", E->RockClass, double(std::floor(E->RockRadius / 50.0f) * 50.0f));
        char Path[MAX_PATH] = {};
        if (Seen.size() < 200 && Seen.insert(Key).second && GetEnvironmentVariableA("LOCALAPPDATA", Path, MAX_PATH))
        {
            strcat(Path, "\\Freelancer-Decomp\\Diagnostics\\rock_debug.txt");
            if (FILE* File = fopen(Path, "a")) { fprintf(File, "%s\n", Key); fclose(File); }
        }
    }
    return GR_OK;
}

void FDirectX9::ExRockNormalsPrepare()
{
    auto* E = Ex_;
    if (!E || !Device_ || E->bRockNormalsPrepared) return;
    E->bRockNormalsPrepared = true;
    E->bRockEnabled = ReadShadowSetting("rock_normals", 1, 0, 1) > 0.5f;
    E->RockDetailStrength = ReadShadowSetting("rock_relief", 2.4f, 0, 4);
    E->RockMacroStrength = ReadShadowSetting("rock_macro_relief", 3.0f, 0, 4);
    // rock_pits = 1: the same relief inside out, craters and hollows instead of ridges.
    if (ReadShadowSetting("rock_pits", 0, 0, 1) > 0.5f)
    {
        E->RockDetailStrength = -E->RockDetailStrength;
        E->RockMacroStrength = -E->RockMacroStrength;
    }
    E->RockParallax = ReadShadowSetting("rock_parallax", 0.0f, 0, 8);
    E->bRockShadows = ReadShadowSetting("rock_shadows", 1, 0, 1) > 0.5f;
    // Quality by distance: each limit at least as far as the one before.
    E->RockLod[0] = ReadShadowSetting("rock_lod_full", 300, 20, 20000);
    E->RockLod[1] = (std::max)(E->RockLod[0], ReadShadowSetting("rock_lod_macro", 700, 20, 20000));
    E->RockLod[2] = (std::max)(E->RockLod[1], ReadShadowSetting("rock_lod_coarse", 1000, 20, 40000));
    E->RockLod[3] = (std::max)(E->RockLod[2], ReadShadowSetting("rock_lod_end", 2000, 20, 40000));
    E->RockLod[4] = (std::max)(E->RockLod[3], ReadShadowSetting("rock_lod_far", 5000, 20, 100000));
    E->RockAsteroidGloss = ReadShadowSetting("rock_asteroid_gloss", 0.04f, 0, 1);
    E->RockDebrisGloss = ReadShadowSetting("rock_debris_gloss", 0.55f, 0, 1);
    E->RockDebrisRelief = ReadShadowSetting("rock_debris_relief", 0.8f, 0, 4);
    E->RockDebrisMacro = ReadShadowSetting("rock_debris_macro", 0.8f, 0, 4);
    if (!E->bRockEnabled) return;
    RuntimeHitchScope Hitch("rock_detail", "procedural 512 map");
    const unsigned Size = 512;
    if (FAILED(D3DXCreateTexture(Device_, Size, Size, 0, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &E->RockDetail)) || !E->RockDetail)
    {
        E->RockDetail = nullptr;
        ExLogf(kExFdumpWarning, "WARNING", __LINE__, "rock normals: detail map not created; native asteroids kept");
        return;
    }
    std::vector<float> Height(Size * Size);
    for (unsigned Y = 0; Y < Size; ++Y)
        for (unsigned X = 0; X < Size; ++X)
            Height[Y * Size + X] = RockHeight((X + 0.5f) / Size, (Y + 0.5f) / Size);
    // Slopes in height per texel, rescaled so their spread is the same whatever the noise did.
    std::vector<float> Gx(Size * Size), Gy(Size * Size);
    double Sum2 = 0;
    for (unsigned Y = 0; Y < Size; ++Y)
        for (unsigned X = 0; X < Size; ++X)
        {
            const unsigned Xp = (X + 1) % Size, Xm = (X + Size - 1) % Size, Yp = (Y + 1) % Size, Ym = (Y + Size - 1) % Size;
            const float Dx = Height[Y * Size + Xp] - Height[Y * Size + Xm];
            const float Dy = Height[Yp * Size + X] - Height[Ym * Size + X];
            Gx[Y * Size + X] = Dx; Gy[Y * Size + X] = Dy;
            Sum2 += double(Dx) * Dx + double(Dy) * Dy;
        }
    const float Rms = float(std::sqrt(Sum2 / (2.0 * Size * Size)));
    const float Gain = Rms > 1.0e-6f ? 0.42f / Rms : 1.0f;
    D3DLOCKED_RECT Locked = {};
    if (SUCCEEDED(E->RockDetail->LockRect(0, &Locked, nullptr, 0)))
    {
        for (unsigned Y = 0; Y < Size; ++Y)
        {
            unsigned* Row = reinterpret_cast<unsigned*>(static_cast<unsigned char*>(Locked.pBits) + Y * Locked.Pitch);
            for (unsigned X = 0; X < Size; ++X)
            {
                const float Sx = (std::max)(-1.0f, (std::min)(1.0f, Gx[Y * Size + X] * Gain));
                const float Sy = (std::max)(-1.0f, (std::min)(1.0f, Gy[Y * Size + X] * Gain));
                const float H = Height[Y * Size + X];
                const float Hn = (std::max)(0.0f, (std::min)(1.0f, (H - 0.2f) / 0.6f));
                const float Cavity = 0.25f + 0.75f * Hn * Hn * (3.0f - 2.0f * Hn);
                auto Byte = [](float V) { return unsigned((std::max)(0.0f, (std::min)(1.0f, V)) * 255.0f + 0.5f); };
                Row[X] = (Byte(Cavity) << 24) | (Byte(Sx * 0.5f + 0.5f) << 16) | (Byte(Sy * 0.5f + 0.5f) << 8) | Byte(Hn);
            }
        }
        E->RockDetail->UnlockRect(0);
        D3DXFilterTexture(E->RockDetail, nullptr, 0, D3DX_FILTER_BOX);
        E->RockDetail->PreLoad();
    }
    ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "rock normals: %ux%u detail map, relief %.2f, macro %.2f, tiers %.0f/%.0f/%.0f/%.0f/%.0f m",
        Size, Size, double(E->RockDetailStrength), double(E->RockMacroStrength),
        double(E->RockLod[0]), double(E->RockLod[1]), double(E->RockLod[2]), double(E->RockLod[3]), double(E->RockLod[4]));
}

void FDirectX9::ExRockNormalsRelease()
{
    auto* E = Ex_;
    if (!E) return;
    E->RockClass = 0;
    if (E->RockDetail) { E->RockDetail->Release(); E->RockDetail = nullptr; }
    for (auto*& Ps : E->RockPs) if (Ps) { Ps->Release(); Ps = nullptr; }
    E->bRockNormalsPrepared = false;
    ExFlushSurfaceInstances();
}
