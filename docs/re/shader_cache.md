# RP9 shader bytecode cache

## Mandatory game startup (2026-11-11)

RP9 now blocks device initialization until `RP9ShaderManifest.h` has prepared every
required stage. This also applies to direct `bin/freelancer.exe` launches and when
`surface_shaders=0`. The preparation window is before gameplay, not an overlay over
an already running game. It counts successfully cached stages only.

The sequence is: read required sources/includes, validate cached bytecode, compile
missing entries, atomically store and read back new entries, then create each shader
on the current D3D9 device. Compilation, missing source, persistence or GPU creation
failure blocks startup and names the failing stage. Closing preparation cancels
the launch after active compiler calls finish; workers are joined. Device resets
do not reopen the startup window.

The manifest currently has 123 stages, including black hole main/composite, all
nebula styles, cloak, HUD, beams, soft particles, color grading, gamma, driver warmup
and supersample resolve. `RP9_SKIP_OPTIMIZATION` has one shared flags policy; the
supersample resolve retains its level-3 optimization flag. The offline
`tools/warm_surface_cache.cpp` uses this same manifest and persistence checks.
Add any new runtime stage/variant to the manifest as part of its implementation.

This is a persistent **bytecode** cache. D3D shader objects and other GPU resources
must still be recreated per device; scene driver draw warmup remains separate.
Hot reload still recompiles changed sources. The historical background surface
warmup and permissive no-disk-write behavior described below have been superseded
for production RP9 paths.

Validation: `python tools/shader_startup/check.py` exercises cold/warm cache,
native D3D9 shader acceptance, malformed HLSL, missing sources and a cache path that
cannot be written. On the local RTX 5080 all 123 stages passed; the warm pass had
123 hits. `tools/hitch_log/check_warmup_gpu.py` also passed after routing its
auxiliary vertex shader through the persistent cache.

GTX 1060 investigation: the old queue omitted black hole and some nebula styles,
ignored compile/store failures, and only waited for surface jobs. These defects
are fixed, but no GTX 1060 reproduction is available locally. Startup logs the
adapter/caps/depth and per-stage compile/cache/GPU outcome. Client diagnostics
distinguish disabled settings, missing scene depth, resource failures and draw
submission. A successful submission does not prove visible pixels. Confirm the
affected scene on GTX 1060 before closing that bug.

Live installation/direct-launch check: `RP9.dll` and `freelancer.exe` installed
into `D:\Games\FL_MOD\bin` with verified backups. The 2026-11-11 22:38 launch
reported 117 stage cache hits and six newly stored/verified stages, then READY.
The sampled subsequent gameplay log contained no shader cache MISS; the intro
black-hole draw also succeeded. Evidence: `out/shader_startup/game_startup_verified.txt`.
Runtime diagnostics are in `%LOCALAPPDATA%\Freelancer\FLSpew.txt` on this installation
(the directory follows the game's local user-data path).

Windowed startup regression: the 23:02 reproduction recorded Clear failures with
valid color target/viewport but no bound depth surface (`depth=0x0`). The startup
window previously activated after INTZ creation; activation handlers can release
device resources while initialization is still running. Preparation now finishes
before depth and other device resources are created, and its window neither
activates on show nor on mouse clicks. Filtering PeekMessage by HWND alone does
not prevent sent activation messages. The native startup check verifies that
show/update/click/destroy preserve the active window and that depth clear succeeds.
Failure evidence: `out/shader_startup/clear_failure_reproduced.txt`.
After installation, the 23:07 windowed launch logged READY before INTZ creation,
with no Clear/INVALIDCALL failures in the sampled log and no accumulated menu
trails in the capture (`out/shader_startup/window_fix_verified.txt`,
`out/shader_startup/window_fix.png`). One clean launch is not proof against every
intermittent activation sequence.

All RP9 Ex shaders use the shared `CompileStage` wrapper. Successful Shader Model
3 bytecode is stored in `%LOCALAPPDATA%\Freelancer-Decomp\RP9\ShaderCache`.
`FREELANCER_SHADER_CACHE_DIR` overrides the directory for portable installs/tests.
No setting or game-data edits are required. Missing write permissions keep normal
compilation working; failed compilations are never cached.

The source is preprocessed through the existing include resolver first. SHA-256
keys cover expanded source (including nested includes and macro variants), entry
point, target profile, compiler flags, cache revision and the loaded D3DX/compiler
DLL contents. Filesystem timestamps alone do not validate a hit. The expanded
source used for the key is also the source actually compiled, avoiding a second
include read with potentially different contents.

Cache records bind their key, format version, exact bounded payload size and
SHA-256 bytecode checksum. A malformed/truncated/corrupt record is treated as a
miss and replaced after successful compilation. Records are written to unique
temporary files and atomically renamed, so concurrent readers cannot observe a
partial write. Old keys may remain on disk and can be removed with the cache
directory; it is rebuilt as needed. No GPU shader objects are persisted: each
device still creates them from the cached bytecode.

This covers reflective 2D/cube materials, local shadows, FXAA, soft particles,
volumetric and debug Ex programs. Hot reload still reads/preprocesses source and
detects changes; unchanged variants hit the cache. Cache HIT/MISS/store status
and elapsed milliseconds are reported through the existing RP9Ex diagnostic log.

Validation uses the same header/compiler path as RP9. The standalone regression
checks cold/warm bytecode identity, nested include invalidation, source/macro
changes, entry/profile/flag key separation, corrupt payload recovery, compilation
errors and unavailable cache-directory fallback. The HAL material/route checks
also run against the cache-enabled backend to check rendering and shader
recreation. A warm cache does not eliminate resource loading, shadow-map allocation
or any remaining driver-side shader creation cost.

On this machine, a cold surface PS compilation took 18,484 ms (2D) and 18,672 ms
(cube). Repeating each through the same cache-enabled path took 16 ms and 15 ms,
respectively, with identical bytecode lengths. These are shader preparation
measurements, not total game startup times. The GPU route/regression suite passed
with cache-enabled compilation. Prepared records for the matching compiler DLLs
can be copied into the user cache to avoid those particular first-launch misses.

## Key fixes and warm-up (2026-10-22)

Two inputs made keys differ between processes, so pre-built entries were never found and
every RP9 rebuild recompiled everything:

- The compiler identity hashed the module containing `&D3DXPreprocessShader`, which is the
  import thunk inside the *calling* module (RP9.dll, or the tool's exe), not d3dx9_43.dll. It
  now hashes `d3dx9_43.dll` and `d3dcompiler_43.dll` by name (the latter loaded explicitly, so
  load order does not matter).
- D3DX names an in-memory source `"<current directory>\memory"` in the expanded text's
  `#line` directives. The file names are removed before hashing and compiling.

The cache revision is now `v2`. RP9 starts a warm-up at device creation (in the menus): one
worker thread per surface variant compiles into the cache, and while it runs `ExSurfaceBegin`
uses the native materials instead of compiling on the render thread; a "caching shaders N/M"
line (Russian or English from port.ini [Language]) is drawn in the top-left corner at
SwapBuffers. With a warm cache the warm-up ends in milliseconds. `tools/warm_surface_cache`
compiles the same variants in parallel (about 71 s cold for the two full variants on this
machine, 31 ms warm); the real-RP9 route check, run from another directory, then finds every
surface entry (1 s instead of over a minute).

## Warm-up of every shader (2026-10-28)

The warm-up (`StartSurfaceShaderWarmup`) now covers all the shaders, not only `surface_material.hlsl`:

- the surface variants, including the asteroid / debris relief (`SURFACE_ROCK`, 4 variants);
- the other RP9 shaders as their sites compile them (whole file, no prefix): code beam, planet atmosphere /
  surface / ring, room material / shadow / contact, local shadow, FXAA, and SMAA's three entries;
- the client's `CreateExProgram` programs (engine heat, far rocks, field dust, hyperspace, jumpgate, jumphole,
  nebula, solar rays / corona, ship warp, space haze, trade lane): the `#line` header plus the file, with
  `#include` read from the shader folder.

Jobs run on a pool of `cores - 1` workers (not a thread per job), surface variants first; identical jobs are
dropped. A key that does not match a site's text only costs one wasted compile: the site compiles (and caches)
for itself as before. Check `shader cache HIT` lines in the RP9 log on the second launch: a `MISS` after the
warm-up means a mismatched key.

## Space/interior quality keys (2026-11-14)

`Rp9Startup::SurfaceQualityPrefix` is shared by the startup manifest, driver
warm-up and material compilation. Full 3/3 quality uses the unprefixed source,
preserving the existing cache. Reduced quality uses the same relief/highlight
defines at all three sites. The manifest includes the active space pair and,
when different and enabled, the interior pair, with duplicate jobs removed.
`tools/shader_startup/check_manifest.cpp` checks these source identities.

The startup counter reports successfully prepared stages, not the current
job index. Up to four compiler workers can all be busy while that count stays
unchanged. After a source change the full shadow variants may take minutes;
the startup window now displays elapsed seconds. This is not a compiler timeout
or a claim that compilation has completed. Already stored stages survive a restart.
