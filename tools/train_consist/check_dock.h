// Native docking fixture: real inspect/AI/physics, local control setters.
#include "common_dockbehavior.h"
#include "common_systemmanager.h"
struct DockHandle: IObjInspectImpl {
 CShip* ship(){return static_cast<CShip*>(Object);}
 int set_throttle(float Throttle) override {ship()->set_throttle(Throttle);return 0;}
 int set_axis_throttle(Vector const& AxisThrottle) override {ship()->set_axis_throttle(AxisThrottle);return 0;}
 int set_nudge_vec(Vector const& NudgeVec) override {ship()->set_nudge_vec(NudgeVec);return 0;}
 int set_strafe_dir(StrafeDir Dir) override {return -3;}
 int set_formation_leader(IObjRW* Leader) override {return -3;}
 int set_formation_offset(Vector const& Offset) override {return -3;}
 int add_formation_follower(IObjRW* Follower) override {return -3;}
 int remove_formation_follower(IObjRW* Follower) override {return -3;}
 int get_formation_follower_count() override {return -3;}
 int set_follow_leader(IObjRW* Leader) override {return -3;}
 int set_follow_offset(Vector const& Offset) override {return -3;}
 int add_follow_follower(IObjRW* Follower) override {return -3;}
 int remove_follow_follower(IObjRW* Follower) override {return -3;}
 int slot_34(unsigned short const* EquipIds, unsigned Count, Vector const* TargetPos,
                        int SourceClient) override {return -3;}
 int slot_38(unsigned short EquipId, int Count, int SourceClient) override {return -3;}
 int slot_3c(unsigned short const* EquipId, std::vector<IObjRW*> const& Targets,
                        int SourceClient) override {return -3;}
 int slot_40(unsigned short const* EquipId, IObjRW* Target, int SourceClient) override {return -3;}
 int slot_44(unsigned short const* EquipId, IObjRW* Target, unsigned short SubTarget,
                        int SourceClient) override {return -3;}
 int set_target(IObjRW* Target, unsigned short SubTarget, int SourceClient) override {return -3;}
 int slot_4c(unsigned short const* EquipId, bool bActivate, int SourceClient) override {return -3;}
 int slot_50(bool bEngage, bool bArg2, int SourceClient) override {return 0;}
 int slot_54(bool bActivate, int SourceClient) override {return -3;}
 int slot_58(unsigned short EquipId, unsigned Count, int SourceClient) override {return -3;}
 int slot_5c(int RequestType, unsigned const* TargetId, unsigned const* SecondId,
                        int bFlag, RequestCB* Callback) override {return -3;}
 int slot_60(int RequestType, unsigned const* TargetId, int Arg3) override {return -3;}
 int go_tradelane(IObjInspect const* EntranceRing, IObjInspect const* ExitRing,
                             bool bFastExit, float Speed) override {return -3;}
 int stop_tradelane() override {return -3;}
 int slot_6c(int ArgA, int ArgB) override {return -3;}
 int slot_70(unsigned Id) override {return -3;}
 int slot_74(unsigned Arg) override {return -3;}
};
