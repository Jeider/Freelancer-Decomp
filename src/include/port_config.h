// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// Port-only (FREELANCER_ADOXA / FREELANCER_MOD_PLUGINS / FREELANCER_LANGUAGE): port.ini next to
// freelancer.exe. Retail has no such file: its plugins were DLLs listed in dacom.ini [Libraries],
// and a translated build was a second, byte-patched exe. See docs/adoxa.md, docs/language.md.
//
//   [Plugins]          one key per built-in plugin, 1 = on (missing = off)
//   [Language]         language = ru          (the -lang:xx command line switch wins)
//   [Language.ru]      per-language keys: freelancer_ini, resources, data_overlay, plugin texts
//
// Values are read once and cached; the file is optional.

#include "common_exports.h"

// [Plugins] Name (case-insensitive), as a 0/1 switch.
COMMON_API bool __cdecl PortPluginEnabled(char const* Name);

// Any section/key of port.ini; Default when missing.
COMMON_API int __cdecl PortConfigInt(char const* Section, char const* Key, int Default);
COMMON_API float __cdecl PortConfigFloat(char const* Section, char const* Key, float Default);
COMMON_API unsigned __cdecl PortConfigString(char const* Section, char const* Key, char const* Default,
                                            char* Out, unsigned OutSize);

// The active language code ("ru", "en", ...; empty when none is configured).
COMMON_API char const* __cdecl PortLanguage();

// [Language.<code>] Key of the active language; Default when missing (or no language is set).
COMMON_API unsigned __cdecl PortLanguageString(char const* Key, char const* Default, char* Out,
                                              unsigned OutSize);

// The directory freelancer.exe runs from, with a trailing backslash.
COMMON_API char const* __cdecl PortExeDirectory();
