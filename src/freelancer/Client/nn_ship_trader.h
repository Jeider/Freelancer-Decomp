// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#pragma once

// The ship dealer of a base (retail NN_ShipTrader, freelancer.exe 0x004b7440..0x004b9850).
//
// RTTI .?AVNN_ShipTrader@@ : WinControl, Event::Handler (COL 0x005ebd9c; the IDataViewOwner face
// at +0x7c has COL 0x005ebdb0). operator_new(0x448) (0x004b9738).
// WINFACTORY<NN_ShipTrader> DAT_006722d0 "NN_ShipTrader": static init LAB_004b7410 (ctor
// FUN_004b96b0, atexit LAB_004b7430 -> FUN_00579380); Create FUN_004b9720 (operator_new, the
// WinControl ctor FUN_0059f860 and the three vptrs inlined, the class-name pointer, slot 9; a
// failed Create is followed by the scalar deleting destructor).
//
// vftable 0x005d593c -- WinControl's with these overrides (raw dword dump):
//   0 FUN_004b97e0 scalar deleting dtor (FUN_004b9800), 9 FUN_004b7440 Create, 11 FUN_004b93d0
//   Update, 13 LAB_004b9260 Draw, 20 LAB_004b89a0 KeyEvent, 42 LAB_004b85f0 SetProperty.
// IDataViewOwner face +0x7c: vftable 0x005d5930 (WinControl's LAB_0053aaa0 / FUN_0053e4a0).
// Event::Handler face +0x32c: vftable 0x005d5928, slot 0 LAB_004b9370.
//
// Port: three reusable visible rows show the complete base market (category 3, ship
// packages), each with its icon, name, class and price, and the player's current ship; picking
// one shows it in the 3D view with its three info panes. Offsets below document retail;
// this client-only class now owns a dynamic catalogue and does not retain the retail layout.

#include "event_handler.h"
#include "wincontrol_base.h"

#include <stddef.h>
#include <stdint.h>
#include <vector>

struct GoodInfo;
class RichTextWin;
class ShipViewControl;
class UiScroll;

class NnShipTrader : public WinControl, public EventHandler
{
public:
    static constexpr int VisibleRows = 3;
    // Retail FUN_004b9720 plus the port's catalogue/viewport initialization.
    NnShipTrader();
    // FUN_004b9800 -- the Event::Handler (FUN_00576010) and WinControl (FUN_0059fa50)
    // destructors.
    ~NnShipTrader() override;

    // slot 9 FUN_004b7440 (RET 8) -- the market's ships and every control; Win3D's Create last.
    bool Create(Win3D* NewParent, void* Data) override;
    // slot 11 FUN_004b93d0 -- the children, then RefreshRows when the player's rank level moved.
    void Update() override;
    // slot 13 LAB_004b9260 -- the row frames' layers, the two frame columns, WinControl's Draw and
    // the drag rotation of the 3D ship.
    void Draw() override;
    // slot 20 LAB_004b89a0 (RET 8) -- Escape closes the window; returns false.
    bool KeyEvent(unsigned Key, unsigned char* Modifiers) override;
    // slot 42 LAB_004b85f0 (RET 0xc) -- clicks (0x26 / 0x27), hover (0x2c / 0x2d), close (0x4e).
    intptr_t SetProperty(int Msg, uintptr_t A, uintptr_t B) override;

    // Event::Handler face LAB_004b9370 (RET 4) -- USER_CANCEL (0x10) closes the window.
    bool OnEvent(unsigned MsgId) override;

    // FUN_004b8a00 (RET 4) -- select a row (0..RowCount-1), -2 for the current ship.
    void SelectRow(int Row);
    // FUN_004b93f0 -- every row's rank / reputation status, the rows sorted by status, the row
    // controls refilled.
    void RefreshRows();
    bool ScrollWheel(Win3D* Source, int Wheel);

    WinControl* CancelButton;        // +0x330 "ShipTraderCancelButton"
    WinControl* NameFrames[VisibleRows];       // "ShipTraderShipNameFrame%d"
    WinControl* NameIconFrames[VisibleRows];   // "ShipTraderShipNameIconFrame%d"
    WinControl* ShipMeshes[VisibleRows];       // "ShipTraderShipMesh%d"
    WinControl* ShipNames[VisibleRows];        // "ShipTraderShipName%d"
    WinControl* ShipPrices[VisibleRows];       // "ShipTraderShipPrice%d"
    ShipViewControl* ShipView;       // +0x370 "ShipTrader3DShip"
    RichTextWin* InfoFacts;          // +0x374 "ShipInfoCard_Facts"
    RichTextWin* InfoStats;          // +0x378 "ShipInfoCard_Stats"
    RichTextWin* InfoValues;         // +0x37c "ShipInfoCard_Values"
    WinControl* BuyButton;           // +0x380 "ShipTraderBuyButton"
    WinControl* ViewName;            // +0x384 "ShipTraderViewName"
    WinControl* ViewClass;           // +0x388 "ShipTraderViewClass"
    WinControl* BuyText;             // +0x38c "ShipTraderBuytext"
    WinControl* PlayerCash;          // +0x390 "PlayerCash"
    WinControl* WelcomeText;         // +0x394 "WelcomeText"
    WinControl* WelcomeLine;         // +0x398 "WelcomeLine"
    WinControl* WelcomeHelp;         // +0x39c "WelcomeHelp"
    WinControl* ErrorHelp;           // +0x3a0 "ErrorHelp"
    int PlayerWorth;                 // +0x3a4 credits + loadout resale + ship resale
    int RowCount;                    // Full market count, independent of visible controls.
    int Selected;                    // Catalogue index; -1 none, -2 the current ship
    int Hovered;                     // Visible control index, -1 none
    WinControl* CurrentShipButton;   // +0x3d8 "ShipTraderCurrentShip" (null without a ship)
    WinControl* CurrentShipFrame;    // +0x3dc "ShipTraderCurrentShipFrame"
    WinControl* CurrentShipMesh;     // +0x3e0 "ShipTraderCurrentShipMesh"
    unsigned char bDragStart;        // +0x3e4 the next drag starts a rotation
    unsigned char Pad3e5[3];
    int CurrentShipClass;            // +0x3e8 Archetype::Ship::ShipClass, 0..3
    float BaseFeeling;               // +0x3f8 NnDealer::GetBaseFactionFeeling
    int RankLevel;                   // +0x420 the rank level RefreshRows used
    WinControl* RowClassTexts[VisibleRows];    // "ShipTraderShipClass%d"

private:
    struct Entry
    {
        int Price = 0;
        GoodInfo const* Package = nullptr;
        unsigned GoodId = 0;
        int ShipClass = 0, Status = 0, RequiredLevel = 0, MarketIndex = 0;
        int RepPercent = 0, NameId = 0;
        char const* MeshPath = "";
    };
    std::vector<Entry> Entries;
    UiScroll* ListScroll = nullptr;
    int FirstVisible = 0;
    int VisibleCount() const;
    void BindVisibleRows();
    void ScrollTo(int First);

    // The close sequence of KeyEvent, SetProperty 0x26 / 0x27 / 0x4e and OnEvent: the NavBar
    // (FUN_004424f0(0), FUN_00442850), FUN_0043d2a0 on every child, slot 10, scalar deleting dtor.
    void Close();
    NnShipTrader(NnShipTrader const&) = delete;
    NnShipTrader& operator=(NnShipTrader const&) = delete;
};


// Route only the catalogue area; other panes keep their own wheel behaviour.
bool NnShipTraderWheel(Win3D* Source, int Wheel);
