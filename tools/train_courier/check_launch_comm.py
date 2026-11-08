"""Run production greeting scheduling against launch, cancellation and docking events."""
from pathlib import Path
import subprocess
import sys
from check_orders import function

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    source=(ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    methods='\n'.join(function(source,'void '+name+'(') for name in
                      ('armBoardingComm','updateBoardingComm','completeBoardingComm'))
    text=r'''
#include <cassert>
#include <cstdlib>
#include <cstdio>
#define FDUMP(...) ((void)0)
enum class Stage {Boarding,TransferIn};
enum class CommResult {SUCCESS=0,FAILED=1,CANCELLED=2,TIMEOUT=3};
struct Mission {
    struct {float boardingCommDelay=3,boardingCommDelayMax=5;} config;
    struct {Stage stage=Stage::Boarding;} state;
    unsigned PlayerId=1,boarding=2,boardingCommId=0,boardingCommListener=0,sends=0;
    bool boardingLaunchReady=false,boardingSpoken=false;
    float boardingCommWait=0;
    void say(char const*){++sends;boardingCommId=11;boardingCommListener=7;}
'''+methods+r'''
};
int main(){
    for(unsigned seed=0;seed<100;++seed){
        srand(seed);Mission m;
        m.updateBoardingComm(60);assert(m.sends==0); // scene is launching
        m.armBoardingComm();assert(m.boardingCommWait>=3 && m.boardingCommWait<=5);
        m.updateBoardingComm(2);assert(m.sends==0);
        float left=m.boardingCommWait;m.armBoardingComm();assert(m.boardingCommWait==left);
        m.updateBoardingComm(left+.01f);assert(m.sends==1);
        m.updateBoardingComm(60);assert(m.sends==1); // one outstanding greeting
        unsigned unrelated[]={8,0,0,11,2};m.completeBoardingComm(unrelated);assert(m.boardingSpoken);
        unsigned cancelled[]={7,0,0,11,2};m.completeBoardingComm(cancelled);
        assert(!m.boardingSpoken);m.updateBoardingComm(1);assert(m.sends==1);
        m.updateBoardingComm(1.1f);assert(m.sends==2);
        unsigned success[]={7,0,0,11,0};m.completeBoardingComm(success);
        m.updateBoardingComm(60);assert(m.sends==2);
        Mission docked;docked.armBoardingComm();docked.state.stage=Stage::TransferIn;
        docked.updateBoardingComm(60);assert(docked.sends==0);
    }
    Mission custom;custom.config={0,0};custom.armBoardingComm();custom.updateBoardingComm(.01f);assert(custom.sends==1);
    puts("PASS: 100 greeting schedules; no comm before launch; 3-5 sec delay; cancelled comm retry; no duplicates or obsolete greeting after docking; configurable delay");
}
'''
    out=ROOT/'src/obj/train_courier/launch_comm';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'check.cpp';cpp.write_text(text,encoding='utf-8')
    compiler,env=compiler_env();exe=out/'check.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',str(cpp),
                    '/Fo'+str(out/'check.obj'),'/Fe'+str(exe)],env=env,cwd=out,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)


if __name__=='__main__':main()
