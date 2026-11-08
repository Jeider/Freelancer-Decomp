#pragma once
struct FSpaceCamera;
// Visual only: never changes CEqObj::CloakPercent, targeting or collision geometry.
void CloakVisualDraw(FSpaceCamera* Camera);
void CloakVisualShutdown();
