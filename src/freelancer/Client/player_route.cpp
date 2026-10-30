#include "player_route.h"
#include "navigation_settings.h"
#ifdef FREELANCER_PLAYER_FLIGHT_ACTIONS
#include "route_planner.h"
#include "player_flight_actions.h"
#include "player_behavior.h"
#include "player_spawn.h"
#include "character_select_equip.h"
#include "hud_maneuvers.h"
#include "hud_waypoint.h"
#include "hud_target.h"
#include "client_objdb.h"
#include "common_gotobehavior.h"
#include "common_server.h"
#include "common_pub.h"
#include "globals.h"
#include "login_mgr.h"
#include "space_letterbox.h"
#include "nn_messaging.h"
#include "nn_arrival_text.h"
#include "port_config.h"
#include "best_path.h"
#include "cockpit_free_look.h"
#include "input_manager.h"
#include "win3d.h"
#include "hud_status_core.h"
#include <deque>
#include <cstring>

namespace PlayerRoute {
namespace {
using namespace RouteGeometry;
V v(Vector const& p) { return {p.x,p.y,p.z}; }
Vector vec(V p) { return {p.x,p.y,p.z}; }
struct Node { FPlayerWaypointRecord point; bool user=false; bool dock=false; bool laneExit=false; };
enum class State { Off,Flying,Docking,Lane,Jump };
State state=State::Off;
std::deque<Node> route;
std::deque<V> leg;
BaseWatcher owner;
unsigned connection=0,system=0,jumpSystem=0,exitGate=0;
bool internal=false,refining=false;
bool issued=false;
bool cruiseRequested=true;
bool mouseOverride=false,replanAfterMouse=false;
bool haveGoal=false,rebuildOnStart=false,pendingStart=false,receivingPath=false;
FPlayerWaypointRecord savedGoal{};
unsigned goalConnection=0;
V previous;
float elapsed=0,stalled=0,bestDistance=0;
struct Guard { bool old=internal; Guard(){internal=true;} ~Guard(){internal=old;} };
IObjRW* player() { return static_cast<IObjRW*>(GetPlayerObjRW()); }
CShip* ship() { return player()?HudShipOfObjRw(player()):nullptr; }
IBehaviorManager* manager() { auto s=ship(); return s?s->get_behavior_interface():nullptr; }
IObjRW* object(unsigned id) { return id?GetClientObjDb()->FindById(&id):nullptr; }
unsigned typeOf(IObjRW* p) { unsigned t=0; if(p) p->get_type(t); return t; }
int selectedRouteIndex(IObjRW* target) {
    if(!target) return -1;
    auto waypoint=GetHudWaypoint();
    // Free-space waypoints have ObjectId=0. Their spawned HUD solar has a
    // different id; match the persistent AutoId, never a stale list index.
    bool userPoint=waypoint && waypoint->bUser && waypoint->GetWaypointObject()==target;
    for(int i=0;i<GetPlayerWaypointCountRetail();++i) {
        auto point=GetPlayerWaypointRetail(i);
        if((point->ObjectId && point->ObjectId==target->get_id()) ||
           (userPoint && point->AutoId==waypoint->Id)) return i;
    }
    return -1;
}
bool rebuildRoute(bool useRoute) {
    if(!useRoute || !haveGoal || !rebuildOnStart || goalConnection!=GetPlayerConnectionId()) return false;
    rebuildOnStart=false; pendingStart=true;
    Guard guard;
    // Ask for fresh topology and local detours from HERE, retaining only the
    // final destination. Do not feed old generated waypoints back as goals.
    RequestBestPathRetail(player()->get_position(),savedGoal.Pos,savedGoal.ObjectId,savedGoal.SystemId);
    return true;
}
float dockingRange(unsigned id) {
    float range=PortConfigFloat("Navigation","dock_distance",2000);
    range=std::isfinite(range)?std::clamp(range,750.f,5000.f):2000.f;
    if(auto target=object(id)) {
        float radius=0; Vector center; target->get_physical_radius(radius,center);
        range=(std::max)(range,radius+1000.f);
    }
    return range;
}
IDirectiveInfo directive(int id) {
    IDirectiveInfo info{}; unsigned words[3]={1,0,static_cast<unsigned>(id)};
    std::memcpy(info.Data,words,sizeof(words)); return info;
}
void notify(unsigned target,int behavior) {
    if(!target || !player()) return;
    XSetManeuver packet{};
    packet.Field_0x00=player()->get_id(); packet.ObjectId=target; packet.Field_0x08=behavior;
    G_Server->SetManeuver(GetPlayerConnectionId(),packet);
}
// A selected planet names a base; approach the corresponding docking ring,
// never the planet centre. Dock itself still uses its standard request protocol.
IObjRW* dockingObject(IObjRW* target) {
    if(!target) return nullptr;
    unsigned type=typeOf(target);
    if((type&0x8c0)!=0 || ((type&0x120)!=0 && target->has_dock_hardpoints())) return target;
    if((type&3)==0) return nullptr;
    unsigned base=0; target->get_base(base);
    if(!base) return nullptr;
    uintptr_t iter[3]={0,0,0xfdff};
    while(auto candidate=GetClientObjDb()->GetNext(iter)) {
        unsigned dock=0; candidate->get_dock_target(dock);
        if(dock==base && candidate->has_dock_hardpoints()) return candidate;
    }
    return nullptr;
}
void select(Node const& node) {
    if(auto target=object(node.point.ObjectId)) {
        player()->set_target(target,SUBOBJ_ID_NONE,GetPlayerConnectionId());
    } else if(node.user) {
        for(int i=0;i<GetPlayerWaypointCountRetail();++i)
            if(GetPlayerWaypointRetail(i)->AutoId==node.point.AutoId) { HudWaypointSelectPlayerWaypoint(i); break; }
    }
}
void consume() {
    if(route.empty()) return;
    Guard guard;
    Node node=route.front(); route.pop_front(); leg.clear();
    if(route.empty()) haveGoal=false;
    if(node.user) for(int i=0;i<GetPlayerWaypointCountRetail();++i)
        if(GetPlayerWaypointRetail(i)->AutoId==node.point.AutoId) { RemovePlayerWaypointRetail(i); break; }
    elapsed=stalled=0; bestDistance=std::numeric_limits<float>::infinity();
}
void fail(bool noPath=false) {
    Cancel(true);
    NnVoiceEnqueueByName("cancelled");
    bool ru=std::strcmp(PortLanguage(),"ru")==0;
    NnArrivalTextShowCaption(noPath ?
        (ru?L"\u041d\u0435\u0442 \u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0433\u043e \u043f\u0443\u0442\u0438 \u043a \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u0439 \u0442\u043e\u0447\u043a\u0435":L"No safe path to the next waypoint") :
        (ru?L"\u0410\u0432\u0442\u043e\u043f\u0438\u043b\u043e\u0442: \u043c\u0430\u0440\u0448\u0440\u0443\u0442 \u043f\u0440\u0435\u0440\u0432\u0430\u043d":L"Autopilot: route interrupted"));
}
bool dock() {
    auto b=manager(); auto target=object(route.front().point.ObjectId);
    if(!b || !target) return false;
    // Native Dock also handles lane entry and jumps. Those are route travel,
    // always included in F2; only landing at a base needs separate permission.
    unsigned const type=typeOf(target);
    bool const routeTransition=(type&0x8c0)!=0; // Lane, jump gate or jump hole.
    if(!routeTransition && !NavigationSettings::Get(NavigationSettings::AutoDock)) {
        // At the checked approach, continue with the exact native F2-to-object
        // command. RequestManeuver releases the route without braking; native
        // Go To owns the remaining approach distance and eventual slowdown.
        auto panel=GetHudManeuvers();
        if(!panel) return false;
        player()->set_target(target,SUBOBJ_ID_NONE,GetPlayerConnectionId());
        ClearMouseFlightSteering();
        return panel->RequestManeuver(2,false);
    }
    Guard guard;
    player()->set_target(target,SUBOBJ_ID_NONE,GetPlayerConnectionId());
    if(b->external_player_evaluate(7)==EvalSkip) return false;
    PlayerFlightActions::Cancel();
    pub::AI::DirectiveDockOp op; op.DockObjectId=target->get_id();
    if((type&0x80)!=0 && route.size()>1 && route[1].point.SystemId==system &&
       (typeOf(object(route[1].point.ObjectId))&0x80)!=0)
        op.Field_10=static_cast<int>(route[1].point.ObjectId);
    if(!b->set_current_directive(directive(7),&op)) return false;
    notify(target->get_id(),7);
    state=State::Docking; elapsed=0; issued=true;
    if((type&0x840)!=0) {
        auto c=target->cobject();
        if(c && (c->ObjectClass&CObject::ClassSolar)==CObject::ClassSolar) {
            auto solar=static_cast<CSolar const*>(c);
            jumpSystem=solar->DestSystem; exitGate=solar->DestGate.Id;
        }
    }
    return true;
}
bool gotoPoint(V goal,bool flyThrough) {
    auto b=manager(); if(!b) return false;
    Guard guard;
    pub::AI::DirectiveGotoOp op;
    op.Field_0C=1; op.Destination=vec(goal); op.Field_50=flyThrough?10.f:100.f;
    op.Field_58=flyThrough?1:0;
    bool ok;
    if(b->CurrentBehaviorIndex==2 && issued) {
        // Update the active directive in-place: no Slot4/Slot3, no reset of the
        // cruise engine or behavior state between free-space points.
        ok=b->BehaviorDispatchTable[2]->Slot10(&op);
    } else ok=b->set_current_directive(directive(2),&op);
    if(!ok) return false;
    auto go=static_cast<GotoBehavior*>(b->BehaviorDispatchTable[2]);
    // Short intermediate legs must not clear a previously engaged cruise.
    // Native obstacle avoidance still has the final say; Field_5A stays zero.
    if(flyThrough) { go->Flag364=1; go->Flag365=0; }
    b->update_current_behavior_cruise(cruiseRequested);
    issued=true; previous=v(player()->get_position());
    bestDistance=length(goal-previous); stalled=0;
    notify(route.front().point.ObjectId,2);
    return true;
}
bool prepare() {
    if(route.empty()) return false;
    auto& node=route.front();
    if(node.point.SystemId!=system) return false;
    if(auto target=object(node.point.ObjectId)) {
        if(auto dockTarget=node.laneExit?nullptr:dockingObject(target)) {
            node.point.ObjectId=dockTarget->get_id(); node.point.Pos=dockTarget->get_position(); node.dock=true;
        } else node.point.Pos=target->get_position();
    } else if(node.point.ObjectId) return false;
    select(node);
    V from=v(player()->get_position()),to=v(node.point.Pos);
    auto target=object(node.point.ObjectId);
    bool approach=target && typeOf(target)!=0x200 && !node.dock && !node.laneExit;
    std::vector<V> plan;
    bool planned=node.dock ? RoutePlanner::PlanDock(from,to,node.point.ObjectId,dockingRange(node.point.ObjectId),plan)
        : approach ? RoutePlanner::PlanApproach(from,node.point.ObjectId,plan) : RoutePlanner::Plan(from,to,plan);
    if(!planned || plan.empty()) return false;
    if(node.dock && plan.size()==1 && length(plan.front()-from)<1) return dock();
    leg.assign(plan.begin(),plan.end());
    return gotoPoint(leg.front(),leg.size()>1 || route.size()>1 || node.dock);
}
}
bool InternalCommand() { return internal; }
bool Active() { return state!=State::Off; }
void Cancel(bool freeFlight) {
    if(internal) return;
    if(haveGoal && (pendingStart || (Active() && !route.empty() && route.front().user))) rebuildOnStart=true;
    pendingStart=false; mouseOverride=false; replanAfterMouse=false;
    bool wasActive=Active(); state=State::Off; route.clear(); leg.clear(); owner.set(nullptr);
    issued=false; jumpSystem=exitGate=0; elapsed=stalled=0;
    if(wasActive && freeFlight) {
        Guard guard;
        PlayerFlightActions::Cancel();
        auto b=manager(); auto s=ship();
        if(b && s && !s->is_using_tradelane() && !s->is_launching() && !b->LockManeuversByte) {
            b->set_current_directive(directive(0x13),nullptr);
            b->update_current_behavior_cruise(false);
            b->update_current_behavior_throttle(0);
            ResetPlayerBehaviorDirection();
        }
    }
}
bool Keyboard(float x,float y,float z) {
    if(!Active() || (x==0 && y==0 && z==0)) return false;
    Cancel(true); return true;
}
bool BlockMouse() {
    if(!Active()) return false;
    bool steering=state==State::Flying && !CockpitFreeLook::BlocksMouseFlight() &&
        !HudStatusIsTurretView() && !HudStatusIsRearView() &&
        (IsMouseFlightLocked() || (GetClientMouseButtons()&1u)!=0) && Win3DGetHover()==nullptr;
    if(!steering && mouseOverride) {
        ClearMouseFlightSteering();
    }
    return !steering;
}
bool MouseSteering(float x,float y,float z) {
    if(!Active()) return false;
    if(state!=State::Flying || CockpitFreeLook::BlocksMouseFlight() ||
       HudStatusIsTurretView() || HudStatusIsRearView()) return true;
    auto b=manager();
    if(b && b->CurrentBehaviorIndex==2) {
        mouseOverride=true;
        // Native Go To has a manual direction override. It retains its
        // directive, destination and cruise instead of switching to Freeflight.
        b->update_current_behavior_direction(vec({x,y,z}));
    }
    return true;
}
bool ReleaseMouseSteering() {
    if(!Active()) return false;
    if(mouseOverride) replanAfterMouse=true;
    mouseOverride=false;
    if(auto b=manager()) {
        // Common replays LastCommandedDirection every simulation tick. Clear
        // that cache and UserTurningInputState through its normal input API,
        // even if the client has already cleared G_MouseFlightEngaged.
        b->update_current_behavior_direction(vec({0,0,0}));
        // A zero direction still enables manual "ahead" steering for a point
        // target. Release it AFTER zeroing the cache, so it cannot be replayed.
        if(b->CurrentBehaviorIndex==2)
            static_cast<GotoBehavior*>(b->BehaviorDispatchTable[2])->Flag2ea=0;
    }
    return true;
}
void SetCruiseRequested(bool enabled) {
    if(Active() && !internal) cruiseRequested=enabled;
}
void Landed() { Cancel(); haveGoal=rebuildOnStart=false; RoutePlanner::Invalidate(); }
void RouteChanged() {
    if(internal || refining || receivingPath) return;
    Cancel(true); haveGoal=rebuildOnStart=false;
}
void PathRequested() {
    if(internal) return;
    Cancel(); haveGoal=rebuildOnStart=false;
}
void BeginPathResponse() {
    receivingPath=true;
    if(!pendingStart) Cancel();
}

bool Start(HUD_Maneuvers*,bool rebuilt) {
    if(!NavigationSettings::Get(NavigationSettings::Autopilot)) return false;
    if(pendingStart) return true;
    auto p=player(); auto s=ship(); auto b=manager();
    if(!p || !s || !b || p->is_dying() || b->LockManeuversByte || s->is_using_tradelane() || s->is_launching()) return true;
    Cancel(); PlayerFlightActions::Cancel(); RoutePlanner::Invalidate();
    cruiseRequested=true;
    auto target=s->get_target(); unsigned selected=target?target->get_id():0;
    int selectedIndex=rebuilt?0:selectedRouteIndex(target);
    bool useRoute=rebuilt || !target || selectedIndex>=0;
    if(rebuildRoute(useRoute)) return true;
    int start=(std::max)(selectedIndex,0);
    if(useRoute) {
        for(int i=start;i<GetPlayerWaypointCountRetail();++i) route.push_back({*GetPlayerWaypointRetail(i),true});
    }
    if(route.empty() && target) {
        // Mission waypoints are left owned by the mission system. Follow its
        // currently selected objective without deleting or inventing objectives.
        route.push_back({{target->get_position(),GetPlayerStarSystemIdRetail(),typeOf(target)==0x200?0:selected,0}});
    }
    if(route.empty()) return false; // Native Go To's "ahead" action.
    // Ships retain normal Go To/follow behavior rather than snapshot coordinates.
    if(target && (typeOf(target)&0x7f0000)!=0 && !useRoute) {route.clear();return false;}
    connection=GetPlayerConnectionId(); system=GetPlayerStarSystemIdRetail();
    state=State::Flying; owner.set(static_cast<Watchable*>(p)); previous=v(p->get_position());
    ClearMouseFlightSteering();
    while(route.size()>1 && route.front().point.SystemId==system && !route.front().point.ObjectId &&
          length(v(route.front().point.Pos)-previous)<150) consume();
    if(!prepare()) fail(true);
    return true;
}

void Tick(float dt,bool docking) {
    if(!Active()) return;
    // Finish the current native maneuver if automation is disabled in settings.
    if(!NavigationSettings::Get(NavigationSettings::Autopilot)) {Cancel();return;}
    if(!std::isfinite(dt) || dt<=0) return;
    auto p=player(); auto s=ship(); auto b=manager();
    if(connection!=GetPlayerConnectionId() || !p || !s || !b || p->is_dying() ||
       owner.target()!=static_cast<Watchable*>(p)) { Cancel(); return; }
    if(route.empty()) { Cancel(); return; }
    elapsed+=dt;
    unsigned now=GetPlayerStarSystemIdRetail();
    if(now!=system) {
        if((state!=State::Docking && state!=State::Jump) || now!=jumpSystem) {Cancel();return;}
        system=now; RoutePlanner::Invalidate(); consume();
        // The paired arrival gate is an arrival marker, never a request to dock
        // back through it. All other route points remain mandatory.
        if(!route.empty() && route.front().point.SystemId==system &&
           route.front().point.ObjectId==exitGate) consume();
        state=State::Jump;
    }
    if(state==State::Jump) {
        if(IsLetterboxVisible() || s->is_launching() || docking || b->LockManeuversByte) return;
        if(route.empty()) {Cancel();return;}
        state=State::Flying;
        if(!prepare()) fail();
        return;
    }
    if(state==State::Docking || state==State::Lane) {
        if(s->is_using_tradelane()) { state=State::Lane; return; }
        if(state==State::Lane && !IsLetterboxVisible() && !docking) {
            consume();
            if(!route.empty() && route.front().point.SystemId==system &&
               (typeOf(object(route.front().point.ObjectId))&0x80)!=0) {
                route.front().laneExit=true; route.front().dock=false;
            }
            // A lane's second endpoint is reached by the lane ride itself.
            if(!route.empty() && route.front().point.SystemId==system &&
               (typeOf(object(route.front().point.ObjectId))&0x80)!=0 &&
               length(v(route.front().point.Pos)-v(p->get_position()))<2000) consume();
            if(route.empty()) {Cancel();return;}
            state=State::Flying; if(!prepare()) fail(); return;
        }
        if(!docking && !IsLetterboxVisible() && elapsed>2 && b->CurrentBehaviorIndex!=7) fail();
        else if(elapsed>300) fail();
        return;
    }
    if(docking || IsLetterboxVisible() || b->LockManeuversByte) { Cancel(); return; }
    // Input may change between simulation and rendering. Resume before the
    // behavior manager's next update, without waiting for the render callback.
    BlockMouse();
    if(mouseOverride) {
        if(b->CurrentBehaviorIndex!=2) {Cancel();return;}
        // Manual steering may last arbitrarily long. Count only actual passage
        // through free-space objectives; do not fight the pilot or time out.
        V pos=v(p->get_position());
        while(!route.empty() && route.front().point.SystemId==system && !route.front().point.ObjectId &&
              passed(previous,pos,v(route.front().point.Pos),150)) consume();
        previous=pos; stalled=0;
        if(route.empty()) Cancel();
        return;
    }
    if(replanAfterMouse) {
        replanAfterMouse=false; leg.clear();
        if(!prepare()) fail(true);
        return;
    }
    if(leg.empty()) { if(!prepare()) fail(); return; }
    V pos=v(p->get_position());
    float radius=0; Vector center; p->get_physical_radius(radius,center);
    float reach=(std::max)(150.f,radius+80.f);
    float distance=length(leg.front()-pos);
    bool flyThrough=leg.size()>1 || route.size()>1 || route.front().dock;
    if(passed(previous,pos,leg.front(),reach)) {
        do {leg.pop_front();} while(!leg.empty() && passed(previous,pos,leg.front(),reach));
        if(leg.empty()) {
            // The final leg is a checked approach point, not the base centre.
            // Reaching it must start Dock, never consume/skip the destination.
            if(route.front().dock) {if(!dock()) fail();return;}
            consume();
            while(!route.empty() && route.front().point.SystemId==system && !route.front().point.ObjectId &&
                  passed(previous,pos,v(route.front().point.Pos),reach)) consume();
            if(route.empty()) { Cancel(true); NnVoiceEnqueueByName("objective_reached"); return; }
            if(!prepare()) fail();
        } else if(!gotoPoint(leg.front(),leg.size()>1 || route.size()>1 || route.front().dock)) fail();
        return;
    }
    // Respect mission/directive takeover. A stalled/denied route does not
    // continually reissue F2 or Dock and fight the player's controls.
    if(b->CurrentBehaviorIndex!=2) {
        if(!flyThrough && distance<reach+150) {consume();Cancel();}
        else Cancel();
        return;
    }
    if(distance<bestDistance-10) { bestDistance=distance; stalled=0; } else stalled+=dt;
    if(stalled>60) {fail();return;}
    previous=pos;
}

static bool refineWaypoints() {
    auto selectStart=[]() {
        if(NavigationSettings::Get(NavigationSettings::Autopilot) && GetPlayerWaypointCountRetail()>0 &&
           GetPlayerWaypointRetail(0)->SystemId==GetPlayerStarSystemIdRetail())
            HudWaypointSelectPlayerWaypoint(0);
    };
    if(!player()) return true;
    if(!RoutePlanner::BetaEnabled()) {selectStart();return true;}
    RoutePlanner::Invalidate();
    std::vector<FPlayerWaypointRecord> original,refined;
    for(int i=0;i<GetPlayerWaypointCountRetail();++i) original.push_back(*GetPlayerWaypointRetail(i));
    V from=v(player()->get_position());
    unsigned local=GetPlayerStarSystemIdRetail();
    bool previousLane=false;
    bool localLeg=true;
    auto noPath=[]() {
        refining=true; ResetPlayerWaypointsRetail(); refining=false; return false;
    };
    for(auto point:original) {
        if(point.SystemId!=local) localLeg=false;
        auto target=point.SystemId==local?object(point.ObjectId):nullptr;
        bool lane=(typeOf(target)&0x80)!=0;
        bool laneRide=lane && previousLane;
        V reached=v(point.Pos);
        if(localLeg && !laneRide) {
            auto dockTarget=dockingObject(target);
            if(dockTarget) {point.ObjectId=dockTarget->get_id();point.Pos=dockTarget->get_position();}
            bool approach=target && typeOf(target)!=0x200 && !dockTarget;
            std::vector<V> path;
            bool planned=dockTarget ? RoutePlanner::PlanDock(from,v(point.Pos),point.ObjectId,dockingRange(point.ObjectId),path)
                : approach ? RoutePlanner::PlanApproach(from,point.ObjectId,path) : RoutePlanner::Plan(from,v(point.Pos),path);
            if(!planned || path.empty()) return noPath();
            // Retain the object as the final goal, preceded by its safe arrival
            // point. F2 uses the same approach planner and never flies to its centre.
            size_t intermediate=path.size()-((dockTarget || approach)?0:1);
            if(refined.size()+intermediate+1>99) return noPath();
            for(size_t i=0;i<intermediate;++i) refined.push_back({vec(path[i]),local,0,0});
            reached=path.back();
        }
        refined.push_back(point); from=reached; previousLane=lane && !laneRide;
    }
    if(refined.size()>99) return noPath();
    refining=true;
    ResetPlayerWaypointsRetail();
    for(auto const& p:refined) AddPlayerWaypointRetail(p.Pos,p.SystemId,p.ObjectId);
    refining=false;
    selectStart();
    return true;
}
bool RefineWaypoints() {
    bool resume=pendingStart && goalConnection==GetPlayerConnectionId();
    FPlayerWaypointRecord expected=savedGoal;
    auto tail=GetPlayerWaypointCountRetail()>0 ? GetPlayerWaypointRetail(GetPlayerWaypointCountRetail()-1):nullptr;
    // Compare the response before refinement can replace a planet with its
    // docking ring, which has different coordinates but is the same requested trip.
    bool matches=tail && tail->SystemId==expected.SystemId && length(v(tail->Pos)-v(expected.Pos))<2;
    bool ok=refineWaypoints();
    receivingPath=false; pendingStart=false; rebuildOnStart=false;
    haveGoal=ok && GetPlayerWaypointCountRetail()>0;
    if(haveGoal) {
        savedGoal=*GetPlayerWaypointRetail(GetPlayerWaypointCountRetail()-1);
        goalConnection=GetPlayerConnectionId();
    }
    if(resume) {
        // A changed/new map request must never resume an unrelated route.
        if(!haveGoal) fail(true);
        else if(matches)
            Start(nullptr,true);
    }
    return ok;
}
}
#endif
