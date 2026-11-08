#include "player_flight_actions.h"
#ifdef FREELANCER_PLAYER_FLIGHT_ACTIONS
#include "flight_action_math.h"
#include "flight_action_camera.h"
#include "hud_maneuvers.h"
#include "hud_target.h"
#include "nn_button_control.h"
#include "cockpit_free_look.h"
#include "tooltip_hover.h"
#include "player_behavior.h"
#include "space_letterbox.h"
#include "space_camera.h"
#include "input_manager.h"
#include "globals.h"
#include "win3d.h"
#include "common_archetype.h"
#include "common_cobject.h"
#include "common_iface.h"
#include "common_gotobehavior.h"
#include "common_physys.h"
#include "port_config.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <windows.h>

namespace PlayerFlightActions {
namespace {
using namespace FlightActionMath;
enum Kind { SpiralClockwise,ReverseTurn,ReverseStrafe,GotoWeave,Count,None };
HUD_Maneuvers* panel=nullptr;
WinControl* buttons[Count]{};
BaseWatcher owner;
BaseWatcher cameraOwner;
Kind active=None;
V start[3],axis,cameraUp;
float elapsed=0,progress=0,total=0,throttle=0,cameraBlend=0;
float reverseBoost=0;
bool reverseExit=false;
bool engine=true;
ReverseStrafeCycle strafeCycle;
FlightActionCamera::ReverseTurnCamera turnCamera;
bool restoringControls=false;
V gotoOrigin,gotoCourse,gotoUp,gotoBaseSteering,gotoAppliedSteering,gotoCameraOffset;
float gotoAngle=25.f*Pi/180.f,gotoCameraBlend=0;
bool gotoSteeringApplied=false,gotoCameraCaptured=false;
unsigned system=0;
POINT mouseStart{};
constexpr int TipBase=0x7f5100;
void finish(bool completed);
Vector vec(V v) { return {v.x,v.y,v.z}; }
V v(Vector const& a) { return {a.x,a.y,a.z}; }
V column(Matrix const& m,int i) { return {m.E[0][i],m.E[1][i],m.E[2][i]}; }
IObjRW* player() { return static_cast<IObjRW*>(GetPlayerObjRW()); }
bool enabled() { return PortConfigInt("FlightActions","enabled",1)!=0; }
bool allowed(CShip* ship) { return ship && ship->shiparch()->GetExtraManeuvers(); }
bool valid(IObjRW* p,Kind k=ReverseTurn) {
    if (!p || p->is_dying() || IsLetterboxVisible() || HudIsMousePickBlocked()) return false;
    CShip* s=HudShipOfObjRw(p);
    IBehaviorManager* b=s ? s->get_behavior_interface() : nullptr;
    return allowed(s) && b && b->CurrentBehaviorIndex==(k==GotoWeave ? 2:0x13) && !b->LockManeuversByte &&
        (k!=GotoWeave || s->get_target()) && !s->is_launching() && !s->is_using_tradelane() &&
        (k==GotoWeave || k==ReverseTurn || !s->is_cruise_active());
}
bool assets() {
    char path[MAX_PATH];
    char const* files[]={"HUD_drasticevade.3db","HUD_turntoface.3db","hud_mnvrstrafe.3db","hud_mnvrevade.3db"};
    for (auto f:files) {
        std::snprintf(path,sizeof(path),"%s..\\DATA\\INTERFACE\\HUD\\EXTRA\\%s",PortExeDirectory(),f);
        if (GetFileAttributesA(path)==INVALID_FILE_ATTRIBUTES) return false;
    }
    return true;
}
bool clearPath(CShip* s,V direction) {
    // Conservative look-ahead in the chosen direction and current flight direction.
    // This is an obstruction veto, not a claim of full collision-free path planning.
    V from=v(s->WorldPosition),velocity=v(player()->get_velocity());
    V paths[]={direction*120.0f,velocity*0.7f+direction*50.0f};
    for (auto d:paths) {
        if(length(d)<0.01f) continue;
        PhySys::RayHit hits[32];
        int n=PhySys::FindRayCollisions(s->PhysicsSystemId,vec(from),vec(from+d),hits,32);
        for(int i=0;i<n;++i) if(hits[i].Object && hits[i].Object!=s) return false;
    }
    return true;
}
bool supported(Kind k,CShip* s) {
    auto a=s->shiparch();
    if(k==GotoWeave) return a->SteeringTorqueY>0;
    if(k==ReverseStrafe) return a->StrafeForce>0;
    return k==ReverseTurn ? a->SteeringTorqueY>0 : a->NudgeForce>0 && a->SteeringTorqueZ>0;
}
bool gotoDestination(CShip* s,V& destination,float& clearance) {
    auto manager=s->get_behavior_interface();
    if(!manager || manager->CurrentBehaviorIndex!=2 || !manager->BehaviorDispatchTable[2]) return false;
    auto go=static_cast<GotoBehavior*>(manager->BehaviorDispatchTable[2]);
    float radius=0;
    if(go->Field2f4==0) {
        auto target=ObjRwFromWatchable(const_cast<Watchable*>(go->Watcher310.target()));
        if(!target || target->is_dying()) return false;
        destination=v(target->get_position());
        Vector center;
        target->get_physical_radius(radius,center);
    } else if(go->Field2f4==1) destination=v(go->Field304);
    else return false; // Scripted spline routes keep their own movement.
    clearance=length(destination-v(s->WorldPosition))-radius-(std::max)(go->Field358,0.f);
    return std::isfinite(clearance);
}
void restoreGotoSteering() {
    if(!gotoSteeringApplied) return;
    gotoSteeringApplied=false;
    auto held=ObjRwFromWatchable(const_cast<Watchable*>(owner.target()));
    CShip* s=held ? HudShipOfObjRw(held) : nullptr;
    Vector current;
    if(s && s->PhysicsSystemId==system && held->get_axis_throttle(current)==0 &&
        length(v(current)-gotoAppliedSteering)<1e-5f)
        held->set_axis_throttle(vec(gotoBaseSteering));
}
void tickGoto(IObjRW* p,CShip* s,float dt) {
    auto b=s->get_behavior_interface();
    if(b && b->CurrentBehaviorIndex==2 && static_cast<GotoBehavior*>(b->BehaviorDispatchTable[2])->Flag2ea) {
        p->set_strafe_dir(StrafeNone);
        return; // Native manual steering temporarily takes precedence over weaving.
    }
    V destination; float clearance;
    if(!gotoDestination(s,destination,clearance) || clearance<=0) { Cancel(); return; }
    // Route heading is measured from the centre line's origin, not from each
    // side of the weave; the camera must not yaw back and forth with the ship.
    V course=unit(destination-gotoOrigin);
    if(length(course)>0.5f)
        gotoCourse=unit(gotoCourse+(course-gotoCourse)*(1-std::exp(-dt*2.f)));
    V right=column(s->Orientation,0),up=column(s->Orientation,1),back=column(s->Orientation,2);
    V bearing=unit(destination-v(s->WorldPosition));
    // Let Go To first face the destination if activated during a large turn.
    // Never fight the native initial alignment with a 180-degree servo error.
    if(dot(back*-1.f,bearing)<0.5f) {
        p->set_strafe_dir(StrafeNone);
        strafeCycle.phase=0; elapsed=0;
        return;
    }
    float fade=std::clamp(clearance/(std::max)(250.f,length(v(p->get_velocity()))*2.f),0.f,1.f);
    elapsed=(std::min)(elapsed+dt,1.f);
    float entry=elapsed*elapsed*(3-2*elapsed);
    // Positive yaw around up turns the nose left (local forward is -Z).
    float angle=-strafeCycle.sine()*gotoAngle*fade*entry;
    strafeCycle.advance(dt);
    auto courseFrame=FlightActionCamera::levelCourse(bearing,gotoUp);
    V turnUp=FlightActionCamera::transform(courseFrame,{0,1,0});
    V desired[3];
    V axes[]={{1,0,0},{0,1,0},{0,0,1}};
    for(int i=0;i<3;++i)
        desired[i]=rotate(FlightActionCamera::transform(courseFrame,axes[i]),turnUp,angle);
    if(!clearPath(s,desired[2]*-1.f)) { Cancel(); return; }
    Vector native;
    if(p->get_axis_throttle(native)!=0) return;
    gotoBaseSteering=v(native);
    V error=(cross(right,desired[0])+cross(up,desired[1])+cross(back,desired[2]))*0.5f;
    V omega=v(p->get_angular_velocity());
    auto a=s->shiparch();
    float drag=s->AngularDragFactor;
    float tx=torque(dot(error,right),dot(omega,right),a->RotationInertiaX,a->AngularDragX*drag,a->SteeringTorqueX);
    float ty=torque(dot(error,up),dot(omega,up),a->RotationInertiaY,a->AngularDragY*drag,a->SteeringTorqueY);
    float tz=torque(dot(error,back),dot(omega,back),a->RotationInertiaZ,a->AngularDragZ*drag,a->SteeringTorqueZ);
    // Turn the physical ship and apply native strafe in the same direction.
    // Forward and lateral thrust trace the weave; orientation/velocity are never assigned.
    p->set_strafe_dir(strafeCycle.left() ? StrafeLeft : StrafeRight);
    p->set_axis_throttle(vec(right*tx+up*ty+back*tz));
    Vector applied;
    if(p->get_axis_throttle(applied)==0) { gotoAppliedSteering=v(applied); gotoSteeringApplied=true; }
}
void applyReverseStrafe(IObjRW* p) {
    // The same native controls as held reverse/strafe keys, including engine
    // reverse_fraction and strafe power consumption. No persistent brake flag.
    p->set_throttle(-1.f);
    p->set_strafe_dir(strafeCycle.left() ? StrafeLeft : StrafeRight);
}
bool afterburnerAvailable(CShip const* s) {
    auto thruster=CEThruster::cast(s->EquipManager.FindFirst(EquipTypeThruster));
    return thruster && !thruster->IsDestroyed() && !thruster->IsDisabled() &&
        thruster->IsControllerEnabled() && std::isfinite(thruster->GetThrust()) &&
        thruster->GetThrust()>0;
}
bool reverseNeedsBoost(IObjRW* p,V forward) {
    float maximum=p->get_speed(1.f,ThrustEquipEngine);
    return std::isfinite(maximum) && maximum>0 &&
        dot(v(p->get_velocity()),forward)<maximum*1.05f;
}
bool locksInput(Kind k) { return k==SpiralClockwise || k==ReverseTurn; }
void begin(Kind k) {
    // A finite figure owns the controls until it settles. Its button/key cannot
    // restart it or replace it halfway through; reverse/strafe remains a toggle.
    if(locksInput(active)) return;
    if(active==k || (k==ReverseTurn && active==None && turnCamera.holding())) { Cancel(); return; }
    Cancel();
    IObjRW* p=player();
    if(!enabled() || !valid(p,k)) return;
    CShip* s=HudShipOfObjRw(p);
    bool const cruising=s->is_cruise_active();
    if(!supported(k,s)) return;
    for(int i=0;i<3;++i) start[i]=column(s->Orientation,i);
    if(k==GotoWeave) {
        V destination; float clearance;
        if(!gotoDestination(s,destination,clearance) || clearance<=0) return;
        gotoOrigin=v(p->get_position()); gotoCourse=unit(destination-gotoOrigin);
        gotoUp=FlightActionCamera::transform(FlightActionCamera::levelCourse(gotoCourse,start[1]),{0,1,0});
        gotoCameraBlend=0; gotoCameraCaptured=false;
        strafeCycle.reset(PortConfigFloat("FlightActions","goto_weave_interval",2.f));
        float angle=PortConfigFloat("FlightActions","goto_weave_angle",25.f);
        gotoAngle=(std::isfinite(angle) ? std::clamp(angle,0.f,60.f) : 25.f)*Pi/180.f;
    } else if(k!=ReverseStrafe && !clearPath(s,k==ReverseTurn ? V{} : start[0])) return;
    owner.set(static_cast<Watchable*>(p));
    cameraOwner.set(static_cast<Watchable*>(p));
    system=s->PhysicsSystemId;
    p->get_throttle(throttle);
    engine=GetPlayerEngineIsActive();
    cameraUp=start[1];
    // +Z points aft: rotation about -Z is clockwise from the chase camera.
    axis=k==ReverseTurn ? start[1] : start[2]*-1.f;
    total=k==ReverseTurn ? Pi : k==SpiralClockwise ? 2*Pi : 0;
    elapsed=progress=0;
    GetCursorPos(&mouseStart);
    if(k!=GotoWeave) ClearMouseFlightSteering();
    if(k==ReverseTurn) {
        // Outside cruise, boost for the full second whenever forward speed is
        // below 105% of the ordinary engine maximum and a working thruster exists.
        reverseExit=false;
        reverseBoost=!cruising && afterburnerAvailable(s) && reverseNeedsBoost(p,start[2]*-1.f) ? 1.f : 0.f;
        if(cruising) SetPlayerCruise(false);
        engine=true;
        SetPlayerEngageEngine(false);
        if(reverseBoost>0) SetPlayerAfterburner(true);
    }
    if(k==ReverseStrafe) {
        strafeCycle.reset(PortConfigFloat("FlightActions","reverse_strafe_interval",2.f));
        SetPlayerEngageEngine(true);
        applyReverseStrafe(p); // Begin with reverse + left immediately.
    }
    active=k;
    if(k==ReverseTurn) {
        cameraBlend=0;
        FSpaceCamera* cam=GetActiveSpaceCamera();
        if(cam && cam==GetThirdPersonSpaceCamera()) {
            V offset=V{cam->WorldPos[0],cam->WorldPos[1],cam->WorldPos[2]}-v(p->get_position());
            if(length(offset)>1.f)
                turnCamera.begin({offset,FlightActionCamera::fromMatrix(cam->World)},start[1]);
        }
    }
}

void finish(bool completed) {
    // State-restoration helpers also call Cancel; they are not manual input.
    if(restoringControls) return;
    if(completed) turnCamera.complete(); else turnCamera.cancel();
    if(active==None) return;
    restoringControls=true;
    Kind previous=active;
    bool const stopBoost=previous==ReverseTurn && reverseBoost>0;
    reverseBoost=0;
    reverseExit=false;
    if(previous==GotoWeave) restoreGotoSteering();
    active=None;
    IObjRW* held=ObjRwFromWatchable(const_cast<Watchable*>(owner.target()));
    IObjRW* p=player();
    if(held) {
        CShip* s=HudShipOfObjRw(held);
        if(s && s->PhysicsSystemId==system) {
            Vector zero={0,0,0};
            if(previous!=GotoWeave) held->set_nudge_vec(zero);
            if(previous==ReverseStrafe || previous==GotoWeave) held->set_strafe_dir(StrafeNone);
            // Never write an old free-flight state into a new docking/lane behavior.
            auto manager=s->get_behavior_interface();
            if(previous!=GotoWeave && manager && manager->CurrentBehaviorIndex==0x13 && !held->is_dying() &&
                !s->is_launching() && !s->is_using_tradelane()) {
                held->set_axis_throttle(zero);
                // Restore before wheel/held-throttle input reads the current value.
                if(previous==ReverseStrafe || previous==ReverseTurn) held->set_throttle(throttle);
                if(held==p) {
                    if(stopBoost) SetPlayerAfterburner(false);
                    SetPlayerThrottle(throttle);
                    SetPlayerEngageEngine(engine);
                    ClearMouseFlightSteering();
                } else {
                    manager->update_current_behavior_throttle(throttle);
                    manager->update_current_behavior_engage_engine(engine);
                }
            }
        }
    }
    owner.set(nullptr);
    restoringControls=false;
}
}

void Cancel() {
    finish(false);
}

bool RequestCancel() {
    // Manual input cannot abandon a half-finished finite figure. Internal
    // handoffs still use Cancel for death, docking, behavior and system safety.
    if(locksInput(active)) return false;
    Cancel();
    return true;
}

bool Enabled() { return enabled(); }
bool Command(unsigned id) {
    if (!enabled() || !IsCommand(id)) return false;
    IObjRW* p = player();
    CShip* ship = p ? HudShipOfObjRw(p) : nullptr;
    auto behavior = ship ? ship->get_behavior_interface() : nullptr;
    int action = CommandAction(id, behavior ? behavior->CurrentBehaviorIndex : -1);
    // An unavailable shortcut must not cancel the action belonging to another mode.
    if (action >= 0 && valid(p, static_cast<Kind>(action)) && supported(static_cast<Kind>(action), ship))
        begin(static_cast<Kind>(action));
    return true;
}

wchar_t const* KeyText(unsigned ids) {
    if (ids < KeyIdsBase || ids >= KeyIdsBase + CommandCount) return nullptr;
    wchar_t const* en[] = {L"Evade: spiral / Go To weave", L"Engine kill: turn 180 degrees", L"Reverse + alternating strafe"};
    wchar_t const* ru[] = {L"\u0423\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0435: \u0441\u043f\u0438\u0440\u0430\u043b\u044c / \u0441\u0438\u043d\u0443\u0441\u043e\u0438\u0434\u0430 F2", L"Engine kill: \u0440\u0430\u0437\u0432\u043e\u0440\u043e\u0442 \u043d\u0430 180\u00b0", L"\u0420\u0435\u0432\u0435\u0440\u0441 + \u043f\u043e\u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0439 \u0441\u0442\u0440\u0435\u0439\u0444"};
    return (std::strcmp(PortLanguage(), "ru") == 0 ? ru : en)[ids - KeyIdsBase];
}

void BeforeUpdate() {
    // Return the last native steering before the autopilot updates. On manual
    // cancellation, do not overwrite controls already changed by another owner.
    restoreGotoSteering();
}

void Tick(float dt,bool docking) {
    if(GetActiveSpaceCamera()!=GetThirdPersonSpaceCamera()) {
        gotoCameraBlend=0; gotoCameraCaptured=false;
    }
    if(turnCamera.running()) {
        IObjRW* p=player();
        CShip* s=p ? HudShipOfObjRw(p) : nullptr;
        if(!enabled() || docking || !s || p->is_dying() || IsLetterboxVisible() ||
            ObjRwFromWatchable(const_cast<Watchable*>(cameraOwner.target()))!=p ||
            s->PhysicsSystemId!=system || GetActiveSpaceCamera()!=GetThirdPersonSpaceCamera())
            turnCamera.reset();
        else if(!valid(p)) turnCamera.cancel();
    }
    if(active==None) return;
    IObjRW* p=player();
    if(!enabled() || docking || !valid(p,active) ||
        ObjRwFromWatchable(const_cast<Watchable*>(owner.target()))!=p) { Cancel(); return; }
    CShip* s=HudShipOfObjRw(p);
    if(s->PhysicsSystemId!=system) { Cancel(); return; }
    if(!(dt>0) || !std::isfinite(dt)) return;
    if(active==GotoWeave) { tickGoto(p,s,dt); return; }
    // A stalled frame cannot skip a complete figure or leave stale commands running.
    if(active!=ReverseStrafe) {
        if(dt>0.25f) { Cancel(); return; }
        if(active==ReverseTurn && reverseBoost>0) {
            auto manager=s->get_behavior_interface();
            if(reverseExit) {
                // Explicitly leave Engine Kill and accelerate in the new
                // direction before returning any controls to the player.
                manager->update_current_behavior_engage_engine(true);
                manager->update_current_behavior_throttle(1.f);
                p->set_throttle(1.f);
            } else if(!afterburnerAvailable(s)) {
                reverseBoost=0; // The thruster disappeared or broke mid-boost.
            }
            if(reverseBoost>0) {
                // Speed does not cut this phase short: hold the full second.
                if(!reverseExit || afterburnerAvailable(s))
                    manager->update_current_behavior_afterburner(true);
                reverseBoost-=dt;
            }
            if(reverseBoost>0) {
                Vector zero={0,0,0};
                p->set_axis_throttle(zero);
                return;
            }
            reverseBoost=0;
            SetPlayerAfterburner(false);
            if(reverseExit) { finish(true); return; }
        }
        elapsed+=dt;
        if(elapsed>12.f) { Cancel(); return; }
    }
    V omega=v(p->get_angular_velocity());
    if(total>0) progress+=dot(omega,axis)*dt;
    V right=column(s->Orientation,0), up=column(s->Orientation,1), back=column(s->Orientation,2);
    V desired[3];
    float angle=total>0 ? goal(progress,total) : 0;
    for(int i=0;i<3;++i) desired[i]=rotate(start[i],axis,angle);
    V error=(cross(right,desired[0])+cross(up,desired[1])+cross(back,desired[2]))*0.5f;
    auto a=s->shiparch();
    float tx=torque(dot(error,right),dot(omega,right),a->RotationInertiaX,a->AngularDragX,a->SteeringTorqueX);
    float ty=torque(dot(error,up),dot(omega,up),a->RotationInertiaY,a->AngularDragY,a->SteeringTorqueY);
    float tz=torque(dot(error,back),dot(omega,back),a->RotationInertiaZ,a->AngularDragZ,a->SteeringTorqueZ);
    p->set_axis_throttle(vec(right*tx+up*ty+back*tz));
    V nudge{};
    if(active==SpiralClockwise) {
        if(!clearPath(s,right)) { Cancel(); return; }
        // Local lateral thrust follows the roll: a real curved trajectory.
        float strength=std::clamp((total-progress)/0.7f,0.f,1.f)*0.65f;
        nudge={strength,0,0};
    } else if(active==ReverseStrafe) {
        applyReverseStrafe(p);
        strafeCycle.advance(dt);
    }
    p->set_nudge_vec(vec(nudge));
    if(total>0 && settled(progress,total,length(error),length(omega))) {
        if(active==ReverseTurn) {
            // Keep the action (and its input lock) alive for a one-second,
            // explicitly powered exit. Camera release can follow real motion.
            reverseExit=true;
            reverseBoost=1.f;
            turnCamera.complete();
            auto manager=s->get_behavior_interface();
            manager->update_current_behavior_engage_engine(true);
            manager->update_current_behavior_throttle(1.f);
            if(afterburnerAvailable(s)) manager->update_current_behavior_afterburner(true);
            p->set_throttle(1.f);
            Vector zero={0,0,0};
            p->set_axis_throttle(zero);
            return;
        }
        finish(true);
    }
}

bool BlockMouse() {
    if(active==GotoWeave) return false; // Native Go To accepts temporary manual steering.
    if(locksInput(active)) return true;
    if(active==None && !turnCamera.holding()) return false;
    POINT now; GetCursorPos(&now);
    // A click in the HUD must not count as steering. Moving back into space does.
    if(!CockpitFreeLook::BlocksMouseFlight() &&
        (IsMouseFlightLocked() || (GetClientMouseButtons()&1u)!=0) && Win3DGetHover()==nullptr &&
        (std::abs(now.x-mouseStart.x)>10 || std::abs(now.y-mouseStart.y)>10)) {
        Cancel(); return false;
    }
    return true;
}
bool Keyboard(float x,float y,float z) {
    if((active==None && !turnCamera.holding()) || (x==0 && y==0 && z==0)) return false;
    if(!locksInput(active)) Cancel();
    return true;
}

void CreateButtons(HUD_Maneuvers* hud) {
    panel=hud;
    if(!enabled() || !assets()) return;
    float half[3]={0.0156f,0.0157f,0},pos[3]={0,0.297f,0};
    char const* meshes[]={"HUD_drasticevade.3db","HUD_turntoface.3db","hud_mnvrstrafe.3db","hud_mnvrevade.3db"};
    for(int i=0;i<Count;++i) {
        char path[160],name[40];
        std::snprintf(path,sizeof(path),"INTERFACE\\HUD\\EXTRA\\%s",meshes[i]);
        std::snprintf(name,sizeof(name),"FlightAction%d",i);
        buttons[i]=hud->CreateButtonControl(name,path,nullptr,"ui_select_item",nullptr,pos,nullptr,half,0,1,0,0,TipBase+i,0,0);
        buttons[i]->SetProperty(1,1,0);
    }
}
bool HasButtons(int behavior) {
    if(!enabled() || !buttons[0] || !allowed(HudShipOfObjRw(player()))) return false;
    if(behavior!=2) return true;
    CShip* ship=HudShipOfObjRw(player());
    return ship && ship->get_target();
}
bool IsGotoWeaving() { return active==GotoWeave; }
char const* TelemetryAction() {
    switch(active) {
    case SpiralClockwise: return "spiral_clockwise";
    case ReverseTurn: return "reverse_turn";
    case ReverseStrafe: return "reverse_strafe";
    case GotoWeave: return "goto_weave";
    default: return "none";
    }
}
void Layout(HUD_Maneuvers* hud,int behavior) {
    if(hud!=panel || !buttons[0]) return;
    IObjRW* p=player();
    CShip* ship=HudShipOfObjRw(p);
    bool freeflight=enabled() && allowed(ship) && behavior==0x13;
    bool go=enabled() && allowed(ship) && behavior==2 && ship->get_target();
    float pos[3]{};
    hud->CruiseButton->SetProperty(7,reinterpret_cast<uintptr_t>(pos),0);
    float center=pos[0];
    if(freeflight || go) {
        pos[0]=center-(go ? 0.016f:0.048f);
        hud->CruiseButton->SetProperty(6,reinterpret_cast<uintptr_t>(pos),0);
    }
    for(int i=0;i<Count;++i) {
        bool show=i==GotoWeave ? go:freeflight;
        buttons[i]->SetProperty(1,show ? 0:1,0);
        pos[0]=i==GotoWeave ? center+0.016f : center-0.016f+0.032f*i;
        buttons[i]->SetProperty(6,reinterpret_cast<uintptr_t>(pos),0);
        buttons[i]->SetProperty(0xc,active==i || (i==ReverseTurn && turnCamera.holding()) ? 1:0,0);
        auto b=static_cast<NnButtonControl*>(buttons[i]);
        bool available=show && valid(p,static_cast<Kind>(i)) && supported(static_cast<Kind>(i),ship);
        b->SetFlags331(static_cast<unsigned char>((b->GetFlags331()&~2u)|(available?2u:0u)));
    }
}
bool Click(unsigned long button) {
    for(int i=0;i<Count;++i) if(buttons[i] && reinterpret_cast<unsigned long>(buttons[i])==button) {
        begin(static_cast<Kind>(i)); return true;
    }
    return false;
}
void Release(HUD_Maneuvers* hud) {
    if(hud!=panel) return;
    Cancel(); panel=nullptr; cameraBlend=0; cameraOwner.set(nullptr);
    turnCamera.reset();
    gotoCameraBlend=0; gotoCameraCaptured=false;
    for(auto& b:buttons) b=nullptr; // Win3D owns/deletes its child controls.
}
void Tooltip(NnButtonControl* button,FToolTipHoverInfo* info) {
    int i=button->ToolTipIds-TipBase;
    if(i<0 || i>=Count || button!=buttons[i]) return;
    wchar_t const* en[]={L"Clockwise spiral",L"Engine kill: turn 180 degrees",L"Reverse + alternating strafe",L"Go To: sine weave"};
    wchar_t const* ru[]={L"\u0421\u043f\u0438\u0440\u0430\u043b\u044c \u043f\u043e \u0447\u0430\u0441\u043e\u0432\u043e\u0439 \u0441\u0442\u0440\u0435\u043b\u043a\u0435",L"Engine kill: \u0440\u0430\u0437\u0432\u043e\u0440\u043e\u0442 \u043d\u0430 180\u00b0",L"\u0420\u0435\u0432\u0435\u0440\u0441 + \u043f\u043e\u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0439 \u0441\u0442\u0440\u0435\u0439\u0444",L"Go To: \u0441\u0438\u043d\u0443\u0441\u043e\u0438\u0434\u0430\u043b\u044c\u043d\u043e\u0435 \u0443\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0435"};
    info->CaptionW=_wcsdup(std::strcmp(PortLanguage(),"ru")==0 ? ru[i]:en[i]);
    info->CaptionCapacity=static_cast<unsigned>(wcslen(info->CaptionW)+1);
    info->AuxField=static_cast<int>(FirstCommand+(i==GotoWeave ? 0:i));
}
void Camera(float* view,float dt) {
    float goTarget=active==GotoWeave ? 1.f:0.f;
    gotoCameraBlend+=(goTarget-gotoCameraBlend)*std::clamp(dt*4.f,0.f,1.f);
    float target=active==SpiralClockwise && !turnCamera.running() && gotoCameraBlend<0.001f ? 1.f:0.f;
    cameraBlend+=(target-cameraBlend)*std::clamp(dt*5.f,0.f,1.f);
    if(cameraBlend<0.001f && gotoCameraBlend<0.001f && !turnCamera.running()) return;
    if(!player() || ObjRwFromWatchable(const_cast<Watchable*>(cameraOwner.target()))!=player() ||
        player()->is_dying() || IsLetterboxVisible()) { cameraBlend=0; gotoCameraBlend=0; turnCamera.reset(); return; }
    V pos={view[9],view[10],view[11]},ship=v(player()->get_position());
    if(gotoCameraBlend>=0.001f && !turnCamera.running()) {
        CShip* s=HudShipOfObjRw(player());
        if(!s || s->PhysicsSystemId!=system) { gotoCameraBlend=0; gotoCameraCaptured=false; return; }
        FlightActionCamera::Pose normal{pos-ship,FlightActionCamera::fromMatrix(view)};
        if(!gotoCameraCaptured) {
            gotoCameraOffset=FlightActionCamera::transform(FlightActionCamera::conjugate(normal.rotation),normal.offset);
            gotoCameraCaptured=true;
        }
        auto pose=FlightActionCamera::blendCourse(normal,
            FlightActionCamera::levelCourse(gotoCourse,gotoUp),gotoCameraOffset,gotoCameraBlend);
        FlightActionCamera::toMatrix(pose.rotation,view);
        pos=ship+pose.offset;
        view[9]=pos.x; view[10]=pos.y; view[11]=pos.z;
        return;
    }
    if(turnCamera.running()) {
        CShip* s=HudShipOfObjRw(player());
        if(!s || s->PhysicsSystemId!=system) { turnCamera.reset(); return; }
        float remaining=active==ReverseTurn ? FlightActionCamera::remainingTurnTime(
            progress,dot(v(player()->get_angular_velocity()),axis),engine,throttle) : -1.f;
        auto pose=turnCamera.update({pos-ship,FlightActionCamera::fromMatrix(view)},
            v(player()->get_velocity()),column(s->Orientation,2)*-1.f,dt,remaining);
        FlightActionCamera::toMatrix(pose.rotation,view);
        pos=ship+pose.offset;
        view[9]=pos.x; view[10]=pos.y; view[11]=pos.z;
        return;
    }
    pos=ship+(pos-ship)*(1+0.22f*cameraBlend);
    view[9]=pos.x;view[10]=pos.y;view[11]=pos.z;
    V back={view[2],view[5],view[8]},up={view[1],view[4],view[7]};
    V stable=unit(cameraUp-back*dot(cameraUp,back));
    if(length(stable)<0.5f) return;
    // Interpolate the signed roll, not opposite vectors (which cancel at 50%).
    float roll=std::atan2(dot(back,cross(up,stable)),dot(up,stable));
    up=rotate(up,back,roll*cameraBlend);
    V right=unit(cross(up,back)); up=cross(back,right);
    view[0]=right.x;view[3]=right.y;view[6]=right.z;
    view[1]=up.x;view[4]=up.y;view[7]=up.z;
}
}
#endif
