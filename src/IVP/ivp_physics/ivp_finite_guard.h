#pragma once
#include <cstdint>
#include <cstring>

// Integer checks survive /fp:fast and reject both quiet/signalling NaN and infinity.
namespace IvpFinite
{
    inline bool Scalar(float value)
    {
        uint32_t bits;
        std::memcpy(&bits, &value, sizeof bits);
        return (bits & 0x7f800000u) != 0x7f800000u;
    }
    template<class V> bool Vector3(V const& v)
    { return Scalar(v.x) && Scalar(v.y) && Scalar(v.z); }

    template<class V> bool StopInvalid(V& v)
    {
        if (Vector3(v)) return false;
        v.x = v.y = v.z = 0.0f;
        return true;
    }

    // Consume an invalid impulse without poisoning the last finite velocity.
    // Reject a finite addition too if its float result overflows.
    template<class V> bool Accumulate(V& velocity, V& delta)
    {
        bool rejected = StopInvalid(velocity);
        V next = velocity;
        next.x += delta.x; next.y += delta.y; next.z += delta.z;
        if (Vector3(delta) && Vector3(next)) velocity = next;
        else rejected = true;
        delta.x = delta.y = delta.z = 0.0f;
        return rejected;
    }

    template<class H> bool HullNumbers(H const& h)
    {
        return Scalar(h.PoolKeyThreshold) && Scalar(h.AccumulatedDeltaA)
            && Scalar(h.OuterGradient) && Scalar(h.InnerGradient)
            && Scalar(h.OuterValueAtLastEdit) && Scalar(h.InnerValueAtLastEdit)
            && Scalar(h.LastEditTimeHi) && Scalar(h.LastEditTimeLo);
    }
    template<class H> bool HullEntry(H const& h)
    {
        if (!h.PoolEntries || !h.PoolCount || h.PoolCount > h.PoolCapacity
            || h.PoolLiveIndex == 0xffff || h.PoolLiveIndex >= h.PoolCapacity) return false;
        auto payload = reinterpret_cast<uintptr_t>(h.PoolEntries[h.PoolLiveIndex].Payload);
        return payload != 0 && payload != uintptr_t(-1);
    }
}
