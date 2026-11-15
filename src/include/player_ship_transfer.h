#pragma once
#include "player_ship_transfer_state.h"
#include "ship_cache.h"
#include "common_csys.h"

// Private in-process API, built with the same CRT as Content/Server/client.
// Never a network packet. Size/version must match before accessing its C++ fields.
namespace PlayerShipTransfer {
enum class Operation : unsigned { Poll, Prepare, Commit, Finish, Cancel, QueueReturn };
struct Packet {
    unsigned size = sizeof(Packet), version = 1;
    Operation operation = Operation::Poll;
    unsigned player = 0, system = 0, source = 0, target = 0, anchor = 0;
    unsigned base = 0; // Dock/skip-animation requests have a base but no solar watcher.
    std::uint64_t generation = 0;
    bool returning = false;
    int result = 0;
    Vector position{};
    Matrix orientation{};
    ShipCacheRecord ship;
};
using Bridge = int (__cdecl*)(Packet*);
// Content callback: 0 = authorize queued request, 1 = committed notification.
using Mission = int (__cdecl*)(Packet*, int);
}
