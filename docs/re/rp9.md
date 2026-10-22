# RP9.dll — Direct3D 9 render pipeline (a mirror of RP8)

## Purpose

`RP9.dll` is a port-only module (retail has none): a Direct3D 9 fork of `RP8.dll`. It answers the
same IIDs as RP8 (`RenderPipeline8B`, `VertexBufferManager`, `RPDraw`, `RPIndexBuffer`,
`RPVertexBuffer`, `GammaControl`, `RPTexture`, `AggregateComponent`), reads the same
`[RenderPipeline]` section with the same keys and registers as the `DirectX9` component
(`kRp9ComponentName`, priority `0x40000000`). The consumers (exe, Shading, flmaterials, alchemy,
Deformable2, RendComp, ximage) do not change: they look interfaces up by IID.

Build: the `FreelancerRp9` property (`src/Directory.Build.props`, `src/Freelancer.Diagnostics.props`,
VS property page "Features"), `0` by default. With `0`, `RP9.vcxproj` turns into an empty Utility
project (no `RP9.dll`, no DirectX SDK June 2010 needed) and the client's Ex hooks (`render_ex.*`,
`nebula_volume.*` and their calls in `cli_asteroid`, `cli_nebula`, `client_gameobj`,
`engine_init`, `main`, `space_scene_obj_draw`, `star_sphere`, `star_sys`) sit under
`#ifdef FREELANCER_RP9` — the client is identical to master. With `1` both are built.

Runtime selection: `bin/DACOM.INI` — `RP9.dll` in `[Libraries]` (commented out by default), and in
`[System]` exactly one line is active: `DirectX8` (the default) or `DirectX9`.

## Relation to RP8

- **RP8 is the reference.** RP9 behaviour = RP8 behaviour; every RP8 change is repeated in RP9.
  The functions in `src/RP9/RP9.cpp` follow the order of `RP8.cpp`, each with a
  `// RP8: <class>::<name>` line; `Mgsdb.*` is a copy of `src/RP8/Mgsdb.*`.
- Comments with `rp8.dll` addresses are evidence for RP8 (D3D8), not a claim that the D3D9 calls
  are retail.
- Places where D3D9 cannot reproduce RP8 exactly are marked `// RP9-GAP:` (list below).
- The module is not entered in decomp-tracker (there is no listing); `deviations.md` does not
  cover it — the retail path (RP8) remains the default.

## Build and dependencies

- `d3d9.h` / `d3d9.lib` come from the Windows SDK. D3DX9 and DxErr come from the DirectX SDK
  June 2010 (`$(Dx9SdkDir)`, default `$(DXSDK_DIR)`). Its `Include` is appended at the **end** of
  `IncludePath` (it holds an old `d3d9.h`); `d3dx9.lib` and `DxErr.lib` are linked by full path,
  `Lib\x86` is not put on the library path (it holds an old `d3d9.lib`).
- `RP_DIRECT3D9` selects the D3D9 branch of `render/d3d8_min.h`: `<d3d9.h>` instead of `d3d8.h`,
  `D3DLIGHT8 = D3DLIGHT9`, `D3DMATERIAL8 = D3DMATERIAL9` (identical layouts, static_assert).
  `d3d8types.h` and `d3d9types.h` cannot share one translation unit; every other module builds
  the `#else` branch unchanged.
- The `d3dx9_43.dll` (x86) runtime is needed next to the exe (`SysWOW64` has none): RP9's PostBuild
  extracts it from `Redist\Jun2010_d3dx9_43_x86.cab` into `$(OutDir)` (`bin\` / `bin_debug\` /
  `binasan\`) when the file is not there yet.
- D3DX9 has no `D3DXGetErrorStringA` — the error text comes from `DXGetErrorStringA` (DxErr.lib,
  which needs `legacy_stdio_definitions.lib`).

## The object and the data it hands out

- The object layout is not retail: there are no `0x230C` static_asserts, RP8's raw offsets became
  named fields (`ScratchIb_` = node +0x14C, `PipelineStates_[14]` = slots +0x354,
  `VbList_`/`IbList_` = +0x22E4/+0x22F0). RP8's "accidental" aliases are kept:
  `GetPipelineState(0xE)` reads `Ability_[0]`, `QueryDeviceAbility(0x14)` the `Cached`
  render state 0.
- Everything goes out in D3D8 form: the 0x520-byte `GetDeviceInfo` record
  (`FRp9Identifier8` + `D3DDISPLAYMODE` + `FRp9Caps8` + 4 dwords, `Rp9D3d8Types.h`), the 10-dword
  mode block, `D3DLIGHT8`/`D3DMATERIAL8`, `_D3DXIMAGE_INFO` (7 dwords — D3DX9 has the same layout).
- The render-state (256) and texture-stage (8×29) caches use **D3D8 numbering**; `Get*` answer
  exactly as RP8, the translation happens only when sending to the device.

## D3D8 → D3D9 translation table

| RP8 (D3D8) | RP9 (D3D9) |
|---|---|
| `Direct3DCreate8(0x78)` | `Direct3DCreate9(D3D_SDK_VERSION)` |
| `GetAdapterIdentifier(i, 2 = NO_WHQL)` | `GetAdapterIdentifier(i, 0)` → `FRp9Identifier8` (without `DeviceName`) |
| `GetDeviceCaps` (D3DCAPS8) | `D3DCAPS9` → `FRp9Caps8`: the prefix is copied, `RasterCaps`: `ZBIAS` ← `DEPTHBIAS`, `ANTIALIASEDGES` ← `D3DLINECAPS_ANTIALIAS`, D3D9 bits cleared; `Caps2`: `CANRENDERWINDOWED` set, D3D9 bits cleared |
| `GetAdapterModeCount/EnumAdapterModes(i, n)` | walks formats `R5G6B5`, then `X8R8G8B8` as one index list |
| `D3DSWAPEFFECT_COPY_VSYNC` (4) | `COPY` + `PresentationInterval`: `ONE` windowed, RP8's interval full-screen |
| windowed, `COPY` | `COPY` + `INTERVAL_IMMEDIATE` (windowed D3D8 does not wait for VBlank) |
| `FullScreen_PresentationInterval` | `PresentationInterval` (same bits); `MultiSampleQuality = 0` |
| `CreateDevice` flags | the same `D3DCREATE_*` bits; without `FPU_PRESERVE` D3D9 also drops x87 to 24 bits |
| `SetVertexShader(FVF)` | `SetFVF(FVF)` (shaders are never set) |
| `SetStreamSource(0, vb, stride)` | `SetStreamSource(0, vb, 0, stride)` |
| `SetIndices(ib, Base)` | `SetIndices(ib)`; `Base` is remembered (`DeviceBaseVertex_`, 0 after create/reset) and goes into every `DrawIndexedPrimitive` |
| `Lock(..., BYTE**, ...)` | `Lock(..., void**, ...)` |
| `Create{Vertex,Index}Buffer`, `CreateTexture` | + `HANDLE* = nullptr` |
| `D3DTSS_ADDRESSU/V/W, BORDERCOLOR, MAG/MIN/MIPFILTER, MIPMAPLODBIAS, MAXMIPLEVEL, MAXANISOTROPY` (13–21, 25) | `Set/GetSamplerState(stage, D3DSAMP_*)`, same values |
| `D3DRS_SOFTWAREVERTEXPROCESSING` (153) | `SetSoftwareVertexProcessing(v != 0)` |
| `D3DRS_ZBIAS` (47) | `D3DRS_DEPTHBIAS` (float), formula below |
| `D3DRS_EDGEANTIALIAS` (40) | `D3DRS_ANTIALIASEDLINEENABLE` |
| `D3DRS_PATCHSEGMENTS` (164) | `SetNPatchMode(float)` |
| `D3DRS_LINEPATTERN` (10), `D3DRS_ZVISIBLE` (30) | cache only, never sent to the device (treated as set) |
| other `D3DRS_*` | same numbers and values (`D3DORDER_*` = `D3DDEGREE_*`) |
| `GetBackBuffer(0, type, &s)` | `GetBackBuffer(0, 0, type, &s)` |
| `CreateImageSurface` | `CreateOffscreenPlainSurface(..., D3DPOOL_SYSTEMMEM, ...)` |
| `CopyRects(back → copy)` | no rect: `GetRenderTargetData`; with a window rect: `D3DXLoadSurfaceFromSurface(..., FILTER_NONE)` (the back buffer is lockable — lock_buffer requires it) |
| `GetFrontBuffer(s)` | `GetFrontBufferData(0, s)` |
| `Set/GetGammaRamp(...)` | `(0, ...)` — swap chain 0 |
| D3DX 8.1 `CreateTexture/CubeTexture FromFileInMemory`, `LoadSurfaceFromMemory/FromSurface/FromFileInMemory`, `GetImageInfoFromFileInMemory`, `SaveSurfaceToFileA` | the D3DX9 functions of the same name with the same arguments and filters |
| `D3DXGetErrorStringA` | `DXGetErrorStringA` (DxErr) |
| DirectDraw7 for the video-memory size | unchanged |

## ZBIAS → DEPTHBIAS

D3D8 `ZBIAS` is an integer 0..16 in driver units; D3D9 `DEPTHBIAS` is a float added to the [0,1]
depth. One ZBIAS step is taken as one Z-buffer step:

`DEPTHBIAS = -ZBIAS · 2^-ZBits`, where `ZBits` is the depth of the auto buffer (`DepthFormatZBits`,
dword 5 of the mode block; D16 → 1/65536, D24* → 1/16777216, D32 → 2^-32).

The minus sign: a larger ZBIAS pulls geometry closer, a positive DEPTHBIAS pushes it away. `ZBits`
is set by `create_buffers` before the default states are applied. This is the module's only
numerical approximation.

## Display mode order

D3D8 returns every mode in one list in runtime order; D3D9 enumerates per format. RP9 joins them:
first all `D3DFMT_R5G6B5` modes (D3D9 treats 565 and 555 as one and returns the driver's real
format), then `D3DFMT_X8R8G8B8`. `R8G8B8` is never a display format in D3D9 and `A2R10G10B10` did
not exist in D3D8 — neither is enumerated. Mode indices are RP9's own (`GetDisplayModeEnum` /
`SelectMode` / `create_buffers` agree with each other); they need not match RP8's indices.

## Known differences from RP8 (`RP9-GAP`)

- `ZBIAS → DEPTHBIAS` — an approximation (above).
- `LINEPATTERN`, `ZVISIBLE` — never reach the device.
- The `D3DTEXF_FLATCUBIC` (4) / `GAUSSIANCUBIC` (5) filters are passed as they are; D3D9 has none.
- `SetSoftwareVertexProcessing` on a non-mixed device may return a different HRESULT than D3D8's
  `SetRenderState` (on failure the cache behaves as in RP8).
- Display mode order/indices (above).
- The other `D3DCAPS9` dwords (apart from `RasterCaps`/`Caps2`) go into the D3D8 form with D3D9
  bits; RP8 does not read them, and `flconfigdatabase.txt` has no caps conditions.
- `WHQLLevel` is whatever D3D9 returns without `D3DENUM_WHQL_LEVEL`.
- HRESULT text in the logs comes from DxErr (`Unknown` for unknown codes) instead of D3DX 8.1.
- Texture/cube-map loading: D3DX9 picks the format and mip chain, not D3DX 8.1.
- `SetPipelineState` with an id outside 0..0xE writes nothing (RP8 writes into arbitrary object
  memory).

## Ex extensions (Direct3D 9, port only)

New functionality of the RP9 branch (the basis for volumetric nebulae, soft particles, HDR).
Retail and RP8 have no counterpart; listing verification, the tracker and `deviations.md` do not
apply here.

### Interfaces

`src/include/render/IRenderPipelineEx.h`, IIDs in `dacom_iids.h` (port-only):
`IRenderPipelineEx` = `"RP9_IRenderPipelineEx"`, `IRPDrawEx` = `"RP9_IRPDrawEx"`.
`FDirectX9` inherits both and `QueryLocal` hands them out; the implementation is
`src/RP9/RP9Ex.cpp`, the state `FRp9ExState` (`RP9Ex.h`, member `FDirectX9::Ex_`). **RP8 does not
know them → QueryInterface fails → the consumer stays on its old algorithm.** The API has no
notion of "nebula":

- `GetExCaps` — VS/PS versions, INTZ (whether a scene depth exists), FP16/FP32 RTs, FP16 blending,
  volume textures, maximum sizes.
- Programs: `CreateExProgram(IFileSystem*, path from the FileSystem root, VS entry, PS entry)` —
  reads the file through `IFileSystem` (the exe passes `RenderEx::GetExtraData()`, rooted at
  `DATA_EXTRA`), `#include` through the same FileSystem (first next to the file, then from its
  root), `D3DXCompileShader` to `vs_3_0` / `ps_3_0`. A
  handle is returned even when compilation fails (result `GR_GENERIC`, the compiler text goes to
  FDUMP line by line as `ERROR`). `ReloadExPrograms` re-reads and rebuilds everything; on failure
  the previous bytecode and shaders stay. `DestroyExProgram`.
- Textures: `CreateExRenderTarget` (a size or a fraction of the back buffer; formats A8R8G8B8, L8,
  A16B16G16R16F, R16F, R32F, G16R16F), `CreateExVolumeTexture` (MANAGED, 1 level, the data is
  copied — for noise), `DestroyExTexture`, `GetExTextureSize`, `GetSceneDepth`.
- Pass: `BeginExPass` / `EndExPass`; inside them `SetExRenderTarget`, `BindExProgram` (`nullptr`
  goes back to fixed function), `SetExVertexConstants` / `SetExPixelConstants`, `BindExTexture` /
  `BindExPipelineTexture` (an ordinary `IRenderPipeline`/`IRPTexture` handle) on samplers 0..15
  with explicit sampler states.
- `IRPDrawEx`: `DrawFullscreenQuad` (FVF XYZ|TEX1 in clip space, the D3D9 half-pixel offset is
  already applied for the current target's size; the VS just passes the position through —
  `RPExFullscreenVS`), `DrawExPrimitiveUp` (the caller's FVF). Both work only inside a pass with a
  program bound; they follow the same scheme as `IRPDraw::DrawPrimitive` (stream cache →
  `FlushDrawState` → `DrawPrimitiveUP` → stream cache reset).

### Scene depth (INTZ)

`CreateBuffers` asks `ExWantsIntzDepth`: when the format chosen by `PickDepthFormat` is 24-bit
(D24S8/D24X8/D24X4S4) and the adapter supports `INTZ` as a depth-stencil texture, the device is
created (or `Reset`) with `EnableAutoDepthStencil = FALSE`, and right after that
`ExCreateDeviceResources` makes a back-buffer-sized INTZ texture and binds its level 0 through
`SetDepthStencilSurface`. `AutoDepthStencilFormat` stays the chosen format, so the depth/stencil
bits in the mode block and the ZBIAS scale do not change. If the INTZ texture could not be created,
an ordinary surface of the chosen format is bound (no scene depth). D16/D32 or an adapter without
INTZ take the old path, and `GetSceneDepth` answers `GR_GENERIC`. The replacement is transparent
to fixed-function rendering.

### Pass contract and RP9's caches

Everything that writes to the device past RP9's lazy caches is done only inside a pass, and
`EndExPass` restores consistency:

- **Render states** are changed by a pass only through the cache (`MarkDirty`; the caller uses the
  ordinary `IRenderPipeline::SetRenderState`). `BeginExPass` copies the `Pending` column and sets a
  base (no blending, alpha test, fog, stencil or lighting, `CULL_NONE`, all colour channels written;
  without `RPExPassKeepDepth` also `ZENABLE`/`ZWRITEENABLE` off).
  `FRp9RenderStateCache::RestorePending` in `EndExPass` queues the previous values — the device
  receives them at the next flush, and `Get*` answers as before the pass.
- **Stages 0..7** (fixed function): on the first touch of a sampler the pass saves the texture
  binding and the 10 sampler entries of the cache (`ExSaveStage`) and marks them invalid, so that
  `IRenderPipeline` calls inside the pass reach the device; `ExRestoreStage` in `EndExPass` resends
  what was saved (unknown entries get the D3D9 defaults and stay unknown). Samplers 8..15 are simply
  unbound.
- Shaders are unbound; the colour target and the depth surface are the ones from before the pass
  (`GetRenderTarget`/`GetDepthStencilSurface` at the start); the viewport comes from
  `ViewportCache_` together with its validity bytes (`SetRenderTarget` resets the viewport in
  D3D9). Device `Get*` state calls are not used — it works on a PUREDEVICE too.
- The scene depth cannot be the bound depth surface and a texture at the same time: binding
  `GetSceneDepth` to a sampler takes the depth surface off until the end of the pass (and turns Z
  off), and `SetExRenderTarget(..., bKeepDepth = 1)` unbinds samplers holding the scene depth.
- Passes do not nest. Textures (`DestroyExTexture`, and the pipeline's own `DestroyTexture`) must
  not be destroyed inside a pass.

### Surface route between draws

The reflective surface shader (`ExSurfaceBegin`, outside passes) keeps its device state between
draws instead of restoring fixed-function state after each one:

- Its environment map is on sampler 10 and the shadow maps on samplers 8/9. Fixed-function
  rendering only uses stages 0..7, so nothing is saved or restored per draw; the environment
  sampler states are copied from the stage that holds the map (address U/V/W, filters, max
  anisotropy, LOD bias).
- Vertex and pixel shaders stay bound after a surface draw. `ExSurfaceRelease` unbinds them before
  the next fixed-function draw (all five draw paths), and before `BeginExPass`,
  `BeginLocalShadowMap` and the frame antialiasing. It is a no-op inside a pass or a shadow map.
- `FRp9DeviceCallCache` counts shader, pixel-constant and sampler-8+ writes (`Invalidate`, after
  every state-block `Apply`, counts as one). The surface route re-sends a shader, a sampler or a
  block of pixel constants (material 0..11, lights 12..51, shadow frame 52..76, glints 77..93,
  style/tier 94..95) only when it differs from what the route last sent or its counter moved.
- `ExShadowRelease` and `ExReleaseDeviceResources` unbind samplers 8..10 first: the device holds a
  reference to bound textures and `Reset` needs every default-pool one released.

### Device loss/reset

`DestroyGpuResources` (also called by `CreateBuffers` before `Reset`) closes an open pass, takes
off and releases the INTZ/fallback depth surface and every Ex render target (DEFAULT pool).
`CreateBuffers` recreates them behind the same handles after a successful `CreateDevice`/`Reset`.
Programs and MANAGED volumes survive `Reset`; `ShutdownPipeline` releases them too (the bytecode and
the volume data remain and are restored on the next device), the destructor frees the handles.

### Data and the exe

- The port's data lives in `DATA_EXTRA/`, tracked by git, not inside the retail `DATA` (which is
  not tracked): an install puts the retail or mod `DATA` in place and adds `DATA_EXTRA` next to it,
  without copying files over `DATA`. `RenderEx::Startup` finds it next to the `[Freelancer] data
  path` directory (`..\DATA` → `..\DATA_EXTRA`, an absolute path the same way) and opens a second
  DOS FileSystem on it, described like `DALib::OpenData`'s (`RenderEx::GetExtraData`). Without the
  folder it logs an `ERROR` and the extensions stay off (`IsAvailable` false, retail paths).
- `DATA_EXTRA/SHADERS/` — shaders (`common.hlsli`: `RPExFullscreenVS`, `RPExLinearDepth`;
  `debug_depth.hlsl`; the volumetric nebula — `nebula_volume.hlsl` + `nebula_volume.hlsli`,
  `nebula_composite.hlsl`). `DATA_EXTRA/VOLUMETRIC/volumetric.ini` — settings (`[Debug]`,
  `[Nebula]`, `[NebulaOverride]`; every key is commented in the file itself). Paths are relative to
  the `DATA_EXTRA` root.
- `src/freelancer/Client/render_ex.*`: `RenderEx::Startup` (after `StartupRenderPipeline` in
  `InitializeEngine`) — QI of both interfaces and reading the ini through `INI_Reader`;
  `RenderEx::Shutdown` (after `ShutdownRenderMgr` in `main.cpp`); `RenderEx::AfterSpaceScene` in
  `SpaceCameraRenderSlot78` — after `SpaceObjDrawPass`, before the depth clear under the HUD.
- `RenderEx::GetCaps` caches `GetExCaps`. There is usually no device yet in `Startup`, so the caps
  are queried lazily (the first `AfterSpaceScene` or `NebulaVolume::BeginFrame`) and logged once as
  a `NOTICE` line such as
  `Ex caps: adapter "NVIDIA GeForce RTX 5080", vs 3.0 (4096 slots), ps 3.0 (4096 slots, 65535
  executed), INTZ scene depth 1, volume textures 1 (max …), FP16 target 1, FP16 blending 1,
  R32F target 1`.
- `FRPExCaps` is versioned by its `Size` field: the caller sets its own `sizeof`, `GetExCaps`
  accepts anything not smaller than `RPExCapsSizeV1` (32 bytes, the fields up to `Reserved[3]`),
  fills `min(Size, its own sizeof)` and returns the size filled. New fields are only appended.
  Version 2: `MaxVertexShaderSlots` / `MaxPixelShaderSlots`
  (`D3DCAPS9::MaxVertexShader30InstructionSlots` / `MaxPixelShader30InstructionSlots`),
  `MaxPixelShaderInstructionsExecuted` (`MaxPShaderInstructionsExecuted`),
  `AdapterDescription` (`GetAdapterIdentifier`).
- **The SM3 instruction budget.** 512 slots is only the guaranteed Shader Model 3 minimum
  (`D3DMIN30SHADERINSTRUCTIONS`), not a compiler limit: `fxc` / `D3DXCompileShader` do not check it
  for `ps_3_0`. The limit is set by the driver: on the owner's RTX 5080
  `MaxPixelShader30InstructionSlots` = `MaxVertexShader30InstructionSlots` = 4096,
  `MaxPShaderInstructionsExecuted` = 65535; the device accepts a 4071-slot shader and rejects a
  4401-slot one. So a consumer checks its measured size against `MaxPixelShaderSlots`, not 512.
- **Hot reload** (`AfterSpaceScene`, i.e. only in space). The real paths are found once in
  `Startup` the same way as the ini (`GetFileSysPath` through `DALib::Data`): `volumetric.ini` and
  the mask `<DATA>\SHADERS\*.hlsl*` (.hlsl and .hlsli). Once a second by `GetTickCount`: one
  `GetFileAttributesEx` for the ini and one directory walk (`FindFirstFile`/`FindNextFile` return
  every file's write time) for the shaders; no memory allocation. The ini changed → `[Debug]` and
  the volumetric nebula settings are re-read (effective from the next frame). A shader file's write
  time or the number of shader files changed → `ReloadExPrograms` (a program that fails to compile
  keeps its previous bytecode, errors go to the RP9 log) and `NebulaVolume::OnProgramsReloaded`.
  Every reload is a `NOTICE` line in the log.
- `[Debug] scene_depth_view = true` — debug display of the scene depth: a pass onto the back buffer
  without a depth surface, `debug_depth.hlsl`, the constants are the z/w rows of the current
  projection (`GetProjection`), near/far are derived from them. Logarithmic scale, or linear
  (`scene_depth_view_max`).

### Volumetric nebula

The nebula is drawn by ray marching through a volume instead of the retail fog — from inside
(phase 1) and from outside, up to four nebulae per frame (phase 3). The volume is not "fog with
noise" but a medium of two parts (a thin uniform haze and dense cloud masses with empty corridors
between them) that *scatters* the light of the key source and the ambient instead of glowing by
itself: the structure shows through uneven lighting (lit edges, dark self-shadowed cores and
undersides, light shafts in the haze), and the star sphere and the space colour are visible behind
the volume. Code: `src/freelancer/Client/nebula_volume.*`, shaders:
`DATA_EXTRA/SHADERS/nebula_volume.hlsl` (+ `nebula_volume.hlsli`) and `nebula_composite.hlsl`, settings:
`[Nebula]` / `[NebulaOverride]` in `DATA_EXTRA/VOLUMETRIC/volumetric.ini`.

**When it is on.** `NebulaVolume::BeginFrame(Camera, G_FieldController, G_FieldEnclosure,
options, G_SpaceDrawFar)` in `SpaceObjDrawPass`, right after `SelectFieldControllers`, picks the
frame's nebulae from all the registered ones (`RegisterNebula`): every nebula the camera sits in
(immersion +0x294 > 0) and, with `exterior`, every nebula whose surface is closer than
`exterior_max_distance` (the distance is measured the way retail measures immersion: the length to
the centre minus `GetRadiusAlong`); nearest first, at most `max_nebulae` (≤ 4; no memory
allocation — insertion into a four-element array). Nothing is picked if: there are no Ex interfaces
(`RenderEx::IsAvailable`, i.e. RP9), the caps do not give vs/ps 3.0, volume textures or
`MaxPixelShaderSlots >= kRaymarchPsSlotsRequired`, there is no INTZ scene depth (`GetSceneDepth`,
checked every frame), the `[EFFECTS]`/`NEBULA` options are off (retail draws no nebulae then), the
nebula's `enabled` is off, the programs did not compile, the noise or the target were not created.
Then `IsActive()` is false and every retail path runs byte for byte as before (RP8, no INTZ, off in
the ini, no nebula in range). The selection lives from `BeginFrame` to `Draw` of one frame; the
target resolution comes from the nearest nebula's settings.

**What it replaces** (the questions in the retail code are `Replaces*`; each can be turned off with
a `replace_*` key for comparison). The interior replacements apply to any nebula drawn; the
exterior ones (object fog, "bits", fill sheets) only while the volume draws the nebula at full
strength (closer than `exterior_max_distance − exterior_fade_distance`); in the fade band both the
(weakening) volume and the retail exterior are drawn:

- the fullscreen fog quad `FNebulaEffect::DrawFogOverlay` (`ReplacesFogOverlay`); the +0x2b8 flag
  and the lightning after the quad stay;
- the interior cloud puffs `DrawCloudsPanels` (`ReplacesClouds`) — together with their own D3D fog;
- the D3D fog of objects inside this nebula (`ReplacesObjectFog`): the fog block of
  `StarSysApplyObjectLighting` (FUN_005554d0) is skipped when the object's "containing nebula" is
  the active controller. Ships and solars (Gameobj +0x38), first person
  (`space_camera_first.cpp`) and asteroid fields with `contains_fog_zone` (`CliAsteroidAmbientPass`
  passes the controller) all go through this function, so there is no separate predicate for
  asteroids. The ambient lerp in the same function stays. Objects inside a nebula the volume does
  not draw (or draws in the fade band) keep the retail fog;
- the exterior billboards `NebulaDrawBolts` (FUN_00507ed0, misnamed "bolts" — they are the exterior
  puffs) in `DrawBoltsPass` (`ReplacesExteriorBits`, `replace_exterior_bits`);
- the two crossed fill sheets `NebulaUpdateBoltCamera` (FUN_005074e0) in `DrawFogShell`
  (`ReplacesFillSheets`, `replace_fill_sheets`).

Both exterior gates sit inside the methods and skip only the draw call itself — the path the
retail function takes on its own (no fill shape / zone out of view); the states around it stay.
So they apply both to the controller (`DrainMeshAndAsteroids`, from outside and when partly
immersed) and to the `ZItemNebula` nodes of far bucket 2 (`FZItemNebula::Draw`).

**What stays retail** and why (every D3D fog site in the space frame):

| Site | Decision |
|---|---|
| `StarSysApplyObjectLighting` — object / asteroid fog | replaced (see above) |
| `NebulaDrawCloudsPanels` (texture_panels.cpp) — puff fog | goes away with the puffs |
| `DrawBoltsPass` (cli_nebula.cpp) — exterior billboard fog | the billboards themselves are replaced (`ReplacesExteriorBits`); `FogApplyColorAndRange` and the fog switch-off around them stay |
| `SpaceObjDrawPass`, effects block (0x0051c741) — black fog of alchemy effects | stays: effects are drawn after the volume and are not attenuated by it; without this fog distant additive effects would shine through the nebula |
| `GfFogApply` / `room_control.cpp` | not space (base rooms) |

Also unchanged: the ambient lerp to `[NebulaLight] ambient`, the DynamicLightning light (while the
camera is fully inside and the volume's lightning is on, the strikes drive it — see "Lightning"),
`sun_burnthrough` (the stars' `DrawBillboard`), the exclusion shells (`DrawExclusionShell`: retail
draws them only for the controller while the camera is inside an exclusion zone — from outside
there is nothing to replace; from inside the volume cuts the zones out itself, the shell stays as
in phase 1).

**Real background** (`real_background`, `extend_far_plane`; the questions `ShowsRealBackground` /
`InsideFarPlane`). Fully immersed (`enclosure == 2`), retail draws no star sphere, clears the frame
with the fog colour and cuts the far plane at `FogFarClamp` (≈ `[Fog]` far + 500). With a thin
haze that would give a flat fog-coloured background in the gaps and objects popping in at the
plane, so while the volume is drawn:

- the star sphere is drawn even when fully immersed;
- the clear colour stays the system's `space_color`; `FillFogRgb` is still called (it has side
  effects — the background-lightning timer and `rand()`), only its result is discarded, so the
  background lightning flash through the clear colour disappears — distant lightning strikes in the
  haze and a faint flash of the whole nebula (`lightning_far_chance`, `lightning_haze_flash`)
  replace it;
- the far plane inside is pushed out to 1.5 march limits (there the haze has hidden everything:
  `march_end_transmittance^1.5`), but not beyond `G_SpaceDrawFar`.

`ShowsRealBackground` is true from `BeginFrame` to the end of the frame (the clear colour is set
after `Draw`) when the volume draws the field controller from inside; a failed controller draw
clears it. The real background and the far plane matter only at immersion ≥ 1 (`enclosure == 2`),
and before that retail shows the stars and the space colour anyway — so nothing switches abruptly
when entering a nebula from outside. On RP8, with the volume off or with no nebulae, everything is
as in retail.

**Outside and the transition.** Inside and outside use the same shader code: the ray starts at the
zone entry point (`max(entry, 0)` — from inside that is the camera), the march limit is counted
from it, the haze tail runs to the zone exit or the scene. Crossing the surface changes only the
geometry, so there is no jump. Everything exterior is off exactly where the entry is the camera
itself: the LOD and the large-scale shadow depend on the distance to the entry (0 inside), the
`exterior_max_distance` fade on the camera's distance to the surface (0 inside, strength 1). The
key star lights from the camera position when inside (as in phase 1); outside, the reference point
moves smoothly to the zone centre (`s / (s + largest radius)`), so a distant nebula is lit from
where it is. When partly immersed, the fill sheets and billboards are now replaced too — the volume
does not overlap the retail shell on entry.

**Several nebulae.** Each picked nebula has its own ray march into the shared half-res target and
its own composite onto the back buffer, far to near (`scene · T + light` in turn). A single pass
looping over the nebulae at each step was rejected: one nebula's constants are 103 of the 224
`ps_3_0` registers (with eight exclusion zones), and the executed instructions per step would be
multiplied by the number of nebulae; separate passes are also cheap where the ray misses the zone
(early exit after ~40 instructions). The price: overlapping zones add their media without mutual
attenuation inside the overlap, and tone mapping is per layer — zones rarely overlap.

**The far bucket.** Retail puts distant solars (beyond `G_SpaceDrawRange`) into bucket 2 and draws
them without a depth test, in painter order together with the `ZItemNebula` nodes. A volume over
the opaque scene would paint over a planet standing in front of a distant nebula. So a nebula whose
surface is beyond the opaque scene's far plane (`G_SpaceDrawFar`, the whole drawn world in front of
it), and which is not the controller (only those have a node), is drawn in its bucket-2 node
(`NebulaVolume::DrawBackground` from `FZItemNebula::Draw`) without the scene depth (a flag in the
ray march's c78.w and the composite's c2.w). If the node is not in the frame (the buckets were
cleared by full immersion in another nebula), it is drawn in `Draw` with the others.

**Stars and planets (objects without depth).** A sun is only glow sprites (`FStarSphere::
DrawBillboard`: star_glow and star_center, no depth test or write, both in the solar's ordinary
draw through `DrawSimple` and in the retail `sun_burnthrough` inside a nebula); bucket 2 draws
distant planets and moons without depth test or write. In INTZ, under them is whatever lies behind
them (usually sky, 1.0), the volume marched the whole way behind them, and the `scene · T + light`
composite painted over a star standing in front of the nebula (Red Dwarf in Omicron Gamma,
7.5 km). A star in the near bucket has no depth either, so the bucket is not the issue. The draw
order does not change; instead the volume learns about these objects from the places where they
are actually drawn in the frame (only while active, from `BeginFrame` to the end of `Draw`, no
memory allocation):

- `NoteOpaqueSphere` (from `FClientSolarGameobj::Slot188`, the planet/moon branch) — the bounding
  sphere (`Slot178`); up to the 4 largest on screen (c93..c96: centre relative to the camera,
  `|c|² − r²`). The ray ends at the intersection with the sphere as it would on the scene depth —
  a planet in front of the nebula is visible, inside it fogged to its distance, behind it hidden.
- `NoteStarGlow` (from `DrawBillboard`) — the position, the sprite's half size (the larger of
  star_glow and star_center × radius × scale) and its alpha; drawing the same star again in a frame
  merges; up to 3 (c97..c101). The glow is additive and the sky shows beneath it, so the ray is not
  cut (otherwise the nebula behind the star would have a glow-sized hole): inside the glow disc the
  pixel's transmittance is pulled from the whole ray's transmittance towards the transmittance up
  to the star with the weight `star_glow_weight · alpha · (1 − r/R)` (r — the offset in the sprite
  plane). The volume's light does not change — the nebula behind the star adds to the glow, as it
  should. The transmittance up to the star: 1 in front of the zone entry (a star in front of the
  nebula is fully visible), the closed-form tail beyond the marched part (a star behind the nebula —
  as before), inside — an estimate with the extinction spread evenly over the marched part
  (recording it per step would need a temporary register the march does not have).

Each pass uses what was drawn before it: `Draw` — everything, a bucket-2 node (`DrawBackground`) —
only the suns/planets the bucket drew before the node (i.e. beyond the nebula's surface in the
retail sort); those drawn after the node cover the nebula anyway. So several nebulae combine
correctly: a star between a far and a near nebula is not fogged by the far one and is fogged by the
near one. A star's flares/corona (`Draw`/`DrawFlare`) are drawn after the volume in screen space,
the retail zone occlusion dims them, the volume does not touch them. On RP8 and with the volume off
`Note*` do nothing.

**LOD.** By the distance from the camera to the entry point (`lod_start_distance` ..
`lod_end_distance`): the step count drops to `lod_min_step_fraction` (the steps are spread over the
segment inside the zone, no longer than the march limit — a distant nebula costs about as much per
pixel as from inside); past the `lod_shadow_switch` fraction of the range the shadow ray takes 3
samples, merged in pairs from six (c81..c83: pair middle, sum of the weights); the detail erosion
noise is blended towards its mean when its texel is smaller than the pixel footprint
(`T · pixel angle`) or half a step — without mips this removes edge shimmer. The base noise and the
warp are left alone (their cells are an order of magnitude larger). In addition, with LOD the
clouds turn into soft masses instead of a "camouflage" of sharp blotches: the coverage threshold
ramp widens `1 + far_cloud_softening · LOD` times around its middle (the mean cloud fraction barely
changes, the 50 % isosurface stays in place; the ramp middle is c91.w), and `1 − far_detail_fade ·
LOD` of the erosion detail remains.

**Large-scale shadow from outside.** The key's shadow from the clouds spans one cloud cell; for the
sunlit side of the nebula to be bright and the far side darker, from outside the optical depth gets
the haze from the sample to the zone surface towards the key (the ray's exit from the ellipsoid,
analytically) × `exterior_shadow_density`, with a weight growing from 0 at the surface over
`exterior_shadow_fade_in` metres of distance to the entry. Inside the weight is 0 — the tuned look
does not change. The same two-lobe phase gives the silver lining at grazing angles.

**Exclusion zones from outside.** Cutting works the same way (up to the 8 zones nearest the
camera, now sorted by distance). Once per pixel the ray's span through the zones' bounding spheres
(radius — the largest semi-axis, c53..c60.w) and the index of the last zone hit are computed; the
zone loop runs only on the steps inside that span and only up to that zone. The result is the same
(outside the sphere the immersion is 0), and rays missing the zones do not pay for them. The zone
test is unrolled (zone 0 always, zone k when the ray hits more than k): `ps_3_0` has no relative
constant addressing in the pixel shader, and a loop would select every array element through a
`cmp` chain (~57 instructions per zone and step against ~15 now) and eat temporary registers.

**Asteroids.** Retail draws the field's cubes (`CliAsteroidDrawNearField`, FUN_00522a60) out to a
depth of `fill_dist × detail + 1.25 cubes` and fades the material alpha only over the last half
cube; at the seam the `[AsteroidBillboards]` fade in between `fill` and that depth (FUN_0054feb0).
The opaque retail fog hid the boundary; in a thin haze the cubes popped in. While a drawn nebula
intersects the field (bounding spheres), `NebulaVolume::AsteroidSpawnReach` gives a new depth: the
haze length down to `asteroid_spawn_transmittance` (the haze around the camera, with the thinning
of the nebula's current exclusion zone; half the `[Fog] near` clear radius) plus the camera's
distance to the half-density surface of the shell (the ellipsoid `1 − width/2`, no noise; 0 deeper
in), at most `asteroid_max_spawn_distance`; the field-nebula intersection test uses the sphere
widened to the outer edge of the halo. `CliAsteroidTickOne` then walks the cubes out to that depth
(the same code, a fill parameter), fades them over `asteroid_fade_fraction` of that depth, moves
the billboards' fade-in planes to the same band, temporarily raises the field's exclusion-zone
cut-off `MaxCliDist` to `(fill · 1.25)²` (otherwise the far cubes would be drawn inside exclusion
zones), and tests near_field with the same extended fill (its own copy of the formula; the common
field's `FillDist` is left alone — Common populates asteroids by it). When fully immersed the far
plane is no closer than 1.1 of that depth. Without an intersection or with `asteroid_spawn 0` —
retail byte for byte. Dynamic asteroids (`[DynamicAsteroids]`, placement radius ~150 m) are not
affected.

The fading cubes write depth even while translucent (retail turns depth writes off only for fields
with `max_alpha < 1`). The march then ends on the asteroid, and an almost transparent asteroid cut
its silhouette out of everything behind it (the haze to the zone exit, clouds, the tail): the
silhouette appeared in full the moment the cube entered the walk. While the nebula around the field
was dense (clouds with coverage 0.65 are opaque within ~1 km) this was invisible; the shell
(`shell_width 0.55`, `shell_cloud_falloff`) thinned the clouds and haze exactly where fields like
Gredos lie (Omicron Gamma: the field is at 0.7–0.8 of the nebula radius), and the boundary at 6 km
became visible. So `CliAsteroidTickOne` reports the fade band (`NebulaVolume::NoteAsteroidFade`:
the view depth where a cube's alpha reaches 0, the band width, the cube size), and for a pixel whose
scene depth lies in that band the ray march adds, after the march, the haze behind it to the zone
exit (closed form, like the tail) with the fraction `1 − Keep`, where `Keep` is the asteroid's
alpha at the pixel's depth (c102). The pixel's depth is the asteroid's surface, up to a cube from
the centre the alpha was computed for, so in the shader the fade ends a cube earlier (`Keep` ≤ the
alpha: no silhouette, the near ones in the band are only slightly more fogged), and a pixel up to a
cube past the end of the band still counts as asteroid. If such a pixel stands in front of another
nebula's zone entry, the march is empty but the haze behind it is added the same way.

**The frame.** `Draw(Camera, near, Far)` comes after `DrainMeshAndAsteroids` (the opaque scene is
done, its depth is in INTZ) and before the effects; it draws every frame nebula not drawn yet, far
to near, each in its own pass, and ends the frame. Pass 1: a fullscreen quad into a target of
`resolution_scale` of the back buffer (A16B16G16R16F if `bFloat16Target`, otherwise A8R8G8B8): rgb
— the light scattered towards the camera (HDR on FP16, may exceed 1), a — the transmittance. Pass 2:
the composite onto the back buffer with `ONE, SRCALPHA` blending (`scene * a + tonemap(rgb *
exposure)`; only the volume's light is tone mapped, the scene behind it is only attenuated;
`tonemap` 0 — clamp, 1 — Reinhard on luminance with `tonemap_white`, 2 — ACES fit). On an 8-bit
target (no FP16) the ray march tone maps itself and the composite passes the values through. A
depth-aware upsample: if the depths of the four neighbouring low-res texels differ from the pixel's
depth by less than `upsample_depth_threshold` (a fraction), bilinear, otherwise the best one by
depth is taken (no halos around ships). Everything is camera-relative: positions are subtracted in
double on the CPU (a system spans up to ±200 km). The ray runs from the zone entry (from inside —
from the camera) to min(zone exit, scene depth, entry + march limit); the sky (depth 1.0) has no
scene limit. Steps cluster towards the entry (`step_distribution`), samples are jittered by
interleaved gradient noise (`jitter`). The outside fade (c78.x < 1) scales the light and pulls the
transmittance towards 1. By default the march limit is the distance at which the haze alone
transmits `march_end_transmittance` (no less than `auto_march_fog_distances` × the largest
`fog_far` span of the exclusion zones, within 1..30 `[Fog] distance`). Beyond the limit, with
`haze_tail`, the (uniform) haze is integrated analytically to the zone exit or the scene, lit by the
mean shadow of the marched part: the distance and the sky fade into lit haze instead of being cut
off.

**The medium.** Both parts are multiplied by the zone profile (an ellipsoid in the zone's local
axes with rotation; a sphere; box, cylinder and ring are approximated by the inscribed ellipsoid)
and by the `[Fog] near` "clear radius" around the camera.

*Outer shell and halo* (c88..c91, `ComputeShellFrame` — shared by the constants and the CPU copy).
The density used to stop at the surface within `edge_softness` (8 % of the radius); from outside
that gave an opaque ellipse with a sharp edge: the optical depth of a tangent ray through the zone
is in the tens (clouds with `cloud_density 12` are opaque within ~150 m), and the translucent rim
took ~1 % of the radius. Now, in the normalised radius `Q = |local|`:

- the radius is displaced by low-frequency noise: `Qd = Q + shell_noise · (2a − 1)`, `a` being the
  a channel of the volume noise (Perlin 4 + 8 cells), sampled in the zone's unit space at frequency
  `1 / (4 · shell_noise_scale)` with an offset from the zone position (each nebula has its own
  silhouette); sampled only when `Q > 1 − width − amplitude` (deeper in, the displacement cannot
  reach the shell);
- a shell `max(shell_width, edge_softness)` wide: `Outer` grows from 0 on its inner side to 1 on
  the displaced surface; the density is `1 − Outer²` (the inner part nearly full, the outer part
  melting to 0) — shared by haze and clouds (`NebulaShellProfile`);
- clouds in the shell also thin out: the coverage threshold moves `Outer² · shell_cloud_falloff`
  of the way to 1 — near the surface separate puffs and wisps remain, beyond it there are no clouds;
- the halo is haze only, beyond the surface: `halo_density · ((1 + halo_extent − Qd) /
  halo_extent)²`, the maximum with the profile is taken (`NebulaHalo`);
- from outside the profile is multiplied by `1 + (exterior_shell_density − 1) · Outer · w`, where
  `w` is a smoothstep of the camera's position from the inner side of the shell (0) to the outer
  edge (1), computed on the CPU (c91.x): from inside the core the look does not change, flying
  through the shell nothing jumps, and from outside the rim is translucent (stars show through the
  outer layers).

The ray marches inside the ellipsoid of radius `1 + halo_extent + shell_noise` (`NebulaZoneSpan`
with the radius from c89.w); the same boundary is used for the nebula selection distance
(`exterior_max_distance`, the fade), the far bucket and the key star's reference point
(`FVolumeEntry::SurfaceDistance`, `SpanScale`). The haze tail beyond the march limit takes the
density as the mean of the profile (without noise) at one and two thirds of the remainder — a ray
through thin outer layers stays thin. The large-scale shadow from outside does not act in the halo
(the ellipsoid exit is undefined there). The shell width is ≥ `edge_softness`, so `shell_width 0,
shell_noise 0, halo_density 0` give back the old edge (the ramp is smoothed quadratically). The
price of the width: with 0.35 and noise 0.12 the look from inside changes only at `Q > 0.53` — but
that is the outer part of the volume, and near the zone edge it became sparser and thinner from
inside.

- *Haze* — uniform, extinction `-ln(haze_transmittance_at_fog_distance) / [Fog] distance` (0.5 by
  default — much thinner than the retail fog, which is opaque at that distance); in exclusion zones
  (up to the 8 nearest the camera) it thins down to the retail visibility
  (`distance / (fog_far − near)` × `exclusion_density_scale`).
- *Clouds* — extinction `cloud_density / [Fog] distance`. Shape: the base noise (channel r) after
  a domain warp (an rgb sample at half the base cell, amplitude `warp` × base cell) is cut by the
  coverage threshold — `coverage` is the fraction of space inside clouds; the threshold and the
  width of the soft edge (`cloud_softness` of the cloud volume is the ramp, the rest a solid core)
  come from a histogram of channel r computed when the noise is generated, so the values do not
  depend on the noise distribution. The edges are eroded by the detail noise (g/b, `erosion`;
  `wispiness` blends it with its inverse — from puffs to wisps) after Schneider (Horizon Zero
  Dawn): cores stay, thin parts tear. The detail sample is taken only inside a cloud. Clouds fade in
  over `[Clouds] near_fade_distance` × `cloud_near_fade_scale`, like the retail puffs (the camera
  does not sink blindly into a cloud), and vanish in exclusion zones.
- *Scales*: the base cell is `cloud_scale_m` or `cloud_scale_fog_distances` × `[Fog] distance`, no
  more than a quarter of the zone's smallest radius (Badlands: 2.5 km); the detail cell is
  `puff_radius × detail_scale` (Badlands: 400 m). All noise samples are taken in "noise space": the
  zone's up axis is squeezed `layer_stretch` times, flattening the clouds into layers/decks.

The noise is a tiling 64³ A8R8G8B8 volume texture generated on the CPU once at the first entry (the
time is logged): r — Perlin-Worley (4 cells per tile), g/b — Worley fBm (8/16 cells), a —
low-frequency Perlin for blending the puff colours. The base, detail and warp samples drift at
different speeds and in different directions (the tile offsets are the camera in noise space minus
the drift, computed on the CPU in double and wrapped into the tile).

**Lighting — scattering, not emission.** A sample's radiance is a mix of the two parts weighted by
their extinctions:

- clouds: `albedo (puff_colora/b by channel a × cloud_brightness) × (key × K × powder + ambient ×
  AO) + [Fog] color × emission`;
- haze: `albedo ([Fog] color hue at full brightness × haze_albedo) × (key × phase × shadow +
  ambient × AO) + [Fog] color × haze_emission`.

The key source (`key_light_source`): the system's star (the first in `StarSphereList`, colour —
the inner `star_glow` halfway to white, × `sun_burnthrough_intensity` × `key_light_intensity`) if
the nebula's `sun_burnthrough_intensity` > 0; otherwise a fixed key `key_light_dir` in the zone's
axes with the colour `key_light_colour` (0 — `puff_colora`, brightened) ×
`key_light_fixed_intensity`. The phase is a two-lobe Henyey–Greenstein (`phase_g` forward,
`phase_back_g` backward with weight `phase_back_weight`): a silver lining when looking at the
light. The shadow is the optical depth of the clouds' base shape (without erosion) along the ray to
the key: up to 6 segments growing 1.6× over `shadow_distance` (0 — one base cell), ×
`shadow_density`; the haze is not part of the shadow (light falls between clouds in shafts). `K`
approximates multiple scattering (Wrenninge): single `phase·e^(−τ)` plus two octaves with weight
`ms_strength^i`, extinction `τ·ms_extinction^i` and anisotropy `g·ms_phase^i` — thick clouds are
not black. The three octaves' phases are computed once per pixel (the angle to the key does not
change along the ray). `powder` (`powder_strength`) darkens thin edges when the light is behind. AO
is one sample of the base shape above the point along the zone's up axis (`ao_distance`, 0 — half
the layer height; `ao_strength`): dark cloud undersides and the haze below them. The step is
energy-conserving (`alpha = 1 − exp(−sigma·dt)`).

**Lightning.** Discharges inside cloud masses are point sources of the ray march (up to four per
nebula, c69..c76, count in c35.y): the cloud glows from inside (a bright core, light scattered in
the cloud and in the surrounding haze, silhouettes of neighbouring clouds), the flash flickers in
several pulses, sometimes in series, and nearby ships are lit from its side. Visible both from
inside and from outside. All of it is `NebulaVolume::BeginFrame` → `UpdateLightning` (after the
frame's nebulae are picked), with no memory allocation: `GStrikes[4]` holds the strikes of all
nebulae at once, the scheduler lives in the nebula record (`FRegisteredNebula`).

- *Schedule.* While the nebula is drawn and has `lightning_enabled`, the next strike comes after
  `gap × (0.8 .. 1.5)` (the way retail rolls its timers). The values come from the nebula's INI:
  `[Clouds] lightning_gap / lightning_duration / lightning_color / lightning_intensity` if gap and
  duration are set (retail flashed every puff on its own timer, so gap is divided by 4 —
  `kCloudLightningSources`), otherwise `[BackgroundLightning] gap / duration / intensity`,
  otherwise 8 s / 0.4 s. Colour: `lightning_colour`, otherwise `[Clouds] lightning_color`,
  `[DynamicLightning] color`, `[BackgroundLightning] color` — as a hue halfway to white (the retail
  colours are dim additive offsets), otherwise pale blue. `lightning_frequency_scale` divides the
  gap, `lightning_duration_scale` multiplies the duration. With probability
  `lightning_burst_chance` a strike is followed by 1–2 more nearby (after 0.5–1 of its duration).
  The strikes of a nebula that is no longer drawn go out at once; after a long break the schedule
  is re-armed. All random numbers come from an own xorshift: the retail `rand()` sequence does not
  change.
- *Envelope.* 2–4 pulses: the first one at once and the strongest (decay `0.10..0.22` of the
  duration), the others later within the duration, weaker and shorter, each an 8 ms rise and an
  exponential decay; the sum ≤ 1.25; late pulses are offset by `lightning_pulse_jitter` of the
  radius (another discharge channel — the lighting "jumps"). On top, a random dip of up to
  `0.6 × lightning_flicker` per frame (like the retail `rand·rand` flashes). A strike lives until the
  last pulse has decayed (5 of its time constants).
- *Placement.* `lightning_candidates` random points, the densest wins: the same base cloud shape as
  in the shader (warp + base + coverage threshold, no erosion), computed on the CPU from a copy of
  the noise volume (`GNoiseTexels`, trilinear with wrap, like the sampler) in the same coordinates
  (`FNoiseFrame` / `ComputeNoiseFrame` — shared with the constants c12..c17, drift included), with
  the raised coverage threshold in the shell and × the shell profile with the noise-displaced
  radius (`ShellProfileAt`, shared `FShellFrame`). No strikes in exclusion zones (and at their edge,
  |L| < 1.05). Camera inside: points at `lightning_min_distance .. lightning_max_distance` from it,
  the `lightning_view_bias` fraction in the field of view (slightly wider than the frame); with
  probability `lightning_far_chance` the strike is distant — up to `lightning_far_distance` (0 —
  the march limit): flicker in the haze instead of the retail background flash. Camera outside:
  points over the whole zone ellipsoid, the `lightning_view_bias` fraction is mirrored to the
  camera's side. A near strike needs `lightning_min_density`, otherwise the attempt is repeated
  after 0.25 s; a distant strike and a series strike only need to be inside the zone. With no free
  slot a new strike displaces the least important one (envelope × peak × closeness to the camera)
  if it is more important.
- *Shader* (`NebulaPointLight`). The source at a sample: `colour × peak × envelope × falloff ×
  phase × e^(−τ)`. The falloff is an inverse square with a soft core (`core² / (d² + core²)`,
  `lightning_core_size` of the radius), zeroed by the window `(1 − d²/R²)²` at the
  `lightning_radius` (0 — 1.5 cloud cells). The phase is Henyey–Greenstein with `lightning_phase_g`
  (nearly isotropic). A full shadow ray to the source is too expensive, so `τ` is an estimate:
  (haze + cloud averaged over the ends — the density at the sample and the base density at the
  strike point, c69.w) × the distance, with `lightning_shadow 2` with one base-shape sample in the
  middle (without it at the far LOD), × `lightning_shadow_density`; the attenuation is diffusive
  `1 / (1 + τ)`, not `e^(−τ)` (multiply scattered light passes through a dense cloud algebraically,
  as through a conservative slab).

  Why the lightning was barely visible (and what changed). A strike is placed at the densest point
  of a cloud, and the camera sees only the surface of the cloud mass — about one cell (~1–2 km)
  from the strike. With the old values ~1 % got there: an inverse square with a 0.2 R core at
  R = 0.75 cells (0.03 by falloff at 1 km) and `e^(−τ)` with `cloud_density 12` (another ×0.3). An
  addition of ~0.05 to a cloud brightness of ~0.8, and ACES already compresses in that range
  (0.8 → 0.75, 2.2 → 0.93) — the flash was invisible. Now: radius 1.5 cells, core 0.45 R, diffusive
  attenuation, strength `lightning_intensity_scale 20` (the mass surface at 1–1.5 km gets +0.7..3 of
  brightness, white at the strike), `lightning_haze_scale 4` (distant strikes light the haze around
  them: background flicker), `lightning_haze_flash 0.025` (it is multiplied by the increased
  strength). The light enters the sample's radiance with the cloud albedo and the haze albedo ×
  `lightning_haze_scale`, like the rest of the light (energy-conserving step). It runs only on the
  steps inside the ray's span through the sources' spheres (computed per pixel). The core of the
  strike itself is a Gaussian spot (`lightning_core_glow_size` of the radius,
  `lightning_core_emission`) integrated across the ray (by the distance of closest approach), added
  on the step whose segment contains the strike, with the transmittance up to it; strikes beyond
  the march limit are added after the loop with the final transmittance. Nothing depends on the
  inside/outside mode; LOD only drops the middle sample. In addition, each strike of a nebula adds
  `colour × envelope × lightning_haze_flash / (1 + (d / march limit)²)` to its ambient — a faint
  flash of the whole nebula.
- *Ships.* The strike that lights the camera's surroundings most (`envelope × R²/(d² + R²)`, fading
  out towards `lightning_ship_distance`, 0 — 3 radii, × `lightning_ship_intensity`) drives a
  directional light from the strike to the camera in its hue. If the camera is fully inside a drawn
  nebula (immersion ≥ 1, when retail ticks the light) that has `[DynamicLightning]` (GameLight
  +0x270, created when duration +0x278 > 0) and `lightning_lights_ships ≥ 1`, it is that nebula's
  retail light: `NebulaAmbientTick` (FUN_005097c0) then returns at once
  (`NebulaVolume::DrivesNebulaLight`), the random direction and random flash do not run. Otherwise,
  with `lightning_lights_ships 2`, the volume's own GameLight, built like the retail light (type 3,
  range 500000), switched on only for the duration of a strike. A released light is left off: the
  retail tick continues from dark. The own light holds two references (`GameLightReleaseAll` takes
  one off each enabled light when space is torn down), is switched off on leaving the system (the
  last `UnregisterNebula` after `GameLightLeaveSystem`) and destroyed in `Shutdown` (before the
  pipeline: `RemoveLight`). On RP8, with the volume or the lightning off, no light is touched —
  retail byte for byte.
- *Debugging.* `[Debug] lightning_force 1` — strikes one after another near the camera (no pauses,
  no distant ones, no series), `lightning_show_positions 1` — the cores are visible through
  everything (also between pulses).

**Debug views** (`[Debug] nebula_view`): 1 — cloud density (1 − the transmittance of the clouds
alone along the ray), 2 — the key's shadow transmittance averaged by visible contribution, both
covering the scene; 3 — haze only, 4 — clouds only (the other part's extinction is zeroed on the
CPU).

**How the nebula's INI values are used:**

| Value | Use |
|---|---|
| `[Fog] distance` (+0x298) | the medium's unit of length: haze and cloud extinctions, automatic cloud-mass scale, bounds of the automatic march limit |
| `[Fog] near` (+0x29c) | the clear radius around the camera (density smoothstep from 0); the start of the march limit |
| `[Fog] color` (+0x2a0) | the haze albedo hue; the haze's and clouds' own glow |
| `[NebulaLight] ambient` | the ambient light (× `ambient_scale`), dimmed by AO |
| `[NebulaLight] sun_burnthrough_intensity` (+0x2c4) | the key star's strength (× `key_light_intensity`); 0 — a fixed key instead of the star |
| `[Clouds] puff_radius` (+0xa8) | the erosion detail cell = `puff_radius × detail_scale`; the powder length |
| `[Clouds] puff_colora` / `puff_colorb` (+0x78 / +0x84) | the cloud albedo, blended by the noise's channel a (× `cloud_brightness`); `puff_colora` is the default fixed-key colour |
| `[Clouds] puff_drift` (+0xb0) | drift speed `puff_drift × drift_scale` m/s (base, detail and warp in different directions and at different speeds) |
| `[Clouds] near_fade_distance` (+0xe4 / +0xe8) | the cloud fade-in range from the camera (× `cloud_near_fade_scale`), as retail fades the puffs in |
| `[Exclusion Zones] exclusion` + `fog_far` | inside an exclusion zone the haze thins down to retail visibility, no clouds; the largest `fog_far` lengthens the automatic march limit |
| the system's star (the first in `StarSphereList`) | the key's direction and colour (the inner `star_glow` colour, halfway to white) |
| `[Clouds] lightning_gap` / `lightning_duration` (+0x9c / +0xa0) | schedule and duration of lightning strikes (gap / 4) |
| `[Clouds] lightning_color` / `lightning_intensity` (+0x90 / +0xdc) | the strikes' hue and peak strength (× `lightning_intensity_scale`) |
| `[BackgroundLightning] gap` / `duration` / `color` / `intensity` (+0x250 / +0x254 / +0x25c / +0x268) | the same, when `[Clouds]` has no lightning |
| `[DynamicLightning] color` (+0x280), light +0x270 | the strikes' hue (after `[Clouds]`); the light the strikes use to light ships from inside |

Only the nebula's first `[Clouds]` block is used; `puff_max_alpha` is no longer used.

**Settings.** `[Nebula]` holds the global values, `[NebulaOverride]` one section per nebula:
`file = <the nebula ini's name without directory and extension>` (for example
`li01_badlands_nebula`), then any `[Nebula]` keys; keys not given come from `[Nebula]` regardless of
section order. `NebulaVolume::RegisterNebula` remembers the name when the system's `[Nebula]` is
loaded (`star_sys.cpp`), `UnregisterNebula` is called in `NebulaDestroy`. All keys are floats
(`key_light_dir` / `key_light_colour` / `lightning_colour` — three floats), described in the ini
itself; `[Debug] nebula_view`, `lightning_force`, `lightning_show_positions` are global and do not
take part in `[NebulaOverride]`. A hot reload of the ini applies them from the next frame (changing
`resolution_scale` recreates the target).

**Instruction budget.** `PSRaymarch` under `fxc /T ps_3_0` (the same compiler generation as
`D3DXCompileShader` in RP9) is 1327 slots (24 texture) with lightning (`NEBULA_POINT_LIGHTS 1`;
937 without); `PSComposite` is 179. `kRaymarchPsSlotsRequired` = 1660 (measured + ~25 %): below
that `MaxPixelShaderSlots` the volume does not turn on (one `WARNING` line). The owner's card has a
limit of 4096, 512 is only the SM3 minimum; the compiler does not check the limit.

Temporary registers are the bottleneck: the shader uses all 32 `ps_3_0` registers (`r0..r31`), and
any change may produce `X4505 maximum temp register index exceeded`. The compiler hoists everything
that does not depend on the step out of the march loop and keeps each such value in a register; so
the CPU computes the invariants (reciprocals in c19.w, c22.w, c37..c44.w, `scale − 1` in
c45..c52.w, the puff colour difference c87, the squared distance to a source c73..c76.w, the
lightning phase coefficients c84.z / c86.zw, `ms_extinction²` in c28.w, the coverage ramp middle
c91.w, the key direction in zone axes c92), debug views 1–2 accumulate in `Light`, and the source
code derives everything from the current step's "towards the source" vector (not from per-ray
constants). In `NebulaMedium` only the displaced radius lives across the exclusion-zone test: the
shell profile is computed after it, the early exit is on `Qd ≥ halo end` (otherwise X4505). Arrays
are not indexed in loops (the compiler would build `cmp` chains): the exclusion zones and the
sources are unrolled. The shadow loops and the march loop are dynamic (`[fastopt]` on the march is
mandatory: without it the compiler never finishes).

Executed instructions per the fxc listing: a step in a shell cloud (with the displacement sample)
with detail, full shadow, large-scale shadow and the source-span test ≈ 295, each exclusion zone on
a step ≈ 15, each source whose sphere contains the step ≈ 65 (with the middle sample and the core
test) plus ≈ 15 per block; pixel setup ≈ 540 (with 8 zones in the span test and the planet
spheres), after the loop ≈ 240 (cores, tail, haze behind a fading asteroid, star glows; these
changes did not touch the march loop). The shader limits a pixel's step count itself: `steps ≤
(limit − 1000) / (300 + 80 · sources + 16 · zones on the ray)` (c79; the nebula's source count in
c79.x on the CPU), the limit being `MaxPixelShaderInstructionsExecuted` from the caps. The worst
cases at 65535: from inside, 4 sources and 8 zones on the ray — 86 steps instead of 96 (≈ 64 k);
without sources and with 8 zones there are steps for all 96 (≈ 39 k); far outside (LOD 0.5,
3 shadow samples, 4 sources) — 48 steps ≈ 27 k; two nebulae — two passes, the limit applies to each
separately. Texture samples per step: the shell displacement (only in the zone's outer part), warp,
base, detail (only in a cloud), 6 or 3 shadow, AO and one per nearby source — up to 15.

**Resources.** The programs are created once (the handles live until `Shutdown`, a shader reload
rebuilds them behind the same handles); the noise is MANAGED and survives `Reset`; the target is
DEFAULT pool, RP9 recreates it behind the same handle (while it is missing `GetExTextureSize` fails
and the frame stays retail). Failures are not retried every frame: programs that failed to compile
wait for a shader reload, a failed target for an ini reload, the noise for a restart.
`RenderEx::Shutdown` calls `NebulaVolume::Shutdown`, which destroys everything through
`IRenderPipelineEx`. The frame allocates no memory: the constants are static arrays.

**Known limitations.**

- Everything `SpaceObjDrawPass` draws before `Draw` without writing depth, apart from star glows
  and planet spheres (see "Stars and planets"), is fogged by the volume by the depth *behind* it:
  exclusion shells, retail billboards and fill sheets in the fade band, the transparent parts of
  asteroid fields (apart from the fade band of the extended walk).
- A planet is a bounding sphere (`GetInstanceExtent`): a non-spherical one, or one with a
  translucent atmosphere, has no nebula in the rim beyond the sphere; rings (`FZItemPlanetRing`)
  are not taken into account. At most 4 planets and 3 stars per frame. At the edge of a planet
  without depth the composite filters bilinearly (a one-half-res-pixel rim).
- Star glow: the weight follows the profile, not the glow's real share of the pixel — in the disc
  centre the sky behind the star is attenuated as up to the star (hidden by the bright glow), at
  the edge the glow is attenuated as the whole ray. For a star inside the zone the transmittance up
  to it is estimated with the extinction spread evenly over the marched part (clouds in between are
  not taken into account exactly).
- The asteroid fade band is decided by the pixel's depth, not by the object: a ship or a station at
  that view depth (up to a cube past its end) inside the field also gets the haze behind it with the
  fraction `1 − Keep` (almost hidden at the end of the band, visible again beyond it). The haze
  behind an asteroid is a closed form without clouds or exclusion zones.
- With `haze_tail` the sky deep inside a large nebula is fully covered by haze (tens of kilometres
  to the zone exit): stars are visible only near the zone edge or with a thin haze.
- Effects after the volume are not attenuated by it; only the retail black effect fog attenuates
  them.
- Lightning: the attenuation between a strike and a sample is an estimate (no shadow ray), so a
  cloud between them that is not at the ends or the middle does not block the light; the source
  also shines through exclusion zones. At most four strikes for all nebulae at once. One radius and
  shape per nebula. Ships are lit by one directional light from the strongest strike (not a point
  light: distant ships are lit like near ones). A nebula's strike lights only its own volume (in a
  zone overlap — not the neighbour's). The retail puff flashes (`[Clouds]`) and `[Lightning]` (the
  lightning after the fog quad) are retail.
- At most 4 nebulae per frame, each its own pass (a fullscreen half-res march with early exit and a
  fullscreen composite). Overlapping zones add up without mutual attenuation inside the overlap.
- In the fade band (`exterior_fade_distance`) both the volume and the retail exterior are drawn; at
  its inner boundary the retail billboards and fill sheets vanish at once (their alpha is left
  alone). Billboards reaching far outside the zone (`bit_radius` up to 15 km) then disappear outside
  the volume too.
- The controller from outside and nebulae closer than the scene's far plane are drawn over the
  opaque scene; distant bucket-2 planets in front of them cut the ray with their sphere, but other
  distant bucket-2 solars (stations beyond `G_SpaceDrawRange`) have no depth and are painted over.
- Switching the shadow ray to 3 samples (`lod_shadow_switch`) is a boundary by distance to the
  entry; a faint lighting seam on a distant nebula is possible (2 — off).
- From inside a fully immersed nebula the other picked ones are still marched (retail does not draw
  them): they are hidden by the haze but cost time.
- The extended asteroid depth grows the walk volume with the cube of the distance (CPU: the cube
  walk, immersion, exclusions, a draw call per cube) — `asteroid_max_spawn_distance` caps it.
- Box/cylinder/ring as an ellipsoid. The shadow ray and AO see only the clouds' base shape (no
  erosion, no shell — neither the profile nor the raised threshold — and no exclusion zones): in the
  shell and near exclusion zones a shadow from clouds that are not there is possible (more visible
  in the shell with a large `shell_cloud_falloff`). The haze tail beyond the march limit does not
  see exclusion zones or the shell noise (the profile at two points). The shell is displaced in the
  zone's unit space: an elongated ellipsoid has its lobes elongated the same way. The shell noise
  does not move (no drift).
- The `exterior_shell_density` factor depends on the camera's position: the same point of the shell
  is thinner from outside than from inside (smoothly, without a jump).
- The noise tile repeats (base — 4 cells, Badlands: 10 km; detail — 3.2 km).
- The first entry generates the noise on the CPU (a one-off hitch, the time is logged).
- Hot reload is polled only in the space frame.
- Bilinear filtering of the FP16 target is assumed (present on any D3D10-class GPU).


### Optional volume alongside ring puffs

An RP9 build accepts an optional section in a planet-ring INI:

```ini
[Volumetric]
file = ..\DATA_EXTRA\VOLUMETRIC\li_cal_light_cloud_volume.ini
```

The file uses the nebula INI format (`[Fog]`, `[NebulaLight]`, optionally
`[Clouds]`). Its volume shares the ring zone, uses its inscribed ellipsoid,
and currently requires a solid RING (`size = outer_radius, 0, thickness`).
Hollow rings are rejected instead of filling their hole. Existing ring puffs
and meshes are still rendered independently. The companion does not enter
the retail nebula/controller list: it sets no object fog, background colour,
or fog far plane. The ring owns and destroys its companion on Clear/reload.

Tune it with `[NebulaOverride] file = li_cal_light_cloud_volume` in
`DATA_EXTRA/VOLUMETRIC/volumetric.ini`. This settings file hot-reloads in space;
adding/changing the ring's `[Volumetric]` reference requires reloading the system.
The supplied profile concentrates the volume within an 18 km march cap, with
6.5 km cloud masses and 2.4 km puff-texture tiles. A zero-count `[Clouds]` block
provides `crow_exterior1`, the original blue puff colours and drift without
spawning additional billboards. `puff_texture_density`, `puff_texture_colour`
and `puff_texture_scale` control the texture contribution. Its projection uses
a wrapped camera-position/drift offset (c105), so it stays in world space and
moves with the detail flow instead of following the camera. Lower key-light
intensity and forward scattering reduce the glare toward the sun. Inspect this
initial tuning profile in game.

Global `[Nebula] enabled = 0` suppresses all volumes, including overrides;
the original ring puffs continue. With `FreelancerRp9=0` or RP8 the extra section
is ignored and the original ring path is retained. No UI quality selector is added.


### Asset-family cloud styles

`[NebulaStyle] name = crow` supplies the crow cloud look independently of the
global defaults. The same mechanism recognises `edge` and `walker`; no presets
for those families are supplied yet. The client detects a family once when
registering a nebula, from `[Clouds] puff_shape` (`crow_`, `edge_`, `walker_`),
falling back to the `[TexturePanels] file` base name. Generated nebula INIs do
not need edits. Ring companions are classified by their own source INI too.

Settings are resolved as global `[Nebula]`, then the matching `[NebulaStyle]`,
then the explicitly listed keys of a `[NebulaOverride]`. An override may choose
`style = crow` explicitly. Section and key order do not affect inheritance;
styles hot-reload with the rest of volumetric.ini. The global enabled switch
still disables all volumes. RP8 and builds without RP9 retain the retail path.

`cloud_billow` (0..1, default 0) adds smaller rounded cellular lobes to the
large cloud base using the noise volume's existing green channel. The CPU
lightning-placement estimate, shadow probes and visible density use the same
base shape; there is no extra texture fetch. Coverage remains approximate
because the coverage histogram describes the original red-channel noise.
Crow combines these lobes with round layers, weak edge erosion, dense cloud
cores and subdued ambient/emissive light. Puff texture modulation is secondary.
The li_cal ring inherits the style but uses larger, more transparent clouds
than actual crow nebula zones. Visual matching to the supplied Lonestar frames
requires in-game inspection; a still frame does not specify the animation speed.


Crow tuning revision: lower coverage/extinction and a wider, thinner outer shell
restore a more open exterior. Ambient illumination is raised while lightning
is disabled, including the retail random ship-light flash while the volume is
available. The ring's own puff lightning is disabled in its game-data INI.

`cloud_near_fade_start/end` override the local cloud fade distances in metres;
when set, the shader uses smoothstep instead of the original linear fade.
Crow ramps over 0.5..4 km (ring: 0.9..4.5 km), to surround the ship progressively.
`object_ambient_strength/scale` tint lit objects using the containing nebula's
own `[NebulaLight] ambient`, with a smooth inward ramp over
`ambient_blend_distance` metres. A smaller nebula takes precedence over a
system-wide ring companion. Defaults leave the original ambient code intact.

`dynamic_asteroid_fade_fraction` widens the fade band as a fraction of the
recycling sphere's radius; `dynamic_asteroid_fade_seconds` limits fade-in speed
from each fresh placement. Crow uses a 70% distance band and a four-second
fade-in; fade-out follows the smooth spatial curve to zero before recycling.
Collision, damage, asteroid count and spawn radius are unchanged. The cube
asteroids' existing distance fade is widened separately to 65%.


Crow background/distance revision: `background_scale` dims only the sky in a
single pass before planets, asteroid meshes, ships and HUD. Overlapping volumes
use the darkest requested scale once. The sky multiplier blends by zone immersion.
`max_march_distance` is 45 km for crow nebulae and 30 km for the system-wide ring;
`cloud_distance_fade` softens the last 12/10 km of those ranges. It fades relative
to the march cap, never to an object's scene-depth endpoint. Exterior volumes
fade over 30 km before the 90 km selection limit. These remain artistic limits,
not an increase in ship or asteroid spawn counts.

Crow now uses `replace_object_fog = 0` to preserve the original per-object fog
and the mod's field/nebula placement, alongside the volumetric clouds. Lighting
entries remain valid through the late ship/effect passes, with invalidation on
nebula destruction, so the player receives the same ambient tint as other lit
objects. `use_sun_burnthrough = 1` also uses `[NebulaLight]
sun_burnthrough_intensity` for directional object lighting: the per-object GPU
light colour is attenuated while the shared CPU light descriptor is restored.
The upload is reset on leaving the volume and bookkeeping is removed with the
light. The benchmark's ring companion uses intensity 0.5; the five ordinary
li_cal nebula INIs already use 0.5. RP8 and disabled features retain their paths.

The FL_MOD benchmark asteroid field INIs also require `[Field]
contains_fog_zone = 1`: spatial overlap alone does not enable the retail asteroid
ambient/fog pass. This is enabled for li_cal_ast1/2/3 and li_cal_pocket1 with
backups; their zones, exclusions, counts and placement stay intact.

The ordinary sun billboard also uses this intensity when a ring volume supplies
the lighting. Inside a volumetric controller it yields to the controller's
burn-through draw, avoiding a full-bright sprite plus a second burn-through
sprite now that the old opaque fog overlay no longer covers the first one.


### Crow hybrid: exterior, nearby volume, interior detail sprites

The latest benchmark tuning separates the system ring from real nebulae. The
ring uses density_scale 0.12, cloud_density 1 and coverage 0.2; its original
ring puffs remain independent, at puff_max_alpha 0.22. It is a thin system haze.

For ordinary crow nebulae, `exterior_radius_fraction = 0.1` limits volume
selection to a small margin around each zone instead of a system-wide 90 km
radius. It uses 10% of the smallest zone radius, capped by
exterior_max_distance. With halo_extent 0.02 and shell_noise 0.03 the drawn
bound is about 1.05 zone radii; the selection margin is slightly wider again.
Across that margin a smoothstep raises the ray-marched volume from zero and
complementarily lowers the original exterior bits and fill-sheet alpha.
Outside it the original exterior alone remains. The volume marches at most
10 km, fading cloud density over its last 4 km; it does not depict a distant
dense interior. Actual zone size/orientation and exclusion masks remain.

`hybrid_clouds = 1` moves the existing interior puff sprites into a separate
pass after the volume composite, before other effects. Original puff counts,
positions, shapes, drift, immersion fade and exclusions are preserved.
`hybrid_puff_alpha = 0.22` adds restrained local detail; RP9 soft intersections,
individual camera-facing quads and the particle sorting/fade settings provide
the spatial detail. Puff lightning flashes stay suppressed during this pass.
These are 2D textured quads distributed in 3D, not a new volumetric-impostor
system or per-pixel shaded 3D meshes. Ray marching supplies the mass and
self-shadowing; the sprites supply nearby texture and parallax. Families
without hybrid_clouds retain their old drawing order and switch behaviour.

### Crow atmospheric fog and system backdrop tuning

Crow now uses `replace_object_fog = 1`: the existing depth-integrated volume
replaces the retail linear object fog, which otherwise turns distant solars
and static asteroids into opaque fog-coloured silhouettes behind fading
dynamic asteroids. Haze transmittance is 0.8 per source `[Fog]` distance before
the 0.85 density multiplier (about 0.827 afterwards, before cloud extinction).
The ray marcher supplies exponential extinction, directional scattering and
cloud shadows. Ambient tint, cloud shapes, the hybrid puff pass and the
near-boundary entry crossfade remain. This reduces the silhouette contrast;
it does not implement order-independent transparency for dynamic asteroids.

The li_cal ring companion explicitly retains very thin haze (0.995), uses
`background_scale = 1` to preserve the original sky brightness, and extends
its sparse volume to 60 km, fading clouds over the last 45 km. Cloud masses
are 14 km across with puff-texture detail and a 2--12 km near ramp, so the
system backdrop continues into spatial clouds rather than a dark flat veil.
Density 0.16, coverage 0.2 and brighter volume lighting keep this layer
subtle; the companion's sun burn-through remains 0.5. Ordinary crow nebulae
keep their 10 km march cap and 10% near-boundary selection margin. Runtime
global settings are preserved when installing the two profile sections.

### Bounded backdrop, distant fog transition and solar edge halo

The follow-up benchmark gives the companion `backdrop_radius = 115000`:
`RenderZoneScale` scales its rendering ellipsoid (preserving axis proportions),
outside selection distance and inside classification consistently, leaving the
600 km gameplay ring and its lighting zones intact. `backdrop_falloff = 0.35`
sets its soft outer shell; existing shell noise supplies an irregular edge.
The system volume starts fading in over 35--65 km along the camera ray,
marches at most 180 km and fades over its last 80 km. Its 14 km cloud masses,
coverage 0.42 and density 0.32 make the distant shape more readable while
haze transmittance 0.9999 and background_scale 1 preserve the sky and sun.
Only profiles opting into backdrop_radius use the separate rendering extent.

Local crow restores strong atmospheric fog with haze transmittance 0.18,
but `fog_ramp_start = 500` and `fog_ramp_distance = 5000` grow its density
using smoothstep inside the ray integral. This replaces the instant opaque
linear ramp without removing the distance fog. Isolated haze retains about
94%, 31% and 5% of surface contrast at 2, 5 and 8 km respectively, before
cloud extinction and exclusion zones. Cloud entry/crossfade is unchanged.
`c106.xy` carries this ramp; zero ramp distance preserves earlier profiles.

`sun_occlusion_halo = 0.18` enables an inexpensive, artistic partial-eclipse
halo. Nine physics rays sample the actual centre sprite's disc, excluding
the sun itself, shields and the cockpit player's hull. A modest expanded
glow is strongest at partial visibility and absent at full visibility or
full blockage. It draws with the sun so later opaque geometry still covers
the blocked side. This is a diffraction/bloom approximation, not physical
refraction or a screen-space light-shaft algorithm. No halo rays run when
the setting is zero, the volume is disabled or RP9 is unavailable.

The dynamic asteroid temporal fade now depends on distance: at the near
end it takes 0.12 seconds; at the recycling edge it approaches the configured
4 seconds. Crow's spatial fade occupies the outer 40% of the radius, leaving
the inner 60% opaque. Counts, placement and collisions remain untouched.

`port.ini [Render] solar_draw_distance = 50000` is the RP9 equivalent of
patching the spatial render query at original file offset 0x213ec8
(DAT_00613ec8). The inspected FL_ND/FL_ND/EXE/Freelancer.exe holds 10000
there. Mesh LOD ranges, the camera far clip and the spatial query capacity
remain separate limits; this does not globally rescale mesh LODs.
The benchmark Trade_Lane_Ring already specifies LODranges 0,100000.

Generator persistence: FL_MOD/Assets/Pythonlancer/universe/systems/li_cal.py
now sets FIELD/ FIELD_TEMPLATE on CalAsteroidDefinition1 and adds
contains_fog_zone to the CalGasPockets field template. The actual generator
was checked to emit the flag for both definitions without regenerating the
whole system. The generated gen_ nebula INIs have not been edited; the new
render settings live in the separate DATA_EXTRA profile.

Related references: GPU Gems 2, [Accurate Atmospheric Scattering](https://developer.nvidia.com/gpugems/gpugems2/part-ii-shading-lighting-and-shadows/chapter-16-accurate-atmospheric-scattering),
and GPU Gems 3, [Volumetric Light Scattering as a Post-Process](https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process).
These explain distance scattering and occlusion-driven light effects;
the benchmark keeps its existing volume integrator and the simpler solar halo above.

### Hollow outer shield and transparent gas mines

The current system backdrop is a hollow ellipsoidal shell rather than a solid
cloud body. `backdrop_inner_radius = 80000` and `backdrop_inner_fade = 12000`
describe its clear inner cavity and smooth inner density ramp along the long
axis; `backdrop_radius = 115000` and `backdrop_falloff = 0.18` bound the outer
edge. Axis proportions still follow the source ring, so vertical radii are
half these distances. Shell noise gently displaces the edge. `c106.zw` carries
the inner radius and inverse fade in normalized volume space. The mask
multiplies both cloud and haze density; ordinary nebulae default to no cavity.
The companion keeps haze_tail disabled. Near fading is now 0--800 metres:
the shell's world-space geometry, rather than a camera-following distance
band, places the background behind the system. The original llight cloud
puff INI, textures and independent draw path remain unchanged.

California's explosive clouds are static `mine_oxygen` asteroid mines using
mine_gas.3db / ast_gas_mine.mat in li_cal_pocket1. Their field max_alpha is
0.3, so the existing cube renderer disables depth writes. Previously they
drew before the volume, which saw the distant background depth and integrated
the entire cloud bank over them. RP9 now queues inherently transparent cube
fields while the volume is active and flushes them after the volume and its
detail puffs. Each field restores its own ambient, fog and material, retains
the depth test, and uses the source fill_dist instead of the opaque asteroid
spawn extension. The queue clears on frame start and before flush, and falls
back to immediate drawing if its 64 field slots are full. Dynamic asteroids,
mine physics, textures, source alpha and explosion activation are unchanged.
RP8 and disabled volume paths keep their existing draw order.

The next backdrop preset doubles the long-axis shell thickness from 35 km
to 70 km by preserving the 80 km cavity and moving the outer edge to 150 km.
Inner fade is 24 km; the outer fade is 0.276 of the radius (41.4 km), so both
transitions scale with the thicker body. Cloud cells are now 50 km across,
compressed along the system up axis by layer_stretch 3.5 into broad sheets.
Coverage 0.62, softness 0.7, erosion 0.12 and no billow connect the separate
cloudlets; weaker puff modulation and a 48 km puff-texture tile retain texture
without breaking the banks into many small blobs. Density 0.2 compensates
for the longer path. The world-space shell controls the finite far edge;
cloud_distance_fade is zero and the 320 km march cap covers the full body.
Only the ring override changes; local crow, generated INIs and original
llight cloud puffs keep their settings.

Solar visibility, equipment cone sources, external light_anim and the proposed
surface shader/local-shadow architecture are documented in
[local_surface_lighting.md](local_surface_lighting.md). The material and shadow
parts of that document are proposals; the solar/equipment fixes are implemented.

### Planet atmosphere

Port-only. `FMaterial::SubmitAtmosphereLock` (Shading) queries `IRPPlanetAtmosphere`
(`render/IRPPlanetAtmosphere.h`, IID `RP9_IRPPlanetAtmosphere_v1`) and wraps the shell draw in
`SetPlanetAtmosphere(&Desc)` / `SetPlanetAtmosphere(nullptr)`. The Desc carries the material name,
the object-space radius of the shell mesh (length of a vertex position), the material Scale, the
diffuse tint and Alpha. The five indexed/unindexed draw entry points of RP9.cpp call
`ExAtmosphereBegin` before `ExSoftBegin`/`ExSurfaceBegin`; when it qualifies (requested, XYZ
vertices, not in a shadow pass, Ex pass, soft or surface draw) the draw runs with
`DATA_EXTRA/SHADERS/planet_atmosphere.hlsl` (soft artistic model, one shell side per pixel) and `ExAtmosphereEnd` restores shaders and the six render states from the pending cache.
Materials whose name contains an `atmosphere_exclude` substring (default `sw_center`, `bh_`,
`blackhole`) keep the retail fixed-function draw, as does a shader that failed to compile.

The look: beyond the limb a glow that fades with height (exp(-h * falloff) * (1-h)^2, h = 0 at
the limb, 1 at the outer radius); over the disc a haze lerp(haze, 1, (1 - N.V)^rim) that meets the
glow at the limb and veils the surface (alpha veil * amount); both lit by a wrapped diffuse
(soft terminator), tinted warm where the sun is low and brightened by forward scattering when
looking past the planet towards the sun. A physical single-scattering model (O'Neil, GPU Gems 2)
was tried first and rejected: it gives a thin hard ring and almost no haze over the disc.

Constants (view space): VS c0..c3 world*view, c4..c7 projection, c8 (planet centre, outer radius *
1.03). PS c0 (centre, surface radius), c1 (outer, 1/(outer-surface)), c2 (sun direction,
brightness * density), c3 (tint with its brightest channel 1), c4 (haze, rim, falloff, wrap), c5
(sun colour, 1), c6 (forward, warmth, veil). Surface = MeshRadius * world scale / Scale, outer =
surface * (1 + thickness). The sun is the brightest surface light (`ExCollectSurfaceLights`), or
the direction to the camera when there is none; density is Alpha/0.6 clamped to 0.5..1.5.

port.ini `[Render]`: `planet_atmosphere` (1), `atmosphere_thickness` (0.06), `atmosphere_brightness`
(0.9), `atmosphere_haze` (0.12), `atmosphere_rim` (2.5), `atmosphere_falloff` (3),
`atmosphere_wrap` (0.3), `atmosphere_forward` (1.5), `atmosphere_warmth` (0.5), `atmosphere_veil`
(0.5), `atmosphere_exclude`.

The atmosphere pixel shader writes its own depth: the analytic surface point under the haze, or the closest approach to the planet for the limb glow (c7/c8 carry the projection z and w columns). Each pixel shades one side of the shell: the near side from outside the drawn (inflated) shell, the far side from inside it, so close to the surface the far side, hidden behind the planet by its own polygons, still passes the depth test.

### Planet surface

Port-only. For `DetailMapMaterial` (mode 3: the one-pass BindDetailMap/SubmitKernel family, `Dt * 2Dm`
everywhere; gas giants, deserts, ice, crater moons), `DetailMap2Dm1Msk2PassMaterial` (mode 0), `Masked2DetailMapMaterial` (mode 1) and
`IllumDetailMapMaterial` (mode 2) instances named `planet_*`, with both retail passes available
(`DetailPassCount == 2`, stage 1 verified), `FMaterial::SubmitPlanetSurface` (Shading) queries
`IRPPlanetSurface` (`render/IRPPlanetSurface.h`, IID `RP9_IRPPlanetSurface_v1`) and asks RP9 to
draw the material once. RP9 compiles `DATA_EXTRA/SHADERS/planet_surface.hlsl` inside
`SetPlanetSurface`, so a successful Set means the draw is RP9's; a refusal (disabled, excluded,
shader failure) keeps the retail two-pass draw. Shading applies the first retail pass's states,
binds the base map (Dt) to stage 0, detail map 0 to stage 1 and detail map 1 to stage 2, and
draws once with alpha test off.

The shader reproduces the retail combines: mode 0 `Dt * lerp(2*Dm, 1, Dt.a)`; mode 1
`lerp(Dt * 2*Dm0, Dt * 2*Dm1, Dt.a)` (alpha is the land/ocean mask, white = ocean); mode 2 the
lit `Dt * 2*Dm0` with the unlit `Dt * 2*Dm1` glow blended over by `Dt.a * Dm1.a`. Lighting is the
fixed-function sum per pixel for the brightest light (`ExPickSun`, shared with the atmosphere)
plus material ambient/emissive, then fixed-function-equivalent fog. Additions:

- layers: layer 0 is detail map 0 (black mask), layer 1 detail map 1 (white mask, Masked2 only).
  RP9 classifies each by its detail map name: `ocean` water (DetailMapMaterial only on `wat*`
  planets; desert uses it for sand), `rock`/`crater` strongest relief and highest elevation,
  `ice`, ground (default), `grass`, `city`, `cloud` nearly flat; `gas*` planets get none. The mask's
  white is not always ocean (`desorgrck`: ocean under black, rock under white).
- relief: height = base luminance + the layers' elevation through the mask (so rock stands
  above sand even where it is painted dark); a 4-tap gradient spaced by the pixel footprint and a
  screen-derivative cotangent frame perturb the normal on the day side (not on wet water, less
  under clouds). Detail relief adds the layer's detail map as fine screen-derivative bumps, a
  fraction of a tile high, faded out once the detail is smaller than a pixel.
- terrain shadows: four steps along the height field towards the sun; ridges shadow what lies
  behind them, longest near the terminator.
- glint: GGX highlight with Schlick fresnel on water layers where the colour is water-like
  (blue exceeds red); clouds (bright, low-chroma texels) suppress it.

Pixel constants: c0 sun dir + wrap, c1 sun colour * material diffuse, c2 ambient, c3 mode / water
kind / tile rates, c4 glint strength / roughness / F0 / cloud threshold, c5 relief / detail
relief / base texel size, c6 glow strength / night-only (1, 0: retail) / terrain shadows, c7-c8
fog, c9 layer water/relief (layer 0, layer 1), c10 layer elevations / luminance weight. Samplers 0-2 get linear or
anisotropic filtering for the draw and are restored afterwards.

port.ini `[Render]`: `planet_surface` (1), `planet_relief` (6), `planet_glint` (10),
`planet_glint_roughness` (0.13), `planet_glint_fresnel` (0.02), `planet_cloud_threshold` (0.45),
`planet_terminator_wrap` (0.05), `planet_detail_relief` (1), `planet_terrain_shadows` (8),
`planet_surface_exclude` (`sw_center,bh_,blackhole,neutron`).

Gas giants (`planet_gas*`, sides and caps) animate within each part: the parts are separate
textures, so the deformation is computed in longitude/latitude (object space, y the pole), mapped
to the part's uv through the screen-derivative Jacobian of uv against longitude/latitude, and faded
out towards the part's uv edges, so the seams stay exactly as painted. The flow is zonal jets (each
latitude its own speed and sign), eddies from the curl of a 3D noise stream function
(divergence-free, after Bridson et al., "Curl-noise for procedural fluid flow") and three storm
vortices (a great spot and two small ovals from a hash of the planet's name), as a two-phase flow
map (each phase displaces by velocity times its age and restarts while the other is shown).
`gas_swirl_planets` (default `gasyelcld`) names chaotic giants: no jets, larger eddies churning in
place. Also limb darkening and a wider terminator. (A whole-planet cube map captured from the parts
was tried and dropped: faces sharing a material were not all captured, leaving seams.)
c11 time / jet speed (rad/s) / eddy speed / -, c12-c14 storms (longitude, latitude, radius, spin),
c15 planet centre (view) + seam band, c16 eddy frequency / - / animated / flow period.

Glow, ice, airless: an IllumDetailMapMaterial glow layer named city/glow lights up at night
(`planet_city_lights` 0.6: the day side keeps 40%), one named lava is half as bright by day and
pulses (`planet_lava_pulse`); ice layers get a soft GGX sheen (`planet_ice_sheen` 0.6, roughness
0.35, F0 0.04); moon*, mercury*, crater* families and crater detail maps are lit with
Lommel-Seeliger (brightness ~ cos(i)/(cos(i)+cos(e)): a flat disc to the limb and a sharp
terminator; `planet_airless`). c6.w lava pulse, c17 airless / ice sheen / layer 0 ice / layer 1 ice.

Seams: the normal is the analytic sphere normal (no facets, no lighting step between side and
cap meshes); base samples stay half a texel inside 0..1 (no wrap bleeding); within the seam band
of a uv edge the colour fades to a blurred mip and relief/terrain shadows fade out, so two
mismatched textures meet as a soft gradient. port.ini: `planet_seam_blend` (0.01), `gas_flow`,
`gas_turbulence`, `gas_storms` (1 each), `gas_swirl_planets`.
