"""Run production order/YES-NO/NNPath setup against the exported trade graph.

World spawning, reputation and path traversal are mocked; selection and order
transitions are extracted from TrainCourier.cpp, not reimplemented in this test.
"""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def function(text,name):
    start=text.index(name);end=text.index('{',start)+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]

PREFIX=r'''
#include "train_courier_state.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <set>
using namespace TrainCourier;
#define FDUMP(...) ((void)0)
unsigned CreateID(char const*){return 1;}
struct Vector {float x=0,y=0,z=0;};
struct Matrix {float E[3][3]={{1,0,0},{0,1,0},{0,0,1}};};
float distance(Vector a,Vector b){return std::sqrt((a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z));}
struct Point {
    std::string nickname,base;std::vector<std::string> commodities;
    unsigned systemId=1;Vector position;Matrix orientation;unsigned name=123;
    std::vector<std::string> demand;std::map<std::string,int> prices;bool freightHub=false,largePlanet=false,refinery=false;
};
struct Config {
    Rules rules;std::vector<Point> points;std::vector<Route> routes;
    std::map<std::string,std::string> commodityVoices;unsigned title=40,missionTitle=42,cargoName=43,pickup=3,pickupFrom=3,deliver=4,park=5,voice=1;
    std::map<std::string,std::vector<unsigned>> descriptions;
};
unsigned mockSystem=1;Vector mockPosition;bool mockReady=true;unsigned marks=0;
struct FmtStr {unsigned value=0;void begin_mad_lib(unsigned v){value=v;}void end_mad_lib(){}};
unsigned popups=0;FmtStr const* popupBody=nullptr;
namespace pub {
namespace SpaceObj {
int GetSystem(unsigned,unsigned& id){id=mockSystem;return mockReady?0:-1;}
int GetLocation(unsigned,Vector& pos,Matrix&){pos=mockPosition;return mockReady?0:-1;}
int GetRep(unsigned,int& rep){rep=10;return mockReady?0:-1;}
}
namespace Player {int PopUpDialog(unsigned,FmtStr const& title,FmtStr const& body,unsigned buttons){assert(title.value==42 && buttons==3);++popups;popupBody=&body;return 0;} void MarkObj(unsigned,unsigned,unsigned){++marks;}}
}
struct MissionPlayer {void ClearObjectives(){}};
struct CourierMission;
struct ActNnPath {
    CourierMission* Mission;Vector Position;unsigned SystemId=0;int TravelIds=0,TargetIds=0;std::string Label;
    explicit ActNnPath(CourierMission* m):Mission(m){} bool Execute();
};
struct CourierMission {
    Config config;State state;Point source,destination;std::string commodity;
    bool returnImmediately=false,repositionedOrder=false,cargoPending=false,continueSpoken=false;float pause=0;unsigned PlayerId=1,trailer=0,spawned=0,pathStarts=0;
    std::string spoken;MissionPlayer player;
    unsigned objectiveObject=0,objectiveName=0,pendingObject=0,pendingIds=0;
    bool arrivalSpoken=false;
    unsigned proseIds=0,lostPods=0;int quotedReward=0,lossCharge=0;float remaining=0,expectedSeconds=0;
    FmtStr Field_0x68;void describeOrder(){Field_0x68.value=state.reward;}
    std::vector<std::string> goodsFor(Point const&) const;
    std::set<std::string> hostile;
    Point pendingPoint;std::string pendingLabel;float markerDelay=0,uncoupledTime=0;
    struct {bool bActive=false;unsigned SystemId=0;int TargetIds=0;Vector Position;void Reset(){bActive=false;}} NnPath;
    MissionPlayer* GetOrCreatePlayer(unsigned){return &player;}
    bool friendly(Point const& p){return hostile.count(p.base)==0;}
    bool spawnCargo(){assert(system()==source.systemId);cargoPending=false;trailer=++spawned;mockPosition=source.position;return true;}
    unsigned system(){return mockSystem;}
    void say(char const* family,Point const*){spoken=family;}
    unsigned ship(){return 123;}
    void parking(){state.stage=Stage::Parking;cargoPending=false;}
    void objective(unsigned,Point const&,unsigned,char const*);
    void objectObjective(unsigned,Point const&,unsigned,char const*);
    void updateObjectObjective(float);bool choose();bool createPendingCargo();bool next();void advanceOrder();void showOffer();void onContinue(unsigned);
};
bool ActNnPath::Execute(){
    assert(TravelIds==TargetIds && SystemId);
    ++Mission->pathStarts;Mission->NnPath={true,SystemId,TargetIds,Position};return true;
}
Config catalog(){Config c;
'''

MAIN=r'''
void accept(CourierMission& m){
    assert(m.state.stage==Stage::Offer);unsigned before=m.spawned;
    m.showOffer();assert(m.state.popup && popupBody==&m.Field_0x68 && popupBody->value==unsigned(m.state.reward));
    unsigned shown=popups;m.showOffer();assert(popups==shown);
    m.onContinue(1);assert(m.state.stage==Stage::Pickup);
    m.onContinue(1);assert(m.spawned<=before+1);
}
void handover(CourierMission& m){
    m.state.stage=Stage::AwaitContinue;m.state.pickedUp=m.state.retired=m.state.paid=true;
    m.state.deliveriesAtSize=std::min(2u,m.state.deliveriesAtSize+1);
    m.trailer=0;m.source=m.destination;mockSystem=m.source.systemId;m.advanceOrder();
}
void validate(CourierMission const& m){
    assert(m.state.valid(m.config.rules) && m.state.wagons<=m.state.unlockedWagons);
    auto r=std::find_if(m.config.routes.begin(),m.config.routes.end(),[&](auto const& r){return r.source==m.source.base && r.destination==m.destination.base;});
    assert(r!=m.config.routes.end());
    assert(r->distance>=minimumRouteDistance(m.config.rules,m.state.wagons));
    assert(r->jumps>=minimumRouteJumps(m.config.rules,m.state.wagons));
    assert(m.source.freightHub || m.state.wagons<20);
    assert(m.state.wagons<=orderWagonLimit(m.state,m.config.rules));
    if(!m.source.freightHub)assert(m.state.wagons==feederWagons(m.config.rules,orderWagonLimit(m.state,m.config.rules),r->distance,r->jumps));
    assert(std::find(m.destination.demand.begin(),m.destination.demand.end(),m.commodity)!=m.destination.demand.end());
    assert(m.expectedSeconds==(5+3*m.state.wagons)*60);
}
int main(){
    Config tiny;
    tiny.points={{"origin","origin",{"goods"}},{"near","near",{"goods"}},
                 {"far","far",{"goods"}},{"target","target",{}},{"foreign","foreign",{"goods"}}};
    tiny.points[3].demand={"goods"};tiny.points[3].largePlanet=tiny.points[3].freightHub=true;tiny.points[4].systemId=2;
    for(auto& p:tiny.points)p.prices["goods"]=100;
    tiny.commodityVoices["goods"]="voice";tiny.descriptions["goods"]={1};
    tiny.routes={{"origin","near",1},{"origin","far",2},{"origin","foreign",1},
                 {"origin","target",2},{"near","target",2},{"far","target",2},{"foreign","target",9}};
    mockSystem=1;
    CourierMission small;small.config=tiny;small.source=tiny.points[0];small.state.unlockedWagons=10;small.state.deliveriesAtSize=1;
    assert(small.next() && small.state.wagons==3 && small.state.unlockedWagons==10 && small.state.deliveriesAtSize==1);
    assert(small.spawned==0);validate(small);accept(small);assert(small.spawned==1);
    CourierMission grow;grow.config=tiny;grow.source=tiny.points[0];assert(grow.next());accept(grow);
    for(unsigned i=0;i<2;++i){grow.destination=tiny.points[0];handover(grow);assert(grow.state.unlockedWagons==(i?3:2));accept(grow);}
    assert(grow.state.deliveriesAtSize==0 && grow.state.wagons==3);
    CourierMission reject;reject.config=tiny;reject.source=tiny.points[0];assert(reject.next());reject.showOffer();
    reject.onContinue(0);assert(!reject.state.popup && reject.state.stage==Stage::Offer && reject.pause==1);
    reject.showOffer();reject.onContinue(2);assert(reject.state.stage==Stage::Parking && reject.spawned==0);
    tiny.points[0].commodities.clear();
    CourierMission nearby;nearby.config=tiny;nearby.source=tiny.points[0];assert(nearby.next() && nearby.source.base=="near");
    tiny.points[1].commodities.clear();
    CourierMission pooled;pooled.config=tiny;pooled.source=tiny.points[0];assert(pooled.next() && pooled.source.base=="origin");accept(pooled);
    pooled.source=tiny.points[0];assert(pooled.choose() && pooled.commodity=="goods");
    CourierMission deferred;deferred.config=tiny;deferred.source=tiny.points[0];mockSystem=2;
    assert(deferred.next());accept(deferred);assert(deferred.cargoPending && deferred.spawned==0 && deferred.pathStarts==1);
    assert(deferred.createPendingCargo() && deferred.spawned==0);
    mockSystem=1;assert(deferred.createPendingCargo() && !deferred.cargoPending && deferred.spawned==1);
    assert(deferred.createPendingCargo() && deferred.spawned==1);
    CourierMission hostile;hostile.config=tiny;hostile.source=tiny.points[0];hostile.hostile.insert("far");assert(!hostile.next());
    tiny.points[2].commodities.clear();CourierMission foreign;foreign.config=tiny;foreign.source=tiny.points[0];assert(!foreign.next());
    puts("PASS: first/subsequent offer description; YES/NO/close/duplicate; no spawn before YES; 2 deliveries unlock +1; feeder preserves capacity/progress; nearest local stock; deferred single spawn");

    Config bulk=tiny;bulk.points[2].commodities={"goods"};bulk.points[2].refinery=bulk.points[2].freightHub=true;
    bulk.points.push_back({"mega","mega",{}});bulk.points.back().freightHub=true;bulk.points.back().demand={"goods"};
    bulk.routes.push_back({"far","mega",19,4});
    CourierMission refinery;refinery.config=bulk;refinery.source=bulk.points[0];refinery.state.unlockedWagons=20;
    assert(refinery.next() && refinery.source.refinery && refinery.destination.base=="mega" && refinery.state.wagons==20);validate(refinery);
    bulk.routes.back().jumps=2;
    CourierMission shorter;shorter.config=bulk;shorter.source=bulk.points[2];shorter.state.unlockedWagons=20;
    assert(shorter.next() && shorter.state.wagons==14 && shorter.state.unlockedWagons==20);validate(shorter);
    puts("PASS: local refinery pickup -> megastation at 20 wagons; 19 edges + 4 jumps required; 2 jumps reduce load to 14 without losing unlocked capacity");

    Config rotation;
    for(auto const& name:{"origin","previous","planet","megabase","neighbor","distant"}) {
        Point p;p.base=p.nickname=name;p.commodities=p.demand={"goods"};p.prices["goods"]=100;
        p.freightHub=p.base!="neighbor";p.largePlanet=p.base=="origin" || p.base=="planet";
        rotation.points.push_back(p);
    }
    rotation.commodityVoices["goods"]="voice";rotation.descriptions["goods"]={1};
    rotation.routes={{"origin","previous",9,2},{"origin","planet",10,2},{"origin","megabase",10,2},
        {"origin","neighbor",1,0},{"neighbor","previous",9,2},{"neighbor","planet",9,2},
        {"neighbor","megabase",10,2},{"origin","distant",19,4}};
    unsigned planets=0,megabases=0;
    for(unsigned seed=0;seed<64;++seed) {
        std::srand(seed);CourierMission m;m.config=rotation;m.source=rotation.points[0];
        m.state.unlockedWagons=20;m.state.order=1;m.state.wagons=3;
        m.state.recentBases={"previous","origin"};assert(m.next());validate(m);
        assert(m.state.wagons==10 && m.state.unlockedWagons==20);
        assert(m.source.base=="origin" && m.destination.base=="previous" && m.state.distance==9);
        // Equal-distance planets and megabases share the same candidate pool.
        m.hostile.insert("previous");assert(m.next());validate(m);
        assert(m.source.base=="origin" && m.state.distance==10);
        planets+=m.destination.base=="planet";megabases+=m.destination.base=="megabase";
    }
    assert(planets && megabases);
    // History is a weight, never a veto. Both base types get the same 4:1
    // preference when they are new, and the longer unseen route stays out.
    for(auto const& recent:{"planet","megabase"}) {
        unsigned fresh=0,repeated=0;
        for(unsigned seed=0;seed<1024;++seed) {
            std::srand(seed);CourierMission m;m.config=rotation;m.source=rotation.points[0];
            m.state.unlockedWagons=10;m.state.wagons=10;
            m.state.recentBases={recent};m.hostile.insert("previous");
            assert(m.choose() && m.state.distance==10);
            assert(m.destination.base=="planet" || m.destination.base=="megabase");
            if(m.destination.base==recent)++repeated;else ++fresh;
        }
        assert(repeated>0 && fresh>3*repeated && fresh<5*repeated);
        std::printf("PASS: recent %s: unseen/repeat %u/%u; both remain eligible, longer unseen route excluded\n",recent,fresh,repeated);
    }
    CourierMission nearbyFallback;nearbyFallback.config=rotation;nearbyFallback.source=rotation.points[0];
    nearbyFallback.source.commodities.clear();nearbyFallback.state.unlockedWagons=10;
    assert(nearbyFallback.next() && nearbyFallback.source.base=="neighbor" && nearbyFallback.state.distance==9);validate(nearbyFallback);
    // A closer megabase beats a farther planet, including an ordinary depot's feeder route.
    CourierMission closerMega;closerMega.config=rotation;closerMega.source=rotation.points[4];
    closerMega.config.routes.push_back({"neighbor","megabase",8,2});closerMega.state.unlockedWagons=10;
    assert(closerMega.next() && closerMega.destination.base=="megabase" && closerMega.state.distance==8);
    // Reduce a local load before relocating to a refinery for a full train.
    CourierMission reducedHere;reducedHere.config=bulk;reducedHere.source=bulk.points[0];
    reducedHere.source.commodities={"goods"};reducedHere.source.freightHub=true;reducedHere.state.unlockedWagons=20;
    assert(reducedHere.next() && reducedHere.source.base=="origin" && reducedHere.state.wagons==3 && reducedHere.state.distance==2);
    CourierMission longRun;longRun.config=rotation;longRun.source=rotation.points[0];longRun.state.unlockedWagons=20;
    longRun.state.order=2;assert(longRun.next() && longRun.state.wagons==20 && longRun.destination.base=="distant");validate(longRun);
    CourierMission onlyReturn;onlyReturn.config=rotation;onlyReturn.source=rotation.points[0];
    onlyReturn.state.unlockedWagons=10;onlyReturn.state.recentBases={"previous","origin"};
    onlyReturn.hostile={"planet","megabase","neighbor","distant"};assert(onlyReturn.next() && onlyReturn.destination.base=="previous");
    for(unsigned n:{2u,3u,10u,11u,20u}) {
        State s;s.unlockedWagons=n;s.wagons=2;s.order=1;
        assert(orderWagonLimit(s,rotation.rules)==std::max(2u,n/2));
        s.order=2;assert(orderWagonLimit(s,rotation.rules)==n);
    }
    std::printf("PASS: nearest suitable route despite history; current depot first, neighbor fallback, local load reduction; equal-distance planet/megabase targets %u/%u; closer megabase feeder; short=half unlocked, long=full\n",planets,megabases);

    Config c=catalog();unsigned tested=0,refineries=0,fullLoads=0;
    for(auto const& first:c.points)for(unsigned start:{2u,10u,20u}) {
        CourierMission m;m.config=c;m.source=first;m.state.unlockedWagons=start;mockSystem=first.systemId;
        if(!m.next())continue;
        validate(m);assert(m.spawned==0);accept(m);assert(m.spawned==1);
        m.updateObjectObjective(.1f);assert(m.pathStarts==0);
        mockReady=false;m.updateObjectObjective(.06f);assert(m.pathStarts==0);
        mockReady=true;m.updateObjectObjective(.01f);assert(m.pathStarts==1);
        if(m.source.refinery)++refineries;if(m.state.wagons==20)++fullLoads;
        for(unsigned step=0;step<3;++step){
            unsigned capacity=m.state.unlockedWagons;handover(m);
            if(m.state.stage==Stage::Parking)break;
            assert(m.state.stage==Stage::Offer && m.state.unlockedWagons>=capacity);
            validate(m);accept(m);
        }
        ++tested;
    }
    assert(tested && refineries && fullLoads);
    printf("PASS: %u real-catalog starts with 2/10/20 capacity plus follow-up offers; %u refinery starts; %u full 20-car loads; planet feeders; true demand; route distance and jump floors\n",tested,refineries,fullLoads);
    CourierMission rep;rep.config=c;
    for(auto const& p:c.points)if(p.base=="rh_biz_01_base"){rep.source=p;break;}
    assert(rep.choose());rep.hostile.insert(rep.destination.base);assert(rep.choose());
    rep.hostile.insert(rep.source.base);assert(!rep.choose());rep.state.pickedUp=true;assert(rep.choose());
    for(auto const& p:c.points)rep.hostile.insert(p.base);assert(!rep.choose());
}
'''


def main(data=None, required_bases=()):
    if data is None:data=json.loads((ROOT/'out/train_courier/catalog.json').read_text(encoding='utf-8'))
    rows=[]
    systems={name:i+1 for i,name in enumerate(sorted({b['system'] for b in data['bases'].values()}))}
    for base in data['bases'].values():
        for p in base['points']:
            xyz=list(p['position']);xyz[1]+=350
            # Yaw is immaterial to route choice; an orthonormal frame suffices
            # for testing the 350 m parallel-track displacement.
            rows.append('c.points.push_back({'+','.join([json.dumps(p['nickname']),json.dumps(p['base']),
                        '{'+','.join(map(json.dumps,p['commodities']))+'}',str(systems[base['system']]),
                        '{'+','.join(str(float(x))+'f' for x in xyz)+'}'])+'});')
            rows.append('c.points.back().freightHub='+str(base['freight_hub']).lower()+';c.points.back().largePlanet='+str(base['large_planet']).lower()+';c.points.back().refinery='+str(base['refinery']).lower()+';')
            rows.append('c.points.back().demand={'+','.join(json.dumps(n) for n,m in base['market'].items() if m['demand'])+'};')
            rows.append('c.points.back().prices={'+','.join('{'+json.dumps(n)+','+str(m['price'])+'}' for n,m in base['market'].items() if m['supply'])+'};')
    for r in data['routes']:
        rows.append('c.routes.push_back({'+json.dumps(r['source'])+','+json.dumps(r['destination'])+','+str(r['distance'])+','+str(r['minimum_jumps'])+'});')
    for name in data['commodities']:
        rows.append('c.commodityVoices['+json.dumps(name)+']="voice";')
        rows.append('c.descriptions['+json.dumps(name)+']={1,2,3};')
    source=(ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    methods=[]
    for result,name in [('void','objective'),('void','objectObjective'),('void','updateObjectObjective'),
                        ('std::vector<std::string>','goodsFor'),('bool','choose'),('bool','createPendingCargo'),('bool','next'),('void','advanceOrder'),('void','showOffer'),('void','onContinue')]:
        methods.append(function(source,result+' '+name+'(').replace(result+' '+name+'(',result+' CourierMission::'+name+'(',1))
    main=MAIN
    if required_bases:
        required=r'''
    for(char const* base:{BASES})for(unsigned capacity:{2u,5u,10u,20u}) {
        CourierMission m;m.config=c;
        auto it=std::find_if(c.points.begin(),c.points.end(),[&](auto const& p){return p.base==base;});
        assert(it!=c.points.end());m.source=*it;mockSystem=it->systemId;m.state.unlockedWagons=capacity;
        assert(m.next());validate(m);
    }
    puts("PASS: every locomotive owner can issue an order at capacities 2/5/10/20");
'''.replace('BASES',','.join(json.dumps(b) for b in required_bases))
        pos=main.rfind('}')
        main=main[:pos]+required+main[pos:]
    text=PREFIX+'\n'.join(rows)+'return c;}\n'+'\n'.join(methods)+main
    out=ROOT/'src/obj/train_courier/orders';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'orders.cpp';cpp.write_text(text,encoding='utf-8')
    compiler,env=compiler_env();exe=out/'orders.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',
                    '/I'+str(ROOT/'src/include'),str(cpp),'/Fo'+str(out/'orders.obj'),'/Fe'+str(exe)],
                   env=env,cwd=out,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)

if __name__=='__main__':main()
