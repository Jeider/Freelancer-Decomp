"""Reproduce the reused locomotive's busy berth with real Content queue functions."""
from pathlib import Path
import subprocess
import sys
from check_transfer_docking import block
from check_transfer_controls import docking

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/train_courier/evacuation/checks'
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    source = (ROOT/'src/Content/DockQueues.cpp').read_text(encoding='utf-8')
    # Reuse the world/permission stubs, replacing their artificial terminal
    # selector with the actual berth reservation and waiting queue machinery.
    code = docking().split('int main(){')[0]
    code = code.replace('#include <cassert>', '#include <cassert>\n#include <list>\n#include <map>\n#include <cfloat>\n#include <cstdlib>')
    code = code.replace('void GetType(unsigned,unsigned& type){type=0;}',
                        'int GetType(unsigned,unsigned& type){type=0;return 0;}')
    code = code.replace('void GetTerminalInfo(unsigned,int,TerminalInfo&){}',
                        'int GetTerminalInfo(unsigned,int index,TerminalInfo& info){info.Value=6;return index==0?0:-1;}\n'
                        'int GetHardpoint(unsigned,char const*,Vector* position,void*){*position={};return 0;}')
    code = code.replace('struct TerminalInfo{unsigned Value=6;};', 'struct TerminalInfo{unsigned Value=6;char Name[8]="berth";};')
    fake = 'int ChooseDockTerminal(std::vector<unsigned>const*,unsigned const*,Vector const*,int* index){*index=0;return terminalResponse;}'
    code = code.replace(fake, 'int ChooseDockTerminal(std::vector<unsigned>const*,unsigned const*,Vector const*,int*);')
    # Queue completion can grant a waiting ship; record every native response.
    code = code.replace('namespace SpaceObj{', 'namespace SpaceObj{\n'
        'struct Answer{unsigned ship,target;int index,response;};std::vector<Answer> answers;\n'
        'void Dock(unsigned ship,unsigned target,int index,int response){answers.push_back({ship,target,index,response});}\n')
    code += r'''
#define FDUMP(...) ((void)0)
using DOCK_HOST_RESPONSE=int;
struct FDockQueueEntry{
    unsigned SystemId=7,ShipId=0,DockTargetId=0;int DockIndex=-1;
    bool bField_0x10=false;double Time=0;bool bField_0x20=false;
};
struct FDockTerminal{unsigned DockTargetId;int DockIndex;bool bOccupied;};
std::list<FDockQueueEntry> GDockingShips,GDockWaitingShips;
std::vector<FDockTerminal> GDockTerminals;
std::map<unsigned,std::list<int>> GDockLaunchQueues;
double GetContentGameTime(){return 1;}
bool DoesTerminalFitClasses(unsigned type,std::vector<unsigned> const*){return type==6;}
struct Rep{int GetReputation(){return 1;}}repHandle;
struct FContentShipBase{
    unsigned SpaceObjId=0;std::vector<unsigned> ClassIds{1};Rep* ReputationHandle=&repHandle;
    void GetPosition(Vector* out){*out={};}
};
struct FSystemInfo{
    std::map<unsigned,FContentShipBase> ships;
    FContentShipBase* FindShip(unsigned id){auto it=ships.find(id);return it==ships.end()?nullptr:&it->second;}
}world;
FSystemInfo* FindSystemInfo(unsigned const*){return &world;}
struct FGcsDockGrantedEvent{
    FSystemInfo* System=nullptr;unsigned DockType=0,Speaker=0,Listener=0;int DockIndex=-1,Response=5;
    bool bWaitedInQueue=false;
};
struct{void QueueConversation(FGcsDockGrantedEvent*){}}GGcsConversations;
int GetDockTypeForClasses(unsigned const*,std::vector<unsigned>const*){return 6;}
void BreakFormationAtDock(unsigned const*,unsigned const*,bool,bool){}
void DockFormationFollowers(unsigned const*,unsigned const*,unsigned const*,int const*){}
int TryStartDocking(unsigned,unsigned const*,unsigned const*,int*,bool);
void FinishDocking(std::list<FDockQueueEntry>::iterator*);
'''
    for marker in ('bool IsDockTerminalInUse(', 'void __cdecl MarkDockTerminal(',
                   'int __cdecl ChooseDockTerminal(', 'int __cdecl TryStartDocking(',
                   'void __cdecl FinishDocking(', 'void FinishShipTransferDocking('):
        code += '\n'+block(source, marker)+'\n'
    mission = (ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    callback = block(mission, 'int spaceTransfer(')
    assert callback.index('if(phase==1)FinishShipTransferDocking(p->source);') < callback.index('evacuationTransfer(p,phase)')
    code += r'''
FDockQueueEntry entry(unsigned ship,unsigned target,int index=0){
    FDockQueueEntry result;result.ShipId=ship;result.DockTargetId=target;result.DockIndex=index;return result;
}
int permission(unsigned ship,unsigned target){
    int rep=1,index=-1;std::vector<unsigned> classes{1};Vector position;
    return CheckDockPermission(&classes,&rep,&ship,&position,&target,&index);
}
void live(unsigned ship){world.ships[ship].SpaceObjId=ship;}
int main(){
    parked=false;returnAllowed=true;
    // First boarding reserves the berth for the original fighter (12). LAND
    // is intercepted, then fighter 12 is removed without DockComplete.
    live(34);live(99);GDockingShips.push_back(entry(12,33));
    GDockingShips.push_back(entry(99,77)); // an unrelated occupied terminal
    assert(permission(34,33)==3); // reproduces the reported queue, despite owner access
    FinishShipTransferDocking(12);
    assert(permission(34,33)==4 && permission(34,77)==3);
    assert(GDockingShips.size()==1 && !GDockTerminals.back().bOccupied);
    assert(pub::SpaceObj::answers.empty()); // no cancel sent to deleted fighter
    // The same solar ID can be reused for many evacuations and reboardings.
    for(unsigned ship:{34u,36u,38u}){
        live(ship);unsigned target=33;int index=-1;
        assert(TryStartDocking(7,&ship,&target,&index,false)==4);
        assert(IsDockTerminalInUse(33,0));world.ships.erase(ship);
        FinishShipTransferDocking(ship);
        assert(!IsDockTerminalInUse(33,0) && permission(40,33)==4);
        FinishShipTransferDocking(ship); // repeated completion is harmless
        assert(IsDockTerminalInUse(77,0));
    }
    // Remove every source reservation/wait entry before waking other waiters.
    live(50);live(51);GDockingShips.push_back(entry(44,33));
    GDockingShips.push_back(entry(44,88));
    GDockWaitingShips.push_back(entry(44,33));GDockWaitingShips.push_back(entry(50,33));
    GDockWaitingShips.push_back(entry(51,77));
    FinishShipTransferDocking(44);
    assert(pub::SpaceObj::answers.size()==1);
    assert(pub::SpaceObj::answers[0].ship==50 && pub::SpaceObj::answers[0].response==4);
    assert(GDockWaitingShips.size()==1 && GDockWaitingShips.front().ShipId==51);
    assert(IsDockTerminalInUse(33,0) && IsDockTerminalInUse(77,0) && !IsDockTerminalInUse(88,0));
    auto size=GDockingShips.size();FinishShipTransferDocking(0);FinishShipTransferDocking(123);
    assert(GDockingShips.size()==size && pub::SpaceObj::answers.size()==1);
    puts("PASS actual dock queues: reproduced stale berth; repeated board/evacuate/return frees it; unrelated ports and live waiting grants preserved");
}
'''
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'transfer_queue.cpp').write_text(code, encoding='utf-8')
    compiler, env = compiler_env()
    subprocess.run([str(compiler/'cl.exe'), '/nologo', '/EHsc', '/std:c++17',
                    'transfer_queue.cpp', '/Fe:transfer_queue.exe'], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'transfer_queue.exe')], cwd=OUT, check=True, timeout=10)


if __name__ == '__main__':
    main()
