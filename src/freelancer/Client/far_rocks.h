#pragma once

class INI_Reader;
struct FCliAsteroid;
struct ICamera;

// Port-only (RP9) far rocks: the distant look of an asteroid field as thousands of lit rock
// impostors instead of the retail [Band] ribbon. A fixed per-field set of camera-facing quads, each
// drawn as a lumpy sphere (outline, normal, bump) lit by the field's sun and the system ambient and
// coloured with the diffuse texture of one of the field's dynamic asteroids, fills the zone's
// ellipsoid (clumpy, size classes by a power law), is depth-tested against the scene, and fades in
// where the billboards end and out where the band fades out. Data: a [FarRocks] section of the
// field ini; DATA_EXTRA/SHADERS/far_rocks.hlsl and docs/re/asteroid_far_look.md.

// Reads the keys of a [FarRocks] section of Field's ini (the header already consumed). The defaults
// are filled in when the rocks are first built, from the field's other sections.
void FarRocksParseSection(FCliAsteroid* Field, INI_Reader& Reader);
// Drops the field's rocks and entry (field reload / destruct).
void FarRocksForget(FCliAsteroid const* Field);
// Whether the retail band of Field is skipped: its [FarRocks] has replace_band, the feature and its
// program are on and the field is not fog-blocked. True from the first frame, built or not yet.
bool FarRocksReplacesBand(FCliAsteroid const* Field);
// Draws the rocks of every field in one pass, with the scene depth bound. Far is the far plane the
// scene was drawn with, Enclosure the field enclosure state (0 none, 1 partial, 2 inside).
void FarRocksDrawAll(ICamera* Cam, float Far, int Enclosure);
// Releases the program and every field's rocks (RenderEx::Shutdown, before the pipeline goes).
void FarRocksShutdown();
