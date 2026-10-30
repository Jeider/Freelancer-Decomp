#pragma once
#include "player_action_stats.h"
struct CObject;
struct DamageList;
namespace PlayerActionCounters {
void BeginFrame(float dt,bool paused);
void EndFrame(bool docking);
void LeaveSpace();
void Shot(unsigned ship,unsigned short equipment,bool automatic);
void Damage(unsigned object,DamageList const& damage);
void Collision(CObject* a,CObject* b);
bool Snapshot(PlayerActionStats::State& result);
}
