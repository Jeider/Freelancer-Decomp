// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#include "nn_ship_park.h"

#include "character_select_equip.h"
#include "hud_command_dispatch.h"
#include "hud_weapon_groups.h"
#include "ids_rdl.h"
#include "nav_bar.h"
#include "inventory_categories.h"
#include "nn_inventory.h"
#include "player_spawn.h"
#include "rich_text_win.h"
#include "nn_static_control.h"
#include "ship_view_control.h"
#include "input_manager.h"
#include "ui_scroll.h"
#include "win3d.h"
#include "win_factory.h"
#include "wire_controls.h"

#include "common_archetype.h"
#include "common_goods.h"
#include "common_ini.h"
#include "common_misc.h"
#include "common_text.h"
#include "ship_cache.h"
#include "common_universe.h"
#include "ids_strings.h"
#include "port_config.h"

#include <stdio.h>
#include <string.h>
#include <windows.h>

WINFACTORY<NnShipPark> G_NnShipParkFactory("NN_ShipPark");

namespace {

char const kParkMesh[] = "Interface\\NeuroNet\\Inventory\\INV_biginforcard.cmp";
char const kParkCloseMesh[] = "Interface\\NeuroNet\\Inventory\\X.3db";
int const kClassIds[4] = {0x39b, 0x39c, 0x39d, 0x39e};

struct FShipCacheApi {
    ShipParkingStatusFn Status;
    int (__cdecl* Park)(unsigned);
    int (__cdecl* Take)(unsigned, int);
    int (__cdecl* Count)(unsigned);
    int (__cdecl* Get)(unsigned, int, PlayerShipCacheView*);
    int (__cdecl* EquipCount)(unsigned, int);
    int (__cdecl* EquipAt)(unsigned, int, int, PlayerShipCacheEquip*);
};

FShipCacheApi const* CacheApi() {
    static FShipCacheApi Api = {};
    static int Ready = 0;
    if (Ready == 0) {
        Ready = -1;
        HMODULE const Server = GetModuleHandleA("Server.dll");
        if (Server != nullptr) {
            Api.Status = reinterpret_cast<ShipParkingStatusFn>(GetProcAddress(Server, "PlayerShipParking_Status"));
            Api.Park = reinterpret_cast<int (__cdecl*)(unsigned)>(
                GetProcAddress(Server, "PlayerShipCache_Park"));
            Api.Take = reinterpret_cast<int (__cdecl*)(unsigned, int)>(
                GetProcAddress(Server, "PlayerShipCache_Take"));
            Api.Count = reinterpret_cast<int (__cdecl*)(unsigned)>(
                GetProcAddress(Server, "PlayerShipCache_Count"));
            Api.Get = reinterpret_cast<int (__cdecl*)(unsigned, int, PlayerShipCacheView*)>(
                GetProcAddress(Server, "PlayerShipCache_Get"));
            Api.EquipCount = reinterpret_cast<int (__cdecl*)(unsigned, int)>(
                GetProcAddress(Server, "PlayerShipCache_EquipCount"));
            Api.EquipAt = reinterpret_cast<int (__cdecl*)(unsigned, int, int, PlayerShipCacheEquip*)>(
                GetProcAddress(Server, "PlayerShipCache_EquipAt"));
            if (Api.Status != nullptr && Api.Park != nullptr && Api.Take != nullptr && Api.Count != nullptr && Api.Get != nullptr &&
                Api.EquipCount != nullptr && Api.EquipAt != nullptr)
                Ready = 1;
        }
    }
    return Ready == 1 ? &Api : nullptr;
}

uintptr_t PointerArg(void const* Pointer) {
    return reinterpret_cast<uintptr_t>(Pointer);
}

void SetCaption(WinControl* Control, wchar_t const* Text) {
    if (Control != nullptr)
        Control->SetProperty(0x1d, PointerArg(Text), 0);
}

void Hide(WinControl* Control, int bHide) {
    if (Control != nullptr)
        Control->SetProperty(1, static_cast<uintptr_t>(bHide), 0);
}

char const* ShipIcon(unsigned Archetype, char* Out, int OutSize) {
    if (Out == nullptr || OutSize <= 0)
        return "";
    Out[0] = 0;
    GoodInfoList const* const Goods = GoodList_get();
    if (Goods == nullptr)
        return Out;
    GoodInfo const* const Good = Goods->find_by_ship_arch(Archetype);
    if (Good == nullptr || Good->ItemIcon.Value == nullptr)
        return Out;
    strncpy(Out, Good->ItemIcon.Value, static_cast<size_t>(OutSize - 1));
    Out[OutSize - 1] = 0;
    return Out;
}

void SetIcon(WinControl* Icon, char const* Path) {
    if (Icon != nullptr)
        Icon->SetProperty(4, PointerArg(Path != nullptr ? Path : ""), 0);
}

void CachedEquipment(int Index, EquipDescList& Out) {
    FShipCacheApi const* const Api = CacheApi();
    if (Api == nullptr || Index < 0)
        return;
    unsigned const PlayerId = GetPlayerConnectionId();
    int const Count = Api->EquipCount(PlayerId, Index);
    for (int Item = 0; Item < Count; ++Item) {
        PlayerShipCacheEquip Row;
        memset(&Row, 0, sizeof(Row));
        if (Api->EquipAt(PlayerId, Index, Item, &Row) != 0 || Row.ArchId == 0)
            continue;
        EquipDesc Desc;
        Desc.set_arch_id(Row.ArchId);
        Desc.set_count(Row.Count > 0 ? Row.Count : 1);
        Desc.set_status(Row.Health);
        Desc.set_equipped(Row.bEquipped);
        if (Row.Hardpoint[0] != 0 && strcmp(Row.Hardpoint, "-") != 0) {
            CacheString Hp;
            Hp.Value = StringAlloc(Row.Hardpoint, false);
            Desc.set_hardpoint(Hp);
        }
        Out.Items.push_back(Desc);
    }
}

void FillShipCard(RichTextWin* Pane, Archetype::Ship const* Ship) {
    if (Pane == nullptr)
        return;
    RenderDisplayList Text;
    {
        StyleNode Style(0x9ca4);
        RdlAppendNode(Text, Style.Clone());
    }
    // Complete facts and description cards only. IdsInfo2/3 are the separate
    // label/value columns used by the trader's comparison layout.
    int const Ids[2] = {Ship != nullptr ? Ship->IdsInfo1 : 0, Ship != nullptr ? Ship->IdsInfo : 0};
    for (int Index = 0; Index < 2; ++Index) {
        if (Ids[Index] != 0)
            LoadIdsIntoRdl(static_cast<unsigned>(Ids[Index]), Text);
    }
    Pane->SetScrollOrigin(0, 0);
    Pane->ClearContent();
    Pane->AppendContent(Text);
    Pane->SetAutoScrollbar(true);
}

int GearTabOf(unsigned ArchId) {
    Archetype::Equipment* const Arch = Archetype::GetEquipment(ArchId);
    if (Arch == nullptr)
        return 2;
    int const Mode = NnItemFilterMode(ArchId);
    if (Mode == 0)
        return 0;
    if (Mode == 1)
        return 1;
    if (Mode == InventoryCategories::Boosters)
        return 4;
    if (Mode == InventoryCategories::Keys)
        return 5;
    if (Mode == 3)
        return 3;
    if (Mode == 4)
        return 6;
    return 2;
}

} // namespace

bool ShipParkApiReady() {
    return SinglePlayer() && CacheApi() != nullptr;
}

void ShipParkOpen() {
    NavBarOpenParking();
}

NnShipPark::NnShipPark() {}

NnShipPark::~NnShipPark() {
    delete[] ParkedShips;
}

void NnShipPark::Close() {
    delete[] ParkedShips;
    ParkedShips = nullptr;
    ParkedCount = 0;
    ParkedCap = 0;
    Win3D* Child = ChildHead;
    while (Child != nullptr) {
        Win3D* const Next = Child->NextSibling;
        Win3DDeleteTree(Child);
        Child = Next;
    }
    Destroy();
    delete this;
}

void NnShipPark::Leave() {
    NavBarCloseService(false);
    Close();
}

int NnShipPark::VisibleCount() const {
    int const Left = ParkedCount - FirstVisible;
    if (Left < 0)
        return 0;
    return Left < VisibleRows ? Left : VisibleRows;
}

void NnShipPark::AddGear(EquipDesc const& Desc) {
    if (GearCount >= GearCap || Desc.ArchId == 0)
        return;
    if (Archetype::GetEquipment(Desc.ArchId) == nullptr || NnItemFilterMode(Desc.ArchId) == 5)
        return;
    GearItem& Item = Gear[GearCount++];
    Item = GearItem();
    Item.ArchId = Desc.ArchId;
    Item.Tab = GearTabOf(Desc.ArchId);
    Item.Health = Desc.Health;
    Item.Count = Desc.Count;
    Item.bEquipped = Desc.bEquipped;
    if (Desc.Hardpoint != nullptr)
        strncpy(Item.Hardpoint, Desc.Hardpoint, 63);
    unsigned const GoodId = Arch2Good(Desc.ArchId);
    GoodInfo const* const Good = GoodId != 0 ? GoodList::find_by_id(GoodId) : nullptr;
    if (Good != nullptr) {
        if (Good->ItemIcon.Value != nullptr)
            strncpy(Item.Icon, Good->ItemIcon.Value, 127);
        Item.NameId = Good->IdsName;
    }
}

void NnShipPark::ScrollGear(int First) {
    if (First < 0)
        First = 0;
    int Matched = 0;
    for (int Index = 0; Index < GearCount; ++Index)
        if (Gear[Index].Tab == GearFilter)
            ++Matched;
    int const Max = Matched > GearRows ? Matched - GearRows : 0;
    if (First > Max)
        First = Max;
    GearFirst = First;
    BindGear();
}

void NnShipPark::BindGear() {
    int const bShow = (bLeftSelected != 0 && CurrentArch != 0) ||
                      (RightSelected >= 0 && RightSelected < ParkedCount);
    if (bShow == 0) {
        for (int Row = 0; Row < GearRows; ++Row) {
            Hide(GearIcons[Row], 1);
            Hide(GearIconFrames[Row], 1);
            Hide(GearFrames[Row], 1);
            Hide(GearNames[Row], 1);
            Hide(GearSubs[Row], 1);
        }
        for (int Tab = 0; Tab < GearTabs; ++Tab)
            Hide(GearTabButtons[Tab], 1);
        Hide(CargoFull, 1);
        Hide(CargoEmpty, 1);
        Hide(CargoLabel, 1);
        Hide(static_cast<WinControl*>(GearScrollHost), 1);
        CargoUsed = 0.0f;
        CargoHold = 0.0f;
        if (GearScroll != nullptr)
            GearScroll->SetProperty(1, 1, 0);
        return;
    }
    for (int Tab = 0; Tab < GearTabs; ++Tab)
        Hide(GearTabButtons[Tab], 0);
    Hide(static_cast<WinControl*>(GearScrollHost), 0);
    Hide(CargoFull, 0);
    Hide(CargoEmpty, 0);
    Hide(CargoLabel, 1);
    int Matched = 0;
    int Shown = 0;
    for (int Index = 0; Index < GearCount; ++Index) {
        if (Gear[Index].Tab != GearFilter)
            continue;
        if (Matched++ < GearFirst)
            continue;
        if (Shown >= GearRows)
            continue;
        Hide(GearIcons[Shown], 0);
        Hide(GearIconFrames[Shown], 0);
        Hide(GearFrames[Shown], 0);
        Hide(GearNames[Shown], 0);
        Hide(GearSubs[Shown], 0);
        SetIcon(GearIcons[Shown], Gear[Index].Icon);
        if (GearNames[Shown] != nullptr)
            GearNames[Shown]->SetProperty(0x1e, static_cast<uintptr_t>(Gear[Index].NameId), 0);
        if (GearSubs[Shown] != nullptr) {
            wchar_t CountText[32];
            if (Gear[Index].Count > 1)
                swprintf(CountText, 32, L"x%d", Gear[Index].Count);
            else
                CountText[0] = 0;
            SetCaption(GearSubs[Shown], CountText);
        }
        ++Shown;
    }
    for (int Row = Shown; Row < GearRows; ++Row) {
        Hide(GearIcons[Row], 1);
        Hide(GearIconFrames[Row], 1);
        Hide(GearFrames[Row], 1);
        Hide(GearNames[Row], 1);
        Hide(GearSubs[Row], 1);
    }
    for (int Tab = 0; Tab < GearTabs; ++Tab)
        if (GearTabButtons[Tab] != nullptr)
            GearTabButtons[Tab]->SetProperty(0xc, Tab == GearFilter ? 1 : 0, 0);
    if (GearScroll != nullptr) {
        GearScroll->SetProperty(0x37, 0, static_cast<uintptr_t>(GearCount + GearRows + 1));
        GearScroll->Flags = static_cast<unsigned char>(GearScroll->Flags | 3);
        GearScroll->SetProperty(1, 0, 0);
    }
    unsigned const Hull = bLeftSelected != 0 ? CurrentArch :
                          (RightSelected >= 0 && RightSelected < ParkedCount
                               ? ParkedShips[RightSelected].Archetype
                               : 0);
    Archetype::Ship const* const Ship = Archetype::GetShip(Hull);
    CargoHold = Ship != nullptr ? Ship->HoldSize : 0.0f;
    if (CargoUsed < 0.0f)
        CargoUsed = 0.0f;
    if (CargoHold > 0.0f && CargoUsed > CargoHold)
        CargoUsed = CargoHold;
    Hide(CargoEmpty, Hull == 0 ? 1 : 0);
    Hide(CargoLabel, 1);
    float Fill = CargoHold > 0.0f ? CargoUsed / CargoHold : 0.0f;
    if (Fill < 0.0f)
        Fill = 0.0f;
    if (Fill > 1.0f)
        Fill = 1.0f;
    Hide(CargoFull, Hull == 0 || Fill <= 0.0f ? 1 : 0);
}

void NnShipPark::ShowShip(unsigned Archetype) {
    Archetype::Ship const* const Ship = Archetype::GetShip(Archetype);
    GearCount = 0;
    GearFirst = 0;
    EquipDescList Mounted;
    if (bLeftSelected != 0) {
        for (std::list<EquipDesc>::const_iterator It = GetPlayerEquipDescListRetail().Items.begin();
             It != GetPlayerEquipDescListRetail().Items.end(); ++It) {
            AddGear(*It);
            Mounted.Items.push_back(*It);
        }
    } else if (RightSelected >= 0) {
        CachedEquipment(ParkedShips[RightSelected].CacheIndex, Mounted);
        for (std::list<EquipDesc>::const_iterator It = Mounted.Items.begin(); It != Mounted.Items.end();
             ++It)
            AddGear(*It);
    }
    CargoUsed = Mounted.get_cargo_space_occupied();
    if (ShipView != nullptr) {
        if (Ship == nullptr) {
            ShipView->SetProperty(1, 1, 0);
        } else {
            ShipView->LoadShip(&Ship->Nickname, true, false);
            ShipView->LoadEquipment(&Mounted);
            float const Ypr[3] = {162.581f, -71.6442f, 0.0f};
            ShipView->SetObjectYpr(Ypr);
            ShipView->SetDragYpr(Ypr);
            ShipView->SetProperty(1, 0, 0);
        }
    }
    if (Ship != nullptr) {
        if (ViewName != nullptr)
            ViewName->SetProperty(0x1e, static_cast<uintptr_t>(Ship->IdsName), 0);
        int const Class = Ship->ShipClass >= 0 && Ship->ShipClass < 4 ? Ship->ShipClass : 0;
        if (ViewClass != nullptr)
            ViewClass->SetProperty(0x1e, static_cast<uintptr_t>(kClassIds[Class]), 0);
        FillShipCard(InfoCard, Ship);
    }
    if (GearScroll != nullptr)
        GearScroll->SetProperty(0x38, 0, 0);
    BindGear();
}

void NnShipPark::UpdateAction() {
    int const bPark = bLeftSelected != 0 && CurrentArch != 0;
    int const bParked = RightSelected >= 0 && RightSelected < ParkedCount;
    int const bUse = bParked;
    int const bShow = bPark || bParked;
    Hide(ParkButton, (bPark || bUse) ? 0 : 1);
    Hide(ParkText, (bPark || bUse) ? 0 : 1);
    bool const English = _stricmp(PortLanguage(), "en") == 0;
    SetCaption(ParkText, bUse ? (CurrentArch ? (English ? L"SWITCH SHIP" : L"\u0421\u041c\u0415\u041d\u0418\u0422\u042c \u041a\u041e\u0420\u0410\u0411\u041b\u042c") :
        (English ? L"USE" : L"\u0418\u0421\u041f\u041e\u041b\u042c\u0417\u041e\u0412\u0410\u0422\u042c")) :
        (English ? L"PARK" : L"\u041f\u0420\u0418\u041f\u0410\u0420\u041a\u041e\u0412\u0410\u0422\u042c"));
    bool const Blocked = (bPark && ParkingStatus.CanPark != ParkingOk) ||
        (bUse && ParkingStatus.CanPark == ParkingMissionShip);
    if (ParkButton) ParkButton->SetProperty(2, Blocked ? 1 : 0, 0);
    Hide(ViewName, bShow ? 0 : 1);
    Hide(ViewClass, bShow ? 0 : 1);
    Hide(ShipView, bShow ? 0 : 1);
    if (LeftIconFrame != nullptr)
        LeftIconFrame->SetProperty(0xc, bLeftSelected != 0 ? 1 : 0, 0);
    if (LeftFrame != nullptr)
        LeftFrame->SetProperty(0xc, bLeftSelected != 0 ? 1 : 0, 0);
}

void NnShipPark::BindParked() {
    int const Shown = VisibleCount();
    for (int Row = 0; Row < VisibleRows; ++Row) {
        int const bHide = Row >= Shown ? 1 : 0;
        Hide(RightIcons[Row], bHide);
        Hide(RightIconFrames[Row], bHide);
        Hide(RightFrames[Row], bHide);
        Hide(RightNames[Row], bHide);
        Hide(RightClasses[Row], bHide);
        if (bHide != 0)
            continue;
        Parked const& Item = ParkedShips[FirstVisible + Row];
        SetIcon(RightIcons[Row], Item.Icon);
        if (RightNames[Row] != nullptr)
            RightNames[Row]->SetProperty(0x1e, static_cast<uintptr_t>(Item.NameId), 0);
        int const Class = Item.ShipClass >= 0 && Item.ShipClass < 4 ? Item.ShipClass : 0;
        if (RightClasses[Row] != nullptr)
            RightClasses[Row]->SetProperty(0x1e, static_cast<uintptr_t>(kClassIds[Class]), 0);
        int const bChecked = FirstVisible + Row == RightSelected ? 1 : 0;
        if (RightIconFrames[Row] != nullptr)
            RightIconFrames[Row]->SetProperty(0xc, static_cast<uintptr_t>(bChecked), 0);
        if (RightFrames[Row] != nullptr)
            RightFrames[Row]->SetProperty(0xc, static_cast<uintptr_t>(bChecked), 0);
    }
}

void NnShipPark::ScrollTo(int First) {
    if (First < 0)
        First = 0;
    int const Max = ParkedCount > VisibleRows ? ParkedCount - VisibleRows : 0;
    if (First > Max)
        First = Max;
    FirstVisible = First;
    BindParked();
}

void NnShipPark::Rebuild() {
    FShipCacheApi const* const Api = CacheApi();
    unsigned const PlayerId = GetPlayerConnectionId();
    ParkingStatus = ShipParkingStatus();
    bool const HaveStatus = Api && Api->Status(PlayerId, &ParkingStatus) == ParkingOk;
    bool const English = _stricmp(PortLanguage(), "en") == 0;
    wchar_t Caption[256] = {};
    if (auto const* Base = Universe::get_base(ParkingStatus.BaseId))
        GetIdsStringWWithRawFallback(Base->GetStridName(), Caption, 256);
    SetCaption(RightTitle, Caption);
    unsigned const Remaining = ParkingStatus.Maximum > ParkingStatus.Owned ? ParkingStatus.Maximum - ParkingStatus.Owned : 0;
    swprintf(Caption, 256, English ? L"Occupied: %u / %u | Buy: %u" :
        L"\u0417\u0430\u043d\u044f\u0442\u043e: %u / %u | \u041a\u0443\u043f\u0438\u0442\u044c: %u", ParkingStatus.Used, ParkingStatus.Owned, Remaining);
    SetCaption(ParkingCapacity, Caption);
    wchar_t const* Message = L"";
    wchar_t const* Hint = L"";
    if (!HaveStatus) Message = English ? L"Parking unavailable" : L"\u0421\u0442\u043e\u044f\u043d\u043a\u0430 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430";
    else if (ParkingStatus.CanPark == ParkingMissionShip) Message = English ? L"Finish the temporary ship assignment first" : L"\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0432\u0435\u0440\u043d\u0438\u0442\u0435 \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0439 \u043a\u043e\u0440\u0430\u0431\u043b\u044c";
    else if (!ParkingStatus.Free) {
        Message = English ? L"No free slots." : L"\u041d\u0435\u0442 \u0441\u0432\u043e\u0431\u043e\u0434\u043d\u044b\u0445 \u043c\u0435\u0441\u0442.";
        if (Remaining && ParkingStatus.SellerId) Hint = English ? L"Buy a slot from the manager in the bar." :
            L"\u041a\u0443\u043f\u0438\u0442\u0435 \u043c\u0435\u0441\u0442\u043e \u0443 \u0441\u043c\u043e\u0442\u0440\u0438\u0442\u0435\u043b\u044f \u0432 \u0431\u0430\u0440\u0435.";
        else Hint = English ? L"You can switch parked ships." :
            L"\u041c\u043e\u0436\u043d\u043e \u0441\u043c\u0435\u043d\u0438\u0442\u044c \u043a\u043e\u0440\u0430\u0431\u043b\u044c.";
    }
    SetCaption(ParkingMessage, Message);
    SetCaption(ParkingHint, Hint);
    int Cached = Api != nullptr ? Api->Count(PlayerId) : 0;
    if (Cached < 0)
        Cached = 0;
    if (Cached > ParkedCap) {
        Parked* const Grown = new Parked[static_cast<size_t>(Cached)];
        delete[] ParkedShips;
        ParkedShips = Grown;
        ParkedCap = Cached;
    }
    ParkedCount = 0;
    for (int Index = 0; Index < Cached; ++Index) {
        PlayerShipCacheView View;
        memset(&View, 0, sizeof(View));
        if (Api->Get(PlayerId, Index, &View) != 0)
            continue;
        if (!HaveStatus || View.BaseId != ParkingStatus.BaseId) continue;
        Parked& Row = ParkedShips[ParkedCount++];
        Row = Parked();
        Row.CacheIndex = Index;
        Row.Archetype = View.ShipArchetype;
        strncpy(Row.CacheName, View.Name, 63);
        ShipIcon(View.ShipArchetype, Row.Icon, static_cast<int>(sizeof(Row.Icon)));
        Archetype::Ship const* const Ship = Archetype::GetShip(View.ShipArchetype);
        if (Ship != nullptr) {
            Row.NameId = Ship->IdsName;
            Row.ShipClass = Ship->ShipClass;
        }
    }
    CurrentArch = GetPlayerShipArchetypeIdRetail();
    int const HasCurrent = CurrentArch != 0 ? 0 : 1;
    Hide(LeftIcon, HasCurrent);
    Hide(LeftIconFrame, HasCurrent);
    Hide(LeftFrame, HasCurrent);
    Hide(LeftName, HasCurrent);
    Hide(LeftClass, HasCurrent);
    if (CurrentArch != 0) {
        char Icon[128];
        SetIcon(LeftIcon, ShipIcon(CurrentArch, Icon, static_cast<int>(sizeof(Icon))));
        Archetype::Ship const* const Ship = Archetype::GetShip(CurrentArch);
        if (Ship != nullptr) {
            if (LeftName != nullptr)
                LeftName->SetProperty(0x1e, static_cast<uintptr_t>(Ship->IdsName), 0);
            int const Class = Ship->ShipClass >= 0 && Ship->ShipClass < 4 ? Ship->ShipClass : 0;
            if (LeftClass != nullptr)
                LeftClass->SetProperty(0x1e, static_cast<uintptr_t>(kClassIds[Class]), 0);
        }
    } else {
        bLeftSelected = 0;
    }
    if (RightSelected >= ParkedCount)
        RightSelected = -1;
    if (ListScroll != nullptr)
        ListScroll->SetProperty(1, ParkedCount <= VisibleRows ? 1 : 0, 0);
    ScrollTo(FirstVisible);
    UpdateAction();
    if (bLeftSelected != 0 && CurrentArch != 0)
        ShowShip(CurrentArch);
    else if (RightSelected >= 0)
        ShowShip(ParkedShips[RightSelected].Archetype);
    else
        BindGear();
}

void NnShipPark::ParkCurrent() {
    FShipCacheApi const* const Api = CacheApi();
    if (Api == nullptr || CurrentArch == 0 || bLeftSelected == 0)
        return;
    if (Api->Park(GetPlayerConnectionId()) != 0) { Rebuild(); return; }
    SetPlayerShipArchetypeIdRetail(0);
    EquipDescList Empty;
    SyncPlayerEquipDescListRetail(Empty);
    G_WeaponGroups.Clear();
    bLeftSelected = 0;
    RightSelected = -1;
    Rebuild();
    CurrentArch = 0;
    bLeftSelected = 0;
    Hide(LeftIcon, 1);
    Hide(LeftIconFrame, 1);
    Hide(LeftFrame, 1);
    Hide(LeftName, 1);
    Hide(LeftClass, 1);
    if (ParkedCount <= 0)
        return;
    RightSelected = ParkedCount - 1;
    ScrollTo(RightSelected);
    ShowShip(ParkedShips[RightSelected].Archetype);
    UpdateAction();
}

void NnShipPark::TakeParked(int Index) {
    FShipCacheApi const* const Api = CacheApi();
    if (Api == nullptr || Index < 0 || Index >= ParkedCount)
        return;
    unsigned const Taken = ParkedShips[Index].Archetype;
    if (Taken == 0)
        return;
    EquipDescList TakenGear;
    CachedEquipment(ParkedShips[Index].CacheIndex, TakenGear);
    if (Api->Take(GetPlayerConnectionId(), ParkedShips[Index].CacheIndex) != 0) { Rebuild(); return; }
    SyncPlayerEquipDescListRetail(TakenGear);
    SetPlayerShipArchetypeIdRetail(Taken);
    bLeftSelected = 1;
    RightSelected = -1;
    Rebuild();
    CurrentArch = Taken;
    bLeftSelected = 1;
    RightSelected = -1;
    Hide(LeftIcon, 0);
    Hide(LeftIconFrame, 0);
    Hide(LeftFrame, 0);
    Hide(LeftName, 0);
    Hide(LeftClass, 0);
    char Icon[128];
    SetIcon(LeftIcon, ShipIcon(Taken, Icon, static_cast<int>(sizeof(Icon))));
    Archetype::Ship const* const Ship = Archetype::GetShip(Taken);
    if (Ship != nullptr) {
        if (LeftName != nullptr)
            LeftName->SetProperty(0x1e, static_cast<uintptr_t>(Ship->IdsName), 0);
        int const Class = Ship->ShipClass >= 0 && Ship->ShipClass < 4 ? Ship->ShipClass : 0;
        if (LeftClass != nullptr)
            LeftClass->SetProperty(0x1e, static_cast<uintptr_t>(kClassIds[Class]), 0);
    }
    BindParked();
    ShowShip(Taken);
    UpdateAction();
}

bool NnShipPark::Create(Win3D* NewParent, void* Data) {
    SetMesh(kParkMesh, 0);
    HalfExtents[0] = 0.66f;
    HalfExtents[1] = 0.64f;
    HalfExtents[2] = 0.0f;
    HitOffset[0] = 0.64f;
    HitOffset[1] = -0.27f;
    HitOffset[2] = 0.0f;

    {
        float const Position[3] = {1.25f, -0.04f, 0.0f};
        float const Half[3] = {0.02f, 0.02f, 0.0f};
        CancelButton = CreateButtonControl("ShipParkCancelButton", kParkCloseMesh, nullptr,
                                           "ui_select_item", nullptr, Position, nullptr, Half, 0, 0,
                                           0, 0, 0x2148, 0, 0);
    }
    {
        float const Position[3] = {0.235f, -0.085f, 0.0f};
        LeftTitle = CreateTextControl("ShipParkLeftTitle", "PageHeader", Position, nullptr, 0.41f,
                                      0.03f, 1.6f, 0, 1, 0, 0);
        SetCaption(LeftTitle, L"\x0422\x0415\x041A\x0423\x0429\x0418\x0419");
    }
    {
        float const Position[3] = {-0.557f, 0.13f, -1.288f};
        float const Half[3] = {0.035f, 0.041f, 0.0f};
        float const Zero[3] = {0.0f, 0.0f, 0.0f};
        LeftIcon = CreateStaticControl("ShipParkCurrentIcon", "", Position, nullptr, Half, 0, 0, 0,
                                       1, 1, 1, 1, 0x50, 0, 0, Zero);
        if (LeftIcon != nullptr)
            LeftIcon->Flags = static_cast<unsigned char>(LeftIcon->Flags & 0xf7);
    }
    {
        float const Position[3] = {0.082f, -0.2f, 0.0f};
        float const Half[3] = {0.035f, 0.0335f, 0.0f};
        LeftIconFrame = CreateWireButtonControl("ShipParkCurrentIconFrame", "ui_item_select",
                                                Position, Half, 0, 0, 0, 0, 0);
    }
    {
        float const Position[3] = {0.264f, -0.2f, 0.0f};
        float const Half[3] = {0.138f, 0.034f, 0.0f};
        LeftFrame = CreateWireButtonControl("ShipParkCurrentFrame", "ui_item_select", Position, Half,
                                            0, 0, 0, 0, 0);
    }
    {
        float const Position[3] = {0.135f, -0.167f, 0.0f};
        LeftName = CreateTextControl("ShipParkCurrentName", "ItemName", Position, nullptr, 0.26f,
                                     0.03f, 1.6f, 0, 0, 0, 1);
    }
    {
        float const Position[3] = {0.135f, -0.198f, 0.0f};
        LeftClass = CreateTextControl("ShipParkCurrentClass", "ItemName", Position, nullptr, 0.146f,
                                      0.03f, 1.6f, 0, 0, 0, 1);
    }
    {
        float const Base[3] = {0.055f, -0.469f, 0.0f};
        for (int Row = 0; Row < GearRows; ++Row) {
            double const RowOffset = static_cast<double>(Row) * static_cast<double>(-0.068f);
            float const RowY = static_cast<float>(RowOffset);
            float const ButtonY = static_cast<float>(RowOffset - 0.131);
            char Name[64];
            sprintf(Name, "ShipParkItemButton%d", Row + 1);
            {
                float const Position[3] = {Base[0] + 0.067f, Base[1] + ButtonY, 0.0f};
                float const Half[3] = {0.035f, 0.0335f, 0.0f};
                GearIconFrames[Row] =
                    CreateWireButtonControl(Name, "ui_item_select", Position, Half, 0, 0, 0, 0, 0);
            }
            sprintf(Name, "ShipParkItemView%d", Row + 1);
            {
                float const Position[3] = {Base[0] + 0.248f, Base[1] + ButtonY, 0.0f};
                float const Half[3] = {0.138f, 0.034f, 0.0f};
                GearFrames[Row] =
                    CreateWireButtonControl(Name, "ui_item_select", Position, Half, 0, 0, 0, 0, 0);
            }
            sprintf(Name, "ShipParkItemMesh%d", Row + 1);
            {
                float const FrameX = Base[0] + 0.067f;
                float const FrameY = Base[1] + ButtonY;
                float const Position[3] = {FrameX - 0.639f, FrameY + 0.33f, -1.288f};
                float const Half[3] = {0.035f, 0.041f, 0.0f};
                float const Zero[3] = {};
                GearIcons[Row] = CreateStaticControl(Name, "", Position, nullptr, Half, 0, 0, 0, 1, 1,
                                                     1, 1, 0x50, 0, 0, Zero);
                if (GearIcons[Row] != nullptr)
                    GearIcons[Row]->Flags = static_cast<unsigned char>(GearIcons[Row]->Flags & 0xf7);
            }
            sprintf(Name, "ShipParkItemName%d", Row + 1);
            {
                float const Position[3] = {
                    Base[0] + 0.256f,
                    static_cast<float>(static_cast<double>(RowY) - 0.118 + static_cast<double>(Base[1])),
                    0.0f};
                GearNames[Row] = CreateTextControl(Name, "ItemName", Position, nullptr, 0.27f, 0.04f,
                                                   1.5f, 0, 0, 0, 0);
            }
            sprintf(Name, "ShipParkItemQuantity%d", Row + 1);
            {
                float const Position[3] = {
                    Base[0] + 0.171f,
                    static_cast<float>(static_cast<double>(RowY) - 0.148 + static_cast<double>(Base[1])),
                    0.0f};
                GearSubs[Row] = CreateTextControl(Name, "ItemName", Position, nullptr, 0.1f, 0.04f, 1.5f,
                                                  0, 0, 0, 0);
            }
        }
        char const* const Icons[GearTabs] = {
            "Interface\\NeuroNet\\Inventory\\weaponsicon.3db",
            "Interface\\NeuroNet\\Inventory\\ammo.3db",
            "Interface\\NeuroNet\\Inventory\\equipmenticon.3db",
            "Interface\\NeuroNet\\Inventory\\cargobay.3db",
            "Interface\\NeuroNet\\Inventory\\boosters.3db",
            "Interface\\NeuroNet\\Inventory\\keys.3db",
            "Interface\\NeuroNet\\Inventory\\commodities.3db",
        };
        unsigned const Tips[GearTabs] = {0x2135, 0x214a, 0x2142, 0x2141, InventoryCategories::BoostersName,
                                         InventoryCategories::KeysName, 0x2138};
        float const FilterHalf[3] = {0.017f, 0.017f, 0.0f};
        float const FilterY = -0.528f;
        for (int Tab = 0; Tab < GearTabs; ++Tab) {
            char Name[32];
            sprintf(Name, "ShipParkFilter%d", Tab);
            float const Position[3] = {0.10f + Tab * 0.034f, FilterY, 0.0f};
            GearTabButtons[Tab] = CreateButtonControl(Name, Icons[Tab], nullptr, "ui_filter_select",
                                                      nullptr, Position, nullptr, FilterHalf, 0, 1, 0,
                                                      0, Tips[Tab], 0, 0);
        }
        {
            float const BarPos[3] = {0.38f - 0.64f, -0.528f + 0.33f, -1.288f};
            float const BarHalf[3] = {0.16f, 0.04f, 0.0f};
            float const Zero[3] = {0.0f, 0.0f, 0.0f};
            CargoEmpty = CreateStaticControl("ShipParkCargoEmpty",
                                             "Interface\\NeuroNet\\Inventory\\cargoempty.3db", BarPos,
                                             nullptr, BarHalf, 0, 0, 0, 1, 0, 1, 1, 0x50, 0, 0, Zero);
            CargoFull = CreateStaticControl("ShipParkCargoFull",
                                            "Interface\\NeuroNet\\Inventory\\cargofull.3db", BarPos,
                                            nullptr, BarHalf, 0, 0, 0, 1, 0, 1, 1, 0x50, 0, 0, Zero);
            if (CargoEmpty != nullptr)
                CargoEmpty->Flags = static_cast<unsigned char>(CargoEmpty->Flags & 0xf7);
            if (CargoFull != nullptr) {
                CargoFull->Flags = static_cast<unsigned char>(CargoFull->Flags & 0xf7);
                CargoFull->ToolTipIds = 0x43b;
            }
        }
        Hide(CargoLabel, 1);
        float const Host[3] = {-0.08f, -0.16f, -1.0f};
        GearScrollHost = CreateRichTextWin("ShipParkGearScrollHost", 0.02f, 0.22f, Host, true);
        if (GearScrollHost != nullptr) {
            RenderDisplayList Lines;
            {
                StyleNode Style(0x9ca4);
                RdlAppendNode(Lines, Style.Clone());
            }
            wchar_t const Breaks[] = L"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n";
            AppendTextMaybeXmlRdl(Breaks, static_cast<unsigned>(wcslen(Breaks)), Lines, false);
            GearScrollHost->ClearContent();
            GearScrollHost->AppendContent(Lines);
            GearScrollHost->SetAutoScrollbar(true);
        }
    }
    {
        float const Position[3] = {1.07f, -0.085f, 0.0f};
        RightTitle = CreateTextControl("ShipParkRightTitle", "PageHeader", Position, nullptr, 0.422f,
                                       0.03f, 1.6f, 0, 1, 0, 0);
        SetCaption(RightTitle, L"\x041D\x0410 \x041F\x0410\x0420\x041A\x041E\x0412\x041A\x0415");
        float const CapacityPos[3] = {1.07f, -0.123f, 0.0f};
        ParkingCapacity = CreateTextControl("ShipParkCapacity", "ItemName", CapacityPos, nullptr, 0.422f,
                                           0.03f, 1.6f, 0, 1, 0, 0);
        float const MessagePos[3] = {1.07f, -0.385f, 0.0f};
        ParkingMessage = CreateTextControl("ShipParkMessage", "ItemName", MessagePos, nullptr, 0.422f,
                                          0.03f, 1.6f, 0, 1, 0, 0);
        float const HintPos[3] = {1.07f, -0.417f, 0.0f};
        ParkingHint = CreateTextControl("ShipParkHint", "ItemName", HintPos, nullptr, 0.422f,
                                       0.03f, 1.6f, 0, 1, 0, 0);
    }
    for (int Row = 0; Row < VisibleRows; ++Row) {
        float const RowStep = static_cast<float>(static_cast<double>(Row) * 0.068);
        float const FrameY = static_cast<float>(-0.2 - static_cast<double>(RowStep));
        char Name[64];
        {
            sprintf(Name, "ShipParkRightIcon%d", Row);
            float const Position[3] = {0.277f, 0.13f - Row * 0.068f, -1.288f};
            float const Half[3] = {0.036f, 0.041f, 0.0f};
            float const Zero[3] = {0.0f, 0.0f, 0.0f};
            RightIcons[Row] = CreateStaticControl(Name, "", Position, nullptr, Half, 0, 0, 0, 1, 1,
                                                  1, 1, 0x50, 0, 0, Zero);
            if (RightIcons[Row] != nullptr)
                RightIcons[Row]->Flags = static_cast<unsigned char>(RightIcons[Row]->Flags & 0xf7);
        }
        {
            sprintf(Name, "ShipParkRightIconFrame%d", Row);
            float const Position[3] = {0.916f, FrameY, 0.0f};
            float const Half[3] = {0.035f, 0.0335f, 0.0f};
            RightIconFrames[Row] =
                CreateWireButtonControl(Name, "ui_select_item", Position, Half, 0, 0, 0, 0, 0);
        }
        {
            sprintf(Name, "ShipParkRightFrame%d", Row);
            float const Position[3] = {1.098f, FrameY, 0.0f};
            float const Half[3] = {0.138f, 0.034f, 0.0f};
            RightFrames[Row] =
                CreateWireButtonControl(Name, "ui_select_item", Position, Half, 0, 0, 0, 0, 0);
        }
        {
            sprintf(Name, "ShipParkRightName%d", Row);
            float const Position[3] = {0.97f, -0.167f - RowStep, 0.0f};
            RightNames[Row] = CreateTextControl(Name, "ItemName", Position, nullptr, 0.264f, 0.03f,
                                                1.6f, 0, 0, 0, 1);
        }
        {
            sprintf(Name, "ShipParkRightClass%d", Row);
            float const Position[3] = {0.97f, -0.195f - RowStep, 0.0f};
            RightClasses[Row] = CreateTextControl(Name, "ItemName", Position, nullptr, 0.15f, 0.03f,
                                                  1.6f, 0, 0, 0, 1);
        }
    }
    {
        float const Position[3] = {0.642f, -0.472f, 0.0f};
        float const Half[3] = {0.15f, 0.026f, 0.0f};
        ParkButton = CreateWireButtonControl("ShipParkAction", "ui_select_item", Position, Half, 0,
                                             0, 0, 0, 0);
        float const TextPos[3] = {0.64f, -0.465f, 0.0f};
        ParkText = CreateTextControl("ShipParkActionText", "ButtonText", TextPos, nullptr, 0.198f,
                                     0.03f, 1.6f, 0, 1, 0, 0);
        SetCaption(ParkText, L"\x041F\x0420\x0418\x041F\x0410\x0420\x041A\x041E\x0412\x0410\x0422\x042C");
    }
    {
        float const RotSpeed[3] = {0.0f, 0.0f, 0.0f};
        float const ViewOffset[3] = {0.005f, 0.078f, -1.288f};
        float const Ypr[3] = {0.0f, 0.0f, 0.0f};
        float const ViewSize[3] = {0.18f, -0.162f, 0.0f};
        unsigned const RectColor = 0xffffdc0cu;
        unsigned const WireColor = 0xffffffffu;
        ShipView = static_cast<ShipViewControl*>(CreateShipViewControl(
            "ShipPark3DShip", RotSpeed, ViewOffset, Ypr, ViewSize, nullptr, false, false,
            &RectColor, &WireColor));
    }
    {
        float const Position[3] = {0.647f, -0.031f, 0.0f};
        ViewName = CreateTextControl("ShipParkViewName", "PageHeader", Position, nullptr, 0.367f,
                                     0.03f, 1.6f, 0, 1, 0, 0);
    }
    {
        float const Position[3] = {0.647f, -0.07f, 0.0f};
        ViewClass = CreateTextControl("ShipParkViewClass", "SubHeader", Position, nullptr, 0.367f,
                                      0.03f, 1.6f, 0, 1, 0, 0);
    }
    {
        float const Offset[3] = {0.01f, -0.164f, -1.0f};
        InfoCard = CreateRichTextWin("ShipParkInfoCard", 0.40f, 0.2f, Offset, true);
    }
    {
        float const Position[3] = {0.606f, 0.164f, -1.288f};
        ListScroll = CreateUIScroll("ShipParkScroll", Position, 0.014f, 0.204f, 0, 256, VisibleRows, 0);
    }

    DrawLayer = 100;
    SetOffset(-0.64f, 0.33f, -1.288f);
    SetPosition(Position);
    Rebuild();
    HudPushCancelHandler(AsHudCmdHandler(), 0);
    return Win3D::Create(NewParent, Data);
}

void NnShipPark::Update() {
    Win3D::Update();
    int const bGear = (bLeftSelected != 0 && CurrentArch != 0) ||
                      (RightSelected >= 0 && RightSelected < ParkedCount);
    if (GearScrollHost == nullptr || bGear == 0)
        return;
    int OriginX = 0;
    int OriginY = 0;
    GearScrollHost->GetScrollOrigin(&OriginX, &OriginY);
    int const Row = OriginY / 16;
    if (Row != GearFirst)
        ScrollGear(Row);
}

void NnShipPark::Draw() {
    int const Shown = RightSelected - FirstVisible;
    for (Win3D* Child = ChildHead; Child != nullptr; Child = Child->NextSibling) {
        Child->DrawLayer = 0;
        WinControl* const Control = Child->AsWinControl();
        if (Control == nullptr)
            continue;
        if (Hovered >= 0 && Hovered < VisibleRows &&
            (Control == RightFrames[Hovered] || Control == RightIconFrames[Hovered]))
            Child->DrawLayer = 1;
        if (bLeftSelected != 0 && (Control == LeftFrame || Control == LeftIconFrame))
            Child->DrawLayer = 2;
        if (Shown >= 0 && Shown < VisibleRows &&
            (Control == RightFrames[Shown] || Control == RightIconFrames[Shown]))
            Child->DrawLayer = 2;
    }
    if (VisibleCount() > 0) {
        WireControlsJoinColumn(RightFrames, VisibleCount());
        WireControlsJoinColumn(RightIconFrames, VisibleCount());
    }
    float Fill = CargoHold > 0.0f ? CargoUsed / CargoHold : 0.0f;
    if (Fill < 0.0f)
        Fill = 0.0f;
    if (Fill > 1.0f)
        Fill = 1.0f;
    NnStaticControlSetClip(static_cast<NnStaticControl*>(CargoFull), Fill);
    WinControl::Draw();
    NnStaticControlSetClip(nullptr, 1.0f);
    if (ShipView == nullptr)
        return;
    float Ray[3];
    if (!ShipView->HitTest(Win3DGetMouseRay(Ray)))
        return;
    if ((GetClientMouseButtons() & 3) != 0) {
        ShipView->DragRotate(bDragStart != 0);
        bDragStart = 0;
    } else {
        bDragStart = 1;
    }
}

bool NnShipPark::KeyEvent(unsigned Key, unsigned char* Modifiers) {
    if (Modifiers != nullptr && (*Modifiers & 2) != 0 && Key == 0x1b)
        Leave();
    return false;
}

intptr_t NnShipPark::SetProperty(int Msg, uintptr_t A, uintptr_t B) {
    WinControl* const Sender = reinterpret_cast<WinControl*>(A);
    if (Msg == 0x3e) {
        if (Sender == ListScroll) {
            ScrollTo(static_cast<int>(B));
            return 1;
        }
        if (Sender == GearScroll) {
            ScrollGear(static_cast<int>(B));
            return 1;
        }
        return 0;
    }
    if (Msg == 0x4e) {
        Leave();
        return 0;
    }
    if (Msg == 0x2c || Msg == 0x2d) {
        if (Sender == LeftIconFrame && LeftFrame != nullptr)
            LeftFrame->SetProperty(Msg, 0, 0);
        else if (Sender == LeftFrame && LeftIconFrame != nullptr)
            LeftIconFrame->SetProperty(Msg, 0, 0);
        for (int Row = 0; Row < VisibleCount(); ++Row) {
            if (Sender != RightFrames[Row] && Sender != RightIconFrames[Row])
                continue;
            if (Sender != RightFrames[Row] && RightFrames[Row] != nullptr)
                RightFrames[Row]->SetProperty(Msg, 0, 0);
            if (Sender != RightIconFrames[Row] && RightIconFrames[Row] != nullptr)
                RightIconFrames[Row]->SetProperty(Msg, 0, 0);
            Hovered = Msg == 0x2c ? Row : -1;
        }
        return 0;
    }
    if (Msg != 0x26)
        return 0;
    if (Sender == CancelButton) {
        Leave();
        return 1;
    }
    if (Sender == ParkButton) {
        if (bLeftSelected != 0)
            ParkCurrent();
        else if (RightSelected >= 0)
            TakeParked(RightSelected);
        return 1;
    }
    for (int Tab = 0; Tab < GearTabs; ++Tab) {
        if (Sender != GearTabButtons[Tab])
            continue;
        GearFilter = Tab;
        GearFirst = 0;
        if (GearScroll != nullptr)
            GearScroll->SetProperty(0x38, 0, 0);
        BindGear();
        return 1;
    }
    if (Sender == LeftFrame || Sender == LeftIconFrame) {
        if (CurrentArch == 0)
            return 1;
        bLeftSelected = 1;
        RightSelected = -1;
        ShowShip(CurrentArch);
        UpdateAction();
        BindParked();
        return 1;
    }
    for (int Row = 0; Row < VisibleCount(); ++Row) {
        if (Sender != RightFrames[Row] && Sender != RightIconFrames[Row])
            continue;
        int const Index = FirstVisible + Row;
        if (Index < 0 || Index >= ParkedCount)
            return 1;
        bLeftSelected = 0;
        RightSelected = Index;
        ShowShip(ParkedShips[Index].Archetype);
        UpdateAction();
        BindParked();
        return 1;
    }
    return 0;
}

bool NnShipPark::OnEvent(unsigned MsgId) {
    if (MsgId != 0x10)
        return false;
    Leave();
    return true;
}
