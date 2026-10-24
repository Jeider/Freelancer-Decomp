#pragma once
#include "dacom.h"

struct FRPExTexture;

// Optional GPU-only snapshot of the current colour target, outside any Ex/material pass.
// Query Iids::RPSceneCapture; older pipelines need not implement this interface.
// Destination is a caller-owned, full-size A8R8G8B8 Ex render target. It follows the normal
// Ex texture reset/destroy lifetime. A failed capture leaves its contents unspecified.
// An open scene is temporarily closed for the copy and reopened even when the copy fails.
// If reopening fails (for example device loss), the pipeline records the scene as closed.
struct IRPSceneCapture : IDAComponent
{
    virtual GENRESULT DACOM_API CaptureSceneColor(FRPExTexture* Destination) = 0;
};
