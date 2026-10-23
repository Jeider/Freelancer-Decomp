#pragma once

class INI_Reader;
struct FCliAsteroid;
struct ICamera;

// Port-only (RP9) far rocks: the distant look of an asteroid field as thousands of lit rock
// impostors instead of the retail [Band] ribbon. A fixed per-field set of camera-facing quads fills
// the zone's ellipsoid (clumpy, size classes by a power law), is lit per pixel by the sun and the
// planets' shadows, depth-tested against the scene, and fades in where the near field (billboards,
// dynamic asteroids, cubes) ends and out where the band fades out. Data: a [FarRocks] section of the
// field ini; DATA_EXTRA/SHADERS/far_rocks.hlsl and docs/re/asteroid_far_look.md.

// Reads the keys of a [FarRocks] section of Field's ini (the header already consumed). The defaults
// are filled in when the rocks are first built, from the field's other sections.
void FarRocksParseSection(FCliAsteroid* Field, INI_Reader& Reader);
// Drops the field's rocks and entry (field reload / destruct).
void FarRocksForget(FCliAsteroid const* Field);
// Whether the rocks of Field are built and would draw this frame, so the retail band is skipped.
bool FarRocksReplacesBand(FCliAsteroid const* Field);
// Draws the rocks of every field in one pass, with the scene depth bound. Far is the far plane the
// scene was drawn with, Enclosure the field enclosure state (0 none, 1 partial, 2 inside).
void FarRocksDrawAll(ICamera* Cam, float Far, int Enclosure);
// Releases the program and every field's rocks (RenderEx::Shutdown, before the pipeline goes).
void FarRocksShutdown();
