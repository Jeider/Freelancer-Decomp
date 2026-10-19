// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_DBG_OPTIONS, docs/dbg_options.md): the 2002 beta's DBG_OPTIONS window
// (command 221, opt_KHandler at beta 0x00570410, list drawing FUN_0056ffd0) over retail's own
// option table (game_options.h), and the [OUTLINES] drawing of beta FUN_005167a0.
//
// Retail kept the option table and its 138 guards but stripped the window and every [OUTLINES]
// consumer; retail has no DBG_* keymap commands, so the window opens on Ctrl+Shift+O.

#ifdef FREELANCER_DBG_OPTIONS

struct ICamera;

// From KeyMapRouteInputMessage: true when the key was used by the window.
bool DbgOptionsHandleKey(unsigned Message, unsigned Key);

// From the end of the frame (next to DrawClientTickProfile): the window, when open.
void DbgOptionsDrawWindow();

// Before font teardown.
void DbgOptionsShutdown();

// From the space pass after the effects: PHYS WIRES, PHYS SPHERES, SHIELDS and PHANTOMS.
void DbgOutlinesDraw(ICamera* Camera);

#endif
