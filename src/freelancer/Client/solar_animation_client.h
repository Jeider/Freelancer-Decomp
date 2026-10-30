#pragma once
class FClientGameobj;
struct FPayloadServerActivateObject;
void ClientSolarAnimation(FPayloadServerActivateObject const&);
void ClientSolarAnimationTick(FClientGameobj*);
void ClientSolarAnimationForget(FClientGameobj*);
