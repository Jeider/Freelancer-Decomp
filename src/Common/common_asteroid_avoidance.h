#pragma once
struct IObjRW;
class Vector;
bool FindServerAsteroidAvoidance(IObjRW* ship, unsigned system, Vector const& goal,
                                 Vector& point, float& scale);
