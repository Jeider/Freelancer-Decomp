#pragma once

// Port-only courier rules, shared by the native controller and its deterministic
// checks. Runtime object IDs are deliberately kept out of the durable state.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

namespace TrainCourier {
enum class Stage : unsigned {
    Boarding, TransferIn, Pickup, Deliver, AwaitContinue, Parking, TransferOut, Complete, Failed, Offer
};
struct Rules {
    unsigned firstWagons=2, maxWagons=20, firstDistance=1, distanceStep=1;
    unsigned wagonsPerJump=5;
    unsigned shortLoadPercent=50;
    int baseReward=2000, perWagonReward=500, perDistanceReward=1000;
    float deliveryRadius=250.f, deliverySpeed=2.f, cleanupDistance=25000.f;
    int perWagonDistanceReward=150;
    double cargoValueRate=.01, lossValueRate=.05;
    float orderSeconds=300.f, wagonSeconds=180.f;
    bool valid() const {
        return firstWagons>=2 && firstWagons<=maxWagons && maxWagons<=20 &&
            firstDistance>=1 && distanceStep>=1 && wagonsPerJump>=2 && wagonsPerJump<=20 &&
            shortLoadPercent>=1 && shortLoadPercent<=100 && baseReward>=0 &&
            perWagonReward>=0 && perDistanceReward>=0 && perWagonDistanceReward>=0 &&
            std::isfinite(cargoValueRate) && cargoValueRate>=0 && cargoValueRate<=1 &&
            std::isfinite(lossValueRate) && lossValueRate>=0 && lossValueRate<=1 &&
            std::isfinite(orderSeconds) && orderSeconds>=0 && orderSeconds<=86400 &&
            std::isfinite(wagonSeconds) && wagonSeconds>=0 && wagonSeconds<=86400 &&
            std::isfinite(deliveryRadius) && deliveryRadius>0 &&
            std::isfinite(deliverySpeed) && deliverySpeed>=0 &&
            std::isfinite(cleanupDistance) && cleanupDistance>deliveryRadius;
    }
};
struct State {
    Stage stage=Stage::Boarding;
    unsigned order=0, wagons=2, distance=1;
    unsigned unlockedWagons=2;
    unsigned deliveriesAtSize=0;
    std::string source, destination;
    std::vector<std::string> recentBases;
    bool pickedUp=false, retired=false, paid=false, popup=false;
    int reward=0;
    bool valid(Rules const& rules) const {
        return static_cast<unsigned>(stage)<=static_cast<unsigned>(Stage::Offer) &&
            wagons>=2 && wagons<=unlockedWagons && unlockedWagons<=rules.maxWagons && deliveriesAtSize<=2 && recentBases.size()<=4 && distance>=1 && reward>=0 &&
            (!paid || retired) && (!retired || pickedUp) && (!popup || paid || stage==Stage::Offer);
    }
};
inline unsigned orderWagonLimit(State const& state,Rules const& rules) {
    return state.order%2 ? (std::max)(2u,state.unlockedWagons*rules.shortLoadPercent/100) : state.unlockedWagons;
}
inline void rememberBase(State& state,std::string const& base) {
    if(base.empty())return;
    auto& recent=state.recentBases;
    recent.erase(std::remove(recent.begin(),recent.end(),base),recent.end());
    recent.push_back(base);
    if(recent.size()>4)recent.erase(recent.begin());
}
inline unsigned revisitPenalty(State const& state,std::string const& base) {
    auto it=std::find(state.recentBases.begin(),state.recentBases.end(),base);
    return it==state.recentBases.end()?0u:unsigned(it-state.recentBases.begin())+1;
}
struct DeliveryObservation {
    bool correctSystem=false, assignedConsistAlive=false, coupled=false;
    float distance=0, speed=0;
    bool nonHostileDestination=true;
};
inline bool canDeliver(State const& state, Rules const& rules, DeliveryObservation const& o) {
    return state.stage==Stage::Deliver && state.pickedUp && !state.retired &&
        o.nonHostileDestination && o.correctSystem && o.assignedConsistAlive && !o.coupled &&
        std::isfinite(o.distance) && o.distance<=rules.deliveryRadius && o.distance>=0 &&
        std::isfinite(o.speed) && o.speed<=rules.deliverySpeed && o.speed>=0;
}
inline bool needsRecovery(State const& state, Rules const& rules, DeliveryObservation const& o, bool inTransit) {
    // Uncoupling inside the depot is intentional, even while the wagons are
    // settling. Jump transport temporarily uncouples the consist as well.
    return state.stage==Stage::Deliver && state.pickedUp && !state.retired &&
        o.assignedConsistAlive && !o.coupled && !inTransit &&
        std::isfinite(o.distance) && o.distance>=0 &&
        (!o.correctSystem || o.distance>rules.deliveryRadius);
}
inline bool cleanupRetired(unsigned wagonSystem,unsigned playerSystem,float distance,Rules const& rules) {
    return playerSystem!=0 && (wagonSystem!=playerSystem ||
        (std::isfinite(distance) && distance>rules.cleanupDistance));
}
inline int rewardFor(Rules const& rules,unsigned wagons,unsigned distance) {
    const std::int64_t value=rules.baseReward+std::int64_t(rules.perWagonReward)*wagons+
        std::int64_t(rules.perDistanceReward)*distance;
    return static_cast<int>((std::min)(value,std::int64_t(2000000000)));
}
inline unsigned minimumRouteDistance(Rules const& rules,unsigned wagons) {
    return rules.firstDistance+(wagons>2?wagons-2:0)*rules.distanceStep;
}
inline unsigned minimumRouteJumps(Rules const& rules,unsigned wagons) {
    return wagons/rules.wagonsPerJump;
}
inline unsigned feederWagons(Rules const& rules,unsigned unlocked,unsigned distance,unsigned jumps) {
    if(distance<rules.firstDistance)return 0;
    unsigned byDistance=2+(distance-rules.firstDistance)/rules.distanceStep;
    unsigned byJumps=(jumps+1)*rules.wagonsPerJump-1;
    // Full 20-car loading belongs exclusively to a marked freight hub.
    return (std::min)({unlocked,19u,byDistance,byJumps});
}
inline int freightQuote(Rules const& r,unsigned wagons,unsigned depth,int unitPrice) {
    double value=rewardFor(r,wagons,depth)+double(r.perWagonDistanceReward)*wagons*depth+
        double((std::max)(1,unitPrice))*wagons*100*r.cargoValueRate;
    return static_cast<int>((std::min)(2000000000.,std::round(value)));
}
inline int podLossCharge(Rules const& r,unsigned wagons,int quote,int unitPrice) {
    return static_cast<int>((std::min)(2000000000.,std::ceil(double(quote)/(wagons*2))+
        std::round(double((std::max)(1,unitPrice))*50*r.lossValueRate)));
}
inline int freightPayment(int quote,unsigned lost,int perPod) {
    return static_cast<int>((std::max)(std::int64_t(0),std::int64_t(quote)-std::int64_t(lost)*perPod));
}
// Each authored TradeConnection and each jumpgate crossing costs one edge.
struct Route {std::string source,destination;unsigned distance=0,jumps=0;};
inline std::vector<size_t> candidates(std::vector<Route> const& routes,std::string const& source,
                                    unsigned distance,std::vector<std::string> const& eligible) {
    std::vector<size_t> out;
    for(size_t i=0;i<routes.size();++i) {
        auto const& r=routes[i];
        if(r.source==source && r.destination!=source && r.distance==distance &&
           std::find(eligible.begin(),eligible.end(),r.destination)!=eligible.end())out.push_back(i);
    }
    return out;
}
}
