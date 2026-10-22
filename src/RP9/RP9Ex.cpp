// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// RP9 Ex: the port-only Direct3D 9 extensions of RP9.dll -- IRenderPipelineEx and IRPDrawEx
// (render/IRenderPipelineEx.h). Retail and RP8 have nothing like this; the code below is new
// port feature work, not a mirror of an RP8 function. docs/re/rp9.md, "Ex extensions",
// describes the contract.
//
// How it stays out of the way of the RP8-mirrored fixed-function code:
// - Nothing here runs unless a consumer QueryInterfaces Iids::RenderPipelineEx / RPDrawEx --
//   except the INTZ depth buffer, which CreateBuffers creates instead of the auto depth-stencil
//   whenever the device supports it (transparent to fixed-function rendering).
// - Every device write that bypasses RP9's lazy caches happens inside BeginExPass/EndExPass,
//   and EndExPass makes the caches true again: render states go through the cache itself and
//   are re-queued to their pre-pass values, fixed-function stages the pass touched are saved
//   and re-sent, shaders are unbound, colour target / depth surface / viewport are restored.
#include "RP9Ex.h"
#include "RP9DeviceCallCache.h"
#include "readfile.h"

#include <cstdarg>
#include <cstddef>
#include <cmath>
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <atomic>
#include <thread>

// d3dx9.h after RP9.h (render/d3d8_min.h already pulled the Windows SDK d3d9.h).
#include <d3dx9.h>
#include "RP9ShaderCache.h"

namespace
{
    void StartSurfaceShaderWarmup();
    float ReadPortFade(const char* Key);
    extern std::atomic<int> G_SurfaceWarmState;
    extern std::atomic<int> G_SurfaceWarmPending;
    extern int G_SurfaceWarmTotal;

    const int kExFdumpError = 0x100001;
    const int kExFdumpWarning = 0x100002;
    const int kExFdumpNotice = 0x100003;
    const char kExSource[] = "RP9Ex.cpp";

    // The INTZ FOURCC: a depth-stencil format that can also be sampled (24-bit depth, 8-bit
    // stencil; the sampled value is the depth in .r). Supported by every D3D10-class driver.
    const D3DFORMAT kIntzFormat = (D3DFORMAT)(MAKEFOURCC('I', 'N', 'T', 'Z'));

    // ps_3_0 has 16 samplers; fixed-function stages are 0..7.
    const unsigned long kExSamplerCount = 16;

    // One FDUMP line per text line ("%s(%d) : <KIND>:General:RP9Ex: <text>"), so a long
    // compiler log is never cut by the 0x400-byte line buffer of the log hook.
    void ExLog(int Flags, const char* Kind, int Line, const char* Text)
    {
        const char* Cursor = Text;
        while (Cursor != nullptr && *Cursor != '\0')
        {
            const char* End = Cursor;
            while (*End != '\0' && *End != '\n' && (End - Cursor) < 0x300)
                ++End;
            char Chunk[0x301];
            const size_t Length = (size_t)(End - Cursor);
            memcpy(Chunk, Cursor, Length);
            Chunk[Length] = '\0';
            if (Length != 0 && Chunk[Length - 1] == '\r')
                Chunk[Length - 1] = '\0';
            if (Chunk[0] != '\0')
                FDUMP(Flags, "%s(%d) : %s:General:RP9Ex: %s", kExSource, Line, Kind, Chunk);
            Cursor = (*End == '\n') ? End + 1 : End;
        }
    }

    void ExLogf(int Flags, const char* Kind, int Line, const char* Format, ...)
    {
        char Text[0x800];
        va_list Args;
        va_start(Args, Format);
        _vsnprintf(Text, sizeof(Text), Format, Args);
        va_end(Args);
        Text[sizeof(Text) - 1] = '\0';
        ExLog(Flags, Kind, Line, Text);
    }

    // Reads a whole FileSystem-relative file (the open descriptor RP9's LoadTexture uses).
    bool ReadFsFile(IFileSystem* FileSystem, const char* Path, std::vector<char>* Out)
    {
        Out->clear();
        if (FileSystem == nullptr || Path == nullptr)
            return false;
        FFileSystemDesc Desc;
        memset(&Desc, 0, sizeof(Desc));
        Desc.Size = 0x34;
        Desc.ComponentName = "FileSystem";
        Desc.Path = Path;
        Desc.Access = 0x80000000; // GENERIC_READ
        Desc.ShareMode = 1;       // FILE_SHARE_READ
        Desc.Creation = 3;        // OPEN_EXISTING
        Desc.Flags = 0x8000080;
        Desc.Field30 = 0xFFFFFFFF;
        const int Handle = FileSystem->OpenByDesc(&Desc);
        if (Handle == -1)
            return false;
        const unsigned long Size = FileSystem->GetSize((unsigned long)(Handle), nullptr);
        bool bOk = Size != 0xFFFFFFFF;
        if (bOk && Size != 0)
        {
            Out->resize(Size);
            unsigned long Got = 0;
            bOk = FileSystem->Read((unsigned long)(Handle), &(*Out)[0], Size, &Got, 0) != 0 &&
                  Got == Size;
        }
        FileSystem->CloseFile((unsigned long)(Handle));
        if (!bOk)
            Out->clear();
        return bOk;
    }

    // "SHADERS\\x.hlsl" -> "SHADERS\\" (empty without a directory part).
    std::string DirectoryOf(const std::string& Path)
    {
        const size_t Slash = Path.find_last_of("\\/");
        if (Slash == std::string::npos)
            return std::string();
        return Path.substr(0, Slash + 1);
    }

    // #include "x" / <x>: first next to the top-level file, then from the FileSystem root.
    class FRp9ExShaderInclude final : public ID3DXInclude
    {
    public:
        FRp9ExShaderInclude(IFileSystem* InFileSystem, const std::string& InDirectory)
            : FileSystem(InFileSystem), Directory(InDirectory)
        {
        }

        // STDMETHOD keeps the base's COM_DECLSPEC_NOTHROW on the override.
        STDMETHOD(Open)(D3DXINCLUDE_TYPE /*Type*/, LPCSTR FileName, LPCVOID /*ParentData*/,
                        LPCVOID* OutData, UINT* OutBytes) override
        {
            std::vector<char> Data;
            bool bFound = false;
            if (!Directory.empty())
                bFound = ReadFsFile(FileSystem, (Directory + FileName).c_str(), &Data);
            if (!bFound)
                bFound = ReadFsFile(FileSystem, FileName, &Data);
            if (!bFound)
            {
                ExLogf(kExFdumpError, "ERROR", __LINE__, "shader include \"%s\" not found",
                       FileName);
                return E_FAIL;
            }
            char* Copy = new char[Data.size() + 1];
            if (!Data.empty())
                memcpy(Copy, &Data[0], Data.size());
            Copy[Data.size()] = '\0';
            *OutData = Copy;
            *OutBytes = (UINT)(Data.size());
            return S_OK;
        }

        STDMETHOD(Close)(LPCVOID Data) override
        {
            delete[] (const char*)(Data);
            return S_OK;
        }

    private:
        IFileSystem* FileSystem;
        std::string Directory;
    };

    // Preprocess dependencies and reuse persistent bytecode; compile only on a
    // cache miss. Diagnostics retain the original warning/error reporting.
    bool CompileStage(const std::string& Source, const std::string& Path, ID3DXInclude* Include,
                      const std::string& Entry, const char* Profile,
                      std::vector<unsigned char>* OutCode)
    {
        std::string Messages;bool Hit=false,Stored=false;
        ULONGLONG Start=GetTickCount64();
        const HRESULT Hr=Rp9ShaderCache::Compile(Source,Include,Entry,Profile,0,OutCode,&Messages,&Hit,&Stored);
        const bool bOk = SUCCEEDED(Hr);
        if (!bOk)
            ExLogf(kExFdumpError, "ERROR", __LINE__, "%s: %s %s failed to compile (hr 0x%08x)",
                   Path.c_str(), Profile, Entry.c_str(), (unsigned int)(Hr));
        if(!Messages.empty()) ExLog(bOk ? kExFdumpWarning : kExFdumpError,
            bOk ? "WARNING" : "ERROR",__LINE__,Messages.c_str());
        if(bOk) ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"shader cache %s: %s %s %s (%llu ms)",
            Hit ? "HIT" : (Stored ? "MISS/stored" : "MISS/no disk write"),Path.c_str(),
            Entry.c_str(),Profile,(unsigned long long)(GetTickCount64()-Start));
        return bOk;
    }

    // Shader objects from the program's bytecode, where missing (new device, first compile).
    HRESULT CreateProgramShaders(IDirect3DDevice9* Device, FRPExProgram* Program)
    {
        if (Device == nullptr || Program->VsBytecode.empty() || Program->PsBytecode.empty())
            return S_OK;
        HRESULT Hr = S_OK;
        if (Program->Vs == nullptr)
            Hr = Device->CreateVertexShader((const DWORD*)(&Program->VsBytecode[0]), &Program->Vs);
        if (SUCCEEDED(Hr) && Program->Ps == nullptr)
            Hr = Device->CreatePixelShader((const DWORD*)(&Program->PsBytecode[0]), &Program->Ps);
        if (FAILED(Hr))
            ExLogf(kExFdumpError, "ERROR", __LINE__, "%s: creating the shaders failed (hr 0x%08x)",
                   Program->Path.c_str(), (unsigned int)(Hr));
        return Hr;
    }

    void ReleaseProgramShaders(FRPExProgram* Program)
    {
        if (Program->Vs != nullptr)
        {
            Program->Vs->Release();
            Program->Vs = nullptr;
        }
        if (Program->Ps != nullptr)
        {
            Program->Ps->Release();
            Program->Ps = nullptr;
        }
    }

    // Read + compile both stages; only when both compiled (and, with a device, both shader
    // objects were made) does the program switch to the new code. Otherwise the previous
    // bytecode and shaders stay.
    bool CompileProgram(IDirect3DDevice9* Device, FRPExProgram* Program)
    {
        std::vector<char> File;
        if (!ReadFsFile(Program->FileSystem, Program->Path.c_str(), &File))
        {
            ExLogf(kExFdumpError, "ERROR", __LINE__, "%s: cannot read the shader file",
                   Program->Path.c_str());
            return false;
        }
        // #line names the file in the compiler's messages (it reports "memory" otherwise).
        std::string Source = "#line 1 \"";
        for (size_t Index = 0; Index < Program->Path.size(); ++Index)
            Source += Program->Path[Index] == '\\' ? '/' : Program->Path[Index];
        Source += "\"\n";
        if (!File.empty())
            Source.append(&File[0], File.size());

        FRp9ExShaderInclude Include(Program->FileSystem, DirectoryOf(Program->Path));
        std::vector<unsigned char> VsCode;
        std::vector<unsigned char> PsCode;
        const bool bVs = CompileStage(Source, Program->Path, &Include, Program->VsEntry, "vs_3_0",
                                      &VsCode);
        const bool bPs = CompileStage(Source, Program->Path, &Include, Program->PsEntry, "ps_3_0",
                                      &PsCode);
        if (!bVs || !bPs)
        {
            if (!Program->VsBytecode.empty())
                ExLogf(kExFdumpError, "ERROR", __LINE__, "%s: keeping the previous shader code",
                       Program->Path.c_str());
            return false;
        }

        FRPExProgram Fresh;
        Fresh.FileSystem = nullptr;
        Fresh.Vs = nullptr;
        Fresh.Ps = nullptr;
        Fresh.VsBytecode.swap(VsCode);
        Fresh.PsBytecode.swap(PsCode);
        if (FAILED(CreateProgramShaders(Device, &Fresh)))
        {
            ReleaseProgramShaders(&Fresh);
            return false;
        }
        ReleaseProgramShaders(Program);
        Program->Vs = Fresh.Vs;
        Program->Ps = Fresh.Ps;
        Program->VsBytecode.swap(Fresh.VsBytecode);
        Program->PsBytecode.swap(Fresh.PsBytecode);
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "%s: compiled (%s, %s)", Program->Path.c_str(),
               Program->VsEntry.c_str(), Program->PsEntry.c_str());
        return true;
    }

    // ERPExFormat -> D3DFORMAT and bytes per texel; D3DFMT_UNKNOWN for an unknown value.
    D3DFORMAT ExFormatToD3d(ERPExFormat Format, unsigned long* OutBytes)
    {
        switch (Format)
        {
        case RPExFormatA8R8G8B8: *OutBytes = 4; return D3DFMT_A8R8G8B8;
        case RPExFormatL8: *OutBytes = 1; return D3DFMT_L8;
        case RPExFormatA16B16G16R16F: *OutBytes = 8; return D3DFMT_A16B16G16R16F;
        case RPExFormatR16F: *OutBytes = 2; return D3DFMT_R16F;
        case RPExFormatR32F: *OutBytes = 4; return D3DFMT_R32F;
        case RPExFormatG16R16F: *OutBytes = 4; return D3DFMT_G16R16F;
        default: *OutBytes = 0; return D3DFMT_UNKNOWN;
        }
    }

    void ReleaseExTextureGpu(FRPExTexture* Texture)
    {
        if (Texture->Surface != nullptr)
        {
            Texture->Surface->Release();
            Texture->Surface = nullptr;
        }
        if (Texture->Texture != nullptr)
        {
            Texture->Texture->Release();
            Texture->Texture = nullptr;
        }
    }

    // A D3DPOOL_DEFAULT render target at its requested size (absolute, or a fraction of the
    // back buffer). Failure leaves the handle without GPU objects (binding it then fails).
    HRESULT CreateRenderTargetGpu(IDirect3DDevice9* Device, FRPExTexture* Target,
                                  unsigned long BackBufferWidth, unsigned long BackBufferHeight)
    {
        unsigned long Width = Target->TargetDesc.Width;
        unsigned long Height = Target->TargetDesc.Height;
        if (Width == 0 || Height == 0)
        {
            Width = (unsigned long)((float)(BackBufferWidth) * Target->TargetDesc.BackBufferScale);
            Height = (unsigned long)((float)(BackBufferHeight) * Target->TargetDesc.BackBufferScale);
        }
        if (Width == 0)
            Width = 1;
        if (Height == 0)
            Height = 1;
        unsigned long Bytes = 0;
        const D3DFORMAT Format = ExFormatToD3d(Target->Format, &Bytes);
        IDirect3DTexture9* Texture = nullptr;
        HRESULT Hr = Device->CreateTexture((UINT)(Width), (UINT)(Height), 1, D3DUSAGE_RENDERTARGET,
                                           Format, D3DPOOL_DEFAULT, &Texture, nullptr);
        IDirect3DSurface9* Surface = nullptr;
        if (SUCCEEDED(Hr))
            Hr = Texture->GetSurfaceLevel(0, &Surface);
        if (FAILED(Hr))
        {
            if (Texture != nullptr)
                Texture->Release();
            ExLogf(kExFdumpWarning, "WARNING", __LINE__,
                   "render target %lux%lu (format %u) could not be created (hr 0x%08x)", Width,
                   Height, (unsigned int)(Target->Format), (unsigned int)(Hr));
            return Hr;
        }
        Target->Texture = Texture;
        Target->Surface = Surface;
        Target->Width = Width;
        Target->Height = Height;
        return S_OK;
    }

    // A D3DPOOL_MANAGED one-level volume texture filled from the kept texels.
    HRESULT CreateVolumeGpu(IDirect3DDevice9* Device, FRPExTexture* Volume)
    {
        unsigned long Bytes = 0;
        const D3DFORMAT Format = ExFormatToD3d(Volume->Format, &Bytes);
        IDirect3DVolumeTexture9* Texture = nullptr;
        HRESULT Hr = Device->CreateVolumeTexture((UINT)(Volume->Width), (UINT)(Volume->Height),
                                                 (UINT)(Volume->Depth), 1, 0, Format,
                                                 D3DPOOL_MANAGED, &Texture, nullptr);
        if (SUCCEEDED(Hr))
        {
            D3DLOCKED_BOX Box;
            Hr = Texture->LockBox(0, &Box, nullptr, 0);
            if (SUCCEEDED(Hr))
            {
                const unsigned long RowBytes = Volume->Width * Bytes;
                const unsigned char* Source = Volume->VolumeData.empty() ? nullptr
                                                                         : &Volume->VolumeData[0];
                for (unsigned long Slice = 0; Slice < Volume->Depth; ++Slice)
                {
                    unsigned char* SliceBits = (unsigned char*)(Box.pBits) + Slice * Box.SlicePitch;
                    for (unsigned long Row = 0; Row < Volume->Height; ++Row)
                    {
                        unsigned char* Dest = SliceBits + Row * Box.RowPitch;
                        if (Source != nullptr)
                            memcpy(Dest, Source + (Slice * Volume->Height + Row) * RowBytes,
                                   RowBytes);
                        else
                            memset(Dest, 0, RowBytes);
                    }
                }
                Texture->UnlockBox(0);
            }
        }
        if (FAILED(Hr))
        {
            if (Texture != nullptr)
                Texture->Release();
            ExLogf(kExFdumpWarning, "WARNING", __LINE__,
                   "volume texture %lux%lux%lu (format %u) could not be created (hr 0x%08x)",
                   Volume->Width, Volume->Height, Volume->Depth, (unsigned int)(Volume->Format),
                   (unsigned int)(Hr));
            return Hr;
        }
        Volume->Texture = Texture;
        return S_OK;
    }

    DWORD ExFilterToD3d(ERPExFilter Filter)
    {
        return Filter == RPExFilterLinear ? D3DTEXF_LINEAR : D3DTEXF_POINT;
    }

    DWORD ExMipFilterToD3d(ERPExMipFilter Filter)
    {
        if (Filter == RPExMipPoint)
            return D3DTEXF_POINT;
        if (Filter == RPExMipLinear)
            return D3DTEXF_LINEAR;
        return D3DTEXF_NONE;
    }

    DWORD ExAddressToD3d(ERPExAddress Address)
    {
        if (Address == RPExAddressClamp)
            return D3DTADDRESS_CLAMP;
        if (Address == RPExAddressMirror)
            return D3DTADDRESS_MIRROR;
        return D3DTADDRESS_WRAP;
    }

    // Pass-scoped render state through RP9's own cache: it reaches the device at the next
    // flush, and EndExPass re-queues the pre-pass value (FRp9RenderStateCache::RestorePending).
    void ExSetPassState(FDirectX9* Self, D3DRENDERSTATETYPE State, unsigned long Value)
    {
        Self->RenderStates_.MarkDirty((unsigned int)(State), Value);
    }

    // No depth surface bound: depth test and write off too (D3D9 leaves them undefined there).
    void ExUnbindDepth(FDirectX9* Self)
    {
        FRp9ExState* Ex = Self->Ex_;
        Self->Device_->SetDepthStencilSurface(nullptr);
        Ex->bDepthBound = false;
        ExSetPassState(Self, D3DRS_ZENABLE, D3DZB_FALSE);
        ExSetPassState(Self, D3DRS_ZWRITEENABLE, FALSE);
    }

    // The pass's colour target (null = the back buffer the pass started on) and depth.
    // SetRenderTarget also resets the device viewport to the whole target.
    HRESULT ExSelectTarget(FDirectX9* Self, FRPExTexture* Target, bool bKeepDepth)
    {
        FRp9ExState* Ex = Self->Ex_;
        IDirect3DDevice9* Device = Self->Device_;
        IDirect3DSurface9* Surface = Target != nullptr ? Target->Surface : Ex->SavedColor;
        if (Surface == nullptr)
            return E_FAIL;
        // A texture cannot be sampled while it is the render target.
        for (unsigned long Sampler = 0; Target != nullptr && Sampler < kExSamplerCount; ++Sampler)
        {
            if (Ex->BoundTextures[Sampler] != nullptr && Ex->BoundTextures[Sampler] == Target->Texture)
            {
                Rp9SetTexture(Device, Sampler, nullptr);
                Ex->BoundTextures[Sampler] = nullptr;
            }
        }
        HRESULT Hr = Device->SetRenderTarget(0, Surface);
        if (FAILED(Hr))
        {
            ExLogf(kExFdumpWarning, "WARNING", __LINE__, "SetRenderTarget failed (hr 0x%08x)",
                   (unsigned int)(Hr));
            return Hr;
        }
        D3DSURFACE_DESC Desc;
        if (SUCCEEDED(Surface->GetDesc(&Desc)))
        {
            Ex->TargetWidth = Desc.Width;
            Ex->TargetHeight = Desc.Height;
        }
        Ex->CurrentTarget = Target;
        if (bKeepDepth && Ex->SavedDepth != nullptr)
        {
            // The scene depth cannot be sampled while it is the bound depth surface.
            for (unsigned long Sampler = 0; Sampler < kExSamplerCount; ++Sampler)
            {
                if ((Ex->SceneDepthSamplers & (1ul << Sampler)) != 0)
                {
                    Rp9SetTexture(Device, Sampler, nullptr);
                    Ex->BoundTextures[Sampler] = nullptr;
                }
            }
            Ex->SceneDepthSamplers = 0;
            Hr = Device->SetDepthStencilSurface(Ex->SavedDepth);
            Ex->bDepthBound = SUCCEEDED(Hr);
        }
        else
            ExUnbindDepth(Self);
        return S_OK;
    }

    // Binds a D3D texture on a sampler with explicit states. The first touch of a
    // fixed-function stage saves its cache entries (restored by EndExPass).
    GENRESULT ExBindSampler(FDirectX9* Self, unsigned long Sampler, IDirect3DBaseTexture9* Texture,
                            const FRPExSamplerState* State, bool bSceneDepth)
    {
        FRp9ExState* Ex = Self->Ex_;
        IDirect3DDevice9* Device = Self->Device_;
        if (bSceneDepth && Ex->bDepthBound)
            ExUnbindDepth(Self);
        const unsigned long Bit = 1ul << Sampler;
        if ((Ex->TouchedSamplers & Bit) == 0)
        {
            if (Sampler < FRp9DeviceStateCaches::StageCount)
                Self->ExSaveStage(Sampler, &Ex->SavedStages[Sampler]);
            Ex->TouchedSamplers |= Bit;
        }
        const HRESULT Hr = Rp9SetTexture(Device, Sampler, Texture);
        if (FAILED(Hr))
        {
            ExLogf(kExFdumpWarning, "WARNING", __LINE__, "SetTexture(%lu) failed (hr 0x%08x)",
                   Sampler, (unsigned int)(Hr));
            return (GENRESULT)(Hr);
        }
        Ex->BoundTextures[Sampler] = Texture;
        FRPExSamplerState Default;
        Default.MinMagFilter = RPExFilterPoint;
        Default.MipFilter = RPExMipNone;
        Default.AddressU = RPExAddressClamp;
        Default.AddressV = RPExAddressClamp;
        Default.AddressW = RPExAddressClamp;
        const FRPExSamplerState* Use = State != nullptr ? State : &Default;
        Rp9SetSamplerState(Device, Sampler, D3DSAMP_MAGFILTER, ExFilterToD3d(Use->MinMagFilter));
        Rp9SetSamplerState(Device, Sampler, D3DSAMP_MINFILTER, ExFilterToD3d(Use->MinMagFilter));
        Rp9SetSamplerState(Device, Sampler, D3DSAMP_MIPFILTER, ExMipFilterToD3d(Use->MipFilter));
        Rp9SetSamplerState(Device, Sampler, D3DSAMP_ADDRESSU, ExAddressToD3d(Use->AddressU));
        Rp9SetSamplerState(Device, Sampler, D3DSAMP_ADDRESSV, ExAddressToD3d(Use->AddressV));
        Rp9SetSamplerState(Device, Sampler, D3DSAMP_ADDRESSW, ExAddressToD3d(Use->AddressW));
        if (bSceneDepth && Texture != nullptr)
            Ex->SceneDepthSamplers |= Bit;
        else
            Ex->SceneDepthSamplers &= ~Bit;
        return GR_OK;
    }

    // EndExPass's body (also run by DestroyGpuResources on a pass left open).
    void ExEndPassInternal(FDirectX9* Self)
    {
        FRp9ExState* Ex = Self->Ex_;
        IDirect3DDevice9* Device = Self->Device_;
        if (Device != nullptr)
        {
            Rp9SetVertexShader(Device, nullptr);
            Rp9SetPixelShader(Device, nullptr);
            for (unsigned long Sampler = 0; Sampler < kExSamplerCount; ++Sampler)
            {
                if ((Ex->TouchedSamplers & (1ul << Sampler)) == 0)
                    continue;
                if (Sampler < FRp9DeviceStateCaches::StageCount)
                    Self->ExRestoreStage(Sampler, &Ex->SavedStages[Sampler]);
                else
                    Rp9SetTexture(Device, Sampler, nullptr);
            }
            if (Ex->SavedColor != nullptr)
                Device->SetRenderTarget(0, Ex->SavedColor);
            Device->SetDepthStencilSurface(Ex->SavedDepth);
            // SetRenderTarget reset the device viewport; put back the cached one RP9's
            // SetViewportRect / SetDepthRange last sent, with its validity bytes.
            Self->ViewportCache_ = Ex->SavedViewport;
            Self->bViewportRectValid_ = Ex->bSavedViewportRectValid;
            Self->bDepthRangeValid_ = Ex->bSavedDepthRangeValid;
            Device->SetViewport(&Self->ViewportCache_);
        }
        Self->RenderStates_.RestorePending(Ex->SavedPending);
        if (Ex->SavedColor != nullptr)
        {
            Ex->SavedColor->Release();
            Ex->SavedColor = nullptr;
        }
        if (Ex->SavedDepth != nullptr)
        {
            Ex->SavedDepth->Release();
            Ex->SavedDepth = nullptr;
        }
        Ex->TouchedSamplers = 0;
        Ex->SceneDepthSamplers = 0;
        memset(Ex->BoundTextures, 0, sizeof(Ex->BoundTextures));
        Ex->BoundProgram = nullptr;
        Ex->CurrentTarget = nullptr;
        Ex->bDepthBound = false;
        Ex->bInPass = false;
    }

    // The IRPDraw::DrawPrimitive sequence: the stream cache selects the FVF, FlushDrawState
    // sends the queued render states (the pass's included), DrawPrimitiveUP, stream cache reset.
    GENRESULT ExDrawUp(FDirectX9* Self, unsigned long Prim, unsigned long Fvf, const void* Verts,
                       unsigned long Count)
    {
        const unsigned int PrimCount = Self->PrimCountFromVerts(Prim, (unsigned int)(Count));
        if ((int)(PrimCount) <= 0 || Verts == nullptr)
            return GR_INVALID_PARMS;
        Self->StreamCache_.SelectVertexStream(nullptr, Fvf);
        Self->FlushDrawState(Self->Device_);
        const HRESULT Hr = Self->Device_->DrawPrimitiveUP((D3DPRIMITIVETYPE)(Prim), PrimCount, Verts,
                                                          Self->FvfStride((unsigned int)(Fvf)));
        // D3D9 DrawPrimitiveUP leaves stream 0 unbound; the cache forgets it as DrawPrimitive does.
        Self->StreamCache_.Reset();
        if (FAILED(Hr))
            ExLogf(kExFdumpWarning, "WARNING", __LINE__, "DrawPrimitiveUP failed (hr 0x%08x)",
                   (unsigned int)(Hr));
        return (GENRESULT)(Hr);
    }

    GENRESULT NeedExPass(FDirectX9* Self, const char* Method)
    {
        if (Self->Ex_->bInPass && Self->Device_ != nullptr)
            return GR_OK;
        ExLogf(kExFdumpWarning, "WARNING", __LINE__, "%s() called outside of an Ex pass", Method);
        return GR_GENERIC;
    }
}

FRp9ExState::FRp9ExState()
    : SceneDepth(), FallbackDepth(nullptr), BackBufferWidth(0), BackBufferHeight(0),
      bInPass(false), bDepthBound(false), SavedColor(nullptr), SavedDepth(nullptr),
      bSavedViewportRectValid(0), bSavedDepthRangeValid(0), TouchedSamplers(0),
      SceneDepthSamplers(0), BoundProgram(nullptr), CurrentTarget(nullptr), TargetWidth(0),
      TargetHeight(0), SoftKind(0), bSoftConfigRead(false), bSoftCompileFailed(false),
      bSoftActive(false), SoftVs(nullptr), SoftPs(nullptr)
{
    SoftFade[0] = SoftFade[1] = SoftFade[2] = 0.0f;
    SoftFadeOverride = 0.0f;
    memset(&SoftSavedStage1, 0, sizeof(SoftSavedStage1));
    SceneDepth.Kind = Rp9ExTextureSceneDepth;
    SceneDepth.Format = RPExFormatR32F;
    memset(&SavedViewport, 0, sizeof(SavedViewport));
    memset(SavedPending, 0, sizeof(SavedPending));
    memset(SavedStages, 0, sizeof(SavedStages));
    memset(BoundTextures, 0, sizeof(BoundTextures));
}

// ---- lifetime hooks (called from the RP8-mirrored code in RP9.cpp) ----

bool FDirectX9::ExWantsIntzDepth(D3DFORMAT AdapterFormat, D3DFORMAT DepthFormat)
{
    // Only where INTZ keeps the picked bit depth: INTZ is 24-bit depth + 8-bit stencil. A D16
    // or D32 choice keeps today's auto depth-stencil (and reports no scene depth).
    if (D3d_ == nullptr)
        return false;
    if (DepthFormat != D3DFMT_D24S8 && DepthFormat != D3DFMT_D24X8 &&
        DepthFormat != D3DFMT_D24X4S4)
        return false;
    return SUCCEEDED(D3d_->CheckDeviceFormat(AdapterIndex_, (D3DDEVTYPE)(DeviceType_),
                                             AdapterFormat, D3DUSAGE_DEPTHSTENCIL,
                                             D3DRTYPE_TEXTURE, kIntzFormat));
}

HRESULT FDirectX9::ExCreateDeviceResources(bool bIntzDepth, D3DFORMAT DepthFormat)
{
    FRp9ExState* Ex = Ex_;
    IDirect3DSurface9* BackBuffer = nullptr;
    if (SUCCEEDED(Device_->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &BackBuffer)))
    {
        D3DSURFACE_DESC Desc;
        if (SUCCEEDED(BackBuffer->GetDesc(&Desc)))
        {
            Ex->BackBufferWidth = Desc.Width;
            Ex->BackBufferHeight = Desc.Height;
        }
        BackBuffer->Release();
    }

    if (bIntzDepth)
    {
        // The device was made with EnableAutoDepthStencil = FALSE: the INTZ texture's level 0
        // is the depth surface from now on (same size as the back buffer, no multisampling).
        IDirect3DTexture9* Texture = nullptr;
        IDirect3DSurface9* Surface = nullptr;
        HRESULT Hr = Device_->CreateTexture((UINT)(Ex->BackBufferWidth),
                                            (UINT)(Ex->BackBufferHeight), 1, D3DUSAGE_DEPTHSTENCIL,
                                            kIntzFormat, D3DPOOL_DEFAULT, &Texture, nullptr);
        if (SUCCEEDED(Hr))
            Hr = Texture->GetSurfaceLevel(0, &Surface);
        if (SUCCEEDED(Hr))
        {
            Ex->SceneDepth.Texture = Texture;
            Ex->SceneDepth.Surface = Surface;
            Ex->SceneDepth.Width = Ex->BackBufferWidth;
            Ex->SceneDepth.Height = Ex->BackBufferHeight;
            Hr = Device_->SetDepthStencilSurface(Surface);
            ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "scene depth: INTZ %lux%lu",
                   Ex->BackBufferWidth, Ex->BackBufferHeight);
        }
        else
        {
            if (Texture != nullptr)
                Texture->Release();
            ExLogf(kExFdumpWarning, "WARNING", __LINE__,
                   "INTZ depth texture failed (hr 0x%08x); plain depth surface instead, no scene "
                   "depth", (unsigned int)(Hr));
            Hr = Device_->CreateDepthStencilSurface((UINT)(Ex->BackBufferWidth),
                                                    (UINT)(Ex->BackBufferHeight), DepthFormat,
                                                    D3DMULTISAMPLE_NONE, 0, FALSE,
                                                    &Ex->FallbackDepth, nullptr);
            if (SUCCEEDED(Hr))
                Hr = Device_->SetDepthStencilSurface(Ex->FallbackDepth);
        }
        if (FAILED(Hr))
            return Hr;
    }

    for (size_t Index = 0; Index < Ex->Programs.size(); ++Index)
        CreateProgramShaders(Device_, Ex->Programs[Index]);
    for (size_t Index = 0; Index < Ex->Textures.size(); ++Index)
    {
        FRPExTexture* Texture = Ex->Textures[Index];
        if (Texture->Texture != nullptr)
            continue;
        if (Texture->Kind == Rp9ExTextureRenderTarget)
            CreateRenderTargetGpu(Device_, Texture, Ex->BackBufferWidth, Ex->BackBufferHeight);
        else if (Texture->Kind == Rp9ExTextureVolume)
            CreateVolumeGpu(Device_, Texture);
    }
    if (ReadPortFade("surface_shaders") > 0.5f)
        StartSurfaceShaderWarmup();
    return S_OK;
}

void FDirectX9::ExReleaseDeviceResources()
{
    ExReleaseSurfaceInstances();
    Rp9DeviceCalls().Invalidate();
    ExShadowRelease();
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr)
        return;
    Ex->bSurfaceNormalCached=Ex->bSurfaceLightsCached=false;
    if(Device_)
    {
        // Bound textures hold a device reference; Reset needs every default-pool one gone.
        Rp9SetTexture(Device_,10,nullptr);
        Rp9SetVertexShader(Device_,nullptr);Rp9SetPixelShader(Device_,nullptr);
    }
    memset(Ex->SurfaceSamplerValid,0,sizeof(Ex->SurfaceSamplerValid));
    Ex->SurfaceBoundVs=nullptr;Ex->SurfaceBoundPs=nullptr;
    ExGpuRelease();
    if(Ex->QualitySavedState) {Ex->QualitySavedState->Release();Ex->QualitySavedState=nullptr;}
    if(Ex->WarmupFont) {Ex->WarmupFont->Release();Ex->WarmupFont=nullptr;}
    if(Ex->WarmupSavedState) {Ex->WarmupSavedState->Release();Ex->WarmupSavedState=nullptr;}
    if(Ex->QualitySceneCopy) {Ex->QualitySceneCopy->Release();Ex->QualitySceneCopy=nullptr;}
    if(Ex->QualityFxaaPs) {Ex->QualityFxaaPs->Release();Ex->QualityFxaaPs=nullptr;}
    if (Ex->bInPass)
        ExEndPassInternal(this);
    // The device must not hold the surface being released (Reset requires every
    // D3DPOOL_DEFAULT resource gone).
    if (Device_ != nullptr && (Ex->SceneDepth.Surface != nullptr || Ex->FallbackDepth != nullptr))
        Device_->SetDepthStencilSurface(nullptr);
    ReleaseExTextureGpu(&Ex->SceneDepth);
    if (Ex->FallbackDepth != nullptr)
    {
        Ex->FallbackDepth->Release();
        Ex->FallbackDepth = nullptr;
    }
    for (size_t Index = 0; Index < Ex->Textures.size(); ++Index)
    {
        if (Ex->Textures[Index]->Kind == Rp9ExTextureRenderTarget)
            ReleaseExTextureGpu(Ex->Textures[Index]);
    }
}

void FDirectX9::ExReleaseAllGpu()
{
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr)
        return;
    ExReleaseDeviceResources();
    ExSurfaceEnd();
    if (Ex->SurfaceVs != nullptr) { Ex->SurfaceVs->Release(); Ex->SurfaceVs = nullptr; }
    if (Ex->SurfaceLowPs) { Ex->SurfaceLowPs->Release(); Ex->SurfaceLowPs=nullptr; }
    if (Ex->SurfaceLowCubePs) { Ex->SurfaceLowCubePs->Release(); Ex->SurfaceLowCubePs=nullptr; }
    if (Ex->SurfacePs != nullptr) { Ex->SurfacePs->Release(); Ex->SurfacePs = nullptr; }
    if (Ex->SurfaceCubePs != nullptr) { Ex->SurfaceCubePs->Release(); Ex->SurfaceCubePs = nullptr; }
    if (Ex->SurfaceNoShadowPs) { Ex->SurfaceNoShadowPs->Release(); Ex->SurfaceNoShadowPs=nullptr; }
    if (Ex->SurfaceNoShadowCubePs) { Ex->SurfaceNoShadowCubePs->Release(); Ex->SurfaceNoShadowCubePs=nullptr; }
    Ex->SurfaceDirectLights.clear();
    Ex->bSurfaceMaterialValid = false;
    if (Ex->SoftVs != nullptr)
    {
        Ex->SoftVs->Release();
        Ex->SoftVs = nullptr;
    }
    if (Ex->SoftPs != nullptr)
    {
        Ex->SoftPs->Release();
        Ex->SoftPs = nullptr;
    }
    for (size_t Index = 0; Index < Ex->Programs.size(); ++Index)
        ReleaseProgramShaders(Ex->Programs[Index]);
    for (size_t Index = 0; Index < Ex->Textures.size(); ++Index)
        ReleaseExTextureGpu(Ex->Textures[Index]);
}

void FDirectX9::ExDestroyAll()
{
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr)
        return;
    ExReleaseAllGpu();
    for (size_t Index = 0; Index < Ex->Programs.size(); ++Index)
    {
        FRPExProgram* Program = Ex->Programs[Index];
        if (Program->FileSystem != nullptr)
            Program->FileSystem->Release();
        delete Program;
    }
    Ex->Programs.clear();
    for (size_t Index = 0; Index < Ex->Textures.size(); ++Index)
        delete Ex->Textures[Index];
    Ex->Textures.clear();
}

// ---- IRenderPipelineEx ----

GENRESULT DACOM_API FDirectX9::GetExCaps(FRPExCaps* Out)
{
    // Size-versioned (FRPExCaps): a caller built against an older header passes its smaller
    // Size and gets only the fields it knows about.
    if (Out == nullptr || Out->Size < RPExCapsSizeV1)
        return GR_INVALID_PARMS;
    if (Device_ == nullptr)
        return GR_GENERIC;
    D3DCAPS9 Caps;
    memset(&Caps, 0, sizeof(Caps));
    const HRESULT Hr = Device_->GetDeviceCaps(&Caps);
    if (FAILED(Hr))
        return (GENRESULT)(Hr);
    FRPExCaps Full;
    memset(&Full, 0, sizeof(Full));
    Full.VertexShaderVersion = (D3DSHADER_VERSION_MAJOR(Caps.VertexShaderVersion) << 8) |
                               D3DSHADER_VERSION_MINOR(Caps.VertexShaderVersion);
    Full.PixelShaderVersion = (D3DSHADER_VERSION_MAJOR(Caps.PixelShaderVersion) << 8) |
                              D3DSHADER_VERSION_MINOR(Caps.PixelShaderVersion);
    Full.MaxTextureWidth = Caps.MaxTextureWidth;
    Full.MaxTextureHeight = Caps.MaxTextureHeight;
    Full.MaxVolumeExtent = Caps.MaxVolumeExtent;
    Full.bSceneDepth = Ex_->SceneDepth.Texture != nullptr ? 1 : 0;
    Full.bVolumeTextures = (Caps.TextureCaps & D3DPTEXTURECAPS_VOLUMEMAP) != 0 ? 1 : 0;
    const UINT Adapter = AdapterIndex_;
    D3DDISPLAYMODE Mode;
    if (SUCCEEDED(Device_->GetDisplayMode(0, &Mode)))
    {
        const D3DDEVTYPE Type = (D3DDEVTYPE)(DeviceType_);
        Full.bFloat16Target =
            SUCCEEDED(D3d_->CheckDeviceFormat(Adapter, Type, Mode.Format, D3DUSAGE_RENDERTARGET,
                                              D3DRTYPE_TEXTURE, D3DFMT_A16B16G16R16F)) ? 1 : 0;
        Full.bFloat16Blending =
            SUCCEEDED(D3d_->CheckDeviceFormat(
                Adapter, Type, Mode.Format,
                D3DUSAGE_RENDERTARGET | D3DUSAGE_QUERY_POSTPIXELSHADER_BLENDING, D3DRTYPE_TEXTURE,
                D3DFMT_A16B16G16R16F)) ? 1 : 0;
        Full.bFloat32Target =
            SUCCEEDED(D3d_->CheckDeviceFormat(Adapter, Type, Mode.Format, D3DUSAGE_RENDERTARGET,
                                              D3DRTYPE_TEXTURE, D3DFMT_R32F)) ? 1 : 0;
    }
    // Version 2: shader instruction budgets and the adapter name.
    Full.MaxVertexShaderSlots = Caps.MaxVertexShader30InstructionSlots;
    Full.MaxPixelShaderSlots = Caps.MaxPixelShader30InstructionSlots;
    Full.MaxPixelShaderInstructionsExecuted = Caps.MaxPShaderInstructionsExecuted;
    D3DADAPTER_IDENTIFIER9 Identifier;
    memset(&Identifier, 0, sizeof(Identifier));
    if (D3d_ != nullptr && SUCCEEDED(D3d_->GetAdapterIdentifier(Adapter, 0, &Identifier)))
    {
        strncpy(Full.AdapterDescription, Identifier.Description,
                sizeof(Full.AdapterDescription) - 1);
        Full.AdapterDescription[sizeof(Full.AdapterDescription) - 1] = '\0';
    }
    const unsigned long Filled =
        Out->Size < (unsigned long)(sizeof(FRPExCaps)) ? Out->Size
                                                       : (unsigned long)(sizeof(FRPExCaps));
    Full.Size = Filled;
    memcpy(Out, &Full, Filled);
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::CreateExProgram(IFileSystem* FileSystem, const char* Path,
                                               const char* VsEntry, const char* PsEntry,
                                               FRPExProgram** Out)
{
    if (Out == nullptr)
        return GR_INVALID_PARMS;
    *Out = nullptr;
    if (FileSystem == nullptr || Path == nullptr || VsEntry == nullptr || PsEntry == nullptr)
        return GR_INVALID_PARMS;
    FRPExProgram* Program = new FRPExProgram();
    Program->FileSystem = FileSystem;
    FileSystem->AddRef();
    Program->Path = Path;
    Program->VsEntry = VsEntry;
    Program->PsEntry = PsEntry;
    Program->Vs = nullptr;
    Program->Ps = nullptr;
    Ex_->Programs.push_back(Program);
    *Out = Program;
    // Without a device only the bytecode is made; ExCreateDeviceResources makes the shaders.
    return CompileProgram(Device_, Program) ? GR_OK : GR_GENERIC;
}

GENRESULT DACOM_API FDirectX9::DestroyExProgram(FRPExProgram* Program)
{
    FRp9ExState* Ex = Ex_;
    for (size_t Index = 0; Index < Ex->Programs.size(); ++Index)
    {
        if (Ex->Programs[Index] != Program)
            continue;
        if (Ex->bInPass && Ex->BoundProgram == Program && Device_ != nullptr)
        {
            Rp9SetVertexShader(Device_, nullptr);
            Rp9SetPixelShader(Device_, nullptr);
            Ex->BoundProgram = nullptr;
        }
        ReleaseProgramShaders(Program);
        if (Program->FileSystem != nullptr)
            Program->FileSystem->Release();
        Ex->Programs.erase(Ex->Programs.begin() + (std::ptrdiff_t)(Index));
        delete Program;
        return GR_OK;
    }
    return GR_INVALID_PARMS;
}

GENRESULT DACOM_API FDirectX9::ReloadExPrograms()
{
    FRp9ExState* Ex = Ex_;
    bool bAllOk = true;
    for (size_t Index = 0; Index < Ex->Programs.size(); ++Index)
    {
        FRPExProgram* Program = Ex->Programs[Index];
        if (!CompileProgram(Device_, Program))
            bAllOk = false;
        // A reload inside a pass rebinds the (possibly new) shaders of the bound program.
        if (Ex->bInPass && Ex->BoundProgram == Program && Device_ != nullptr)
        {
            Rp9SetVertexShader(Device_, Program->Vs);
            Rp9SetPixelShader(Device_, Program->Ps);
        }
    }
    return bAllOk ? GR_OK : GR_GENERIC;
}

GENRESULT DACOM_API FDirectX9::CreateExRenderTarget(const FRPExRenderTargetDesc* Desc,
                                                    FRPExTexture** Out)
{
    if (Out == nullptr || Desc == nullptr)
        return GR_INVALID_PARMS;
    *Out = nullptr;
    unsigned long Bytes = 0;
    if (ExFormatToD3d(Desc->Format, &Bytes) == D3DFMT_UNKNOWN)
        return GR_INVALID_PARMS;
    if ((Desc->Width == 0 || Desc->Height == 0) && !(Desc->BackBufferScale > 0.0f))
        return GR_INVALID_PARMS;
    FRPExTexture* Target = new FRPExTexture();
    Target->Kind = Rp9ExTextureRenderTarget;
    Target->Format = Desc->Format;
    Target->TargetDesc = *Desc;
    if (Device_ != nullptr && (DeviceReady_ & 1) != 0)
    {
        const HRESULT Hr =
            CreateRenderTargetGpu(Device_, Target, Ex_->BackBufferWidth, Ex_->BackBufferHeight);
        if (FAILED(Hr))
        {
            delete Target;
            return (GENRESULT)(Hr);
        }
    }
    Ex_->Textures.push_back(Target);
    *Out = Target;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::CreateExVolumeTexture(unsigned long Width, unsigned long Height,
                                                     unsigned long Depth, ERPExFormat Format,
                                                     const void* Data, FRPExTexture** Out)
{
    if (Out == nullptr)
        return GR_INVALID_PARMS;
    *Out = nullptr;
    unsigned long Bytes = 0;
    if (ExFormatToD3d(Format, &Bytes) == D3DFMT_UNKNOWN || Width == 0 || Height == 0 || Depth == 0)
        return GR_INVALID_PARMS;
    FRPExTexture* Volume = new FRPExTexture();
    Volume->Kind = Rp9ExTextureVolume;
    Volume->Format = Format;
    Volume->Width = Width;
    Volume->Height = Height;
    Volume->Depth = Depth;
    if (Data != nullptr)
    {
        const unsigned char* Source = (const unsigned char*)(Data);
        Volume->VolumeData.assign(Source, Source + Width * Height * Depth * Bytes);
    }
    if (Device_ != nullptr)
    {
        const HRESULT Hr = CreateVolumeGpu(Device_, Volume);
        if (FAILED(Hr))
        {
            delete Volume;
            return (GENRESULT)(Hr);
        }
    }
    Ex_->Textures.push_back(Volume);
    *Out = Volume;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::DestroyExTexture(FRPExTexture* Texture)
{
    FRp9ExState* Ex = Ex_;
    if (Ex->bInPass)
    {
        ExLogf(kExFdumpWarning, "WARNING", __LINE__, "destroy_ex_texture() inside an Ex pass");
        return GR_GENERIC;
    }
    for (size_t Index = 0; Index < Ex->Textures.size(); ++Index)
    {
        if (Ex->Textures[Index] != Texture)
            continue;
        ReleaseExTextureGpu(Texture);
        Ex->Textures.erase(Ex->Textures.begin() + (std::ptrdiff_t)(Index));
        delete Texture;
        return GR_OK;
    }
    return GR_INVALID_PARMS;
}

GENRESULT DACOM_API FDirectX9::GetExTextureSize(FRPExTexture* Texture, unsigned long* OutWidth,
                                                unsigned long* OutHeight)
{
    if (Texture == nullptr || OutWidth == nullptr || OutHeight == nullptr)
        return GR_INVALID_PARMS;
    if (Texture->Texture == nullptr)
        return GR_GENERIC;
    *OutWidth = Texture->Width;
    *OutHeight = Texture->Height;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::GetSceneDepth(FRPExTexture** Out)
{
    if (Out == nullptr)
        return GR_INVALID_PARMS;
    *Out = nullptr;
    if (Ex_->SceneDepth.Texture == nullptr)
        return GR_GENERIC;
    *Out = &Ex_->SceneDepth;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::BeginExPass(const FRPExPassDesc* Desc)
{
    ExFlushSurfaceInstances();
    const GENRESULT Ready =
        NeedBuffers("begin_ex_pass() called outside of create_buffers/destroy_buffers", __LINE__);
    if (Ready != GR_OK)
        return Ready;
    FRp9ExState* Ex = Ex_;
    if (Ex->bInPass)
    {
        ExLogf(kExFdumpWarning, "WARNING", __LINE__, "begin_ex_pass(): Ex passes do not nest");
        return GR_GENERIC;
    }
    if (Desc == nullptr)
        return GR_INVALID_PARMS;
    FRPExTexture* Target = Desc->ColorTarget;
    if (Target != nullptr && (Target->Kind != Rp9ExTextureRenderTarget || Target->Surface == nullptr))
        return GR_INVALID_PARMS;

    IDirect3DSurface9* Color = nullptr;
    const HRESULT ColorHr = Device_->GetRenderTarget(0, &Color);
    if (FAILED(ColorHr))
    {
        ExLogf(kExFdumpWarning, "WARNING", __LINE__, "GetRenderTarget failed (hr 0x%08x)",
               (unsigned int)(ColorHr));
        return (GENRESULT)(ColorHr);
    }
    IDirect3DSurface9* Depth = nullptr;
    if (FAILED(Device_->GetDepthStencilSurface(&Depth))) // D3DERR_NOTFOUND: none bound
        Depth = nullptr;
    Ex->SavedColor = Color;
    Ex->SavedDepth = Depth;
    Ex->SavedViewport = ViewportCache_;
    Ex->bSavedViewportRectValid = bViewportRectValid_;
    Ex->bSavedDepthRangeValid = bDepthRangeValid_;
    for (unsigned int StateId = 0; StateId < FRp9RenderStateCache::StateCount; ++StateId)
        Ex->SavedPending[StateId] = RenderStates_.Entries[StateId].Pending;
    Ex->TouchedSamplers = 0;
    Ex->SceneDepthSamplers = 0;
    memset(Ex->BoundTextures, 0, sizeof(Ex->BoundTextures));
    Ex->BoundProgram = nullptr;
    Ex->CurrentTarget = nullptr;
    Ex->bDepthBound = Depth != nullptr;
    // A pass may draw before binding a program: no surface shader may remain bound.
    ExSurfaceRelease();
    Ex->bInPass = true;
    ExGpuMark(FRp9GpuTimers::ExBegin);

    // The pass's starting render states (through the cache; EndExPass re-queues the old ones).
    ExSetPassState(this, D3DRS_ALPHABLENDENABLE, FALSE);
    ExSetPassState(this, D3DRS_ALPHATESTENABLE, FALSE);
    ExSetPassState(this, D3DRS_FOGENABLE, FALSE);
    ExSetPassState(this, D3DRS_STENCILENABLE, FALSE);
    ExSetPassState(this, D3DRS_CULLMODE, D3DCULL_NONE);
    ExSetPassState(this, D3DRS_LIGHTING, FALSE);
    ExSetPassState(this, D3DRS_COLORWRITEENABLE, 0xF);

    const HRESULT Hr = ExSelectTarget(this, Target, (Desc->Flags & RPExPassKeepDepth) != 0);
    if (FAILED(Hr))
    {
        ExEndPassInternal(this);
        return (GENRESULT)(Hr);
    }
    if ((Desc->Flags & RPExPassClearColor) != 0)
    {
        const HRESULT ClearHr = Device_->Clear(0, nullptr, D3DCLEAR_TARGET, Desc->ClearColor, 1.0f, 0);
        if (FAILED(ClearHr))
            ExLogf(kExFdumpWarning, "WARNING", __LINE__, "Clear failed (hr 0x%08x)",
                   (unsigned int)(ClearHr));
    }
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::EndExPass()
{
    if (!Ex_->bInPass)
    {
        ExLogf(kExFdumpWarning, "WARNING", __LINE__, "end_ex_pass() without begin_ex_pass()");
        return GR_GENERIC;
    }
    ExEndPassInternal(this);
    ExGpuMark(FRp9GpuTimers::ExEnd);
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetExRenderTarget(FRPExTexture* ColorTarget,
                                                 unsigned long bKeepDepth)
{
    ExFlushSurfaceInstances();
    const GENRESULT Ready = NeedExPass(this, "set_ex_render_target");
    if (Ready != GR_OK)
        return Ready;
    if (ColorTarget != nullptr &&
        (ColorTarget->Kind != Rp9ExTextureRenderTarget || ColorTarget->Surface == nullptr))
        return GR_INVALID_PARMS;
    return (GENRESULT)(ExSelectTarget(this, ColorTarget, bKeepDepth != 0));
}

GENRESULT DACOM_API FDirectX9::BindExProgram(FRPExProgram* Program)
{
    const GENRESULT Ready = NeedExPass(this, "bind_ex_program");
    if (Ready != GR_OK)
        return Ready;
    if (Program == nullptr)
    {
        Rp9SetVertexShader(Device_, nullptr);
        Rp9SetPixelShader(Device_, nullptr);
        Ex_->BoundProgram = nullptr;
        return GR_OK;
    }
    // A program that never compiled has no shaders; its compile errors are already logged.
    if (Program->Vs == nullptr || Program->Ps == nullptr)
        return GR_GENERIC;
    Rp9SetVertexShader(Device_, Program->Vs);
    Rp9SetPixelShader(Device_, Program->Ps);
    Ex_->BoundProgram = Program;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetExVertexConstants(unsigned long StartRegister, const float* Data,
                                                    unsigned long Vector4Count)
{
    if (Device_ == nullptr || Data == nullptr)
        return GR_GENERIC;
    return (GENRESULT)(Rp9SetVertexConstants(Device_, (UINT)(StartRegister), Data,
                                                         (UINT)(Vector4Count)));
}

GENRESULT DACOM_API FDirectX9::SetExPixelConstants(unsigned long StartRegister, const float* Data,
                                                   unsigned long Vector4Count)
{
    if (Device_ == nullptr || Data == nullptr)
        return GR_GENERIC;
    return (GENRESULT)(Rp9SetPixelConstants(Device_, (UINT)(StartRegister), Data,
                                                        (UINT)(Vector4Count)));
}

GENRESULT DACOM_API FDirectX9::BindExTexture(unsigned long Sampler, FRPExTexture* Texture,
                                             const FRPExSamplerState* State)
{
    const GENRESULT Ready = NeedExPass(this, "bind_ex_texture");
    if (Ready != GR_OK)
        return Ready;
    if (Sampler >= kExSamplerCount)
        return GR_INVALID_PARMS;
    if (Texture != nullptr)
    {
        if (Texture->Texture == nullptr)
            return GR_GENERIC; // lost render target, or no scene depth
        if (Texture == Ex_->CurrentTarget)
        {
            ExLogf(kExFdumpWarning, "WARNING", __LINE__,
                   "bind_ex_texture(): the texture is the current render target");
            return GR_GENERIC;
        }
    }
    const bool bSceneDepth = Texture != nullptr && Texture == &Ex_->SceneDepth;
    return ExBindSampler(this, Sampler, Texture != nullptr ? Texture->Texture : nullptr, State,
                         bSceneDepth);
}

GENRESULT DACOM_API FDirectX9::BindExPipelineTexture(unsigned long Sampler, void* Handle,
                                                     const FRPExSamplerState* State)
{
    const GENRESULT Ready = NeedExPass(this, "bind_ex_pipeline_texture");
    if (Ready != GR_OK)
        return Ready;
    if (Sampler >= kExSamplerCount)
        return GR_INVALID_PARMS;
    IDirect3DBaseTexture9* Texture = PipelineTextureFromHandle(Handle);
    if (Handle != nullptr && Texture == nullptr)
        return GR_GENERIC;
    return ExBindSampler(this, Sampler, Texture, State, false);
}

// ---- IRPDrawEx ----

GENRESULT DACOM_API FDirectX9::DrawFullscreenQuad()
{
    const GENRESULT Ready = NeedExPass(this, "draw_fullscreen_quad");
    if (Ready != GR_OK)
        return Ready;
    if (Ex_->BoundProgram == nullptr || Ex_->TargetWidth == 0 || Ex_->TargetHeight == 0)
        return GR_GENERIC;
    // Direct3D 9 puts pixel centres on integer coordinates, texel centres sit half a texel in:
    // shifting the quad by half a pixel left and up (1/W, 1/H in clip units) makes pixel (i, j)
    // sample UV ((i + 0.5) / W, (j + 0.5) / H) exactly.
    const float HalfX = 1.0f / (float)(Ex_->TargetWidth);
    const float HalfY = 1.0f / (float)(Ex_->TargetHeight);
    struct FQuadVertex
    {
        float X;
        float Y;
        float Z;
        float U;
        float V;
    };
    const FQuadVertex Quad[4] = {
        {-1.0f - HalfX, 1.0f + HalfY, 0.0f, 0.0f, 0.0f},
        {1.0f - HalfX, 1.0f + HalfY, 0.0f, 1.0f, 0.0f},
        {-1.0f - HalfX, -1.0f + HalfY, 0.0f, 0.0f, 1.0f},
        {1.0f - HalfX, -1.0f + HalfY, 0.0f, 1.0f, 1.0f},
    };
    return ExDrawUp(this, D3DPT_TRIANGLESTRIP, D3DFVF_XYZ | D3DFVF_TEX1, Quad, 4);
}

GENRESULT DACOM_API FDirectX9::DrawExPrimitiveUp(unsigned long Prim, unsigned long Fvf,
                                                 const void* Verts, unsigned long Count)
{
    const GENRESULT Ready = NeedExPass(this, "draw_ex_primitive_up");
    if (Ready != GR_OK)
        return Ready;
    if (Ex_->BoundProgram == nullptr)
        return GR_GENERIC;
    return ExDrawUp(this, Prim, Fvf, Verts, Count);
}

// ---- soft particles ----

namespace
{
    // vs_3_0 + ps_3_0: the fixed-function transform and stage 0 (SELECTARG1 / SELECTARG2 /
    // MODULATE of the texture and the diffuse colour) and fog, plus the fade against the scene
    // depth. Built in so it needs no DATA_EXTRA.
    const char kSoftParticleShader[] =
        "row_major float4x4 WorldView : register(c0);\n"
        "row_major float4x4 Proj : register(c4);\n"
        "struct FVsIn { float4 Pos : POSITION; float4 Col : COLOR0; float2 Uv : TEXCOORD0; };\n"
        "struct FVsOut { float4 Pos : POSITION; float4 Col : COLOR0; float2 Uv : TEXCOORD0;\n"
        "                float ViewZ : TEXCOORD1; };\n"
        "FVsOut VSMain(FVsIn In)\n"
        "{\n"
        "    FVsOut Out;\n"
        "    float4 V = mul(float4(In.Pos.xyz, 1.0), WorldView);\n"
        "    Out.Pos = mul(V, Proj);\n"
        "    Out.Col = In.Col;\n"
        "    Out.Uv = In.Uv;\n"
        "    Out.ViewZ = V.z;\n"
        "    return Out;\n"
        "}\n"
        "sampler2D Tex0 : register(s0);\n"
        "sampler2D SceneDepth : register(s1);\n"
        "float4 Fade : register(c0);     // 1 / fade distance, scale rgb too, colour op, alpha op\n"
        "float4 ProjZ : register(c1);    // depth = (x z + y) / (z z + w)\n"
        "float4 Screen : register(c2);   // 1 / depth width, 1 / depth height\n"
        "float4 Fog : register(c3);      // start, end, density, mode (0 none, 1 exp, 2 exp2, 3 linear)\n"
        "float4 FogColor : register(c4);\n"
        "float4 StageOp(float Op, float4 T, float4 D)\n"
        "{\n"
        "    return Op < 2.5 ? T : (Op < 3.5 ? D : T * D);\n"
        "}\n"
        "float4 PSMain(FVsOut In, float2 Pixel : VPOS) : COLOR\n"
        "{\n"
        "    float4 T = tex2D(Tex0, In.Uv);\n"
        "    float4 C = float4(StageOp(Fade.z, T, In.Col).rgb, StageOp(Fade.w, T, In.Col).a);\n"
        "    float Device = tex2D(SceneDepth, (Pixel + 0.5) * Screen.xy).r;\n"
        "    float Scene = abs((ProjZ.y - Device * ProjZ.w) / (Device * ProjZ.z - ProjZ.x));\n"
        "    float F = saturate((Scene - In.ViewZ) * Fade.x);\n"
        "    if (Fog.w > 0.5)\n"
        "    {\n"
        "        float K;\n"
        "        if (Fog.w > 2.5)\n"
        "            K = saturate((Fog.y - In.ViewZ) / max(Fog.y - Fog.x, 1.0e-4));\n"
        "        else if (Fog.w > 1.5)\n"
        "            K = exp(-(In.ViewZ * Fog.z) * (In.ViewZ * Fog.z));\n"
        "        else\n"
        "            K = exp(-In.ViewZ * Fog.z);\n"
        "        C.rgb = lerp(FogColor.rgb, C.rgb, saturate(K));\n"
        "    }\n"
        "    C.a *= F;\n"
        "    if (Fade.y > 0.5)\n"
        "        C.rgb *= F;\n"
        "    return C;\n"
        "}\n";

    // Direct3D 8 numbers of the render and stage states read here (the caches use them).
    const unsigned int kRsZEnable = 7;
    const unsigned int kRsZWriteEnable = 14;
    const unsigned int kRsSrcBlend = 19;
    const unsigned int kRsAlphaBlendEnable = 27;
    const unsigned int kRsFogEnable = 28;
    const unsigned int kRsFogColor = 34;
    const unsigned int kRsFogTableMode = 35;
    const unsigned int kRsFogStart = 36;
    const unsigned int kRsFogEnd = 37;
    const unsigned int kRsFogDensity = 38;
    const unsigned int kRsLighting = 137;
    const unsigned int kRsFogVertexMode = 140;
    const unsigned long kTssColorOp = 1;
    const unsigned long kTssColorArg1 = 2;
    const unsigned long kTssColorArg2 = 3;
    const unsigned long kTssAlphaOp = 4;
    const unsigned long kTssAlphaArg1 = 5;
    const unsigned long kTssAlphaArg2 = 6;

    float FloatBits(unsigned long Bits)
    {
        float Value;
        memcpy(&Value, &Bits, sizeof(Value));
        return Value;
    }

    float ReadShadowSetting(const char* Key, float Default, float Min, float Max)
    {
        char Path[MAX_PATH]={};
        DWORD Length=GetModuleFileNameA(nullptr,Path,MAX_PATH);
        if(!Length || Length>=MAX_PATH) return Default;
        char* Slash=strrchr(Path,'\\'); if(!Slash) return Default;
        strcpy(Slash+1,"port.ini");
        char Text[64]={};
        GetPrivateProfileStringA("Render",Key,"",Text,sizeof(Text),Path);
        char* End=nullptr;
        double Value=strtod(Text,&End);
        if(End==Text || !std::isfinite(Value)) return Default;
        return (float)std::fmax(Min,std::fmin(Max,Value));
    }

    // port.ini next to the exe, [Render] <Key> (metres; 0 or missing = off).
    float ReadPortFade(const char* Key)
    {
        char Path[MAX_PATH];
        const DWORD Length = GetModuleFileNameA(nullptr, Path, MAX_PATH);
        if (Length == 0 || Length >= MAX_PATH)
            return 0.0f;
        char* Slash = strrchr(Path, '\\');
        if (Slash == nullptr)
            return 0.0f;
        strcpy(Slash + 1, "port.ini");
        char Text[64] = {};
        GetPrivateProfileStringA("Render", Key, "0", Text, sizeof(Text), Path);
        const double Value = atof(Text);
        return Value > 0.0 ? (float)(Value) : 0.0f;
    }

    // Surface shader warm-up: at device creation (in the menus) every surface variant is compiled
// into the RP9 shader cache on worker threads, one per variant. A full variant takes 25-60 s
// to compile; until the warm-up finishes, ExSurfaceBegin draws with the native materials
// instead of compiling on the render thread. The sources and prefixes match ExSurfaceBegin
// and ExFlushSurfaceInstances exactly, so the later compiles there are cache hits.
std::atomic<int> G_SurfaceWarmState{0}; // 0 not started, 1 compiling, 2 finished
std::atomic<int> G_SurfaceWarmPending{0};
int G_SurfaceWarmTotal = 0;

void StartSurfaceShaderWarmup()
{
    int Expected = 0;
    if (!G_SurfaceWarmState.compare_exchange_strong(Expected, 1))
        return;
    char Module[MAX_PATH] = {};
    const DWORD Length = GetModuleFileNameA(nullptr, Module, MAX_PATH);
    char* Slash = strrchr(Module, '\\');
    std::string Source;
    if (Length > 0 && Length < MAX_PATH && Slash != nullptr)
    {
        Slash[1] = '\0';
        const std::string Path = std::string(Module) + "../DATA_EXTRA/SHADERS/surface_material.hlsl";
        if (FILE* File = fopen(Path.c_str(), "rb"))
        {
            char Buffer[4096]; size_t N;
            while ((N = fread(Buffer, 1, sizeof(Buffer), File)) != 0) Source.append(Buffer, N);
            fclose(File);
        }
    }
    if (Source.empty())
    {
        G_SurfaceWarmState = 2;
        return;
    }
    struct FJob { std::string Text; const char* Entry; const char* Profile; };
    std::vector<FJob> Jobs = {
        {Source, "VSMain", "vs_3_0"},
        {"#define SURFACE_INSTANCED 1\n" + Source, "VSMain", "vs_3_0"}};
    const char* Variants[3] = {"", "#define SURFACE_NO_SHADOW 1\n", "#define SURFACE_LOW_DETAIL 1\n"};
    for (const char* Variant : Variants)
        for (const char* Cube : {"", "#define SURFACE_ENV_CUBE 1\n"})
            Jobs.push_back({std::string(Variant) + Cube + Source, "PSMain", "ps_3_0"});
    G_SurfaceWarmTotal = (int)Jobs.size();
    G_SurfaceWarmPending = (int)Jobs.size();
    for (FJob& Job : Jobs)
    {
        std::thread([Job]() {
            std::vector<unsigned char> Code; std::string Messages; bool Hit = false, Stored = false;
            Rp9ShaderCache::Compile(Job.Text, nullptr, Job.Entry, Job.Profile, 0, &Code, &Messages, &Hit, &Stored);
            if (--G_SurfaceWarmPending == 0)
                G_SurfaceWarmState = 2;
        }).detach();
    }
    ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "surface shader warm-up: %u variants on worker threads",
           (unsigned)Jobs.size());
}

// Stage-0 op the shader can stand in for: SELECTARG1 (2) / SELECTARG2 (3) / MODULATE (4)
    // with arg1 the texture and arg2 the diffuse colour (or CURRENT, the same on stage 0).
    bool SoftStageOk(const FRp9TextureStageState* Stage, unsigned long OpType, unsigned long Arg1Type,
                     unsigned long Arg2Type, float* OutOp)
    {
        const unsigned long Op = Stage[OpType].bValid != 0 ? Stage[OpType].Value : 0;
        if (Op < 2 || Op > 4)
            return false;
        const unsigned long Arg1 = Stage[Arg1Type].bValid != 0 ? Stage[Arg1Type].Value : D3DTA_TEXTURE;
        const unsigned long Arg2 = Stage[Arg2Type].bValid != 0 ? Stage[Arg2Type].Value : D3DTA_CURRENT;
        if (Op != 3 && Arg1 != D3DTA_TEXTURE)
            return false;
        if (Op != 2 && Arg2 != D3DTA_DIFFUSE && Arg2 != D3DTA_CURRENT)
            return false;
        *OutOp = (float)(Op);
        return true;
    }

    void MulMatrix4(const float* A, const float* B, float* Out)
    {
        for (int Row = 0; Row < 4; ++Row)
            for (int Col = 0; Col < 4; ++Col)
                Out[Row * 4 + Col] = (float)((double)(A[Row * 4 + 0]) * B[0 * 4 + Col] +
                                             (double)(A[Row * 4 + 1]) * B[1 * 4 + Col] +
                                             (double)(A[Row * 4 + 2]) * B[2 * 4 + Col] +
                                             (double)(A[Row * 4 + 3]) * B[3 * 4 + Col]);
    }
}

GENRESULT DACOM_API FDirectX9::SetSoftParticles(unsigned long Kind)
{
    FRp9ExState* Ex = Ex_;
    if (!Ex->bSoftConfigRead)
    {
        Ex->bSoftConfigRead = true;
        Ex->SoftFade[RPExSoftEffects] = ReadPortFade("soft_particles_effects");
        Ex->SoftFade[RPExSoftClouds] = ReadPortFade("soft_particles_clouds");
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "soft particles: effects %.1f, clouds %.1f",
               (double)(Ex->SoftFade[RPExSoftEffects]), (double)(Ex->SoftFade[RPExSoftClouds]));
    }
    Ex->SoftKind = Kind <= RPExSoftClouds ? Kind : RPExSoftOff;
    Ex->SoftFadeOverride = 0.0f;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetSoftParticleFade(float Metres)
{
    Ex_->SoftFadeOverride = Metres > 0.0f ? Metres : 0.0f;
    return GR_OK;
}

bool FDirectX9::ExSoftBegin()
{
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr || Ex->bShadowDrawing || Ex->SoftKind == RPExSoftOff || Ex->bInPass || Ex->bSoftCompileFailed ||
        Device_ == nullptr || Ex->SceneDepth.Texture == nullptr || Ex->SceneDepth.Surface == nullptr)
        return false;
    const float FadeDistance =
        Ex->SoftFadeOverride > 0.0f ? Ex->SoftFadeOverride : Ex->SoftFade[Ex->SoftKind];
    if (!(FadeDistance > 0.0f))
        return false;

    // The vertices: XYZ, a diffuse colour, a 2D first texture coordinate.
    unsigned long Fvf = StreamCache_.Fvf;
    if (Fvf == 0 && StreamCache_.VertexBuffer != nullptr)
        Fvf = StreamCache_.VertexBuffer->Fvf;
    if ((Fvf & D3DFVF_POSITION_MASK) != D3DFVF_XYZ || (Fvf & D3DFVF_DIFFUSE) == 0 ||
        ((Fvf & D3DFVF_TEXCOUNT_MASK) >> D3DFVF_TEXCOUNT_SHIFT) == 0 || (Fvf & 0x30000) != 0)
        return false;
    // Blended, depth-tested, not writing depth, unlit; the blend is SRCALPHA or ONE.
    const unsigned long SrcBlend = RenderStates_.GetPending(kRsSrcBlend);
    if (RenderStates_.GetPending(kRsZEnable) == 0 || RenderStates_.GetPending(kRsZWriteEnable) != 0 ||
        RenderStates_.GetPending(kRsAlphaBlendEnable) == 0 || RenderStates_.GetPending(kRsLighting) != 0 ||
        (SrcBlend != D3DBLEND_SRCALPHA && SrcBlend != D3DBLEND_ONE))
        return false;
    const FRp9TextureStageState* Stage0 = DeviceStates_.TextureStates[0];
    const FRp9TextureStageState* Stage1 = DeviceStates_.TextureStates[1];
    float ColorOp = 0.0f;
    float AlphaOp = 0.0f;
    if (!SoftStageOk(Stage0, kTssColorOp, kTssColorArg1, kTssColorArg2, &ColorOp) ||
        !SoftStageOk(Stage0, kTssAlphaOp, kTssAlphaArg1, kTssAlphaArg2, &AlphaOp))
        return false;
    if (Stage1[kTssColorOp].bValid != 0 && Stage1[kTssColorOp].Value != D3DTOP_DISABLE)
        return false;

    if (Ex->SoftVs == nullptr || Ex->SoftPs == nullptr)
    {
        std::vector<unsigned char> VsCode;
        std::vector<unsigned char> PsCode;
        const std::string Source(kSoftParticleShader);
        const std::string Name("soft particles (RP9 built-in)");
        bool bOk = CompileStage(Source, Name, nullptr, "VSMain", "vs_3_0", &VsCode) &&
                   CompileStage(Source, Name, nullptr, "PSMain", "ps_3_0", &PsCode);
        if (bOk && Ex->SoftVs == nullptr)
            bOk = SUCCEEDED(Device_->CreateVertexShader((const DWORD*)(&VsCode[0]), &Ex->SoftVs));
        if (bOk && Ex->SoftPs == nullptr)
            bOk = SUCCEEDED(Device_->CreatePixelShader((const DWORD*)(&PsCode[0]), &Ex->SoftPs));
        if (!bOk)
        {
            ExLogf(kExFdumpError, "ERROR", __LINE__, "soft particles: shaders unavailable, off");
            Ex->bSoftCompileFailed = true;
            return false;
        }
    }

    // Vertex constants: world * view, projection (as the fixed-function pipeline has them).
    float VsConstants[32];
    MulMatrix4(Transforms_.World.Values, Transforms_.View.Values, &VsConstants[0]);
    memcpy(&VsConstants[16], Transforms_.Projection.Values, sizeof(float) * 16);
    const float* const P = Transforms_.Projection.Values;

    // Fog as the fixed-function pipeline would apply it (table mode first, then vertex mode).
    float FogMode = 0.0f;
    if (RenderStates_.GetPending(kRsFogEnable) != 0)
    {
        unsigned long Mode = RenderStates_.GetPending(kRsFogTableMode);
        if (Mode == D3DFOG_NONE)
            Mode = RenderStates_.GetPending(kRsFogVertexMode);
        FogMode = (float)(Mode);
    }
    const unsigned long FogColor = RenderStates_.GetPending(kRsFogColor);
    const float PsConstants[20] = {
        1.0f / FadeDistance, SrcBlend == D3DBLEND_ONE ? 1.0f : 0.0f, ColorOp, AlphaOp,
        P[10], P[14], P[11], P[15],
        1.0f / (float)(Ex->SceneDepth.Width), 1.0f / (float)(Ex->SceneDepth.Height), 0.0f, 0.0f,
        FloatBits(RenderStates_.GetPending(kRsFogStart)), FloatBits(RenderStates_.GetPending(kRsFogEnd)),
        FloatBits(RenderStates_.GetPending(kRsFogDensity)), FogMode,
        (float)((FogColor >> 16) & 0xff) / 255.0f, (float)((FogColor >> 8) & 0xff) / 255.0f,
        (float)(FogColor & 0xff) / 255.0f, 1.0f,
    };

    // The scene depth cannot be the depth surface while it is sampled: the shader does the
    // depth test itself (the fade is zero behind the scene).
    Device_->SetDepthStencilSurface(nullptr);
    ExSaveStage(1, &Ex->SoftSavedStage1);
    Rp9SetTexture(Device_, 1, Ex->SceneDepth.Texture);
    Rp9SetSamplerState(Device_, 1, D3DSAMP_MAGFILTER, D3DTEXF_POINT);
    Rp9SetSamplerState(Device_, 1, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    Rp9SetSamplerState(Device_, 1, D3DSAMP_MIPFILTER, D3DTEXF_NONE);
    Rp9SetSamplerState(Device_, 1, D3DSAMP_ADDRESSU, D3DTADDRESS_CLAMP);
    Rp9SetSamplerState(Device_, 1, D3DSAMP_ADDRESSV, D3DTADDRESS_CLAMP);
    Rp9SetVertexShader(Device_, Ex->SoftVs);
    Rp9SetPixelShader(Device_, Ex->SoftPs);
    Rp9SetVertexConstants(Device_, 0, VsConstants, 8);
    Rp9SetPixelConstants(Device_, 0, PsConstants, 5);
    Ex->bSoftActive = true;
    return true;
}

void FDirectX9::ExSoftEnd()
{
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr || !Ex->bSoftActive)
        return;
    Ex->bSoftActive = false;
    Rp9SetVertexShader(Device_, nullptr);
    Rp9SetPixelShader(Device_, nullptr);
    ExRestoreStage(1, &Ex->SoftSavedStage1);
    Device_->SetDepthStencilSurface(Ex->SceneDepth.Surface);
}

// ---- generic surface materials ------------------------------------------------------------

GENRESULT DACOM_API FDirectX9::SetSurfaceShader(unsigned long Shader, float Roughness,
                                               float EnvironmentStrength)
{
    if (Shader > RPSurfaceReflective || !std::isfinite(Roughness) || !std::isfinite(EnvironmentStrength))
        return GR_INVALID_PARMS;
    Ex_->SurfaceShader = Shader;
    Ex_->SurfaceRoughness = Roughness;
    Ex_->SurfaceEnvironment = EnvironmentStrength;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetCockpitSurface(unsigned long Enabled)
{
    Ex_->bSurfaceCockpit=Enabled!=0;return GR_OK;
}
GENRESULT DACOM_API FDirectX9::SetGlassSurface(unsigned long Enabled)
{
    Ex_->bSurfaceGlass=Enabled!=0;return GR_OK;
}

bool FDirectX9::ExSurfaceBegin()
{
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr || Device_ == nullptr || Ex->bInPass || Ex->bShadowDrawing || Ex->bSoftActive ||
        Ex->bSurfaceActive || !Ex->bSurfaceMaterialValid)
        return false;
    if (!Ex->bSurfaceConfigRead)
    {
        Ex->bSurfaceConfigRead = true;
        Ex->bSurfaceEnabled = ReadPortFade("surface_shaders") > 0.5f;
        Ex->SurfaceHighlights=ReadShadowSetting("surface_highlights",1.35f,0,4);
        Ex->SurfaceCoat=ReadShadowSetting("surface_clearcoat",0.9f,0,3);
        Ex->SurfaceBrushed=ReadShadowSetting("surface_brushed",0.8f,0,3);
        Ex->bCockpitShader=ReadShadowSetting("cockpit_shader",1,0,1)>0.5f;
        Ex->bGlassShader=ReadShadowSetting("glass_shader",1,0,1)>0.5f;
        Ex->SurfaceCockpitStrength=ReadShadowSetting("cockpit_finish",0.65f,0,2);
        Ex->SurfaceGlassStrength=ReadShadowSetting("glass_reflections",1.5f,0,4);
    }
    if (!Ex->bSurfaceEnabled || Ex->SurfaceShader == RPSurfaceLegacy ||
        (Ex->SurfaceDistanceTier==2 && !Ex->bSurfaceCockpit))
        return false;
    const bool Blended=RenderStates_.GetPending(kRsAlphaBlendEnable)!=0;
    const bool Glass=Ex->bSurfaceGlass && Ex->bGlassShader && Blended;
    const bool Cockpit=Ex->bSurfaceCockpit && Ex->bCockpitShader && !Blended;
    // Native glass back-face/opaque pass is retained. Only its authored alpha pass
    // receives the glass finish; unrelated transparent materials remain excluded.
    if(Ex->bSurfaceGlass && !Blended) return false;
    if(Glass && (RenderStates_.GetPending(D3DRS_SRCBLEND)!=D3DBLEND_SRCALPHA ||
                 RenderStates_.GetPending(D3DRS_DESTBLEND)!=D3DBLEND_INVSRCALPHA)) return false;
    unsigned long Fvf = StreamCache_.Fvf;
    if (Fvf == 0 && StreamCache_.VertexBuffer != nullptr)
        Fvf = StreamCache_.VertexBuffer->Fvf;
    const unsigned long TexCount = (Fvf & D3DFVF_TEXCOUNT_MASK) >> D3DFVF_TEXCOUNT_SHIFT;
    // Rigid lit surfaces only. Skinned/RHW, particles, transparent/glass and special
    // multi-stage materials keep their authored fixed-function path.
    if ((Fvf & D3DFVF_POSITION_MASK) != D3DFVF_XYZ || (!(Fvf & D3DFVF_NORMAL) && !Glass) ||
        (TexCount == 0 && !Glass && !Cockpit) || TexCount > 3 || (Fvf & 0xffff0000ul) != 0 ||
        RenderStates_.GetPending(kRsLighting) == 0 ||
        (Blended && !Glass))
        return false;
    auto Tss = [&](unsigned Stage, unsigned Type, unsigned Default) -> unsigned long {
        auto const& S = DeviceStates_.TextureStates[Stage][Type];
        return S.bValid ? S.Value : Default;
    };
    int EnvStage = -1;
    for (unsigned Stage = 0; Stage < 2; ++Stage)
    {
        if (Tss(Stage, kTssColorOp, Stage == 0 ? D3DTOP_MODULATE : D3DTOP_DISABLE) == D3DTOP_DISABLE)
            break;
        if ((Tss(Stage, D3DTSS_TEXCOORDINDEX, Stage) & 0xffff0000ul) == D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR)
        {
            EnvStage = (int)Stage;
            break;
        }
    }
    const bool PlainShadowReceiver = EnvStage < 0 &&
        ((Ex->bShadowReceiver && (Ex->ShadowReadyMask&3u)==3u) ||
         (Ex->bWeaponGlintReceiver && Ex->WeaponGlintReceiverMask!=0) || Cockpit || Glass);
    if ((!PlainShadowReceiver && EnvStage < 0) ||
        Tss(EnvStage < 0 ? 1 : EnvStage + 1, kTssColorOp, D3DTOP_DISABLE) != D3DTOP_DISABLE)
        return false;
    const unsigned long EnvColorOp = PlainShadowReceiver ? D3DTOP_MODULATE2X : Tss(EnvStage, kTssColorOp, D3DTOP_MODULATE2X);
    if (!PlainShadowReceiver && ((EnvColorOp != D3DTOP_SELECTARG1 && EnvColorOp != D3DTOP_MODULATE &&
         EnvColorOp != D3DTOP_MODULATE2X && EnvColorOp != D3DTOP_MODULATE4X &&
         EnvColorOp != D3DTOP_ADD) ||
        Tss(EnvStage, kTssColorArg1, D3DTA_TEXTURE) != D3DTA_TEXTURE ||
        Tss(EnvStage, kTssColorArg2, D3DTA_CURRENT) != D3DTA_CURRENT))
        return false;
    void* EnvHandle = PlainShadowReceiver ? nullptr : DeviceStates_.TextureBindings[EnvStage].Handle;
    if (!PlainShadowReceiver && !DeviceStates_.TextureBindings[EnvStage].bValid)
        return false;
    IDirect3DBaseTexture9* EnvTexture = PipelineTextureFromHandle(EnvHandle);
    if (!PlainShadowReceiver && (EnvTexture == nullptr || (EnvTexture->GetType() != D3DRTYPE_TEXTURE &&
                                 EnvTexture->GetType() != D3DRTYPE_CUBETEXTURE)))
        return false;
    const bool IsCube = EnvTexture && EnvTexture->GetType() == D3DRTYPE_CUBETEXTURE;
    bool& CompileFailed = IsCube ? Ex->bSurfaceCubeCompileFailed : Ex->bSurfaceCompileFailed;
    if (CompileFailed)
        return false;
    const bool WantsBase=EnvStage>0 || PlainShadowReceiver;
    auto* BaseTexture=PipelineTextureFromHandle(DeviceStates_.TextureBindings[0].Handle);
    const bool HasBase=WantsBase && DeviceStates_.TextureBindings[0].bValid && BaseTexture &&
                       BaseTexture->GetType()==D3DRTYPE_TEXTURE;
    if(WantsBase && !HasBase && !Glass && !Cockpit) return false;
    unsigned long ColorOp = D3DTOP_SELECTARG2, AlphaOp = D3DTOP_SELECTARG2;
    unsigned long BaseUv = 0;
    if (HasBase)
    {
        ColorOp = Tss(0, kTssColorOp, D3DTOP_MODULATE);
        AlphaOp = Tss(0, kTssAlphaOp, D3DTOP_SELECTARG1);
        BaseUv = Tss(0, D3DTSS_TEXCOORDINDEX, 0);
        if (BaseUv >= TexCount || ColorOp < 2 || ColorOp > 5 || AlphaOp < 2 || AlphaOp > 5 ||
            Tss(0, kTssColorArg1, D3DTA_TEXTURE) != D3DTA_TEXTURE ||
            (Tss(0, kTssColorArg2, D3DTA_DIFFUSE) != D3DTA_DIFFUSE &&
             Tss(0, kTssColorArg2, D3DTA_DIFFUSE) != D3DTA_CURRENT) ||
            Tss(0, D3DTSS_TEXTURETRANSFORMFLAGS, 0) != 0)
            return false;
        if (Tss(0, kTssAlphaArg1, D3DTA_TEXTURE) != D3DTA_TEXTURE ||
            (Tss(0, kTssAlphaArg2, D3DTA_CURRENT) != D3DTA_CURRENT &&
             Tss(0, kTssAlphaArg2, D3DTA_CURRENT) != D3DTA_DIFFUSE))
            return false;
        auto* Base = PipelineTextureFromHandle(DeviceStates_.TextureBindings[0].Handle);
        if (!DeviceStates_.TextureBindings[0].bValid || Base == nullptr || Base->GetType() != D3DRTYPE_TEXTURE)
            return false;
    }
    const unsigned long EnvTransform = PlainShadowReceiver ? 0 : Tss(EnvStage, D3DTSS_TEXTURETRANSFORMFLAGS, 0);
    if (IsCube ? (EnvTransform != 0 && EnvTransform != D3DTTFF_COUNT3) :
        (EnvTransform != 0 && EnvTransform != D3DTTFF_COUNT2 &&
         EnvTransform != (D3DTTFF_COUNT3 | D3DTTFF_PROJECTED)))
        return false;

    const bool LowDetail=Ex->SurfaceDistanceTier==1 && !Cockpit && !Glass;
    const bool ShadowReceiver=!LowDetail && Ex->bShadowReceiver && (Ex->ShadowReadyMask&3u)==3u;
    // Non-receivers use a variant without the shadow code: fewer registers for every pixel.
    IDirect3DPixelShader9*& SurfacePs = LowDetail ?
        (IsCube ? Ex->SurfaceLowCubePs : Ex->SurfaceLowPs) :
        (ShadowReceiver ? (IsCube ? Ex->SurfaceCubePs : Ex->SurfacePs) :
                          (IsCube ? Ex->SurfaceNoShadowCubePs : Ex->SurfaceNoShadowPs));
    // The warm-up is still compiling: draw this one with the native material rather than
    // stall the render thread on the same compile.
    if ((Ex->SurfaceVs == nullptr || SurfacePs == nullptr) && G_SurfaceWarmState == 1)
        return false;
    if (Ex->SurfaceVs == nullptr || SurfacePs == nullptr)
    {
        char Module[MAX_PATH] = {};
        DWORD Length = GetModuleFileNameA(nullptr, Module, MAX_PATH);
        char* Slash = strrchr(Module, '\\');
        std::string Source;
        std::string Path;
        if (Length > 0 && Length < MAX_PATH && Slash != nullptr)
        {
            Slash[1] = '\0';
            Path = std::string(Module) + "../DATA_EXTRA/SHADERS/surface_material.hlsl";
            FILE* File = fopen(Path.c_str(), "rb");
            if (File != nullptr)
            {
                char Buffer[4096]; size_t N;
                while ((N = fread(Buffer, 1, sizeof(Buffer), File)) != 0) Source.append(Buffer, N);
                fclose(File);
            }
        }
        std::vector<unsigned char> Vs, Ps;
        const char* Variant = LowDetail ? "#define SURFACE_LOW_DETAIL 1\n" :
            (ShadowReceiver ? "" : "#define SURFACE_NO_SHADOW 1\n");
        const std::string PixelSource = std::string(Variant) +
            (IsCube ? "#define SURFACE_ENV_CUBE 1\n" : "") + Source;
        bool Ok = !Source.empty() && CompileStage(Source, Path, nullptr, "VSMain", "vs_3_0", &Vs) &&
            CompileStage(PixelSource, Path, nullptr, "PSMain", "ps_3_0", &Ps);
        if (Ok && Ex->SurfaceVs == nullptr)
            Ok = SUCCEEDED(Device_->CreateVertexShader((const DWORD*)Vs.data(), &Ex->SurfaceVs));
        if (Ok && SurfacePs == nullptr)
            Ok = SUCCEEDED(Device_->CreatePixelShader((const DWORD*)Ps.data(), &SurfacePs));
        if (!Ok)
        {
            ExLogf(kExFdumpError, "ERROR", __LINE__, "surface shaders unavailable; legacy fallback: %s", Path.c_str());
            CompileFailed = true;
            return false;
        }
    }

    float Vs[68] = {};
    MulMatrix4(Transforms_.World.Values, Transforms_.View.Values, Vs);
    memcpy(Vs + 16, Transforms_.Projection.Values, sizeof(float) * 16);
    D3DXMATRIX M, Inverse, Normal;
    memcpy(&M, Vs, sizeof(M));
    if(Ex->bSurfaceNormalCached && !memcmp(Ex->SurfaceLastWorldView,Vs,64))
        memcpy(&Normal,Ex->SurfaceLastNormal,64);
    else
    {
        bool Rigid=true;
        for(unsigned I=0;I<3;++I) for(unsigned J=I;J<3;++J)
        {
            float Dot=0;for(unsigned K=0;K<3;++K) Dot+=Vs[I*4+K]*Vs[J*4+K];
            if(std::fabs(Dot-(I==J ? 1.0f : 0.0f))>1.e-6f) Rigid=false;
        }
        if(Rigid)
        {
            D3DXMatrixIdentity(&Normal);
            for(unsigned I=0;I<3;++I) for(unsigned J=0;J<3;++J) Normal.m[I][J]=M.m[I][J];
        }
        else
        {
            if(D3DXMatrixInverse(&Inverse,nullptr,&M)==nullptr) return false;
            D3DXMatrixTranspose(&Normal,&Inverse);
        }
        memcpy(Ex->SurfaceLastWorldView,Vs,64);memcpy(Ex->SurfaceLastNormal,&Normal,64);
        Ex->bSurfaceNormalCached=true;
    }
    memcpy(Vs + 32, &Normal, sizeof(Normal));
    const float* EnvMatrix = DeviceStates_.TextureTransforms[PlainShadowReceiver ? 0 : EnvStage].Values;
    memcpy(Vs + 48, EnvMatrix, sizeof(float) * 16);
    const bool ColourVertex = (Fvf & D3DFVF_DIFFUSE) && RenderStates_.GetPending(D3DRS_COLORVERTEX) &&
        RenderStates_.GetPending(D3DRS_DIFFUSEMATERIALSOURCE) == D3DMCS_COLOR1;
    Vs[64] = ColourVertex ? 1.0f : 0.0f;
    Vs[65] = (float)BaseUv;
    Vs[66] = (float)EnvTransform;

    float Ps[96 * 4] = {};
    auto Set = [&](unsigned Reg, float X, float Y, float Z, float W) {
        float* D = Ps + Reg * 4; D[0] = X; D[1] = Y; D[2] = Z; D[3] = W;
    };
    auto Clamp = [](float V, float Lo, float Hi) { return std::fmax(Lo, std::fmin(V, Hi)); };
    const D3DMATERIAL9& Mat = Ex->SurfaceMaterial;
    memcpy(Ps, &Mat.Diffuse, sizeof(float) * 4);
    const unsigned long Ambient = RenderStates_.GetPending(D3DRS_AMBIENT);
    Set(1, Mat.Ambient.r * ((Ambient >> 16) & 255) / 255.0f,
        Mat.Ambient.g * ((Ambient >> 8) & 255) / 255.0f, Mat.Ambient.b * (Ambient & 255) / 255.0f, 1);
    memcpy(Ps + 8, &Mat.Emissive, sizeof(float) * 4);
    const float Roughness = Ex->SurfaceRoughness > 0.0f ? Ex->SurfaceRoughness :
        (Mat.Power > 0.0f ? std::sqrt(2.0f / (Mat.Power + 2.0f)) : 0.65f);
    Set(3, Clamp(Mat.Specular.r > 0 ? Mat.Specular.r : 0.04f, 0.02f, 0.16f),
        Clamp(Mat.Specular.g > 0 ? Mat.Specular.g : 0.04f, 0.02f, 0.16f),
        Clamp(Mat.Specular.b > 0 ? Mat.Specular.b : 0.04f, 0.02f, 0.16f), Clamp(Roughness, 0.28f, 1.0f));
    D3DLIGHT9 Lights[8];
    const unsigned Count = ExCollectSurfaceLights(Lights, 8);
    Set(4, HasBase ? 1.0f : 0.0f, ColourVertex ? 1.0f : 0.0f,
        PlainShadowReceiver ? 0 : (Ex->SurfaceEnvironment >= 0 ? Clamp(Ex->SurfaceEnvironment, 0, 2) : 1.0f), (float)Count);
    unsigned long FogMode = RenderStates_.GetPending(kRsFogTableMode);
    if (FogMode == D3DFOG_NONE) FogMode = RenderStates_.GetPending(kRsFogVertexMode);
    if (!RenderStates_.GetPending(kRsFogEnable)) FogMode = 0;
    Set(5, FloatBits(RenderStates_.GetPending(kRsFogStart)), FloatBits(RenderStates_.GetPending(kRsFogEnd)),
        FloatBits(RenderStates_.GetPending(kRsFogDensity)), (float)FogMode);
    const unsigned long FogColour = RenderStates_.GetPending(kRsFogColor);
    Set(6, ((FogColour >> 16) & 255) / 255.0f, ((FogColour >> 8) & 255) / 255.0f,
        (FogColour & 255) / 255.0f, RenderStates_.GetPending(D3DRS_RANGEFOGENABLE) ? 1.0f : 0.0f);
    Set(7, (float)ColorOp, (float)AlphaOp, (float)EnvTransform, PlainShadowReceiver ? -1.0f : (float)EnvColorOp);
    memcpy(Ps + 8 * 4, EnvMatrix, sizeof(float) * 16);
    float LightView[16];memcpy(LightView,Transforms_.View.Values,64);
    bool AllDirectional=true;
    for(unsigned I=0;I<Count;++I) if(Lights[I].Type!=D3DLIGHT_DIRECTIONAL) AllDirectional=false;
    if(AllDirectional) LightView[12]=LightView[13]=LightView[14]=0;
    const bool RebuildLights=!Ex->bSurfaceLightsCached || Count!=Ex->SurfaceLastLightCount ||
        memcmp(Lights,Ex->SurfaceLastLights,Count*sizeof(D3DLIGHT9)) ||
        memcmp(LightView,Ex->SurfaceLastLightView,64);
    if(RebuildLights)
    {
        memset(Ex->SurfaceLightAmbient,0,sizeof(Ex->SurfaceLightAmbient));
        for (unsigned I = 0; I < Count; ++I)
        {
            D3DLIGHT9 const& L = Lights[I];
            D3DXVECTOR3 Pos(0,0,0), Dir;
            D3DXMatrixIdentity(&M);
            memcpy(&M,LightView,sizeof(M));
            // Directional lights have no position. Canonical zero also lets equal
            // materials at different translations share the same instance group.
            if(L.Type!=D3DLIGHT_DIRECTIONAL)
                D3DXVec3TransformCoord(&Pos, reinterpret_cast<const D3DXVECTOR3*>(&L.Position), &M);
            D3DXVec3TransformNormal(&Dir, reinterpret_cast<const D3DXVECTOR3*>(&L.Direction), &M);
            unsigned R = 12 + I * 5;
            Set(R, Pos.x, Pos.y, Pos.z, (float)L.Type);
            Set(R + 1, Dir.x, Dir.y, Dir.z, L.Range);
            Set(R + 2, L.Diffuse.r, L.Diffuse.g, L.Diffuse.b, L.Falloff);
            // Retail lights often author only diffuse colour: reflective materials still need
            // a specular radiance from that source, rather than an all-zero highlight.
            const bool HasSpec = L.Specular.r > 0 || L.Specular.g > 0 || L.Specular.b > 0;
            Set(R + 3, HasSpec ? L.Specular.r : L.Diffuse.r, HasSpec ? L.Specular.g : L.Diffuse.g,
                HasSpec ? L.Specular.b : L.Diffuse.b, std::cos(L.Phi * 0.5f));
            Set(R + 4, L.Attenuation0, L.Attenuation1, L.Attenuation2, std::cos(L.Theta * 0.5f));
            Ex->SurfaceLightAmbient[0]+=L.Ambient.r;
            Ex->SurfaceLightAmbient[1]+=L.Ambient.g;
            Ex->SurfaceLightAmbient[2]+=L.Ambient.b;
        }
        memcpy(Ex->SurfacePackedLights,Ps+12*4,sizeof(Ex->SurfacePackedLights));
        memcpy(Ex->SurfaceLastLights,Lights,Count*sizeof(D3DLIGHT9));
        memcpy(Ex->SurfaceLastLightView,LightView,64);
        Ex->SurfaceLastLightCount=Count;Ex->bSurfaceLightsCached=true;
    }
    else memcpy(Ps+12*4,Ex->SurfacePackedLights,sizeof(Ex->SurfacePackedLights));
    Ps[4]+=Mat.Ambient.r*Ex->SurfaceLightAmbient[0];
    Ps[5]+=Mat.Ambient.g*Ex->SurfaceLightAmbient[1];
    Ps[6]+=Mat.Ambient.b*Ex->SurfaceLightAmbient[2];

    memcpy(Ps+52*4,Ex->ShadowMatrices[0],64); memcpy(Ps+56*4,Ex->ShadowMatrices[1],64);
    Set(60,ShadowReceiver ? 1.0f : 0.0f,1.0f/Ex->ShadowResolution[0],
        Ex->ShadowFarRadius*0.9f,Ex->ShadowFarRadius);
    memcpy(Ps+61*4,Ex->ShadowSunDirection,16);
    // y: the near map's moving casters (ships, asteroids) are in their own map (cascade 2).
    const bool NearLive=ShadowReceiver && (Ex->ShadowReadyMask&4u) && Ex->ShadowMaps[2];
    Set(62,(float)Ex->ShadowPlanetCount,NearLive ? 1.0f : 0.0f,0,0);
    memcpy(Ps+64*4,Ex->ShadowPlanets,sizeof(Ex->ShadowPlanets));
    Set(63,Ex->ShadowMaxLength,Ex->ShadowMaxLength*0.8f,
        Ex->ShadowNearRadius*2,Ex->ShadowFarRadius*2);
    Set(72,std::tan(Ex->ShadowLightAngle*0.00872664626f),
        (float)Ex->ShadowSearchSamples,(float)Ex->ShadowFilterSamples,Ex->ShadowStrength);
    Set(73,Ex->ShadowNearRadius*2/Ex->ShadowResolution[0],
        Ex->ShadowFarRadius*2/Ex->ShadowResolution[1],Ex->ShadowBiasScale,0);
    Set(74,Ex->ShadowDepthSpan[0],Ex->ShadowDepthSpan[1],0,0);
    Set(75,Ex->SurfaceHighlights,Ex->SurfaceCoat,Ex->SurfaceBrushed,1);
    const unsigned Tier=Ex->bShadowReceiverIsShip ? Ex->ShadowReceiverTier : 0u;
    if(Tier==1)
        // A zero quality distance selects the reduced counts for every pixel.
        Set(76,0.001f,1.0f,Ex->ShadowModerateSearchSamples,Ex->ShadowModerateFilterSamples);
    else
        Set(76,Ex->bShadowReceiverIsShip ? Ex->ShadowShipQualityDistance : Ex->ShadowStaticQualityDistance,
            Ex->bShadowAdaptiveQuality ? 1.0f : 0.0f,Ex->ShadowLowSearchSamples,Ex->ShadowLowFilterSamples);
    unsigned GlintCount=0;
    if(!LowDetail && Ex->bWeaponGlintReceiver) for(unsigned I=0;I<Ex->WeaponGlintCount;++I)
    {
        if(!(Ex->WeaponGlintReceiverMask&(1u<<I))) continue;
        auto const& G=Ex->WeaponGlints[I];
        Set(78+GlintCount*2,G.Position[0],G.Position[1],G.Position[2],0);
        Set(79+GlintCount*2,G.Colour[0],G.Colour[1],G.Colour[2],0);
        ++GlintCount;
    }
    Set(77,(float)GlintCount,Ex->WeaponGlintStrength,
        1.0f/(Ex->WeaponGlintRadius*Ex->WeaponGlintRadius),
        Ex->WeaponGlintDistance*Ex->WeaponGlintDistance);
    Set(94,Cockpit ? 1.0f : 0.0f,Glass ? 1.0f : 0.0f,Ex->SurfaceGlassStrength,Ex->SurfaceCockpitStrength);
    // The far map's station cache this frame (built or reused): sampled beside the far map.
    const bool StationMap=ShadowReceiver && Ex->bShadowStaticPrepared && Ex->ShadowStaticMap;
    Set(95,1.0f/Ex->ShadowResolution[1],Ex->ShadowShortReach,Tier==2 ? 1.0f : 0.0f,StationMap ? 1.0f : 0.0f);

    // Device state is re-sent only where it differs from what the previous surface draw left
    // and nothing else has written since (the device-call write counters).
    auto& Calls = Rp9DeviceCalls();
    HRESULT Hr = S_OK;
    if (Calls.HighSamplerWrites != Ex->SurfaceSamplerWrites)
        memset(Ex->SurfaceSamplerValid, 0, sizeof(Ex->SurfaceSamplerValid));
    auto BindHigh = [&](unsigned Slot, IDirect3DBaseTexture9* Texture, const unsigned long* States) {
        static const D3DSAMPLERSTATETYPE Types[8] = {D3DSAMP_ADDRESSU, D3DSAMP_ADDRESSV, D3DSAMP_ADDRESSW,
            D3DSAMP_MAGFILTER, D3DSAMP_MINFILTER, D3DSAMP_MIPFILTER, D3DSAMP_MAXANISOTROPY, D3DSAMP_MIPMAPLODBIAS};
        const DWORD Sampler = 8 + Slot;
        const bool Valid = Ex->SurfaceSamplerValid[Slot];
        if (SUCCEEDED(Hr) && (!Valid || Ex->SurfaceSamplerTexture[Slot] != Texture))
            Hr = Rp9SetTexture(Device_, Sampler, Texture);
        for (unsigned I = 0; I < 8 && SUCCEEDED(Hr); ++I)
            if (!Valid || Ex->SurfaceSamplerStates[Slot][I] != States[I])
                Hr = Rp9SetSamplerState(Device_, Sampler, Types[I], States[I]);
        Ex->SurfaceSamplerValid[Slot] = SUCCEEDED(Hr);
        Ex->SurfaceSamplerTexture[Slot] = Texture;
        memcpy(Ex->SurfaceSamplerStates[Slot], States, sizeof(Ex->SurfaceSamplerStates[Slot]));
    };
    if (ShadowReceiver)
    {
        static const unsigned long ShadowStates[8] = {D3DTADDRESS_CLAMP, D3DTADDRESS_CLAMP, D3DTADDRESS_CLAMP,
            D3DTEXF_POINT, D3DTEXF_POINT, D3DTEXF_NONE, 1, 0};
        BindHigh(0, Ex->ShadowMaps[0], ShadowStates);
        BindHigh(1, Ex->ShadowMaps[1], ShadowStates);
        if (StationMap)
            BindHigh(3, Ex->ShadowStaticMap, ShadowStates);
        if (NearLive)
            BindHigh(4, Ex->ShadowMaps[2], ShadowStates);
    }
    // The authored addressing and filtering of the stage holding the environment map.
    // An entry the cache does not know (e.g. after soft particles saved the stage) is read back
    // from the device, which still holds what the stage used; only if that fails, defaults.
    const unsigned EnvSource = EnvStage < 0 ? 0u : (unsigned)EnvStage;
    auto EnvState = [&](unsigned long Type, unsigned long Default) -> unsigned long {
        const unsigned long Value = DeviceStates_.ReadTextureStageState(Device_, EnvSource, Type);
        return DeviceStates_.TextureStates[EnvSource][Type].bValid ? Value : Default;
    };
    const unsigned long EnvStates[8] = {
        EnvState(13, D3DTADDRESS_WRAP), EnvState(14, D3DTADDRESS_WRAP),
        EnvState(25, D3DTADDRESS_WRAP), EnvState(16, D3DTEXF_LINEAR),
        EnvState(17, D3DTEXF_LINEAR), EnvState(18, D3DTEXF_LINEAR),
        EnvState(21, 1), EnvState(19, 0)};
    BindHigh(2, EnvTexture, EnvStates);
    Ex->SurfaceSamplerWrites = Calls.HighSamplerWrites;

    if (Calls.ShaderWrites != Ex->SurfaceShaderWrites)
        Ex->SurfaceBoundVs = nullptr, Ex->SurfaceBoundPs = nullptr;
    if (SUCCEEDED(Hr) && Ex->SurfaceBoundVs != Ex->SurfaceVs)
    {
        Hr = Rp9SetVertexShader(Device_, Ex->SurfaceVs);
        Ex->SurfaceBoundVs = SUCCEEDED(Hr) ? Ex->SurfaceVs : nullptr;
    }
    if (SUCCEEDED(Hr) && Ex->SurfaceBoundPs != SurfacePs)
    {
        Hr = Rp9SetPixelShader(Device_, SurfacePs);
        Ex->SurfaceBoundPs = SUCCEEDED(Hr) ? SurfacePs : nullptr;
    }
    Ex->SurfaceShaderWrites = Calls.ShaderWrites;
    if (SUCCEEDED(Hr)) Hr = Rp9SetVertexConstants(Device_, 0, Vs, 17);

    if (Calls.PixelConstantWrites != Ex->SurfacePsWrites)
        memset(Ex->SurfacePsMirrorValid, 0, sizeof(Ex->SurfacePsMirrorValid));
    auto Upload = [&](unsigned Start, unsigned Count) {
        bool Same = true;
        for (unsigned I = Start; I < Start + Count && Same; ++I)
            Same = Ex->SurfacePsMirrorValid[I];
        if (Same && !memcmp(Ex->SurfacePsMirror + Start * 4, Ps + Start * 4, Count * 16))
            return;
        if (SUCCEEDED(Hr)) Hr = Rp9SetPixelConstants(Device_, Start, Ps + Start * 4, Count);
        memcpy(Ex->SurfacePsMirror + Start * 4, Ps + Start * 4, Count * 16);
        for (unsigned I = Start; I < Start + Count; ++I)
            Ex->SurfacePsMirrorValid[I] = SUCCEEDED(Hr);
    };
    // Per material / lights / per-frame shadow block / weapon glints / style and tier.
    Upload(0, 12);
    Upload(12, 40);
    if (!LowDetail)
    {
        Upload(52, 25);
        Upload(77, 17);
        Upload(94, 2);
    }
    Ex->SurfacePsWrites = Calls.PixelConstantWrites;
    Ex->bSurfaceActive = true;
    if (FAILED(Hr))
    {
        ExSurfaceEnd();
        ExSurfaceRelease();
        Ex->SurfaceBoundVs = nullptr; Ex->SurfaceBoundPs = nullptr;
        memset(Ex->SurfaceSamplerValid, 0, sizeof(Ex->SurfaceSamplerValid));
        memset(Ex->SurfacePsMirrorValid, 0, sizeof(Ex->SurfacePsMirrorValid));
        return false;
    }
    if (!Ex->bSurfaceLogged)
    {
        Ex->bSurfaceLogged = true;
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "reflective surface shader active, FVF 0x%lx, env stage %d", Fvf, EnvStage);
    }
    return true;
}

void FDirectX9::ExSurfaceEnd()
{
    // Shaders and samplers 8..12 stay bound for the next surface draw; ExSurfaceRelease
    // unbinds the shaders before a fixed-function draw.
    if (Ex_ != nullptr)
        Ex_->bSurfaceActive = false;
}

void FDirectX9::ExSurfaceRelease()
{
    if (Ex_ == nullptr || Device_ == nullptr || Ex_->bShadowDrawing || Ex_->bInPass || Ex_->bSurfaceActive)
        return;
    auto& Calls = Rp9DeviceCalls();
    if (!Calls.VsValid || Calls.Vs != nullptr)
        Rp9SetVertexShader(Device_, nullptr);
    if (!Calls.PsValid || Calls.Ps != nullptr)
        Rp9SetPixelShader(Device_, nullptr);
}

bool FDirectX9::ExQueueSurfaceInstance(unsigned long Prim,unsigned int Min,unsigned int Vertices,
                                      unsigned int Start,unsigned int Count)
{
    auto* E=Ex_;
    if(!E->bInstanceConfigRead)
    {
        E->bInstanceConfigRead=true;
        E->bSurfaceInstancing=ReadShadowSetting("surface_instancing",0,0,1)>0.5f;
        D3DCAPS9 Caps={};D3DDEVICE_CREATION_PARAMETERS Params={};
        if(FAILED(Device_->GetDeviceCaps(&Caps)) || FAILED(Device_->GetCreationParameters(&Params)) ||
           Caps.VertexShaderVersion<D3DVS_VERSION(3,0) || Caps.MaxStreams<2 ||
           (Params.BehaviorFlags&D3DCREATE_SOFTWARE_VERTEXPROCESSING)) E->bSurfaceInstancing=false;
    }
    auto* Vb=StreamCache_.VertexBuffer;auto* Ib=StreamCache_.IndexBuffer;
    if(!E->bInstanceScope || !E->bSurfaceInstancing || E->bInstanceFailed || !E->bSurfaceActive ||
       E->bShadowDrawing || E->bInPass || E->bSurfaceCockpit || E->bSurfaceGlass ||
       Prim!=D3DPT_TRIANGLELIST || !Vb || !Vb->Gpu || !Ib || !Ib->Gpu || Ib==&ScratchIb_ ||
       (Vb->Flags&D3DUSAGE_DYNAMIC) || (Ib->Flags&D3DUSAGE_DYNAMIC) ||
       RenderStates_.GetPending(D3DRS_ALPHABLENDENABLE) || !RenderStates_.GetPending(D3DRS_ZWRITEENABLE) ||
       !RenderStates_.GetPending(D3DRS_ZENABLE) || RenderStates_.GetPending(D3DRS_DEPTHBIAS) ||
       RenderStates_.GetPending(47) || RenderStates_.GetPending(D3DRS_SLOPESCALEDEPTHBIAS))
    {ExFlushSurfaceInstances();return false;}
    if(E->SurfaceInstanceQueued>=1024 || E->SurfaceInstanceGroups.size()>=128) ExFlushSurfaceInstances();
    auto& Calls=Rp9DeviceCalls();
    unsigned long Fvf=StreamCache_.Fvf ? StreamCache_.Fvf : Vb->Fvf;
    std::string Key;Key.reserve(4096);
    auto Append=[&](const void* P,size_t S){Key.append(static_cast<const char*>(P),S);};
    unsigned long Draw[]={Prim,(unsigned long)DeviceBaseVertex_,Min,Vertices,Start,Count,Fvf};
    Append(Draw,sizeof(Draw));Append(&Vb->Gpu,sizeof(Vb->Gpu));Append(&Ib->Gpu,sizeof(Ib->Gpu));
    Append(Calls.Pc,96*16);Append(Calls.Vc+16,64);Append(Calls.Vc+48,80);
    Append(Calls.Render,sizeof(Calls.Render));Append(Calls.RenderValid,sizeof(Calls.RenderValid));
    Append(Calls.Textures,4*sizeof(Calls.Textures[0]));Append(Calls.TextureValid,4);
    Append(Calls.Samplers,4*sizeof(Calls.Samplers[0]));Append(Calls.SamplerValid,4*sizeof(Calls.SamplerValid[0]));
    // The surface route's environment and shadow maps (samplers 8..12).
    Append(Calls.Textures+8,5*sizeof(Calls.Textures[0]));Append(Calls.TextureValid+8,5);
    Append(Calls.Samplers+8,5*sizeof(Calls.Samplers[0]));Append(Calls.SamplerValid+8,5*sizeof(Calls.SamplerValid[0]));
    D3DVIEWPORT9 Viewport={};if(FAILED(Device_->GetViewport(&Viewport))) return false;
    Append(&Viewport,sizeof(Viewport));
    auto Found=E->SurfaceInstanceGroups.find(Key);
    if(Found==E->SurfaceInstanceGroups.end())
    {
        // Draw the first occurrence normally. Unique meshes incur no state-block
        // allocation or deferred draw. Only repeated identical opaque state queues.
        FRp9SurfaceInstanceGroup Group;
        Group.Prim=Prim;Group.Base=DeviceBaseVertex_;Group.Min=Min;Group.Vertices=Vertices;
        Group.Start=Start;Group.Count=Count;Group.Fvf=Fvf;
        E->SurfaceInstanceGroups.emplace(std::move(Key),std::move(Group));
        return false;
    }
    auto& Group=Found->second;
    if(!Group.State && FAILED(Device_->CreateStateBlock(D3DSBT_ALL,&Group.State)))
    {ExFlushSurfaceInstances();return false;}
    std::array<float,32> Matrices;
    memcpy(Matrices.data(),Calls.Vc,64);memcpy(Matrices.data()+16,Calls.Vc+32,64);
    Group.Matrices.push_back(Matrices);++E->SurfaceInstanceQueued;
    return true;
}

void FDirectX9::ExFlushSurfaceInstances()
{
    auto* E=Ex_;
    if(!E || E->SurfaceInstanceGroups.empty()) return;
    if(!E->SurfaceInstanceQueued)
    {E->SurfaceInstanceGroups.clear();return;}
    IDirect3DStateBlock9* Saved=nullptr;
    HRESULT Hr=Device_->CreateStateBlock(D3DSBT_ALL,&Saved);
    if(FAILED(Hr))
    {
        // A device loss cannot safely submit deferred work. Release all retained
        // state/resources; the normal reset path reconstructs the next frame.
        for(auto& Item:E->SurfaceInstanceGroups) if(Item.second.State) Item.second.State->Release();
        E->SurfaceInstanceGroups.clear();E->SurfaceInstanceQueued=0;return;
    }
    if(!E->SurfaceInstanceVs && !E->bInstanceFailed)
    {
        char Module[MAX_PATH]={};GetModuleFileNameA(nullptr,Module,MAX_PATH);
        char* Slash=strrchr(Module,'\\');std::string Source,Path;
        if(Slash)
        {
            Slash[1]=0;Path=std::string(Module)+"../DATA_EXTRA/SHADERS/surface_material.hlsl";
            FILE* File=fopen(Path.c_str(),"rb");
            if(File){char B[4096];size_t N;while((N=fread(B,1,sizeof(B),File))) Source.append(B,N);fclose(File);}
        }
        std::vector<unsigned char> Code;
        if(Source.empty() || !CompileStage("#define SURFACE_INSTANCED 1\n"+Source,Path,nullptr,"VSMain","vs_3_0",&Code) ||
           FAILED(Device_->CreateVertexShader((DWORD*)Code.data(),&E->SurfaceInstanceVs)) ||
           FAILED(Device_->CreateVertexBuffer(1024*128,D3DUSAGE_DYNAMIC|D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT,
                                              &E->SurfaceInstanceVb,nullptr))) E->bInstanceFailed=true;
    }
    for(auto& Item:E->SurfaceInstanceGroups)
    {
        auto& G=Item.second;if(!G.State || G.Matrices.empty()) continue;
        G.State->Apply();Rp9DeviceCalls().Invalidate();
        bool Instanced=G.Matrices.size()>=2 && !E->bInstanceFailed;
        IDirect3DVertexDeclaration9* Decl=nullptr;
        if(Instanced)
        {
            auto It=E->SurfaceInstanceDecls.find(G.Fvf);
            if(It!=E->SurfaceInstanceDecls.end()) Decl=It->second;
            else
            {
                D3DVERTEXELEMENT9 Elements[MAX_FVF_DECL_SIZE+9]={};
                Hr=D3DXDeclaratorFromFVF(G.Fvf,Elements);
                unsigned End=0;while(End<MAX_FVF_DECL_SIZE && Elements[End].Stream!=0xff) ++End;
                if(SUCCEEDED(Hr) && End<MAX_FVF_DECL_SIZE)
                {
                    for(unsigned I=0;I<8;++I) Elements[End+I]={1,(WORD)(I*16),D3DDECLTYPE_FLOAT4,
                        D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_TEXCOORD,(BYTE)(3+I)};
                    D3DVERTEXELEMENT9 Terminator=D3DDECL_END();Elements[End+8]=Terminator;
                    Hr=Device_->CreateVertexDeclaration(Elements,&Decl);
                }
                if(SUCCEEDED(Hr) && Decl) E->SurfaceInstanceDecls.emplace(G.Fvf,Decl);
                else Instanced=false;
            }
        }
        if(Instanced)
        {
            void* Data=nullptr;
            Hr=E->SurfaceInstanceVb->Lock(0,(UINT)G.Matrices.size()*128,&Data,D3DLOCK_DISCARD);
            if(SUCCEEDED(Hr)){memcpy(Data,G.Matrices.data(),G.Matrices.size()*128);Hr=E->SurfaceInstanceVb->Unlock();}
            if(SUCCEEDED(Hr)) Hr=Device_->SetVertexDeclaration(Decl);
            if(SUCCEEDED(Hr)) Hr=Rp9SetVertexShader(Device_,E->SurfaceInstanceVs);
            if(SUCCEEDED(Hr)) Hr=Device_->SetStreamSource(1,E->SurfaceInstanceVb,0,128);
            if(SUCCEEDED(Hr)) Hr=Device_->SetStreamSourceFreq(0,D3DSTREAMSOURCE_INDEXEDDATA|(UINT)G.Matrices.size());
            if(SUCCEEDED(Hr)) Hr=Device_->SetStreamSourceFreq(1,D3DSTREAMSOURCE_INSTANCEDATA|1);
            if(SUCCEEDED(Hr))
            {
                Hr=Device_->DrawIndexedPrimitive((D3DPRIMITIVETYPE)G.Prim,G.Base,G.Min,G.Vertices,G.Start,G.Count);
                ExNoteDraw(G.Count*(unsigned)G.Matrices.size());
                if(SUCCEEDED(Hr)){++Rp9DeviceCalls().InstancedDraws;Rp9DeviceCalls().Instances+=G.Matrices.size();}
            }
            Device_->SetStreamSourceFreq(0,1);Device_->SetStreamSourceFreq(1,1);
            Device_->SetStreamSource(1,nullptr,0,0);
            if(FAILED(Hr))
            {
                E->bInstanceFailed=true;Instanced=false;
                G.State->Apply();Rp9DeviceCalls().Invalidate();
            }
        }
        if(!Instanced)
        {
            for(auto const& Matrices:G.Matrices)
            {
                Rp9SetVertexConstants(Device_,0,Matrices.data(),4);
                Rp9SetVertexConstants(Device_,8,Matrices.data()+16,4);
                Device_->DrawIndexedPrimitive((D3DPRIMITIVETYPE)G.Prim,G.Base,G.Min,G.Vertices,G.Start,G.Count);
                ExNoteDraw(G.Count);
            }
        }
        G.State->Release();G.State=nullptr;
    }
    Saved->Apply();Saved->Release();Rp9DeviceCalls().Invalidate();
    E->SurfaceInstanceGroups.clear();E->SurfaceInstanceQueued=0;
}

void FDirectX9::ExReleaseSurfaceInstances()
{
    auto* E=Ex_;if(!E) return;
    for(auto& Item:E->SurfaceInstanceGroups) if(Item.second.State) Item.second.State->Release();
    E->SurfaceInstanceGroups.clear();E->SurfaceInstanceQueued=0;
    for(auto& Item:E->SurfaceInstanceDecls) Item.second->Release();E->SurfaceInstanceDecls.clear();
    if(E->SurfaceInstanceVb){E->SurfaceInstanceVb->Release();E->SurfaceInstanceVb=nullptr;}
    if(E->SurfaceInstanceVs){E->SurfaceInstanceVs->Release();E->SurfaceInstanceVs=nullptr;}
    E->bInstanceFailed=false;E->bInstanceScope=false;
}

void FDirectX9::ExNoteDraw(unsigned long Primitives)
{
    auto& C=Rp9DeviceCalls();
    if(Ex_ && Ex_->bShadowDrawing){++C.ShadowDraws;C.ShadowPrimitives+=Primitives;}
    else {++C.MainDraws;C.MainPrimitives+=Primitives;}
}

void FDirectX9::ExReportFrameStats()
{
    auto* E=Ex_;if(!E) return;
    if(!E->bRenderStatsRead)
    {E->bRenderStatsRead=true;E->bRenderStats=ReadShadowSetting("render_stats",0,0,1)>0.5f;E->RenderStatsAt=GetTickCount();}
    if(!E->bRenderStats){Rp9DeviceCalls().ResetCounters();return;}
    ++E->RenderStatsFrames;DWORD Now=GetTickCount(),Elapsed=Now-E->RenderStatsAt;
    if(Elapsed<2000) return;
    auto& C=Rp9DeviceCalls();double F=(double)E->RenderStatsFrames;
    auto& T=E->GpuTimers;const double G=T.Collected ? 1.0/T.Collected : 0.0;
    ExLogf(kExFdumpNotice,"NOTICE",__LINE__,
        "render perf: %.1f FPS, GPU ms/frame %.2f (shadow maps %.2f, ex passes %.2f, fxaa %.2f; %u frames timed), "
        "draws/frame normal %.0f shadow %.0f, state sent %.0f skipped %.0f, constant vectors %.0f, instanced draws %.1f instances %.1f",
        F*1000/Elapsed,T.Sum[0]*G,T.Sum[1]*G,T.Sum[2]*G,T.Sum[3]*G,T.Collected,
        C.MainDraws/F,C.ShadowDraws/F,C.Submitted/F,C.Skipped/F,C.ConstantVectors/F,C.InstancedDraws/F,C.Instances/F);
    C.ResetCounters();E->RenderStatsFrames=0;E->RenderStatsAt=Now;
    memset(T.Sum,0,sizeof(T.Sum));T.Collected=0;
}

void FDirectX9::ExGpuMark(unsigned Kind)
{
    auto* E=Ex_;
    if(!E || !Device_ || !E->bRenderStats) return;
    auto& T=E->GpuTimers;
    const unsigned F=T.Current;
    if(T.bFailed || !T.bOpen[F] || T.Used[F]>=FRp9GpuTimers::Slots) return;
    IDirect3DQuery9*& Query=T.Stamps[F][T.Used[F]];
    if(!Query && FAILED(Device_->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&Query))) {T.bFailed=true;return;}
    Query->Issue(D3DISSUE_END);
    T.Kinds[F][T.Used[F]++]=(unsigned char)Kind;
}

void FDirectX9::ExGpuFrameBoundary()
{
    auto* E=Ex_;
    if(!E || !Device_ || !E->bRenderStats) return;
    auto& T=E->GpuTimers;
    if(T.bFailed) return;
    unsigned F=T.Current;
    if(T.bOpen[F])
    {
        ExGpuMark(FRp9GpuTimers::FrameEnd);
        T.Disjoint[F]->Issue(D3DISSUE_END);T.Frequency[F]->Issue(D3DISSUE_END);
        T.bOpen[F]=false;T.bPending[F]=true;
    }
    F=T.Current=(T.Current+1)%FRp9GpuTimers::Frames;
    if(T.bPending[F])
    {
        // Three frames later: read without flushing; a frame not finished yet is skipped.
        T.bPending[F]=false;
        BOOL Disjoint=TRUE;UINT64 Frequency=0;
        bool Ready=T.Disjoint[F]->GetData(&Disjoint,sizeof(Disjoint),0)==S_OK &&
                   T.Frequency[F]->GetData(&Frequency,sizeof(Frequency),0)==S_OK && !Disjoint && Frequency;
        UINT64 Stamps[FRp9GpuTimers::Slots]={};
        for(unsigned I=0;I<T.Used[F] && Ready;++I)
            Ready=T.Stamps[F][I]->GetData(&Stamps[I],sizeof(UINT64),0)==S_OK;
        if(Ready)
        {
            double Ms[4]={};UINT64 Open[4]={};bool HasFrame=false;
            for(unsigned I=0;I<T.Used[F];++I)
            {
                const unsigned Kind=T.Kinds[F][I];
                const unsigned Slot=Kind/2; // frame, shadow, ex, aa
                if((Kind&1u)==0) Open[Slot]=Stamps[I];
                else if(Open[Slot] && Stamps[I]>=Open[Slot])
                {
                    Ms[Slot]+=(double)(Stamps[I]-Open[Slot])*1000.0/(double)Frequency;
                    Open[Slot]=0;HasFrame|=Slot==0;
                }
            }
            if(HasFrame)
            {
                for(unsigned I=0;I<4;++I) T.Sum[I]+=Ms[I];
                ++T.Collected;
            }
        }
    }
    if(!T.Disjoint[F] &&
       (FAILED(Device_->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&T.Disjoint[F])) ||
        FAILED(Device_->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&T.Frequency[F]))))
    {
        T.bFailed=true;
        ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"render perf: GPU timestamp queries unavailable");
        return;
    }
    T.Disjoint[F]->Issue(D3DISSUE_BEGIN);
    T.Used[F]=0;T.bOpen[F]=true;
    ExGpuMark(FRp9GpuTimers::FrameBegin);
}

// While the surface shader warm-up compiles, a line of text in the top-left corner of the
// finished frame (SwapBuffers, after the antialiasing): "caching shaders N/M" in the
// port.ini [Language] language (ru or en; -lang:xx on the command line wins).
void FDirectX9::ExDrawWarmupOverlay()
{
    FRp9ExState* E = Ex_;
    if (E == nullptr || Device_ == nullptr)
        return;
    if (G_SurfaceWarmState != 1)
    {
        if (E->WarmupFont) { E->WarmupFont->Release(); E->WarmupFont = nullptr; }
        if (E->WarmupSavedState) { E->WarmupSavedState->Release(); E->WarmupSavedState = nullptr; }
        return;
    }
    if (E->WarmupLanguage < 0)
    {
        char Path[MAX_PATH] = {}, Text[16] = {};
        const DWORD Length = GetModuleFileNameA(nullptr, Path, MAX_PATH);
        if (char* Slash = Length && Length < MAX_PATH ? strrchr(Path, '\\') : nullptr)
        {
            strcpy(Slash + 1, "port.ini");
            GetPrivateProfileStringA("Language", "language", "", Text, sizeof(Text), Path);
        }
        if (const char* Switch = strstr(GetCommandLineA(), "-lang"))
            strncpy(Text, Switch[5] ? Switch + 6 : "", 2);
        E->WarmupLanguage = _strnicmp(Text, "ru", 2) == 0 ? 1 : 0;
    }
    if (E->WarmupFont == nullptr &&
        FAILED(D3DXCreateFontW(Device_, 22, 0, FW_BOLD, 1, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS,
                               ANTIALIASED_QUALITY, DEFAULT_PITCH | FF_DONTCARE, L"Arial", &E->WarmupFont)))
        return;
    HRESULT Hr = E->WarmupSavedState ? E->WarmupSavedState->Capture() :
        Device_->CreateStateBlock(D3DSBT_ALL, &E->WarmupSavedState);
    if (FAILED(Hr))
        return;
    const bool InScene = E->bInScene;
    if (!InScene && FAILED(Device_->BeginScene()))
        return;
    wchar_t Text[96];
    const int Done = G_SurfaceWarmTotal - G_SurfaceWarmPending;
    // "Кэширование шейдеров" / "Caching shaders"
    _snwprintf(Text, 96, E->WarmupLanguage ?
        L"\x041a\x044d\x0448\x0438\x0440\x043e\x0432\x0430\x043d\x0438\x0435 \x0448\x0435\x0439\x0434\x0435\x0440\x043e\x0432... %d/%d" :
        L"Caching shaders... %d/%d", Done, G_SurfaceWarmTotal);
    Text[95] = 0;
    RECT Shadow = {18, 18, 900, 60}, Rect = {16, 16, 900, 60};
    E->WarmupFont->DrawTextW(nullptr, Text, -1, &Shadow, DT_NOCLIP, D3DCOLOR_ARGB(200, 0, 0, 0));
    E->WarmupFont->DrawTextW(nullptr, Text, -1, &Rect, DT_NOCLIP, D3DCOLOR_ARGB(235, 255, 214, 130));
    if (!InScene)
        Device_->EndScene();
    E->WarmupSavedState->Apply();
    Rp9DeviceCalls().Invalidate();
}

void FDirectX9::ExGpuRelease()
{
    auto* E=Ex_;
    if(!E) return;
    auto& T=E->GpuTimers;
    for(unsigned F=0;F<FRp9GpuTimers::Frames;++F)
    {
        if(T.Disjoint[F]) {T.Disjoint[F]->Release();T.Disjoint[F]=nullptr;}
        if(T.Frequency[F]) {T.Frequency[F]->Release();T.Frequency[F]=nullptr;}
        for(auto*& Query:T.Stamps[F]) if(Query) {Query->Release();Query=nullptr;}
        T.Used[F]=0;T.bOpen[F]=T.bPending[F]=false;
    }
}

GENRESULT DACOM_API FDirectX9::SetWeaponGlintReceiver(unsigned long Enabled)
{
    Ex_->bWeaponGlintReceiver=Enabled!=0;
    Ex_->WeaponGlintReceiverMask=Enabled ? (1u<<Ex_->WeaponGlintCount)-1u : 0;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetWeaponGlintReceiverBounds(const float* Center,float Radius)
{
    auto* E=Ex_;E->bWeaponGlintReceiver=false;E->WeaponGlintReceiverMask=0;
    if(!E->WeaponGlintCount) return GR_OK;
    if(!Center || !std::isfinite(Radius) || Radius<0) return GR_INVALID_PARMS;
    for(unsigned I=0;I<3;++I) if(!std::isfinite(Center[I])) return GR_INVALID_PARMS;
    D3DXVECTOR3 P((float)((double)Center[0]-E->WeaponGlintEye[0]),
                 (float)((double)Center[1]-E->WeaponGlintEye[1]),
                 (float)((double)Center[2]-E->WeaponGlintEye[2]));
    float Range=E->WeaponGlintDistance+Radius;
    if(D3DXVec3LengthSq(&P)>Range*Range) return GR_OK;
    D3DXVec3TransformNormal(&P,&P,reinterpret_cast<D3DXMATRIX const*>(E->WeaponGlintRotation));
    float Reach=Radius+E->WeaponGlintRadius;
    for(unsigned I=0;I<E->WeaponGlintCount;++I)
    {
        auto const& G=E->WeaponGlints[I];
        float X=P.x-G.Position[0],Y=P.y-G.Position[1],Z=P.z-G.Position[2];
        if(X*X+Y*Y+Z*Z<=Reach*Reach) E->WeaponGlintReceiverMask|=1u<<I;
    }
    E->bWeaponGlintReceiver=E->WeaponGlintReceiverMask!=0;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::BeginWeaponGlints(const float* View12,const float* Eye)
{
    auto* E=Ex_;
    E->WeaponGlintCount=0; E->WeaponGlintReceiverMask=0; E->bWeaponGlintFrame=false; E->bWeaponGlintReceiver=false;
    if(!View12 || !Eye) return GR_OK;
    if(!E->bWeaponGlintConfigRead)
    {
        E->bWeaponGlintConfigRead=true;
        E->bWeaponGlintsEnabled=ReadShadowSetting("weapon_glints",1,0,1)>0.5f;
        E->WeaponGlintBudget=(unsigned)ReadShadowSetting("weapon_glint_groups",8,1,8);
        E->WeaponGlintStrength=ReadShadowSetting("weapon_glint_strength",1.25f,0,4);
        E->WeaponGlintRadius=ReadShadowSetting("weapon_glint_radius",22.5f,5,100);
        E->WeaponGlintDistance=ReadShadowSetting("weapon_glint_distance",1000,100,1000);
    }
    if(!E->bWeaponGlintsEnabled || E->WeaponGlintStrength<=0) return GR_OK;
    for(unsigned I=0;I<12;++I) if(!std::isfinite(View12[I])) return GR_INVALID_PARMS;
    for(unsigned I=0;I<3;++I) if(!std::isfinite(Eye[I])) return GR_INVALID_PARMS;
    float Flip[12];memcpy(Flip,View12,sizeof(Flip));
    Flip[6]=-Flip[6];Flip[7]=-Flip[7];Flip[8]=-Flip[8];
    Flip[9]=Flip[10]=Flip[11]=0;
    FRp9TransformCache Rotation={};Rotation.StoreAffine(Flip);
    memcpy(E->WeaponGlintRotation,Rotation.Values,64);
    memcpy(E->WeaponGlintEye,Eye,12);
    E->bWeaponGlintFrame=true;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::AddWeaponGlint(const float* Position,const float* Direction,
                                            const float* Colour,unsigned long Owner)
{
    auto* E=Ex_;
    if(!E->bWeaponGlintFrame) return GR_OK;
    if(!Position || !Colour) return GR_INVALID_PARMS;
    for(unsigned I=0;I<3;++I)
        if(!std::isfinite(Position[I]) ||
           !std::isfinite(Colour[I]) || Colour[I]<0 || Colour[I]>1) return GR_INVALID_PARMS;
    D3DXVECTOR3 P((float)((double)Position[0]-E->WeaponGlintEye[0]),
                  (float)((double)Position[1]-E->WeaponGlintEye[1]),
                  (float)((double)Position[2]-E->WeaponGlintEye[2]));
    if(D3DXVec3LengthSq(&P)>E->WeaponGlintDistance*E->WeaponGlintDistance) return GR_OK;
    // Direction is retained in the interface for compatibility, but the cheap
    // spherical accent needs neither direction normalisation nor a capsule.
    auto const* Rotation=reinterpret_cast<D3DXMATRIX const*>(E->WeaponGlintRotation);
    D3DXVec3TransformNormal(&P,&P,Rotation);
    unsigned Group=E->WeaponGlintCount;
    // One admitted accent per shooter: colours merge, directions never split it.
    for(unsigned I=0;I<E->WeaponGlintCount;++I)
        if(E->WeaponGlints[I].Owner==Owner) {Group=I;break;}
    if(Group==E->WeaponGlintCount)
    {
        if(Group>=E->WeaponGlintBudget) return GR_OK;
        auto& G=E->WeaponGlints[E->WeaponGlintCount++];
        G={};G.Owner=Owner;memcpy(G.Position,&P,12);
    }
    auto& G=E->WeaponGlints[Group];
    ++G.Shots;
    for(unsigned C=0;C<3;++C) G.Colour[C]+=(Colour[C]-G.Colour[C])/G.Shots;
    // Keep the first tracked position; only average colour, never add per-shot brightness.
    // Let the client retain the admitted seed instead of reselecting muzzle shots.
    return (GENRESULT)(Group+1);
}

// ---- local directional shadow maps -------------------------------------------------------
GENRESULT DACOM_API FDirectX9::SetLocalShadowReceiver(unsigned long Enabled)
{
    bool Scope=(Enabled&4u)!=0;
    if(!Scope || !Ex_->bInstanceScope || Ex_->bShadowReceiverIsShip!=((Enabled&2u)!=0))
        ExFlushSurfaceInstances();
    Ex_->SurfaceDistanceTier=(Enabled&16u) ? 2u : ((Enabled&8u) ? 1u : 0u);
    Ex_->bInstanceScope=Scope;
    Ex_->bShadowReceiver = (Enabled&1u)!=0;
    Ex_->bShadowReceiverIsShip = (Enabled&2u)!=0;
    Ex_->ShadowReceiverTier = (std::min)((unsigned)((Enabled>>5)&3u),2u);
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetLocalShadowCaster(unsigned long Flags)
{
    if(!Ex_->bShadowDrawing) return GR_GENERIC;
    Ex_->bShadowShortCaster=(Flags&1u)!=0;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::BeginLocalShadowFrame(const float* View12, const float* Position,
                                                   const float* SunDirection)
{
    ExFlushSurfaceInstances();
    FRp9ExState* E = Ex_;
    E->ShadowReadyMask = 0; E->ShadowPlanetCount = 0; E->bShadowReceiver = false;
    E->bShadowFrameValid=false;
    E->bShadowStaticPrepared=false;
    if (!Device_ || E->bShadowDrawing || !View12 || !Position || !SunDirection || E->bShadowFailed)
        return GR_GENERIC;
    if(!E->bShadowConfigRead)
    {
        E->bShadowConfigRead=true;
        E->bShadowStaticCache=ReadShadowSetting("shadow_static_cache",1,0,1)>0.5f;
        // shadow_near_resolution / shadow_far_resolution, each falling back to the older
        // single shadow_resolution key, then to 4096.
        const float Shared=ReadShadowSetting("shadow_resolution",4096,1024,8192);
        const float Requested[2]={ReadShadowSetting("shadow_near_resolution",Shared,1024,8192),
                                  ReadShadowSetting("shadow_far_resolution",Shared,1024,8192)};
        D3DCAPS9 Caps={}; Device_->GetDeviceCaps(&Caps);
        unsigned Limit=(std::min)((unsigned)Caps.MaxTextureWidth,(unsigned)Caps.MaxTextureHeight);
        for(unsigned C=0;C<2;++C)
        {
            E->ShadowResolution[C]=1024;
            while(E->ShadowResolution[C]*2<=(unsigned)Requested[C] && E->ShadowResolution[C]*2<=Limit)
                E->ShadowResolution[C]*=2;
        }
        E->ShadowStaticMaxAge=(DWORD)(ReadShadowSetting("shadow_static_cache_seconds",10,1,600)*1000.0f);
        E->ShadowShortReach=ReadShadowSetting("shadow_npc_ship_length",100,1,200);
        E->ShadowModerateSearchSamples=ReadShadowSetting("shadow_moderate_search_samples",8,2,64);
        E->ShadowModerateFilterSamples=ReadShadowSetting("shadow_moderate_filter_samples",8,2,192);
        E->ShadowNearRadius=ReadShadowSetting("shadow_near_radius",150,100,1500);
        E->ShadowFarRadius=ReadShadowSetting("shadow_scene_radius",5000,E->ShadowNearRadius*2,15000);
        E->ShadowMaxLength=ReadShadowSetting("shadow_max_length",200,1,200);
        E->ShadowStrength=ReadShadowSetting("shadow_strength",0.85f,0,1);
        E->ShadowLightAngle=ReadShadowSetting("shadow_light_angle",2,0,10);
        E->ShadowSearchSamples=(unsigned)ReadShadowSetting("shadow_search_samples",16,8,64);
        E->ShadowFilterSamples=(unsigned)ReadShadowSetting("shadow_filter_samples",32,16,192);
        E->ShadowBiasScale=ReadShadowSetting("shadow_bias",0.5f,0.05f,4);
        E->bShadowAdaptiveQuality=ReadShadowSetting("shadow_adaptive_quality",1,0,1)>0.5f;
        E->ShadowStaticQualityDistance=ReadShadowSetting("shadow_static_quality_distance",500,50,5000);
        E->ShadowShipQualityDistance=ReadShadowSetting("shadow_ship_quality_distance",150,25,2000);
        E->ShadowLowSearchSamples=ReadShadowSetting("shadow_low_search_samples",4,2,16);
        E->ShadowLowFilterSamples=ReadShadowSetting("shadow_low_filter_samples",4,2,16);
    }
    for (unsigned I=0; I<12; ++I) if (!std::isfinite(View12[I])) return GR_INVALID_PARMS;
    for (unsigned I=0; I<3; ++I)
        if (!std::isfinite(Position[I]) || !std::isfinite(SunDirection[I])) return GR_INVALID_PARMS;
    D3DXVECTOR3 Ray(SunDirection), Up(0,1,0), Zero(0,0,0);
    if (D3DXVec3LengthSq(&Ray) < 0.5f) return GR_INVALID_PARMS;
    D3DXVec3Normalize(&Ray,&Ray);
    // Cache in a world-anchored light frame, independent of camera rotation.
    // Preserve the light direction only within a sub-texel angular tolerance.
    float MoveSq=0,RaySq=0;
    for(unsigned I=0;I<3;++I)
    {
        float D=Position[I]-E->ShadowStaticAnchor[I]; MoveSq+=D*D;
        D=(&Ray.x)[I]-E->ShadowStaticRay[I]; RaySq+=D*D;
    }
    const float Margin=E->ShadowFarRadius*0.05f;
    // A cached map built for a slightly different sun direction displaces a shadow by the
    // angle times its length: keep that under one far texel for the longest shadow.
    const float RayTolerance=(std::max)(1.e-6f,2.0f*E->ShadowFarRadius/E->ShadowResolution[1]/
        (E->ShadowMaxLength+50.0f));
    if(!E->bShadowStaticValid || MoveSq>Margin*Margin || RaySq>RayTolerance*RayTolerance ||
       (DWORD)(GetTickCount()-E->ShadowStaticBuiltAt)>E->ShadowStaticMaxAge)
    {
        if(E->bShadowStaticValid)
            ++E->ShadowStaticReasons[MoveSq>Margin*Margin ? 0 : RaySq>RayTolerance*RayTolerance ? 1 : 2];
        E->bShadowStaticValid=false;
        memcpy(E->ShadowStaticAnchor,Position,12);
        memcpy(E->ShadowStaticRay,&Ray,12);
    }
    if (fabs(Ray.y)>0.95f) Up=D3DXVECTOR3(1,0,0);
    // RP9 SetModelview flips game-view Z. Undo exactly that rotation for shadow space.
    float Flip[12]; memcpy(Flip,View12,sizeof(Flip));
    Flip[6]=-Flip[6]; Flip[7]=-Flip[7]; Flip[8]=-Flip[8];
    Flip[9]=Flip[10]=Flip[11]=0;
    FRp9TransformCache Rotation={}; Rotation.StoreAffine(Flip);
    memcpy(E->ShadowCameraRotation,Rotation.Values,64);
    memcpy(E->ShadowCameraPosition,Position,12);
    D3DXMATRIX CameraRotation, InverseRotation, LightView, Projection, RelativeLight;
    memcpy(&CameraRotation,Rotation.Values,64);
    if (!D3DXMatrixInverse(&InverseRotation,nullptr,&CameraRotation)) return GR_GENERIC;
    D3DXVECTOR3 ViewRay; D3DXVec3TransformNormal(&ViewRay,&Ray,&CameraRotation);
    memcpy(E->ShadowSunDirection,&ViewRay,12);
    D3DXVECTOR3 Eye=-Ray*30000.0f;
    D3DXMatrixLookAtLH(&LightView,&Eye,&Zero,&Up);
    for (unsigned C=0; C<2; ++C)
    {
        const float Half=C==0 ? E->ShadowNearRadius : E->ShadowFarRadius;
        const float DepthHalf=Half+E->ShadowMaxLength+50.0f;
        E->ShadowDepthSpan[C]=DepthHalf*2;
        D3DXMATRIX Snapped=LightView;
        // A reused far map must use precisely its original light basis.
        if(C==1 && E->bShadowStaticValid)
        {
            D3DXVECTOR3 CachedRay(E->ShadowStaticRay),CachedUp(0,1,0);
            if(fabs(CachedRay.y)>0.95f) CachedUp=D3DXVECTOR3(1,0,0);
            D3DXVECTOR3 CachedEye=-CachedRay*30000.0f;
            D3DXMatrixLookAtLH(&Snapped,&CachedEye,&Zero,&CachedUp);
        }
        // A local map needs only receivers in its region plus short upstream
        // casters. Remote station walls must not hide nearby ship casters in
        // the first-depth map when their own shadow reach is already exhausted.
        Snapped._43=DepthHalf;
        // Snap the world-space shadow centre to texels to suppress camera shimmer.
        const float* Anchor=C==1 && E->bShadowStaticValid ? E->ShadowStaticAnchor : Position;
        const double X=(double)Anchor[0]*Snapped._11+(double)Anchor[1]*Snapped._21+(double)Anchor[2]*Snapped._31;
        const double Y=(double)Anchor[0]*Snapped._12+(double)Anchor[1]*Snapped._22+(double)Anchor[2]*Snapped._32;
        const double Texel=2.0*Half/E->ShadowResolution[C];
        Snapped._41+=(float)(X-std::floor(X/Texel+0.5)*Texel);
        Snapped._42+=(float)(Y-std::floor(Y/Texel+0.5)*Texel);
        if(C==1 && E->bShadowStaticValid)
        {
            D3DXVECTOR3 Delta(Position[0]-Anchor[0],Position[1]-Anchor[1],Position[2]-Anchor[2]),Shift;
            D3DXVec3TransformNormal(&Shift,&Delta,&Snapped);
            Snapped._41+=Shift.x; Snapped._42+=Shift.y; Snapped._43+=Shift.z;
        }
        D3DXMatrixMultiply(&RelativeLight,&InverseRotation,&Snapped);
        D3DXMatrixOrthoLH(&Projection,Half*2,Half*2,0,DepthHalf*2);
        D3DXMATRIX Result; D3DXMatrixMultiply(&Result,&RelativeLight,&Projection);
        memcpy(E->ShadowMatrices[C],&Result,64);
    }
    E->bShadowFrameValid=true;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::AddLocalShadowPlanet(const float* Center, float Radius)
{
    FRp9ExState* E=Ex_;
    if (!Center || !(Radius>0) || !std::isfinite(Radius) || E->ShadowPlanetCount>=8) return GR_INVALID_PARMS;
    D3DXVECTOR3 Delta;
    for(unsigned I=0;I<3;++I) { if(!std::isfinite(Center[I])) return GR_INVALID_PARMS; (&Delta.x)[I]=Center[I]-E->ShadowCameraPosition[I]; }
    if (D3DXVec3Length(&Delta)-Radius>35000) return GR_OK;
    D3DXMATRIX Rotation; memcpy(&Rotation,E->ShadowCameraRotation,64);
    D3DXVECTOR3 View; D3DXVec3TransformNormal(&View,&Delta,&Rotation);
    float* P=E->ShadowPlanets[E->ShadowPlanetCount++]; memcpy(P,&View,12); P[3]=Radius;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::BeginStaticShadowCache(unsigned long Low,unsigned long High)
{
    FRp9ExState* E=Ex_;
    if(!E->bShadowStaticCache || E->bShadowStaticFailed) return GR_GENERIC;
    E->bShadowStaticPrepared=false;
    E->ShadowStaticPendingKey[0]=Low; E->ShadowStaticPendingKey[1]=High;
    if(E->bShadowStaticValid && E->ShadowStaticKey[0]==Low && E->ShadowStaticKey[1]==High)
    {
        E->bShadowStaticPrepared=true; ++E->ShadowStaticHits;
        if(E->ShadowStaticHits==1 || (E->ShadowStaticHits%600)==0)
            ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"static shadow cache: builds %u, reused %u (far cascade); "
                   "rebuilt for camera move %u, sun direction %u, age %u, scene key %u",
                   E->ShadowStaticBuilds,E->ShadowStaticHits,E->ShadowStaticReasons[0],E->ShadowStaticReasons[1],
                   E->ShadowStaticReasons[2],E->ShadowStaticReasons[3]);
        return 1;
    }
    if(E->bShadowStaticValid) ++E->ShadowStaticReasons[3];
    E->bShadowStaticValid=false;
    // The frame matrix may still use a previous anchor. Keep that anchor when
    // rebuilding after a geometry-key change; the transform remains consistent.
    return BeginLocalShadowMap(0x101u);
}

GENRESULT DACOM_API FDirectX9::BeginLocalShadowMap(unsigned long Cascade)
{
    ExFlushSurfaceInstances();
    FRp9ExState* E=Ex_;
    const bool StaticPass=(Cascade==0x101u);
    if(StaticPass) Cascade=1;
    // Cascade 2: the near map's moving casters (ships, asteroids), same projection as cascade 0.
    if (!Device_ || !E->bShadowFrameValid || Cascade>2 || E->bInPass || E->bShadowDrawing || E->bSurfaceActive || E->bShadowFailed)
        return GR_GENERIC;
    ExSurfaceRelease();
    HRESULT Hr=S_OK;
    if (!E->ShadowVs || !E->ShadowPs)
    {
        char Module[MAX_PATH]={}; GetModuleFileNameA(nullptr,Module,MAX_PATH);
        char* Slash=strrchr(Module,'\\'); if(!Slash) return GR_GENERIC; Slash[1]=0;
        std::string Path=std::string(Module)+"../DATA_EXTRA/SHADERS/local_shadow.hlsl", Source;
        FILE* File=fopen(Path.c_str(),"rb");
        if(File) { char B[4096]; size_t N; while((N=fread(B,1,sizeof(B),File))!=0) Source.append(B,N); fclose(File); }
        std::vector<unsigned char> Vs,Ps;
        bool Ok=!Source.empty() && CompileStage(Source,Path,nullptr,"VSMain","vs_3_0",&Vs) && CompileStage(Source,Path,nullptr,"PSMain","ps_3_0",&Ps);
        if(Ok && !E->ShadowVs) Ok=SUCCEEDED(Device_->CreateVertexShader((DWORD*)Vs.data(),&E->ShadowVs));
        if(Ok && !E->ShadowPs) Ok=SUCCEEDED(Device_->CreatePixelShader((DWORD*)Ps.data(),&E->ShadowPs));
        if(!Ok) { E->bShadowFailed=true; return GR_GENERIC; }
    }
    for(;;)
    {
        // One depth surface serves both maps: the larger size, with a per-map viewport.
        const unsigned DepthSize=(std::max)(E->ShadowResolution[0],E->ShadowResolution[1]);
        for(unsigned C=0;C<2 && SUCCEEDED(Hr);++C)
            if(!E->ShadowMaps[C]) Hr=Device_->CreateTexture(E->ShadowResolution[C],E->ShadowResolution[C],1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&E->ShadowMaps[C],nullptr);
        if(SUCCEEDED(Hr) && !E->ShadowDepth) Hr=Device_->CreateDepthStencilSurface(DepthSize,DepthSize,D3DFMT_D24X8,D3DMULTISAMPLE_NONE,0,TRUE,&E->ShadowDepth,nullptr);
        if(SUCCEEDED(Hr) || DepthSize<=1024) break;
        for(auto*& Map:E->ShadowMaps) if(Map) {Map->Release();Map=nullptr;} // incl. cascade 2
        if(E->ShadowDepth) {E->ShadowDepth->Release();E->ShadowDepth=nullptr;}
        for(unsigned C=0;C<2;++C) E->ShadowResolution[C]=(std::max)(1024u,E->ShadowResolution[C]/2);
        Hr=S_OK;
        ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"shadow allocation fallback: near %u, far %u",
               E->ShadowResolution[0],E->ShadowResolution[1]);
    }
    if(FAILED(Hr)) { E->bShadowFailed=true; return GR_GENERIC; }
    if(Cascade==2 && !E->ShadowMaps[2] &&
       FAILED(Device_->CreateTexture(E->ShadowResolution[0],E->ShadowResolution[0],1,D3DUSAGE_RENDERTARGET,
                                    D3DFMT_R32F,D3DPOOL_DEFAULT,&E->ShadowMaps[2],nullptr)))
        return GR_GENERIC; // the caller draws those casters into the near map instead
    if(StaticPass && !E->ShadowStaticMap)
    {
        unsigned Required=E->ShadowResolution[1]*E->ShadowResolution[1]*4u;
        unsigned Available=Device_->GetAvailableTextureMem();
        if(Available && Available<Required+128u*1024u*1024u)
        {
            ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"static shadow cache disabled: insufficient texture-memory headroom");
            E->bShadowStaticFailed=true; return GR_GENERIC;
        }
        Hr=Device_->CreateTexture(E->ShadowResolution[1],E->ShadowResolution[1],1,D3DUSAGE_RENDERTARGET,
                                 D3DFMT_R32F,D3DPOOL_DEFAULT,&E->ShadowStaticMap,nullptr);
        if(FAILED(Hr)) {E->bShadowStaticFailed=true;return GR_GENERIC;}
    }
    FlushDrawState(Device_);
    E->ShadowSavedRenderStates=RenderStates_; E->ShadowSavedDeviceStates=DeviceStates_;
    E->ShadowSavedTransforms=Transforms_; E->ShadowSavedStream=StreamCache_;
    E->ShadowSavedBaseVertex=DeviceBaseVertex_;
    E->ShadowSavedMaterial=E->SurfaceMaterial;E->bShadowSavedMaterialValid=E->bSurfaceMaterialValid;
    memcpy(E->ShadowSavedPipeline,PipelineStates_,sizeof(PipelineStates_));
    // Creating a D3DSBT_ALL block allocates and captures the whole device state; capture
    // into the one block instead (released with the shadow maps before a device reset).
    Hr=E->ShadowSavedState ? E->ShadowSavedState->Capture() :
        Device_->CreateStateBlock(D3DSBT_ALL,&E->ShadowSavedState);
    if(FAILED(Hr)) return GR_GENERIC;
    Hr=Device_->GetRenderTarget(0,&E->ShadowSavedColor);
    if(SUCCEEDED(Hr)) Hr=Device_->GetViewport(&E->ShadowSavedViewport);
    if(FAILED(Hr))
    {
        if(E->ShadowSavedColor) {E->ShadowSavedColor->Release();E->ShadowSavedColor=nullptr;}
        return GR_GENERIC;
    }
    Device_->GetDepthStencilSurface(&E->ShadowSavedDepth); // no surface is valid too
    E->bShadowDrawing=true; E->ShadowCascade=Cascade; E->bShadowStaticDrawing=StaticPass;
    E->bShadowShortCaster=false;
    ExGpuMark(FRp9GpuTimers::ShadowBegin);
    // Remove any sampler alias before making its texture the render target (the surface
    // route keeps the maps on samplers 8/9 and the station map on 11). The far map holds only
    // moving casters when the station map is valid; receivers read both (no composite).
    Rp9SetTexture(Device_, 8,nullptr); Rp9SetTexture(Device_, 9,nullptr); Rp9SetTexture(Device_, 11,nullptr);
    Rp9SetTexture(Device_, 12,nullptr);
    IDirect3DSurface9* Target=nullptr;
    Hr=(StaticPass ? E->ShadowStaticMap : E->ShadowMaps[Cascade])->GetSurfaceLevel(0,&Target);
    if(SUCCEEDED(Hr)) Hr=Device_->SetDepthStencilSurface(nullptr);
    if(SUCCEEDED(Hr)) Hr=Device_->SetRenderTarget(0,Target);
    if(Target) Target->Release();
    if(SUCCEEDED(Hr)) Hr=Device_->SetDepthStencilSurface(E->ShadowDepth);
    const unsigned Size=E->ShadowResolution[Cascade==2 ? 0 : Cascade];
    D3DVIEWPORT9 V={0,0,Size,Size,0,1}; if(SUCCEEDED(Hr)) Hr=Device_->SetViewport(&V);
    if(SUCCEEDED(Hr)) Hr=Device_->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xffffffff,1,0);
    if(FAILED(Hr))
    {
        EndLocalShadowMap(); E->ShadowReadyMask=0;
        if(StaticPass) {E->bShadowStaticValid=false;E->bShadowStaticPrepared=false;E->bShadowStaticFailed=true;}
        return GR_GENERIC;
    }
    return GR_OK;
}

// Ordinary draws are NEVER suppressed outside a successfully opened shadow map.
// During that map only opaque rigid triangles enter the depth-only shaders.
bool FDirectX9::ExShadowDrawBegin()
{
    FRp9ExState* E=Ex_;
    if (!E || !E->bShadowDrawing) return true;
    unsigned long Fvf=StreamCache_.Fvf;
    if(!Fvf && StreamCache_.VertexBuffer) Fvf=StreamCache_.VertexBuffer->Fvf;
    if((Fvf&D3DFVF_POSITION_MASK)!=D3DFVF_XYZ || RenderStates_.GetPending(kRsAlphaBlendEnable)) return false;
    float C[20]={}; float WorldView[16];
    MulMatrix4(Transforms_.World.Values,Transforms_.View.Values,WorldView);
    MulMatrix4(WorldView,E->ShadowMatrices[E->ShadowCascade==2 ? 0 : E->ShadowCascade],C);
    if(RenderStates_.GetPending(D3DRS_ALPHATESTENABLE))
    {
        const unsigned Func=RenderStates_.GetPending(D3DRS_ALPHAFUNC);
        if(Func!=D3DCMP_GREATER && Func!=D3DCMP_GREATEREQUAL) return false;
        C[16]=1; C[17]=RenderStates_.GetPending(D3DRS_ALPHAREF)/255.0f;
        C[18]=E->bSurfaceMaterialValid ? E->SurfaceMaterial.Diffuse.a : 1;
    }
    Rp9SetRenderState(Device_, D3DRS_ZENABLE,TRUE); Rp9SetRenderState(Device_, D3DRS_ZWRITEENABLE,TRUE);
    Rp9SetRenderState(Device_, D3DRS_ZFUNC,D3DCMP_LESSEQUAL); Rp9SetRenderState(Device_, D3DRS_ALPHABLENDENABLE,FALSE);
    Rp9SetRenderState(Device_, D3DRS_ALPHATESTENABLE,FALSE); Rp9SetRenderState(Device_, D3DRS_COLORWRITEENABLE,15);
    Rp9SetRenderState(Device_, D3DRS_FOGENABLE,FALSE); Rp9SetRenderState(Device_, D3DRS_SRGBWRITEENABLE,FALSE);
    if(FAILED(Rp9SetVertexShader(Device_, E->ShadowVs)) || FAILED(Rp9SetPixelShader(Device_, E->ShadowPs))) return false;
    C[19]=E->bShadowShortCaster ? -1.0f : 1.0f;
    Rp9SetVertexConstants(Device_, 0,C,4); Rp9SetPixelConstants(Device_, 4,C+16,1);
    return true;
}

GENRESULT DACOM_API FDirectX9::EndLocalShadowMap()
{
    FRp9ExState* E=Ex_;
    if(!E->bShadowDrawing) return GR_GENERIC;
    E->bShadowDrawing=false;
    Device_->SetDepthStencilSurface(nullptr); Device_->SetRenderTarget(0,E->ShadowSavedColor);
    Device_->SetDepthStencilSurface(E->ShadowSavedDepth); Device_->SetViewport(&E->ShadowSavedViewport);
    HRESULT Hr=E->ShadowSavedState->Apply();
    Rp9DeviceCalls().Invalidate();
    E->bShadowShortCaster=false;
    ExGpuMark(FRp9GpuTimers::ShadowEnd);
    if(E->ShadowSavedColor) {E->ShadowSavedColor->Release();E->ShadowSavedColor=nullptr;}
    if(E->ShadowSavedDepth) {E->ShadowSavedDepth->Release();E->ShadowSavedDepth=nullptr;}
    RenderStates_=E->ShadowSavedRenderStates; DeviceStates_=E->ShadowSavedDeviceStates;
    Transforms_=E->ShadowSavedTransforms; StreamCache_=E->ShadowSavedStream;
    DeviceBaseVertex_=E->ShadowSavedBaseVertex;
    E->SurfaceMaterial=E->ShadowSavedMaterial;E->bSurfaceMaterialValid=E->bShadowSavedMaterialValid;
    memcpy(PipelineStates_,E->ShadowSavedPipeline,sizeof(PipelineStates_));
    if(E->bShadowStaticDrawing)
    {
        E->bShadowStaticValid=SUCCEEDED(Hr);
        E->bShadowStaticPrepared=SUCCEEDED(Hr);
        if(SUCCEEDED(Hr))
        {
            memcpy(E->ShadowStaticKey,E->ShadowStaticPendingKey,sizeof(E->ShadowStaticKey));
            E->ShadowStaticBuiltAt=GetTickCount(); ++E->ShadowStaticBuilds;
            if(E->ShadowStaticBuilds==1 || (E->ShadowStaticBuilds%30)==0)
                ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"static shadow cache: builds %u, reused %u (far cascade); "
                       "rebuilt for camera move %u, sun direction %u, age %u, scene key %u",
                       E->ShadowStaticBuilds,E->ShadowStaticHits,E->ShadowStaticReasons[0],E->ShadowStaticReasons[1],
                       E->ShadowStaticReasons[2],E->ShadowStaticReasons[3]);
        }
        E->bShadowStaticDrawing=false;
    }
    else if(SUCCEEDED(Hr)) E->ShadowReadyMask|=1u<<E->ShadowCascade;
    return (GENRESULT)Hr;
}

void FDirectX9::ExShadowRelease()
{
    FRp9ExState* E=Ex_; if(!E) return;
    if(E->bShadowDrawing && Device_) EndLocalShadowMap();
    E->ShadowReadyMask=0; E->bShadowReceiver=false;
    E->bShadowFrameValid=false;
    // The device holds a reference to bound textures: unbind before releasing the maps.
    if(Device_) {Rp9SetTexture(Device_,8,nullptr);Rp9SetTexture(Device_,9,nullptr);Rp9SetTexture(Device_,11,nullptr);
                 Rp9SetTexture(Device_,12,nullptr);}
    if(E->ShadowSavedState) {E->ShadowSavedState->Release();E->ShadowSavedState=nullptr;}
    E->bShadowStaticValid=false; E->bShadowStaticPrepared=false;
    E->bShadowStaticFailed=false;
    if(E->ShadowStaticMap) {E->ShadowStaticMap->Release();E->ShadowStaticMap=nullptr;}
    for(unsigned C=0;C<3;++C) if(E->ShadowMaps[C]) {E->ShadowMaps[C]->Release();E->ShadowMaps[C]=nullptr;}
    if(E->ShadowDepth) {E->ShadowDepth->Release();E->ShadowDepth=nullptr;}
    if(E->ShadowVs) {E->ShadowVs->Release();E->ShadowVs=nullptr;}
    if(E->ShadowPs) {E->ShadowPs->Release();E->ShadowPs=nullptr;}
}

void FDirectX9::ExInitQualityConfig()
{
    if(Ex_->bQualityConfigRead || !Device_) return;
    Ex_->bQualityConfigRead=true;
    D3DCAPS9 Caps={};Device_->GetDeviceCaps(&Caps);
    Ex_->QualityAnisotropy=(unsigned)ReadShadowSetting("anisotropy",16,1,16);
    Ex_->QualityAnisotropy=(std::min)(Ex_->QualityAnisotropy,(unsigned)Caps.MaxAnisotropy);
    if(!(Caps.TextureFilterCaps&D3DPTFILTERCAPS_MINFANISOTROPIC)) Ex_->QualityAnisotropy=1;
    // 0 off, 1 the space scene before the HUD, 2 the whole frame at SwapBuffers (HUD included;
    // FXAA damages small interface text, so it is opt-in).
    Ex_->QualityFxaaMode=(unsigned)ReadShadowSetting("fxaa",1,0,2);
    ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"frame quality: AF %ux, FXAA %s, MSAA off (INTZ depth)",
        Ex_->QualityAnisotropy,Ex_->QualityFxaaMode==2 ? "full frame" : Ex_->QualityFxaaMode==1 ? "before HUD" : "off");
}

GENRESULT DACOM_API FDirectX9::ApplySceneAntialiasing()
{
    // Called after the space scene, before the HUD (fxaa = 1). fxaa = 2 filters the finished
    // frame at SwapBuffers instead (HUD and wireframes included).
    ExInitQualityConfig();
    if(!Ex_ || Ex_->QualityFxaaMode!=1) return GR_OK;
    return ExApplyFrameAntialiasing();
}

GENRESULT FDirectX9::ExApplyFrameAntialiasing()
{
    ExFlushSurfaceInstances();
    if(!Device_ || !Ex_ || Ex_->bInPass || Ex_->bShadowDrawing || Ex_->bSurfaceActive) return GR_GENERIC;
    ExInitQualityConfig();
    FRp9ExState* E=Ex_;
    if(!E->QualityFxaaMode || E->bQualityFxaaFailed) return GR_OK;
    if(!E->QualityFxaaPs)
    {
        char Module[MAX_PATH]={};GetModuleFileNameA(nullptr,Module,MAX_PATH);
        char* Slash=strrchr(Module,'\\');if(!Slash) return GR_GENERIC;Slash[1]=0;
        std::string Path=std::string(Module)+"../DATA_EXTRA/SHADERS/scene_fxaa.hlsl",Source;
        FILE* File=fopen(Path.c_str(),"rb");
        if(File) {char B[4096];size_t N;while((N=fread(B,1,sizeof(B),File))!=0) Source.append(B,N);fclose(File);}
        std::vector<unsigned char> Code;
        if(Source.empty() || !CompileStage(Source,Path,nullptr,"PSMain","ps_3_0",&Code) ||
            FAILED(Device_->CreatePixelShader((DWORD*)Code.data(),&E->QualityFxaaPs)))
        {E->bQualityFxaaFailed=true;return GR_GENERIC;}
    }
    ExSurfaceRelease();
    IDirect3DSurface9* Target=nullptr;
    HRESULT Hr=Device_->GetRenderTarget(0,&Target);if(FAILED(Hr)) return (GENRESULT)Hr;
    D3DSURFACE_DESC Desc={};Hr=Target->GetDesc(&Desc);
    if(SUCCEEDED(Hr) && E->QualitySceneCopy)
    {
        D3DSURFACE_DESC Old={};E->QualitySceneCopy->GetLevelDesc(0,&Old);
        if(Old.Width!=Desc.Width || Old.Height!=Desc.Height || Old.Format!=Desc.Format)
        {E->QualitySceneCopy->Release();E->QualitySceneCopy=nullptr;}
    }
    if(SUCCEEDED(Hr) && !E->QualitySceneCopy)
        Hr=Device_->CreateTexture(Desc.Width,Desc.Height,1,D3DUSAGE_RENDERTARGET,Desc.Format,
                                 D3DPOOL_DEFAULT,&E->QualitySceneCopy,nullptr);
    IDirect3DSurface9* Copy=nullptr;
    if(SUCCEEDED(Hr)) Hr=E->QualitySceneCopy->GetSurfaceLevel(0,&Copy);
    // StretchRect runs outside BeginScene/EndScene. Inside the caller's scene (fxaa = 2)
    // the scene is closed around it; after the frame's EndScene (SwapBuffers) a scene is
    // opened for the filter draw only.
    const bool InScene=E->bInScene;
    if(SUCCEEDED(Hr))
    {
        Hr=InScene ? Device_->EndScene() : S_OK;
        if(SUCCEEDED(Hr))
        {
            HRESULT CopyHr=Device_->StretchRect(Target,nullptr,Copy,nullptr,D3DTEXF_NONE);
            Hr=Device_->BeginScene();if(SUCCEEDED(Hr)) Hr=CopyHr;
        }
    }
    if(Copy) Copy->Release();Target->Release();
    if(FAILED(Hr)) return (GENRESULT)Hr;
    ExGpuMark(FRp9GpuTimers::AaBegin);
    FlushDrawState(Device_);
    Hr=E->QualitySavedState ? E->QualitySavedState->Capture() :
        Device_->CreateStateBlock(D3DSBT_ALL,&E->QualitySavedState);
    if(FAILED(Hr)) {if(!InScene) Device_->EndScene();return (GENRESULT)Hr;}
    float P[4]={1.0f/Desc.Width,1.0f/Desc.Height,0,0};
    struct Vertex {float X,Y,Z,W,U,V;};
    Vertex Quad[]={{-.5f,-.5f,0,1,0,0},{Desc.Width-.5f,-.5f,0,1,1,0},
                   {-.5f,Desc.Height-.5f,0,1,0,1},{Desc.Width-.5f,Desc.Height-.5f,0,1,1,1}};
    D3DVIEWPORT9 View={0,0,Desc.Width,Desc.Height,0,1};Device_->SetViewport(&View);
    Rp9SetVertexShader(Device_, nullptr);Rp9SetFvf(Device_, D3DFVF_XYZRHW|D3DFVF_TEX1);
    Rp9SetPixelShader(Device_, E->QualityFxaaPs);Rp9SetPixelConstants(Device_, 0,P,1);
    Device_->SetTextureStageState(0,D3DTSS_TEXCOORDINDEX,0);
    Device_->SetTextureStageState(0,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_DISABLE);
    Rp9SetRenderState(Device_, D3DRS_ZENABLE,FALSE);Rp9SetRenderState(Device_, D3DRS_ZWRITEENABLE,FALSE);
    Rp9SetRenderState(Device_, D3DRS_ALPHATESTENABLE,FALSE);Rp9SetRenderState(Device_, D3DRS_ALPHABLENDENABLE,FALSE);
    Rp9SetRenderState(Device_, D3DRS_FOGENABLE,FALSE);Rp9SetRenderState(Device_, D3DRS_CULLMODE,D3DCULL_NONE);
    Rp9SetRenderState(Device_, D3DRS_SCISSORTESTENABLE,FALSE);Rp9SetRenderState(Device_, D3DRS_SRGBWRITEENABLE,FALSE);
    Rp9SetRenderState(Device_, D3DRS_CLIPPLANEENABLE,0);Rp9SetRenderState(Device_, D3DRS_STENCILENABLE,FALSE);
    Rp9SetRenderState(Device_, D3DRS_FILLMODE,D3DFILL_SOLID);
    Rp9SetRenderState(Device_, D3DRS_COLORWRITEENABLE,15);Rp9SetTexture(Device_, 0,E->QualitySceneCopy);
    Rp9SetSamplerState(Device_, 0,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);Rp9SetSamplerState(Device_, 0,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
    Rp9SetSamplerState(Device_, 0,D3DSAMP_MIPFILTER,D3DTEXF_NONE);Rp9SetSamplerState(Device_, 0,D3DSAMP_SRGBTEXTURE,FALSE);
    Rp9SetSamplerState(Device_, 0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Rp9SetSamplerState(Device_, 0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    Hr=Device_->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Quad,sizeof(Vertex));
    HRESULT Restore=E->QualitySavedState->Apply();
    Rp9DeviceCalls().Invalidate();
    ExGpuMark(FRp9GpuTimers::AaEnd);
    if(!InScene)
    {
        HRESULT EndHr=Device_->EndScene();
        if(SUCCEEDED(Restore)) Restore=EndHr;
    }
    return (GENRESULT)(FAILED(Hr) ? Hr : Restore);
}
