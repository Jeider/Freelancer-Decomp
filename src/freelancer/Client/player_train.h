#pragma once
class HUD_Maneuvers;
class NnButtonControl;
struct FToolTipHoverInfo;
struct IObjAffect;
class Vector;
namespace PlayerTrain {
void Create(HUD_Maneuvers*);
void Release(HUD_Maneuvers*);
void Update(HUD_Maneuvers*,int behavior);
bool HasButton(int behavior);
void Layout(HUD_Maneuvers*,int behavior);
bool IsApproaching();
void CancelApproach();
void Tooltip(NnButtonControl*,FToolTipHoverInfo*);
bool Click(unsigned long button);
void FireCoupled(IObjAffect* host,unsigned short const* ids,unsigned count,Vector const* aim,int player);
}
