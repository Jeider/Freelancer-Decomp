#include "base_neural_render.h"
#include "base_neural_preferences.h"
#include "menu_universe_base.h"
#include "render/IRPBaseNeural.h"
#include "dalib.h"
#include "port_config.h"
#include "room_camera.h"
#include "gf_script.h"
#include <cmath>
#include <cstring>

namespace
{
    bool Allowed = false;
    IRPBaseNeural* Pipeline = nullptr;
    unsigned LastBase = 0, LastRoom = 0;
    uint64_t FrameId = 0;
    int LastResult = -100;
    int LastCameraSlot = -2;
    DWORD LastTick = 0;
    float LastPosition[3] = {}, LastOrientation[9] = {}, LastFov = 0;
    bool Supersampling = false;
}

BaseNeural::FrameScope::FrameScope() { Allowed = true; }
BaseNeural::FrameScope::~FrameScope() { EndScene(); Allowed = false; }

void BaseNeural::BeginScene()
{
    if(!Allowed||!Enabled()||!GetClientLocationCurrentBase()||!GetClientLocationCurrentRoom())return;
    if(!Pipeline&&DALib::Pipeline)DALib::Pipeline->QueryInterface(Iids::RPBaseNeural,reinterpret_cast<void**>(&Pipeline));
    if(!Pipeline)return;
    float scale=PortConfigFloat("BaseNeural","supersample_scale",1.f);
    if(!std::isfinite(scale)||scale<=1.f)return;
    Supersampling=Pipeline->BeginBaseSupersample(scale)==0;
}
bool BaseNeural::EndScene()
{
    bool resolved=false;
    if(Supersampling&&Pipeline)resolved=Pipeline->EndBaseSupersample()==0;
    Supersampling=false;return resolved;
}

void BaseNeural::Stop()
{
    Allowed = false;
    Supersampling=false;
    if (Pipeline)
    {
        Pipeline->StopBaseNeural();
        Pipeline->Release();
        Pipeline = nullptr;
    }
    LastBase = LastRoom = 0;
    LastResult = -100;
    LastCameraSlot = -2; LastTick = 0;
}

bool BaseNeural::FinishScene()
{
    if (!Allowed) return false;
    if (!Enabled()) { Stop(); return false; }
    unsigned const Base = GetClientLocationCurrentBase();
    unsigned const Room = GetClientLocationCurrentRoom();
    if (!Base || !Room) { Stop(); return false; }
    if (!Pipeline && DALib::Pipeline)
        DALib::Pipeline->QueryInterface(Iids::RPBaseNeural, reinterpret_cast<void**>(&Pipeline));
    if (!Pipeline) return false;
    BaseNeuralBridge::Frame F = {};
    F.size = sizeof(F); F.version = BaseNeuralBridge::Version;
    F.frame_id = ++FrameId; F.base = Base; F.room = Room;
    F.reset = Base != LastBase || Room != LastRoom;
    DWORD const Now = GetTickCount();
    auto* Camera = static_cast<FRoomCamera*>(GetClientRoomCamera());
    F.reset |= G_GfCameraPool.ActiveIndex != LastCameraSlot || Now - LastTick > 250 || !Camera;
    if (Camera && !F.reset)
    {
        float PositionDelta = 0, OrientationDelta = 0;
        for (unsigned i = 0; i < 3; ++i)
        { float d = Camera->Pos[i] - LastPosition[i]; PositionDelta += d*d; }
        for (unsigned i = 0; i < 9; ++i)
        { float d = Camera->Orient[i] - LastOrientation[i]; OrientationDelta += d*d; }
        F.reset |= PositionDelta > 4.f || OrientationDelta > .2f || std::fabs(Camera->HalfFovXDeg - LastFov) > 1.f;
    }
    F.mode = PortConfigInt("BaseNeural", "mode", 1) == 2 ? BaseNeuralBridge::Neural : BaseNeuralBridge::Passthrough;
    int const Timeout = PortConfigInt("BaseNeural", "result_deadline_ms", 50);
    F.timeout_ms = Timeout < 1 ? 1u : Timeout > 250 ? 250u : static_cast<unsigned>(Timeout);
    F.strength = StrengthPercent() / 100.f;
    int const Result = Pipeline->ProcessBaseNeural(&F);
    if (Result != LastResult)
    {
        FDUMP(0x100001, "BaseNeural: mode=%u result=%d (0=unavailable,1=applied,2=warming,-1=fault)\n", F.mode, Result);
        LastResult = Result;
    }
    // A skipped evaluation cannot inherit motion from an unrelated earlier frame.
    if (Result == BaseNeuralBridge::Applied)
    {
        LastBase = Base; LastRoom = Room; LastTick = Now; LastCameraSlot = G_GfCameraPool.ActiveIndex;
        if (Camera)
        {
            std::memcpy(LastPosition, Camera->Pos, sizeof(LastPosition));
            std::memcpy(LastOrientation, Camera->Orient, sizeof(LastOrientation));
            LastFov = Camera->HalfFovXDeg;
        }
    }
    else { LastBase = LastRoom = 0; }
    // At zero show the ordinary room including its normal AA. Keep the base
    // session warm so moving the slider back up does not reload the model.
    return Result == BaseNeuralBridge::Applied && F.strength > 0;
}
