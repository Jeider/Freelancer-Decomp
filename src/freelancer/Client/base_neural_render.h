#pragma once

namespace BaseNeural
{
    // A scope is issued by the gameplay base frame only, never by intro/menu.
    class FrameScope
    {
    public:
        FrameScope();
        ~FrameScope();
        FrameScope(FrameScope const&) = delete;
        FrameScope& operator=(FrameScope const&) = delete;
    };
    bool FinishScene(); // true only when a processed frame replaced the original
    void BeginScene();
    bool EndScene(); // resolve base supersampling before native-resolution UI
    void Stop();
}
