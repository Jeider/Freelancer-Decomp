#pragma once
struct IObjRW;
class Vector;
// Owner is the PathfindManager; its destructor releases the persistent bypass.
void ResetServerAsteroidAvoidance(void const* owner, IObjRW* ship=nullptr);
bool FindServerAsteroidAvoidance(void const* owner, IObjRW* ship, unsigned system, Vector const& goal,
                                 Vector& point, float& scale);
