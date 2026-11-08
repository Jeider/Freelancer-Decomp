#pragma once
#define NOMINMAX
#include <windows.h>
#include <d3d11_4.h>
#include <wrl/client.h>
#include <atomic>
#include <thread>
#include <string>
#include <stdint.h>

namespace BaseFeed
{
    using Microsoft::WRL::ComPtr;
    // Wire layouts derived from DLSS5 Feeder v0.7.0, protocol 2 (MIT).
    // https://github.com/jlrouzies-fr/DLSS5-Feeder/blob/v0.7.0/src/feed_ipc.h
    // Private magic/version/pipe: adds FrameAck and full-frame identity transport.
    // Stock Feeder cannot silently attach or report a failed evaluation as success.
    constexpr uint32_t Magic = 0x4e424c46, Version = 0x464c0001;
    enum Slot { Color, Output, Depth, Motion, Count };
#pragma pack(push, 1)
    struct Hello { uint32_t magic, version, pid, kind; };
    struct HelloAck { uint32_t magic, version; };
    struct Build
    {
        uint32_t width, height, color_format, output_format;
        int32_t hdr, inverted, flags, transport;
        float mv_x, mv_y;
        uint64_t textures[Count];
    };
    struct BuildAck
    {
        int32_t ok; uint32_t ngx;
        uint64_t fence_in, fence_out, textures[Count], sizes[Count];
    };
    struct Frame { uint64_t number; uint32_t reset; };
    struct FrameAck { uint64_t number; int32_t ok; };
#pragma pack(pop)
    static_assert(sizeof(Build) == 72 && sizeof(BuildAck) == 88 && sizeof(Frame) == 12, "Feed v2 wire ABI");

    class Client
    {
    public:
        ~Client() { Stop(); }
        bool Start(ID3D11Device* device, unsigned width, unsigned height, unsigned mode, wchar_t const* directory);
        int Poll(); // 0 warming, 1 ready, -1 fault
        bool Evaluate(ID3D11DeviceContext4* context, bool reset, unsigned timeout_ms);
        bool Submit(ID3D11DeviceContext4* context, bool reset, unsigned timeout_ms);
        int Complete(ID3D11DeviceContext4* context, unsigned timeout_ms); // 0 pending, 1 ready, -1 fault
        void Stop();
        DWORD HostPid() const { return state.load(std::memory_order_acquire)==1 && process ? GetProcessId(process) : 0; }
        ComPtr<ID3D11Texture2D> textures[Count];
    private:
        void Connect(std::wstring directory, Build request);
        bool Io(bool write, void* bytes, DWORD length, DWORD timeout);
        bool WaitFence(ID3D11Fence* fence, uint64_t value, unsigned timeout);
        std::atomic<int> state{0};
        std::thread worker;
        HANDLE cancel = nullptr, job = nullptr, process = nullptr, pipe = INVALID_HANDLE_VALUE;
        HANDLE shared[Count] = {};
        ComPtr<ID3D11Device5> device5;
        ComPtr<ID3D11Fence> input, output;
        BuildAck ack = {};
        uint64_t frame = 0;
        bool pending = false;
        bool acknowledged = false;
    };
}
