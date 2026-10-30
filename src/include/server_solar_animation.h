#pragma once
#include "server_exports.h"
class StarSystem;
void UpdateSolarAnimations(StarSystem&, float);
void ForgetSolarAnimations(StarSystem&);
void SendSolarAnimations(StarSystem&, unsigned player);
SERVER_API bool StartSolarAnimation(unsigned object, char const* name);
