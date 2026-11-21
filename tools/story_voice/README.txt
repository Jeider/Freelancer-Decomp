English campaign acting direction

Canonical Pythonlancer: D:/Games/FL_MOD/Assets/Pythonlancer.
Topic: D:/work/Freelancer-Decomp/out/story_cutscenes/voice_direction_en.

Reviewed every active translated VoiceLine in main missions 1-13 and the
translated epilogue scenes in missions 14-17. There are no active English space
lines in the epilogue yet. Untranslated lines, debug/scratch scripts, RPG/freeplay,
dispatchers, actors, audio references and game DATA are outside this change.

Canonical line syntax:
  from audio import story_delivery as performance
  VoiceLine(290, Reichman, ru=..., en=..., delivery_en=performance.FURIOUS)

The new delivery_en field is read only by English VoiceStudio generation.
The existing delivery field still controls legacy behavior, including RU.
The EN overlay inherits the prior line/actor pitch and age instructions, speed
and reference. It overrides only emotion. Most presets send an eight-value
IndexTTS emotion vector; teasing, sardonic and weary use text emotion at .6.
No speed-only imitation of anger is used. Presets express intentions; generated
takes still need listening for voice identity, wording and performance quality.

space_direction.py and scene_direction.py record individually reviewed line IDs.
They are not sentiment classifiers or keyword-matching rules. Unmarked lines
retain their previous performance. Neuralnet and LogosRobot stay unmarked.
direction.tsv in the topic lists every marked line with source segment, actor,
EN text and existing author direction.
plan.json also contains short narrative notes for each main mission.

Authoring commands (run from repository root):
  python -B tools/story_voice/en_direction.py inventory
  python -B tools/story_voice/en_direction.py stage
  D:/Games/FL_MOD/Assets/Pythonlancer/.venv/Scripts/python.exe -B tools/story_voice/check_en_direction.py
  python -B tools/story_voice/en_direction.py publish

Inventory is intentionally one-time: it pins the user's original sources.
Stage/publish reject concurrent edits. Once published, do not rerun stage against
that old baseline; start a new explicitly reviewed revision under the same topic.
The checker exercises all 2,086 Russian lines and 1,946 English lines through
the actual request composer, with network and audio output replaced by capture
stubs. No synthesized audio or final THN is needed for this regression.

Generation behavior: the existing AudioFolder generators skip existing WAV/MP3
source recordings. Markers apply when a line is actually generated; they do not
silently invalidate, delete or overwrite approved recordings. For a future
regeneration, use the marked-line inventory to select EN recordings only, keep
review separate from DATA installation, and do not regenerate RU. This task
does not synthesize voices, build THNs or change mission/cutscene timing.
