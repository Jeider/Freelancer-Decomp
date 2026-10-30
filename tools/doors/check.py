"""Asset invariants and executable tests of the production server manager and wire codecs."""
from prepare import *
import os
import subprocess

def leaves(data):
    result={}
    def walk(node,path=''):
        path+='/'+node.name
        if node.blob is not None: result[path]=node.blob
        for c in node.children: walk(c,path)
    for n in read_tree(data)[1]: walk(n)
    return result
raw=(GAME/MODEL).read_bytes(); patched=patch_model(raw)
before,after=leaves(raw),leaves(patched)
assert all(after[k]==v for k,v in before.items()), 'legacy clips/geometry changed'
assert leaves(patch_model(patched))==after
scripts=child(child(read_tree(patched)[1][0],'Animation'),'Script')
for name,count in [('sc_door_open',101),('sc_door_close',2)]:
    script=child(scripts,name); assert len(script.children)==6
    for joint in script.children:
        c=child(joint,'Channel'); n,step,flags=struct.unpack('<IfI',child(c,'Header').blob)
        frames=list(struct.iter_unpack('<ff',child(c,'Frames').blob))
        assert n==count==len(frames) and step==-1 and flags==1
        assert abs(frames[-1][0]-3.333333)<.00001
        assert all(a[0]<b[0] for a,b in zip(frames,frames[1:]))
        assert abs(frames[-1][1] - (-1.047198 if name.endswith('open') else 0))<.00001
ini=(GAME/SOLAR).read_bytes(); modified=patch_solar(ini)
assert modified.startswith(ini), 'existing solar definitions changed'
assert patch_solar(modified)==modified
print('PASS assets: six joints, finite open/close, original poses/geometry/legacy scripts preserved, idempotent')

out=ROOT/'src/obj/doors/check'; out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(str(p) for p in [vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB']=';'.join(str(p) for p in [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
def run(name,source):
    (out/(name+'.cpp')).write_text(source)
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT',name+'.cpp','/Fe'+name+'.exe'],cwd=out,env=env,check=True)
    subprocess.run([str(out/(name+'.exe'))],check=True)
def body(path):
    return re.sub(r'^#include.*\n','', (ROOT/path).read_text(),flags=re.M)
header=body('src/include/solar_animation.h').replace('#pragma once','').replace('COMMON_API','')
server=body('src/Server/server_solar_animation.cpp')
run('manager',r'''
#include <map>
#include <set>
#include <cmath>
#include <cstring>
#include <algorithm>
#include <vector>
#include <cassert>
#include <cstdio>
#define FDUMP(...) ((void)0)
''' + header + '\n#include "'+str(ROOT/'src/include/door_state.h').replace('\\','/')+'"\n'+r'''
struct Vector { float x=0,y=0,z=0; };
namespace Archetype { struct Root { bool automatic=true; }; }
class CSolar { public: Archetype::Root* Archetype=nullptr; unsigned ObjectClass=0x303; float Radius=10; float get_radius(){return Radius;} };
struct GameObject { CSolar* raw; unsigned id; Vector pos; bool dead=false;
 bool is_destroyed(){return dead;} CSolar* cobj(){return raw;} unsigned get_id(){return id;} Vector const& get_position(){return pos;} };
struct Node { Node* Next=nullptr; GameObject* Data=nullptr; };
struct SystemPlayerNode { SystemPlayerNode* Next; struct { unsigned PlayerId; } View; };
class StarSystem { public: struct { Node* Head=nullptr; } Solars,Ships; void* PlayerListHead; };
struct FPayloadServerActivateObject { unsigned ObjectId=0; unsigned char bActivate=0; unsigned Field_0x08=0; SolarAnimationCommand Animation; };
struct Client { std::vector<FPayloadServerActivateObject> packets; void SendServerActivateObject(unsigned,FPayloadServerActivateObject const& p){packets.push_back(p);} } client;
using IClient=Client;
IClient* g_pClientInterface=&client;
std::map<unsigned,GameObject*> objects; StarSystem* world;
GameObject* Server_LookupGameObject(unsigned id){auto it=objects.find(id);return it==objects.end()?nullptr:it->second;}
bool Server_FindLiveObject(unsigned id,GameObject*& obj,StarSystem*& sys){obj=Server_LookupGameObject(id);sys=world;return obj&&!obj->dead;}
namespace SolarAnimation {
 bool GetConfig(Archetype::Root const* a, Config& c){strcpy_s(c.Open,"open");strcpy_s(c.Close,"close");c.OpenSound=11;c.CloseSound=12;return a&&a->automatic;}
 float Duration(CSolar const*,char const* n){return (!strcmp(n,"open")||!strcmp(n,"close")||!strcmp(n,"extra"))?3.333333f:-1;}
 unsigned plays=0;
 bool Play(CSolar*,SolarAnimationCommand const& c){++plays;return c.Name[0]!=0;}
}
''' + server + r'''
int main(){
 StarSystem sys;world=&sys;SystemPlayerNode head{},player{};head.Next=&player;player.Next=&head;player.View.PlayerId=1;sys.PlayerListHead=&head;
 Archetype::Root arch;CSolar door,ship;door.Archetype=&arch;ship.ObjectClass=0x503;
 GameObject d{&door,101,{}},s{&ship,201,{5000,0,0}};Node dn{nullptr,&d},sn{nullptr,&s};sys.Solars.Head=&dn;sys.Ships.Head=&sn;objects[101]=&d;
 auto step=[&](int count){for(int i=0;i<count;++i)UpdateSolarAnimations(sys,.1f);};
 step(40);assert(client.packets.empty()); // no activation while empty
 s.pos.x=700;step(1);assert(client.packets.size()==1&&!strcmp(client.packets.back().Animation.Name,"open"));
 assert(!StartSolarAnimation(101,"close")); // busy: no restart or queue
 step(100);assert(client.packets.size()==1); // occupant cannot retrigger
 s.pos.x=1000;step(60);assert(client.packets.size()==1); // hysteresis
 s.pos.x=5000;step(29);assert(client.packets.size()==1);step(2);assert(client.packets.size()==2);
 assert(!strcmp(client.packets.back().Animation.Name,"close"));
 step(10);float at=Managers[&sys].Objects[101].Command.Time;
 s.pos.x=700;step(1);assert(client.packets.size()==3&&client.packets.back().Animation.Reverse==1);
 assert(fabs(client.packets.back().Animation.Time-(at+.1f))<.001); // reverse exact current clip time
 step(40);assert(Managers[&sys].Objects[101].Door.Current==ProximityDoor::Phase::Open);
 auto last=client.packets.size();SendSolarAnimations(sys,2);assert(client.packets.size()==last+1&&client.packets.back().Animation.Sound==0);
 assert(client.packets.back().Animation.Time==0); // late join sees held open pose of reversed closing clip
 s.pos.x=5000;step(80);assert(Managers[&sys].Objects[101].Door.Current==ProximityDoor::Phase::Closed);
 assert(!StartSolarAnimation(101,"missing"));assert(!StartSolarAnimation(999,"open"));
 assert(StartSolarAnimation(101,"open"));last=client.packets.size();step(10);assert(client.packets.size()==last); // script owns busy clip
 assert(!StartSolarAnimation(101,"open"));
 step(80);assert(StartSolarAnimation(101,"extra"));step(80);last=client.packets.size();s.pos.x=0;step(80);assert(client.packets.size()==last); // unrelated clip suspends scanner
 assert(StartSolarAnimation(101,"open"));step(40);assert(Managers[&sys].Objects[101].Door.Current==ProximityDoor::Phase::Open);
 d.dead=true;step(1);assert(Managers[&sys].Objects.empty());ForgetSolarAnimations(sys);assert(Managers.empty());
 puts("PASS production manager: proximity, NPCs, hysteresis, delay, no repeat/queue, reversal, snapshots, script ownership, missing clips, cleanup");
}
''')

run('playback',r'''
#include <map>
#include <set>
#include <cmath>
#include <cstring>
#include <algorithm>
#include <string>
#include <cassert>
#include <cstdio>
#define FDUMP(...) ((void)0)
''' + header + r'''
namespace Archetype {struct Root{int get_script_index()const{return 1;}};}
class CSolar {public: Archetype::Root* Archetype; int EngineInstanceId=1;};
class INI_Reader { public: std::string key,text;
 bool is_value(char const* k){return key==k;} bool get_value_bool(int){return text=="true";}
 float get_value_float(int){return std::stof(text);} char const* get_value_string(){return text.c_str();} };
unsigned CreateID(char const* s){return *s?42:0;}
void* AsOpaqueDword(int n){return reinterpret_cast<void*>(n);}
void* AsOpaqueDword(float f){unsigned n;memcpy(&n,&f,4);return reinterpret_cast<void*>(n);}
namespace AnimDB { std::set<int> active;void Add(int n){active.insert(n);}void Rem(int n){active.erase(n);} }
struct Engine {
 struct Record {float time=0;unsigned flags=0;};std::map<int,Record> records;int next=0;bool fail=false,empty=false;
 float GetNamedDuration(void*,char const* n){return !strcmp(n,"missing")?-1:!strcmp(n,"forever")?1e16f:3.333333f;}
 unsigned PlayScript(void*,void*,char const*,void*,void*){if(fail)return -1;records[++next]={};return next;}
 void EnumObjects(void* cb,int,void* count){if(!empty)for(int i=0;i<6;++i)reinterpret_cast<unsigned char(__cdecl*)(void*,void*)>(cb)(nullptr,count);}
 void StopPlayback(int){}
 void DestroyScript(void* p){records.erase(reinterpret_cast<int>(p));}
 void EvalPlayback(int h,unsigned flags,float t,float,void*,void*,void*,void*){records.at(h)={t,flags};}
}engine;
namespace DALib {Engine* Anim=&engine;}
''' + body('src/Common/solar_animation.cpp') + r'''
int main(){
 Archetype::Root a,b;CSolar obj{&a};SolarAnimation::Config config;
 auto read=[&](char const*k,char const*v){INI_Reader r{k,v};assert(SolarAnimation::Read(&a,r));};
 assert(!SolarAnimation::GetConfig(&a,config));read("proximity_door","true");read("anim_open","open");read("anim_close","close");
 read("door_scan_radius","900");read("door_release_radius","100");read("door_close_delay","nan");
 assert(SolarAnimation::GetConfig(&a,config)&&config.ReleaseRadius==901&&config.CloseDelay==3);
 SolarAnimation::Copy(&b,&a);assert(SolarAnimation::GetConfig(&b,config));SolarAnimation::ForgetDefinition(&b);assert(!SolarAnimation::GetConfig(&b,config));
 SolarAnimation::Initialize(&obj);assert(engine.records.size()==1);assert(engine.records.begin()->second.time>3.3f); // held closed, finite clip
 SolarAnimationCommand c;strcpy_s(c.Name,"open");c.Serial=1;assert(SolarAnimation::Play(&obj,c));assert(engine.records.size()==1);
 int last=engine.next;assert(!SolarAnimation::Play(&obj,c)&&engine.next==last); // packet dedup
 c.Serial=2;c.Time=1.5f;c.Reverse=1;assert(SolarAnimation::Play(&obj,c));assert(engine.records.at(engine.next).flags==1&&engine.records.at(engine.next).time==1.5f);
 c.Serial=3;engine.empty=true;assert(!SolarAnimation::Play(&obj,c));engine.empty=false;assert(engine.records.size()==1); // unbound clip leaves old pose
 engine.fail=true;assert(!SolarAnimation::Play(&obj,c));engine.fail=false;
 strcpy_s(c.Name,"forever");assert(!SolarAnimation::Play(&obj,c));strcpy_s(c.Name,"missing");assert(!SolarAnimation::Play(&obj,c));
 memset(c.Name,'x',sizeof(c.Name));assert(!SolarAnimation::Play(&obj,c));strcpy_s(c.Name,"open");c.Time=NAN;assert(!SolarAnimation::Play(&obj,c));
 SolarAnimation::Forget(&obj);SolarAnimation::Forget(&obj);assert(engine.records.empty()&&AnimDB::active.empty());
 SolarAnimation::ForgetDefinition(&a);
 puts("PASS production playback: finite duration, terminal hold, reverse seek, config/inheritance, duplicate/invalid packets, missing bindings, lifetime cleanup");
}
''')

def function(path,name):
    text=(ROOT/path).read_text(); start=text.index('unsigned int '+name+'(')
    brace=text.index('{',start); depth=1; end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}'); end+=1
    return text[start:end]
remote='src/RemoteCommon/remote_server_channel_codecs.cpp'
local='src/rpclocal/rpc_wire_fields.cpp'
run('wire',r'''
#include <cstring>
#include <cassert>
#include <cstdio>
#include <algorithm>
''' + header + r'''
struct FPayloadServerActivateObject {unsigned ObjectId;unsigned char bActivate;unsigned char pad[3];unsigned Field_0x08;SolarAnimationCommand Animation;};
struct FPacketBase {unsigned PacketId=0x2000a;FPayloadServerActivateObject data{};void* Payload(){return &data;}};
struct Stream {
 unsigned char* buf;unsigned capacity,pos=2;bool failed=false;
 Stream(unsigned char* b,unsigned c):buf(b),capacity(c){if(c<2)failed=true;}
 bool Put(void const* p,unsigned n){if(failed||n>capacity-pos){failed=true;return false;}memcpy(buf+pos,p,n);pos+=n;return true;}
 bool Get(void* p,unsigned n){if(failed||n>capacity-pos){failed=true;return false;}memcpy(p,buf+pos,n);pos+=n;return true;}
 void PutHeader(){buf[0]=0x0a;buf[1]=2;}
 unsigned FinishEncodeSuccess(unsigned* out){*out=pos;return failed?22:0;}
 unsigned Finish(unsigned* out,bool){return FinishEncodeSuccess(out);}
};
struct FRpcWireStream:Stream {
 FRpcWireStream(FPacketBase&,unsigned char** p,unsigned c):Stream(*p,c){}
 FRpcWireStream(FPacketBase&,unsigned char* p,unsigned c):Stream(p,c){}
};
struct FRpcMarshalStream:Stream {
 FRpcMarshalStream(FPacketBase&,unsigned char* p,unsigned c):Stream(p,c){}
 void PutHeaderUnchecked(unsigned){PutHeader();}void PutDword(unsigned v){Put(&v,4);}void PutByte(unsigned char v){Put(&v,1);}
 bool PutBytes(void const*p,unsigned n){return Put(p,n);}bool GetBytes(void*p,unsigned n){return Get(p,n);}
 bool GetDword(unsigned& v){return Get(&v,4);}bool GetByte(unsigned char& v){return Get(&v,1);}
 bool Failed(){return failed;}unsigned GetError(){return 22;}unsigned Length(){return pos;}
};
unsigned RpcPacketHeaderWord(unsigned){return 0x020a;}void RpcRecordEncodedPacket(unsigned,unsigned){}void RpcRecordDecodedPacket(unsigned,unsigned){}
struct FRpcServerActivateObjectPacket:FPacketBase {
 unsigned ObjectId=0;unsigned char bActivate=0;unsigned Field_0x08=0;SolarAnimationCommand Animation;
 unsigned MarshalError=22;
 unsigned Encode(unsigned char**,unsigned,unsigned*);unsigned Decode(unsigned char const*,unsigned,unsigned*);
};
''' + '\n'.join(function(remote,'FRpcServerActivateObjectPacket::'+n) for n in ['Encode','Decode'])+
 '\n'+ '\n'.join(function(local,'Rpc'+n+'ServerActivateObject') for n in ['Encode','Decode'])+r'''
int main(){
 unsigned char a[256]{},b[256]{};unsigned char* pa=a;unsigned char* pb=b;unsigned an=0,bn=0,read=0;
 for(unsigned mode: {0u,1u,2u}){
  FRpcServerActivateObjectPacket p,q;p.ObjectId=123;p.bActivate=mode;p.Field_0x08=5;
  strcpy_s(p.Animation.Name,"sc_door_close");p.Animation.Time=1.25f;p.Animation.Reverse=1;p.Animation.Sound=456;p.Animation.Serial=77;
  FPacketBase l,m;l.data.ObjectId=p.ObjectId;l.data.bActivate=p.bActivate;l.data.Field_0x08=p.Field_0x08;l.data.Animation=p.Animation;
  assert(p.Encode(&pa,sizeof(a),&an)==0);assert(RpcEncodeServerActivateObject(l,&pb,sizeof(b),&bn)==0);
  assert(an==bn&&an==(mode==2?123:11)&&!memcmp(a,b,an)); // original native wire stays 11 bytes including header
  assert(q.Decode(b,bn,&read)==0&&read==bn&&q.ObjectId==123&&q.Field_0x08==5&&q.bActivate==mode);
  assert(RpcDecodeServerActivateObject(m,a,an,&read)==0&&read==an&&m.data.ObjectId==123);
  if(mode==2){assert(!memcmp(&q.Animation,&p.Animation,sizeof(p.Animation)));assert(!memcmp(&m.data.Animation,&p.Animation,sizeof(p.Animation)));}
  for(unsigned size=2;size<an;++size){assert(q.Decode(a,size,&read)!=0);assert(RpcDecodeServerActivateObject(m,a,size,&read)!=0);}
 }
 puts("PASS production local/remote codecs: native wire unchanged, animation roundtrip/cross-transport, all truncated lengths rejected");
}
''')
