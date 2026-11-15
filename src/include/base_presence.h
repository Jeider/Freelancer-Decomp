#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>

namespace BasePresence {
// Private binary channel on the existing authenticated chat transport. Never RDL.
constexpr unsigned Channel = 0x0001ff01;
constexpr unsigned Magic = 0x31505742; // BWP1
constexpr unsigned IntervalMs = 100, TimeoutMs = 2000;
struct Packet {
    std::uint32_t magic = Magic, version = 2;
    std::uint32_t player = 0, base = 0, room = 0, visible = 0, motion = 0;
    float position[3] = {}, yaw = 0;
    std::uint32_t parts[4] = {}, accessories[8] = {}, accessoryCount = 0;
    char16_t name[33] = {};
    std::uint32_t animationSerial = 0, animationMs = 0;
};
static_assert(sizeof(Packet) == 172, "Base presence wire layout");
inline bool Decode(void const* data, unsigned size, Packet& out) {
    if (!data || size != sizeof(Packet)) return false;
    std::memcpy(&out, data, sizeof(out));
    if (out.magic != Magic || out.version != 2 || out.visible > 1 || out.motion > 7 || out.animationMs > 300000) return false;
    for (float value : out.position)
        if (!std::isfinite(value) || std::fabs(value) > 100000.f) return false;
    return std::isfinite(out.yaw) && std::fabs(out.yaw) <= 100000.f;
}
inline bool SameRoom(unsigned base, unsigned room, unsigned otherBase, unsigned otherRoom) {
    return base && room && base == otherBase && room == otherRoom;
}
}
