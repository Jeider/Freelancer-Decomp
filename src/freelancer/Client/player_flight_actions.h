#pragma once
class HUD_Maneuvers;
class NnButtonControl;
struct FToolTipHoverInfo;
namespace PlayerFlightActions {
constexpr unsigned FirstCommand = 0xd0;
constexpr unsigned CommandCount = 3;
constexpr unsigned KeyIdsBase = 0x7f5120;
inline bool IsCommand(unsigned id) { return id >= FirstCommand && id < FirstCommand + CommandCount; }
inline int CommandAction(unsigned id, int behavior) {
    if (!IsCommand(id)) return -1;
    if (behavior == 2) return id == FirstCommand ? 3 : -1;
    return behavior == 0x13 ? static_cast<int>(id - FirstCommand) : -1;
}
#ifdef FREELANCER_PLAYER_FLIGHT_ACTIONS
bool Enabled();
bool Command(unsigned id);
wchar_t const* KeyText(unsigned ids);
void CreateButtons(HUD_Maneuvers* hud);
bool HasButtons(int behavior);
bool IsGotoWeaving();
char const* TelemetryAction();
void Layout(HUD_Maneuvers* hud,int behavior);
bool Click(unsigned long button);
void Release(HUD_Maneuvers* hud);
void Cancel();
bool RequestCancel();
void BeforeUpdate();
void Tick(float dt,bool docking);
bool BlockMouse();
bool Keyboard(float x,float y,float z);
void Camera(float* view,float dt);
void Tooltip(NnButtonControl* button,FToolTipHoverInfo* info);
#else
inline bool Enabled() { return false; }
inline bool Command(unsigned) { return false; }
inline wchar_t const* KeyText(unsigned) { return nullptr; }
inline void CreateButtons(HUD_Maneuvers*) {}
inline bool HasButtons(int) { return false; }
inline bool IsGotoWeaving() { return false; }
inline char const* TelemetryAction() { return "none"; }
inline void Layout(HUD_Maneuvers*,int) {}
inline bool Click(unsigned long) { return false; }
inline void Release(HUD_Maneuvers*) {}
inline void Cancel() {}
inline bool RequestCancel() { return true; }
inline void BeforeUpdate() {}
inline void Tick(float,bool) {}
inline bool BlockMouse() { return false; }
inline bool Keyboard(float,float,float) { return false; }
inline void Camera(float*,float) {}
inline void Tooltip(NnButtonControl*,FToolTipHoverInfo*) {}
#endif
}
