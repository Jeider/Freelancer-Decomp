"""Exercise the production contact HUD rebind with different ship scanners."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from check_transfer_docking import block
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    source = (ROOT / 'src/freelancer/Client/hud_contact_list.cpp').read_text(encoding='utf-8')
    method = block(source, 'void HUD_ContactList::SetTarget(')
    code = r'''
#include <cassert>
#include <cstdio>
#include <vector>
struct CEquip { float range; float GetRadarRange() const { return range; } };
struct CShip {
    struct { CEquip* scanner; CEquip const* FindFirst(unsigned type) const {
        assert(type==0x80000); return scanner;
    }} EquipManager;
};
CShip* AsShip(CShip* ship) { return ship; }
struct IObjRW { CShip* ship; CShip* cobject() { return ship; } };
struct HUDItem { IObjRW* Target=nullptr; void SetTarget(IObjRW* p) { Target=p; } };
struct HUD_ContactList : HUDItem {
    CEquip* Scanner=nullptr;std::vector<unsigned> Contacts{11,12};
    unsigned ScrollPos=8;int bDirty=0;
    void SetTarget(IObjRW*);
};
''' + method + r'''
int main() {
    auto* oldScanner=new CEquip{2500};CEquip locomotive{8000};
    CShip oldShip{{oldScanner}},newShip{{&locomotive}},noScanner{{nullptr}};
    IObjRW oldObj{&oldShip},newObj{&newShip},emptyObj{&noScanner},nonShip{nullptr};
    HUD_ContactList hud;
    hud.SetTarget(&oldObj);assert(hud.Scanner==oldScanner);
    hud.Contacts={11,12};hud.ScrollPos=7;hud.bDirty=0;
    hud.SetTarget(&newObj);delete oldScanner;
    assert(hud.Target==&newObj && hud.Scanner==&locomotive);
    assert(hud.Scanner->GetRadarRange()==8000);
    assert(hud.Contacts.empty() && hud.ScrollPos==0 && hud.bDirty);
    hud.SetTarget(&emptyObj);assert(!hud.Scanner);
    hud.SetTarget(&newObj);hud.SetTarget(nullptr);assert(!hud.Scanner && !hud.Target);
    hud.SetTarget(&newObj);hud.SetTarget(&nonShip);assert(!hud.Scanner);
    CEquip personal{4000};oldShip.EquipManager.scanner=&personal;
    hud.SetTarget(&oldObj);assert(hud.Scanner->GetRadarRange()==4000);
    puts("PASS HUD rebind: old scanner released, new range, contacts invalidated, return/null/no-scanner targets");
}
'''
    # Rebinding must precede both the server's release and the client deletion.
    transfer = (ROOT / 'src/freelancer/Client/player_spawn.cpp').read_text(encoding='utf-8')
    transfer = block(transfer, 'bool UpdatePlayerShipTransfer()')
    assert transfer.index('HudElementListSetTarget(') < transfer.index('Operation::Finish') < transfer.index('delete previous;')
    out = ROOT / 'out/train_space_transfer/check'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'hud.cpp').write_text(code, encoding='utf-8')
    compiler, env = compiler_env()
    subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17',
                    'hud.cpp', '/Fe:hud.exe'], cwd=out, env=env, check=True)
    subprocess.run([str(out / 'hud.exe')], cwd=out, env=env, check=True, timeout=10)


if __name__ == '__main__':
    main()
