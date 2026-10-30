"""Exercise production zone selection and ship drag with independent zone effects."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/zone_drag_check'


def function(file, signature):
    source = (ROOT / 'src/Common' / file).read_text(encoding='utf-8-sig')
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


STUB = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
#include <initializer_list>
bool healing=false;
#define HEALING_ON() healing
struct Vector {float x=0,y=0,z=0;};
struct ZONE {
    float DragModifier=1,Interference=0,Damage=0,Radius=100;
    mutable int PhysicalEffect=-1;
    bool inside=true;
    bool HasPhysicalEffect() const;
    float GetDragModifier() const{return DragModifier;}
    float GetInterference() const{return Interference;}
    float GetRadius() const{return Radius;}
    bool InZone(Vector const&,float)const{return inside;}
};
namespace Universe {using IZone=ZONE;}
namespace Geometry {struct Sphere {Vector Center;float Radius;};}
struct FSpatialQueryResult {unsigned Capacity=0,Count=0;ZONE const* Items[8]={};};
struct SpatialTree {std::vector<ZONE const*> zones;};
int SpatialFill(SpatialTree* tree,Geometry::Sphere const*,FSpatialQueryResult* result){
    result->Count=static_cast<unsigned>(tree->zones.size());
    for(unsigned i=0;i<result->Count;++i)result->Items[i]=tree->zones[i];
    return result->Count!=0;
}
namespace CmnUniverse {
constexpr float kNoZoneRadius=1e20f;
struct SYSTEM {
    SpatialTree* Spatial=nullptr;
    void BuildZoneTree()const{}
    Universe::IZone const* GetSmallestPhysicalZoneAt(Vector const*)const;
};
}
struct CSimple {
    ZONE const* ZoneAtA4=nullptr;
    float ScannerInterference=0; // production field stores immersion
    float get_scanner_interference()const;
};
namespace Archetype {struct Ship {float LinearDrag=10,NudgeForce=80;};}
struct CEquip {bool active=true;bool IsActive()const{return active;}};
struct CEEngine:CEquip {
    int bCruiseActive=0;
    static CEEngine* cast(CEquip* e){return static_cast<CEEngine*>(e);}
    float GetThrust(float throttle)const{return 100*throttle;}
    float GetLinearDrag()const{return 20;}
    float GetCruiseThrust(float throttle)const{return 200*throttle;}
    float GetCruiseDrag()const{return 40;}
};
struct CEThruster:CEquip {
    static CEThruster* cast(CEquip* e){return static_cast<CEThruster*>(e);}
    float GetThrust()const{return 50;}
};
struct CEquipTraverser {unsigned index=0;explicit CEquipTraverser(unsigned){}};
struct CEquipManager {
    CEEngine* engine=nullptr;CEThruster* thruster=nullptr;
    CEquip const* FindFirst(unsigned)const{return engine;}
    CEquip* Traverse(CEquipTraverser& t){return t.index++==0?thruster:nullptr;}
};
void AddAdoxaEquipDrag(CEquipManager const&,float& drag){drag+=3;}
enum ThrustEquipType {ThrustEquipEngine,ThrustEquipThruster,ThrustEquipCruise,ThrustEquipTradelane};
struct CShip:CSimple {
    Archetype::Ship arch;CEquipManager EquipManager;
    Archetype::Ship const* shiparch()const{return &arch;}
    void collect_force_components(float,ThrustEquipType,float&,float&)const;
    double get_linear_drag()const;
};
'''

CHECK = r'''
bool near(double a,double b){return std::fabs(a-b)<.0001;}
int main(){
    Vector point;
    ZONE plain,dragOnly,interferenceOnly,damageOnly,healingOnly;
    dragOnly.DragModifier=3;interferenceOnly.Interference=.8f;
    damageOnly.Damage=15;healingOnly.Damage=-10;
    assert(!plain.HasPhysicalEffect());
    assert(dragOnly.HasPhysicalEffect() && dragOnly.HasPhysicalEffect());
    assert(interferenceOnly.HasPhysicalEffect() && damageOnly.HasPhysicalEffect());
    assert(!healingOnly.HasPhysicalEffect());
    healing=true;healingOnly.PhysicalEffect=-1;assert(healingOnly.HasPhysicalEffect());
    healing=false;
    SpatialTree tree;CmnUniverse::SYSTEM system;system.Spatial=&tree;
    for(ZONE* zone:{&dragOnly,&interferenceOnly,&damageOnly}){
        tree.zones={&plain,zone};assert(system.GetSmallestPhysicalZoneAt(&point)==zone);
    }
    // Existing smallest-containing-zone priority and exit behavior are retained.
    dragOnly.Radius=20;damageOnly.Radius=50;
    tree.zones={&damageOnly,&dragOnly};assert(system.GetSmallestPhysicalZoneAt(&point)==&dragOnly);
    dragOnly.inside=false;assert(system.GetSmallestPhysicalZoneAt(&point)==&damageOnly);
    damageOnly.inside=false;assert(!system.GetSmallestPhysicalZoneAt(&point));
    CEEngine engine;CEThruster thruster;CShip ship;
    ship.EquipManager.engine=&engine;ship.EquipManager.thruster=&thruster;
    // Changes in damage, interference and immersion must not change drag.
    for(float modifier:{1.f,2.f,5.f})for(float interference:{0.f,.7f})
    for(float damage:{0.f,30.f})for(float immersion:{0.f,.25f,1.f}){
        ZONE zone;zone.DragModifier=modifier;zone.Interference=interference;zone.Damage=damage;
        ship.ZoneAtA4=&zone;ship.ScannerInterference=immersion;
        assert(near(ship.get_scanner_interference(),interference*immersion));
        for(auto mode:{ThrustEquipEngine,ThrustEquipThruster,ThrustEquipCruise,ThrustEquipTradelane}){
            float force=-1,drag=-1;
            ship.collect_force_components(.5f,mode,force,drag);
            float base=mode==ThrustEquipCruise?50.f:30.f;
            assert(near(drag,base*modifier));
            float expectedForce=mode==ThrustEquipEngine?50.f:mode==ThrustEquipTradelane?40.f:100.f;
            assert(near(force,expectedForce));
            engine.bCruiseActive=mode==ThrustEquipCruise;
#ifdef FREELANCER_ADOXA
            assert(near(ship.get_linear_drag(),(base+3)*modifier));
#else
            assert(near(ship.get_linear_drag(),drag));
#endif
        }
    }
    ship.ZoneAtA4=nullptr;engine.bCruiseActive=0;
    float force,drag;ship.collect_force_components(.5f,ThrustEquipEngine,force,drag);
    assert(near(drag,30) && ship.get_scanner_interference()==0);
    ship.EquipManager.engine=nullptr;ship.ZoneAtA4=&dragOnly;
    ship.collect_force_components(1,ThrustEquipEngine,force,drag);
    assert(force==0 && near(drag,30));
    puts("PASS: drag-only zone selection; independent drag/interference/damage; engine, thruster, cruise, tradelane and zone exit");
}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    code = STUB + function('common_zone.cpp', 'bool ZONE::HasPhysicalEffect(')
    code += 'namespace CmnUniverse {\n' + function(
        'common_universe_system.cpp', 'Universe::IZone const* SYSTEM::GetSmallestPhysicalZoneAt(') + '}\n'
    code += function('common_csimple.cpp', 'float CSimple::get_scanner_interference(')
    code += function('common_cship.cpp', 'void CShip::collect_force_components(')
    code += function('common_cship.cpp', 'double CShip::get_linear_drag(')
    (OUT / 'check.cpp').write_text(code + CHECK)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10')
    version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include'] +
                            [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')])
    env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] +
                        [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')])
    for adoxa in (False, True):
        exe = 'adoxa.exe' if adoxa else 'retail.exe'
        defines = ['/DFREELANCER_ADOXA'] if adoxa else []
        subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                        '/EHsc', '/MT', *defines, 'check.cpp', '/Fe'+exe], cwd=OUT, env=env, check=True)
        subprocess.run([str(OUT/exe)], cwd=OUT, check=True)


if __name__ == '__main__':
    main()
