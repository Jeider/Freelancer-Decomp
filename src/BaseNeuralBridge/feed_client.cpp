#include "feed_client.h"
#include <dxgi1_2.h>
#include <vector>

bool BaseFeed::Client::Io(bool write, void* bytes, DWORD length, DWORD timeout)
{
    if (pipe == INVALID_HANDLE_VALUE || WaitForSingleObject(cancel, 0) != WAIT_TIMEOUT) return false;
    OVERLAPPED operation = {};
    operation.hEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    if (!operation.hEvent) return false;
    DWORD transferred = 0;
    BOOL done = write ? WriteFile(pipe, bytes, length, &transferred, &operation)
                      : ReadFile(pipe, bytes, length, &transferred, &operation);
    if (!done && GetLastError() == ERROR_IO_PENDING)
    {
        HANDLE waits[] = { cancel, operation.hEvent };
        if (WaitForMultipleObjects(2, waits, FALSE, timeout) == WAIT_OBJECT_0 + 1)
            done = GetOverlappedResult(pipe, &operation, &transferred, FALSE);
        else
        {
            CancelIoEx(pipe, &operation);
            // Retire the cancelled OVERLAPPED before its stack/event can disappear.
            GetOverlappedResult(pipe, &operation, &transferred, TRUE);
        }
    }
    CloseHandle(operation.hEvent);
    return done && transferred == length;
}

bool BaseFeed::Client::Start(ID3D11Device* device, unsigned width, unsigned height, unsigned mode, wchar_t const* directory)
{
    Stop();
    if (!device || width < 1 || height < 1 || width > 8192 || height > 8192 || (mode != 1 && mode != 2)) return false;
    if (FAILED(device->QueryInterface(IID_PPV_ARGS(&device5)))) return false;
    cancel = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    job = CreateJobObjectW(nullptr, nullptr);
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits = {};
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if (!cancel || !job || !SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof(limits)))
    { Stop(); return false; }
    Build request = {};
    request.width = width; request.height = height;
    request.color_format = request.output_format = DXGI_FORMAT_R8G8B8A8_UNORM;
    request.flags = -1; request.transport = mode == 1; request.mv_x = request.mv_y = 1;
    for (unsigned i = 0; i < Count; ++i)
    {
        D3D11_TEXTURE2D_DESC d = {};
        d.Width = width; d.Height = height; d.MipLevels = d.ArraySize = d.SampleDesc.Count = 1;
        d.Format = i == Depth ? DXGI_FORMAT_R32_FLOAT : i == Motion ? DXGI_FORMAT_R16G16_FLOAT : DXGI_FORMAT_R8G8B8A8_UNORM;
        d.Usage = D3D11_USAGE_DEFAULT;
        d.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_UNORDERED_ACCESS;
        d.MiscFlags = D3D11_RESOURCE_MISC_SHARED_NTHANDLE | D3D11_RESOURCE_MISC_SHARED;
        ComPtr<IDXGIResource1> resource;
        if (FAILED(device->CreateTexture2D(&d, nullptr, &textures[i])) || FAILED(textures[i].As(&resource)) ||
            FAILED(resource->CreateSharedHandle(nullptr, DXGI_SHARED_RESOURCE_READ | DXGI_SHARED_RESOURCE_WRITE, nullptr, &shared[i])))
        { Stop(); return false; }
        request.textures[i] = reinterpret_cast<uintptr_t>(shared[i]);
    }
    state = 0;
    try { worker = std::thread(&Client::Connect, this, std::wstring(directory), request); }
    catch (...) { Stop(); return false; }
    return true;
}

void BaseFeed::Client::Connect(std::wstring directory, Build request)
{
    std::wstring exe = directory + L"\\fl_base_neural_host.exe";
    std::wstring command = L"\"" + exe + L"\" " + std::to_wstring(GetCurrentProcessId()) + L" --hide";
    std::vector<wchar_t> args(command.begin(), command.end()); args.push_back(0);
    STARTUPINFOW start = {}; start.cb = sizeof(start); start.dwFlags = STARTF_USESHOWWINDOW; start.wShowWindow = SW_HIDE;
    PROCESS_INFORMATION info = {};
    if (WaitForSingleObject(cancel, 0) != WAIT_TIMEOUT ||
        !CreateProcessW(exe.c_str(), args.data(), nullptr, nullptr, FALSE, CREATE_NO_WINDOW | CREATE_SUSPENDED,
                        nullptr, directory.c_str(), &start, &info)) { state = -1; return; }
    process = info.hProcess;
    if (!AssignProcessToJobObject(job, process))
    {
        TerminateProcess(process, 1); CloseHandle(info.hThread); state = -1; return;
    }
    ResumeThread(info.hThread); CloseHandle(info.hThread);
    wchar_t name[128]; swprintf_s(name, L"\\\\.\\pipe\\fl-base-neural.%lu", GetCurrentProcessId());
    ULONGLONG const deadline = GetTickCount64() + 60000;
    while (GetTickCount64() < deadline && WaitForSingleObject(cancel, 0) == WAIT_TIMEOUT &&
           WaitForSingleObject(process, 0) == WAIT_TIMEOUT)
    {
        pipe = CreateFileW(name, GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, nullptr);
        if (pipe != INVALID_HANDLE_VALUE) break;
        if (WaitForSingleObject(cancel, 50) != WAIT_TIMEOUT) break;
    }
    Hello hello = { Magic, Version, GetCurrentProcessId(), 0 };
    ULONG server = 0;
    if (!GetNamedPipeServerProcessId(pipe, &server) || server != info.dwProcessId) { state = -1; return; }
    HelloAck response = {};
    BYTE tag = 'B';
    bool ok = Io(true, &hello, sizeof(hello), 10000) && Io(false, &response, sizeof(response), 10000) &&
              response.magic == Magic && response.version == Version &&
              Io(true, &tag, 1, 10000) && Io(true, &request, sizeof(request), 10000) &&
              Io(false, &ack, sizeof(ack), 60000) && ack.ok == 1;
    state.store(ok ? 1 : -1, std::memory_order_release);
}

int BaseFeed::Client::Poll()
{
    int result = state.load(std::memory_order_acquire);
    if (result == 0) return 0;
    if (worker.joinable()) worker.join();
    if (result < 0 || !process || WaitForSingleObject(process, 0) != WAIT_TIMEOUT) return -1;
    if (!input || !output)
    {
        HANDLE in = reinterpret_cast<HANDLE>(static_cast<uintptr_t>(ack.fence_in));
        HANDLE out = reinterpret_cast<HANDLE>(static_cast<uintptr_t>(ack.fence_out));
        HRESULT a = device5->OpenSharedFence(in, IID_PPV_ARGS(&input));
        HRESULT b = device5->OpenSharedFence(out, IID_PPV_ARGS(&output));
        if (in) CloseHandle(in);
        if (out) CloseHandle(out);
        ack.fence_in = ack.fence_out = 0;
        if (FAILED(a) || FAILED(b)) { state = -1; return -1; }
    }
    return 1;
}

bool BaseFeed::Client::WaitFence(ID3D11Fence* fence, uint64_t value, unsigned timeout)
{
    ULONGLONG const end = GetTickCount64() + timeout;
    do
    {
        uint64_t const completed = fence->GetCompletedValue();
        if (completed == UINT64_MAX) return false; // device removed
        if (completed >= value) return true;
        if (WaitForSingleObject(process, 0) != WAIT_TIMEOUT || WaitForSingleObject(cancel, 1) != WAIT_TIMEOUT) return false;
    } while (GetTickCount64() < end);
    return false;
}

bool BaseFeed::Client::Evaluate(ID3D11DeviceContext4* context, bool reset, unsigned timeout)
{
    ULONGLONG const end = GetTickCount64() + timeout;
    if (!Submit(context, reset, timeout)) return false;
    ULONGLONG const now = GetTickCount64();
    return Complete(context, now < end ? static_cast<unsigned>(end-now) : 0) == 1;
}

bool BaseFeed::Client::Submit(ID3D11DeviceContext4* context, bool reset, unsigned timeout)
{
    if (Poll() != 1 || pending) return false;
    uint64_t const n = ++frame;
    if (FAILED(context->Signal(input.Get(), n))) return false;
    context->Flush();
    BYTE tag = 'F'; Frame request = { n, reset ? 1u : 0u };
    // No GPU-side wait on a fence owned by another process: a dead host cannot
    // strand the game's graphics queue. Output is used only after CPU proof of completion.
    ULONGLONG const deadline = GetTickCount64() + timeout;
    auto remaining = [&]() -> DWORD {
        ULONGLONG const now = GetTickCount64();
        return now < deadline ? static_cast<DWORD>(deadline - now) : 0;
    };
    if (!Io(true, &tag, 1, remaining()) || !Io(true, &request, sizeof(request), remaining())) return false;
    pending = true;
    acknowledged = false;
    return true;
}

int BaseFeed::Client::Complete(ID3D11DeviceContext4* context, unsigned timeout)
{
    if (!pending || Poll() != 1) return -1;
    ULONGLONG const end = GetTickCount64() + timeout;
    while (!acknowledged)
    {
        DWORD bytes = 0;
        if (!PeekNamedPipe(pipe, nullptr, 0, nullptr, &bytes, nullptr)) return -1;
        if (bytes >= sizeof(FrameAck))
        {
            FrameAck result = {};
            if (!Io(false, &result, sizeof(result), 1) || result.number != frame || result.ok != 1) return -1;
            acknowledged = true;
        }
        else
        {
            if (GetTickCount64() >= end) return 0;
            if (WaitForSingleObject(cancel, 1) != WAIT_TIMEOUT) return -1;
        }
    }
    ULONGLONG const now = GetTickCount64();
    timeout = now < end ? static_cast<unsigned>(end - now) : 0;
    if (!WaitFence(output.Get(), frame, timeout))
    {
        if (output->GetCompletedValue() == UINT64_MAX || FAILED(device5->GetDeviceRemovedReason()) ||
            WaitForSingleObject(process, 0) != WAIT_TIMEOUT) return -1;
        return 0;
    }
    // The CPU check bounds the wait. The already-completed GPU wait is still
    // required for D3D12->D3D11 shared-resource visibility/cache invalidation.
    pending = false;
    return SUCCEEDED(context->Wait(output.Get(), frame)) ? 1 : -1;
}

void BaseFeed::Client::Stop()
{
    if (cancel) SetEvent(cancel);
    // All worker pipe operations observe cancel; joining avoids releasing handles
    // or this object while CreateProcess/pipe initialization still owns them.
    if (worker.joinable()) worker.join();
    if (pipe != INVALID_HANDLE_VALUE) { CloseHandle(pipe); pipe = INVALID_HANDLE_VALUE; }
    if (process)
    {
        if (WaitForSingleObject(process, 500) != WAIT_OBJECT_0)
        { TerminateJobObject(job, 1); WaitForSingleObject(process, 500); }
        CloseHandle(process); process = nullptr;
    }
    if (job) { CloseHandle(job); job = nullptr; }
    if (ack.fence_in) CloseHandle(reinterpret_cast<HANDLE>(static_cast<uintptr_t>(ack.fence_in)));
    if (ack.fence_out) CloseHandle(reinterpret_cast<HANDLE>(static_cast<uintptr_t>(ack.fence_out)));
    ack = {};
    input.Reset(); output.Reset(); device5.Reset();
    for (unsigned i = 0; i < Count; ++i)
    {
        textures[i].Reset();
        if (shared[i]) { CloseHandle(shared[i]); shared[i] = nullptr; }
    }
    if (cancel) { CloseHandle(cancel); cancel = nullptr; }
    frame = 0; state = 0; pending = false; acknowledged = false;
}
