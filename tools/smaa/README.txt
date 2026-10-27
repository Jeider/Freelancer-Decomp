SMAA 1x High (initial integration)

Enabled in RP9 before HUD/UI. No new user configuration in this version.
The existing FXAA shader and path remain intact; a failed SMAA setup/draw logs
the error and switches to FXAA before UI, without applying both filters.
Device resource reset permits retrying SMAA.

Coverage:
  SpaceCameraRenderSlot78 -> RenderEx::AfterSpaceScene -> AntialiasScene
  FirstPersonCameraSceneDraw -> AntialiasScene after world + cockpit, before HUD
  DrawClientLocation -> AntialiasScene after room, before menu/logo/UI
  (bases, Thorn cutscenes and animated main menu)

Three ps_3_0 passes use upstream SMAA High color edge detection, area/search
lookup tables and neighborhood blending. Source and license provenance lives
in DATA_EXTRA/SHADERS/SMAA/UPSTREAM.txt. No motion history, depth sampling or jitter.

The pass saves and restores device state, all supported render targets, depth
and viewport; clears intermediate targets every frame; recreates resources on
resolution changes/device reset. A scene copy preserves input and avoids sampling
the active render target. FXAA and gamma retain their existing code.

Checks:
  python tools/smaa/check_gpu.py
    Actual production ExApplySmaa plus actual device-call cache, D3D9 HAL in a
    hidden window: compiles all SM3 shaders, tests contour blending, untouched
    flat areas, state/depth/viewport restoration, inside/outside scene, odd size
    and 1080p, no previous-frame edges, resize, reset and missing assets.
    Close fullscreen games before running (they can make the test device lost).
  python tools/cockpit/check_scene_pass.py
    Includes ordering assertion: exactly one AA pass after cabin, before HUD;
    tests RP8/RP9 and cockpit/HUD/lighting combinations.

Installation:
  Build client and RP9 Release Win32, then:
  python tools/smaa/prepare_install.py
  python tools/smaa/install.py --apply
  Stage, verify originals/payload, back up existing files, install and hash-check.
  On failure roll back. Explicit rollback: --restore <backup directory>.
  No port.ini changes. Existing saved settings and gameplay changes are retained.

Remaining manual validation: actual space/base/cutscene/cockpit images in motion,
text sharpness, Alt+Enter and GPU frame time with a representative busy scene.
