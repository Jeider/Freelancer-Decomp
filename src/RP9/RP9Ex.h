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

struct FRp9ExState
{
    FRp9ExState();

    std::vector<FRPExProgram*> Programs;
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
    IDirect3DPixelShader9* SurfacePs = nullptr;
    IDirect3DPixelShader9* SurfaceCubePs = nullptr;
    FRp9ExStageSave SurfaceSavedStage1 = {};
    FRp9ExStageSave SurfaceSavedShadowStages[2] = {};
    bool bSurfaceShadowSamplers = false;

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
    unsigned ShadowResolution = 8192;
    float ShadowNearRadius = 150.0f;
    float ShadowFarRadius = 5000.0f;
    float ShadowMaxLength = 200.0f;
    float ShadowDepthSpan[2] = {800.0f,10500.0f};
    float ShadowStrength = 0.85f;
    float ShadowLightAngle = 2.0f;
    unsigned ShadowSearchSamples = 64;
    unsigned ShadowFilterSamples = 192;
    bool bQualityConfigRead = false;
    unsigned QualityAnisotropy = 16;
    bool bQualityFxaa = true;
    bool bQualityFxaaFailed = false;
    IDirect3DTexture9* QualitySceneCopy = nullptr;
    IDirect3DPixelShader9* QualityFxaaPs = nullptr;
    float ShadowBiasScale = 0.5f;
    IDirect3DTexture9* ShadowMaps[2] = {};
    IDirect3DSurface9* ShadowDepth = nullptr;
    IDirect3DVertexShader9* ShadowVs = nullptr;
    IDirect3DPixelShader9* ShadowPs = nullptr;
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
    FRp9RenderStateCache ShadowSavedRenderStates = {};
    FRp9DeviceStateCaches ShadowSavedDeviceStates = {};
    FRp9PipelineTransforms ShadowSavedTransforms = {};
    FRp9StreamCache ShadowSavedStream = {};
    FRp9PipelineStateSlot ShadowSavedPipeline[kRp9PipelineStateCount] = {};
    INT ShadowSavedBaseVertex = 0;
    D3DMATERIAL9 ShadowSavedMaterial = {};
    bool bShadowSavedMaterialValid = false;
};
