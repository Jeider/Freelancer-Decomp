#include "flight_telemetry_recording.h"
#include <cassert>
#include <cmath>
#include <limits>
#include <locale>
#include <string>

struct CommaDecimal : std::numpunct<char> {
    char do_decimal_point() const override { return ','; }
};
int wmain(int argc, wchar_t** argv) {
    using namespace FlightTelemetry;
    assert(argc == 2);
    std::wstring root = argv[1];
    auto path = [&](wchar_t const* name) { return root + L"/" + name; };
    Recording record;
    assert(!record.Active());
    assert(!record.Record("idle", 0, 0, "{}"));
    assert(record.Stop());
    assert(!record.Start(nullptr, "{}"));
    assert(record.LastError() == Error::InvalidPath);
    assert(!record.Start(path(L"absent/record.jsonl").c_str(), "{}"));
    assert(record.LastError() == Error::Open);

    // Serialization must be independent of the UI/OS numeric locale.
    std::locale::global(std::locale(std::locale::classic(), new CommaDecimal));
    assert(Number(1.25) == "1.25");
    auto special = Json().Text("text", "quote\" slash\\ line\n tab\t control\x01")
        .Num("nan", std::numeric_limits<double>::quiet_NaN())
        .Num("infinity", std::numeric_limits<double>::infinity()).Num("decimal", 1.25).Str();
    assert(record.Start(path(L"flight.jsonl").c_str(), special));
    assert(!record.Start(path(L"must_not_exist.jsonl").c_str(), "{}"));
    // A press and release inside a single state interval must both survive.
    assert(record.Record("mapped_input", 0, 1, Json().Num("command", 119).Bool("down", true).Str()));
    assert(record.Record("mapped_input", 0, 1, Json().Num("command", 119).Bool("down", false).Str()));
    for (unsigned i = 0; i < 6000; ++i)
        assert(record.Record("snapshot", i/30.0, i+2, Json().Num("index", i).Str()));
    assert(record.Stop("test_complete"));
    assert(record.Stop());
    assert(!record.Record("after_stop", 0, 0, "{}"));
    assert(!record.Start(path(L"flight.jsonl").c_str(), "{}"));
    assert(record.LastError() == Error::Open); // Previously written file stays intact.

    // Bound overflow is deterministic: a single record cannot fit one byte.
    assert(record.Start(path(L"overflow.jsonl").c_str(), "{}", 1));
    assert(!record.Record("event", 0, 0, "{}"));
    assert(!record.Active());
    assert(record.LastError() == Error::QueueFull);
    assert(!record.Stop());
    assert(record.Start(path(L"restart.jsonl").c_str(), "{}"));
    assert(record.Record("fresh", 0, 0, "{}"));
    assert(record.Stop());
    {
        Recording shutdown;
        assert(shutdown.Start(path(L"shutdown.jsonl").c_str(), "{}"));
        assert(shutdown.Record("last", 0, 0, "{}"));
    }

    SampleClock clock;
    unsigned samples = 0;
    for (unsigned i = 0; i < 120; ++i) samples += clock.Advance(1.f/120, false) ? 1u : 0u;
    assert(samples == 30 && clock.frame == 120 && std::abs(clock.simulation-1) < 1.e-6);
    double time = clock.simulation;
    assert(!clock.Advance(5, true) && clock.simulation == time);
    assert(!clock.Advance(-1, false) && clock.simulation == time);
    assert(!clock.Advance(std::numeric_limits<float>::quiet_NaN(), false));
    assert(clock.Advance(1, false) && clock.missed == 29);
    assert(!clock.Advance(0, false)); // No fabricated catch-up states.
    puts("PASS: exclusive start, inactive path, restart, drain, overflow, shutdown, locale, sample clock");
}
