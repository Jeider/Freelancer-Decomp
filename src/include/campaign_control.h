#pragma once
#include "campaign_server.h"
#include <cstdint>
#include <initializer_list>

namespace CampaignControl {
struct Mission { char const* name; unsigned start, finish, after; bool automaticNext; };
inline Mission const* Missions() {
    static Mission const rows[] = {
        {"Mission_01a",1,2,3,true}, {"Mission_01b",4,4,5,false},
        {"Mission_02",7,8,9,false}, {"Mission_03",10,11,12,false},
        {"Mission_04",13,14,15,false}, {"Mission_05",16,17,18,false},
        {"Mission_06",19,20,21,true}, {"Mission_07",22,23,24,false},
        {"Mission_08",25,26,27,false}, {"Mission_09",28,29,30,true},
        {"Mission_10",31,32,33,true}, {"Mission_11",34,35,36,true},
        {"Mission_12",37,38,39,true}, {"Mission_13",40,41,42,false}
    };
    return rows;
}
constexpr unsigned MissionCount = 14;
enum Phase : unsigned { First, Running, Freeflight, Automatic, Interrupted, Complete, Error };
enum Notice : unsigned { Ready, NoPlayers, PlayerBusy, CreateFailed, DiskError, CorruptSave, OwnerAbsent };
struct State {
    unsigned phase = First, completed = 0, chapter = 0, rank = 1;
    std::uint64_t attempt = 0;
    unsigned revision = 1;
};
struct Snapshot {
    State state; unsigned controller = 0, owner = 0, notice = Ready, initialized = 0;
    std::uintptr_t ownerState = 0;
    wchar_t ownerName[64] = {};
};
struct Request { unsigned mission = 0, revision = 0; };

inline unsigned RankForChapter(unsigned chapter) {
    unsigned rank = 1;
    for (unsigned at : {3u,5u,7u,9u,10u,12u,13u,15u,16u,18u,19u,22u,24u,25u,27u,28u,31u,42u})
        if (at <= chapter) ++rank;
    return rank;
}
inline bool CanRequest(State const& state, Request const& request) {
    return (state.phase == First || state.phase == Automatic || state.phase == Freeflight || state.phase == Interrupted) &&
        state.completed < MissionCount && request.mission == state.completed && request.revision == state.revision;
}
inline Snapshot Get() {
    Snapshot result;
    using Fn = int (__cdecl*)(Snapshot*, unsigned);
    auto fn = reinterpret_cast<Fn>(GetProcAddress(GetModuleHandleW(nullptr), "FreelancerCampaignGetState"));
    if (fn) fn(&result, sizeof(result));
    return result;
}
inline void Publish(Snapshot const& state) {
    using Fn = void (__cdecl*)(Snapshot const*, unsigned);
    auto fn = reinterpret_cast<Fn>(GetProcAddress(GetModuleHandleW(nullptr), "FreelancerCampaignSetState"));
    if (fn) fn(&state, sizeof(state));
}
inline bool Take(Request& request) {
    using Fn = int (__cdecl*)(Request*, unsigned);
    auto fn = reinterpret_cast<Fn>(GetProcAddress(GetModuleHandleW(nullptr), "FreelancerCampaignTakeStart"));
    return fn && fn(&request, sizeof(request)) == 1;
}
inline unsigned Rank() { auto status=Get();return status.initialized && status.state.phase!=Error ? status.state.rank : 0; }
}
