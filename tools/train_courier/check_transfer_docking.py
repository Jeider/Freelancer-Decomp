"""Run the production dock hook and courier authorization with fake world objects."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env


def block(text, marker):
    start = text.index(marker)
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def main():
    server = (ROOT / 'src/Server/player_ship_transfer.inl').read_text(encoding='utf-8')
    mission = (ROOT / 'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    update = (ROOT / 'src/Server/IServerImpl.cpp').read_text(encoding='utf-8')
    authorize = block(mission[mission.index('int spaceTransfer('):], 'if(phase==0)')
    hook = block(update, 'if (SinglePlayer() && Obj && Obj->is_player() &&')
    code = r'''
#include <cassert>
#include <cstdio>
#include "player_ship_transfer_state.h"
#define FREELANCER_RPG_WORLD
#define FDUMP(...) ((void)0)
namespace PlayerShipTransfer {
struct Packet { unsigned player=0,anchor=0,base=0,source=0,system=0; bool returning=false;
    int position=0,orientation=0; };
}
bool sp=true, mp=false, swapped=false;
bool SinglePlayer() { return sp; }
bool IsMPServer() { return mp; }
enum class Stage { Boarding, TransferOut, Other };
struct { Stage stage=Stage::Boarding; } state;
unsigned boarding=20,transferBase=30;
int transferPosition=40,transferOrientation=50;
struct PlayerSlot { unsigned ship_object_id=10,system_id=7; } slot;
bool ValidPlayer(unsigned p,PlayerSlot*& out) { out=&slot;return p==1; }
int Authorize(PlayerShipTransfer::Packet* p,int phase) {
''' + authorize + r'''
    return 0;
}
auto SpaceTransferMission() { return &Authorize; }
struct { PlayerShipTransfer::State state; PlayerShipTransfer::Packet request;
    bool clientReady=true,rejected=false; } GSpaceTransfer;
unsigned queued=0,landed=0;
bool QueueSpaceTransfer(PlayerShipTransfer::Packet& p) {
    if(!GSpaceTransfer.clientReady)return false;
    ++queued;GSpaceTransfer.request=p;
    return GSpaceTransfer.state.begin(true,p.player,p.system,p.source);
}
''' + block(server, 'bool PlayerShipTransferDock(') + r'''
struct Object {
    unsigned OwnerPlayer=1;
    bool is_player() { return true; }
    Object* csimple() { return this; }
    unsigned get_id() { return boarding; }
} ship,solar;
struct NodeType { struct { unsigned BaseId=0; } Entry; NodeType* Next=nullptr; };
void RunDock(bool target,unsigned base) {
    NodeType node;node.Entry.BaseId=base;
    auto* Obj=&ship;auto* DockTarget=target?&solar:nullptr;
    auto* Node=&node;
    while(Node) {
''' + hook + r'''
        ++landed;Node=Node->Next;
    }
}
void Reset() { GSpaceTransfer.state.resetSession();GSpaceTransfer.rejected=false;queued=landed=0; }
int main() {
    // Normal docking and Escape/skip animation must reach the same transaction.
    RunDock(true,transferBase);assert(queued==1 && landed==0);
    RunDock(false,transferBase);assert(queued==1 && landed==0); // duplicate skip
    Reset();RunDock(false,transferBase);
    assert(queued==1 && landed==0 && GSpaceTransfer.request.anchor==boarding);
    Reset();RunDock(false,99);assert(queued==0 && landed==1); // ordinary base
    Reset();GSpaceTransfer.clientReady=false;RunDock(false,transferBase);
    assert(queued==0 && landed==0 && GSpaceTransfer.rejected); // no hidden fallback
    Reset();RunDock(true,transferBase);assert(landed==0 && GSpaceTransfer.rejected);
    Reset();GSpaceTransfer.clientReady=true;swapped=true;RunDock(false,transferBase);
    assert(queued==0 && landed==1); // not a boarding mission
    swapped=false;Reset();sp=false;RunDock(false,transferBase);assert(landed==1 && queued==0);
    Reset();sp=true;mp=true;RunDock(true,transferBase);assert(landed==1 && queued==0);
    puts("PASS docking: solar and base-only skip, duplicates, ordinary base, unavailable client, MP isolation");
}
'''
    out = ROOT / 'out/train_space_transfer/check'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'docking.cpp').write_text(code, encoding='utf-8')
    compiler, env = compiler_env()
    subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17',
                    '/I' + str(ROOT / 'src/include'), 'docking.cpp', '/Fe:docking.exe'],
                   cwd=out, env=env, check=True)
    subprocess.run([str(out / 'docking.exe')], cwd=out, env=env, check=True, timeout=10)


if __name__ == '__main__':
    main()
