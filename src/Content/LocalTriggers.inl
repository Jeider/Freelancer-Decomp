// Included by MissionScript.cpp. Keep local execution outside the retail object
// layout: no second Story/controller or mission world is created for a participant.
#include "LocalTriggers.h"
#include "campaign_server.h"
#include <memory>
#include <string>

namespace LocalTriggers {
struct SavedTrigger { int state = 1; std::string condition; };
struct SavedRtc { std::string path; bool done = false, repeat = false; };
struct Snapshot {
    std::map<unsigned, SavedTrigger> triggers;
    std::vector<SavedRtc> scenes;
};
// MP character names are unique on the server; never key progress by a reusable
// connection slot. Campaign restart/reset is intentionally not inferred here.
using Character = std::wstring;
std::map<Character, std::map<std::string, Snapshot>> Loaded;
struct Bank {
    FmtStr title, offer;
    bool uiInitialized = false;
    unsigned slot = 0, location = 0;
    bool initialized = false;
    FTriggerMap triggers;
    std::list<FTriggerMap::iterator> active;
    std::map<unsigned, unsigned> pending, initial;
    std::list<FMissionTimer> timers;
    std::list<FStoryMissionListNode_0x2f4> scenes;
    ~Bank() {
        for (auto& item : triggers) DeleteTriggerContents(&item.second);
        for (auto& scene : scenes) delete scene.Field_0x90;
    }
};
struct Runtime {
    bool m01a = false;
    bool accepted = false;
    std::map<unsigned, unsigned> globalPending;
    std::map<unsigned, bool> globalActivated;
    std::string source;
    Character owner;
    std::map<unsigned, std::string> definitions;
    std::map<Character, std::unique_ptr<Bank>> players;
    bool started = false, executing = false;
};
std::map<FMissionScript*, Runtime> Runtimes;

Snapshot Remember(Bank const& bank) {
    Snapshot snapshot;
    for (auto const& item : bank.triggers) {
        SavedTrigger saved; saved.state = item.second.State;
        // Of the deliberately limited local condition set, only Timer has
        // mutable serialized data. Do not reset it through OnActivate on load.
        if (auto* timer = dynamic_cast<CndTimer*>(item.second.Condition)) {
            char value[96]; snprintf(value, sizeof(value), "Cnd_Timer = %.9g\n", timer->Elapsed);
            saved.condition = value;
        }
        snapshot.triggers.emplace(item.first, saved);
    }
    for (auto const& scene : bank.scenes)
        snapshot.scenes.push_back({scene.Path, scene.Field_0x94 != 0, scene.Field_0x95 != 0});
    return snapshot;
}

Character Identity(unsigned player) {
    Character name;
    if (pub::Player::GetName(player, name) != 0) name.clear();
    return name;
}

bool Allowed(char const* name) {
    static char const* const keys[] = {
        "nickname", "execution_scope", "InitState", "repeatable", "system",
        "Cnd_True", "Cnd_Timer", "Cnd_BaseEnter", "Cnd_BaseExit",
        "Cnd_LocEnter", "Cnd_LocExit", "Cnd_PopUpDialog", "Cnd_RTCDone",
        "Cnd_WatchTrigger", "Cnd_CharSelect", "Cnd_MsnResponse",
        "Act_ActTrig", "Act_DeactTrig", "Act_PopUpDialog",
        "Act_AddRTC", "Act_RemoveRTC", "Act_SetShipAndLoadout",
        "Act_NNIds", "Act_SetNNObj", "Act_SetTitle", "Act_SetOffer"
    };
    for (auto key : keys) if (!_stricmp(name, key)) return true;
    return false;
}

// Consumes only explicitly local (or invalid-scope) sections. Missing scope is
// always the original global path, including old save/load behavior.
bool Capture(FMissionScript* mission, INI_Reader* reader) {
    if (!CampaignServer::Enabled()) return false;
    INI_Reader::State cursor; reader->get_state(cursor);
    std::string scope = "global", text, nickname;
    bool valid = true; unsigned conditions = 0;
    while (reader->read_value()) {
        auto name = std::string(reader->get_name_ptr());
        text += name + " = " + reader->get_value_string() + "\n";
        if (reader->is_value("execution_scope")) scope = reader->get_value_string(0);
        if (reader->is_value("nickname")) nickname = reader->get_value_string(0);
        if (!_strnicmp(name.c_str(), "Cnd_", 4)) ++conditions;
        valid = valid && Allowed(name.c_str());
    }
    auto configured = Runtimes.find(mission);
    if (configured != Runtimes.end() && configured->second.m01a) {
        static char const* personal[] = {"real_mission_init", "init_bar", "START_vendor_do_accept", "return_to_deck"};
        for (auto name : personal) if (!_stricmp(nickname.c_str(), name)) scope = "local";
        if (!_stricmp(nickname.c_str(), "real_mission_init")) text += "InitState = ACTIVE\n";
    }
    if (!_stricmp(scope.c_str(), "global")) { reader->set_state(cursor); return false; }
    if (_stricmp(scope.c_str(), "local") || !valid || conditions != 1 || nickname.empty()) {
        FDUMP(0x100002, "LocalTriggers: rejected trigger '%s': scope/command/condition invalid", nickname.c_str());
        return true;
    }
    auto& runtime = Runtimes[mission];
    if (runtime.source.empty()) runtime.source = reader->get_file_name();
    runtime.definitions.emplace(CreateID(nickname.c_str()), text);
    return true;
}

// Existing conditions/actions resolve Mission->PlayerId and PlayerState. Scope
// these and their mutable containers together, then restore even on early return.
struct Context {
    FMissionScript* mission; Bank& bank; unsigned player, location;
    FContentPlayerState* state;
    std::map<unsigned, FMissionPlayer*> players;
    FmtStr title, offer;
    Context(FMissionScript* m, Bank& b) : mission(m), bank(b), player(m->PlayerId),
        location(m->CurrentLocationId), state(m->PlayerState) {
        auto* personal = m->GetOrCreatePlayer(b.slot);
        if (personal && (!b.uiInitialized || personal->Objectives.Objectives.empty())) {
            auto original = m->Players.find(m->PlayerId);
            if (original != m->Players.end() && original->second && original->second != personal)
                personal->Objectives = original->second->Objectives;
        }
        if (personal) personal->PlayerState = FindContentPlayerState(b.slot);
        players.swap(m->Players);
        if (personal) m->Players.emplace(b.slot, personal);
        title = m->Field_0x50; offer = m->Field_0x68;
        if (!b.uiInitialized) { b.title = title; b.offer = offer; b.uiInitialized = true; }
        m->Field_0x50 = b.title; m->Field_0x68 = b.offer;
        swap(); m->PlayerId = b.slot; m->PlayerState = FindContentPlayerState(b.slot);
        m->CurrentLocationId = b.location;
    }
    void swap() {
        mission->TriggerMap.swap(bank.triggers); mission->ActiveTriggers.swap(bank.active);
        mission->PendingActivations.swap(bank.pending); mission->InitiallyActive.swap(bank.initial);
        mission->Timers.swap(bank.timers); mission->List_0x2f4.swap(bank.scenes);
    }
    ~Context() {
        bank.title = mission->Field_0x50; bank.offer = mission->Field_0x68;
        mission->Field_0x50 = title; mission->Field_0x68 = offer;
        mission->Players.clear(); mission->Players.swap(players);
        bank.location = mission->CurrentLocationId; swap();
        mission->PlayerId = player; mission->PlayerState = state; mission->CurrentLocationId = location;
    }
};

void Initialize(FMissionScript* mission, Runtime& runtime, Bank& bank, Character const& identity) {
    Snapshot const* saved = nullptr;
    auto character = Loaded.find(identity);
    if (character != Loaded.end()) {
        auto found = character->second.find(runtime.source);
        if (found != character->second.end()) saved = &found->second;
    }
    for (auto const& definition : runtime.definitions) {
        INI_Reader reader;
        auto text = std::string("[Trigger]\n") + definition.second;
        if (!reader.open_memory(text.c_str(), static_cast<unsigned>(text.size())) || !reader.read_header()) continue;
        FTrigger trigger{}; trigger.State = G_TriggerStateInactive;
        trigger.Id = definition.first; trigger.Mission = mission;
        // The definition's nickname need not be its first line.
        LoadTrigger(&trigger, &reader);
        auto inserted = mission->TriggerMap.emplace(trigger.Id, trigger).first;
        auto& live = inserted->second;
        if (saved) {
            auto entry = saved->triggers.find(trigger.Id);
            // A changed script does not silently reissue an initial reward.
            live.State = entry == saved->triggers.end() ? G_TriggerStateInactive : entry->second.state;
            if (entry != saved->triggers.end() && !entry->second.condition.empty()) {
                INI_Reader condition;
                auto data = std::string("[Condition]\n") + entry->second.condition;
                if (condition.open_memory(data.c_str(), static_cast<unsigned>(data.size())) && condition.read_header())
                    live.Condition->Load(&condition);
            }
            if (live.State == G_TriggerStateActive) mission->ActiveTriggers.push_back(inserted);
        } else if (live.State == G_TriggerStateActive) mission->InitiallyActive.emplace(trigger.Id, trigger.Id);
    }
    // Cross-scope Act_ActTrig/DeactTrig references cannot fall through to global
    // maps: this execution context contains local definitions only.
    if (saved) for (auto const& scene : saved->scenes) {
        if (scene.path.size() >= sizeof(FStoryMissionListNode_0x2f4().Path)) continue;
        FStoryMissionListNode_0x2f4 record;
        strcpy(record.Path, scene.path.c_str()); record.PathLength = static_cast<unsigned>(scene.path.size());
        record.Field_0x94 = scene.done; record.Field_0x95 = scene.repeat;
        mission->List_0x2f4.push_back(record);
    }
    bank.initialized = true;
    if (!saved) ActivateInitialMissionTriggers(mission);
}

unsigned Recipient(EMessage event, void const* data) {
    if (!data) return 0;
    auto words = static_cast<unsigned const*>(data);
    switch (event) {
    case EMessage::BaseEnter: case EMessage::BaseExit:
    case EMessage::LocationEnter: case EMessage::LocationExit: case EMessage::GFObjSelect: return words[1];
    case EMessage::PopUpDialog: case EMessage::RtcDone: case EMessage::PlayerLogout: return words[0];
    case EMessage::MissionResponse: return words[3];
    default: return 0;
    }
}

void Dispatch(FMissionScript* mission, EMessage event, void const* data) {
    auto found = Runtimes.find(mission);
    if (found == Runtimes.end()) return;
    auto& runtime = found->second;
    if (runtime.executing) return;
    if (event == EMessage::MissionStart && !runtime.started) {
        runtime.owner = Identity(mission->PlayerId);
        runtime.started = !runtime.owner.empty();
    }
    if (!runtime.started) return;
    unsigned recipient = Recipient(event, data);
    if (event == EMessage::MissionResponse && static_cast<unsigned const*>(data)[0] != mission->ControllerId) return;
    if (event != EMessage::Heartbeat && event != EMessage::MissionStart && !recipient) return;
    runtime.executing = true;
    struct Reset { bool& flag; ~Reset() { flag = false; } } reset{runtime.executing};
    for (auto const& player : GetContentPlayerStates()) {
        auto* state = player.second.get();
        if (!state || (recipient && recipient != player.first)) continue;
        auto identity = Identity(player.first);
        if (identity.empty() || (identity != runtime.owner && state->GetLiveMission() != mission->ControllerId)) continue;
        if (event == EMessage::PlayerLogout && !runtime.players.count(identity)) continue;
        auto& holder = runtime.players[identity];
        if (!holder) holder.reset(new Bank);
        auto& bank = *holder; bank.slot = player.first;
        Context context(mission, bank);
        if (!bank.initialized) {
            Initialize(mission, runtime, bank, identity);
            // A joining guest may already have entered the base. Replay only to
            // their personal bank; completed triggers in a save remain completed.
            unsigned base = 0;
            pub::Player::GetBase(player.first, base);
            if (base) {
                unsigned entry[] = {base, player.first}; EMessage arrival = EMessage::BaseEnter;
                DispatchMissionTriggerEvent(mission, &arrival, entry);
            }
        }
        switch (event) {
        case EMessage::PlayerLogout:
        case EMessage::BaseExit: {
            // Keep RTC descriptors for a reconnect, release only their runtime handles.
            std::vector<SavedRtc> scenes;
            for (auto const& scene : mission->List_0x2f4)
                scenes.push_back({scene.Path, scene.Field_0x94 != 0, scene.Field_0x95 != 0});
            mission->ReleaseRtcScripts();
            for (auto const& scene : scenes) if (!scene.done) {
                FStoryMissionListNode_0x2f4 record;
                strcpy(record.Path, scene.path.c_str());record.PathLength = static_cast<unsigned>(scene.path.size());
                record.Field_0x95 = scene.repeat;mission->List_0x2f4.push_back(record);
            }
            if (event == EMessage::PlayerLogout) { bank.slot = 0; break; }
            DispatchMissionTriggerEvent(mission, &event, data); break;
        }
        case EMessage::BaseEnter:
            for (auto& scene : mission->List_0x2f4)
                if (!scene.Field_0x94 && scene.Field_0x8c == -1) mission->StartRtcScript(&scene);
            DispatchMissionTriggerEvent(mission, &event, data); break;
        case EMessage::LocationEnter:
            mission->CurrentLocationId = *static_cast<unsigned const*>(data);
            DispatchMissionTriggerEvent(mission, &event, data); break;
        case EMessage::GFObjSelect: mission->OnCharacterSelect(data); break;
        case EMessage::LocationExit: mission->OnLocationExit(data); break;
        case EMessage::Heartbeat:
            TickMissionTimers(mission, *static_cast<float const*>(data));
            DispatchMissionTriggerEvent(mission, &event, data); break;
        default: DispatchMissionTriggerEvent(mission, &event, data); break;
        }
    }
    // Run shared successors outside the per-character context, once per campaign.
    runtime.executing = false;
    if (runtime.m01a && !runtime.accepted && !runtime.globalPending.empty()) {
        runtime.accepted = true;
        LocalTriggersAcceptedMission(mission);
    }
    for (auto const& activation : runtime.globalPending) {
        auto target = mission->TriggerMap.find(activation.first);
        if (target != mission->TriggerMap.end() && !runtime.globalActivated[activation.first]) {
            runtime.globalActivated[activation.first] = true;
            mission->PendingActivations.emplace(activation.first, activation.second);
        }
    }
    runtime.globalPending.clear();
}

void Destroy(FMissionScript* mission) {
    auto found = Runtimes.find(mission);
    if (found == Runtimes.end()) return;
    for (auto& player : found->second.players) {
        auto& bank = *player.second;
        if (bank.initialized) Loaded[player.first][found->second.source] = Remember(bank);
        // Never access another character which has since reused this slot.
        if (bank.slot && Identity(bank.slot) == player.first && FindContentPlayerState(bank.slot)) {
            Context context(mission, bank); mission->ReleaseRtcScripts();
        }
    }
    Runtimes.erase(found);
}
} // namespace LocalTriggers

void LocalTriggersConfigureM01a(FMissionScript* mission) {
    if (CampaignServer::Enabled()) LocalTriggers::Runtimes[mission].m01a = true;
}
bool LocalTriggersExecuting(FMissionScript* mission) {
    auto it = LocalTriggers::Runtimes.find(mission);
    return it != LocalTriggers::Runtimes.end() && it->second.executing;
}
bool LocalTriggersBridgeActivation(FMissionScript* mission, unsigned trigger) {
    auto it = LocalTriggers::Runtimes.find(mission);
    if (it == LocalTriggers::Runtimes.end() || !it->second.m01a || !it->second.executing) return false;
    // Explicit m01a boundary, not an unrestricted cross-scope fallback.
    for (auto name : {"LAUNCH_SIG13", "LAUNCH_SIG13_COMPLETE", "MSN_REP_BEFORE"})
        if (trigger == CreateID(name)) { it->second.globalPending.emplace(trigger, trigger); return true; }
    return false;
}

bool LocalTriggersPersonalOffer(unsigned controller) {
    for (auto const& runtime : LocalTriggers::Runtimes)
        if (runtime.first->ControllerId == controller && runtime.second.executing)
            return true;
    return false;
}

void LocalTriggersPlayerLogout(unsigned player) {
    for (auto& runtime : LocalTriggers::Runtimes) {
        LocalTriggers::Dispatch(runtime.first, EMessage::PlayerLogout, &player);
        for (auto& entry : runtime.second.players)
            if (entry.second->initialized)
                LocalTriggers::Loaded[entry.first][runtime.second.source] = LocalTriggers::Remember(*entry.second);
    }
}

void LocalTriggersPlayerLoad(unsigned player, INI_Reader* reader) {
    if (!CampaignServer::Enabled()) return;
    auto identity = LocalTriggers::Identity(player);
    if (identity.empty() || !reader) return;
    auto& saves = LocalTriggers::Loaded[identity]; saves.clear();
    // Character selection/load is a restore boundary, including SP load in the
    // same process. Discard an old bank instead of retaining post-save progress.
    for (auto& runtime : LocalTriggers::Runtimes) {
        auto old = runtime.second.players.find(identity);
        if (old != runtime.second.players.end()) {
            auto& bank = *old->second;
            if (bank.slot == player && FindContentPlayerState(player)) {
                LocalTriggers::Context context(runtime.first, bank);
                runtime.first->ReleaseRtcScripts();
            }
            runtime.second.players.erase(old);
        }
    }
    INI_Reader::State cursor; reader->get_state(cursor); reader->reset();
    while (reader->read_header()) {
        bool trigger = reader->is_header("LocalTriggerState");
        bool rtc = reader->is_header("LocalTriggerRtc");
        if (!trigger && !rtc) continue;
        std::string source;unsigned id = 0; int version = 0;
        LocalTriggers::SavedTrigger state;LocalTriggers::SavedRtc scene;
        while (reader->read_value()) {
            if (reader->is_value("version")) version = reader->get_value_int(0);
            else if (reader->is_value("mission")) source = reader->get_value_string();
            else if (reader->is_value("trigger")) id = static_cast<unsigned>(reader->get_value_int(0));
            else if (reader->is_value("state")) state.state = reader->get_value_int(0);
            else if (reader->is_value("rtc")) scene.path = reader->get_value_string();
            else if (reader->is_value("done")) scene.done = reader->get_value_bool(0);
            else if (reader->is_value("repeatable")) scene.repeat = reader->get_value_bool(0);
            else state.condition += std::string(reader->get_name_ptr()) + " = " + reader->get_value_string() + "\n";
        }
        if (version != 1 || source.empty()) continue;
        if (trigger && id && state.state >= 0 && state.state <= 2) saves[source].triggers[id] = state;
        if (rtc && !scene.path.empty()) saves[source].scenes.push_back(scene);
    }
    reader->set_state(cursor);
}

void LocalTriggersPlayerSave(unsigned player, FILE* file) {
    if (!CampaignServer::Enabled()) return;
    auto identity = LocalTriggers::Identity(player);
    if (identity.empty() || !file) return;
    // Preserve saved progress for missions not currently instantiated as well.
    auto remaining = LocalTriggers::Loaded[identity];
    for (auto& runtime : LocalTriggers::Runtimes) {
        auto found = runtime.second.players.find(identity);
        if (found == runtime.second.players.end() || runtime.second.executing) continue;
        LocalTriggers::Loaded[identity][runtime.second.source] = LocalTriggers::Remember(*found->second);
        remaining.erase(runtime.second.source);
        for (auto const& trigger : found->second->triggers) {
            fprintf(file, "\n[LocalTriggerState]\nversion = 1\nmission = %s\ntrigger = %u\nstate = %d\n",
                    runtime.second.source.c_str(), trigger.first, trigger.second.State);
            if (trigger.second.Condition) trigger.second.Condition->Save(file);
        }
        for (auto const& scene : found->second->scenes)
            fprintf(file, "\n[LocalTriggerRtc]\nversion = 1\nmission = %s\nrtc = %s\ndone = %d\nrepeatable = %d\n",
                    runtime.second.source.c_str(), scene.Path, scene.Field_0x94 != 0, scene.Field_0x95 != 0);
    }
    for (auto const& mission : remaining) {
        for (auto const& trigger : mission.second.triggers)
            fprintf(file, "\n[LocalTriggerState]\nversion = 1\nmission = %s\ntrigger = %u\nstate = %d\n%s",
                    mission.first.c_str(), trigger.first, trigger.second.state, trigger.second.condition.c_str());
        for (auto const& scene : mission.second.scenes)
            fprintf(file, "\n[LocalTriggerRtc]\nversion = 1\nmission = %s\nrtc = %s\ndone = %d\nrepeatable = %d\n",
                    mission.first.c_str(), scene.path.c_str(), scene.done, scene.repeat);
    }
}
