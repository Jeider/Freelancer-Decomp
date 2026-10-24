// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// RP9 Ex: the port-only Direct3D 9 extensions of RP9.dll (render/IRenderPipelineEx.h). The
// interface methods are members of FDirectX9 (RP9.h) defined in RP9Ex.cpp; this header holds
// their state. Nothing here exists in RP8.dll or retail; see docs/re/rp9.md, "Ex extensions".

#include "RP9.h"

#include <string>
#include <vector>
#include <map>
#include <array>
#include <set>
#include <cstdint>

// GPU time per frame from D3D9 timestamp queries ([Render] render_stats = 1): the whole frame,
// the shadow-map passes, the Ex passes (nebula, sun rays) and the frame antialiasing. Results
// are read a few frames late without stalling.
struct ID3DXFont;

struct FRp9GpuTimers
{
    enum EMark : unsigned char { FrameBegin, FrameEnd, ShadowBegin, ShadowEnd, ExBegin, ExEnd,
                                 AaBegin, AaEnd };
    static const unsigned Frames = 4, Slots = 32;
    IDirect3DQuery9* Disjoint[Frames] = {};
    IDirect3DQuery9* Frequency[Frames] = {};
    IDirect3DQuery9* Stamps[Frames][Slots] = {};
    unsigned char Kinds[Frames][Slots] = {};
    unsigned Used[Frames] = {};
    bool bOpen[Frames] = {}, bPending[Frames] = {};
    unsigned Current = 0;
    bool bFailed = false;
    // Milliseconds summed over the frames collected since the last report.
    double Sum[4] = {};
    unsigned Collected = 0;
};

struct FRp9SurfaceInstanceGroup
{
    IDirect3DStateBlock9* State=nullptr;
    std::vector<std::array<float,32>> Matrices;
    unsigned long Prim=0,Min=0,Vertices=0,Start=0,Count=0,Fvf=0;
    INT Base=0;
};

// A shader program: the source location for reloads, the last bytecode that compiled, and the
// shader objects made from it (null while no device, or when the source never compiled).
struct FRPExProgram
{
    IFileSystem* FileSystem; // AddRef'd
    std::string Path;
    std::string VsEntry;
    std::string PsEntry;
    std::vector<unsigned char> VsBytecode;
    std::vector<unsigned char> PsBytecode;
    IDirect3DVertexShader9* Vs;
    IDirect3DPixelShader9* Ps;
};

enum ERp9ExTextureKind : unsigned int
{
    Rp9ExTextureRenderTarget = 0, // D3DPOOL_DEFAULT, re-created on every reset
    Rp9ExTextureVolume = 1,       // D3DPOOL_MANAGED, survives resets
    Rp9ExTextureSceneDepth = 2,   // the INTZ depth buffer (owned by FRp9ExState)
};

struct FRPExTexture
{
    ERp9ExTextureKind Kind;
    ERPExFormat Format;
    // Render targets: the creation request (Width/Height 0 = BackBufferScale of the back buffer).
    FRPExRenderTargetDesc TargetDesc;
    // The current size (render targets: after the last re-creation).
    unsigned long Width;
    unsigned long Height;
    unsigned long Depth;
    // IDirect3DTexture9 (render target, scene depth) or IDirect3DVolumeTexture9.
    IDirect3DBaseTexture9* Texture;
    // Level 0 of a render target / the scene depth surface; null for volumes.
    IDirect3DSurface9* Surface;
    // Volumes: the creation texels, for a device re-creation after ShutdownPipeline.
    std::vector<unsigned char> VolumeData;
};

// A static vertex buffer (CreateExVertexBuffer): D3DPOOL_MANAGED, so it survives a Reset; the bytes
// are kept for a device re-creation after ShutdownPipeline.
struct FRPExBuffer
{
    unsigned long Bytes;
    std::vector<unsigned char> Data;
    IDirect3DVertexBuffer9* Vb;
};

struct FRp9ExState
{
    FRp9ExState();

    std::vector<FRPExProgram*> Programs;
    std::vector<FRPExBuffer*> Buffers;
    // Render targets and volume textures created through the interface.
    std::vector<FRPExTexture*> Textures;
    // The INTZ depth buffer; Texture/Surface null when the device has no INTZ depth.
    FRPExTexture SceneDepth;
    // A plain depth surface made when the INTZ texture could not be created after the device
    // was already made without an auto depth-stencil.
    IDirect3DSurface9* FallbackDepth;
    unsigned long BackBufferWidth;
    unsigned long BackBufferHeight;

    // The open pass (BeginExPass .. EndExPass).
    bool bInPass;
    bool bDepthBound;
    IDirect3DSurface9* SavedColor;
    IDirect3DSurface9* SavedDepth;
    D3DVIEWPORT9 SavedViewport;
    unsigned char bSavedViewportRectValid;
    unsigned char bSavedDepthRangeValid;
    unsigned long SavedPending[FRp9RenderStateCache::StateCount];
    // Bit per sampler 0..15 the pass bound a texture on; stages 0..7 also saved their cache.
    unsigned long TouchedSamplers;
    FRp9ExStageSave SavedStages[FRp9DeviceStateCaches::StageCount];
    // Bit per sampler that holds the scene depth.
    unsigned long SceneDepthSamplers;
    // What the pass bound on each sampler (not AddRef'd; Get* is unavailable on a pure device).
    IDirect3DBaseTexture9* BoundTextures[16];
    FRPExProgram* BoundProgram;
    // The pass's colour target (null = the back buffer) and its size.
    FRPExTexture* CurrentTarget;
    unsigned long TargetWidth;
    unsigned long TargetHeight;

    // Soft particles (SetSoftParticles): the requested kind, the fade distance of each kind
    // (port.ini [Render], read once), the built-in shaders and the draw in flight.
    unsigned long SoftKind;
    float SoftFade[3];
    float SoftFadeOverride; // SetSoftParticleFade; 0 = SoftFade[SoftKind]
    bool bSoftConfigRead;
    bool bSoftCompileFailed;
    bool bSoftActive;
    IDirect3DVertexShader9* SoftVs;
    IDirect3DPixelShader9* SoftPs;
    FRp9ExStageSave SoftSavedStage1;

    // Planet atmosphere (SetPlanetAtmosphere): requested by Shading around the shell draw,
    // port.ini [Render] settings (read once) and the shaders of planet_atmosphere.hlsl.
    bool bAtmosphereRequested = false, bAtmosphereActive = false, bAtmosphereConfigRead = false;
    bool bAtmosphereEnabled = true, bAtmosphereFailed = false;
    FRPPlanetAtmosphere AtmosphereDesc = {};
    std::string AtmosphereName;
    float AtmosphereThickness = 0.06f, AtmosphereBrightness = 0.9f, AtmosphereHaze = 0.12f, AtmosphereRim = 2.5f;
    float AtmosphereFalloff = 3.0f, AtmosphereWrap = 0.3f, AtmosphereForward = 1.5f, AtmosphereWarmth = 0.5f,
          AtmosphereVeil = 0.5f;
    std::string AtmosphereExclude;
    IDirect3DVertexShader9* AtmosphereVs = nullptr;
    IDirect3DPixelShader9* AtmospherePs = nullptr;
    std::set<std::string> AtmosphereLogged;

    // Planet surface (SetPlanetSurface): requested by Shading around a planet material draw, port.ini
    // [Render] settings (read once), the classification of the requested material and planet_surface.hlsl.
    bool bPlanetRequested = false, bPlanetActive = false, bPlanetConfigRead = false;
    bool bPlanetEnabled = true, bPlanetFailed = false;
    std::string PlanetName, PlanetExclude;
    unsigned long PlanetMode = 0, PlanetWater = 0;
    float PlanetTile0 = 1.0f, PlanetTile1 = 1.0f, PlanetReliefNow = 0.0f, PlanetGlintNow = 0.0f;
    float PlanetLayers[4] = {}, PlanetElevation[2] = {}; // per layer: water, relief; elevation
    float PlanetGlow[4] = {1.0f, 0.0f, 0.0f, 0.0f};    // strength, night-only, (shadows), pulse
    float PlanetSurface[4] = {};                        // airless, ice sheen, layer 0 ice, layer 1 ice
    float PlanetCityLights = 0.6f, PlanetLavaPulse = 1.0f, PlanetIceSheen = 0.6f, PlanetAirless = 1.0f;
    bool bPlanetGas = false;     // a gas giant side: animated jets, eddies, storms, lightning
    float PlanetStorms[12] = {}; // three vortices: longitude, latitude, radius, spin
    float PlanetGasFlow = 1.0f, PlanetGasTurbulence = 1.0f, PlanetGasStorms = 1.0f,
          PlanetSeam = 0.01f;
    LARGE_INTEGER PlanetClockStart = {}, PlanetClockFrequency = {};
    std::string PlanetSwirlList;
    bool bPlanetSwirl = false; // a chaotic gas giant: eddies churning in place, no jets
    float PlanetRelief = 6.0f, PlanetGlint = 10.0f, PlanetGlintRoughness = 0.13f, PlanetGlintFresnel = 0.02f,
          PlanetCloud = 0.45f, PlanetWrap = 0.05f, PlanetDetailRelief = 1.0f, PlanetShadows = 8.0f;
    IDirect3DVertexShader9* PlanetVs = nullptr;
    IDirect3DPixelShader9* PlanetPs = nullptr;
    std::set<std::string> PlanetLogged;
    FRp9ExStageSave PlanetSavedStage[3];
    // A planet eclipsing the planet being drawn (SetPlanetEclipse, from the client).
    bool bPlanetEclipse = false;
    FRPPlanetEclipse PlanetEclipse = {};

    // Planet rings (SetPlanetRing): the band being drawn, port.ini settings and planet_ring.hlsl.
    bool bRingRequested = false, bRingActive = false, bRingConfigRead = false, bRingEnabled = true, bRingFailed = false, bRingDebug = false;
    FRPPlanetRing RingDesc = {};
    float RingBrightness = 2.0f, RingBacklight = 1.0f, RingOpacity = 1.0f, RingForward = 1.5f;
    IDirect3DVertexShader9* RingVs = nullptr;
    IDirect3DPixelShader9* RingPs = nullptr;
    FRp9ExStageSave RingSavedStage[2];
    std::set<std::string> RingLogged; // one line per distinct ring (inner, outer)
    // The band's opacity profile per shape texture and rectangle (empty: unreadable), and the
    // one of the band last drawn (GetPlanetRingProfile).
    std::map<std::string, std::vector<float>> RingProfiles;
    const std::vector<float>* RingLastProfile = nullptr;

    // Generic surface shader route, independent of objects (ships/stations/asteroids).
    bool bSurfaceConfigRead = false;
    bool bSurfaceEnabled = false;
    bool bSurfaceCompileFailed = false;
    bool bSurfaceCubeCompileFailed = false;
    bool bSurfaceActive = false;
    bool bSurfaceCockpit = false, bSurfaceGlass = false;
    bool bCockpitShader = true, bGlassShader = true;
    float SurfaceGlassStrength = 1.5f, SurfaceCockpitStrength = 0.65f;
    bool bSurfaceMaterialValid = false;
    bool bSurfaceLogged = false;
    unsigned long SurfaceShader = RPSurfaceAuto;
    float SurfaceRoughness = 0.0f;
    float SurfaceEnvironment = -1.0f;
    float SurfaceHighlights = 1.35f;
    float SurfaceCoat = 0.9f;
    float SurfaceBrushed = 0.8f;
    D3DMATERIAL9 SurfaceMaterial = {};
    std::map<unsigned long, D3DLIGHT9> SurfaceDirectLights;
    IDirect3DVertexShader9* SurfaceVs = nullptr;
    unsigned SurfaceDistanceTier = 0; // 0 full, 1 diffuse/env only, 2 native
    IDirect3DPixelShader9* SurfaceLowPs = nullptr;
    IDirect3DPixelShader9* SurfaceLowCubePs = nullptr;
    IDirect3DPixelShader9* SurfacePs = nullptr;
    IDirect3DPixelShader9* SurfaceCubePs = nullptr;
    // Receivers without a shadow this frame (SURFACE_NO_SHADOW): no shadow registers or taps.
    IDirect3DPixelShader9* SurfaceNoShadowPs = nullptr;
    IDirect3DPixelShader9* SurfaceNoShadowCubePs = nullptr;
    // What the surface route last left on the device. Shaders stay bound after a surface draw
    // (a fixed-function draw unbinds them, ExSurfaceRelease); the shadow maps (s8/s9) and the
    // environment map (s10) sit on samplers fixed-function rendering never uses, so no stage
    // is saved or restored per draw. Each mirror is valid while the matching device-call
    // write counter is unchanged.
    std::uint32_t SurfaceShaderWrites = 0, SurfacePsWrites = 0, SurfaceSamplerWrites = 0;
    IDirect3DVertexShader9* SurfaceBoundVs = nullptr;
    IDirect3DPixelShader9* SurfaceBoundPs = nullptr;
    float SurfacePsMirror[96 * 4] = {};
    bool SurfacePsMirrorValid[96] = {};
    IDirect3DBaseTexture9* SurfaceSamplerTexture[5] = {};
    unsigned long SurfaceSamplerStates[5][8] = {};
    bool SurfaceSamplerValid[5] = {};

    struct WeaponGlintGroup
    {
        float Position[3] = {}, Colour[3] = {};
        unsigned long Owner = 0;
        unsigned Shots = 0;
    };
    WeaponGlintGroup WeaponGlints[8] = {};
    unsigned WeaponGlintCount = 0, WeaponGlintBudget = 8, WeaponGlintReceiverMask = 0;
    bool bWeaponGlintConfigRead = false, bWeaponGlintsEnabled = true;
    bool bWeaponGlintFrame = false, bWeaponGlintReceiver = false;
    float WeaponGlintStrength = 1.25f, WeaponGlintRadius = 22.5f;
    float WeaponGlintDistance = 1000.0f;
    float WeaponGlintEye[3] = {}, WeaponGlintRotation[16] = {};

    bool bShadowDrawing = false;
    bool bShadowFrameValid = false;
    bool bShadowReceiver = false;
    bool bShadowReceiverIsShip = false;
    bool bShadowAdaptiveQuality = true;
    float ShadowStaticQualityDistance = 500.0f;
    float ShadowShipQualityDistance = 150.0f;
    float ShadowLowSearchSamples = 4.0f;
    float ShadowLowFilterSamples = 4.0f;
    bool bShadowFailed = false;
    unsigned ShadowReadyMask = 0;
    unsigned ShadowCascade = 0;
    bool bShadowConfigRead = false;
    // Per map: [0] near, [1] far (and the far map's static cache).
    unsigned ShadowResolution[2] = {4096, 4096};
    float ShadowNearRadius = 150.0f;
    float ShadowFarRadius = 5000.0f;
    float ShadowMaxLength = 200.0f;
    float ShadowDepthSpan[2] = {800.0f,10500.0f};
    float ShadowStrength = 0.85f;
    float ShadowLightAngle = 2.0f;
    unsigned ShadowSearchSamples = 16;
    unsigned ShadowFilterSamples = 32;
    // NPC ship receivers (SetLocalShadowReceiver bits 5..6): 0 best, 1 moderate, 2 simple.
    unsigned ShadowReceiverTier = 0;
    float ShadowModerateSearchSamples = 8.0f, ShadowModerateFilterSamples = 8.0f;
    // Casters marked by SetLocalShadowCaster(1) (NPC ships) store a negative depth; their
    // shadow reaches only this far behind them.
    float ShadowShortReach = 100.0f;
    bool bShadowShortCaster = false;
    // The far map's static cache is rebuilt after this long even when nothing changed.
    DWORD ShadowStaticMaxAge = 10000;
    bool bQualityConfigRead = false;
    unsigned QualityAnisotropy = 16;
    unsigned QualityFxaaMode = 1;
    // Between a successful BeginScene and EndScene.
    bool bInScene = false;
    bool bQualityFxaaFailed = false;
    IDirect3DTexture9* QualitySceneCopy = nullptr;
    IDirect3DPixelShader9* QualityFxaaPs = nullptr;
    // Port-only windowed gamma: D3D9 ignores the gamma ramp in a window, so the game's curve
    // (SetGammaFunction: 1/gamma, brightness, contrast, bias) is applied to the finished frame at
    // SwapBuffers while windowed ([Render] windowed_gamma).
    bool bWindowed = true;
    bool bGammaFailed = false;
    float Gamma[4] = {1.0f, 0.0f, 1.0f, 0.0f};
    IDirect3DPixelShader9* GammaPs = nullptr;
    IDirect3DStateBlock9* QualitySavedState = nullptr;
    float ShadowBiasScale = 0.5f;
    // [0] near, [1] far, [2] the near map's moving casters (ships, asteroids).
    IDirect3DTexture9* ShadowMaps[3] = {};
    // Only the far cascade is cached: the near map stays live and needs no
    // additional 8192-square allocation. Cache failure falls back to full draws.
    IDirect3DTexture9* ShadowStaticMap = nullptr;
    bool bShadowStaticCache = true, bShadowStaticValid = false;
    bool bShadowStaticDrawing = false, bShadowStaticPrepared = false;
    bool bShadowStaticFailed = false;
    float ShadowStaticAnchor[3] = {}, ShadowStaticRay[3] = {};
    unsigned long ShadowStaticKey[2] = {}, ShadowStaticPendingKey[2] = {};
    DWORD ShadowStaticBuiltAt = 0;
    unsigned ShadowStaticHits = 0, ShadowStaticBuilds = 0;
    // Invalidations of a valid cache: camera move, sun direction, age, scene key.
    unsigned ShadowStaticReasons[4] = {};
    IDirect3DSurface9* ShadowDepth = nullptr;
    IDirect3DVertexShader9* ShadowVs = nullptr;
    IDirect3DPixelShader9* ShadowPs = nullptr;
    // Created once and re-captured per shadow map; released before a device reset.
    IDirect3DStateBlock9* ShadowSavedState = nullptr;
    IDirect3DSurface9* ShadowSavedColor = nullptr;
    IDirect3DSurface9* ShadowSavedDepth = nullptr;
    D3DVIEWPORT9 ShadowSavedViewport = {};
    float ShadowMatrices[2][16] = {};
    float ShadowCameraRotation[16] = {};
    float ShadowCameraPosition[3] = {};
    float ShadowSunDirection[4] = {};
    float ShadowPlanets[8][4] = {};
    unsigned ShadowPlanetCount = 0;
    // The eclipse caster among ShadowPlanets (radius stored negative): its reach and the
    // sun's angular radius (penumbra).
    float ShadowEclipseRange = 0.0f, ShadowEclipseSunAngle = 0.0f;
    FRp9RenderStateCache ShadowSavedRenderStates = {};
    FRp9DeviceStateCaches ShadowSavedDeviceStates = {};
    FRp9PipelineTransforms ShadowSavedTransforms = {};
    FRp9StreamCache ShadowSavedStream = {};
    FRp9PipelineStateSlot ShadowSavedPipeline[kRp9PipelineStateCount] = {};
    INT ShadowSavedBaseVertex = 0;
    D3DMATERIAL9 ShadowSavedMaterial = {};
    bool bShadowSavedMaterialValid = false;
    bool bSurfaceNormalCached=false,bSurfaceLightsCached=false;
    float SurfaceLastWorldView[16]={},SurfaceLastNormal[16]={};
    D3DLIGHT9 SurfaceLastLights[8]={};unsigned SurfaceLastLightCount=0;
    float SurfaceLastLightView[16]={},SurfacePackedLights[8*20]={},SurfaceLightAmbient[3]={};
    bool bRenderStatsRead=false,bRenderStats=false;
    FRp9GpuTimers GpuTimers;
    // The "caching shaders" line drawn while the surface shader warm-up runs.
    ID3DXFont* WarmupFont = nullptr;
    IDirect3DStateBlock9* WarmupSavedState = nullptr;
    int WarmupLanguage = -1; // -1 unread, 0 English, 1 Russian
    DWORD RenderStatsAt=0;unsigned RenderStatsFrames=0;
    bool bInstanceConfigRead=false,bSurfaceInstancing=false,bInstanceScope=false,bInstanceFailed=false;
    IDirect3DVertexBuffer9* SurfaceInstanceVb=nullptr;
    IDirect3DVertexShader9* SurfaceInstanceVs=nullptr;
    std::map<unsigned long,IDirect3DVertexDeclaration9*> SurfaceInstanceDecls;
    std::map<std::string,FRp9SurfaceInstanceGroup> SurfaceInstanceGroups;
    unsigned SurfaceInstanceQueued=0;
};
