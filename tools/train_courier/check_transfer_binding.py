"""Execute the production Content ship-rebinding method with a fake object DB."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    text = (ROOT / 'src/Content/PlayerState.cpp').read_text(encoding='utf-8')
    start = text.index('bool FContentPlayerShip::RebindShip(')
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    method = text[start:end]
    code = r'''
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
unsigned world=7, type=0x20000;
namespace pub { namespace SpaceObj {
int GetSystem(unsigned ship,unsigned& out) { out=world;return ship==42?0:-1; }
int GetType(unsigned,unsigned& out) { out=type;return 0; }
}}
unsigned CreateID(char const* s) { return std::strcmp(s,"fighter")==0?11:12; }
void GetShipMissionProperties(unsigned arch,std::vector<unsigned>* ids) { ids->push_back(arch); }
struct SystemRecord { unsigned SystemId=7; } record;
struct FContentPlayerShip {
    SystemRecord* System=&record;
    unsigned SpaceObjId=21,ShipArchId=90,TargetId=65;
    unsigned TradeLaneEntryRing=3,TradeLaneEndRing=4;
    std::vector<unsigned> ClassIds{90,11},Damage{55};
    unsigned HostileContactCount=8;
    bool bInCombat=true;
    bool RebindShip(unsigned,unsigned);
};
''' + method + r'''
int main() {
    FContentPlayerShip ship;
    auto* identity=&ship;
    assert(!ship.RebindShip(0,91));
    assert(!ship.RebindShip(42,0));
    world=8; assert(!ship.RebindShip(42,91));
    assert(ship.SpaceObjId==21 && ship.ShipArchId==90 && ship.TargetId==65);
    world=7; assert(ship.RebindShip(42,91));
    assert(&ship==identity && ship.System==&record);
    assert(ship.SpaceObjId==42 && ship.ShipArchId==91);
    assert((ship.ClassIds==std::vector<unsigned>{91,12}));
    assert(ship.bInCombat && ship.HostileContactCount==8);
    assert(ship.TargetId==0 && ship.Damage.empty());
    assert(ship.TradeLaneEntryRing==0 && ship.TradeLaneEndRing==0);
    type=0x10000;assert(ship.RebindShip(42,92));assert(ship.RebindShip(42,92));
    assert((ship.ClassIds==std::vector<unsigned>{92,11}));
    puts("PASS Content rebind: new ship/class, same player/system/combat state, invalid target leaves state intact");
}
'''
    out = ROOT / 'out/train_space_transfer/check'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'binding.cpp').write_text(code, encoding='utf-8')
    compiler, env = compiler_env()
    subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17',
                    'binding.cpp', '/Fe:binding.exe'], cwd=out, env=env, check=True)
    subprocess.run([str(out / 'binding.exe')], cwd=out, env=env, check=True, timeout=10)

if __name__ == '__main__':
    main()
