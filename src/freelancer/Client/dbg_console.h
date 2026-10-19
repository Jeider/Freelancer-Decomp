// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_DBG_OPTIONS, docs/dbg_options.md): the 2002 beta's in-game console
// (con_KHandler at beta 0x006862a8, open/close 0x00554eb0, draw 0x00555020, the CONSOLE command
// table at 0x00690fb0). Retail has no console. The ` key (the one under Esc) opens it; the
// first commands ported are the beta's time ones -- TimeScale slows the single-player game.

#ifdef FREELANCER_DBG_OPTIONS

// From KeyMapRouteInputMessage: true when the console used the message (it eats every key
// and character while open).
bool DbgConsoleHandleMessage(unsigned Message, unsigned Wparam, unsigned Lparam);

// From the end of the frame, after the DBG_OPTIONS window.
void DbgConsoleDraw();

// Before font teardown.
void DbgConsoleShutdown();

#endif
