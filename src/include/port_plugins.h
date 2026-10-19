// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_ADOXA / FREELANCER_MOD_PLUGINS): the switch of one built-in plugin,
// port.ini [Plugins] <Name> = 1, read once per call site.

#include "port_config.h"

#define PORT_PLUGIN_ON(Name) ([]() -> bool { static bool const S_bOn = PortPluginEnabled(Name); return S_bOn; }())
