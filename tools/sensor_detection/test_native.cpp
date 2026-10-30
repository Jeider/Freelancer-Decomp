#include "sensor_detection.h"
#include "common_goods.h"
#include "common_ini.h"
#include "common_misc.h"
#include "dacom.h"
#include <cassert>
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <fstream>
#include <limits>
#include <new>

struct BeamFixture : Archetype::Munition { static void Set(long value) { BEAM_ARCH_INDEX=value; } };
static void __cdecl TestDump(int,char const* format,...)
{
    va_list args; va_start(args,format); std::vfprintf(stderr,format,args); va_end(args);
    std::fputc('\n',stderr);
}
static void Parse(Archetype::Root& arch,char const* text)
{
    INI_Reader ini;
    assert(ini.open_memory(text,unsigned(std::strlen(text))) && ini.read_header());
    while(ini.read_value()) assert(arch.read(ini));
}
static EquipDesc Item(char const* name,unsigned short id,bool mounted)
{
    EquipDesc d;
    d.set_arch_id(CreateID(name)); d.set_id(id); d.set_count(1);
    d.set_status(1.f); d.make_internal(); d.set_equipped(mounted);
    return d;
}
int main(int argc,char** argv)
{
    std::setvbuf(stdout,nullptr,_IONBF,0);
    FDUMP=TestDump;
    assert(LoadLibraryA("x86math.dll"));
    assert(argc==2);
    BeamFixture::Set(0);
    assert(Archetype::LoadEquipment(argv[1],false,nullptr)==5);
    auto* scanner=static_cast<Archetype::Scanner*>(Archetype::GetEquipment(CreateID("sensor_test_scanner")));
    auto* inherited=static_cast<Archetype::Scanner*>(Archetype::GetEquipment(CreateID("sensor_test_inherited")));
    assert(scanner->GetDiscoveryRange()==18000 && scanner->GetValuableDetectionRange()==5000);
    assert(inherited->GetDiscoveryRange()==18000 && inherited->GetValuableDetectionRange()==7500);
    assert(scanner->bRadarValuable && inherited->bRadarValuable);
    Archetype::Scanner copy(*scanner),assigned;
    assigned=*scanner;
    assert(copy.GetDiscoveryRange()==18000 && assigned.GetValuableDetectionRange()==5000);
    assigned=assigned;
    assert(assigned.GetDiscoveryRange()==18000);
    Archetype::Scanner legacy;
    copy.redefine(legacy);
    assert(copy.GetDiscoveryRange()==-1 && copy.GetValuableDetectionRange()==0 && !copy.bRadarValuable);
    alignas(Archetype::Scanner) unsigned char storage[sizeof(Archetype::Scanner)];
    auto* reused=new(storage) Archetype::Scanner(*scanner);
    reused->~Scanner();
    reused=new(storage) Archetype::Scanner();
    assert(reused->GetDiscoveryRange()==-1 && reused->GetValuableDetectionRange()==0);
    reused->~Scanner();
    Parse(assigned,"[Scanner]\ndiscovery_range=-100\nvaluable_detection_range=0\nradar_valuable=false\n");
    assert(assigned.GetDiscoveryRange()==0 && assigned.GetValuableDetectionRange()==0 && !assigned.bRadarValuable);

    Archetype::Solar solarArch;
    Parse(solarArch,"[Solar]\nradar_valuable=true\n");
    CSolar solar;
    solar.Archetype=&solarArch;
    assert(SensorDetection::IsValuable(&solar));
    Archetype::Solar ordinary;
    solarArch.redefine(ordinary);
    assert(!SensorDetection::IsValuable(&solar));
    // A flagged cargo in the loadout is equivalent to the Solar flag.
    assert(solar.add_item(Item("sensor_test_ore",1,false)));
    assert(SensorDetection::IsValuable(&solar));
    auto* cargo=CECargo::cast(solar.EquipManager.FindByID(1));
    assert(cargo);
    cargo->SetCount(0);
    assert(!SensorDetection::IsValuable(&solar));
    cargo->SetCount(1);
    assert(SensorDetection::IsValuable(&solar));
    solar.clear_equip_and_cargo();
    assert(!SensorDetection::IsValuable(&solar));

    Archetype::Ship hull; hull.HoldSize=100;
    CShip ship; ship.Archetype=&hull;
    assert(!SensorDetection::IsValuable(&ship));
    assert(ship.add_item(Item("sensor_test_scanner",2,true)));
    assert(SensorDetection::IsValuable(&ship));
    auto* equipment=ship.EquipManager.FindByID(2);
    equipment->bDestroyed=1;
    assert(!SensorDetection::IsValuable(&ship));
    equipment->bDestroyed=0;
    // A headless fixture has no rendered hardpoints. Construct the tractor with
    // its identity source transform, then attach it to the real equipment list.
    auto* tractorArch=static_cast<Archetype::Tractor*>(Archetype::GetEquipment(CreateID("sensor_test_tractor")));
    auto* mountedTractor=new CETractor(nullptr,3,tractorArch,false);
    mountedTractor->Owner=&ship;
    assert(ship.EquipManager.AddNewEquipment(mountedTractor));
    auto const* tractor=SensorDetection::WorkingTractor(&ship);
    assert(tractor && tractor->GetRange()==2500);
    CLoot loot;
    loot.ContentsArch=Archetype::GetEquipment(CreateID("sensor_test_ore")); loot.Units=1;
    assert(SensorDetection::IsValuable(&loot));
    auto const origin=tractor->GetSourcePos();
    loot.WorldPosition={origin.x+2000,origin.y,origin.z};
    assert(SensorDetection::CanCollect(tractor,&loot)); // beyond old 1000 m limit
    tractorArch->MaxLength=500;
    assert(!SensorDetection::CanCollect(tractor,&loot));
    loot.WorldPosition.x=origin.x+500;
    assert(SensorDetection::CanCollect(tractor,&loot)); // exact native boundary
    loot.WorldPosition.x=origin.x+501;
    assert(!SensorDetection::CanCollect(tractor,&loot));
    tractorArch->MaxLength=0;
    assert(SensorDetection::CanCollect(tractor,&loot)); // native unlimited convention
    hull.HoldSize=0;
    assert(!SensorDetection::CanCollect(tractor,&loot));
    hull.HoldSize=100;
    loot.Units=0;
    assert(!SensorDetection::CanCollect(tractor,&loot) && !SensorDetection::IsValuable(&loot));
    ship.EquipManager.FindByID(3)->bDestroyed=1;
    assert(!SensorDetection::WorkingTractor(&ship));
    ship.clear_equip_and_cargo();
    assert(!SensorDetection::IsValuable(&ship) && !SensorDetection::WorkingTractor(&ship));

    assert(SensorDetection::EffectiveRange(5000,.4f)==3000);
    assert(SensorDetection::EffectiveRange(5000,2)==0);
    assert(SensorDetection::EffectiveRange(5000,-1)==5000);
    assert(SensorDetection::EffectiveRange(std::numeric_limits<float>::infinity(),0)==0);
    assert(SensorDetection::InRange({0,0,0},{18000,0,0},18000));
    assert(!SensorDetection::InRange({0,0,0},{18001,0,0},18000));
    assert(!SensorDetection::InRange({0,0,0},{0,0,0},0));
    std::ofstream("reload.ini") << "[Scanner]\nnickname=sensor_test_scanner\nrange=1000\n";
    Archetype::LoadEquipment("reload.ini",true,nullptr);
    assert(scanner->GetDiscoveryRange()==-1 && scanner->GetValuableDetectionRange()==0 && !scanner->bRadarValuable);
    BeamFixture::Set(-1);
    puts("PASS: native parsing/inherit/copy/reload, Solar OR equipment/cargo, live depletion, tractor range/capacity, interference and discovery bounds");
}
