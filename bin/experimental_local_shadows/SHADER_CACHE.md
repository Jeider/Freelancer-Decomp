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
