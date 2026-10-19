// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_MOD_PLUGINS, docs/mod_plugins.md): Common.dll state of the mod plugins
// the port carries (MultiCruise, Interceptor, PowerDamage) that Server.dll and the client read.

#include "common_exports.h"

namespace Archetype
{
    struct Engine;
    struct Explosion;
}

// MultiCruise.dll: the engine's cruise_speed, else [EngineEquipConsts] CRUISING_SPEED.
COMMON_API float __cdecl ModEngineCruiseSpeed(Archetype::Engine const* Engine);

// Interceptor.dll: a gun archetype with interceptor = true fires in cruise.
COMMON_API bool __cdecl ModGunIsInterceptor(unsigned GunArchId);

// PowerDamage.dll: an explosion with force_energy_damage = true deals energy damage even when
// the mod switches energy damage off.
COMMON_API bool __cdecl ModExplosionForcesEnergyDamage(Archetype::Explosion const* Explosion);

struct CEqObj;

// The wing animation system that replaces the mod's AnimKey.dll (docs/mod_plugins.md):
// [InternalFX] use_animation_oneshot = <script> plays the script once when the equipment is
// created (the launch extension), instead of use_animation's loop. The playback lives in that
// InternalFX (the ship's first one with a one-shot), so it goes with the ship.
// The ship's wing playback handle, -1 when it has none.
COMMON_API int __cdecl ModShipOneShotAnim(CEqObj const* Ship);
// Replaces it with a new playback of Script (not yet evaluated); returns its handle or -1.
COMMON_API int __cdecl ModSwapShipOneShotAnim(CEqObj* Ship, char const* Script);
