#include "native_subtitles.h"
#include "subtitle_data.h"
#include "voice_profiles.h"
#include "port_config.h"
#include "dacom.h"
#include "font_imp.h"
#include "font_string.h"
#include "globals.h"
#include "win3d_immediate.h"
#include "win3d_renderables.h"
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <memory>
#include <unordered_map>

namespace NativeSubtitles
{
namespace
{
    Database Entries;
    std::unordered_map<void*, Playback> Playing;
    unsigned long long Order = 0;
    bool Loaded = false;
    std::vector<std::unique_ptr<FFontString>> Lines;
    std::wstring LastText;
    int LastWidth = 0, LastHeight = 0;
    IFont* LastFont = nullptr;

    std::wstring Wide(char const* s)
    {
        if (!s) return {};
        int n = MultiByteToWideChar(CP_ACP, 0, s, -1, nullptr, 0);
        if (n <= 0) return {};
        std::wstring result(n, 0);
        MultiByteToWideChar(CP_ACP, 0, s, -1, &result[0], n);
        result.pop_back();
        return result;
    }
    void Load()
    {
        if (Loaded) return;
        Loaded = true;
        if (!PortConfigInt("Subtitles", "enabled", 1)) return;
        char path[MAX_PATH] = {};
        PortLanguageString("subtitles_xml", "", path, sizeof(path));
        char configured[MAX_PATH] = {};
        PortConfigString("Subtitles", "xml", path, configured, sizeof(configured));
        std::filesystem::path exe(Wide(PortExeDirectory()));
        std::vector<std::filesystem::path> candidates;
        if (*configured) candidates.push_back(exe / Wide(configured));
        else
        {
            candidates.push_back(exe / L"subtitles.xml");
            auto lang = Wide(PortLanguage());
            auto difficulty = Wide(PortDifficulty());
            if (lang.empty()) lang = L"en";
            if (difficulty.empty()) difficulty = L"normal";
            candidates.push_back(exe / L".." / L"BUILDS" / (lang + L"_" + difficulty) / L"EXE/subtitles.xml");
            candidates.push_back(exe / L"../EXE/subtitles.xml");
        }
        for (auto const& candidate : candidates)
        {
            std::error_code ec;
            if (!std::filesystem::is_regular_file(candidate, ec)) continue;
            std::wstring error;
            if (!ReadXml(candidate.c_str(), Entries, error))
                FDUMP(0x100002, "Native subtitles: %ls: %ls", candidate.c_str(), error.c_str());
            else FDUMP(0x100003, "Native subtitles: loaded %u entries from %ls", unsigned(Entries.size()), candidate.c_str());
            return;
        }
        FDUMP(0x100002, "Native subtitles: no XML found; set [Subtitles] xml in port.ini");
    }
    int Priority(std::wstring const& area)
    {
        if (area == L"Cinematic") return 5;
        if (area == L"News") return 4;
        if (area == L"Ingame") return 3;
        if (area == L"Ingame_NN") return 2;
        if (area == L"Ingame_BG") return 1;
        return 0;
    }
}

void Start(void* source, Archetype::ISound* arch)
{
    Load();
    Playing.erase(source);
    if (!arch || Entries.empty()) return;
    std::wstring key;
    if (auto* voice = dynamic_cast<FVoiceMsg*>(arch); voice && voice->Owner && !voice->Owner->UtfPath.empty())
    {
        wchar_t id[16];
        swprintf_s(id, L"|0x%08x", voice->Id.Id);
        key = Wide(voice->Owner->UtfPath.c_str()) + id;
    }
    else key = Wide(arch->GetFileName());
    auto found = Entries.find(AudioKey(key));
    if (found != Entries.end()) Playing.emplace(source, Playback{&found->second, 0, false, ++Order});
}

void Stop(void* source) { Playing.erase(source); }

void Sync(void* source, double seconds, bool started, bool paused, float dt)
{
    auto found = Playing.find(source);
    if (found == Playing.end()) return;
    found->second.Sync(seconds, started, paused, dt);
}

void Draw()
{
    Playback const* chosen = nullptr;
    std::wstring text;
    // Main dialogue wins over radio chatter; ties select the most recent source.
    // Sources remain tracked independently, so stopping one cannot erase another.
    for (auto const& pair : Playing)
    {
        auto const& play = pair.second;
        if (!play.started) continue;
        auto current = play.entry->At(play.time);
        if (current.empty()) continue;
        if (!chosen || Priority(play.entry->area) > Priority(chosen->entry->area) ||
            (Priority(play.entry->area) == Priority(chosen->entry->area) && play.order > chosen->order))
        { chosen = &play; text = std::move(current); }
    }
    if (text.empty()) return;
    char fontName[64];
    PortConfigString("Subtitles", "font", "Normal", fontName, sizeof(fontName));
    auto* font = FindMenuFontImp(fontName);
    if (!font || G_RenderSurfaceWidth < 64 || G_RenderSurfaceHeight < 64) return;
    int const width = int(G_RenderSurfaceWidth * .78f);
    int const height = (std::max)(1, font->GetLineHeight());
    if (text != LastText || width != LastWidth || height != LastHeight || font != LastFont)
    {
        Lines.clear();
        size_t pos = 0;
        while (pos < text.size())
        {
            auto end = text.find(L'\n', pos);
            if (end == text.npos) end = text.size();
            int fit = font->ProbeString(width, text.c_str() + pos, int(end - pos));
            size_t count = (std::max)(size_t(1), size_t((std::max)(0, fit)));
            count = (std::min)(count, end - pos);
            if (pos + count < end)
            {
                auto space = text.find_last_of(L" \t", pos + count);
                if (space != text.npos && space > pos) count = space - pos;
            }
            auto line = std::make_unique<FFontString>();
            FontStringSetFont(line.get(), font);
            FontStringSetText(line.get(), text.substr(pos, count).c_str());
            Lines.push_back(std::move(line));
            pos += count;
            while (pos < text.size() && (text[pos] == L' ' || text[pos] == L'\t' || text[pos] == L'\n' || text[pos] == L'\r')) ++pos;
        }
        LastText = text; LastWidth = width; LastHeight = height; LastFont = font;
    }
    int viewport[4] = {};
    Win3DGetViewport(0xba2, viewport);
    UiOverlayPrepPipeline();
    Win3DSetViewportRect(0, 0, int(G_RenderSurfaceWidth), int(G_RenderSurfaceHeight), __FILE__, __LINE__);
    unsigned const oldColor = FontAtlasDrawColor();
    float const bottom = (std::max)(.5f, (std::min)(.95f, PortConfigFloat("Subtitles", "bottom", .84f)));
    float y = (std::max)(8.f, G_RenderSurfaceHeight * bottom - float(Lines.size() * height));
    int const outline = (std::max)(0, (std::min)(3, PortConfigInt("Subtitles", "outline", 1)));
    for (auto const& line : Lines)
    {
        auto draw = [&](int dx, int dy, unsigned color) {
            FFontStringDrawOrigin origin = {};
            origin.X = (G_RenderSurfaceWidth - width) * .5f + dx;
            origin.Y = y + dy; origin.Scale = float(width); origin.Height = float(height); origin.Field10 = 1;
            FontAtlasSetDrawColor(color);
            FontStringDrawChildren(&origin, line.get(), nullptr, nullptr);
        };
        if (outline) for (int dy = -1; dy <= 1; ++dy) for (int dx = -1; dx <= 1; ++dx)
            if (dx || dy) draw(dx * outline, dy * outline, 0xff000000u);
        draw(0, 0, 0xffffffffu);
        y += height;
    }
    FontAtlasSetDrawColor(oldColor);
    UiOverlayPrepPipeline();
    Win3DSetViewportRect(viewport[0], viewport[1], viewport[2], viewport[3], __FILE__, __LINE__);
}

void Shutdown()
{
    Lines.clear(); LastText.clear(); LastFont = nullptr;
    Playing.clear(); Entries.clear(); Loaded = false;
}
}
