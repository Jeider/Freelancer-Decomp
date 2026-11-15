"""Check shipped clip names and the actual peer playback/restart logic."""
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_courier'))
from check_transfer_docking import block
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
names=re.findall(r'"(Sc_[^"]+)"',(ROOT/'src/include/base_emotes.h').read_text())
asset=Path('D:/Games/FL_MOD/DATA/CHARACTERS/ANIMATIONS/bodygenericmale.anm').read_bytes().lower()
assert len(names)==8
for name in names: assert name.lower().encode()+b'\0' in asset,name
code=r'''
#include <cassert>
#include <cstring>
#include <cstdint>
#include <map>
#include <string>
#include "base_presence.h"
#include "base_emotes.h"
unsigned now=1100;unsigned GetTickCount(){return now;}
unsigned CreateID(char const* s){unsigned h=0;while(*s)h=h*33+*s++;return h;}
void* AsOpaqueDword(float f){unsigned v;memcpy(&v,&f,4);return (void*)(uintptr_t)v;}
void* AsOpaqueDword(unsigned long n){return (void*)(uintptr_t)n;}
struct Body {struct {void* Instance=(void*)1;} Lod;void RemoveMotionHandle(int){}void AddMotionHandle(int){}} body;
struct Db {
 struct Record{std::string Name;};std::map<unsigned,Record> Scripts;
 int refs=0;void* AcquireScriptByName(char const*){++refs;return (void*)1;}
 void ReleaseScript(unsigned){--refs;}
} db;
Db* GetCharacterInfoDb(){return &db;}
int plays=0;float offset=0;unsigned flags=0;
struct Deform {
 void DestroyHandle(void*,int){}
 void Play(void*,int* h,void*,char*,void* start,void*,void*,void*,void* f,void*,void*) {
  ++plays;*h=42;unsigned bits=(unsigned)(uintptr_t)start;memcpy(&offset,&bits,4);flags=(unsigned)(uintptr_t)f;
 }
} deform;
int held=0;float heldTime=0;
struct Anim {
 float GetNamedDuration(void*,char const*){return 2.f;}
 void StopChannels(unsigned handle,void* time){assert(handle==42);unsigned bits=(unsigned)(uintptr_t)time;memcpy(&heldTime,&bits,4);}
 void ApplyChannels(unsigned handle){assert(handle==42&&heldTime==-1.f);++held;}
} anim;
namespace DALib {Deform* Deform=&deform;Anim* Anim=&anim;}
struct FBasePeer {
 BasePresence::Packet state;Body* body=&::body;int motion=-1,motionHandle=-1;
 unsigned animationSerial=0,scriptId=0,received=1000;struct{float Yaw=0;}pose;
 float duration=0;
};
'''
source=(ROOT/'src/freelancer/Client/base_presence_client.inl').read_text()
walk=(ROOT/'src/freelancer/Client/base_walk.cpp').read_text()
code+=block(walk,'void HoldEmoteLastFrame(')+'\n'
code+=block(source,'void PeerMotion(')+r'''
int main(){
 for(unsigned i=0;i<8;++i)db.Scripts[CreateID(BaseEmotes::Name(i))]={BaseEmotes::Name(i)};
 FBasePeer p;p.state.motion=3;p.state.animationSerial=1;p.state.animationMs=500;
 PeerMotion(p);assert(plays==1&&db.refs==1&&offset>.59f&&offset<.61f&&flags==0);
 now+=100;PeerMotion(p);assert(plays==1);
 p.state.animationSerial=2;PeerMotion(p);assert(plays==2&&db.refs==1);
 p.state.motion=1;PeerMotion(p);assert(plays==3&&db.refs==1&&offset==0&&flags==2);
 p.state.motion=0;PeerMotion(p);assert(plays==4&&db.refs==1);
 assert(held==0&&BaseEmotes::Finished(3,3.f,2.f)&&!BaseEmotes::Finished(7,300.f,2.f));
 p.state.motion=7;p.state.animationMs=500;PeerMotion(p);assert(plays==5&&held==0);
 now+=2500;PeerMotion(p);assert(plays==5&&held==1); // finish without idle or replay
 PeerMotion(p);assert(plays==5&&held==2);
 p.state.animationSerial++;p.state.animationMs=0;p.received=now;
 PeerMotion(p);assert(plays==6&&held==2); // click again starts raising again
 p.state.motion=1;PeerMotion(p);assert(plays==7&&held==2); // movement cancels hold
 FBasePeer late;late.state.motion=7;late.state.animationSerial=9;late.state.animationMs=300000;late.received=now;
 PeerMotion(late);assert(plays==8&&held==3&&offset==0.f); // late join at held final pose
 HoldEmoteLastFrame(7,-1,99.f,2.f);assert(held==3);
 puts("PASS raised hands: final pose, repeated packets, replay, movement cancellation and late join after long hold");
 puts("PASS peer emotes: late phase, no restart on repeated state, new serial restarts, movement/idle cancellation, balanced script refs");
}
'''
out=ROOT/'out/base_presence/emotes';out.mkdir(parents=True,exist_ok=True)
(out/'check.cpp').write_text(code)
compiler,env=compiler_env()
subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17','/I'+str(ROOT/'src/include'),'check.cpp','/Fe:check.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True)
print('PASS all five standard emotes found in bodygenericmale.anm')
