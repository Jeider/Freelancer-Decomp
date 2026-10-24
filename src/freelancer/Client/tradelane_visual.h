#pragma once

struct FTransform;
struct FSpaceCamera;
struct FTradeLaneVisualStyle;

// Shared by the surrounding corridor and ship-attached effects, including NPCs.
FTradeLaneVisualStyle TradeLaneVisualResolveStyle(FTransform const& Lane, unsigned RouteId);

// Port-only player corridor. Simulation owns travel/age; rendering only follows camera position.
void TradeLaneVisualStart(FTransform const& Lane, unsigned RouteId = 0);
void TradeLaneVisualStop();
void TradeLaneVisualTick(float Dt, float X, float Y, float Z);
void TradeLaneVisualReset();
void TradeLaneVisualDraw(FSpaceCamera* Camera);
void TradeLaneVisualRenderShutdown();
