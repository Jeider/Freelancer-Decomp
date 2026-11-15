#pragma once
#include "server_exports.h"
class StarSystem;
class GameObject;
void ActivatePhysicalTradeLane(GameObject*, bool active, unsigned ship);
void UpdateSolarAnimations(StarSystem&, float);
void ForgetSolarAnimations(StarSystem&);
void SendSolarAnimations(StarSystem&, unsigned player);
SERVER_API bool StartSolarAnimation(unsigned object, char const* name);
