#include "solar_animation_client.h"
#include "solar_animation.h"
#include "rpc_iclient_args.h"
#include "client_gameobj.h"
#include "client_objdb.h"
#include "common_cobject.h"
#include "common_misc.h"
#include "common_id.h"
#include "menu_sound_arch.h"
#include "soundmanager.h"
#include <map>

namespace {
struct Entry { unsigned Serial = 0; ISoundSource* Sound = nullptr; };
std::map<FClientGameobj*,Entry> Playing;
void Stop(Entry& e) { if (e.Sound) { e.Sound->Stop(); e.Sound->Release(); e.Sound = nullptr; } }
}
void ClientSolarAnimation(FPayloadServerActivateObject const& packet)
{
    auto* go = ClientObjDb_FindObject(packet.ObjectId, 2);
    if (!go || !go->GetObject()) return;
    auto* obj = go->GetObject();
    if ((static_cast<unsigned>(obj->ObjectClass) & 0x303u) != 0x303u) return;
    auto& e = Playing[go];
    auto const& cmd = packet.Animation;
    if (cmd.Serial && e.Serial && static_cast<int>(cmd.Serial - e.Serial) <= 0) return;
    // SP shares Common objects with its local server, which already started it.
    if (!SinglePlayer() && !SolarAnimation::Play(static_cast<CSolar*>(obj), cmd)) return;
    e.Serial = cmd.Serial;
    Stop(e);
    if (!cmd.Sound) return; // late-join snapshots never replay sound
    ID_String id; id.Id = cmd.Sound;
    void* arch = LookupClientSoundArch(&id);
    if (!arch) return;
    auto* sound = static_cast<ISoundSource*>(CreateClientSoundSource3D());
    if (!sound) return;
    float transform[12] = {1,0,0,0,1,0,0,0,1,0,0,0};
    sound->SetLooping(0);
    sound->SetPose(obj->EngineInstanceId, transform);
    if (!sound->Start(arch,0)) { sound->Release(); return; }
    e.Sound = sound;
}
void ClientSolarAnimationTick(FClientGameobj* go)
{
    auto it = Playing.find(go);
    if (it != Playing.end() && it->second.Sound && it->second.Sound->IsFinished()) Stop(it->second);
}
void ClientSolarAnimationForget(FClientGameobj* go)
{
    auto it = Playing.find(go);
    if (it != Playing.end()) { Stop(it->second); Playing.erase(it); }
}
