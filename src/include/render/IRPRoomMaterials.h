#pragma once
#include "dacom.h"

// Optional RP9 interface; no change to retail material, model or pipeline layouts.
struct IRPRoomMaterials : IDAComponent
{
    virtual GENRESULT DACOM_API SetRoomMaterialFrame(unsigned long Enabled) = 0;
    virtual GENRESULT DACOM_API SetRoomMaterial(const char* Name, const char* Texture) = 0;
    virtual GENRESULT DACOM_API ApplyRoomContactShadows() = 0;
};

// Separate optional ABI: opaque silhouettes projected vertically onto room depth.
struct IRPRoomShadows : IDAComponent
{
    virtual GENRESULT DACOM_API BeginRoomShadow(const float* CameraView12, const float* Center3, float Radius,
                                               unsigned long Character = 0) = 0;
    virtual GENRESULT DACOM_API EndRoomShadow() = 0;
};
