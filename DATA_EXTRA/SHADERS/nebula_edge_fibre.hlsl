// Edge: clouds of fine fibres drawn out along the flow (see NEBULA_FIBRE in nebula_volume.hlsl).
// No point lights, to leave SM3 registers for the fibre lookup.
#define NEBULA_FIBRE 1
#define NEBULA_POINT_LIGHTS 0
#include "nebula_volume.hlsl"
