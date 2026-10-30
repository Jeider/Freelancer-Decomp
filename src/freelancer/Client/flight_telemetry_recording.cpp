#include "flight_telemetry_recording.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <fcntl.h>
#include <iomanip>
#include <io.h>
#include <locale>
#include <share.h>
#include <sstream>
#include <sys/stat.h>

namespace FlightTelemetry {
bool SampleClock::Advance(float dt, bool paused) noexcept {
    ++frame; missed = 0;
    if (paused || !std::isfinite(dt) || dt <= 0) return false;
    simulation += dt; remainder += dt;
    constexpr double step = 1.0 / 30.0;
    if (remainder < step) return false;
    double intervals = std::floor(remainder / step);
    missed = static_cast<unsigned>((std::min)(intervals - 1, 4294967295.0));
    remainder = std::fmod(remainder, step);
    return true; // At most one real observation per frame, even after a stall.
}
std::string Quote(char const* text) {
    std::string out = "\"";
    for (auto p = reinterpret_cast<unsigned char const*>(text ? text : ""); *p; ++p) {
        if (*p == '"' || *p == '\\') { out += '\\'; out += static_cast<char>(*p); }
        else if (*p < 32) {
            char escaped[7]; sprintf_s(escaped, "\\u%04x", *p); out += escaped;
        } else out += static_cast<char>(*p);
    }
    return out + '"';
}
std::string Number(double value) {
    if (!std::isfinite(value)) return "null";
    std::ostringstream stream;
    stream.imbue(std::locale::classic());
    stream << std::setprecision(17) << value;
    return stream.str();
}
Json& Json::Raw(char const* key, std::string const& value) {
    if (!fields.empty()) fields += ',';
    fields += Quote(key) + ':' + value; return *this;
}
Json& Json::Num(char const* key, double value) { return Raw(key, Number(value)); }
Json& Json::Bool(char const* key, bool value) { return Raw(key, value ? "true" : "false"); }
Json& Json::Text(char const* key, char const* value) { return Raw(key, Quote(value)); }
std::string Json::Str() const { return '{' + fields + '}'; }
char const* ErrorName(Error e) {
    switch (e) {
    case Error::None: return "none";
    case Error::InvalidPath: return "invalid_path";
    case Error::Open: return "open_failed";
    case Error::Write: return "write_failed";
    case Error::QueueFull: return "queue_full";
    case Error::Allocation: return "allocation_failed";
    case Error::Thread: return "thread_failed";
    }
    return "unknown";
}
Recording::~Recording() { Stop("shutdown"); }
bool Recording::Write(std::string const& line) noexcept {
    if (fwrite(line.data(), 1, line.size(), file) == line.size()) return true;
    Fail(Error::Write); return false;
}
void Recording::Fail(Error why) noexcept {
    Error expected = Error::None;
    error.compare_exchange_strong(expected, why);
    accepting = false;
    ready.notify_one();
}
bool Recording::Start(wchar_t const* path, std::string const& metadata, size_t queueLimitBytes) noexcept {
    if (file || worker.joinable()) return false; // Never replace a running recording.
    error = Error::None;
    if (!path || !*path || !queueLimitBytes) { Fail(Error::InvalidPath); return false; }
    int descriptor = -1;
    if (_wsopen_s(&descriptor, path, _O_CREAT | _O_EXCL | _O_WRONLY | _O_BINARY,
                  _SH_DENYWR, _S_IREAD | _S_IWRITE) != 0) { Fail(Error::Open); return false; }
    file = _fdopen(descriptor, "wb");
    if (!file) { _close(descriptor); Fail(Error::Open); return false; }
    try {
        queue.clear(); queuedBytes = 0; limit = queueLimitBytes;
        stopping = false; sequence = 0; strcpy_s(stopReason, "requested");
        started = std::chrono::steady_clock::now();
        auto header = Json().Text("type", "header").Num("schema_version", 1)
            .Text("format", "freelancer_flight_telemetry").Num("sample_hz", 30)
            .Raw("metadata", metadata).Str() + '\n';
        if (!Write(header) || fflush(file) != 0) {
            Fail(Error::Write); fclose(file); file = nullptr; return false;
        }
        accepting = true;
        worker = std::thread(&Recording::Run, this);
        return true;
    } catch (...) {
        Fail(Error::Thread); fclose(file); file = nullptr; return false;
    }
}
bool Recording::Record(char const* type, double simulationSeconds, unsigned long long frame,
                       std::string const& payload) noexcept {
    if (!Active()) return false;
    try {
        auto us = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now() - started).count();
        auto line = Json().Text("type", type).Num("sequence", static_cast<double>(sequence))
            .Num("wall_us", static_cast<double>(us)).Num("simulation_s", simulationSeconds)
            .Num("frame", static_cast<double>(frame)).Raw("data", payload).Str() + '\n';
        {
            std::lock_guard<std::mutex> guard(mutex);
            if (!Active()) return false;
            if (line.size() > limit - queuedBytes) { Fail(Error::QueueFull); return false; }
            queue.push_back(std::move(line));
            queuedBytes += queue.back().size(); ++sequence;
        }
        ready.notify_one(); return true;
    } catch (...) { Fail(Error::Allocation); return false; }
}
void Recording::Run() noexcept {
    unsigned long long written = 0;
    try {
        auto flushed = std::chrono::steady_clock::now();
        for (;;) {
            std::string line;
            {
                std::unique_lock<std::mutex> guard(mutex);
                ready.wait_for(guard, std::chrono::seconds(1), [this] {
                    return stopping || error != Error::None || !queue.empty();
                });
                if (!queue.empty()) {
                    line = std::move(queue.front()); queue.pop_front(); queuedBytes -= line.size();
                } else if (stopping || error != Error::None) break;
            }
            if (!line.empty()) { if (!Write(line)) break; ++written; }
            if (std::chrono::steady_clock::now() - flushed >= std::chrono::seconds(1)) {
                if (fflush(file) != 0) { Fail(Error::Write); break; }
                flushed = std::chrono::steady_clock::now();
            }
        }
        // A footer is authoritative only when complete=true AND the file ends here.
        // A disk failure/crash may leave a partial last line or no footer at all.
        std::string reason;
        { std::lock_guard<std::mutex> guard(mutex); reason = stopReason; }
        Write(Json().Text("type", "footer").Bool("complete", error == Error::None)
            .Text("reason", error == Error::None ? reason.c_str() : ErrorName(error.load()))
            .Num("records", static_cast<double>(written)).Str() + '\n');
        if (fflush(file) != 0) Fail(Error::Write);
    } catch (...) { Fail(Error::Allocation); }
    accepting = false;
}
bool Recording::Stop(char const* reason) noexcept {
    accepting = false;
    if (worker.joinable()) {
        {
            std::lock_guard<std::mutex> guard(mutex);
            strncpy_s(stopReason, reason ? reason : "requested", _TRUNCATE);
            stopping = true;
        }
        ready.notify_one(); worker.join();
    }
    if (file) { if (fclose(file) != 0) Fail(Error::Write); file = nullptr; }
    queue.clear(); queuedBytes = 0;
    return error == Error::None;
}
}
