"""Exercise production NPC matching with online-player/faction fixtures; optionally verify the DLL."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/train_courier'))
from check_transfer_docking import block
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', action='store_true')
    args = parser.parse_args()
    policy = ROOT / 'src/Content/ServerNpcScaling.h'
    params = ROOT / 'src/Content/EncounterParams.cpp'
    loader = ROOT / 'src/Content/Encounters.cpp'
    loot = ROOT / 'src/Content/LootProps.cpp'
    cargo = ROOT / 'src/Content/Cargo.cpp'
    source = params.read_text(encoding='utf-8')
    # Exercise the exact selector called by Spawn, not a parallel test algorithm.
    spawn = block(source, 'int FEncounterParameters::Spawn(')
    assert 'MatchedLevel = ServerNpcScaling::EncounterLevel(Difficulty);' in spawn
    assert 'PickEncounterShipArch(Formation->Faction, *Ship, Difficulty, MatchedLevel)' in spawn
    code = r'''
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <memory>
#include <list>
#include <string>
#include <vector>
bool sp=false, campaign=false, plugin=true;
#define PORT_PLUGIN_ON(name) plugin
namespace CampaignServer {bool Enabled(){return campaign;}}
struct State {};
std::map<unsigned,std::unique_ptr<State>> players;
std::map<unsigned,int> ranks;
auto& GetContentPlayerStates(){return players;}
namespace pub {
bool SinglePlayer(){return sp;}
namespace Player {
int GetRank(unsigned id,int& out){auto it=ranks.find(id);if(it==ranks.end())return -2;out=it->second;return 0;}
int GetRep(unsigned id,int& out){out=id;return 0;}
}
namespace Reputation {void GetRank(int,float& out){out=4;}}
}
unsigned CreateID(char const* name){unsigned hash=2166136261u;while(*name)hash=(hash^*name++)*16777619u;return hash;}
struct FId {unsigned Id=0;};
struct FNpcShipArch {unsigned ShipArchetype=0;std::vector<unsigned> NpcClasses;int Level=0;int GetLevel()const{return Level;}};
struct FEncounterShip {std::vector<unsigned> ShipClasses;FId NpcArch;int DifficultyOffset=0;};
struct FFactionProps {std::vector<unsigned> NpcShips;};
std::map<unsigned,FNpcShipArch> GNpcShipArchs;
std::map<unsigned,FFactionProps> factions;
std::map<unsigned,std::vector<unsigned>> classes,GRmShipMissionProperties;
auto* FindNpcShipArch(unsigned const* id,decltype(GNpcShipArchs)* db){auto it=db->find(*id);return it==db->end()?nullptr:&it->second;}
auto* FindShipClass(unsigned const* id){auto it=classes.find(*id);return it==classes.end()?nullptr:&it->second;}
auto* GetFactionProps(unsigned const* id){auto it=factions.find(*id);return it==factions.end()?nullptr:&it->second;}
bool ContainsId(std::vector<unsigned> const& v,unsigned id){return std::find(v.begin(),v.end(),id)!=v.end();}
struct FRankDiff {int Rank;float MinDifficulty,MaxDifficulty;};
std::vector<FRankDiff> const& RankDiffs(){static std::vector<FRankDiff> rows={{0,1,2},{4,4,8},{20,20,40},{38,38,76}};return rows;}
'''
    code += block(policy.read_text(encoding='utf-8'), 'namespace ServerNpcScaling')
    code += '\nint LoadedLevel(int Level) {\n'
    code += block(loader.read_text(encoding='utf-8'), 'if (PORT_PLUGIN_ON("MatchPlayer")')
    code += '\nreturn Level;}\n'
    text = cargo.read_text(encoding='utf-8')
    code += block(text, 'bool __cdecl NpcArchFitsShipLine(') + '\n'
    code += block(text, 'FNpcShipArch* __cdecl PickFactionShipLineArch(') + '\n'
    code += block(source, 'FNpcShipArch* PickEncounterShipArch(') + '\n'
    code += block(loot.read_text(encoding='utf-8'), 'void AdoxaMatchJobDifficulty(') + '\n'
    code += r'''
void Join(unsigned id,int rank){players[id]=std::make_unique<State>();ranks[id]=rank;}
void AddArch(unsigned id,int level,char const* type,unsigned faction){
    char name[32];sprintf_s(name,"diff%d",level);unsigned diff=CreateID(name);
    GNpcShipArchs[id]={id,{CreateID(type),diff},level};classes[diff]={diff};factions[faction].NpcShips.push_back(id);
}
int main(){
    assert(ServerNpcScaling::HighestRank()==0 && ServerNpcScaling::EncounterLevel(6)==6);
    int loaded=LoadedLevel(3); // systems may load before any character joins
    Join(2,10);Join(7,38); // no slot 1, no ships/base/system filter
    assert(ServerNpcScaling::HighestRank()==38 && ServerNpcScaling::EncounterLevel(loaded)==19);
    assert(LoadedLevel(3)==3 && ServerNpcScaling::EncounterLevel(21)==21);
    players[9]=nullptr;ranks[9]=100;players[10]=std::make_unique<State>();
    assert(ServerNpcScaling::HighestRank()==38); // invalid/half-loaded states ignored
    ranks[2]=42;assert(ServerNpcScaling::EncounterLevel(loaded)==21);
    players.erase(2);ranks.erase(2);assert(ServerNpcScaling::EncounterLevel(loaded)==19);
    Join(7,8);assert(ServerNpcScaling::EncounterLevel(loaded)==4); // character swap in same slot
    players.erase(7);ranks.erase(7);assert(ServerNpcScaling::EncounterLevel(loaded)==3);
    Join(1,20);Join(7,38);
    float lo=0,hi=0;AdoxaMatchJobDifficulty(1,lo,hi);assert(lo==38&&hi==76);
    lo=90;hi=100;AdoxaMatchJobDifficulty(1,lo,hi);assert(lo==90&&hi==100);
    campaign=true;assert(!ServerNpcScaling::Active()&&LoadedLevel(3)==10&&ServerNpcScaling::EncounterLevel(3)==3);
    lo=0;hi=0;AdoxaMatchJobDifficulty(1,lo,hi);assert(lo==4&&hi==8); // existing campaign MP policy
    campaign=false;sp=true;assert(!ServerNpcScaling::Active()&&LoadedLevel(3)==10);
    lo=0;hi=0;AdoxaMatchJobDifficulty(1,lo,hi);assert(lo==20&&hi==40);
    sp=false;plugin=false;assert(LoadedLevel(3)==3&&ServerNpcScaling::EncounterLevel(3)==3);plugin=true;

    AddArch(1,3,"fighter",10);AddArch(2,10,"fighter",10);AddArch(3,19,"fighter",10);
    AddArch(4,19,"freighter",10);AddArch(5,19,"fighter",20);
    FEncounterShip ship;ship.ShipClasses={CreateID("fighter"),CreateID("diff3")};
    auto original=ship.ShipClasses;
    assert(PickEncounterShipArch(10,ship,3,3)==&GNpcShipArchs[1]);
#ifdef FREELANCER_ADOXA
    assert(PickEncounterShipArch(10,ship,3,19)==&GNpcShipArchs[3]);
    assert(PickEncounterShipArch(10,ship,3,10)==&GNpcShipArchs[2]);
    assert(PickEncounterShipArch(10,ship,3,1000000)==&GNpcShipArchs[3]); // finite fallback above content range
    assert(PickEncounterShipArch(10,ship,3,15)==&GNpcShipArchs[3]); // nearest supported variant
    ship.DifficultyOffset=-2;ship.ShipClasses[1]=CreateID("diff1");
    assert(PickEncounterShipArch(10,ship,3,21)==&GNpcShipArchs[3]);
    ship.DifficultyOffset=0;ship.ShipClasses=original;
#else
    assert(PickEncounterShipArch(10,ship,3,19)==&GNpcShipArchs[1]);
#endif
    assert(ship.ShipClasses==original); // repeated scaling never mutates the zone
    assert(PickEncounterShipArch(10,ship,3,3)==&GNpcShipArchs[1]); // highest player left
    ship.NpcArch.Id=4;assert(PickEncounterShipArch(10,ship,3,19)==&GNpcShipArchs[4]); // explicit NPC untouched
    ship.NpcArch.Id=0;assert(PickEncounterShipArch(999,ship,3,19)==nullptr);
    // A faction without higher variants must still spawn its authored ships.
    factions[30].NpcShips={1};assert(PickEncounterShipArch(30,ship,3,19)==&GNpcShipArchs[1]);
    puts("PASS online maximum, login/logout/slot reuse/rank changes, zone floor, SP/campaign/plugin-off, MatchJob");
    puts("PASS production archetype selection: faction/type, offsets, missing levels, content ceiling, explicit NPCs, unchanged zone");
}
'''
    out = ROOT / 'out/npc_scaling/check'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'check.cpp').write_text(code, encoding='utf-8')
    compiler, env = compiler_env()
    for enabled in (True, False):
        exe = 'check_on.exe' if enabled else 'check_off.exe'
        cmd = [str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17', '/W4', 'check.cpp', '/Fe:'+exe]
        if enabled: cmd.append('/DFREELANCER_ADOXA')
        subprocess.run(cmd, cwd=out, env=env, check=True)
        subprocess.run([str(out / exe)], cwd=out, env=env, check=True, timeout=10)
    if args.bundle:
        subprocess.run([sys.executable, str(ROOT/'tools/train_courier/check_local_triggers.py')], check=True)
        checks = json.loads((ROOT/'out/local_triggers/check/verified.json').read_text(encoding='utf-8'))
        inputs = [Path(__file__), policy, params, loader, loot, cargo, ROOT/'src/include/campaign_server.h',
                  ROOT/'tools/npc_scaling/install.py', ROOT/'tools/train_courier/install_local_triggers.py']
        checks.update({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
        (out/'verified.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
        print('PASS checked Content.dll bundle and campaign regression')


if __name__ == '__main__': main()
