#pragma once

// Port-only SP API. All decisions and cash mutations belong to Server.dll.
enum ShipParkingResult {
    ParkingOk = 0, ParkingBadPlayer = -2, ParkingMultiplayer = -3,
    ParkingInvalid = -4, ParkingFull = -5, ParkingNoMoney = -6,
    ParkingMaxOwned = -7, ParkingWrongBase = -8, ParkingStale = -9,
    ParkingNoSeller = -10, ParkingMissionShip = -11, ParkingBadReputation = -12
};

struct ShipParkingStatus {
    unsigned BaseId = 0;
    unsigned SellerId = 0;
    unsigned Owned = 0;
    unsigned Used = 0;
    unsigned Maximum = 0;
    unsigned Free = 0;
    int Price = 0;
    int CanPark = ParkingInvalid;
};

// Resolve these exports dynamically in Content/client, keeping retail imports intact.
using ShipParkingStatusFn = int (__cdecl*)(unsigned, ShipParkingStatus*);
using ShipParkingBuyFn = int (__cdecl*)(unsigned, unsigned, unsigned, unsigned, int);
using ShipParkingCanBuyFn = int (__cdecl*)(unsigned);
