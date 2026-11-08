#pragma once
#include "common_csys.h"
class Quaternion;
bool TrainCourierLaunchPose(unsigned player, Vector& position, Quaternion& orientation,
                           unsigned& solar, int& dockIndex);
void TrainCourierTick();
void TrainCourierReset(unsigned player=0);
