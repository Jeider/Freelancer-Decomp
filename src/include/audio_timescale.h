// Optional port extension. No changes to the retail sound interfaces or object layouts.
#pragma once

#include <stdint.h>

struct ISoundSource;

struct PortAudioTimeScaleState
{
    double ElapsedMs; // source time before the source's original pitch multiplier
    float Rate;
};

// Mixer-thread only. A null State reports an unsupported buffer; the client falls
// back to rate 1 for that source while retaining its accumulated playback time.
typedef int (__cdecl* PortAudioTimeScaleQuery)(ISoundSource*, PortAudioTimeScaleState*);
typedef void (__cdecl* PortAudioTimeScaleInstall)(PortAudioTimeScaleQuery);
// Optional SoundStreamer extension; all changes happen under its worker lock.
typedef int (__cdecl* PortStreamTimeScaleSet)(void* Handle, float Rate);

namespace AudioTimeScale
{
    inline float SlowRate(float Scale)
    {
        if (!(Scale > 0.f) || Scale >= 1.f)
            return 1.f;
        return Scale < .01f ? .01f : Scale;
    }

    // Kept outside the ABI objects, and instantiated only for affected sources.
    struct Clock
    {
        double ElapsedMs = 0;
        uint32_t LastTick = 0;
        float Rate = 1.f;
        bool Failed = false;

        void Advance(uint32_t Now, bool Paused)
        {
            if (!Paused)
                ElapsedMs += double(uint32_t(Now - LastTick)) * Rate;
            LastTick = Now;
        }

        void SetRate(uint32_t Now, bool Paused, float Next)
        {
            Advance(Now, Paused);
            Rate = Failed ? 1.f : SlowRate(Next);
        }

        void Seek(uint32_t Now, double Offset)
        {
            LastTick = Now;
            ElapsedMs = Offset;
        }
    };
}
