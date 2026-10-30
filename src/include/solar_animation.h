#pragma once
#include "common_exports.h"
class INI_Reader;
class CSolar;
namespace Archetype { struct Root; }

// Optional ACTIVATEOBJECT extension. Native boolean activation packets are unchanged.
struct SolarAnimationCommand
{
    char Name[96]{};
    float Time = 0;
    unsigned Reverse = 0;
    unsigned Sound = 0;
    unsigned Serial = 0;
};
static_assert(sizeof(SolarAnimationCommand) == 112, "animation wire extension");

namespace SolarAnimation
{
struct Config
{
    bool Enabled = false;
    float Radius = 800, ReleaseRadius = 1100, CloseDelay = 3;
    char Open[96]{}, Close[96]{};
    unsigned OpenSound = 0, CloseSound = 0;
};
COMMON_API bool Read(Archetype::Root const*, INI_Reader&);
COMMON_API void Copy(Archetype::Root const*, Archetype::Root const*);
COMMON_API void ForgetDefinition(Archetype::Root const*);
COMMON_API bool GetConfig(Archetype::Root const*, Config&);
COMMON_API float Duration(CSolar const*, char const*);
COMMON_API bool Play(CSolar*, SolarAnimationCommand const&);
COMMON_API void Initialize(CSolar*);
COMMON_API void Forget(CSolar*);
}
