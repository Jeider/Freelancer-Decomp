#pragma once
#include <algorithm>
#include <cmath>
#include <map>

// Track severity, not the animated/hover colours of the rendered wireframe.
// A repaired part can trigger a fresh warning if it deteriorates again.
struct HealthDamageState
{
    std::map<unsigned, unsigned> previous, current;
    bool initialized = false;

    void Reset() { previous.clear(); current.clear(); initialized = false; }
    void Begin() { current.clear(); }
    void Sample(unsigned key, double health, bool vulnerable = false, bool destroyed = false)
    {
        unsigned band;
        if (destroyed || health <= 0) band = 4;
        else if (!std::isfinite(health))
        {
            auto old = previous.find(key);
            band = old == previous.end() ? 0 : old->second;
        }
        else if (health < 0.25) band = 3;
        else if (health <= 0.5) band = 2;
        else if (health <= 0.75) band = 1;
        else band = 0;
        current[key] = vulnerable ? (std::max)(1u, band) : band;
    }
    bool Finish()
    {
        bool worse = false;
        if (initialized)
            for (auto const& old : previous)
            {
                auto now = current.find(old.first);
                unsigned const band = now == current.end() ? 4 : now->second;
                worse |= band > old.second;
            }
        previous.swap(current);
        initialized = true;
        return worse;
    }
};

struct HealthWindowState
{
    bool open = false;
    bool locked = false;
    bool automaticOpening = false;
    void Damage()
    {
        if (!locked && !open) { open = true; automaticOpening = true; }
    }
    void ToggleOpen() { open = !open; automaticOpening = false; }
    void Opened() { automaticOpening = false; }
    // Unlocking arms future warnings; it does not replay old damage.
    void SetLocked(bool value)
    {
        locked = value;
        if (locked && automaticOpening) { open = false; automaticOpening = false; }
    }
};
