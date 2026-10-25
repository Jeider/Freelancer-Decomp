// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: the wing animation system. See wing_anim.h.

#include "wing_anim.h"

#ifdef FREELANCER_MOD_PLUGINS

#include "player_behavior.h"     // GetPlayerEngineCruiseActive, GetPlayerObjRW
#include "port_plugins.h"

#include "DALib.h"
#include "common_animdb.h"
#include "common_cobject.h"
#include "common_iface.h"
#include "common_mod_plugins_api.h"
#include "engine/engbase.h"

#include <windows.h>

namespace
{
    enum class EWing
    {
        None,      // no wing on this ship
        Launching, // the one-shot launch script is running
        Extended,
        Folding,
        Folded,
        Extending,
    };

    // A request made while the wing moves waits here and runs when the move ends (the last
    // request wins; one that the move already satisfies is dropped).
    enum class EPending
    {
        None,
        Fold,
        Extend,
    };

    CEqObj* G_Ship = nullptr;
    EWing G_State = EWing::None;
    EPending G_Pending = EPending::None;
    bool G_bCruiseLast = false;
    bool G_bDockFolded = false;
    enum class EManual { None, Toggle, Pause, Resume };
    EManual G_Manual = EManual::None;
    bool G_bPaused = false;
    bool G_bCruiseLocked = false;
    bool G_bPendingCruise = false;
    int G_PausedHandle = -1;

    char const* WingScript()
    {
        static char S_Script[64] = {};
        if (S_Script[0] == '\0')
            PortConfigString("WingAnim", "script", "Sc_extend wing", S_Script, sizeof(S_Script));
        return S_Script;
    }

    CEqObj* PlayerShip()
    {
        // The chain space_state.cpp's PlayerShipEqObj walks: the player IObjRW's +0x10 object,
        // a ship (class mask 0x503).
        void* const ObjRW = GetPlayerObjRW();
        if (ObjRW == nullptr)
            return nullptr;
        CEqObj* const Ship = *reinterpret_cast<CEqObj**>(static_cast<unsigned char*>(ObjRW) + 0x10);
        if (Ship == nullptr || (static_cast<unsigned>(Ship->ObjectClass) & 0x503u) != 0x503u)
            return nullptr;
        return Ship;
    }

    void Play(int Handle, unsigned long bReverse)
    {
        // EvalPlayback(handle, 0 forward / 1 reverse, -2 = from the current time, speed 1),
        // as CShip's bay doors (close_bay 062b2c4b).
        DALib::Anim->EvalPlayback(static_cast<unsigned long>(Handle), bReverse, -2.0f, 1.0f, nullptr,
                                  AsOpaqueDword(1.0f), AsOpaqueDword(1.0f), nullptr);
        AnimDB::Add(Handle);
    }

    bool IsMoving()
    {
        return G_State == EWing::Launching || G_State == EWing::Folding || G_State == EWing::Extending;
    }

    bool Resume()
    {
        if (!G_bPaused) return false;
        int const handle = ModShipOneShotAnim(G_Ship);
        if (handle == -1 || handle != G_PausedHandle) return false;
        // StopPlayback retains each channel's time. -2 continues those times,
        // including the launch script; only Extending plays in reverse.
        Play(handle, G_State == EWing::Extending ? 1 : 0);
        G_bPaused = false;
        G_PausedHandle = -1;
        return true;
    }

    void RequestFold(bool fromCruise = false)
    {
        Resume();
        if (IsMoving())
        {
            G_Pending = EPending::Fold;
            G_bPendingCruise = fromCruise;
            return;
        }
        if (G_State != EWing::Extended)
            return;
        int const Handle = ModShipOneShotAnim(G_Ship);
        if (Handle == -1)
            return;
        Play(Handle, 0);
        G_State = EWing::Folding;
    }

    void RequestExtend(bool fromCruise = false)
    {
        Resume();
        if (IsMoving())
        {
            G_Pending = EPending::Extend;
            G_bPendingCruise = fromCruise;
            return;
        }
        if (G_State != EWing::Folded)
            return;
        int const Handle = ModShipOneShotAnim(G_Ship);
        if (Handle == -1)
            return;
        Play(Handle, 1);
        G_State = EWing::Extending;
    }

    // After a move ends: the waiting request, unless the wing is already where it asked.
    void RunPending()
    {
        EPending const Pending = G_Pending;
        G_Pending = EPending::None;
        G_bPendingCruise = false;
        if (Pending == EPending::Fold)
            RequestFold();
        else if (Pending == EPending::Extend)
            RequestExtend();
    }

    bool IsDockingWithBase(CEqObj* Ship)
    {
        IBehaviorManager* const Behavior = Ship->get_behavior_interface();
        if (Behavior == nullptr)
            return false;
        IObjRW const* Port = nullptr;
        int PortIndex = 0;
        if (!Behavior->get_docking_port(Port, PortIndex) || Port == nullptr)
            return false;
        unsigned Type = 0;
        Port->get_type(Type);
        // TRADELANE_RING 0x80, JUMP_GATE 0x40, AIRLOCK_GATE 0x400, JUMP_HOLE 0x800: no fold.
        return (Type & (0x80u | 0x40u | 0x400u | 0x800u)) == 0;
    }
}

void WingAnimTick()
{
    if (!PORT_PLUGIN_ON("WingAnim"))
        return;
    CEqObj* const Ship = PlayerShip();
    if (Ship != G_Ship)
    {
        // A new ship (launch, respawn): its one-shot InternalFX, when it has one, is running.
        G_Ship = Ship;
        G_State = (Ship != nullptr && ModShipOneShotAnim(Ship) != -1) ? EWing::Launching : EWing::None;
        G_bCruiseLast = Ship != nullptr && GetPlayerEngineCruiseActive();
        G_bDockFolded = false;
        G_Manual = EManual::None;
        G_bPaused = false;
        G_PausedHandle = -1;
        G_bCruiseLocked = false;
        G_bPendingCruise = false;
        G_Pending = EPending::None;
        return;
    }
    if (Ship == nullptr || G_State == EWing::None)
    {
        G_Manual = EManual::None;
        return;
    }
    int const Handle = ModShipOneShotAnim(Ship);
    if (Handle == -1)
    {
        G_State = EWing::None;
        G_bPaused = false;
        G_PausedHandle = -1;
        G_Manual = EManual::None;
        G_Pending = EPending::None;
        return;
    }

    // Finished transitions: forward ends at the script's duration, reverse at 0.
    float const Current = DALib::Anim->GetStoredDuration(static_cast<unsigned long>(Handle));
    float const Total = DALib::Anim->GetScriptDuration(reinterpret_cast<void*>(static_cast<intptr_t>(Handle)));
    if (!G_bPaused) switch (G_State)
    {
    case EWing::Launching:
        if (!(Current < Total))
        {
            // The launch script has extended the wing: the wing script takes the slot, held at
            // its start (reverse from time 0 ends at once), which is the extended pose.
            int const Wing = ModSwapShipOneShotAnim(Ship, WingScript());
            if (Wing == -1)
            {
                G_State = EWing::None;
                return;
            }
            DALib::Anim->EvalPlayback(static_cast<unsigned long>(Wing), 1, 0.0f, 1.0f, nullptr,
                                      AsOpaqueDword(1.0f), AsOpaqueDword(1.0f), nullptr);
            AnimDB::Add(Wing);
            G_State = EWing::Extended;
            RunPending();
        }
        break;
    case EWing::Folding:
        if (!(Current < Total))
        {
            G_State = EWing::Folded;
            RunPending();
        }
        break;
    case EWing::Extending:
        if (!(Current > 0.0f))
        {
            G_State = EWing::Extended;
            RunPending();
        }
        break;
    default:
        break;
    }

    // Cruise: fold when it engages, extend when it stops.
    bool const bCruise = GetPlayerEngineCruiseActive();
    if (bCruise != G_bCruiseLast)
    {
        G_bCruiseLast = bCruise;
        // Track changes even while locked: unlocking does not replay old events.
        if (!G_bCruiseLocked)
        {
            if (bCruise) RequestFold(true);
            else RequestExtend(true);
        }
    }

    // Docking with a base: fold once.
    if (IsDockingWithBase(Ship))
    {
        if (!G_bDockFolded)
        {
            G_bDockFolded = true;
            RequestFold();
        }
    }
    else
        G_bDockFolded = false;

    // Both the key and Health use this command path. A Resume captured while
    // paused must not toggle direction if an automatic event resumed it first.
    EManual const command = G_Manual;
    G_Manual = EManual::None;
    if (command == EManual::Pause && IsMoving() && !G_bPaused)
    {
        int const currentHandle = ModShipOneShotAnim(Ship);
        if (currentHandle != -1)
        {
            DALib::Anim->StopPlayback(static_cast<unsigned long>(currentHandle));
            G_bPaused = true;
            G_PausedHandle = currentHandle;
        }
    }
    else if (command == EManual::Resume || (command == EManual::Toggle && G_bPaused))
    {
        Resume();
    }
    else if (command == EManual::Toggle)
    {
        bool bWillBeFolded;
        if (G_Pending != EPending::None)
            bWillBeFolded = G_Pending == EPending::Fold;
        else
            bWillBeFolded = G_State == EWing::Folded || G_State == EWing::Folding;
        if (bWillBeFolded)
            RequestExtend();
        else
            RequestFold();
    }
}

bool WingAnimHandleKey(unsigned Message, unsigned Wparam)
{
    if (Message != WM_KEYDOWN || !PORT_PLUGIN_ON("WingAnim"))
        return false;
    // [WingAnim] key = a virtual-key code (0 = none), modifiers = 1 Shift | 2 Ctrl | 4 Alt.
    static int const S_Key = PortConfigInt("WingAnim", "key", 0);
    static int const S_Modifiers = PortConfigInt("WingAnim", "modifiers", 0);
    if (S_Key == 0 || static_cast<int>(Wparam) != S_Key)
        return false;
    int const Held = ((GetKeyState(VK_SHIFT) & 0x8000) ? 1 : 0) | ((GetKeyState(VK_CONTROL) & 0x8000) ? 2 : 0) |
                     ((GetKeyState(VK_MENU) & 0x8000) ? 4 : 0);
    if (Held != S_Modifiers || G_State == EWing::None)
        return false;
    return WingAnimRequestToggle();
}

bool WingAnimAvailable()
{
    return PORT_PLUGIN_ON("WingAnim") && G_Ship && PlayerShip() == G_Ship &&
        G_State != EWing::None && ModShipOneShotAnim(G_Ship) != -1;
}

bool WingAnimPaused() { return WingAnimAvailable() && G_bPaused; }
bool WingAnimCanPause() { return WingAnimAvailable() && IsMoving(); }
bool WingAnimCruiseLocked() { return WingAnimAvailable() && G_bCruiseLocked; }

bool WingAnimRequestToggle()
{
    if (!WingAnimAvailable()) return false;
    G_Manual = G_bPaused ? EManual::Resume : EManual::Toggle;
    return true;
}

bool WingAnimTogglePause()
{
    if (!WingAnimCanPause()) return false;
    G_Manual = G_bPaused ? EManual::Resume : EManual::Pause;
    return true;
}

void WingAnimSetCruiseLocked(bool locked)
{
    if (!WingAnimAvailable()) return;
    G_bCruiseLocked = locked;
    if (locked && G_bPendingCruise)
    {
        G_Pending = EPending::None;
        G_bPendingCruise = false;
    }
}

int WingAnimDisplayState()
{
    switch (G_State)
    {
    case EWing::None:
        return 0;
    case EWing::Folded:
        return 1;
    case EWing::Extended:
        return 3;
    default:
        return 2;
    }
}

#endif
