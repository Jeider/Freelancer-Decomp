// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: the client half of flplusplus.dll (flplusplus.h, docs/flplusplus.md). The code
// follows the plugin's sources (TheStarport/flplusplus, BSD-2-Clause, Callum McGing and
// contributors; WheelScroll by Jason Hood) on the port's own classes.

#ifdef FREELANCER_FLPLUSPLUS

#include "flplusplus.h"

#include "DALib.h"
#include "common_ini.h"
#include "common_misc.h" // GetScreenShotPath
#include "dacom.h"       // FDUMP
#include "nn_inventory.h"
#include "nn_load_save.h"
#include "nn_mission_vendor.h"
#include "nn_navmap.h"
#include "nn_news.h"
#include "nn_preferences.h"
#include "nn_text_control.h"
#include "page_character_select_single.h"
#include "page_server_select.h"
#include "render/IRenderPipeline.h"
#include "rich_text_win.h"
#include "ui_fast_table.h"
#include "ui_list_box.h"
#include "ui_rich_text_win.h"
#include "ui_scroll.h"
#include "win3d.h"
#include "wire_controls.h"

#include <windows.h>
#include <objidl.h>
#include <gdiplus.h>

#include <io.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <typeinfo>

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "gdi32.lib")

namespace
{
    void(__cdecl* G_FdumpOriginal)(int, char const*, ...) = nullptr;

    // log.cpp fdump_timestamped.
    void __cdecl FdumpTimestamped(int Flags, char const* Format, ...)
    {
        char Buffer[4096];
        va_list Args;
        va_start(Args, Format);
        vsnprintf(Buffer, sizeof(Buffer), Format, Args);
        va_end(Args);
        Buffer[sizeof(Buffer) - 1] = '\0';
        time_t Now;
        time(&Now);
        char Stamp[100];
        strftime(Stamp, 80, "%Y-%m-%d %H:%M:%S", localtime(&Now));
        G_FdumpOriginal(Flags, "[%s] %s", Stamp, Buffer);
    }

    // config::read_font_files + fontresource::init.
    void AddFontFiles(char const* DataPath)
    {
        char IniPath[MAX_PATH];
        _snprintf(IniPath, MAX_PATH, "%s\\FONTS\\fonts.ini", DataPath);
        IniPath[MAX_PATH - 1] = '\0';
        if (_access(IniPath, 0) != 0)
            return;
        INI_Reader Reader;
        if (!Reader.open(IniPath, false))
            return;
        while (Reader.read_header())
        {
            if (!Reader.is_header("FontFiles"))
                continue;
            while (Reader.read_value())
            {
                if (!Reader.is_value("path"))
                    continue;
                char const* const File = Reader.get_value_string(0);
                char Path[MAX_PATH];
                _snprintf(Path, MAX_PATH, "%s\\%s", DataPath, File);
                Path[MAX_PATH - 1] = '\0';
                if (_access(Path, 0) != 0)
                {
                    FDUMP(0x100002, "path to font %s does not exist (%s)", File, Path);
                    continue;
                }
                if (AddFontResourceExA(Path, FR_PRIVATE, nullptr) != 0)
                    FDUMP(0x100002, "successfully added font %s", File);
                else
                    FDUMP(0x100002, "error adding font %s", File);
            }
        }
        Reader.close();
    }

    // screenshot.cpp GetEncoderClsid.
    bool PngEncoder(CLSID* Out)
    {
        UINT Count = 0;
        UINT Size = 0;
        Gdiplus::GetImageEncodersSize(&Count, &Size);
        if (Size == 0)
            return false;
        Gdiplus::ImageCodecInfo* const Codecs = static_cast<Gdiplus::ImageCodecInfo*>(malloc(Size));
        if (Codecs == nullptr)
            return false;
        Gdiplus::GetImageEncoders(Count, Size, Codecs);
        bool bFound = false;
        for (UINT Index = 0; Index < Count; ++Index)
        {
            if (wcscmp(Codecs[Index].MimeType, L"image/png") == 0)
            {
                *Out = Codecs[Index].Clsid;
                bFound = true;
                break;
            }
        }
        free(Codecs);
        return bFound;
    }
}

void FlplusplusStartup(char const* DataPath)
{
    if (G_FdumpOriginal == nullptr && FDUMP != nullptr)
    {
        G_FdumpOriginal = FDUMP;
        FDUMP = FdumpTimestamped;
    }
    if (DataPath != nullptr)
        AddFontFiles(DataPath);
}

int FlplusplusTakeScreenShot()
{
    // OnScreenshot: "%Y-%m-%d_%H-%M-%S" (+ "_N" while taken) .png in the screenshot folder.
    char Directory[MAX_PATH];
    if (!GetScreenShotPath(Directory) || Directory[0] == '\0')
        return -1;
    time_t Now;
    time(&Now);
    char Stamp[100];
    strftime(Stamp, 80, "%Y-%m-%d_%H-%M-%S", localtime(&Now));
    char Base[MAX_PATH];
    _snprintf(Base, MAX_PATH, "%s\\%s", Directory, Stamp);
    Base[MAX_PATH - 1] = '\0';
    char PngPath[MAX_PATH];
    _snprintf(PngPath, MAX_PATH, "%s.png", Base);
    for (int Suffix = 1; _access(PngPath, 0) == 0; ++Suffix)
        _snprintf(PngPath, MAX_PATH, "%s_%d.png", Base, Suffix);
    PngPath[MAX_PATH - 1] = '\0';

    // The plugin copies the desktop through GDI, which a fullscreen Direct3D surface does not
    // reach; the port takes the frame from the pipeline (FUN_00425170's PrintScreen) into a
    // temporary BMP and re-encodes it.
    char BmpPath[MAX_PATH];
    _snprintf(BmpPath, MAX_PATH, "%s.flpp.bmp", Base);
    BmpPath[MAX_PATH - 1] = '\0';
    IRPTexture* Texture = nullptr;
    IRenderPipeline* const Pipe = DALib::Pipeline;
    if (Pipe == nullptr ||
        Pipe->QueryInterface(Iids::RPTexture, reinterpret_cast<void**>(&Texture)) != GR_OK)
        return -1;
    Texture->PrintScreen(nullptr, BmpPath);
    Texture->Release();

    wchar_t BmpWide[MAX_PATH];
    wchar_t PngWide[MAX_PATH];
    MultiByteToWideChar(CP_ACP, 0, BmpPath, -1, BmpWide, MAX_PATH);
    MultiByteToWideChar(CP_ACP, 0, PngPath, -1, PngWide, MAX_PATH);
    Gdiplus::GdiplusStartupInput StartupInput;
    ULONG_PTR Token = 0;
    if (Gdiplus::GdiplusStartup(&Token, &StartupInput, nullptr) == Gdiplus::Ok)
    {
        CLSID Png;
        Gdiplus::Bitmap* const Image = Gdiplus::Bitmap::FromFile(BmpWide);
        bool bSaved = false;
        if (Image != nullptr && Image->GetLastStatus() == Gdiplus::Ok && PngEncoder(&Png))
            bSaved = Image->Save(PngWide, &Png, nullptr) == Gdiplus::Ok;
        delete Image;
        Gdiplus::GdiplusShutdown(Token);
        if (bSaved)
            DeleteFileA(BmpPath);
        else
            MoveFileA(BmpPath, PngPath); // keep the frame (as BMP data) if encoding failed
    }
    return -1;
}

bool FlplusplusHasWheelScroll(Win3D const* Window)
{
    // WheelScroll's ten vftable slots (0x005d1da4 .. 0x005e6194): these exact classes.
    std::type_info const& Type = typeid(*Window);
    return Type == typeid(NnLoadSave) || Type == typeid(NeuroNetNavMap) ||
           Type == typeid(NnPreferences) || Type == typeid(RichTextWin) ||
           Type == typeid(NnTextControl) || Type == typeid(UiFastTable) ||
           Type == typeid(UiScroll) || Type == typeid(UiRichTextWin) ||
           Type == typeid(UiListBox) || Type == typeid(WireButtonControl);
}

bool FlplusplusWindowWheel(Win3D* Window, int Wheel)
{
    // WheelScroll Window_Wheel: walk up from the window to the first one that owns a visible
    // scroll bar; two held-arrow steps (UICycle LAB_00597560) per call.
    for (Win3D* Win = Window; Win != nullptr; Win = Win->GetParent())
    {
        UiScroll* Scroll = nullptr;
        bool bMatched = true;
        char const* const Name = Win->GetName();
        std::type_info const& Type = typeid(*Win);
        if (Type == typeid(UiScroll))
        {
            Scroll = static_cast<UiScroll*>(Win);
        }
        else if (Type == typeid(RichTextWin) || Type == typeid(UiRichTextWin))
        {
            Scroll = static_cast<BaseRichTextWin*>(Win)->ScrollBarV; // +0x3f0
        }
        else if (strcmp(Name, "NN_Inventory") == 0 || strcmp(Name, "NN_Dealer") == 0)
        {
            NnInventory* const Inventory = dynamic_cast<NnInventory*>(Win);
            if (Inventory != nullptr)
                Scroll = dynamic_cast<UiScroll*>(Inventory->InventoryScroll); // +0x3d0
        }
        else if (strcmp(Name, "NN_MissionVendor") == 0)
        {
            NnMissionVendor* const Vendor = dynamic_cast<NnMissionVendor*>(Win);
            if (Vendor != nullptr)
                Scroll = Vendor->SummaryScroll; // +0x428
        }
        else if (strcmp(Name, "NN_News") == 0)
        {
            NnNews* const News = dynamic_cast<NnNews*>(Win);
            if (News != nullptr)
                Scroll = News->Scroll; // +0x648
        }
        else if (strcmp(Name, "NN_LoadSave") == 0)
        {
            NnLoadSave* const LoadSave = dynamic_cast<NnLoadSave*>(Win);
            if (LoadSave != nullptr)
                Scroll = LoadSave->Scroll; // +0x1758
        }
        else if (strcmp(Name, "CharSelDesc") == 0 || strcmp(Name, "CharSelTime") == 0)
        {
            Win = Win->GetParent();
            PageCharacterSelectSingle* const Page =
                dynamic_cast<PageCharacterSelectSingle*>(Win);
            if (Page != nullptr)
                Scroll = Page->CharScroll; // +0xd4
        }
        else if (strcmp(Name, "ServerTable") == 0)
        {
            Win = Win->GetParent();
            PageServerSelect* const Page = dynamic_cast<PageServerSelect*>(Win);
            if (Page != nullptr)
                Scroll = Page->ServerScroll; // +0xc8
        }
        else if (strcmp(Name, "NN_Preferences") == 0)
        {
            NnPreferences* const Preferences = dynamic_cast<NnPreferences*>(Win);
            if (Preferences != nullptr)
                Scroll = Preferences->KeyScroll; // +0x4b8
        }
        else if (strcmp(Name, "NeuroNetNavMap") == 0)
        {
            NeuroNetNavMap* const NavMap = dynamic_cast<NeuroNetNavMap*>(Win);
            if (NavMap != nullptr)
                Scroll = NavMap->ObjectiveScroll; // +0xae0
        }
        else if (strncmp(Name, "NavMapBase", 10) == 0 ||
                 strcmp(Name, "NavMapSystemTitleText") == 0)
        {
            Win = Win->GetParent();
            NeuroNetNavMap* const NavMap = dynamic_cast<NeuroNetNavMap*>(Win);
            if (NavMap != nullptr)
                Scroll = NavMap->BaseListScroll; // +0xfc4
        }
        else
        {
            bMatched = false;
        }

        if (bMatched && Scroll != nullptr && Scroll->IsShown())
        {
            bool const bUp = Wheel > 0;
            Scroll->WheelStep(bUp);
            Scroll->WheelStep(bUp);
            return true;
        }
        if (Win == nullptr)
            break;
    }
    return false;
}

#endif
