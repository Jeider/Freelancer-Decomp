"""Compile production command handlers with mocked world/UI; verify parsing and dispatch."""
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_courier'))
from check_orders import function
from build_asf_hq import compiler_env

PREFIX=r'''
#include "port_console_api.h"
#include "port_console_parse.h"
#include <cassert>
#include <climits>
#include <cstdio>
#include <map>
#include <string>
#include <vector>
unsigned const kPlayer=1;
int cash=100,playerRep=7;
std::map<unsigned,float> reps={{1,-.6f},{2,0.f},{3,.6f}};
namespace pub {
namespace Player {
int InspectCash(unsigned,int& out){out=cash;return 0;}
int AdjustCash(unsigned,int delta){cash+=delta;return 0;}
int GetRep(unsigned,int& out){out=playerRep;return 0;}
}
namespace Reputation {
struct Enumerator {virtual char Execute(unsigned)=0;};
int EnumerateGroups(Enumerator& e){for(auto const& r:reps)if(!e.Execute(r.first))break;return 0;}
int GetReputation(int,unsigned id,float& out){if(!reps.count(id))return -4;out=reps[id];return 0;}
int SetReputation(int,unsigned id,float value){if(!reps.count(id))return -4;reps[id]=value;return 0;}
int GetReputation(unsigned id,unsigned faction,float& out){if(!reps.count(faction))return -4;out=id==faction?1.f:-.2f;return 0;}
}
}
bool G_bOpen=true,inSpace=false,inIntro=false,transition=false,single=true,haveServer=true;
unsigned baseId=1,roomId=12;
std::vector<std::string> events;
void Printf(char const*,...){}
bool InSpace(){return inSpace;}
bool IsClientIntroEnvironment(){return inIntro;}
bool IsClientLocationInTransition(){return transition;}
unsigned GetClientLocationCurrentBase(){return baseId;}
unsigned GetClientLocationCurrentRoom(){return roomId;}
unsigned GetPlayerConnectionId(){return 1;}
struct IServer {void CharacterSkipAutosave(unsigned){events.push_back("skip");}} server;
void* GetLocalServerInterface(){return haveServer?&server:nullptr;}
void QueueClientLocationChange(unsigned,float,bool){events.push_back("queue-clear");}
void LeaveClientLocationBase(){events.push_back("exit");baseId=0;}
void EnterClientLocationBase(unsigned id){assert(!baseId);baseId=id;events.push_back("enter");}
void SetPlayerBaseIdRetail(unsigned id){assert(id==baseId);events.push_back("base-id");}
void SetPlayerFactionScratchRetail(unsigned id){assert(id==roomId);}
void SetGameflowLocationBase(unsigned id){assert(id==baseId);}
void NnArrivalTextShowBase(float){events.push_back("caption");}
namespace Universe {struct IBase {unsigned GetId(){return 2;}char const* GetNickname(){return "test_base";}};}
Universe::IBase base;
Universe::IBase* FindBase(char const* name){return std::string(name)=="missing"?nullptr:&base;}
int __cdecl MockServer(int op,void*){assert(op==kPortConsoleForceLand);events.push_back("force-land");return 0;}
FPortConsoleServerFn ServerConsole(){return single&&haveServer?MockServer:nullptr;}
struct Win3D {};
struct FNavBarButton {unsigned Type=0;unsigned char bRoomSwitch=1;void* Hotspot=nullptr;};
struct NavBar:Win3D {void OnButtonClicked(FNavBarButton* b){assert(b->Type==4 && !b->bRoomSwitch && !b->Hotspot);events.push_back("launch");}} bar;
Win3D* Win3DFindByName(char const*){return baseId?&bar:nullptr;}
'''

MAIN=r'''
int main(){
    int mode,amount;
    assert(PortConsoleParse::Money("",mode,amount) && mode==0);
    assert(PortConsoleParse::Money("100k",mode,amount) && mode==1 && amount==100000);
    assert(PortConsoleParse::Money("+20K",mode,amount) && mode==2 && amount==20000);
    assert(PortConsoleParse::Money("-500",mode,amount) && mode==2 && amount==-500);
    for(auto bad:{"foo","100oops","1.5","+","999999999k","9999999999999999999999999"})
        assert(!PortConsoleParse::Money(bad,mode,amount));
    FPortConsoleMoney m={1,100000,0};assert(Money(m)==0 && m.Balance==100000);
    m.Mode=2;m.Amount=-150000;assert(Money(m)==0 && m.Balance==0);
    m.Amount=INT_MAX;assert(Money(m)==0 && m.Balance==999999999);
    m.Amount=INT_MIN;assert(Money(m)==0 && m.Balance==0);
    float value;
    for(auto const& entry:std::map<std::string,float>{{"H",-.9f},{"h",-.6f},{"nh",-.2f},{"n",0.f},{"nf",.2f},{"f",.6f},{"F",.9f},{"60",.6f},{"-90",-.9f},{".5",.5f},{"200",1.f}})
        assert(PortConsoleParse::Rep(entry.first.c_str(),value) && value==entry.second);
    for(auto bad:{"","NaN","inf","1oops","friendly","1e9999"})assert(!PortConsoleParse::Rep(bad,value));
    FPortConsoleRep r={5,0,0,1};assert(Rep(r)==kPortConsoleFailed);
    r.Mode=1;r.Faction=1;r.Value=.9f;assert(Rep(r)==0 && reps[1]==.9f);
    auto original=reps;
    r.Mode=2;assert(Rep(r)==0);
    r.Mode=3;r.Value=0;assert(Rep(r)==0 && reps[1]==0 && reps[3]==0);
    r.Mode=3;r.Value=.6f;assert(Rep(r)==0);
    r.Mode=5;assert(Rep(r)==0 && reps==original);assert(Rep(r)==kPortConsoleFailed);
    r.Mode=4;r.Faction=2;assert(Rep(r)==0 && reps[2]==1 && reps[1]==-.2f);
    r.Mode=5;assert(Rep(r)==0 && reps==original);
    r.Mode=4;r.Faction=999;assert(Rep(r)==kPortConsoleFailed && reps==original);
    r.Mode=3;r.Value=.9f;assert(Rep(r)==0);
    r.Mode=5;++r.Revision;assert(Rep(r)==kPortConsoleFailed && reps[2]==.9f);
    puts("PASS: money set/add/subtract/clamp, strict parsing, rep symbolic/percent, snapshot-once/undo, faction relations, no undo across loads");
    CmdBase("test_base");
    assert((events==std::vector<std::string>{"skip","queue-clear","exit","enter","base-id","caption"}));
    events.clear();inSpace=true;CmdBase("test_base");assert(events==std::vector<std::string>{"force-land"});
    events.clear();inSpace=false;single=false;CmdBase("test_base");assert(events.empty());
    single=true;transition=true;CmdBase("test_base");assert(events.empty());
    transition=false;CmdBase("missing");assert(events.empty());
    CmdLaunch("");assert(events==std::vector<std::string>{"launch"});
    events.clear();transition=true;CmdLaunch("");assert(events.empty());
    transition=false;baseId=0;CmdLaunch("");assert(events.empty());
    puts("PASS: docked base transfer exit/enter without ship or launch; no autosave; space ForceLand unchanged; invalid/MP/transition rejection; launch without room tab");
}
'''

def main():
    client=(ROOT/'src/freelancer/Client/dbg_console.cpp').read_text(encoding='utf-8')
    server=(ROOT/'src/Server/server_port_console.cpp').read_text(encoding='utf-8')
    table=client.split('FCommand const kCommands[] = {',1)[1].split('};',1)[0]
    aliases={}
    for name,alias,handler in re.findall(r'\{"([^"]+)", (nullptr|"[^"]+"), "[^"]*", &(\w+)\}',table):
        for word in [name]+([] if alias=='nullptr' else [alias.strip('"')]):
            assert word.lower() not in aliases,word
            aliases[word.lower()]=handler
    for word,handler in {'s':'CmdSystem','b':'CmdBase','ju':'CmdJump','j':'CmdJump','save':'CmdSave','money':'CmdMoney','cash':'CmdMoney','rep':'CmdRep','launch':'CmdLaunch'}.items():
        assert aliases[word]==handler,(word,aliases.get(word))
    print('PASS: unique command names and requested aliases',flush=True)
    code=PREFIX+'\n'.join(function(server,name) for name in ['int Money(','int Rep('])+'\n'
    code+='\n'.join(function(client,name) for name in ['void CmdBase(','void CmdLaunch('])+MAIN
    out=ROOT/'src/obj/console';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'check.cpp';cpp.write_text(code,encoding='utf-8');exe=out/'check.exe'
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2','/I'+str(ROOT/'src/include'),
        str(cpp),'/Fo'+str(out/'check.obj'),'/Fe'+str(exe)],cwd=out,env=env,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)

if __name__=='__main__':main()
