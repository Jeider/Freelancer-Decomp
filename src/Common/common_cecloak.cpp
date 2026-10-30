// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// CECloakingDevice -- split out of common_cequip.cpp (CMN-B2).
// Declared in common_cequip.h; helpers shared with the sibling TUs are in
// common_cequip_internal.h (namespace CmnCequip).
#include "common_cequip.h"
#include "x86math.h"

#include "common_animdb.h"  // AnimDB::Add/Rem (common_animdb.cpp)

#include "common_cobject.h"
#include "common_csys.h"     // Acquire3DMathEngine (MatrixToQuaternionViaMathEngine)
#include "common_fuses.h"    // WeaponModDB_GetShieldMod (CEShield::GetWeaponModifier)
#include "common_iface.h"    // EquipStatus, EquipStatusFlag* (CEquip::GetStatus)
#include "common_ini.h"
#include "common_misc.h"     // ComputeExplosiveImpulses (CAttachedEquip::Disconnect)
#include "common_physys.h"
#include "common_spatial.h"  // ISpatialPartition (ScanList::add_in_range bucket query)
#include "common_timing.h"   // Timing::GetGlobalTime (CEShieldGenerator / CEShield)
#include "common_universe.h"
#include "DALib.h"
#include "dacom.h"
#include "../IVP/ivp_physics/ivp_real_object.h"
#include "../IVP/ivp_physics/ivp_controller.h"  // IVP_Event_Sim (do_simulation_controller)

#include <cstdarg>
#include <cstdint>
#include <math.h>
#include <new>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <algorithm>
#include <cmath>
#include <map>
#include <mutex>
#include "common_cequip_internal.h"

using namespace CmnCequip;

namespace
{
    std::recursive_mutex& StateMutex()
    {
        static auto* mutex = new std::recursive_mutex;
        return *mutex;
    }
    struct Runtime
    {
        float durationElapsed = 0, cooldown = 0, toggle = 0;
        unsigned player = 0;
        bool registered = false;
        bool remote = false;
    };
    std::map<CECloakingDevice const*, Runtime>& States()
    {
        // Common's archetype/object globals may outlive other static destructors.
        static auto* states = new std::map<CECloakingDevice const*, Runtime>;
        return *states;
    }
    std::map<unsigned, std::map<unsigned, float>>& Saved()
    {
        static auto* saved = new std::map<unsigned, std::map<unsigned, float>>;
        return *saved;
    }
    float SafeTime(float value) { return std::isfinite(value) && value > 0 ? value : 0; }
    float SaveRemaining(CECloakingDevice const& device, Runtime const& state)
    {
        auto const config = device.CloakArch()->GetSettings();
        // Loading never grants a fresh cloak charge halfway through its use.
        if (device.IsActive()) return config.cooldown + SafeTime(device.CloakArch()->CloakInTime);
        if (device.FadeTarget != device.BaselineState)
            return config.cooldown + SafeTime(device.CloakArch()->CloakInTime - device.CloakTimer);
        return (std::max)(state.cooldown, state.toggle);
    }
}

CECloakingDevice::CECloakingDevice(CEqObj* OwnerObj, unsigned short EquipId,
                                   Archetype::CloakingDevice const* ArchObj, bool bMissionFlag)
    : CAttachedEquip(EquipTypeCloak, OwnerObj, EquipId, ArchObj, bMissionFlag)
    , FadeTarget(0)
    , BaselineState(0)
{
    auto const config = ArchObj->GetSettings();
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    if (config.enabled)
    {
        States()[this] = Runtime();
        bActive = FadeTarget = BaselineState = config.defaultState ? 1 : 0;
        CloakTimer = 0;
        if (Owner) Owner->CloakPercent = config.defaultState ? 1.0f : 0.0f;
        return;
    }
    // .text:06294460-06294516: retail inlines the CAttachedEquip ctor body (the base ctor
    // above), then +0x50 = +0x51 = 0 (the pad bytes +0x52/+0x53 and the timer +0x4c are not
    // written), calls CECloakingDevice::Activate(true) directly (062944f3), and finally copies
    // Arch->CloakOutTime (+0x90) into the timer, overwriting what Activate stored.
    CECloakingDevice::Activate(true);
    CloakTimer = CloakArch()->CloakOutTime;
}

CECloakingDevice::CECloakingDevice(CECloakingDevice const& Other)
    : CAttachedEquip(Other)
    , CloakTimer(Other.CloakTimer)
    , FadeTarget(Other.FadeTarget)
    , BaselineState(Other.BaselineState)
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    auto it = States().find(&Other);
    if (it != States().end())
    {
        States()[this] = it->second;
        States()[this].registered = false;
        States()[this].player = 0;
    }
    // Common.dll.c 55259 (0x32fb0): plain field-by-field copy re-stamping the vtable at
    // each base level (CEquip::_vftable_, CExternalEquip::_vftable_, CAttachedEquip::
    // _vftable_, then this class's own) -- ordinary MSVC base-then-derived copy-ctor
    // codegen, reproduced here via CAttachedEquip(Other)'s own copy plus this level's own
    // fields. Retail only copies the first 6 of the trailing 8 bytes here (the dword at
    // +0x4c plus the two bytes at +0x50/+0x51) -- the trailing +0x52/+0x53 pad bytes are
    // left uninitialized by this ctor, so Pad52 is intentionally not copied.
}

CECloakingDevice::~CECloakingDevice()
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    auto it = States().find(this);
    if (it != States().end())
    {
        if (it->second.player) Saved()[it->second.player][Arch->get_id()] = SaveRemaining(*this, it->second);
        States().erase(it);
    }
    // Common.dll.c 56458 (0x34520): retail force-calls the non-virtual CExternalEquip::
    // Destroy() here (bDestroyed=1 + EquipDestroying notify, then Disconnect()) as a safety
    // net during unwind -- same "Destroy() force-call" pattern as CEPower/CEAttachedFX/
    // CERepairDroid/CEInternalFX's destructors in this file. The Debris/Attachment/Arch
    // cleanup that follows in the decompilation is identical to ~CAttachedEquip()'s body
    // and runs automatically as that base destructor executes after this one returns.
    CExternalEquip::Destroy();
}

bool CECloakingDevice::Update(float Dt, unsigned Flags)
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    auto const config = CloakArch()->GetSettings();
    if (config.enabled)
    {
        auto& state = States()[this];
        float remaining = SafeTime(Dt);
        if (IsDestroyed() || IsDisabled())
        {
            if (IsActive() || FadeTarget || BaselineState)
            {
                CEquip::Activate(false);
                FadeTarget = BaselineState = 0;
                CloakTimer = 0;
                state.cooldown = config.cooldown;
            }
        }
        // Consume time at state boundaries, including a long frame crossing the
        // fade, expiry and recharge. Timers only advance through this one update.
        for (int boundary = 0; boundary < 4; ++boundary)
        {
            if (FadeTarget != BaselineState)
            {
                float total = SafeTime(FadeTarget ? CloakArch()->CloakOutTime : CloakArch()->CloakInTime);
                float step = (std::min)(remaining, (std::max)(0.0f, total - CloakTimer));
                CloakTimer += step; remaining -= step;
                state.toggle = (std::max)(0.0f, state.toggle - step);
                if (CloakTimer < total) break;
                BaselineState = FadeTarget; CloakTimer = 0;
                state.durationElapsed = 0;
                if (!FadeTarget) state.cooldown = config.cooldown;
            }
            else if (IsActive())
            {
                if (config.duration < 0)
                {
                    state.toggle = (std::max)(0.0f, state.toggle - remaining);
                    break;
                }
                float step = (std::min)(remaining, (std::max)(0.0f, config.duration - state.durationElapsed));
                state.durationElapsed += step; remaining -= step;
                state.toggle = (std::max)(0.0f, state.toggle - step);
                if (state.durationElapsed < config.duration) break;
                // MP replicas await the authoritative off packet. Expiring a
                // predicted cloak early could make periodic on packets flicker it.
                if (state.remote && !state.registered) break;
                ChangeState(false); // Expiry bypasses the manual toggle interval.
            }
            else
            {
                state.cooldown = (std::max)(0.0f, state.cooldown - remaining);
                state.toggle = (std::max)(0.0f, state.toggle - remaining);
                break;
            }
        }
        if (Owner) Owner->CloakPercent = IsDestroyed() ? 0 : static_cast<float>(cloak_percent());
        if (IsDestroyed() && Debris) return true;
        return CExternalEquip::Update(Dt, Flags);
    }
    // .text:06294660-0629476c.
    //  - vt+8 IsDestroyed false and FadeTarget != BaselineState: Total = FadeTarget ? Arch+0x90
    //    (CloakOutTime) : Arch+0x8c (CloakInTime); FLD Dt; FADD timer; FST float timer -- the
    //    compare (FCOMP vs Total, TEST AH,0x41 / JNZ) uses the unrounded sum: only a strictly
    //    greater, ordered sum settles the fade (BaselineState = FadeTarget, timer = 0).
    //  - Owner non-null: Owner+0x140 = the inlined cloak_percent() body, one FSTP float.
    //  - Tail: vt+8 IsDestroyed and Debris (+0x2c) -> true; else CExternalEquip::Update.
    if (!IsDestroyed() && FadeTarget != BaselineState)
    {
        Archetype::CloakingDevice const* CloakingArch = CloakArch();
        float const Total = (FadeTarget != 0) ? CloakingArch->CloakOutTime : CloakingArch->CloakInTime;
        double const Elapsed = (double)Dt + (double)CloakTimer;
        CloakTimer = (float)Elapsed;
        if (Elapsed > Total)
        {
            BaselineState = FadeTarget;
            CloakTimer = 0.0f;
        }
        if (Owner != nullptr)
            Owner->CloakPercent = (float)cloak_percent();
    }
    if (IsDestroyed() && Debris != nullptr)
        return true;
    return CExternalEquip::Update(Dt, Flags);
}

bool CECloakingDevice::Activate(bool bActive)
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    // .text:06294770-06294852.
    //  - vt+4 IsActive() == bActive -> return bActive.
    //  - Result = CEquip::Activate(bActive) (direct); New = CEquip::bActive (+0x10).
    //  - FadeTarget == New -> return Result. FadeTarget == BaselineState -> FadeTarget = New,
    //    timer = 0, return Result.
    //  - Mid-fade: Frac = the inlined cloak_percent() fade branch, kept on the FPU stack;
    //    old FadeTarget != 0 -> timer = (1 - Frac) * CloakInTime (+0x8c), else
    //    timer = Frac * CloakOutTime (+0x90); one FSTP float; FadeTarget = New.
    if (IsActive() == bActive)
        return bActive;

    if (CloakArch()->GetSettings().enabled)
    {
        if (!CanToggle()) return IsActive();
        ChangeState(bActive);
        return IsActive();
    }

    bool const Result = CEquip::Activate(bActive);
    unsigned char const NewFadeTarget = this->bActive; // CEquip::bActive, post-toggle
    unsigned char const OldFadeTarget = FadeTarget;
    if (OldFadeTarget == NewFadeTarget)
        return Result;
    if (OldFadeTarget == BaselineState)
    {
        FadeTarget = NewFadeTarget;
        CloakTimer = 0.0f;
        return Result;
    }
    Archetype::CloakingDevice const* CloakingArch = CloakArch();
    double const Frac = cloak_percent();
    if (OldFadeTarget != 0)
        CloakTimer = (float)((1.0 - Frac) * (double)CloakingArch->CloakInTime);
    else
        CloakTimer = (float)(Frac * (double)CloakingArch->CloakOutTime);
    FadeTarget = NewFadeTarget;
    return Result;
}

bool CECloakingDevice::CanToggle() const
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    if (IsDestroyed() || IsDisabled()) return false;
    if (!CloakArch()->GetSettings().enabled) return true;
    if (FadeTarget != BaselineState) return false;
    auto it = States().find(this);
    return it == States().end() || (it->second.toggle <= 0 && (IsActive() || it->second.cooldown <= 0));
}

void CECloakingDevice::ApplyRemoteState(bool active)
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    States()[this].remote = true;
    ChangeState(active);
}

void CECloakingDevice::ChangeState(bool active)
{
    if (!CloakArch()->GetSettings().enabled) { Activate(active); return; }
    if (IsActive() == active || (active && IsDestroyed())) return;
    float fraction = static_cast<float>((std::max)(0.0, (std::min)(1.0, cloak_percent())));
    CEquip::Activate(active);
    FadeTarget = active ? 1 : 0;
    BaselineState = active ? 0 : 1;
    CloakTimer = (active ? fraction : 1 - fraction) *
        SafeTime(active ? CloakArch()->CloakOutTime : CloakArch()->CloakInTime);
    auto& state = States()[this];
    state.toggle = CloakArch()->GetSettings().toggleCooldown;
    state.durationElapsed = 0;
}

float CECloakingDevice::GetCooldownRemaining() const
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    auto it = States().find(this);
    return it == States().end() ? 0 : it->second.cooldown;
}

float CECloakingDevice::GetDurationRemaining() const
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    float total = CloakArch()->GetSettings().duration;
    if (total < 0) return -1;
    auto it = States().find(this);
    return (std::max)(0.0f, total - (it == States().end() ? 0 : it->second.durationElapsed));
}

void CECloakingDevice::RegisterServerState()
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    if (!CloakArch()->GetSettings().enabled) return;
    auto& state = States()[this];
    if (state.registered) return;
    state.registered = true;
    state.player = Owner ? Owner->OwnerPlayer : 0;
    if (state.player)
    {
        auto player = Saved().find(state.player);
        if (player != Saved().end())
        {
            auto item = player->second.find(Arch->get_id());
            if (item != player->second.end() && item->second > 0)
            {
                state.cooldown = item->second;
                bActive = FadeTarget = BaselineState = 0;
                CloakTimer = 0;
                Owner->CloakPercent = 0;
            }
        }
    }
}

std::map<unsigned, float> CECloakingDevice::SavedCooldowns(unsigned player)
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    auto result = Saved()[player];
    for (auto const& item : States())
        if (item.second.registered && item.second.player == player && player)
            result[item.first->Arch->get_id()] = SaveRemaining(*item.first, item.second);
    return result;
}

void CECloakingDevice::LoadCooldowns(unsigned player, std::map<unsigned, float> const& values)
{
    std::lock_guard<std::recursive_mutex> lock(StateMutex());
    // Detach stale objects before a character switch/disconnect can destroy them.
    for (auto& item : States()) if (item.second.player == player) item.second.player = 0;
    Saved()[player].clear();
    for (auto const& item : values)
        if (item.first && SafeTime(item.second) > 0) Saved()[player][item.first] = item.second;
}

double CECloakingDevice::cloak_percent() const
{
    // .text:062945d0-06294653. Settled (FadeTarget == BaselineState): BaselineState ? 1.0f
    // : 0.0f. Fading in (FadeTarget != 0): CloakOutTime (+0x90) FCOMP the double 0.001
    // (.rdata:0639c9f0), TEST AH,0x41 / JNZ: not greater or unordered -> 1.0f, else
    // timer / CloakOutTime. Fading out: 0.0 or timer / CloakInTime (+0x8c) by the same test,
    // then FSUBR the double 1.0 (.rdata:06399410). The result is left unrounded in ST0.
    if (FadeTarget == BaselineState)
        return (BaselineState != 0) ? 1.0f : 0.0f;
    Archetype::CloakingDevice const* CloakingArch = CloakArch();
    if (FadeTarget != 0)
    {
        if (CloakingArch->CloakOutTime > 0.001)
            return (double)CloakTimer / (double)CloakingArch->CloakOutTime;
        return 1.0f;
    }
    double Frac = 0.0f;
    if (CloakingArch->CloakInTime > 0.001)
        Frac = (double)CloakTimer / (double)CloakingArch->CloakInTime;
    return 1.0 - Frac;
}

Archetype::CloakingDevice const* CECloakingDevice::CloakArch() const
{
    return (Archetype::CloakingDevice const*)(Arch);
}

CECloakingDevice* __cdecl CECloakingDevice::cast(CEquip* Equip)
{
    // Listing 0x34860: null-check, then Type == 0x1000.
    if (Equip == nullptr || Equip->GetType() != EquipTypeCloak)
        return nullptr;
    return (CECloakingDevice*)(Equip);
}

CECloakingDevice const* __cdecl CECloakingDevice::cast(CEquip const* Equip)
{
    return cast(const_cast<CEquip*>(Equip));
}
