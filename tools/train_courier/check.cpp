#include "train_courier_state.h"
#include <cstdlib>
#include <cstdio>
#include <limits>
using namespace TrainCourier;
void need(bool value,char const* message) {
    if(!value){std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}
}
int main() {
    Rules rules;
    State state;state.stage=Stage::Deliver;state.pickedUp=true;
    DeliveryObservation observed{true,true,true,100,0};
    need(!canDeliver(state,rules,observed),"arrival with coupled cargo cannot pay or open popup");
    observed.coupled=false;
    need(canDeliver(state,rules,observed),"parked assigned consist can be handed over after uncoupling");
    observed.nonHostileDestination=false;
    need(!canDeliver(state,rules,observed),"hostile destination cannot accept cargo or pay");
    observed.nonHostileDestination=true;
    observed.distance=251;
    need(!canDeliver(state,rules,observed),"detaching outside the depot is not a delivery");
    need(needsRecovery(state,rules,observed,false),"detached cargo outside depot needs recovery");
    need(!needsRecovery(state,rules,observed,true),"jump transfer must not announce cargo lost");
    observed.coupled=true;
    need(!needsRecovery(state,rules,observed,false),"attached cargo keeps its delivery objective");
    observed.coupled=false;observed.distance=250;observed.speed=8;
    need(!needsRecovery(state,rules,observed,false),"cargo settling inside depot must not demand recoupling");
    observed.speed=0;
    observed.distance=100;observed.correctSystem=false;
    need(!canDeliver(state,rules,observed),"same coordinates in another system are not the destination");
    need(needsRecovery(state,rules,observed,false),"uncoupled cargo in wrong system needs recovery");
    observed.correctSystem=true;observed.assignedConsistAlive=false;
    need(!canDeliver(state,rules,observed),"destroyed cargo cannot be delivered");
    need(!needsRecovery(state,rules,observed,false),"destroyed cargo must not get a recovery waypoint");
    observed.assignedConsistAlive=true;observed.speed=3;
    need(!canDeliver(state,rules,observed),"moving cargo is not parked");
    observed.speed=0;state.retired=true;
    need(!canDeliver(state,rules,observed),"duplicate delivery callback is rejected");
    need(!needsRecovery(state,rules,observed,false),"retired cargo must not get a recovery order");
    state.retired=false;state.paid=true;
    need(!state.valid(rules),"payment cannot precede handover");
    state.retired=true;state.popup=true;
    need(state.valid(rules),"popup permitted after handover and payment");
    need(!cleanupRetired(1,1,24999,rules),"delivered consist remains visible nearby");
    need(!cleanupRetired(1,1,25000,rules),"threshold is strictly beyond 25 km");
    need(cleanupRetired(1,1,25001,rules),"delivered consist removed beyond 25 km");
    need(cleanupRetired(1,2,0,rules),"system change clears delivered consist regardless of coordinates");
    need(!cleanupRetired(1,0,999999,rules),"transitional zero system does not mean completed system change");
    float nan=std::numeric_limits<float>::quiet_NaN();
    need(!cleanupRetired(1,1,nan,rules),"invalid position cannot delete a visible consist");
    need(cleanupRetired(1,2,nan,rules),"confirmed system change needs no valid distance");
    std::vector<Route> routes={{"a","b",1},{"a","c",2},{"a","d",2},{"b","c",1}};
    need(candidates(routes,"a",2,{"c"})==std::vector<size_t>{1},"graph depth and destination eligibility both apply");
    need(candidates(routes,"a",3,{"b","c","d"}).empty(),"no invented fallback route if graph depth exhausted");
    need(rewardFor(rules,3,2)>rewardFor(rules,2,1),"longer assignments increase reward");
    std::puts("PASS: delivery ordering, retired cleanup, graph selection and reward rules");
}
