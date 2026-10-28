#pragma once
#include <cstdint>
#include <string>
class HUD_Status;
namespace PlayerTurretHud
{
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
    void Update(HUD_Status* host, float const* attachment, bool visible, float x, float y);
    void UpdateRows(HUD_Status* host);
    void Release(HUD_Status const* host);
    bool Property(HUD_Status const* host, int msg, uintptr_t control);
    bool Text(unsigned id, std::wstring& text);
#else
    inline void Update(HUD_Status*, float const*, bool, float, float) {}
    inline void UpdateRows(HUD_Status*) {}
    inline void Release(HUD_Status const*) {}
    inline bool Property(HUD_Status const*, int, uintptr_t) { return false; }
    inline bool Text(unsigned, std::wstring&) { return false; }
#endif
}
