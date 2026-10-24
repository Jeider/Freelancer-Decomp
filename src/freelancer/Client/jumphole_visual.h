#pragma once
class FClientGameobj;
class FClientSolarGameobj;
struct FSpaceCamera;
struct FJumpShipEffect;
bool JumpHoleVisualReplaceAttached(FClientGameobj* Host, unsigned EffectId);
bool JumpHoleVisualReplaceActivation(FClientSolarGameobj* Host, unsigned EffectId);
void JumpHoleVisualTick(FClientSolarGameobj* Host, float Dt);
void JumpHoleVisualEvent(FClientSolarGameobj* Host, int Sub);
void JumpHoleVisualForget(FClientSolarGameobj* Host);
void JumpHoleVisualDraw(FSpaceCamera* Camera);
void JumpHoleVisualBindTransit(FJumpShipEffect const* Effect, FClientSolarGameobj* Host);
void JumpHoleVisualForgetTransit(FJumpShipEffect const* Effect);
bool JumpHoleVisualDrawIngress(FSpaceCamera* Camera, FJumpShipEffect const* Effect);
void JumpHoleVisualRenderShutdown();
