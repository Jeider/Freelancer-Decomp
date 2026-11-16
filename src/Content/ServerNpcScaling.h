#pragma once

#include "ContentPlayerState.h"
#include "campaign_server.h"
#include "common_server.h"
#include "port_plugins.h"

// Server-wide MatchPlayer/MatchJob policy for non-campaign multiplayer only.
namespace ServerNpcScaling {
inline bool Active()
{
    return !pub::SinglePlayer() && !CampaignServer::Enabled();
}

inline int HighestRank()
{
    int highest = 0;
    // Content states exist after character load and are removed on logout.
    // Include players on bases, in transit and in other systems, without caching
    // a slot's rank across character changes or disconnects.
    for (auto const& item : GetContentPlayerStates()) {
        if (!item.second) continue;
        int rank = 0;
        if (pub::Player::GetRank(item.first, rank) == 0 && rank > highest)
            highest = rank;
    }
    return highest;
}

inline int EncounterLevel(int authoredLevel)
{
    if (!Active() || !PORT_PLUGIN_ON("MatchPlayer")) return authoredLevel;
    int const matched = HighestRank() / 2;
    return matched > authoredLevel ? matched : authoredLevel;
}
}
