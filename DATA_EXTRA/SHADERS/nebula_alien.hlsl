// Alien: glowing vein filaments threading the gas (see NEBULA_VEINS in nebula_volume.hlsl).
// No point lights, to leave SM3 registers for the vein lookups.
#define NEBULA_VEINS 1
#define NEBULA_POINT_LIGHTS 0
#include "nebula_volume.hlsl"
