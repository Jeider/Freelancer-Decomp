#include "common_archetype.h"
#include "common_cequip.h"
#include "common_cobject.h"
#include "common_goods.h"
#include "common_ini.h"
#include "common_misc.h"
#include "inventory_categories.h"
#include "dacom.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <map>
#include <string>

struct BeamFixture:Archetype::Munition {static void Set(long value){BEAM_ARCH_INDEX=value;}};
static void __cdecl Dump(int,char const*,...) {}
struct FClientMarket {} market;
unsigned currentBase=0;
float marketPrice=100;
unsigned GetClientLocationCurrentBase(){return currentBase;}
FClientMarket* GetClientLocationBaseMarket(unsigned){return &market;}
float ClientMarketGetPrice(FClientMarket*,unsigned){return marketPrice;}
struct FContentPlayerState {unsigned PlayerId=0;};
struct FDockKey {unsigned Key;bool bMounted;};
std::map<unsigned,FDockKey> locks;
std::map<unsigned,FDockKey> const& DockKeys(){return locks;}
struct PlayerEquipment {EquipDescList equipment;};
PlayerEquipment Players[2];
struct FClientMarketGood {struct {unsigned GoodId=0;} Info;int Stock=100;} stock;
FClientMarketGood* ClientMarketFindEntry(FClientMarket*,unsigned){return &stock;}
unsigned shipId=0,credits=10000;
unsigned G_NanobotArchId=0,G_ShieldBatteryArchId=0;
unsigned GetPlayerShipArchetypeIdRetail(){return shipId;}
unsigned GetPlayerCreditsRetail(){return credits;}
float GetPlayerShipHoldSizeRetail(){return 100;}
EquipDescList const& GetPlayerEquipDescListRetail(){return Players[0].equipment;}
struct ShipViewFixture {char const* FindHardpointForGood(unsigned,bool){return nullptr;}};
struct InventoryFixture {
    int Mode=InventoryCategories::Boosters;
    struct {char const* Value="";void clear(){Value="";}} Field394;
    struct {ShipViewFixture* ShipView=nullptr;EquipDescList Loadout;} Ship;
};
struct NnDealer {
    InventoryFixture* Inventory=nullptr;int Mode=InventoryCategories::Boosters;
    unsigned GetSelectedMarketGood(){return 0;}
    int GetMarketPackagePrice(unsigned){return static_cast<int>(marketPrice);}
    int GetMaxBuyCount(unsigned,int*);
};
#include "production.inc"

static EquipDesc Cargo(char const* name,unsigned short id){
    EquipDesc item;item.set_arch_id(CreateID(name));item.set_id(id);
    item.set_count(1);item.set_status(1);item.set_equipped(false);item.make_internal();return item;
}
int main(){
    _set_error_mode(_OUT_TO_STDERR);_set_abort_behavior(0,_WRITE_ABORT_MSG|_CALL_REPORTFAULT);
    FDUMP=Dump;BeamFixture::Set(0);
    std::ofstream("equipment.ini")
        <<"[DoorKey]\nnickname=test_key\nids_name=1\nvolume=0\nlootable=false\n"
        <<"[DoorKey]\nnickname=test_key_copy\ninherit=test_key\n"
        <<"[RepairKit]\nnickname=test_repair\nids_name=1\n"
        <<"[ShieldBattery]\nnickname=test_battery\nids_name=1\n"
        <<"[RepairDroid]\nnickname=test_legacy_key\nids_name=1\n"
        <<"[Power]\nnickname=test_internal\nids_name=1\n";
    assert(Archetype::LoadEquipment("equipment.ini",false,nullptr)==6);
    std::ofstream goods("goods.ini");
    for(auto name:{"test_key","test_key_copy","test_repair","test_battery","test_legacy_key","test_internal"})
        goods<<"[Good]\nnickname="<<name<<"\nequipment="<<name<<"\ncategory=equipment\nprice=100\ncombinable=true\n";
    goods.close();char absolute[4096];assert(_fullpath(absolute,"goods.ini",sizeof absolute));GoodList_load(absolute);
    auto* key=Archetype::GetEquipment(CreateID("test_key"));
    auto* copy=Archetype::GetEquipment(CreateID("test_key_copy"));
    assert(key&&copy&&key->get_class_type()==Archetype::AClassDoorKey&&copy->IdsName==1);
    assert(copy->get_class_type()==Archetype::AClassDoorKey&&key->get_hp_type()==HpTypeNone);
    assert(!key->is_attached());
    assert(NnItemFilterMode(CreateID("test_repair"))==InventoryCategories::Boosters);
    assert(NnItemFilterMode(CreateID("test_battery"))==InventoryCategories::Boosters);
    assert(NnItemFilterMode(CreateID("test_key"))==InventoryCategories::Keys);
    assert(NnItemFilterMode(CreateID("test_legacy_key"))==3);
    assert(NnItemFilterMode(CreateID("test_internal"))==3);
    currentBase=1;marketPrice=0;
    assert(NnItemFilterMode(CreateID("test_key"))==InventoryCategories::Keys);
    assert(NnItemFilterMode(CreateID("test_internal"))==5);
    marketPrice=100;assert(NnItemFilterMode(CreateID("test_repair"))==InventoryCategories::Boosters);
    puts("PASS: real DoorKey parsing/inheritance; Boosters/Keys classification; legacy internals and zero-price keys");
    {
        Archetype::Ship hull(nullptr);hull.HoldSize=100;
        CShip ship;ship.Archetype=&hull;
        EquipDesc item=Cargo("test_key",40);item.set_count(2);
        assert(ship.add_item(item));
        CEquip* cargo=ship.EquipManager.FindByID(40);
        assert(cargo&&cargo->GetType()==EquipTypeCargo);
        assert(!ship.EquipManager.FindFirst(EquipTypeRepairDroid|EquipTypeGravityDevice|EquipTypeCloak));
        EquipDesc saved;assert(cargo->GetEquipDesc(saved));
        assert(!saved.bEquipped&&saved.Count==2&&saved.ArchId==key->Nickname.Id);
        ship.clear_equip_and_cargo();assert(ship.add_item(saved));
        assert(ship.EquipManager.FindByID(40)->GetEquipDesc(saved));
        assert(!saved.bEquipped&&saved.Count==2&&saved.ArchId==key->Nickname.Id);
        Players[0].equipment.Items.push_back(saved);
        ship.clear_equip_and_cargo();
    }
    FContentPlayerState owner{0},other{1};locks[5]={key->Nickname.Id,true};
    assert(DockKeyUnlocks(5,&owner));assert(!DockKeyUnlocks(5,&other));
    assert(!DockKeyUnlocks(5,nullptr)&&!DockKeyUnlocks(6,&owner));
    Players[0].equipment.Items.front().Count=0;assert(!DockKeyUnlocks(5,&owner));
    Players[0].equipment.Items.front().Count=2;assert(DockKeyUnlocks(5,&owner));
    assert(Players[0].equipment.Items.front().Count==2); // No consumption.
    locks[5].Key=CreateID("test_legacy_key");
    Players[0].equipment.Items.clear();Players[0].equipment.Items.push_back(Cargo("test_legacy_key",41));
    assert(!DockKeyUnlocks(5,&owner));
    Players[0].equipment.Items.front().set_equipped(true);assert(DockKeyUnlocks(5,&owner));
    Players[0].equipment.Items.front().set_equipped(false);locks[5].bMounted=false;assert(DockKeyUnlocks(5,&owner));
    puts("PASS: DoorKey cargo serialization/reload; unmounted key unlocks existing locks without consumption; legacy mounted rules retained");
    std::ofstream("ships.ini")<<"[Ship]\nnickname=test_ship\nnanobot_limit=12\nshield_battery_limit=9\nhold_size=100\n";
    assert(Archetype::LoadShips("ships.ini",false,nullptr)==1);
    shipId=CreateID("test_ship");
    G_NanobotArchId=CreateID("test_repair");G_ShieldBatteryArchId=CreateID("test_battery");
    InventoryFixture inventory;NnDealer dealer;dealer.Inventory=&inventory;int reason=0;
    stock.Info.GoodId=Arch2Good(G_NanobotArchId);
    assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==12&&reason==0);
    auto carried=Cargo("test_repair",50);carried.Count=7;inventory.Ship.Loadout.Items.push_back(carried);
    assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==5&&reason==0);
    inventory.Ship.Loadout.Items.front().Count=12;
    assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==0&&reason==9);
    stock.Info.GoodId=Arch2Good(G_ShieldBatteryArchId);
    assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==9&&reason==0);
    carried=Cargo("test_battery",51);carried.Count=9;inventory.Ship.Loadout.Items.push_back(carried);
    assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==0&&reason==10);
    inventory.Mode=InventoryCategories::Keys;dealer.Mode=inventory.Mode;
    stock.Info.GoodId=Arch2Good(key->Nickname.Id);stock.Stock=3;marketPrice=0;credits=0;
    assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==3&&reason==0);
    marketPrice=100;assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==0&&reason==2);
    credits=100;assert(dealer.GetMaxBuyCount(stock.Info.GoodId,&reason)==1&&reason==0);
    puts("PASS: Boosters retain nanobot/battery capacity limits; free and paid DoorKey purchases respect stock and credits");
    BeamFixture::Set(-1);
}
