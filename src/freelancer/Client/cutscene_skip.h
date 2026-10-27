#pragma once

struct FGfScriptSequence;

inline bool CutsceneSkipIsCinematicEntry(int kind)
{
    return kind == 0 || kind == 2 || kind == 3 || kind == 6;
}

// Native skippable Thorn scenes use Esc; locked single-player scenes require Enter.
bool CutsceneSkipHandleKey(unsigned message, unsigned key, unsigned flags);
bool CutsceneSkipRequest(); // Uses the native +0x15 skip permission to choose the path.
void CutsceneSkipDraw();
void CutsceneSkipReset();
void CutsceneSkipInvalidate(FGfScriptSequence const* sequence);
