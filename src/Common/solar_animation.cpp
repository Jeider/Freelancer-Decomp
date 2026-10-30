#include "solar_animation.h"
#include "common_archetype.h"
#include "common_cobject.h"
#include "common_ini.h"
#include "common_id.h"
#include "common_animdb.h"
#include "DALib.h"
#include "dacom.h"
#include "engine/engbase.h"
#include <map>
#include <cmath>
#include <cstring>
#include <algorithm>

namespace {
std::map<Archetype::Root const*, SolarAnimation::Config>& Definitions()
{ static std::map<Archetype::Root const*, SolarAnimation::Config> data; return data; }
struct Playback { int Handle = -1; unsigned Serial = 0; };
unsigned char __cdecl CountChannel(void*, void* count) { ++*static_cast<unsigned*>(count); return 1; }
std::map<CSolar*, Playback>& Playing()
{ static std::map<CSolar*, Playback> data; return data; }
void Release(Playback& p)
{
    if (p.Handle == -1) return;
    AnimDB::Rem(p.Handle);
    DALib::Anim->StopPlayback(p.Handle);
    DALib::Anim->DestroyScript(AsOpaqueDword(p.Handle));
    p.Handle = -1;
}
}
bool SolarAnimation::Read(Archetype::Root const* arch, INI_Reader& r)
{
    bool enabled = r.is_value("proximity_door");
    bool radius = r.is_value("door_scan_radius"), release = r.is_value("door_release_radius");
    bool delay = r.is_value("door_close_delay");
    bool open = r.is_value("anim_open"), close = r.is_value("anim_close");
    bool os = r.is_value("door_open_sound"), cs = r.is_value("door_close_sound");
    if (!(enabled || radius || release || delay || open || close || os || cs)) return false;
    auto& c = Definitions()[arch];
    if (enabled) c.Enabled = r.get_value_bool(0);
    if (radius || release || delay) {
        float v = r.get_value_float(0);
        if (std::isfinite(v) && v >= (delay ? 0.0f : 1.0f) && v <= (delay ? 3600.0f : 100000.0f))
            (radius ? c.Radius : release ? c.ReleaseRadius : c.CloseDelay) = v;
    }
    if (open || close) {
        char const* name = r.get_value_string();
        char* dest = open ? c.Open : c.Close;
        if (name && strlen(name) < sizeof(c.Open)) strcpy_s(dest, sizeof(c.Open), name);
        else { dest[0] = 0; FDUMP(0x100001, "solar animation name too long"); }
    }
    if (os || cs) (os ? c.OpenSound : c.CloseSound) = CreateID(r.get_value_string());
    return true;
}
void SolarAnimation::Copy(Archetype::Root const* to, Archetype::Root const* from)
{
    if (to == from) return;
    auto it = Definitions().find(from);
    if (it == Definitions().end()) Definitions().erase(to); else Definitions()[to] = it->second;
}
void SolarAnimation::ForgetDefinition(Archetype::Root const* arch) { Definitions().erase(arch); }
bool SolarAnimation::GetConfig(Archetype::Root const* arch, Config& c)
{
    auto it = Definitions().find(arch);
    if (it == Definitions().end()) return false;
    c = it->second;
    c.ReleaseRadius = (std::max)(c.ReleaseRadius, c.Radius + 1.0f);
    return c.Enabled && c.Open[0] && c.Close[0];
}
float SolarAnimation::Duration(CSolar const* obj, char const* name)
{
    if (!obj || !obj->Archetype || !name || !name[0]) return -1;
    float d = DALib::Anim->GetNamedDuration(AsOpaqueDword(obj->Archetype->get_script_index()), name);
    return std::isfinite(d) && d > 0 && d <= 3600 ? d : -1;
}
bool SolarAnimation::Play(CSolar* obj, SolarAnimationCommand const& cmd)
{
    if (!memchr(cmd.Name, 0, sizeof(cmd.Name)) || !std::isfinite(cmd.Time) || cmd.Time < 0 || cmd.Reverse > 1) return false;
    float d = Duration(obj, cmd.Name);
    if (d < 0) { FDUMP(0x100001, "invalid/missing finite solar animation: %s", cmd.Name); return false; }
    auto& p = Playing()[obj];
    if (cmd.Serial && p.Serial && static_cast<int>(cmd.Serial - p.Serial) <= 0) return false;
    int handle = static_cast<int>(DALib::Anim->PlayScript(AsOpaqueDword(obj->Archetype->get_script_index()),
        AsOpaqueDword(obj->EngineInstanceId), cmd.Name, nullptr, nullptr));
    if (handle == -1) return false;
    unsigned channels = 0;
    DALib::Anim->EnumObjects(reinterpret_cast<void*>(&CountChannel), handle, &channels);
    if (!channels) {
        DALib::Anim->DestroyScript(AsOpaqueDword(handle));
        FDUMP(0x100001, "solar animation has no bound channels: %s", cmd.Name);
        return false;
    }
    Release(p);
    p.Handle = handle; p.Serial = cmd.Serial;
    DALib::Anim->EvalPlayback(handle, cmd.Reverse, (std::min)(d, cmd.Time), 1.0f, nullptr,
        AsOpaqueDword(1.0f), AsOpaqueDword(1.0f), nullptr);
    // Keep the playback alive at its terminal pose. AnimDB updates model AND physics,
    // then unregisters finished channels itself. No forever frame or polling is needed.
    AnimDB::Add(handle);
    return true;
}
void SolarAnimation::Initialize(CSolar* obj)
{
    Config c;
    if (!GetConfig(obj->Archetype, c)) return;
    SolarAnimationCommand cmd;
    strcpy_s(cmd.Name, c.Close);
    cmd.Time = Duration(obj, c.Close);
    if (cmd.Time > 0) Play(obj, cmd);
}
void SolarAnimation::Forget(CSolar* obj)
{
    auto it = Playing().find(obj);
    if (it != Playing().end()) { Release(it->second); Playing().erase(it); }
}
