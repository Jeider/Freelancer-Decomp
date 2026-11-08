// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

#include "common_archetype.h"
#include "common_goods.h"

#include <stdio.h>
#include <string>
#include <vector>
#include <map>

class INI_Reader;

struct PlayerShipCacheView {
    unsigned Id;
    char Name[64];
    unsigned ShipArchetype;
    float RelativeHealth;
    unsigned BaseId;
    int bActive;
};

struct PlayerShipCacheEquip {
    unsigned ArchId;
    char Hardpoint[64];
    float Health;
    int Count;
    unsigned char bEquipped;
};

struct ShipCacheRecord {
    unsigned Id = 0;
    char Name[64] = {};
    unsigned ShipArchetype = 0;
    float RelativeHealth = 1.0f;
    unsigned BaseId = 0;
    bool Parking = false;
    std::string WeaponGroups;
    EquipDescList Equipment;
    std::list<CollisionGroupDesc> Groups;
};

struct ShipParkingSave {
    bool Initialized = false;
    std::map<unsigned, unsigned> Owned;
};

void ShipCache_Clear(unsigned ClientId);
void ShipCache_Install(unsigned ClientId, std::vector<ShipCacheRecord> const& Records,
                       ShipParkingSave const& Parking);
bool ShipCache_TryRead(std::vector<ShipCacheRecord>& Records, ShipParkingSave& Parking, INI_Reader& Reader);
void ShipCache_Write(FILE* Out, unsigned ClientId);
