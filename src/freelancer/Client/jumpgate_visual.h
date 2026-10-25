#pragma once
class FClientSolarGameobj;
struct FSpaceCamera;
struct FJumpShipEffect;
bool JumpGateVisualReplaceActivation(FClientSolarGameobj* Host, unsigned EffectId);
void JumpGateVisualEvent(FClientSolarGameobj* Host, int Sub);
void JumpGateVisualTick(FClientSolarGameobj* Host, float Dt);
void JumpGateVisualForget(FClientSolarGameobj* Host);
void JumpGateVisualDraw(FSpaceCamera* Camera);
void JumpGateVisualBindTransit(FJumpShipEffect const* Effect, FClientSolarGameobj* Host);
void JumpGateVisualForgetTransit(FJumpShipEffect const* Effect);
bool JumpGateVisualMatchesTransit(FJumpShipEffect const* Effect);
void JumpGateVisualRenderStartup();
void JumpGateVisualRenderShutdown();
