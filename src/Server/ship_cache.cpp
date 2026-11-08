// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#include "../include/ship_cache.h"
#include "../include/ship_parking.h"
#include "../include/readfile.h"

#include "../include/common_id.h"
#include "../include/common_ini.h"
#include "../include/common_misc.h"
#include "../include/common_net.h"
#include "../include/common_server.h"
#include "../include/common_server_playerdb.h"
#include "../include/rpc_iclient.h"

#include <ctype.h>
#include <map>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

extern IClient* g_pClientInterface;

struct ParkingRules {
    unsigned Maximum = 3;
    unsigned Initial = 0;
    int Price = 20000;
    unsigned Seller = 0;
    unsigned ReputationFaction = 0;
};

// Read once per process; configuration edits take effect after restarting the game.
static ParkingRules RulesFor(unsigned Base) {
    static bool Loaded = false;
    static ParkingRules Defaults;
    static std::map<unsigned, ParkingRules> Bases;
    if (!Loaded && pub::GetDataPath()) {
        Loaded = true;
        char Directory[260] = {}, Path[520] = {};
        pub::GetDataPath()->GetFileSysPath(Directory, sizeof(Directory));
        snprintf(Path, sizeof(Path), "%s\\RPG\\ship_parking.ini", Directory);
        INI_Reader Reader;
        if (Reader.open(Path, false)) {
            // Defaults are resolved before overrides, independent of section order.
            for (int Pass = 0; Pass < 2; ++Pass) {
                Reader.reset();
                while (Reader.read_header()) {
                    bool const Default = Reader.is_header("ParkingDefaults");
                    if ((Pass == 0 && !Default) ||
                        (Pass == 1 && !Reader.is_header("ParkingBase"))) continue;
                    ParkingRules Rules = Defaults;
                    unsigned Id = 0;
                    bool Valid = true;
                    while (Reader.read_value()) {
                        if (Reader.is_value("base")) Id = CreateID(Reader.get_value_string());
                        else if (Reader.is_value("seller")) Rules.Seller = CreateID(Reader.get_value_string());
                        else if (Reader.is_value("reputation_faction"))
                            pub::Reputation::GetReputationGroup(Rules.ReputationFaction, Reader.get_value_string());
                        else if (Reader.is_value("max_slots") || Reader.is_value("initial_slots") || Reader.is_value("slot_price")) {
                            char const* Value = Reader.get_value_string();
                            char* End = nullptr;
                            long const Number = strtol(Value, &End, 10);
                            while (End && isspace(static_cast<unsigned char>(*End))) ++End;
                            if (!Value[0] || !End || *End || Number < 0 || Number > 999999999) { Valid = false; continue; }
                            if (Reader.is_value("max_slots")) Rules.Maximum = static_cast<unsigned>(Number);
                            else if (Reader.is_value("initial_slots")) Rules.Initial = static_cast<unsigned>(Number);
                            else Rules.Price = static_cast<int>(Number);
                        }
                    }
                    if (Rules.Initial > Rules.Maximum) Valid = false;
                    if (!Valid) {
                        FDUMP(0x100001, "Ship parking: invalid settings for base %u; sales disabled", Id);
                        if (!Default && Id) { Rules = Defaults; Rules.Seller = 0; Bases[Id] = Rules; }
                        continue;
                    }
                    if (Default) Defaults = Rules;
                    else if (Id) Bases[Id] = Rules;
                }
            }
        }
    }
    auto const It = Bases.find(Base);
    return It == Bases.end() ? Defaults : It->second;
}

struct LiveCache {
    std::vector<ShipCacheRecord> Ships;
    ShipParkingSave Parking;
};

static std::map<unsigned, LiveCache> GCaches;

static unsigned OwnedAt(LiveCache const& Cache, unsigned Base, ParkingRules const& Rules) {
    auto const It = Cache.Parking.Owned.find(Base);
    return It == Cache.Parking.Owned.end() ? Rules.Initial : It->second;
}

static unsigned UsedAt(LiveCache const& Cache, unsigned Base) {
    unsigned Used = 0;
    for (auto const& Ship : Cache.Ships) if (Ship.Parking && Ship.BaseId == Base) ++Used;
    return Used;
}

static bool HasMissionShip(LiveCache const& Cache) {
    for (auto const& Ship : Cache.Ships) if (!Ship.Parking) return true;
    return false;
}

static ShipCacheRecord* ParkingRecord(LiveCache& Cache, int Index) {
    if (Index < 0) return nullptr;
    for (auto& Ship : Cache.Ships) if (Ship.Parking && Index-- == 0) return &Ship;
    return nullptr;
}

static bool ValidName(char const* Name) {
    if (Name == nullptr || Name[0] == '\0' || strlen(Name) >= 64)
        return false;
    for (char const* It = Name; *It != '\0'; ++It) {
        unsigned char const Ch = static_cast<unsigned char>(*It);
        if (!isalnum(Ch) && Ch != '_')
            return false;
    }
    return true;
}

static void CopyName(char* Dest, char const* Src) {
    Dest[0] = '\0';
    if (Src == nullptr)
        return;
    strncpy(Dest, Src, 63);
    Dest[63] = '\0';
}

static bool ValidPlayer(unsigned PlayerId, PlayerSlot*& Slot) {
    Slot = nullptr;
    if (PlayerId == 0 || (PlayerId - 1) >= PlayerDB_GetMaxPlayers())
        return false;
    Slot = PlayerDB_GetPlayer(PlayerId);
    return Slot != nullptr && Slot->client_id != 0;
}

static ShipCacheRecord* FindByName(LiveCache& Cache, char const* Name) {
    for (size_t Index = 0; Index < Cache.Ships.size(); ++Index) {
        if (_stricmp(Cache.Ships[Index].Name, Name) == 0)
            return &Cache.Ships[Index];
    }
    return nullptr;
}

static ShipCacheRecord* FindById(std::vector<ShipCacheRecord>& Records, unsigned Id) {
    for (size_t Index = 0; Index < Records.size(); ++Index) {
        if (Records[Index].Id == Id)
            return &Records[Index];
    }
    return nullptr;
}

static bool Snapshot(PlayerSlot& Slot, char const* Name, ShipCacheRecord& Out) {
    if ((Slot.ship_archetype & 0x3fffffffu) == 0)
        return false;
    CopyName(Out.Name, Name);
    Out.Id = CreateID(Out.Name);
    Out.ShipArchetype = Slot.ship_archetype;
    Out.RelativeHealth = Slot.relative_health;
    Out.BaseId = Slot.current_base;
    Out.WeaponGroups = Slot.weapon_group_name;
    Out.Equipment = Slot.equipment;
    Out.Groups = Slot.collision_groups;
    return true;
}

static void SendWeaponGroups(unsigned ClientId, std::string const& Groups) {
    if (g_pClientInterface == nullptr)
        return;
    g_pClientInterface->SendCommonSetWeaponGroup(
        ClientId, reinterpret_cast<unsigned char const*>(Groups.c_str()),
        static_cast<unsigned>(Groups.size()));
}

static void ClearActiveShip(PlayerSlot& Slot) {
    PlayerData_SetShipArch(Slot, 0);
    EquipDescList Empty;
    PlayerData_LoadEquipment(Slot, Empty);
    PlayerData_SetRelativeHealth(Slot, 1.0f, true);
    Slot.weapon_group_name.clear();
    SendWeaponGroups(Slot.client_id, Slot.weapon_group_name);
}

static void InstallRecord(PlayerSlot& Slot, ShipCacheRecord const& Record) {
    PlayerData_SetShipArch(Slot, Record.ShipArchetype);
    PlayerData_SetCollisionGroups(Slot, Record.Groups);
    PlayerData_SetRelativeHealth(Slot, Record.RelativeHealth, true);
    EquipDescList Fresh;
    for (std::list<EquipDesc>::const_iterator It = Record.Equipment.Items.begin();
         It != Record.Equipment.Items.end(); ++It) {
        EquipDesc Copy(*It);
        Copy.set_id(SUBOBJ_ID_NONE);
        Fresh.Items.push_back(Copy);
    }
    PlayerData_LoadEquipment(Slot, Fresh);
    Slot.weapon_group_name = Record.WeaponGroups;
    SendWeaponGroups(Slot.client_id, Slot.weapon_group_name);
}

static int StoreNamed(PlayerSlot& Slot, char const* Name, bool Parking = false) {
    if (!ValidName(Name))
        return -4;
    ShipCacheRecord Snap;
    if (!Snapshot(Slot, Name, Snap))
        return -4;
    Snap.Parking = Parking;
    LiveCache& Cache = GCaches[Slot.client_id];
    ShipCacheRecord* Existing = FindByName(Cache, Name);
    if (Existing && Existing->Parking != Parking) return ParkingInvalid;
    if (Existing == nullptr) {
        Cache.Ships.push_back(Snap);
    } else {
        *Existing = Snap;
    }
    return 0;
}

static void HexEncode(std::string const& In, std::string& Out) {
    static char const Digits[] = "0123456789abcdef";
    Out.clear();
    Out.reserve(In.size() * 2);
    for (size_t Index = 0; Index < In.size(); ++Index) {
        unsigned char const Byte = static_cast<unsigned char>(In[Index]);
        Out.push_back(Digits[Byte >> 4]);
        Out.push_back(Digits[Byte & 0x0f]);
    }
}

static int HexNibble(char Ch) {
    if (Ch >= '0' && Ch <= '9')
        return Ch - '0';
    if (Ch >= 'a' && Ch <= 'f')
        return Ch - 'a' + 10;
    if (Ch >= 'A' && Ch <= 'F')
        return Ch - 'A' + 10;
    return -1;
}

static bool HexDecode(char const* Text, std::string& Out) {
    Out.clear();
    if (Text == nullptr)
        return true;
    size_t const Length = strlen(Text);
    if ((Length & 1u) != 0)
        return false;
    Out.reserve(Length / 2);
    for (size_t Index = 0; Index < Length; Index += 2) {
        int const Hi = HexNibble(Text[Index]);
        int const Lo = HexNibble(Text[Index + 1]);
        if (Hi < 0 || Lo < 0)
            return false;
        Out.push_back(static_cast<char>((Hi << 4) | Lo));
    }
    return true;
}

static char const* HardpointText(EquipDesc const& Item) {
    if (Item.Hardpoint == nullptr || Item.Hardpoint[0] == '\0')
        return "-";
    return Item.Hardpoint;
}

static bool NameTaken(unsigned ClientId, char const* Name) {
    std::map<unsigned, LiveCache>::iterator It = GCaches.find(ClientId);
    if (It == GCaches.end())
        return false;
    return FindByName(It->second, Name) != nullptr;
}

void ShipCache_Clear(unsigned ClientId) {
    if (ClientId == 0)
        return;
    GCaches.erase(ClientId);
}

void ShipCache_Install(unsigned ClientId, std::vector<ShipCacheRecord> const& Records,
                       ShipParkingSave const& Parking) {
    if (ClientId == 0)
        return;
    LiveCache& Cache = GCaches[ClientId];
    Cache.Ships = Records;
    Cache.Parking = Parking;
    if (!Parking.Initialized) {
        for (auto const& Ship : Records) if (Ship.Parking && Ship.BaseId) {
            ParkingRules const Rules = RulesFor(Ship.BaseId);
            unsigned Used = UsedAt(Cache, Ship.BaseId);
            unsigned Owned = Used < Rules.Maximum ? Used : Rules.Maximum;
            Cache.Parking.Owned[Ship.BaseId] = Owned > Rules.Initial ? Owned : Rules.Initial;
        }
    }
    Cache.Parking.Initialized = true;
}

bool ShipCache_TryRead(std::vector<ShipCacheRecord>& Records, ShipParkingSave& Parking, INI_Reader& Reader) {
    if (Reader.is_value("ship_parking_version")) {
        Parking.Initialized = true;
        return true;
    }
    if (Reader.is_value("ship_parking_owned")) {
        unsigned const Base = static_cast<unsigned>(Reader.get_value_int(0));
        int const Count = Reader.get_value_int(1);
        if (Base && Count >= 0) Parking.Owned[Base] = static_cast<unsigned>(Count);
        Parking.Initialized = true;
        return true;
    }
    if (Reader.is_value("ship_cache")) {
        unsigned const Id = static_cast<unsigned>(Reader.get_value_int(0));
        char const* Name = Reader.get_value_string(1);
        if (!ValidName(Name))
            return true;
        ShipCacheRecord* Record = FindById(Records, Id);
        if (Record == nullptr) {
            Records.push_back(ShipCacheRecord());
            Record = &Records.back();
        }
        Record->Id = CreateID(Name);
        CopyName(Record->Name, Name);
        Record->ShipArchetype = static_cast<unsigned>(Reader.get_value_int(2));
        Record->RelativeHealth = static_cast<float>(Reader.get_value_float(3));
        Record->BaseId = static_cast<unsigned>(Reader.get_value_int(4));
        Record->Parking = Reader.get_num_parameters() > 5 ? Reader.get_value_int(5) == 1 :
            (_strnicmp(Record->Name, "park_", 5) == 0 && Record->Name[5] != 0 &&
             strspn(Record->Name + 5, "0123456789") == strlen(Record->Name + 5));
        return true;
    }
    if (Reader.is_value("ship_cache_equip")) {
        unsigned const Id = static_cast<unsigned>(Reader.get_value_int(0));
        ShipCacheRecord* Record = FindById(Records, Id);
        if (Record == nullptr) {
            Records.push_back(ShipCacheRecord());
            Record = &Records.back();
            Record->Id = Id;
        }
        EquipDesc Item;
        Item.set_arch_id(static_cast<unsigned>(Reader.get_value_int(1)));
        char const* Hardpoint = Reader.get_value_string(2);
        CacheString Hp;
        Hp.Value = StringAlloc(
            Hardpoint != nullptr && strcmp(Hardpoint, "-") != 0 ? Hardpoint : "", false);
        Item.set_hardpoint(Hp);
        Item.set_status(static_cast<float>(Reader.get_value_float(3)));
        Item.set_count(Reader.get_value_int(4));
        Item.set_equipped(static_cast<unsigned char>(Reader.get_value_int(5)));
        Item.bMission = Reader.get_value_int(6) != 0;
        Item.set_owner(Reader.get_value_int(7));
        Item.set_id(SUBOBJ_ID_NONE);
        Record->Equipment.Items.push_back(Item);
        return true;
    }
    if (Reader.is_value("ship_cache_group")) {
        unsigned const Id = static_cast<unsigned>(Reader.get_value_int(0));
        ShipCacheRecord* Record = FindById(Records, Id);
        if (Record == nullptr) {
            Records.push_back(ShipCacheRecord());
            Record = &Records.back();
            Record->Id = Id;
        }
        CollisionGroupDesc Group = {};
        Group.Id = static_cast<unsigned short>(Reader.get_value_int(1));
        Group.Health = static_cast<float>(Reader.get_value_float(2));
        Record->Groups.push_back(Group);
        return true;
    }
    if (Reader.is_value("ship_cache_wg")) {
        unsigned const Id = static_cast<unsigned>(Reader.get_value_int(0));
        ShipCacheRecord* Record = FindById(Records, Id);
        if (Record == nullptr)
            return true;
        std::string Decoded;
        if (HexDecode(Reader.get_value_string(1), Decoded))
            Record->WeaponGroups = Decoded;
        return true;
    }
    return false;
}

void ShipCache_Write(FILE* Out, unsigned ClientId) {
    if (Out == nullptr || ClientId == 0)
        return;
    std::map<unsigned, LiveCache>::const_iterator It = GCaches.find(ClientId);
    fprintf(Out, "ship_parking_version = 1\n");
    if (It == GCaches.end()) return;
    for (auto const& Entry : It->second.Parking.Owned)
        fprintf(Out, "ship_parking_owned = %u, %u\n", Entry.first, Entry.second);
    for (size_t Index = 0; Index < It->second.Ships.size(); ++Index) {
        ShipCacheRecord const& Record = It->second.Ships[Index];
        fprintf(Out, "ship_cache = %u, %s, %u, %.9g, %u, %u\n", Record.Id, Record.Name,
                Record.ShipArchetype, static_cast<double>(Record.RelativeHealth), Record.BaseId, Record.Parking ? 1u : 0u);
        for (std::list<EquipDesc>::const_iterator Equip = Record.Equipment.Items.begin();
             Equip != Record.Equipment.Items.end(); ++Equip) {
            fprintf(Out, "ship_cache_equip = %u, %u, %s, %.9g, %d, %u, %u, %u\n", Record.Id,
                    Equip->ArchId, HardpointText(*Equip), static_cast<double>(Equip->Health),
                    Equip->Count, static_cast<unsigned>(Equip->bEquipped),
                    Equip->bMission ? 1u : 0u, Equip->Owner);
        }
        for (std::list<CollisionGroupDesc>::const_iterator Group = Record.Groups.begin();
             Group != Record.Groups.end(); ++Group) {
            fprintf(Out, "ship_cache_group = %u, %u, %.9g\n", Record.Id,
                    static_cast<unsigned>(Group->Id), static_cast<double>(Group->Health));
        }
        if (!Record.WeaponGroups.empty()) {
            std::string Hex;
            HexEncode(Record.WeaponGroups, Hex);
            fprintf(Out, "ship_cache_wg = %u, %s\n", Record.Id, Hex.c_str());
        }
    }
}

namespace pub {
namespace Player {

SERVER_API int __cdecl CacheShipAndSetLoadout(const unsigned int& PlayerId, char const* CacheId,
                                              unsigned int ShipArchId,
                                              const EquipDescVector& Loadout) {
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    if (!ValidName(CacheId))
        return -4;
    if (ShipArchId != 0 && Archetype::GetShip(ShipArchId) == nullptr)
        return -4;
    if ((Slot->ship_archetype & 0x3fffffffu) != 0) {
        int const Stored = StoreNamed(*Slot, CacheId);
        if (Stored != 0)
            return Stored;
    }
    return SetShipAndLoadout(PlayerId, ShipArchId, Loadout);
}

SERVER_API int __cdecl RestoreCachedShip(const unsigned int& PlayerId, char const* CacheId) {
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    if (!ValidName(CacheId))
        return -4;
    std::map<unsigned, LiveCache>::iterator It = GCaches.find(Slot->client_id);
    if (It == GCaches.end())
        return -4;
    ShipCacheRecord* Record = FindByName(It->second, CacheId);
    if (Record == nullptr || Record->Parking)
        return -4;
    if (Record->ShipArchetype != 0 && Archetype::GetShip(Record->ShipArchetype) == nullptr)
        return -4;
    size_t const Index = static_cast<size_t>(Record - &It->second.Ships[0]);
    ShipCacheRecord const Held = It->second.Ships[Index];
    It->second.Ships.erase(It->second.Ships.begin() + static_cast<std::ptrdiff_t>(Index));
    InstallRecord(*Slot, Held);
    return 0;
}

} // namespace Player
} // namespace pub

extern "C" {

SERVER_API int __cdecl PlayerShipParking_Status(unsigned PlayerId, ShipParkingStatus* Out) {
    if (!Out) return ParkingInvalid;
    *Out = ShipParkingStatus();
    if (IsMPServer()) return ParkingMultiplayer;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot)) return ParkingBadPlayer;
    if (!Slot->current_base || Slot->ship_object_id) return ParkingWrongBase;
    LiveCache& Cache = GCaches[Slot->client_id];
    ParkingRules const Rules = RulesFor(Slot->current_base);
    Cache.Parking.Owned.emplace(Slot->current_base, Rules.Initial);
    Out->BaseId = Slot->current_base;
    Out->SellerId = Rules.Seller;
    Out->Owned = OwnedAt(Cache, Slot->current_base, Rules);
    Out->Used = UsedAt(Cache, Slot->current_base);
    Out->Maximum = Rules.Maximum;
    Out->Price = Rules.Price;
    unsigned const Capacity = Out->Owned < Out->Maximum ? Out->Owned : Out->Maximum;
    Out->Free = Capacity > Out->Used ? Capacity - Out->Used : 0;
    Out->CanPark = HasMissionShip(Cache) ? ParkingMissionShip :
        !(Slot->ship_archetype & 0x3fffffffu) ? ParkingInvalid :
        Out->Free ? ParkingOk : ParkingFull;
    return ParkingOk;
}

// Sales alone require positive standing. Existing property remains accessible.
SERVER_API int __cdecl PlayerShipParking_CanBuy(unsigned PlayerId) {
    ShipParkingStatus Status;
    int const Result = PlayerShipParking_Status(PlayerId, &Status);
    if (Result) return Result;
    if (!Status.SellerId) return ParkingNoSeller;
    ParkingRules const Rules = RulesFor(Status.BaseId);
    int Rep = -1; float Attitude = 0;
    if (!Rules.ReputationFaction || pub::Player::GetRep(PlayerId, Rep) ||
        pub::Reputation::GetReputation(Rep, Rules.ReputationFaction, Attitude)) return ParkingInvalid;
    return Attitude > 0 ? ParkingOk : ParkingBadReputation;
}

// Expected ownership and price are the confirmed quote. A repeated confirmation is stale.
SERVER_API int __cdecl PlayerShipParking_Buy(unsigned PlayerId, unsigned Base,
                                             unsigned Seller, unsigned ExpectedOwned, int Price) {
    ShipParkingStatus Status;
    int const Result = PlayerShipParking_Status(PlayerId, &Status);
    if (Result) return Result;
    if (Base != Status.BaseId) return ParkingWrongBase;
    if (!Seller || Seller != Status.SellerId) return ParkingNoSeller;
    if (ExpectedOwned != Status.Owned || Price != Status.Price) return ParkingStale;
    int const Eligible = PlayerShipParking_CanBuy(PlayerId);
    if (Eligible) return Eligible;
    if (Status.Owned >= Status.Maximum) return ParkingMaxOwned;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot)) return ParkingBadPlayer;
    if (Slot->cash < Status.Price) return ParkingNoMoney;
    // The map node is allocated by Status before touching the player's cash.
    unsigned& Owned = GCaches[Slot->client_id].Parking.Owned.at(Base);
    if (pub::Player::AdjustCash(PlayerId, -Status.Price) != 0) return ParkingInvalid;
    ++Owned;
    return ParkingOk;
}

SERVER_API int __cdecl PlayerShipCache_Park(unsigned PlayerId) {
    ShipParkingStatus Status;
    int const Result = PlayerShipParking_Status(PlayerId, &Status);
    if (Result) return Result;
    if (Status.CanPark) return Status.CanPark;
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    if (Slot->ship_object_id != 0)
        return -4;
    char Name[64];
    unsigned Number = 1;
    for (;;) {
        sprintf(Name, "park_%u", Number);
        if (!NameTaken(Slot->client_id, Name))
            break;
        ++Number;
    }
    int const Stored = StoreNamed(*Slot, Name, true);
    if (Stored != 0)
        return Stored;
    ClearActiveShip(*Slot);
    return 0;
}

SERVER_API int __cdecl PlayerShipCache_Take(unsigned PlayerId, int Index) {
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    if (Slot->ship_object_id != 0 || Slot->current_base == 0)
        return -4;
    std::map<unsigned, LiveCache>::iterator It = GCaches.find(Slot->client_id);
    if (It == GCaches.end())
        return -4;
    ShipCacheRecord* Record = ParkingRecord(It->second, Index);
    if (!Record) return ParkingInvalid;
    if (Record->BaseId != Slot->current_base) return ParkingWrongBase;
    if (HasMissionShip(It->second)) return ParkingMissionShip;
    ShipCacheRecord const Held = *Record;
    if (Held.ShipArchetype != 0 && Archetype::GetShip(Held.ShipArchetype) == nullptr)
        return -4;
    if ((Slot->ship_archetype & 0x3fffffffu) != 0) {
        ShipCacheRecord Replacement;
        if (!Snapshot(*Slot, Held.Name, Replacement)) return ParkingInvalid;
        Replacement.Parking = true;
        *Record = Replacement; // Exchange in place; a full lot needs no extra slot.
    } else {
        size_t const Position = static_cast<size_t>(Record - It->second.Ships.data());
        It->second.Ships.erase(It->second.Ships.begin() + Position);
    }
    InstallRecord(*Slot, Held);
    return 0;
}

SERVER_API int __cdecl PlayerShipCache_Count(unsigned PlayerId) {
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    std::map<unsigned, LiveCache>::const_iterator It = GCaches.find(Slot->client_id);
    if (It == GCaches.end())
        return 0;
    int Count = 0;
    for (auto const& Ship : It->second.Ships) if (Ship.Parking) ++Count;
    return Count;
}

SERVER_API int __cdecl PlayerShipCache_Get(unsigned PlayerId, int Index, PlayerShipCacheView* Out) {
    if (Out == nullptr)
        return -4;
    memset(Out, 0, sizeof(*Out));
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    auto It = GCaches.find(Slot->client_id);
    ShipCacheRecord const* Found = It == GCaches.end() ? nullptr : ParkingRecord(It->second, Index);
    if (!Found) return ParkingInvalid;
    ShipCacheRecord const& Record = *Found;
    Out->Id = Record.Id;
    CopyName(Out->Name, Record.Name);
    Out->ShipArchetype = Record.ShipArchetype;
    Out->RelativeHealth = Record.RelativeHealth;
    Out->BaseId = Record.BaseId;
    Out->bActive = 0;
    return 0;
}

static ShipCacheRecord const* CacheRecord(unsigned PlayerId, int Index) {
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot) || IsMPServer())
        return nullptr;
    auto It = GCaches.find(Slot->client_id);
    return It == GCaches.end() ? nullptr : ParkingRecord(It->second, Index);
}

SERVER_API int __cdecl PlayerShipCache_EquipCount(unsigned PlayerId, int Index) {
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    ShipCacheRecord const* Record = CacheRecord(PlayerId, Index);
    if (Record == nullptr)
        return -4;
    return static_cast<int>(Record->Equipment.Items.size());
}

SERVER_API int __cdecl PlayerShipCache_EquipAt(unsigned PlayerId, int Index, int Item,
                                               PlayerShipCacheEquip* Out) {
    if (Out == nullptr)
        return -4;
    memset(Out, 0, sizeof(*Out));
    if (IsMPServer())
        return -3;
    PlayerSlot* Slot = nullptr;
    if (!ValidPlayer(PlayerId, Slot))
        return -2;
    ShipCacheRecord const* Record = CacheRecord(PlayerId, Index);
    if (Record == nullptr || Item < 0)
        return -4;
    int At = 0;
    for (std::list<EquipDesc>::const_iterator It = Record->Equipment.Items.begin();
         It != Record->Equipment.Items.end(); ++It, ++At) {
        if (At != Item)
            continue;
        Out->ArchId = It->ArchId;
        CopyName(Out->Hardpoint, It->Hardpoint);
        Out->Health = It->Health;
        Out->Count = It->Count;
        Out->bEquipped = It->bEquipped;
        return 0;
    }
    return -4;
}

} // extern "C"
