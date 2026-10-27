#include "cutscene_skip.h"

#include "common_misc.h"
#include "font_atlas.h"
#include "font_imp.h"
#include "font_string.h"
#include "gf_script_object.h"
#include "globals.h"
#include "hud_interface_ids.h"
#include "ids_strings.h"
#include "nn_arrival_text.h"
#include "nn_modal.h"
#include "win3d_immediate.h"
#include "win3d_renderables.h"

#include <algorithm>
#include <windows.h>

namespace
{
    FGfScriptSequence* PromptSequence = nullptr;
    int PromptEntry = -1;
    FFontString* PromptText = nullptr;
    bool ConsumeEscape = false;
    bool ConsumeEnter = false;

    FGfScriptSequence* ActiveScene()
    {
        if (IsClientServerTickPaused() || G_bNnScreenUp) return nullptr;
        FGfScriptSequence* active = nullptr;
        for (auto* sequence : G_GfScriptManager.Sequences)
        {
            if (!sequence || !sequence->bLetterbox || sequence->bLoop || !sequence->bPlaying || !sequence->bActive ||
                sequence->bStopped || sequence->bSkip || !sequence->Entries || sequence->Current < 0 ||
                sequence->Current >= sequence->Count) continue;
            // Retail +0x15 permits a one-key skip. Only bypass a disabled
            // native skip for single-player story scenes, with confirmation.
            if (!SinglePlayer() && !sequence->Field_0x15) continue;
            auto const& entry = sequence->Entries[sequence->Current];
            // These are interactive mission-offer/info entries, not footage. The
            // native skip loop also stops before them; never choose an answer here.
            // Traffic (5) and unknown kinds do not advance NextEntryIndex.
            if (!entry.Script || !CutsceneSkipIsCinematicEntry(entry.Kind)) continue;
            if (!active || sequence->Priority >= active->Priority) active = sequence;
        }
        return active;
    }

    FGfScriptSequence* ConfirmableScene()
    {
        auto* active = ActiveScene();
        if (!PromptSequence || active != PromptSequence || active->Current != PromptEntry || active->Field_0x15)
        {
            CutsceneSkipReset();
            return nullptr;
        }
        return active;
    }
}

void CutsceneSkipReset()
{
    PromptSequence = nullptr;
    PromptEntry = -1;
    delete PromptText;
    PromptText = nullptr;
}

void CutsceneSkipInvalidate(FGfScriptSequence const* sequence)
{
    if (PromptSequence == sequence) CutsceneSkipReset();
}

bool CutsceneSkipRequest()
{
    auto* active = ActiveScene();
    if (!active) { CutsceneSkipReset(); return false; }
    if (active->Field_0x15)
    {
        CutsceneSkipReset();
        active->bSkip = 1;
        NnArrivalTextHurry();
        return true;
    }
    if (PromptSequence != active || PromptEntry != active->Current)
    {
        CutsceneSkipReset();
        PromptSequence = active;
        PromptEntry = active->Current;
    }
    return true;
}

bool CutsceneSkipHandleKey(unsigned message, unsigned key, unsigned flags)
{
    if (message == WM_KILLFOCUS || (message == WM_ACTIVATEAPP && !key))
    {
        CutsceneSkipReset();
        ConsumeEscape = ConsumeEnter = false;
        return false;
    }
    if (key != VK_ESCAPE && key != VK_RETURN) return false;
    bool& consumed = key == VK_ESCAPE ? ConsumeEscape : ConsumeEnter;
    // Keep the release/repeats out of normal UI even if confirming the skip has
    // already ended the scene and opened a mission dialog or returned to flight.
    if (message == WM_KEYUP || message == WM_SYSKEYUP)
    {
        bool const result = consumed;
        consumed = false;
        return result;
    }
    if (message == WM_CHAR) return consumed;
    if (message != WM_KEYDOWN) return false; // Alt+Enter remains a window command.
    if (consumed) return true;
    bool const repeat = (flags & (1u << 30)) != 0;
    if (key == VK_ESCAPE)
    {
        if (!ActiveScene()) return false;
        consumed = true;
        if (!repeat)
        {
            if (ConfirmableScene()) CutsceneSkipReset(); // Second Esc dismisses the hint.
            else CutsceneSkipRequest();
        }
        return true;
    }
    auto* sequence = ConfirmableScene();
    if (!sequence) return false;
    consumed = true;
    if (!repeat)
    {
        // Use the native sequence teardown/next-entry path. It restores the room,
        // stops at choices and delivers RTCDone / mission callbacks normally.
        sequence->bSkip = 1;
        CutsceneSkipReset();
        NnArrivalTextHurry();
    }
    return true;
}

void CutsceneSkipDraw()
{
    if (!ConfirmableScene()) return;
    auto* font = FindMenuFontImp("Normal");
    if (!font || G_RenderSurfaceWidth < 64 || G_RenderSurfaceHeight < 64) return;
    if (!PromptText)
    {
        wchar_t text[128] = {};
        if (!GetIdsStringWWithRawFallback(HudIds::CutsceneSkipPrompt, text, 128)) return;
        PromptText = new FFontString;
        FontStringSetText(PromptText, text);
    }
    FontStringSetFont(PromptText, font);
    int extent[2] = {};
    FontStringGetExtent(PromptText, extent);
    int viewport[4] = {};
    Win3DGetViewport(0xba2, viewport);
    UiOverlayPrepPipeline();
    Win3DSetViewportRect(0, 0, static_cast<int>(G_RenderSurfaceWidth),
                        static_cast<int>(G_RenderSurfaceHeight), __FILE__, __LINE__);
    unsigned const color = FontAtlasDrawColor();
    FFontStringDrawOrigin origin = {};
    origin.X = 17.f;
    origin.Y = static_cast<float>(G_RenderSurfaceHeight) * .91f - extent[1] + 1.f;
    origin.Scale = static_cast<float>(G_RenderSurfaceWidth) - 32.f;
    origin.Height = static_cast<float>((std::max)(extent[1], 24));
    origin.Field10 = 1; // Centred on the full screen, independent of shifted HUD panels.
    FontAtlasSetDrawColor(0xff000000u);
    FontStringDrawChildren(&origin, PromptText, nullptr, nullptr);
    origin.X -= 1.f;
    origin.Y -= 1.f;
    FontAtlasSetDrawColor(0xffffffffu);
    FontStringDrawChildren(&origin, PromptText, nullptr, nullptr);
    FontAtlasSetDrawColor(color);
    UiOverlayPrepPipeline();
    Win3DSetViewportRect(viewport[0], viewport[1], viewport[2], viewport[3], __FILE__, __LINE__);
}
