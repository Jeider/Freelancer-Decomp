"""Run production scope adapter, parser and trigger scheduler with fake player/actions."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from check_transfer_docking import block
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    source = (ROOT / 'src/Content/MissionScript.cpp').read_text(encoding='utf-8')
    methods = '\n'.join(block(source, signature) for signature in (
        'void LoadTrigger(', 'void LoadMissionTriggerSection(', 'void RearmTrigger(',
        'void DeleteTriggerContents(', 'void ActivateMissionTrigger(',
        'void DeactivateMissionTrigger(', 'void DispatchMissionTriggerEvent(',
        'void TickMissionTimers(', 'void ActivateInitialMissionTriggers('))
    code = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <list>
#include <vector>
#include <memory>
#include <string>
#include <windows.h>
#include "dacom.h"
#include "dalib_core.h"
struct IFileSystem;
namespace DALib { DALIB_API extern ICOManager* Dacom; DALIB_API extern IFileSystem* Data; }
void __cdecl QuietDump(int,char const*,...){}
#include "common_ini.h"
#include "common_id.h"
#include "common_server_controller.h"
using pub::Controller::EMessage;
bool TestCampaignMode=true;
extern "C" __declspec(dllexport) int __cdecl FreelancerCampaignServerEnabled(){return TestCampaignMode?1:0;}
#define FDUMP(...) ((void)0)
int const G_TriggerStateActive=0,G_TriggerStateInactive=1,G_TriggerStateComplete=2;
struct FMissionScript;
struct Cnd {
    FMissionScript* Mission; unsigned TriggerId=0;
    explicit Cnd(FMissionScript* m):Mission(m){} virtual ~Cnd()=default;
    virtual void Parse(INI_Reader&){} virtual void OnActivate(){}
    virtual bool Matches(EMessage,void const*)=0;
    virtual void Save(FILE*){} virtual void Load(INI_Reader*){}
    void SetTriggerId(unsigned id){TriggerId=id;}
};
struct CndTimer:Cnd {
    using Cnd::Cnd; float Elapsed=0,Duration=0;
    void Parse(INI_Reader& r) override { Duration=static_cast<float>(r.get_value_float(0)); }
    void OnActivate() override { Elapsed=0; }
    bool Matches(EMessage,void const* p) override {if(p)Elapsed+=*static_cast<float const*>(p);return Elapsed>=Duration;}
    void Save(FILE* f) override {fprintf(f,"Cnd_Timer = %.9g\n",Elapsed);}
    void Load(INI_Reader* r) override {while(r->read_value())if(r->is_value("Cnd_Timer"))Elapsed=static_cast<float>(r->get_value_float(0));}
};
struct True:Cnd { using Cnd::Cnd; bool Matches(EMessage,void const*) override {return true;} };
struct Popup:Cnd { using Cnd::Cnd; bool Matches(EMessage,void const* p) override {return p!=nullptr;} };
struct BaseCondition:Cnd {using Cnd::Cnd;unsigned id=0;
    void Parse(INI_Reader& r)override{id=CreateID(r.get_value_string(0));}
    bool Matches(EMessage,void const* p)override{return p&&*static_cast<unsigned const*>(p)==id;}};
struct Response:Cnd {using Cnd::Cnd;
    bool Matches(EMessage,void const* p)override{return p&&static_cast<unsigned char const*>(p)[8]!=0;}};
struct Act {
    FMissionScript* Mission;unsigned TriggerId=0;
    explicit Act(FMissionScript* m):Mission(m){}virtual ~Act()=default;
    virtual void Parse(INI_Reader&){} virtual bool Execute()=0;
    void SetTriggerId(unsigned id){TriggerId=id;}
};
struct FTrigger {int State; Cnd* Condition;std::list<Act*> Actions;FMissionScript* Mission;
    std::vector<EMessage> EventIds;unsigned char bRepeatable;unsigned Id;};
using FTriggerMap=std::map<unsigned,FTrigger>;
struct FMissionTimer {float Remaining;Act* Action;};
struct FCharacterEncounter {};
struct FStoryMissionListNode_0x2f4 {
    unsigned PathLength=0;char Path[128]={};int Field_0x8c=-1;
    FCharacterEncounter* Field_0x90=nullptr;bool Field_0x94=false,Field_0x95=false;
};
struct FContentPlayerState {unsigned live=77;unsigned GetLiveMission(){return live;}};
std::map<unsigned,std::unique_ptr<FContentPlayerState>> players;
std::map<unsigned,std::wstring> names;
auto& GetContentPlayerStates(){return players;}
FContentPlayerState* FindContentPlayerState(unsigned id){auto p=players.find(id);return p==players.end()?nullptr:p->second.get();}
std::map<unsigned,unsigned> bases;
namespace pub {namespace Player {
int GetName(unsigned id,std::wstring& name){name=names[id];return name.empty()?-1:0;}
int GetBase(unsigned id,unsigned& base){base=bases[id];return 0;}
}}
struct FmtStr {unsigned MadLibId=0;};
struct FMissionPlayer {struct {std::vector<int> Objectives;} Objectives;FContentPlayerState* PlayerState=nullptr;};
struct FMissionScript {
    std::map<unsigned,FMissionPlayer*> Players;FmtStr Field_0x50,Field_0x68;
    FMissionPlayer* GetOrCreatePlayer(unsigned id){auto& p=Players[id];if(!p)p=new FMissionPlayer;return p;}
    unsigned PlayerId=2,ControllerId=77,CurrentLocationId=0;FContentPlayerState* PlayerState=nullptr;
    FTriggerMap TriggerMap;std::list<FTriggerMap::iterator> ActiveTriggers;
    std::map<unsigned,unsigned> PendingActivations,InitiallyActive;
    std::list<FMissionTimer> Timers;std::list<FStoryMissionListNode_0x2f4> List_0x2f4;
    int MissionStateFromName(char const*){return 0;}
    void ReleaseRtcScripts(){for(auto& s:List_0x2f4)delete s.Field_0x90;List_0x2f4.clear();}
    void StartRtcScript(FStoryMissionListNode_0x2f4*){}
    void OnCharacterSelect(void const*){}void OnLocationExit(void const*){}
};
std::map<unsigned,unsigned> rewards;
std::map<unsigned,unsigned> scenes,uiUpdates;
unsigned globalSpawns=0,acceptNotifications=0;
void LocalTriggersAcceptedMission(FMissionScript*){++acceptNotifications;}
struct Scene:Act {using Act::Act;bool Execute()override{++scenes[Mission->PlayerId];return true;}};
struct Ui:Act {using Act::Act;bool Execute()override{
    assert(Mission->Players.size()==1&&Mission->Players.count(Mission->PlayerId));
    ++uiUpdates[Mission->PlayerId];Mission->Field_0x50.MadLibId=Mission->PlayerId;return true;}};
struct Spawn:Act {using Act::Act;bool Execute()override{++globalSpawns;return true;}};
struct Noop:Act {using Act::Act;bool Execute()override{return true;}};
struct Reward:Act {using Act::Act;bool Execute()override{++rewards[Mission->PlayerId];return true;}};
struct Activate:Act {
    using Act::Act;unsigned target=0;
    void Parse(INI_Reader& r)override{target=CreateID(r.get_value_string(0));}
    bool Execute()override{Mission->PendingActivations.emplace(target,TriggerId);return true;}
};
template<class T>Cnd* NewCnd(FMissionScript* m){return new T(m);}
template<class T>Act* NewAct(FMissionScript* m){return new T(m);}
struct FCndFactoryEntry {char const* Name;Cnd*(*Create)(FMissionScript*);int EventCount;EMessage EventIds[3];};
FCndFactoryEntry GCndFactory[]={
    {"Cnd_True",NewCnd<True>,1,{EMessage::Heartbeat}},
    {"Cnd_Timer",NewCnd<CndTimer>,1,{EMessage::Heartbeat}},
    {"Cnd_PopUpDialog",NewCnd<Popup>,1,{EMessage::PopUpDialog}},
    {"Cnd_BaseEnter",NewCnd<BaseCondition>,1,{EMessage::BaseEnter}},
    {"Cnd_LocEnter",NewCnd<BaseCondition>,1,{EMessage::LocationEnter}},
    {"Cnd_MsnResponse",NewCnd<Response>,1,{EMessage::MissionResponse}}};
struct FActFactoryEntry {char const* Name;Act*(*Create)(FMissionScript*);};
FActFactoryEntry GActFactory[]={
    {"Act_SetShipAndLoadout",NewAct<Reward>},{"Act_ActTrig",NewAct<Activate>},
    {"Act_AddRTC",NewAct<Scene>},{"Act_RemoveRTC",NewAct<Noop>},
    {"Act_DeactTrig",NewAct<Noop>},{"Act_SetNNObj",NewAct<Ui>},
    {"Act_SetTitle",NewAct<Ui>},{"Act_SetOffer",NewAct<Ui>},{"Act_NNIds",NewAct<Ui>},
    {"Act_SpawnShip",NewAct<Spawn>}};
void LoadTrigger(FTrigger*,INI_Reader*);void LoadMissionTriggerSection(FMissionScript*,INI_Reader*);
void RearmTrigger(FTrigger*);void DeleteTriggerContents(FTrigger*);
void ActivateMissionTrigger(FMissionScript*,unsigned const*);void DeactivateMissionTrigger(FMissionScript*,unsigned const*);
void DispatchMissionTriggerEvent(FMissionScript*,EMessage const*,void const*);
void TickMissionTimers(FMissionScript*,float);void ActivateInitialMissionTriggers(FMissionScript*);
#include "LocalTriggers.inl"
''' + methods + r'''
void Load(FMissionScript& m,std::string const& text){
    INI_Reader r;assert(r.open_memory(text.c_str(),static_cast<unsigned>(text.size())));
    while(r.read_header())if(r.is_header("Trigger"))LoadMissionTriggerSection(&m,&r);
    if(LocalTriggers::Runtimes.count(&m))LocalTriggers::Runtimes[&m].source="test_campaign.ini";
}
void Join(unsigned id,wchar_t const* name){names[id]=name;players[id].reset(new FContentPlayerState);}
std::string Save(unsigned id){FILE* f=tmpfile();assert(f);LocalTriggersPlayerSave(id,f);fflush(f);rewind(f);
    std::string result;char buf[256];while(fgets(buf,sizeof(buf),f))result+=buf;fclose(f);return result;}
void Restore(unsigned id,std::string const& text){INI_Reader r;assert(r.open_memory(text.c_str(),static_cast<unsigned>(text.size())));LocalTriggersPlayerLoad(id,&r);}
int main(int argc,char** argv){
    HMODULE content=nullptr,server=nullptr;
    if(argc>1){
        FDUMP=QuietDump;
        if(!LoadLibraryA("ReadFile.dll"))return 2;
        DALib::Dacom=DACOM_Acquire();DALib::OpenData(".");if(!DALib::Data)return 3;
        if(!LoadLibraryA("x86math.dll"))return 4;
        if(argc>2){server=LoadLibraryA(argv[2]);if(!server){printf("Server load failed: %lu\n",GetLastError());return 5;}}
        content=LoadLibraryA(argv[1]);if(!content){printf("Content load failed: %lu\n",GetLastError());return 1;}
    }
    Join(2,L"leader");Join(1,L"guest");
    FMissionScript m;m.PlayerState=players[2].get();
    std::string text=R"ini(
[Trigger]
nickname = world
InitState = ACTIVE
Cnd_True = no_params
Act_SetShipAndLoadout = ship, loadout
[Trigger]
execution_scope = local
nickname = talk
InitState = ACTIVE
Cnd_PopUpDialog = YES
Act_SetShipAndLoadout = ship, loadout
Act_ActTrig = wait
[Trigger]
nickname = wait
execution_scope = local
Cnd_Timer = 10, true
Act_SetShipAndLoadout = ship, loadout
Act_ActTrig = world
[Trigger]
nickname = never
execution_scope = local
Cnd_True = no_params
Act_SetShipAndLoadout = ship, loadout
)ini";
    Load(m,text);assert(m.TriggerMap.size()==1);
    auto world=CreateID("world"),talk=CreateID("talk"),wait=CreateID("wait");
    ActivateInitialMissionTriggers(&m);assert(rewards[2]==1 && rewards[1]==0);
    LocalTriggers::Dispatch(&m,EMessage::MissionStart,nullptr);
    assert(m.PlayerId==2 && m.PlayerState==players[2].get() && m.TriggerMap.count(world));
    unsigned answer[]={1,1};LocalTriggers::Dispatch(&m,EMessage::PopUpDialog,answer);
    assert(rewards[1]==1 && rewards[2]==1);
    LocalTriggers::Dispatch(&m,EMessage::PopUpDialog,answer);assert(rewards[1]==1);
    auto& runtime=LocalTriggers::Runtimes[&m];
    assert(runtime.players[L"guest"]->triggers[talk].State==2);
    assert(runtime.players[L"leader"]->triggers[talk].State==0);
    float dt=3;LocalTriggers::Dispatch(&m,EMessage::Heartbeat,&dt);
    auto saved=Save(1);assert(saved.find("Cnd_Timer = 3")!=std::string::npos);
    LocalTriggersPlayerLogout(1);players.erase(1);names.erase(1);
    Join(1,L"stranger");players[1]->live=0;
    LocalTriggers::Dispatch(&m,EMessage::Heartbeat,&dt);assert(rewards[1]==1);
    Join(3,L"guest");Restore(3,saved);
    LocalTriggers::Dispatch(&m,EMessage::Heartbeat,&dt);assert(rewards[3]==0);
    dt=4;LocalTriggers::Dispatch(&m,EMessage::Heartbeat,&dt);assert(rewards[3]==1);
    answer[0]=3;LocalTriggers::Dispatch(&m,EMessage::PopUpDialog,answer);assert(rewards[3]==1);
    // Completed and inactive states survive reload, not just the last trigger.
    auto complete=Save(3);Restore(3,complete);
    LocalTriggers::Dispatch(&m,EMessage::Heartbeat,&dt);assert(rewards[3]==1);
    assert(runtime.players[L"guest"]->triggers[CreateID("never")].State==1);
    answer[0]=2;LocalTriggers::Dispatch(&m,EMessage::PopUpDialog,answer);assert(rewards[2]==2);
    LocalTriggers::Destroy(&m);
    assert(Save(3).find("state = 2")!=std::string::npos); // preserve after controller teardown
    for(auto& t:m.TriggerMap)DeleteTriggerContents(&t.second);
    FMissionScript invalid;
    Load(invalid,"[Trigger]\nnickname = bad\nexecution_scope = local\nCnd_True = no_params\nAct_SpawnShip = npc\n");
    assert(invalid.TriggerMap.empty() && !LocalTriggers::Runtimes.count(&invalid));
    Load(invalid,"[Trigger]\nnickname = typo\nexecution_scope = locla\nCnd_True = no_params\n");
    assert(invalid.TriggerMap.empty());
    TestCampaignMode=false;
    FMissionScript ordinary;
    Load(ordinary,"[Trigger]\nnickname = unscoped_sp\nexecution_scope = local\nInitState = ACTIVE\nCnd_True = no_params\nAct_SetShipAndLoadout = ship, loadout\n");
    assert(ordinary.TriggerMap.size()==1 && !LocalTriggers::Runtimes.count(&ordinary));
    for(auto& t:ordinary.TriggerMap)DeleteTriggerContents(&t.second);
    TestCampaignMode=true;
    FMissionScript repeated;
    Load(repeated,"[Trigger]\nnickname = repeat\nexecution_scope = local\nInitState = ACTIVE\nrepeatable = true\nCnd_PopUpDialog = YES\nAct_SetShipAndLoadout = ship, loadout\n");
    LocalTriggers::Runtimes[&repeated].source="repeat_campaign.ini";
    LocalTriggers::Dispatch(&repeated,EMessage::MissionStart,nullptr);
    auto before=rewards[2];answer[0]=2;
    LocalTriggers::Dispatch(&repeated,EMessage::PopUpDialog,answer);
    LocalTriggers::Dispatch(&repeated,EMessage::PopUpDialog,answer);
    assert(rewards[2]==before+2);
    LocalTriggers::Destroy(&repeated);
    puts("PASS production local scopes: default global, two participants, private chains/timers, duplicate events, save/load, reconnect to new slot, foreign slot, invalid scope/action");
    LocalTriggers::Loaded.clear();players.clear();names.clear();rewards.clear();
    Join(2,L"leader");Join(1,L"guest");bases[1]=bases[2]=CreateID("sig13_01_base");
    FMissionScript shared;shared.PlayerState=players[2].get();
    shared.GetOrCreatePlayer(2)->Objectives.Objectives.push_back(42);
    LocalTriggersConfigureM01a(&shared);
    Load(shared,R"m01a(/*M01A*/
[Trigger]
nickname = LAUNCH_SIG13
Cnd_True = no_params
Act_SpawnShip = alaric
[Trigger]
nickname = LAUNCH_SIG13_COMPLETE
Cnd_True = no_params
[Trigger]
nickname = MSN_REP_BEFORE
Cnd_True = no_params
)m01a");
    assert(LocalTriggers::Runtimes[&shared].definitions.size()==4);
    assert(!LocalTriggersPersonalOffer(shared.ControllerId));
    LocalTriggers::Runtimes[&shared].executing=true;
    assert(LocalTriggersPersonalOffer(shared.ControllerId));
    assert(!LocalTriggersPersonalOffer(shared.ControllerId+1));
    LocalTriggers::Runtimes[&shared].executing=false;
    LocalTriggers::Dispatch(&shared,EMessage::MissionStart,nullptr);
    assert(scenes[1]==1&&scenes[2]==1&&rewards[1]==0&&rewards[2]==0);
    assert(shared.Players.size()==2&&shared.Players[1]->Objectives.Objectives[0]==42);
    assert(shared.Field_0x50.MadLibId==0); // UI context restored
    unsigned room[]={CreateID("Bar"),1};LocalTriggers::Dispatch(&shared,EMessage::LocationEnter,room);
    assert(scenes[1]==2&&scenes[2]==1);
    unsigned accept[]={77,0,1,1};LocalTriggers::Dispatch(&shared,EMessage::MissionResponse,accept);
    assert(rewards[1]==1&&rewards[2]==0&&acceptNotifications==1);
    EMessage heartbeat=EMessage::Heartbeat;float step=0.1f;
    DispatchMissionTriggerEvent(&shared,&heartbeat,&step);assert(globalSpawns==1);
    LocalTriggers::Dispatch(&shared,EMessage::MissionResponse,accept);assert(rewards[1]==1);
    room[1]=2;LocalTriggers::Dispatch(&shared,EMessage::LocationEnter,room);
    accept[3]=2;LocalTriggers::Dispatch(&shared,EMessage::MissionResponse,accept);
    DispatchMissionTriggerEvent(&shared,&heartbeat,&step);
    assert(rewards[2]==1&&globalSpawns==1&&acceptNotifications==1);
    Join(3,L"late");bases[3]=CreateID("sig13_01_base");unsigned arrival[]={bases[3],3};
    LocalTriggers::Dispatch(&shared,EMessage::BaseEnter,arrival);assert(scenes[3]==1);
    room[1]=3;LocalTriggers::Dispatch(&shared,EMessage::LocationEnter,room);
    accept[3]=3;accept[0]=999;LocalTriggers::Dispatch(&shared,EMessage::MissionResponse,accept);assert(rewards[3]==0);
    accept[0]=77;LocalTriggers::Dispatch(&shared,EMessage::MissionResponse,accept);assert(rewards[3]==1);
    auto progress=Save(1);LocalTriggersPlayerLogout(1);players.erase(1);names.erase(1);
    Join(5,L"guest");bases[5]=CreateID("sig13_01_base");Restore(5,progress);
    LocalTriggers::Dispatch(&shared,EMessage::Heartbeat,&step);
    accept[3]=5;LocalTriggers::Dispatch(&shared,EMessage::MissionResponse,accept);assert(rewards[5]==0);
    LocalTriggers::Destroy(&shared);
    for(auto& trigger:shared.TriggerMap)DeleteTriggerContents(&trigger.second);
    puts("PASS actual m01a base sections: private arrival/Alaric/ship/UI, late join, foreign response rejected, no duplicate reward or shared spawn, reconnect");
    if(content){FreeLibrary(content);if(server)FreeLibrary(server);DALib::CloseData();puts("PASS built Content.dll loads with live game dependencies");}
}
'''
    mission_path = Path('D:/Games/FL_MOD/DATA/MISSIONS/M01a/m01a.ini')
    mission_text = mission_path.read_text(encoding='utf-8-sig')
    sections = re.split(r'(?m)(?=^\[)', mission_text)
    selected = []
    wanted = {'real_mission_init', 'init_bar', 'START_vendor_do_accept', 'return_to_deck'}
    for section in sections:
        name = re.search(r'(?m)^nickname\s*=\s*([^\r\n]+)', section)
        if section.startswith('[Trigger]') and name and name.group(1).strip() in wanted:
            selected.append(section)
    assert len(selected) == 4, 'Missing m01a personal base sections'
    code = code.replace('/*M01A*/', '\n'.join(selected))
    out = ROOT / 'out/local_triggers/check'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'check.cpp').write_text(code, encoding='utf-8')
    compiler, env = compiler_env()
    binary = ROOT / 'src/obj/train_courier/rpg1/bin'
    env['PATH'] = 'D:/Games/FL_MOD/bin;' + env['PATH']
    subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17', '/MD',
                    '/D_ITERATOR_DEBUG_LEVEL=1', '/I'+str(ROOT/'src/include'), '/I'+str(ROOT/'src/Content'),
                    'check.cpp', '/Fe:check.exe', '/link', '/LIBPATH:'+str(binary), 'Common.lib',
                    str(ROOT/'bin/dacom.lib'),str(ROOT/'bin/DALib.lib')],
                   cwd=out, env=env, check=True)
    staged_server = [str(binary/'Server.dll')] if '--campaign' in sys.argv else []
    subprocess.run([str(out / 'check.exe'), str(binary / 'Content.dll')]+staged_server, cwd='D:/Games/FL_MOD/bin', env=env, check=True, timeout=20)
    inputs = [Path(__file__), mission_path, ROOT/'src/Content/LocalTriggers.inl', ROOT/'src/Content/LocalTriggers.h',
              ROOT/'src/Content/MissionScript.cpp', ROOT/'src/Content/GameSupport.cpp',
              ROOT/'src/Content/MissionAct.cpp', ROOT/'src/Content/Story.cpp',
              ROOT/'src/Content/StoryMissions.cpp', ROOT/'src/include/campaign_server.h',
              binary/'Content.dll', binary/'Content.pdb']
    inputs += [Path('D:/Games/FL_MOD/bin')/name for name in ('Common.dll','Server.dll','DALib.dll','dacom.dll')]
    report = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (out/'verified.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
