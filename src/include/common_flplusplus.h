// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_FLPLUSPLUS): the settings of TheStarport's flplusplus.dll, read from
// flplusplus.ini next to freelancer.exe, as the plugin reads them (config.cpp). The plugin
// patches retail addresses and cannot be loaded; its behaviour is source in the modules it
// patched (docs/flplusplus.md). Common.dll owns the settings: it needs them itself (save and
// screenshot folders, character detail), and the client reads them through the export.

#ifdef FREELANCER_FLPLUSPLUS

#include "common_exports.h"

struct FFlplusplusConfig
{
    float LodScale;                   // lod_scale = 1
    float PbubbleScale;               // pbubble_scale = 1
    float CharacterDetailScale;       // character_detail_scale = 1
    char SaveFolderName[260];         // save_folder_name = Freelancer
    bool bSaveInDirectory;            // save_in_directory = false (EXE\..\SAVE)
    char ScreenshotsFolderName[260];  // screenshots_folder_name = FreelancerShots
    bool bScreenshotsInDirectory;     // screenshots_in_directory = false (EXE\..\SCREENSHOTS)
    float ShipPreviewScrollingSpeed;  // ship_preview_scrolling_speed = 2, clamped to 0..50
    bool bShipPreviewScrollingInverse; // ship_preview_scrolling_inverse = false
};

// The settings, read once on the first call (defaults without the file).
COMMON_API FFlplusplusConfig const& FlplusplusGetConfig();

// flplusplus applies a scale only inside [1, 1000000] (graphics.cpp minScale / maxScale);
// outside it the retail value stays.
inline bool FlplusplusScaleApplies(float Scale)
{
    return Scale >= 1.0f && Scale <= 1000000.0f;
}

#endif
