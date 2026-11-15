#pragma once
#include <windows.h>
#include <d3d9.h>
#include <string>

namespace Rp9D3DLoader
{
    inline std::wstring ExecutableDirectory()
    {
        wchar_t path[32768]={};
        DWORD size=GetModuleFileNameW(nullptr,path,32768);
        if (!size || size>=32768) return {};
        std::wstring result(path,size);
        auto slash=result.find_last_of(L"\\/");
        return slash==std::wstring::npos ? std::wstring{} : result.substr(0,slash+1);
    }

    inline bool OptionalRuntimeEnabled(std::wstring const& directory)
    {
#ifdef FREELANCER_DLSS5
        // The client owns saved preferences. Older/non-DLSS clients fail closed.
        using Enabled=bool (__cdecl*)();
        auto enabled=reinterpret_cast<Enabled>(GetProcAddress(GetModuleHandleW(nullptr),"FlBaseNeuralRuntimeEnabled"));
        if (!enabled || !enabled() || directory.empty()) return false;
        for (auto file : {L"D3D9.dll",L"dxgi.dll",L"fl_base_neural.addon32",
                         L"neural\\host64\\fl_base_neural_host.exe",
                         L"neural\\host64\\dxgi.dll",L"neural\\host64\\renodx-dlss5.addon64",
                         L"neural\\host64\\nvngx_dlss.dll",L"neural\\host64\\nvngx_dlssnr.dll"}) {
            DWORD attributes=GetFileAttributesW((directory+file).c_str());
            if (attributes==INVALID_FILE_ATTRIBUTES || (attributes&FILE_ATTRIBUTE_DIRECTORY)) return false;
        }
        return true;
#else
        (void)directory;
        return false;
#endif
    }

    inline HMODULE Load()
    {
        auto directory=ExecutableDirectory();
        if (OptionalRuntimeEnabled(directory))
            return LoadLibraryExW((directory+L"D3D9.dll").c_str(),nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
        // Absolute system path: never search beside the executable or in CWD.
        wchar_t system[32768]={};
        UINT size=GetSystemDirectoryW(system,32768);
        if (!size || size>=32768) return nullptr;
        return LoadLibraryExW((std::wstring(system)+L"\\d3d9.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
    }

    inline IDirect3D9* Create(UINT version)
    {
        // Keep the module alive for all devices/resources, including renderer restarts.
        // Changing the optional runtime requires restarting the game process.
        static HMODULE module=Load();
        using Factory=IDirect3D9* (WINAPI*)(UINT);
        auto create=module?reinterpret_cast<Factory>(GetProcAddress(module,"Direct3DCreate9")):nullptr;
        return create?create(version):nullptr;
    }
}
