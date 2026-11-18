// Included by check.py after the real buffer upload/upgrade helpers.
// Creates stopped DirectSound buffers; never plays audio or launches the game.
int main()
{
    IDirectSound* Device = nullptr;
    assert(SUCCEEDED(DirectSoundCreate(nullptr, &Device, nullptr)));
    assert(SUCCEEDED(Device->SetCooperativeLevel(GetDesktopWindow(), DSSCL_NORMAL)));
    for (bool Spatial : {false, true})
    {
        WAVEFORMATEX Format = {};
        Format.wFormatTag = WAVE_FORMAT_PCM;
        Format.nChannels = 1;
        Format.nSamplesPerSec = 48000;
        Format.wBitsPerSample = 16;
        Format.nBlockAlign = 2;
        Format.nAvgBytesPerSec = 96000;
        std::vector<unsigned char> Pcm(96000);
        for (unsigned I = 0; I < Pcm.size(); ++I) Pcm[I] = (I * 31) & 255;
        DSBUFFERDESC Desc = {};
        Desc.dwSize = sizeof(Desc);
        Desc.dwFlags = DSBCAPS_CTRLVOLUME | DSBCAPS_LOCSOFTWARE |
                       (Spatial ? DSBCAPS_CTRL3D : DSBCAPS_CTRLPAN);
        Desc.dwBufferBytes = unsigned(Pcm.size());
        Desc.lpwfxFormat = &Format;
        IDirectSoundBuffer *Original = nullptr, *Copy = nullptr;
        assert(SUCCEEDED(Device->CreateSoundBuffer(&Desc, &Original, nullptr)));
        assert(UploadSoundBuffer(Original, Pcm.data(), unsigned(Pcm.size())) == 0);
        assert(CreateTimeScaleBuffer(Device, Original, &Copy));
        DSBCAPS Caps = {}; Caps.dwSize = sizeof(Caps);
        assert(SUCCEEDED(Original->GetCaps(&Caps)));
        assert((Caps.dwFlags & DSBCAPS_CTRLFREQUENCY) == 0);
        assert(SUCCEEDED(Copy->GetCaps(&Caps)));
        assert((Caps.dwFlags & DSBCAPS_CTRLFREQUENCY) != 0);
        assert(Caps.dwBufferBytes == Pcm.size());
        assert(bool(Caps.dwFlags & DSBCAPS_CTRL3D) == Spatial);
        for (auto* Buffer : {Original, Copy})
        {
            void* Data = nullptr; DWORD Bytes = 0;
            assert(SUCCEEDED(Buffer->Lock(0, 0, &Data, &Bytes, nullptr, nullptr, DSBLOCK_ENTIREBUFFER)));
            assert(Bytes == Pcm.size() && memcmp(Data, Pcm.data(), Bytes) == 0);
            assert(SUCCEEDED(Buffer->Unlock(Data, Bytes, nullptr, 0)));
        }
        for (DWORD Rate : {48000u, 12000u, 480u, 48000u})
        {
            assert(SUCCEEDED(Copy->SetFrequency(Rate)));
            DWORD Actual = 0;
            assert(SUCCEEDED(Copy->GetFrequency(&Actual)) && Actual == Rate);
        }
        DWORD Status = 0;
        assert(SUCCEEDED(Copy->GetStatus(&Status)) && !(Status & DSBSTATUS_PLAYING));

        // Real mixer frequency code: engine throttle pitch and time scale multiply.
        ISoundSource Engine;
        FFrequencyNode Node{&Engine, Copy};
        TestSlowEnabled = true;
        for (float Pitch : {-25.f, 0.f, 65.f})
        {
            Engine.Pitch = Pitch;
            for (float Scale : {.25f, .5f, 1.f})
            {
                TestSlowRate = Scale;
                ApplyFrequency(&Node);
                DWORD Actual = 0;
                assert(SUCCEEDED(Copy->GetFrequency(&Actual)));
                DWORD Expected = DWORD(48000 * std::pow(2., double(Pitch) * double(.01f)) * Scale);
                assert(Actual == Expected);
            }
        }
        // Fixed-pitch effects must slow even after legacy mixing cleared StatusFlags.
        Engine.HasPitch = false; Node.StatusFlags = 0; TestSlowRate = .25f;
        ApplyFrequency(&Node);
        DWORD Actual = 0;
        assert(SUCCEEDED(Copy->GetFrequency(&Actual)) && Actual == 12000);
        TestSlowRate = 1.f; ApplyFrequency(&Node);
        assert(SUCCEEDED(Copy->GetFrequency(&Actual)) && Actual == 48000);

        if (!Spatial)
        {
            FStreamingSound Stream;
            Original->AddRef(); Stream.Buffer = Original;
            assert(SetStreamTimeScale(Device, &Stream, 1.f) && Stream.Buffer == Original);
            assert(SUCCEEDED(Original->SetCurrentPosition(24000)));
            assert(SetStreamTimeScale(Device, &Stream, .25f));
            assert(Stream.Buffer != Original);
            DWORD Cursor = 0;
            assert(SUCCEEDED(Stream.Buffer->GetCurrentPosition(&Cursor, nullptr)) && Cursor == 24000);
            assert(SUCCEEDED(Stream.Buffer->GetFrequency(&Actual)) && Actual == 12000);
            long Value = 0;
            assert(SUCCEEDED(Stream.Buffer->GetVolume(&Value)) && Value == Stream.Volume);
            assert(SUCCEEDED(Stream.Buffer->GetPan(&Value)) && Value == Stream.Pan);
            void* Data = nullptr; DWORD Bytes = 0;
            assert(SUCCEEDED(Stream.Buffer->Lock(0, 0, &Data, &Bytes, nullptr, nullptr, DSBLOCK_ENTIREBUFFER)));
            assert(Bytes == Pcm.size() && memcmp(Data, Pcm.data(), Bytes) == 0);
            assert(SUCCEEDED(Stream.Buffer->Unlock(Data, Bytes, nullptr, 0)));
            auto* Upgraded = Stream.Buffer;
            assert(SetStreamTimeScale(Device, &Stream, 1.f) && Stream.Buffer == Upgraded);
            assert(SUCCEEDED(Stream.Buffer->GetFrequency(&Actual)) && Actual == 48000);
            assert(SUCCEEDED(Stream.Buffer->GetStatus(&Status)) && !(Status & DSBSTATUS_PLAYING));
            Stream.Buffer->Release();
        }
        Copy->Release(); Original->Release();
    }
    Device->Release();
    puts("PASS: real DirectSound 2D/3D buffers, engine throttle pitch x time scale, fixed-pitch effects, stream cursor/PCM/volume/pan and restore (no playback)");
}
