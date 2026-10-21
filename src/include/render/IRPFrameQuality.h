#pragma once
#include "dacom.h"

// Optional port-only postprocess, called once after the space scene, before HUD.
struct IRPFrameQuality : IDAComponent
{
    virtual GENRESULT DACOM_API ApplySceneAntialiasing() = 0;
};
