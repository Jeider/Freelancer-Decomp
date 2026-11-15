#pragma once
#include "common_csys.h"
class Quaternion;
bool TrainCourierLaunchPose(unsigned player, Vector& position, Quaternion& orientation,
                           unsigned& solar, int& dockIndex);
void TrainCourierTick();
void TrainCourierReset(unsigned player=0);
bool PlayerShipTransferDock(unsigned player, unsigned anchor, unsigned base);
void PlayerShipTransferReset(unsigned player);
struct CShip;
bool TrainConsistParkForSystemSwitch(CShip* loco, unsigned& trailer, unsigned& owner, float& hitpoints);
bool TrainConsistArriveAfterSystemSwitch(CShip* loco, unsigned trailer, unsigned owner, float hitpoints,
    unsigned system, Vector const& position, Matrix const& orientation);
