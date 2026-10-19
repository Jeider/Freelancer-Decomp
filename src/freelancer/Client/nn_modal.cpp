// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#include "nn_modal.h"

#include "character_select_equip.h" // GetPlayerBaseIdRetail (DAT_00673358), GetPlayerStarSystemIdRetail
#include "client_base_market.h" // GetClientCurrentLocationBaseData (FUN_0043b630)
#include "globals.h"       // SetClientServerTickPause (FUN_0042d6f0), GetClientFrameTimeCapped
#include "hud_comm.h"      // HudCommIsWindowOpen (FUN_004cc8d0)
#include "ids_strings.h"   // GetIdsStringWWithRawFallback (FUN_004347e0)
#include "input_manager.h" // Get/SetClientMouseCursorDrawFlag (FUN_0041dd90 / FUN_0041dda0)
#include "menu_universe_base.h" // GetClientCurrentBaseStridName (FUN_0043bbe0)
#include "infocard_map.h"  // InfocardMapCreate / InfocardMapDestroy (FUN_00458790 / FUN_00458860)
#include "knowledge_map.h" // KnowledgeMapCreate / KnowledgeMapDestroy (FUN_00459830 / FUN_00459900)
#include "cargo_bar_control.h"
#include "font_string.h"   // FontStringConstruct (FUN_004144b0)
#include "menu_ui_widgets.h"
#include "nn_rollover.h"   // NnRolloverShowHoverGlobal (FUN_004b62d0)
#include "tooltip_hover.h" // FToolTipHoverInfo, ToolTipHoverReset (FUN_004963a0)
#include "nav_bar.h"       // NavBarHasServiceWindow (FUN_00442720)
#include "nn_arrival_text.h"
#include "nn_inventory.h"  // IsPlayerDockedRetail (FUN_004c4810)
#include "nn_main_button.h"
#include "nn_messaging.h"  // NnVoiceInit (FUN_00489de0)
#include "nn_trade.h"      // G_NnTrade (DAT_006724b4)
#include "nn_story_star.h" // G_MissionObjectiveWindow (DAT_00672400), StoryStarReset
#include "nn_text_control.h"
#include "nn_text_scratch.h" // G_NnTextScratchA/B, G_NnTextScratchCapacity
#include "nn_ui_pulse.h"   // G_NnPaletteArgb_679b90 (DAT_00679b90)
#include "player_behavior.h" // OnMouseFlightRawMessage (FUN_004c80f0)
#include "room_control.h"  // FRoomRuntime, GetRoomRuntimeRoomId (runtime +0x38)
#include "space_letterbox.h" // IsLetterboxVisible (FUN_0041a3e0)
#include "win3d.h"         // Win3DDeleteTree (FUN_0043d2a0)
#include "win_factory.h"   // WinFactoryCreate (FUN_0059db20)

#include "common_goods.h"  // BaseData::get_base_id
#include "common_id.h"     // CreateID, MakeLocationID
#include "common_universe.h"

#include <stdio.h>
#include <wchar.h>
#include <windows.h>

#ifdef FREELANCER_ADOXA
#include "port_plugins.h" // port-only adoxa plugins (territory)
#include "common_ini.h"   // INI_Reader (territory.ini)
#include "font_string.h"  // FFontString::bMultiLine (the caption's Font::String)
#include <stdlib.h>
#include <string.h>
#include <map>
#include <string>
#include <vector>
#endif

bool G_bNnScreenUp = false;              // DAT_0067dcc8
NN_MainButton* G_NnMainButton = nullptr; // DAT_0066d3f0
NnArrivalText* G_NnArrivalText = nullptr; // DAT_0066d398

// Retail DAT_0066d35c -- WINFACTORY<NN_ArrivalText> static (LAB_0045ab60 -> FUN_0045b4c0; Create
// FUN_0045b530; atexit LAB_0045ab80 -> FUN_00579380).
WINFACTORY<NnArrivalText> G_NnArrivalTextFactory("NN_ArrivalText");

namespace
{
    // DAT_0066d344 -- set by the static initializer LAB_0045a0e0 to
    // CreateID("click_on_characters_and_buttons"); only reader FUN_0045a270 (0x0045a37e).
    unsigned const G_NnVoiceClickOnCharactersId = CreateID("click_on_characters_and_buttons");

    // FUN_0059db20("NN_ArrivalText", "NN_ArrivalText", 0, 0) when DAT_0066d398 is null, then the
    // pointer re-read -- the head every cdecl entry point spells out (0x0045b2d0.., 0x0045b310..,
    // 0x0045b340.., 0x0045b430.., 0x0045b490..).
    NnArrivalText* EnsureNnArrivalText()
    {
        if (G_NnArrivalText == nullptr)
            WinFactoryCreate("NN_ArrivalText", "NN_ArrivalText", nullptr, nullptr);
        return G_NnArrivalText;
    }

    // The strid_name of the player's system: Universe::get_system(FUN_004c4830()) and its slot 3
    // (+0x0c), or 0 when there is no such system -- 0x0045aebd..0x0045aed7, 0x0045b004..
    // 0x0045b01e, 0x0045b1d4..0x0045b1ee.
    int PlayerSystemStridName()
    {
        Universe::ISystem const* const System =
            Universe::get_system(GetPlayerStarSystemIdRetail());
        if (System == nullptr)
            return 0;
        return System->GetStridName();
    }

    // .rdata 0x005ce928: the typing time per character ShowBaseArrival reserves.
    constexpr float kArrivalSecondsPerChar = 0.06f;
    // Each Show* reads its format (ids 0x55c / 0x55d / 0x55e) with a count of 0x80 into a stack
    // buffer of 0x80 BYTES (0x40 wchars) -- a retail overrun for a format of 64 characters or
    // more. The port's buffer holds the 0x80 wchars the count allows; the formats are short.
    constexpr int kArrivalFormatChars = 0x80;
}

#ifdef FREELANCER_ADOXA
// Port-only, adoxa's territory.dll v1.03 (docs/adoxa.md): the system entry caption and the Nav
// Map houses customised by DATA\UNIVERSE\territory.ini. The plugin read the file once at load
// (DllMain) and patched Freelancer.exe; here it is read on first use. The file name is port.ini
// [Language.<code>] territory_ini (default territory.ini, relative to DATA\UNIVERSE): the mod's
// Russian and English territory DLLs differed only in that name (territory.ini / territ_en.ini).
// Strings are converted with [Settings] codepage; without one, port.ini [Language.<code>]
// territory_codepage, else the system ANSI code page (CP_ACP) as the plugin's default.
namespace
{
    // The plugin's TTer.
    struct FTerritory
    {
        int Res; // the house: > 0 its ids, < 0 ~index into Store (house = name), 0 none
        int Fmt; // the format: > 0 its ids, < 0 ~index into Store, 0 the retail format
    };

    struct FTerritoryData
    {
        bool bCaps = true;            // [Settings] caps
        unsigned CodePage = CP_ACP;   // [Settings] codepage
        std::map<int, FTerritory> Territories; // keyed by system nickname hash or strid_name
        std::vector<std::wstring> Store;       // the plugin's StringStore
        bool bLabelSet[4] = {false, false, false, false};
        FTerritoryNavMapHouse Labels[4] = {}; // house_id 1249..1252 (the retail labels)
        std::vector<FTerritoryNavMapHouse> Houses; // every other house with NavMap =
    };

    // stows: the string converted with the code page and kept, its NOT index returned (0 for an
    // empty one). At most 63 characters; '^' becomes a new line when bNewLines.
    int TerritoryStoreString(FTerritoryData& Data, char const* Text, bool bNewLines)
    {
        int const Pos = ~static_cast<int>(Data.Store.size());
        int const Len = MultiByteToWideChar(Data.CodePage, 0, Text, -1, nullptr, 0);
        if (Len <= 1)
            return 0;
        std::wstring Wide(static_cast<size_t>(Len), L'\0');
        MultiByteToWideChar(Data.CodePage, 0, Text, -1, &Wide[0], Len);
        Wide.resize(static_cast<size_t>(Len > 64 ? 63 : Len - 1));
        if (bNewLines)
        {
            for (size_t Index = 0; Index < Wide.size(); ++Index)
            {
                if (Wide[Index] == L'^')
                    Wide[Index] = L'\n';
            }
        }
        Data.Store.push_back(Wide);
        return Pos;
    }

    // codepage = UTF-8 / ANSI / OEM / MAC / a number.
    unsigned TerritoryParseCodePage(char const* Text)
    {
        if (_stricmp(Text, "UTF-8") == 0)
            return CP_UTF8;
        if (_stricmp(Text, "ANSI") == 0)
            return CP_ACP;
        if (_stricmp(Text, "OEM") == 0)
            return CP_OEMCP;
        if (_stricmp(Text, "MAC") == 0)
            return CP_MACCP;
        return static_cast<unsigned>(atoi(Text));
    }

    // The plugin's range reader: NUMBER, FIRST-LAST or STRINGNN-MM (LAST / MM may give only the
    // changed digits: "196609-13", "Li01-5"); anything else is a nickname.
    struct FTerritoryRange
    {
        int Pos = 0;
        int Last = 0;
        char String[128] = {};
        int Digit = 0;

        static int GetNum(char const*& Text)
        {
            for (int Num = 0;; ++Text)
            {
                if (*Text < '0' || *Text > '9')
                    return Num;
                Num = Num * 10 + *Text - '0';
            }
        }

        int First(char const* Text)
        {
            char Buffer[32];
            String[0] = '\0';
            Last = 0;

            char const* const Start = Text;
            Pos = GetNum(Text);
            if (Text != Start)
            {
                if (*Text == '\0')
                    return Pos;
                int Prefix = static_cast<int>(Text - Start);
                if (*Text == '-' && Prefix <= 10)
                {
                    Prefix -= static_cast<int>(strlen(++Text));
                    if (Prefix > 0)
                    {
                        _snprintf(Buffer, sizeof(Buffer), "%.*s%s", Prefix, Start, Text);
                        Buffer[sizeof(Buffer) - 1] = '\0';
                        Text = Buffer;
                    }
                    Last = GetNum(Text);
                    if (*Text == '\0' && Last >= Pos)
                        return Pos;
                }
            }

            char const* Dash = strchr(Start, '-');
            int const Len = Dash != nullptr ? static_cast<int>(Dash - Start) : 0;
            if (Len < 3 || Len >= static_cast<int>(sizeof(String)) || Dash[-1] < '0' ||
                Dash[-1] > '9' || Dash[-2] < '0' || Dash[-2] > '9')
                return static_cast<int>(CreateID(Start));
            Pos = (Dash[-2] - '0') * 10 + Dash[-1] - '0';
            Last = GetNum(++Dash);
            if (*Dash != '\0' || Last < Pos)
                return static_cast<int>(CreateID(Start));

            Digit = Len - 1;
            memcpy(String, Start, static_cast<size_t>(Len));
            String[Len] = '\0';
            return static_cast<int>(CreateID(String));
        }

        int Next()
        {
            if (++Pos > Last)
                return 0;
            if (String[0] != '\0')
            {
                if (++String[Digit] > '9')
                {
                    String[Digit] = '0';
                    ++String[Digit - 1];
                }
                return static_cast<int>(CreateID(String));
            }
            return Pos;
        }
    };

    // set_territories: every parameter of systems =, last first.
    void TerritorySetSystems(FTerritoryData& Data, INI_Reader& Ini, FTerritory const& Ter)
    {
        FTerritoryRange Range;
        for (int Index = static_cast<int>(Ini.get_num_parameters()); --Index >= 0;)
        {
            int Id = Range.First(Ini.get_value_string(static_cast<unsigned>(Index)));
            while (Id != 0)
            {
                Data.Territories[Id] = Ter;
                Id = Range.Next();
            }
        }
    }

    // The plugin's Patch(): the ini read in order (the code page applies to the strings after
    // it). Null when the plugin is off or the file does not open (the plugin patched nothing).
    FTerritoryData const* TerritoryData()
    {
        static FTerritoryData* S_Data = nullptr;
        static bool S_bRead = false;
        if (S_bRead)
            return S_Data;
        S_bRead = true;
        if (!PORT_PLUGIN_ON("territory"))
            return nullptr;

        char Name[MAX_PATH];
        PortLanguageString("territory_ini", "territory.ini", Name, sizeof(Name));
        char Path[MAX_PATH + 32];
        _snprintf(Path, sizeof(Path), "..\\data\\universe\\%s", Name);
        Path[sizeof(Path) - 1] = '\0';

        INI_Reader Ini;
        if (!Ini.open(Path, false))
            return nullptr;

        FTerritoryData* const Data = new FTerritoryData;
        char CodePage[32];
        if (PortLanguageString("territory_codepage", "", CodePage, sizeof(CodePage)) != 0 &&
            CodePage[0] != '\0')
            Data->CodePage = TerritoryParseCodePage(CodePage);

        // The plugin's globals: ter is reset per section, nm (the Nav Map house) is not.
        FTerritory Ter = {0, 0};
        FTerritoryNavMapHouse House = {0, 0.0f, 0.0f, nullptr};
        while (Ini.read_header())
        {
            Ter.Res = 0;
            Ter.Fmt = 0;
            if (Ini.is_header("Houses"))
            {
                while (Ini.read_value())
                {
                    if (Ini.is_value("house"))
                        Ter.Res = TerritoryStoreString(*Data, Ini.get_value_string(), false);
                    else if (Ini.is_value("house_id"))
                    {
                        if (Ini.is_value_empty(0))
                            House.Ids = static_cast<unsigned>(Ini.get_value_int(1));
                        else
                        {
                            Ter.Res = Ini.get_value_int(0);
                            House.Ids = Ini.is_value_empty(1)
                                            ? static_cast<unsigned>(Ter.Res)
                                            : static_cast<unsigned>(Ini.get_value_int(1));
                        }
                    }
                    else if (Ini.is_value("format"))
                        Ter.Fmt = TerritoryStoreString(*Data, Ini.get_value_string(), true);
                    else if (Ini.is_value("format_id"))
                        Ter.Fmt = Ini.get_value_int(0);
                    else if (Ini.is_value("systems"))
                    {
                        if (Ter.Res != 0)
                            TerritorySetSystems(*Data, Ini, Ter);
                    }
                    else if (Ini.is_value("NavMap"))
                    {
                        if (House.Ids != 0)
                        {
                            // The system pos scaled onto the universe view.
                            House.X = static_cast<float>(Ini.get_value_float(0)) * 0.0272f - 0.2090f;
                            House.Y = static_cast<float>(Ini.get_value_float(1)) * -0.0272f + 0.2010f;
                            House.Font = Ini.is_value_empty(2) ? "SubHeader"
                                                               : _strdup(Ini.get_value_string(2));
                            // 0x00490358 / 0x004903b4 / 0x00490410 / 0x0049046c: the four
                            // retail labels take the new ids, position and font in place.
                            if (Ter.Res >= 1249 && Ter.Res <= 1252)
                            {
                                Data->bLabelSet[Ter.Res - 1249] = true;
                                Data->Labels[Ter.Res - 1249] = House;
                            }
                            else
                                Data->Houses.push_back(House);
                            House.Ids = 0;
                        }
                    }
                }
            }
            else if (Ini.is_header("Systems"))
            {
                while (Ini.read_value())
                {
                    if (Ini.is_value("format"))
                        Ter.Fmt = TerritoryStoreString(*Data, Ini.get_value_string(), true);
                    else if (Ini.is_value("format_id"))
                        Ter.Fmt = Ini.get_value_int(0);
                    else if (Ini.is_value("systems"))
                    {
                        if (Ter.Fmt != 0)
                            TerritorySetSystems(*Data, Ini, Ter);
                    }
                }
            }
            else if (Ini.is_header("Settings"))
            {
                while (Ini.read_value())
                {
                    if (Ini.is_value("caps"))
                    {
                        if (!Ini.get_value_bool(0))
                            Data->bCaps = false;
                    }
                    else if (Ini.is_value("codepage"))
                        Data->CodePage = TerritoryParseCodePage(Ini.get_value_string(0));
                }
            }
        }
        Ini.close();
        S_Data = Data;
        return S_Data;
    }

    // find_territory: the system's nickname hash first (DAT_00673354), then its strid_name.
    bool TerritoryFind(FTerritoryData const& Data, int SystemIds, FTerritory* Out)
    {
        std::map<int, FTerritory>::const_iterator It =
            Data.Territories.find(static_cast<int>(GetPlayerStarSystemIdRetail()));
        if (It == Data.Territories.end())
            It = Data.Territories.find(SystemIds);
        if (It == Data.Territories.end())
            return false;
        *Out = It->second;
        return true;
    }

    // A format: a stored string, or ids (count 0x40, as the plugin) -- Default for 0.
    void TerritoryFormat(FTerritoryData const& Data, int Fmt, unsigned Default, wchar_t* Out)
    {
        if (Fmt < 0)
        {
            wcscpy(Out, Data.Store[static_cast<size_t>(~Fmt)].c_str());
            return;
        }
        GetIdsStringWWithRawFallback(Fmt != 0 ? static_cast<unsigned>(Fmt) : Default, Out, 0x40);
    }
}

FTerritoryNavMapHouse const* TerritoryNavMapLabel(int Index)
{
    FTerritoryData const* const Data = TerritoryData();
    if (Data == nullptr || Index < 0 || Index >= 4 || !Data->bLabelSet[Index])
        return nullptr;
    return &Data->Labels[Index];
}

FTerritoryNavMapHouse const* TerritoryNavMapHouses(unsigned* OutCount)
{
    FTerritoryData const* const Data = TerritoryData();
    if (Data == nullptr || Data->Houses.empty())
    {
        *OutCount = 0;
        return nullptr;
    }
    *OutCount = static_cast<unsigned>(Data->Houses.size());
    return &Data->Houses[0];
}
#endif

namespace
{
    // CharUpperW on the caption (0x0045af5a, 0x0045b0d8, 0x0045b142, 0x0045b278).
    void ArrivalUpper(wchar_t* Text)
    {
#ifdef FREELANCER_ADOXA
        // Port-only, adoxa's territory.dll (docs/adoxa.md; 0x0045af5b / 0x0045b0d9 / 0x0045b143
        // / 0x0045b279): [Settings] caps = false turned each PUSH 0x0066fc60 into 0x0066fc5e --
        // the empty string before the text -- so the caption keeps its case.
        FTerritoryData const* const Data = TerritoryData();
        if (Data != nullptr && !Data->bCaps)
            return;
#endif
        CharUpperW(Text);
    }
}

NnArrivalText::NnArrivalText()
{
    // FUN_0045b530 0x0045b569..0x0045b583: FUN_0059f860, vptrs, DAT_0066d398 = this, +0x338 = 0.
    G_NnArrivalText = this;
    bWaitForLetterbox = 0;
}

NnArrivalText::~NnArrivalText()
{
    // FUN_0045abb0: the vptrs, DAT_0066d398 = 0, JMP FUN_0059fa50 (the WinControl dtor).
    G_NnArrivalText = nullptr;
}

bool NnArrivalText::Create(Win3D* NewParent, void* Data)
{
    // FUN_0045abd0 (RET 8).
    (void)NewParent;

    // 0x0045abd4..0x0045ac22: FUN_005a0e30 "ArrivalText" / "PageHeader" at (-0.45f, 0.24f, 0),
    // no hardpoint, 0.95f x 0.06f, 1.4f, ids 0, 0, 0, last byte 1 -> +0x32c.
    float const CaptionPosition[3] = {NnFloatBits(0xbee66666), NnFloatBits(0x3e75c28f), 0.0f};
    Caption = static_cast<NnTextControl*>(CreateTextControl(
        "ArrivalText", "PageHeader", CaptionPosition, nullptr, NnFloatBits(0x3f733333),
        NnFloatBits(0x3d75c28f), NnFloatBits(0x3fb33333), 0, 0, 0, 1));

    // 0x0045ac1b..0x0045ac2e: the caption's slot 42 (0x33, &DAT_00679b90, 1) -- the colour
    // override. No null test on the control.
    Caption->SetProperty(0x33, reinterpret_cast<uintptr_t>(&G_NnPaletteArgb_679b90), 1);
    // 0x0045ac34..0x0045ac3a: the caption hidden (flags &= 0xfc).
    Caption->Flags = static_cast<unsigned char>(Caption->Flags & 0xfc);

#ifdef FREELANCER_ADOXA
    // Port-only, adoxa's territory.dll v1.02+ (docs/adoxa.md; 0x0045ac3e JMP 0x0045acb1): with
    // any territory defined, the caption's Font::String is multi-line (+0x30 = 1) so a '^' in a
    // format breaks the line.
    {
        FTerritoryData const* const Territory = TerritoryData();
        if (Territory != nullptr && !Territory->Territories.empty())
            Caption->GetFontString()->bMultiLine = 1;
    }
#endif

    // 0x0045ac3e..0x0045ac73: slot 31 SetOffset(0, 0, -1.0f), the vector passed by value.
    SetOffset(0.0f, 0.0f, -1.0f);
    // 0x0045ac76..0x0045ac7e: slot 5 SetPosition(this + 0x60).
    SetPosition(Position);

    // 0x0045ac8c / 0x0045ac96
    HoldTime = 2.0f;
    Delay = 4.0f;

    // 0x0045ac81..0x0045aca7: FUN_004b5060 with [this + 4] (the window's current parent, not
    // NewParent) and Data, SETNZ.
    return Win3D::Create(GetParent(), Data);
}

void NnArrivalText::DestroySelf()
{
    Win3D* Child = GetChildHead();
    while (Child != nullptr)
    {
        Win3D* const Next = Child->GetNextSibling();
        Win3DDeleteTree(Child);
        Child = Next;
    }
    Destroy();
    delete this;
}

void NnArrivalText::Update()
{
    // LAB_0045acc0. 0x0045acc8..0x0045ad07: FUN_0045a470 (NN_MainButton has a panel open) tears
    // the caption down.
    if (NnMainButtonHasActivePanel())
    {
        DestroySelf();
        return;
    }

    // 0x0045ad08..0x0045ad49: waiting for the letterbox. While it is up (FUN_0041a3e0) the
    // caption stays hidden and nothing else runs; once it is down a delay at or below zero (FCOMP
    // 0.0f, TEST AH,0x41 / JP skips -- NaN skips) shows it.
    if (bWaitForLetterbox != 0)
    {
        if (IsLetterboxVisible())
        {
            Caption->Flags = static_cast<unsigned char>(Caption->Flags & 0xfc);
            return;
        }
        if (Delay <= 0.0f)
            Caption->Flags = static_cast<unsigned char>(Caption->Flags | 3);
    }

    // 0x0045ad4d..0x0045adb7: the caption's visible bit is sampled here. A caption that is
    // showing with its delay spent goes away as soon as the mission-objective banner
    // (DAT_00672400, MissionObjectiveWindow) or HUD_Comm's window (FUN_004cc8d0) is up.
    bool const bWasVisible = ((Caption->Flags >> 1) & 1) != 0;
    if (Delay <= 0.0f && bWasVisible)
    {
        if (G_MissionObjectiveWindow != nullptr || HudCommIsWindowOpen())
        {
            DestroySelf();
            return;
        }
    }

    // 0x0045adb8: FUN_005a17b0, the base Update.
    Win3D::Update();

    if ((Caption->Flags & 2) == 0)
    {
        // 0x0045adcb..0x0045ae03: hidden -- unless one of those windows is up, the delay runs
        // down by the capped frame time (in double, stored as float) and a negative delay
        // (TEST AH,5 / JP skips) shows the caption.
        if (G_MissionObjectiveWindow == nullptr && !HudCommIsWindowOpen())
        {
            Delay = static_cast<float>(static_cast<double>(Delay) - GetClientFrameTimeCapped());
            if (Delay < 0.0f)
                Caption->Flags = static_cast<unsigned char>(Caption->Flags | 3);
        }
    }
    else if (Caption->bTypewriter == 0)
    {
        // 0x0045ae2c..0x0045ae8a: showing and fully typed (+0x362 clear) -- the hold time runs
        // down the same way; a negative one tears the caption down.
        HoldTime = static_cast<float>(static_cast<double>(HoldTime) - GetClientFrameTimeCapped());
        if (HoldTime < 0.0f)
        {
            DestroySelf();
            return;
        }
    }

    // 0x0045ae07..0x0045ae1f: a caption that became visible this frame starts typing
    // (property 0x50 with 1 and 60 ms per character).
    if (!bWasVisible && (Caption->Flags & 2) != 0)
        Caption->SetProperty(0x50, 1, 0x3c);
}

void NnArrivalText::ShowBaseArrival(float ArrivalTime)
{
    // FUN_0045ae90 (RET 4). 0x0045ae9b..0x0045aea2: FUN_004c4810 -- only docked.
    if (!IsPlayerDockedRetail())
        return;
    // 0x0045aead
    bWaitForLetterbox = 0;

    // 0x0045aea8..0x0045aee3: FUN_0043bbe0 on DAT_00668708 (the base's strid_name), then the
    // system's; either one zero returns.
    int const BaseIds = GetClientCurrentBaseStridName();
    int const SystemIds = PlayerSystemStridName();
    if (BaseIds == 0 || SystemIds == 0)
        return;

    // 0x0045aee9..0x0045af5f: ids 0x55c is the format; base and system names into the two halves
    // of scratch A; swprintf into scratch B; CharUpperW.
    wchar_t Format[kArrivalFormatChars];
    GetIdsStringWWithRawFallback(0x55c, Format, kArrivalFormatChars);
    int const Half = G_NnTextScratchCapacity / 2;
    wchar_t* const SecondHalf = G_NnTextScratchA + Half;
    GetIdsStringWWithRawFallback(static_cast<unsigned>(BaseIds), G_NnTextScratchA, Half);
    GetIdsStringWWithRawFallback(static_cast<unsigned>(SystemIds), SecondHalf, Half);
    _swprintf(G_NnTextScratchB, Format, G_NnTextScratchA, SecondHalf);
    ArrivalUpper(G_NnTextScratchB);

    // 0x0045af65..0x0045af76: the caption's property 0x1d (the text).
    Caption->SetProperty(0x1d, reinterpret_cast<uintptr_t>(G_NnTextScratchB), 0);
    int const Length = static_cast<int>(wcslen(G_NnTextScratchB));

    // 0x0045af87..0x0045afcd: only a positive ArrivalTime (TEST AH,0x41 / JNZ skips) sets the
    // delay so typing (0.06f a character) plus the hold ends with it; a negative result (TEST
    // AH,5 / JP skips) is clamped to 0.
    if (!(ArrivalTime > 0.0f))
        return;
    Delay = ArrivalTime - (static_cast<float>(Length) * kArrivalSecondsPerChar + HoldTime);
    if (Delay < 0.0f)
        Delay = 0.0f;
}

void NnArrivalText::ShowSystemArrival(bool bResetDelay)
{
    // FUN_0045aff0 (RET 4). 0x0045affb
    bWaitForLetterbox = 1;

    int const SystemIds = PlayerSystemStridName();

#ifdef FREELANCER_ADOXA
    // Port-only, adoxa's territory.dll v1.03 (docs/adoxa.md; 0x0045b020 JMP Territory_Patch): a
    // system territory.ini names (by nickname, then strid_name) gets its own house / format.
    FTerritoryData const* const Territory = TerritoryData();
    FTerritory Ter;
    if (Territory != nullptr && TerritoryFind(*Territory, SystemIds, &Ter))
    {
        wchar_t TerFormat[kArrivalFormatChars];
        int const Half = G_NnTextScratchCapacity / 2;
        wchar_t* const SecondHalf = G_NnTextScratchA + Half;
        if (Ter.Res == 0)
        {
            // [Systems] ("sys"): the format (ids 0x55d's place, 0x0045b108 / 0x0045b10e) with
            // the system alone, then the retail tail -- delay 2.0f. No zero-system test.
            TerritoryFormat(*Territory, Ter.Fmt, 0x55d, TerFormat);
            GetIdsStringWWithRawFallback(static_cast<unsigned>(SystemIds), G_NnTextScratchA,
                                         Half);
            _swprintf(G_NnTextScratchB, TerFormat, G_NnTextScratchA);
            ArrivalUpper(G_NnTextScratchB);
            Caption->SetProperty(0x1d, reinterpret_cast<uintptr_t>(G_NnTextScratchB), 0);
            Delay = 2.0f;
        }
        else if (Ter.Res > 0 && Ter.Fmt == 0)
        {
            // A house by ids with the retail format: the retail house path from 0x0045b057
            // (its zero-system test included) with the house as the region.
            if (SystemIds == 0)
                return;
            GetIdsStringWWithRawFallback(0x55e, TerFormat, kArrivalFormatChars);
            GetIdsStringWWithRawFallback(static_cast<unsigned>(SystemIds), G_NnTextScratchA,
                                         Half);
            GetIdsStringWWithRawFallback(static_cast<unsigned>(Ter.Res), SecondHalf, Half);
            _swprintf(G_NnTextScratchB, TerFormat, G_NnTextScratchA, SecondHalf);
            ArrivalUpper(G_NnTextScratchB);
            Caption->SetProperty(0x1d, reinterpret_cast<uintptr_t>(G_NnTextScratchB), 0);
        }
        else
        {
            // "tp1": the house format (ids 0x55e when none), the system into the first half
            // and the house -- by ids (0x0045b083) or the stored name copied into the second
            // half (0x0045b0bf) -- then the retail house tail. No zero-system test.
            TerritoryFormat(*Territory, Ter.Fmt, 0x55e, TerFormat);
            GetIdsStringWWithRawFallback(static_cast<unsigned>(SystemIds), G_NnTextScratchA,
                                         Half);
            if (Ter.Res > 0)
                GetIdsStringWWithRawFallback(static_cast<unsigned>(Ter.Res), SecondHalf, Half);
            else
                wcscpy(SecondHalf, Territory->Store[static_cast<size_t>(~Ter.Res)].c_str());
            _swprintf(G_NnTextScratchB, TerFormat, G_NnTextScratchA, SecondHalf);
            ArrivalUpper(G_NnTextScratchB);
            Caption->SetProperty(0x1d, reinterpret_cast<uintptr_t>(G_NnTextScratchB), 0);
        }
        // 0x0045b16e..0x0045b179
        if (bResetDelay)
            Delay = 2.0f;
        return;
    }
#endif

    // 0x0045b020..0x0045b055: the region caption by the strid_name's place in 0x30001..0x30018
    // (byte table 0x0045b1a0 over the jump table 0x0045b190).
    unsigned const Index = static_cast<unsigned>(SystemIds) - 0x30001u;
    unsigned RegionIds = 0;
    if (Index <= 4)
        RegionIds = 0x4e1;
    else if (Index <= 10)
        RegionIds = 0x4e2;
    else if (Index <= 16)
        RegionIds = 0x4e4;
    else if (Index <= 0x17)
        RegionIds = 0x4e3;

    // 0x0045b057
    if (SystemIds == 0)
        return;

    wchar_t Format[kArrivalFormatChars];
    if (RegionIds != 0)
    {
        // 0x0045b071..0x0045b0fb: ids 0x55e, the system and the region into the two halves.
        GetIdsStringWWithRawFallback(0x55e, Format, kArrivalFormatChars);
        int const Half = G_NnTextScratchCapacity / 2;
        wchar_t* const SecondHalf = G_NnTextScratchA + Half;
        GetIdsStringWWithRawFallback(static_cast<unsigned>(SystemIds), G_NnTextScratchA, Half);
        GetIdsStringWWithRawFallback(RegionIds, SecondHalf, Half);
        _swprintf(G_NnTextScratchB, Format, G_NnTextScratchA, SecondHalf);
        ArrivalUpper(G_NnTextScratchB);
        Caption->SetProperty(0x1d, reinterpret_cast<uintptr_t>(G_NnTextScratchB), 0);
    }
    else
    {
        // 0x0045b0fd..0x0045b164: ids 0x55d with the system alone; the delay becomes 2.0f.
        GetIdsStringWWithRawFallback(0x55d, Format, kArrivalFormatChars);
        GetIdsStringWWithRawFallback(static_cast<unsigned>(SystemIds), G_NnTextScratchA,
                                     G_NnTextScratchCapacity / 2);
        _swprintf(G_NnTextScratchB, Format, G_NnTextScratchA);
        ArrivalUpper(G_NnTextScratchB);
        Caption->SetProperty(0x1d, reinterpret_cast<uintptr_t>(G_NnTextScratchB), 0);
        Delay = 2.0f;
    }

    // 0x0045b16e..0x0045b179
    if (bResetDelay)
        Delay = 2.0f;
}

void NnArrivalText::ShowNamedArrival(unsigned NameIds)
{
    // FUN_0045b1c0 (RET 4). 0x0045b1cb
    bWaitForLetterbox = 0;

    int const SystemIds = PlayerSystemStridName();
    // 0x0045b1f0..0x0045b201
    if (NameIds == 0 || SystemIds == 0)
        return;

    // 0x0045b207..0x0045b29a: ids 0x55c, NameIds and the system into the two halves, the text,
    // delay 2.0f.
    wchar_t Format[kArrivalFormatChars];
    GetIdsStringWWithRawFallback(0x55c, Format, kArrivalFormatChars);
    int const Half = G_NnTextScratchCapacity / 2;
    wchar_t* const SecondHalf = G_NnTextScratchA + Half;
    GetIdsStringWWithRawFallback(NameIds, G_NnTextScratchA, Half);
    GetIdsStringWWithRawFallback(static_cast<unsigned>(SystemIds), SecondHalf, Half);
    _swprintf(G_NnTextScratchB, Format, G_NnTextScratchA, SecondHalf);
    ArrivalUpper(G_NnTextScratchB);
    Caption->SetProperty(0x1d, reinterpret_cast<uintptr_t>(G_NnTextScratchB), 0);
    Delay = 2.0f;
}

bool NnArrivalText::IsCaptionVisible() const
{
    // FUN_0045b2c0: MOV EAX,[ECX+0x32c] / MOV AL,[EAX+0x6c] / SHR AL,1 / AND AL,1.
    return ((Caption->Flags >> 1) & 1) != 0;
}

void NnArrivalTextShow()
{
    // FUN_0045b310 (cdecl): ensure, then FUN_0045aff0(0) (0x0045b338..0x0045b33a).
    NnArrivalText* const Self = EnsureNnArrivalText();
    if (Self == nullptr)
        return;
    Self->ShowSystemArrival(false);
}

void NnArrivalTextShowBase(float ArrivalTime)
{
    // FUN_0045b2d0 (cdecl): ensure, then FUN_0045ae90(ArrivalTime).
    NnArrivalText* const Self = EnsureNnArrivalText();
    if (Self == nullptr)
        return;
    Self->ShowBaseArrival(ArrivalTime);
}

void NnArrivalTextShowNamed(unsigned NameIds)
{
    // FUN_0045b340 (cdecl): ensure, then FUN_0045b1c0(NameIds).
    NnArrivalText* const Self = EnsureNnArrivalText();
    if (Self == nullptr)
        return;
    Self->ShowNamedArrival(NameIds);
}

void NnArrivalTextDestroy()
{
    // FUN_0045b380 (cdecl): no window -> nothing; else the teardown.
    NnArrivalText* const Self = G_NnArrivalText;
    if (Self == nullptr)
        return;
    Self->DestroySelf();
}

void NnArrivalTextHurry()
{
    // FUN_0045b3c0 (cdecl). 0x0045b3cb..0x0045b3fc: a delay above 0 (TEST AH,0x41 / JNZ goes to
    // the teardown -- NaN too) is cut to 1.0f when above it; otherwise the window goes.
    NnArrivalText* const Self = G_NnArrivalText;
    if (Self == nullptr)
        return;
    if (Self->Delay > 0.0f)
    {
        if (Self->Delay > 1.0f)
            Self->Delay = 1.0f;
        return;
    }
    Self->DestroySelf();
}

void NnArrivalTextShowRaw(float Delay, uintptr_t Arg)
{
    // FUN_0045b430 (cdecl): ensure; +0x334 = Delay (dword copy), +0x338 = 0, then the caption's
    // slot 42 (0x1e, Arg, 0).
    NnArrivalText* const Self = EnsureNnArrivalText();
    if (Self == nullptr)
        return;
    Self->Delay = Delay;
    Self->bWaitForLetterbox = 0;
    Self->Caption->SetProperty(0x1e, Arg, 0);
}

void NnArrivalTextShowSystemNow()
{
    // FUN_0045b490 (cdecl): ensure, then FUN_0045aff0(1).
    NnArrivalText* const Self = EnsureNnArrivalText();
    if (Self == nullptr)
        return;
    Self->ShowSystemArrival(true);
}

void NnMainButtonOnModalOpen()
{
    // FUN_0045a460: MOV ECX,[DAT_0066d3f0] / TEST / JZ RET / JMP FUN_0045cf60.
    if (G_NnMainButton == nullptr)
        return;
    G_NnMainButton->ClosePanel();
}

void NnMainButtonSetPanelOrigin(int PanelId, float const* Origin)
{
    // FUN_0045a780: MOV ECX,[DAT_0066d3f0] / TEST / JZ RET / FUN_0045c7a0(PanelId, Origin).
    if (G_NnMainButton == nullptr)
        return;
    G_NnMainButton->SetPanelOrigin(PanelId, Origin);
}

WinControl* NnMainButtonGetPanelButton(int PanelId)
{
    // FUN_0045a7a0: null -> XOR EAX,EAX; else FUN_0045c820(PanelId).
    if (G_NnMainButton == nullptr)
        return nullptr;
    return G_NnMainButton->GetPanelButton(PanelId);
}

bool NnMainButtonHasActivePanel()
{
    // FUN_0045a470: null -> XOR AL,AL; else JMP FUN_0045da00 (`[ECX + 0x3a8] != 0`).
    if (G_NnMainButton == nullptr)
        return false;
    return G_NnMainButton->HasActivePanel();
}

WinControl* G_NnMissionMessage = nullptr; // DAT_00671ff4

void NnMissionMessageDestroy()
{
    // FUN_0048a130: with a NeuroNetMissionMessage window, DAT_0067dcc8 = 0, FUN_0043d2a0 on every
    // child (next sibling read first), slot 10 Destroy, slot 0 with 1. The pointer is not
    // cleared here; the window's dtor (0x0048a46c) does that.
    WinControl* const Window = G_NnMissionMessage;
    if (Window == nullptr)
        return;
    G_bNnScreenUp = false;
    Win3DDeleteTree(Window);
}

unsigned char G_bNnStoryStarKeepPending = 0; // DAT_0066d35a

void NnSystemInit(bool bCreateMainButton)
{
    // FUN_0045a100 (cdecl). Nothing when NN_MainButton already exists.
    if (G_NnMainButton != nullptr)
        return;
    G_bNnStoryStarKeepPending = 0;
    // 0x0045a110: FUN_00459830 -- the KnowledgeMap singleton DAT_0066d334
    // (interface\KnowledgeMap.ini).
    KnowledgeMapCreate();
    // 0x0045a115: FUN_00458790 -- the InfocardMap singleton DAT_0066d320
    // (interface\InfocardMap.ini).
    InfocardMapCreate();
    // 0x0045a11a..0x0045a130: FUN_0059db20("NN_MainButton", "NN_MainButton", 0, 0).
    if (bCreateMainButton)
        WinFactoryCreate("NN_MainButton", "NN_MainButton", nullptr, nullptr);
    // 0x0045a138: JMP FUN_00489de0.
    NnVoiceInit();
}

void NnSystemShutdown()
{
    // FUN_0045a140 (cdecl).
    // 0x0045a140..0x0045a15d: NN_MainButton slot 10 Destroy, then (re-read) slot 0 with 1.
    if (G_NnMainButton != nullptr)
    {
        G_NnMainButton->Destroy();
        if (G_NnMainButton != nullptr)
            delete G_NnMainButton;
    }
    // 0x0045a15f..0x0045a174: the trade window's slot 42 (0xef02, 0, 0).
    if (G_NnTrade != nullptr)
        G_NnTrade->SetProperty(0xef02, 0, 0);
    // 0x0045a17a: FUN_00459900 -- free the KnowledgeMap.
    KnowledgeMapDestroy();
    // 0x0045a17f: FUN_00458860 -- free the InfocardMap.
    InfocardMapDestroy();
    // 0x0045a184: FUN_0045b380.
    NnArrivalTextDestroy();
    // 0x0045a189: FUN_004b9bb0 -- the story star reset (the DAT_00672328 pending FmtStr list
    // unless DAT_0066d35a, then the DAT_00672400 banner).
    StoryStarReset();
    // 0x0045a18e: JMP FUN_0048a130.
    NnMissionMessageDestroy();
}

void NnMainButtonOnUnclaimedMouse(unsigned Msg, unsigned WParam, unsigned LParam)
{
    // FUN_0045a270 (cdecl, 3 args).
    (void)WParam;
    (void)LParam;

    // 0x0045a28a..0x0045a2a0: FUN_0041dd90() and DAT_0067dcc8 == 0.
    if (GetClientMouseCursorDrawFlag() == 0)
        return;
    if (G_bNnScreenUp)
        return;

    // 0x0045a2a6: FUN_004c4810 -- `(DAT_00673358 & 0x3fffffff) != 0`, the player is docked.
    // In space the message goes to FUN_004c80f0(Msg, WParam, LParam) (0x0045a424).
    if ((GetPlayerBaseIdRetail() & 0x3fffffffu) == 0)
    {
        OnMouseFlightRawMessage(Msg);
        return;
    }

    // 0x0045a2b3: docked, and no NN_MainButton -> nothing.
    if (G_NnMainButton == nullptr)
        return;
    // 0x0045a2bf..0x0045a2c6: FUN_00442720 -- a NavBar with one of the service windows up.
    if (NavBarHasServiceWindow())
        return;
    // 0x0045a2cc..0x0045a2d9: FUN_0045da00 -- the NN_MainButton has a panel open.
    if (G_NnMainButton->HasActivePanel())
        return;

    // 0x0045a2df..0x0045a32c: a hover record -- caption null, the Font::String constructed
    // (FUN_004144b0), IdsAlt 0, Ids -1, +0x44 0, the caption cleared (FUN_00414280), +0x60 0 --
    // then Ids = IdsAlt = 0x45e.
    FToolTipHoverInfo Record; // caption null + FUN_004144b0: the record's constructor
    ToolTipHoverReset(&Record);
    Record.Ids = 0x45e;
    Record.IdsAlt = 0x45e;
    // 0x0045a330..0x0045a36a: in the base's "Cityscape" room (the current room runtime's id
    // +0x38 against MakeLocationID(BaseData's id, "Cityscape"); FUN_0043a460 / FUN_0043b630,
    // both null-tested) the ids are 0x3a0 instead.
    FRoomRuntime* const Runtime = static_cast<FRoomRuntime*>(GetClientCurrentLocationRuntime());
    BaseData* const Base = GetClientCurrentLocationBaseData();
    if (Runtime != nullptr && Base != nullptr &&
        GetRoomRuntimeRoomId(Runtime) == MakeLocationID(Base->get_base_id(), "Cityscape"))
    {
        Record.Ids = 0x3a0;
        Record.IdsAlt = 0x3a0;
    }

    // 0x0045a36e..0x0045a379: FUN_004b62d0(&record, 8.0f) -- the rollover shows the record for
    // eight seconds.
    NnRolloverShowHoverGlobal(&Record, NnFloatBits(0x41000000));
    // 0x0045a37e..0x0045a386: FUN_00489e80(DAT_0066d344, 0) -- the voice line.
    NnVoiceEnqueue(G_NnVoiceClickOnCharactersId, 0);
    // 0x0045a38e..0x0045a40e: the record's dtor inlined (FUN_00444ee0) -- ~FToolTipHoverInfo.
}

unsigned char NnModalPauseGame()
{
    // FUN_004a7670: 004a7671 PUSH 1 / CALL FUN_0042d6f0; 004a7678 CALL FUN_0041dd90, MOV BL,AL;
    // 004a767d PUSH 1 / CALL FUN_0041dda0; 004a7689 MOV AL,BL.
    SetClientServerTickPause(true);
    unsigned char const bPrevious = GetClientMouseCursorDrawFlag();
    SetClientMouseCursorDrawFlag(1);
    return bPrevious;
}

void NnModalResumeGame(unsigned char bCursorDrawFlag)
{
    // FUN_004a7690: 004a7690 PUSH 0 / CALL FUN_0042d6f0; 004a76a2 JMP FUN_0041dda0 with the
    // argument slot rewritten to param_1.
    SetClientServerTickPause(false);
    SetClientMouseCursorDrawFlag(bCursorDrawFlag);
}
