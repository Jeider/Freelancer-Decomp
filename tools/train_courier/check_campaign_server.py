"""Test saved mode and production campaign launcher/story event routing."""
from pathlib import Path
import subprocess
import sys
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from check_transfer_docking import block
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    subprocess.run([sys.executable, str(ROOT/'tools/train_courier/check_campaign_arrival.py')], check=True)
    subprocess.run([sys.executable, str(ROOT/'tools/train_courier/check_campaign_control.py')], check=True)
    launcher = (ROOT/'src/Content/StoryLauncher.cpp').read_text(encoding='utf-8')
    story = (ROOT/'src/Content/Story.cpp').read_text(encoding='utf-8')
    code = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <memory>
#include <map>
#include "campaign_server.h"
#include "server_campaign_config.h"
bool mode=false,sp=false;unsigned creates=0,starts=0,loads=0,saves=0,npcLoads=0,kicks=0,replays=0;
extern "C" __declspec(dllexport) int __cdecl FreelancerCampaignServerEnabled(){return mode?1:0;}
#define FDUMP(...) ((void)0)
namespace pub {
bool SinglePlayer(){return sp;}
namespace Controller {
enum class EMessage {Heartbeat,BaseEnter,PlayerLogin,PlayerLoad,PlayerSave,PlayerWorthChanged,PlayerShipArchSet,PlayerMissionChanged};
enum {NORMAL=2};struct FStoryCreateParms{unsigned PlayerId;};
void SetHeartbeatInterval(unsigned,float){}
void _SendMessage(unsigned id,EMessage event,void const* data){
    if(event==EMessage::BaseEnter){assert(id==42&&static_cast<unsigned const*>(data)[1]==1);++replays;}
    else {assert(id==creates&&event==EMessage::Heartbeat);++kicks;}
}
unsigned Create(char const*,char const* kind,FStoryCreateParms* p,int){assert(!strcmp(kind,"CampaignStory")&&p->PlayerId==0);return ++creates;}
}
namespace Player {int GetName(unsigned,std::wstring&);}
}
using pub::Controller::EMessage;
struct State {
    bool base=false,ship=false;void* ShipObject=nullptr;unsigned LocationId=0,live=0,joins=0;
    void* GetBaseRecord(){return base?this:nullptr;}
    unsigned GetLiveMission(){return live;}
    void JoinMission(unsigned const* id,unsigned,bool,unsigned){live=*id;++joins;}
};
std::map<unsigned,std::unique_ptr<State>> players;
std::map<unsigned,std::wstring> names;
auto& GetContentPlayerStates(){return players;}
State* FindContentPlayerState(unsigned id){auto it=players.find(id);return it==players.end()?nullptr:it->second.get();}
int pub::Player::GetName(unsigned id,std::wstring& n){n=names[id];return n.empty()?-1:0;}
struct IDLL {virtual ~IDLL()=default;virtual void HandleMessage(EMessage,void const*)=0;};
std::map<unsigned,unsigned> GSpecificNpcs;
void LoadStoryNpcs(){++npcLoads;}
''' + block(launcher, 'class FCampaignLauncher final') + ';\n' + block(launcher, 'IDLL* CreateCampaignLauncher(') + r'''
unsigned GStoryMissionController=0;
struct FStorySaveMessage {unsigned PlayerId;FILE* File;};
struct FStoryLoadMessage {unsigned PlayerId;void* Reader;};
struct FStory {
    bool bCampaign=true,bCampaignStarted=false,bShipBought=false;
    unsigned PlayerId=2;int MissionNum=0;float DeltaWorth=-1;
    std::wstring CampaignOwner=L"leader";char MissionName[32]="No_Mission";
    void HandleMessage(EMessage,void const*);
    void StartMission(unsigned chapter,char const* name){assert(chapter==1&&!strcmp(name,"Mission_01a"));++starts;GStoryMissionController=42;strcpy(MissionName,name);}
    void AdvanceMission(){}void SetShipBoughtReputation(){}
    void OnSave(FILE*){++saves;}void OnLoad(void*){++loads;}
};
''' + block(story, 'void FStory::HandleMessage(') + r'''
void ConfigTests(){
    FILE* f=tmpfile();assert(f);assert(!CampaignServerConfig::Read(f));
    rewind(f);assert(CampaignServerConfig::Write(f,false));rewind(f);assert(!CampaignServerConfig::Read(f));
    rewind(f);assert(CampaignServerConfig::Write(f,true));rewind(f);assert(CampaignServerConfig::Read(f));
    rewind(f);unsigned corrupt[]={0x504d4143,2,1};fwrite(corrupt,sizeof(corrupt),1,f);rewind(f);assert(!CampaignServerConfig::Read(f));
    fclose(f);f=tmpfile();unsigned tag=0x504d4143;fwrite(&tag,4,1,f);rewind(f);assert(!CampaignServerConfig::Read(f));fclose(f);
}
int main(){
    ConfigTests();assert(!CampaignServer::Enabled());
    players[2].reset(new State);names[2]=L"leader";
    assert(!CreateCampaignLauncher("CampaignLauncher",10,nullptr)&&!creates);
    mode=true;assert(CampaignServer::Enabled());
    sp=true;assert(!CreateCampaignLauncher("CampaignLauncher",10,nullptr)&&!creates);
    sp=false;std::unique_ptr<IDLL> launcher(CreateCampaignLauncher("CampaignLauncher",10,nullptr));
    assert(launcher&&creates==1&&npcLoads==1&&!starts); // progress loaded before first player
    unsigned arrival[]={123,2};
    launcher->HandleMessage(EMessage::BaseEnter,arrival);
    launcher->HandleMessage(EMessage::PlayerLogin,nullptr);
    launcher->HandleMessage(EMessage::Heartbeat,nullptr);assert(creates==1&&!starts);
    FStory story;story.bCampaign=false;sp=true;
    FStoryLoadMessage load{2,nullptr};FStorySaveMessage save{2,nullptr};
    story.HandleMessage(EMessage::PlayerLoad,&load);story.HandleMessage(EMessage::PlayerSave,&save);assert(loads==1&&saves==1);
    puts("PASS campaign mode: config off/on/legacy/corrupt, one controller before login, gated factory, SP StoryInfo preserved");
}
'''
    out = ROOT/'out/campaign_server/check'
    out.mkdir(parents=True, exist_ok=True)
    (out/'check.cpp').write_text(code, encoding='utf-8')
    compiler, env = compiler_env()
    command = [str(compiler/'cl.exe'), '/nologo', '/EHsc', '/std:c++17', '/I'+str(ROOT/'src/include')]
    subprocess.run(command+['check.cpp', '/Fe:check.exe'], cwd=out, env=env, check=True)
    subprocess.run([str(out/'check.exe')], cwd=out, env=env, check=True, timeout=15)
    (out/'no_host.cpp').write_text('#include "campaign_server.h"\nint main(){return CampaignServer::Enabled()?1:0;}\n', encoding='utf-8')
    subprocess.run(command+['no_host.cpp', '/Fe:no_host.exe'], cwd=out, env=env, check=True)
    subprocess.run([str(out/'no_host.exe')], cwd=out, env=env, check=True, timeout=15)
    print('PASS no dedicated-host export: mode disabled')
    subprocess.run([sys.executable, str(ROOT/'tools/train_courier/check_local_triggers.py'), '--campaign'], check=True)
    binary = ROOT/'src/obj/train_courier/rpg1/bin'
    game = Path('D:/Games/FL_MOD/bin')
    def exports(path):
        output = subprocess.check_output([str(compiler/'dumpbin.exe'), '/exports', str(path)], env=env, text=True)
        return set(re.findall(r'^\s+\d+\s+[0-9A-F]+\s+(?:[0-9A-F]+\s+)?(\S+)', output, re.M))
    for name in ('Server.dll', 'Content.dll', 'FLServer.exe'):
        before, after = exports(game/name), exports(binary/name)
        assert before <= after, (name, before-after)
        if name == 'FLServer.exe':
            assert {'FreelancerCampaignServerEnabled','FreelancerCampaignGetState',
                    'FreelancerCampaignSetState','FreelancerCampaignTakeStart'} <= after
    print('PASS installed exports preserved and dedicated host mode query exported')
    inputs = [Path(__file__), ROOT/'tools/train_courier/check_local_triggers.py', ROOT/'tools/train_courier/check_campaign_arrival.py',
              ROOT/'tools/train_courier/check_campaign_control.py']
    for folder in ('Content', 'Server', 'FLServer'):
        inputs += [p for p in (ROOT/'src'/folder).iterdir() if p.suffix in ('.cpp', '.h', '.inl', '.def')]
    inputs += [ROOT/'src/include'/name for name in ('campaign_server.h', 'server_campaign_config.h', 'campaign_control.h', 'campaign_progress_file.h')]
    inputs += [binary/name for name in ('Server.dll', 'Server.pdb', 'Content.dll', 'Content.pdb', 'FLServer.exe', 'FLServer.pdb')]
    inputs += [game/name for name in ('Common.dll', 'DALib.dll', 'dacom.dll', 'ServerResources.dll')]
    inputs += [Path('D:/Games/FL_MOD/DATA/MISSIONS/M01a/m01a.ini')]
    if '--with-client' in sys.argv:
        subprocess.run([sys.executable, str(ROOT/'tools/cutscene_skip/check_skip.py')], check=True)
        # Check actual client imports against the modules that will remain installed.
        imported = subprocess.check_output([str(compiler/'dumpbin.exe'), '/imports', str(binary/'freelancer.exe')], env=env, text=True)
        dependency = None
        cache = {}
        for line in imported.splitlines():
            match = re.match(r'^    (\S+\.dll)\s*$', line, re.I)
            if match:
                dependency = match.group(1)
                continue
            symbol = re.match(r'^\s+[0-9A-F]+\s+(\?\S+|[A-Za-z_]\S*)\s*$', line)
            if not symbol or not dependency or not (game/dependency).exists():
                continue
            path = binary/dependency if dependency.lower() in ('server.dll','content.dll') else game/dependency
            if path not in cache: cache[path] = exports(path)
            assert symbol.group(1) in cache[path], (dependency, symbol.group(1))
        inputs += list(cache)
        inputs += [binary/name for name in ('freelancer.exe','freelancer.pdb')]
        inputs += [ROOT/'src/freelancer/Client'/name for name in ('cutscene_skip.cpp','cutscene_skip.h')]
        inputs += [ROOT/'tools/cutscene_skip/check_skip.py']
        print('PASS client skip tests and named imports against installed dependencies')
    (out/'verified.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
