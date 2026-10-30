"""Exercise the production server repair tick/target selection with deterministic objects."""
from pathlib import Path
import os, subprocess
from check_gravity import function
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/repair_droid_check'
STUB=r"""
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
#include <map>
constexpr unsigned short SUBOBJ_ID_ROOT=1,SUBOBJ_ID_NONE=65535;
struct CEqObj;
struct CEquip { CEqObj* Owner=nullptr;unsigned short Id=40;unsigned Type=0x200000;float hp=100;bool active=true, attached=false;
    virtual ~CEquip()=default;float GetHitPoints()const{return hp;}bool IsFunctioning()const{return active&&hp>0;}
    double GetRelativeHealth()const{return hp/100.;}float GetMaxHitPoints()const{return 100;}
};
struct DroidArch {float RepairRate=10;};
struct CERepairDroid:CEquip {DroidArch arch;static CERepairDroid* cast(CEquip* x){return dynamic_cast<CERepairDroid*>(x);}
    DroidArch const* RepairDroidArch()const{return &arch;}
};
struct CAttachedEquip {static CEquip const* cast(CEquip const* x){return x->attached?x:nullptr;}};
struct CEquipTraverser {size_t next=0;};
struct CEquipManager {std::vector<CEquip*> items;CEquip const* Traverse(CEquipTraverser& w)const{return w.next<items.size()?items[w.next++]:nullptr;}
    CEquip const* FindByID(unsigned short id)const{for(auto* x:items)if(x->Id==id)return x;return nullptr;}
};
struct GroupArch {unsigned short Id=3;};
struct CArchGroup {GroupArch* Arch=nullptr;float hp=100;double GetRelativeHealth()const{return hp/100.;}
    float GetHitPoints()const{return hp;}float GetMaxHitPoints()const{return 100;}
};
struct CArchGrpTraverser {size_t next=0;};
struct CArchGroupManager {std::vector<CArchGroup*> items;CArchGroup const* Traverse(CArchGrpTraverser& w)const{return w.next<items.size()?items[w.next++]:nullptr;}
    CArchGroup* FindByID(unsigned short id){for(auto* x:items)if(x->Arch->Id==id)return x;return nullptr;}
};
struct CSimple {float hull=50,maxHull=100;
    float get_hit_pts()const{return hull;}float get_max_hit_pts()const{return maxHull;}
    double get_relative_health()const{return hull/maxHull;}
};
struct CEqObj:CSimple {unsigned OwnerPlayer=1;CEquipManager EquipManager;CArchGroupManager ArchGroups;
    bool get_sub_obj_hit_pts(unsigned short,float&)const;
    bool get_sub_obj_max_hit_pts(unsigned short,float&)const;
    bool get_sub_obj_relative_health(unsigned short,float&)const;
};
enum class DamageCause{};
struct DamageEntry {enum class SubObjFate{None};};
struct DamageList {DamageCause Cause{};unsigned InflictorId=0,InflictorOwner=0;std::vector<std::pair<unsigned short,float>> changes;
    void add_damage_entry(unsigned short id,float hp,DamageEntry::SubObjFate){changes.push_back({id,hp});}
};
struct EqObj {CEqObj* ship;unsigned get_id()const{return 1;}CEqObj* csimple()const{return ship;}
    void apply_damage_list(DamageList const& list){for(auto const& change:list.changes){
        if(change.first==SUBOBJ_ID_ROOT)ship->hull=change.second;
        for(auto* x:ship->EquipManager.items)if(x->Id==change.first){x->hp=change.second;if(x->hp<=0)x->active=false;}
        for(auto* x:ship->ArchGroups.items)if(x->Arch->Id==change.first)x->hp=change.second;
    }}
};
struct SrvRepairDroid {CEquip* Equip;EqObj* Owner;float RepairTimer=0;unsigned short TargetId=SUBOBJ_ID_NONE;
    bool update(float);unsigned short pick_target()const;
};
"""
CHECK=r"""
int main(){
    CEqObj ship;EqObj owner{&ship};CERepairDroid device;device.Owner=&ship;ship.EquipManager.items={&device};
    SrvRepairDroid repair{&device,&owner};
    // Production Common helpers intentionally omit root HP/max HP, unlike
    // relative health. This distinction previously let the mock hide the bug.
    float value=0;
    assert(!ship.get_sub_obj_hit_pts(SUBOBJ_ID_ROOT,value));
    assert(!ship.get_sub_obj_max_hit_pts(SUBOBJ_ID_ROOT,value));
    assert(ship.get_sub_obj_relative_health(SUBOBJ_ID_ROOT,value)&&value==.5f);
    assert(repair.pick_target()==SUBOBJ_ID_ROOT);
    repair.update(1);repair.update(1);assert(ship.hull==50&&device.hp==100);
    device.active=false;repair.update(3);assert(ship.hull==50&&repair.RepairTimer==0);
    device.active=true;repair.update(3);assert(ship.hull==80&&device.hp==70);
    // A manual nanobot repair between ticks must not waste the droid's reserve.
    repair.update(1);ship.hull=99;repair.update(2);assert(ship.hull==100&&device.hp==69);
    repair.update(20);assert(device.hp==69&&ship.hull==100);
    ship.hull=50;device.hp=4;repair.update(3);assert(ship.hull==54&&device.hp==0&&!device.active);
    device.hp=100;device.active=true;ship.hull=0;repair.update(3);assert(ship.hull==0&&device.hp==100);
    ship.hull=100;CEquip gun;gun.attached=true;gun.Id=41;gun.Type=0x80;gun.hp=10;ship.EquipManager.items.push_back(&gun);
    assert(repair.pick_target()==41);repair.update(3);assert(gun.hp==40&&device.hp==70);
    gun.hp=0;assert(repair.pick_target()==SUBOBJ_ID_NONE);repair.update(3);assert(gun.hp==0&&device.hp==70);
    GroupArch arch;CArchGroup group{&arch,50};ship.ArchGroups.items.push_back(&group);
    repair.update(3);assert(group.hp==80&&device.hp==40);
    group.hp=0;assert(repair.pick_target()==SUBOBJ_ID_NONE);
    // Zero-rate quest keys, disabled devices and invalid timesteps never repair.
    ship.hull=50;device.arch.RepairRate=0;repair.update(3);assert(ship.hull==50);
    device.arch.RepairRate=10;repair.update(NAN);repair.update(-1);assert(ship.hull==50);
    // Installed improved device: 555 HP/s, 10,000 HP reserve on a larger hull.
    ship.maxHull=10000;ship.hull=4000;device.hp=10000;device.arch.RepairRate=555;
    repair.RepairTimer=0;repair.TargetId=SUBOBJ_ID_NONE;
    repair.update(1);repair.update(1);assert(ship.hull==4000);
    repair.update(1);assert(ship.hull==5665&&device.hp==8335);
    ship.hull=9990;repair.update(3);assert(ship.hull==10000&&device.hp==8325);
    puts("PASS: production server automatic repair; toggle; hull/equipment/groups; separate finite reserve; manual repair coexistence; exhaustion; no resurrection; idle/invalid inputs");
}
"""
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    production='namespace SubObjectID {\n'+''.join(function('src/Common/common_subobjectid.cpp',sig) for sig in ('bool IsArchGroupID(', 'bool IsEquipID('))+'}\n'
    production+=''.join(function('src/Common/common_ceqobj.cpp',sig) for sig in (
        'bool CEqObj::get_sub_obj_hit_pts(', 'bool CEqObj::get_sub_obj_max_hit_pts(', 'bool CEqObj::get_sub_obj_relative_health('))
    source=STUB+production+function('src/Server/server_gameobject.cpp','bool SrvRepairDroid::update(')+function('src/Server/server_gameobject.cpp','unsigned short SrvRepairDroid::pick_target(')+CHECK
    (OUT/'check.cpp').write_text(source)
    vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk=Path('C:/Program Files (x86)/Windows Kits/10');v='10.0.26100.0';env=dict(os.environ)
    env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/v/x for x in ('ucrt','shared','um')]))
    env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/v/x/'x86' for x in ('ucrt','um')]))
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=OUT,env=env,check=True)
    subprocess.run([str(OUT/'check.exe')],cwd=OUT,check=True)
if __name__=='__main__':main()
