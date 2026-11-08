#pragma once
#include <stdint.h>

// Private, versioned in-process x86 ABI. No runtime/NGX dependency in the game.
// The adapter owns all helper processes, history and GPU resources until Stop.
namespace BaseNeuralBridge
{
    static const uint32_t Version = 1;
    enum Result : int32_t { Unavailable = 0, Applied = 1, Warming = 2, Failed = -1 };
    enum Mode : uint32_t { Passthrough = 1, Neural = 2 };
    struct Frame
    {
        uint32_t size, version;
        uint64_t frame_id;
        uint32_t base, room, width, height;
        uint32_t mode, reset, timeout_ms;
        float strength;
    };
    struct Api
    {
        uint32_t size, version;
        int32_t (__cdecl *process)(Frame const*);
        void (__cdecl *stop)();
    };
    typedef Api const* (__cdecl *GetApi)(uint32_t version);
    static_assert(sizeof(Frame) == 48, "bridge frame ABI");
}
