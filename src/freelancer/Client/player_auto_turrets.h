#pragma once
#include "player_turret_rules.h"

class CEquip;
class CEGun;
struct IObjRW;
class Vector;

namespace PlayerAutoTurrets
{
    enum class Mode { Manual, Hostiles };
    enum class Status { Off, Ready, NoTurrets, NoTarget, NoScanner, Suspended, Energy, Aiming, Blocked, Firing, Multiplayer };
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
    bool Enabled();
    void Reconcile();
    void Reset();
    void Tick(float dt, bool docking);
    bool Owns(CEquip const* equip);
    bool GroupActivation(CEquip const* equip, bool active);
    bool ManualActive(CEquip const* equip);
    void ActivationChanged(CEquip const* equip, bool active);
    void SetMode(Mode mode);
    Mode GetMode();
    Status GetStatus();
    unsigned ReservePercent();
    unsigned MemberCount();
    CEGun* Member(unsigned index);
    bool Selected(unsigned index);
    void ToggleMember(unsigned index);
    // Resolve effective behavior here when equipment/perk modifiers are added.
    PlayerTurretRules::Behavior BehaviorFor(CEGun const* gun);
    void SetFocused(bool focused);
#else
    inline bool Enabled() { return false; }
    inline void Reconcile() {}
    inline void Reset() {}
    inline void Tick(float, bool) {}
    inline bool Owns(CEquip const*) { return false; }
    inline bool GroupActivation(CEquip const*, bool) { return false; }
#endif
}
