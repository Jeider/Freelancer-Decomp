# Layered-station shadow optimisation

2026-10-22: install Freelancer.exe and RP9.dll together. No shader/material/model
changes are required for this optimisation.

Enabled by default. Add `[Render] shadow_static_cache = 0` to port.ini to compare
with the previous full-station shadow submission path (restart required).

- Far map caches individual stationary solar components, including fixed panels.
- Ships/asteroids stay live. Moving attachments leave the cache immediately.
- A stationary component needs 500 ms of observations before entering the cache.
- Any fixed component uses the cache. The station map is not copied into the far map:
  receivers sample both (sampler s11) and take the darker result, so a ship above a station
  beyond its shadow reach no longer cuts a lit hole into the station's shadow.
- World-anchored map survives camera rotation and limited translation; changes
  to geometry, sunlight, region or the `shadow_static_cache_seconds` age limit
  (default 10 s) trigger a rebuild.
- Near map stays live, with conservative component-level light-volume culling.
- Groups of depth-only component submissions share a material-batch flush.
- Additional texture memory: 256 MiB at 8192 / 64 MiB at 4096 (`shadow_far_resolution`). Insufficient memory
  headroom or allocation failure selects the ordinary rendering path.
- Log counters: `static shadow cache: builds ..., reused ... (far cascade)`.

Validation: Win32 Release client/RP9 builds; source-extracted GPU tests for
static/live depth composition, removal of moving shadows, camera translation
and rotation, invalidation and release; component-motion and near-culling tests.
In-game FPS benefit needs comparison at the same position/view near ku_tgk_01.
Additional main-pass instancing/state optimisations are described in
RENDER_OPTIMIZATION.md. The shadow cache itself does not perform occlusion culling.
