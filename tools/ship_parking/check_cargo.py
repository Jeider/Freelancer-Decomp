"""Exercise parking's real cache decoder and inventory cargo accounting together."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/customization'))
from check import function
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

out = ROOT / 'src/obj/ship_parking/cargo_check'
out.mkdir(parents=True, exist_ok=True)
park = (ROOT / 'src/freelancer/Client/nn_ship_park.cpp').read_text(encoding='utf-8')
equip = (ROOT / 'src/Common/common_equipdesc.cpp').read_text(encoding='utf-8')
code = r'''
#include <cassert>
#include <cstring>
#include <list>
#include <set>
#include <string>
#include <cstdio>
char const* StringAlloc(char const* text,bool) {
    static std::set<std::string> strings;
    return strings.insert(text).first->c_str();
}
struct CacheString {char const* Value;};
namespace Archetype {
struct Equipment {float Volume;};
Equipment* GetEquipment(unsigned id) {static Equipment a[]={{0},{5},{25},{2}};return &a[id];}
}
struct EquipDesc {
    static CacheString const CARGO_BAY_HP_NAME;
    unsigned ArchId=0;int Count=1;float Health=1;bool bEquipped=false;
    char const* Hardpoint=CARGO_BAY_HP_NAME.Value;
    void set_arch_id(unsigned id){ArchId=id;}void set_count(int n){Count=n;}
    void set_status(float h){Health=h;}void set_equipped(bool b){bEquipped=b;}
    void set_hardpoint(CacheString hp){Hardpoint=hp.Value;}
    double get_cargo_space_occupied()const;
};
CacheString const EquipDesc::CARGO_BAY_HP_NAME={StringAlloc("BAY",false)};
struct EquipDescList {std::list<EquipDesc> Items;float get_cargo_space_occupied()const;};
struct PlayerShipCacheEquip {unsigned ArchId;int Count;float Health;bool bEquipped;char Hardpoint[64];};
PlayerShipCacheEquip rows[]={
    {1,1,1,true,""}, {2,1,1,true,"-"}, {2,1,1,true,"HpShield01"},
    {3,7,1,false,"BAY"}, {1,2,1,false,"BAY"}
};
struct FShipCacheApi {
    int EquipCount(unsigned,int index)const{return index==0?5:0;}
    int EquipAt(unsigned,int,int i,PlayerShipCacheEquip* out)const{*out=rows[i];return 0;}
};
FShipCacheApi const* CacheApi(){static FShipCacheApi api;return &api;}
unsigned GetPlayerConnectionId(){return 1;}
'''
code += function(equip, 'double EquipDesc::get_cargo_space_occupied() const')
code += function(equip, 'float EquipDescList::get_cargo_space_occupied() const')
code += function(park, 'void CachedEquipment(')
code += r'''
int main() {
    EquipDescList cached;CachedEquipment(0,cached);
    assert(cached.Items.size()==5);
    auto i=cached.Items.begin();assert(!strcmp(i->Hardpoint,""));++i;
    assert(!strcmp(i->Hardpoint,""));++i;
    assert(!strcmp(i->Hardpoint,"HpShield01"));
    assert(cached.get_cargo_space_occupied()==24); // 7*2 + 2*5, no installed gear
    EquipDescList current;
    for(auto const& row:rows) {
        EquipDesc d;d.set_arch_id(row.ArchId);d.set_count(row.Count);d.set_equipped(row.bEquipped);
        d.set_hardpoint({StringAlloc(!strcmp(row.Hardpoint,"-")?"":row.Hardpoint,false)});
        current.Items.push_back(d);
    }
    assert(current.get_cargo_space_occupied()==cached.get_cargo_space_occupied());
    EquipDescList empty;CachedEquipment(1,empty);assert(empty.get_cargo_space_occupied()==0);
    CachedEquipment(-1,empty);assert(empty.Items.empty());
    cached.Items.back().set_count(100);assert(cached.get_cargo_space_occupied()==514);
    puts("PASS: current/parked cargo parity; empty, legacy internal and named hardpoints; counts and over-capacity values");
}
'''
(out / 'check.cpp').write_text(code, encoding='utf-8')
compiler, env = compiler_env()
subprocess.run([str(compiler/'cl.exe'), '/nologo', '/std:c++17', '/EHsc', '/W4', '/WX',
                'check.cpp', '/Fe:check.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out/'check.exe')], cwd=out, check=True)
