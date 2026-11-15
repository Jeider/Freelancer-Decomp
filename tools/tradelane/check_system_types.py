"""Run the production Object parser and lane builder without live space objects."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'src/obj/tradelane_system_types'
sys.path.insert(0, str(ROOT/'tools/cursors'))
from check import compiler_env, VC


def braced(source, marker):
    start = source.index('{', source.index(marker))
    depth = 1
    end = start + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def main():
    source_path = ROOT/'src/Content/SystemInfo.cpp'
    source = source_path.read_text(encoding='utf-8')
    obj = braced(source, 'else if (Reader->is_header("Object"))')
    build = braced(source, 'int FSystemInfo::BuildTradeLanes(')
    # Only the engine/INI boundary is faked; classification, field parsing and
    # prev/next traversal below are extracted verbatim from production.
    stub = r'''
#include <cassert>
#include <cmath>
#include <cstring>
#include <cstdio>
#include <map>
#include <string>
#include <vector>
#include <utility>
#include <cctype>
struct Vector {float x=0,y=0,z=0;};
struct FMatrix {float D[3][3] = {};};
struct FTransform {FMatrix Rotation;struct {float X=0,Y=0,Z=0;} Translation;};
void SetMatrixIdentity(FMatrix* m){*m={};for(int i=0;i<3;++i)m->D[i][i]=1;}
// Case-insensitive IDs stand in for the engine hash; no object registry exists.
unsigned CreateID(char const* text){
 if(!text || !*text)return 0;
 unsigned h=2166136261u;while(*text)h=(h^std::tolower((unsigned char)*text++))*16777619u;
 return (h&0x3fffffffu)|1u;
}
namespace Archetype {
 struct Solar {unsigned ObjectType;};std::map<unsigned,Solar> Registry;
 Solar const* GetSolar(unsigned id){auto it=Registry.find(id);return it==Registry.end()?nullptr:&it->second;}
}
namespace pub {
 unsigned GetNicknameId(char const* s){return CreateID(s);}
 void GetSystemID(unsigned& id,char const* s){id=CreateID(s);}
 namespace Reputation {void GetReputationGroup(unsigned& id,char const* s){id=CreateID(s);}}
}
using Section=std::vector<std::pair<std::string,std::vector<std::string>>>;
struct INI_Reader {
 Section rows;size_t index=0;
 bool read_value(){return index++<rows.size();}
 bool is_value(char const* s){return rows.at(index-1).first==s;}
 char const* get_value_string(int n=0){auto const& v=rows.at(index-1).second;return n<int(v.size())?v[n].c_str():nullptr;}
 float get_value_float(int n=0){return std::stof(get_value_string(n));}
};
struct FTradeLaneRingInfo {unsigned ObjectId=0;Vector Position;FTransform Placement;unsigned PrevRing=0,NextRing=0,Reputation=0;};
struct FTradeLaneRing {unsigned ObjectId;Vector Position;FTransform Placement;unsigned Reputation;};
FTradeLaneRing MakeTradeLaneRing(FTradeLaneRingInfo const& r){return {r.ObjectId,r.Position,r.Placement,r.Reputation};}
struct FSystemJump {unsigned ObjectId=0;int Type=0;Vector Position;unsigned GotoSystem=0,GotoObject=0;};
struct FTradeLane {std::vector<FTradeLaneRing> Rings;Vector StartPosition,EndPosition;FTransform Placement;};
struct FSystemInfo {
 std::vector<FTradeLane> TradeLanes;std::vector<FSystemJump> Jumps;
 int BuildTradeLanes(std::map<unsigned,FTradeLaneRingInfo>* Rings);
 std::map<unsigned,FTradeLaneRingInfo> Parse(std::vector<Section> const& objects);
};
'''
    parser = '''
std::map<unsigned,FTradeLaneRingInfo> FSystemInfo::Parse(std::vector<Section> const& objects){
 std::map<unsigned,FTradeLaneRingInfo> Rings;
 for(auto const& section:objects){INI_Reader input{section};INI_Reader* Reader=&input;
''' + obj + '\n}\nreturn Rings;\n}\n'
    tests = r'''
Section Ring(char const* name,char const* arch,char const* prev,char const* next,char const* x){
 return {{"nickname",{name}},{"archetype",{arch}},{"pos",{x,"2","3"}},
 {"rotate",{"0","90","0"}},{"prev_ring",{prev}},{"next_ring",{next}},{"reputation",{"fc_test"}}};
}
int main(){
 using Archetype::Registry;
 Registry[CreateID("Trade_Lane_Ring")]={0x80};
 Registry[CreateID("custom_ring")]={0x80};
 Registry[CreateID("TLR_CORSAIR")]={0x80};
 Registry[CreateID("custom_ring_flags")]={0x80|0x100};
 Registry[CreateID("station")]={0x100};
 FSystemInfo system;
 auto a=Ring("a","TRADE_LANE_RING","","b","10");
 auto b=Ring("b","custom_ring","a","c","20");
 auto c=Ring("c","TLR_CORSAIR","b","","30");
 // Archetype can be before or after the links and transform.
 auto late=b.front();b.erase(b.begin());b.push_back(late);
 late=b.front();b.erase(b.begin());b.push_back(late);
 auto rings=system.Parse({c,a,b});assert(rings.size()==3);
 assert(rings.at(CreateID("b")).PrevRing==CreateID("a"));
 assert(rings.at(CreateID("b")).NextRing==CreateID("c"));
 assert(rings.at(CreateID("c")).Reputation==CreateID("fc_test"));
 assert(std::fabs(rings.at(CreateID("a")).Placement.Rotation.D[0][2]-1)<.0001f);
 assert(system.BuildTradeLanes(&rings)==1 && rings.empty());
 auto const& lane=system.TradeLanes.front();assert(lane.Rings.size()==3);
 assert(lane.Rings[0].ObjectId==CreateID("a") && lane.Rings[1].ObjectId==CreateID("b") && lane.Rings[2].ObjectId==CreateID("c"));
 assert(lane.StartPosition.x==10 && lane.EndPosition.x==30);
 // Unknown/empty archetypes and a station are not rings; scanning continues
 // with later sections after the production parser's early break.
 auto empty=Ring("bad_empty","","","","0");
 auto missing=empty;missing[1].second.clear();
 rings=system.Parse({Ring("bad","station","","","0"),
 Ring("unknown","unknown_ring","","","0"),empty,missing,
 Ring("good","custom_ring_flags","","","50")});
 assert(rings.size()==1 && rings.count(CreateID("good")));
 // Literal name alone is no longer sufficient.
 Registry[CreateID("Trade_Lane_Ring")].ObjectType=0x100;
 assert(system.Parse({a}).empty());
 // Existing jump classification is unchanged by the lane-only fix.
 system.Parse({{{"nickname",{"gate"}},{"archetype",{"jumpgate"}},{"goto",{"sys2","gate2"}}},
               {{"nickname",{"hole"}},{"archetype",{"jumphole"}},{"goto",{"sys3","hole3"}}}});
 assert(system.Jumps.size()==2 && system.Jumps[0].Type==1 && system.Jumps[1].Type==2);
 assert(system.Jumps[0].GotoSystem==CreateID("sys2"));
 puts("PASS: production parser + lane builder: custom/retail/mixed types, unloaded systems, links, transforms, invalid definitions and jumps");
}
'''
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'check.cpp').write_text(stub+parser+'\nint FSystemInfo::BuildTradeLanes(std::map<unsigned,FTradeLaneRingInfo>* Rings)'+build+tests, encoding='utf-8')
    subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'), '/nologo','/std:c++17','/EHsc','/MT',
                    'check.cpp','/Fecheck.exe'], cwd=OUT, env=compiler_env(), check=True)
    subprocess.run([str(OUT/'check.exe')], check=True)
    paths=[source_path, ROOT/'src/Content/SystemInfo.h',Path(__file__)]
    (OUT/'verified.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))


if __name__=='__main__':main()
