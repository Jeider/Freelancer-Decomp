"""Exercise the actual courier docked objective against DestroyMission's contract."""
from pathlib import Path
import subprocess
import sys
from check_orders import function

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    source=(ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    method=function(source,'void launchObjective(')
    text=r'''
#include <cassert>
#include <cstring>
#include <cstdio>
#define FDUMP(...) ((void)0)
enum class Stage {Boarding,TransferIn};
struct Vector {float x,y,z;};
struct FNNObjectiveNavMarker {
    int Ids=0;unsigned bHidden=1;
    struct {unsigned Type=1;} Objective;
    struct {unsigned Data[5]{};} Marker;
    bool built=false;void BuildDescription(){built=true;}
};
struct Player {
    struct List {
        FNNObjectiveNavMarker item;bool present=false;unsigned kind=0;
        FNNObjectiveNavMarker* GetFront(){return present?&item:nullptr;}
        FNNObjectiveNavMarker* Add(unsigned type,void*){kind=type;present=true;item={};return &item;}
    } Objectives;
    void ClearObjectives(){Objectives.present=false;}
};
struct ContentPlayer {
    void* ShipObject=nullptr;
    unsigned GetSystemId(){return 42;}
    void GetPosition(Vector* p){*p={1,2,3};}
};
struct Mission {
    struct {unsigned launch=238276;} config;
    struct {Stage stage=Stage::Boarding;} state;
    struct {Vector position{};} source;
    struct {void Reset(){}} NnPath;
    unsigned PlayerId=1,pendingObject=7,objectiveObject=8,objectiveName=9,sends=0;
    ContentPlayer content;ContentPlayer* PlayerState=&content;Player player;
    unsigned ship(){return 999;} // stale server ID while Content is docked
    Player* GetOrCreatePlayer(unsigned){return &player;}
    void RenumberObjectives(unsigned){
        ++sends;auto& o=player.Objectives.item;
        assert(player.Objectives.kind==2 && !o.bHidden && o.Ids==238276 && o.Objective.Type==0x10 && o.built);
        assert(o.Marker.Data[0]==42 && o.Marker.Data[1]==0);
        Vector p;std::memcpy(&p,&o.Marker.Data[2],sizeof(p));assert(p.x==1 && p.y==2 && p.z==3);
    }
'''+method+r'''
};
int main(){
    Mission m;m.launchObjective();assert(m.sends==1 && m.pendingObject==0 && m.objectiveObject==0);
    m.launchObjective();assert(m.sends==1); // no repeated alert on heartbeat
    m.player.ClearObjectives();m.launchObjective();assert(m.sends==2); // restore missing objective
    m.content.ShipObject=&m;m.player.ClearObjectives();m.launchObjective();assert(m.sends==2);
    m.content.ShipObject=nullptr;m.state.stage=Stage::TransferIn;m.launchObjective();assert(m.sends==2);
    m.state.stage=Stage::Boarding;m.PlayerState=nullptr;m.launchObjective();assert(m.sends==2);
    puts("PASS: launch objective uses DestroyMission nav marker/type 0x10; stale ship ID accepted while docked; one notification; repair missing goal; no launch goal in space/transfer");
}
'''
    out=ROOT/'src/obj/train_courier/launch_objective';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'check.cpp';cpp.write_text(text,encoding='utf-8')
    compiler,env=compiler_env();exe=out/'check.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',str(cpp),
                    '/Fo'+str(out/'check.obj'),'/Fe'+str(exe)],env=env,cwd=out,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)


if __name__=='__main__':main()
