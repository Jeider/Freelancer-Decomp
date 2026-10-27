Automatic hitch logging
======================
Enabled by default in this diagnostic build. No key presses or on-screen overlay.
Files: %LOCALAPPDATA%/Freelancer-Decomp/Diagnostics/hitches_DATE_TIME_PID_PART.csv
Disable for a launch with environment variable FREELANCER_HITCH_LOG=0.

The client starts logging on its first tick. All modules share one QPC clock and
one asynchronous CSV writer. Producers only copy to a bounded queue; they never
write a file or wait for the writer lock. A full/contended queue increments the
dropped_events diagnostic. Writer flushes every 250 ms and on normal shutdown.
Up to three 64 MiB parts rotate within each run; previous runs remain available.

Rows include start/end/duration in ms since logger start, thread ID and frame ID.
frame: client tick >=10 ms. frame_interval: start-to-start >=16 ms, INCLUDING
the previous tick, frame limiter, message pump and OS scheduling.
render: every completed scene submission. phase: existing UI/server/game/object/
physics/sound/present scopes >=2 ms. These durations are inclusive, NOT additive.
Resource scopes >=1 ms: model loader and client model request, texture load,
room sidecar load, shader cache/compile, WAV load, voice archive/acquire, ACM
decode, DirectSound buffer creation/play and streaming-sound creation.
Resource names may be archive member names, with the containing voice UTF in a
nested/overlapping voice_archive row. This is timing, not a record of audio.

python tools/hitch_log/analyze.py [optional CSV]
Reads the newest run by default. Lists longest ticks and concurrent resource/
phase spans. Same-thread overlap helps identify a stall; a worker-thread event
at the same time is only correlation. This does not directly measure GPU work,
OS disk paging, driver internals or every file read. Initial startup before the
first tick is excluded. No cause is assigned automatically without evidence.

python tools/hitch_log/collect.py
Preserves complete-row snapshots under src/obj/hitch_log/collected/captures and
updates resources.json / resources.csv. Repeated snapshots are deduplicated.
Ranks observed resource scopes by count, total, maximum and p95 duration, with
same-thread slow-frame association. Nested loader wrappers are not counted as
additional resources. Opaque voice IDs remain unresolved until their archive is
known. These are candidate preload inputs, not a ready-to-use preload manifest:
current logs do not identify system/base boundaries or distinguish loading from
flight, and resource calls faster than 1 ms are absent. Present stalls remain a
separate investigation. Collection/report generation runs only when invoked;
the game's automatic CSV logging continues independently.

Checks: python tools/hitch_log/check.py
Stage/install: python tools/hitch_log/install.py [--apply]
Installer includes Common, SoundManager, SoundStreamer, RP9 and client binaries;
all changed files are backed up and verified, and existing shader cache warmed.
