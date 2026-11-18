// Included inside menu_sound_arch.cpp's private namespace, after the source types.
// This feature never changes StartTick or the normal SoundManager clock.
#ifdef FREELANCER_DBG_OPTIONS
    bool G_AudioTimeScaleEnabled = false;
    float G_AudioSlowRate = 1.f;
    PortAudioTimeScaleInstall G_InstallAudioTimeScale = nullptr;
    bool G_AudioTimeScaleRegistered = false;
    std::map<ISoundSource*, AudioTimeScale::Clock> G_AudioSlowClocks;
    PortStreamTimeScaleSet G_SetStreamTimeScale = nullptr;
    struct FSlowStream
    {
        void* Handle = nullptr;
        float Rate = 1.f;
        bool Failed = false;
    };
    std::map<FStreamedSource*, FSlowStream> G_AudioSlowStreams;

    int __cdecl QueryAudioTimeScale(ISoundSource* Key, PortAudioTimeScaleState* State)
    {
        auto It = G_AudioSlowClocks.find(Key);
        if (It == G_AudioSlowClocks.end())
            return 0;
        auto& Clock = It->second;
        Clock.Advance(GetTickCount(), Key->IsPaused() != 0);
        if (State)
        {
            State->ElapsedMs = Clock.ElapsedMs;
            State->Rate = Clock.Rate;
        }
        else
        {
            Clock.Failed = true;
            Clock.Rate = 1.f;
        }
        return 1;
    }

    bool ConnectAudioTimeScale()
    {
        if (!G_SetStreamTimeScale)
        {
            HMODULE Module = GetModuleHandleA("SoundStreamer.dll");
            if (Module)
                G_SetStreamTimeScale = reinterpret_cast<PortStreamTimeScaleSet>(
                    GetProcAddress(Module, "PortSetStreamTimeScaleV1"));
        }
        if (!G_InstallAudioTimeScale)
        {
            HMODULE Module = GetModuleHandleA("SoundManager.dll");
            if (!Module)
                return false;
            G_InstallAudioTimeScale = reinterpret_cast<PortAudioTimeScaleInstall>(
                GetProcAddress(Module, "PortInstallAudioTimeScaleV1"));
        }
        return G_InstallAudioTimeScale != nullptr;
    }

    void RegisterAudioTimeScale(bool Active)
    {
        if (G_InstallAudioTimeScale && Active != G_AudioTimeScaleRegistered)
        {
            G_InstallAudioTimeScale(Active ? &QueryAudioTimeScale : nullptr);
            G_AudioTimeScaleRegistered = Active;
        }
    }

    void TrackAudioTimeScale(FSoundSource* Source)
    {
        if (G_AudioSlowRate >= 1.f || (Source->Flags & 0x18u) != 0x18u ||
            (Source->Flags & 4u) == 0 || Source->Type == 1 || Source->Type == 3)
            return;
        unsigned Now = GetTickCount();
        auto Inserted = G_AudioSlowClocks.emplace(Source, AudioTimeScale::Clock{});
        if (Inserted.second)
        {
            auto& Clock = Inserted.first->second;
            unsigned Tick = Source->IsPaused() ? unsigned(Source->Field08) : Now;
            Clock.Seek(Now, double(Tick - unsigned(Source->StartTick)));
            Clock.Rate = G_AudioSlowRate;
        }
    }

    void ApplyStreamAudioTimeScale(FStreamedSource* Source)
    {
        if (!G_SetStreamTimeScale || !IsStreamHandle(Source->StreamHandle))
            return;
        float Rate = Source->Type == 1 || Source->Type == 3 ? 1.f : G_AudioSlowRate;
        auto It = G_AudioSlowStreams.find(Source);
        if (It == G_AudioSlowStreams.end())
        {
            if (Rate == 1.f)
                return;
            It = G_AudioSlowStreams.emplace(Source, FSlowStream{}).first;
        }
        auto& State = It->second;
        if (State.Handle != Source->StreamHandle)
        {
            State = FSlowStream{};
            State.Handle = Source->StreamHandle;
        }
        if (Rate != State.Rate && (!State.Failed || Rate == 1.f))
        {
            State.Failed = G_SetStreamTimeScale(State.Handle, Rate) == 0;
            if (!State.Failed) State.Rate = Rate;
        }
        if (State.Rate == 1.f && Rate == 1.f)
            G_AudioSlowStreams.erase(It);
    }

    void TickStreamAudioTimeScale()
    {
        if (G_AudioSlowRate < 1.f && G_SetStreamTimeScale)
        {
            for (auto* Node = G_PlayingSources.Head->Next;
                 Node != G_PlayingSources.Head; Node = Node->Next)
                if ((Node->Value->Flags & 4u) == 0)
                    ApplyStreamAudioTimeScale(static_cast<FStreamedSource*>(Node->Value));
        }
        else
        {
            for (auto It = G_AudioSlowStreams.begin(); It != G_AudioSlowStreams.end();)
            {
                auto* Source = (It++)->first; // Apply may erase the current entry.
                ApplyStreamAudioTimeScale(Source);
            }
        }
    }

    void TickAudioTimeScale()
    {
        // Disabled by default. No map walks or DLL calls on the untouched path.
        if (!G_AudioTimeScaleEnabled && G_AudioSlowClocks.empty() && G_AudioSlowStreams.empty())
        {
            RegisterAudioTimeScale(false);
            G_AudioSlowRate = 1.f;
            return;
        }
        G_AudioSlowRate = G_AudioTimeScaleEnabled && SinglePlayer()
            ? AudioTimeScale::SlowRate(GetClientTimeScale()) : 1.f;
        TickStreamAudioTimeScale();
        if (G_AudioSlowRate < 1.f)
        {
            RegisterAudioTimeScale(true);
            for (auto* Node = G_PlayingSources.Head->Next;
                 Node != G_PlayingSources.Head; Node = Node->Next)
                TrackAudioTimeScale(Node->Value);
        }
        unsigned Now = GetTickCount();
        for (auto& Entry : G_AudioSlowClocks)
            Entry.second.SetRate(Now, Entry.first->IsPaused() != 0, G_AudioSlowRate);
        if (G_AudioSlowClocks.empty() && G_AudioSlowRate == 1.f)
            RegisterAudioTimeScale(false);
    }

    bool AudioTimeScaleElapsed(FSoundSource* Source, double& Elapsed)
    {
        if (G_AudioSlowClocks.empty())
            return false;
        PortAudioTimeScaleState State;
        if (!QueryAudioTimeScale(Source, &State))
            return false;
        Elapsed = State.ElapsedMs;
        return true;
    }

    void ForgetAudioTimeScale(FSoundSource* Source)
    {
        if (!G_AudioSlowStreams.empty() && (Source->Flags & 4u) == 0)
            G_AudioSlowStreams.erase(static_cast<FStreamedSource*>(Source));
        if (G_AudioSlowClocks.empty())
            return;
        G_AudioSlowClocks.erase(Source);
        if (G_AudioSlowClocks.empty() && G_AudioSlowRate == 1.f)
            RegisterAudioTimeScale(false);
    }

    void SeekAudioTimeScale(FSoundSource* Source, int Offset)
    {
        auto It = G_AudioSlowClocks.find(Source);
        if (It != G_AudioSlowClocks.end())
            It->second.Seek(GetTickCount(), double(unsigned(Offset)));
    }
#else
    void TickAudioTimeScale() {}
    void TrackAudioTimeScale(FSoundSource*) {}
    bool AudioTimeScaleElapsed(FSoundSource*, double&) { return false; }
    void ForgetAudioTimeScale(FSoundSource*) {}
    void SeekAudioTimeScale(FSoundSource*, int) {}
    void ApplyStreamAudioTimeScale(FStreamedSource*) {}
#endif
