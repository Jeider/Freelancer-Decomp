// Optional path only: ordinary archetypes and their DirectSound flags stay intact.
// An affected instance gets a private PCM copy only if its buffer cannot change pitch.
    bool CreateTimeScaleBuffer(IDirectSound* Device, IDirectSoundBuffer* Original,
                               IDirectSoundBuffer** Out)
    {
        DSBCAPS Caps = {};
        Caps.dwSize = sizeof(Caps);
        WAVEFORMATEX Format = {};
        if (Original->GetCaps(&Caps) < 0 ||
            Original->GetFormat(&Format, sizeof(Format), nullptr) < 0)
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
        void* Samples = nullptr;
        DWORD Bytes = 0;
        bool Ok = false;
        if (Original->Lock(0, 0, &Samples, &Bytes, nullptr, nullptr, DSBLOCK_ENTIREBUFFER) >= 0)
        {
            Ok = Bytes == Caps.dwBufferBytes && UploadSoundBuffer(Copy, Samples, Bytes) >= 0;
            Original->Unlock(Samples, Bytes, nullptr, 0);
        }
        if (!Ok)
        {
            Copy->Release();
            return false;
        }
        *Out = Copy;
        return true;
    }
