#pragma once

class FClientGameobj;

// Port-only solar spheres, shared by the planet eclipse (space_scene_obj_draw.cpp) and the planet
// rings (texture_panels.cpp). All results are world space: centre xyz, radius w in Out[4].

// The solid sphere of a solar (its archetype's solar_radius when set, else the render extent).
bool SolarSphere(FClientGameobj* Go, float* Out);
// The current system's sun (the first solar of type SUN).
bool FindSystemSunSphere(float* Out);
// The planet or moon (type bits 1|2) whose centre is nearest Centre within MaxDistance.
bool FindHostPlanetSphere(const float* Centre, float MaxDistance, float* Out);
// The same, skipping the solar centred at Exclude (when not null): the nearest other planet.
bool FindNearestPlanetSphere(const float* Centre, float MaxDistance, const float* Exclude, float* Out);
// The sunlight reaching At: the enabled system light ([LightSource]) nearest the sun's centre,
// its colour through its color/atten curves at At's distance, as the engine lights objects there.
// Out rgb.
bool FindSunLightColour(const float* SunCentre, const float* At, float* Out);

// Port-only: the fraction of sunlight (0..1) reaching a world point past the system's planets and
// moons, matching the ship shadows (penumbra from the sun's size; a ringed planet's shadow reaches
// past its ring). 1 with no sun. Cached per frame.
float SolarSunlitAt(const float* Position);
// Port-only: the planets and moons that can shadow the point At within MaxDistance of it (surface
// distance), nearest first -- the list SolarSunlitAt tests, with its shadow reaches (metres behind
// the surface). OutSphere gets 4 floats per caster (centre xyz, radius), OutReach one. Returns the
// count (at most Max); 0 with no sun.
int SolarShadowCasters(const float* At, float MaxDistance, float* OutSphere, float* OutReach, int Max);
// Port-only: whether Position lies within Scale times the radius plus Pad of the sun, a planet or a
// moon -- the ring puff layer keeps its clouds off the bodies (a light cloud round the sun must not
// hang in front of a planet or over the sun). Cached per frame.
bool SolarNearBody(const float* Position, float Scale, float Pad);
// Port-only: how far behind its surface (metres) the shadow of the planet at Centre / Radius must
// reach to cover its ring, or 0 when it carries no ring.
float SolarRingShadowReach(const float* Centre, float Radius);
// Port-only (space_scene_obj_draw.cpp): a planet_eclipses caster's shadow reach, 0 for any other.
float PlanetEclipseCasterReach(FClientGameobj* Go);
