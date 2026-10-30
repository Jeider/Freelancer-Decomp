#pragma once

// A moving, destructible solar with server-owned physics. Keep the satellite bit
// for the existing solar buckets; the new bit identifies this subtype.
// CEqObj::is_targetable excludes this subtype from scanner/HUD targeting.
// Client-only DynamicAsteroids keep their original type and lifecycle.
constexpr unsigned SERVER_ASTEROID_TYPE = 0x00800010u;
inline bool IsServerAsteroidType(unsigned type) { return type == SERVER_ASTEROID_TYPE; }
