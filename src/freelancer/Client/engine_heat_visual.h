#pragma once
class FClientGameobj;
class CEEngine;
struct FSpaceCamera;

// Additional player exhaust optics. Retail ALE ownership/intensity stays unchanged.
void EngineHeatVisualUpdate(FClientGameobj* Host,CEEngine const* Engine,float Intensity,float Dt);
void EngineHeatVisualForget(FClientGameobj* Host,CEEngine const* Engine);
void EngineHeatVisualDraw(FSpaceCamera* Camera);
void EngineHeatVisualShutdown();
