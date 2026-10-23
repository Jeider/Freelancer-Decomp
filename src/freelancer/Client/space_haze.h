#pragma once

class INI_Reader;
struct ICamera;
struct FRPExTexture;

// Port-only (RP9) space haze: one cheap fullscreen pass of world-anchored gas at a few fixed
// distances from the camera (2..4 shells sampled in a tileable 3D noise along each pixel's view
// ray, front to back), so open space has depth and a medium without big overdrawing sprites.
// Data comes from a [SpaceHaze] section of a system ini; DATA_EXTRA/SHADERS/space_haze.hlsl and
// docs/re/space_layers.md ("Space haze").

// Reads the keys of a [SpaceHaze] section (the header already consumed); the last one wins.
void SpaceHazeParseSection(INI_Reader& Reader);
// Drops the haze (system load / leave).
void SpaceHazeClear();
// Draws the haze once for the frame (no field enclosure): before the sprite layers. Far is the
// far plane the scene was drawn with.
void SpaceHazeDraw(ICamera* Cam, float Far);
// Releases the program and the noise volume (RenderEx::Shutdown, before the pipeline goes).
void SpaceHazeShutdown();
// The shared 32^3 tileable noise volume (R: percentile-normalised density fBm 0..1, G: a colour mix
// fBm), created on first use and owned by SpaceHazeShutdown. Null when it cannot be made.
FRPExTexture* SpaceHazeEnsureNoise();
