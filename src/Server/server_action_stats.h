#pragma once
#include "player_action_stats.h"
#include <cstdio>
struct PlayerData;
struct DamageList;
struct IObjRW;
namespace ServerActionStats {
using PlayerActionStats::Counter;
using PlayerActionStats::State;
void Load(unsigned player, State const& state);
void Clear(unsigned player);
State Snapshot(unsigned player);
void Add(unsigned player, Counter counter, double amount=1);
void Save(FILE* file, State const& state);
void BeginTrade(unsigned player, unsigned good, unsigned count, bool buy);
void CashChanged(PlayerData const& player, int before);
void InventoryChanged(PlayerData const& player);
void UsedItem(PlayerData const& player, unsigned short equipment, int count);
void Damaged(IObjRW* object, DamageList const& damage);
void Visited(unsigned player, unsigned object);
void EnteredSpace(unsigned player, bool launched);
void Landed(unsigned player);
}
