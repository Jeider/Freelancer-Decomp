// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_ADOXA, docs/adoxa.md): Common.dll state of adoxa's plugins that
// Server.dll and the client read. Retail had none of it: each plugin patched the modules
// directly.

#include "common_exports.h"

namespace Archetype
{
    struct Explosion;
}

// criticalhit.dll: [Explosion] critical_hit = percent, multiplier. Rolls rand() and returns the
// damage multiplier of this hit (1 when the explosion has none or the roll misses).
COMMON_API float __cdecl AdoxaCriticalHitMultiplier(Archetype::Explosion const* Explosion);

struct CObject;
struct DamageList;

// DamagePerFire.dll: the launcher wear queued for this ship by its shots since the last call
// (CELauncher::ConsumeFireResources); moved into Out. Returns false when there is none.
COMMON_API bool __cdecl AdoxaTakeFireDamage(CObject const* Ship, DamageList& Out);

// moors.dll: whether a ship archetype has the can_use_berths mission property. Content.dll owns
// the mission properties and registers the query; unregistered -> true (retail behaviour).
// AmmoLimit.dll: the player's ammo limit of a munition / mine / countermeasure archetype
// (ammo_limit, else MAX_PLAYER_AMMO).
COMMON_API int __cdecl AdoxaAmmoLimit(unsigned AmmoArchId);

typedef bool(__cdecl* FAdoxaBerthQuery)(unsigned ShipArchId);
COMMON_API void __cdecl AdoxaSetBerthQuery(FAdoxaBerthQuery Query);
COMMON_API bool __cdecl AdoxaShipCanUseBerths(unsigned ShipArchId);
