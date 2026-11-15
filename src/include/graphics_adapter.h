#pragma once
#include <windows.h>
#include <d3d9.h>
#include <dxcore_interface.h>
#include <cstdio>

namespace GraphicsAdapter
{
    enum Kind { Unknown, Integrated, Discrete };
    struct Info { Kind Type=Unknown; char Key[96]={}; char Name[512]={}; };

    // RP9 currently renders on adapter zero (RP9.cpp, AdapterIndex_ = 0).
    // Query that D3D9 adapter's LUID; never select an unrelated GPU from an inventory.
    inline Info Detect(unsigned ordinal=0)
    {
        Info result;
        HMODULE d3d=LoadLibraryExA("d3d9.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
        HMODULE dx=LoadLibraryExA("dxcore.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
        using Create9=HRESULT(WINAPI*)(UINT,IDirect3D9Ex**);
        using CreateCore=HRESULT(WINAPI*)(REFIID,void**);
        auto create9=d3d?reinterpret_cast<Create9>(GetProcAddress(d3d,"Direct3DCreate9Ex")):nullptr;
        auto createCore=dx?reinterpret_cast<CreateCore>(GetProcAddress(dx,"DXCoreCreateAdapterFactory")):nullptr;
        IDirect3D9Ex* api=nullptr;
        IDXCoreAdapterFactory* factory=nullptr;
        IDXCoreAdapter* adapter=nullptr;
        LUID luid={};
        D3DADAPTER_IDENTIFIER9 id={};
        if (create9 && createCore && SUCCEEDED(create9(D3D_SDK_VERSION,&api)) &&
            SUCCEEDED(api->GetAdapterIdentifier(ordinal,0,&id)) &&
            SUCCEEDED(api->GetAdapterLUID(ordinal,&luid)) &&
            SUCCEEDED(createCore(__uuidof(IDXCoreAdapterFactory),reinterpret_cast<void**>(&factory))) &&
            SUCCEEDED(factory->GetAdapterByLuid(luid,__uuidof(IDXCoreAdapter),reinterpret_cast<void**>(&adapter))))
        {
            bool hardware=false, integrated=false;
            if (SUCCEEDED(adapter->GetProperty(DXCoreAdapterProperty::IsHardware,sizeof(hardware),&hardware)) && hardware &&
                SUCCEEDED(adapter->GetProperty(DXCoreAdapterProperty::IsIntegrated,sizeof(integrated),&integrated)))
            {
                result.Type=integrated?Integrated:Discrete;
                // Unlike LUID, these identifiers remain stable across reboots.
                sprintf_s(result.Key,"%04x_%04x_%08x_%02x_%u",id.VendorId,id.DeviceId,id.SubSysId,id.Revision,unsigned(result.Type));
                strncpy_s(result.Name,id.Description,_TRUNCATE);
            }
        }
        if (adapter) adapter->Release();
        if (factory) factory->Release();
        if (api) api->Release();
        if (dx) FreeLibrary(dx);
        if (d3d) FreeLibrary(d3d);
        return result;
    }
}
