#pragma once
#include <algorithm>
// Pure policy shared by the server manager and its executable regression tests.
namespace ProximityDoor {
enum class Phase { Closed, Opening, Open, Closing };
enum class Decision { None, Open, Close, ReverseClose };
struct State {
    Phase Current = Phase::Closed;
    float EmptyTime = 0;
    bool Occupied = false;
    Decision Scan(bool insideOpen, bool insideRelease, float dt, float delay, bool finished) {
        Occupied = insideOpen || (Occupied && insideRelease);
        if (Occupied) EmptyTime = 0; else EmptyTime += dt;
        if (finished && Current == Phase::Opening) Current = Phase::Open;
        if (finished && Current == Phase::Closing) Current = Phase::Closed;
        if (Occupied && Current == Phase::Closed) { Current = Phase::Opening; return Decision::Open; }
        if (Occupied && Current == Phase::Closing) { Current = Phase::Opening; return Decision::ReverseClose; }
        if (!Occupied && Current == Phase::Open && EmptyTime >= delay) { Current = Phase::Closing; return Decision::Close; }
        return Decision::None;
    }
};
}
