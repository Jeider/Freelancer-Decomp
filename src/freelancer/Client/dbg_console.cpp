// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: the beta's console. See dbg_console.h.

#include "dbg_console.h"

#ifdef FREELANCER_DBG_OPTIONS

#include "font_atlas.h"
#include "font_imp.h"
#include "font_string.h"
#include "globals.h"
#include "player_spawn.h"      // GetPlayerShipObject
#include "win3d_immediate.h"
#include "win3d_renderables.h" // UiOverlayPrepPipeline

#include "client_state.h"     // QueueLoadGameCharacter (load)
#include "game_options.h"      // kGameOptDisableCollide (ghost)
#include "hud_waypoint.h"      // GetHudWaypoint (jump to a targeted waypoint)
#include "ids_strings.h"       // GetIdsStringW (base / system names)
#include "nav_bar.h"           // NavBar (launch)
#include "player_behavior.h"   // GetPlayerObjRW
#include "space_state.h"       // SetPendingJumpSystem (system)
#include "win3d.h"             // Win3DFindByName

#include "common_cobject.h"
#include "common_id.h"
#include "common_iface.h"      // IObjRW::get_position (waypoint)
#include "common_misc.h"       // SinglePlayer, GetUserDataPath
#include "common_server_types.h" // CHARACTER_ID
#include "common_universe.h"
#include "port_config.h"
#include "port_console_api.h"

#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <string>
#include <vector>
#include <windows.h>

namespace
{
    // The beta's TextDisplay at 0x00686318: 256 lines of 80 wide characters, 10 shown by default
    // (`lines` takes 2..40), the input buffer 0x006862c4 holds 79 characters.
    int const kMaxLines = 256;
    int const kMaxInput = 79;

    bool G_bOpen = false;
    std::deque<std::wstring> G_Lines;
    int G_Visible = 10;
    int G_Scroll = 0;           // lines scrolled up from the bottom
    bool G_bQuiet = false;
    std::string G_Input;
    std::vector<std::string> G_History;
    int G_HistoryCursor = 0;
    unsigned G_FrameCounter = 0;

    struct FConsoleText
    {
        FFontString Rows[41];
        std::wstring Shown[41];
        int RowHeight = 0;
    };
    FConsoleText* G_Text = nullptr;

    void Print(wchar_t const* Text)
    {
        G_Lines.push_back(std::wstring(Text).substr(0, 80));
        while (static_cast<int>(G_Lines.size()) > kMaxLines)
            G_Lines.pop_front();
        G_Scroll = 0;
    }

    void Printf(char const* Format, ...)
    {
        if (G_bQuiet)
            return;
        char Narrow[256];
        va_list Args;
        va_start(Args, Format);
        _vsnprintf(Narrow, sizeof(Narrow) - 1, Format, Args);
        va_end(Args);
        Narrow[sizeof(Narrow) - 1] = '\0';
        wchar_t Wide[256];
        MultiByteToWideChar(CP_ACP, 0, Narrow, -1, Wide, 256);
        Print(Wide);
    }

    // ---- Commands (beta CONSOLE table, 0x00690fb0) -------------------------------------------

    typedef void (*FCommandFn)(char const* Args);

    struct FCommand
    {
        char const* Name;
        char const* Alias;
        char const* Help;
        FCommandFn Fn;
    };

    void CmdHelp(char const* Args);

    void CmdTimeScale(char const* Args)
    {
        // Beta 0x00550b10: atof, at least 0.01 (no upper limit in the beta; the port stops at
        // 10, as IVP gets dt times the scale), applied by the frame timer in single player.
        if (*Args != '\0')
        {
            float Scale = static_cast<float>(std::atof(Args));
            if (Scale < 0.01f)
                Scale = 0.01f;
            if (Scale > 10.0f)
                Scale = 10.0f;
            SetClientTimeScale(Scale);
        }
        Printf("TimeScale = %g%s", static_cast<double>(GetClientTimeScale()),
               SinglePlayer() ? "" : " (single player only)");
    }

    void CmdTime(char const*)
    {
        Printf("Time = %0.2f seconds", GetClientElapsedTime());
    }

    void CmdMaxFps(char const* Args)
    {
        // Beta 0x00550c80: the busy-wait cap (retail DAT_00610a0c), at least 1.
        if (*Args != '\0')
        {
            float Cap = static_cast<float>(std::atof(Args));
            if (Cap < 1.0f)
                Cap = 1.0f;
            SetClientFpsCap(Cap);
        }
        Printf("max_fps = %g", static_cast<double>(GetClientFpsCap()));
    }

    void CmdLines(char const* Args)
    {
        if (*Args != '\0')
        {
            int const Lines = std::atoi(Args);
            G_Visible = Lines < 2 ? 2 : Lines > 40 ? 40 : Lines;
        }
        Printf("lines = %d", G_Visible);
    }

    void CmdClear(char const*)
    {
        G_Lines.clear();
        G_Scroll = 0;
    }

    void CmdQuiet(char const*)
    {
        G_bQuiet = !G_bQuiet;
        if (!G_bQuiet)
            Printf("quiet off");
    }

    void RunJump(FPortConsoleServerFn Server, FPortConsoleJump& Jump);
    bool ReadVector(char const*& Text, Vector& Out);
    FPortConsoleServerFn ServerConsole();

    void CmdPos(char const* Args)
    {
        CObject const* const Ship = static_cast<CObject const*>(GetPlayerShipObject());
        if (Ship == nullptr)
        {
            Printf("* No player ship.");
            return;
        }
        if (*Args != '\0')
        {
            // pos x,y,z: move the ship there in this system, keeping its orientation.
            FPortConsoleJump Jump = {};
            Jump.Mode = 3;
            char const* Text = Args;
            if (!ReadVector(Text, Jump.Offset))
            {
                Printf("* pos x,y,z");
                return;
            }
            FPortConsoleServerFn const Server = ServerConsole();
            if (Server == nullptr)
            {
                Printf("* Single player only.");
                return;
            }
            RunJump(Server, Jump);
            return;
        }
        Vector const& Pos = Ship->get_position();
        Printf("pos = %.1f, %.1f, %.1f", static_cast<double>(Pos.x), static_cast<double>(Pos.y),
               static_cast<double>(Pos.z));
    }

    void CmdQuit(char const*)
    {
        PostQuitMessage(0);
    }

    // ---- adoxa's console.dll commands (save, load, base, system, jump, launch, ghost) -------

    FPortConsoleServerFn ServerConsole()
    {
        // Single player loads Server.dll into the process; the client does not link it.
        HMODULE const Server = GetModuleHandleA("server.dll");
        return Server != nullptr ? reinterpret_cast<FPortConsoleServerFn>(GetProcAddress(Server, PORT_CONSOLE_SERVER_EXPORT))
                                 : nullptr;
    }

    bool InSpace()
    {
        return GetPlayerObjRW() != nullptr && GetPlayerShipObject() != nullptr;
    }

    std::wstring Widen(char const* Text)
    {
        wchar_t Wide[256];
        MultiByteToWideChar(CP_ACP, 0, Text, -1, Wide, 256);
        return Wide;
    }

    bool ContainsNoCase(std::wstring const& Text, std::wstring const& Part)
    {
        if (Part.empty() || Text.size() < Part.size())
            return false;
        for (size_t At = 0; At + Part.size() <= Text.size(); ++At)
            if (_wcsnicmp(Text.c_str() + At, Part.c_str(), Part.size()) == 0)
                return true;
        return false;
    }

    // console.dll fl_name: "" or one character -> "qsave<c>.fl", "Quick Save <c>"; else
    // "<CreateID>.fl" with the text as the description.
    void SaveName(char const* Desc, char* File, size_t FileSize, std::wstring& Description)
    {
        if (Desc[0] == '\0' || Desc[1] == '\0')
        {
            char Slot = Desc[0] == ':' ? '?' : static_cast<char>(std::toupper(static_cast<unsigned char>(Desc[0])));
            _snprintf(File, FileSize - 1, "qsave%s%c.fl", "", Slot);
            if (Slot == '\0')
                _snprintf(File, FileSize - 1, "qsave.fl");
            File[FileSize - 1] = '\0';
            Description = L"Quick Save";
            if (Slot != '\0')
            {
                Description += L' ';
                Description += static_cast<wchar_t>(Slot);
            }
        }
        else
        {
            _snprintf(File, FileSize - 1, "%x.fl", CreateID(Desc));
            File[FileSize - 1] = '\0';
            Description = Widen(Desc);
        }
    }

    void CmdSave(char const* Args)
    {
        FPortConsoleServerFn const Server = ServerConsole();
        if (Server == nullptr || !SinglePlayer())
        {
            Printf("* Single player only.");
            return;
        }
        char File[64];
        std::wstring Description;
        SaveName(Args, File, sizeof(File), Description);
        FPortConsoleSave Save = {File, Description.c_str()};
        Printf(Server(kPortConsoleSave, &Save) ? "Game saved (%s)." : "* Save failed (%s).", File);
    }

    void CmdLoad(char const* Args)
    {
        char File[64];
        std::wstring Description;
        SaveName(Args, File, sizeof(File), Description);
        char Path[512] = {};
        GetUserDataPath(Path);
        char Folder[64];
        PortConfigString("ModServer", "account_folder", "Accts", Folder, sizeof(Folder));
        std::strncat(Path, "\\", sizeof(Path) - std::strlen(Path) - 1);
        std::strncat(Path, Folder, sizeof(Path) - std::strlen(Path) - 1);
        std::strncat(Path, "\\SinglePlayer\\", sizeof(Path) - std::strlen(Path) - 1);
        std::strncat(Path, File, sizeof(Path) - std::strlen(Path) - 1);
        if (GetFileAttributesA(Path) == INVALID_FILE_ATTRIBUTES)
        {
            Printf("* Game not found (%s).", File);
            return;
        }
        CHARACTER_ID Character;
        std::strncpy(Character.Buffer, File, sizeof(Character.Buffer) - 1);
        QueueLoadGameCharacter(&Character, true);
        G_bOpen = false;
    }

    Universe::IBase* FindBase(char const* Name)
    {
        // console.dll cmdBase: the nickname, else the first base whose name contains the text
        // (not the intro bases).
        unsigned const Id = CreateID(Name);
        std::wstring const Part = Widen(Name);
        Universe::IBase* Partial = nullptr;
        for (Universe::IBase* Base = Universe::GetFirstBase(); Base != nullptr; Base = Universe::GetNextBase())
        {
            if (Base->GetId() == Id)
                return Base;
            if (Partial == nullptr && _strnicmp(Base->GetNickname(), "intro", 5) != 0)
            {
                wchar_t Text[128] = {};
                GetIdsStringW(static_cast<unsigned>(Base->GetStridName()), Text, 128);
                if (ContainsNoCase(Text, Part) || ContainsNoCase(Widen(Base->GetNickname()), Part))
                    Partial = Base;
            }
        }
        return Partial;
    }

    Universe::ISystem* FindSystem(char const* Name)
    {
        unsigned const Id = CreateID(Name);
        std::wstring const Part = Widen(Name);
        Universe::ISystem* Partial = nullptr;
        for (Universe::ISystem* System = Universe::GetFirstSystem(); System != nullptr; System = Universe::GetNextSystem())
        {
            if (System->GetId() == Id)
                return System;
            if (Partial == nullptr)
            {
                wchar_t Text[128] = {};
                GetIdsStringW(static_cast<unsigned>(System->GetStridName()), Text, 128);
                if (ContainsNoCase(Text, Part) || ContainsNoCase(Widen(System->GetNickname()), Part))
                    Partial = System;
            }
        }
        return Partial;
    }

    void CmdBase(char const* Args)
    {
        if (*Args == '\0')
        {
            Printf("base <nickname or part of the name>");
            return;
        }
        if (!InSpace())
        {
            Printf("* Launch first (base works in space).");
            return;
        }
        Universe::IBase* const Base = FindBase(Args);
        if (Base == nullptr)
        {
            Printf("* Base not found.");
            return;
        }
        FPortConsoleServerFn const Server = ServerConsole();
        unsigned Id = Base->GetId();
        if (Server == nullptr || Server(kPortConsoleForceLand, &Id) != kPortConsoleOk)
        {
            Printf("* Landing failed.");
            return;
        }
        Printf("Landing at %s.", Base->GetNickname());
    }

    bool ReadVector(char const*& Text, Vector& Out)
    {
        float Values[3] = {};
        int Count = 0;
        while (Count < 3)
        {
            while (*Text == ' ' || *Text == ',')
                ++Text;
            char* End = nullptr;
            double const Value = std::strtod(Text, &End);
            if (End == Text)
                break;
            Values[Count++] = static_cast<float>(Value);
            Text = End;
        }
        Out.x = Values[0];
        Out.y = Values[1];
        Out.z = Values[2];
        return Count > 0;
    }

    // The server moves its copy of the ship; the client owns the position in single player
    // (it sends it up every frame), so its own ship is beamed to the same place.
    void RunJump(FPortConsoleServerFn Server, FPortConsoleJump& Jump)
    {
        switch (Server(kPortConsoleJump, &Jump))
        {
        case kPortConsoleOk:
        {
            CObject* Ship = static_cast<CObject*>(GetPlayerShipObject());
            if (Ship != nullptr && (static_cast<unsigned>(Ship->ObjectClass) & 0x503u) == 0x503u)
                Ship->beam_object(Jump.OutPos, Jump.OutOrient, false);
            Printf("pos = %.1f, %.1f, %.1f", static_cast<double>(Jump.OutPos.x),
                   static_cast<double>(Jump.OutPos.y), static_cast<double>(Jump.OutPos.z));
            break;
        }
        case kPortConsoleNotInSpace: Printf("* Not in space."); break;
        case kPortConsoleNoTarget: Printf("* No target."); break;
        case kPortConsoleObjectNotFound: Printf("* Object not found."); break;
        default: break;
        }
    }

    void CmdSystem(char const* Args)
    {
        // console.dll cmdSystem: system [x,y,z [rx,ry,rz] | object]; without a position the
        // ship keeps its coordinates.
        if (*Args == '\0')
        {
            Printf("system <nickname or part of the name> [x,y,z [rx,ry,rz] | object]");
            return;
        }
        if (!InSpace())
        {
            Printf("* Launch first (system works in space).");
            return;
        }
        char Name[64] = {};
        int Length = 0;
        while (Args[Length] != '\0' && Args[Length] != ' ' && Length < 63)
        {
            Name[Length] = Args[Length];
            ++Length;
        }
        char const* Rest = Args + Length;
        while (*Rest == ' ')
            ++Rest;
        Universe::ISystem* const System = FindSystem(Name);
        if (System == nullptr)
        {
            Printf("* System not found.");
            return;
        }
        FPortConsoleSystem Switch = {};
        Switch.System = System->GetId();
        Switch.Orient = Matrix(1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f);
        if (std::isdigit(static_cast<unsigned char>(*Rest)) || *Rest == '-' || *Rest == ',')
        {
            Switch.Mode = 1;
            ReadVector(Rest, Switch.Pos);
            Vector Rotation;
            if (ReadVector(Rest, Rotation))
                Switch.Orient = EulerMatrix(Rotation);
        }
        else if (*Rest != '\0')
        {
            Switch.Mode = 2;
            std::strncpy(Switch.Object, Rest, sizeof(Switch.Object) - 1);
        }
        FPortConsoleServerFn const Server = ServerConsole();
        if (Server == nullptr || Server(kPortConsoleSystem, &Switch) != kPortConsoleOk)
        {
            Printf("* Single player only.");
            return;
        }
        unsigned const Id = Switch.System;
        SetPendingJumpSystem(&Id, false);
        Printf("Switching to %s.", System->GetNickname());
    }

    void CmdJump(char const* Args)
    {
        // console.dll cmdJump: jump [forward,right,up | object]; nothing = the target.
        FPortConsoleJump Jump = {};
        if (std::isdigit(static_cast<unsigned char>(*Args)) || *Args == '-' || *Args == ',')
        {
            Jump.Mode = 1;
            ReadVector(Args, Jump.Offset);
        }
        else if (*Args != '\0')
        {
            Jump.Mode = 2;
            std::strncpy(Jump.Object, Args, sizeof(Jump.Object) - 1);
        }
        else
        {
            // A targeted waypoint is a client-only Solar the server does not know: jump onto it.
            HUD_Waypoint* const Waypoint = GetHudWaypoint();
            IObjRW* const WaypointObj = Waypoint != nullptr && Waypoint->IsActive() ? Waypoint->GetWaypointObject() : nullptr;
            if (WaypointObj != nullptr)
            {
                Jump.Mode = 3;
                Jump.Offset = WaypointObj->get_position();
            }
        }
        FPortConsoleServerFn const Server = ServerConsole();
        if (Server == nullptr)
        {
            Printf("* Single player only.");
            return;
        }
        RunJump(Server, Jump);
    }

    void CmdLaunch(char const*)
    {
        // console.dll cmdLaunch: what clicking the launch tab does (NavBar case 4, 0x00440f94).
        Win3D* const Found = Win3DFindByName("NavBar");
        if (Found == nullptr)
        {
            Printf("* Not in a base.");
            return;
        }
        NavBar* const Bar = static_cast<NavBar*>(Found);
        for (FNavBarButton& Button : Bar->Buttons)
        {
            if (Button.Type == 4 && Button.Hotspot == nullptr)
            {
                G_bOpen = false;
                Bar->OnButtonClicked(&Button);
                return;
            }
        }
        Printf("* No launch button.");
    }

    void CmdGhost(char const*)
    {
        // console.dll cmdGhost toggled the DISABLE_COLLIDE option (DAT_00679cc4); the player's
        // ship update applies it (client_gameobj.cpp, 0x00545092).
        int& Option = g_display.options[kGameOptDisableCollide];
        Option = Option != 0 ? 0 : 1;
        Printf(Option != 0 ? "Ghost on: no collisions." : "Ghost off.");
    }

    FCommand const kCommands[] = {
        {"help", "h", "list the commands", &CmdHelp},
        {"TimeScale", "ts", "[scale] slow down / speed up the single-player game (1 = normal)", &CmdTimeScale},
        {"time", nullptr, "seconds since the start", &CmdTime},
        {"max_fps", "fps", "[fps] the frame-rate cap", &CmdMaxFps},
        {"lines", nullptr, "[2..40] visible console lines", &CmdLines},
        {"clear", nullptr, "clear the console", &CmdClear},
        {"quiet", "q", "toggle command output", &CmdQuiet},
        {"pos", "p", "[x,y,z] the player's position (with x,y,z: move there)", &CmdPos},
        {"quit", nullptr, "quit the game", &CmdQuit},
        {"save", "s", "[name | 1-9] save the game (in space too)", &CmdSave},
        {"load", "l", "[name | 1-9] load a game saved with save", &CmdLoad},
        {"base", nullptr, "<name> land at a base", &CmdBase},
        {"system", nullptr, "<name> [x,y,z [rx,ry,rz] | object] move to another system", &CmdSystem},
        {"jump", "j", "[forward,right,up | object] move in this system (nothing: to the target)", &CmdJump},
        {"launch", nullptr, "launch from the base", &CmdLaunch},
        {"ghost", nullptr, "toggle the ship's collisions", &CmdGhost},
    };

    void CmdHelp(char const*)
    {
        for (FCommand const& Command : kCommands)
        {
            if (Command.Alias != nullptr)
                Printf("%s/%s - %s", Command.Name, Command.Alias, Command.Help);
            else
                Printf("%s - %s", Command.Name, Command.Help);
        }
    }

    void Execute(std::string const& Line)
    {
        // Beta 0x005536a0: the first word (split at a space or ';') by name or alias.
        size_t Start = Line.find_first_not_of(' ');
        if (Start == std::string::npos)
            return;
        size_t End = Line.find_first_of(" ;", Start);
        std::string const Word = Line.substr(Start, End == std::string::npos ? std::string::npos : End - Start);
        std::string Args;
        if (End != std::string::npos)
        {
            size_t const ArgStart = Line.find_first_not_of(" ;", End);
            if (ArgStart != std::string::npos)
                Args = Line.substr(ArgStart);
        }
        for (FCommand const& Command : kCommands)
        {
            if (_stricmp(Word.c_str(), Command.Name) == 0 ||
                (Command.Alias != nullptr && _stricmp(Word.c_str(), Command.Alias) == 0))
            {
                Command.Fn(Args.c_str());
                return;
            }
        }
        Printf("* Unknown command.");
    }

    void Complete()
    {
        // Beta 0x00553bc0: complete the last word against the command names.
        for (FCommand const& Command : kCommands)
        {
            if (!G_Input.empty() && _strnicmp(Command.Name, G_Input.c_str(), G_Input.size()) == 0)
            {
                G_Input = Command.Name;
                G_Input += ' ';
                return;
            }
        }
    }

    void SetOpen(bool bOpen)
    {
        G_bOpen = bOpen;
        G_Input.clear();
        G_HistoryCursor = static_cast<int>(G_History.size());
    }
}

namespace
{
    // The console eats the key-down while open, so the pump skips TranslateMessage and no
    // WM_CHAR follows: the character is produced here from the key, the scan code and the
    // current keyboard layout, and converted to the ANSI code page the window uses.
    void TypeKey(unsigned Wparam, unsigned Lparam)
    {
        BYTE State[256];
        if (!GetKeyboardState(State))
            return;
        // Ctrl / Alt combinations are commands, not text.
        if ((State[VK_CONTROL] & 0x80) != 0 || (State[VK_MENU] & 0x80) != 0)
            return;
        wchar_t Wide[4] = {};
        int const Count = ToUnicodeEx(Wparam, (Lparam >> 16) & 0xff, State, Wide, 4, 0, GetKeyboardLayout(0));
        if (Count != 1 || Wide[0] < 0x20)
            return;
        char Narrow[4] = {};
        if (WideCharToMultiByte(CP_ACP, 0, Wide, 1, Narrow, sizeof(Narrow), nullptr, nullptr) != 1)
            return;
        if (static_cast<int>(G_Input.size()) < kMaxInput)
            G_Input += Narrow[0];
    }
}

bool DbgConsoleHandleMessage(unsigned Message, unsigned Wparam, unsigned Lparam)
{
    if (!G_bOpen)
    {
        // VK_OEM_3: the ` / ~ key (ё on a Russian layout).
        if (Message == WM_KEYDOWN && Wparam == VK_OEM_3)
        {
            SetOpen(true);
            if (G_Lines.empty())
                Printf("Console. \"help\" lists the commands; ` or Esc closes it.");
            return true;
        }
        return false;
    }

    if (Message == WM_CHAR || Message == WM_SYSCHAR || Message == WM_DEADCHAR)
        return true; // text comes from TypeKey below
    if (Message != WM_KEYDOWN && Message != WM_SYSKEYDOWN)
        return Message == WM_KEYUP || Message == WM_SYSKEYUP;

    switch (Wparam)
    {
    case VK_OEM_3:
    case VK_ESCAPE:
        SetOpen(false);
        break;
    case VK_RETURN:
        Printf(">%s", G_Input.c_str());
        if (!G_Input.empty())
        {
            G_History.push_back(G_Input);
            Execute(G_Input);
        }
        G_Input.clear();
        G_HistoryCursor = static_cast<int>(G_History.size());
        break;
    case VK_BACK:
        if (!G_Input.empty())
            G_Input.pop_back();
        break;
    case VK_TAB:
        Complete();
        break;
    case VK_PRIOR:
        G_Scroll += G_Visible;
        break;
    case VK_NEXT:
        G_Scroll -= G_Visible;
        break;
    case VK_HOME:
        G_Scroll = static_cast<int>(G_Lines.size());
        break;
    case VK_END:
        G_Scroll = 0;
        break;
    case VK_UP:
        if (G_HistoryCursor > 0)
            G_Input = G_History[--G_HistoryCursor];
        break;
    case VK_DOWN:
        if (G_HistoryCursor + 1 < static_cast<int>(G_History.size()))
            G_Input = G_History[++G_HistoryCursor];
        else
        {
            G_HistoryCursor = static_cast<int>(G_History.size());
            G_Input.clear();
        }
        break;
    default:
        // Beta 0x005551c0: every other key types its character (the toggle key never does).
        TypeKey(Wparam, Lparam);
        break;
    }
    int const MaxScroll = static_cast<int>(G_Lines.size()) - G_Visible;
    if (G_Scroll > MaxScroll)
        G_Scroll = MaxScroll > 0 ? MaxScroll : 0;
    if (G_Scroll < 0)
        G_Scroll = 0;
    return true;
}

void DbgConsoleDraw()
{
    ++G_FrameCounter;
    if (!G_bOpen)
        return;
    IFont* Font = FindMenuFontImp("DebugText");
    if (Font == nullptr)
        Font = FindMenuFontImp("ListText");
    if (Font == nullptr)
        Font = FindMenuFontImp("Normal");
    if (Font == nullptr)
        return;
    if (G_Text == nullptr)
    {
        G_Text = new FConsoleText;
        for (FFontString& Row : G_Text->Rows)
            FontStringSetFont(&Row, Font);
    }

    // The rows: the last G_Visible lines (less the scroll), then the input line -- beta draws
    // ">%S%S" with a blinking cursor glyph, or "[more]" while scrolled up.
    int const Count = static_cast<int>(G_Lines.size());
    int const First = Count - G_Scroll - G_Visible;
    for (int Row = 0; Row <= G_Visible; ++Row)
    {
        std::wstring Text;
        if (Row < G_Visible)
        {
            int const Line = First + Row;
            if (Line >= 0 && Line < Count)
                Text = G_Lines[static_cast<size_t>(Line)];
        }
        else if (G_Scroll != 0)
            Text = L"[more]";
        else
        {
            wchar_t Wide[128];
            MultiByteToWideChar(CP_ACP, 0, G_Input.c_str(), -1, Wide, 128);
            Text = L">";
            Text += Wide;
            Text += (G_FrameCounter / 15) % 2 == 0 ? L"_" : L" ";
        }
        if (Text.empty())
            Text = L" ";
        if (G_Text->Shown[Row] != Text)
        {
            FontStringSetText(&G_Text->Rows[Row], Text.c_str());
            G_Text->Shown[Row] = Text;
        }
    }
    if (G_Text->RowHeight == 0)
    {
        int Size[2] = {};
        FontStringGetExtent(&G_Text->Rows[0], Size);
        G_Text->RowHeight = Size[1] > 0 ? Size[1] : 16;
    }

    UiOverlayPrepPipeline();
    int SavedViewport[4] = {};
    Win3DGetViewport(0xba2, SavedViewport);
    Win3DSetViewportRect(0, 0, static_cast<int>(G_RenderSurfaceWidth),
                        static_cast<int>(G_RenderSurfaceHeight), __FILE__, __LINE__);
    unsigned const SavedColor = FontAtlasDrawColor();

    FFontStringDrawOrigin Origin = {};
    Origin.Scale = static_cast<float>(G_RenderSurfaceWidth) - 16.0f;
    Origin.Height = static_cast<float>(G_RenderSurfaceHeight) - 8.0f;
    int const Top = static_cast<int>(G_RenderSurfaceHeight) - (G_Visible + 1) * (G_Text->RowHeight + 1) - 8;
    for (int Row = 0; Row <= G_Visible; ++Row)
    {
        FontAtlasSetDrawColor(Row == G_Visible ? 0xffffff80u : 0xffe0e0e0u);
        Origin.X = 8.0f;
        Origin.Y = static_cast<float>(Top + Row * (G_Text->RowHeight + 1));
        FontStringDrawChildren(&Origin, &G_Text->Rows[Row], nullptr, nullptr);
    }

    UiOverlayPrepPipeline();
    FontAtlasSetDrawColor(SavedColor);
    Win3DSetViewportRect(SavedViewport[0], SavedViewport[1], SavedViewport[2],
                        SavedViewport[3], __FILE__, __LINE__);
}

void DbgConsoleShutdown()
{
    delete G_Text;
    G_Text = nullptr;
}

#endif
