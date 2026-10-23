#pragma once

class INI_Reader;
struct ICamera;

// Port-only (RP9) space layers: world-anchored layers of camera-facing sprites, each living in
// its own distance shell around the camera, so open space has parallax between the star sphere
// and the ship (faint far veils, near dust and debris, a sparse star-point layer). Data comes
// from [SpaceLayer] sections of a system ini; docs/re/space_layers.md.

// Reads the keys of one [SpaceLayer] section (the header already consumed). At most 8 layers
// per system; a layer without a resolvable shape is dropped.
void SpaceLayersParseSection(INI_Reader& Reader);
// Drops every layer (system load / leave).
void SpaceLayersClear();
// Draws every layer once for the frame (no field enclosure): after the texture panels.
void SpaceLayersDraw(ICamera* Cam);
