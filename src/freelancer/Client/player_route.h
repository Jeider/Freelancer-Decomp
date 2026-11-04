#pragma once
class HUD_Maneuvers;
class Vector;
namespace PlayerRoute {
#ifdef FREELANCER_PLAYER_FLIGHT_ACTIONS
bool Start(HUD_Maneuvers* panel,bool rebuilt=false);
void Cancel(bool freeFlight=false);
bool Active();
bool InternalCommand();
void Tick(float dt,bool docking);
bool Keyboard(float x,float y,float z);
bool BlockMouse();
bool MouseSteering(float x,float y,float z);
// Release both Common's cached turn command and Go To's manual override.
bool ReleaseMouseSteering();
void SetCruiseRequested(bool enabled);
void PathRequested();
void BeginPathResponse();
void Landed();
void RouteChanged();
void WaypointRemoved();
// The map still asks the server for intersystem/tradelane topology. This refines
// its free-space legs with the selectable beta corridor planner and hazard checks.
bool RefineWaypoints();
#else
inline bool Start(HUD_Maneuvers*,bool=false) { return false; }
inline void Cancel(bool=false) {}
inline bool Active() { return false; }
inline bool InternalCommand() { return false; }
inline void Tick(float,bool) {}
inline bool Keyboard(float,float,float) { return false; }
inline bool BlockMouse() { return false; }
inline bool MouseSteering(float,float,float) { return false; }
inline bool ReleaseMouseSteering() { return false; }
inline void SetCruiseRequested(bool) {}
inline void PathRequested() {}
inline void BeginPathResponse() {}
inline void Landed() {}
inline void RouteChanged() {}
inline void WaypointRemoved() {}
inline bool RefineWaypoints() { return true; }
#endif
}
