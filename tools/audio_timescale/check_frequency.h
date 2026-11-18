// Minimal sources around the real SoundManager pitch/frequency block.
struct ISoundSource
{
    float Pitch = 0;
    bool HasPitch = true;
    int GetArchId() { return 1; }
    int GetPitch(float* Out) { *Out = Pitch; return HasPitch ? 0 : -7; }
};
struct FSoundArchetype
{
    unsigned short nSamplesPerSec = 48000;
    float Gain = 0;
    void Release() {}
} FrequencyArch;
FSoundArchetype* LookupArchetype(int) { return &FrequencyArch; }
struct FFrequencyNode
{
    ISoundSource* PlayKey;
    IDirectSoundBuffer* Buffer;
    unsigned StatusFlags = 0x20;
    unsigned DsCapsFlags = DSBCAPS_CTRLFREQUENCY;
};
float TestSlowRate = .25f;
bool TestSlowEnabled = true;
bool QueryTimeScale(ISoundSource*, PortAudioTimeScaleState& State)
{
    State.ElapsedMs = 0;
    State.Rate = TestSlowRate;
    return TestSlowEnabled;
}
void G_AudioTimeScaleQuery(ISoundSource*, void*) { assert(false); }

struct FStreamingSound
{
    IDirectSoundBuffer* Buffer = nullptr;
    unsigned PcmRate = 48000;
    long Volume = -1300;
    long Pan = 1000;
};
