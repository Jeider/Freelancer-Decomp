// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: FLSharp.ini (common_flsharp.h, docs/flsharp.md).

#ifdef FREELANCER_FLSHARP

#include "common_flsharp.h"
#include "common_id.h"
#include "common_ini.h"

#include <windows.h>
#include <shlwapi.h>

#include <map>

#pragma comment(lib, "shlwapi.lib")

namespace
{
    std::map<unsigned, bool>* G_FlsharpSwitches = nullptr;

    void LoadFlsharpSwitches()
    {
        G_FlsharpSwitches = new std::map<unsigned, bool>();
        char Path[MAX_PATH];
        GetModuleFileNameA(nullptr, Path, MAX_PATH);
        PathRemoveFileSpecA(Path);
        PathAppendA(Path, "FLSharp.ini");
        if (!PathFileExistsA(Path))
            return;
        INI_Reader Reader;
        if (!Reader.open(Path, false))
            return;
        while (Reader.read_header())
        {
            while (Reader.read_value())
                (*G_FlsharpSwitches)[CreateID(Reader.get_name_ptr())] = Reader.get_value_bool(0);
        }
        Reader.close();
    }
}

bool FlsharpFeatureEnabled(char const* Name)
{
    if (G_FlsharpSwitches == nullptr)
        LoadFlsharpSwitches();
    std::map<unsigned, bool>::const_iterator const It = G_FlsharpSwitches->find(CreateID(Name));
    return It == G_FlsharpSwitches->end() || It->second;
}

#endif
