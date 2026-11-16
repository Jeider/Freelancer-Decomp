"""Run production campaign controller, host queue, rank policy and atomic checkpoint IO."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from check_transfer_docking import block
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    host=(ROOT/'src/FLServer/CampaignControl.inl').read_text(encoding='utf-8')
    code=r'''
#include <windows.h>
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include "campaign_progress_file.h"
bool mode=true,sp=false,failCreate=false;
extern "C" __declspec(dllexport) int __cdecl FreelancerCampaignServerEnabled(){return mode;}
extern "C" __declspec(dllexport) int __cdecl FreelancerCampaignGetState(CampaignControl::Snapshot*,unsigned);
extern "C" __declspec(dllexport) void __cdecl FreelancerCampaignSetState(CampaignControl::Snapshot const*,unsigned);
extern "C" __declspec(dllexport) int __cdecl FreelancerCampaignTakeStart(CampaignControl::Request*,unsigned);
struct CCmdUI {bool enabled=false;void Enable(bool value){enabled=value;}};
struct CFLServerApp {
    struct {bool bCampaignServer=true;} ServerControl;
    struct Window {HWND m_hWnd=nullptr;} main;
    Window* m_pMainWnd=&main;
    bool IsShuttingDown(){return false;}
    void OnCampaign();void OnUpdateCampaign(CCmdUI*);
} app;
CFLServerApp* GApp=&app;int GServerRunning=1;
'''
    code+=host
    code+=r'''
namespace pub { namespace Controller {
enum class EMessage {Heartbeat,BaseEnter,PlayerShipArchSet,PlayerWorthChanged,PlayerMissionChanged,PlayerLoad,PlayerSave,MissionStart};
enum {ABOVE_NORMAL=1};
} }
using pub::Controller::EMessage;
struct IDLL {virtual ~IDLL()=default;virtual void HandleMessage(EMessage,void const*)=0;};
struct IStoryMissionEvents {virtual void OnMissionEvent(unsigned,unsigned,unsigned)=0;};
struct FStoryMissionCreateParms {unsigned PlayerId;IStoryMissionEvents* StoryEvents;};
struct PlayerSlot {unsigned rank_level=1;};
std::map<unsigned,PlayerSlot> slots;
struct FContentPlayerState {
    unsigned PlayerId=0,MissionNumber=42,live=0,ended=0;int Reputation=0;bool base=true;void* ShipObject=nullptr;
    void* GetBaseRecord(){return base?this:nullptr;}
    unsigned GetLiveMission(){return live;}
    void JoinMission(unsigned const* id,unsigned,bool,unsigned){live=*id;}
    void EndLiveMission(unsigned,int,bool group){assert(!group);live=0;++ended;}
    void SetDockAccess(int,void const*){}void SetTradelaneAccess(int,void const*){}
};
std::map<unsigned,std::unique_ptr<FContentPlayerState>> players;
std::map<unsigned,std::wstring> names;
auto& GetContentPlayerStates(){return players;}
FContentPlayerState* FindContentPlayerState(unsigned id){auto it=players.find(id);return it==players.end()?nullptr:it->second.get();}
bool SinglePlayer(){return sp;}
bool IsValidPlayer(unsigned id){return slots.count(id)!=0;}
PlayerSlot* PlayerDB_GetPlayer(unsigned id){auto it=slots.find(id);return it==slots.end()?nullptr:&it->second;}
struct Client {unsigned notices=0;void SendServerMiscObjUpdateRank(unsigned,unsigned,int){++notices;}} client;
Client* g_pClientInterface=&client;
#define SERVER_API
unsigned creates=0,starts=0,destroys=0,lastController=0,shipReputations=0;
std::string lastMission;
namespace pub {
bool SinglePlayer(){return sp;}
namespace Player {
int GetName(unsigned id,std::wstring& name){auto it=names.find(id);if(it==names.end())return -1;name=it->second;return 0;}
int GetRank(unsigned id,int& rank){auto p=PlayerDB_GetPlayer(id);if(!p)return -2;rank=int(p->rank_level);return 0;}
int GetRep(unsigned id,int& rep){rep=int(id);return 0;}
int SetRank(unsigned,int);
void SetMoneyNeededToNextRank(unsigned,int){}
void InspectCash(unsigned,int& cash){cash=100000000;}
void GetAssetValue(unsigned,float& assets){assets=100000000;}
}
namespace Reputation {void SetRank(int,float){}void GetReputationGroup(unsigned& id,char const*){id=1;}void SetReputation(int,unsigned,float){++shipReputations;}}
namespace Controller {
void SetHeartbeatInterval(unsigned,float){}
unsigned Create(char const*,char const* name,FStoryMissionCreateParms* p,int){
    ++creates;if(failCreate)return 0;assert(p->PlayerId&&p->StoryEvents);lastMission=name;return lastController=100+creates;
}
void Destroy(unsigned){++destroys;}
void _SendMessage(unsigned id,EMessage event,void const*){assert(id);if(event==EMessage::MissionStart)++starts;}
}
}
'''
    pub=(ROOT/'src/Server/server_pub.cpp').read_text(encoding='utf-8')
    code+='namespace pub { namespace Player {\n'+block(pub,'SERVER_API int __cdecl SetRank(unsigned int player_id, int rank)')+'\n}}\n'
    support=(ROOT/'src/Content/Support.cpp').read_text(encoding='utf-8')
    code+='struct FPlayerToughPt {int Experience,Toughness;};\nstd::vector<FPlayerToughPt> GPlayerToughnessScale={{0,1},{100,40}};\n'
    code+=block(support,'void RecalculateContentPlayerRank(')+'\n'
    code+=block(support,'void SetContentPlayerMissionNumber(')+'\n'
    code+=(ROOT/'src/Content/ServerCampaign.inl').read_text(encoding='utf-8')
    code+=r'''
void Join(unsigned id,wchar_t const* name){auto p=std::make_unique<FContentPlayerState>();p->PlayerId=id;players[id]=std::move(p);names[id]=name;slots[id].rank_level=38;}
void Tick(FServerCampaign& story){story.HandleMessage(EMessage::Heartbeat,nullptr);}
void RequestNext(FServerCampaign& story){auto s=CampaignControl::Get();assert(QueueCampaignStart({s.state.completed,s.state.revision}));Tick(story);}
void Succeed(FServerCampaign& story){auto s=CampaignControl::Get();story.OnMissionEvent(3,CampaignControl::Missions()[s.state.completed].finish,s.controller);}
int main(){
    using namespace CampaignControl;
    auto path=ProgressFile::ServerPath();DeleteFileW(path.c_str());DeleteFileW((path+L".tmp").c_str());
    assert(Rank()==0);
    ProgressFile store(path);State loaded;assert(store.Load(loaded)==0);
    {FServerCampaign story(1);Tick(story);assert(creates==0&&Get().notice==NoPlayers);}
    Join(2,L"leader");Join(5,L"guest");
    FServerCampaign story(1);Tick(story);
    assert(creates==1&&starts==1&&lastMission=="Mission_01a"&&Get().state.phase==Running);
    assert(players[2]->live==lastController&&players[5]->live==lastController);
    assert(slots[2].rank_level==1&&slots[5].rank_level==1);
    pub::Player::SetRank(2,99);RecalculateContentPlayerRank(players[2].get());
    SetContentPlayerMissionNumber(players[2].get(),7,1);assert(slots[2].rank_level==1);
    unsigned owner=2;story.HandleMessage(EMessage::PlayerWorthChanged,&owner);Tick(story);assert(creates==1);
    assert(!QueueCampaignStart({0,Get().state.revision}));
    auto old=Get();Succeed(story);assert(Get().state.phase==Automatic&&Get().state.completed==1);
    assert(!players[2]->live&&!players[5]->live&&players[5]->ended==1);
    story.OnMissionEvent(3,2,old.controller);assert(Get().state.completed==1);
    Tick(story);assert(lastMission=="Mission_01b"&&creates==2);
    Succeed(story);assert(Get().state.phase==Freeflight&&Rank()==3);
    for(int i=0;i<4;++i){story.HandleMessage(EMessage::PlayerWorthChanged,&owner);Tick(story);}
    assert(creates==2);assert(store.Load(loaded)==1&&loaded.phase==Freeflight&&loaded.completed==2);

    // Exercise real native controls without showing a window or starting the game.
    WNDCLASSW cls={};cls.lpfnWndProc=CampaignWindowProc;cls.hInstance=GetModuleHandleW(nullptr);cls.lpszClassName=L"CampaignTest";
    assert(RegisterClassW(&cls));
    HWND window=CreateWindowExW(0,cls.lpszClassName,L"",WS_OVERLAPPED,0,0,630,435,nullptr,nullptr,cls.hInstance,nullptr);
    assert(window&&!IsWindowVisible(window));
    HWND list=GetDlgItem(window,1),button=GetDlgItem(window,3);
    assert(SendMessageW(list,LB_GETCOUNT,0,0)==MissionCount&&SendMessageW(list,LB_GETCURSEL,0,0)==2&&IsWindowEnabled(button));
    wchar_t row[128];SendMessageW(list,LB_GETTEXT,2,reinterpret_cast<LPARAM>(row));assert(wcsstr(row,L"Mission_02"));
    SendMessageW(list,LB_SETCURSEL,3,0);SendMessageW(window,WM_COMMAND,MAKEWPARAM(1,LBN_SELCHANGE),0);
    assert(!IsWindowEnabled(button));
    SendMessageW(list,LB_SETCURSEL,2,0);SendMessageW(window,WM_COMMAND,MAKEWPARAM(1,LBN_SELCHANGE),0);
    assert(IsWindowEnabled(button));SendMessageW(window,WM_COMMAND,MAKEWPARAM(3,BN_CLICKED),0);assert(!IsWindowEnabled(button));
    Request uiRequest;assert(Take(uiRequest)&&uiRequest.mission==2&&uiRequest.revision==Get().state.revision);
    DestroyWindow(window);
    CCmdUI menu;app.OnUpdateCampaign(&menu);assert(menu.enabled);
    app.ServerControl.bCampaignServer=false;app.OnUpdateCampaign(&menu);assert(!menu.enabled);app.ServerControl.bCampaignServer=true;

    // Freeflight remains freeflight after restarting the controller; old owner is unnecessary.
    players.erase(2);names.erase(2);slots.erase(2);
    FServerCampaign resumed(2);Tick(resumed);assert(creates==2&&Rank()==3);
    auto ready=Get();assert(!QueueCampaignStart({3,ready.state.revision}));
    assert(!QueueCampaignStart({2,ready.state.revision-1}));
    std::atomic<int> accepted=0;std::vector<std::thread> callers;
    for(int i=0;i<8;++i)callers.emplace_back([&]{if(QueueCampaignStart({2,ready.state.revision}))++accepted;});
    for(auto& thread:callers)thread.join();assert(accepted==1);
    players[5]->live=999;Tick(resumed);assert(creates==2&&Get().notice==PlayerBusy);
    players[5]->live=0;RequestNext(resumed);assert(lastMission=="Mission_02"&&creates==3&&Get().owner==5&&Rank()==4);
    auto savedAttempt=Get().state.attempt;
    auto running=Get();resumed.OnMissionEvent(4,8,running.controller);
    assert(Get().state.phase==Interrupted&&Get().state.completed==2&&!players[5]->live);
    RequestNext(resumed);assert(creates==4&&Get().state.attempt!=savedAttempt);
    Succeed(resumed);
    // M03..M13: only the authored direct continuations are automatic.
    for(unsigned index=3;index<MissionCount;++index){
        auto before=Get();unsigned count=creates;
        if(before.state.phase==Automatic){Tick(resumed);assert(creates==count+1);}
        else {Tick(resumed);assert(creates==count);RequestNext(resumed);}
        assert(lastMission==Missions()[index].name&&Get().state.phase==Running);
        Succeed(resumed);
        if(index==4){ // buying a ship in the authored freeflight after Mission_04
            unsigned owner=Get().owner;
            resumed.HandleMessage(EMessage::PlayerShipArchSet,&owner);
            resumed.HandleMessage(EMessage::PlayerShipArchSet,&owner);assert(shipReputations==1);
        }
    }
    assert(Get().state.phase==Complete&&Get().state.completed==MissionCount&&Rank()==19);
    assert(!QueueCampaignStart({MissionCount,Get().state.revision}));
    Tick(resumed);assert(store.Load(loaded)==1&&loaded.phase==Complete);

    // A restart during a mission exposes an explicit retry, never a silent skip.
    State active;active.phase=Running;active.completed=2;active.chapter=7;active.rank=4;active.attempt=123;assert(store.Save(active));
    {FServerCampaign interrupted(3);unsigned count=creates;Tick(interrupted);assert(creates==count&&Get().state.phase==Interrupted);
     RequestNext(interrupted);assert(lastMission=="Mission_02");
     names[5]=L"replacement";Tick(interrupted);assert(Get().notice==OwnerAbsent);names[5]=L"guest";}
    players[5]->live=0;
    State first;assert(store.Save(first));failCreate=true;
    {FServerCampaign failed(4);unsigned count=creates;Tick(failed);Tick(failed);assert(creates==count+1&&Get().notice==CreateFailed);
     assert(Get().state.phase==First&&Rank()==1);failCreate=false;RequestNext(failed);assert(Get().state.phase==Running);}
    players[5]->live=0;
    // Atomic replacement failure preserves the previous file.
    assert(store.Save(first));HANDLE locked=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    assert(locked!=INVALID_HANDLE_VALUE);assert(!store.Save(active));CloseHandle(locked);
    assert(store.Load(loaded)==1&&loaded.phase==First);
    FILE* bad=nullptr;assert(_wfopen_s(&bad,path.c_str(),L"wb")==0);fputs("broken",bad);fclose(bad);
    assert(store.Load(loaded)==-1);
    {FServerCampaign broken(5);unsigned count=creates;Tick(broken);assert(Get().state.phase==Error&&Get().notice==CorruptSave&&creates==count);}
    // The rank setter still behaves normally outside campaign MP.
    mode=false;pub::Player::SetRank(5,25);assert(slots[5].rank_level==25);
    mode=true;sp=true;pub::Player::SetRank(5,30);assert(slots[5].rank_level==30);
    SetContentPlayerMissionNumber(players[5].get(),7,1);assert(slots[5].rank_level==31);
    DeleteFileW(path.c_str());
    puts("PASS first auto, manual freeflight, automatic links, all 14 missions, duplicate/stale commands, busy players, owner change between missions");
    puts("PASS native mission list, selection/button/queue, server rank lock, SP/MP isolation, failure/retry, attempt identity, atomic checkpoint, freeflight restart, corruption rejection");
}
'''
    out=ROOT/'out/campaign_control/check';out.mkdir(parents=True,exist_ok=True)
    (out/'check.cpp').write_text(code,encoding='utf-8')
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17','/I'+str(ROOT/'src/include'),
                    'check.cpp','/Fe:check.exe','/link','user32.lib','gdi32.lib'],cwd=out,env=env,check=True)
    subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True,timeout=20)


if __name__=='__main__':main()
