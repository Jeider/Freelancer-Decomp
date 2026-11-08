"""Exercise production save/read, clock and loss observation with real snapshots.

Only game I/O, INI tokenization and objective notifications are stubbed. No
alternative implementation of the courier state machine is used here.
"""
from pathlib import Path
import subprocess
import sys
from check_orders import function
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

PREFIX=r'''
#include "train_courier_state.h"
#include "train_courier_hud.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <fstream>
#include <sstream>
#include <limits>
struct Vector {float x=0,y=0,z=0;};
struct Matrix {float E[3][3]={{1,0,0},{0,1,0},{0,0,1}};};
'''
MOCKS=r'''
using namespace TrainCourier;
#define FDUMP(...) ((void)0)
enum class MissionMessageType {Warning=2};
struct FmtStr {void begin_mad_lib(unsigned){} void append_int(unsigned){} void end_mad_lib(){}};
unsigned warnings=0;
namespace pub {namespace Player {void DisplayMissionMessage(unsigned,FmtStr const&,MissionMessageType,bool){++warnings;}}}
struct INI_Reader {
    struct Section {std::string name;std::vector<std::pair<std::string,std::vector<std::string>>> values;};
    std::vector<Section> sections;int h=-1,v=-1;
    static std::string trim(std::string s){auto a=s.find_first_not_of(" \r\t");return a==s.npos?"":s.substr(a,s.find_last_not_of(" \r\t")-a+1);}
    explicit INI_Reader(char const* path){
        std::ifstream f(path);std::string line;
        while(std::getline(f,line)){
            line=trim(line);if(line.empty())continue;
            if(line[0]=='['){sections.push_back({line.substr(1,line.size()-2),{}});continue;}
            auto eq=line.find('=');if(eq==line.npos || sections.empty())continue;
            std::vector<std::string> fields;std::stringstream s(line.substr(eq+1));std::string item;
            while(std::getline(s,item,','))fields.push_back(trim(item));
            sections.back().values.push_back({trim(line.substr(0,eq)),fields});
        }
    }
    void reset(){h=v=-1;}
    bool read_header(){v=-1;return ++h<int(sections.size());}
    bool read_value(){return ++v<int(sections[h].values.size());}
    bool is_header(char const* s){return sections[h].name==s;}
    bool is_value(char const* s){return sections[h].values[v].first==s;}
    char const* get_value_string(int i=0){auto const& a=sections[h].values[v].second;return i<int(a.size())?a[i].c_str():"";}
    int get_value_int(int i=0){return int(std::strtoll(get_value_string(i),nullptr,10));}
    bool get_value_bool(int i=0){return get_value_int(i)!=0;}
    double get_value_float(int i=0){return std::strtod(get_value_string(i),nullptr);}
};
struct Point {std::string nickname;unsigned systemId=1;std::map<std::string,int> prices;std::string base;};
struct Config {
    Rules rules;std::vector<Point> points,parkingPoints;
    std::map<std::string,unsigned> commodityPods;
    std::map<std::string,std::vector<unsigned>> descriptions;
    unsigned lossIds=1,timerIds=2,overdueIds=3;float timerX=.275f,timerY=-.16f;
};
struct Mission {
    Config config;State state;Point source,destination;std::string commodity="comm_basic_meds";
    unsigned PlayerId=1,trailer=0,transferBase=0;
    bool returnImmediately=false,repositionedOrder=false,cargoPending=false,ready=true,started=true,swapped=false,failed=false,restoreCargo=false,restoreObjective=false,bPendingDestroy=false;
    float pause=0,remaining=-1,expectedSeconds=0;unsigned proseIds=0,lostPods=0,updates=0;
    struct {bool bActive=true;int State=4;unsigned sends=0;void SendObjectives(bool skip,bool launch){assert(skip && !launch);++sends;}} NnPath;
    int quotedReward=0,lossCharge=0;
    Vector transferPosition;Matrix transferOrientation;
    CargoSnapshot savedCargo;BridgeFn bridge=nullptr;
    bool request(Operation){return true;}
    unsigned system(){return 777;}
    void describeOrder(){++updates;}
    void RenumberObjectives(unsigned){assert(false && "must preserve NNPath goals when updating losses");}
'''
MAIN=r'''
};
Mission fresh(unsigned wagons=2){
    Mission m;m.config.points={{"source",1,{{"comm_basic_meds",32}}},{"destination",2,{}}};
    for(auto& p:m.config.points)p.base=p.nickname+"_base";
    m.config.descriptions[m.commodity]={238500,238501};m.config.commodityPods[m.commodity]=123;
    m.source=m.config.points[0];m.destination=m.config.points[1];
    m.state.recentBases={"old_base","source_base","destination_base"};
    m.state.unlockedWagons=m.state.wagons=wagons;m.state.stage=Stage::Deliver;m.state.pickedUp=true;
    m.state.distance=wagons-1;m.state.source=m.source.nickname;m.state.destination=m.destination.nickname;
    m.quotedReward=freightQuote(m.config.rules,wagons,m.state.distance,32);m.state.reward=m.quotedReward;
    m.lossCharge=podLossCharge(m.config.rules,wagons,m.quotedReward,32);m.proseIds=238501;
    m.remaining=m.expectedSeconds=m.config.rules.orderSeconds+m.config.rules.wagonSeconds*wagons;
    m.savedCargo.arch=99;m.savedCargo.hitpoints=10500;m.savedCargo.system=1;m.savedCargo.coupled=1;
    for(unsigned i=0;i<wagons*2;++i){
        auto& e=m.savedCargo.equipment[m.savedCargo.equipmentCount++];
        e.arch=123;e.count=1;e.health=1;e.mounted=1;std::sprintf(e.hardpoint,"HpCargo%02u",i+1);
    }
    return m;
}
void save(Mission& m){FILE* f=std::fopen("state.ini","wb");assert(f);m.save(f);std::fclose(f);}
Mission blank(){Mission m=fresh();m.savedCargo={};m.remaining=-1;m.expectedSeconds=0;m.state={};m.proseIds=m.lostPods=0;m.quotedReward=m.lossCharge=0;return m;}
int main(){
    for(Stage stage:{Stage::Boarding,Stage::TransferIn}) {
        Mission m=fresh();m.state.stage=stage;m.state.pickedUp=false;m.commodity.clear();
        m.state.destination.clear();m.source.base="ku_ksu_03_base";
        m.config.points[0].base=m.source.base;m.transferBase=4321;
        save(m);INI_Reader input("state.ini");Mission restored=blank();
        restored.config.points[0].base=m.source.base;
        assert(restored.readSave(input) && restored.source.base=="ku_ksu_03_base" && restored.transferBase==4321);
    }
    Rules prices;assert(freightQuote(prices,2,1,32)==4364);
    assert(podLossCharge(prices,2,4364,32)==1171);
    assert(freightQuote(prices,10,9,234)==31840);
    for(unsigned n:{2u,10u,20u}) {
        Mission m=fresh(n);assert(m.remaining==(5+3*n)*60);
        m.observeLoss(m.savedCargo);assert(m.lostPods==0 && m.state.reward==m.quotedReward);
        m.savedCargo.equipment[0].health=.01f;m.observeLoss(m.savedCargo);assert(!m.lostPods);
        m.savedCargo.equipment[0].health=0;m.observeLoss(m.savedCargo);
        assert(m.lostPods==1 && m.state.reward==m.quotedReward-m.lossCharge && warnings);
        unsigned messages=warnings;m.observeLoss(m.savedCargo);assert(warnings==messages);
        m.savedCargo.equipment[0].health=1;m.observeLoss(m.savedCargo);assert(m.lostPods==1); // no repair exploit
        m.state.unlockedWagons=20;m.state.deliveriesAtSize=1;m.advanceClock(123.25f);float left=m.remaining;
        save(m);INI_Reader input("state.ini");Mission restored=blank();
        restored.config.rules.orderSeconds=900; // config edits never restart an existing clock
        assert(restored.readSave(input));
        assert(restored.state.deliveriesAtSize==1 && restored.state.unlockedWagons==20);
        assert(restored.state.recentBases==m.state.recentBases);
        assert(restored.remaining==left && restored.lostPods==1 && restored.state.reward==m.state.reward);
        assert(restored.expectedSeconds==m.expectedSeconds && m.NnPath.sends==1);
        assert(restored.proseIds==m.proseIds && restored.lossCharge==m.lossCharge && restored.quotedReward==m.quotedReward);
        assert(restored.restoreCargo && restored.savedCargo.system==777); // cross-system restoration
        assert(restored.savedCargo.equipmentCount==n*2);
        restored.advanceClock(left+12.5f);assert(restored.remaining==-12.5f && restored.state.stage==Stage::Deliver);
        assert(restored.state.reward==m.state.reward); // overdue never changes payment
        save(restored);INI_Reader overdue("state.ini");Mission again=blank();assert(again.readSave(overdue));
        assert(again.remaining==-12.5f);
        TrainCourierHud hud;assert(again.hud(&hud) && hud.caption==3 && hud.remaining==-12.5f);
        again.state.stage=Stage::Parking;again.advanceClock(100);assert(again.remaining==-12.5f && !again.hud(&hud));
        m.savedCargo.equipmentCount=0;m.observeLoss(m.savedCargo);assert(m.lostPods==n*2 && m.state.reward==0);
        m.advanceClock(std::numeric_limits<float>::quiet_NaN());assert(std::isfinite(m.remaining));
    }
    Mission pending=fresh();pending.state.stage=Stage::Pickup;pending.state.pickedUp=false;pending.cargoPending=true;
    pending.state.deliveriesAtSize=1;save(pending);INI_Reader waiting("state.ini");Mission loaded=blank();
    assert(loaded.readSave(waiting) && loaded.cargoPending && !loaded.restoreCargo);
    assert(loaded.savedCargo.arch==0 && loaded.state.deliveriesAtSize==1 && loaded.remaining==pending.remaining);
    Mission uncollected=fresh();uncollected.state.stage=Stage::Pickup;uncollected.state.pickedUp=false;
    float full=uncollected.remaining;uncollected.advanceClock(999);assert(uncollected.remaining==full);
    uncollected.state.pickedUp=true;uncollected.state.stage=Stage::Deliver;uncollected.advanceClock(15);
    uncollected.state.stage=Stage::Pickup;uncollected.advanceClock(15);assert(uncollected.remaining==full-30);
    Mission offer=fresh();offer.state.stage=Stage::Offer;offer.state.pickedUp=false;offer.state.popup=true;
    offer.state.unlockedWagons=20;offer.advanceClock(999);assert(offer.remaining==offer.expectedSeconds);
    save(offer);INI_Reader offered("state.ini");Mission offeredAgain=blank();assert(offeredAgain.readSave(offered));
    assert(offeredAgain.state.stage==Stage::Offer && !offeredAgain.state.popup && !offeredAgain.restoreCargo && offeredAgain.state.unlockedWagons==20);
    // Existing v1 saves keep their agreed reward and receive a timer once.
    Mission old=fresh();old.remaining=-40;save(old);
    INI_Reader legacy("state.ini");
    for(auto& section:legacy.sections)if(section.name=="TrainCourierSave") {
        auto& values=section.values;
        values.erase(std::remove_if(values.begin(),values.end(),[](auto const& v){return v.first=="recent_base" || v.first=="unlocked_wagons" || v.first=="order_remaining" || v.first=="order_expected" || v.first=="prose_ids" || v.first=="quoted_reward" || v.first=="loss_charge" || v.first=="lost_pods";}),values.end());
        for(auto& value:values)if(value.first=="version")value.second={"1"};
    }
    Mission upgraded=blank();
    assert(upgraded.readSave(legacy) && upgraded.state.unlockedWagons==old.state.wagons && upgraded.remaining==660 && upgraded.quotedReward==old.state.reward);
    assert((upgraded.state.recentBases==std::vector<std::string>{"source_base","destination_base"}));
    puts("PASS: native save/read round trips at 2/10/20 wagons; system transfer; persistent overdue clock; v1 upgrade; partial and total cargo loss; no repeat penalties; HUD lifecycle");
}
'''

def main():
    source=(ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    methods='\n'.join(function(source,signature) for signature in
        ('bool activeOrder(', 'void advanceClock(', 'void refreshBrief(', 'void observeLoss(', 'bool readSave(', 'void save(', 'bool hud('))
    bridge=(ROOT/'src/include/train_courier_bridge.h').read_text().replace('#pragma once','').replace('#include "common_csys.h"','')
    out=ROOT/'src/obj/train_courier/order_state';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'state.cpp';cpp.write_text(PREFIX+bridge+MOCKS+methods+MAIN,encoding='utf-8')
    compiler,env=compiler_env();exe=out/'state.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2','/D_CRT_SECURE_NO_WARNINGS',
                    '/I'+str(ROOT/'src/include'),str(cpp),'/Fo'+str(out/'state.obj'),'/Fe'+str(exe)],env=env,cwd=out,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)

if __name__=='__main__':main()
