#pragma once
#include <windows.h>
#include <atomic>

inline float Rp9UserGraphics(char const* key, float authored)
{
    using Read = float (__cdecl*)(char const*,float);
    // Do not cache a missing Common.dll: standalone renderer tools have no game
    // preferences, and the game may load Common after creating the component.
    static std::atomic<Read> cached{nullptr};
    Read read=cached.load(std::memory_order_relaxed);
    if (!read)
        if (HMODULE common=GetModuleHandleA("Common.dll")) {
            read=reinterpret_cast<Read>(GetProcAddress(common,"PortGraphicsRenderValue"));
            if (read) cached.store(read,std::memory_order_relaxed);
        }
    return read ? read(key,authored) : authored;
}
