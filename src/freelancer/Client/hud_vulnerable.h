#pragma once

struct FSpaceCamera;
struct FMouseEvent;

// Port-only toggled targeting of marked collision groups in the world.
bool VulnerableTargetingMouse(FMouseEvent const& event);
bool VulnerableAutoselectEnabled();
void SetVulnerableAutoselect(bool enabled);
void VulnerableTargetingDraw(FSpaceCamera* camera);
void VulnerableTargetingReset();
