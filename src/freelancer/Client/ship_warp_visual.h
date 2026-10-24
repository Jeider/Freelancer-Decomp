#pragma once
class FClientGameobj;
class FClientShipGameobj;
struct FJumpShipEffect;
struct FSpaceCamera;

// Ship-attached travel light; independent of the player's surrounding corridor.
bool ShipWarpVisualStartLane(FClientGameobj* Ship,unsigned EffectId,unsigned RouteId);
void ShipWarpVisualStopLane(FClientGameobj* Ship);
void ShipWarpVisualTickLanes(float Dt);
void ShipWarpVisualTickJump(FJumpShipEffect const* Effect,float Dt);
void ShipWarpVisualForgetJump(FJumpShipEffect const* Effect);
void ShipWarpVisualReset();
void ShipWarpVisualDraw(FSpaceCamera* Camera,FClientShipGameobj* TunnelShip=nullptr);
void ShipWarpVisualRenderShutdown();
