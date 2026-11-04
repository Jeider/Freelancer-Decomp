// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// FUN_005792b0 and the option-table scatter loop at 0x005621c0 (inside FUN_005621a0).

#include "game_options.h"
#include "globals.h"
#include "login_mgr.h"    // G_Server (DAT_0067ecd0)
#include "player_spawn.h" // GetPlayerConnectionId (DAT_00673344)

#include "common_server.h" // IServer::SetInterfaceState (slot 77)

#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <windows.h>
#include "common_misc.h"
#include "dacom.h"

// The values themselves live in the options object: DisplaySettings::options (globals.h), .data
// 0x00679be8 = 0x00679bc0 + 0x28. FUN_005621a0 (LoadStartupConfig) scatters the table below into
// it before anything reads an option.

// The descriptor table at .data 0x006143b8, transcribed row for row. Rows are in the order the
// options menu would have listed them, which is NOT index order -- see the two comments below,
// both of which are retail's own quirks and are reproduced deliberately.
const FGameOptionDesc GGameOptionDescs[] =
{
    {0x00, "[OUTLINES]",                        0, 0},
    {0x01, "PHYS WIRES",                        0, 1},
    {0x02, "PHYS SPHERES",                      0, 1},
    {0x03, "SHIELDS",                           0, 1},
    {0x04, "PHANTOMS",                          0, 1},
    {0x05, "HOTSPOTS",                          0, 1},

    {0x06, "[INTERFACE]",                       1, 0},
    {0x07, "BUTTONS",                           0, 1},
    {0x08, "TEXT",                              1, 1},
    {0x09, "NEURONET",                          2, 1},
    {0x0a, "HUD",                               1, 1},
    {0x0c, "TARGET WINDOW LOCK",                0, 1},
    {0x0d, "AUTO OPEN TARGET WINDOW",           1, 1},
    {0x0e, "DRAW MOUSE",                        1, 1},
    {0x0f, "DISPLAY SHIP IDS",                  0, 1},
    {0x10, "DISPLAY INTERFACE TIMING",          0, 1},
    {0x11, "DISPLAY PLAYER STATS",              0, 1},
    {0x12, "SWITCHING TARGETS CLEARS MANEUVER", 1, 1},

    // Out of sequence in retail: index 0x0b sits here, after 0x12, not up with the other
    // interface toggles. Row order is menu order.
    {0x0b, "SHIP WIRES",                        1, 1},

    {0x13, "DRAW TEXT CONTROLS",                1, 1},
    {0x14, "DRAW BUTTON CONTROLS",              1, 1},
    {0x15, "DRAW STATIC CONTROLS",              1, 1},
    {0x16, "DRAW SCROLL BAR CONTROLS",          1, 1},
    {0x17, "INVERSE MOUSE",                     0, 1},

    // Not bracketed, yet flagged like a category header rather than a toggle. Retail's own
    // inconsistency; nothing reads the flag, so it changes nothing.
    {0x18, "LIGHTING",                          2, 0},

    {0x19, "[BACKGROUND]",                      1, 0},
    {0x1a, "STARS",                             1, 1},

    {0x1b, "[OBJECTS]",                         1, 0},
    {0x1c, "CHARACTERS",                        1, 1},
    {0x1d, "SHIPS",                             1, 1},
    {0x1e, "PROJECTILES",                       1, 1},
    {0x1f, "DEBRIS",                            1, 1},
    {0x20, "SOLAR",                             1, 1},
    {0x21, "ASTEROIDS",                         1, 1},
    {0x22, "DYN_ASTEROIDS",                     1, 1},
    {0x23, "PLANETS",                           1, 1},
    {0x24, "SUN",                               1, 1},

    {0x25, "[EFFECTS]",                         1, 0},
    {0x26, "PARTICLES",                         1, 1},
    {0x27, "NEBULA",                            1, 1},
    {0x28, "SUN_EFFECTS",                       1, 1},
    {0x29, "FLASHLIGHTS",                       1, 1},
    {0x2a, "TRADE_LANES",                       1, 1},
    {0x2b, "SHADOWS",                           1, 1},
    {0x2c, "ASTEROID_EXT",                      2, 1},

    {0x2d, "[AUDIO]",                           1, 0},

    // Retail really does list index 0x2f twice, here and three rows down, with 0x2e wedged
    // between them. Whatever this row was meant to be, both copies write the same 0, so the
    // duplicate is invisible at runtime -- but it is why the table has 71 rows for 70 options.
    {0x2f, "VOL_VOICE",                         0, 1},
    {0x2e, "VOL_MUSIC",                         0, 1},
    {0x2f, "VOL_VOICE",                         0, 1},

    {0x30, "VOL_SFX",                           0, 1},
    {0x31, "VOL_INTERFACE",                     0, 1},
    {0x32, "VOL_AMBIENCE",                      0, 1},
    {0x33, "VOICE PROFILE OFFSET",              0, 1},
    {0x34, "PITCH_BEND_SOUNDS",                 1, 1},

    {0x35, "[PLAYER]",                          0, 0},
    {0x36, "AUTO_AIM",                          0, 1},
    {0x37, "DISABLE_COLLIDE",                   0, 1},
    {0x38, "SURFACE_HIT_EFFECTS",               1, 1},
    {0x39, "SPLASH_HIT_EFFECTS",                0, 1},

    {0x3a, "[MISC]",                            0, 0},
    {0x3b, "AMBIENT",                           0, 1},
    {0x3c, "DETAIL_LEVELS",                     0, 1},
    {0x3d, "CHAR_PLACES",                       0, 1},
    {0x3e, "LIKE_PETAL",                        0, 1},
    {0x3f, "LIGHTS_DEBUG",                      0, 1},
    {0x40, "ALCHEMY_LOD",                       1, 1},
    {0x41, "COMM_LOG",                          0, 1},

    {0x42, "[ALCHEMY_DEBUG]",                   1, 0},
    {0x43, "BATCH_PARTICLES",                   0, 1},
    {0x44, "USE_DYN_VB",                        1, 1},
    {0x45, "COPY_TO_DYN_VB",                    1, 1},
};

const int GGameOptionDescCount = static_cast<int>(sizeof(GGameOptionDescs) / sizeof(GGameOptionDescs[0]));

// Retail's loop bound is a byte count: `while (Off < 0x470)` over 0x10-byte records, so exactly
// 0x470 / 0x10 = 71 rows. If this ever fires, a row was lost or gained in transcription.
static_assert(sizeof(GGameOptionDescs) / sizeof(GGameOptionDescs[0]) == 0x470 / 0x10,
              "the option descriptor table must have 71 rows, as retail's 0x470 byte span does");

// FUN_005792b0 (.text:005792b0-005792c3): `CMP EAX,0x46; JGE -> return 0; MOV EAX,[EAX*4 +
// 0x00679be8]`. The compare is signed, so a negative index reads the options-object fields in
// front of the array, exactly as retail does. No caller in the PE passes one.
int GetGameOption(int Index)
{
    if (Index >= kGameOptCount)
        return 0;

    const int* const Values = reinterpret_cast<const int*>(&g_display) + 10;
    return Values[Index];
}

char const* GetGameOptionName(int Index)
{
    for (int Row = 0; Row < GGameOptionDescCount; ++Row)
    {
        if (GGameOptionDescs[Row].Index == Index)
            return GGameOptionDescs[Row].Name;
    }

    return nullptr;
}

namespace
{
    // .data:00612274. See the header's "Session/game-mode flags word" section. Its initialised
    // value in the PE is 3 (masks 1 and 2 set). Only native flags remain in saves.
    unsigned GSessionFlags = 3;

    // Port-only: bits 0..3 retain their native HUD meanings. Bits 4..5 store
    // Targeting's Vanilla/Fit/Top/Side choice in the global profile (legacy bit encoding).
    constexpr unsigned TargetingProjectionShift = 4;
    constexpr unsigned TargetingProjectionMask = 3u << TargetingProjectionShift;
    // Inverted autoselect bit gives legacy/new saves the enabled default.
    constexpr unsigned TargetingAutoselectOff = 1u << 6;
    constexpr unsigned TargetingWindowLocked = 1u << 7;
    constexpr unsigned HealthWindowLocked = 1u << 8;
    constexpr unsigned HealthWindowClosed = 1u << 9;
    constexpr unsigned HealthViewLeft = 1u << 10;
    constexpr unsigned TargetingWindowClosed = 1u << 11;
    constexpr unsigned WeaponGroupShift = 12;
    constexpr unsigned WeaponGroupMask = 7u << WeaponGroupShift;
    constexpr unsigned HealthVisibilitySaved = 1u << 15;
    constexpr unsigned TargetingVisibilitySaved = 1u << 16;
    constexpr unsigned RadarEnabled = 1u << 17; // New/legacy saves default to off.
    constexpr unsigned RadarRangeShift = 18;
    constexpr unsigned RadarRangeMask = 3u << RadarRangeShift; // 0 unset; 1..3 range index + 1.
    constexpr unsigned RadarAutoMask = 3u << 20;
    constexpr unsigned RadarTopView = 1u << 30;
    constexpr unsigned AutoTurretsOff = 1u << 22;
    constexpr unsigned AutoTurretsSaved = 1u << 23;
    constexpr unsigned AutoTurretReserveMask = 31u << 24; // 0 unset, 1..19 = 0..90%.
    unsigned GSessionLoadRevision = 0;
    constexpr unsigned HudPreferencesMask = 0xfffffff0u;
    constexpr unsigned WeaponGroupsHidden = 1u << 29;
    constexpr unsigned WingCruiseAnimationOff = 1u << 31;
    unsigned GHudPreferences = 0;
    bool GHudLoaded = false, GHudStored = false, GHudSaveOk = true;
    char GHudPath[MAX_PATH] = {};

    unsigned HudPreferencesFlags()
    {
        if (!GHudLoaded && GetUserDataPath(GHudPath))
        {
            GHudLoaded = true;
            strcat_s(GHudPath, "\\hud_preferences.ini");
            char text[32] = {};
            GetPrivateProfileStringA("HUD", "flags", "", text, sizeof(text), GHudPath);
            char* end = nullptr;
            unsigned long const flags = std::strtoul(text, &end, 10);
            GHudStored = text[0] && end && !*end;
            if (GHudStored) GHudPreferences = flags & HudPreferencesMask;
        }
        return GHudPreferences;
    }

    void SaveHudPreferences(unsigned flags)
    {
        HudPreferencesFlags();
        char text[32]; sprintf_s(text, "%u", flags & HudPreferencesMask);
        GHudSaveOk = GHudLoaded && WritePrivateProfileStringA("HUD", "flags", text, GHudPath);
        if (GHudSaveOk) { GHudPreferences = flags & HudPreferencesMask; GHudStored = true; }
        else FDUMP(0x100001, "HUD: could not save global preferences (%lu)\n", GetLastError());
    }
}

static void SetGameSessionFlagValue(unsigned Mask, unsigned Value)
{
    if (Mask & HudPreferencesMask)
    {
        unsigned const old = HudPreferencesFlags();
        unsigned const next = (old & ~Mask) | (Value & Mask);
        if (!GHudStored || next != old) SaveHudPreferences(next);
        else GHudSaveOk = true;
        return;
    }
    Mask &= 0xfu;
    GSessionFlags = (GSessionFlags & ~Mask) | (Value & Mask);

    // 0x004c815a..0x004c817e: the new word in the first dword of a 0x80-byte local, sent with
    // IServer slot 77 (+0x134) SetInterfaceState(DAT_00673344, &local, 4) when DAT_0067ecd0 is
    // set. The rest of the local is never written.
    unsigned char Buffer[0x80];
    memcpy(Buffer, &GSessionFlags, sizeof(GSessionFlags));
    if (G_Server != nullptr)
        G_Server->SetInterfaceState(GetPlayerConnectionId(), Buffer, 4);
}

void SetGameSessionFlags(unsigned Mask, bool bSet)
{
    // 0x004c8120..0x004c8155: set or clear the native flags, preserving other bits.
    SetGameSessionFlagValue(Mask, bSet ? Mask : 0);
}

unsigned GetSavedTargetingProjection()
{
    return (HudPreferencesFlags() & TargetingProjectionMask) >> TargetingProjectionShift;
}

void SetSavedTargetingProjection(unsigned Projection)
{
    if (Projection > 3) return;
    // Replace both bits in one message; never send an intermediate projection.
    SetGameSessionFlagValue(TargetingProjectionMask, Projection << TargetingProjectionShift);
}

bool GetSavedTargetingAutoselect()
{
    return (HudPreferencesFlags() & TargetingAutoselectOff) == 0;
}

void SetSavedTargetingAutoselect(bool enabled)
{
    SetGameSessionFlagValue(TargetingAutoselectOff, enabled ? 0 : TargetingAutoselectOff);
}

bool GetSavedTargetingWindowLocked()
{
    return (HudPreferencesFlags() & TargetingWindowLocked) != 0;
}

void SetSavedTargetingWindowLocked(bool locked)
{
    SetGameSessionFlagValue(TargetingWindowLocked, locked ? TargetingWindowLocked : 0);
}

bool GetSavedHealthWindowLocked()
{
    return (HudPreferencesFlags() & HealthWindowLocked) != 0;
}

void SetSavedHealthWindowLocked(bool locked)
{
    SetGameSessionFlagValue(HealthWindowLocked, locked ? HealthWindowLocked : 0);
}

bool GetSavedHealthWindowOpen()
{
    return (HudPreferencesFlags() & HealthVisibilitySaved) && (HudPreferencesFlags() & HealthWindowClosed) == 0;
}
void SetSavedHealthWindowOpen(bool open)
{
    if (!(HudPreferencesFlags() & HealthVisibilitySaved) || GetSavedHealthWindowOpen() != open)
        SetGameSessionFlagValue(HealthWindowClosed | HealthVisibilitySaved,
                               HealthVisibilitySaved | (open ? 0 : HealthWindowClosed));
}
bool GetSavedHealthViewLeft() { return (HudPreferencesFlags() & HealthViewLeft) != 0; }
void SetSavedHealthViewLeft(bool left)
{
    if (GetSavedHealthViewLeft() != left)
        SetGameSessionFlagValue(HealthViewLeft, left ? HealthViewLeft : 0);
}
bool GetSavedTargetingWindowOpen()
{
    return (HudPreferencesFlags() & TargetingVisibilitySaved) ? (HudPreferencesFlags() & TargetingWindowClosed) == 0
                                                     : !GetSavedTargetingWindowLocked();
}
void SetSavedTargetingWindowOpen(bool open)
{
    if (!(HudPreferencesFlags() & TargetingVisibilitySaved) || GetSavedTargetingWindowOpen() != open)
        SetGameSessionFlagValue(TargetingWindowClosed | TargetingVisibilitySaved,
                               TargetingVisibilitySaved | (open ? 0 : TargetingWindowClosed));
}
unsigned GetSavedWeaponGroup()
{
    unsigned const group = (HudPreferencesFlags() & WeaponGroupMask) >> WeaponGroupShift;
    return group < 6 ? group : 0;
}
void SetSavedWeaponGroup(unsigned group)
{
    if (group < 6 && ((HudPreferencesFlags() & WeaponGroupMask) >> WeaponGroupShift) != group)
        SetGameSessionFlagValue(WeaponGroupMask, group << WeaponGroupShift);
}
unsigned GetGameSessionLoadRevision() { return GSessionLoadRevision; }
bool GetSavedRadarEnabled() { return (HudPreferencesFlags() & RadarEnabled) != 0; }
bool GetSavedRadarTopView() { return (HudPreferencesFlags() & RadarTopView) != 0; }
void SetSavedRadarTopView(bool top)
{
    SetGameSessionFlagValue(RadarTopView, top ? RadarTopView : 0);
}
void SetSavedRadarEnabled(bool enabled)
{
    SetGameSessionFlagValue(RadarEnabled, enabled ? RadarEnabled : 0);
}
unsigned GetSavedRadarRange(unsigned defaultRange)
{
    unsigned const saved = (HudPreferencesFlags() & RadarRangeMask) >> RadarRangeShift;
    return saved ? saved - 1 : defaultRange < 3 ? defaultRange : 2;
}
void SetSavedRadarRange(unsigned range)
{
    if (range < 3 && ((HudPreferencesFlags() & RadarRangeMask) >> RadarRangeShift) != range + 1)
        SetGameSessionFlagValue(RadarRangeMask, (range + 1) << RadarRangeShift);
}
unsigned GetSavedRadarAutoMode()
{
    unsigned const mode = (HudPreferencesFlags() & RadarAutoMask) >> 20;
    return mode <= 2 ? mode : 0;
}
void SetSavedRadarAutoMode(unsigned mode)
{
    if (mode > 2) return;
    // Choosing automation hands visibility to contacts; manual mode preserves the toggle.
    unsigned const mask = RadarAutoMask | (mode ? RadarEnabled : 0);
    SetGameSessionFlagValue(mask, mode << 20);
}
bool GetSavedAutoTurretsEnabled(bool fallback)
{
    return (HudPreferencesFlags() & AutoTurretsSaved) ? !(HudPreferencesFlags() & AutoTurretsOff) : fallback;
}
void SetSavedAutoTurretsEnabled(bool enabled)
{
    SetGameSessionFlagValue(AutoTurretsSaved | AutoTurretsOff,
        AutoTurretsSaved | (enabled ? 0 : AutoTurretsOff));
}
unsigned GetSavedAutoTurretReserve(unsigned fallback)
{
    unsigned const value = (HudPreferencesFlags() & AutoTurretReserveMask) >> 24;
    return value >= 1 && value <= 19 ? (value - 1) * 5 : fallback;
}
void SetSavedAutoTurretReserve(unsigned percent)
{
    if (percent <= 90) SetGameSessionFlagValue(AutoTurretReserveMask, (percent / 5 + 1) << 24);
}

void AssignGameSessionFlags(unsigned Value)
{
    // Import legacy HUD choices once. Loading another character never replaces the profile.
    HudPreferencesFlags();
    if (!GHudStored) SaveHudPreferences(Value & HudPreferencesMask);
    GSessionFlags = Value & 0xfu;
    ++GSessionLoadRevision;
}

bool HudPreferencesSaved() { return GHudSaveOk; }
bool GetShowWeaponGroups() { return !(HudPreferencesFlags() & WeaponGroupsHidden); }
void SetShowWeaponGroups(bool show)
{
    SetGameSessionFlagValue(WeaponGroupsHidden, show ? 0 : WeaponGroupsHidden);
}
bool GetWingCruiseAnimationEnabled()
{
    return (HudPreferencesFlags() & WingCruiseAnimationOff) == 0;
}
void SetWingCruiseAnimationEnabled(bool enabled)
{
    SetGameSessionFlagValue(WingCruiseAnimationOff, enabled ? 0 : WingCruiseAnimationOff);
}

bool TestGameSessionFlags(unsigned Mask)
{
    // 0x004c8110: `(DAT_00612274 & Mask) != 0`.
    return (GSessionFlags & Mask) != 0;
}
