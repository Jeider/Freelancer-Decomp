// Native courier controller. MissionScript supplies the MsnSolar/RTC lifecycle;
// there are no per-order triggers or generated single-mission scripts.
#include "ContentInternal.h"
#include "TrainCourier.h"
#include "train_courier_hud.h"
#ifdef FREELANCER_RPG_WORLD
#include "MissionScript.h"
#include "MissionAct.h"
#include "ContentPlayerState.h"
#include "BaseDB.h"
#include "SystemInfo.h"
#include "Gcs.h"
#include "RpgDialog.h"
#include "DockQueues.h"
#include "common_id.h"
#include "common_ini.h"
#include "common_server.h"
#include "common_universe.h"
#include "common_misc.h"
#include "server_cobject.h"
#include "train_courier_bridge.h"
#include "train_courier_state.h"
#include <windows.h>
#include <cstring>
#include <cstdlib>
#include <map>
#include <string>

namespace {
using namespace TrainCourier;
INI_Reader* restoreReader=nullptr;
class CourierMission;
std::map<unsigned,CourierMission*> controllers;
struct Point {
    std::string nickname,base,system,voice,transfer;
    std::vector<std::string> commodities;
    std::vector<std::string> demand;
    std::map<std::string,int> prices;
    unsigned baseId=0,systemId=0,faction=0,name=0;
    bool freightHub=false,largePlanet=false,refinery=false;
    Vector position{};Matrix orientation{1,0,0, 0,1,0, 0,0,1};
};
Matrix pointOrientation(float yawDegrees) {
    // Same row-major matrix as Pythonlancer story.math.euler_to_matrix(0,y,0).
    // Matrix's default constructor is empty: every element must be assigned.
    float a=yawDegrees*0.0174532925199433f;
    float c=std::cos(a),s=std::sin(a);
    return Matrix(c,0,s, 0,1,0, -s,0,c);
}
struct Config {
    Rules rules;
    std::vector<Point> points,parkingPoints;
    std::vector<Route> routes;
    std::map<std::string,std::string> commodityVoices;
    std::map<std::string,unsigned> commodityNames,commodityPods;
    std::map<std::string,std::vector<unsigned>> descriptions;
    unsigned description=0,timerIds=0,overdueIds=0,lossIds=0;
    float timerX=.275f,timerY=-.16f;
    unsigned title=0,board=0,pickup=0,deliver=0,park=0,question=0,voice=0,launch=0,recover=0;
    unsigned missionTitle=0,cargoName=0;
    bool audio=false,repositionAudio=false;
    unsigned pickupFrom=0;
    float boardingCommDelay=3.f,boardingCommDelayMax=5.f;
    bool load() {
        INI_Reader reader;
        if(!OpenContentDataIni("Missions\\TrainCourier\\courier.ini",&reader))return false;
        while(reader.read_header())while(reader.read_value()) {
            if(reader.is_value("first_wagons"))rules.firstWagons=reader.get_value_int(0);
            else if(reader.is_value("max_wagons"))rules.maxWagons=reader.get_value_int(0);
            else if(reader.is_value("first_distance"))rules.firstDistance=reader.get_value_int(0);
            else if(reader.is_value("distance_step"))rules.distanceStep=reader.get_value_int(0);
            else if(reader.is_value("wagons_per_jump"))rules.wagonsPerJump=reader.get_value_int(0);
            else if(reader.is_value("short_load_percent"))rules.shortLoadPercent=reader.get_value_int(0);
            else if(reader.is_value("base_reward"))rules.baseReward=reader.get_value_int(0);
            else if(reader.is_value("per_wagon_reward"))rules.perWagonReward=reader.get_value_int(0);
            else if(reader.is_value("per_distance_reward"))rules.perDistanceReward=reader.get_value_int(0);
            else if(reader.is_value("per_wagon_distance_reward"))rules.perWagonDistanceReward=reader.get_value_int(0);
            else if(reader.is_value("cargo_value_rate"))rules.cargoValueRate=reader.get_value_float(0);
            else if(reader.is_value("loss_value_rate"))rules.lossValueRate=reader.get_value_float(0);
            else if(reader.is_value("order_seconds"))rules.orderSeconds=float(reader.get_value_float(0));
            else if(reader.is_value("wagon_seconds"))rules.wagonSeconds=float(reader.get_value_float(0));
            else if(reader.is_value("description_ids"))description=reader.get_value_int(0);
            else if(reader.is_value("timer_ids"))timerIds=reader.get_value_int(0);
            else if(reader.is_value("overdue_ids"))overdueIds=reader.get_value_int(0);
            else if(reader.is_value("loss_ids"))lossIds=reader.get_value_int(0);
            else if(reader.is_value("timer_position")){timerX=float(reader.get_value_float(0));timerY=float(reader.get_value_float(1));}
            else if(reader.is_value("delivery_radius"))rules.deliveryRadius=float(reader.get_value_float(0));
            else if(reader.is_value("delivery_speed"))rules.deliverySpeed=float(reader.get_value_float(0));
            else if(reader.is_value("cleanup_distance"))rules.cleanupDistance=float(reader.get_value_float(0));
            else if(reader.is_value("title_ids"))title=reader.get_value_int(0);
            else if(reader.is_value("mission_title_ids"))missionTitle=reader.get_value_int(0);
            else if(reader.is_value("cargo_name_ids"))cargoName=reader.get_value_int(0);
            else if(reader.is_value("board_ids"))board=reader.get_value_int(0);
            else if(reader.is_value("pickup_ids"))pickup=reader.get_value_int(0);
            else if(reader.is_value("deliver_ids"))deliver=reader.get_value_int(0);
            else if(reader.is_value("park_ids"))park=reader.get_value_int(0);
            else if(reader.is_value("continue_ids"))question=reader.get_value_int(0);
            else if(reader.is_value("launch_ids"))launch=reader.get_value_int(0);
            else if(reader.is_value("recover_ids"))recover=reader.get_value_int(0);
            else if(reader.is_value("voice"))voice=CreateID(reader.get_value_string());
            else if(reader.is_value("audio_enabled"))audio=reader.get_value_bool(0);
            else if(reader.is_value("reposition_audio_enabled"))repositionAudio=reader.get_value_bool(0);
            else if(reader.is_value("pickup_from_ids"))pickupFrom=reader.get_value_int(0);
            else if(reader.is_value("boarding_comm_delay"))boardingCommDelay=float(reader.get_value_float(0));
            else if(reader.is_value("boarding_comm_delay_max"))boardingCommDelayMax=float(reader.get_value_float(0));
        }
        reader.close();
        if(!OpenContentDataIni("Missions\\TrainCourier\\catalog.ini",&reader))return false;
        while(reader.read_header()) {
            if(reader.is_header("CourierPoint") || reader.is_header("CourierParking")) {
                bool parking=reader.is_header("CourierParking");
                Point p;Vector angles{};
                while(reader.read_value()) {
                    if(reader.is_value("nickname"))p.nickname=reader.get_value_string();
                    else if(reader.is_value("base"))p.base=reader.get_value_string();
                    else if(reader.is_value("system"))p.system=reader.get_value_string();
                    else if(reader.is_value("voice_name"))p.voice=reader.get_value_string();
                    else if(reader.is_value("transfer_base"))p.transfer=reader.get_value_string();
                    else if(reader.is_value("commodity"))p.commodities.push_back(reader.get_value_string());
                    else if(reader.is_value("demand"))p.demand.push_back(reader.get_value_string());
                    else if(reader.is_value("supply_price")){std::string n=reader.get_value_string(0);p.prices[n]=reader.get_value_int(1);}
                    else if(reader.is_value("faction"))pub::Reputation::GetReputationGroup(p.faction,reader.get_value_string());
                    else if(reader.is_value("name_ids"))p.name=reader.get_value_int(0);
                    else if(reader.is_value("freight_hub"))p.freightHub=reader.get_value_bool(0);
                    else if(reader.is_value("large_planet"))p.largePlanet=reader.get_value_bool(0);
                    else if(reader.is_value("refinery"))p.refinery=reader.get_value_bool(0);
                    else if(reader.is_value("position"))p.position={float(reader.get_value_float(0)),float(reader.get_value_float(1)),float(reader.get_value_float(2))};
                    else if(reader.is_value("rotation"))angles={float(reader.get_value_float(0)),float(reader.get_value_float(1)),float(reader.get_value_float(2))};
                }
                pub::GetBaseID(p.baseId,p.base.c_str());pub::GetSystemID(p.systemId,p.system.c_str());
                // Trading points in this catalog are horizontal; reject unsupported
                // poses rather than placing long cargo through a station.
                if(angles.x!=0 || angles.z!=0 || !p.baseId || !p.systemId)return false;
                if((p.largePlanet || p.refinery) && !p.freightHub)return false;
                p.orientation=pointOrientation(angles.y);
                // Clear the static moored trains and the approach to the fixture.
                if(!parking)p.position.y+=350.f;
                (parking?parkingPoints:points).push_back(p);
            } else if(reader.is_header("CourierCommodity")) {
                std::string nickname,voiceName;unsigned name=0,pod=0;
                while(reader.read_value()) {
                    if(reader.is_value("nickname"))nickname=reader.get_value_string();
                    else if(reader.is_value("voice_name"))voiceName=reader.get_value_string();
                    else if(reader.is_value("name_ids"))name=reader.get_value_int(0);
                    else if(reader.is_value("pod"))pod=CreateID(reader.get_value_string());
                }
                if(!nickname.empty())commodityVoices[nickname]=voiceName;
                commodityNames[nickname]=name;commodityPods[nickname]=pod;
            } else if(reader.is_header("CourierRoute")) {
                Route r;
                while(reader.read_value()) {
                    if(reader.is_value("source"))r.source=reader.get_value_string();
                    else if(reader.is_value("destination"))r.destination=reader.get_value_string();
                    else if(reader.is_value("distance"))r.distance=reader.get_value_int(0);
                    else if(reader.is_value("jumps"))r.jumps=reader.get_value_int(0);
                }
                if(!r.source.empty() && !r.destination.empty() && r.distance)routes.push_back(r);
            }
        }
        reader.close();
        if(!OpenContentDataIni("Missions\\TrainCourier\\descriptions.ini",&reader))return false;
        while(reader.read_header())if(reader.is_header("CourierDescription")) {
            std::string nick;std::vector<unsigned> variants;
            while(reader.read_value()) {
                if(reader.is_value("commodity"))nick=reader.get_value_string();
                else if(reader.is_value("text_ids"))variants.push_back(reader.get_value_int(0));
            }
            if(!nick.empty() && !variants.empty())descriptions[nick]=variants;
        }
        if(!pickupFrom)pickupFrom=pickup; // compatibility with existing configs
        if(!missionTitle)missionTitle=title;
        if(!cargoName)cargoName=title;
        return rules.valid() && description && timerIds && overdueIds && std::isfinite(timerX) && std::isfinite(timerY) &&
            std::isfinite(boardingCommDelay) && boardingCommDelay>=0 && std::isfinite(boardingCommDelayMax) && boardingCommDelayMax>=boardingCommDelay && title && board && pickup && deliver && park && question && launch && recover && !points.empty() && !parkingPoints.empty() && !routes.empty();
    }
};
Point const* boardingPoint(Config const& config,unsigned base) {
    if(!base)return nullptr;
    for(auto const& berth:config.parkingPoints)if(berth.baseId==base && !berth.transfer.empty()) {
        unsigned transfer=0;pub::GetBaseID(transfer,berth.transfer.c_str());
        if(!transfer)continue;
        for(auto const& point:config.points)if(point.baseId==base && point.systemId==berth.systemId)
            for(auto const& route:config.routes)if(route.source==point.base)return &berth;
    }
    return nullptr;
}
float length(Vector const& v){return std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z);}
float distance(Vector const& a,Vector const& b){return length({a.x-b.x,a.y-b.y,a.z-b.z});}

// Keep native path/rep/nav tokens; append the localized destination name for
// the delivery template's %s. A base token would redirect the waypoint to its
// docking solar instead of the cargo depot, so use the base's string IDS.
class CourierPathObjective final : public FNNObjectiveType5 {
    unsigned nameIds;
public:
    CourierPathObjective(FNNObjectiveType5 const& other,unsigned name):FNNObjectiveType5(other),nameIds(name){}
    bool BuildDescription() override {
        if(!FNNObjectiveType5::BuildDescription())return false;
        if(nameIds)Objective.Description.append_string(nameIds);
        return true;
    }
    FMissionObjective* Clone() override {return new CourierPathObjective(*this);}
};

class CourierMission final : public FMissionScript {
    Config config;
    State state;
    Point source,destination;
    std::string commodity;
    unsigned trailer=0,boarding=0,transferBase=0,jumpDestination=0;
    bool ready=false,swapped=false,started=false,jumping=false,failed=false;
    bool jumpArrived=false;
    float pause=0;
    bool boardingLaunchReady=false,boardingSpoken=false;
    float boardingCommWait=0;
    unsigned boardingCommId=0,boardingCommListener=0;
    Vector transferPosition{};Matrix transferOrientation{};
    BridgeFn bridge=nullptr;
    CargoSnapshot savedCargo{};
    bool restoreCargo=false,restoreObjective=false,continueSpoken=false,transferInSpace=false;
    bool cargoPending=false;
    bool returnImmediately=false,repositionedOrder=false;
    unsigned objectiveObject=0,objectiveName=0;
    Point pendingPoint;
    unsigned pendingObject=0,pendingIds=0;
    std::string pendingLabel;
    float markerDelay=0,uncoupledTime=0;
    bool arrivalSpoken=false;
    unsigned questionComm=0,questionListener=0;
    float remaining=-1.f,expectedSeconds=0.f;
    unsigned proseIds=0,lostPods=0;
    int quotedReward=0,lossCharge=0;
    bool activeOrder() const {return (state.stage==Stage::Pickup || state.stage==Stage::Deliver) && !state.retired;}
    void advanceClock(float dt) {
        if(activeOrder() && state.pickedUp && std::isfinite(dt) && dt>0)remaining=(std::max)(-604800.f,remaining-dt);
    }
    std::vector<std::string> goodsFor(Point const& target) const {
        std::vector<std::string> goods;
        // Consolidated freight may not belong to this depot's regular stock.
        auto const available=(trailer || cargoPending)?std::vector<std::string>{commodity}:source.commodities;
        for(auto const& name:available) {
            if(std::find(target.demand.begin(),target.demand.end(),name)!=target.demand.end() &&
               config.descriptions.find(name)!=config.descriptions.end() && !config.descriptions.at(name).empty())goods.push_back(name);
        }
        return goods;
    }
    void describeOrder() {
        if(!proseIds || commodity.empty())return;
        FmtStr prose;prose.begin_mad_lib(proseIds);prose.append_string(destination.name);prose.end_mad_lib();
        Field_0x68=FmtStr();Field_0x68.begin_mad_lib(config.description);
        Field_0x68.append_fmt_str(prose);
        Field_0x68.append_string(config.commodityNames[commodity]);
        Field_0x68.append_string(source.name);Field_0x68.append_string(destination.name);
        auto const* targetSystem=Universe::get_system(destination.systemId);
        Field_0x68.append_string(targetSystem?targetSystem->GetStridName():0);
        Field_0x68.append_int(state.wagons);Field_0x68.append_int(state.wagons*100);
        Field_0x68.append_int(state.distance);Field_0x68.append_int(quotedReward);
        Field_0x68.append_int(lossCharge);Field_0x68.append_int(lostPods);
        Field_0x68.append_int(state.reward);
        Field_0x68.append_int(unsigned(expectedSeconds/60));
        Field_0x68.append_int(state.unlockedWagons);Field_0x68.append_int(state.unlockedWagons*100);
        Field_0x68.end_mad_lib();
        // Reward stays zero: individual orders are paid exactly once at handover.
    }
    void refreshBrief() {
        describeOrder();
        // NNPath owns the live goals. Sending the empty ordinary mission list
        // here would erase navigation when a container is hit.
        if(NnPath.bActive)NnPath.SendObjectives(NnPath.State==4,false);
    }
    void observeLoss(CargoSnapshot const& cargo) {
        if(!activeOrder() || !quotedReward)return;
        unsigned alive=0,pod=config.commodityPods[commodity];
        for(unsigned i=0;i<cargo.equipmentCount;++i) {
            auto const& e=cargo.equipment[i];
            if(e.arch==pod && e.mounted && e.health>0 && !_strnicmp(e.hardpoint,"HpCargo",7))++alive;
        }
        unsigned lost=state.wagons*2-(std::min)(alive,state.wagons*2);
        if(lost<=lostPods)return;
        lostPods=lost;state.reward=freightPayment(quotedReward,lostPods,lossCharge);
        refreshBrief();
        if(config.lossIds) {
            FmtStr message;message.begin_mad_lib(config.lossIds);message.append_int(lostPods);message.append_int(state.reward);message.end_mad_lib();
            pub::Player::DisplayMissionMessage(PlayerId,message,static_cast<MissionMessageType>(2),false);
        }
        FDUMP(0x100001,"TrainCourier: lost pods=%u/%u payment=%d quote=%d",lostPods,state.wagons*2,state.reward,quotedReward);
    }
    bool readSave(INI_Reader& reader) {
        reader.reset();bool found=false;
        while(reader.read_header())if(reader.is_header("TrainCourierSave")) {
            found=true;unsigned version=0;bool haveSizeProgress=false,haveCapacity=false;
            while(reader.read_value()) {
                if(reader.is_value("version"))version=reader.get_value_int(0);
                else if(reader.is_value("stage"))state.stage=static_cast<Stage>(reader.get_value_int(0));
                else if(reader.is_value("order"))state.order=reader.get_value_int(0);
                else if(reader.is_value("wagons"))state.wagons=reader.get_value_int(0);
                else if(reader.is_value("unlocked_wagons")){state.unlockedWagons=reader.get_value_int(0);haveCapacity=true;}
                else if(reader.is_value("deliveries_at_size")){state.deliveriesAtSize=reader.get_value_int(0);haveSizeProgress=true;}
                else if(reader.is_value("cargo_pending"))cargoPending=reader.get_value_bool(0);
                else if(reader.is_value("return_immediately"))returnImmediately=reader.get_value_bool(0);
                else if(reader.is_value("repositioned_order"))repositionedOrder=reader.get_value_bool(0);
                else if(reader.is_value("distance"))state.distance=reader.get_value_int(0);
                else if(reader.is_value("source"))state.source=reader.get_value_string();
                else if(reader.is_value("destination"))state.destination=reader.get_value_string();
                else if(reader.is_value("recent_base"))rememberBase(state,reader.get_value_string());
                else if(reader.is_value("picked_up"))state.pickedUp=reader.get_value_bool(0);
                else if(reader.is_value("retired"))state.retired=reader.get_value_bool(0);
                else if(reader.is_value("paid"))state.paid=reader.get_value_bool(0);
                else if(reader.is_value("reward"))state.reward=reader.get_value_int(0);
                else if(reader.is_value("order_remaining"))remaining=float(reader.get_value_float(0));
                else if(reader.is_value("order_expected"))expectedSeconds=float(reader.get_value_float(0));
                else if(reader.is_value("prose_ids"))proseIds=reader.get_value_int(0);
                else if(reader.is_value("quoted_reward"))quotedReward=reader.get_value_int(0);
                else if(reader.is_value("loss_charge"))lossCharge=reader.get_value_int(0);
                else if(reader.is_value("lost_pods"))lostPods=reader.get_value_int(0);
                else if(reader.is_value("swapped"))swapped=reader.get_value_bool(0);
                else if(reader.is_value("failed"))failed=reader.get_value_bool(0);
                else if(reader.is_value("commodity"))commodity=reader.get_value_string();
                else if(reader.is_value("transfer_base"))transferBase=reader.get_value_int(0);
                else if(reader.is_value("transfer_position"))transferPosition={float(reader.get_value_float(0)),float(reader.get_value_float(1)),float(reader.get_value_float(2))};
                else if(reader.is_value("transfer_rotation"))for(int i=0;i<9;++i)(&transferOrientation.E[0][0])[i]=float(reader.get_value_float(i));
                else if(reader.is_value("cargo")) {
                    savedCargo.arch=reader.get_value_int(0);savedCargo.system=reader.get_value_int(1);
                    savedCargo.hitpoints=reader.get_value_int(2);savedCargo.coupled=reader.get_value_int(3);
                } else if(reader.is_value("cargo_position"))savedCargo.position={float(reader.get_value_float(0)),float(reader.get_value_float(1)),float(reader.get_value_float(2))};
                else if(reader.is_value("cargo_rotation"))for(int i=0;i<9;++i)(&savedCargo.orientation.E[0][0])[i]=float(reader.get_value_float(i));
                else if(reader.is_value("cargo_equipment")) {
                    if(savedCargo.equipmentCount>=CargoSnapshot::MaxEquipment)return false;
                    auto& e=savedCargo.equipment[savedCargo.equipmentCount++];
                    e.arch=reader.get_value_int(0);e.count=reader.get_value_int(1);e.health=float(reader.get_value_float(2));e.mounted=reader.get_value_int(3);
                    std::snprintf(e.hardpoint,sizeof(e.hardpoint),"%s",reader.get_value_string(4));
                } else if(reader.is_value("cargo_group")) {
                    if(savedCargo.groupCount>=CargoSnapshot::MaxGroups)return false;
                    savedCargo.groups[savedCargo.groupCount++]={unsigned(reader.get_value_int(0)),float(reader.get_value_float(1))};
                }
            }
            if(!haveSizeProgress && state.paid)state.deliveriesAtSize=1;
            if(!haveCapacity)state.unlockedWagons=state.wagons;
            if((version!=1 && version!=2) || !state.valid(config.rules) || !std::isfinite(remaining) ||
               !std::isfinite(expectedSeconds) || expectedSeconds<0 || expectedSeconds>1814400 ||
               remaining < -604800 || remaining>1814400 ||
               lostPods>state.wagons*2 || quotedReward<0 || lossCharge<0)return false;
            if(version==1)remaining=config.rules.orderSeconds+config.rules.wagonSeconds*state.wagons;
            if(!expectedSeconds)expectedSeconds=config.rules.orderSeconds+config.rules.wagonSeconds*state.wagons;
        }
        if(!found)return false;
        bool haveSource=false,haveDest=false;
        for(auto const& p:config.points) {
            if(p.nickname==state.source){source=p;haveSource=true;}
            if(p.nickname==state.destination){destination=p;haveDest=true;}
        }
        if(state.stage==Stage::Parking || state.stage==Stage::TransferOut)
            for(auto const& p:config.parkingPoints)if(p.nickname==state.source){source=p;haveSource=true;}
        // Legacy boarding saves did not store their source; those originated at Bismarck.
        if((state.stage==Stage::Boarding || state.stage==Stage::TransferIn) && state.source.empty())
            for(auto const& p:config.points)if(p.base=="rh_biz_01_base") {
                source=p;state.source=p.nickname;haveSource=true;break;
            }
        if(!haveSource || ((state.pickedUp || state.stage==Stage::Offer || state.stage==Stage::Pickup) && !haveDest))return false;
        if(!commodity.empty()) {
            auto found=config.descriptions.find(commodity);
            if(found==config.descriptions.end())return false;
            if(std::find(found->second.begin(),found->second.end(),proseIds)==found->second.end())proseIds=found->second.front();
            if(!quotedReward)quotedReward=state.reward;
            if(!lossCharge)lossCharge=podLossCharge(config.rules,state.wagons,quotedReward,source.prices[commodity]);
            state.reward=freightPayment(quotedReward,lostPods,lossCharge);
            describeOrder();
        }
        if(cargoPending && (state.stage!=Stage::Pickup || state.pickedUp || state.retired))return false;
        restoreCargo=(state.stage==Stage::Pickup || state.stage==Stage::Deliver) && !state.retired && !cargoPending;
        if(restoreCargo && (!savedCargo.arch || savedCargo.hitpoints<=0))return false;
        if(restoreCargo && savedCargo.coupled)savedCargo.system=system();
        // Old saves have no travel history: their current contract still gives
        // enough context to avoid immediately returning to its pickup planet.
        if(state.recentBases.empty()) {rememberBase(state,source.base);rememberBase(state,destination.base);}
        if(state.stage==Stage::AwaitContinue)source=destination;
        restoreObjective=true;
        started=true;pause=1;state.popup=false;
        return request(Operation::Register);
    }
    void save(FILE* file) {
        if(!ready || state.stage==Stage::Complete || state.stage==Stage::Failed)return;
        Packet packet;packet.player=PlayerId;packet.operation=Operation::Snapshot;
        if(trailer && bridge && bridge(&packet) && packet.result==1){savedCargo=packet.cargo;observeLoss(savedCargo);}
        std::fprintf(file,"\n[TrainCourierSave]\nversion = 2\nstage = %u\norder = %u\nwagons = %u\ndistance = %u\nsource = %s\ndestination = %s\npicked_up = %u\nretired = %u\npaid = %u\nreward = %d\nswapped = %u\n",
            unsigned(state.stage),state.order,state.wagons,state.distance,source.nickname.c_str(),destination.nickname.c_str(),
            state.pickedUp,state.retired,state.paid,state.reward,swapped);
        std::fprintf(file,"failed = %u\n",failed);
        std::fprintf(file,"commodity = %s\n",commodity.c_str());
        std::fprintf(file,"order_remaining = %.9g\nprose_ids = %u\nquoted_reward = %d\nloss_charge = %d\nlost_pods = %u\n",
            remaining,proseIds,quotedReward,lossCharge,lostPods);
        std::fprintf(file,"order_expected = %.9g\n",expectedSeconds);
        std::fprintf(file,"deliveries_at_size = %u\ncargo_pending = %u\n",state.deliveriesAtSize,cargoPending);
        std::fprintf(file,"unlocked_wagons = %u\n",state.unlockedWagons);
        for(auto const& base:state.recentBases)std::fprintf(file,"recent_base = %s\n",base.c_str());
        std::fprintf(file,"return_immediately = %u\nrepositioned_order = %u\n",returnImmediately,repositionedOrder);
        std::fprintf(file,"transfer_base = %u\ntransfer_position = %.9g, %.9g, %.9g\ntransfer_rotation = ",transferBase,transferPosition.x,transferPosition.y,transferPosition.z);
        for(int i=0;i<9;++i)std::fprintf(file,"%s%.9g",i?", ":"",(&transferOrientation.E[0][0])[i]);
        std::fputc('\n',file);
        if((state.stage==Stage::Pickup || state.stage==Stage::Deliver) && !state.retired && !cargoPending) {
            auto const& c=savedCargo;
            std::fprintf(file,"cargo = %u, %u, %d, %u\ncargo_position = %.9g, %.9g, %.9g\ncargo_rotation = ",c.arch,c.system,c.hitpoints,c.coupled,c.position.x,c.position.y,c.position.z);
            for(int i=0;i<9;++i)std::fprintf(file,"%s%.9g",i?", ":"",(&c.orientation.E[0][0])[i]);
            std::fputc('\n',file);
            for(unsigned i=0;i<c.equipmentCount;++i) {
                auto const& e=c.equipment[i];std::fprintf(file,"cargo_equipment = %u, %d, %.9g, %u, %s\n",e.arch,e.count,e.health,e.mounted,e.hardpoint);
            }
            for(unsigned i=0;i<c.groupCount;++i)std::fprintf(file,"cargo_group = %u, %.9g\n",c.groups[i].id,c.groups[i].health);
        }
    }
    void onJumpDeparture(pub::Controller::EMessage msg,unsigned const* p) {
        using M=pub::Controller::EMessage;
        // DockComplete is sent BEFORE the player's old client world is torn
        // down. Msg0x25 arrives afterwards, when the physical coupling may
        // already be gone; keep it only as an idempotent fallback.
        if((msg!=M::DockComplete && msg!=M::Msg0x25) || !p || jumping ||
           p[0]!=ship() || !trailer || !query().coupled)return;
        unsigned targetSystem=0,targetGate=0;
        if(pub::SpaceObj::GetJumpTarget(p[1],targetSystem,targetGate)==0 && targetSystem) {
            // Capture the exact damage/cargo state before physics is removed;
            // the arrival autosave runs while the train is still in transit.
            Packet snapshot;snapshot.player=PlayerId;snapshot.operation=Operation::Snapshot;
            if(bridge && bridge(&snapshot) && snapshot.result==1){savedCargo=snapshot.cargo;observeLoss(savedCargo);}
            Packet transit;transit.player=PlayerId;transit.operation=Operation::SuspendCargo;transit.system=targetSystem;
            jumpDestination=targetSystem;jumpArrived=false;jumping=true;
            jumping=bridge && bridge(&transit) && transit.result==1;
            FDUMP(0x100001,"TrainCourier: jump begin player=%u trailer=%u target=%u suspended=%u",PlayerId,trailer,targetSystem,jumping);
        }
    }
    void onJumpArrival(pub::Controller::EMessage msg,unsigned const* p) {
        if(msg!=pub::Controller::EMessage::JumpInComplete || !p || !jumping ||
           p[1]!=ship() || p[0]!=jumpDestination)return;
        jumpArrived=true;
        FDUMP(0x100001,"TrainCourier: jump-in complete player=%u trailer=%u system=%u",PlayerId,trailer,jumpDestination);
    }
    bool resumeJump() {
        if(!jumping)return true;
        // The new physics world exists BEFORE the client starts JumpInAction.
        // is_jumping() is false in that interval. Wait for the actual arrival
        // callback, which follows the final beam to the exit position.
        if(!jumpArrived || system()!=jumpDestination || !request(Operation::ResumeCargo))return false;
        jumping=false;jumpArrived=false;
        FDUMP(0x100001,"TrainCourier: jump restored player=%u trailer=%u system=%u",PlayerId,trailer,jumpDestination);
        return true;
    }
    bool request(Operation op,unsigned object=0) {
        Packet p;p.player=PlayerId;p.operation=op;p.trailer=object;
        p.cleanupDistance=config.rules.cleanupDistance;
        return bridge && bridge(&p) && p.result==1;
    }
    Packet query() {
        Packet p;p.player=PlayerId;
        if(bridge)bridge(&p);
        return p;
    }
    unsigned ship() const {unsigned id=0;pub::Player::GetShip(PlayerId,id);return id;}
    unsigned system() const {unsigned id=0;pub::Player::GetSystem(PlayerId,id);return id;}
    void say(char const* family,Point const* base=nullptr) {
        if(!config.audio || !ship())return;
        unsigned ids[16]{};int count=0;
        auto variant=[&](char const* name,char const* suffix) {
            auto line=MakeVoiceLineName(name,suffix,config.voice);
            if(!line.Data[0] || count==16)return false;
            ids[count++]=CreateID(line.Data);return true;
        };
        bool english=config.voice==CreateID("atc_leg_m01_new");
        bool reposition=!std::strcmp(family,"tc_reposition");
        if(english && (!std::strcmp(family,"tc_pickup") || !std::strcmp(family,"tc_next") || reposition)) {
            // Same commodity identification as FGcsLineHailTrade: the Good's
            // msg_id_prefix is already a complete clip name. '+' belongs to
            // the surrounding sentence fragments, never to the commodity ID.
            TString<64> cargo;
            if(!base || base->voice.empty() || config.commodityVoices.find(commodity)==config.commodityVoices.end() ||
               pub::TranslateGoodToMsgIdPrefix(CreateID(commodity.c_str()),cargo)!=0 || !cargo.Data[0])return;
            if(reposition && config.repositionAudio && !source.voice.empty()) {
                if(!variant("tc_reposition","+"))return;
                ids[count++]=CreateID(source.voice.c_str());
                if(!variant("tc_reposition_empty","-"))return;
            }
            if(!variant("tc_order","+"))return;
            ids[count++]=CreateID(cargo.Data);
            if(!variant("tc_destination","+"))return;
            ids[count++]=CreateID(base->voice.c_str());
            if(!variant("tc_collect","-"))return;
        } else if(english && (!std::strcmp(family,"tc_depart") || !std::strcmp(family,"tc_park"))) {
            if(!base || base->voice.empty() || !variant(family,"+"))return;
            ids[count++]=CreateID(base->voice.c_str());
        } else {
            if(!variant(family,"-"))return;
            if(!english && base && !base->voice.empty()) {
                ids[count++]=CreateID("tc_destination_name_01+");ids[count++]=CreateID(base->voice.c_str());
                auto cargoVoice=config.commodityVoices.find(commodity);
                if(cargoVoice!=config.commodityVoices.end() && !cargoVoice->second.empty()) {
                    ids[count++]=CreateID("tc_cargo_name_01+");ids[count++]=CreateID(cargoVoice->second.c_str());
                }
            }
        }
        Costume costume{};
        costume.PartIds[0]=CreateID("br_brighton_head");
        costume.PartIds[1]=CreateID("rh_male_guard_body");
        costume.PartIds[2]=CreateID("benchmark_male_hand_left");
        costume.PartIds[3]=CreateID("benchmark_male_hand_right");
        unsigned listener=ship();
        bool question=!std::strcmp(family,"tc_continue");
        bool greeting=!std::strcmp(family,"tc_board");
        if(question){questionComm=ids[count-1];questionListener=listener;}
        if(greeting){boardingCommId=ids[count-1];boardingCommListener=listener;}
        int result=pub::SpaceObj::SendComm(0,listener,config.voice,&costume,config.title,ids,count,0,.5f,true);
        FDUMP(0x100001,"TrainCourier: comm family=%s player=%u parts=%d result=%d",family,PlayerId,count,result);
        if(result!=0 && question)
            questionComm=questionListener=0;
        if(result!=0 && greeting) {
            boardingCommId=boardingCommListener=0;
            boardingSpoken=false;boardingCommWait=2.f;
        }
    }
    void armBoardingComm() {
        if(boardingLaunchReady)return;
        boardingLaunchReady=true;
        boardingCommWait=config.boardingCommDelay+(config.boardingCommDelayMax-config.boardingCommDelay)*
            (float(std::rand())/float(RAND_MAX));
        FDUMP(0x100001,"TrainCourier: boarding comm armed player=%u delay=%.2f",PlayerId,boardingCommWait);
    }
    void updateBoardingComm(float dt) {
        if(state.stage!=Stage::Boarding || !boarding || !boardingLaunchReady || boardingSpoken)return;
        boardingCommWait-=dt;
        if(boardingCommWait<=0){boardingSpoken=true;say("tc_board");}
    }
    void completeBoardingComm(unsigned const* p) {
        if(!boardingCommId || p[0]!=boardingCommListener || p[2]!=0 || p[3]!=boardingCommId)return;
        FDUMP(0x100001,"TrainCourier: boarding comm completed player=%u result=%u",PlayerId,p[4]);
        boardingCommId=boardingCommListener=0;
        if(p[4]==unsigned(CommResult::CANCELLED) && state.stage==Stage::Boarding) {
            boardingSpoken=false;boardingCommWait=2.f;
        }
    }
    void objective(unsigned ids,Point const& p,unsigned object=0,char const* label=nullptr) {
        // Boarding may request the same destination every heartbeat while the
        // player is in another system. Do not restart NNPath's initial timer.
        pendingObject=0;
        if(NnPath.bActive && objectiveObject==object && NnPath.SystemId==p.systemId && NnPath.TargetIds==int(ids) &&
           distance(NnPath.Position,p.position)<.01f)return;
        ActNnPath path(this);
        path.Position=p.position;path.SystemId=p.systemId;
        if(label)path.Label=label;
        path.TravelIds=path.TargetIds=static_cast<int>(ids);
        if(!path.Execute())return;
        objectiveObject=object;objectiveName=(ids==config.deliver || ids==config.park || ids==config.pickupFrom)?p.name:0;
        GetOrCreatePlayer(PlayerId)->ClearObjectives();
        // Use the actual Act_NNPath implementation and its normal heartbeat,
        // tradelane and system-entry handlers for every leg of the route.
        FDUMP(0x100001,"TrainCourier: NNPath player=%u target=%s system=%u ids=%u",PlayerId,p.nickname.c_str(),p.systemId,ids);
    }
    void objectObjective(unsigned ids,Point const& p,unsigned object,char const* label=nullptr) {
        // Like the story's spawn -> Cnd_Timer -> mark/set-NN sequence: let the
        // client create the object before resolving its reputation waypoint.
        NnPath.Reset();objectiveObject=objectiveName=0;
        pendingPoint=p;pendingObject=object;pendingIds=ids;pendingLabel=label?label:"";markerDelay=.15f;
    }
    void updateObjectObjective(float dt) {
        if(!pendingObject)return;
        markerDelay-=dt;if(markerDelay>0)return;
        if(pendingPoint.systemId!=system()) {
            objective(pendingIds,pendingPoint,pendingObject,pendingLabel.empty()?nullptr:pendingLabel.c_str());
            return;
        }
        Matrix rotation;unsigned liveSystem=0;int rep=-1;
        if(pub::SpaceObj::GetSystem(pendingObject,liveSystem)!=0 || liveSystem!=system() ||
           pub::SpaceObj::GetLocation(pendingObject,pendingPoint.position,rotation)!=0 ||
           pub::SpaceObj::GetRep(pendingObject,rep)!=0 || rep==-1)return;
        pendingPoint.systemId=liveSystem;
        unsigned object=pendingObject;
        objective(pendingIds,pendingPoint,object,pendingLabel.empty()?nullptr:pendingLabel.c_str());
        pub::Player::MarkObj(PlayerId,object,1);
    }
    void launchObjective() {
        // Match DestroyMission's UpdateDockedObjective: Content's live ship,
        // a nav-marker objective and notification flag 0x10. GetShip can retain
        // an object ID during the base transition; it is not the docked state.
        if(!PlayerState || PlayerState->ShipObject || state.stage!=Stage::Boarding)return;
        auto* player=GetOrCreatePlayer(PlayerId);
        auto* front=player->Objectives.GetFront();
        if(front && front->Ids==static_cast<int>(config.launch))return;
        NnPath.Reset();pendingObject=objectiveObject=objectiveName=0;
        player->ClearObjectives();
        auto* goal=static_cast<FNNObjectiveNavMarker*>(player->Objectives.Add(2,this));
        Vector position=source.position;PlayerState->GetPosition(&position);
        goal->bHidden=0;goal->Ids=static_cast<int>(config.launch);goal->Objective.Type=0x10;
        goal->Marker.Data[0]=PlayerState->GetSystemId();goal->Marker.Data[1]=0;
        std::memcpy(&goal->Marker.Data[2],&position,sizeof(position));
        goal->BuildDescription();RenumberObjectives(PlayerId);
        FDUMP(0x100001,"TrainCourier: launch objective player=%u ids=%u type=0x10",PlayerId,config.launch);
    }
    bool friendly(Point const& p) {
        int rep=-1;float attitude=-1;
        return pub::Player::GetRep(PlayerId,rep)==0 && pub::Reputation::GetReputation(rep,p.faction,attitude)==0 && attitude>GDockHostileAttitude;
    }
    bool choose() {
        if(!state.pickedUp && !friendly(source))return false;
        bool existing=trailer || cargoPending;
        bool feeder=!source.freightHub && !existing;
        std::map<std::string,Point const*> eligible;
        std::vector<std::string> hubs;
        for(auto const& p:config.points)if(friendly(p)) {
            if(p.freightHub)hubs.push_back(p.base);
            if(!goodsFor(p).empty())eligible[p.base]=&p;
        }
        auto depthToHub=[&](std::string const& base) {
            auto const& targets=hubs;
            if(std::find(targets.begin(),targets.end(),base)!=targets.end())return 0u;
            unsigned depth=~0u;
            for(auto const& r:config.routes)if(r.source==base &&
                std::find(targets.begin(),targets.end(),r.destination)!=targets.end())depth=(std::min)(depth,r.distance);
            return depth;
        };
        unsigned originDepth=feeder?depthToHub(source.base):0;
        unsigned bestRank=~0u,bestDistance=~0u;
        std::vector<size_t> choices;
        for(size_t i=0;i<config.routes.size();++i) {
            auto const& r=config.routes[i];auto found=eligible.find(r.destination);
            if(r.source!=source.base || r.destination==source.base || found==eligible.end())continue;
            Point const& target=*found->second;
            unsigned rank=0;
            if(feeder) {
                if(feederWagons(config.rules,orderWagonLimit(state,config.rules),r.distance,r.jumps)<2)continue;
                rank=target.freightHub?0:1;
                // Planets and megabases share the same pool. Intermediate
                // ordinary depots must still make progress towards a hub.
                if(rank==1 && depthToHub(target.base)>=originDepth)continue;
            } else {
                if(r.distance<minimumRouteDistance(config.rules,state.wagons) ||
                   r.jumps<minimumRouteJumps(config.rules,state.wagons))continue;
                if(source.refinery && !existing)
                    rank=target.freightHub?0:1;
            }
            if(rank>bestRank || (rank==bestRank && r.distance>bestDistance))continue;
            if(rank<bestRank || r.distance<bestDistance) {
                choices.clear();bestRank=rank;bestDistance=r.distance;
            }
            choices.push_back(i);
        }
        if(choices.empty())return false;
        // Among equal shortest routes, favor bases outside recent history 4:1.
        // A repeat remains possible; history never adds distance or changes
        // the shared priority of planets and megabases.
        auto weight=[&](size_t i) {
            return revisitPenalty(state,config.routes[i].destination)?1u:4u;
        };
        unsigned totalWeight=0;
        for(auto i:choices)totalWeight+=weight(i);
        unsigned draw=std::rand()%totalWeight;
        size_t selected=choices.front();
        for(auto i:choices) {
            unsigned w=weight(i);
            if(draw<w){selected=i;break;}
            draw-=w;
        }
        auto const& route=config.routes[selected];
        state.distance=route.distance;
        if(feeder)state.wagons=feederWagons(config.rules,orderWagonLimit(state,config.rules),route.distance,route.jumps);
        std::vector<size_t> points;
        for(size_t i=0;i<config.points.size();++i)if(config.points[i].base==route.destination && friendly(config.points[i]))points.push_back(i);
        if(points.empty())return false;
        destination=config.points[points[std::rand()%points.size()]];
        state.source=source.nickname;state.destination=destination.nickname;
        if(!existing) {
            auto goods=goodsFor(destination);if(goods.empty())return false;
            commodity=goods[std::rand()%goods.size()];
            auto const& texts=config.descriptions[commodity];proseIds=texts[std::rand()%texts.size()];
            quotedReward=freightQuote(config.rules,state.wagons,state.distance,source.prices[commodity]);
            lossCharge=podLossCharge(config.rules,state.wagons,quotedReward,source.prices[commodity]);
            state.reward=quotedReward;lostPods=0;
        }
        describeOrder();
        return true;
    }
    bool spawnCargo() {
        // In SP, an inactive system has no physics child objects. Attaching a
        // pod to HpCargo03 there dereferences null CObject user data (12:38 dump).
        // Wait for the player/physics world to arrive before creating the train.
        if(system()!=source.systemId)return false;
        pub::SpaceObj::ShipInfo info{};
        char arch[48],loadout[192];
        std::snprintf(arch,sizeof(arch),"tc_wagons_%02u",state.wagons);
        std::snprintf(loadout,sizeof(loadout),"tc_wagons_%02u_%s",state.wagons,commodity.c_str());
        info.ControllerId=ControllerId;info.SystemID=source.systemId;
        info.ShipArchID=CreateID(arch);info.LoadoutID=CreateID(loadout);
        info.Position=source.position;info.Orientation=source.orientation;info.HitPts=-1;
        FmtStr name,empty;name.begin_mad_lib(config.cargoName);name.end_mad_lib();
        if(pub::Reputation::Alloc(info.VibeGroupId,empty,name)!=0)return false;
        int playerRep=-1;pub::Player::GetRep(PlayerId,playerRep);
        pub::Reputation::SetAttitude(info.VibeGroupId,playerRep,1.f);
        pub::Reputation::SetAttitude(playerRep,info.VibeGroupId,1.f);
        if(pub::SpaceObj::Create(trailer,info)!=0){pub::Reputation::Free(info.VibeGroupId);return false;}
        if(!request(Operation::Register,trailer)){pub::SpaceObj::Destroy(trailer,DESTROY_NORMAL);trailer=0;return false;}
        cargoPending=false;return true;
    }
    bool createPendingCargo() {
        if(!cargoPending || state.stage!=Stage::Pickup || system()!=source.systemId)return true;
        if(!spawnCargo())return false;
        objectObjective(config.pickupFrom,source,trailer);
        return true;
    }
    bool next() {
        arrivalSpoken=false;
        std::string previousBase=source.base;
        state.pickedUp=state.retired=state.paid=state.popup=false;
        uncoupledTime=0;
        continueSpoken=false;
        // The previous delivery still occupies its track. The next consist uses
        // a parallel track at the same depot, keeping the old train visible.
        if(state.order) {
            source.position.x+=source.orientation.E[0][0]*350.f;
            source.position.z+=source.orientation.E[2][0]*350.f;
        }
        Point origin=source;
        unsigned previousWagons=state.wagons;
        std::vector<std::pair<unsigned,size_t>> suppliers;
        for(size_t i=0;i<config.points.size();++i) {
            auto const& p=config.points[i];
            if(p.base==origin.base || p.systemId!=origin.systemId || p.commodities.empty() || !friendly(p))continue;
            for(auto const& r:config.routes)if(r.source==origin.base && r.destination==p.base)
                suppliers.push_back({r.distance,i});
        }
        std::sort(suppliers.begin(),suppliers.end());
        auto tryPickup=[&](Point const& p) {
            source=p;
            // Ordinary depots derive the load from their nearest hub route.
            // At hubs, reduce the load if no route meets its distance/jumps.
            if(!source.freightHub)return choose();
            for(unsigned n=orderWagonLimit(state,config.rules);n>=2;--n) {
                state.wagons=n;
                if(choose())return true;
            }
            return false;
        };
        bool haveOrder=tryPickup(origin);
        // Keep loading here whenever possible. Only a missing local order
        // sends the player to the nearest eligible supplier in this system.
        if(!haveOrder)for(auto const& candidate:suppliers) {
            auto const& p=config.points[candidate.second];
            if(candidate.first>1 && !p.refinery)continue;
            if(tryPickup(p)){haveOrder=true;break;}
        }
        // Actual system stock can be consolidated at the original depot.
        if(!haveOrder)for(auto const& candidate:suppliers) {
            source=origin;
            source.commodities=config.points[candidate.second].commodities;
            source.prices=config.points[candidate.second].prices;
            if(source.freightHub) {
                for(unsigned n=orderWagonLimit(state,config.rules);n>=2 && !haveOrder;--n){state.wagons=n;haveOrder=choose();}
            } else haveOrder=choose();
            if(haveOrder)break;
        }
        if(!haveOrder) {
            source=origin;state.wagons=previousWagons;
            FDUMP(0x100001,"TrainCourier: no eligible route player=%u order=%u source=%s capacity=%u",PlayerId,state.order+1,source.base.c_str(),state.unlockedWagons);
            return false;
        }
        expectedSeconds=config.rules.orderSeconds+config.rules.wagonSeconds*state.wagons;
        describeOrder();
        if(config.commodityVoices.find(commodity)==config.commodityVoices.end())return false;
        rememberBase(state,source.base);rememberBase(state,destination.base);
        state.stage=Stage::Offer;
        pendingObject=objectiveObject=objectiveName=0;markerDelay=0;NnPath.Reset();
        GetOrCreatePlayer(PlayerId)->ClearObjectives();
        remaining=expectedSeconds;
        repositionedOrder=state.order && source.base!=previousBase && config.voice==CreateID("atc_leg_m01_new");
        FDUMP(0x100001,"TrainCourier: order=%u wagons=%u distance=%u source=%s destination=%s trailer=%u reward=%d",state.order+1,state.wagons,state.distance,source.nickname.c_str(),destination.nickname.c_str(),trailer,state.reward);
        return true;
    }
    void advanceOrder() {
        if(state.stage!=Stage::AwaitContinue)return;
        ++state.order;
        if(state.deliveriesAtSize>=2){
            state.unlockedWagons=(std::min)(config.rules.maxWagons,state.unlockedWagons+1);
            state.deliveriesAtSize=0;
        }
        if(!next())parking();
    }
    void showOffer() {
        if(state.stage!=Stage::Offer || state.popup)return;
        FmtStr title;title.begin_mad_lib(config.missionTitle);title.end_mad_lib();
        // Same localized dynamic description as the native mission log.
        state.popup=pub::Player::PopUpDialog(PlayerId,title,Field_0x68,3)==0;
    }
    void onContinue(unsigned answer) {
        // Duplicate replies must never spawn or charge another order.
        if(state.stage!=Stage::Offer || !state.popup)return;
        state.popup=false;
        if(answer==1) {
            if(!friendly(source) || !friendly(destination)){parking();return;}
            state.stage=Stage::Pickup;cargoPending=true;
            if(!createPendingCargo()){parking();return;}
            if(cargoPending)objective(config.pickupFrom,source);
            say(repositionedOrder?"tc_reposition":state.order?"tc_next":"tc_pickup",&destination);
        } else if(answer==2) {
            parking();
            if(state.order==0 && source.systemId==system()) {
                returnImmediately=true;
                // First refusal returns the personal ship at the locomotive.
                Vector pos{};Matrix rotation{};
                if(pub::SpaceObj::GetLocation(ship(),pos,rotation)==0)source.position=pos;
            }
        } else pause=1.f; // Closing is neither YES nor NO; offer again.
    }
    void parking() {
        state.popup=false;state.stage=Stage::Parking;
        unsigned old=trailer;trailer=0;restoreCargo=false;cargoPending=false;jumping=false;
        request(Operation::Register);
        if(old)pub::SpaceObj::Destroy(old,DESTROY_NORMAL);
        selectParking();
    }
    bool selectParking() {
        Vector pos{};Matrix rot{};
        if(pub::SpaceObj::GetLocation(ship(),pos,rot)!=0)return false;
        Point const* chosen=nullptr;unsigned bestDepth=~0u;float nearest=1.e30f;
        for(auto const& point:config.parkingPoints)if(friendly(point)) {
            unsigned depth=point.base==source.base?0:~0u;
            for(auto const& route:config.routes)if(route.source==source.base && route.destination==point.base)
                depth=(std::min)(depth,route.distance);
            if(depth==~0u)continue;
            // Prefer a friendly planet in this system; otherwise follow the
            // reachable trade graph. No station/depot fallback is permitted.
            if(point.systemId==system())depth=0;
            float d=distance(pos,point.position);
            if(depth<bestDepth || (depth==bestDepth && d<nearest)){
                chosen=&point;bestDepth=depth;nearest=d;
            }
        }
        if(!chosen){NnPath.Reset();pause=1;return false;}
        source=*chosen;state.source=source.nickname;
        objective(config.park,source);say("tc_park",&source);return true;
    }
    bool hasParkingPoint() const {
        for(auto const& p:config.parkingPoints)if(p.nickname==source.nickname)return true;
        return false;
    }
    FMissionSolar* solar() {
        for(auto& s:MissionSolars)if(s.Nickname=="tc_boarding")return &s;
        return nullptr;
    }
    void startBoarding() {
        auto* s=solar();if(!s)return;
        auto const* berth=boardingPoint(config,source.baseId);
        if(!berth){OnMissionFail();return;}
        s->SystemId=berth->systemId;s->Position=berth->position;
        s->Faction=berth->faction;
        std::memcpy(&s->Orientation,&berth->orientation,sizeof(Matrix));
        pub::GetBaseID(s->BaseId,berth->transfer.c_str());
        if(!SpawnMissionSolarRecord(s)){OnMissionFail();return;}
        boarding=s->SpaceObjId;transferBase=s->BaseId;
        // SpawnMissionSolarRecord can move an obstructed solar to an empty pose.
        // Capture the actual object, not the authored position in its record.
        if(pub::SpaceObj::GetLocation(boarding,transferPosition,transferOrientation)!=0){OnMissionFail();return;}
        Point marker=source;marker.position=transferPosition;
        objectObjective(config.board,marker,boarding,"tc_boarding");
    }
    void onPlayerLaunch(unsigned base) {
        if(base!=transferBase || (state.stage!=Stage::TransferIn && state.stage!=Stage::TransferOut))return;
        // switcher.ini creates its launch solar on Cnd_PlayerLaunch, when
        // StarSysEnter has restarted physics. Never create one inside BaseEnter:
        // SP has already shut down IVP and cleared the client object database.
        RespawnSolars.clear();
        unsigned anchorSystem=0;
        if(!boarding || pub::SpaceObj::GetSystem(boarding,anchorSystem)!=0 || anchorSystem!=system()) {
            boarding=0;
            auto* s=solar();if(!s)return;
            s->BaseId=transferBase;s->SystemId=system();s->Position=transferPosition;
            std::memcpy(&s->Orientation,&transferOrientation,sizeof(Matrix));
            s->ArchetypeId=CreateID(state.stage==Stage::TransferOut?"tc_parked_locomotive":"spawn_point");
            s->Radius=0;s->bSpawned=0;
            if(!SpawnMissionSolarRecord(s)) {
                FDUMP(0x100001,"TrainCourier: launch solar unavailable player=%u; using prepared space pose",PlayerId);
                return;
            }
            boarding=s->SpaceObjId;
        }
        if(state.stage==Stage::TransferOut) {
            Packet p;p.player=PlayerId;p.operation=Operation::LaunchSolar;p.launchSolar=boarding;
            if(!bridge || !bridge(&p) || p.result!=1)
                FDUMP(0x100001,"TrainCourier: parked launch anchor rejected player=%u solar=%u",PlayerId,boarding);
        }
        FDUMP(0x100001,"TrainCourier: PlayerLaunch player=%u solar=%u",PlayerId,boarding);
    }
    bool prepareTransfer() {
        // Only cache the pose here. Physics and client solar creation belong to
        // PlayerLaunch, after the hidden base has been left.
        Packet p;p.player=PlayerId;p.operation=Operation::Transfer;p.base=transferBase;
        p.system=system();p.position=transferPosition;p.orientation=transferOrientation;
        if(!bridge || !bridge(&p) || p.result!=1) {
            FDUMP(0x100001,"TrainCourier: transfer rejected player=%u base=%u system=%u solar=%u result=%d",
                  PlayerId,p.base,p.system,p.launchSolar,p.result);
            return false;
        }
        transferInSpace=false;
        return true;
    }
    bool onDocked() {
        if(state.stage==Stage::Boarding) {
            EquipDescVector loadout;
            pub::GetLoadout(loadout,CreateID("tc_locomotive"));
            int changed=pub::Player::CacheShipAndSetLoadout(PlayerId,"train_courier_ship",CreateID("ge_train_loco_player"),loadout);
            if(changed!=0){FDUMP(0x100001,"TrainCourier: ship swap failed player=%u result=%d",PlayerId,changed);return false;}
            swapped=true;state.stage=Stage::TransferIn;
        } else if(state.stage==Stage::TransferOut) {
            if(swapped && pub::Player::RestoreCachedShip(PlayerId,"train_courier_ship")!=0)return false;
            swapped=false;
        } else if(state.stage!=Stage::TransferIn || !swapped)return false;
        return prepareTransfer();
    }
    void tick(float dt) {
        if(!ready || !started)return;
        launchObjective();
        advanceClock(dt);
        if(pause>0){pause-=dt;if(pause>0)return;}
        unsigned playerShip=ship();Vector livePos{};Matrix liveRotation{};
        if(!playerShip || pub::SpaceObj::GetLocation(playerShip,livePos,liveRotation)!=0)return;
        updateObjectObjective(dt);
        if(restoreObjective) {
            restoreObjective=false;
            if(state.stage==Stage::Parking)objective(config.park,source);
            else if(state.stage==Stage::Deliver)objective(config.deliver,destination);
            else if(state.stage==Stage::Pickup && cargoPending)objective(config.pickupFrom,source);
            // Pickup/recovery objectives need the restored object, not its old id.
        }
        if(restoreCargo) {
            if(savedCargo.system!=system())return;
            Packet p;p.player=PlayerId;p.operation=Operation::Restore;p.cargo=savedCargo;
            if(!bridge || !bridge(&p) || p.result!=1)return;
            trailer=p.trailer;restoreCargo=false;
            // The generic restore bridge initially uses the yard's name.
            // SP shares the vibe registry; apply the configured cargo name to
            // the restored train before its next client/HUD update.
            int rep=-1;
            if(pub::SpaceObj::GetRep(trailer,rep)==0) {
                FmtStr name,empty;name.begin_mad_lib(config.cargoName);name.end_mad_lib();
                ::Reputation::Vibe::SetName(rep,empty,name,nullptr);
            }
            if(state.stage==Stage::Pickup) {
                Point target=source;target.position=savedCargo.position;target.systemId=savedCargo.system;
                objectObjective(state.pickedUp?config.recover:config.pickupFrom,target,trailer);
            } else objective(config.deliver,destination);
        }
        if(!resumeJump())return;
        if(state.stage==Stage::Boarding) {
            if(system()!=source.systemId){objective(config.board,source);return;}
            Vector pos{};Matrix orientation{};
            if(boarding && pub::SpaceObj::GetLocation(boarding,pos,orientation)!=0)boarding=0;
            if(!boarding)startBoarding();
            updateBoardingComm(dt);
            return;
        }
        if(state.stage==Stage::TransferIn) {
            if(!transferInSpace)return;
            if(boarding){pub::SpaceObj::Destroy(boarding,DESTROY_NORMAL);boarding=0;}
            if(!next())parking();return;
        }
        if(state.stage==Stage::TransferOut && !swapped) {
            if(!transferInSpace)return;
            if(!boarding || query().launchSolar!=boarding) {
                // A failed anchor spawn must not dereference a missing client
                // solar or complete the job. Retry after physics restarts.
                transferInSpace=false;
                if(pub::Player::ForceLand(PlayerId,transferBase)!=0)transferInSpace=true;
                pause=1;return;
            }
            // The server now owns this temporary launch solar. Do not leave a
            // mission record that can respawn it on another base visit.
            if(auto* systemInfo=PlayerState->GetSystemRecord()) {
                auto* objects=systemInfo->GetMissionObjects();
                objects->erase(std::remove(objects->begin(),objects->end(),boarding),objects->end());
                // RemoveMissionObject also frees the reputation: this solar is
                // still alive and must retain its name/rep until server cleanup.
            }
            MissionSolars.clear();RespawnSolars.clear();boarding=0;
            state.stage=failed?Stage::Failed:Stage::Complete;say("tc_done");
            if(failed)OnMissionFail();else OnMissionSucceed();return;
        }
        if(state.stage==Stage::AwaitContinue){advanceOrder();return;}
        if(state.stage==Stage::Offer) {
            if(!continueSpoken) {
                continueSpoken=true;
                if(state.order)say("tc_continue");
            }
            if(!questionComm)showOffer();
            return;
        }
        Packet attached=query();
        if((state.stage==Stage::Pickup || state.stage==Stage::Deliver) && !state.retired) {
            if(!state.pickedUp && !friendly(source)) {
                FDUMP(0x100001,"TrainCourier: source became hostile; cancelling unpaid order player=%u",PlayerId);
                failed=true;parking();return;
            }
            if(!friendly(destination)) {
                if(!choose()){failed=true;parking();return;}
                arrivalSpoken=false;
                if(state.stage==Stage::Deliver)objective(config.deliver,destination);
                say(state.stage==Stage::Deliver?"tc_depart":"tc_next",&destination);
                FDUMP(0x100001,"TrainCourier: hostile destination replaced player=%u destination=%s",PlayerId,destination.base.c_str());
            }
        }
        if(cargoPending && state.stage==Stage::Pickup && system()==source.systemId) {
            if(!createPendingCargo()){failed=true;parking();return;}
            attached=query();
        }
        if(trailer && !jumping) {
            Packet snapshot;snapshot.player=PlayerId;snapshot.operation=Operation::Snapshot;
            if(bridge && bridge(&snapshot) && snapshot.result==1){savedCargo=snapshot.cargo;observeLoss(savedCargo);}
        }
        if(attached.result!=1 || attached.inTransit){uncoupledTime=0;return;}
        if(state.stage==Stage::Pickup && attached.coupled) {
            state.pickedUp=true;state.stage=Stage::Deliver;
            objective(config.deliver,destination);say("tc_depart",&destination);
        }
        if(state.stage==Stage::Deliver && !state.retired) {
            Vector pos{},linear{},angular{};Matrix rotation{};unsigned cargoSystem=0;
            DeliveryObservation observed;
            observed.nonHostileDestination=friendly(destination);
            observed.assignedConsistAlive=pub::SpaceObj::GetLocation(trailer,pos,rotation)==0;
            pub::SpaceObj::GetSystem(trailer,cargoSystem);
            observed.correctSystem=cargoSystem==destination.systemId && system()==cargoSystem;
            observed.coupled=attached.coupled!=0;observed.distance=distance(pos,destination.position);
            if(!arrivalSpoken && observed.assignedConsistAlive && observed.correctSystem && observed.coupled &&
               observed.distance<=config.rules.deliveryRadius) {
                arrivalSpoken=true;say("tc_arrival");
            }
            if(pub::SpaceObj::GetMotion(trailer,linear,angular)!=0)return;
            observed.speed=length(linear);
            if(canDeliver(state,config.rules,observed) && request(Operation::Retire,trailer)) {
                pub::Player::MarkObj(PlayerId,trailer,0);trailer=0;
                state.retired=true;
            } else if(needsRecovery(state,config.rules,observed,attached.inTransit!=0)) {
                uncoupledTime+=dt;
                if(uncoupledTime<.25f)return; // ignore a single transient coupling update
                // pickedUp remains true, so existing saves distinguish a lost
                // consist from the first pickup without changing the save format.
                state.stage=Stage::Pickup;
                Point target=source;target.position=pos;target.systemId=cargoSystem;
                objectObjective(config.recover,target,trailer);
                say("tc_recover");
                FDUMP(0x100001,"TrainCourier: recover order=%u trailer=%u system=%u distance=%.1f speed=%.1f",state.order+1,trailer,cargoSystem,observed.distance,observed.speed);
            } else uncoupledTime=0;
        } else if(state.stage==Stage::Parking && (!hasParkingPoint() || !friendly(source))) {
            selectParking();
        } else if(state.stage==Stage::Parking && system()==source.systemId) {
            Vector pos{},linear{},angular{};Matrix rot{};
            if(pub::SpaceObj::GetLocation(playerShip,pos,rot)!=0 || pub::SpaceObj::GetMotion(playerShip,linear,angular)!=0)return;
            if(!returnImmediately && (distance(pos,source.position)>config.rules.deliveryRadius || length(linear)>config.rules.deliverySpeed))return;
            auto* s=solar();if(!s)return;
            s->Position=pos;std::memcpy(&s->Orientation,&rot,sizeof(Matrix));
            s->SystemId=source.systemId;pub::GetBaseID(s->BaseId,source.transfer.c_str());
            s->Faction=source.faction;
            s->ArchetypeId=CreateID("spawn_point");s->bSpawned=0;s->Radius=0;
            if(!SpawnMissionSolarRecord(s))return;
            // The invisible landing anchor is unloaded normally on BaseEnter.
            // Recreate the visible locomotive only on PlayerLaunch.
            boarding=0;transferBase=s->BaseId;transferPosition=pos;transferOrientation=rot;
            state.stage=Stage::TransferOut;
            if(pub::Player::ForceLand(PlayerId,transferBase)!=0){
                pub::SpaceObj::Destroy(s->SpaceObjId,DESTROY_NORMAL);s->bSpawned=0;state.stage=Stage::Parking;
            }
        }
        if(state.stage==Stage::Deliver && state.retired && !state.paid && pub::Player::AdjustCash(PlayerId,state.reward)==0) {
            if(lostPods<state.wagons*2)state.deliveriesAtSize=(std::min)(2u,state.deliveriesAtSize+1);
            state.paid=true;state.stage=Stage::AwaitContinue;
            NnPath.Reset();
            source=destination;say("tc_paid");pause=6;
            FDUMP(0x100001,"TrainCourier: paid order=%u reward=%d; awaiting continuation",state.order+1,state.reward);
        }
    }
public:
    bool hud(TrainCourierHud* out) const {
        if(!out || out->size!=sizeof(*out) || !ready || bPendingDestroy || !activeOrder())return false;
        out->remaining=remaining;out->caption=remaining>0?config.timerIds:config.overdueIds;
        out->x=config.timerX;out->y=config.timerY;return true;
    }
    bool BuildPathObjectives(FSystemInfo* systemInfo,std::list<FNnPathLeg>* legs,
                             FMissionObjectiveList* list,int firstIds,int legIds,int targetIds,
                             unsigned target,int firstType,int legType,int targetType,
                             std::list<FMissionObjective*>::iterator const* where) override {
        // Directly spawned cargo is not a MissionScript NPC label. Supply its
        // live object id to the same native path builder, which emits rep_inst.
        if(objectiveObject && systemInfo->SystemId==NnPath.SystemId)target=objectiveObject;
        bool changed=FMissionScript::BuildPathObjectives(systemInfo,legs,list,firstIds,legIds,targetIds,
                                                        target,firstType,legType,targetType,where);
        if(changed && objectiveName)for(auto*& entry:list->Objectives)if(entry->GetType()==5) {
            auto* named=new CourierPathObjective(*static_cast<FNNObjectiveType5*>(entry),objectiveName);
            delete entry;entry=named;
        }
        return changed;
    }
    bool prepareBaseTransfer(unsigned base,bool prepare) {
        if(!ready || bPendingDestroy || !transferBase || base!=transferBase ||
           (state.stage!=Stage::Boarding && state.stage!=Stage::TransferIn && state.stage!=Stage::TransferOut))return false;
        if(!prepare)return true;
        unsigned docked=0;pub::Player::GetBase(PlayerId,docked);
        if(docked!=base || !PlayerState->GetBaseRecord() || PlayerState->GetBaseRecord()->BaseId!=base)return false;
        return onDocked();
    }
    CourierMission(unsigned const* id,FStoryMissionCreateParms const* parms):FMissionScript(id,parms) {
        HMODULE server=GetModuleHandleA("Server.dll");
        bridge=server?reinterpret_cast<BridgeFn>(GetProcAddress(server,BridgeExport)):nullptr;
        ready=bridge && config.load();
        if(!ready)return;
        if(!restoreReader) {
            unsigned base=PlayerState && PlayerState->GetBaseRecord()?PlayerState->GetBaseRecord()->BaseId:0;
            ready=boardingPoint(config,base)!=nullptr;if(!ready)return;
            for(auto const& p:config.points)if(p.baseId==base){source=p;break;}
            state.source=source.nickname;
        }
        LoadMissionIni("Missions\\TrainCourier\\objects.ini");
        state.wagons=config.rules.firstWagons;
        unsigned firstWagons=RpgPendingCourierWagons();
        if(!restoreReader && firstWagons) {
            if(firstWagons<2 || firstWagons>config.rules.maxWagons){ready=false;return;}
            state.wagons=firstWagons;
        }
        state.distance=minimumRouteDistance(config.rules,state.wagons);
        state.unlockedWagons=state.wagons;
        Field_0x50.begin_mad_lib(config.missionTitle);Field_0x50.end_mad_lib();Reward=0;
        if(restoreReader)ready=readSave(*restoreReader);
        controllers[PlayerId]=this;
    }
    void prepareReload() {
        ready=false;bDestroyed=1;
        ReleaseRtcScripts();
        while(!Players.empty())RemovePlayer(Players.begin()->second);
        pub::Controller::Destroy(ControllerId);
    }
    ~CourierMission() override {
        // Controller destruction is deferred; GameSupport may already have
        // replaced this player's state by the time base destructors run.
        PlayerState=FindContentPlayerState(PlayerId);
        auto it=controllers.find(PlayerId);if(it!=controllers.end() && it->second==this)controllers.erase(it);
    }
    void HandleMissionMessage(pub::Controller::EMessage msg,void const* data) override {
        using M=pub::Controller::EMessage;
        auto* p=static_cast<unsigned const*>(data);
        if(msg==M::CommComplete && p)completeBoardingComm(p);
        if(msg==M::CommComplete && p && questionComm && p[0]==questionListener && p[2]==0 && p[3]==questionComm)
            questionComm=questionListener=0;
        if(msg==M::PlayerSave && p && p[0]==PlayerId) {
            struct SaveMessage {unsigned player;FILE* file;};
            save(static_cast<SaveMessage const*>(data)->file);return;
        }
        // Native restoration is performed by GameSupport; do not load a retail
        // campaign [MissionState] into this manual controller.
        if(msg==M::PlayerLoad)return;
        if(msg==M::MissionStart) {
            started=true;
            if(!ready || !request(Operation::Register)){OnMissionFail();return;}
        }
        if(msg==M::AbortMission && p && p[0]==PlayerId && swapped){parking();return;}
        if(msg==M::ObjectDestroyed && p && p[0]==trailer && trailer && !jumping) {
            lostPods=state.wagons*2;state.reward=0;describeOrder();
            trailer=0;failed=true;parking();return;
        }
        onJumpDeparture(msg,p);
        onJumpArrival(msg,p);
        if(msg==M::PlayerLaunch && p && p[0]==PlayerId && ready)onPlayerLaunch(p[1]);
        if(msg==M::LaunchComplete && p && p[1]==ship() && state.stage==Stage::Boarding) {
            armBoardingComm();
        }
        // Rep-bound cargo markers follow the actual parked/moving object, not
        // the source depot's cached coordinates. NNPath keeps its own timers.
        if(ready && objectiveObject && NnPath.bActive) {
            unsigned targetSystem=0;Matrix rotation;Vector position;
            if(pub::SpaceObj::GetSystem(objectiveObject,targetSystem)==0 && targetSystem==NnPath.SystemId &&
               pub::SpaceObj::GetLocation(objectiveObject,position,rotation)==0)NnPath.Position=position;
        }
        FMissionScript::HandleMissionMessage(msg,data);
        if(bPendingDestroy || !ready)return;
        if(msg==M::MissionStart)launchObjective();
        else if(msg==M::Heartbeat)tick(*static_cast<float const*>(data));
        else if(msg==M::SpaceEnter && p[1]==PlayerId) {
            // Like switcher.ini's Cnd_InSpace -> Cnd_Timer=1 -> Act_Destroy.
            transferInSpace=true;pause=1.f;
            // A restored free-space save has no launch animation/completion event.
            if(state.stage==Stage::Boarding && (p[2]==0 || p[3]==unsigned(-1))) {
                armBoardingComm();
            }
            if(state.stage==Stage::TransferOut && p[2]!=boarding)boarding=0;
        }
        else if(msg==M::PopUpDialog && p[0]==PlayerId)onContinue(p[1]);
    }
    void EndMission() override {
        request(Operation::Release);
        unsigned old=trailer;trailer=0;
        if(old)pub::SpaceObj::Destroy(old,DESTROY_NORMAL);
        FMissionScript::EndMission();
    }
};
}
IDLL* CreateTrainCourier(char const*,unsigned id,void const* parms) {
    return new CourierMission(&id,static_cast<FStoryMissionCreateParms const*>(parms));
}
bool TrainCourierCanStart(unsigned base) {
    Config config;
    return config.load() && boardingPoint(config,base)!=nullptr;
}
extern "C" int __cdecl TrainCourierBaseTransfer(unsigned player,unsigned base,int prepare) {
    auto found=controllers.find(player);
    return pub::SinglePlayer() && found!=controllers.end() && found->second->prepareBaseTransfer(base,prepare!=0);
}
extern "C" int __cdecl TrainCourierGetHud(unsigned player,TrainCourierHud* out) {
    auto found=controllers.find(player);
    return pub::SinglePlayer() && found!=controllers.end() && found->second->hud(out);
}
void TrainCourierOnPlayerLoad(unsigned player,INI_Reader* reader) {
    auto old=controllers.find(player);
    if(old!=controllers.end()){auto* mission=old->second;controllers.erase(old);mission->prepareReload();}
    if(!reader)return;
    reader->reset();bool exists=false;
    while(reader->read_header())if(reader->is_header("TrainCourierSave")){exists=true;break;}
    reader->reset();if(!exists)return;
    auto* state=FindContentPlayerState(player);if(!state)return;
    FStoryMissionCreateParms parms;parms.PlayerId=player;parms.StoryEvents=nullptr;
    restoreReader=reader;
    unsigned id=pub::Controller::Create("content.dll","TrainCourier",&parms,pub::Controller::ABOVE_NORMAL);
    restoreReader=nullptr;
    if(!id)return;
    ID_String noNpc;noNpc.clear();
    unsigned base=state->GetBaseRecord()?state->GetBaseRecord()->BaseId:0;
    state->JoinMissionAsGroup(id,base,&noNpc,false,0);
    pub::Controller::_SendMessage(id,pub::Controller::EMessage::MissionStart,nullptr);
}
#else
bool TrainCourierCanStart(unsigned) {return false;}
extern "C" int __cdecl TrainCourierGetHud(unsigned,TrainCourierHud*) {return 0;}
extern "C" int __cdecl TrainCourierBaseTransfer(unsigned,unsigned,int) {return 0;}
IDLL* CreateTrainCourier(char const*,unsigned,void const*) {return nullptr;}
void TrainCourierOnPlayerLoad(unsigned,INI_Reader*) {}
#endif
