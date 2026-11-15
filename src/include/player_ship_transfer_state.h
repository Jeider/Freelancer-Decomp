#pragma once
#include <cstdint>

// Private SP transaction protocol. A generation prevents delayed callbacks from
// completing a later transfer. No world/player mutation belongs in this class.
namespace PlayerShipTransfer {
enum class Phase { Idle, Preparing, Ready, Committed };
struct State {
    Phase phase = Phase::Idle;
    std::uint64_t generation = 0;
    unsigned player = 0, system = 0, source = 0, target = 0;

    bool begin(bool singlePlayer, unsigned owner, unsigned world, unsigned oldShip) {
        if (!singlePlayer || phase != Phase::Idle || !owner || !world || !oldShip ||
            generation == UINT64_MAX) return false;
        ++generation;
        player = owner; system = world; source = oldShip; target = 0;
        phase = Phase::Preparing;
        return true;
    }
    bool matches(std::uint64_t id, unsigned owner) const {
        return phase != Phase::Idle && id == generation && owner == player;
    }
    bool ready(std::uint64_t id, unsigned owner, unsigned newShip) {
        if (!matches(id, owner) || phase != Phase::Preparing || !newShip || newShip == source)
            return false;
        target = newShip; phase = Phase::Ready; return true;
    }
    bool commit(std::uint64_t id, unsigned owner, unsigned world, unsigned oldShip) {
        if (!matches(id, owner) || phase != Phase::Ready || world != system || oldShip != source)
            return false;
        phase = Phase::Committed; return true;
    }
    bool cancel(std::uint64_t id, unsigned owner) {
        if (!matches(id, owner) || phase == Phase::Committed) return false;
        clear(); return true;
    }
    bool finish(std::uint64_t id, unsigned owner) {
        if (!matches(id, owner) || phase != Phase::Committed) return false;
        clear(); return true;
    }
    bool blocksSave() const { return phase != Phase::Idle; }
    void resetSession() { clear(); }
private:
    void clear() {
        phase = Phase::Idle;
        player = system = source = target = 0;
        // Keep generation across cancel/finish; never recycle a transaction id.
    }
};
}
