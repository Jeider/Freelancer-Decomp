#pragma once
#include <cmath>
#include <cstddef>
#include <cstring>

// Append-only identifiers. Values are cumulative, finite and nonnegative.
// C = measured by the local pilot; S = confirmed by the server.
#define PLAYER_ACTION_STATS(X) \
 X(FlightSeconds, flight_seconds, C) \
 X(ManualSeconds, manual_flight_seconds, C) \
 X(Distance, distance_flown, C) \
 X(InertiaSeconds, inertia_seconds, C) \
 X(InertiaDistance, inertia_distance, C) \
 X(BoostSeconds, boost_seconds, C) \
 X(InertiaBoostSeconds, inertia_boost_seconds, C) \
 X(ReverseSeconds, reverse_seconds, C) \
 X(StrafeSeconds, strafe_seconds, C) \
 X(AimedStrafeSeconds, aimed_strafe_seconds, C) \
 X(TargetTrackingSeconds, target_tracking_seconds, C) \
 X(CruiseSeconds, cruise_seconds, C) \
 X(TradelaneSeconds, tradelane_seconds, C) \
 X(AutopilotSeconds, autopilot_seconds, C) \
 X(CockpitSeconds, cockpit_seconds, C) \
 X(EngineKills, engine_kill_entries, C) \
 X(BoostActivations, boost_activations, C) \
 X(StrafeChanges, strafe_changes, C) \
 X(TargetSwitches, target_switches, C) \
 X(SubtargetSelections, subtarget_selections, C) \
 X(InertiaTurnarounds, inertia_turnarounds, C) \
 X(ThrustDepletions, thrust_depletions, C) \
 X(ManualShots, manual_launcher_shots, C) \
 X(AutoShots, auto_turret_shots, C) \
 X(Missiles, missiles_fired, C) \
 X(Mines, mines_deployed, C) \
 X(Countermeasures, countermeasures_deployed, C) \
 X(ReverseShots, reverse_shots, C) \
 X(StrafeShots, strafe_shots, C) \
 X(InertiaShots, inertia_shots, C) \
 X(CombatSeconds, combat_seconds, C) \
 X(CombatInertiaSeconds, combat_inertia_seconds, C) \
 X(CombatSessions, combat_sessions, C) \
 X(CombatSurvived, combat_sessions_survived, C) \
 X(CombatNoRepair, combat_survived_without_repairs, C) \
 X(CombatNoDamage, combat_survived_without_damage, C) \
 X(CombatNoThrustEmpty, combat_survived_without_empty_thrust, C) \
 X(CriticalSurvivals, critical_hull_survivals, C) \
 X(ProjectileHits, projectile_contacts_dealt, C) \
 X(ProjectileHitsReceived, projectile_contacts_received, C) \
 X(Collisions, physical_contacts, C) \
 X(ClosePasses, close_projectile_passes, C) \
 X(MissilesEvaded, guided_missiles_evaded, C) \
 X(PursuitSeconds, pursuing_target_seconds, C) \
 X(EscapeSeconds, escaping_target_seconds, C) \
 X(EnemyWeaponsDisabled, enemy_weapons_destroyed, S) \
 X(DamageDealtEvents, damage_reports_dealt, S) \
 X(DamageReceivedEvents, damage_reports_received, S) \
 X(Kills, credited_kills, S) \
 X(Deaths, player_deaths, S) \
 X(Nanobots, nanobots_used, S) \
 X(Batteries, shield_batteries_used, S) \
 X(LootObjects, loot_pickups, S) \
 X(LootUnits, loot_units_collected, S) \
 X(JettisonUnits, cargo_units_jettisoned, S) \
 X(Landings, landings, S) \
 X(Launches, launches, S) \
 X(SystemEntries, system_entries, S) \
 X(Discoveries, newly_visited_objects, S) \
 X(SystemsDiscovered, newly_visited_systems, S) \
 X(BasesDiscovered, newly_visited_bases, S) \
 X(BuyTransactions, confirmed_buy_transactions, S) \
 X(SellTransactions, confirmed_sell_transactions, S) \
 X(UnitsBought, units_bought, S) \
 X(UnitsSold, units_sold, S) \
 X(CreditsSpent, trade_credits_spent, S) \
 X(CreditsReceived, trade_credits_received, S) \
 X(MissionsSucceeded, missions_succeeded, S) \
 X(MissionsFailed, missions_failed, S) \
 X(AllyAttackersDestroyed, attackers_of_allies_destroyed, S)

namespace PlayerActionStats {
enum class Counter {
#define STAT_ENUM(id, name, owner) id,
    PLAYER_ACTION_STATS(STAT_ENUM)
#undef STAT_ENUM
    Count
};
constexpr size_t Count = static_cast<size_t>(Counter::Count);
inline char const* Name(Counter key) {
    static char const* const names[] = {
#define STAT_NAME(id, name, owner) #name,
        PLAYER_ACTION_STATS(STAT_NAME)
#undef STAT_NAME
    };
    return names[static_cast<size_t>(key)];
}
inline bool ClientOwned(Counter key) {
    constexpr bool C = true, S = false;
    static bool const owners[] = {
#define STAT_OWNER(id, name, owner) owner,
        PLAYER_ACTION_STATS(STAT_OWNER)
#undef STAT_OWNER
    };
    return owners[static_cast<size_t>(key)];
}
constexpr double Limit = 1.e15;
struct State {
    double values[Count] = {};
    double Get(Counter key) const { return values[static_cast<size_t>(key)]; }
    bool Set(Counter key, double value) {
        if (!std::isfinite(value) || value < 0 || value > Limit) return false;
        values[static_cast<size_t>(key)] = value; return true;
    }
    void Add(Counter key, double amount = 1) {
        if (std::isfinite(amount) && amount > 0) {
            double total = Get(key) + amount;
            Set(key, total < Limit ? total : Limit);
        }
    }
    bool Load(char const* name, double value) {
        for (size_t i=0; i<Count; ++i) if (std::strcmp(name,Name(static_cast<Counter>(i)))==0)
            return Set(static_cast<Counter>(i),value);
        return false;
    }
};

// SP in-process bridge, deliberately independent of debug console settings and
// of retail RPC layouts. No STL ownership crosses the DLL boundary.
constexpr unsigned BridgeVersion = 1;
struct Bridge {
    unsigned size = sizeof(Bridge), version = BridgeVersion, player = 1, operation = 0;
    unsigned long long epoch = 0;
    State state;
};
using BridgeFn = int(__cdecl*)(Bridge*);
constexpr char BridgeExport[] = "PlayerActionStatsBridge";

struct V { double x=0,y=0,z=0; };
inline double Dot(V a,V b) {return a.x*b.x+a.y*b.y+a.z*b.z;}
inline double Length(V a) {return std::sqrt(Dot(a,a));}
struct Flight {
    double dt=0;
    bool valid=false, manual=false, engine=true, boost=false, cruise=false, lane=false, cockpit=false;
    bool targetHostile=false, targetingUs=false, critical=false;
    int strafe=0;
    unsigned target=0, subtarget=0;
    double thrust=1, distance=0, closing=0, aimDot=-1;
    V velocity, forward;
};
struct Tracker {
    bool havePrevious=false, wasInertia=false, wasBoost=false, wasEmpty=false;
    int lastStrafe=0;
    unsigned target=0, subtarget=0;
    V inertiaForward;
    bool turnArmed=false;
    bool combat=false, repaired=false, damaged=false, emptied=false, critical=false;
    double quiet=0;
    bool inertia=false, reverse=false, strafing=false;
    void Break() { havePrevious=false; turnArmed=false; inertia=reverse=strafing=false; }
    void Reset() { *this=Tracker(); }
    void Combat(State& state) {
        if (!combat) {combat=true;repaired=damaged=emptied=critical=false;state.Add(Counter::CombatSessions);}
        quiet=0;
    }
    void Step(State& state, Flight const& f) {
        if (!f.valid || !std::isfinite(f.dt) || f.dt<=0 || f.dt>1) {Break();return;}
        double speed=Length(f.velocity);
        if (!std::isfinite(speed)) {Break();return;}
        state.Add(Counter::FlightSeconds,f.dt);
        state.Add(Counter::Distance,speed*f.dt);
        if (f.cockpit) state.Add(Counter::CockpitSeconds,f.dt);
        if (f.cruise) state.Add(Counter::CruiseSeconds,f.dt);
        if (f.lane) state.Add(Counter::TradelaneSeconds,f.dt);
        if (!f.manual) {state.Add(Counter::AutopilotSeconds,f.dt);Break();return;}
        state.Add(Counter::ManualSeconds,f.dt);
        inertia=!f.engine && speed>=1 && !f.cruise && !f.lane;
        reverse=speed>=1 && Dot(f.velocity,f.forward)<-1;
        strafing=f.strafe!=0;
        if (inertia) {state.Add(Counter::InertiaSeconds,f.dt);state.Add(Counter::InertiaDistance,speed*f.dt);}
        if (f.boost) state.Add(Counter::BoostSeconds,f.dt);
        if (inertia && f.boost) state.Add(Counter::InertiaBoostSeconds,f.dt);
        if (reverse) state.Add(Counter::ReverseSeconds,f.dt);
        if (strafing) state.Add(Counter::StrafeSeconds,f.dt);
        bool aimed=f.targetHostile && f.aimDot>=0.965925826 && f.distance<=2500;
        if (aimed) state.Add(Counter::TargetTrackingSeconds,f.dt);
        if (aimed && strafing) state.Add(Counter::AimedStrafeSeconds,f.dt);
        if (f.targetHostile && f.distance<=5000) {
            if (f.closing>10) state.Add(Counter::PursuitSeconds,f.dt);
            if (f.targetingUs && f.closing<-10) state.Add(Counter::EscapeSeconds,f.dt);
        }
        bool empty=std::isfinite(f.thrust) && f.thrust<=0.001;
        if (havePrevious) {
            if (inertia && !wasInertia) state.Add(Counter::EngineKills);
            if (f.boost && !wasBoost) state.Add(Counter::BoostActivations);
            if (f.strafe && f.strafe!=lastStrafe) state.Add(Counter::StrafeChanges);
            if (f.target && f.target!=target) state.Add(Counter::TargetSwitches);
            if (f.target && f.subtarget && (f.target!=target || f.subtarget!=subtarget)) state.Add(Counter::SubtargetSelections);
            if (empty && !wasEmpty) state.Add(Counter::ThrustDepletions);
        }
        if (inertia && !turnArmed) {inertiaForward=f.forward;turnArmed=true;}
        if (!inertia) turnArmed=false;
        if (inertia && turnArmed && Dot(inertiaForward,f.forward)<-0.866025404 &&
            Dot(inertiaForward,f.velocity)>speed*0.5) {
            state.Add(Counter::InertiaTurnarounds);inertiaForward=f.forward;
        }
        if (combat) {
            state.Add(Counter::CombatSeconds,f.dt);
            if (inertia) state.Add(Counter::CombatInertiaSeconds,f.dt);
            emptied|=empty;critical|=f.critical;
            if (f.targetHostile && f.distance<2500) quiet=0; else quiet+=f.dt;
            if (quiet>=15) {
                state.Add(Counter::CombatSurvived);
                if(!repaired)state.Add(Counter::CombatNoRepair);
                if(!damaged)state.Add(Counter::CombatNoDamage);
                if(!emptied)state.Add(Counter::CombatNoThrustEmpty);
                if(critical)state.Add(Counter::CriticalSurvivals);
                combat=false;
            }
        }
        havePrevious=true;wasInertia=inertia;wasBoost=f.boost;wasEmpty=empty;
        lastStrafe=f.strafe;target=f.target;subtarget=f.subtarget;
    }
};
}
