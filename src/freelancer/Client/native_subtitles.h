#pragma once
namespace Archetype { struct ISound; }
namespace NativeSubtitles
{
    void Start(void* source, Archetype::ISound* arch);
    void Stop(void* source);
    // WAV time comes from the SoundManager clock. Streams use the client clock
    // because the retail IStreamer2 interface exposes no playback-position query.
    void Sync(void* source, double seconds, bool started, bool paused, float dt);
    void Draw();
    void Shutdown();
}
