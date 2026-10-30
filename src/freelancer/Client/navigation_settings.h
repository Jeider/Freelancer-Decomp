#pragma once

namespace NavigationSettings {
enum Setting { Generator, Autopilot, AutoDock, Count };
// Autopilot includes lane entry and jumps; AutoDock controls base docking only.
// User preferences override the installation's port.ini defaults.
int Default(Setting setting);
int Get(Setting setting);
bool Set(Setting setting,int value);
}
