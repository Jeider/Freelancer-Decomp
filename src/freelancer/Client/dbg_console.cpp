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

#include "common_cobject.h"
#include "common_misc.h"       // SinglePlayer

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

    void CmdPos(char const*)
    {
        CObject const* const Ship = static_cast<CObject const*>(GetPlayerShipObject());
        if (Ship == nullptr)
        {
            Printf("* No player ship.");
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

    FCommand const kCommands[] = {
        {"help", "h", "list the commands", &CmdHelp},
        {"TimeScale", "ts", "[scale] slow down / speed up the single-player game (1 = normal)", &CmdTimeScale},
        {"time", nullptr, "seconds since the start", &CmdTime},
        {"max_fps", "fps", "[fps] the frame-rate cap", &CmdMaxFps},
        {"lines", nullptr, "[2..40] visible console lines", &CmdLines},
        {"clear", nullptr, "clear the console", &CmdClear},
        {"quiet", "q", "toggle command output", &CmdQuiet},
        {"pos", "p", "the player's position", &CmdPos},
        {"quit", nullptr, "quit the game", &CmdQuit},
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

bool DbgConsoleHandleMessage(unsigned Message, unsigned Wparam)
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

    if (Message == WM_CHAR || Message == WM_SYSCHAR)
    {
        // Beta 0x005551c0: printable characters; backquote, backspace, return and tab are keys.
        // The window is ANSI (RegisterClassA), so the character is a code-page byte; the
        // toggle key's own character (` / ~, or cp1251 ё / Ё) is not typed.
        unsigned char const Char = static_cast<unsigned char>(Wparam);
        if (Char >= 0x20 && Char != '`' && Char != '~' && Char != 0xb8 && Char != 0xa8 &&
            static_cast<int>(G_Input.size()) < kMaxInput)
            G_Input += static_cast<char>(Char);
        return true;
    }
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
