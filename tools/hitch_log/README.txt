Automatic hitch logging
======================
Enabled by default in this diagnostic build. No key presses or on-screen overlay.
Files: %LOCALAPPDATA%/Freelancer-Decomp/Diagnostics/hitches_DATE_TIME_PID_PART.csv
Disable for a launch with environment variable FREELANCER_HITCH_LOG=0.

Heavy synchronous legacy dumps are off by default. To investigate collision hulls
or sun halo visibility, explicitly set collision_dump=1 or sun_halo_dump=1 in
port.ini [Diagnostics] and restart. Do not use those dumps for frame-time baselines.

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
Asteroid scopes >=1 ms: server population maintenance, individual server rock
creation, and the client's moving-rock update/spatial-entry pass. The population
scope includes creation; do not add their times together.
Render probes >=1 ms: render_phase separates shadows, opaque objects/asteroids,
FarRocks, dust and nebula volume. render_prepare measures FarRocks construction.
shader_setup includes loading/compiling a surface variant; shader_device measures
D3D9 shader-object creation separately from bytecode cache access. These are CPU
durations, not GPU timestamp queries: deferred driver/GPU work can stall Present.

System loading now prepares registered FarRocks geometry/buffers and field-dust
programs/noise/targets before flight. Server asteroid archetypes are deduplicated
and pinned until system exit. Existing [Object] and [Archetype] preloads remain.
IRPRenderWarmup is an optional RP9 interface: on the device thread it creates and
retains surface shader variants and submits private 8x8 warmup draws, then waits
for a bounded GPU completion fence. A state block plus explicit target/depth
restoration preserves the loading screen. Successful warmups are reused between
systems; shader reload/device reset clears the corresponding readiness state.
This moves preparation into loading; it does not guarantee that every driver
combination, later scripted ship or effect is known before its first appearance.
Checks: python tools/hitch_log/check_system_preload.py and check_warmup_gpu.py
(the latter uses an invisible D3D9 window and the installed shader sources/cache).
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
