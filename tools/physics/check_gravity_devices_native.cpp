// Real Common.dll: dedicated device, hardware class validation and save/load lifecycle.
#include "common_archetype.h"
#include "common_cequip.h"
#include "common_cobject.h"
#include "common_goods.h"
#include "common_ini.h"
#include "common_misc.h"
#include "equipment_slots.h"
#include "dacom.h"
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
struct BeamFixture:Archetype::Munition {static void Set(long value){BEAM_ARCH_INDEX=value;}};
static void __cdecl Dump(int,char const* format,...){
    va_list args;va_start(args,format);vfprintf(stderr,format,args);fputc('\n',stderr);va_end(args);
}
static void Parse(Archetype::Root& arch,std::string const& text){
    INI_Reader ini;assert(ini.open_memory(text.c_str(),unsigned(text.size())));
    assert(ini.read_header());while(ini.read_value()) assert(arch.read(ini));
}
static EquipDesc Item(char const* name,unsigned short id,char const* slot="HpHardware01"){
    EquipDesc desc;desc.set_id(id);desc.set_arch_id(CreateID(name));desc.set_count(1);
    desc.set_status(1);desc.set_equipped(true);
    CacheString hp;hp.Value=StringAlloc(slot,false);desc.set_hardpoint(hp);return desc;
}
static void CheckHardwareLimits(){
    char const* names[]={"cloak_class_1","repair_class_1","gravity_generator"};
    char const* alternatives[]={"cloak_class_2","repair_class_2","gravity_compensator_full"};
    char const* slots[]={"HpHardware01","HpHardware02","HpHardware03"};
    for(int capacity=1;capacity<=3;++capacity){
        Archetype::Ship hull(nullptr);
        std::string config="[Ship]\n";
        for(int i=0;i<capacity;++i)config+="equipment_slot="+std::string(slots[i])+",hardware,10\n";
        Parse(hull,config);
        // Every order of choosing distinct module types, on 1/2/3-slot hulls.
        for(int first=0;first<3;++first)for(int second=0;second<3;++second){
            if(first==second)continue;
            int order[]={first,second,3-first-second};
            EquipDescList mounted;
            for(int i=0;i<3;++i){
                auto item=Item(names[order[i]],static_cast<unsigned short>(40+i),slots[i]);
                assert(EquipmentSlots::CanMount(&hull,mounted,item,slots[i])==(i<capacity));
                auto candidate=mounted;candidate.Items.push_back(item);
                assert(EquipmentSlots::Validate(&hull,candidate)==(i<capacity));
                assert(EquipmentSlots::ValidateChange(&hull,mounted,candidate)==(i<capacity));
                if(i<capacity)mounted=candidate;
            }
        }
        if(capacity<2)continue;
        for(int kind=0;kind<3;++kind){
            EquipDescList mounted;mounted.Items.push_back(Item(names[kind],40));
            for(auto duplicate:{names[kind],alternatives[kind]}){
                auto item=Item(duplicate,41,slots[1]);
                assert(!EquipmentSlots::CanMount(&hull,mounted,item,slots[1]));
                auto candidate=mounted;candidate.Items.push_back(item);
                assert(!EquipmentSlots::Validate(&hull,candidate));
                assert(!EquipmentSlots::ValidateChange(&hull,mounted,candidate));
                candidate.Items.back().set_equipped(false);candidate.Items.back().set_count(3);
                assert(EquipmentSlots::Validate(&hull,candidate)); // Cargo copies do not occupy hardware.
                assert(EquipmentSlots::ValidateChange(&hull,mounted,candidate));
            }
            auto replacement=mounted;replacement.Items.front().set_equipped(false);
            replacement.Items.push_back(Item(alternatives[kind],41));
            assert(EquipmentSlots::ValidateChange(&hull,mounted,replacement));
            // An authored/internal resident also blocks installing a second device.
            mounted.Items.front().make_internal();
            assert(!EquipmentSlots::CanMount(&hull,mounted,Item(alternatives[kind],41),slots[1]));
        }
    }
    puts("PASS: 1/2/3 hardware slots, every module order, one per type across classes/variants, cargo and replacements");
}
static void Check(CEqObj& owner,char const* name){
    auto item=Item(name,40);
    assert(owner.add_item(item));
    auto* device=owner.EquipManager.FindByID(40);
    assert(device&&device->GetType()==EquipTypeGravityDevice&&device->IsFunctioning());
    assert(CEGravityDevice::cast(device)&&CInternalEquip::cast(device)&&!CERepairDroid::cast(device));
    assert(owner.EquipManager.FindFirst(EquipTypeGravityDevice)==device);
    auto traversalCargo=Item(name,39);traversalCargo.set_equipped(false);traversalCargo.make_internal();
    assert(owner.add_item(traversalCargo)); // Retail reverse traversal requires both manager lists.
    CEquipTraverser reverse(EquipTypeGravityDevice);
    assert(owner.EquipManager.ReverseTraverse(reverse)==device);
    assert(device->GetHitPoints()==1000);
    EquipDesc saved;assert(device->GetEquipDesc(saved)&&!saved.is_internal()&&saved.is_equipped());
    assert(!_stricmp(saved.Hardpoint,"HpHardware01")&&saved.ArchId==item.ArchId);
    { CEGravityDevice copy(*CEGravityDevice::cast(device));
      EquipDesc copied;assert(copy.GetEquipDesc(copied));assert(!_stricmp(copied.Hardpoint,saved.Hardpoint)); }
    owner.clear_equip_and_cargo();
    assert(owner.add_item(saved));device=owner.EquipManager.FindByID(40);
    assert(device&&device->IsFunctioning());
    device->Activate(false);assert(!device->IsFunctioning());assert(device->Activate(true));
    device->SetHitPoints(0);assert(!device->IsFunctioning());assert(!device->Activate(true));
    device->GetEquipDesc(saved);assert(saved.Health==0);
    owner.clear_equip_and_cargo();assert(owner.add_item(saved));
    assert(!owner.EquipManager.FindByID(40)->IsFunctioning());owner.clear_equip_and_cargo();
    auto cargo=Item(name,41);cargo.set_equipped(false);cargo.make_internal();
    assert(owner.add_item(cargo));assert(owner.EquipManager.FindByID(41)->GetType()==EquipTypeCargo);
    owner.clear_equip_and_cargo();
}
static void CheckCargoOnly(CShip& ship,char const* name,unsigned type){
    auto item=Item(name,55);
    assert(ship.add_item(item));
    auto* mounted=ship.EquipManager.FindByID(55);assert(mounted&&mounted->GetType()==type);
    if(type==EquipTypeCloak){
        mounted->Activate(true);mounted->Update(1,0);assert(ship.get_cloak_percentage()==1);
        {CECloakingDevice copy(*CECloakingDevice::cast(mounted));}
        assert(ship.get_cloak_percentage()==1);
        mounted->Destroy();assert(ship.get_cloak_percentage()==0);
        ship.clear_equip_and_cargo();assert(ship.add_item(item));
        mounted=ship.EquipManager.FindByID(55);mounted->Update(1,0);
        assert(ship.get_cloak_percentage()==1);
    }
    ship.clear_equip_and_cargo();
    assert(ship.get_cloak_percentage()==0);
    // Even a stale hardpoint string must not make an unmounted item functional.
    item.set_equipped(false);item.set_count(3);
    assert(ship.add_item(item));
    auto* cargo=ship.EquipManager.FindByID(55);assert(cargo&&cargo->GetType()==EquipTypeCargo);
    assert(!ship.EquipManager.FindFirst(EquipTypeCloak|EquipTypeGravityDevice|EquipTypeRepairDroid));
    assert(!CECloakingDevice::cast(cargo)&&!CEGravityDevice::cast(cargo)&&!CERepairDroid::cast(cargo));
    cargo->Activate(true);cargo->Update(1,0);assert(ship.get_cloak_percentage()==0);
    EquipDesc saved;assert(cargo->GetEquipDesc(saved)&&!saved.bEquipped&&saved.Count==3);
    ship.clear_equip_and_cargo();assert(ship.add_item(saved));
    assert(ship.EquipManager.FindByID(55)->GetType()==EquipTypeCargo);
    assert(!ship.EquipManager.FindFirst(type));ship.clear_equip_and_cargo();
    item.set_equipped(true);item.set_count(1);assert(ship.add_item(item));
    assert(ship.EquipManager.FindFirst(type));ship.clear_equip_and_cargo();
    printf("PASS: mounted/cargo/remount and cargo save reload: %s\n",name);
}
int main(int argc,char** argv){
    _set_error_mode(_OUT_TO_STDERR);_set_abort_behavior(0,_WRITE_ABORT_MSG|_CALL_REPORTFAULT);
    FDUMP=Dump;assert(argc==3);BeamFixture::Set(0);assert(EquipmentSlots::Enabled());
    assert(Archetype::LoadEquipment(argv[1],false,nullptr)==5);
    assert(Archetype::LoadEquipment(argv[2],false,nullptr)==1);
    std::ofstream fixture("hardware.ini");
    for(int level=1;level<=10;++level){
        fixture<<"[GravityDevice]\nnickname=gravity_class_"<<level<<"\ninherit=gravity_generator\nhp_type=hp_hardware_special_"<<level<<"\n";
        fixture<<"[RepairDroid]\nnickname=repair_class_"<<level<<"\ninherit=repair_droid_auto\nhp_type=hp_hardware_special_"<<level<<"\n";
        fixture<<"[CloakingDevice]\nnickname=cloak_class_"<<level<<"\nhit_pts=1000\nhp_type=hp_hardware_special_"<<level<<"\n";
    }
    fixture<<"[RepairDroid]\nnickname=quest_key\n[RepairKit]\nnickname=normal_nanobots\n";
    fixture.close();assert(Archetype::LoadEquipment("hardware.ini",false,nullptr)==32);
    CheckHardwareLimits();
    Archetype::Ship hull(nullptr);hull.HoldSize=100;
    Parse(hull,"[Ship]\nequipment_slot=HpHardware01,hardware,10\nequipment_slot=HpHardware02,hardware,10\nequipment_slot=HpHardware03,hardware,10\n");
    Archetype::Solar solarArch(nullptr);
    Parse(solarArch,"[Solar]\nequipment_slot=HpHardware01,hardware,10\n");
    {
        CShip ship;ship.Archetype=&hull;ship.OwnerPlayer=1;
        CShip npc;npc.Archetype=&hull;
        CSolar solar;solar.Archetype=&solarArch;
        CheckCargoOnly(ship,"cloak_class_1",EquipTypeCloak);
        CheckCargoOnly(ship,"gravity_generator",EquipTypeGravityDevice);
        CheckCargoOnly(ship,"gravity_compensator_full",EquipTypeGravityDevice);
        CheckCargoOnly(ship,"repair_droid_auto",EquipTypeRepairDroid);
        for(auto name:{"gravity_generator","gravity_repulsor","gravity_suppressor","gravity_compensator_70","gravity_compensator_full"}){
            assert(Archetype::GetEquipment(CreateID(name))->get_class_type()==Archetype::AClassGravityDevice);
            Check(ship,name);Check(npc,name);Check(solar,name);
        }
        auto key=Item("quest_key",35);key.make_internal();assert(ship.add_item(key));
        auto bots=Item("normal_nanobots",36);bots.make_internal();bots.set_equipped(false);bots.set_count(10);
        hull.NanobotLimit=50;assert(ship.add_item(bots));
        assert(ship.add_item(Item("repair_droid_auto",37)));
        auto* repair=CERepairDroid::cast(ship.EquipManager.FindByID(37));
        assert(repair&&!repair->IsFunctioning()&&repair->GetHitPoints()==10000);
        assert(repair->Activate(true));assert(repair->IsFunctioning());repair->Activate(false);
        assert(!repair->IsFunctioning());repair->SetHitPoints(0);assert(!repair->Activate(true));
        EquipDesc robotSave;assert(repair->GetEquipDesc(robotSave)&&!_stricmp(robotSave.Hardpoint,"HpHardware01"));
        EquipDesc botSave;assert(ship.EquipManager.FindByID(36)->GetEquipDesc(botSave)&&botSave.Count==10);
        EquipDescList existingRepair;existingRepair.Items.push_back(Item("repair_droid_auto",37));
        assert(!EquipmentSlots::CanMount(&hull,existingRepair,Item("repair_droid_auto",38),"HpHardware02"));
        ship.clear_equip_and_cargo();
        // Every class on both device types must obey the hull's actual ceiling.
        for(int level=1;level<=10;++level){
            Archetype::Ship limited(nullptr);
            Parse(limited,"[Ship]\nequipment_slot=HpHardware01,hardware,"+std::to_string(level)+"\n");
            for(int itemClass=1;itemClass<=10;++itemClass)
                for(auto prefix:{"gravity_class_","cloak_class_","repair_class_"}){
                    std::string name=prefix+std::to_string(itemClass);EquipDescList list;
                    list.Items.push_back(Item(name.c_str(),40));
                    assert(EquipmentSlots::Validate(&limited,list)==(itemClass<=level));
                }
        }
        assert(ship.add_item(Item("cloak_class_10",40)));
        assert(ship.add_item(Item("gravity_class_10",41,"HpHardware02")));
        assert(ship.add_item(Item("repair_class_10",42,"HpHardware03")));
        EquipDescList occupied;occupied.Items.push_back(Item("gravity_class_10",41,"HpHardware02"));
        assert(!EquipmentSlots::CanMount(&hull,occupied,Item("gravity_generator",43),"HpHardware02"));
        ship.clear_equip_and_cargo();
        assert(ship.add_item(Item("cloak_class_1",40)));
        EquipDescList cloaked;cloaked.Items.push_back(Item("cloak_class_1",40));
        assert(!EquipmentSlots::CanMount(&hull,cloaked,Item("cloak_class_2",41),"HpHardware02"));
        ship.clear_equip_and_cargo();
        auto* gravity=Archetype::GetEquipment(CreateID("gravity_class_10"));
        for(auto bad:{"hp_hardware_special_0","hp_hardware_special_11","hp_scanner_special_1"}){
            Parse(*gravity,std::string("[GravityDevice]\nhp_type=")+bad+"\n");
            EquipDescList none;
            assert(!EquipmentSlots::CanMount(&hull,none,Item("gravity_class_10",40),"HpHardware01"));
        }
        Parse(*gravity,"[GravityDevice]\nhp_type=hp_hardware_special_10\n");
        // Loading must preserve every authored mount, including built-in internal devices.
        EquipDescList saved;saved.Items.push_back(Item("gravity_generator",40,"HpHardware03"));
        auto old=Item("gravity_compensator_full",41);old.make_internal();saved.Items.push_back(old);
        EquipmentSlots::RestoreLoadout(&hull,saved);
        assert(!_stricmp(saved.Items.front().Hardpoint,"HpHardware03"));
        for(auto const& item:saved.Items){assert(item.bEquipped);assert(ship.add_item(item));}
        ship.clear_equip_and_cargo();
        Archetype::Ship noSlots(nullptr);EquipmentSlots::RestoreLoadout(&noSlots,saved);
        for(auto const& item:saved.Items)assert(item.bEquipped);
        // Copy/redefine solar slot metadata, without changing the retail Solar layout.
        Archetype::Solar copy(solarArch);solar.Archetype=&copy;Check(solar,"gravity_generator");
        Archetype::Solar empty(nullptr);copy.redefine(empty);
        assert(solar.add_item(Item("gravity_generator",40)));solar.clear_equip_and_cargo();solar.Archetype=&solarArch;
    }
    // Authored mounts accept any name without shiparch declarations or physical geometry.
    {
        Archetype::Ship rootHull(nullptr);rootHull.HoldSize=100;
        CShip ship;ship.Archetype=&rootHull;ship.OwnerPlayer=1;
        EquipDescList empty;
        assert(!EquipmentSlots::CanMount(&rootHull,empty,Item("repair_droid_auto",40),"HpRoot"));
        for(auto name:{"repair_droid_auto","gravity_generator","cloak_class_1"}){
            assert(ship.add_item(Item(name,40,"HpRoot")));
            auto* device=ship.EquipManager.FindByID(40);assert(device);
            EquipDesc saved;assert(device->GetEquipDesc(saved)&&!_stricmp(saved.Hardpoint,"HpRoot"));
            if(device->GetType()==EquipTypeRepairDroid){
                assert(!device->IsActive());assert(device->Activate(true));assert(device->IsFunctioning());
            }
            if(device->GetType()==EquipTypeGravityDevice)assert(device->IsFunctioning());
            ship.clear_equip_and_cargo();
        }
    }
    // Existing scripted mounts cannot block unrelated inventory transactions.
    {
        EquipDescList before;before.Items.push_back(Item("repair_droid_auto",40,"HpRoot"));
        auto after=before;after.Items.push_back(Item("gravity_generator",41,"HpHardware02"));
        assert(EquipmentSlots::ValidateChange(&hull,before,after));
        assert(EquipmentSlots::CanMount(&hull,before,Item("gravity_generator",41),"HpHardware02"));
        assert(!EquipmentSlots::Validate(&hull,after)); // Full transfer to a new hull stays strict.
        after=before;after.Items.front().Hardpoint=StringAlloc("HpArbitrary",false);
        assert(!EquipmentSlots::ValidateChange(&hull,before,after)); // Player relocation needs a legal slot.
        after=before;after.Items.push_back(before.Items.front());
        assert(!EquipmentSlots::ValidateChange(&hull,before,after)); // No duplicated grandfathered entries.
        after=before;after.Items.front().set_equipped(false);
        assert(EquipmentSlots::ValidateChange(&hull,before,after)); // Unmounting is always possible.
        assert(!EquipmentSlots::ValidateChange(&hull,after,before)); // Cargo does not retain mount privileges.
        after=before;auto cargo=Item("gravity_generator",42,"HpRoot");cargo.set_equipped(false);cargo.set_count(3);
        after.Items.push_back(cargo);assert(EquipmentSlots::ValidateChange(&hull,before,after));
    }
    puts("PASS: authored HpRoot works without slot declarations; player mount rules remain strict; repair activates; gravity starts automatically");
    BeamFixture::Set(-1);
    puts("PASS: GravityDevice identity; all 10 gravity/cloak/repair classes and ceilings; ships/NPC/solars; mixed slots; duplicates; save preservation; copy; damage; cargo");
}
