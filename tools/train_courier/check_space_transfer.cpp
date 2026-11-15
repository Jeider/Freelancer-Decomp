#include "player_ship_transfer_state.h"
#include "common_misc.h"
#include "common_net.h"
#include <windows.h>
#include <cassert>
#include <cstdio>

int main(int argc, char** argv) {
    using namespace PlayerShipTransfer;
    State state;
    assert(!state.begin(false, 1, 2, 3));
    assert(!state.blocksSave() && state.generation == 0);
    for (unsigned failure = 0; failure != 3; ++failure) {
        assert(state.begin(true, 1, 2, 3));
        auto generation = state.generation;
        assert(state.blocksSave());
        assert(!state.begin(true, 1, 2, 3));
        assert(!state.ready(generation - 1, 1, 4));
        assert(!state.ready(generation, 2, 4));
        assert(!state.ready(generation, 1, 3));
        assert(!state.finish(generation, 1));
        if (failure > 0) {
            assert(state.ready(generation, 1, 4));
            assert(!state.commit(generation, 1, 5, 3)); // system changed
            assert(!state.commit(generation, 1, 2, 6)); // death/another ship
        }
        assert(state.cancel(generation, 1));
        assert(!state.blocksSave());
        assert(!state.commit(generation, 1, 2, 3));
    }
    for (unsigned i = 0; i != 10000; ++i) {
        assert(state.begin(true, 1, 2, 3));
        auto generation = state.generation;
        assert(state.ready(generation, 1, 4));
        assert(state.commit(generation, 1, 2, 3));
        assert(!state.cancel(generation, 1));
        assert(!state.commit(generation, 1, 2, 3));
        assert(state.finish(generation, 1));
        assert(!state.finish(generation, 1));
        assert(!state.blocksSave());
    }
    state.generation = UINT64_MAX;
    assert(!state.begin(true, 1, 2, 3));
    assert(!state.blocksSave());
    State session;
    assert(session.begin(true, 1, 2, 3));
    auto oldGeneration = session.generation;
    session.resetSession();
    assert(session.begin(true, 1, 2, 3));
    assert(!session.ready(oldGeneration, 1, 4));
    std::puts("PASS transaction: cancellation, stale callbacks, identity, repeated commit, generation exhaustion");

    if (argc != 2) return 2;
    HMODULE server = LoadLibraryA(argv[1]);
    if (!server) { std::printf("LoadLibrary error %lu\n", GetLastError()); return 3; }
    auto bridge = reinterpret_cast<int (__cdecl*)(void*)>(GetProcAddress(server, "PlayerShipTransferBridge"));
    assert(bridge);
    // Use an intentionally inaccessible packet: mode isolation must precede
    // even reading its size, never mind changing player/world state.
    void* invalidPacket = reinterpret_cast<void*>(1);
    SetMultiPlayer(true);
    SetIsMPServer(false);
    assert(bridge(invalidPacket) == 0);
    SetIsMPServer(true);
    assert(bridge(invalidPacket) == 0);
    SetIsMPServer(false);
    SetMultiPlayer(false);
    assert(bridge(nullptr) == 0);
    std::puts("PASS actual Server.dll: MP client/server reject before packet access; SP null packet rejected");
    FreeLibrary(server);
}
