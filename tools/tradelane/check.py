"""Validate generated models and execute the production one-shot lifecycle with a fake engine."""
import os
from pathlib import Path
import re
import struct
import subprocess
import math
from prepare import ROOT, GAME, NAMES, JOINTS, patch_model, patch_solar, patch_loadout, read_tree, child


def leaves(data):
    result = {}
    def walk(node, path=''):
        path += '/' + node.name
        if node.blob is not None:
            result[path] = node.blob
        for c in node.children:
            walk(c, path)
    for n in read_tree(data)[1]: walk(n)
    return result


for model in ['tlr_root.3db', 'tlr_legal_lod5.cmp']:
    original = (GAME/'DATA/SOLAR/DOCKABLE'/model).read_bytes()
    modified = patch_model(original)
    old, new = leaves(original), leaves(modified)
    assert all(new[k] == v for k, v in old.items() if not any(n in k for n in NAMES))
    assert leaves(patch_model(modified)) == new
    for name, joint in zip(NAMES, JOINTS):
        base = '/\\/Animation/Script/' + name + '/Joint map 0/'
        assert new[base+'Child name'].rstrip(b'\0').decode() == joint
        count, dt, flags = struct.unpack('<IfI', new[base+'Channel/Header'])
        assert count == 181 and flags == 1 and abs(dt*180 - 6) < 1e-5
        values = struct.unpack('<181f', new[base+'Channel/Frames'])
        assert values[0] == values[-1] == 0
        # Same shortest-arc interpolation as EngBase's revolute channel.
        deltas = [math.remainder(b-a, math.tau) for a,b in zip(values, values[1:])]
        assert all(0 < d < .05 for d in deltas)
        assert abs(sum(deltas) - math.tau) < 1e-5
        assert deltas[0] < 0.0001 and deltas[-1] < 0.0001
        assert max(abs(a-b) for a,b in zip(deltas,deltas[1:])) < .002
        assert max(deltas[45:135])-min(deltas[45:135]) < 1e-6

solar = (GAME/'DATA/SOLAR/solararch.ini').read_bytes()
loadout = (GAME/'DATA/SOLAR/loadouts.ini').read_bytes()
assert patch_solar(patch_solar(solar)) == patch_solar(solar)
assert patch_loadout(patch_loadout(loadout)) == patch_loadout(loadout)
assert len(patch_loadout(loadout)) < len(loadout) or b'equip = legal_tradelane_animation' not in loadout
print('PASS: geometry/LODs/hardpoints/old scripts unchanged; correct side joints; 181 frames, smooth one-turn motion; idempotent INI edits')

stub = r'''
#include <array>
#include <cmath>
#include <map>
#include <set>
#include <string>
#include <cassert>
#include <cstdio>
#include <cstdint>
template<class T> void* AsOpaqueDword(T x){return reinterpret_cast<void*>(static_cast<intptr_t>(x));}
#define FDUMP(...) ((void)0)
struct INI_Reader{std::string key,value;bool is_value(char const* s){return key==s;}char const* get_value_string(){return value.c_str();}};
struct Arch{void* Companion=nullptr;int get_script_index(){return 7;}};
struct CObject{Arch* Archetype;int EngineInstanceId=123;};
struct FClientGameobj{CObject* obj;CObject* GetObject(){return obj;}};
namespace AnimDB{std::set<int> active;void Add(int h){assert(active.insert(h).second);}void Rem(int h){active.erase(h);}}
struct Engine{
 struct Record{float t=0;bool started=false;};
 std::map<int,Record> records; int count=0, destroyed=0;bool fail=false;std::string last;
 float GetNamedDuration(void*,char const* n){return std::string(n)=="missing" ? -1 : 6;}
 unsigned long PlayScript(void*,void*,char const* n,void*,void*){last=n;if(fail)return ~0ul;records[++count]={};return count;}
 unsigned long EvalPlayback(int h,int flags,float t,float speed,void*,void*,void*,void*){assert(flags==0&&t==0&&speed==1);records.at(h).started=true;return 0;}
 float GetStoredDuration(int h){return records.at(h).t;}
 unsigned long FilterObjects(void* p){return records.at(int(reinterpret_cast<intptr_t>(p))).t>=6 ? 1 : 0;}
 void StopPlayback(int h){assert(records.count(h));}
 void DestroyScript(void* p){int h=int(reinterpret_cast<intptr_t>(p));assert(!AnimDB::active.count(h));assert(records.erase(h)==1);++destroyed;}
} engine;
namespace DALib{Engine* Anim=&engine;}
'''
source = (ROOT/'src/freelancer/Client/tradelane_ring_anim.cpp').read_text()
source = re.sub(r'^#include[^\n]*\n', '', source, flags=re.M)
code = stub + source + r'''
int main(){
 int companion, inherited; Arch a{&companion};CObject o{&a};FClientGameobj solar{&o};
 TradeLaneRingAnimStart(&solar,0);assert(engine.count==0); // opt-in
 INI_Reader left{"left_ring_anim","left"},right{"right_ring_anim","right"},other{"other",""};
 assert(TradeLaneRingAnimRead(&companion,left));assert(TradeLaneRingAnimRead(&companion,right));
 assert(!TradeLaneRingAnimRead(&companion,other));
 TradeLaneRingAnimCopy(&inherited,&companion);TradeLaneRingAnimForgetConfig(&companion);
 a.Companion=&inherited;assert(TradeLaneRingAnimConfigured(&solar,0)&&TradeLaneRingAnimConfigured(&solar,1));
 TradeLaneRingAnimStart(&solar,0);assert(engine.count==1&&engine.last=="left");
 for(int i=0;i<100;++i){engine.records.at(1).t=5.99f;TradeLaneRingAnimTick();TradeLaneRingAnimStart(&solar,i%2);}
 assert(engine.count==1&&engine.destroyed==0); // no retrigger from either side, no queued request
 engine.records.at(1).t=6;TradeLaneRingAnimTick();assert(engine.records.empty());
 TradeLaneRingAnimTick();assert(engine.count==1); // completion never auto-restarts
 TradeLaneRingAnimStart(&solar,1);assert(engine.count==2&&engine.last=="right");
 engine.records.at(2).t=10;TradeLaneRingAnimStart(&solar,0);assert(engine.count==3&&engine.destroyed==2);
 TradeLaneRingAnimForget(&solar);assert(engine.records.empty()&&AnimDB::active.empty());
 TradeLaneRingAnimForget(&solar); // destruction is idempotent; address reuse is safe
 TradeLaneRingAnimStart(&solar,0);TradeLaneRingAnimShutdown();assert(engine.records.empty());
 engine.fail=true;TradeLaneRingAnimStart(&solar,1);assert(Playing.empty()&&AnimDB::active.empty());engine.fail=false;
 left.value="missing";TradeLaneRingAnimRead(&inherited,left);TradeLaneRingAnimStart(&solar,0);assert(Playing.empty());
 TradeLaneRingAnimForgetConfig(&inherited);assert(!TradeLaneRingAnimConfigured(&solar,0));
 puts("PASS: production lifecycle: optional config, inheritance, both sides, repeated activation, completion, no queue, failure, destruction and system unload");
}
'''
out = ROOT/'src/obj/tradelane_anim_check'
out.mkdir(parents=True, exist_ok=True)
(out/'check.cpp').write_text(code)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(str(p) for p in [vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB']=';'.join(str(p) for p in [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],check=True)
