// Used only by the explicit port export. The regular streaming path is untouched.
// Keep the decoded ring, read/write offsets and playback cursor when adding frequency
// control to an already running stream. Caller owns the streamer's worker lock.
    bool SetStreamTimeScale(IDirectSound* Device, FStreamingSound* Stream, float Rate)
    {
        IDirectSoundBuffer* Original = Stream->Buffer;
        if (!Original)
            return false;
        Rate = AudioTimeScale::SlowRate(Rate);
        DWORD Frequency = static_cast<DWORD>(double(Stream->PcmRate) * Rate);
        if (Frequency < 100) Frequency = 100;
        if (Frequency > 100000) Frequency = 100000;
        DSBCAPS Caps = {};
        Caps.dwSize = sizeof(Caps);
        if (Original->GetCaps(&Caps) < 0)
            return false;
        if (Caps.dwFlags & DSBCAPS_CTRLFREQUENCY)
            return Original->SetFrequency(Frequency) >= 0;
        if (Rate == 1.f)
            return true;

        WAVEFORMATEX Format = {};
        if (Original->GetFormat(&Format, sizeof(Format), nullptr) < 0)
            return false;
        DSBUFFERDESC Desc = {};
        Desc.dwSize = sizeof(Desc);
        Desc.dwFlags = (Caps.dwFlags & ~(DSBCAPS_LOCHARDWARE | DSBCAPS_LOCDEFER)) |
                      DSBCAPS_CTRLFREQUENCY | DSBCAPS_LOCSOFTWARE;
        Desc.dwBufferBytes = Caps.dwBufferBytes;
        Desc.lpwfxFormat = &Format;
        IDirectSoundBuffer* Copy = nullptr;
        if (Device->CreateSoundBuffer(&Desc, &Copy, nullptr) < 0)
            return false;

        DWORD Status = 0;
        bool Ok = Original->GetStatus(&Status) >= 0;
        bool Playing = (Status & DSBSTATUS_PLAYING) != 0;
        if (Ok && Playing)
            Ok = Original->Stop() >= 0;
        DWORD Cursor = 0;
        if (Ok)
            Ok = Original->GetCurrentPosition(&Cursor, nullptr) >= 0;
        void *Src = nullptr, *Dst = nullptr;
        DWORD SrcBytes = 0, DstBytes = 0;
        if (Ok)
        {
            Ok = false;
            if (Original->Lock(0, 0, &Src, &SrcBytes, nullptr, nullptr, DSBLOCK_ENTIREBUFFER) >= 0)
            {
                if (Copy->Lock(0, 0, &Dst, &DstBytes, nullptr, nullptr, DSBLOCK_ENTIREBUFFER) >= 0)
                {
                    Ok = SrcBytes == Caps.dwBufferBytes && DstBytes == SrcBytes;
                    if (Ok) memcpy(Dst, Src, SrcBytes);
                    if (Copy->Unlock(Dst, DstBytes, nullptr, 0) < 0) Ok = false;
                }
                if (Original->Unlock(Src, SrcBytes, nullptr, 0) < 0) Ok = false;
            }
        }
        if (Ok)
            Ok = Copy->SetCurrentPosition(Cursor) >= 0 &&
                 Copy->SetVolume(Stream->Volume) >= 0 && Copy->SetPan(Stream->Pan) >= 0 &&
                 Copy->SetFrequency(Frequency) >= 0;
        if (Ok && Playing)
            Ok = Copy->Play(0, 0, DSBPLAY_LOOPING) >= 0;
        if (!Ok)
        {
            Copy->Release();
            if (Playing) Original->Play(0, 0, DSBPLAY_LOOPING);
            return false;
        }
        Stream->Buffer = Copy;
        Original->Release();
        return true;
    }
