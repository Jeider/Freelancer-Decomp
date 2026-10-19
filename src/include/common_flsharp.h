// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_FLSHARP): the feature switches of BC46's FLSharp.dll, read from
// FLSharp.ini next to the exe as the plugin reads them (config_reader.cpp): every value of
// every section, "name = true/false"; a feature not listed (or no file) is enabled. The
// plugin patches retail addresses; its fixes are source in the modules they patch
// (docs/flsharp.md). Common.dll owns the switches so the client, Common and Server share them.

#ifdef FREELANCER_FLSHARP

#include "common_exports.h"

// True unless FLSharp.ini sets Name to false.
COMMON_API bool FlsharpFeatureEnabled(char const* Name);

#endif
