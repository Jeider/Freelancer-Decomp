#pragma once
#include "procedural_asteroids.h"
#include <vector>
struct FClientGameobj;
class Vector;
// Persistent recipe/pose; nearby replicated bodies draw their native material.
void ProceduralAsteroidClientEnter(unsigned system);
void ProceduralAsteroidClientTick(unsigned system);
bool ProceduralAsteroidClientReceive(unsigned sender,unsigned size,void const* data);
bool ProceduralAsteroidClientRecipe(unsigned zone,unsigned& seed,unsigned& models,unsigned& revision);
bool ProceduralAsteroidClientResolve(unsigned zone,ProceduralAsteroids::Rock& rock);
void ProceduralAsteroidClientRenderer(unsigned zone,bool available);
bool ProceduralAsteroidClientOwns(FClientGameobj* object);
bool ProceduralAsteroidClientPhysical(FClientGameobj* object);
void ProceduralAsteroidClientBeginVisuals();
void ProceduralAsteroidClientDrawn(FClientGameobj* object);
void ProceduralAsteroidClientCommitVisuals();
bool ProceduralAsteroidClientNativeVisual(ProceduralAsteroids::Key key);
void ProceduralAsteroidClientObserve(FClientGameobj* object);
void ProceduralAsteroidClientForget(FClientGameobj* object);
void ProceduralAsteroidClientExtras(unsigned zone,std::vector<ProceduralAsteroids::Rock>& rocks);
void ProceduralAsteroidClientVisible(ProceduralAsteroids::Key key);
void ProceduralAsteroidClientHide(ProceduralAsteroids::Key key);
float ProceduralAsteroidClientClock();
void ProceduralAsteroidClientChanges(std::vector<ProceduralAsteroids::Key>& keys);
bool ProceduralAsteroidClientSpatialUpdate(FClientGameobj* object,Vector const& position,float radius);
