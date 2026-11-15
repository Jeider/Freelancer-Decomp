"""Replay the dump's empty/NaN hull state against the actual dispatch function."""
import os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/physics_nan_guard';OUT.mkdir(exist_ok=True)
FILE='src/IVP/ivp_physics/ivp_calc_next_psi_solver.cpp'
def function(source):
    start=source.index('    void CheckHullSynapsesAndReset(');end=source.index('{',start)+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
stub=r'''
#define NOMINMAX
#include <windows.h>
#include <initializer_list>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <limits>
#include "ivp_finite_guard.h"
#define FDUMP(...) ((void)0)
constexpr float GIvpZero=0,GIvpHullResetInterval=10;
struct IVP_Hull_Manager;
struct IVP_Listener_Hull {virtual void hull_limit_exceeded_event(IVP_Hull_Manager*,float)=0;};
struct Entry {void* Payload=nullptr;};
struct IVP_Hull_Manager {
 float LastEditTimeHi=4,LastEditTimeLo=.60238945f,OuterGradient=0,InnerGradient=0;
 float OuterValueAtLastEdit=0,InnerValueAtLastEdit=0,AccumulatedDeltaA=0;
 int TimeOfNextReset=13;
 uint16_t PoolCapacity=17,PoolLiveIndex=0xffff,PoolCount=0;
 Entry* PoolEntries=nullptr;float PoolKeyThreshold=1e10f;int drains=0;
 void DrainAndShift(){++drains;}
};
struct V {float x,y,z;};
struct Listener:IVP_Listener_Hull {
 int calls=0;bool poison=false;
 void hull_limit_exceeded_event(IVP_Hull_Manager* h,float d) override {
  assert(d==-1);++calls;h->PoolCount=0;h->PoolLiveIndex=0xffff;
  if(poison)h->AccumulatedDeltaA=std::numeric_limits<float>::quiet_NaN();
 }
};
'''
check=r'''
int main(int argc,char**){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 float nan=std::numeric_limits<float>::quiet_NaN(),inf=std::numeric_limits<float>::infinity();
 IVP_Hull_Manager h;h.OuterGradient=h.InnerGradient=h.OuterValueAtLastEdit=h.InnerValueAtLastEdit=h.AccumulatedDeltaA=nan;
 CheckHullSynapsesAndReset(&h); // The exact fatal empty-pool state from 2026-11-13.
 assert(h.drains==0);if(argc>1)return 0;
 h={};h.PoolKeyThreshold=-1;CheckHullSynapsesAndReset(&h);
 Listener l;Entry e{&l};h={};h.PoolCapacity=1;h.PoolCount=1;h.PoolLiveIndex=0;h.PoolEntries=&e;h.PoolKeyThreshold=-1;
 CheckHullSynapsesAndReset(&h);assert(l.calls==1); // callback emptied the queue
 h.PoolCount=1;h.PoolLiveIndex=0;l.poison=true;CheckHullSynapsesAndReset(&h);assert(l.calls==2);
 h={};h.LastEditTimeHi=20;CheckHullSynapsesAndReset(&h);assert(h.drains==1&&h.TimeOfNextReset==30);
 h={};h.PoolCapacity=1;h.PoolCount=1;h.PoolLiveIndex=1;h.PoolEntries=&e;h.PoolKeyThreshold=-1;
 CheckHullSynapsesAndReset(&h);assert(l.calls==2);
 for(float bad:{nan,inf,-inf}){
  V v{1,2,3},d{bad,1,2};assert(IvpFinite::Accumulate(v,d));assert(v.x==1&&v.y==2&&v.z==3&&d.x==0&&d.y==0&&d.z==0);
  v={bad,0,1};assert(IvpFinite::StopInvalid(v));assert(v.x==0&&v.y==0&&v.z==0);
 }
 V v{1,2,3},d{2,3,4};assert(!IvpFinite::Accumulate(v,d));assert(v.x==3&&v.y==5&&v.z==7);
 v={std::numeric_limits<float>::max(),0,0};d=v;assert(IvpFinite::Accumulate(v,d));assert(IvpFinite::Vector3(v));
 puts("PASS dump replay, callback queue removal, NaN callback, invalid indices, finite reset, NaN/Inf/overflow impulses and normal motion");
}
'''
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');ver='10.0.26100.0';env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[ROOT/'src/IVP/ivp_physics',vc/'include']+[sdk/'Include'/ver/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/ver/x/'x86' for x in ('ucrt','um')]))
for mode in ('old','guarded'):
    source=subprocess.check_output(['git','show','HEAD:'+FILE],cwd=ROOT).decode() if mode=='old' else (ROOT/FILE).read_text()
    (OUT/'check.cpp').write_text(stub+function(source)+check)
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/fp:fast','/EHsc','/MT','check.cpp','/Fe'+mode+'.exe'],cwd=OUT,env=env,check=True)
    result=subprocess.run([str(OUT/(mode+'.exe')),*(['dump-only'] if mode=='old' else [])],cwd=OUT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15)
    (OUT/(mode+'.log')).write_bytes(result.stdout)
    if mode=='old':assert result.returncode==0xc0000005,hex(result.returncode);print('REPRODUCED original access violation 0xc0000005')
    else:print(result.stdout.decode(errors='replace'));result.check_returncode()
