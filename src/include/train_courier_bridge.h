#pragma once
#include "common_csys.h"

namespace TrainCourier {
// Private in-process SP bridge. No raw pointers cross the boundary. Every
// operation validates the player and object ownership on the server.
enum class Operation : unsigned { Query, Register, Retire, Release, Transfer, ClearTransfer, SuspendCargo, ResumeCargo, Snapshot, Restore, LaunchSolar, IsParkedSolar };
struct CargoSnapshot {
    enum { MaxEquipment=128, MaxGroups=64 };
    struct Equipment {unsigned arch=0;int count=0;float health=0;unsigned mounted=0;char hardpoint[64]{};};
    struct Group {unsigned id=0;float health=0;};
    unsigned arch=0,system=0,equipmentCount=0,groupCount=0,coupled=0;
    int hitpoints=0;
    Vector position{};Matrix orientation{};
    Equipment equipment[MaxEquipment]{};
    Group groups[MaxGroups]{};
};
struct Packet {
    unsigned size=sizeof(Packet),version=1,player=0;
    Operation operation=Operation::Query;
    unsigned trailer=0,system=0,base=0,launchSolar=0;
    Vector position{};
    Matrix orientation{};
    float cleanupDistance=25000.f;
    int result=0,coupled=0,retired=0,inTransit=0;
    CargoSnapshot cargo{};
};
using BridgeFn=int (__cdecl*)(Packet*);
constexpr char BridgeExport[]="TrainCourierBridge";
}
