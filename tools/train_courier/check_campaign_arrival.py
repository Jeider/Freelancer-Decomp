"""Exercise production m01a campaign bootstrap and new-character location override."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from check_transfer_docking import block
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    story = (ROOT/'src/Content/StoryMissions.cpp').read_text(encoding='utf-8')
    setup = block(story, 'if (CampaignServer::Enabled() && !pub::SinglePlayer())')
    handler = block(story[story.index('void FMission01a::HandleMissionMessage'):], 'if (CampaignServer::Enabled())')
    save = (ROOT/'src/Server/server_savegame.cpp').read_text(encoding='utf-8')
    location = save[save.index('const bool campaignStart ='):save.index('while (Reader.read_value()) {', save.index('const bool campaignStart ='))]
    skip_start = save.index('if (campaignStart &&')
    skip = save[skip_start:save.index('if (_stricmp(Key, "%%Package%%") == 0)', skip_start)]
    code = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <map>
bool mode=true,sp=false;
namespace CampaignServer {bool Enabled(){return mode;}}
namespace CampaignControl {
struct Snapshot {struct {unsigned completed=0;} state;} current;
Snapshot Get(){return current;}
}
bool SinglePlayer(){return sp;}
namespace pub {
bool SinglePlayer(){return sp;}
namespace Controller {enum class EMessage {MissionStart,BaseEnter,PlayerSave,PlayerLoad,Heartbeat};}
namespace Player {
std::wstring name=L"leader";unsigned base=1;
int GetName(unsigned,std::wstring& out){out=name;return 0;}
int GetBase(unsigned,unsigned& out){out=base;return 0;}
}}
using EMessage=pub::Controller::EMessage;
unsigned CreateID(char const* s){return !strcmp(s,"sig13_01_base")?1:!strcmp(s,"real_mission_init")?2:3;}
void FDUMP(int,char const*,...){}
struct State{} state;State* live=&state;
State* FindContentPlayerState(unsigned){return live;}
struct FMissionScript {int starts=0;void HandleMissionMessage(EMessage,void const*){++starts;}};
unsigned arrivals=0;
void DispatchMissionTriggerEvent(void*,EMessage const* e,void const* p){
    auto a=static_cast<unsigned const*>(p);assert(*e==EMessage::BaseEnter&&a[0]==1&&a[1]==7);++arrivals;
}
struct Mission:FMissionScript {
    std::map<unsigned,unsigned> TriggerMap,InitiallyActive;
    unsigned PlayerId=7;State* PlayerState=&state;std::wstring CampaignOwner=L"leader";
    bool CampaignArrivalPending=false,CampaignMissionStarted=false;
    void Setup(){SETUP}
    void Handle(EMessage MessageId,void const* MessageParms){HANDLER}
};
struct ReaderMock {bool player=true;bool is_header(char const*){return player;}};
std::string Save(bool player){
    auto Out=tmpfile();assert(Out);ReaderMock Reader;Reader.player=player;
    LOCATION
    for(auto Key:{"system","base","last_base","pos","rotate","money","name","ship_archetype","%%Package%%","equip","cargo","base_equip","base_cargo"}){
        SKIP
        fprintf(Out,"%s = original\n",Key);
    }
    rewind(Out);std::string s;char b[256];while(fgets(b,sizeof(b),Out))s+=b;fclose(Out);return s;
}
int main(){
    auto file=Save(true);assert(file.find("system = sig13\nbase = sig13_01_base\n")!=std::string::npos);
    assert(file.find("last_base")==std::string::npos&&file.find("pos =")==std::string::npos);
    assert(file.find("money = original")!=std::string::npos&&file.find("ship_archetype")==std::string::npos);
    assert(file.find("%%Package%%")==std::string::npos&&file.find("equip")==std::string::npos&&file.find("cargo")==std::string::npos);
    assert(Save(false).find("system = original")!=std::string::npos);
    CampaignControl::current.state.completed=1;file=Save(true);
    assert(file.find("base = original")!=std::string::npos&&file.find("ship_archetype = original")!=std::string::npos);
    CampaignControl::current.state.completed=0;
    mode=false;assert(Save(true).find("base = original")!=std::string::npos);
    mode=true;sp=true;assert(Save(true).find("base = original")!=std::string::npos);sp=false;
    Mission m;m.TriggerMap[2]=0;m.InitiallyActive[3]=3;m.InitiallyActive[99]=99;m.Setup();
    assert(m.InitiallyActive.count(2)&&!m.InitiallyActive.count(3)&&m.InitiallyActive.count(99));
    m.Handle(EMessage::MissionStart,nullptr);assert(arrivals==1&&m.starts==1&&!m.CampaignArrivalPending);
    m.Handle(EMessage::MissionStart,nullptr);assert(arrivals==1&&m.starts==1);
    Mission elsewhere;elsewhere.TriggerMap[2]=0;elsewhere.Setup();pub::Player::base=9;
    elsewhere.Handle(EMessage::MissionStart,nullptr);assert(arrivals==1&&elsewhere.CampaignArrivalPending);
    unsigned arrival[]={1,7};elsewhere.Handle(EMessage::BaseEnter,arrival);assert(!elsewhere.CampaignArrivalPending);
    Mission stale;stale.TriggerMap[2]=0;stale.Setup();live=nullptr;stale.Handle(EMessage::MissionStart,nullptr);assert(!stale.starts);
    live=&state;pub::Player::name=L"stranger";stale.Handle(EMessage::MissionStart,nullptr);assert(!stale.starts);pub::Player::name=L"leader";
    mode=false;Mission ordinary;ordinary.InitiallyActive[3]=3;ordinary.TriggerMap[2]=0;ordinary.Setup();assert(ordinary.InitiallyActive.count(3)&&!ordinary.InitiallyActive.count(2));
    mode=true;Mission personal;personal.InitiallyActive[3]=3;personal.Setup();assert(!personal.InitiallyActive.count(3)&&!personal.CampaignArrivalPending);
    puts("PASS production arrival: campaign-only shipless spawn, skip intro, single arrival, other base, disconnect/slot reuse, SP/MP unchanged");
}
'''.replace('SETUP',setup).replace('HANDLER',handler).replace('LOCATION',location).replace('SKIP',skip)
    out=ROOT/'out/campaign_arrival/check'
    out.mkdir(parents=True,exist_ok=True)
    (out/'check.cpp').write_text(code,encoding='utf-8')
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17','check.cpp','/Fe:check.exe'],cwd=out,env=env,check=True)
    subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True,timeout=15)


if __name__=='__main__':main()
