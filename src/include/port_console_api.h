// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_DBG_OPTIONS, docs/dbg_options.md): the server half of the console
// commands taken from adoxa's console.dll (save, base, system, jump). The client console finds
// the export with GetProcAddress (the client does not link Server.dll; single player loads it).

#include "common_csys.h" // Vector, Matrix

enum EPortConsoleOp
{
    kPortConsoleSave = 1,      // In: FPortConsoleSave            Out: int (1 saved)
    kPortConsoleForceLand = 2, // In: unsigned base id
    kPortConsoleSystem = 3,    // In: FPortConsoleSystem
    kPortConsoleJump = 4,      // In: FPortConsoleJump
};

enum EPortConsoleResult
{
    kPortConsoleOk = 0,
    kPortConsoleNotInSpace = 1,
    kPortConsoleNoTarget = 2,
    kPortConsoleObjectNotFound = 3,
    kPortConsoleFailed = 4,
};

struct FPortConsoleSave
{
    char const* File;          // "qsave1.fl" / "<hash>.fl"
    wchar_t const* Description;
};

struct FPortConsoleSystem
{
    unsigned System;           // destination system id
    int Mode;                  // 0: keep the ship's coordinates, 1: Pos / Orient, 2: at Object
    Vector Pos;
    Matrix Orient;
    char Object[64];           // nickname, or "~part" of one
};

struct FPortConsoleJump
{
    int Mode;                  // 0: the ship's target, 1: Offset (forward, right, up), 2: Object,
                               // 3: Offset is an absolute position (the orientation is kept)
    Vector Offset;
    char Object[64];
    // Out: where the ship goes. In single player the client owns its ship's position (it
    // sends it to the server every frame), so the console beams the client's ship there too.
    Vector OutPos;
    Matrix OutOrient;
};

typedef int(__cdecl* FPortConsoleServerFn)(int Op, void* InOut);
#define PORT_CONSOLE_SERVER_EXPORT "PortConsoleServer"
