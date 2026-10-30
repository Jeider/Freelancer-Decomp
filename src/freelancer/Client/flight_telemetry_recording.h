#pragma once

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <deque>
#include <mutex>
#include <string>
#include <thread>

// Independent of the game ABI; exercised by tools/flight_telemetry/check.py.
namespace FlightTelemetry {
struct SampleClock {
    double simulation = 0, remainder = 0;
    unsigned long long frame = 0;
    unsigned missed = 0;
    bool Advance(float dt, bool paused) noexcept;
};
std::string Quote(char const* text);
std::string Number(double value); // Non-finite/unavailable values become JSON null.
struct Json {
    std::string fields;
    Json& Raw(char const* key, std::string const& value);
    Json& Num(char const* key, double value);
    Json& Bool(char const* key, bool value);
    Json& Text(char const* key, char const* value);
    std::string Str() const;
};

enum class Error { None, InvalidPath, Open, Write, QueueFull, Allocation, Thread };
char const* ErrorName(Error error);

// Start/Record/Stop have one producer (the client thread). The worker only owns
// disk I/O and never touches game objects. Stop drains and joins the worker.
class Recording {
public:
    ~Recording();
    bool Start(wchar_t const* path, std::string const& metadata,
               size_t queueLimitBytes = 4 * 1024 * 1024) noexcept;
    bool Active() const noexcept { return accepting.load(); }
    Error LastError() const noexcept { return error.load(); }
    bool Record(char const* type, double simulationSeconds, unsigned long long frame,
                std::string const& payload) noexcept;
    void Fail(Error why) noexcept;
    bool Stop(char const* reason = "requested") noexcept;
private:
    void Run() noexcept;
    bool Write(std::string const& line) noexcept;
    std::atomic<bool> accepting{false};
    std::atomic<Error> error{Error::None};
    std::thread worker;
    std::mutex mutex;
    std::condition_variable ready;
    std::deque<std::string> queue;
    size_t queuedBytes = 0, limit = 0;
    bool stopping = false;
    char stopReason[96] = {};
    FILE* file = nullptr;
    unsigned long long sequence = 0;
    std::chrono::steady_clock::time_point started;
};
}
