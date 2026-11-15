#pragma once
#include <cstdio>
#include <string>
namespace Archetype { struct ISound; }
namespace NativeSubtitles
{
    bool CutsceneEnabled();
    void SetCutsceneEnabled(bool enabled);
    void WritePreferences(FILE* file);
    bool AreaEnabled(std::wstring const& area);
    void Start(void* source, Archetype::ISound* arch);
    void Stop(void* source);
    // WAV time comes from the SoundManager clock. Streams use the client clock
    // because the retail IStreamer2 interface exposes no playback-position query.
    void Sync(void* source, double seconds, bool started, bool paused, float dt);
    void Draw();
    void Shutdown();
}
