#pragma once
#include "dacom.h"

// Optional RP9 interface; no change to retail material, model or pipeline layouts.
struct IRPRoomMaterials : IDAComponent
{
    virtual GENRESULT DACOM_API SetRoomMaterialFrame(unsigned long Enabled) = 0;
    virtual GENRESULT DACOM_API SetRoomMaterial(const char* Name, const char* Texture) = 0;
    virtual GENRESULT DACOM_API ApplyRoomContactShadows() = 0;
    virtual GENRESULT DACOM_API SetRoomBase(const char* Nickname) = 0;
    virtual GENRESULT DACOM_API SetRoomDetail(const char* Detail) = 0;
    virtual GENRESULT DACOM_API SetRoomProp(unsigned long Prop) = 0;
};

// Separate optional ABI: opaque silhouettes projected vertically onto room depth.
struct IRPRoomShadows : IDAComponent
{
    virtual GENRESULT DACOM_API BeginRoomShadow(const float* CameraView12, const float* Center3, float Radius,
                                               unsigned long Character = 0) = 0;
    virtual GENRESULT DACOM_API EndRoomShadow() = 0;
};

// Optional, separate ABI. Owners are room-runtime identities, not render frames.
// Calls run on the render/device thread while room assets are being loaded.
struct IRPRoomMaterialCache : IDAComponent
{
    virtual GENRESULT DACOM_API BeginRoomMaterialCache(void* Owner, const char* Base) = 0;
    virtual GENRESULT DACOM_API PreloadRoomMaterial(const char* Name, const char* Texture) = 0;
    virtual GENRESULT DACOM_API EndRoomMaterialCache(void* Owner) = 0;
};

// Draw-local character context. Never stored on shared materials or textures.
struct IRPCharacterQuality : IDAComponent
{
    virtual unsigned long DACOM_API CharacterQualityPass() = 0; // 0 other, 1 room colour, 2 shadow
    virtual float DACOM_API SetCharacterQuality(float Strength) = 0; // returns previous value
};
