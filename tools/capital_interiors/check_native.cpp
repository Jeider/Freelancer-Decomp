#include "capital_interiors.h"
#include "common_goods.h"
#include "common_fuses.h"
#include "thorn_iface.h"
#include <windows.h>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>
#include <cstring>

static int Errors = 0;
void __cdecl Log(int Level, char const* Format, ...)
{
    va_list Args;
    va_start(Args, Format);
    vprintf(Format, Args);
    va_end(Args);
    if (Level == 0x100001) ++Errors;
}
void Require(bool Value, char const* What)
{
    if (!Value) { printf("FAIL: %s\n", What); exit(1); }
}
int main(int argc, char** argv)
{
    Require(argc == 3, "data root and staged Server arguments");
    FDUMP = Log;
    Require(LoadLibraryA("ReadFile.dll") != nullptr, "ReadFile");
    Require(LoadLibraryA("x86math.dll") != nullptr, "x86math");
    Require(LoadLibraryA("Thorn.dll") != nullptr, "Thorn");
    DALib::Dacom = DACOM_Acquire();
    DALib::OpenData(argv[1]);
    Require(DALib::Data != nullptr, "data filesystem");
    char ShipFile[1024];
    GetFileSysPath(ShipFile, "test_ships.ini", DALib::Data);
    Require(Archetype::LoadShips(ShipFile, false, nullptr) == 4, "test archetypes loaded");
    unsigned Base = CreateID("om15_01_base");
    unsigned Deck = MakeLocationID(Base, "Deck");
    Require(CapitalInteriors::Active(Base, CreateID("test_train")), "transport uses capital rooms");
    Require(CapitalInteriors::Active(Base, CreateID("test_cruiser")), "cruiser uses capital rooms");
    Require(!CapitalInteriors::Active(Base, CreateID("test_freighter")), "ordinary freighter keeps normal rooms");
    Require(!CapitalInteriors::Active(Base, CreateID("test_fighter")), "fighter keeps normal rooms");
    Require(!CapitalInteriors::Active(CreateID("another_base"), CreateID("test_train")), "unconfigured base unchanged");
    Require(!CapitalInteriors::Active(Base, 0), "missing player ship");
    {
        RoomData Room;
        Room.init(Base, Deck, "Deck", CapitalInteriors::RoomFile(Base, Deck, CreateID("test_train")));
        Room.load();
        printf("Room file: %s; ships=%u hotspots=%u cameras=%u\n", Room.File,
               unsigned(Room.ShipPlacements.size()), unsigned(Room.Hotspots.size()), unsigned(Room.Cameras.size()));
        Require(Room.RoomId == Deck && !strcmp(Room.Nickname, "Deck"), "logical location preserved");
        Require(Room.CharacterPlacements.empty(), "no character placements");
        Require(Room.ShipPlacements.size() == 1, "one player ship");
        Require(Room.ShipPlacements[0]->bIsPlayerShip && !Room.ShipPlacements[0]->bIsForSale, "player, not showroom model");
        Require(!Room.ShipPlacements[0]->LandingScript && !Room.ShipPlacements[0]->LaunchingScript, "no fighter landing/launch scene");
        Require(Room.ShipPlacements[0]->Frame.Pos.x > 100, "external mount");
        Require(Room.find_camera("Camera_0", "test") != nullptr, "main camera");
        Require(Room.find_camera("Camera_0", "test")->Frame.Orient.E[0][2] == -1.0f,
                "camera faces exterior +X (THN column orientation)");
        Require(Room.find_camera("Camera_Trader_Desk", "test") != nullptr, "trader camera");
        Require(Room.find_camera("Camera_Equip_Desk", "test") != nullptr, "equipment camera");
        bool Trader = false, Equipment = false;
        for (auto* Hotspot : Room.Hotspots)
        {
            Require(!Hotspot->RoomSwitch || _stricmp(Hotspot->RoomSwitch, "ShipDealer"), "no ship dealer route");
            Trader |= Hotspot->Behavior == 5;
            Equipment |= Hotspot->Behavior == 8;
        }
        Require(Trader && Equipment, "commodity and equipment services retained");
        Room.unload();
        Room.load();
        Require(Room.ShipPlacements.size() == 1, "room can unload/reload");
    }
    Require(Errors == 0, "native loaders reported no errors");
    Require(LoadLibraryA(argv[2]) != nullptr, "staged Server loads with installed DLLs");
    Require(LoadLibraryA("Content.dll") != nullptr, "installed Content loads with staged Server");
    puts("PASS native THN/RoomData loading, services, ship type selection and room lifecycle");
    DALib::CloseData();
    return 0;
}
