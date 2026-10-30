#include "tradelane_ring_anim.h"

#include "client_gameobj.h"
#include "common_animdb.h"
#include "common_cobject.h"
#include "common_ini.h"
#include "common_misc.h"
#include "DALib.h"
#include "dacom.h"
#include "engine/engbase.h"

#include <array>
#include <cmath>
#include <map>
#include <string>

namespace
{
    using Names = std::array<std::string, 2>; // 0 HpLeftLane, 1 HpRightLane
    std::map<void const*, Names> Config;
    struct Playback
    {
        int Handle = -1;
        float Duration = 0.0f;
    };
    // Independent of the short-lived travel-effect nodes: cancellation, departure
    // and empty ship lists must never interrupt a ring's one-shot.
    std::map<FClientGameobj*, std::array<Playback, 2>> Playing;

    char const* Name(FClientGameobj* Solar, unsigned Side)
    {
        if (!Solar || Side > 1) return "";
        CObject* Object = Solar->GetObject();
        if (!Object || !Object->Archetype) return "";
        auto It = Config.find(Object->Archetype->Companion);
        return It == Config.end() ? "" : It->second[Side].c_str();
    }

    void Release(Playback& Play)
    {
        if (Play.Handle == -1) return;
        AnimDB::Rem(Play.Handle);
        DALib::Anim->StopPlayback(Play.Handle);
        DALib::Anim->DestroyScript(AsOpaqueDword(Play.Handle));
        Play.Handle = -1;
    }

    bool Finish(Playback& Play)
    {
        if (Play.Handle == -1) return true;
        if (DALib::Anim->GetStoredDuration(Play.Handle) < Play.Duration &&
            DALib::Anim->FilterObjects(AsOpaqueDword(Play.Handle)) == 0) return false;
        Release(Play);
        return true;
    }
}

bool TradeLaneRingAnimRead(void const* Companion, INI_Reader& Reader)
{
    unsigned Side;
    if (Reader.is_value("left_ring_anim")) Side = 0;
    else if (Reader.is_value("right_ring_anim")) Side = 1;
    else return false;
    char const* Text = Reader.get_value_string();
    Config[Companion][Side] = Text ? Text : "";
    return true;
}

void TradeLaneRingAnimCopy(void const* Destination, void const* Source)
{
    if (Destination == Source) return;
    auto It = Config.find(Source);
    if (It == Config.end()) Config.erase(Destination);
    else Config[Destination] = It->second;
}

void TradeLaneRingAnimForgetConfig(void const* Companion) { Config.erase(Companion); }

bool TradeLaneRingAnimConfigured(FClientGameobj* Solar, unsigned Side)
{
    return Name(Solar, Side)[0] != '\0';
}

void TradeLaneRingAnimStart(FClientGameobj* Solar, unsigned Side)
{
    char const* ScriptName = Name(Solar, Side);
    if (!ScriptName[0]) return;
    auto& Pair = Playing[Solar];
    // No restart and no queued request, including after an early cancellation.
    if (!Finish(Pair[0]) || !Finish(Pair[1])) return;
    CObject* Object = Solar->GetObject();
    void* Script = AsOpaqueDword(Object->Archetype->get_script_index());
    float Duration = DALib::Anim->GetNamedDuration(Script, ScriptName);
    if (!std::isfinite(Duration) || Duration <= 0.0f)
    {
        FDUMP(0x100001, "tradelane ring animation missing/invalid: %s", ScriptName);
        Playing.erase(Solar);
        return;
    }
    int Handle = static_cast<int>(DALib::Anim->PlayScript(
        Script, AsOpaqueDword(Object->EngineInstanceId), ScriptName, nullptr, nullptr));
    if (Handle == -1)
    {
        FDUMP(0x100001, "tradelane ring animation cannot bind: %s", ScriptName);
        Playing.erase(Solar);
        return;
    }
    Pair[Side].Handle = Handle;
    Pair[Side].Duration = Duration;
    // Flags 0: forward ONCE. Explicit time zero, no looping or reverse-on-release.
    DALib::Anim->EvalPlayback(Handle, 0, 0.0f, 1.0f, nullptr,
                             AsOpaqueDword(1.0f), AsOpaqueDword(1.0f), nullptr);
    if (DALib::Anim->FilterObjects(AsOpaqueDword(Handle)) != 0)
    {
        FDUMP(0x100001, "tradelane ring animation has no playable channels: %s", ScriptName);
        Release(Pair[Side]);
        Playing.erase(Solar);
        return;
    }
    AnimDB::Add(Handle);
}

void TradeLaneRingAnimTick()
{
    for (auto It = Playing.begin(); It != Playing.end(); )
    {
        bool LeftDone = Finish(It->second[0]);
        bool RightDone = Finish(It->second[1]);
        if (LeftDone && RightDone) It = Playing.erase(It);
        else ++It;
    }
}

void TradeLaneRingAnimForget(FClientGameobj* Solar)
{
    auto It = Playing.find(Solar);
    if (It == Playing.end()) return;
    for (auto& Play : It->second) Release(Play);
    Playing.erase(It);
}

void TradeLaneRingAnimShutdown()
{
    while (!Playing.empty()) TradeLaneRingAnimForget(Playing.begin()->first);
}
