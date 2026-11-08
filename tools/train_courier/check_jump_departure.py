"""Regress the live jump order: dock committed, client teardown, switch done."""
from pathlib import Path
import subprocess
from check_orders import function,compiler_env

ROOT=Path(__file__).resolve().parents[2]
PREFIX=r'''
#include <cassert>
#include <cstdio>
#define FDUMP(...) ((void)0)
namespace pub {
namespace Controller {enum class EMessage {DockComplete=0x11,Msg0x25=0x25,DockRequest=0x12,Heartbeat=0x20,JumpInComplete=0x26};}
namespace SpaceObj {int GetJumpTarget(unsigned gate,unsigned& system,unsigned& target){system=gate==90?2:0;target=91;return gate==90?0:-1;}}
}
enum class Operation {Snapshot,SuspendCargo,ResumeCargo};
struct Cargo {unsigned pods=0;};
struct Packet {unsigned player=0,system=0;Operation operation;Cargo cargo;int result=0;};
bool coupled=true;unsigned snapshots=0,suspends=0;bool failSuspend=false;
bool bridge(Packet* p){
    assert(p->player==1);
    if(p->operation==Operation::Snapshot){++snapshots;p->cargo.pods=20;p->result=1;}
    else {assert(p->system==2);++suspends;if(!failSuspend){coupled=false;p->result=1;}}
    return true;
}
struct Mission {
    unsigned PlayerId=1,trailer=43,jumpDestination=0,currentSystem=1,resumes=0;bool jumping=false,jumpArrived=false,failResume=false;Cargo savedCargo;
    unsigned ship(){return 12;}
    unsigned system(){return currentSystem;}
    bool request(Operation op){assert(op==Operation::ResumeCargo);++resumes;return !failResume;}
    struct Status{bool coupled;};Status query(){return {::coupled};}
    void observeLoss(Cargo const& cargo){assert(cargo.pods==20);}
'''
MAIN=r'''
};
int main(){
    using M=pub::Controller::EMessage;
    unsigned gate[]={12,90,1},base[]={12,80,1},other[]={42,90,1};
    Mission m;
    m.onJumpDeparture(M::DockRequest,gate);m.onJumpDeparture(M::DockComplete,base);
    m.onJumpDeparture(M::DockComplete,other);m.onJumpDeparture(M::DockComplete,nullptr);
    assert(suspends==0 && !m.jumping);
    // The old 0x25-only handler gets here after the shared physics is gone.
    coupled=false;m.onJumpDeparture(M::Msg0x25,gate);assert(suspends==0 && !m.jumping);
    // Production must act at the earlier event, while the consist still exists.
    coupled=true;m.onJumpDeparture(M::DockComplete,gate);
    assert(m.jumping && m.jumpDestination==2 && snapshots==1 && suspends==1 && m.savedCargo.pods==20);
    // Client unload follows; the later event must not repeat or reset transit.
    coupled=false;m.onJumpDeparture(M::Msg0x25,gate);m.onJumpDeparture(M::DockComplete,gate);
    assert(m.jumping && snapshots==1 && suspends==1);
    // Destination physics exists while the client is still inside the tunnel;
    // JumpInAction has not started yet. A heartbeat must NOT resume cargo.
    m.currentSystem=2;assert(!m.resumeJump() && m.resumes==0);
    unsigned arrived[]={2,12},wrongShip[]={2,42},wrongSystem[]={3,12};
    m.onJumpArrival(M::JumpInComplete,nullptr);m.onJumpArrival(M::Heartbeat,arrived);
    m.onJumpArrival(M::JumpInComplete,wrongShip);m.onJumpArrival(M::JumpInComplete,wrongSystem);
    assert(!m.resumeJump() && m.resumes==0);
    m.onJumpArrival(M::JumpInComplete,arrived);
    m.failResume=true;assert(!m.resumeJump() && m.jumping && m.jumpArrived);
    m.failResume=false;assert(m.resumeJump() && !m.jumping && !m.jumpArrived && m.resumes==2);
    m.onJumpArrival(M::JumpInComplete,arrived);assert(m.resumeJump() && m.resumes==2);
    // Legitimately detached freight stays behind, not teleported with player.
    Mission detached;detached.onJumpDeparture(M::DockComplete,gate);assert(!detached.jumping && suspends==1);
    Mission fallback;coupled=true;failSuspend=true;fallback.onJumpDeparture(M::DockComplete,gate);
    assert(!fallback.jumping);failSuspend=false;fallback.onJumpDeparture(M::Msg0x25,gate);assert(fallback.jumping);
    // Each successive jump must receive its own completion.
    coupled=true;m.onJumpDeparture(M::DockComplete,gate);assert(m.jumping && !m.resumeJump() && m.resumes==2);
    puts("PASS: exact late-event failure reproduced; DockComplete snapshots/suspends before teardown; later 0x25 idempotent; detached cargo, ordinary base and other ships ignored; failed suspend can retry");
}
'''
def main():
    source=(ROOT/'src/Content/TrainCourier.cpp').read_text()
    out=ROOT/'src/obj/train_courier/jump_departure';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'departure.cpp';cpp.write_text(PREFIX+''.join(function(source,s) for s in ('void onJumpDeparture(', 'void onJumpArrival(', 'bool resumeJump('))+MAIN)
    compiler,env=compiler_env();exe=out/'departure.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',str(cpp),'/Fo'+str(out/'departure.obj'),'/Fe'+str(exe)],cwd=out,env=env,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)

if __name__=='__main__':main()
