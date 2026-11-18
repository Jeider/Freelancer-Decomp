#pragma once
#include <cstdio>

// Event order, rather than a single numeric priority, determines obsolescence.
// Rescue, safe separation and loss are consecutive reports and must all survive.
namespace TrainEvacuationAudio {
enum Kind { Other, Courier, Intro, Confirm, Cancel, Waiting, ExitFailed, Departed,
    Warning30, Warning10, Returned, ReturnFailed, Timeout, Denied, Critical,
    Clear, Battle, Late, Delivered, Abandoned, CargoLost };
struct Family { char const* name; Kind kind; };
static Family const families[] = {
    {"te_intro",Intro}, {"te_confirm_loaded",Confirm}, {"te_confirm_empty",Confirm},
    {"te_cancel",Cancel}, {"te_waiting",Waiting}, {"te_exit_failed",ExitFailed},
    {"te_departed",Departed}, {"te_return_30",Warning30}, {"te_return_10",Warning10},
    {"te_return_loaded",Returned}, {"te_return_empty",Returned},
    {"te_return_failed",ReturnFailed}, {"te_timeout_loaded",Timeout},
    {"te_timeout_empty",Timeout}, {"te_access_denied",Denied}, {"te_critical",Critical},
    {"te_emergency_clear",Clear}, {"te_battle_loaded",Battle}, {"te_battle_empty",Battle},
    {"te_late",Late}, {"te_delivered",Delivered}, {"te_delivered_late",Delivered},
    {"te_order_abandoned",Abandoned}, {"te_cargo_destroyed",CargoLost},
    {"tc_board",Courier}, {"tc_order",Courier}, {"tc_destination",Courier},
    {"tc_collect",Courier}, {"tc_depart",Courier}, {"tc_arrival",Courier},
    {"tc_paid",Courier}, {"tc_continue",Courier}, {"tc_recover",Courier},
    {"tc_park",Courier}, {"tc_done",Courier}, {"tc_reposition",Courier},
    {"tc_reposition_empty",Courier}
};
template<class Hash> Kind classify(unsigned id, Hash hash) {
    struct Cache {
        unsigned ids[sizeof(families)/sizeof(*families)][20]{};
        Cache(Hash hash) {
            for(unsigned f=0; f<sizeof(families)/sizeof(*families); ++f)
                for(unsigned v=0; v<20; ++v) {
                    char name[80];
                    std::snprintf(name,sizeof(name),"%s_%02u%c",families[f].name,v/2+1,v%2?'+':'-');
                    ids[f][v]=hash(name);
                }
        }
    };
    static Cache const cache(hash);
    for(unsigned f=0; f<sizeof(families)/sizeof(*families); ++f)
        for(unsigned v=0; v<(families[f].kind==Courier?20u:10u); ++v)
            if(cache.ids[f][v]==id)return families[f].kind;
    return Other;
}
inline bool transient(Kind k) {
    return k>=Intro && k<=ReturnFailed;
}
inline bool supersedes(Kind next, Kind old) {
    if(next<=Courier || old==Other)return false;
    if(next==Intro)return old==Courier;
    if(next==Critical)return old!=Critical && old!=Clear && old!=Battle;
    if(next==Clear || next==Battle)
        return old!=Critical && old!=Clear && old!=Battle;
    if(next==Timeout)return old!=Timeout;
    if(next==Returned || next==Departed || next==ExitFailed || next==ReturnFailed)
        return transient(old) || old==Courier;
    if(next==Warning10)return transient(old) || old==Courier || old==Late;
    if(next==Warning30)return old==Intro || old==Departed || old==ReturnFailed || old==Courier || old==Late;
    if(next==Confirm || next==Cancel || next==Waiting)
        return old==Intro || old==Confirm || old==Cancel || old==Waiting || old==ExitFailed;
    if(next==Denied)return transient(old);
    if(next==Delivered || next==Abandoned || next==CargoLost)
        return old==Intro || old==Late;
    return false;
}
}
