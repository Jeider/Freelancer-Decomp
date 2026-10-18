// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: flplusplus.ini (common_flplusplus.h, docs/flplusplus.md).

#ifdef FREELANCER_FLPLUSPLUS

#include "common_flplusplus.h"
#include "common_ini.h"

#include <windows.h>
#include <shlwapi.h>
#include <string.h>

#pragma comment(lib, "shlwapi.lib")

namespace
{
    FFlplusplusConfig G_FlplusplusConfig;
    bool G_bFlplusplusConfigLoaded = false;

    void CopyName(char* Dest, char const* Source)
    {
        strncpy(Dest, Source != nullptr ? Source : "", 259);
        Dest[259] = '\0';
    }

    // flplusplus config::init_defaults and config::init_from_file.
    void LoadFlplusplusConfig()
    {
        FFlplusplusConfig& Conf = G_FlplusplusConfig;
        Conf.LodScale = 1.0f;
        Conf.PbubbleScale = 1.0f;
        Conf.CharacterDetailScale = 1.0f;
        CopyName(Conf.SaveFolderName, "Freelancer");
        Conf.bSaveInDirectory = false;
        CopyName(Conf.ScreenshotsFolderName, "FreelancerShots");
        Conf.bScreenshotsInDirectory = false;
        Conf.ShipPreviewScrollingSpeed = 2.0f;
        Conf.bShipPreviewScrollingInverse = false;

        char Path[MAX_PATH];
        GetModuleFileNameA(nullptr, Path, MAX_PATH);
        PathRemoveFileSpecA(Path);
        PathAppendA(Path, "flplusplus.ini");
        if (!PathFileExistsA(Path))
            return;

        INI_Reader Reader;
        if (!Reader.open(Path, false))
            return;
        while (Reader.read_header())
        {
            if (!Reader.is_header("flplusplus"))
                continue;
            while (Reader.read_value())
            {
                if (Reader.is_value("lod_scale"))
                    Conf.LodScale = static_cast<float>(Reader.get_value_float(0));
                if (Reader.is_value("pbubble_scale"))
                    Conf.PbubbleScale = static_cast<float>(Reader.get_value_float(0));
                if (Reader.is_value("character_detail_scale"))
                    Conf.CharacterDetailScale = static_cast<float>(Reader.get_value_float(0));
                if (Reader.is_value("save_folder_name"))
                    CopyName(Conf.SaveFolderName, Reader.get_value_string(0));
                if (Reader.is_value("save_in_directory"))
                    Conf.bSaveInDirectory = Reader.get_value_bool(0);
                if (Reader.is_value("screenshots_folder_name"))
                    CopyName(Conf.ScreenshotsFolderName, Reader.get_value_string(0));
                if (Reader.is_value("screenshots_in_directory"))
                    Conf.bScreenshotsInDirectory = Reader.get_value_bool(0);
                if (Reader.is_value("ship_preview_scrolling_speed"))
                    Conf.ShipPreviewScrollingSpeed = static_cast<float>(Reader.get_value_float(0));
                if (Reader.is_value("ship_preview_scrolling_inverse"))
                    Conf.bShipPreviewScrollingInverse = Reader.get_value_bool(0);
            }
        }
        Reader.close();

        // shippreviewscroll::init: the speed clamped to 0..50.
        if (Conf.ShipPreviewScrollingSpeed < 0.0f)
            Conf.ShipPreviewScrollingSpeed = 0.0f;
        else if (Conf.ShipPreviewScrollingSpeed > 50.0f)
            Conf.ShipPreviewScrollingSpeed = 50.0f;
    }
}

FFlplusplusConfig const& FlplusplusGetConfig()
{
    if (!G_bFlplusplusConfigLoaded)
    {
        G_bFlplusplusConfigLoaded = true;
        LoadFlplusplusConfig();
    }
    return G_FlplusplusConfig;
}

#endif
