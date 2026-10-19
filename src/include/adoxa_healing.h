// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_ADOXA, docs/adoxa.md): adoxa's healing.dll lets zones, munitions and
// explosions carry negative damage that repairs (port.ini [Plugins] healing = 1). Where retail
// tests "damage > 0" the plugin tests "damage != 0"; these macros keep each site one line.
// Without the flag they are retail's own tests.

#ifdef FREELANCER_ADOXA
#include "port_plugins.h"
#include <cmath>
#define HEALING_ON() PORT_PLUGIN_ON("healing")
// Retail "X > Eps" (a damaging amount); with healing a negative amount counts too.
#define HEALING_DAMAGES(X, Eps) \
    (HEALING_ON() ? std::fabs(static_cast<double>(X)) > (Eps) : static_cast<double>(X) > (Eps))
#else
#define HEALING_ON() false
#define HEALING_DAMAGES(X, Eps) (static_cast<double>(X) > (Eps))
#endif
