# RP9 shader bytecode cache

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
