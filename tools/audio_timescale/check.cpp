// Deterministic test of the actual client extension with a fake clock/backend.
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include <map>
#include "audio_timescale.h"

unsigned Now = 1000;
unsigned GetTickCount() { return Now; }
float Scale = 1;
bool SP = true;
float GetClientTimeScale() { return Scale; }
bool SinglePlayer() { return SP; }
using HMODULE = void*;
HMODULE GetModuleHandleA(char const*) { return nullptr; }
void* GetProcAddress(HMODULE, char const*) { return nullptr; }
struct ISoundSource
{
    int Field08 = 0;
    unsigned IsPaused() { return Field08 != 0; }
};
struct FSoundSource : ISoundSource
{
    unsigned Flags = 0x1c;
    int Type = 2, StartTick = 1000;
};
struct FStreamedSource : FSoundSource { void* StreamHandle = nullptr; };
bool IsStreamHandle(void* Handle) { return Handle && Handle != reinterpret_cast<void*>(-1); }
struct Node { Node* Next; FSoundSource* Value; };
Node Head{&Head, nullptr};
struct { Node* Head; } G_PlayingSources{&Head};
#define FREELANCER_DBG_OPTIONS
#include "../../src/freelancer/Client/audio_timescale.inl"

PortAudioTimeScaleQuery Installed = nullptr;
unsigned Installs = 0;
void __cdecl Install(PortAudioTimeScaleQuery Query) { Installed = Query; ++Installs; }
std::map<void*, float> StreamRates;
unsigned StreamCalls = 0;
int __cdecl SetStreamRate(void* Handle, float Rate)
{
    StreamRates[Handle] = Rate;
    ++StreamCalls;
    return 1;
}
double Elapsed(FSoundSource& Source)
{
    double Value = -1;
    assert(AudioTimeScaleElapsed(&Source, Value));
    return Value;
}
void Near(double Actual, double Expected) { assert(std::abs(Actual - Expected) < .001); }

int main()
{
    FSoundSource Voice, Sfx, Ambient, Ui, Music;
    FStreamedSource Stream;
    Sfx.Type = 0; Ambient.Type = 4; Ui.Type = 1; Music.Type = 3; Stream.Flags = 0;
    Node Nodes[6]{};
    FSoundSource* Sources[] = {&Voice, &Sfx, &Ambient, &Ui, &Music, &Stream};
    Head.Next = Nodes;
    for (int I = 0; I < 6; ++I)
        Nodes[I] = {I == 5 ? &Head : &Nodes[I+1], Sources[I]};

    // No opt-in: no registration, tracking or backend activity, even at a slow scale.
    Scale = .25f;
    TickAudioTimeScale();
    TrackAudioTimeScale(&Voice);
    assert(G_AudioSlowClocks.empty() && Installs == 0);
    assert(!ConnectAudioTimeScale()); // older DLL is a supported no-feature fallback
    G_InstallAudioTimeScale = &Install;
    G_AudioTimeScaleEnabled = true;
    TickAudioTimeScale();
    assert(G_AudioSlowClocks.size() == 3 && Installed);
    assert(!G_AudioSlowClocks.count(&Ui) && !G_AudioSlowClocks.count(&Music));
    assert(!G_AudioSlowClocks.count(&Stream));
    Now += 3000;
    TickAudioTimeScale();
    Near(Elapsed(Voice), 750); // a 1-second line is still alive after 3 real seconds
    assert(Voice.StartTick == 1000); // retail timestamps are never rewritten

    // Rate changes apply prospectively, not to the already-played portion.
    Scale = .5f;
    TickAudioTimeScale();
    Now += 500;
    Near(Elapsed(Voice), 1000);
    Now += 2;
    Near(Elapsed(Voice), 1001);
    Elapsed(Voice); Voice.Field08 = Now; // production Pause hook order
    Now += 10000;
    Near(Elapsed(Voice), 1001);
    Elapsed(Voice); Voice.Field08 = 0; // production Resume hook order
    Now += 200;
    Near(Elapsed(Voice), 1101);

    SeekAudioTimeScale(&Voice, 100);
    Now += 1000;
    Near(Elapsed(Voice), 600);
    G_AudioTimeScaleEnabled = false;
    TickAudioTimeScale();
    Now += 1000;
    Near(Elapsed(Voice), 1600); // disabling keeps the current position
    assert(G_AudioSlowClocks.at(&Voice).Rate == 1);

    G_AudioTimeScaleEnabled = true;
    Scale = .1f;
    TickAudioTimeScale();
    Installed(&Voice, nullptr); // failed buffer upgrade: per-source normal-rate fallback
    TickAudioTimeScale();
    assert(G_AudioSlowClocks.at(&Voice).Rate == 1);
    assert(G_AudioSlowClocks.at(&Sfx).Rate == .1f);
    SP = false;
    TickAudioTimeScale();
    assert(G_AudioSlowClocks.at(&Sfx).Rate == 1);
    SP = true; Scale = 2;
    TickAudioTimeScale();
    assert(G_AudioSlowClocks.at(&Sfx).Rate == 1); // slowdown only
    G_AudioTimeScaleEnabled = false;
    TickAudioTimeScale();
    for (auto* Source : Sources) ForgetAudioTimeScale(Source);
    assert(G_AudioSlowClocks.empty() && !Installed);
    auto Before = Installs;
    TickAudioTimeScale();
    assert(Installs == Before);

    // Last source stops while slow, then the user disables with nothing playing.
    G_AudioTimeScaleEnabled = true; Scale = .25f;
    TickAudioTimeScale();
    for (auto* Source : Sources) ForgetAudioTimeScale(Source);
    assert(G_AudioSlowClocks.empty() && Installed);
    G_AudioTimeScaleEnabled = false;
    TickAudioTimeScale();
    assert(!Installed && G_AudioSlowRate == 1.f);

    // Streamed world effects now opt in too; ordinary music/UI stay excluded.
    G_SetStreamTimeScale = &SetStreamRate;
    Stream.StreamHandle = reinterpret_cast<void*>(1);
    Stream.Type = 0;
    G_AudioTimeScaleEnabled = true;
    TickAudioTimeScale();
    assert(StreamRates.at(Stream.StreamHandle) == .25f);
    assert(G_AudioSlowStreams.size() == 1);
    unsigned Calls = StreamCalls;
    TickAudioTimeScale();
    assert(StreamCalls == Calls); // unchanged rate does not touch the backend again
    Stream.Field08 = 1; Scale = .5f;
    TickAudioTimeScale();
    assert(StreamRates.at(Stream.StreamHandle) == .5f); // paused stream retains its state
    Stream.Field08 = 0; Stream.Type = 3;
    TickAudioTimeScale();
    assert(StreamRates.at(Stream.StreamHandle) == 1 && G_AudioSlowStreams.empty());
    Stream.Type = 1; TickAudioTimeScale();
    assert(G_AudioSlowStreams.empty());
    Stream.Type = 4; TickAudioTimeScale();
    assert(StreamRates.at(Stream.StreamHandle) == .5f);
    Stream.StreamHandle = reinterpret_cast<void*>(2); // replacement of a stream on the same source
    ApplyStreamAudioTimeScale(&Stream);
    assert(StreamRates.at(Stream.StreamHandle) == .5f);
    G_AudioTimeScaleEnabled = false; TickAudioTimeScale();
    assert(StreamRates.at(Stream.StreamHandle) == 1 && G_AudioSlowStreams.empty());
    G_AudioTimeScaleEnabled = true; TickAudioTimeScale();
    ForgetAudioTimeScale(&Stream);
    assert(G_AudioSlowStreams.empty());

    // Fractional accumulation, GetTickCount wrap and invalid scales.
    AudioTimeScale::Clock C;
    C.Seek(0xfffffff0u, 0); C.Rate = .25f;
    C.Advance(0x10, false); Near(C.ElapsedMs, 8);
    C.Seek(0, 0); C.Rate = .01f;
    for (unsigned I = 1; I <= 1000; ++I) C.Advance(I, false);
    Near(C.ElapsedMs, 10);
    assert(AudioTimeScale::SlowRate(std::numeric_limits<float>::quiet_NaN()) == 1);
    assert(AudioTimeScale::SlowRate(0) == 1 && AudioTimeScale::SlowRate(-1) == 1);
    puts("PASS: opt-in isolation, categories, clocks, transitions, pause/seek, disable, unsupported backend, MP, cleanup, wrap, streamed effects");
}
