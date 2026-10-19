// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_DBG_OPTIONS, docs/dbg_options.md): the 2002 beta's ChaseCamera (vtable
// beta 0x005c79e4, ctor 0x004f1510, update 0x004f1dd0, events 0x004f2ac0, draw 0x004f3670) -- an
// external camera that watches any ship or solar -- with its hardpoint display (beta
// 0x0040c040 / 0x0040c100 / 0x0040c160). Retail 1.1 dropped the class with the debug keys.
//
// Keys (retail has no DBG_* or chase keymap commands, so they are fixed here):
//   Ctrl+Shift+C      enter (the player's target, else the player) / leave; Esc leaves too
//   PgDn / PgUp       next / previous ship (Ctrl: solar); with hardpoints shown: next / previous
//   arrows            orbit; Num+ / Num- zoom out / in; Home resets the view
//   V                 view mode (orbit, ahead, behind, facing); Backspace: minimum distance 1
//   Num*              hardpoints: off, on top, depth-tested; I: the info line

#ifdef FREELANCER_DBG_OPTIONS

struct FSpaceCamera;

// From KeyMapRouteInputMessage: true when the key was used.
bool DbgChaseHandleKey(unsigned Message, unsigned Key);

// From SwitchSpaceCameraMode("chase"): the camera object.
FSpaceCamera* DbgChaseCamera();

// From the end of the frame (next to the DBG_OPTIONS window): help, info and hardpoint texts.
void DbgChaseDrawOverlay();

void DbgChaseShutdown();

#endif
