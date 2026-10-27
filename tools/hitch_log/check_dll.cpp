#include "runtime_hitch_log.h"
#pragma comment(linker,"/EXPORT:RunFixture=_RunFixture")
extern "C" void RunFixture(){RuntimeHitchScope s("model_load","from_dll.cmp",0);Sleep(5);}
