#pragma once
#include <cstdio>
class INI_Reader;
class FMissionScript;
void LocalTriggersConfigureM01a(FMissionScript* mission);
bool LocalTriggersExecuting(FMissionScript* mission);
bool LocalTriggersPersonalOffer(unsigned controller);
bool LocalTriggersBridgeActivation(FMissionScript* mission, unsigned trigger);
void LocalTriggersAcceptedMission(FMissionScript* mission);
// Character-save integration. These sections do not create a campaign or enroll a player.
void LocalTriggersPlayerLoad(unsigned player, INI_Reader* reader);
void LocalTriggersPlayerSave(unsigned player, FILE* file);
void LocalTriggersPlayerLogout(unsigned player);
