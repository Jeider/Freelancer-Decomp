// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_MOD_PLUGINS, docs/mod_plugins.md): the wing animation system that
// replaces the mod's AnimKey.dll (which sent console.dll's "anim wings" on Ctrl + the cruise key).
//
// A player ship whose loadout has an [InternalFX] with use_animation_oneshot (the mod's
// launch_extend) starts with its wing folded; that script runs once at spawn and extends it.
// Afterwards the wing script ([WingAnim] script in port.ini, default "Sc_extend wing": forward
// folds, reverse extends) takes over the same playback slot:
//   - the wing folds when cruise engages and extends again when it stops;
//   - it folds when the ship starts docking with a station, base or planet (not a trade lane,
//     gate or hole);
//   - the [WingAnim] key toggles it by hand.
// A request made while the wing moves (the launch included) is queued and runs when the move
// ends; the last request wins, and one the move already satisfies is dropped.

#ifdef FREELANCER_MOD_PLUGINS

// Per frame in space (UpdateSpaceDocking).
void WingAnimTick();

// From KeyMapRouteInputMessage: true when the message was the wing key.
bool WingAnimHandleKey(unsigned Message, unsigned Wparam);

// For a HUD indicator: 0 none (the ship has no wing), 1 folded, 2 moving, 3 extended.
int WingAnimDisplayState();

#endif
