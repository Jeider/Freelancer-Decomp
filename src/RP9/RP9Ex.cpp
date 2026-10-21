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
#include "readfile.h"

#include <cstdarg>
#include <cstddef>
#include <cmath>
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

// d3dx9.h after RP9.h (render/d3d8_min.h already pulled the Windows SDK d3d9.h).
#include <d3dx9.h>
#include "RP9ShaderCache.h"

namespace
{
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
                Device->SetTexture(Sampler, nullptr);
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
                    Device->SetTexture(Sampler, nullptr);
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
        const HRESULT Hr = Device->SetTexture(Sampler, Texture);
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
        Device->SetSamplerState(Sampler, D3DSAMP_MAGFILTER, ExFilterToD3d(Use->MinMagFilter));
        Device->SetSamplerState(Sampler, D3DSAMP_MINFILTER, ExFilterToD3d(Use->MinMagFilter));
        Device->SetSamplerState(Sampler, D3DSAMP_MIPFILTER, ExMipFilterToD3d(Use->MipFilter));
        Device->SetSamplerState(Sampler, D3DSAMP_ADDRESSU, ExAddressToD3d(Use->AddressU));
        Device->SetSamplerState(Sampler, D3DSAMP_ADDRESSV, ExAddressToD3d(Use->AddressV));
        Device->SetSamplerState(Sampler, D3DSAMP_ADDRESSW, ExAddressToD3d(Use->AddressW));
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
            Device->SetVertexShader(nullptr);
            Device->SetPixelShader(nullptr);
            for (unsigned long Sampler = 0; Sampler < kExSamplerCount; ++Sampler)
            {
                if ((Ex->TouchedSamplers & (1ul << Sampler)) == 0)
                    continue;
                if (Sampler < FRp9DeviceStateCaches::StageCount)
                    Self->ExRestoreStage(Sampler, &Ex->SavedStages[Sampler]);
                else
                    Device->SetTexture(Sampler, nullptr);
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
    return S_OK;
}

void FDirectX9::ExReleaseDeviceResources()
{
    ExShadowRelease();
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr)
        return;
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
    if (Ex->SurfacePs != nullptr) { Ex->SurfacePs->Release(); Ex->SurfacePs = nullptr; }
    if (Ex->SurfaceCubePs != nullptr) { Ex->SurfaceCubePs->Release(); Ex->SurfaceCubePs = nullptr; }
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
            Device_->SetVertexShader(nullptr);
            Device_->SetPixelShader(nullptr);
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
            Device_->SetVertexShader(Program->Vs);
            Device_->SetPixelShader(Program->Ps);
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
    Ex->bInPass = true;

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
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetExRenderTarget(FRPExTexture* ColorTarget,
                                                 unsigned long bKeepDepth)
{
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
        Device_->SetVertexShader(nullptr);
        Device_->SetPixelShader(nullptr);
        Ex_->BoundProgram = nullptr;
        return GR_OK;
    }
    // A program that never compiled has no shaders; its compile errors are already logged.
    if (Program->Vs == nullptr || Program->Ps == nullptr)
        return GR_GENERIC;
    Device_->SetVertexShader(Program->Vs);
    Device_->SetPixelShader(Program->Ps);
    Ex_->BoundProgram = Program;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetExVertexConstants(unsigned long StartRegister, const float* Data,
                                                    unsigned long Vector4Count)
{
    if (Device_ == nullptr || Data == nullptr)
        return GR_GENERIC;
    return (GENRESULT)(Device_->SetVertexShaderConstantF((UINT)(StartRegister), Data,
                                                         (UINT)(Vector4Count)));
}

GENRESULT DACOM_API FDirectX9::SetExPixelConstants(unsigned long StartRegister, const float* Data,
                                                   unsigned long Vector4Count)
{
    if (Device_ == nullptr || Data == nullptr)
        return GR_GENERIC;
    return (GENRESULT)(Device_->SetPixelShaderConstantF((UINT)(StartRegister), Data,
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
    Device_->SetTexture(1, Ex->SceneDepth.Texture);
    Device_->SetSamplerState(1, D3DSAMP_MAGFILTER, D3DTEXF_POINT);
    Device_->SetSamplerState(1, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    Device_->SetSamplerState(1, D3DSAMP_MIPFILTER, D3DTEXF_NONE);
    Device_->SetSamplerState(1, D3DSAMP_ADDRESSU, D3DTADDRESS_CLAMP);
    Device_->SetSamplerState(1, D3DSAMP_ADDRESSV, D3DTADDRESS_CLAMP);
    Device_->SetVertexShader(Ex->SoftVs);
    Device_->SetPixelShader(Ex->SoftPs);
    Device_->SetVertexShaderConstantF(0, VsConstants, 8);
    Device_->SetPixelShaderConstantF(0, PsConstants, 5);
    Ex->bSoftActive = true;
    return true;
}

void FDirectX9::ExSoftEnd()
{
    FRp9ExState* Ex = Ex_;
    if (Ex == nullptr || !Ex->bSoftActive)
        return;
    Ex->bSoftActive = false;
    Device_->SetVertexShader(nullptr);
    Device_->SetPixelShader(nullptr);
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
    if (!Ex->bSurfaceEnabled || Ex->SurfaceShader == RPSurfaceLegacy)
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
        ((Ex->bShadowReceiver && Ex->ShadowReadyMask==3) ||
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

    IDirect3DPixelShader9*& SurfacePs = IsCube ? Ex->SurfaceCubePs : Ex->SurfacePs;
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
        const std::string PixelSource = IsCube ? "#define SURFACE_ENV_CUBE 1\n" + Source : Source;
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
    if (D3DXMatrixInverse(&Inverse, nullptr, &M) == nullptr)
        return false;
    D3DXMatrixTranspose(&Normal, &Inverse);
    memcpy(Vs + 32, &Normal, sizeof(Normal));
    const float* EnvMatrix = DeviceStates_.TextureTransforms[PlainShadowReceiver ? 0 : EnvStage].Values;
    memcpy(Vs + 48, EnvMatrix, sizeof(float) * 16);
    const bool ColourVertex = (Fvf & D3DFVF_DIFFUSE) && RenderStates_.GetPending(D3DRS_COLORVERTEX) &&
        RenderStates_.GetPending(D3DRS_DIFFUSEMATERIALSOURCE) == D3DMCS_COLOR1;
    Vs[64] = ColourVertex ? 1.0f : 0.0f;
    Vs[65] = (float)BaseUv;
    Vs[66] = (float)EnvTransform;

    float Ps[95 * 4] = {};
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
    for (unsigned I = 0; I < Count; ++I)
    {
        D3DLIGHT9 const& L = Lights[I];
        D3DXVECTOR3 Pos, Dir;
        D3DXMatrixIdentity(&M);
        memcpy(&M, Transforms_.View.Values, sizeof(M));
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
        Ps[4] += Mat.Ambient.r * L.Ambient.r;
        Ps[5] += Mat.Ambient.g * L.Ambient.g;
        Ps[6] += Mat.Ambient.b * L.Ambient.b;
    }

    ExSaveStage(1, &Ex->SurfaceSavedStage1);
    const bool ShadowReceiver=Ex->bShadowReceiver && Ex->ShadowReadyMask==3;
    memcpy(Ps+52*4,Ex->ShadowMatrices[0],64); memcpy(Ps+56*4,Ex->ShadowMatrices[1],64);
    Set(60,ShadowReceiver ? 1.0f : 0.0f,1.0f/Ex->ShadowResolution,
        Ex->ShadowFarRadius*0.9f,Ex->ShadowFarRadius);
    memcpy(Ps+61*4,Ex->ShadowSunDirection,16);
    Set(62,(float)Ex->ShadowPlanetCount,0,0,0);
    memcpy(Ps+64*4,Ex->ShadowPlanets,sizeof(Ex->ShadowPlanets));
    Set(63,Ex->ShadowMaxLength,Ex->ShadowMaxLength*0.8f,
        Ex->ShadowNearRadius*2,Ex->ShadowFarRadius*2);
    Set(72,std::tan(Ex->ShadowLightAngle*0.00872664626f),
        (float)Ex->ShadowSearchSamples,(float)Ex->ShadowFilterSamples,Ex->ShadowStrength);
    Set(73,Ex->ShadowNearRadius*2/Ex->ShadowResolution,
        Ex->ShadowFarRadius*2/Ex->ShadowResolution,Ex->ShadowBiasScale,0);
    Set(74,Ex->ShadowDepthSpan[0],Ex->ShadowDepthSpan[1],0,0);
    Set(75,Ex->SurfaceHighlights,Ex->SurfaceCoat,Ex->SurfaceBrushed,1);
    Set(76,Ex->bShadowReceiverIsShip ? Ex->ShadowShipQualityDistance : Ex->ShadowStaticQualityDistance,
        Ex->bShadowAdaptiveQuality ? 1.0f : 0.0f,Ex->ShadowLowSearchSamples,Ex->ShadowLowFilterSamples);
    Ex->bSurfaceShadowSamplers=ShadowReceiver;
    if(ShadowReceiver) for(unsigned I=0;I<2;++I)
    {
        ExSaveStage(2+I,&Ex->SurfaceSavedShadowStages[I]);
        Device_->SetTexture(2+I,Ex->ShadowMaps[I]);
        Device_->SetSamplerState(2+I,D3DSAMP_MINFILTER,D3DTEXF_POINT);
        Device_->SetSamplerState(2+I,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
        Device_->SetSamplerState(2+I,D3DSAMP_MIPFILTER,D3DTEXF_NONE);
        Device_->SetSamplerState(2+I,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);
        Device_->SetSamplerState(2+I,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    }
    HRESULT Hr = Device_->SetTexture(1, EnvTexture);
    if (EnvStage == 0)
    {
        // The env-only profile moves sampler 0 to 1; retain the texture's authored wrapping
        // and filters, including special asteroid envmaps.
        const unsigned Types[] = {13, 14, 16, 17, 18};
        const D3DSAMPLERSTATETYPE Samplers[] = {D3DSAMP_ADDRESSU, D3DSAMP_ADDRESSV,
            D3DSAMP_MAGFILTER, D3DSAMP_MINFILTER, D3DSAMP_MIPFILTER};
        const unsigned Defaults[] = {D3DTADDRESS_WRAP, D3DTADDRESS_WRAP, D3DTEXF_POINT, D3DTEXF_POINT, D3DTEXF_NONE};
        for (unsigned I = 0; I < 5 && SUCCEEDED(Hr); ++I)
            Hr = Device_->SetSamplerState(1, Samplers[I], Tss(0, Types[I], Defaults[I]));
    }
    if (SUCCEEDED(Hr)) Hr = Device_->SetVertexShader(Ex->SurfaceVs);
    if (SUCCEEDED(Hr)) Hr = Device_->SetPixelShader(SurfacePs);
    if (SUCCEEDED(Hr)) Hr = Device_->SetVertexShaderConstantF(0, Vs, 17);
    unsigned GlintCount=0;
    if(Ex->bWeaponGlintReceiver) for(unsigned I=0;I<Ex->WeaponGlintCount;++I)
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
    if (SUCCEEDED(Hr)) Hr = Device_->SetPixelShaderConstantF(0, Ps, 95);
    Ex->bSurfaceActive = true;
    if (FAILED(Hr)) { ExSurfaceEnd(); return false; }
    if (!Ex->bSurfaceLogged)
    {
        Ex->bSurfaceLogged = true;
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "reflective surface shader active, FVF 0x%lx, env stage %d", Fvf, EnvStage);
    }
    return true;
}

void FDirectX9::ExSurfaceEnd()
{
    if (Ex_ == nullptr || !Ex_->bSurfaceActive || Device_ == nullptr)
        return;
    Ex_->bSurfaceActive = false;
    Device_->SetVertexShader(nullptr);
    Device_->SetPixelShader(nullptr);
    ExRestoreStage(1, &Ex_->SurfaceSavedStage1);
    if(Ex_->bSurfaceShadowSamplers) for(unsigned I=0;I<2;++I)
        ExRestoreStage(2+I,&Ex_->SurfaceSavedShadowStages[I]);
    Ex_->bSurfaceShadowSamplers=false;
}

// ---- grouped projectile surface glints ---------------------------------------------------
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
    Ex_->bShadowReceiver = Enabled != 0;
    Ex_->bShadowReceiverIsShip = (Enabled&2u)!=0;
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::BeginLocalShadowFrame(const float* View12, const float* Position,
                                                   const float* SunDirection)
{
    FRp9ExState* E = Ex_;
    E->ShadowReadyMask = 0; E->ShadowPlanetCount = 0; E->bShadowReceiver = false;
    E->bShadowFrameValid=false;
    if (!Device_ || E->bShadowDrawing || !View12 || !Position || !SunDirection || E->bShadowFailed)
        return GR_GENERIC;
    if(!E->bShadowConfigRead)
    {
        E->bShadowConfigRead=true;
        unsigned Requested=(unsigned)ReadShadowSetting("shadow_resolution",8192,1024,8192);
        D3DCAPS9 Caps={}; Device_->GetDeviceCaps(&Caps);
        unsigned Limit=(std::min)((unsigned)Caps.MaxTextureWidth,(unsigned)Caps.MaxTextureHeight);
        E->ShadowResolution=1024;
        while(E->ShadowResolution*2<=Requested && E->ShadowResolution*2<=Limit) E->ShadowResolution*=2;
        E->ShadowNearRadius=ReadShadowSetting("shadow_near_radius",150,100,1500);
        E->ShadowFarRadius=ReadShadowSetting("shadow_scene_radius",5000,E->ShadowNearRadius*2,15000);
        E->ShadowMaxLength=ReadShadowSetting("shadow_max_length",200,1,200);
        E->ShadowStrength=ReadShadowSetting("shadow_strength",0.85f,0,1);
        E->ShadowLightAngle=ReadShadowSetting("shadow_light_angle",2,0,10);
        E->ShadowSearchSamples=(unsigned)ReadShadowSetting("shadow_search_samples",64,8,64);
        E->ShadowFilterSamples=(unsigned)ReadShadowSetting("shadow_filter_samples",192,16,192);
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
        // A local map needs only receivers in its region plus short upstream
        // casters. Remote station walls must not hide nearby ship casters in
        // the first-depth map when their own shadow reach is already exhausted.
        Snapped._43=DepthHalf;
        // Snap the world-space shadow centre to texels to suppress camera shimmer.
        const double X=(double)Position[0]*LightView._11+(double)Position[1]*LightView._21+(double)Position[2]*LightView._31;
        const double Y=(double)Position[0]*LightView._12+(double)Position[1]*LightView._22+(double)Position[2]*LightView._32;
        const double Texel=2.0*Half/E->ShadowResolution;
        Snapped._41+=(float)(X-std::floor(X/Texel+0.5)*Texel);
        Snapped._42+=(float)(Y-std::floor(Y/Texel+0.5)*Texel);
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

GENRESULT DACOM_API FDirectX9::BeginLocalShadowMap(unsigned long Cascade)
{
    FRp9ExState* E=Ex_;
    if (!Device_ || !E->bShadowFrameValid || Cascade>1 || E->bInPass || E->bShadowDrawing || E->bSurfaceActive || E->bShadowFailed)
        return GR_GENERIC;
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
        for(unsigned C=0;C<2 && SUCCEEDED(Hr);++C)
            if(!E->ShadowMaps[C]) Hr=Device_->CreateTexture(E->ShadowResolution,E->ShadowResolution,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&E->ShadowMaps[C],nullptr);
        if(SUCCEEDED(Hr) && !E->ShadowDepth) Hr=Device_->CreateDepthStencilSurface(E->ShadowResolution,E->ShadowResolution,D3DFMT_D24X8,D3DMULTISAMPLE_NONE,0,TRUE,&E->ShadowDepth,nullptr);
        if(SUCCEEDED(Hr) || E->ShadowResolution<=1024) break;
        for(auto*& Map:E->ShadowMaps) if(Map) {Map->Release();Map=nullptr;}
        if(E->ShadowDepth) {E->ShadowDepth->Release();E->ShadowDepth=nullptr;}
        E->ShadowResolution/=2; Hr=S_OK;
        ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"shadow allocation fallback: %u",E->ShadowResolution);
    }
    if(FAILED(Hr)) { E->bShadowFailed=true; return GR_GENERIC; }
    FlushDrawState(Device_);
    E->ShadowSavedRenderStates=RenderStates_; E->ShadowSavedDeviceStates=DeviceStates_;
    E->ShadowSavedTransforms=Transforms_; E->ShadowSavedStream=StreamCache_;
    E->ShadowSavedBaseVertex=DeviceBaseVertex_;
    E->ShadowSavedMaterial=E->SurfaceMaterial;E->bShadowSavedMaterialValid=E->bSurfaceMaterialValid;
    memcpy(E->ShadowSavedPipeline,PipelineStates_,sizeof(PipelineStates_));
    Hr=Device_->CreateStateBlock(D3DSBT_ALL,&E->ShadowSavedState);
    if(FAILED(Hr)) return GR_GENERIC;
    Hr=Device_->GetRenderTarget(0,&E->ShadowSavedColor);
    if(SUCCEEDED(Hr)) Hr=Device_->GetViewport(&E->ShadowSavedViewport);
    if(FAILED(Hr))
    {
        if(E->ShadowSavedColor) {E->ShadowSavedColor->Release();E->ShadowSavedColor=nullptr;}
        E->ShadowSavedState->Release();E->ShadowSavedState=nullptr;
        return GR_GENERIC;
    }
    Device_->GetDepthStencilSurface(&E->ShadowSavedDepth); // no surface is valid too
    E->bShadowDrawing=true; E->ShadowCascade=Cascade;
    // Remove any sampler alias before making its texture the render target.
    Device_->SetTexture(2,nullptr); Device_->SetTexture(3,nullptr);
    IDirect3DSurface9* Target=nullptr; Hr=E->ShadowMaps[Cascade]->GetSurfaceLevel(0,&Target);
    if(SUCCEEDED(Hr)) Hr=Device_->SetDepthStencilSurface(nullptr);
    if(SUCCEEDED(Hr)) Hr=Device_->SetRenderTarget(0,Target);
    if(Target) Target->Release();
    if(SUCCEEDED(Hr)) Hr=Device_->SetDepthStencilSurface(E->ShadowDepth);
    D3DVIEWPORT9 V={0,0,E->ShadowResolution,E->ShadowResolution,0,1}; if(SUCCEEDED(Hr)) Hr=Device_->SetViewport(&V);
    if(SUCCEEDED(Hr)) Hr=Device_->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xffffffff,1,0);
    if(FAILED(Hr)) { EndLocalShadowMap(); E->ShadowReadyMask=0; return GR_GENERIC; }
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
    MulMatrix4(WorldView,E->ShadowMatrices[E->ShadowCascade],C);
    if(RenderStates_.GetPending(D3DRS_ALPHATESTENABLE))
    {
        const unsigned Func=RenderStates_.GetPending(D3DRS_ALPHAFUNC);
        if(Func!=D3DCMP_GREATER && Func!=D3DCMP_GREATEREQUAL) return false;
        C[16]=1; C[17]=RenderStates_.GetPending(D3DRS_ALPHAREF)/255.0f;
        C[18]=E->bSurfaceMaterialValid ? E->SurfaceMaterial.Diffuse.a : 1;
    }
    Device_->SetRenderState(D3DRS_ZENABLE,TRUE); Device_->SetRenderState(D3DRS_ZWRITEENABLE,TRUE);
    Device_->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL); Device_->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    Device_->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE); Device_->SetRenderState(D3DRS_COLORWRITEENABLE,15);
    Device_->SetRenderState(D3DRS_FOGENABLE,FALSE); Device_->SetRenderState(D3DRS_SRGBWRITEENABLE,FALSE);
    if(FAILED(Device_->SetVertexShader(E->ShadowVs)) || FAILED(Device_->SetPixelShader(E->ShadowPs))) return false;
    Device_->SetVertexShaderConstantF(0,C,4); Device_->SetPixelShaderConstantF(4,C+16,1);
    return true;
}

GENRESULT DACOM_API FDirectX9::EndLocalShadowMap()
{
    FRp9ExState* E=Ex_;
    if(!E->bShadowDrawing) return GR_GENERIC;
    E->bShadowDrawing=false;
    Device_->SetDepthStencilSurface(nullptr); Device_->SetRenderTarget(0,E->ShadowSavedColor);
    Device_->SetDepthStencilSurface(E->ShadowSavedDepth); Device_->SetViewport(&E->ShadowSavedViewport);
    HRESULT Hr=E->ShadowSavedState->Apply(); E->ShadowSavedState->Release(); E->ShadowSavedState=nullptr;
    if(E->ShadowSavedColor) {E->ShadowSavedColor->Release();E->ShadowSavedColor=nullptr;}
    if(E->ShadowSavedDepth) {E->ShadowSavedDepth->Release();E->ShadowSavedDepth=nullptr;}
    RenderStates_=E->ShadowSavedRenderStates; DeviceStates_=E->ShadowSavedDeviceStates;
    Transforms_=E->ShadowSavedTransforms; StreamCache_=E->ShadowSavedStream;
    DeviceBaseVertex_=E->ShadowSavedBaseVertex;
    E->SurfaceMaterial=E->ShadowSavedMaterial;E->bSurfaceMaterialValid=E->bShadowSavedMaterialValid;
    memcpy(PipelineStates_,E->ShadowSavedPipeline,sizeof(PipelineStates_));
    if(SUCCEEDED(Hr)) E->ShadowReadyMask|=1u<<E->ShadowCascade;
    return (GENRESULT)Hr;
}

void FDirectX9::ExShadowRelease()
{
    FRp9ExState* E=Ex_; if(!E) return;
    if(E->bShadowDrawing && Device_) EndLocalShadowMap();
    E->ShadowReadyMask=0; E->bShadowReceiver=false;
    E->bShadowFrameValid=false;
    for(unsigned C=0;C<2;++C) if(E->ShadowMaps[C]) {E->ShadowMaps[C]->Release();E->ShadowMaps[C]=nullptr;}
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
    Ex_->bQualityFxaa=ReadShadowSetting("fxaa",1,0,1)>0.5f;
    ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"frame quality: AF %ux, FXAA %u (before HUD), MSAA off (INTZ depth)",
        Ex_->QualityAnisotropy,Ex_->bQualityFxaa ? 1u : 0u);
}

GENRESULT DACOM_API FDirectX9::ApplySceneAntialiasing()
{
    if(!Device_ || !Ex_ || Ex_->bInPass || Ex_->bShadowDrawing || Ex_->bSurfaceActive) return GR_GENERIC;
    ExInitQualityConfig();
    FRp9ExState* E=Ex_;
    if(!E->bQualityFxaa || E->bQualityFxaaFailed) return GR_OK;
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
    // StretchRect is outside BeginScene/EndScene; always resume the caller's scene.
    if(SUCCEEDED(Hr))
    {
        Hr=Device_->EndScene();
        if(SUCCEEDED(Hr))
        {
            HRESULT CopyHr=Device_->StretchRect(Target,nullptr,Copy,nullptr,D3DTEXF_NONE);
            Hr=Device_->BeginScene();if(SUCCEEDED(Hr)) Hr=CopyHr;
        }
    }
    if(Copy) Copy->Release();Target->Release();
    if(FAILED(Hr)) return (GENRESULT)Hr;
    FlushDrawState(Device_);
    IDirect3DStateBlock9* Saved=nullptr;
    Hr=Device_->CreateStateBlock(D3DSBT_ALL,&Saved);if(FAILED(Hr)) return (GENRESULT)Hr;
    float P[4]={1.0f/Desc.Width,1.0f/Desc.Height,0,0};
    struct Vertex {float X,Y,Z,W,U,V;};
    Vertex Quad[]={{-.5f,-.5f,0,1,0,0},{Desc.Width-.5f,-.5f,0,1,1,0},
                   {-.5f,Desc.Height-.5f,0,1,0,1},{Desc.Width-.5f,Desc.Height-.5f,0,1,1,1}};
    D3DVIEWPORT9 View={0,0,Desc.Width,Desc.Height,0,1};Device_->SetViewport(&View);
    Device_->SetVertexShader(nullptr);Device_->SetFVF(D3DFVF_XYZRHW|D3DFVF_TEX1);
    Device_->SetPixelShader(E->QualityFxaaPs);Device_->SetPixelShaderConstantF(0,P,1);
    Device_->SetTextureStageState(0,D3DTSS_TEXCOORDINDEX,0);
    Device_->SetTextureStageState(0,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_DISABLE);
    Device_->SetRenderState(D3DRS_ZENABLE,FALSE);Device_->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);
    Device_->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);Device_->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    Device_->SetRenderState(D3DRS_FOGENABLE,FALSE);Device_->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
    Device_->SetRenderState(D3DRS_SCISSORTESTENABLE,FALSE);Device_->SetRenderState(D3DRS_SRGBWRITEENABLE,FALSE);
    Device_->SetRenderState(D3DRS_CLIPPLANEENABLE,0);Device_->SetRenderState(D3DRS_STENCILENABLE,FALSE);
    Device_->SetRenderState(D3DRS_FILLMODE,D3DFILL_SOLID);
    Device_->SetRenderState(D3DRS_COLORWRITEENABLE,15);Device_->SetTexture(0,E->QualitySceneCopy);
    Device_->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);Device_->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
    Device_->SetSamplerState(0,D3DSAMP_MIPFILTER,D3DTEXF_NONE);Device_->SetSamplerState(0,D3DSAMP_SRGBTEXTURE,FALSE);
    Device_->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Device_->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    Hr=Device_->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Quad,sizeof(Vertex));
    HRESULT Restore=Saved->Apply();Saved->Release();
    return (GENRESULT)(FAILED(Hr) ? Hr : Restore);
}
