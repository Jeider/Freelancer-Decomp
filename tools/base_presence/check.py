"""Compile the actual base-presence router with fake authenticated connections."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
sys.path.insert(0,str(ROOT/'tools/train_courier'))
from check_transfer_docking import block


def main():
    code = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <vector>
#include <string>
#include <limits>
#include "base_presence.h"
using DWORD=unsigned;DWORD clockMs=1000;
DWORD GetTickCount(){return clockMs;}
bool single=false;bool SinglePlayer(){return single;}
struct Costume {unsigned PartIds[4]={},AccessoryIds[8]={},AccessoryCount=0;};
struct Slot {unsigned client_id=0,current_base=0,current_location=0;Costume costume;std::wstring name;};
struct Database {
    std::map<unsigned,Slot> slots;
    bool is_valid(unsigned id){return id&&slots.count(id)&&slots[id].client_id;}
    Slot& operator[](unsigned id){return slots.at(id);}
    Slot* traverse_active(Slot* previous){
        auto it=previous?slots.upper_bound(previous->client_id):slots.begin();
        return it==slots.end()?nullptr:&it->second;
    }
} Players;
struct CHAT_ID {unsigned Id;explicit CHAT_ID(unsigned id):Id(id){}};
struct Delivery {unsigned to,from;BasePresence::Packet packet;};
struct ChatClient {
    std::vector<Delivery> sent;
    void SendCommonChatMsg(CHAT_ID to,CHAT_ID from,unsigned size,void const* data){
        BasePresence::Packet packet;assert(BasePresence::Decode(data,size,packet));
        sent.push_back({to.Id,from.Id,packet});
    }
} chat;
ChatClient* g_pChatClientInterface=&chat;
namespace pub {namespace Player {int GetName(unsigned id,std::wstring& name){name=Players[id].name;return 0;}}}
#include "base_presence.inl"
BasePresence::Packet Request(unsigned base=10,unsigned room=20){BasePresence::Packet p;p.base=base;p.room=room;return p;}
void Send(unsigned id,BasePresence::Packet p){clockMs+=100;RouteBasePresence(id,sizeof(p),&p);}
void Join(unsigned id,unsigned base,unsigned room){auto& s=Players.slots[id];s.client_id=id;s.current_base=base;s.current_location=room;s.name=L"Guest"+std::to_wstring(id);s.costume.PartIds[1]=100+id;}
int main(){
    Join(1,10,20);Join(2,10,20);Join(3,10,21);Join(4,11,20);Join(5,10,20);
    Send(1,Request());assert(chat.sent.empty());
    Send(2,Request());Send(3,Request(10,21));Send(4,Request(11,20));chat.sent.clear();
    auto p=Request();p.visible=1;p.motion=2;p.position[0]=12.5f;p.player=99;p.parts[1]=999;p.name[0]=u'X';p.accessoryCount=999;
    Send(1,p);assert(chat.sent.size()==1);
    auto const& d=chat.sent.back();assert(d.to==2&&d.from==BasePresence::Channel&&d.packet.player==1);
    assert(d.packet.parts[1]==101&&d.packet.name[0]==u'G'&&d.packet.accessoryCount==0&&d.packet.position[0]==12.5f);
    chat.sent.clear();RouteBasePresence(1,sizeof(p),&p);assert(chat.sent.empty()); // rate limit
    auto bad=p;bad.position[1]=std::numeric_limits<float>::quiet_NaN();Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.yaw=std::numeric_limits<float>::infinity();Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.position[0]=100001;Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.visible=2;Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.motion=8;Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.version=1;Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.animationMs=300001;Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.magic=0;Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.base=11;Send(1,bad);assert(chat.sent.empty());
    bad=p;bad.room=21;Send(1,bad);assert(chat.sent.empty());
    RouteBasePresence(1,sizeof(p)-1,&p);RouteBasePresence(1,sizeof(p),nullptr);Send(999,p);assert(chat.sent.empty());
    single=true;Send(1,p);assert(chat.sent.empty());single=false;
    Send(2,Request());chat.sent.clear();Send(1,p);assert(chat.sent.size()==1);chat.sent.clear();
    Server_BasePresenceForget(1);assert(chat.sent.size()==1&&!chat.sent.back().packet.visible&&!GPresenceClients.count(1));
    chat.sent.clear();Send(2,Request());assert(chat.sent.empty()); // no stale slot capability
    Players[1].current_location=21;Send(1,Request(10,21));chat.sent.clear();
    Send(2,p);assert(chat.sent.empty()); // different rooms after movement
    clockMs+=BasePresence::TimeoutMs+1;Players[1].current_location=20;Send(1,p);assert(chat.sent.empty());
    // Request validation also rejects an unaligned buffer safely via memcpy.
    char raw[sizeof(p)+1];memcpy(raw+1,&p,sizeof(p));BasePresence::Packet decoded;
    assert(BasePresence::Decode(raw+1,sizeof(p),decoded));
    Send(2,Request());chat.sent.clear();p.motion=5;p.animationSerial=17;p.animationMs=1250;
    Send(1,p);assert(chat.sent.size()==1);
    assert(chat.sent.back().packet.motion==5&&chat.sent.back().packet.animationSerial==17&&chat.sent.back().packet.animationMs==1250);
    puts("PASS actual router: authenticated identity/costume, capability, base+room isolation, rate limit, malformed payload, SP, exit/reuse, expiry");
}
'''
    out=ROOT/'out/base_presence/check'
    out.mkdir(parents=True,exist_ok=True)
    (out/'router.cpp').write_text(code,encoding='utf-8')
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17',
                    '/I'+str(ROOT/'src/include'),'/I'+str(ROOT/'src/Server'),
                    'router.cpp','/Fe:router.exe'],cwd=out,env=env,check=True)
    subprocess.run([str(out/'router.exe')],cwd=out,env=env,check=True,timeout=15)
    source=(ROOT/'src/freelancer/Client/base_presence_client.inl').read_text(encoding='utf-8')
    client=r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <memory>
#include "base_presence.h"
using DWORD=unsigned;DWORD GetTickCount(){return 1000;}
bool single=false,onBase=true;bool SinglePlayer(){return single;}bool IsBase(){return onBase;}
unsigned GetPlayerConnectionId(){return 1;}
struct FRoomRuntime{unsigned base=10,room=20;} room,other;
FRoomRuntime* current=&room;
void* GetClientCurrentLocationRuntime(){return current;}
unsigned GetRoomRuntimeBaseId(FRoomRuntime* r){return r->base;}
unsigned GetRoomRuntimeRoomId(FRoomRuntime* r){return r->room;}
int clears=0,destroyed=0;
struct FBasePeer {
    BasePresence::Packet state;unsigned received=0;void* body=nullptr;
    std::unique_ptr<int> label;
    void ClearBody(){++clears;body=nullptr;}
    ~FBasePeer(){++destroyed;}
};
std::map<unsigned,std::unique_ptr<FBasePeer>> GBasePeers;
FRoomRuntime* GBasePeerRoom=nullptr;DWORD GBasePresenceSent=0;
'''+block(source,'void BasePresenceClear()')+'\n'+block(source,'void BasePresenceRoomDestroyed(')+'\n'+block(source,'bool BaseWalkReceivePresence(')+r'''
int main(){
    BasePresence::Packet p;p.player=2;p.base=10;p.room=20;p.visible=1;p.parts[1]=11;p.name[0]=u'B';
    auto receive=[&](){return BaseWalkReceivePresence(BasePresence::Channel,sizeof(p),&p);};
    assert(!BaseWalkReceivePresence(2,sizeof(p),&p));assert(GBasePeers.empty());
    assert(receive()&&GBasePeers.size()==1&&GBasePeerRoom==&room);
    auto& peer=*GBasePeers[2];peer.body=&room;peer.label.reset(new int(1));
    unsigned before=clears;receive();assert(clears==before&&peer.body&&peer.label);
    p.parts[1]=12;receive();assert(!peer.body&&peer.label);peer.body=&room;
    p.name[0]=u'C';receive();assert(!peer.body&&!peer.label);peer.body=&room;
    p.visible=0;receive();assert(!peer.body);p.visible=1;
    p.player=1;receive();assert(GBasePeers.size()==1);p.player=3;
    p.base=11;receive();assert(GBasePeers.size()==1);p.base=10;p.room=21;receive();assert(GBasePeers.size()==1);p.room=20;
    p.accessoryCount=9;receive();assert(GBasePeers.size()==1);p.accessoryCount=0;
    single=true;receive();assert(GBasePeers.size()==1);single=false;onBase=false;receive();assert(GBasePeers.size()==1);onBase=true;
    BasePresenceRoomDestroyed(&other);assert(GBasePeers.size()==1);
    BasePresenceRoomDestroyed(&room);assert(GBasePeers.empty()&&!GBasePeerRoom&&destroyed==1);
    receive();assert(GBasePeers.size()==1);other.base=10;other.room=21;current=&other;p.room=21;
    receive();assert(GBasePeers.size()==1&&GBasePeerRoom==&other&&destroyed==2);
    BasePresenceClear();assert(GBasePeers.empty()&&destroyed==3);
    puts("PASS actual client receiver: channel/room/self/size validation, repeated pose, costume/name change, hide, room teardown and transition");
}
'''
    (out/'client.cpp').write_text(client,encoding='utf-8')
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17',
                    '/I'+str(ROOT/'src/include'),'client.cpp','/Fe:client.exe'],cwd=out,env=env,check=True)
    subprocess.run([str(out/'client.exe')],cwd=out,env=env,check=True,timeout=15)


if __name__=='__main__':main()
