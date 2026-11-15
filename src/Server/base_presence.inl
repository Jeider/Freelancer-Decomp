// Included by server_chat.cpp. Sender is supplied by the authenticated RPC connection.
#include "base_presence.h"
#include <map>
#include <algorithm>
namespace {
struct FPresenceClient { DWORD last = 0; bool seen = false; };
std::map<unsigned, FPresenceClient> GPresenceClients;

void RouteBasePresence(unsigned sender, unsigned size, void const* data)
{
    if (SinglePlayer() || !Players.is_valid(sender) || !g_pChatClientInterface) return;
    BasePresence::Packet request;
    if (!BasePresence::Decode(data, size, request)) return;
    auto const& source = Players[sender];
    if (!BasePresence::SameRoom(source.current_base, source.current_location, request.base, request.room)) return;
    DWORD now = GetTickCount();
    auto& client = GPresenceClients[sender];
    if (client.seen && now - client.last < BasePresence::IntervalMs / 2) return;
    client.last = now; client.seen = true;
    // Never accept player identity, costume or name from the submitted payload.
    BasePresence::Packet state;
    state.player = sender; state.base = source.current_base; state.room = source.current_location;
    state.visible = request.visible; state.motion = request.motion;
    state.animationSerial = request.animationSerial; state.animationMs = request.animationMs;
    std::memcpy(state.position, request.position, sizeof(state.position)); state.yaw = request.yaw;
    std::memcpy(state.parts, source.costume.PartIds, sizeof(state.parts));
    std::memcpy(state.accessories, source.costume.AccessoryIds, sizeof(state.accessories));
    state.accessoryCount = (std::min)(source.costume.AccessoryCount, 8u);
    std::wstring name; pub::Player::GetName(sender, name);
    for (size_t n = 0; n < name.size() && n < 32; ++n) state.name[n] = static_cast<char16_t>(name[n]);
    for (auto* target = Players.traverse_active(nullptr); target; target = Players.traverse_active(target)) {
        unsigned id = target->client_id;
        auto capable = GPresenceClients.find(id);
        if (id == sender || capable == GPresenceClients.end() || !capable->second.seen ||
            now - capable->second.last > BasePresence::TimeoutMs ||
            !BasePresence::SameRoom(state.base, state.room, target->current_base, target->current_location)) continue;
        g_pChatClientInterface->SendCommonChatMsg(CHAT_ID(id), CHAT_ID(BasePresence::Channel), sizeof(state), &state);
    }
}
}

void Server_BasePresenceForget(unsigned player)
{
    bool known = GPresenceClients.erase(player) != 0;
    if (known && Players.is_valid(player)) {
        BasePresence::Packet hidden;
        hidden.base = Players[player].current_base;
        hidden.room = Players[player].current_location;
        RouteBasePresence(player, sizeof(hidden), &hidden);
    }
    GPresenceClients.erase(player);
}
