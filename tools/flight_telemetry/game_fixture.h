// Minimal game facade for executing the unmodified telemetry adapter in isolation.
#include "flight_telemetry.h"
#include "flight_telemetry_recording.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <limits>
#include <vector>

class Vector { public: float x=0, y=0, z=0; };
struct Matrix { float E[3][3]={{1,0,0},{0,1,0},{0,0,1}}; };
enum StrafeDir { StrafeNone, StrafeLeft };
namespace Archetype {
struct Ship {
    float LinearDrag=2, AngularDragX=3, AngularDragY=4, AngularDragZ=5;
    float SteeringTorqueX=6, SteeringTorqueY=7, SteeringTorqueZ=8;
    float RotationInertiaX=9, RotationInertiaY=10, RotationInertiaZ=11;
    float StrafeForce=12, NudgeForce=13;
    unsigned get_id() const { return 444; }
};
}
inline Archetype::Ship fixtureArch;
struct IObjRW {
    unsigned id=1; Vector position, velocity, angular; Matrix rotation;
    IObjRW* target=nullptr; bool shieldKnown=true;
    int get_status(float& hp,float& max) const { hp=500;max=1000;return 0; }
    int get_shield_status(float& hp,float& max,bool& active) const {
        if(!shieldKnown)return -1;
        hp=100;max=200;active=true;return 0;
    }
    int get_type(unsigned& type) const {type=1;return 0;}
    unsigned get_id() const {return id;}
    Vector const& get_position() const {return position;}
    Vector get_velocity() const {return velocity;}
    Matrix const& get_orientation() const {return rotation;}
    Vector get_angular_velocity() const {return angular;}
    bool is_dying() const {return false;}
    int get_throttle(float& v) const {v=-1;return 0;}
    int get_axis_throttle(Vector& v) const {v={.25f,-.5f,0};return 0;}
    int get_nudge_vec(Vector& v) const {v={};return 0;}
    int get_strafe_dir(StrafeDir& v) const {v=StrafeLeft;return 0;}
    int are_thrusters_active(bool& v) const {v=true;return 0;}
    int is_cruise_active(bool& cruise,bool& lane) const {cruise=lane=false;return 0;}
    int get_target(IObjRW*& v) const {v=target;return 0;}
    int get_subtarget(unsigned short& v) const {v=7;return 0;}
    int get_attitude_towards(float& v,IObjRW*) const {v=-1;return 0;}
    int get_physical_radius(float& v,Vector& center) const {v=10;center=position;return 0;}
    float get_mass() const {return 100;}
};
struct Watchable {IObjRW* object=nullptr;};
struct Watcher {Watchable const* value=nullptr;Watchable const* target() const{return value;}};
struct CEquip {
    unsigned short GetID() const {return 9;}
    unsigned GetType() const {return 1;}
    Archetype::Ship const* EquipArch() const {return &fixtureArch;}
    bool IsActive() const {return true;}
};
struct CEScanner:CEquip {
    struct {int Count=0; Watcher Entries[256];} Scans;
    static CEScanner* cast(CEquip* equip) {return static_cast<CEScanner*>(equip);}
};
inline CEScanner fixtureScanner;
constexpr int EquipTypeScanner=123;
struct CEquipTraverser {bool done=false;};
struct EquipmentManager {
    CEquip const* FindFirst(int type) const {assert(type==EquipTypeScanner);return &fixtureScanner;}
    CEquip const* Traverse(CEquipTraverser& t) const {
        if(t.done)return nullptr;t.done=true;return &fixtureScanner;
    }
};
struct CShip {
    float Power=30, MaxPower=60, ThrustPower=40, MaxThrustPower=80;
    EquipmentManager EquipManager;
    Archetype::Ship const* shiparch() const {return &fixtureArch;}
};
struct IBehaviorManager {int CurrentBehaviorIndex=19;};
inline IObjRW fixturePlayer,fixtureTarget;
inline CShip fixtureShip;
inline IBehaviorManager fixtureBehavior;
inline unsigned fixtureRevision=1,fixtureSystem=22;
inline bool fixturePresent=true,fixtureInput=true,fixturePaused=false;
inline bool G_bNnScreenUp=false;
inline void* GetPlayerObjRW(){return fixturePresent ? &fixturePlayer : nullptr;}
inline void* GetPlayerShipObject(){return fixturePresent ? &fixtureShip : nullptr;}
inline unsigned GetPlayerShipId(){return fixturePlayer.id;}
inline unsigned GetPlayerConnectionId(){return 99;}
inline unsigned GetPlayerShipArchetypeId(){return 555;}
inline unsigned GetGameSessionLoadRevision(){return fixtureRevision;}
inline unsigned StarSysGetActiveSystemId(){return fixtureSystem;}
inline bool ShouldSkipLocalServerTick(){return fixturePaused;}
inline IBehaviorManager* GetBehaviorManager(IObjRW*){return &fixtureBehavior;}
inline bool ClientInputIsActive(){return fixtureInput;}
inline void* HudGetInputFocus(){return nullptr;}
inline bool IsLetterboxVisible(){return false;}
inline bool IsMouseFlightLocked(){return true;}
inline bool IsMouseFlightHoldThresholdReached(){return true;}
inline bool GetPlayerEngineIsActive(){return false;}
inline bool KeyMapIsCommandHeld(unsigned id){return id==0x78;}
inline IObjRW* ObjRwFromWatchable(Watchable* watch){return watch ? watch->object : nullptr;}
namespace PlayerRoute {inline bool Active(){return false;}}
namespace PlayerFlightActions {inline char const* TelemetryAction(){return "none";}}
namespace CockpitFreeLook {inline bool Enabled(){return false;}}
enum class DamageCause { Collision=4 };
struct DamageEntry {unsigned short SubObjId=1;float HitPts=250;int Fate=0;};
struct DamageList {
    std::vector<DamageEntry> Entries{{}};
    unsigned get_inflictor_id() const{return 2;}
    unsigned get_inflictor_owner_player() const{return 0;}
    DamageCause get_cause() const{return DamageCause::Collision;}
    bool is_destroyed() const{return false;}
};
