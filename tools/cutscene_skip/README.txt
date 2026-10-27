Story cutscene skip

Native skippable scenes (sequence +0x15 != 0) skip immediately on Esc, also in MP.
Only originally locked single-player scenes (+0x15 == 0) open the localized
confirmation prompt; Enter fast-forwards through the native completion path.
A second Esc dismisses the prompt. Confirmation is invalidated when the entry,
sequence, focus or modal/pause state changes. Key repeats cannot confirm.
Mission offer/info entries and looping room traffic are excluded; the native
skip loop stops at these boundaries. Native RTCDone/callback handling is retained.
The legacy skip event follows the same native-permission rule. Language.skip_any_cutscene is
obsolete and ignored; no executable byte patch is needed.

python tools/cutscene_skip/check_skip.py
  Compiles the production input/overlay functions and native Update/NextEntryIndex
  against engine stubs: input, lifecycle, priority, viewport restoration, native
  script teardown and offer/info/traffic boundaries. Requires local MSVC/SDK.

After building Release Win32:
python tools/cutscene_skip/stage_prompt.py
  Stages freelancer.exe/pdb, IDS 238226 in RU/EN NameResources.dll and Pythonlancer.
  Verifies every unrelated resource and records original/prepared SHA256 hashes.
  Run the generated src/obj/cutscene_skip/install/install.ps1 with the game closed
  to install, back up originals and verify hashes; failure restores the originals.

In-game validation still needed: mandatory story cutscenes, subtitles, a mission
offer after skipping, continuation/save/reload, Russian/English and windowed mode.
This applies to Thorn scenes; startup video files use a separate playback system.
