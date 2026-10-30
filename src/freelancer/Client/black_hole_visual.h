#pragma once
class FClientGameobj;
class FClientSolarGameobj;
struct FSpaceCamera;
struct ICamera;
struct FThornPsys;
// Port-only (RP9): ray-marched, gravitationally lensed black hole with an accretion
// disc. Replaces the ALE gf_bhring / gf_neutronstar attachments of listed archetypes.
bool BlackHoleVisualReplaceAttached(FClientGameobj* Host, unsigned EffectId);
void BlackHoleVisualTick(FClientSolarGameobj* Host, float Dt);
void BlackHoleVisualForget(FClientSolarGameobj* Host);
void BlackHoleVisualDraw(FSpaceCamera* Camera);
// Console "bh <bits>": 1 scene depth off, 2 one layer, 4 no second band family / smoke,
// 8 no haze / vortices, 16 background not lensed (0 = all on).
void BlackHoleVisualSetDebug(int Mode);
// How deep a world point sits in a space black hole's disc gas (0..1; port.ini black_hole_slab_height),
// with the unit world direction from the point to that hole's centre and the distance to it in
// metres. False when the point is in no disc.
bool BlackHoleVisualShipImmersion(float const* WorldPos, float* OutStrength, float* OutToCentre, float* OutDistance);
void BlackHoleVisualRenderShutdown();

// Base-room (Thorn script) scenes such as the main-menu intro. Claim returns true when the
// PSYS entity bound to EffectName is replaced (the caller then leaves its VisEffect unbound).
// True when a cutscene COMPOUND of this template is left out (the old core sphere, the flute).
bool BlackHoleVisualThornHides(char const* TemplateName);
bool BlackHoleVisualThornClaim(FThornPsys* Psys, char const* EffectName);
void BlackHoleVisualThornTick(FThornPsys* Psys, float Dt);
void BlackHoleVisualThornForget(FThornPsys* Psys);
void BlackHoleVisualDrawRoom(ICamera* Camera);
