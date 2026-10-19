// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_ADOXA, docs/adoxa.md): state shared between the Common.dll files that
// carry adoxa's plugins.

#ifdef FREELANCER_ADOXA

#include "port_plugins.h"

#include <map>

// LaneSpeed.dll: the trade lane speed (retail constant DAT_0639f3cc, 2500), set from the
// entrance ring's lane_speed when the player enters a lane.
extern float G_AdoxaLaneSpeed;
// Archetype nickname id -> [Solar] lane_speed.
std::map<unsigned, float>& AdoxaLaneSpeeds();

namespace Archetype
{
    struct Explosion;
}
// AmmoLimit.dll: ammo nickname id -> ammo_limit.
std::map<unsigned, int>& AdoxaAmmoLimits();

// EquipDrag.dll: equipment nickname id -> linear_drag.
std::map<unsigned, float>& AdoxaEquipDrags();

// criticalhit.dll: explosion archetype -> (probability 0..1, damage multiplier).
std::map<Archetype::Explosion const*, std::pair<float, float>>& AdoxaCriticalHits();

#endif
