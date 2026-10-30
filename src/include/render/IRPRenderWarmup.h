#pragma once
#include "dacom.h"

// Optional loading-screen operation; existing rendering interfaces keep their ABI.
struct IRPRenderWarmup : IDAComponent
{
    virtual GENRESULT DACOM_API WarmSceneCaches() = 0;
};
