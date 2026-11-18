"""Reproduce campaign defeat and verify the courier's immediate soft failure."""
from pathlib import Path
import subprocess
import sys
from check_transfer_docking import block
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/train_courier/evacuation/checks'
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    courier=(ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    objects=(ROOT/'src/Content/MissionObject.cpp').read_text(encoding='utf-8')
    script=(ROOT/'src/Content/MissionScript.cpp').read_text(encoding='utf-8')
    player=(ROOT/'src/Content/PlayerState.cpp').read_text(encoding='utf-8')
    code=r'''
#include <cassert>
#include <cstdio>
#include <vector>
#include <map>
enum MissionMessageType{MISSION_MSG_TYPE_0=0,MISSION_MSG_TYPE_2=2};
struct FmtStr{unsigned id=0;void begin_mad_lib(unsigned n){id=n;}void end_mad_lib(){}};
bool defeatScreen=false;int messages=0,missionChanges=0;unsigned clientMission=9;
namespace pub{namespace Player{
void DisplayMissionMessage(unsigned,FmtStr const&,MissionMessageType kind,bool){++messages;if(kind==0)defeatScreen=true;}
void GetGroupMembers(unsigned player,std::vector<unsigned>& members){members.push_back(player);}
void SetMsnID(unsigned,unsigned id,unsigned,bool,unsigned){clientMission=id;}
}namespace Controller{
enum class EMessage{PlayerMissionChanged};
void _SendMessage(unsigned,EMessage,unsigned const*){++missionChanges;}
}}
struct FContentPlayerState{
 unsigned PlayerId=1,ValueD8=9,flags=7;int failures=0;
 struct Vnpc{unsigned Values[4]={0,0,0,1};};std::vector<Vnpc> Vnpcs{{}};
 unsigned GetLiveMission(){return ValueD8;}void SetFlags(unsigned f){flags=f;}
 void CountRandomMissionFailed(int type){assert(type==7);++failures;}
 void EndLiveMission(unsigned,int,bool);
}player;
FContentPlayerState* FindContentPlayerState(unsigned id){return id==1?&player:nullptr;}
'''
    code+=block(player,'void LeaveLiveMission(')+'\n'+block(player,'void FContentPlayerState::EndLiveMission(')
    code+=r'''
struct FMissionObject{
 unsigned PlayerId=1,ControllerId=9;bool bPendingDestroy=false;int cleared=0,ended=0,destroyed=0;
 void ClearObjectives(){++cleared;}void DestroyMissionObjects(){++destroyed;}
 virtual void EndMission(){++ended;bPendingDestroy=true;}
 virtual void OnMissionFail();
};
struct FContentNpcShip{void SetField1b1(bool){}};
struct FMissionScript:FMissionObject{
 unsigned Field_0x2e8=1;std::map<unsigned,FContentNpcShip*> NpcObjects;
 void OnMissionFail() override;
};
'''
    code+=block(objects,'void FMissionObject::OnMissionFail(')
    code+=block(script,'void FMissionScript::OnMissionFail(')
    code+=r'''
enum class Stage{Deliver,Failed};
struct CourierMission:FMissionScript{
 bool failed=false;struct{Stage stage=Stage::Deliver;}state;struct{void Reset(){}}NnPath;
'''+block(courier,'void OnMissionFail() override')+r'''
};
void reset(){player=FContentPlayerState{};defeatScreen=false;messages=missionChanges=0;clientMission=9;}
int main(){
 reset();FMissionScript old;old.OnMissionFail();assert(defeatScreen); // Reproduces the reported lockout.
 reset();CourierMission mission;mission.OnMissionFail();
 assert(!defeatScreen && messages==1 && mission.failed && mission.state.stage==Stage::Failed);
 assert(mission.bPendingDestroy && mission.ended==1 && mission.cleared==1 && mission.destroyed==1);
 assert(player.GetLiveMission()==0 && clientMission==0 && missionChanges==1 && player.flags==0);
 assert(player.failures==1 && player.Vnpcs[0].Values[3]==3); // Failed contract, not completed/aborted campaign.
 mission.OnMissionFail();assert(player.failures==1 && messages==1 && mission.ended==1);
 // A new job can start without receiving any radio completion callback.
 assert(player.GetLiveMission()==0);player.ValueD8=10;clientMission=10;
 mission.OnMissionFail();assert(player.ValueD8==10 && clientMission==10);
 puts("PASS: reproduced legacy defeat screen; courier failure is immediate, nonfatal, idempotent and clears the live job for the next contract without waiting for speech");
}
'''
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'courier_failure.cpp').write_text(code,encoding='utf-8')
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17','courier_failure.cpp','/Fe:courier_failure.exe'],cwd=OUT,env=env,check=True)
    subprocess.run([str(OUT/'courier_failure.exe')],cwd=OUT,check=True,timeout=10)

if __name__=='__main__':main()
