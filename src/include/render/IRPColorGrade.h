#pragma once
#include "dacom.h"
struct IRPColorGrade : IDAComponent
{
    virtual GENRESULT DACOM_API ApplyColorGrade(unsigned Preset) = 0;
};
namespace Iids { static const char RPColorGrade[]="IRPColorGrade_v1"; }
