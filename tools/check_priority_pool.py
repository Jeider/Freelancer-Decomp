"""Compile the actual pool implementation in isolation and stress its 16-bit boundary."""
import os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'out/priority_pool';out.mkdir(parents=True,exist_ok=True)
source=(ROOT/'src/IVP/ivp_physics/ivp_real_object.cpp').read_text()
def method(name):
    start=source.index(('uint16_t ' if name=='Insert' else 'void ')+'IVP_Priority_Pool::'+name+'(')
    body=source.index('{',start);depth=1;i=body+1
    while depth:
        depth+=(source[i]=='{')-(source[i]=='}');i+=1
    return source[start:i]
code=r'''
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <new>
#include <cassert>
#include <vector>
#include <algorithm>
#include <random>
#include <cstdio>
float BitsToFloat(uint32_t x) {float f;memcpy(&f,&x,4);return f;}
struct IVP_Priority_Pool {
 struct Entry {uint16_t ExpressNext,ExpressPrev,Next,Prev;float Key;void* Payload;};
 uint16_t PoolCapacity,PoolFreeHead;Entry* PoolEntries;float PoolKeyThreshold;
 uint16_t PoolSortedHead,PoolLiveIndex,PoolCount,Pad;
 void Init(uint16_t);void Destroy();uint16_t Insert(void*,float);void Remove(uint16_t);
};
'''
code+='\n'.join(method(n) for n in ('Init','Destroy','Insert','Remove'))
code+=r'''
void verify(IVP_Priority_Pool& p) {
 assert(p.PoolCount<=p.PoolCapacity && p.PoolCapacity<=0xfffe);
 std::vector<bool> seen(p.PoolCapacity,false);unsigned n=0,prev=0xffff;
 float key=-1e30f;
 for(unsigned i=p.PoolLiveIndex;i!=0xffff;i=p.PoolEntries[i].Next){
  assert(i<p.PoolCapacity && !seen[i]);seen[i]=true;++n;
  auto& e=p.PoolEntries[i];assert(e.Prev==prev && e.Key>=key);prev=i;key=e.Key;
 }
 assert(n==p.PoolCount);unsigned free=0;
 for(unsigned i=p.PoolFreeHead;i!=0xffff;i=p.PoolEntries[i].Next){assert(i<p.PoolCapacity && !seen[i]);seen[i]=true;++free;}
 assert(n+free==p.PoolCapacity);
 std::fill(seen.begin(),seen.end(),false);prev=0xffff;key=-1e30f;
 for(unsigned i=p.PoolSortedHead;i!=0xffff;i=p.PoolEntries[i].ExpressNext){
  assert(i<p.PoolCapacity && !seen[i]);seen[i]=true;
  auto& e=p.PoolEntries[i];assert(e.ExpressPrev==prev && e.Key>=key);prev=i;key=e.Key;
 }
}
int main(){
 for(unsigned initial : {8u,16u}){
  IVP_Priority_Pool p{};p.Init(initial);std::vector<uint16_t> slots;std::mt19937 rng(42);
  for(unsigned i=0;i<65534;++i){slots.push_back(p.Insert(reinterpret_cast<void*>(i+1),float(rng()%100000)));if(i%2048==0)verify(p);}
  verify(p);assert(p.PoolCount==65534);
  bool rejected=false;try{p.Insert(nullptr,0);}catch(std::bad_alloc const&){rejected=true;}assert(rejected);verify(p);
  std::shuffle(slots.begin(),slots.end(),rng);
  for(unsigned i=0;i<slots.size()/2;++i)p.Remove(slots[i]);verify(p);
  for(unsigned i=0;i<slots.size()/2;++i)slots[i]=p.Insert(reinterpret_cast<void*>(i+1),float(rng()%100000));verify(p);
  for(auto slot:slots)p.Remove(slot);verify(p);assert(p.PoolCount==0);p.Destroy();
 }
 puts("PASS: 65,534 entries, sorted/express/free chains, boundary rejection, remove/reinsert/drain (capacities 8 and 16)");
}
'''
(out/'check.cpp').write_text(code)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');ver='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/ver/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/ver/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MD','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,timeout=45,check=True)
