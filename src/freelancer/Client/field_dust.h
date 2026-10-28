#pragma once

class INI_Reader;
struct FCliAsteroid;
struct ICamera;

// Port-only (RP9) field dust: a faint lit dust volume filling an asteroid field's zone ellipsoid --
// the unresolved small debris between the far rocks. One analytic volume per field (the view ray
// against the zone ellipsoid, the exact optical depth of a smooth profile, a few noise samples,
// single scattering with the sun and the planets' shadows), marched at reduced resolution and
// composited depth-aware, over the opaque scene and the far rocks, before the volumetric nebula.
// Data: a [FieldDust] section of the field ini; DATA_EXTRA/SHADERS/field_dust.hlsl and
// docs/re/asteroid_far_look.md ("Field dust").

// Reads the keys of a [FieldDust] section of Field's ini (the header already consumed). The defaults
// are filled in when the dust is first built, from the field's other sections.
void FieldDustParseSection(FCliAsteroid* Field, INI_Reader& Reader);
// Drops the field's dust (field reload / destruct).
void FieldDustForget(FCliAsteroid const* Field);
// Draws the dust of every field in reach for the frame. Near / Far are the planes the scene was drawn
// with, Enclosure the field enclosure state (0 none, 1 partial, 2 inside).
void FieldDustDraw(ICamera* Cam, float Near, float Far, int Enclosure);
// Releases the programs and the march target (RenderEx::Shutdown, before the pipeline goes). The
// shared noise belongs to SpaceHazeShutdown.
void FieldDustShutdown();

namespace Universe { struct IZone; }
// Port-only ring dust: a planetary ring's [Clouds] puffs (flat camera-facing pictures) replaced by a lit
// dust volume in the ring's slab: the same march as the field dust, with a ring's profile (a hole in
// the middle, soft edges, a slab of the ring layer's thickness). The ring calls this every frame it is
// drawn: Zone is the ring's zone, Thickness the ring layer's (0 = the zone's), Density the ring layer's
// density, Tint the ring's colour (rgb 0..1). Returns true when the dust is drawn instead of the puffs
// (port.ini [Render] ring_dust and the extension are available).
bool FieldDustRingUpdate(Universe::IZone const* Zone, float Thickness, float Density, float const* Tint);
