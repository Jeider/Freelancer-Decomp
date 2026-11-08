// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

#include "event_handler.h"
#include "wincontrol_base.h"

#include "common_goods.h"
#include "ship_parking.h"

#include <stdint.h>

class RichTextWin;
class UiScroll;

class NnShipPark : public WinControl, public EventHandler
{
public:
    static int const VisibleRows = 3;

    NnShipPark();
    ~NnShipPark() override;

    bool Create(Win3D* NewParent, void* Data) override;
    void Update() override;
    void Draw() override;
    bool KeyEvent(unsigned Key, unsigned char* Modifiers) override;
    intptr_t SetProperty(int Msg, uintptr_t A, uintptr_t B) override;
    bool OnEvent(unsigned MsgId) override;

private:
    struct Parked
    {
        unsigned Archetype = 0;
        int CacheIndex = -1;
        int NameId = 0;
        int ShipClass = 0;
        char Icon[128] = {};
        char CacheName[64] = {};
    };

    struct GearItem
    {
        unsigned ArchId = 0;
        int NameId = 0;
        int Tab = 0;
        char Hardpoint[64] = {};
        char Icon[128] = {};
        float Health = 1.0f;
        int Count = 1;
        unsigned char bEquipped = 1;
    };

    static int const GearRows = 3;
    static int const GearTabs = 7;
    static int const GearCap = 64;

    void Close();
    void Leave();
    void Rebuild();
    void BindParked();
    void ScrollTo(int First);
    void ShowShip(unsigned Archetype);
    void AddGear(EquipDesc const& Desc);
    void BindGear();
    void ScrollGear(int First);
    void UpdateAction();
    void ParkCurrent();
    void TakeParked(int Index);
    int VisibleCount() const;

    WinControl* CancelButton = nullptr;
    WinControl* LeftIcon = nullptr;
    WinControl* LeftIconFrame = nullptr;
    WinControl* LeftFrame = nullptr;
    WinControl* LeftName = nullptr;
    WinControl* LeftClass = nullptr;
    WinControl* LeftTitle = nullptr;
    WinControl* GearIcons[GearRows] = {};
    WinControl* GearIconFrames[GearRows] = {};
    WinControl* GearFrames[GearRows] = {};
    WinControl* GearNames[GearRows] = {};
    WinControl* GearSubs[GearRows] = {};
    WinControl* GearTabButtons[GearTabs] = {};
    WinControl* CargoFull = nullptr;
    WinControl* CargoEmpty = nullptr;
    WinControl* CargoLabel = nullptr;
    float CargoUsed = 0.0f;
    float CargoHold = 0.0f;
    WinControl* RightTitle = nullptr;
    WinControl* ParkingCapacity = nullptr;
    WinControl* ParkingMessage = nullptr;
    WinControl* ParkingHint = nullptr;
    ShipParkingStatus ParkingStatus;
    WinControl* ParkButton = nullptr;
    WinControl* ParkText = nullptr;
    WinControl* RightIcons[VisibleRows] = {};
    WinControl* RightIconFrames[VisibleRows] = {};
    WinControl* RightFrames[VisibleRows] = {};
    WinControl* RightNames[VisibleRows] = {};
    WinControl* RightClasses[VisibleRows] = {};
    WinControl* ViewName = nullptr;
    WinControl* ViewClass = nullptr;
    RichTextWin* InfoCard = nullptr;
    RichTextWin* GearScrollHost = nullptr;
    class ShipViewControl* ShipView = nullptr;
    UiScroll* ListScroll = nullptr;
    UiScroll* GearScroll = nullptr;
    Parked* ParkedShips = nullptr;
    int ParkedCount = 0;
    int ParkedCap = 0;
    int FirstVisible = 0;
    int RightSelected = -1;
    int Hovered = -1;
    int bLeftSelected = 0;
    int bDragStart = 1;
    int GearFilter = 0;
    int GearFirst = 0;
    int GearCount = 0;
    GearItem Gear[GearCap] = {};
    unsigned CurrentArch = 0;

    NnShipPark(NnShipPark const&) = delete;
    NnShipPark& operator=(NnShipPark const&) = delete;
};

bool ShipParkApiReady();
void ShipParkOpen();
