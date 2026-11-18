"""Exercise production radio pruning with real message/queue cases offline."""
from pathlib import Path
import subprocess
import sys
from check_transfer_docking import block

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/train_courier/evacuation/checks'
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    source=(ROOT/'src/freelancer/Client/hud_comm.cpp').read_text(encoding='utf-8')
    code=r'''
#include <cassert>
#include <cstring>
#include <vector>
#include <string>
#include <map>
#include "train_evacuation_audio.h"
#define FREELANCER_RPG_WORLD 1
const int COMM_CONFLICT_PRIORITY_CUTOFF=-3;
using namespace TrainEvacuationAudio;
unsigned CreateID(char const* s){unsigned h=2166136261u;while(*s)h=(h^unsigned(*s++))*16777619u;return h;}
enum CommResult{SUCCESS,CANCELLED};
struct FCommMessage{unsigned Sender=0,Receiver=1,VoiceId=CreateID("atc_leg_m01_new"),TextIds[16]{};int TextCount=0;CommResult Result=SUCCESS;};
struct FCommInbox{FCommMessage Records[16];unsigned Count=0;
 bool Peek(FCommMessage* out){if(!Count)return false;*out=Records[0];return true;}
 bool Pop(FCommMessage* out){if(!Peek(out))return false;--Count;for(unsigned i=0;i<Count;++i)Records[i]=Records[i+1];return true;}
};
FCommInbox G_CommInboxPlayer,other;
constexpr unsigned kCommInboxCapacity=16;
void CommCopyMessage(FCommMessage* a,FCommMessage const* b){*a=*b;}
struct Line{unsigned MsgId;void* Msg;};
struct Profile{std::map<unsigned,void*> entries;void* FindMessage(unsigned id){return entries[id];}}profile;
Profile* LookupClientVoice(unsigned){return &profile;}
struct Channel{unsigned CompleteSender=0;std::vector<Line> Lines;int cancellations=0;bool done=true;
 void Cancel(){++cancellations;Lines.clear();done=true;}bool TickVoice(float){return done;}}channel;
struct Slot{FCommInbox* Inbox=&G_CommInboxPlayer;bool bActive=false,bDeferred=false;int Priority=0;struct Channel* Channel=&channel;};
using FCommSlot=Slot;
struct HUD_Receiver{Slot SlotA,SlotB;int dispatched=0;
 static void CommCancelled(FCommMessage const* msg){assert(msg->Result==CANCELLED);}
 static int MaxVoicePriority(FCommMessage const* msg){return classify(msg->TextIds[0],CreateID)==Courier?-6:-1;}
 void Dispatch(Slot* slot,FCommMessage*){++dispatched;slot->Channel->done=false;}
 void UpdateSlot(Slot*,float);
}hud;
void* GetHudCommInstance(){return &hud;}
'''
    code+='\n'+block(source,'static TrainEvacuationAudio::Kind EvacuationCommKind(')
    code+='\n'+block(source,'static TrainEvacuationAudio::Kind ActiveEvacuationCommKind(')
    code+='\n'+block(source,'static void PruneEvacuationComms(')
    code+='\n'+block(source,'void HUD_Receiver::UpdateSlot(')
    code+=r'''
FCommMessage msg(char const* name,unsigned receiver=1){FCommMessage m;m.TextCount=1;m.TextIds[0]=CreateID(name);m.Receiver=receiver;return m;}
void add(char const* name){G_CommInboxPlayer.Records[G_CommInboxPlayer.Count++]=msg(name);}
void reset(){G_CommInboxPlayer.Count=0;hud.SlotA=Slot{};hud.SlotB=Slot{};hud.SlotB.Inbox=&other;channel.Lines.clear();channel.cancellations=0;channel.done=true;hud.dispatched=0;}
void play(char const* name){unsigned id=CreateID(name);profile.entries[id]=&profile;channel.Lines.push_back({id,&profile});hud.SlotA.bActive=true;channel.done=false;hud.SlotA.Priority=classify(id,CreateID)==Courier?-6:-1;}
int main(){
 for(auto const& f:families)for(int n=1;n<=5;++n){char s[90];std::snprintf(s,sizeof(s),"%s_%02d-",f.name,n);assert(classify(CreateID(s),CreateID)==f.kind);}
 reset();add("te_confirm_loaded_01-");play("te_confirm_loaded_02-");
 PruneEvacuationComms(msg("te_cancel_03-"),&G_CommInboxPlayer);
 assert(G_CommInboxPlayer.Count==0 && channel.cancellations==1);
 // New player ship ID after return must cancel both pending and playing countdown.
 reset();add("te_return_30_02-");add("te_return_10_04-");add("ordinary_station_01-");play("te_return_10_05-");
 PruneEvacuationComms(msg("te_return_loaded_02-",99),&G_CommInboxPlayer);
 assert(G_CommInboxPlayer.Count==1 && EvacuationCommKind(G_CommInboxPlayer.Records[0])==Other && channel.cancellations==1);
 // Full inbox is freed before the new emergency report is appended.
 reset();for(int n=0;n<16;++n)add("tc_collect_01-");play("tc_depart_03+");
 channel.Lines.push_back({CreateID("base_name"),nullptr});
 PruneEvacuationComms(msg("te_critical_02-"),&G_CommInboxPlayer);
 assert(G_CommInboxPlayer.Count==0 && channel.cancellations==1);
 // Critical -> clear -> loss is a coherent sequence, not a numeric priority drop.
 reset();play("te_critical_01-");add("te_emergency_clear_05-");add("tc_continue_01-");
 PruneEvacuationComms(msg("te_battle_loaded_03-",99),&G_CommInboxPlayer);
 assert(channel.cancellations==0 && G_CommInboxPlayer.Count==1 && EvacuationCommKind(G_CommInboxPlayer.Records[0])==Clear);
 assert(G_CommInboxPlayer.Records[0].Receiver==99);
 reset();add("te_return_30_01-");PruneEvacuationComms(msg("te_return_10_02-"),&G_CommInboxPlayer);assert(!G_CommInboxPlayer.Count);
 reset();add("te_return_failed_01-");play("te_late_01-");PruneEvacuationComms(msg("te_return_10_02-"),&G_CommInboxPlayer);assert(!G_CommInboxPlayer.Count && channel.cancellations==1);
 reset();add("te_departed_01-");play("te_return_10_01-");PruneEvacuationComms(msg("te_timeout_empty_01-"),&G_CommInboxPlayer);assert(!G_CommInboxPlayer.Count && channel.cancellations==1);
 // Other senders, voices, inboxes and ordinary messages keep retail behavior.
 reset();add("te_return_30_01-");auto foreign=msg("te_battle_loaded_01-");foreign.Sender=45;
 PruneEvacuationComms(foreign,&G_CommInboxPlayer);assert(G_CommInboxPlayer.Count==1);
 foreign.Sender=0;foreign.VoiceId=CreateID("other_voice");PruneEvacuationComms(foreign,&G_CommInboxPlayer);assert(G_CommInboxPlayer.Count==1);
 PruneEvacuationComms(msg("te_battle_loaded_01-"),&other);assert(G_CommInboxPlayer.Count==1);
 PruneEvacuationComms(msg("ordinary_station_01-"),&G_CommInboxPlayer);assert(G_CommInboxPlayer.Count==1);
 // Real UpdateSlot must retain the first order while the intro is playing.
 reset();play("te_intro_01-");add("tc_collect_01-");
 for(int i=0;i<60;++i)hud.UpdateSlot(&hud.SlotA,.1f);
 assert(G_CommInboxPlayer.Count==1 && channel.cancellations==0 && hud.dispatched==0);
 channel.done=true;hud.UpdateSlot(&hud.SlotA,.1f);assert(G_CommInboxPlayer.Count==0 && hud.dispatched==1);
 reset();play("tc_paid_01-");add("te_delivered_01-");hud.UpdateSlot(&hud.SlotA,.1f);
 assert(channel.cancellations==0 && G_CommInboxPlayer.Count==1);
 puts("PASS production radio pruning: cancel, transfer, countdown, return, timeout, critical/clear/loss, full queue, unrelated comms");
}
'''
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'evacuation_audio_queue.cpp').write_text(code,encoding='utf-8')
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17','/I'+str(ROOT/'src/include'),
        'evacuation_audio_queue.cpp','/Fe:evacuation_audio_queue.exe'],cwd=OUT,env=env,check=True)
    subprocess.run([str(OUT/'evacuation_audio_queue.exe')],cwd=OUT,check=True,timeout=10)

if __name__=='__main__':main()
