#pragma once
#include <cmath>

// Private SP interface; Content owns the durable job and reputation decisions.
namespace TrainEvacuation {
enum class Phase : unsigned { Onboard, Leaving, Away, Returning, Emergency, Closed };
enum class Command : unsigned { Query, Confirm, Critical };
enum RepEvent : unsigned { Late=0, CargoLost=1, LocomotiveLost=2, EventCount=3 };
inline char const* eventName(unsigned event) {
    static char const* const names[]={"train_delivery_late",
        "train_cargo_loss", "train_locomotive_loss"};
    return event<EventCount?names[event]:"";
}
struct State {
    Phase phase=Phase::Onboard;
    float remaining=0;
    unsigned orderEvents=0;
    bool locomotiveLost=false, warned30=false, warned10=false;
    bool valid() const {
        return unsigned(phase)<=unsigned(Phase::Closed) && std::isfinite(remaining) &&
            remaining>=0 && remaining<=60 && !(orderEvents&~3u);
    }
    bool once(RepEvent event) {
        if(event>=EventCount)return false;
        if(event==LocomotiveLost) {
            if(locomotiveLost)return false;
            locomotiveLost=true;return true;
        }
        unsigned bit=1u<<unsigned(event);
        if(orderEvents&bit)return false;
        if(event==Late && (orderEvents&(1u<<CargoLost)))return false;
        orderEvents|=bit;return true;
    }
    void left() {phase=Phase::Away;remaining=60;warned30=warned10=false;}
    bool tick(float dt) {
        if((phase!=Phase::Away && phase!=Phase::Returning) || !std::isfinite(dt) || dt<=0)return false;
        remaining=remaining>dt?remaining-dt:0;return remaining==0;
    }
    bool canReturn() const {return phase==Phase::Away && remaining>0 && !locomotiveLost;}
};
struct Status {
    unsigned size=sizeof(Status),version=1;
    unsigned ship=0;
    unsigned phase=0;
    int available=0;
};
using Bridge=int (__cdecl*)(unsigned,Command,Status*);
constexpr char Export[]="TrainCourierEvacuation";

// Reserved strings in the courier resource DLLs, identical across RU and EN.
enum Text : unsigned {
    Title=239300, ConfirmLoaded, ConfirmEmpty, ReturnObjective, ReturnTimer,
    Employer, Reputation, DeliveredText, LateText, CargoLostText, LocomotiveLostText,
    EvacuatedText, Warning30, Warning10, ReturnedText, TimeoutLoaded, TimeoutEmpty,
    CriticalText, BattleLoaded, BattleEmpty, AccessDenied, TransferFailed, Waiting,
    LateDelivered, Cancelled, ReturnFailed, RateText, Plus, Minus, OrderWithEmployer
};
}
