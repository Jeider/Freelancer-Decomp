// Run from repo root with exported mesh and texture paths (export_debris_render_check.py).
// Uses the production instancing helper, actual models/shaders, and a hidden D3D9 device.
#include <windows.h>
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <fstream>
#include "../src/RP9/RP9MeshInstances.h"
#include "../src/freelancer/Client/field_dust_batch.h"

static void Check(HRESULT H)
{
    if (FAILED(H)) { std::printf("D3D9 error %08lx\n", H); std::exit(1); }
}
static ID3DXBuffer* Compile(const char* Path, const char* Entry, const char* Profile)
{
    ID3DXBuffer *Code = nullptr, *Errors = nullptr;
    HRESULT H = D3DXCompileShaderFromFileA(Path, nullptr, nullptr, Entry, Profile, 0, &Code, &Errors, nullptr);
    if (Errors) { std::puts(static_cast<const char*>(Errors->GetBufferPointer())); Errors->Release(); }
    Check(H);
    return Code;
}
static void Set(float* C, int R, float X, float Y, float Z, float W)
{
    C[R * 4] = X; C[R * 4 + 1] = Y; C[R * 4 + 2] = Z; C[R * 4 + 3] = W;
}
static unsigned Nonzero(IDirect3DDevice9* D, IDirect3DSurface9* Target, bool Alpha)
{
    IDirect3DSurface9* Read = nullptr;
    Check(D->CreateOffscreenPlainSurface(256, 256, D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &Read, nullptr));
    Check(D->GetRenderTargetData(Target, Read));
    D3DLOCKED_RECT Lock;
    Check(Read->LockRect(&Lock, nullptr, D3DLOCK_READONLY));
    unsigned Count = 0;
    for (int Y = 0; Y < 256; ++Y)
        for (int X = 0; X < 256; ++X)
        {
            DWORD Pixel = reinterpret_cast<const DWORD*>(static_cast<const char*>(Lock.pBits) + Y * Lock.Pitch)[X];
            Count += (Pixel & (Alpha ? 0xff000000 : 0x00ffffff)) != 0;
        }
    Read->UnlockRect(); Read->Release();
    return Count;
}
static void ImageEnergy(IDirect3DDevice9* D, IDirect3DSurface9* Target, double* Rgb)
{
    IDirect3DSurface9* Read = nullptr;
    Check(D->CreateOffscreenPlainSurface(256, 256, D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &Read, nullptr));
    Check(D->GetRenderTargetData(Target, Read));
    D3DLOCKED_RECT Lock; Check(Read->LockRect(&Lock, nullptr, D3DLOCK_READONLY));
    Rgb[0] = Rgb[1] = Rgb[2] = 0;
    for (int Y = 0; Y < 256; ++Y) for (int X = 0; X < 256; ++X)
    {
        DWORD Pixel = reinterpret_cast<const DWORD*>(static_cast<const char*>(Lock.pBits) + Y * Lock.Pitch)[X];
        Rgb[0] += (Pixel >> 16) & 255; Rgb[1] += (Pixel >> 8) & 255; Rgb[2] += Pixel & 255;
    }
    Read->UnlockRect(); Read->Release();
}
static std::vector<DWORD> ReadPixels(IDirect3DDevice9* D, IDirect3DSurface9* Target)
{
    IDirect3DSurface9* Read = nullptr;
    Check(D->CreateOffscreenPlainSurface(256, 256, D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &Read, nullptr));
    Check(D->GetRenderTargetData(Target, Read));
    D3DLOCKED_RECT Lock; Check(Read->LockRect(&Lock, nullptr, D3DLOCK_READONLY));
    std::vector<DWORD> Pixels(256 * 256);
    for (int Y = 0; Y < 256; ++Y)
        memcpy(&Pixels[Y * 256], static_cast<const char*>(Lock.pBits) + Y * Lock.Pitch, 256 * 4);
    Read->UnlockRect(); Read->Release(); return Pixels;
}
int main(int Argc, char** Argv)
{
    if (Argc < 3 || Argc > 5) { std::puts("Usage: check_debris_render <mesh.bin> <texture> [mesh shader] [dust shader]"); return 1; }
    char const* Shader = Argc >= 4 ? Argv[3] : "DATA_EXTRA/SHADERS/far_rocks.hlsl";
    char const* DustShader = Argc == 5 ? Argv[4] : "DATA_EXTRA/SHADERS/field_dust.hlsl";
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    HWND Window = CreateWindowA("STATIC", "debris render check", WS_POPUP, 0, 0, 256, 256,
                                nullptr, nullptr, GetModuleHandle(nullptr), nullptr);
    IDirect3D9* Api = Direct3DCreate9(D3D_SDK_VERSION);
    if (!Api) return 1;
    D3DPRESENT_PARAMETERS P = {};
    P.Windowed = TRUE; P.SwapEffect = D3DSWAPEFFECT_DISCARD;
    P.BackBufferWidth = P.BackBufferHeight = 256; P.BackBufferFormat = D3DFMT_A8R8G8B8;
    P.EnableAutoDepthStencil = TRUE; P.AutoDepthStencilFormat = D3DFMT_D24S8;
    IDirect3DDevice9* D = nullptr;
    Check(Api->CreateDevice(0, D3DDEVTYPE_HAL, Window, D3DCREATE_HARDWARE_VERTEXPROCESSING, &P, &D));
    IDirect3DSurface9* Target = nullptr;
    Check(D->GetRenderTarget(0, &Target));
    IDirect3DTexture9* Texture = nullptr;
    Check(D3DXCreateTextureFromFileA(D, Argv[2], &Texture));
    Check(D->SetTexture(0, Texture));
    D->SetSamplerState(0, D3DSAMP_MINFILTER, D3DTEXF_LINEAR);
    D->SetSamplerState(0, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR);
    D->SetSamplerState(0, D3DSAMP_ADDRESSU, D3DTADDRESS_CLAMP);
    D->SetSamplerState(0, D3DSAMP_ADDRESSV, D3DTADDRESS_CLAMP);
    D->SetRenderState(D3DRS_ZENABLE, TRUE);
    D->SetRenderState(D3DRS_ZWRITEENABLE, TRUE);
    D->SetRenderState(D3DRS_ZFUNC, D3DCMP_LESSEQUAL);
    D->SetRenderState(D3DRS_CULLMODE, D3DCULL_NONE);
    ID3DXBuffer* Code = Compile(Shader, "VSMesh", "vs_3_0");
    IDirect3DVertexShader9* Vs = nullptr;
    Check(D->CreateVertexShader(static_cast<const DWORD*>(Code->GetBufferPointer()), &Vs)); Code->Release();
    Code = Compile(Shader, "PSMesh", "ps_3_0");
    IDirect3DPixelShader9* Ps = nullptr;
    Check(D->CreatePixelShader(static_cast<const DWORD*>(Code->GetBufferPointer()), &Ps)); Code->Release();
    Check(D->SetVertexShader(Vs)); Check(D->SetPixelShader(Ps));
    float V[36] = {}, C[480] = {};
    Set(V, 1, 1, 0, 0, 0); Set(V, 2, 0, 1, 0, 0); Set(V, 3, 0, 0, 1, 0);
    Set(V, 4, 1, 1, 100.f / 99, -100.f / 99); Set(V, 5, 1, 1, 0, 0);
    Set(V, 6, 100, 128, 1, 0.99999f); Set(V, 7, 0, 1, 90, .1f); Set(V, 8, 0, 5, 1, 0);
    Set(C, 0, 1, 1, 1, 1); Set(C, 5, .3f, .3f, .3f, 0);
    Set(C, 6, .7f, .7f, .7f, 0); Set(C, 7, 0, 0, 1, 1); Set(C, 8, 0, 0, 1, 1);
    Check(D->SetVertexShaderConstantF(0, V, 9)); Check(D->SetPixelShaderConstantF(0, C, 9));
    std::ifstream Input(Argv[1], std::ios::binary);
    unsigned Vertices = 0; Input.read(reinterpret_cast<char*>(&Vertices), 4);
    if (!Input || !Vertices || Vertices > 65535 || Vertices % 3) return 1;
    std::vector<float> Geometry(Vertices * 8);
    Input.read(reinterpret_cast<char*>(Geometry.data()), Geometry.size() * sizeof(float));
    if (!Input) return 1;
    IDirect3DVertexBuffer9 *MeshVb = nullptr, *Instances = nullptr;
    Check(D->CreateVertexBuffer(Vertices * 32, 0, 0, D3DPOOL_MANAGED, &MeshVb, nullptr));
    void* Data = nullptr;
    Check(MeshVb->Lock(0, 0, &Data, 0)); memcpy(Data, Geometry.data(), Vertices * 32); Check(MeshVb->Unlock());
    struct Instance { float CentreRadius[4], Rotation[4]; DWORD Colour; };
    Instance Placement[3] = {{{0, 0, -10, 6}, {0, 0, 0, 1}, 0xff800000},
                            {{-4, 0, -10, 3}, {0, .38268343f, 0, .92387953f}, 0xff800000},
                            {{4, 0, -10, 3}, {.38268343f, 0, 0, .92387953f}, 0xff800000}};
    Check(D->CreateVertexBuffer(sizeof(Placement), 0, 0, D3DPOOL_MANAGED, &Instances, nullptr));
    Check(Instances->Lock(0, 0, &Data, 0)); memcpy(Data, Placement, sizeof(Placement)); Check(Instances->Unlock());
    FRp9MeshInstances Renderer;
    unsigned Pixels = 0;
    for (int Pass = 0; Pass < 2; ++Pass)
    {
        Check(D->Clear(0, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, 0, 1, 0)); Check(D->BeginScene());
        Check(Renderer.Draw(D, MeshVb, Instances, Vertices, Pass, Pass + 1)); Check(D->EndScene());
        Pixels = Nonzero(D, Target, false);
        if (Pixels < 100 || Pixels > 40000) { std::printf("Unexpected mesh coverage: %u\n", Pixels); return 1; }
        std::string Preview = std::string(Argv[1]) + (Pass ? ".instances.png" : ".png");
        Check(D3DXSaveSurfaceToFileA(Preview.c_str(), D3DXIFF_PNG, Target, nullptr, nullptr));
        UINT Frequency;
        Check(D->GetStreamSourceFreq(0, &Frequency)); if (Frequency != 1) return 1;
        Check(D->GetStreamSourceFreq(1, &Frequency)); if (Frequency != 1) return 1;
    }
    // Equal geometry must fail LESS after the preceding solid pass wrote its real depth.
    IDirect3DQuery9* Occlusion = nullptr; Check(D->CreateQuery(D3DQUERYTYPE_OCCLUSION, &Occlusion));
    Check(D->SetRenderState(D3DRS_ZFUNC, D3DCMP_LESS)); Check(D->BeginScene());
    Check(Occlusion->Issue(D3DISSUE_BEGIN)); Check(Renderer.Draw(D, MeshVb, Instances, Vertices, 1, 2));
    Check(Occlusion->Issue(D3DISSUE_END)); Check(D->EndScene());
    DWORD Samples = ~0u; HRESULT Ready = S_FALSE;
    for (int Wait = 0; Wait < 1000 && Ready == S_FALSE; ++Wait)
    { Ready = Occlusion->GetData(&Samples, sizeof(Samples), D3DGETDATA_FLUSH); if (Ready == S_FALSE) Sleep(1); }
    Check(Ready); if (Ready != S_OK || Samples != 0) { std::puts("Mesh depth check failed"); return 1; }
    Occlusion->Release();
    Check(D->SetRenderState(D3DRS_ZFUNC, D3DCMP_LESSEQUAL));
    double Energy[4][3] = {};
    char const* LightNames[] = {"front", "back", "ambient", "red"};
    for (int Light = 0; Light < 4; ++Light)
    {
        float const Ambient = Light == 3 ? 0.0f : 0.04f;
        Set(C, 5, Ambient, Ambient, Ambient, 0);
        Set(C, 6, Light == 2 ? 0.0f : .8f, Light >= 2 ? 0.0f : .8f, Light >= 2 ? 0.0f : .8f, 0);
        Set(C, 7, 0, 0, Light == 1 ? -1.0f : 1.0f, 1);
        Check(D->SetPixelShaderConstantF(0, C, 9));
        Check(D->Clear(0, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, 0, 1, 0)); Check(D->BeginScene());
        Check(Renderer.Draw(D, MeshVb, Instances, Vertices, 0, 1)); Check(D->EndScene());
        ImageEnergy(D, Target, Energy[Light]);
        std::string Preview = std::string(Argv[1]) + ".light_" + LightNames[Light] + ".png";
        Check(D3DXSaveSurfaceToFileA(Preview.c_str(), D3DXIFF_PNG, Target, nullptr, nullptr));
    }
    if (Energy[0][0] < 1.5 * Energy[1][0] || Energy[0][0] < 2.0 * Energy[2][0] ||
        Energy[2][0] <= 0 || Energy[3][0] <= 0 || Energy[3][1] > .01 * Energy[3][0] || Energy[3][2] > .01 * Energy[3][0])
    {
        std::printf("Lighting failed: front %.0f, back %.0f, ambient %.0f, red RGB %.0f/%.0f/%.0f\n",
            Energy[0][0], Energy[1][0], Energy[2][0], Energy[3][0], Energy[3][1], Energy[3][2]); return 1;
    }
    std::printf("PASS: light direction, colour and ambient (front/back brightness %.2fx)\n", Energy[0][0] / Energy[1][0]);
    Renderer.Release(); MeshVb->Release(); Instances->Release();
    std::printf("PASS: actual mesh (%u triangles), multiple rotated instances, offset, depth and stream cleanup\n", Vertices / 3);
    Check(D->SetRenderState(D3DRS_ZENABLE, FALSE));
    Vs->Release(); Ps->Release(); Texture->Release();

    Code = Compile(DustShader, "VSMain", "vs_3_0");
    Check(D->CreateVertexShader(static_cast<const DWORD*>(Code->GetBufferPointer()), &Vs)); Code->Release();
    Code = Compile(DustShader, "PSMarch", "ps_3_0");
    Check(D->CreatePixelShader(static_cast<const DWORD*>(Code->GetBufferPointer()), &Ps)); Code->Release();
    Check(D->SetVertexShader(Vs)); Check(D->SetPixelShader(Ps));
    Check(D->CreateTexture(1, 1, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &Texture, nullptr));
    D3DLOCKED_RECT Lock;
    Check(Texture->LockRect(0, &Lock, nullptr, 0)); *static_cast<DWORD*>(Lock.pBits) = 0xffffffff; Texture->UnlockRect(0);
    Check(D->SetTexture(0, Texture));
    IDirect3DVolumeTexture9* Noise = nullptr;
    Check(D->CreateVolumeTexture(1, 1, 1, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &Noise, nullptr));
    D3DLOCKED_BOX Box;
    Check(Noise->LockBox(0, &Box, nullptr, 0)); *static_cast<DWORD*>(Box.pBits) = 0xff808080; Noise->UnlockBox(0);
    Check(D->SetTexture(1, Noise));
    memset(C, 0, sizeof(C));
    Set(C, 0, 100.f / 99, -100.f / 99, 1, 0); Set(C, 1, 0, 0, 1, 1); Set(C, 2, 1, 1, 0, 0);
    Set(C, 3, 1, 0, 0, 0); Set(C, 4, 0, 1, 0, 0); Set(C, 5, 0, 0, 1, 0); Set(C, 6, 1, 0, 0, 0);
    Set(C, 8, 0, 0, -10, 1); Set(C, 9, .25f, 0, 0, 0); Set(C, 10, 0, .25f, 0, 0); Set(C, 11, 0, 0, .25f, 0);
    Set(C, 12, .3f, 1, 0, 8); Set(C, 13, 0, 0, 0, 1); Set(C, 14, .5f, .2f, .1f, .8f);
    Set(C, 15, 1, 1, 1, 1); Set(C, 16, 1, 1, 1, .1f);
    struct Quad { float X, Y, Z, U, V; };
    Quad Q[4] = {{-1,1,0,0,0},{1,1,0,1,0},{-1,-1,0,0,1},{1,-1,0,1,1}};
    Check(D->SetFVF(D3DFVF_XYZ | D3DFVF_TEX1));
    float Template[28 * 4];
    memcpy(Template, &C[8 * 4], sizeof(Template));
    Set(C, 6, 4, 0, 0, 0);
    for (int Active = 0; Active < 4; ++Active)
    {
        for (int Slot = 0; Slot < 4; ++Slot)
        {
            memcpy(&C[(8 + Slot * 28) * 4], Template, sizeof(Template));
            C[(8 + Slot * 28) * 4 + 3] = Slot == Active ? 1.0f : 0.0f;
        }
        for (int Hole = 0; Hole < 2; ++Hole)
        {
            if (Hole)
            {
                int Base = 20 + Active * 28;
                Set(C, Base, 0, 0, -10, 1); Set(C, Base + 1, .2f, 0, 0, 0);
                Set(C, Base + 2, 0, .2f, 0, 0); Set(C, Base + 3, 0, 0, .2f, 0);
            }
            Check(D->SetPixelShaderConstantF(0, C, 120));
            Check(D->Clear(0, nullptr, D3DCLEAR_TARGET, 0, 1, 0)); Check(D->BeginScene());
            Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP, 2, Q, sizeof(Quad))); Check(D->EndScene());
            Pixels = Nonzero(D, Target, true);
            if ((!Hole && Pixels < 100) || (Hole && Pixels != 0))
            { std::printf("Dust exclusion failed: field=%d, hole=%d, pixels=%u\n", Active, Hole, Pixels); return 1; }
        }
    }
    std::puts("PASS: all four dust slots render and respect their own covering exclusion");
    // Identical physical rays through nonuniform density must not differ merely by screen pixel.
    Check(D->SetTexture(1, nullptr)); Noise->Release();
    Check(D->CreateVolumeTexture(32, 32, 32, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &Noise, nullptr));
    Check(Noise->LockBox(0, &Box, nullptr, 0));
    for (int Z = 0; Z < 32; ++Z) for (int Y = 0; Y < 32; ++Y) for (int X = 0; X < 32; ++X)
    {
        DWORD Value = static_cast<DWORD>(127.5 + 120.0 * sin(Z * 6.2831853 / 32.0));
        DWORD* Row = reinterpret_cast<DWORD*>(static_cast<char*>(Box.pBits) + Z * Box.SlicePitch + Y * Box.RowPitch);
        Row[X] = 0xff000000u | Value * 0x010101u;
    }
    Check(Noise->UnlockBox(0)); Check(D->SetTexture(1, Noise));
    Check(D->SetSamplerState(1, D3DSAMP_MINFILTER, D3DTEXF_LINEAR));
    Check(D->SetSamplerState(1, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR));
    Check(D->SetSamplerState(1, D3DSAMP_ADDRESSU, D3DTADDRESS_WRAP));
    Check(D->SetSamplerState(1, D3DSAMP_ADDRESSV, D3DTADDRESS_WRAP));
    Check(D->SetSamplerState(1, D3DSAMP_ADDRESSW, D3DTADDRESS_WRAP));
    memset(&C[8 * 4], 0, sizeof(C) - 8 * 4 * sizeof(float));
    memcpy(&C[8 * 4], Template, sizeof(Template));
    Set(C, 2, 0, 0, 0, 0); Set(C, 6, 1, 0, 0, 0);
    Set(C, 12, .05f, 1, 1, 6); Set(C, 13, .13f, .21f, .37f, .19f); Set(C, 14, .5f, .25f, .1f, .8f);
    Check(D->SetPixelShaderConstantF(0, C, 120));
    Check(D->Clear(0, nullptr, D3DCLEAR_TARGET, 0, 1, 0)); Check(D->BeginScene());
    Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP, 2, Q, sizeof(Quad))); Check(D->EndScene());
    auto Uniform = ReadPixels(D, Target);
    unsigned MinAlpha = 255, MaxAlpha = 0;
    for (DWORD Pixel : Uniform) { unsigned A = Pixel >> 24; MinAlpha = (std::min)(MinAlpha, A); MaxAlpha = (std::max)(MaxAlpha, A); }
    if (!MinAlpha || MaxAlpha - MinAlpha > 1)
    { std::printf("Screen-space dust ripple: identical rays have alpha %u..%u\n", MinAlpha, MaxAlpha); return 1; }
    std::puts("PASS: nonuniform dust density has no screen-pixel-dependent ripple");

    // Use the production batching helper for 13 visible fields and compare with one field
    // per draw. Distinct colours detect reversed batch order as well as lost fifth+ clouds.
    std::vector<FieldDustBatch::Batch> Batches, Singles;
    float Rect[4] = {0, 0, 1, 1};
    for (int I = 0; I < 13; ++I)
    {
        float* Field = FieldDustBatch::Append(Batches, C, Rect);
        memcpy(Field, Template, sizeof(Template));
        Field[4 * 4] = .02f; Field[4 * 4 + 2] = 0; // faint, no clumps
        Field[7 * 4] = I % 3 == 0 ? 1.0f : .1f;
        Field[7 * 4 + 1] = I % 3 == 1 ? 1.0f : .1f;
        Field[7 * 4 + 2] = I % 3 == 2 ? 1.0f : .1f;
        std::vector<FieldDustBatch::Batch> Single;
        memcpy(FieldDustBatch::Append(Single, C, Rect), Field, sizeof(Template));
        Singles.push_back(Single[0]);
    }
    if (Batches.size() != 4 || Batches.back().Count != 1) return 1;
    auto RenderBatches = [&](std::vector<FieldDustBatch::Batch> const& List) {
        Check(D->SetRenderState(D3DRS_ALPHABLENDENABLE, TRUE));
        Check(D->SetRenderState(D3DRS_SRCBLEND, D3DBLEND_ONE));
        Check(D->SetRenderState(D3DRS_DESTBLEND, D3DBLEND_INVSRCALPHA));
        Check(D->Clear(0, nullptr, D3DCLEAR_TARGET, 0, 1, 0)); Check(D->BeginScene());
        for (auto It = List.rbegin(); It != List.rend(); ++It)
        {
            Check(D->SetPixelShaderConstantF(0, It->Constants, 120));
            Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP, 2, Q, sizeof(Quad)));
        }
        Check(D->EndScene()); return ReadPixels(D, Target);
    };
    auto Batched = RenderBatches(Batches), Reference = RenderBatches(Singles);
    unsigned MaxError = 0;
    for (size_t I = 0; I < Batched.size(); ++I) for (unsigned Shift = 0; Shift < 32; Shift += 8)
    {
        unsigned Error = static_cast<unsigned>(abs((int)((Batched[I] >> Shift) & 255) - (int)((Reference[I] >> Shift) & 255)));
        MaxError = (std::max)(MaxError, Error);
    }
    if (MaxError > 6 || (Batched[128 * 256 + 128] >> 24) < 100)
    { std::printf("Dust batch composition failed: max error %u\n", MaxError); return 1; }
    std::printf("PASS: all 13 dust fields contribute in correct batch order (max byte error %u)\n", MaxError);
    D->SetTexture(0, nullptr); D->SetTexture(1, nullptr); D->SetVertexShader(nullptr); D->SetPixelShader(nullptr);
    Noise->Release(); Texture->Release(); Vs->Release(); Ps->Release(); Target->Release();
    D->Release(); Api->Release(); DestroyWindow(Window);
    return 0;
}
