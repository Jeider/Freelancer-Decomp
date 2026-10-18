// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_FLPLUSPLUS): the client half of TheStarport's flplusplus.dll
// (docs/flplusplus.md). The settings live in Common.dll (common_flplusplus.h).

#ifdef FREELANCER_FLPLUSPLUS

#include "common_flplusplus.h"

struct Win3D;

// WinMain, after the spew log opens: FLSpew lines get a "[YYYY-MM-DD HH:MM:SS]" prefix
// (log.cpp patch_fdump), and the [FontFiles] of DATA\FONTS\fonts.ini are added as private
// fonts (fontresource.cpp).
void FlplusplusStartup(char const* DataPath);

// USER_SCREEN_SHOT (screenshot.cpp OnScreenshot): a PNG named by the local time in the
// screenshot folder; the frame comes from the pipeline's PrintScreen. Returns -1 as the
// plugin's replacement of FUN_00425170 does.
int FlplusplusTakeScreenShot();

// adoxa's WheelScroll (in flplusplus): true for the classes whose slot 18 it replaced.
bool FlplusplusHasWheelScroll(Win3D const* Window);
// WheelScroll's Window_Wheel: the first visible scroll bar of the window or an ancestor moves
// two steps per notch. Wheel > 0 scrolls up.
bool FlplusplusWindowWheel(Win3D* Window, int Wheel);

#endif
